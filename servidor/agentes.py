"""Agentes (subagentes) no formato do Claude Code: um .md com cabeçalho e as instruções no corpo.

    ---
    name: revisor
    description: Revisa o que foi feito e aponta problemas
    tools: Read, Grep, Glob
    model: opus
    effort: high
    ---
    Você é um revisor...

De onde vêm, do que vale mais para o que vale menos: a pasta de trabalho (.claude/agents),
os pessoais (~/.claude/agents), os dos plugins ligados e os que vêm com o Clave (<app>/agentes).
Os fluxos usam os agentes para rodar cada etapa.
"""
from __future__ import annotations

import re
from pathlib import Path

import config
import contexto_pasta
import i18n
from i18n import t

EMBUTIDOS = config.RAIZ / "agentes"
ALIAS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5",
         "fable": "claude-fable-5-1"}
NOME_MODELO = {v: k for k, v in ALIAS.items()}
# ferramentas do Claude Code -> o que a etapa pode fazer no Clave
CAPACIDADE = {"read": "ler", "glob": "ler", "grep": "ler", "ls": "ler",
              "edit": "editar", "write": "editar", "multiedit": "editar", "notebookedit": "editar",
              "bash": "comandos", "powershell": "comandos",
              "webfetch": "web", "websearch": "web"}
TODAS = ["ler", "editar", "comandos", "web"]
_NOME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _lista(valor) -> list[str]:
    if isinstance(valor, list):
        return [str(v).strip() for v in valor if str(v).strip()]
    return [x for x in re.split(r"[,\s]+", str(valor or "")) if x and x != "-"]


def capacidades(tools, disallowed=None) -> list[str]:
    """`tools: Read, Grep` -> ['ler']. Sem `tools`, o agente pode tudo (como no Claude Code)."""
    nomes = _lista(tools)
    if not nomes:
        pode = list(TODAS)
    else:
        pode = []
        for n in nomes:
            c = CAPACIDADE.get(re.sub(r"\(.*$", "", n).lower())
            if c and c not in pode:
                pode.append(c)
    for n in _lista(disallowed):
        c = CAPACIDADE.get(re.sub(r"\(.*$", "", n).lower())
        if c in pode:
            pode.remove(c)
    return [c for c in TODAS if c in pode]


def ferramentas_de(pode: list[str]) -> str:
    mapa = {"ler": "Read, Glob, Grep", "editar": "Edit, Write", "comandos": "Bash", "web": "WebFetch, WebSearch"}
    return ", ".join(mapa[c] for c in TODAS if c in pode)


def ler_arquivo(arq: Path, origem: str, prefixo: str = "") -> dict | None:
    try:
        texto = arq.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    fm = contexto_pasta._frontmatter(texto)
    corpo = contexto_pasta._FRONT.sub("", texto, count=1).strip()
    nome = str(fm.get("name") or arq.stem).strip()
    if not nome:
        return None
    descricao = str(fm.get("description") or "").strip()
    if origem == "clave":  # agentes do app: a descrição em português guardada em agentes/i18n/pt-BR.json
        descricao = (i18n.guardado_pt(arq.parent).get(nome) or {}).get("description") or descricao
    elif origem.startswith("plugin:"):
        descricao = (i18n.guardado_pt(arq.parent.parent).get("agents", {}).get(nome) or {}).get("description") or descricao
    return {
        "nome": f"{prefixo}:{nome}" if prefixo else nome,
        "nome_base": nome,
        "descricao": descricao,
        "modelo": str(fm.get("model") or "inherit").strip(),
        "esforco": str(fm.get("effort") or "").strip(),
        "pode": capacidades(fm.get("tools"), fm.get("disallowedTools")),
        "cor": str(fm.get("color") or "").strip(),
        "instrucoes": corpo,
        "origem": origem,
        "caminho": str(arq),
        "editavel": origem in ("pasta", "pessoal"),
    }


def _bases(pasta: str | Path | None) -> list[tuple[str, str, Path]]:
    bases = []
    if pasta:
        bases.append(("pasta", "", Path(pasta) / ".claude" / "agents"))
    bases.append(("pessoal", "", Path.home() / ".claude" / "agents"))
    import plugins
    for nome_plugin, d in plugins.partes("agents"):
        bases.append((f"plugin:{nome_plugin}", nome_plugin, d))
    bases.append(("clave", "", EMBUTIDOS))
    return bases


def listar(pasta: str | Path | None = None) -> list[dict]:
    vistos: dict[str, dict] = {}
    base_vista: set = set()
    for origem, prefixo, base in _bases(pasta):
        if not base.is_dir():
            continue
        for arq in sorted(base.glob("*.md")):
            a = ler_arquivo(arq, origem, prefixo)
            if not a or a["nome"] in vistos:
                continue
            if prefixo and a["nome_base"] in base_vista:
                continue  # um agente da pasta ou pessoal com o mesmo nome vale mais que o do plugin
            vistos[a["nome"]] = a
            if not prefixo:
                base_vista.add(a["nome_base"])
    return sorted(vistos.values(), key=lambda a: ({"pasta": 0, "pessoal": 1, "clave": 3}.get(a["origem"], 2), a["nome"]))


def pegar(nome: str, pasta: str | Path | None = None) -> dict | None:
    nome = (nome or "").strip()
    for a in listar(pasta):
        if a["nome"] == nome or a["nome_base"] == nome:
            return a
    return None


def resolver_modelo(valor: str, padrao: str) -> str:
    v = (valor or "").strip().lower()
    if not v or v == "inherit":
        return padrao
    return ALIAS.get(v, valor.strip())


def salvar(dados: dict, onde: str = "pessoal", pasta: str | Path | None = None) -> dict:
    nome = str(dados.get("nome") or "").strip().lower()
    if not _NOME.match(nome):
        raise ValueError(t("Nome do agente: só letras minúsculas, números e hífen (ex.: revisor-de-texto)."))
    if onde == "pasta":
        if not pasta:
            raise ValueError(t("Escolha a pasta onde o agente vai morar."))
        base = Path(pasta) / ".claude" / "agents"
    else:
        base = Path.home() / ".claude" / "agents"
    pode = [c for c in TODAS if c in (dados.get("pode") or [])] or ["ler"]
    modelo = str(dados.get("modelo") or "inherit").strip()
    linhas = ["---", f"name: {nome}", f"description: {_uma_linha(dados.get('descricao'))}",
              f"tools: {ferramentas_de(pode)}", f"model: {NOME_MODELO.get(modelo, modelo)}"]
    if dados.get("esforco"):
        linhas.append(f"effort: {dados['esforco']}")
    linhas += ["---", "", str(dados.get("instrucoes") or "").strip(), ""]
    base.mkdir(parents=True, exist_ok=True)
    arq = base / f"{nome}.md"
    arq.write_text("\n".join(linhas), encoding="utf-8")
    return ler_arquivo(arq, onde)


def apagar(caminho: str, pasta: str | Path | None = None) -> None:
    p = Path(caminho).resolve()
    permitidas = [(Path.home() / ".claude" / "agents").resolve()]
    if pasta:
        permitidas.append((Path(pasta) / ".claude" / "agents").resolve())
    if p.suffix != ".md" or not any(p.parent == b for b in permitidas):
        raise ValueError(t("Só dá para apagar agente pessoal ou da pasta."))
    p.unlink()


def _uma_linha(texto) -> str:
    return " ".join(str(texto or "").split())[:300]
