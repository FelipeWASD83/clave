#!/usr/bin/env python
"""Procura chamadas de funcao inventadas em codigo GML.

Cruza toda chamada `nome(...)` encontrada no codigo com:
  1. o indice do manual oficial (referencias/indice-manual-<canal>.txt);
  2. as funcoes/metodos definidos dentro do proprio projeto;
  3. as palavras-chave da linguagem.

O que sobrar e suspeito de ser nome inventado ou de versao antiga do GameMaker.
Isto NAO substitui compilar: nao valida assinatura, quantidade de argumentos,
nem se a funcao faz o que voce acha que faz. Serve pra pegar o erro mais comum,
que e citar funcao que nao existe.

Uso:
    python checar-gml.py <arquivo.gml | pasta> [--canal monthly|lts|beta]
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

# Chamadas dinamicas e coisas que parecem chamada mas nao sao.
IGNORAR = {"array", "string", "struct", "method"}


def variantes(nome):
    """GML aceita as duas grafias (color/colour); o manual so documenta a britanica."""
    yield nome
    if "color" in nome:
        yield nome.replace("color", "colour")
    if "colour" in nome:
        yield nome.replace("colour", "color")


def carregar_nomes_manual(canal):
    caminho = os.path.join(REFS, "indice-manual-%s.txt" % canal)
    if not os.path.exists(caminho):
        print("indice ausente: %s" % caminho)
        print("rode antes: python docgml.py atualizar --canal %s" % canal)
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
        print("nenhum .gml em %s" % a.alvo)
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
        # variaveis locais recebendo metodo tambem contam como definidas
        locais = set(m.lower() for m in
                     re.findall(r"\bvar\s+([A-Za-z_]\w*)\s*=\s*function\b", texto))
        for linha_num, linha in enumerate(texto.split("\n"), 1):
            for m in re.finditer(r"(\.?)\b([A-Za-z_]\w*)\s*\(", linha):
                if m.group(1) == ".":       # metodo de struct/instancia
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
        print("OK: %d arquivo(s), nenhuma chamada fora do manual e fora do projeto."
              % len(arquivos))
        print("Lembrete: isto nao valida assinatura nem comportamento.")
        return 0

    vistos = set()
    print("SUSPEITAS (%d):\n" % len(suspeitas))
    for caminho, linha_num, nome, linha in suspeitas:
        rel = os.path.relpath(caminho, os.path.dirname(a.alvo) or ".")
        print("%s:%d  %s()" % (rel, linha_num, nome))
        print("    %s" % linha[:120])
        vistos.add(nome)
    print("\nnomes distintos: %s" % ", ".join(sorted(vistos)))
    print("Confira cada um com: python docgml.py buscar <nome>")
    return 1


if __name__ == "__main__":
    sys.exit(main())
