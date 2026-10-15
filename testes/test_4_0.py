"""4.0.0: Word, e-mail (IMAP e SMTP simulados), mostrar arquivo, /compact e importar do Claude ou do ChatGPT."""
import email
import email.policy
import shutil
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path
from types import SimpleNamespace

import base  # noqa: F401
import anexos
import banco
import compactar
import config
import execucao
import importar
import pedido
import rotinas
import segredos
from ferramentas import code as fc
from ferramentas import email as femail
from ferramentas import memoria
from ferramentas import word


def contexto(raiz: Path) -> fc.Contexto:
    return fc.Contexto(raiz=raiz.resolve(), protegidos=[".env"], execucao_id=banco.novo_id(), conversa_id="c-4",
                       emitir=lambda ev: None)


class TestWord(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-word-"))

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_criar_ler_e_trocar(self):
        p = self.pasta / "proposta.docx"
        word.criar(p, "# Proposta para CLIENTE\n\nValor total: **R$ 1.200,00**\n\n- Item um\n\n| Item | Qtd |\n|---|---|\n| Caixa | 10 |")
        texto = word.ler(p)
        self.assertIn("# Proposta para CLIENTE", texto)
        self.assertIn("R$ 1.200,00", texto)
        self.assertIn("| Caixa | 10 |", texto)
        r = word.trocar(p, [{"de": "CLIENTE", "para": "Padaria Sol & Cia"}, {"de": "não existe", "para": "x"}])
        self.assertIn("1 troca", r)
        self.assertIn("não existe", r)
        self.assertIn("Padaria Sol & Cia", word.ler(p))

    def test_arquivo_que_nao_e_docx(self):
        p = self.pasta / "falso.docx"
        p.write_text("oi", encoding="utf-8")
        with self.assertRaises(word.ErroWord):
            word.ler(p)

    def test_ferramentas_do_code(self):
        ctx = contexto(self.pasta)
        fc.executar("word_criar", {"caminho": "a.docx", "conteudo": "Olá NOME"}, ctx)
        fc.executar("word_alterar", {"caminho": "a.docx", "trocas": [{"de": "NOME", "para": "Ana"}], "saida": "b.docx"}, ctx)
        self.assertIn("NOME", fc.executar("word_ler", {"caminho": "a.docx"}, ctx))   # a original ficou intacta
        self.assertIn("Ana", fc.executar("word_ler", {"caminho": "b.docx"}, ctx))


class _IMAPFalso:
    """Imita o imaplib.IMAP4_SSL com duas mensagens; a segunda tem anexo."""
    caixa: dict = {}

    def __init__(self, host, porta, timeout=None):
        self.host = host

    def login(self, usuario, senha):
        if senha != "senha-de-app":
            import imaplib
            raise imaplib.IMAP4.error("AUTHENTICATIONFAILED")

    def select(self, pasta, readonly=False):
        return "OK", [str(len(self.caixa)).encode()]

    def uid(self, comando, *args):
        if comando == "search":
            return "OK", [b" ".join(self.caixa)]
        uid = args[0] if isinstance(args[0], bytes) else str(args[0]).encode()
        bruto = self.caixa.get(uid)
        if bruto is None:
            return "OK", [None]
        if "HEADER.FIELDS" in args[1]:
            msg = email.message_from_bytes(bruto, policy=email.policy.default)
            cab = f"From: {msg['From']}\r\nSubject: {msg['Subject']}\r\nDate: {msg['Date']}\r\n\r\n".encode()
            return "OK", [(b"1 (UID " + uid + b" FLAGS (\\Seen) BODY[HEADER.FIELDS (FROM SUBJECT DATE)] {10}", cab),
                          (b" BODY[TEXT]<0> {10}", b"Corpo do pedido"), b")"]
        return "OK", [(b"1 (UID " + uid + b" BODY[] {10}", bruto), b")"]

    def logout(self):
        pass


class TestEmail(unittest.TestCase):
    def setUp(self):
        m1 = EmailMessage()
        m1["From"], m1["To"], m1["Subject"], m1["Date"] = "Ana <ana@cliente.com>", "eu@empresa.com", "Pedido 123", "Mon, 12 Oct 2026 10:00:00 -0300"
        m1.set_content("Quero 10 caixas.")
        m2 = EmailMessage()
        m2["From"], m2["To"], m2["Subject"], m2["Date"] = "Beto <beto@cliente.com>", "eu@empresa.com", "Pedido 124", "Tue, 13 Oct 2026 10:00:00 -0300"
        m2["Message-ID"] = "<abc@cliente.com>"
        m2.set_content("Segue a planilha.")
        m2.add_attachment(b"conteudo", maintype="application", subtype="octet-stream", filename="pedido.csv")
        _IMAPFalso.caixa = {b"1": m1.as_bytes(), b"2": m2.as_bytes()}
        self._imap, self._smtp = femail.imaplib.IMAP4_SSL, femail.smtplib.SMTP_SSL
        femail.imaplib.IMAP4_SSL = _IMAPFalso
        self.enviados = []
        teste = self

        class SMTPFalso:
            def __init__(self, host, porta, timeout=None):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def login(self, u, s):
                pass

            def send_message(self, msg):
                teste.enviados.append(msg)
        femail.smtplib.SMTP_SSL = SMTPFalso
        config.salvar({"email": {"tipo": "gmail", "ligado": True, "endereco": "eu@empresa.com", "imap": "imap.gmail.com",
                                 "imap_porta": 993, "smtp": "smtp.gmail.com", "smtp_porta": 465}})
        segredos.guardar(femail.SEGREDO, "senha-de-app")
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-email-"))

    def tearDown(self):
        femail.imaplib.IMAP4_SSL, femail.smtplib.SMTP_SSL = self._imap, self._smtp
        segredos.apagar(femail.SEGREDO)
        config.salvar({"email": {}})
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_ler_lista_e_mensagem(self):
        self.assertTrue(femail.ligado())
        lista = femail.ler({"limite": 10})
        self.assertIn("Pedido 124", lista)
        self.assertIn("Pedido 123", lista)
        inteira = femail.ler({"id": "2"})
        self.assertIn("Segue a planilha.", inteira)
        self.assertIn("pedido.csv", inteira)

    def test_salvar_anexo_e_enviar_com_resposta(self):
        ctx = contexto(self.pasta)
        fc.executar("email_salvar_anexo", {"id": "2", "anexo": "pedido.csv"}, ctx)
        self.assertEqual((self.pasta / "pedido.csv").read_bytes(), b"conteudo")
        r = femail.enviar({"para": "beto@cliente.com", "assunto": "Re: Pedido 124", "corpo": "Recebido!", "responder_a": "2"},
                          [self.pasta / "pedido.csv"])
        self.assertIn("beto@cliente.com", r)
        msg = self.enviados[-1]
        self.assertEqual(msg["In-Reply-To"], "<abc@cliente.com>")
        self.assertEqual([a.get_filename() for a in msg.iter_attachments()], ["pedido.csv"])

    def test_senha_errada_e_previa(self):
        segredos.guardar(femail.SEGREDO, "errada")
        with self.assertRaises(femail.ErroEmail):
            femail.ler({})
        previa = femail.previa({"para": "a@b.com", "assunto": "Oi", "corpo": "Texto"})
        self.assertIn("a@b.com", previa)
        self.assertTrue(previa.endswith("Texto"))


class TestMostrarArquivo(unittest.TestCase):
    def test_copia_e_tipo(self):
        pasta = Path(tempfile.mkdtemp(prefix="clave-mostrar-"))
        try:
            (pasta / "print.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
            (pasta / "video.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"0" * 20)
            ctx = contexto(pasta)
            ctx.ferramenta_id = "toolu_1"
            r = fc.executar("mostrar_arquivo", {"caminho": "print.png", "legenda": "o print"}, ctx)
            aid = r.split("(id ")[1].rstrip(").")
            self.assertEqual(banco.anexo(aid)["tipo"], "image/png")
            r2 = fc.executar("mostrar_arquivo", {"caminho": "video.mp4"}, ctx)
            self.assertEqual(banco.anexo(r2.split("(id ")[1].rstrip(")."))["tipo"], "video/mp4")
            with self.assertRaises(fc.ErroFerramenta):
                fc.executar("mostrar_arquivo", {"caminho": "nao-existe.png"}, ctx)
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


class _ClienteFalso:
    def __init__(self):
        self.pedidos = []
        bloco = SimpleNamespace(model_dump=lambda exclude_none=True: {"type": "compaction", "content": "Resumo: pediu X.", "signature": "sig"})
        uso = SimpleNamespace(model_dump=lambda exclude_none=True: {"input_tokens": 0, "output_tokens": 0,
                                                                    "iterations": [{"type": "compaction", "input_tokens": 100, "output_tokens": 20}]})
        resposta = SimpleNamespace(stop_reason="compaction", content=[bloco], usage=uso)
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: (self.pedidos.append(kw), resposta)[1]))


class TestCompactar(unittest.TestCase):
    def test_compactar_e_continuar_do_resumo(self):
        conv = banco.criar_conversa("chat")
        cid = conv["id"]
        pai = None
        for papel, texto in (("user", "Oi"), ("assistant", "Olá"), ("user", "Faça X"), ("assistant", "Feito")):
            pai = banco.adicionar_mensagem(cid, pai, papel, [{"type": "text", "text": texto}])["id"]
        falso = _ClienteFalso()
        original = execucao.cliente
        execucao.cliente = lambda: falso
        try:
            r = compactar.compactar(cid)
        finally:
            execucao.cliente = original
        self.assertEqual(r["resumo"], "Resumo: pediu X.")
        self.assertEqual(falso.pedidos[0]["compaction"]["type"], "summarize")
        self.assertIn(compactar.BETA, falso.pedidos[0]["betas"])
        caminho = banco.caminho(cid)
        self.assertEqual(caminho[-1]["tipo"], "compactacao")
        pai = banco.adicionar_mensagem(cid, caminho[-1]["id"], "user", [{"type": "text", "text": "E agora?"}])["id"]
        msgs = execucao._para_api(banco.conversa(cid), banco.caminho(cid))
        self.assertEqual(msgs[0]["content"][0]["type"], "compaction")   # o resumo vem primeiro
        self.assertEqual(len(msgs), 2)
        self.assertTrue(compactar.comeca_com_resumo(msgs))
        kw, _ = pedido.montar(modelo="claude-haiku-5-5", esforco="medium", pensar=False, mostrar_raciocinio=False,
                              modo="chat", sistema="", mensagens=msgs, ferramentas_cliente=[], cfg={"compactacao": True})
        self.assertNotIn("context_management", kw)   # a compactação automática não vai junto do bloco
        self.assertIn(compactar.BETA, kw.get("betas", []))

    def test_conversa_curta_nao_compacta(self):
        cid = banco.criar_conversa("chat")["id"]
        banco.adicionar_mensagem(cid, None, "user", [{"type": "text", "text": "Oi"}])
        with self.assertRaises(ValueError):
            compactar.compactar(cid)


EXPORT_PT = """```
## Instruções
[2026-01-10] - Respostas curtas, sem enrolação.
## Identidade
[desconhecida] - Me chamo Bia e tenho uma loja de bolos.
## Carreira
[2025-03-01] - Dona da Doce Bia desde 2025.
## Projetos
[2026-02-01] - Cardápio de Natal | planilha de encomendas | em andamento | fechar até 15/12
## Preferências
[unknown] - Gosto de tabelas.
## Estilo de resposta
- Português do Brasil, tom amigável.
## Automações e rotinas
[2026-03-01] - Resumo das encomendas | seg a sex 08:30 | Leia a planilha de encomendas e me diga o que entregar hoje.
[2026-03-02] - Conferir estoque | a cada 4 horas | Veja se algum ingrediente acabou.
## Ferramentas e conectores
- Google Drive, para as planilhas.
```
Isso é tudo."""

EXPORT_EN = """1. **Instructions**:
[2026-01-10] - Keep it short.
5. **Preferences**:
[unknown] - Likes tables.
7. **Automations and routines**:
[2026-03-01] - Daily digest | every day at 7am | Summarize my unread e-mails.
"""


class TestImportar(unittest.TestCase):
    def test_ler_pt(self):
        r = importar.ler(EXPORT_PT)
        cats = [i["categoria"] for i in r["itens"]]
        for c in importar.CATEGORIAS:
            self.assertIn(c, cats, c)
        rot = [i for i in r["itens"] if i["categoria"] == "rotinas"]
        self.assertEqual(rot[0]["quando"], {"tipo": "semanal", "hora": "08:30", "dias": [0, 1, 2, 3, 4]})
        self.assertEqual(rot[1]["quando"], {"tipo": "horas", "a_cada": 4})
        proj = [i for i in r["itens"] if i["categoria"] == "projetos"][0]
        self.assertEqual(proj["nome"], "Cardápio de Natal")

    def test_ler_en(self):
        r = importar.ler(EXPORT_EN)
        self.assertEqual([i["categoria"] for i in r["itens"]], ["instrucoes", "preferencias", "rotinas"])
        self.assertEqual(r["itens"][2]["quando"], {"tipo": "diaria", "hora": "07:00"})

    def test_aplicar(self):
        config.salvar({"como_responder": "", "sobre_voce": ""})
        itens = importar.ler(EXPORT_PT)["itens"]
        feito = importar.aplicar(itens)
        self.assertEqual(feito["projetos"], 1)
        self.assertEqual(feito["rotinas"], 2)
        cfg = config.carregar()
        self.assertIn("Respostas curtas", cfg["como_responder"])
        self.assertIn("loja de bolos", cfg["sobre_voce"])
        r = [x for x in banco.listar_rotinas() if x["nome"] == "Resumo das encomendas"][0]
        self.assertFalse(r["ligada"])
        self.assertEqual(r["modelo"], "claude-haiku-5-5")
        self.assertIn("preferencias-importadas.md", (memoria.raiz() / memoria.INDICE).read_text(encoding="utf-8"))
        # importar de novo não duplica o projeto nem as regras
        importar.aplicar(itens)
        self.assertEqual(sum(1 for p in banco.listar_projetos() if p["nome"] == "Cardápio de Natal"), 1)
        self.assertEqual(config.carregar()["como_responder"].count("Respostas curtas"), 1)
        for x in banco.listar_rotinas():
            rotinas.apagar(x["id"])

    def test_sem_categoria(self):
        self.assertEqual(importar.ler("oi, tudo bem?")["itens"], [])


if __name__ == "__main__":
    unittest.main()
