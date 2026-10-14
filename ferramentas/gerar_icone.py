"""Gera app/img/icone.png e app/img/icone.ico a partir do icone.svg, desenhando com o Edge sem janela.

Só precisa rodar de novo quando o desenho do ícone mudar.
"""
from __future__ import annotations

import os
import struct
import subprocess
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SVG = RAIZ / "app" / "img" / "icone.svg"
TAMANHOS = [16, 24, 32, 48, 64, 128, 256]


def edge() -> str:
    for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        p = Path(base or "", "Microsoft", "Edge", "Application", "msedge.exe")
        if p.is_file():
            return str(p)
    raise SystemExit("Edge não encontrado.")


def png(tamanho: int, pasta: Path) -> bytes:
    html = pasta / f"icone-{tamanho}.html"
    html.write_text(
        "<!doctype html><meta charset=utf-8><style>html,body{margin:0;background:transparent}"
        f"svg{{display:block;width:{tamanho}px;height:{tamanho}px}}</style>" + SVG.read_text(encoding="utf-8"),
        encoding="utf-8")
    saida = pasta / f"icone-{tamanho}.png"
    subprocess.run([edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={tamanho},{tamanho}",
                    "--default-background-color=00000000", f"--screenshot={saida}", html.as_uri()],
                   check=True, capture_output=True, timeout=60)
    return saida.read_bytes()


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        imagens = [(t, png(t, Path(tmp))) for t in TAMANHOS]
    (RAIZ / "app" / "img" / "icone.png").write_bytes(dict(imagens)[256])
    cab = struct.pack("<HHH", 0, 1, len(imagens))
    entradas, dados = b"", b""
    deslocamento = 6 + 16 * len(imagens)
    for t, b in imagens:
        lado = 0 if t >= 256 else t
        entradas += struct.pack("<BBBBHHII", lado, lado, 0, 0, 1, 32, len(b), deslocamento + len(dados))
        dados += b
    (RAIZ / "app" / "img" / "icone.ico").write_bytes(cab + entradas + dados)
    print("ícones gerados:", ", ".join(str(t) for t, _ in imagens))


if __name__ == "__main__":
    main()
