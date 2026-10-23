"""Regras de permissão no mesmo formato do Claude Code.

Uma regra é `Ferramenta` ou `Ferramenta(padrão)`:

    Bash(git status *)        comando ("*" vale qualquer coisa; "x:*" no fim é o mesmo que "x *")
    Read(docs/**)             ler arquivo ou pasta (padrão de caminho no estilo do .gitignore)
    Edit(*.xlsx)              criar ou mudar arquivo (Write também vale como Edit)
    WebFetch(domain:x.com)    abrir página ("domain:*.x.com" vale os subdomínios)
    mcp__servidor             conector inteiro; mcp__servidor__ferramenta, uma ferramenta dele
    Agent(nome)               usar um agente nos fluxos
    Fluxo                     propor fluxos (só "negar" tem efeito: fluxo pede OK, menos no Livre)
    GitHub(nome)              ferramentas do GitHub que publicam algo
    Navegador(exemplo.com)    o navegador do Code naquele site ("*.exemplo.com" vale o site e os subdomínios)
    Navegador(clicar:x.com)   só uma ação do navegador (abrir, ler, print, rolar, voltar, clicar, digitar, ou em
                              inglês open, read, print, scroll, back, click, type); "clicar:*" vale em qualquer site
    Navegador(localhost:5173) com porta, só aquela porta; sem porta, qualquer uma

O site das regras e o das páginas passam pela mesma leitura que o navegador faz (host_canonico): minúsculas, sem
ponto no fim, %2e e letras largas desfeitos, IDN em punycode, IPv4 em qualquer forma (127.1, 2130706433, 0x7f000001)
em decimal com pontos e IPv6 comprimido entre colchetes. Assim "https://exemplo.com./" não escapa de uma regra
"Navegador(exemplo.com)".

A ordem é a do Claude Code: negar, depois perguntar, depois permitir; a primeira
que casar decide, venha de onde vier. Os escopos são o app (config do Clave), a
pasta de trabalho (.claude/settings.json e .claude/settings.local.json, os mesmos
arquivos do Claude Code) e a tarefa (só enquanto a resposta roda).
"""
from __future__ import annotations

import ipaddress
import json
import os
import re
import sys
import unicodedata
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import config
from i18n import t

ACOES = ("deny", "ask", "allow")
NOME_ACAO = {"deny": "negar", "ask": "perguntar", "allow": "permitir"}
ESCOPOS = {"app": "todo o Clave", "pasta": "esta pasta", "tarefa": "esta tarefa", "comando": "o comando de barra"}  # mostrar com t()

# ferramentas do Claude Code que o Clave entende, e o que cada uma vira aqui
CONHECIDAS = {
    "Bash": "Bash", "PowerShell": "Bash",
    "Read": "Read", "Glob": "Read", "Grep": "Read", "LS": "Read",
    "Edit": "Edit", "Write": "Edit", "MultiEdit": "Edit", "NotebookEdit": "Edit",
    "WebFetch": "WebFetch", "WebSearch": "WebSearch",
    "Agent": "Agent", "Task": "Agent", "Fluxo": "Fluxo", "GitHub": "GitHub", "Email": "Email",
    "Navegador": "Navegador",
}

# as ações do navegador do Code, como aparecem nas regras (navegador_clicar -> "clicar")
ACOES_NAVEGADOR = ("abrir", "ler", "print", "rolar", "voltar", "clicar", "digitar")
# os mesmos nomes em inglês, aceitos nas regras (viram o nome em português)
ACOES_NAVEGADOR_EN = {"open": "abrir", "read": "ler", "print": "print", "scroll": "rolar", "back": "voltar",
                      "click": "clicar", "type": "digitar"}


def acao_navegador(palavra: str) -> str | None:
    """'clicar' ou 'click' -> 'clicar'; qualquer outra coisa -> None."""
    p = str(palavra or "").strip().lower()
    return p if p in ACOES_NAVEGADOR else ACOES_NAVEGADOR_EN.get(p)

# ferramenta do Clave -> (ferramenta do Claude Code, campos que dizem o alvo)
ALVOS = {
    "rodar_comando": ("Bash", ("comando",)),
    "ler_arquivo": ("Read", ("caminho",)),
    "listar_pasta": ("Read", ("caminho",)),
    "buscar_texto": ("Read", ("caminho",)),
    "achar_arquivos": ("Read", ("caminho",)),
    "excel_ler": ("Read", ("caminho",)),
    "mostrar_arquivo": ("Read", ("caminho",)),
    "excel_abrir": ("Read", ("caminho",)),
    "escrever_arquivo": ("Edit", ("caminho",)),
    "editar_arquivo": ("Edit", ("caminho",)),
    "excel_alterar": ("Edit", ("caminho", "saida")),
    "excel_no_app": ("Edit", ("caminho", "saida")),
    "word_ler": ("Read", ("caminho",)),
    "word_criar": ("Edit", ("caminho",)),
    "word_alterar": ("Edit", ("caminho", "saida")),
    "word_no_app": ("Edit", ("caminho", "saida")),
    "email_salvar_anexo": ("Edit", ("caminho",)),
}

_REGRA = re.compile(r"^\s*([A-Za-z_][\w-]*)\s*(?:\((.*)\))?\s*$", re.S)


@dataclass(frozen=True)
class Regra:
    acao: str        # deny | ask | allow
    texto: str       # como foi escrita
    escopo: str      # app | pasta | tarefa | comando
    origem: str = "" # arquivo de onde veio (escopo pasta)

    @property
    def ferramenta(self) -> str:
        return analisar(self.texto)[0]

    @property
    def padrao(self) -> str | None:
        return analisar(self.texto)[1]

    def descrever(self) -> str:
        escopo = t(ESCOPOS[self.escopo]) if self.escopo in ESCOPOS else self.escopo
        return t("regra \"{regra}\" ({escopo})", regra=self.texto, escopo=escopo)


def analisar(texto: str) -> tuple[str, str | None]:
    """'Bash(git status *)' -> ('Bash', 'git status *'). Ferramenta desconhecida volta como veio."""
    m = _REGRA.match(texto or "")
    if not m:
        return "", None
    nome, padrao = m.group(1), m.group(2)
    if nome.startswith("mcp__"):
        return nome, padrao
    nome = CONHECIDAS.get(nome, nome)
    if padrao is not None:
        padrao = padrao.strip()
        if padrao in ("", "*") and nome != "Bash":
            padrao = None
    return nome, padrao


def validar(texto: str) -> str | None:
    """Mensagem de erro (no idioma de quem usa), ou None se a regra é boa."""
    texto = (texto or "").strip()
    if not texto:
        return t("A regra está vazia.")
    m = _REGRA.match(texto)
    if not m:
        return t("Escreva no formato Ferramenta(padrão), por exemplo Bash(git status *) ou Edit(docs/**).")
    nome = m.group(1)
    if nome.startswith("mcp__"):
        if nome.rstrip("_") == "mcp" or "*" in nome.replace("__*", ""):
            return t("Para conector, use mcp__nome-do-conector ou mcp__nome-do-conector__ferramenta.")
        return None
    if nome not in CONHECIDAS:
        return t("\"{nome}\" não é uma ferramenta conhecida. Use Bash, Read, Edit, WebFetch, WebSearch, Agent, Fluxo, GitHub, Email, Navegador ou mcp__conector.", nome=nome)
    padrao = m.group(2)
    if CONHECIDAS[nome] == "WebFetch" and padrao and not padrao.strip().startswith("domain:"):
        return t("Para páginas da web, use WebFetch(domain:exemplo.com).")
    if CONHECIDAS[nome] == "Navegador" and padrao and padrao.strip() not in ("", "*"):
        return _erro_padrao_navegador(padrao)
    return None


def _erro_padrao_navegador(padrao: str) -> str | None:
    if _padrao_navegador(padrao) is not None:
        return None
    acoes = ", ".join(ACOES_NAVEGADOR)
    acoes_en = ", ".join(ACOES_NAVEGADOR_EN)
    m = re.match(r"^\s*([^:/\[\]\s]*):", padrao or "")
    if m and not m.group(1):
        return t("Falta a ação antes dos dois-pontos. Use, por exemplo, Navegador(clicar:exemplo.com). As ações são: {acoes} (ou, em inglês, {acoes_en}).",
                 acoes=acoes, acoes_en=acoes_en)
    if m and re.fullmatch(r"[A-Za-z]+", m.group(1)) and m.group(1).lower() not in ("http", "https", "domain"):
        resto = (padrao or "").split(":", 1)[1]
        if not re.match(r"\s*\d+\s*(/|$)", resto):  # "localhost:5173" é site com porta, não ação
            return t("\"{acao}\" não é uma ação do navegador. As ações são: {acoes} (ou, em inglês, {acoes_en}).",
                     acao=m.group(1), acoes=acoes, acoes_en=acoes_en)
    return t("Para o navegador, use Navegador(exemplo.com), Navegador(clicar:exemplo.com) ou Navegador(clicar:localhost:5173). As ações são: {acoes} (ou, em inglês, {acoes_en}).",
             acoes=acoes, acoes_en=acoes_en)


# ---------------- de onde vêm as regras ----------------

def _do_dict(d: dict, escopo: str, origem: str = "") -> list[Regra]:
    regras = []
    for acao in ACOES:
        for t in (d or {}).get(acao) or []:
            if isinstance(t, str) and t.strip() and not validar(t):
                regras.append(Regra(acao, t.strip(), escopo, origem))
    return regras


def arquivos_da_pasta(pasta: Path) -> list[Path]:
    base = Path(pasta) / ".claude"
    return [base / "settings.json", base / "settings.local.json"]


def ler_pasta(pasta: Path | None) -> tuple[list[Regra], list[str]]:
    """Regras do .claude/settings.json e do .claude/settings.local.json da pasta, mais avisos de leitura."""
    if not pasta:
        return [], []
    regras, avisos = [], []
    for arq in arquivos_da_pasta(Path(pasta)):
        if not arq.is_file():
            continue
        try:
            dados = json.loads(arq.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as e:
            avisos.append(t("{arquivo}: não deu para ler ({erro}).", arquivo=arq, erro=e))
            continue
        perm = dados.get("permissions") if isinstance(dados, dict) else None
        if isinstance(perm, dict):
            regras += _do_dict(perm, "pasta", str(arq))
            for acao in ACOES:
                for texto in perm.get(acao) or []:
                    if isinstance(texto, str) and validar(texto):
                        avisos.append(t("{arquivo}: regra ignorada \"{regra}\" ({erro})", arquivo=arq.name, regra=texto,
                                        erro=validar(texto)))
    return regras, avisos


def do_app(cfg: dict | None = None) -> list[Regra]:
    cfg = cfg if cfg is not None else config.carregar()
    return _do_dict(cfg.get("permissoes") or {}, "app")


def coletar(cfg: dict | None, pasta: Path | None, tarefa: list[Regra] | None = None) -> list[Regra]:
    return do_app(cfg) + ler_pasta(pasta)[0] + list(tarefa or [])


# ---------------- gravar ----------------

def salvar_na_pasta(pasta: Path, acao: str, texto: str) -> Path:
    """Guarda a regra em .claude/settings.local.json (o arquivo pessoal do Claude Code, fora do git)."""
    if acao not in ACOES or validar(texto):
        raise ValueError(validar(texto) or t("Ação inválida."))
    arq = Path(pasta) / ".claude" / "settings.local.json"
    dados: dict = {}
    if arq.is_file():
        try:
            dados = json.loads(arq.read_text(encoding="utf-8-sig"))
        except ValueError as e:
            raise ValueError(t("O arquivo {arquivo} não é um JSON válido; conserte antes ({erro}).", arquivo=arq, erro=e)) from e
        if not isinstance(dados, dict):
            raise ValueError(t("O arquivo {arquivo} não tem o formato esperado.", arquivo=arq))
    perm = dados.setdefault("permissions", {})
    lista = perm.setdefault(acao, [])
    if texto not in lista:
        lista.append(texto)
    arq.parent.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, arq)
    return arq


def remover_da_pasta(pasta: Path, acao: str, texto: str) -> bool:
    mudou = False
    for arq in arquivos_da_pasta(Path(pasta)):
        if not arq.is_file():
            continue
        try:
            dados = json.loads(arq.read_text(encoding="utf-8-sig"))
        except ValueError:
            continue
        lista = ((dados.get("permissions") or {}).get(acao)) if isinstance(dados, dict) else None
        if isinstance(lista, list) and texto in lista:
            lista.remove(texto)
            arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            mudou = True
    return mudou


def salvar_no_app(acao: str, texto: str) -> None:
    if acao not in ACOES or validar(texto):
        raise ValueError(validar(texto) or t("Ação inválida."))
    cfg = config.carregar()
    perm = {a: list((cfg.get("permissoes") or {}).get(a) or []) for a in ACOES}
    if texto not in perm[acao]:
        perm[acao].append(texto)
    config.salvar({"permissoes": perm})


def remover_do_app(acao: str, texto: str) -> bool:
    cfg = config.carregar()
    perm = {a: list((cfg.get("permissoes") or {}).get(a) or []) for a in ACOES}
    if texto not in perm.get(acao, []):
        return False
    perm[acao].remove(texto)
    config.salvar({"permissoes": perm})
    return True


# ---------------- casar padrões ----------------

def subcomandos(cmd: str) -> list[str]:
    """Separa "a && b | c; d" nas partes, respeitando aspas. Regra de permitir precisa valer para todas."""
    partes, atual, aspas, i = [], [], None, 0
    while i < len(cmd):
        ch = cmd[i]
        if aspas:
            atual.append(ch)
            if ch == aspas:
                aspas = None
        elif ch in ("'", '"'):
            aspas = ch
            atual.append(ch)
        elif cmd.startswith(("&&", "||"), i):
            partes.append("".join(atual))
            atual = []
            i += 2
            continue
        elif ch in ";|\n&":
            partes.append("".join(atual))
            atual = []
        else:
            atual.append(ch)
        i += 1
    partes.append("".join(atual))
    return [p.strip() for p in partes if p.strip()]


def casa_comando(padrao: str | None, cmd: str) -> bool:
    if padrao is None or padrao.strip() == "*":
        return True
    p = " ".join(padrao.split())
    c = " ".join(cmd.split())
    if p.endswith(":*"):
        p = p[:-2].rstrip() + " *"
    rx = "".join(".*" if ch == "*" else re.escape(ch) for ch in p)
    if re.fullmatch(rx, c, re.I | re.S):
        return True
    # "npm run *" também vale para "npm run" sozinho
    return p.endswith(" *") and c.lower() == p[:-2].lower()


def _glob_rx(padrao: str) -> str:
    out, i = [], 0
    while i < len(padrao):
        if padrao.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif padrao.startswith("/**", i) and i + 3 == len(padrao):
            out.append("(?:/.*)?")
            i += 3
        elif padrao.startswith("**", i):
            out.append(".*")
            i += 2
        elif padrao[i] == "*":
            out.append("[^/]*")
            i += 1
        elif padrao[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(padrao[i]))
            i += 1
    return "".join(out)


def _posix_abs(p: Path) -> str:
    """C:\\Users\\Ana -> /c/Users/Ana (o jeito que as regras do Claude Code escrevem caminho absoluto)."""
    s = p.as_posix()
    if len(s) >= 2 and s[1] == ":":
        s = "/" + s[0].lower() + s[2:]
    return s


def casa_caminho(padrao: str | None, caminho: Path, base: Path) -> bool:
    if padrao is None:
        return True
    pd = padrao.strip().replace("\\", "/")
    flags = re.I if sys.platform == "win32" else 0
    if pd.startswith("~/"):
        pd = "/" + _posix_abs(Path.home())[1:] + pd[1:]
        absoluto = True
    elif pd.startswith("//"):
        pd = pd[1:]
        absoluto = True
    elif len(pd) >= 3 and pd[1] == ":" and pd[2] == "/":  # C:/... escrito à moda do Windows
        pd = "/" + pd[0].lower() + pd[2:]
        absoluto = True
    else:
        absoluto = False
    if pd.endswith("/") and len(pd) > 1:
        pd = pd + "**"
    if absoluto:
        alvo = _posix_abs(caminho.resolve())
        return bool(re.fullmatch(_glob_rx(pd), alvo, flags)) or _algum_pai(pd, alvo, flags)
    try:
        rel = caminho.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return False  # padrão relativo não vale fora da pasta
    if pd.startswith("./"):
        pd = pd[2:]
    if pd.startswith("/"):
        pd = pd[1:]
    elif "/" not in pd.rstrip("/"):
        pd = "**/" + pd  # sem barra: vale em qualquer profundidade, como no .gitignore
    rel = "" if rel == "." else rel
    return bool(re.fullmatch(_glob_rx(pd), rel, flags)) or _algum_pai(pd, rel, flags)


def _algum_pai(pd: str, alvo: str, flags) -> bool:
    """Regra que casa uma pasta vale para o que está dentro dela (Read(docs) cobre docs/a.md)."""
    partes = alvo.split("/")
    for n in range(1, len(partes)):
        if re.fullmatch(_glob_rx(pd), "/".join(partes[:n]), flags):
            return True
    return False


# ---------------- endereços lidos como o navegador lê (WHATWG URL) ----------------
# A regra e a página precisam falar do mesmo site. Um leitor de URL diferente do navegador (urllib, regex) deixa
# passar "https://exemplo.com\@outro.com/" (o Chromium abre exemplo.com), "exemplo%2ecom", "ｅｘｅｍｐｌｏ.com",
# "exemplo.com." e "127.1". Aqui o endereço é lido como o Chromium lê, e o navegador.py abre o endereço remontado
# a partir destas partes: o que foi conferido é o que abre.

_PROIBIDOS_NO_HOST = set("#/:<>?@[\\]^|%")   # mais controle, espaço e DEL (WHATWG: forbidden domain code point)
_PONTOS = {"。": ".", "．": ".", "｡": "."}


def _termina_em_numero(h: str) -> bool:
    partes = h.split(".")
    if partes[-1] == "" and len(partes) > 1:
        partes.pop()
    ultima = partes[-1]
    return bool(re.fullmatch(r"[0-9]+|0x[0-9a-f]*", ultima))


def _ipv4(h: str) -> str | None:
    """O IPv4 do WHATWG (as mesmas formas que o inet_aton aceita): 127.1, 2130706433, 0x7f000001, 0177.0.0.1."""
    partes = h.split(".")
    if partes[-1] == "" and len(partes) > 1:
        partes.pop()
    if len(partes) > 4:
        return None
    nums = []
    for p in partes:
        if p.startswith("0x"):
            base, dig, rx = 16, p[2:], r"[0-9a-f]*"
        elif len(p) > 1 and p.startswith("0"):
            base, dig, rx = 8, p[1:], r"[0-7]+"
        else:
            base, dig, rx = 10, p, r"[0-9]+"
        if not re.fullmatch(rx, dig):
            return None
        nums.append(int(dig, base) if dig else 0)
    if any(n > 255 for n in nums[:-1]) or nums[-1] >= 256 ** (5 - len(nums)):
        return None
    valor = nums[-1] + sum(n * 256 ** (3 - i) for i, n in enumerate(nums[:-1]))
    return ".".join(str((valor >> s) & 255) for s in (24, 16, 8, 0))


def host_canonico(host: str) -> str | None:
    """O host como o navegador entende: minúsculo, sem ponto no fim, %xx desfeito, NFKC, IDN em punycode, IPv4 em
    decimal com pontos, IPv6 comprimido entre colchetes. None quando o navegador recusaria."""
    h = str(host or "")
    if not h:
        return None
    if h.startswith("["):
        if not h.endswith("]") or "%" in h:
            return None
        try:
            return f"[{ipaddress.IPv6Address(h[1:-1]).compressed}]"
        except ValueError:
            return None
    try:
        h = urllib.parse.unquote_to_bytes(h).decode("utf-8")
    except UnicodeDecodeError:
        return None
    h = unicodedata.normalize("NFKC", "".join(_PONTOS.get(c, c) for c in h))
    if not h.isascii():
        try:
            import idna  # IDNA 2008 com UTS 46 sem a transição, como o Chromium
            h = idna.encode(h, uts46=True, transitional=False).decode("ascii")
        except Exception:  # noqa: BLE001 (idna.IDNAError, UnicodeError...): tenta o IDNA 2003 da biblioteca padrão
            try:
                h = h.encode("idna").decode("ascii")
            except UnicodeError:
                return None
    h = h.lower()
    if any(ord(c) <= 0x20 or ord(c) == 0x7F or c in _PROIBIDOS_NO_HOST for c in h):
        return None
    h = h.rstrip(".")
    if not h or h.startswith(".") or ".." in h:
        return None
    if _termina_em_numero(h):
        return _ipv4(h)
    return h


def partes_url(url: str) -> tuple[str, str, int, str] | None:
    """(esquema, host, porta, caminho) de um endereço http ou https lido como o navegador lê: barra invertida vale
    barra, o host é o que vem depois do último @, porta padrão quando não tem. None quando não é http(s) válido."""
    s = re.sub(r"[\t\n\r]", "", str(url or "")).strip("\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f"
                                                          "\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b"
                                                          "\x1c\x1d\x1e\x1f ")
    m = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):(.*)$", s, re.S)
    if not m or m.group(1).lower() not in ("http", "https"):
        return None
    esquema = m.group(1).lower()
    resto = m.group(2).lstrip("/\\")
    fim = min((i for i in (resto.find(c) for c in "/\\?#") if i >= 0), default=len(resto))
    autoridade, caminho = resto[:fim], resto[fim:]
    host_porta = autoridade.rsplit("@", 1)[-1]
    if host_porta.startswith("["):
        j = host_porta.find("]")
        if j < 0:
            return None
        host_txt, depois = host_porta[:j + 1], host_porta[j + 1:]
        if depois and not depois.startswith(":"):
            return None
        porta_txt = depois[1:]
    else:
        host_txt, _, porta_txt = host_porta.partition(":")
    if porta_txt and not re.fullmatch(r"[0-9]+", porta_txt):
        return None
    porta = int(porta_txt) if porta_txt else (80 if esquema == "http" else 443)
    if porta > 65535:
        return None
    host = host_canonico(host_txt)
    if not host:
        return None
    corte = min((i for i in (caminho.find("?"), caminho.find("#")) if i >= 0), default=len(caminho))
    caminho = caminho[:corte].replace("\\", "/") + caminho[corte:]
    caminho = re.sub(r"[\x00-\x20\x7f]", lambda c: "%%%02X" % ord(c.group()), caminho)
    return esquema, host, porta, caminho


def url_canonica(url: str) -> str | None:
    """O endereço remontado das partes que as regras conferem (sem usuário e senha): é este que o navegador abre."""
    p = partes_url(url)
    if not p:
        return None
    esquema, host, porta, caminho = p
    padrao = 80 if esquema == "http" else 443
    if not caminho.startswith("/"):
        caminho = "/" + caminho
    return f"{esquema}://{host}{'' if porta == padrao else f':{porta}'}{caminho}"


def _com_esquema(url: str) -> str:
    """'exemplo.com' e 'localhost:5173' ganham http:// para serem lidos; 'mailto:x' e 'about:blank' não."""
    s = str(url or "").strip()
    if re.match(r"^https?:", s, re.I):
        return s
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:(?![0-9])", s):
        return ""
    return "http://" + s if s else ""


def site_de(url: str) -> tuple[str, int] | None:
    """(host, porta) de um endereço ou de 'host[:porta]'; None quando não é um site http(s)."""
    p = partes_url(_com_esquema(url))
    return (p[1], p[2]) if p else None


def host_de(url: str) -> str:
    """https://www.exemplo.com:8080/x -> www.exemplo.com, já na forma canônica (o que as regras comparam)."""
    s = site_de(url)
    return s[0] if s else ""


def alvo_navegador(acao: str, url: str) -> str:
    """O que as regras do navegador comparam: 'ação:host:porta' (clicar:exemplo.com:443), ou 'ação:' sem site."""
    s = site_de(url)
    return f"{acao}:{s[0]}:{s[1]}" if s else f"{acao}:"


def _ler_alvo(valor: str) -> tuple[str, str, int | None]:
    acao, _, resto = str(valor or "").partition(":")
    if resto.startswith("["):
        j = resto.find("]")
        host, porta = (resto[:j + 1], resto[j + 2:]) if j >= 0 else (resto, "")
    else:
        h, sep, p = resto.rpartition(":")
        host, porta = (h, p) if sep and re.fullmatch(r"[0-9]+", p) else (resto, "")
    return acao, (host_canonico(host) or "") if host else "", int(porta) if porta.isdigit() else None


def _site_da_regra(texto: str) -> tuple[str, int | None] | None:
    """'exemplo.com', '*.exemplo.com', 'localhost:5173', 'https://x.com/caminho', '[::1]:3000' -> (host, porta)."""
    d = texto.strip()
    if d.startswith("domain:"):
        d = d[len("domain:"):].strip()
    d = re.sub(r"^[a-z][a-z0-9+.-]*://", "", d)
    d = re.split(r"[/\\?#]", d, maxsplit=1)[0].rsplit("@", 1)[-1]
    if d in ("", "*"):
        return "*", None
    if d.startswith("["):
        j = d.find("]")
        if j < 0:
            return None
        host_txt, depois = d[:j + 1], d[j + 1:]
        if depois and not depois.startswith(":"):
            return None
        porta_txt = depois[1:]
    else:
        host_txt, _, porta_txt = d.partition(":")
    if porta_txt and (not re.fullmatch(r"[0-9]+", porta_txt) or int(porta_txt) > 65535):
        return None
    porta = int(porta_txt) if porta_txt else None
    if host_txt == "*":
        return "*", porta
    curinga = host_txt.startswith("*.")
    host = host_canonico(host_txt[2:] if curinga else host_txt)
    if not host or "*" in host:  # curinga só no começo: "*.exemplo.com"
        return None
    return ("*." + host if curinga else host), porta


def _padrao_navegador(padrao: str) -> tuple[str | None, str, int | None] | None:
    """'clicar:exemplo.com' -> ('clicar', 'exemplo.com', None); 'click:localhost:5173' -> ('clicar', 'localhost', 5173);
    'exemplo.com' -> (None, 'exemplo.com', None); 'digitar' -> ('digitar', '*', None). Aceita domain:, http://,
    porta e caminho (o caminho não conta). None quando não dá para entender: ação desconhecida ("apagar:x.com"),
    ação vazia (":x.com") ou site inválido."""
    p = re.sub(r"\s*:\s*", ":", (padrao or "").strip().lower())  # "click : x.com" é o mesmo que "click:x.com"
    if p in ("", "*"):
        return None, "*", None
    if acao_navegador(p):
        return acao_navegador(p), "*", None
    acao = None
    m = re.match(r"^([^:/\[\]\s]*):(.*)$", p, re.S)
    if m:
        palavra, resto = m.group(1), m.group(2)
        eh_url = palavra in ("http", "https") or resto.startswith("//")
        eh_porta = bool(re.match(r"\s*[0-9]+\s*(/|$)", resto))
        if not eh_url and not eh_porta and palavra != "domain":
            if palavra == "*":
                acao = None
            elif acao_navegador(palavra):
                acao = acao_navegador(palavra)
            else:
                return None  # ação vazia ou desconhecida: não vira um site chamado "click"
            p = resto.strip()
    site = _site_da_regra(p)
    if site is None:
        return None
    return acao, site[0], site[1]


def casa_dominio(padrao: str | None, url_ou_dominio: str) -> bool:
    if padrao is None:
        return True
    if not padrao.startswith("domain:"):
        return False
    regra = _site_da_regra(padrao[len("domain:"):])
    host = host_de(url_ou_dominio)
    if regra is None or not host:
        return False
    dom = regra[0]
    if dom == "*":
        return True
    if dom.startswith("*."):
        return host == dom[2:] or host.endswith(dom[1:])
    return host == dom


def casa_navegador(padrao: str | None, valor: str) -> bool:
    """valor é "ação:host:porta" (clicar:exemplo.com:443, de alvo_navegador). "*.exemplo.com" vale o próprio site
    e os subdomínios; uma porta na regra só vale para aquela porta."""
    if padrao is None:
        return True
    lido = _padrao_navegador(padrao)
    if lido is None:
        return False
    acao_regra, dom, porta_regra = lido
    acao, host, porta = _ler_alvo(valor)
    if acao_regra and acao_regra != acao:
        return False
    if porta_regra is not None and porta_regra != porta:
        return False
    if dom == "*":
        return True
    if not host:
        return False
    if dom.startswith("*."):
        return host == dom[2:] or host.endswith(dom[1:])
    return host == dom


def acao_da_regra_navegador(regra: Regra) -> str | None:
    """A ação escrita numa regra do navegador (clicar em Navegador(clicar:x.com)), ou None quando vale para todas."""
    nome, padrao = analisar(regra.texto)
    if nome != "Navegador" or padrao is None:
        return None
    lido = _padrao_navegador(padrao)
    return lido[0] if lido else None


def casa(regra: Regra, ferramenta: str, valor, base: Path | None) -> bool:
    nome, padrao = analisar(regra.texto)
    if ferramenta.startswith("mcp__"):
        if not nome.startswith("mcp__"):
            return False
        r = nome.rstrip("*").rstrip("_")
        return ferramenta == r or ferramenta.startswith(r + "__")
    if nome != ferramenta:
        return False
    if ferramenta == "Bash":
        return casa_comando(padrao, str(valor))
    if ferramenta in ("Read", "Edit"):
        return casa_caminho(padrao, Path(valor), base or Path.cwd())
    if ferramenta in ("WebFetch", "WebSearch"):
        return casa_dominio(padrao, str(valor))
    if ferramenta == "Navegador":
        return casa_navegador(padrao, str(valor))
    return padrao is None or casa_comando(padrao, str(valor))


def generica(regra: Regra) -> bool:
    """Regra que libera tudo de uma ferramenta (Bash, Bash(*), Edit): não vale para o que é perigoso."""
    _, padrao = analisar(regra.texto)
    return padrao is None or padrao.strip() in ("*", "**", "**/*", "//**")


def avaliar(regras: list[Regra], alvos: list[tuple[str, object]], base: Path | None) -> tuple[str | None, Regra | None]:
    """Primeira regra que decide (negar > perguntar > permitir) para todos os alvos de uma ação."""
    if not alvos:
        return None, None
    for acao in ("deny", "ask"):
        for r in (x for x in regras if x.acao == acao):
            for ferr, valor in alvos:
                pedacos = subcomandos(str(valor)) or [str(valor)] if ferr == "Bash" else [valor]
                if any(casa(r, ferr, v, base) for v in pedacos):
                    return acao, r
    # permitir: cada alvo (e cada pedaço de comando) precisa de alguma regra de permitir
    permitidas = [x for x in regras if x.acao == "allow"]
    usada = None
    for ferr, valor in alvos:
        pedacos = (subcomandos(str(valor)) or [str(valor)]) if ferr == "Bash" else [valor]
        for v in pedacos:
            achou = next((r for r in permitidas if casa(r, ferr, v, base)), None)
            if achou is None:
                return None, None
            usada = usada or achou
    return ("allow", usada) if usada else (None, None)


def alvos(nome: str, entrada: dict, resolver) -> list[tuple[str, object]]:
    """O que uma ferramenta do Clave vai tocar, no vocabulário das regras."""
    if nome.startswith(("github_",)):
        return [("GitHub", nome)]
    if nome.startswith("navegador_"):
        # "url" é o endereço que a ação vai tocar: o que navegador_abrir recebe, ou a página aberta (o navegador.py
        # põe ali antes de decidir). O valor leva a porta, para "Navegador(localhost:5173)" não valer na 3000.
        return [("Navegador", alvo_navegador(nome[len("navegador_"):], (entrada or {}).get("url", "")))]
    if nome not in ALVOS:
        return []
    ferr, campos = ALVOS[nome]
    saida = []
    for c in campos:
        v = (entrada or {}).get(c)
        if c == "caminho" and not v and ferr == "Read":
            v = "."
        if isinstance(v, str) and v:
            saida.append((ferr, v if ferr == "Bash" else resolver(v)))
    return saida


# ---------------- sugestões ----------------

_DOIS_TERMOS = {"git", "npm", "pnpm", "yarn", "pip", "py", "python", "dotnet", "gh", "cargo", "winget", "node",
                "npx", "docker", "uv", "poetry"}


def sugerir(nome: str, entrada: dict, ctx) -> str | None:
    """Regra que o cartão de aprovação oferece para "sempre" (a pessoa pode editar antes de salvar)."""
    if nome == "rodar_comando":
        cmd = " ".join(str((entrada or {}).get("comando", "")).split())
        partes = subcomandos(cmd)
        if len(partes) != 1:
            return f"Bash({cmd})" if cmd else None
        toks = partes[0].split(" ")
        if len(toks) >= 2 and toks[0].lower() in _DOIS_TERMOS and not toks[1].startswith("-"):
            return f"Bash({toks[0]} {toks[1]} *)"
        return f"Bash({toks[0]} *)" if len(toks) > 1 else f"Bash({toks[0]})"
    if nome in ALVOS:
        ferr, campos = ALVOS[nome]
        v = (entrada or {}).get(campos[0]) or "."
        p = ctx.resolver(v)
        if ctx.dentro(p):
            rel = ctx.relativo(p)
            if rel in (".", ""):
                return f"{ferr}(**)" if ferr != "Read" else "Read"
            pai = rel.rsplit("/", 1)[0] if "/" in rel else ""
            return f"{ferr}({pai}/**)" if pai else f"{ferr}({rel})"
        pai = p.parent if p.suffix else p
        return f"{ferr}(/{_posix_abs(pai)}/**)"
    if nome.startswith("github_"):
        return f"GitHub({nome})"
    if nome.startswith("navegador_"):
        acao, host = nome[len("navegador_"):], host_de((entrada or {}).get("url", ""))
        return f"Navegador({acao}:{host})" if host else f"Navegador({acao})"
    return None


# ---------------- o que vale para as ferramentas que rodam no servidor da Anthropic ----------------

def dominios_bloqueados(regras: list[Regra]) -> list[str]:
    """WebFetch(domain:x) e WebSearch(domain:x) negados viram a lista blocked_domains da API."""
    doms = []
    for r in regras:
        nome, padrao = analisar(r.texto)
        if r.acao == "deny" and nome in ("WebFetch", "WebSearch") and padrao and padrao.startswith("domain:"):
            d = padrao[len("domain:"):].strip().lower()
            d = d[2:] if d.startswith("*.") else d
            if d and d not in doms:
                doms.append(d)
    return doms


def web_negada(regras: list[Regra]) -> bool:
    return any(r.acao == "deny" and analisar(r.texto) in (("WebFetch", None), ("WebSearch", None)) for r in regras)


def mcp_filtrado(regras: list[Regra], servidor: str) -> tuple[bool, list[str]]:
    """(conector liberado?, ferramentas desligadas). "Perguntar" não existe para conector: vira desligado."""
    desligadas = []
    for r in regras:
        nome, _ = analisar(r.texto)
        if r.acao not in ("deny", "ask") or not nome.startswith("mcp__"):
            continue
        partes = nome[len("mcp__"):].split("__", 1)
        if partes[0] != servidor:
            continue
        if len(partes) == 1 or partes[1] in ("", "*"):
            return False, []
        desligadas.append(partes[1])
    return True, desligadas


def nega(regras: list[Regra], ferramenta: str, valor: str = "") -> Regra | None:
    for r in regras:
        if r.acao == "deny" and casa(r, ferramenta, valor, None):
            return r
    return None
