"""Tira prints das telas do Clave em modo demonstração (Edge sem janela), em vários tamanhos de tela.

Uso: python testes/prints_demo.py <pasta-de-saida> [--porta 8041]
Precisa do servidor de demonstração no ar (servidor.py --demo --sem-senha --porta 8041).
Também lê o console de cada tela e lista os erros.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("cap", RAIZ / "modelo-de-pasta" / ".claude" / "referencias-visuais" / "capturar-print.py")
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)

SAIDA = Path(sys.argv[1] if len(sys.argv) > 1 else "prints")
PORTA = int(sys.argv[sys.argv.index("--porta") + 1]) if "--porta" in sys.argv else 8041
BASE = f"http://127.0.0.1:{PORTA}"
IDIOMA = sys.argv[sys.argv.index("--idioma") + 1] if "--idioma" in sys.argv else "pt-BR"
erros: list[str] = []

_CATALOGO: dict[str, str] = {}
if IDIOMA == "en":
    for _arq in sorted((RAIZ / "app" / "i18n" / "en").glob("*.json")):
        _CATALOGO.update(json.loads(_arq.read_text(encoding="utf-8")))


def T(pt: str) -> str:
    """O texto da tela no idioma dos prints (a chave é o português)."""
    return _CATALOGO.get(pt, pt)


# o que se digita na demonstração; a API de mentira reage às mesmas palavras nos dois idiomas
_MENSAGENS = {
    "api": ("Explique o que é uma API", "Explain what an API is"),
    "fluxo": ("faça isso como um fluxo", "do this as a workflow"),
    "crie": ("crie um arquivo de exemplo", "create an example file"),
    "plano": ("planeje a organização desta pasta", "plan how to organize this folder"),
    "sugestao": ("responda e sugira outra conversa", "answer and suggest another chat"),
}


def M(chave: str) -> str:
    return _MENSAGENS[chave][IDIOMA == "en"]


class Aba:
    def __init__(self):
        self.alvo, url = cap.nova_aba()
        self.ws = cap.WS(url)
        self.ws.cmd("Page.enable")
        self.ws.cmd("Runtime.enable")
        self.ws.cmd("Log.enable")

    def tamanho(self, w, h, celular=False, escuro=False):
        self.ws.cmd("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": celular})
        self.ws.cmd("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": "dark" if escuro else "light"}]})

    def ir(self, rota, espera=1.2):
        self.ws.cmd("Page.navigate", {"url": BASE + "/" + rota})
        time.sleep(espera)

    def js(self, expr, espera=0.0):
        r = self.ws.cmd("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        if "exceptionDetails" in r:
            erros.append(f"JS: {expr[:60]} -> {r['exceptionDetails'].get('text')} {r.get('result', {}).get('description', '')[:200]}")
        time.sleep(espera)
        return r.get("result", {}).get("value")

    def print(self, nome):
        img = self.ws.cmd("Page.captureScreenshot", {"format": "png"})
        (SAIDA / f"{nome}.png").write_bytes(base64.b64decode(img["data"]))
        problemas = self.js("JSON.stringify(window.__erros || [])")
        for p in json.loads(problemas or "[]"):
            erros.append(f"{nome}: {p}")
        vazamento = self.js("document.documentElement.scrollWidth > innerWidth + 1")
        if vazamento:
            erros.append(f"{nome}: a página rola de lado (largura maior que a tela)")


def tour(a: Aba, nome: str, ate_o_passo: int = 0):
    """O tour que abre sozinho na primeira visita a uma tela: print do primeiro passo (e de um do meio) e fecha."""
    if not a.js("!!document.querySelector('.tour-balao')"):
        erros.append(f"{nome}: o tour não abriu")
        return
    a.print(nome)
    if ate_o_passo:
        for _ in range(ate_o_passo - 1):
            a.js("document.querySelector('.tour-acoes .primario').click()", 0.35)
        a.print(nome + "-passo")
    a.js("document.querySelector('.tour-pular').click()", 0.3)


def clicar(texto, seletor="button, a"):
    texto = T(texto)
    return ("(() => { const b = [...document.querySelectorAll('%s')].find(x => x.textContent.trim().startsWith(%s));"
            " if (!b) throw new Error('não achei: ' + %s); b.click(); return true; })()") % (seletor, json.dumps(texto), json.dumps(texto))


GUARDA = ("window.__erros = []; const _e = console.error; console.error = (...a) => { window.__erros.push(a.join(' ')); _e(...a); };"
          "addEventListener('error', (ev) => window.__erros.push(ev.message));")


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    edge = cap.subir_edge()
    try:
        a = Aba()
        a.ws.cmd("Page.addScriptToEvaluateOnNewDocument", {"source": GUARDA})
        a.tamanho(1440, 900)
        # o idioma dos prints e os tours ainda não vistos (cada um abre sozinho na primeira visita à tela dele)
        a.ir("#/novo", 1.0)
        a.js(f"fetch('/api/config',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{idioma:{json.dumps(IDIOMA)},tours_vistos:[]}})}})", 0.3)
        a.ws.cmd("Page.reload")
        time.sleep(1.5)
        if a.js("!!document.querySelector('.janela')"):
            a.print("01-boas-vindas")
            a.js(clicar("Começar"), 0.4)
            a.js(clicar("Continuar"), 0.4)
            a.print("02-teto")
            a.js(clicar("Continuar"), 0.4)
            a.js("(() => { const i = document.querySelector('.janela input'); i.value = 'Ana'; i.dispatchEvent(new Event('input')); })()")
            a.js(clicar("Continuar"), 0.4)
            a.js(clicar("Abrir o Clave"), 0.8)
        time.sleep(0.6)
        tour(a, "03-tour-geral", 6)
        a.print("03-inicio")
        # conversa com resposta de exemplo
        a.js("(() => { const t = document.querySelector('.compositor textarea'); t.value = %s; t.dispatchEvent(new Event('input')); document.querySelector('.enviar').click(); })()" % json.dumps(M("api")), 4.5)
        a.print("04-conversa")
        a.js(clicar("Raciocínio", "summary"), 0.3) if a.js("!!document.querySelector('.pensamento summary')") else None
        a.js("document.querySelector('.compositor .chip:nth-child(3)').click()", 0.4)
        a.print("05-menu-raciocinio")
        a.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}))", 0.2)
        # modo Code: escolher pasta pelo navegador de pastas
        a.ir("#/code", 1.8)
        tour(a, "06-tour-code")
        a.print("06-code-pasta")
        a.ir("#/aprender", 1.0)
        a.print("07-aprender")
        a.ir("#/aprender/excel", 1.5)
        a.print("08-licao-excel")
        a.ir("#/aprender/glossario/json", 1.5)
        a.print("09-glossario-json")
        a.ir("#/config/memoria", 1.5)
        a.print("10-memoria")
        a.ir("#/config/limite", 1.0)
        a.print("11-limite")
        a.ir("#/config/recursos", 1.0)
        a.print("11b-recursos")
        a.ir("#/config/conectores", 1.0)
        a.print("11c-conectores")
        a.ir("#/config/aparencia", 1.0)
        a.print("11d-aparencia")
        # 4.1: o jeito de falar e o exemplo no Haiku (na demonstração, a API de mentira repete as escolhas)
        a.ir("#/config/personalizacao", 1.0)
        a.js("(() => { const s = document.querySelectorAll('.linha-tom select'); s[0].value = 'sincero'; s[0].dispatchEvent(new Event('change')); })()", 0.5)
        a.js("(() => { const s = document.querySelectorAll('.linha-tom select'); s[3].value = 'nenhum'; s[3].dispatchEvent(new Event('change')); })()", 0.5)
        a.js("document.querySelector('.linhas-tom')?.scrollIntoView({block: 'start'})", 0.4)
        a.print("11e-jeito-de-falar")
        a.js(clicar("Ver um exemplo"), 0.5)
        a.js(clicar("Perguntar", ".janela button"), 2.0)
        a.print("11f-exemplo-de-tom")
        a.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}))", 0.3)
        a.js("fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tom:{}})})", 0.3)
        # sistemas do 2.0: fluxos, agentes, plugins, rotinas, permissões e os cartões na conversa
        pasta = tempfile.mkdtemp(prefix="clave-prints-")
        a.js("fetch('/api/permissoes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({escopo:'app',acao:'deny',regra:'Bash(git push *)'})})", 0.3)
        a.js("fetch('/api/permissoes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({escopo:'app',acao:'allow',regra:'Bash(git status *)'})})", 0.3)
        a.js("fetch('/api/rotinas',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nome:'Resumo da manhã',prompt:'Resuma os arquivos novos da pasta e diga o que precisa da minha atenção hoje.',quando:{tipo:'semanal',hora:'08:00',dias:[0,1,2,3,4]},modelo:'claude-sonnet-5-5',teto_usd:0.5})})", 0.5)
        for rota, nome in (("#/fluxos", "30-fluxos"), ("#/fluxos/agentes", "31-agentes"), ("#/plugins", "32-plugins"),
                           ("#/rotinas", "33-rotinas"), ("#/permissoes", "34-permissoes")):
            a.ir(rota, 1.6)
            if rota == "#/fluxos":
                tour(a, "30-tour-fluxos")
            a.print(nome)
        a.ir("#/novo", 1.2)
        a.js("(() => { const t = document.querySelector('.compositor textarea'); t.value = '/'; t.dispatchEvent(new Event('input')); })()", 1.0)
        a.print("35-comandos-de-barra")
        a.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}))", 0.2)
        a.ir("#/novo", 1.2)
        a.js("(() => { const t = document.querySelector('.compositor textarea'); t.value = %s; t.dispatchEvent(new Event('input')); document.querySelector('.enviar').click(); })()" % json.dumps(M("fluxo")), 5.0)
        a.print("36-fluxo-proposta")
        a.js("document.querySelector('.fluxo.proposta button.primario')?.click()", 6.0)
        a.js("document.querySelector('.fluxo .fluxo-etapa.viva')?.setAttribute('open', '')", 0.5)
        a.print("37-fluxo-concluido")
        cid = a.js(f"fetch('/api/conversas',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{modo:'code',pasta:{json.dumps(pasta)}}})}}).then(r=>r.json()).then(d=>d.conversa.id)")
        a.ir(f"#/c/{cid}", 1.5)
        a.js("(() => { const t = document.querySelector('.compositor textarea'); t.value = %s; t.dispatchEvent(new Event('input')); document.querySelector('.enviar').click(); })()" % json.dumps(M("crie")), 3.5)
        a.js("(() => { const b = [...document.querySelectorAll('.aprovacao button')].find(x => x.textContent.startsWith(%s)); b?.click(); })()" % json.dumps(T("Mais opções")), 0.6)
        a.js("(() => { const i = [...document.querySelectorAll('.menu button, .menu [role=menuitem]')].find(x => x.textContent.includes(%s)); i?.click(); })()" % json.dumps(T("Sempre nesta pasta…")), 0.6)
        a.print("38-aprovacao-com-regra")
        a.js("[...document.querySelectorAll('.aprovacao button')].find(x => x.textContent === %s)?.click()" % json.dumps(T("Recusar")), 2.0)
        cid = a.js(f"fetch('/api/conversas',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{modo:'code',pasta:{json.dumps(pasta)}}})}}).then(r=>r.json()).then(d=>d.conversa.id)")
        a.ir(f"#/c/{cid}", 1.5)
        a.js("(() => { const c = [...document.querySelectorAll('.compositor .chip')].find(x => x.textContent.includes(%s)); c?.click(); })()" % json.dumps(T("Perguntar")), 0.4)
        a.js("(() => { const i = [...document.querySelectorAll('.menu button, .menu [role=menuitem]')].find(x => x.textContent.startsWith(%s)); i?.click(); })()" % json.dumps(T("Plano")), 0.3)
        a.js("(() => { const t = document.querySelector('.compositor textarea'); t.value = %s; t.dispatchEvent(new Event('input')); document.querySelector('.enviar').click(); })()" % json.dumps(M("plano")), 3.5)
        a.print("39-plano")
        a.js("[...document.querySelectorAll('.fluxo.plano button')].find(x => x.textContent === %s)?.click()" % json.dumps(T("Continuar planejando")), 2.0)
        # 2.1: preços e planos, painel de uso, ambientes do Code e a sugestão de outra conversa
        a.ir("#/precos", 2.2)
        tour(a, "46-tour-precos")
        a.print("46-precos")
        a.js("document.querySelector('.cartoes-modelos')?.scrollIntoView({block: 'center'})", 0.6)
        a.print("46b-precos-modelos")
        a.js("document.querySelector('.cartao-modelo')?.click()", 0.6)
        a.print("46c-modelo-detalhe")
        a.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape'}))", 0.3)
        a.js("document.querySelector('.estimativa')?.scrollIntoView()", 0.8)
        a.print("47-precos-estimativa")
        a.ir("#/novo", 1.6)
        a.js("document.querySelector('.painel-uso')?.scrollIntoView({block: 'center'})", 0.8)
        a.print("48-painel-uso")
        a.ir("#/code", 1.8)
        a.js("document.querySelector('.painel-ambientes')?.scrollIntoView({block: 'center'})", 0.8)
        a.print("49-code-ambientes")
        a.ir("#/novo", 1.2)
        a.js("(() => { const t = document.querySelector('.compositor textarea'); t.value = %s; t.dispatchEvent(new Event('input')); document.querySelector('.enviar').click(); })()" % json.dumps(M("sugestao")), 4.5)
        a.print("50-sugestao")
        a.ir("#/uso", 1.0)
        a.print("12-uso")
        a.ir("#/projetos", 1.0)
        a.print("13-projetos")
        # tamanhos de tela
        a.ir("#/novo", 1.0)
        for nome, (w, h, cel) in {"ultrawide": (3440, 1440, False), "vertical": (1080, 1920, False), "celular": (390, 844, True)}.items():
            a.tamanho(w, h, cel)
            a.ir("#/novo", 1.2)
            a.print(f"20-{nome}")
        a.tamanho(1440, 900, escuro=True)
        a.ir("#/novo", 1.2)
        a.print("21-escuro")
        cap.fechar_aba(a.alvo)
    finally:
        edge.terminate()
    print("\n".join(erros) if erros else "nenhum erro no console")


if __name__ == "__main__":
    main()
