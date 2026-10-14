"""Os tutoriais (arquivos .md da pasta tutoriais/, com um cabeçalho de metadados)."""
from __future__ import annotations

import re

from config import TUTORIAIS

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def _ler(arq):
    texto = arq.read_text(encoding="utf-8")
    meta = {}
    m = _FRONT.match(texto)
    if m:
        for linha in m.group(1).splitlines():
            if ":" in linha:
                k, v = linha.split(":", 1)
                meta[k.strip()] = v.strip()
        texto = texto[m.end():]
    return meta, texto


def listar() -> list[dict]:
    itens = []
    if not TUTORIAIS.is_dir():
        return itens
    for arq in sorted(TUTORIAIS.glob("*.md")):
        meta, _ = _ler(arq)
        itens.append({
            "slug": arq.stem,
            "titulo": meta.get("titulo", arq.stem),
            "trilha": meta.get("trilha", "Outros"),
            "ordem": int(meta.get("ordem", "99") or 99),
            "duracao": meta.get("duracao", ""),
            "resumo": meta.get("resumo", ""),
        })
    itens.sort(key=lambda t: (t["ordem"], t["slug"]))
    return itens


def ancora(texto: str) -> str:
    """O mesmo id que a interface dá aos títulos do glossário (sem acento, minúsculo, com hífen)."""
    import unicodedata
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"\([^)]*\)", "", t)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def termos_glossario() -> list[tuple[str, str]]:
    """(termo, âncora) de cada título '## ' do glossário."""
    arq = TUTORIAIS / "glossario.md"
    if not arq.is_file():
        return []
    _, texto = _ler(arq)
    saida = []
    for linha in texto.splitlines():
        if linha.startswith("## "):
            termo = linha[3:].strip()
            saida.append((termo, ancora(termo)))
    return saida


def guia_para_o_claude() -> str:
    """Texto que entra no prompt de sistema para o Claude saber indicar as lições."""
    licoes = listar()
    if not licoes:
        return ""
    linhas = [
        "O Clave tem lições para quem está começando, na área Aprender. Quando a pessoa mostrar que não conhece um "
        "termo (mesmo escrito errado ou de um jeito estranho, como \"quem é JASON\" querendo dizer JSON, ou \"guiti "
        "rabi\" querendo dizer GitHub) ou perguntar como usar o próprio app, explique em linguagem bem simples, em "
        "poucas frases, e indique a lição com um link Markdown exatamente no formato abaixo (ele abre dentro do app). "
        "Se o termo foi escrito errado, diga com gentileza o nome certo. Não indique lição para quem claramente já "
        "domina o assunto, e no máximo um ou dois links por resposta.",
        "Lições:",
    ]
    for t in licoes:
        linhas.append(f"- [{t['titulo']}](#/aprender/{t['slug']})")
    termos = termos_glossario()
    if termos:
        linhas.append("Termos do glossário (link direto para cada um): " + ", ".join(
            f"[{termo}](#/aprender/glossario/{anc})" for termo, anc in termos))
    return "\n".join(linhas)


def ler(slug: str) -> dict | None:
    if not re.fullmatch(r"[a-z0-9-]+", slug or ""):
        return None
    arq = TUTORIAIS / f"{slug}.md"
    if not arq.is_file():
        return None
    meta, texto = _ler(arq)
    return {"slug": slug, "titulo": meta.get("titulo", slug), "trilha": meta.get("trilha", ""),
            "duracao": meta.get("duracao", ""), "texto": texto}
