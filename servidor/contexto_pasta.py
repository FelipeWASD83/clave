"""O que o modo Code lê da pasta de trabalho: CLAUDE.md (ou AGENTS.md) e skills.

Segue o mesmo esquema do Claude Code: as instruções valem da pasta de trabalho
para cima (a pasta-mãe pode ter as regras gerais), e as skills ficam em
.claude/skills/<nome>/SKILL.md, nessas mesmas pastas e na pasta pessoal.
"""
from __future__ import annotations

import re
from pathlib import Path

LIMITE_INSTRUCOES = 120_000  # caracteres somando todos os arquivos
SKILLS_DO_APP = Path(__file__).resolve().parent.parent / "skills"


def _ancestrais(pasta: Path) -> list[Path]:
    pasta = pasta.resolve()
    lista = [pasta, *pasta.parents]
    lista.reverse()  # da raiz do disco até a pasta de trabalho
    return lista


def instrucoes(pasta: str | Path) -> list[dict]:
    """Arquivos de instrução que valem para a pasta, do mais geral para o mais específico."""
    achados: list[dict] = []
    pessoal = Path.home() / ".claude" / "CLAUDE.md"
    if pessoal.is_file():
        achados.append({"caminho": str(pessoal), "escopo": "pessoal"})
    for d in _ancestrais(Path(pasta)):
        claude = d / "CLAUDE.md"
        agents = d / "AGENTS.md"
        if claude.is_file():
            achados.append({"caminho": str(claude), "escopo": "pasta"})
        elif agents.is_file():
            achados.append({"caminho": str(agents), "escopo": "pasta"})
    total = 0
    for a in achados:
        try:
            texto = Path(a["caminho"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            texto = ""
        if total + len(texto) > LIMITE_INSTRUCOES:
            sobra = max(0, LIMITE_INSTRUCOES - total)
            texto = texto[:sobra] + "\n\n[... arquivo cortado: as instruções passaram do limite de tamanho ...]"
        total += len(texto)
        a["texto"] = texto
    return achados


_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _frontmatter(texto: str) -> dict:
    m = _FRONT.match(texto)
    if not m:
        return {}
    dados: dict = {}
    chave_atual = None
    for linha in m.group(1).splitlines():
        if not linha.strip():
            continue
        if linha[:1] in (" ", "\t") and chave_atual:
            dados[chave_atual] = (str(dados[chave_atual]) + " " + linha.strip()).strip()
            continue
        if ":" in linha:
            k, v = linha.split(":", 1)
            chave_atual = k.strip()
            v = v.strip()
            if v.startswith(("'", '"')) and v.endswith(v[0]) and len(v) >= 2:
                v = v[1:-1]
            if v.lower() in ("true", "false"):
                dados[chave_atual] = v.lower() == "true"
            else:
                dados[chave_atual] = v
    return dados


def skills(pasta: str | Path | None) -> list[dict]:
    """Skills disponíveis: da pasta de trabalho para cima, depois as pessoais. A mais próxima vence."""
    bases: list[Path] = []
    if pasta:
        for d in reversed(_ancestrais(Path(pasta))):
            bases.append(d / ".claude" / "skills")
    bases.append(Path.home() / ".claude" / "skills")
    bases.append(SKILLS_DO_APP)  # as que vêm com o Clave (ver-video), as mais fracas: perdem para as da pasta
    vistas: dict[str, dict] = {}
    for base in bases:
        if not base.is_dir():
            continue
        try:
            itens = sorted(base.iterdir())
        except OSError:
            continue
        for d in itens:
            arq = d / "SKILL.md"
            if not arq.is_file():
                continue
            try:
                texto = arq.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            fm = _frontmatter(texto)
            nome = str(fm.get("name") or d.name).strip()
            if nome in vistas:
                continue
            vistas[nome] = {
                "nome": nome,
                "descricao": str(fm.get("description") or "").strip(),
                "manual": bool(fm.get("disable-model-invocation")),
                "caminho": str(arq),
                "pasta": str(d),
            }
    return sorted(vistas.values(), key=lambda s: s["nome"])


def conteudo_skill(lista: list[dict], nome: str) -> dict | None:
    for s in lista:
        if s["nome"] == nome:
            try:
                texto = Path(s["caminho"]).read_text(encoding="utf-8", errors="replace")
            except OSError:
                return None
            corpo = _FRONT.sub("", texto, count=1)
            return {**s, "texto": corpo}
    return None
