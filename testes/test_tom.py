"""4.1.0: o jeito de falar (tom básico e os controles de Menos, Padrão e Mais) no prompt e o exemplo no Haiku."""
import unittest
from types import SimpleNamespace

import base  # noqa: F401
import banco
import config
import execucao
import sistema
import tom


class TestJeitoDeFalar(unittest.TestCase):
    def setUp(self):
        self.antes = config.carregar()

    def tearDown(self):
        config.salvar({"tom": self.antes.get("tom", {}), "idioma": self.antes.get("idioma") or "pt-BR"})

    def test_tudo_no_padrao_nao_muda_o_prompt(self):
        cfg = config.carregar()
        cfg.pop("tom", None)
        sem = sistema.chat(cfg)
        cfg["tom"] = {}
        self.assertEqual(sistema.chat(cfg), sem)
        cfg["tom"] = {c["id"]: "padrao" for c in tom.opcoes()}
        self.assertEqual(sistema.chat(cfg), sem)
        self.assertNotIn("jeito_de_falar", sem)

    def test_cada_opcao_vira_uma_frase(self):
        for c in tom.opcoes():
            for o in c["opcoes"]:
                linhas = tom.frases({c["id"]: o["valor"]})
                self.assertEqual(len(linhas), 0 if o["valor"] == "padrao" else 1, (c["id"], o["valor"]))

    def test_escolhas_entram_no_chat_e_no_code(self):
        cfg = config.carregar()
        cfg["tom"] = {"base": "sincero", "emoji": "nenhum", "linguagem": "simples"}
        for prompt in (sistema.chat(cfg), sistema.code(cfg, str(base.DADOS))):
            self.assertIn("<jeito_de_falar>", prompt)
            self.assertIn("Tom sincero", prompt)
            self.assertIn("Não use emoji", prompt)
            self.assertIn("Linguagem: simples", prompt)
            self.assertNotIn("Cordialidade", prompt)

    def test_limpar_tira_o_que_nao_existe_e_o_padrao(self):
        self.assertEqual(tom.limpar({"base": "amigavel", "emoji": "padrao", "cor": "azul", "entusiasmo": "muito"}),
                         {"base": "amigavel"})
        self.assertEqual(tom.limpar("lixo"), {})

    def test_em_ingles(self):
        config.salvar({"idioma": "en"})
        bloco = tom.bloco({"cordialidade": "mais", "sugestao": "nunca"})
        self.assertIn("<way_of_talking>", bloco)
        self.assertIn("Warmth: more.", bloco)
        self.assertIn("want me to...?", bloco)
        self.assertEqual([c["nome"] for c in tom.opcoes()][0], "Base style and tone")


class _ClienteFalso:
    def __init__(self):
        self.pedidos = []
        texto = SimpleNamespace(type="text", text="**Backup** é uma cópia.")
        uso = SimpleNamespace(model_dump=lambda mode="json", exclude_none=True: {"input_tokens": 300, "output_tokens": 40})
        resposta = SimpleNamespace(content=[texto], usage=uso, stop_reason="end_turn")
        self.messages = SimpleNamespace(create=lambda **kw: (self.pedidos.append(kw), resposta)[1])


class TestExemplo(unittest.TestCase):
    def test_exemplo_usa_o_haiku_com_o_tom_e_registra_o_custo(self):
        falso = _ClienteFalso()
        original = execucao.cliente
        execucao.cliente = lambda: falso
        try:
            r = tom.exemplo({"base": "divertido", "emoji": "mais"})
        finally:
            execucao.cliente = original
        pedido = falso.pedidos[0]
        self.assertEqual(pedido["model"], "claude-haiku-5-5")
        self.assertIn("Tom divertido", pedido["system"])
        self.assertIn("Emoji: mais", pedido["system"])
        self.assertEqual(pedido["messages"][0]["content"], tom.pergunta_exemplo())
        self.assertEqual(r["resposta"], "**Backup** é uma cópia.")
        self.assertGreater(r["custo_usd"], 0)
        ultimo = banco.conexao().execute("SELECT origem, modelo FROM uso ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual((ultimo["origem"], ultimo["modelo"]), ("exemplo_tom", "claude-haiku-5-5"))

    def test_pergunta_propria(self):
        falso = _ClienteFalso()
        original = execucao.cliente
        execucao.cliente = lambda: falso
        try:
            r = tom.exemplo({}, "Como faço um bolo?")
        finally:
            execucao.cliente = original
        self.assertEqual(r["pergunta"], "Como faço um bolo?")
        self.assertNotIn("jeito_de_falar", falso.pedidos[0]["system"])


if __name__ == "__main__":
    unittest.main()
