"""Garante UTF-8 com BOM em todos os .ps1 do projeto (o PowerShell 5.1 lê .ps1 sem BOM como ANSI e estraga os acentos)."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"

for arq in RAIZ.rglob("*.ps1"):
    if any(p in arq.parts for p in (".venv", "runtime", "node_modules", "dados")):
        continue
    dados = arq.read_bytes()
    if not dados.startswith(BOM):
        arq.write_bytes(BOM + dados.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        print("BOM:", arq.relative_to(RAIZ))
