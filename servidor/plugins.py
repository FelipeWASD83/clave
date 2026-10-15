"""Plugins no formato do Claude Code: pacotes com skills, agentes e comandos.

Um plugin é uma pasta com `.claude-plugin/plugin.json` (só "name" é obrigatório) e as partes:
`skills/<nome>/SKILL.md`, `agents/*.md` e `commands/*.md`. O Clave acrescenta `fluxos/*.json`
(modelos de fluxo), que o Claude Code ignora. Hooks e servidores MCP locais não são usados aqui:
o app avisa na hora de instalar.

Os embutidos moram em <app>/plugins; os instalados, em dados/plugins. Quais estão ligados fica
em config["plugins"]. Os nomes de skill, agente e comando de um plugin ganham o prefixo
"plugin:", como no Claude Code (ex.: /escrita:revisar-texto).
"""
from __future__ import annotations

import io
import json
import re
import shutil
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import config
import i18n
from i18n import t

EMBUTIDOS = config.RAIZ / "plugins"
LIMITE_BAIXADO = 60 * 1024 * 1024
LIMITE_ARQUIVOS = 4000
_NOME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class ErroPlugin(Exception):
    pass


def instalados_dir() -> Path:
    return config.DADOS / "plugins"


def _slug(nome: str) -> str:
    s = re.sub(r"[^a-z0-9._-]+", "-", (nome or "").strip().lower()).strip("-")
    return s or "plugin"


def ler_manifesto(pasta: Path) -> dict:
    arq = Path(pasta) / ".claude-plugin" / "plugin.json"
    if not arq.is_file():
        raise ErroPlugin(t("Não é um plugin: falta o arquivo .claude-plugin/plugin.json."))
    try:
        dados = json.loads(arq.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        raise ErroPlugin(t("O plugin.json não é um JSON válido ({erro}).", erro=e)) from e
    if not isinstance(dados, dict) or not str(dados.get("name") or "").strip():
        raise ErroPlugin(t("O plugin.json precisa ter o campo \"name\"."))
    return dados


def _caminhos(pasta: Path, manifesto: dict, chave: str, padrao: str) -> list[Path]:
    """Pastas de uma parte do plugin: a padrão mais as que o manifesto indicar (sempre dentro do plugin)."""
    saida = [pasta / padrao]
    extra = manifesto.get(chave)
    if isinstance(extra, str):
        extra = [extra]
    if isinstance(extra, list):
        for c in extra:
            if isinstance(c, str) and c.startswith("./"):
                p = (pasta / c).resolve()
                if p.is_relative_to(pasta.resolve()) and p not in saida:
                    saida.append(p)
    return saida


def _frontmatter(texto: str) -> dict:
    import contexto_pasta
    return contexto_pasta._frontmatter(texto)


def analisar(pasta: Path) -> dict:
    """O que o plugin traz, para mostrar antes de instalar e para listar."""
    pasta = Path(pasta)
    m = ler_manifesto(pasta)
    nome = _slug(str(m["name"]))
    pt = i18n.guardado_pt(pasta)  # plugins do app vêm em inglês, com o português guardado ao lado
    info = {
        "nome": nome,
        "titulo": str(pt.get("displayName") or m.get("displayName") or m.get("title") or m["name"]),
        "versao": str(m.get("version") or ""),
        "descricao": str(pt.get("description") or m.get("description") or ""),
        "autor": (m.get("author") or {}).get("name", "") if isinstance(m.get("author"), dict) else str(m.get("author") or ""),
        "site": str(m.get("homepage") or m.get("repository") or "") if not isinstance(m.get("repository"), dict)
        else str(m["repository"].get("url") or ""),
        "skills": [], "agentes": [], "comandos": [], "fluxos": [], "avisos": [], "mcp_remotos": [],
        "pasta": str(pasta),
    }
    for base in _caminhos(pasta, m, "skills", "skills"):
        if base.is_dir():
            for d in sorted(base.iterdir()):
                arq = d / "SKILL.md"
                if arq.is_file():
                    fm = _frontmatter(arq.read_text(encoding="utf-8", errors="replace"))
                    sk = str(fm.get("name") or d.name)
                    info["skills"].append({"nome": sk, "descricao": str((pt.get("skills", {}).get(sk) or {}).get("description")
                                                                          or fm.get("description") or "")})
    for base in _caminhos(pasta, m, "agents", "agents"):
        if base.is_dir():
            for arq in sorted(base.glob("*.md")):
                fm = _frontmatter(arq.read_text(encoding="utf-8", errors="replace"))
                ag = str(fm.get("name") or arq.stem)
                info["agentes"].append({"nome": ag, "descricao": str((pt.get("agents", {}).get(ag) or {}).get("description")
                                                                       or fm.get("description") or ""),
                                        "modelo": str(fm.get("model") or "")})
    for base in _caminhos(pasta, m, "commands", "commands"):
        if base.is_dir():
            for arq in sorted(base.rglob("*.md")):
                fm = _frontmatter(arq.read_text(encoding="utf-8", errors="replace"))
                rel = arq.relative_to(base).with_suffix("").as_posix().replace("/", ":")
                info["comandos"].append({"nome": rel, "descricao": str((pt.get("commands", {}).get(rel) or {}).get("description")
                                                                        or fm.get("description") or "")})
    fl = pasta / "fluxos"
    if fl.is_dir():
        for arq in sorted(fl.glob("*.json")):
            try:
                d = json.loads(arq.read_text(encoding="utf-8"))
                info["fluxos"].append({"nome": d.get("nome") or arq.stem, "descricao": d.get("descricao", "")})
            except ValueError:
                info["avisos"].append(t("Modelo de fluxo inválido: {arquivo}", arquivo=arq.name))
    if (pasta / "hooks").exists() or m.get("hooks"):
        info["avisos"].append(t("Traz hooks (comandos que rodam sozinhos a cada evento). O Clave não usa hooks: essa parte fica desligada."))
    mcp_arq = pasta / ".mcp.json"
    mcp = m.get("mcpServers")
    if mcp_arq.is_file():
        try:
            mcp = json.loads(mcp_arq.read_text(encoding="utf-8"))
        except ValueError:
            mcp = None
    if isinstance(mcp, dict):
        mcp = mcp.get("mcpServers", mcp)
        for nome_srv, cfg_srv in (mcp or {}).items():
            if isinstance(cfg_srv, dict) and str(cfg_srv.get("url") or "").startswith("https://"):
                info["mcp_remotos"].append({"nome": nome_srv, "url": cfg_srv["url"]})
            else:
                info["avisos"].append(t("O conector \"{nome}\" roda no computador (MCP local); o Clave só usa conectores na internet, então ele fica de fora.", nome=nome_srv))
    if (pasta / ".lsp.json").exists() or m.get("lspServers"):
        info["avisos"].append(t("Traz servidores de linguagem (LSP), que o Clave não usa."))
    return info


# ---------------- lista e estado ----------------

def _estado() -> dict:
    return dict(config.carregar().get("plugins") or {})


def _pastas_de_plugin(base: Path) -> list[Path]:
    if not base.is_dir():
        return []
    return [d for d in sorted(base.iterdir()) if (d / ".claude-plugin" / "plugin.json").is_file()]


def listar() -> list[dict]:
    est = _estado()
    vistos: dict[str, dict] = {}
    for origem, base in (("instalado", instalados_dir()), ("embutido", EMBUTIDOS)):
        for d in _pastas_de_plugin(base):
            try:
                info = analisar(d)
            except ErroPlugin as e:
                vistos.setdefault(d.name, {"nome": d.name, "titulo": d.name, "erro": str(e), "origem": origem,
                                           "ligado": False, "pasta": str(d)})
                continue
            if info["nome"] in vistos:
                continue  # instalado com o mesmo nome substitui o embutido
            e = est.get(info["nome"]) or {}
            info["origem"] = origem
            info["fonte"] = e.get("fonte", "")
            info["ligado"] = bool(e.get("ligado", True))
            vistos[info["nome"]] = info
    return sorted(vistos.values(), key=lambda p: (p.get("origem") != "embutido", p["titulo"].lower()))


def ativos() -> list[dict]:
    return [p for p in listar() if p.get("ligado") and not p.get("erro")]


def ligar(nome: str, ligado: bool) -> None:
    est = _estado()
    e = dict(est.get(nome) or {})
    e["ligado"] = bool(ligado)
    est[nome] = e
    config.salvar({"plugins": est})


def partes(tipo: str) -> list[tuple[str, Path]]:
    """(nome do plugin, pasta) de cada parte dos plugins ligados: tipo = skills | agents | commands | fluxos."""
    saida = []
    for p in ativos():
        pasta = Path(p["pasta"])
        try:
            m = ler_manifesto(pasta)
        except ErroPlugin:
            continue
        if tipo == "fluxos":
            bases = [pasta / "fluxos"]
        else:
            bases = _caminhos(pasta, m, tipo, tipo)
        for b in bases:
            if b.is_dir():
                saida.append((p["nome"], b))
    return saida


# ---------------- instalar ----------------

def _copiar(origem: Path, destino: Path) -> None:
    tmp = destino.with_name(destino.name + ".novo")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(origem, tmp, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "node_modules"),
                    symlinks=False)
    shutil.rmtree(destino, ignore_errors=True)
    tmp.rename(destino)


def instalar_de_pasta(origem: Path, fonte: str = "") -> dict:
    origem = Path(origem)
    info = analisar(origem)
    destino = instalados_dir() / info["nome"]
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.resolve() != origem.resolve():
        _copiar(origem, destino)
    est = _estado()
    est[info["nome"]] = {"ligado": True, "fonte": fonte or str(origem), "instalado_em": time.time(),
                         "versao": info["versao"]}
    config.salvar({"plugins": est})
    return analisar(destino)


def remover(nome: str) -> None:
    destino = instalados_dir() / _slug(nome)
    if not destino.is_dir():
        raise ErroPlugin(t("Só dá para remover plugin instalado; os que vêm com o Clave dá para desligar."))
    shutil.rmtree(destino)
    est = _estado()
    est.pop(_slug(nome), None)
    config.salvar({"plugins": est})


# ---------------- GitHub ----------------

def _ref_github(texto: str) -> tuple[str, str, str]:
    """'dono/repo', 'dono/repo#v1', 'https://github.com/dono/repo/tree/main' -> (dono, repo, ref)."""
    txt = (texto or "").strip()
    ref = ""
    if "#" in txt:
        txt, ref = txt.split("#", 1)
    if txt.startswith(("http://", "https://")):
        u = urllib.parse.urlparse(txt)
        if u.netloc.lower() not in ("github.com", "www.github.com"):
            raise ErroPlugin(t("Só dá para instalar do GitHub (github.com/dono/repositório)."))
        partes_url = [p for p in u.path.split("/") if p]
        if len(partes_url) < 2:
            raise ErroPlugin(t("Endereço do GitHub incompleto."))
        dono, repo = partes_url[0], partes_url[1]
        if len(partes_url) >= 4 and partes_url[2] == "tree" and not ref:
            ref = "/".join(partes_url[3:])
    else:
        partes_txt = txt.split("/")
        if len(partes_txt) != 2:
            raise ErroPlugin(t("Escreva dono/repositório, por exemplo: anthropics/claude-plugins."))
        dono, repo = partes_txt
    repo = repo.removesuffix(".git")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", dono) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise ErroPlugin(t("Nome de repositório inválido."))
    if ref and not re.fullmatch(r"[A-Za-z0-9_./-]+", ref):
        raise ErroPlugin(t("Versão (ref) inválida."))
    return dono, repo, ref or "HEAD"


def _baixar_zip(dono: str, repo: str, ref: str) -> bytes:
    url = f"https://github.com/{dono}/{repo}/archive/{urllib.parse.quote(ref)}.zip"
    req = urllib.request.Request(url, headers={"User-Agent": f"Clave/{config.VERSAO}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            dados = r.read(LIMITE_BAIXADO + 1)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ErroPlugin(t("Repositório não encontrado (ou é privado).")) from e
        raise ErroPlugin(t("O GitHub respondeu {codigo}.", codigo=e.code)) from e
    except (urllib.error.URLError, OSError) as e:
        raise ErroPlugin(t("Sem conexão com o GitHub ({erro}).", erro=e)) from e
    if len(dados) > LIMITE_BAIXADO:
        raise ErroPlugin(t("O repositório é grande demais para um plugin (mais de 60 MB)."))
    return dados


def extrair_zip(dados: bytes, destino: Path) -> Path:
    """Extrai com cuidado (nada fora da pasta, sem atalhos, com limite de tamanho) e devolve a raiz do pacote."""
    destino.mkdir(parents=True, exist_ok=True)
    base = destino.resolve()
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        nomes = z.infolist()
        if len(nomes) > LIMITE_ARQUIVOS:
            raise ErroPlugin(t("O pacote tem arquivos demais para um plugin."))
        if sum(i.file_size for i in nomes) > LIMITE_BAIXADO * 3:
            raise ErroPlugin(t("O pacote descompactado é grande demais."))
        for i in nomes:
            alvo = (destino / i.filename).resolve()
            if not alvo.is_relative_to(base):
                raise ErroPlugin(t("O pacote tenta gravar fora da pasta; instalação cancelada."))
            if (i.external_attr >> 16) & 0o170000 == 0o120000:
                continue  # atalho (symlink): ignorado
            if i.is_dir():
                alvo.mkdir(parents=True, exist_ok=True)
            else:
                alvo.parent.mkdir(parents=True, exist_ok=True)
                with z.open(i) as src, open(alvo, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    filhos = [p for p in destino.iterdir()]
    return filhos[0] if len(filhos) == 1 and filhos[0].is_dir() else destino


def preparar_github(texto: str, _baixar=None) -> dict:
    """Baixa o repositório numa pasta temporária e diz o que dá para instalar (sem instalar nada ainda)."""
    dono, repo, ref = _ref_github(texto)
    baixar = _baixar or _baixar_zip
    pid = f"{_slug(dono)}-{_slug(repo)}-{int(time.time())}"
    tmp = instalados_dir() / ".baixando" / pid
    shutil.rmtree(tmp, ignore_errors=True)
    raiz = extrair_zip(baixar(dono, repo, ref), tmp)
    candidatos: list[dict] = []
    avisos: list[str] = []
    mkt = raiz / ".claude-plugin" / "marketplace.json"
    if mkt.is_file():
        try:
            dados = json.loads(mkt.read_text(encoding="utf-8-sig"))
        except ValueError as e:
            raise ErroPlugin(t("O marketplace.json não é um JSON válido ({erro}).", erro=e)) from e
        for ent in dados.get("plugins") or []:
            fonte = ent.get("source")
            if isinstance(fonte, str) and fonte.startswith("./"):
                p = (raiz / fonte).resolve()
                if p.is_relative_to(raiz.resolve()) and (p / ".claude-plugin" / "plugin.json").is_file():
                    candidatos.append({**analisar(p), "fonte": f"{dono}/{repo}#{ref}:{fonte}"})
                elif p.is_dir() and ent.get("name"):
                    # plugin sem plugin.json próprio: o marketplace descreve (strict: false)
                    (p / ".claude-plugin").mkdir(exist_ok=True)
                    (p / ".claude-plugin" / "plugin.json").write_text(json.dumps(
                        {"name": ent["name"], "description": ent.get("description", ""),
                         "version": ent.get("version", "")}), encoding="utf-8")
                    candidatos.append({**analisar(p), "fonte": f"{dono}/{repo}#{ref}:{fonte}"})
            elif isinstance(fonte, dict) and fonte.get("source") == "github" and fonte.get("repo"):
                avisos.append(t("\"{nome}\" mora em outro repositório ({repo}): instale por lá.", nome=ent.get("name"),
                                repo=fonte["repo"]))
            else:
                avisos.append(t("\"{nome}\" usa um tipo de origem que o Clave não instala.", nome=ent.get("name")))
    elif (raiz / ".claude-plugin" / "plugin.json").is_file():
        candidatos.append({**analisar(raiz), "fonte": f"{dono}/{repo}#{ref}"})
    else:
        shutil.rmtree(tmp, ignore_errors=True)
        raise ErroPlugin(t("Esse repositório não tem plugin do Claude Code (.claude-plugin/plugin.json) nem marketplace (.claude-plugin/marketplace.json)."))
    return {"id": pid, "repositorio": f"{dono}/{repo}", "ref": ref, "plugins": candidatos, "avisos": avisos}


def instalar_preparado(pid: str, nomes: list[str]) -> list[dict]:
    if not re.fullmatch(r"[a-z0-9._-]+", pid or ""):
        raise ErroPlugin(t("Identificador inválido."))
    tmp = instalados_dir() / ".baixando" / pid
    if not tmp.is_dir():
        raise ErroPlugin(t("O download expirou; procure o repositório de novo."))
    feitos = []
    try:
        for d in [p for p in tmp.rglob("plugin.json") if p.parent.name == ".claude-plugin"]:
            pasta = d.parent.parent
            info = analisar(pasta)
            if info["nome"] in nomes:
                feitos.append(instalar_de_pasta(pasta, fonte=f"github:{pid}"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return feitos


def limpar_baixados(idade_s: int = 3600) -> None:
    base = instalados_dir() / ".baixando"
    if not base.is_dir():
        return
    for d in base.iterdir():
        try:
            if time.time() - d.stat().st_mtime > idade_s:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


def nome_valido(nome: str) -> bool:
    return bool(_NOME.match(nome or ""))


def temporaria() -> Path:
    return Path(tempfile.mkdtemp(prefix="clave-plugin-"))
