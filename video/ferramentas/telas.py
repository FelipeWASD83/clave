"""Tira os prints das telas do Clave que os tutoriais mostram, nos dois idiomas, a partir da demonstração.

Sobe a demonstração com as respostas de roteiro (demo_tutorial.py) numa pasta temporária e numa porta só dela, abre
um Edge sem janela, passa pelas telas como uma pessoa passaria (boas-vindas, conversa, troca de modelo, chave, teto,
modo Code arrumando uma pasta Downloads de exemplo) e grava, para cada idioma:

    public/telas/<lingua>/<tela>.png   (1440 × 810 pontos com densidade 2: 2880 × 1620 pixels)
    public/telas/<lingua>/alvos.json   (onde fica cada coisa que a narração cita: [x, y, largura, altura] em pontos)

As cenas leem o alvos.json para pôr o zoom, o cursor e o destaque no lugar certo de cada idioma.

Nada é cobrado e nenhuma chave é usada. A pasta pessoal da demonstração é a pasta temporária (USERPROFILE), para o
modo Code não achar regras nem skills de quem grava. Retoques só nos prints (o app não muda):
- o caminho da pasta temporária aparece como C:\\Users\\Ana\\...;
- o passo da chave e a tela "Conta e chave" aparecem como para quem não está na demonstração (a demonstração
  esconde o campo da chave), com uma chave falsa no campo de senha;
- o custo de cada resposta é recalculado com a tabela de preços do próprio Clave (a demonstração grava zero), e o
  painel "Seu uso" ganha três semanas de uso de exemplo (Haiku e Sonnet, centavos) antes do print dele.

Uso:  python ferramentas/telas.py [--lingua pt-BR|en] [--porta 8051] [--porta-edge 9351]
"""
from __future__ import annotations

import base64
import importlib.util
import json
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

VIDEO = Path(__file__).resolve().parent.parent
CLAVE = VIDEO.parent
PY_CLAVE = CLAVE / ".venv" / "Scripts" / "python.exe"
SAIDA = VIDEO / "public" / "telas"

spec = importlib.util.spec_from_file_location("cap", CLAVE / "modelo-de-pasta" / ".claude" / "referencias-visuais" / "capturar-print.py")
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)

LARGURA, ALTURA, DENSIDADE = 1440, 810, 2
CASA = "C:\\Users\\Ana"  # como a pasta pessoal temporária aparece nos prints

# o que se digita, nos dois idiomas (iguais às lições)
TEXTOS = {
    "presente": {
        "pt-BR": "Me dê 5 ideias de presente de aniversário para uma mãe que gosta de jardinagem, com preço aproximado em reais.",
        "en": "Give me 5 birthday gift ideas for a mom who loves gardening, with approximate prices in dollars.",
    },
    "organizar": {
        "pt-BR": ("Quero organizar esta pasta em subpastas por tipo de arquivo: Documentos (pdf, doc, docx, txt), Imagens "
                  "(jpg, png, gif, webp), Planilhas (xlsx, xls, csv), Instaladores (exe, msi) e Outros. Antes de mexer, "
                  "me mostre quantos arquivos iriam para cada subpasta. Não apague nada."),
        "en": ("I want to organize this folder into subfolders by file type: Documents (pdf, doc, docx, txt), Images "
               "(jpg, png, gif, webp), Spreadsheets (xlsx, xls, csv), Installers (exe, msi) and Other. Before you change "
               "anything, show me how many files would go into each subfolder. Don't delete anything."),
    },
    "pode": {"pt-BR": "Pode fazer.", "en": "Go ahead."},
    "chave": "sk-ant-api03-chave-de-exemplo-que-nao-existe-0000",
}

# a pasta Downloads de exemplo: 23 arquivos soltos (nomes genéricos, vazios)
ARQUIVOS = {
    "pt-BR": ["boleto-outubro.pdf", "contrato-aluguel.pdf", "curriculo.docx", "receita-bolo.txt", "manual-geladeira.pdf",
              "anotacoes.txt", "comprovante.pdf", "foto-praia.jpg", "print-tela.png", "convite.png", "IMG_2041.jpg",
              "IMG_2042.jpg", "meme.gif", "gastos-2026.xlsx", "orcamento-reforma.xlsx", "lista-convidados.csv", "notas.xls",
              "setup-impressora.exe", "instalador-zoom.msi", "VLC-setup.exe", "fotos-viagem.zip", "musica.mp3",
              "documentos-antigos.rar"],
    "en": ["invoice-october.pdf", "lease-contract.pdf", "resume.docx", "cake-recipe.txt", "fridge-manual.pdf", "notes.txt",
           "receipt.pdf", "beach-photo.jpg", "screenshot.png", "invitation.png", "IMG_2041.jpg", "IMG_2042.jpg", "meme.gif",
           "expenses-2026.xlsx", "renovation-budget.xlsx", "guest-list.csv", "grades.xls", "printer-setup.exe",
           "zoom-installer.msi", "VLC-setup.exe", "trip-photos.zip", "song.mp3", "old-documents.rar"],
}

# JavaScript que a página ganha em toda navegação: achar elementos, medir onde estão e esconder o caminho temporário
AJUDA_JS = r"""
window.__v = {
  visivel(e) { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; },
  achar(q) {
    if (typeof q === 'string') { const l = [...document.querySelectorAll(q)].filter((e) => this.visivel(e)); return l[l.length - 1] || null; }
    if (q.css) { const l = [...document.querySelectorAll(q.css)].filter((e) => this.visivel(e)); return l[q.n || 0] || null; }
    const els = [...document.querySelectorAll(q.sel || 'button, a, [role=menuitem], li, span, div')].filter((e) => this.visivel(e));
    const alvo = q.texto.toLowerCase();
    const txt = (e) => (e.innerText || e.textContent || '').trim().toLowerCase().replace(/\s+/g, ' ');
    const iguais = els.filter((e) => txt(e) === alvo);
    if (iguais.length) return iguais[q.ultimo ? iguais.length - 1 : 0];
    const comeca = els.filter((e) => txt(e).startsWith(alvo));
    if (comeca.length) return comeca.sort((a, b) => txt(a).length - txt(b).length)[0];
    return null;
  },
  ret(q) {
    const e = this.achar(q); if (!e) return null;
    const r = e.getBoundingClientRect();
    return [r.x, r.y, r.width, r.height].map((v) => Math.round(v * 10) / 10);
  },
  clicar(q) { const e = this.achar(q); if (!e) throw new Error('não achei: ' + JSON.stringify(q)); e.click(); return true; },
  // tudo o que vem antes do nome da pasta temporária (inteiro ou cortado com "…") vira a pasta pessoal de exemplo
  trocarCaminho(nome, para) {
    const re = new RegExp('[^\\s"\'()<>]*' + nome.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g');
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n; while ((n = w.nextNode())) if (n.nodeValue.includes(nome)) n.nodeValue = n.nodeValue.replace(re, para);
    for (const e of document.querySelectorAll('[title]')) if (e.title.includes(nome)) e.title = e.title.replace(re, para);
  },
};
"""


class Pagina:
    def __init__(self, base: str, lingua: str, raiz: Path):
        self.base = base
        self.lingua = lingua
        self.raiz = raiz
        self.alvos: dict[str, dict] = {}
        self.saida = SAIDA / lingua
        self.saida.mkdir(parents=True, exist_ok=True)
        self.catalogo: dict[str, str] = {}
        if lingua == "en":
            for arq in sorted((CLAVE / "app" / "i18n" / "en").glob("*.json")):
                self.catalogo.update(json.loads(arq.read_text(encoding="utf-8")))
        self.alvo_aba, url = cap.nova_aba()
        self.ws = cap.WS(url)
        for m in ("Page.enable", "Runtime.enable"):
            self.ws.cmd(m)
        self.ws.cmd("Page.addScriptToEvaluateOnNewDocument", {"source": AJUDA_JS})
        self.ws.cmd("Emulation.setDeviceMetricsOverride", {"width": LARGURA, "height": ALTURA, "deviceScaleFactor": DENSIDADE, "mobile": False})
        self.ws.cmd("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": "light"}]})

    def T(self, pt: str) -> str:
        if self.lingua != "en":
            return pt
        if pt not in self.catalogo:
            raise KeyError(f"o catálogo do app não tem: {pt}")
        return self.catalogo[pt]

    def js(self, expr: str, espera: float = 0.0):
        r = self.ws.cmd("Runtime.evaluate", {"expression": expr, "awaitPromise": True, "returnByValue": True})
        if "exceptionDetails" in r:
            desc = r.get("result", {}).get("description", "") or r["exceptionDetails"].get("text", "")
            raise RuntimeError(f"JS falhou: {expr[:120]} -> {desc[:400]}")
        if espera:
            time.sleep(espera)
        return r.get("result", {}).get("value")

    def ir(self, rota: str, espera: float = 1.5):
        self.ws.cmd("Page.navigate", {"url": f"{self.base}/{rota}"})
        time.sleep(espera)

    def recarregar(self, espera: float = 1.8):
        self.ws.cmd("Page.reload")
        time.sleep(espera)

    def esperar(self, cond: str, limite: float = 20.0, o_que: str = ""):
        fim = time.time() + limite
        while time.time() < fim:
            try:
                if self.js(f"!!({cond})"):
                    time.sleep(0.4)
                    return
            except RuntimeError:
                pass
            time.sleep(0.25)
        raise TimeoutError(f"esperei demais por: {o_que or cond}")

    def api(self, metodo: str, rota: str, corpo=None):
        return self.js(f"fetch('/api{rota}', {{method: {json.dumps(metodo)}, headers: {{'Content-Type': 'application/json'}}"
                       + (f", body: JSON.stringify({json.dumps(corpo, ensure_ascii=False)})" if corpo is not None else "")
                       + "}).then((r) => r.json())")

    def clicar(self, texto_pt: str, sel: str | None = None, espera: float = 0.6, traduzir: bool = True):
        q = {"texto": self.T(texto_pt) if traduzir else texto_pt, **({"sel": sel} if sel else {})}
        self.js(f"window.__v.clicar({json.dumps(q, ensure_ascii=False)})", espera)

    def clicar_css(self, sel: str, espera: float = 0.6):
        self.js(f"window.__v.clicar({json.dumps(sel)})", espera)

    def escrever(self, sel: str, texto: str, espera: float = 0.3):
        self.js("(() => { const e = window.__v.achar(%s); e.focus(); e.value = %s; e.dispatchEvent(new Event('input', {bubbles: true})); "
                "e.dispatchEvent(new Event('change', {bubbles: true})); return true; })()" % (json.dumps(sel), json.dumps(texto, ensure_ascii=False)), espera)

    def tecla(self, tecla: str, espera: float = 0.3):
        self.js("document.dispatchEvent(new KeyboardEvent('keydown', {key: %s}))" % json.dumps(tecla), espera)

    def rolar_fim(self, espera: float = 0.6):
        self.js("(() => { const r = document.querySelector('.rolagem'); if (r) r.scrollTop = 1e7; return true; })()", espera)

    def estado(self, codigo: str):
        """Mexe no estado do app (o módulo estado.js é o mesmo que a página usa)."""
        return self.js("(async () => { const m = await import('/js/estado.js'); const estado = m.estado; %s; return true; })()" % codigo)

    def print(self, nome: str, alvos: dict[str, object] | None = None):
        self.js(f"window.__v.trocarCaminho({json.dumps(self.raiz.name)}, {json.dumps(CASA)})")
        self.js("document.activeElement && document.activeElement.blur && document.activeElement.blur()")
        time.sleep(0.35)
        medidas = {}
        for chave, q in (alvos or {}).items():
            opcional = chave.startswith("?")
            chave = chave.lstrip("?")
            if isinstance(q, dict) and "texto" in q:
                q = dict(q)
                if q.pop("traduzir", True):
                    q["texto"] = self.T(q["texto"])
            r = self.js(f"window.__v.ret({json.dumps(q, ensure_ascii=False)})")
            if not r and opcional:
                print(f"  aviso: {self.lingua}/{nome}: sem o alvo opcional {chave}", flush=True)
                continue
            if not r:
                raise RuntimeError(f"{self.lingua}/{nome}: não achei o alvo {chave} ({q})")
            medidas[chave] = r
        img = self.ws.cmd("Page.captureScreenshot", {"format": "png"})
        (self.saida / f"{nome}.png").write_bytes(base64.b64decode(img["data"]))
        self.alvos[nome] = medidas
        print(f"  {self.lingua}/{nome}.png  {len(medidas)} alvos", flush=True)

    def fechar(self):
        (self.saida / "alvos.json").write_text(json.dumps({"largura": LARGURA, "altura": ALTURA, "telas": self.alvos},
                                                          ensure_ascii=False, indent=1), encoding="utf-8")
        self.ws.fechar()
        cap.fechar_aba(self.alvo_aba)


# ---------- custo de verdade e uso de exemplo ----------

def _custo():
    sys.path.insert(0, str(CLAVE / "servidor"))
    import custo  # noqa: E402  (o do próprio Clave: a tabela de preços oficial dele)
    return custo


def recalcular_custos(dados: Path):
    """A demonstração grava custo zero. Aqui cada resposta ganha o custo que o Clave cobraria por aqueles tokens."""
    custo = _custo()
    con = sqlite3.connect(dados / "clave.db")
    for mid, modelo, uso in con.execute("SELECT id, modelo, uso_json FROM mensagens WHERE uso_json IS NOT NULL").fetchall():
        if modelo:
            con.execute("UPDATE mensagens SET custo_usd=? WHERE id=?", (custo.custo_uso(modelo, json.loads(uso))["usd"], mid))
    for uid, modelo, e, ce, cl, s in con.execute("SELECT id, modelo, entrada, cache_escrita, cache_leitura, saida FROM uso").fetchall():
        u = {"input_tokens": e, "cache_creation_input_tokens": ce, "cache_read_input_tokens": cl, "output_tokens": s}
        con.execute("UPDATE uso SET custo_usd=? WHERE id=?", (custo.custo_uso(modelo or "claude-haiku-5-5", u)["usd"], uid))
    con.commit()
    con.close()


def semear_uso(dados: Path):
    """Três semanas de uso de exemplo antes de hoje, para o painel "Seu uso" mostrar o que ele mostra com o tempo."""
    custo = _custo()
    rng = random.Random(7)
    hoje = date.today()
    con = sqlite3.connect(dados / "clave.db")
    for atras in range(1, 22):
        dia = hoje - timedelta(days=atras)
        if atras > 6 and rng.random() < 0.3:  # os últimos 6 dias seguidos; antes, alguns dias de folga
            continue
        pedidos = [("claude-haiku-5-5", rng.randint(6000, 9500), rng.randint(150, 700)) for _ in range(rng.randint(2, 6))]
        pedidos += [("claude-sonnet-5-5", rng.randint(7000, 12000), rng.randint(300, 900)) for _ in range(rng.choice([0, 0, 1, 1, 2]))]
        for modelo, entrada, saida in pedidos:
            quando = datetime.combine(dia, datetime.min.time()) + timedelta(hours=rng.randint(9, 21), minutes=rng.randint(0, 59))
            usd = custo.custo_uso(modelo, {"input_tokens": entrada, "output_tokens": saida})["usd"]
            con.execute("INSERT INTO uso (criado_em, conversa_id, mensagem_id, modelo, origem, entrada, cache_escrita, cache_leitura, "
                        "saida, buscas, custo_usd, estimado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (quando.timestamp(), None, None, modelo, "chat", entrada, 0, 0, saida, 0, usd, 0))
    con.commit()
    con.close()


# ---------- o roteiro das telas ----------

def roteiro(p: Pagina, dados: Path, pasta: Path):
    L = p.lingua
    vistos = {"tours_vistos": ["geral", "code", "precos", "fluxos"],
              "modelos_vistos": [k for k in json.loads((CLAVE / "servidor" / "lancamentos.json").read_text(encoding="utf-8")) if not k.startswith("_")]}
    p.ir("#/novo", 1.5)
    p.api("POST", "/config", {"idioma": L, "configurado": False, "nome": "", "teto_mensal_usd": 20, **vistos})
    p.recarregar()
    p.esperar("document.querySelector('.boas-vindas')", 10, "boas-vindas")
    janela_botao = ".janela button"

    # --- boas-vindas: o que é, a chave, o teto, o nome, pronto
    p.print("boas-1-inicio", {"janela": ".janela", "comecar": {"texto": "Começar", "sel": janela_botao}})
    p.estado("estado.info.demo = false; estado.info.tem_chave = false")
    p.clicar("Começar", janela_botao)
    p.print("boas-2-chave-vazia", {"janela": ".janela", "campo": ".janela input", "passos": ".janela ol"})
    p.escrever(".janela input", TEXTOS["chave"])
    p.print("boas-2-chave", {"janela": ".janela", "campo": ".janela input", "continuar": {"texto": "Continuar", "sel": janela_botao}})
    p.estado("estado.info.demo = true")
    p.clicar("Pular", janela_botao)
    p.print("boas-3-teto", {"janela": ".janela", "opcoes": ".opcoes-teto", "vinte": ".opcoes-teto button[aria-pressed=true]",
                            "continuar": {"texto": "Continuar", "sel": janela_botao}})
    p.clicar("Continuar", janela_botao)
    p.escrever(".janela input", "Ana")
    p.print("boas-4-nome", {"janela": ".janela", "nome": ".janela input", "sobre": ".janela textarea",
                            "continuar": {"texto": "Continuar", "sel": janela_botao}})
    p.clicar("Continuar", janela_botao)
    p.print("boas-5-pronto", {"janela": ".janela", "abrir": {"texto": "Abrir o Clave", "sel": janela_botao}})
    p.clicar("Abrir o Clave", janela_botao, 1.5)
    p.recarregar()  # o estado do app volta ao da demonstração (o passo da chave mexeu nele)

    # --- primeira conversa: escrever, trocar o modelo, enviar, o custo, o painel de uso
    menu_item = ".menu button, .menu [role=menuitem]"
    p.ir("#/novo", 1.8)
    p.print("conversa-1-inicio", {"nova": {"texto": "Nova conversa", "sel": ".lateral button, .lateral a"},
                                  "caixa": ".compositor textarea", "modelo": ".compositor .chip:nth-child(2)",
                                  "tinteiro": ".lateral .tinteiro"})
    p.escrever(".compositor textarea", TEXTOS["presente"][L], 0.5)
    p.print("conversa-2-digitada", {"caixa": ".compositor textarea", "enviar": ".compositor .enviar",
                                    "modelo": ".compositor .chip:nth-child(2)"})
    p.clicar_css(".compositor .chip:nth-child(2)", 0.6)
    p.print("conversa-3-modelos", {"menu": ".menu", "modelo": ".compositor .chip:nth-child(2)",
                                   "haiku": {"texto": "Haiku 5.5", "sel": menu_item, "traduzir": False},
                                   "sonnet": {"texto": "Sonnet 5.5", "sel": menu_item, "traduzir": False},
                                   "opus": {"texto": "Opus 5.5", "sel": menu_item, "traduzir": False}})
    p.clicar("Haiku 5.5", menu_item, 0.6, traduzir=False)
    p.print("conversa-4-haiku", {"caixa": ".compositor textarea", "enviar": ".compositor .enviar",
                                 "modelo": ".compositor .chip:nth-child(2)"})
    p.clicar_css(".compositor .enviar", 0.5)
    p.esperar("location.hash.startsWith('#/c/') && [...document.querySelectorAll('.mensagens .meta')].some((e) => e.textContent.includes('Haiku'))",
              30, "resposta da conversa")
    time.sleep(1.5)
    recalcular_custos(dados)
    p.recarregar()
    p.esperar("document.querySelector('.mensagens')", 10)
    time.sleep(1.0)
    p.js("document.querySelector('.rolagem').scrollTop = 0", 0.5)
    p.print("conversa-5-resposta", {"pergunta": ".msg-usuario .balao", "titulo": ".topo"})
    p.rolar_fim()
    p.print("conversa-6-custo", {"meta": {"texto": "Haiku 5.5", "sel": ".mensagens .meta", "traduzir": False},
                                 "regua": ".regua", "gasto": ".topo .meta", "tinteiro": ".lateral .tinteiro"})
    semear_uso(dados)
    p.ir("#/novo", 0.5)
    p.recarregar()  # o tinteiro da barra lê o gasto ao abrir
    p.js("document.querySelector('.painel-uso')?.scrollIntoView({block: 'center'})", 0.8)
    p.print("conversa-7-painel-uso", {"painel": ".painel-uso", "cartoes": ".painel-uso .painel-blocos", "mapa": ".painel-uso .mapa-calor",
                                      "sete": ".painel-uso .sete-dias",
                                      **{f"bloco{i}": f".painel-uso .painel-bloco:nth-child({i})" for i in range(1, 5)}})

    # --- chave e teto em Configurações
    p.ir("#/novo", 1.5)
    p.print("conta-0-antes", {"configuracoes": {"texto": "Configurações", "sel": ".lateral a, .lateral button"}})
    p.ir("#/config/limite", 1.2)
    p.estado("estado.info.demo = false; estado.info.tem_chave = false")
    p.ir("#/config/conta", 1.2)
    p.print("conta-1-vazia", {"configuracoes": {"texto": "Configurações", "sel": ".lateral a, .lateral button"},
                              "aba": {"texto": "Conta e chave", "sel": "a, button"}, "campo": "input[type=password]",
                              "salvar": {"texto": "Conferir e salvar", "sel": "button"}})
    p.escrever("input[type=password]", TEXTOS["chave"])
    p.print("conta-2-colada", {"campo": "input[type=password]", "salvar": {"texto": "Conferir e salvar", "sel": "button"}})
    p.estado("estado.info.tem_chave = true; estado.info.chave = 'sk-ant-•••••'")
    p.ir("#/config/limite", 0.8)
    p.ir("#/config/conta", 1.2)
    p.print("conta-3-salva", {"salva": {"texto": "Chave salva", "sel": ".item-lista"}})
    p.estado("estado.info.demo = true")
    p.ir("#/config/limite", 1.2)
    p.print("limite-1", {"aba": {"texto": "Limite de gasto", "sel": "a, button"}, "teto": {"css": "input[type=number]", "n": 0},
                         "ao_atingir": "select", "?gasto": ".item-lista"})

    # --- primeira automação: Novo trabalho no Code, a pasta Downloads, o plano, o OK e o desfazer
    p.ir("#/novo", 0.5)
    p.recarregar()  # o estado do app volta ao da demonstração (a tela da chave mexeu nele)
    p.print("code-0-antes", {"novo": {"texto": "Novo trabalho no Code", "sel": ".lateral button, .lateral a"}})
    p.ir("#/code", 1.8)
    p.js("(() => { const b = document.querySelector('.painel-uso button[aria-label]'); if (b) b.click(); return true; })()", 0.8)
    p.recarregar()  # o painel fica escondido e o aviso "Painel escondido" some
    p.js("document.querySelector('.painel-ambientes')?.scrollIntoView({block: 'center'})", 0.6)
    p.print("code-1-inicio", {"novo": {"texto": "Novo trabalho no Code", "sel": ".lateral button, .lateral a"},
                              "escolher": ".ambiente-escolher", "painel": ".painel-ambientes"})
    p.clicar_css(".ambiente-escolher", 0.6)
    p.print("code-2-menu", {"outra": {"texto": "Outra pasta…", "sel": menu_item}, "escolher": ".ambiente-escolher"})
    # no app, "Outra pasta…" abre a janela de pastas do Windows; aqui ela devolve a pasta de exemplo
    p.js(f"window.clave = Object.assign(window.clave || {{}}, {{escolherPasta: async () => {json.dumps(str(pasta))}}})")
    p.clicar("Outra pasta…", menu_item, 1.2)
    p.js("document.querySelector('.compositor')?.scrollIntoView({block: 'center'})", 0.5)
    p.print("code-3-pasta", {"permissao": {"texto": "Perguntar", "sel": ".compositor .chip"}, "caixa": ".compositor textarea",
                             "?selo": {"texto": CASA + "\\Downloads", "sel": "span, div, button", "traduzir": False},
                             "?ambiente": ".painel-ambientes .ambiente.atual"})
    p.clicar("Perguntar", ".compositor .chip", 0.6)
    p.print("code-3b-permissoes", {"menu": ".menu", "perguntar": {"texto": "Perguntar", "sel": menu_item},
                                   "permissao": {"texto": "Perguntar", "sel": ".compositor .chip"}})
    p.tecla("Escape", 0.4)
    p.escrever(".compositor textarea", TEXTOS["organizar"][L], 0.6)
    p.print("code-4-pedido", {"caixa": ".compositor textarea", "enviar": ".compositor .enviar"})
    p.clicar_css(".compositor .enviar", 0.5)
    p.esperar("[...document.querySelectorAll('.mensagens table')].length > 0 && !document.querySelector('.compositor .enviar.parar')",
              40, "a contagem por subpasta")
    time.sleep(1.5)
    p.rolar_fim()
    p.print("code-5-plano", {"tabela": ".mensagens table", "tarefas": ".tarefas",
                             "passo": {"texto": "Olhou a pasta", "sel": ".mensagens summary, .mensagens button, .mensagens div"}})
    p.escrever(".compositor textarea", TEXTOS["pode"][L], 0.4)
    p.print("code-5b-pode", {"caixa": ".compositor textarea", "enviar": ".compositor .enviar"})
    p.clicar_css(".compositor .enviar", 0.5)
    p.esperar("document.querySelector('.aprovacao')", 30, "o cartão de aprovação do script")
    time.sleep(1.0)
    p.rolar_fim()
    p.print("code-6-aprova-script", {"cartao": ".aprovacao", "permitir": {"texto": "Permitir", "sel": ".aprovacao button"},
                                     "recusar": {"texto": "Recusar", "sel": ".aprovacao button"},
                                     "mais": {"texto": "Mais opções", "sel": ".aprovacao button"}, "previa": ".aprovacao pre"})
    p.clicar("Permitir", ".aprovacao button", 1.0)
    p.esperar("[...document.querySelectorAll('.aprovacao')].some((c) => c.querySelector('pre') && c.querySelector('pre').textContent.includes('powershell'))",
              30, "o cartão de aprovação do comando")
    time.sleep(1.0)
    p.rolar_fim()
    p.print("code-7-aprova-comando", {"cartao": ".aprovacao", "permitir": {"texto": "Permitir", "sel": ".aprovacao button"},
                                      "recusar": {"texto": "Recusar", "sel": ".aprovacao button"}, "previa": ".aprovacao pre"})
    p.clicar("Permitir", ".aprovacao button", 1.0)
    p.esperar("[...document.querySelectorAll('.mensagens button')].some((b) => b.textContent.includes(%s))" % json.dumps(p.T("Desfazer mudanças")),
              40, "o botão Desfazer mudanças")
    time.sleep(1.5)
    recalcular_custos(dados)
    p.recarregar()
    p.esperar("document.querySelector('.mensagens')", 10)
    p.rolar_fim()
    p.print("code-8-pronto", {"desfazer": {"texto": "Desfazer mudanças", "sel": ".mensagens button", "ultimo": True},
                              "pasta": {"texto": "Downloads", "sel": ".topo button, .topo a, .topo span", "traduzir": False},
                              "fim": ".mensagens .msg-claude", "caixa": ".compositor textarea"})


def matar_arvore(proc: subprocess.Popen | None):
    if proc and proc.poll() is None:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)


def subir_demo(porta: int, raiz: Path, dados: Path, pasta: Path) -> subprocess.Popen:
    # a pasta pessoal da demonstração é a temporária: o modo Code não acha CLAUDE.md nem skills de quem grava
    env = dict(os.environ, CLAVE_VIDEO_DOWNLOADS=str(pasta), USERPROFILE=str(raiz), PYTHONIOENCODING="utf-8")
    proc = subprocess.Popen([str(PY_CLAVE), str(VIDEO / "ferramentas" / "demo_tutorial.py"), "--porta", str(porta), "--dados", str(dados)],
                            cwd=str(CLAVE), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{porta}/", timeout=1).read()
            return proc
        except Exception:
            if proc.poll() is not None:
                raise RuntimeError("a demonstração não subiu")
            time.sleep(0.25)
    matar_arvore(proc)
    raise RuntimeError("a demonstração não respondeu")


def main():
    args = sys.argv[1:]
    linguas = [args[args.index("--lingua") + 1]] if "--lingua" in args else ["pt-BR", "en"]
    porta = int(args[args.index("--porta") + 1]) if "--porta" in args else 8051
    cap.PORT = int(args[args.index("--porta-edge") + 1]) if "--porta-edge" in args else 9351
    for L in linguas:
        shutil.rmtree(SAIDA / L, ignore_errors=True)  # nada de print velho de uma rodada anterior
        raiz = Path(tempfile.mkdtemp(prefix="clave-video-"))
        cap.PROFILE = str(raiz / "edge")
        dados = raiz / "dados"
        pasta = raiz / "Downloads"
        pasta.mkdir(parents=True)
        for nome in ARQUIVOS[L]:
            (pasta / nome).write_bytes(b"")
        os.environ["CLAVE_DADOS"] = str(dados)  # para o custo.py do Clave, importado aqui
        demo = edge = None
        try:
            demo = subir_demo(porta, raiz, dados, pasta)
            edge = cap.subir_edge()
            print(f"{L}: demonstração na {porta}, Edge na {cap.PORT}", flush=True)
            p = Pagina(f"http://127.0.0.1:{porta}", L, raiz)
            try:
                roteiro(p, dados, pasta)
            finally:
                p.fechar()
        finally:
            matar_arvore(edge)
            matar_arvore(demo)
            time.sleep(1.0)
            shutil.rmtree(raiz, ignore_errors=True)


if __name__ == "__main__":
    main()
