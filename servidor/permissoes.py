"""Regras de permissão no mesmo formato do Claude Code.

Uma regra é `Ferramenta` ou `Ferramenta(padrão)`:

    Bash(git status *)        comando ("*" vale qualquer coisa; "x:*" no fim é o mesmo que "x *")
    Read(docs/**)             ler arquivo ou pasta (padrão de caminho no estilo do .gitignore)
    Edit(*.xlsx)              criar ou mudar arquivo (Write também vale como Edit)
    WebFetch(domain:x.com)    abrir página ("domain:*.x.com" vale os subdomínios)
    mcp__servidor             conector inteiro; mcp__servidor__ferramenta, uma ferramenta dele
    Agent(nome)               usar um agente nos fluxos
    Fluxo                     propor fluxos (só "negar" tem efeito: fluxo sempre pede OK)
    GitHub(nome)              ferramentas do GitHub que publicam algo

A ordem é a do Claude Code: negar, depois perguntar, depois permitir; a primeira
que casar decide, venha de onde vier. Os escopos são o app (config do Clave), a
pasta de trabalho (.claude/settings.json e .claude/settings.local.json, os mesmos
arquivos do Claude Code) e a tarefa (só enquanto a resposta roda).
"""
from __future__ import annotations

import json
import os
import re
import sys
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
    "Agent": "Agent", "Task": "Agent", "Fluxo": "Fluxo", "GitHub": "GitHub",
}

# ferramenta do Clave -> (ferramenta do Claude Code, campos que dizem o alvo)
ALVOS = {
    "rodar_comando": ("Bash", ("comando",)),
    "ler_arquivo": ("Read", ("caminho",)),
    "listar_pasta": ("Read", ("caminho",)),
    "buscar_texto": ("Read", ("caminho",)),
    "achar_arquivos": ("Read", ("caminho",)),
    "excel_ler": ("Read", ("caminho",)),
    "excel_abrir": ("Read", ("caminho",)),
    "escrever_arquivo": ("Edit", ("caminho",)),
    "editar_arquivo": ("Edit", ("caminho",)),
    "excel_alterar": ("Edit", ("caminho", "saida")),
    "excel_no_app": ("Edit", ("caminho", "saida")),
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
        return t("\"{nome}\" não é uma ferramenta conhecida. Use Bash, Read, Edit, WebFetch, WebSearch, Agent, Fluxo, GitHub ou mcp__conector.", nome=nome)
    padrao = m.group(2)
    if CONHECIDAS[nome] == "WebFetch" and padrao and not padrao.strip().startswith("domain:"):
        return t("Para páginas da web, use WebFetch(domain:exemplo.com).")
    return None


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


def casa_dominio(padrao: str | None, url_ou_dominio: str) -> bool:
    if padrao is None:
        return True
    if not padrao.startswith("domain:"):
        return False
    dom = padrao[len("domain:"):].strip().lower()
    host = re.sub(r"^[a-z]+://", "", url_ou_dominio.lower()).split("/")[0].split(":")[0]
    if dom.startswith("*."):
        return host.endswith(dom[1:])
    return host == dom


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
