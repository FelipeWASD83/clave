"""Teste de verdade do navegador do Code: abre o Clave no Electron (modo demonstração, dados numa pasta temporária,
porta de depuração), serve uma página de teste local e fala com a ponte do navegador como o servidor fala.

Confere: abrir, ler (com a senha da página fora do texto, inclusive o campo que só o rótulo diz que é senha),
digitar, a recusa do campo de senha e de cartão, clicar (com o mouse de verdade quando a página está à vista),
Enter num formulário, link com target=_blank na mesma página, rolar, voltar, erro de carga na tela, print
(cabeçalho PNG) com a aba à vista e escondida, a vista dentro do painel (pela conta e por uma foto da janela inteira)
e escondida quando um menu do app abre por cima, e a ponte recusando token errado, Origin e Host de fora.

E o que a revisão do 5.0 pediu: o clique só vale na página e no elemento aprovados (página trocada e elemento
renomeado são recusados, e a página que põe um número falso nos elementos não engana), a leitura não deixa atributo
nenhum na página, o clique que cai em outro elemento é avisado (e não repetido), a página em branco, apagar os dados
do navegador (o cookie some) e os atalhos com o foco na barra da aba (Alt+seta, F5, Ctrl+L).

Uso: python testes/testar_navegador.py [pasta-para-os-prints] [--en]   (--en: a interface em inglês)
Uma janela aparece na tela por uns 30 segundos e fecha sozinha. Nada é cobrado (API de mentira).
"""
from __future__ import annotations

import base64
import ctypes
import ctypes.wintypes as wt
import importlib.util
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("cap", RAIZ / "modelo-de-pasta" / ".claude" / "referencias-visuais" / "capturar-print.py")
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)

PORTA_DEPURACAO = 9563
COR_FAIXA = (47, 111, 222)  # a faixa azul no topo da página de teste: é por ela que a foto da janela acha a página
falhas: list[str] = []
oks: list[str] = []


def conferir(cond, msg):
    (oks if cond else falhas).append(msg)
    print(("  ok  " if cond else "  FALHOU  ") + msg, flush=True)
    return cond


# ---------------- a página de teste ----------------

PAGINA = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Página de teste do navegador</title>
<style>body{margin:0;font-family:sans-serif}header{background:rgb(47,111,222);height:140px;color:#fff;padding:16px}
main{padding:16px;display:grid;gap:12px;max-width:520px}.alto{height:1600px}</style></head><body>
<header><h1>Teste do navegador</h1></header>
<main>
<a href="/segunda">Ir para a segunda página</a>
<a href="/terceira" target="_blank">Abrir em outra janela</a>
<button id="botao" onclick="document.getElementById('saida').textContent='Clicou no botão!'">Mudar o texto</button>
<p id="saida">Ninguém clicou ainda.</p>
<label>Seu nome <input id="nome" name="nome" value="antigo"></label>
<p id="eco"></p>
<label>Senha <input id="senha" type="password" name="senha" value="segredo-da-pagina-123"></label>
<label>Número do cartão <input id="cartao" autocomplete="cc-number"></label>
<label>Senha do banco <input name="c1" value="segredo-do-rotulo-456"></label>
<label for="cv">CVV</label> <input id="cv" name="f2">
<label>Cor <select id="cor"><option>Azul</option><option>Verde</option><option>Vermelho</option></select></label>
<form action="/busca" method="get"><label>Buscar <input name="q" id="q"></label></form>
<button id="alvo" onclick="document.getElementById('saida').textContent='Clicou no alvo'">Alvo</button>
<button id="trocar" onclick="document.getElementById('alvo').textContent='Apagar tudo'">Trocar o nome do alvo</button>
<button id="armadilha" data-clave-ref="1" data-clave-ref-x="2" onclick="document.getElementById('saida').textContent='Caiu na armadilha'">Armadilha</button>
<button id="fujao" onmousemove="this.style.transform='translateX(420px)'" onclick="document.getElementById('saida').textContent='Pegou o fujão'">Fujão</button>
<p id="ultimo"></p>
<div class="alto">Fim da página lá embaixo.</div>
</main>
<script>document.getElementById('nome').addEventListener('input', e => { document.getElementById('eco').textContent = 'Eco: ' + e.target.value; });
for (const tipo of ['mousedown', 'click']) addEventListener(tipo, (e) => { document.getElementById('ultimo').textContent += ' ' + tipo + ':' + (e.target.id || e.target.tagName); }, true);
// a página tenta roubar o número do botão Alvo: qualquer atributo data-c... posto nele vai para a Armadilha
new MutationObserver((ms) => { for (const m of ms) { const n = m.attributeName || '';
  if (m.type === 'attributes' && n.startsWith('data-c') && m.target.id === 'alvo') { const v = m.target.getAttribute(n);
    if (v !== null) { m.target.removeAttribute(n); document.getElementById('armadilha').setAttribute(n, v); } } } })
  .observe(document.body, { attributes: true, subtree: true });</script>
</body></html>"""
CONTADOR = {"n": 0}
# os nomes de todos os atributos da página, para ver que a leitura não deixa marca nenhuma nela
ATRIBUTOS_JS = "JSON.stringify([...document.querySelectorAll('*')].map((e) => [...e.attributes].map((a) => a.name).join(',')))"


class Pagina(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        extra = {}
        if u.path == "/":
            corpo = PAGINA
            extra["Set-Cookie"] = "visita=1; Max-Age=3600; Path=/"
        elif u.path == "/eco-cookie":
            corpo = f"<!doctype html><title>Cookie</title><p>Cookie recebido: {self.headers.get('Cookie') or 'nenhum'}</p>"
        elif u.path == "/contador":
            CONTADOR["n"] += 1
            corpo = f"<!doctype html><title>Contador</title><p>Visita número {CONTADOR['n']}</p>"
        elif u.path == "/segunda":
            corpo = "<!doctype html><title>Segunda página</title><p>Você está na segunda página.</p>"
        elif u.path == "/terceira":
            corpo = "<!doctype html><title>Terceira página</title><p>Abriu aqui mesmo.</p>"
        elif u.path == "/busca":
            q = urllib.parse.parse_qs(u.query).get("q", [""])[0]
            corpo = f"<!doctype html><title>Busca</title><p>Você buscou: {q}</p>"
        else:
            self.send_error(404)
            return
        dados = corpo.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)


# ---------------- foto da janela inteira (com a vista nativa, que o CDP não pega) ----------------

def achar_janela(pid: int):
    """A janela visível "Clave" do processo do Electron."""
    user32 = ctypes.windll.user32
    achadas = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cada(hwnd, _):
        dono = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(dono))
        if dono.value == pid and user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if buf.value == "Clave":
                achadas.append(hwnd)
        return True
    user32.EnumWindows(cada, 0)
    return achadas[0] if achadas else None


def por_cima(pid: int, sim: bool) -> None:
    """Deixa a janela por cima das outras durante o teste: coberta, o Chromium para de desenhar (como quando a pessoa
    está em outro programa) e a foto da janela sairia vazia."""
    hwnd = achar_janela(pid)
    if hwnd:
        ctypes.windll.user32.SetWindowPos(hwnd, -1 if sim else -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)


def foto_da_janela(pid: int, destino: Path):
    """PrintWindow com PW_RENDERFULLCONTENT na janela "Clave" do processo: devolve (largura, altura, BGRA)."""
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    hwnd = achar_janela(pid)
    if not hwnd:
        return None
    r = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    w, h = r.right, r.bottom
    hdc = user32.GetDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 3)  # PW_CLIENTONLY | PW_RENDERFULLCONTENT

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG), ("biPlanes", wt.WORD),
                    ("biBitCount", wt.WORD), ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                    ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG), ("biClrUsed", wt.DWORD),
                    ("biClrImportant", wt.DWORD)]
    bi = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    dados = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mem, bmp, 0, h, dados, ctypes.byref(bi), 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    bgra = dados.raw
    rgba = bytearray(len(bgra))
    rgba[0::4], rgba[1::4], rgba[2::4] = bgra[2::4], bgra[1::4], bgra[0::4]
    rgba[3::4] = b"\xff" * (w * h)
    linhas = b"".join(b"\x00" + bytes(rgba[y * w * 4:(y + 1) * w * 4]) for y in range(h))

    def bloco(tipo, conteudo):
        return struct.pack(">I", len(conteudo)) + tipo + conteudo + struct.pack(">I", zlib.crc32(tipo + conteudo) & 0xFFFFFFFF)
    destino.write_bytes(b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                        + bloco(b"IDAT", zlib.compress(linhas, 6)) + bloco(b"IEND", b""))
    return w, h, bgra


def pixel(foto, x, y):
    w, h, bgra = foto
    x, y = max(0, min(w - 1, int(x))), max(0, min(h - 1, int(y)))
    i = (y * w + x) * 4
    return bgra[i + 2], bgra[i + 1], bgra[i]


def perto(c1, c2, tol=24):
    return all(abs(a - b) <= tol for a, b in zip(c1, c2))


# ---------------- o teste ----------------

def main() -> int:
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # por monitor v2: pixels de verdade
    except Exception:
        pass
    if os.name != "nt":
        print("Este teste é do Windows (a janela do Clave e a foto pela API do Windows).")
        return 1
    exe = subprocess.run([sys.executable, str(RAIZ / "ferramentas" / "preparar.py"), "--checar"], capture_output=True,
                         text=True).stdout.strip()
    if not exe:
        print("Electron não preparado (rode ferramentas/preparar.py).")
        return 1
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    saida = Path(args[0]) if args else Path(tempfile.mkdtemp(prefix="clave-navegador-prints-"))
    saida.mkdir(parents=True, exist_ok=True)
    dados = Path(tempfile.mkdtemp(prefix="clave-janela-nav-"))
    pasta = Path(tempfile.mkdtemp(prefix="clave-janela-nav-pasta-"))
    class Servidor(ThreadingHTTPServer):
        def handle_error(self, request, client_address):  # o Chromium abre conexões de reserva e derruba: não é erro
            if not isinstance(sys.exc_info()[1], ConnectionError):
                super().handle_error(request, client_address)
    servidor_pagina = Servidor(("127.0.0.1", 0), Pagina)
    threading.Thread(target=servidor_pagina.serve_forever, daemon=True).start()
    base = f"http://localhost:{servidor_pagina.server_address[1]}"
    env = dict(os.environ, CLAVE_DADOS=str(dados), CLAVE_TESTE_DEMO="1", CLAVE_IDIOMA="en" if "--en" in sys.argv else "pt-BR")
    # sem o cálculo de oclusão do Chromium: com a tela desligada ou o PC parado, o Windows dá a janela como coberta,
    # a página para de desenhar e a foto da janela sairia vazia (o app de verdade lida com isso; o teste quer ver)
    # perfil do Electron descartável: nada do teste fica no perfil de verdade (preferências, cookies do navegador) e o
    # teste roda mesmo com o Clave da pessoa aberto (a trava de uma janela só é por perfil)
    perfil = Path(tempfile.mkdtemp(prefix="clave-janela-nav-perfil-"))
    proc = subprocess.Popen([exe, str(RAIZ), f"--remote-debugging-port={PORTA_DEPURACAO}", f"--user-data-dir={perfil}",
                             "--disable-features=CalculateNativeWinOcclusion", "--disable-backgrounding-occluded-windows"], env=env)
    ws = None
    try:
        # a ponte e o servidor do app
        arq_ponte, arq_srv = dados / "ponte.json", dados / "servidor.json"
        for _ in range(120):
            if arq_ponte.exists() and arq_srv.exists():
                break
            time.sleep(0.5)
        if not conferir(arq_ponte.exists(), "a janela escreveu ponte.json (só no modo de teste)"):
            return 1
        ponte_info = json.loads(arq_ponte.read_text(encoding="utf-8"))
        porta_app = json.loads(arq_srv.read_text(encoding="utf-8"))["porta"]
        origem_app = f"http://127.0.0.1:{porta_app}/"

        def ponte(acao, token=None, cab=None, **corpo):
            req = urllib.request.Request(ponte_info["url"] + "/navegador", data=json.dumps({"acao": acao, **corpo}).encode(),
                                         method="POST", headers={"Content-Type": "application/json",
                                                                 "X-Clave-Token": token or ponte_info["token"], **(cab or {})})
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read() or b"{}")

        def nav(acao, **corpo):
            return ponte(acao, **corpo)[1]

        # clicar e digitar levam a página e o elemento aprovados (como o servidor manda depois do cartão)
        def esperado_de(ref):
            d = nav("descrever", ref=ref)
            return {"url": d.get("url"), "papel": d.get("papel"), "nome": d.get("nome")}

        def clicar(ref, esperado=None):
            return nav("clicar", ref=ref, esperado=esperado or esperado_de(ref))

        def digitar(ref, texto, enter=False):
            return nav("digitar", ref=ref, texto=texto, enter=enter, esperado=esperado_de(ref))

        def na_vista(expr):
            """Avalia uma expressão na página do navegador (a vista), pela porta de depuração."""
            with urllib.request.urlopen(f"http://127.0.0.1:{PORTA_DEPURACAO}/json", timeout=5) as rr:
                alvos = json.loads(rr.read())
            alvo_v = next((p for p in alvos if p.get("type") == "page" and p.get("url", "").startswith(base)), None)
            if not alvo_v:
                return None
            w = cap.WS(alvo_v["webSocketDebuggerUrl"])
            try:
                return w.cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}).get("result", {}).get("value")
            finally:
                w.fechar()

        # a página do app, pelo endereço do servidor (a vista do navegador também aparece na lista de alvos)
        alvo = None
        for _ in range(120):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{PORTA_DEPURACAO}/json", timeout=2) as r:
                    lista = json.loads(r.read())
                alvo = next((p for p in lista if p.get("type") == "page" and p.get("url", "").startswith(origem_app)), None)
                if alvo:
                    break
            except OSError:
                pass
            time.sleep(0.5)
        if not conferir(alvo is not None, "a janela abriu a página do Clave"):
            return 1
        ws = cap.WS(alvo["webSocketDebuggerUrl"])
        ws.cmd("Runtime.enable")
        ws.cmd("Page.enable")

        def js(expr, espera=0.0):
            r = ws.cmd("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
            if "exceptionDetails" in r:
                falhas.append(f"JS: {expr[:70]} -> {r['exceptionDetails'].get('text')} {r['exceptionDetails'].get('exception', {}).get('description', '')[:200]}")
            time.sleep(espera)
            return r.get("result", {}).get("value")

        def esperar(cond, limite=10.0):
            fim = time.time() + limite
            while time.time() < fim:
                if cond():
                    return True
                time.sleep(0.2)
            return False

        time.sleep(2.5)
        js("fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({configurado:true,nome:'Ana',tours_vistos:['geral','code','precos','fluxos','conversa']})}).then(r=>r.status)")
        js("location.reload()", 3)
        js("window.__erros = []; const _e = console.error; console.error = (...a) => { window.__erros.push(a.join(' ')); _e(...a); }; addEventListener('error', (e) => window.__erros.push(String(e.message))); 1")
        # a aba Navegador: o integrador põe o import no abas.js; até lá, o teste carrega o mesmo módulo
        js("import('/js/navegador.js').then(() => 'carregou')")
        cid = js(f"fetch('/api/conversas',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{modo:'code',pasta:{json.dumps(str(pasta))}}})}}).then(r=>r.json()).then(d=>d.conversa.id)")
        js(f"location.hash = '#/c/{cid}'", 2)
        por_cima(proc.pid, True)
        # o cartão de modelo novo abre sozinho uma vez, um pouco depois de a tela carregar: fecha
        esperar(lambda: js("!!document.querySelector('.apresentacao-fundo')"), 4)
        js("document.querySelectorAll('.tour-camada, .apresentacao-fundo').forEach((e) => e.querySelector('.tour-pular, .apresentacao-fechar')?.click()); 1", 0.6)

        print("\n[ponte]")
        st, r = ponte("estado", token="errado")
        conferir(st == 401, "token errado é recusado (401)")
        st, r = ponte("estado", cab={"Origin": "https://site-qualquer.com"})
        conferir(st == 403, "pedido com Origin (vindo de uma página) é recusado (403)")
        st, r = ponte("estado", cab={"Host": "evil.example:80"})
        conferir(st == 403, "Host de fora é recusado (403)")
        e = nav("estado")
        conferir(e.get("url") == "" and e.get("visivel") is False, f"começa sem página e escondida: {e}")

        print("\n[servidores locais]")
        if js("fetch('/api/navegador/localhosts').then(r => r.status)") != 200:
            # a rota só existe quando o servidor.py importa o navegador.py (o integrador liga). Até lá, a lista
            # verdadeira (a mesma função da rota, rodando aqui) chega à página por um fetch de mentira
            print("   (a rota ainda não está ligada no servidor: a lista vem do navegador.py rodando no teste)")
            os.environ["CLAVE_DADOS"] = str(dados)
            sys.path.insert(0, str(RAIZ / "servidor"))
            import navegador as nav_srv
            lista = nav_srv.servidores_locais(excluir={porta_app, int(ponte_info["url"].rsplit(":", 1)[1])})
            js("(() => { const f = window.fetch; const d = " + json.dumps({"servidores": lista}) + "; window.fetch = (u, o) => "
               "String(u).includes('/api/navegador/localhosts') ? Promise.resolve(new Response(JSON.stringify(d), "
               "{ status: 200, headers: { 'Content-Type': 'application/json' } })) : f(u, o); return 1; })()")

        print("\n[mostrar e abrir]")
        r = nav("mostrar", claude=True)
        conferir(esperar(lambda: js("!!document.querySelector('.aba-navegador:not([hidden]) .navegador-inicio')")),
                 "o pedido 'mostrar' abriu a aba Navegador na tela inicial")
        conferir(bool(js("!document.querySelector('.navegador-claude').hidden")), "a faixa 'O Claude está usando o navegador' apareceu")
        conferir(esperar(lambda: js("[...document.querySelectorAll('.aba-navegador .navegador-local')].some((b) => b.textContent.includes('Página de teste do navegador'))"), 8),
                 "a página de teste aparece em 'Servidores neste computador', com o título")
        time.sleep(0.5)
        img = ws.cmd("Page.captureScreenshot", {"format": "png"})
        (saida / "navegador-inicio-com-locais.png").write_bytes(base64.b64decode(img["data"]))
        js("[...document.querySelectorAll('.aba-navegador .navegador-local')].find((b) => b.textContent.includes('Página de teste do navegador'))?.click()")
        conferir(esperar(lambda: nav("estado").get("titulo") == "Página de teste do navegador", 8),
                 "clicar no servidor da lista abre a página no navegador")
        nav("mostrar", claude=True)
        with socket.socket() as s:  # uma porta que ninguém ouve
            s.bind(("127.0.0.1", 0))
            porta_fechada = s.getsockname()[1]
        r = nav("abrir", url=f"http://127.0.0.1:{porta_fechada}/")
        conferir(r.get("erro") == "carregar" and "ERR_CONNECTION_REFUSED" in str(r.get("detalhe")), f"endereço sem servidor dá erro de carga: {r}")
        conferir(esperar(lambda: js("!!document.querySelector('.aba-navegador .navegador-erro')")), "a tela de erro apareceu na aba")
        img = ws.cmd("Page.captureScreenshot", {"format": "png"})
        (saida / "navegador-erro.png").write_bytes(base64.b64decode(img["data"]))
        r = nav("abrir", url="file:///C:/Windows/win.ini")
        conferir(r.get("erro") == "url_invalida", "file:// é recusado")
        r = nav("abrir", url=base + "/")
        conferir(r.get("ok") and r.get("titulo") == "Página de teste do navegador", f"abriu a página de teste: {r.get('titulo')}")
        conferir(esperar(lambda: nav("estado").get("visivel")), "a vista apareceu (aba à vista e com página)")

        print("\n[a vista dentro do painel]")
        time.sleep(0.8)
        geo = js("(() => { const r = document.querySelector('.aba-navegador .navegador-vista').getBoundingClientRect();"
                 " const p = document.getElementById('painel-lateral').getBoundingClientRect();"
                 " const m = document.querySelector('.aba-navegador').classList.contains('com-claude') ? 2 : 0;"
                 " return { x: r.left + m, y: r.top + m, w: r.width - 2 * m, h: r.height - 2 * m, m, px: p.left, pr: p.right, dpr: devicePixelRatio }; })()")
        lim = nav("estado").get("limites") or {}
        conferir(geo and lim and abs(lim["x"] - geo["x"]) <= 1 and abs(lim["y"] - geo["y"]) <= 1
                 and abs(lim["width"] - geo["w"]) <= 1 and abs(lim["height"] - geo["h"]) <= 1,
                 f"limites da vista = área .navegador-vista (moldura {geo and geo['m']} px com o Claude agindo) ({lim} x {geo})")
        conferir(geo and geo["x"] >= geo["px"] - 1 and geo["x"] + geo["w"] <= geo["pr"] + 1, "a área fica dentro do painel lateral")
        img = ws.cmd("Page.captureScreenshot", {"format": "png"})
        (saida / "navegador-app-cdp.png").write_bytes(base64.b64decode(img["data"]))
        foto = foto_da_janela(proc.pid, saida / "navegador-janela.png")
        if conferir(foto is not None, "foto da janela inteira (PrintWindow)"):
            d = geo["dpr"]
            dentro = pixel(foto, (geo["x"] + 20) * d, (geo["y"] + 30) * d)
            fora = pixel(foto, (geo["px"] - 40) * d, (geo["y"] + 30) * d)
            conferir(perto(dentro, COR_FAIXA), f"a faixa azul da página aparece dentro do painel na foto da janela ({dentro})")
            conferir(not perto(fora, COR_FAIXA), f"e fora do painel não ({fora})")

        print("\n[ler]")
        r = nav("ler")
        elems = r.get("elementos") or []
        ref = {e["nome"]: e["ref"] for e in elems}
        print("   elementos:", [(e["ref"], e["papel"], e["nome"]) for e in elems])
        conferir("Teste do navegador" in r.get("texto", ""), "texto visível lido")
        conferir("segredo-da-pagina-123" not in json.dumps(r, ensure_ascii=False), "o valor do campo de senha não sai na leitura")
        senha = next((e for e in elems if e["nome"] == "Senha"), {})
        conferir(senha.get("sensivel") == "senha", "o campo de senha vem marcado como sensível")
        cartao = next((e for e in elems if e["nome"] == "Número do cartão"), {})
        conferir(cartao.get("sensivel") == "cartao", "o campo de cartão (autocomplete cc-number) vem marcado")
        rotulo = next((e for e in elems if e["nome"] == "Senha do banco"), {})
        conferir(rotulo.get("sensivel") == "senha", f"campo comum cujo rótulo diz Senha vem marcado como senha: {rotulo}")
        conferir("segredo-do-rotulo-456" not in json.dumps(r, ensure_ascii=False), "e o valor dele não sai na leitura")
        cvv = next((e for e in elems if e["nome"] == "CVV"), {})
        conferir(cvv.get("sensivel") == "cartao", f"campo com <label for> CVV vem marcado como cartão: {cvv}")
        conferir(all(k in ref for k in ("Ir para a segunda página", "Mudar o texto", "Seu nome", "Buscar")), "links, botão e campos numerados")

        print("\n[digitar]")
        r = digitar(ref["Seu nome"], "Ana Teste")
        conferir(r.get("ok"), f"digitou no campo de nome ({r.get('metodo')})")
        r = nav("ler")
        nome = next((e for e in r["elementos"] if e["nome"] == "Seu nome"), {})
        conferir(nome.get("valor") == "Ana Teste", f"o campo ficou com o texto novo, trocando o antigo: {nome.get('valor')!r}")
        conferir("Eco: Ana Teste" in r.get("texto", ""), "a página recebeu o evento de digitação (o eco mudou)")
        ref = {e["nome"]: e["ref"] for e in r["elementos"]}
        r = digitar(ref["Senha"], "123")
        conferir(r.get("erro") == "campo_senha", f"campo de senha recusado: {r.get('erro')}")
        r = digitar(ref["Número do cartão"], "4111")
        conferir(r.get("erro") == "campo_cartao", f"campo de cartão recusado: {r.get('erro')}")
        r = digitar(ref["Senha do banco"], "123")
        conferir(r.get("erro") == "campo_senha", f"campo de senha só pelo rótulo recusado: {r.get('erro')}")
        r = digitar(ref["CVV"], "123")
        conferir(r.get("erro") == "campo_cartao", f"CVV recusado: {r.get('erro')}")
        r = nav("digitar", ref=ref["Seu nome"], texto="sem conferência")
        conferir(r.get("erro") == "sem_conferencia", f"digitar sem a página e o elemento aprovados é recusado: {r.get('erro')}")
        r = digitar(ref["Cor"], "verde")
        conferir(r.get("escolhido") == "Verde", f"lista: escolheu a opção pelo texto ({r.get('escolhido')})")

        print("\n[clicar]")
        r = clicar(ref["Mudar o texto"])
        conferir(r.get("ok"), f"clicou no botão (método {r.get('metodo')})")
        metodo_visivel = r.get("metodo")
        r = nav("ler")
        conferir("Clicou no botão!" in r.get("texto", ""), "o botão mudou o texto da página")
        r = nav("print")
        png = base64.b64decode(r.get("png", "") or "")
        conferir(png[:8] == b"\x89PNG\r\n\x1a\n" and r.get("largura", 0) > 100 and r.get("largura", 0) <= 1280,
                 f"print com a aba à vista: PNG {r.get('largura')}x{r.get('altura')}")
        (saida / "navegador-print.png").write_bytes(png)
        ref = {e["nome"]: e["ref"] for e in nav("ler")["elementos"]}
        r = digitar(ref["Buscar"], "gatos pretos", enter=True)
        conferir(r.get("navegou") and "/busca?q=gatos" in r.get("url", ""), f"Enter enviou o formulário: {r.get('url')}")
        r = nav("voltar")
        conferir(r.get("ok") and r.get("url", "").rstrip("/") == base, f"voltou para a página de teste: {r.get('url')}")
        ref = {e["nome"]: e["ref"] for e in nav("ler")["elementos"]}
        r = clicar(ref["Abrir em outra janela"])
        conferir(r.get("url", "").endswith("/terceira"), f"link com target=_blank abre na mesma vista: {r.get('url')}")
        nav("voltar")

        print("\n[o clique só vale na página e no elemento aprovados]")
        nav("abrir", url=base + "/")
        antes = na_vista(ATRIBUTOS_JS)
        r = nav("ler")
        conferir(antes is not None and antes == na_vista(ATRIBUTOS_JS), "a leitura não deixa atributo nenhum na página")
        ref = {e["nome"]: e["ref"] for e in r["elementos"]}
        r = clicar(ref["Alvo"])
        conferir(r.get("ok") and "Clicou no alvo" in nav("ler").get("texto", ""),
                 f"a página que tenta passar o número do Alvo para a Armadilha não engana: {r.get('erro') or r.get('metodo')}")
        r = nav("clicar", ref=ref["Alvo"])
        conferir(r.get("erro") == "sem_conferencia", f"clicar sem a página e o elemento aprovados é recusado: {r.get('erro')}")
        ref = {e["nome"]: e["ref"] for e in nav("ler")["elementos"]}
        aprovado = esperado_de(ref["Alvo"])
        clicar(ref["Trocar o nome do alvo"])
        r = clicar(ref["Alvo"], aprovado)
        conferir(r.get("erro") == "elemento_mudou" and r.get("nome") == "Apagar tudo",
                 f"o elemento renomeado depois do OK não é clicado: {r.get('erro')} {r.get('nome')}")
        ref = {e["nome"]: e["ref"] for e in nav("ler")["elementos"]}
        aprovado = esperado_de(ref["Ir para a segunda página"])
        nav("abrir", url=base + "/terceira")
        r = clicar(ref["Ir para a segunda página"], aprovado)
        conferir(r.get("erro") == "pagina_mudou" and r.get("url", "").endswith("/terceira"),
                 f"com a página trocada enquanto o cartão esperava, nada é clicado: {r.get('erro')} {r.get('url')}")

        print("\n[o clique que cai em outro elemento]")
        nav("abrir", url=base + "/")
        conferir(esperar(lambda: nav("estado").get("visivel"), 4), "a vista está à vista (o clique vai pelo mouse)")
        ref = {e["nome"]: e["ref"] for e in nav("ler")["elementos"]}
        r = clicar(ref["Fujão"])
        texto = nav("ler").get("texto", "")
        conferir(r.get("erro") == "clique_em_outro", f"o botão que foge do mouse: o clique caiu em outro e isso é avisado ({r.get('erro')} {r.get('metodo')} {r.get('clique')}; {texto[-160:]!r})")
        conferir("Pegou o fujão" not in texto, "e o Clave não clicou de novo direto no botão")

        print("\n[página em branco]")
        r = nav("em_branco")
        conferir(r.get("ok") and nav("estado").get("url") == "", f"em_branco tira a página da frente: {r}")

        print("\n[apagar os dados do navegador]")
        nav("abrir", url=base + "/")
        nav("abrir", url=base + "/eco-cookie")
        conferir("visita=1" in nav("ler").get("texto", ""), "o site guardou um cookie")
        r = nav("limpar")
        conferir(r.get("ok") is True, f"limpar respondeu ok: {r}")
        e = nav("estado")
        conferir(e.get("url") == "" and not e.get("podeVoltar"), f"a página ficou em branco e sem histórico: {e}")
        nav("abrir", url=base + "/eco-cookie")
        conferir("Cookie recebido: nenhum" in nav("ler").get("texto", ""), "depois de limpar, o cookie sumiu")

        print("\n[atalhos com o foco na barra da aba]")
        nav("abrir", url=base + "/contador")
        antes = nav("ler").get("texto", "")
        js("window.__marcaDoTeste = 1; document.querySelector('.aba-navegador .navegador-endereco-campo').focus(); 1", 0.2)

        def tecla(key, code, vk, modificadores=0):
            for tipo in ("rawKeyDown", "keyUp"):
                ws.cmd("Input.dispatchKeyEvent", {"type": tipo, "key": key, "code": code, "windowsVirtualKeyCode": vk,
                                                  "nativeVirtualKeyCode": vk, "modifiers": modificadores})
        tecla("F5", "F5", 116)
        conferir(esperar(lambda: nav("ler").get("texto", "") not in ("", antes), 6),
                 f"F5 com o foco no endereço recarrega a página ({antes!r} -> {nav('ler').get('texto', '')!r})")
        conferir(js("window.__marcaDoTeste === 1"), "e não recarregou a tela do Clave")
        nav("abrir", url=base + "/segunda")
        js("document.querySelector('.aba-navegador .navegador-endereco-campo').focus(); 1", 0.2)
        tecla("ArrowLeft", "ArrowLeft", 37, 1)
        conferir(esperar(lambda: nav("estado").get("url", "").endswith("/contador"), 6), "Alt+seta para a esquerda com o foco no endereço volta")
        js("document.querySelector('.aba-navegador .navegador-endereco-campo').focus(); 1", 0.2)
        tecla("ArrowRight", "ArrowRight", 39, 1)
        conferir(esperar(lambda: nav("estado").get("url", "").endswith("/segunda"), 6), "Alt+seta para a direita avança")
        js("document.querySelector('.aba-navegador .navegador-barra button').focus(); 1", 0.2)
        tecla("l", "KeyL", 76, 2)
        conferir(esperar(lambda: js("document.activeElement?.classList.contains('navegador-endereco-campo')"), 3),
                 "Ctrl+L com o foco num botão da barra vai para o endereço")
        js("document.activeElement?.blur(); 1", 0.2)
        nav("abrir", url=base + "/")

        print("\n[um menu do app por cima]")
        js("document.querySelector('.aba-navegador .navegador-botao-locais').click()", 0.2)
        conferir(esperar(lambda: not nav("estado").get("visivel"), 4), "com o menu Locais aberto, a vista sai da frente")
        conferir(esperar(lambda: js("(() => { const f = document.querySelector('.aba-navegador .navegador-foto'); return !f.hidden && f.src.startsWith('data:image/'); })()"), 4),
                 "e uma foto congelada da página fica no lugar")
        time.sleep(1.5)
        foto2 = foto_da_janela(proc.pid, saida / "navegador-menu-por-cima.png")
        js("document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))", 0.3)
        conferir(esperar(lambda: nav("estado").get("visivel"), 4), "fechando o menu, a vista volta")
        js("document.body.classList.add('arrastando-painel')", 0.2)
        conferir(esperar(lambda: not nav("estado").get("visivel"), 4), "arrastando a alça do painel, a vista sai da frente")
        js("document.body.classList.remove('arrastando-painel')", 0.2)
        conferir(esperar(lambda: nav("estado").get("visivel"), 4), "soltando a alça, a vista volta")

        print("\n[aba escondida]")
        js("document.querySelector('#painel-lateral .painel-topo > button').click()", 0.5)
        conferir(esperar(lambda: not nav("estado").get("visivel"), 4), "fechando o painel, a vista some")
        r = nav("print")
        png = base64.b64decode(r.get("png", "") or "")
        conferir(png[:8] == b"\x89PNG\r\n\x1a\n" and r.get("largura", 0) > 100, f"print com a aba escondida: PNG {r.get('largura')}x{r.get('altura')} ({r.get('erro')})")
        (saida / "navegador-print-escondido.png").write_bytes(png or b"")
        r = nav("rolar", direcao="fim")
        conferir(r.get("y", 0) > 500, f"rolou até o fim com a aba escondida: y={r.get('y')}")
        ref = {e["nome"]: e["ref"] for e in nav("ler")["elementos"]}
        r = clicar(ref["Ir para a segunda página"])
        conferir(r.get("navegou") and r.get("url", "").endswith("/segunda"), f"clique com a aba escondida (método {r.get('metodo')}) seguiu o link")
        r = nav("mostrar", claude=True)
        conferir(r.get("visivel") is True, "'mostrar' traz a aba de volta com a página à vista")

        print("\n[janela minimizada]")
        hwnd = achar_janela(proc.pid)
        ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
        time.sleep(1.5)
        r = nav("print")
        png = base64.b64decode(r.get("png", "") or "")
        conferir(png[:8] == b"\x89PNG\r\n\x1a\n" and r.get("largura", 0) > 100,
                 f"print com a janela minimizada: PNG {r.get('largura')}x{r.get('altura')} ({r.get('erro')} {r.get('detalhe')})")
        (saida / "navegador-print-minimizada.png").write_bytes(png or b"")
        r = nav("ler")
        conferir("segunda página" in r.get("texto", ""), "ler com a janela minimizada")
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        time.sleep(1)

        print("\n[alvos da depuração]")
        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA_DEPURACAO}/json", timeout=5) as rr:
            lista = json.loads(rr.read())
        for p in lista:
            print("   ", p.get("type"), p.get("url", "")[:90])
        jeito_antigo = [p for p in lista if p.get("type") == "page" and "127.0.0.1" in p.get("url", "")]
        conferir(jeito_antigo and jeito_antigo[0]["url"].startswith(origem_app),
                 "o filtro dos testar_janela.py/prints_janela.py ainda acha a página do app primeiro")

        for err in json.loads(js("JSON.stringify(window.__erros || [])") or "[]"):
            if "/api/navegador/localhosts" in err or "404" in err:
                print("   (aviso: a rota /api/navegador/localhosts só existe depois que o integrador importar o navegador.py)")
                continue
            falhas.append("console: " + err)
        por_cima(proc.pid, False)
        print(f"\nprints em {saida}")
        # fecha pelo app (como o botão Sair): o Electron passa pelo before-quit, que fecha a ponte e apaga o arquivo
        ws.cmd("Runtime.evaluate", {"expression": "setTimeout(() => window.clave.sair(), 50); 1"})
        ws.fechar()
        ws = None
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            falhas.append("o Clave não fechou pelo Sair em 15 s")
    finally:
        if ws:
            ws.fechar()
        if proc.poll() is None:
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
        servidor_pagina.shutdown()
        time.sleep(1.5)
    conferir(not (dados / "ponte.json").exists(), "ponte.json apagado ao fechar")
    shutil.rmtree(dados, ignore_errors=True)
    shutil.rmtree(pasta, ignore_errors=True)
    shutil.rmtree(perfil, ignore_errors=True)
    print(f"\n{len(oks)} ok, {len(falhas)} falhas")
    for f in falhas:
        print("FALHA:", f)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
