"""Prepara o "motor" da janela do Clave (o Electron) e diz qual executável abrir.

Uso:
  python ferramentas/preparar.py              baixa o Electron se faltar ou se a versão mudou; imprime o caminho do electron.exe
  python ferramentas/preparar.py --checar     só imprime o caminho (ou nada, se não houver Electron pronto)

O Electron vem do pacote oficial (github.com/electron/electron/releases), conferido
pelo SHA-256 publicado junto. Ele fica em runtime/electron, fora do git.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUNTIME = RAIZ / "runtime" / "electron"
MARCA = RUNTIME / "clave-versao.txt"


def versao_pedida() -> str:
    return json.loads((RAIZ / "versao.json").read_text(encoding="utf-8")).get("electron", "")


def executavel() -> Path | None:
    candidatos = [RUNTIME / "electron.exe", RAIZ / "node_modules" / "electron" / "dist" / "electron.exe"]
    if sys.platform != "win32":
        candidatos = [RUNTIME / "electron", RAIZ / "node_modules" / "electron" / "dist" / "electron"]
    for c in candidatos:
        if c.is_file():
            return c
    return None


def runtime_ok() -> bool:
    try:
        return (RUNTIME / "electron.exe").is_file() and MARCA.read_text(encoding="utf-8").strip() == versao_pedida()
    except OSError:
        return False


def _baixar(url: str, destino: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "Clave-instalador"})
    with urllib.request.urlopen(req, timeout=60) as r, open(destino, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        feito = 0
        while True:
            bloco = r.read(1 << 20)
            if not bloco:
                break
            f.write(bloco)
            feito += len(bloco)
            if total:
                print(f"\r  baixando o Electron: {feito * 100 // total}%", end="", flush=True, file=sys.stderr)
    print(file=sys.stderr)


def baixar_electron() -> Path:
    versao = versao_pedida()
    if not versao:
        raise SystemExit("versao.json não diz qual Electron usar.")
    if sys.platform != "win32":
        raise SystemExit("O download automático do Electron é só para Windows. Use: npm install && npm start")
    nome = f"electron-v{versao}-win32-x64.zip"
    base = f"https://github.com/electron/electron/releases/download/v{versao}"
    tmp = RAIZ / "runtime" / "baixando"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    print(f"Baixando o Electron {versao} (uns 110 MB, só desta vez)...", file=sys.stderr)
    _baixar(f"{base}/SHASUMS256.txt", tmp / "SHASUMS256.txt")
    esperado = None
    for linha in (tmp / "SHASUMS256.txt").read_text(encoding="utf-8").splitlines():
        partes = linha.split()
        if len(partes) == 2 and partes[1].lstrip("*") == nome:
            esperado = partes[0].lower()
    if not esperado:
        raise SystemExit("Não achei a assinatura do Electron na lista oficial.")
    _baixar(f"{base}/{nome}", tmp / nome)
    h = hashlib.sha256((tmp / nome).read_bytes()).hexdigest()
    if h != esperado:
        raise SystemExit("O arquivo baixado do Electron não confere com a assinatura oficial. Tente de novo.")
    destino_novo = RAIZ / "runtime" / "electron-novo"
    shutil.rmtree(destino_novo, ignore_errors=True)
    with zipfile.ZipFile(tmp / nome) as z:
        z.extractall(destino_novo)
    shutil.rmtree(RUNTIME, ignore_errors=True)
    destino_novo.rename(RUNTIME)
    MARCA.write_text(versao, encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Electron {versao} pronto em {RUNTIME}", file=sys.stderr)
    return RUNTIME / "electron.exe"


def main() -> int:
    if "--checar" in sys.argv:
        exe = RUNTIME / "electron.exe" if runtime_ok() else executavel()
        if exe:
            print(exe)
        return 0
    if not runtime_ok() and not (RAIZ / "node_modules" / "electron" / "dist" / "electron.exe").is_file():
        try:
            baixar_electron()
        except (OSError, SystemExit) as e:
            print(f"Não deu para preparar o Electron ({e}). O Clave abre no navegador, em modo janela.", file=sys.stderr)
            return 1
    exe = executavel()
    print(exe or "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
