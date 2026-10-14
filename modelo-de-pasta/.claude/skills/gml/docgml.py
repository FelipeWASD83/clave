#!/usr/bin/env python
"""Consulta o manual oficial do GameMaker (manual.gamemaker.io) pela linha de comando.

Existe porque o WebFetch do Claude leva 403 nesse domínio, mas requisição HTTP
normal (curl/urllib) passa. E porque conferir se uma funcao existe no indice
local e instantaneo, enquanto pesquisar na web e lento e sujeito a chute.

Uso:
    python docgml.py buscar <termo> [--canal monthly|lts|beta]
    python docgml.py ver <funcao_ou_caminho> [--canal ...] [--completo]
    python docgml.py atualizar [--canal ...]

Exemplos:
    python docgml.py buscar instance_create
    python docgml.py ver array_foreach
    python docgml.py ver GameMaker_Language/GML_Overview/Structs.htm --completo
"""

import argparse
import html
import os
import re
import sys
import urllib.request

BASE = "https://manual.gamemaker.io"
CANAIS = ("monthly", "lts", "beta")
AQUI = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(AQUI, "referencias")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) docgml"


def caminho_indice(canal):
    return os.path.join(REFS, "indice-manual-%s.txt" % canal)


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def carregar_indice(canal):
    caminho = caminho_indice(canal)
    if not os.path.exists(caminho):
        atualizar(canal)
    with open(caminho, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def atualizar(canal):
    xml = baixar("%s/%s/en/sitemap.xml" % (BASE, canal))
    locs = re.findall(r"<loc>(.*?)</loc>", xml)
    locs = sorted(set(html.unescape(l).strip() for l in locs))
    os.makedirs(REFS, exist_ok=True)
    with open(caminho_indice(canal), "w", encoding="utf-8") as f:
        f.write("\n".join(locs) + "\n")
    print("indice %s atualizado: %d paginas" % (canal, len(locs)))
    return locs


def limpar_html(bruto):
    t = re.sub(r"(?is)<(script|style|head).*?</\1>", " ", bruto)
    t = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</h[1-6]>|</li>|</tr>|</table>", "\n", t)
    t = re.sub(r"(?is)</t[dh]>", " | ", t)
    t = re.sub(r"(?s)<[^>]*>", " ", t)
    t = html.unescape(t)
    t = t.replace("�", "").replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    linhas = [l.strip() for l in t.split("\n")]
    linhas = [l for l in linhas if l and l != "-->" and l != "|"]
    # o cabecalho repete o titulo e o link "Click here to see this page in full context"
    linhas = [l for l in linhas if "Click here to see this page" not in l]
    saida, anterior = [], None
    for l in linhas:
        if l != anterior:
            saida.append(l)
        anterior = l
    return "\n".join(saida)


def buscar(termo, canal, silencioso=False):
    indice = carregar_indice(canal)
    padrao = re.compile(re.escape(termo), re.I)
    achados = [p for p in indice if padrao.search(p)]
    if not silencioso:
        if not achados:
            print("nada no indice %s para '%s'." % (canal, termo))
            print("ATENCAO: nao achar no indice nao prova que a funcao nao existe,")
            print("mas e motivo forte pra nao usar sem confirmar de outra forma.")
        else:
            for p in achados:
                print("%-70s %s/%s/en/%s" % (p, BASE, canal, p))
            print("\n%d resultado(s)." % len(achados))
    return achados


def resolver(alvo, canal):
    if alvo.endswith(".htm"):
        return alvo
    achados = buscar(alvo, canal, silencioso=True)
    if not achados:
        return None
    exatos = [p for p in achados if os.path.basename(p).lower() == alvo.lower() + ".htm"]
    return exatos[0] if exatos else achados[0]


def ver(alvo, canal, completo):
    caminho = resolver(alvo, canal)
    if caminho is None:
        print("nao encontrei '%s' no indice %s. Rode: python docgml.py buscar %s"
              % (alvo, canal, alvo))
        return 1
    url = "%s/%s/en/%s" % (BASE, canal, caminho)
    texto = limpar_html(baixar(url))
    print(url + "\n" + "-" * len(url))
    if completo:
        print(texto)
    else:
        linhas = texto.split("\n")
        print("\n".join(linhas[:120]))
        if len(linhas) > 120:
            print("\n[... %d linhas cortadas, use --completo ...]" % (len(linhas) - 120))
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("comando", choices=("buscar", "ver", "atualizar"))
    p.add_argument("alvo", nargs="?", default="")
    p.add_argument("--canal", default="monthly", choices=CANAIS)
    p.add_argument("--completo", action="store_true")
    a = p.parse_args()

    if a.comando == "atualizar":
        atualizar(a.canal)
        return 0
    if not a.alvo:
        p.error("comando '%s' precisa de um alvo" % a.comando)
    if a.comando == "buscar":
        return 0 if buscar(a.alvo, a.canal) else 0
    return ver(a.alvo, a.canal, a.completo)


if __name__ == "__main__":
    sys.exit(main())
