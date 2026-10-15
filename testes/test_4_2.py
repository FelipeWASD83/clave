"""4.2.0: o cartão de perguntas, o "posso fazer?" com plano fora do modo Plano e os vídeos das lições."""
import io
import shutil
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

import base
import config
import execucao
import sistema
import tutoriais
import videos
from test_servidor import Servidor


class TestPerguntas(unittest.TestCase):
    def test_normaliza_e_corta(self):
        p = execucao.normalizar_perguntas({"perguntas": [
            {"pergunta": "  Qual   formato? ", "titulo": "Formato de saída longo demais para o rótulo",
             "opcoes": ["Excel (recomendado)", {"rotulo": "Word", "descricao": "Para imprimir"}, "A", "B", "C"]}]})
        self.assertEqual(p[0]["pergunta"], "Qual formato?")
        self.assertEqual(len(p[0]["opcoes"]), 4)
        self.assertEqual(p[0]["opcoes"][1], {"rotulo": "Word", "descricao": "Para imprimir"})
        self.assertLessEqual(len(p[0]["titulo"]), 24)
        self.assertFalse(p[0]["varias"])
        cinco = execucao.normalizar_perguntas({"perguntas": [{"pergunta": f"P{i}?", "opcoes": ["a", "b"]} for i in range(6)]})
        self.assertEqual(len(cinco), 4)

    def test_pergunta_errada_volta_com_o_motivo(self):
        for ruim in ({}, {"perguntas": []}, {"perguntas": [{"pergunta": "Só uma opção?", "opcoes": ["a"]}]},
                     {"perguntas": [{"opcoes": ["a", "b"]}]}):
            with self.assertRaises(ValueError):
                execucao.normalizar_perguntas(ruim)

    def test_texto_das_respostas(self):
        p = execucao.normalizar_perguntas({"perguntas": [
            {"pergunta": "Formato?", "opcoes": ["Excel", "Word"]},
            {"pergunta": "Meses?", "opcoes": ["Ago", "Set", "Out"], "varias": True},
            {"pergunta": "Pasta?", "opcoes": ["A", "B"]}]})
        txt = execucao.texto_respostas(p, [{"escolhas": ["Word", "inventada"]}, {"escolhas": ["Ago", "Out"], "outra": "e novembro"}])
        self.assertTrue(txt.startswith("Respostas de quem usa:"))
        self.assertIn("**Formato?**\nWord", txt)
        self.assertNotIn("inventada", txt, "só vale opção que existe")
        self.assertIn("Ago, Out, Outra: e novembro", txt)
        self.assertIn("**Pasta?**\n(sem resposta)", txt)

    def test_prompts(self):
        cfg = config.carregar()
        self.assertIn("use perguntar", sistema.chat(cfg))
        cfg["pedir_ok_plano"] = True
        self.assertIn("apresente o plano com apresentar_plano", sistema.code(cfg, str(base.DADOS)))
        cfg["pedir_ok_plano"] = False
        self.assertNotIn("apresente o plano com apresentar_plano", sistema.code(cfg, str(base.DADOS)))


class TestNoServidor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Servidor(sem_senha=True)

    @classmethod
    def tearDownClass(cls):
        cls.s.fechar()

    def _resultado(self, cid, nome):
        _, v = self.s.pedir("GET", f"/api/conversas/{cid}")
        ids = {b["id"] for m in v["mensagens"] if m["papel"] == "assistant" and isinstance(m["conteudo"], list)
               for b in m["conteudo"] if b.get("type") == "tool_use" and b.get("name") == nome}
        for m in v["mensagens"]:
            for b in (m["conteudo"] if isinstance(m["conteudo"], list) else []):
                if b.get("type") == "tool_result" and b.get("tool_use_id") in ids:
                    c = b.get("content")
                    return c if isinstance(c, str) else " ".join(x.get("text", "") for x in c)
        return None

    def test_cartao_de_perguntas_no_chat(self):
        _, r = self.s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        _, r = self.s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "faça o relatório, mas pergunte antes"})
        respostas = {"respostas": [{"escolhas": ["Documento do Word"]}, {"escolhas": ["Agosto", "Outubro"]}]}
        evs = self.s.eventos(r["execucao"], decidir=lambda ev: ("responder", respostas) if ev["tipo"] == "pergunta" else "recusar")
        pergunta = next(e for e in evs if e["tipo"] == "pergunta")
        self.assertEqual(len(pergunta["perguntas"]), 2)
        self.assertTrue(pergunta["perguntas"][1]["varias"])
        self.assertEqual(evs[-1]["status"], "concluida")
        res = self._resultado(cid, "perguntar")
        self.assertIn("Documento do Word", res)
        self.assertIn("Agosto, Outubro", res)

    def test_pular_a_pergunta(self):
        _, r = self.s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        _, r = self.s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "pergunte o formato"})
        self.s.eventos(r["execucao"], decidir="pular")
        self.assertIn("preferiu não responder", self._resultado(cid, "perguntar"))

    def test_plano_fora_do_modo_plano(self):
        pasta = tempfile.mkdtemp(prefix="clave-ok-")
        try:
            _, r = self.s.pedir("POST", "/api/conversas", {"modo": "code", "pasta": pasta})
            cid = r["conversa"]["id"]
            # "mudar" volta com o comentário e não executa nada
            _, r = self.s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "planeje e organize", "opcoes": {"permissao": "perguntar"}})
            evs = self.s.eventos(r["execucao"], decidir=lambda ev: "mudar" if ev["tipo"] == "plano_proposto" else "recusar")
            plano = next(e for e in evs if e["tipo"] == "plano_proposto")
            self.assertEqual(plano["modo"], "perguntar")
            self.assertFalse(any(e["tipo"] == "modo_mudou" for e in evs), "fora do modo Plano o modo não muda")
            self.assertIn("mudar o plano", self._resultado(cid, "apresentar_plano"))
            self.assertFalse((Path(pasta) / "exemplo-do-plano.txt").exists())
            # "pode ir" executa, e a edição ainda pede o OK do modo Perguntar
            _, r = self.s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "planeje de novo", "opcoes": {"permissao": "perguntar"}})
            evs = self.s.eventos(r["execucao"], decidir=lambda ev: "pode_ir" if ev["tipo"] == "plano_proposto" else "permitir")
            self.assertTrue(any(e["tipo"] == "aprovacao" for e in evs))
            self.assertTrue((Path(pasta) / "exemplo-do-plano.txt").exists())
        finally:
            shutil.rmtree(pasta, ignore_errors=True)

    def test_chave_desliga_o_plano_fora_do_modo_plano(self):
        pasta = tempfile.mkdtemp(prefix="clave-ok-")
        try:
            self.s.pedir("POST", "/api/config", {"pedir_ok_plano": False})
            _, r = self.s.pedir("POST", "/api/conversas", {"modo": "code", "pasta": pasta})
            cid = r["conversa"]["id"]
            _, r = self.s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "planeje", "opcoes": {"permissao": "perguntar"}})
            evs = self.s.eventos(r["execucao"], decidir="recusar")
            self.assertFalse(any(e["tipo"] == "plano_proposto" for e in evs))
        finally:
            self.s.pedir("POST", "/api/config", {"pedir_ok_plano": True})
            shutil.rmtree(pasta, ignore_errors=True)

    def test_video_com_range(self):
        status, r = self.s.pedir("GET", "/api/videos/nao-existe/estado?lingua=en")
        self.assertEqual((status, r["pronto"]), (200, False))
        status, _ = self.s.pedir("GET", "/api/videos/nao-existe?lingua=en")
        self.assertEqual(status, 404)
        cache = Path(self.s.dados) / "videos"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "teste-range.en.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + bytes(range(256)) * 4)
        req = urllib.request.Request(self.s.url("/api/videos/teste-range?lingua=en"), headers={"Range": "bytes=4-11"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.status, 206)
            self.assertEqual(resp.read(), b"ftypmp42")
            self.assertTrue(resp.headers["Content-Range"].startswith("bytes 4-11/"))
        status, r = self.s.pedir("GET", "/api/videos/teste-range/estado?lingua=en")
        self.assertTrue(r["pronto"])


class _Resposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestVideos(unittest.TestCase):
    def setUp(self):
        self.antes = videos.pasta_cache
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-videos-"))
        videos.pasta_cache = lambda: self.pasta

    def tearDown(self):
        videos.pasta_cache = self.antes
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_baixa_uma_vez_e_guarda(self):
        mp4 = b"\x00\x00\x00\x18ftypmp42" + b"x" * 1000
        with mock.patch.object(videos.urllib.request, "urlopen", return_value=_Resposta(mp4)) as m:
            arq = videos.baixar("teste-baixar", "pt-BR")
        self.assertEqual(arq.read_bytes(), mp4)
        self.assertIn("/releases/download/videos/teste-baixar.pt-BR.mp4", m.call_args[0][0].full_url)
        with mock.patch.object(videos.urllib.request, "urlopen", side_effect=AssertionError("baixou de novo")):
            self.assertEqual(videos.baixar("teste-baixar", "pt-BR"), arq)

    def test_nao_video_e_404_viram_aviso(self):
        with mock.patch.object(videos.urllib.request, "urlopen", return_value=_Resposta(b"<html>nada</html>")):
            with self.assertRaises(ValueError):
                videos.baixar("teste-html", "en")
        self.assertFalse((self.pasta / "teste-html.en.mp4").exists())
        erro = urllib.error.HTTPError("u", 404, "Not Found", {}, None)
        with mock.patch.object(videos.urllib.request, "urlopen", side_effect=erro):
            with self.assertRaisesRegex(ValueError, "404"):
                videos.baixar("teste-404", "en")

    def test_id_invalido(self):
        for ruim in ("../segredo", "A", "x" * 61, ""):
            with self.assertRaises(ValueError):
                videos.nome_arquivo(ruim, "en")

    def test_licao_diz_o_video(self):
        # o campo existe em toda lição; vazio enquanto ela não tem vídeo
        for lingua in ("pt-BR", "en"):
            for li in tutoriais.listar(lingua):
                self.assertIn("video", li)


if __name__ == "__main__":
    unittest.main()
