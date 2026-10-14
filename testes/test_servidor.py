"""O servidor de verdade, em processo separado, com a API de mentira: segurança e fluxo completo."""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import base


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Servidor:
    def __init__(self, sem_senha: bool):
        self.dados = tempfile.mkdtemp(prefix="clave-srv-")
        self.porta = porta_livre()
        args = [sys.executable, str(base.RAIZ / "servidor" / "servidor.py"), "--porta", str(self.porta), "--demo",
                "--dados", self.dados]
        if sem_senha:
            args.append("--sem-senha")
        env = {k: v for k, v in os.environ.items() if k not in ("CLAVE_DADOS", "CLAVE_SEM_SENHA", "CLAVE_API_FALSA")}
        self.proc = subprocess.Popen(args, cwd=str(base.RAIZ), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                urllib.request.urlopen(self.url("/api/saude"), timeout=1)
                break
            except urllib.error.HTTPError:
                break
            except OSError:
                time.sleep(0.1)

    def url(self, c):
        return f"http://127.0.0.1:{self.porta}{c}"

    def pedir(self, metodo, caminho, corpo=None, cab=None):
        dados = json.dumps(corpo).encode() if corpo is not None else None
        req = urllib.request.Request(self.url(caminho), data=dados, method=metodo,
                                     headers={"Content-Type": "application/json", **(cab or {})})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    def eventos(self, eid, decidir=None):
        saida = []
        with urllib.request.urlopen(self.url(f"/api/execucoes/{eid}/eventos?desde=0"), timeout=120) as r:
            for linha in r:
                linha = linha.decode().strip()
                if linha.startswith("data: "):
                    ev = json.loads(linha[6:])
                    saida.append(ev)
                    if ev["tipo"] == "aprovacao" and decidir:
                        self.pedir("POST", f"/api/execucoes/{eid}/aprovar", {"id": ev["id"], "decisao": decidir})
                    if ev["tipo"] == "fim":
                        break
        return saida

    def fechar(self):
        self.proc.terminate()
        self.proc.wait(timeout=10)
        shutil.rmtree(self.dados, ignore_errors=True)


class TestSeguranca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Servidor(sem_senha=False)

    @classmethod
    def tearDownClass(cls):
        cls.s.fechar()

    def test_api_sem_sessao_recusa(self):
        status, corpo = self.s.pedir("GET", "/api/estado")
        self.assertEqual(status, 401)
        self.assertEqual(corpo.get("codigo"), "sessao")

    def test_host_estranho_recusa(self):
        status, _ = self.s.pedir("GET", "/api/saude", cab={"Host": "evil.example:80"})
        self.assertEqual(status, 403)

    def test_segredo_errado_nao_vira_cookie(self):
        req = urllib.request.Request(self.s.url("/?t=errado"))
        with urllib.request.urlopen(req, timeout=10) as r:
            self.assertIsNone(r.headers.get("Set-Cookie"))

    def test_segredo_certo_vira_cookie_e_libera(self):
        segredo = (Path(self.s.dados) / "sessao.key").read_text(encoding="ascii").strip()

        class SemRedirecionar(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        abridor = urllib.request.build_opener(SemRedirecionar)
        try:
            abridor.open(self.s.url(f"/?t={segredo}"), timeout=10)
            self.fail("esperava redirecionamento")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 302)
            completo = e.headers.get("Set-Cookie")
            cookie = completo.split(";")[0]
        self.assertIn("HttpOnly", completo)
        self.assertIn("SameSite=Strict", completo)
        status, _ = self.s.pedir("GET", "/api/estado", cab={"Cookie": cookie})
        self.assertEqual(status, 200)
        status, _ = self.s.pedir("POST", "/api/config", {"nome": "x"}, cab={"Cookie": cookie, "Origin": "http://evil.example"})
        self.assertEqual(status, 403, "outra origem não pode mudar nada")

    def test_arquivo_fora_do_app_nao_sai(self):
        req = urllib.request.Request(self.s.url("/..%2F..%2Fversao.json"))
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                self.assertNotIn(b"repositorio", r.read())
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 404)


class TestFluxo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Servidor(sem_senha=True)

    @classmethod
    def tearDownClass(cls):
        cls.s.fechar()

    def test_chat_versoes_e_titulo(self):
        s = self.s
        _, r = s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "Olá!", "opcoes": {"modelo": "claude-haiku-5-5"}})
        evs = s.eventos(r["execucao"])
        self.assertEqual(evs[-1]["status"], "concluida")
        self.assertTrue(any(e["tipo"] == "texto" for e in evs))
        _, v = s.pedir("GET", f"/api/conversas/{cid}")
        self.assertEqual([m["papel"] for m in v["mensagens"]], ["user", "assistant"])
        ultima = v["mensagens"][-1]
        _, r = s.pedir("POST", f"/api/conversas/{cid}/regenerar", {"mensagem_id": ultima["id"]})
        s.eventos(r["execucao"])
        _, v = s.pedir("GET", f"/api/conversas/{cid}")
        self.assertEqual(len(v["mensagens"][-1]["irmaos"]), 2)
        _, v2 = s.pedir("POST", f"/api/conversas/{cid}/folha", {"mensagem_id": v["mensagens"][-1]["irmaos"][0]})
        self.assertEqual(v2["mensagens"][-1]["id"], v["mensagens"][-1]["irmaos"][0])
        time.sleep(1.5)
        _, lista = s.pedir("GET", "/api/conversas")
        self.assertTrue(any(c["id"] == cid and c["titulo"] for c in lista["conversas"]))

    def test_code_com_aprovacao_recusa_e_desfazer(self):
        s = self.s
        pasta = tempfile.mkdtemp(prefix="clave-code-srv-")
        try:
            _, r = s.pedir("POST", "/api/conversas", {"modo": "code", "pasta": pasta})
            cid = r["conversa"]["id"]
            _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "crie um arquivo de exemplo", "opcoes": {"permissao": "perguntar"}})
            evs = s.eventos(r["execucao"], decidir="recusar")
            self.assertTrue(any(e["tipo"] == "aprovacao" for e in evs))
            self.assertFalse((Path(pasta) / "exemplo-do-clave.txt").exists(), "recusado não pode criar")
            _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "crie um arquivo de exemplo", "opcoes": {"permissao": "perguntar"}})
            s.eventos(r["execucao"], decidir="permitir")
            self.assertTrue((Path(pasta) / "exemplo-do-clave.txt").exists())
            _, d = s.pedir("POST", f"/api/execucoes/{r['execucao']}/desfazer")
            self.assertEqual(len(d["arquivos"]), 1)
            self.assertFalse((Path(pasta) / "exemplo-do-clave.txt").exists())
            _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "crie um arquivo de exemplo", "opcoes": {"permissao": "plano"}})
            evs = s.eventos(r["execucao"])
            self.assertFalse(any(e["tipo"] == "aprovacao" for e in evs), "no modo Plano nem pergunta: recusa")
            self.assertFalse((Path(pasta) / "exemplo-do-clave.txt").exists())
        finally:
            shutil.rmtree(pasta, ignore_errors=True)

    def test_ajudantes_ficam_fora_da_lista(self):
        s = self.s
        st, v = s.pedir("POST", "/api/ajudantes/tutor", {"licao": "glossario"})
        self.assertEqual(st, 200)
        self.assertEqual(v["conversa"]["modo"], "tutor")
        _, r = s.pedir("POST", f"/api/conversas/{v['conversa']['id']}/enviar", {"texto": "quem é JASON?"})
        evs = s.eventos(r["execucao"])
        self.assertEqual(evs[-1]["status"], "concluida")
        _, v2 = s.pedir("POST", "/api/ajudantes/tutor", {"licao": "glossario"})
        self.assertEqual(v2["conversa"]["id"], v["conversa"]["id"], "a conversa da lição continua a mesma")
        st, m = s.pedir("POST", "/api/ajudantes/memoria", {})
        self.assertEqual(m["conversa"]["modo"], "memoria")
        _, lista = s.pedir("GET", "/api/conversas")
        self.assertFalse(any(c["modo"] in ("tutor", "memoria") for c in lista["conversas"]))
        st, _ = s.pedir("POST", "/api/ajudantes/tutor", {"licao": "nao-existe"})
        self.assertEqual(st, 404)

    def test_teto_bloqueia_envio(self):
        s = self.s
        # a demonstração não cobra nada: o gasto vem do ajuste manual (gasto feito fora do Clave)
        s.pedir("POST", "/api/config", {"teto_mensal_usd": 1})
        s.pedir("POST", "/api/uso/ajuste", {"valor": 2})
        _, r = s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        st, r2 = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "dois"})
        self.assertEqual(st, 402)
        self.assertIn("teto", r2["erro"])
        s.pedir("POST", "/api/uso/ajuste", {"valor": 0})
        s.pedir("POST", "/api/config", {"teto_mensal_usd": 50})
        _, r3 = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "três"})
        self.assertIn("execucao", r3, "abaixo do teto volta a enviar")
        s.eventos(r3["execucao"])

    def test_paginas_estaticas_e_licoes(self):
        with urllib.request.urlopen(self.s.url("/"), timeout=10) as r:
            self.assertIn("default-src 'self'", r.headers.get("Content-Security-Policy"))
        _, t = self.s.pedir("GET", "/api/tutoriais")
        self.assertGreaterEqual(len(t["tutoriais"]), 15)
        _, l = self.s.pedir("GET", "/api/tutoriais/excel")
        self.assertIn("Excel", l["titulo"])


if __name__ == "__main__":
    unittest.main()
