"""3.1.0: a busca na web vem ligada, e quem já usava é migrado uma vez só."""
import unittest

import base  # noqa: F401
import banco
import config
import servidor


class TestWebPorPadrao(unittest.TestCase):
    def setUp(self):
        config.salvar({"busca_web": False, "web_por_padrao_migrada": False})

    def test_padrao_de_instalacao_nova_e_ligada(self):
        self.assertTrue(config.PADRAO["busca_web"])

    def test_migracao_liga_e_limpa_as_conversas_uma_vez(self):
        chat = banco.criar_conversa("chat", ajustes={"busca_web": False, "modelo": "claude-haiku-5-5"})["id"]
        code = banco.criar_conversa("code", ajustes={"busca_web": False})["id"]
        etapa = banco.criar_conversa("etapa", ajustes={"busca_web": False})["id"]
        servidor.migrar_web_por_padrao()
        cfg = config.carregar()
        self.assertTrue(cfg["busca_web"])
        self.assertTrue(cfg["web_por_padrao_migrada"])
        self.assertEqual(banco.conversa(chat)["ajustes"], {"modelo": "claude-haiku-5-5"})
        self.assertEqual(banco.conversa(code)["ajustes"], {})
        self.assertEqual(banco.conversa(etapa)["ajustes"], {"busca_web": False})  # escondida: fica como está

        # depois da migração, quem desligar de novo continua desligado
        config.salvar({"busca_web": False})
        banco.atualizar_conversa(chat, ajustes={"busca_web": False})
        servidor.migrar_web_por_padrao()
        self.assertFalse(config.carregar()["busca_web"])
        self.assertEqual(banco.conversa(chat)["ajustes"], {"busca_web": False})


if __name__ == "__main__":
    unittest.main()
