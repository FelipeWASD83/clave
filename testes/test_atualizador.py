import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import base  # noqa: F401
import atualizador


class TestVersoes(unittest.TestCase):
    def test_comparacao(self):
        self.assertTrue(atualizador.mais_nova("1.0.1", "1.0.0"))
        self.assertTrue(atualizador.mais_nova("v2.0.0", "1.9.9"))
        self.assertTrue(atualizador.mais_nova("1.10.0", "1.9.0"))
        self.assertFalse(atualizador.mais_nova("1.0.0", "1.0.0"))
        self.assertFalse(atualizador.mais_nova("0.9", "1.0.0"))


class TestTroca(unittest.TestCase):
    """Simula uma atualização numa cópia falsa do app: troca os arquivos, preserva dados/ e volta atrás."""

    def setUp(self):
        self.app = Path(tempfile.mkdtemp(prefix="clave-app-"))
        (self.app / "servidor").mkdir()
        (self.app / "servidor" / "servidor.py").write_text("velho", encoding="utf-8")
        (self.app / "app").mkdir()
        (self.app / "app" / "index.html").write_text("velho", encoding="utf-8")
        (self.app / "app" / "so-no-velho.js").write_text("x", encoding="utf-8")
        (self.app / "versao.json").write_text('{"versao": "1.0.0"}', encoding="utf-8")
        (self.app / "requirements.txt").write_text("anthropic==1\n", encoding="utf-8")
        (self.app / "dados").mkdir()
        (self.app / "dados" / "clave.db").write_text("conversas", encoding="utf-8")
        novo = atualizador.PASTA / "novo" / "clave-1.1.0"
        shutil.rmtree(atualizador.PASTA, ignore_errors=True)
        (novo / "servidor").mkdir(parents=True)
        (novo / "servidor" / "servidor.py").write_text("novo", encoding="utf-8")
        (novo / "app").mkdir()
        (novo / "app" / "index.html").write_text("novo", encoding="utf-8")
        (novo / "versao.json").write_text('{"versao": "1.1.0"}', encoding="utf-8")
        (novo / "requirements.txt").write_text("anthropic==2\n", encoding="utf-8")
        atualizador.PASTA.mkdir(parents=True, exist_ok=True)
        (atualizador.PASTA / "pronta.json").write_text(json.dumps({"versao": "1.1.0", "pasta": str(novo)}), encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.app, ignore_errors=True)
        shutil.rmtree(atualizador.PASTA, ignore_errors=True)

    def test_aplica_preserva_dados_e_reverte(self):
        r = atualizador.aplicar_pendente(self.app)
        self.assertEqual(r["versao"], "1.1.0")
        self.assertTrue(r["dependencias_mudaram"])
        self.assertEqual((self.app / "servidor" / "servidor.py").read_text(encoding="utf-8"), "novo")
        self.assertFalse((self.app / "app" / "so-no-velho.js").exists(), "arquivo que saiu da versão nova sai também")
        self.assertEqual((self.app / "dados" / "clave.db").read_text(encoding="utf-8"), "conversas")
        self.assertIsNone(atualizador.pendente())
        self.assertTrue(atualizador.reverter(self.app))
        self.assertEqual((self.app / "servidor" / "servidor.py").read_text(encoding="utf-8"), "velho")
        self.assertTrue((self.app / "app" / "so-no-velho.js").exists())
        self.assertEqual((self.app / "dados" / "clave.db").read_text(encoding="utf-8"), "conversas")

    def test_aplica_mesmo_rodando_de_dentro_da_pasta(self):
        # no Windows, pasta que é o diretório atual de um processo não pode ser apagada nem movida
        antes = os.getcwd()
        os.chdir(self.app / "servidor")
        try:
            r = atualizador.aplicar_pendente(self.app)
        finally:
            os.chdir(antes)
        self.assertEqual(r["versao"], "1.1.0")
        self.assertEqual((self.app / "servidor" / "servidor.py").read_text(encoding="utf-8"), "novo")

    def test_volta_atras_com_pasta_presa_nao_aninha(self):
        atualizador.aplicar_pendente(self.app)
        real = shutil.rmtree

        def rmtree_preso(caminho, ignore_errors=False, **kw):
            # como no Windows com a pasta em uso por outro programa: o conteúdo sai, a pasta fica
            for item in list(Path(caminho).iterdir()):
                real(item) if item.is_dir() else item.unlink()

        with mock.patch.object(atualizador.shutil, "rmtree", rmtree_preso):
            self.assertTrue(atualizador.reverter(self.app))
        self.assertFalse((self.app / "servidor" / "servidor").exists(), "a versão antiga não pode ir parar dentro da pasta")
        self.assertEqual((self.app / "servidor" / "servidor.py").read_text(encoding="utf-8"), "velho")
        self.assertTrue((self.app / "app" / "so-no-velho.js").exists())

    def test_sem_nada_pendente(self):
        (atualizador.PASTA / "pronta.json").unlink()
        self.assertIsNone(atualizador.aplicar_pendente(self.app))


if __name__ == "__main__":
    unittest.main()
