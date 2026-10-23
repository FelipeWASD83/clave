"""Resposta que para antes do fim sem erro (teto da tarefa, voltas demais) deixa o motivo guardado na conversa.

Antes o aviso só existia como evento: ao terminar, a tela redesenha a conversa a partir do banco e o aviso sumia,
parecendo que a resposta tinha parado do nada no meio da tarefa.
"""
import os
import tempfile
import unittest

import base  # noqa: F401
import banco
import config
import execucao


class TestPausaFicaGuardada(unittest.TestCase):
    def setUp(self):
        self.antes_api = os.environ.get("CLAVE_API_FALSA")
        os.environ["CLAVE_API_FALSA"] = "http://127.0.0.1:9"  # nada chega a ser chamado: o teto para antes
        self.pasta = tempfile.mkdtemp(prefix="clave-pausa-")
        self.teto_antes = config.carregar().get("teto_tarefa_code_usd")
        config.salvar({"teto_tarefa_code_usd": 2.0})

    def tearDown(self):
        config.salvar({"teto_tarefa_code_usd": self.teto_antes})
        if self.antes_api is None:
            os.environ.pop("CLAVE_API_FALSA", None)
        else:
            os.environ["CLAVE_API_FALSA"] = self.antes_api

    def test_teto_da_tarefa_fica_na_ultima_mensagem_e_no_fim(self):
        cid = banco.criar_conversa(modo="code", pasta=self.pasta, titulo="teste")["id"]
        m = banco.adicionar_mensagem(cid, None, "user", [{"type": "text", "text": "faz algo"}])
        ex = execucao.Execucao(cid, {"sem_conselheiro": True, "modelo": "claude-haiku-5-5"})
        ex.custo_total = 2.5  # já gastou acima do teto nas voltas anteriores
        ex.rodar()

        self.assertEqual(ex.status, "concluida")
        fim = ex.eventos[-1]
        self.assertEqual(fim["tipo"], "fim")
        self.assertEqual(fim["pausa"]["motivo"], "teto_tarefa")
        self.assertIn("teto por tarefa", fim["pausa"]["mensagem"])
        guardada = banco.mensagem(m["id"])
        self.assertEqual(guardada["meta"]["pausa"]["motivo"], "teto_tarefa")
        self.assertTrue(any(e["tipo"] == "aviso" for e in ex.eventos))

    def test_limite_de_acoes_vem_da_configuracao(self):
        class Bloco:
            def __init__(self, i):
                self.i = i

            def model_dump(self, **_):
                return {"type": "tool_use", "id": f"t{self.i}", "name": "ler_arquivo", "input": {"caminho": "x"}}

        class Final:
            def __init__(self, i):
                self.content, self.usage, self.model, self.stop_reason = [Bloco(i)], None, "claude-haiku-5-5", "tool_use"

        antes = config.carregar().get("max_voltas_code")
        config.salvar({"max_voltas_code": 12})
        try:
            cid = banco.criar_conversa(modo="code", pasta=self.pasta, titulo="teste")["id"]
            banco.adicionar_mensagem(cid, None, "user", [{"type": "text", "text": "faz algo longo"}])
            ex = execucao.Execucao(cid, {"sem_conselheiro": True, "modelo": "claude-haiku-5-5"})
            chamadas = []
            ex._chamar = lambda cli, kw: chamadas.append(1) or Final(len(chamadas))
            ex._ferramentas = lambda usos, cfg, modo: [
                {"type": "tool_result", "tool_use_id": u["id"], "content": "ok"} for u in usos]
            ex.rodar()
        finally:
            config.salvar({"max_voltas_code": antes})
        self.assertEqual(len(chamadas), 12)
        pausa = ex.eventos[-1]["pausa"]
        self.assertEqual(pausa["motivo"], "voltas")
        self.assertIn("12 ações", pausa["mensagem"])

    def test_resposta_normal_nao_tem_pausa(self):
        cid = banco.criar_conversa(modo="code", pasta=self.pasta, titulo="teste")["id"]
        banco.adicionar_mensagem(cid, None, "user", [{"type": "text", "text": "oi"}])
        ex = execucao.Execucao(cid, {"sem_conselheiro": True})
        ex.parar.set()  # interrompida antes da primeira volta
        ex.rodar()
        self.assertIsNone(ex.eventos[-1]["pausa"])


if __name__ == "__main__":
    unittest.main()
