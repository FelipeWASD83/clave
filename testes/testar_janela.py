"""Abre o Clave de verdade (Electron + servidor) numa pasta de dados temporária e confere a janela pela
porta de depuração do Chromium: a página carregou, sem erro no console, e a API respondeu com a sessão.

Uso: python testes/testar_janela.py [--demo] [--print caminho.png]
Abre uma janela na tela por alguns segundos e fecha sozinho.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("cap", RAIZ / "modelo-de-pasta" / ".claude" / "referencias-visuais" / "capturar-print.py")
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)

PORTA_DEPURACAO = 9561


def main() -> int:
    exe = subprocess.run([sys.executable, str(RAIZ / "ferramentas" / "preparar.py"), "--checar"], capture_output=True,
                         text=True).stdout.strip()
    if not exe:
        print("Electron não preparado (rode ferramentas/preparar.py).")
        return 1
    dados = tempfile.mkdtemp(prefix="clave-janela-")
    env = dict(os.environ, CLAVE_DADOS=dados)
    if "--demo" in sys.argv:
        env["CLAVE_TESTE_DEMO"] = "1"
    proc = subprocess.Popen([exe, str(RAIZ), f"--remote-debugging-port={PORTA_DEPURACAO}"], env=env)
    try:
        alvo = None
        for _ in range(120):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORTA_DEPURACAO}/json", timeout=2) as r:
                    paginas = [p for p in json.loads(r.read()) if p.get("type") == "page" and "127.0.0.1" in p.get("url", "")]
                if paginas:
                    alvo = paginas[0]
                    break
            except OSError:
                pass
            time.sleep(0.5)
        if not alvo:
            print("A janela não abriu a página do Clave.")
            return 1
        ws = cap.WS(alvo["webSocketDebuggerUrl"])
        ws.cmd("Runtime.enable")
        time.sleep(3)
        r = ws.cmd("Runtime.evaluate", {"expression": "JSON.stringify({titulo: document.title, url: location.href, "
                                        "app: !!window.clave, electron: window.clave && window.clave.versaoElectron, "
                                        "lateral: !!document.querySelector('.lateral .marca'), "
                                        "boasVindas: !!document.querySelector('.boas-vindas'), "
                                        "texto: document.body.innerText.slice(0, 160)})", "returnByValue": True})
        print("página:", r.get("result", {}).get("value"))
        if "--print" in sys.argv:
            destino = sys.argv[sys.argv.index("--print") + 1]
            img = ws.cmd("Page.captureScreenshot", {"format": "png"})
            Path(destino).write_bytes(base64.b64decode(img["data"]))
            print("print salvo em", destino)
        ws.fechar()
        print("registro do servidor:")
        log = Path(dados, "logs", "supervisor.log")
        print(log.read_text(encoding="utf-8")[-600:] if log.exists() else "(sem registro)")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
