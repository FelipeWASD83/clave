"""Os tutoriais (arquivos .md da pasta tutoriais/, com um cabeçalho de metadados).

As lições em inglês moram em tutoriais/en/, com o mesmo nome de arquivo (o slug é o mesmo nos dois idiomas).
`lingua` vazio segue o idioma escolhido em Configurações; lição que ainda não tem a versão em inglês cai na
em português.
"""
from __future__ import annotations

import re
from pathlib import Path

import i18n
from config import TUTORIAIS
from i18n import t

_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
_ANCORA_FIXA = re.compile(r"\s*\{#([\w-]+)\}\s*$")  # "## AI (artificial intelligence) {#ia}": âncora igual à do português


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


def _arquivo(slug: str, lingua: str | None = None) -> Path:
    """O .md da lição no idioma pedido (o português quando falta a tradução)."""
    if (lingua or i18n.idioma()) == "en":
        en = TUTORIAIS / "en" / f"{slug}.md"
        if en.is_file():
            return en
    return TUTORIAIS / f"{slug}.md"


def listar(lingua: str | None = None) -> list[dict]:
    itens = []
    if not TUTORIAIS.is_dir():
        return itens
    for base in sorted(TUTORIAIS.glob("*.md")):
        arq = _arquivo(base.stem, lingua)
        meta, _ = _ler(arq)
        itens.append({
            "slug": base.stem,
            "titulo": meta.get("titulo", base.stem),
            "trilha": meta["trilha"] if "trilha" in meta else t("Outros"),
            "ordem": int(meta.get("ordem", "99") or 99),
            "duracao": meta.get("duracao", ""),
            "resumo": meta.get("resumo", ""),
            "video": meta.get("video", ""),
        })
    itens.sort(key=lambda li: (li["ordem"], li["slug"]))
    return itens


def ancora(texto: str) -> str:
    """O mesmo id que a interface dá aos títulos do glossário (sem acento, minúsculo, com hífen)."""
    import unicodedata
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"\([^)]*\)", "", s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def termos_glossario(lingua: str | None = None) -> list[tuple[str, str]]:
    """(termo, âncora) de cada título '## ' do glossário. Um título que termina em {#id} usa esse id como âncora
    (é assim que o glossário em inglês mantém os mesmos links do português)."""
    arq = _arquivo("glossario", lingua)
    if not arq.is_file():
        return []
    _, texto = _ler(arq)
    saida = []
    for linha in texto.splitlines():
        if linha.startswith("## "):
            termo = linha[3:].strip()
            m = _ANCORA_FIXA.search(termo)
            if m:
                saida.append((termo[:m.start()].strip(), m.group(1)))
            else:
                saida.append((termo, ancora(termo)))
    return saida


def guia_para_o_claude() -> str:
    """Texto que entra no prompt de sistema para o Claude saber indicar as lições."""
    licoes = listar()
    if not licoes:
        return ""
    linhas = [
        " ".join([
            t("O Clave tem lições para quem está começando, na área Aprender."),
            t("Quando a pessoa mostrar que não conhece um termo (mesmo escrito errado ou de um jeito estranho, como \"quem é JASON\" querendo dizer JSON, ou \"guiti rabi\" querendo dizer GitHub) ou perguntar como usar o próprio app, explique em linguagem bem simples, em poucas frases, e indique a lição com um link Markdown exatamente no formato abaixo (ele abre dentro do app)."),
            t("Se o termo foi escrito errado, diga com gentileza o nome certo."),
            t("Não indique lição para quem claramente já domina o assunto, e no máximo um ou dois links por resposta."),
        ]),
        t("Lições:"),
    ]
    for li in licoes:
        linhas.append(f"- [{li['titulo']}](#/aprender/{li['slug']})")
    termos = termos_glossario()
    if termos:
        linhas.append(t("Termos do glossário (link direto para cada um): {termos}", termos=", ".join(
            f"[{termo}](#/aprender/glossario/{anc})" for termo, anc in termos)))
    return "\n".join(linhas)


def ler(slug: str, lingua: str | None = None) -> dict | None:
    if not re.fullmatch(r"[a-z0-9-]+", slug or ""):
        return None
    arq = _arquivo(slug, lingua)
    if not arq.is_file():
        return None
    meta, texto = _ler(arq)
    return {"slug": slug, "titulo": meta.get("titulo", slug), "trilha": meta.get("trilha", ""),
            "duracao": meta.get("duracao", ""), "video": meta.get("video", ""), "texto": texto}
