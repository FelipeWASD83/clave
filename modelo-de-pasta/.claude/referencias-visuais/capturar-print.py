# -*- coding: utf-8 -*-
"""Captura prints de referencia visual via Edge headless + CDP (WebSocket na mao).

Uso: python capturar.py lista.json pasta_destino
lista.json = [{"arquivo":"nome.png","url":"https://...","y":0,"espera":6}, ...]
"""
import base64, json, os, secrets, socket, struct, subprocess, sys, tempfile, time
from urllib.request import Request, urlopen

EDGE = next((p for p in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                          r"C:\Program Files\Microsoft\Edge\Application\msedge.exe") if os.path.exists(p)),
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
PORT = 9333
PROFILE = os.path.join(tempfile.gettempdir(), "edgeprof-cdp")
LARGURA, ALTURA = 1440, 900

REVEAL_JS = r"""
new Promise(async (resolve) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  try {
    const st = document.createElement('style');
    st.textContent = '*,*::before,*::after{animation-delay:0s!important;transition-delay:0s!important}';
    document.head.appendChild(st);
  } catch (e) {}
  const pats = ['cookie','consent','gdpr','onetrust','privacy-banner','cmp-'];
  let escondidos = 0;
  document.querySelectorAll('div,section,aside,dialog,iframe,form').forEach(el => {
    let cls = '';
    try {
      cls = typeof el.className === 'string' ? el.className : (el.className && el.className.baseVal) || '';
    } catch (e) {}
    const s = ((el.id || '') + ' ' + cls).toLowerCase();
    if (!pats.some(p => s.includes(p))) return;
    let pos = '';
    try { pos = getComputedStyle(el).position; } catch (e) {}
    if (pos !== 'fixed' && pos !== 'sticky') return;
    const r = el.getBoundingClientRect();
    if (r.width > 200 && r.height > 50) { el.style.display = 'none'; escondidos++; }
  });
  const alturaTotal = document.documentElement.scrollHeight;
  const passo = Math.max(400, Math.round(window.innerHeight * 0.8));
  const limite = Math.min(alturaTotal, window.innerHeight * 8);
  for (let y = 0; y < limite; y += passo) { window.scrollTo(0, y); await sleep(350); }
  window.scrollTo(0, 0);
  await sleep(1400);
  resolve(JSON.stringify({altura: alturaTotal, banners: escondidos}));
})
"""


CLIQUE_JS = r"""
(() => {
  const alvos = %s;
  const els = Array.from(document.querySelectorAll('button,a,[role=button],div,span,li'));
  for (const alvo of alvos) {
    const el = els.find(e => {
      const t = (e.innerText || '').trim().toLowerCase();
      if (t !== alvo) return false;
      const r = e.getBoundingClientRect();
      return r.width > 20 && r.width < 500 && r.height > 10 && r.height < 200;
    });
    if (el) { el.click(); return 'clicou:' + alvo; }
  }
  return 'nao achou';
})()
"""


class WS:
    """Cliente WebSocket minimo, so o suficiente para falar CDP."""

    def __init__(self, url):
        resto = url.split("://", 1)[1]
        hostport, _, caminho = resto.partition("/")
        caminho = "/" + caminho
        host, porta = hostport.split(":")
        self.s = socket.create_connection((host, int(porta)), timeout=120)
        self.s.settimeout(120)
        chave = base64.b64encode(secrets.token_bytes(16)).decode()
        req = ("GET %s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
               "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (caminho, hostport, chave))
        self.s.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            pedaco = self.s.recv(4096)
            if not pedaco:
                raise RuntimeError("handshake falhou")
            buf += pedaco
        cab, _, sobra = buf.partition(b"\r\n\r\n")
        if b"101" not in cab.split(b"\r\n")[0]:
            raise RuntimeError("handshake recusado: %r" % cab[:120])
        self.buf = sobra
        self.id = 0

    def _ler(self, n):
        while len(self.buf) < n:
            pedaco = self.s.recv(65536)
            if not pedaco:
                raise RuntimeError("conexao fechada")
            self.buf += pedaco
        saida, self.buf = self.buf[:n], self.buf[n:]
        return saida

    def _enviar_frame(self, dados):
        cab = bytearray([0x81])
        n = len(dados)
        if n < 126:
            cab.append(0x80 | n)
        elif n < 65536:
            cab.append(0x80 | 126)
            cab += struct.pack(">H", n)
        else:
            cab.append(0x80 | 127)
            cab += struct.pack(">Q", n)
        mascara = secrets.token_bytes(4)
        cab += mascara
        corpo = bytes(b ^ mascara[i % 4] for i, b in enumerate(dados))
        self.s.sendall(bytes(cab) + corpo)

    def _ler_mensagem(self):
        partes = []
        while True:
            b1, b2 = self._ler(2)
            fim = b1 & 0x80
            opcode = b1 & 0x0F
            n = b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._ler(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._ler(8))[0]
            carga = self._ler(n) if n else b""
            if opcode == 0x9:
                self.s.sendall(b"\x8a\x80" + secrets.token_bytes(4))
                continue
            if opcode == 0x8:
                raise RuntimeError("servidor fechou a conexao")
            partes.append(carga)
            if fim:
                break
        return b"".join(partes).decode("utf-8", "replace")

    def cmd(self, metodo, params=None, timeout=120):
        self.id += 1
        meu = self.id
        self._enviar_frame(json.dumps({"id": meu, "method": metodo, "params": params or {}}).encode())
        limite = time.time() + timeout
        while time.time() < limite:
            msg = json.loads(self._ler_mensagem())
            if msg.get("id") == meu:
                if "error" in msg:
                    raise RuntimeError("%s: %s" % (metodo, msg["error"]))
                return msg.get("result", {})
        raise TimeoutError(metodo)

    def fechar(self):
        try:
            self.s.close()
        except Exception:
            pass


def subir_edge():
    args = [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", "--disable-sync", "--mute-audio",
            "--disable-features=Translate,MediaRouter",
            "--remote-debugging-port=%d" % PORT, "--user-data-dir=%s" % PROFILE,
            "--window-size=%d,%d" % (LARGURA, ALTURA), "about:blank"]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            urlopen("http://127.0.0.1:%d/json/version" % PORT, timeout=1).read()
            return proc
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Edge nao subiu na porta %d" % PORT)


def nova_aba():
    url = "http://127.0.0.1:%d/json/new?about:blank" % PORT
    try:
        req = Request(url, method="PUT")
        dados = json.loads(urlopen(req, timeout=20).read().decode())
    except Exception:
        dados = json.loads(urlopen(url, timeout=20).read().decode())
    return dados["id"], dados["webSocketDebuggerUrl"]


def fechar_aba(alvo):
    try:
        urlopen("http://127.0.0.1:%d/json/close/%s" % (PORT, alvo), timeout=10).read()
    except Exception:
        pass


def capturar(item, destino):
    alvo, wsurl = nova_aba()
    ws = WS(wsurl)
    info = {}
    try:
        ws.cmd("Page.enable")
        ws.cmd("Emulation.setDeviceMetricsOverride",
               {"width": LARGURA, "height": ALTURA, "deviceScaleFactor": 1, "mobile": False})
        try:
            ws.cmd("Page.navigate", {"url": item["url"]}, timeout=90)
        except Exception as e:
            info["nav"] = str(e)[:120]
        time.sleep(item.get("espera", 6))
        if item.get("clique"):
            js = CLIQUE_JS % json.dumps([t.lower() for t in item["clique"]])
            try:
                r = ws.cmd("Runtime.evaluate", {"expression": js, "returnByValue": True}, timeout=60)
                info["clique"] = r.get("result", {}).get("value")
            except Exception as e:
                info["clique_erro"] = str(e)[:120]
            time.sleep(item.get("espera_clique", 8))
        try:
            r = ws.cmd("Runtime.evaluate",
                       {"expression": REVEAL_JS, "awaitPromise": True, "returnByValue": True}, timeout=120)
            info["reveal"] = r.get("result", {}).get("value")
        except Exception as e:
            info["reveal_erro"] = str(e)[:120]
        y = item.get("y", 0)
        if y:
            try:
                ws.cmd("Runtime.evaluate",
                       {"expression": "window.scrollTo(0,%d); 'ok'" % y, "returnByValue": True})
            except Exception:
                pass
            time.sleep(2.5)
        else:
            time.sleep(1.0)
        formato = "jpeg" if item["arquivo"].lower().endswith(".jpg") else "png"
        params = {"format": formato, "captureBeyondViewport": False}
        if formato == "jpeg":
            params["quality"] = 88
        shot = ws.cmd("Page.captureScreenshot", params, timeout=120)
        caminho = os.path.join(destino, item["arquivo"])
        with open(caminho, "wb") as f:
            f.write(base64.b64decode(shot["data"]))
        info["bytes"] = os.path.getsize(caminho)
    finally:
        ws.fechar()
        fechar_aba(alvo)
    return info


def main():
    lista = json.load(open(sys.argv[1], encoding="utf-8"))
    destino = sys.argv[2]
    os.makedirs(destino, exist_ok=True)
    proc = subir_edge()
    try:
        for item in lista:
            t0 = time.time()
            try:
                info = capturar(item, destino)
                print("OK    %-40s %6.1fs  %s" % (item["arquivo"], time.time() - t0,
                                                  json.dumps(info, ensure_ascii=False)), flush=True)
            except Exception as e:
                print("FALHA %-40s %6.1fs  %s" % (item["arquivo"], time.time() - t0, str(e)[:160]), flush=True)
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
