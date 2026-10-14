"""Confere se todo link #/aprender/... (nas lições e na interface) aponta para uma lição ou termo que existe."""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "servidor"))

import tutoriais  # noqa: E402


def links() -> list[tuple[str, str]]:
    achados = []
    for arq in list((RAIZ / "tutoriais").glob("*.md")) + list((RAIZ / "app" / "js").glob("*.js")):
        texto = arq.read_text(encoding="utf-8")
        for m in re.finditer(r"#/aprender/([a-z0-9-]+)(?:/([a-z0-9-]+))?", texto):
            achados.append((arq.name, m.group(0)))
    return achados


def quebrados() -> list[str]:
    slugs = {t["slug"] for t in tutoriais.listar()}
    termos = {anc for _, anc in tutoriais.termos_glossario()}
    erros = []
    for arq, link in links():
        partes = link.split("/")
        slug = partes[2]
        if slug not in slugs:
            erros.append(f"{arq}: {link} (lição não existe)")
        elif len(partes) > 3 and slug == "glossario" and partes[3] not in termos:
            erros.append(f"{arq}: {link} (termo não existe no glossário)")
    return erros


if __name__ == "__main__":
    erros = quebrados()
    print("\n".join(erros) if erros else f"ok: {len(links())} links conferidos")
    sys.exit(1 if erros else 0)
