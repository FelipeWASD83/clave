"""5.0: o que liga as partes novas no app (rotas registradas, ferramentas oferecidas, aviso do Haiku só para quem já
tinha configurado)."""
import base  # noqa: F401  (precisa vir antes dos módulos do servidor)

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import config


class TestAvisoDoHaiku(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-testes-integracao-"))
        self.antes = config.DADOS
        config.DADOS = self.pasta
        config.recarregar()

    def tearDown(self):
        config.DADOS = self.antes
        config.recarregar()
        shutil.rmtree(self.pasta, ignore_errors=True)

    def _migrar(self, dados: dict) -> dict:
        (self.pasta / "config.json").write_text(json.dumps(dados), encoding="utf-8")
        config.recarregar()
        import servidor
        servidor.migrar_haiku_padrao()
        config.recarregar()
        return config.carregar()

    def test_quem_nunca_configurou_nao_ganha_aviso(self):
        cfg = self._migrar({"configurado": False, "modelo_chat": "claude-sonnet-5-5", "modelo_code": "claude-opus-5-5"})
        self.assertEqual(cfg["modelo_chat"], "claude-haiku-5-5")
        self.assertIsNone(cfg["aviso_haiku"])

    def test_quem_ja_usava_ganha_aviso(self):
        cfg = self._migrar({"configurado": True, "modelo_chat": "claude-opus-5-5", "modelo_code": "claude-haiku-5-5"})
        self.assertEqual(cfg["aviso_haiku"], {"modelo_chat": "claude-opus-5-5", "modelo_code": "claude-haiku-5-5"})


class TestPartesLigadas(unittest.TestCase):
    def test_rotas_das_partes_registradas(self):
        import servidor  # noqa: F401  (registra tudo)
        from rotas import ROTAS
        padroes = {rx.pattern for _m, rx, _f in ROTAS}
        for trecho in ("/api/consoles", "/api/arquivos/lista", "/api/navegador/localhosts", "/api/tarefas",
                       "/api/widgets/", "/api/mapa/tile/"):
            self.assertTrue(any(trecho in p for p in padroes), trecho)

    def test_provedores_carregam(self):
        import provedores
        nomes = {m.__name__ for m in provedores.todos()}
        self.assertEqual(nomes, {"widgets", "navegador"})
        self.assertIs(provedores.dono("mostrar_widget").__name__, "widgets")
        self.assertIs(provedores.dono("navegador_abrir").__name__, "navegador")

    def test_widget_oferecido_no_chat_e_nao_na_rotina(self):
        import widgets
        cfg = config.carregar()
        ex = SimpleNamespace(op={})
        no_chat = widgets.oferecer(ex, modo="chat", op={}, cfg=cfg, etapa=False, pasta=None)
        self.assertEqual([d["name"] for d in no_chat], ["mostrar_widget"])
        na_rotina = widgets.oferecer(SimpleNamespace(op={"rotina": "r1"}), modo="chat", op={"rotina": "r1"}, cfg=cfg,
                                     etapa=False, pasta=None)
        self.assertEqual(na_rotina, [])

    def test_navegador_fica_de_fora_sem_a_janela_do_clave(self):
        import navegador
        antes = os.environ.pop("CLAVE_PONTE_URL", None)
        try:
            cfg = config.carregar()
            self.assertEqual(navegador.oferecer(SimpleNamespace(op={}), modo="code", op={}, cfg=cfg, etapa=False,
                                                pasta=Path(tempfile.gettempdir())), [])
        finally:
            if antes is not None:
                os.environ["CLAVE_PONTE_URL"] = antes


if __name__ == "__main__":
    unittest.main()
