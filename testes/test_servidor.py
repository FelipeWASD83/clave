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

    def _responder(self, eid, ev, decidir):
        d = decidir(ev) if callable(decidir) else decidir
        decisao, dados = d if isinstance(d, tuple) else (d, None)
        self.pedir("POST", f"/api/execucoes/{eid}/aprovar", {"id": ev["id"], "decisao": decisao, "dados": dados})

    def eventos(self, eid, decidir=None):
        """Acompanha a execução até o fim, respondendo aprovações, propostas de fluxo e planos (e os das etapas)."""
        saida = []
        with urllib.request.urlopen(self.url(f"/api/execucoes/{eid}/eventos?desde=0"), timeout=120) as r:
            for linha in r:
                linha = linha.decode().strip()
                if linha.startswith("data: "):
                    ev = json.loads(linha[6:])
                    saida.append(ev)
                    if ev["tipo"] in ("aprovacao", "fluxo_proposta", "plano_proposto", "pergunta") and decidir:
                        self._responder(eid, ev, decidir)
                    if ev["tipo"] == "etapa_evento" and ev["ev"]["tipo"] == "aprovacao" and decidir:
                        self._responder(ev["execucao"], ev["ev"], decidir)
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
            evs = s.eventos(r["execucao"], decidir="recusar")
            self.assertTrue(any(e["tipo"] == "plano_proposto" for e in evs), "no modo Plano ele apresenta o plano")
            self.assertFalse(any(e["tipo"] == "aprovacao" for e in evs), "no modo Plano nem pergunta: recusa")
            self.assertFalse((Path(pasta) / "exemplo-do-clave.txt").exists())
        finally:
            shutil.rmtree(pasta, ignore_errors=True)

    def test_plano_aprovado_muda_o_modo_e_executa(self):
        s = self.s
        pasta = tempfile.mkdtemp(prefix="clave-plano-")
        try:
            _, r = s.pedir("POST", "/api/conversas", {"modo": "code", "pasta": pasta})
            cid = r["conversa"]["id"]
            _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "planeje", "opcoes": {"permissao": "plano"}})
            evs = s.eventos(r["execucao"], decidir=lambda ev: "executar_aceitar" if ev["tipo"] == "plano_proposto" else "recusar")
            self.assertIn({"tipo": "modo_mudou", "permissao": "aceitar_edicoes"},
                          [{k: e[k] for k in ("tipo", "permissao")} for e in evs if e["tipo"] == "modo_mudou"])
            self.assertFalse(any(e["tipo"] == "aprovacao" for e in evs), "aceitar edições não pergunta")
            self.assertTrue((Path(pasta) / "exemplo-do-plano.txt").exists())

            def pedidos_de_quem_usa():
                _, v = s.pedir("GET", f"/api/conversas/{cid}")
                return [m for m in v["mensagens"] if m["papel"] == "user" and isinstance(m["conteudo"], list)
                        and any(b.get("type") == "text" and b["text"] in ("planeje", "obrigado") for b in m["conteudo"])]
            primeira = pedidos_de_quem_usa()[0]
            self.assertTrue(primeira["conteudo"][-1]["text"].startswith("<modo-do-clave>Modo Plano ligado"),
                            "o modelo fica sabendo do modo Plano pela própria mensagem")
            _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "obrigado", "opcoes": {"permissao": "aceitar_edicoes"}})
            s.eventos(r["execucao"], decidir="recusar")
            self.assertIn("foi desligado", pedidos_de_quem_usa()[-1]["conteudo"][-1]["text"])
            req = urllib.request.Request(s.url(f"/api/conversas/{cid}/exportar"))
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.assertNotIn("<modo-do-clave>", resp.read().decode("utf-8"), "o aviso não aparece para quem usa")
        finally:
            shutil.rmtree(pasta, ignore_errors=True)

    def test_fluxo_pede_ok_roda_as_etapas_e_desfaz(self):
        s = self.s
        pasta = tempfile.mkdtemp(prefix="clave-fluxo-")
        try:
            _, r = s.pedir("POST", "/api/conversas", {"modo": "code", "pasta": pasta})
            cid = r["conversa"]["id"]
            _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "rode isso como um fluxo",
                                                                    "opcoes": {"permissao": "perguntar"}})
            eid = r["execucao"]
            propostas = []

            def decidir(ev):
                if ev["tipo"] == "fluxo_proposta":
                    propostas.append(ev["proposta"])
                    return "permitir", {"etapas": [{"i": 0, "modelo": "haiku"}], "teto_usd": 5}
                return "permitir"
            evs = s.eventos(eid, decidir)
            self.assertEqual(len(propostas), 1)
            self.assertEqual([e["grupo"] for e in propostas[0]["etapas"]], [0, 1, 2, 2])
            tipos = [e["tipo"] for e in evs]
            for t in ("fluxo_inicio", "etapa_inicio", "etapa_fim", "fluxo_fim"):
                self.assertIn(t, tipos)
            self.assertTrue(any(e["tipo"] == "etapa_evento" and e["ev"]["tipo"] == "aprovacao" for e in evs),
                            "a etapa que cria arquivo pede OK na conversa principal")
            self.assertTrue((Path(pasta) / "exemplo-do-fluxo.txt").exists())
            fid = next(e["fluxo"] for e in evs if e["tipo"] == "fluxo_inicio")
            _, f = s.pedir("GET", f"/api/fluxos/{fid}")
            f = f["fluxo"]
            self.assertEqual(f["status"], "concluido")
            self.assertEqual(f["etapas"][0]["modelo"], "claude-haiku-5-5", "a troca de modelo do cartão vale")
            self.assertTrue(all(e["status"] == "concluida" for e in f["etapas"]))
            _, lista = s.pedir("GET", "/api/conversas")
            self.assertFalse(any(c["modo"] == "etapa" for c in lista["conversas"]), "etapas ficam escondidas")
            _, d = s.pedir("POST", f"/api/execucoes/{eid}/desfazer")
            self.assertTrue(any("exemplo-do-fluxo.txt" in a for a in d["arquivos"]), "o Desfazer cobre as etapas")
            self.assertFalse((Path(pasta) / "exemplo-do-fluxo.txt").exists())
            _, h = s.pedir("GET", "/api/permissoes/historico")
            self.assertTrue(any(x["ferramenta"] == "executar_fluxo" and x["decisao"] == "permitir" for x in h["registros"]))
        finally:
            shutil.rmtree(pasta, ignore_errors=True)

    def test_fluxo_recusado_nao_roda_nada(self):
        s = self.s
        _, r = s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "faça um fluxo"})
        evs = s.eventos(r["execucao"], decidir="recusar")
        self.assertTrue(any(e["tipo"] == "fluxo_proposta" for e in evs))
        self.assertFalse(any(e["tipo"] == "etapa_inicio" for e in evs))
        fid = next(e["id"] for e in evs if e["tipo"] == "fluxo_proposta")
        _, f = s.pedir("GET", f"/api/fluxos/{fid}")
        self.assertEqual(f["fluxo"]["status"], "recusado")

    def test_rotina_para_quando_precisa_de_ok_e_roda_com_regra(self):
        s = self.s
        pasta = tempfile.mkdtemp(prefix="clave-rotina-")
        try:
            st, r = s.pedir("POST", "/api/rotinas", {"nome": "Teste", "prompt": "crie um arquivo", "modo": "code",
                                                    "pasta": pasta, "quando": {"tipo": "diaria", "hora": "08:00"}})
            self.assertEqual(st, 200, r)
            rid = r["rotina"]["id"]
            _, run = s.pedir("POST", f"/api/rotinas/{rid}/rodar")
            evs = s.eventos(run["execucao"])
            self.assertTrue(any(e["tipo"] == "rotina_parou" for e in evs))
            self.assertFalse(any(e["tipo"] == "aprovacao" for e in evs), "rotina nunca pergunta")
            self.assertFalse((Path(pasta) / "exemplo-do-clave.txt").exists())
            time.sleep(0.3)
            _, lista = s.pedir("GET", "/api/rotinas")
            rot = next(x for x in lista["rotinas"] if x["id"] == rid)
            self.assertIn("precisaria de OK", rot["ultimo_status"])
            st, _ = s.pedir("POST", "/api/permissoes", {"escopo": "pasta", "pasta": pasta, "acao": "allow",
                                                        "regra": "Edit(exemplo-do-clave.txt)"})
            self.assertEqual(st, 200)
            _, run = s.pedir("POST", f"/api/rotinas/{rid}/rodar")
            s.eventos(run["execucao"])
            self.assertTrue((Path(pasta) / "exemplo-do-clave.txt").exists())
            time.sleep(0.3)
            _, av = s.pedir("GET", "/api/avisos?desde=0")
            self.assertGreaterEqual(len([a for a in av["avisos"] if a.get("rotina") == rid]), 2)
            s.pedir("DELETE", f"/api/rotinas/{rid}")
        finally:
            shutil.rmtree(pasta, ignore_errors=True)

    def test_sugestao_de_outra_conversa_so_abre_com_clique(self):
        s = self.s
        _, r = s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "responda e sugira outra conversa"})
        evs = s.eventos(r["execucao"])
        sug = [e for e in evs if e["tipo"] == "sugestao_conversa"]
        self.assertEqual(len(sug), 1, "a API falsa sugere uma conversa quando o pedido fala nisso")
        sid = sug[0]["id"]
        _, est = s.pedir("GET", f"/api/sugestoes/{sid}")
        self.assertEqual(est["estado"], "nova", "sugerir não abre nada sozinho")
        status, ab = s.pedir("POST", f"/api/sugestoes/{sid}/abrir", {"conversa_id": cid})
        self.assertEqual(status, 200)
        nova = ab["conversa"]
        self.assertEqual(nova["titulo"], sug[0]["titulo"])
        self.assertEqual(nova["modo"], "chat")
        s.eventos(ab["execucao"])
        _, v = s.pedir("GET", f"/api/conversas/{nova['id']}")
        primeira = next(m for m in v["mensagens"] if m["papel"] == "user")
        self.assertEqual(primeira["conteudo"][0]["text"], sug[0]["pedido"])
        self.assertTrue(any(m["papel"] == "assistant" for m in v["mensagens"]), "a conversa nova já roda o pedido")
        _, est = s.pedir("GET", f"/api/sugestoes/{sid}")
        self.assertEqual((est["estado"], est["conversa"]["id"]), ("aberta", nova["id"]))
        _, de_novo = s.pedir("POST", f"/api/sugestoes/{sid}/abrir", {"conversa_id": cid})
        self.assertTrue(de_novo.get("ja_aberta"), "abrir duas vezes não cria outra conversa")
        status, _ = s.pedir("POST", "/api/sugestoes/toolu_que_nao_existe/abrir", {"conversa_id": cid})
        self.assertEqual(status, 404)

    def test_painel_de_uso_e_precos_pela_api(self):
        s = self.s
        status, d = s.pedir("GET", "/api/uso/painel")
        self.assertEqual(status, 200)
        for chave in ("tokens_total", "dias_seguidos", "recorde", "mapa", "ultimos7", "favorito", "projecao"):
            self.assertIn(chave, d["painel"])
        status, d = s.pedir("GET", "/api/precos")
        self.assertEqual(status, 200)
        self.assertEqual([p["id"] for p in d["planos"]], ["pro", "max5", "max20"])
        self.assertTrue(any(m["id"] == "claude-haiku-5-5" for m in d["modelos"]))
        status, d = s.pedir("POST", "/api/precos/estimar", {"plano": "max5", "janelas": 5, "porcentagem": 100})
        self.assertEqual((status, d["mensagens_mes"]), (200, round(5 * 45 * 5 * 52 / 12)))
        status, _ = s.pedir("POST", "/api/precos/estimar", {"plano": "pro", "janelas": "muitas"})
        self.assertEqual(status, 400)

    def test_permissoes_pela_api(self):
        s = self.s
        st, r = s.pedir("POST", "/api/permissoes", {"escopo": "app", "acao": "deny", "regra": "Bash(git push *)"})
        self.assertEqual(st, 200)
        st, r = s.pedir("POST", "/api/permissoes", {"escopo": "app", "acao": "allow", "regra": "Bash(sem fechar"})
        self.assertEqual(st, 400)
        _, t = s.pedir("POST", "/api/permissoes/testar", {"ferramenta": "Bash", "valor": "git push origin main"})
        self.assertEqual(t["decisao"], "negar")
        _, t = s.pedir("POST", "/api/permissoes/testar", {"ferramenta": "Bash", "valor": "git status"})
        self.assertEqual((t["decisao"], t["sugestao"]), ("perguntar", "Bash(git status *)"))
        st, _ = s.pedir("DELETE", "/api/permissoes", {"escopo": "app", "acao": "deny", "regra": "Bash(git push *)"})
        self.assertEqual(st, 200)

    def test_comandos_e_plugins_pela_api(self):
        s = self.s
        _, c = s.pedir("GET", "/api/comandos")
        nomes = [x["nome"] for x in c["comandos"]]
        self.assertIn("fluxo", nomes)
        self.assertIn("fluxo pesquisa-profunda", nomes)
        _, p = s.pedir("GET", "/api/plugins")
        self.assertGreaterEqual(len([x for x in p["plugins"] if x["origem"] == "embutido"]), 7)
        _, a = s.pedir("GET", "/api/agentes")
        self.assertIn("planejador", [x["nome"] for x in a["agentes"]])

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
