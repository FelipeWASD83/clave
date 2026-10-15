"""Abre a janela de verdade do Clave (Electron) com a API de mentira e tira prints dos cartões que acontecem
ao vivo: proposta de fluxo, fluxo rodando e concluído, aprovação com regra e plano.

Uso: python testes/prints_janela.py <pasta-de-saida>
A janela aparece na tela por uns 40 segundos e fecha sozinha. Dados numa pasta temporária; nada é cobrado.
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

PORTA_DEPURACAO = 9562
SAIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "prints-janela")
erros: list[str] = []


def main() -> int:
    exe = subprocess.run([sys.executable, str(RAIZ / "ferramentas" / "preparar.py"), "--checar"], capture_output=True,
                         text=True).stdout.strip()
    if not exe:
        print("Electron não preparado (rode ferramentas/preparar.py).")
        return 1
    SAIDA.mkdir(parents=True, exist_ok=True)
    dados = tempfile.mkdtemp(prefix="clave-janela-")
    pasta = tempfile.mkdtemp(prefix="clave-janela-pasta-")
    env = dict(os.environ, CLAVE_DADOS=dados, CLAVE_TESTE_DEMO="1")
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
        ws.cmd("Page.enable")

        def js(expr, espera=0.0):
            r = ws.cmd("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
            if "exceptionDetails" in r:
                erros.append(f"JS: {expr[:60]} -> {r['exceptionDetails'].get('text')}")
            time.sleep(espera)
            return r.get("result", {}).get("value")

        def foto(nome):
            img = ws.cmd("Page.captureScreenshot", {"format": "png"})
            (SAIDA / f"{nome}.png").write_bytes(base64.b64decode(img["data"]))

        def esperar(cond, limite=15.0):
            fim = time.time() + limite
            while time.time() < fim:
                if js(cond):
                    return True
                time.sleep(0.3)
            erros.append(f"não apareceu: {cond[:80]}")
            return False

        def post(caminho, corpo):
            return js(f"fetch('{caminho}',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({json.dumps(corpo)})}}).then(r=>r.json())")

        time.sleep(2.5)
        js("window.__erros = []; const _e = console.error; console.error = (...a) => { window.__erros.push(a.join(' ')); _e(...a); }; 1")
        post("/api/config", {"configurado": True, "nome": "Ana"})
        js("location.hash = '#/novo'; location.reload()", 2.5)
        js("window.__erros = []; const _e = console.error; console.error = (...a) => { window.__erros.push(a.join(' ')); _e(...a); }; 1")

        # fluxo no chat
        js("(() => { const t = document.querySelector('.compositor textarea'); t.value = 'faça isso como um fluxo'; t.dispatchEvent(new Event('input')); document.querySelector('.enviar').click(); })()")
        esperar("!!document.querySelector('.fluxo.proposta')")
        js("document.querySelector('.fluxo.proposta').scrollIntoView({block: 'center'})", 0.4)
        foto("40-fluxo-proposta")
        js("(() => { const s = document.querySelector('.fluxo.proposta select'); s.value = 'claude-haiku-5-5'; s.dispatchEvent(new Event('change')); })()", 0.8)
        js("document.querySelector('.fluxo.proposta button.primario').click()")
        esperar("!!document.querySelector('.fluxo-etapa.viva[data-status=\"rodando\"]')", 8)
        foto("41-fluxo-rodando")
        esperar("!!document.querySelector('.fluxo[data-status=\"concluido\"], .fluxo.salvo[data-status=\"concluido\"]')", 25)
        time.sleep(2.5)
        js("document.querySelector('.fluxo .fluxo-etapa.viva')?.setAttribute('open', ''); document.querySelector('.fluxo')?.scrollIntoView({block: 'start'})", 0.5)
        foto("42-fluxo-concluido")

        # aprovação com regra, no Code
        cid = js(f"fetch('/api/conversas',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{modo:'code',pasta:{json.dumps(pasta)}}})}}).then(r=>r.json()).then(d=>d.conversa.id)")
        js(f"location.hash = '#/c/{cid}'", 1.5)
        js("(() => { const t = document.querySelector('.compositor textarea'); t.value = 'crie um arquivo de exemplo'; t.dispatchEvent(new Event('input')); document.querySelector('.enviar').click(); })()")
        esperar("!!document.querySelector('.aprovacao')")
        js("[...document.querySelectorAll('.aprovacao button')].find(x => x.textContent.startsWith('Mais opções')).click()", 0.5)
        js("[...document.querySelectorAll('.menu button')].find(x => x.textContent.includes('Sempre nesta pasta')).click()", 0.5)
        foto("43-aprovacao-com-regra")
        js("[...document.querySelectorAll('.aprovacao-regra button')].find(x => x.textContent.startsWith('Salvar')).click()")
        esperar("!document.querySelector('.aprovacao')", 8)
        time.sleep(2)
        regra = Path(pasta, ".claude", "settings.local.json")
        print("regra salva na pasta:", regra.read_text(encoding="utf-8").strip() if regra.exists() else "NÃO")

        # plano
        cid = js(f"fetch('/api/conversas',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{modo:'code',pasta:{json.dumps(pasta)}}})}}).then(r=>r.json()).then(d=>d.conversa.id)")
        js(f"location.hash = '#/c/{cid}'", 1.5)
        js("(() => { const c = [...document.querySelectorAll('.compositor .chip')].find(x => x.textContent.includes('Perguntar')); c.click(); })()", 0.4)
        js("[...document.querySelectorAll('.menu button')].find(x => x.textContent.startsWith('Plano')).click()", 0.3)
        js("(() => { const t = document.querySelector('.compositor textarea'); t.value = 'planeje a organização desta pasta'; t.dispatchEvent(new Event('input')); document.querySelector('.enviar').click(); })()")
        esperar("!!document.querySelector('.fluxo.plano:not(.salvo)')")
        foto("44-plano")
        js("[...document.querySelectorAll('.fluxo.plano button')].find(x => x.textContent.startsWith('Executar e aceitar')).click()")
        esperar("[...document.querySelectorAll('.ferramenta')].some(d => d.textContent.includes('exemplo-do-plano'))", 10)
        time.sleep(2)
        foto("45-plano-executado")
        print("arquivo do plano criado:", Path(pasta, "exemplo-do-plano.txt").exists())
        for e in json.loads(js("JSON.stringify(window.__erros || [])") or "[]"):
            erros.append("console: " + e)
        ws.fechar()
        print("\n".join(erros) if erros else "nenhum erro")
        return 1 if erros else 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)


if __name__ == "__main__":
    sys.exit(main())
