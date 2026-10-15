#!/usr/bin/env python
"""Looks for invented function calls in GML code.

It checks every call `name(...)` found in the code against:
  1. the official manual's index (referencias/indice-manual-<channel>.txt);
  2. the functions/methods defined inside the project itself;
  3. the language keywords.

Whatever is left is suspected of being an invented name or one from an old
version of GameMaker. This does NOT replace compiling: it doesn't validate the
signature, the number of arguments, or whether the function does what you
think it does. It is there to catch the most common mistake, which is citing a
function that doesn't exist.

Usage (--canal = channel):
    python checar-gml.py <file.gml | folder> [--canal monthly|lts|beta]
"""

import argparse
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(AQUI, "referencias")

PALAVRAS = {
    "if", "else", "while", "for", "do", "until", "repeat", "switch", "case",
    "default", "break", "continue", "return", "exit", "with", "var", "globalvar",
    "global", "static", "function", "constructor", "new", "delete", "try",
    "catch", "finally", "throw", "begin", "end", "then", "and", "or", "not",
    "xor", "div", "mod", "self", "other", "all", "noone", "true", "false",
    "undefined", "enum", "macro", "region", "endregion", "argument",
}

# Dynamic calls and things that look like a call but are not.
IGNORAR = {"array", "string", "struct", "method"}


def variantes(nome):
    """GML accepts both spellings (color/colour); the manual only documents the British one."""
    yield nome
    if "color" in nome:
        yield nome.replace("color", "colour")
    if "colour" in nome:
        yield nome.replace("colour", "color")


def carregar_nomes_manual(canal):
    caminho = os.path.join(REFS, "indice-manual-%s.txt" % canal)
    if not os.path.exists(caminho):
        print("index missing: %s" % caminho)
        print("run this first: python docgml.py atualizar --canal %s" % canal)
        sys.exit(2)
    nomes = set()
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            base = os.path.basename(linha.strip())
            if base.endswith(".htm"):
                nomes.add(base[:-4].lower())
    return nomes


def arquivos_gml(alvo):
    if os.path.isfile(alvo):
        return [alvo]
    encontrados = []
    for raiz, _, arqs in os.walk(alvo):
        for a in arqs:
            if a.lower().endswith(".gml"):
                encontrados.append(os.path.join(raiz, a))
    return encontrados


def tirar_comentarios_e_strings(codigo):
    codigo = re.sub(r"/\*.*?\*/", " ", codigo, flags=re.S)
    codigo = re.sub(r"//[^\n]*", " ", codigo)
    codigo = re.sub(r'"(?:[^"\\]|\\.)*"', '""', codigo)
    return codigo


def definidos_no_projeto(textos):
    nomes = set()
    for t in textos:
        nomes |= set(m.lower() for m in re.findall(r"\bfunction\s+([A-Za-z_]\w*)", t))
        nomes |= set(m.lower() for m in
                     re.findall(r"\b([A-Za-z_]\w*)\s*=\s*function\b", t))
        nomes |= set(m.lower() for m in
                     re.findall(r"\b([A-Za-z_]\w*)\s*:\s*function\b", t))
        nomes |= set(m.lower() for m in re.findall(r"#macro\s+([A-Za-z_]\w*)", t))
        nomes |= set(m.lower() for m in re.findall(r"\benum\s+([A-Za-z_]\w*)", t))
    return nomes


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("alvo")
    p.add_argument("--canal", default="monthly", choices=("monthly", "lts", "beta"))
    a = p.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    arquivos = arquivos_gml(a.alvo)
    if not arquivos:
        print("no .gml in %s" % a.alvo)
        return 1

    manual = carregar_nomes_manual(a.canal)
    brutos = {}
    for caminho in arquivos:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            brutos[caminho] = f.read()

    limpos = {c: tirar_comentarios_e_strings(t) for c, t in brutos.items()}
    proprios = definidos_no_projeto(limpos.values())

    suspeitas = []
    for caminho, texto in limpos.items():
        # local variables receiving a method also count as defined
        locais = set(m.lower() for m in
                     re.findall(r"\bvar\s+([A-Za-z_]\w*)\s*=\s*function\b", texto))
        for linha_num, linha in enumerate(texto.split("\n"), 1):
            for m in re.finditer(r"(\.?)\b([A-Za-z_]\w*)\s*\(", linha):
                if m.group(1) == ".":       # method of a struct/instance
                    continue
                nome = m.group(2)
                baixo = nome.lower()
                if baixo in PALAVRAS or baixo in IGNORAR:
                    continue
                conhecido = any(v in manual or v in proprios or v in locais
                                for v in variantes(baixo))
                if conhecido:
                    continue
                suspeitas.append((caminho, linha_num, nome, linha.strip()))

    if not suspeitas:
        print("OK: %d file(s), no call outside the manual and outside the project."
              % len(arquivos))
        print("Reminder: this does not validate signatures or behavior.")
        return 0

    vistos = set()
    print("SUSPECTS (%d):\n" % len(suspeitas))
    for caminho, linha_num, nome, linha in suspeitas:
        rel = os.path.relpath(caminho, os.path.dirname(a.alvo) or ".")
        print("%s:%d  %s()" % (rel, linha_num, nome))
        print("    %s" % linha[:120])
        vistos.add(nome)
    print("\ndistinct names: %s" % ", ".join(sorted(vistos)))
    print("Check each one with: python docgml.py buscar <name>")
    return 1


if __name__ == "__main__":
    sys.exit(main())
