"""5.0: a aba Tarefas. O registro das tarefas, os comandos em segundo plano (Job Object: a árvore inteira morre ao
parar, no tempo limite e quando o Clave fecha), o neto que segurava a saída e as rotas, pelo servidor de verdade."""
import ctypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

import base
import banco
import config
import execucao
import tarefas
from ferramentas import code as fc
from rotas import Erro
from test_servidor import Servidor, porta_livre

PY = sys.executable.replace("'", "''")
SERVIDOR = base.RAIZ / "servidor"


def vivo(pid: int) -> bool:
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.restype = ctypes.c_void_p
    k.OpenProcess.argtypes = (ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32)
    k.GetExitCodeProcess.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32))
    k.CloseHandle.argtypes = (ctypes.c_void_p,)
    h = k.OpenProcess(0x1000, 0, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    codigo = ctypes.c_uint32()
    k.GetExitCodeProcess(h, ctypes.byref(codigo))
    k.CloseHandle(h)
    return codigo.value == 259  # STILL_ACTIVE


def esperar(condicao, tempo=10.0, passo=0.1) -> bool:
    fim = time.time() + tempo
    while time.time() < fim:
        if condicao():
            return True
        time.sleep(passo)
    return condicao()


def matar_pid(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=0x08000000)


# Um "servidor" de mentira: abre um filho (que grava o próprio PID), mostra os PIDs, um endereço local colorido como o
# do npm e do vite, e segue escrevendo para sempre.
SRV = r'''
import os, subprocess, sys, time
from pathlib import Path
marca = Path(__file__).parent / f"filho-{os.getpid()}.pid"
filho = subprocess.Popen([sys.executable, "-c", f"import os, time; open(r'{marca}', 'w').write(str(os.getpid())); time.sleep(120)"])
for _ in range(200):
    if marca.exists() and marca.read_text():
        break
    time.sleep(0.05)
print("PIDS", os.getpid(), filho.pid, marca.read_text(), flush=True)
print("\x1b[36mServidor em http://localhost:\x1b[1m" + sys.argv[1] + "\x1b[22m/\x1b[39m", flush=True)
i = 0
while True:
    print("linha", i, flush=True)
    i += 1
    time.sleep(0.3)
'''

# O pai que deixa um neto segurando a saída e sai (o vazamento antigo: thread e cano presos para sempre).
PAI = r'''
import subprocess, sys, time
subprocess.Popen([sys.executable, "-c", "import os, time; print('NETO', os.getpid(), flush=True); time.sleep(120)"],
                 stdout=sys.stdout, stderr=sys.stderr)
time.sleep(1.5)
print("PAI saindo", flush=True)
'''

# Um programa aberto de propósito numa janela própria (Start-Process): não segura a saída e não deve morrer.
JANELA = r'''
import os, time
from pathlib import Path
(Path(__file__).parent / "janela.pid").write_text(str(os.getpid()))
time.sleep(60)
'''


# Um programa com janela de verdade (o mesmo do teste do console) e um que só dorme, sem escrever nada.
from test_5_0_console import JANELA as JANELA_VISIVEL, PYTHONW as _PYTHONW  # noqa: E402

PYW = _PYTHONW.replace("'", "''")
DORME = r'''
import os, time
from pathlib import Path
(Path(__file__).parent / "dorme.pid").write_text(str(os.getpid()))
time.sleep(60)
'''


def pid_no_arquivo(arq: Path, tempo: float = 15) -> int:
    fim = time.time() + tempo
    while time.time() < fim:
        try:
            return int(arq.read_text().strip())
        except (OSError, ValueError):
            time.sleep(0.1)
    return 0


def pids_de(texto: str) -> list[int]:
    m = re.search(r"PIDS (\d+) (\d+) (\d+)", texto)
    return [int(x) for x in m.groups()] if m else []


class Base(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-tarefas-"))
        (self.pasta / "srv.py").write_text(SRV, encoding="utf-8")
        (self.pasta / "pai.py").write_text(PAI, encoding="utf-8")
        (self.pasta / "janela.py").write_text(JANELA, encoding="utf-8")
        self.ctx = self.contexto()
        self.pids: list[int] = []

    def contexto(self, conversa=None) -> fc.Contexto:
        return fc.Contexto(raiz=self.pasta.resolve(), protegidos=[".env"], execucao_id=banco.novo_id(),
                           conversa_id=conversa or "conv-" + banco.novo_id())

    def tearDown(self):
        for f in list(fc._fundos.values()):
            if f.rodando:
                fc._parar_fundo(f.tarefa.id)
        for pid in self.pids:
            if vivo(pid):
                matar_pid(pid)
        shutil.rmtree(self.pasta, ignore_errors=True)

    def em_segundo_plano(self, comando, ctx=None, descricao="servidor de teste"):
        return fc.executar("rodar_comando", {"comando": comando, "descricao": descricao, "em_segundo_plano": True},
                           ctx or self.ctx)


class TestRegistro(unittest.TestCase):
    def test_registrar_atualizar_terminar(self):
        tf = tarefas.registrar("download", "Vídeo da lição", detalhe="Baixando")
        self.assertTrue(tf.id.startswith("download-"))
        tf.atualizar(progresso=0.5, detalhe="1 MB / 2 MB")
        tf.atualizar(detalhe="1.5 MB / 2 MB")  # sem progresso: mantém o que estava
        item = tf.item()
        self.assertEqual((item["status"], item["progresso"], item["detalhe"]), ("rodando", 0.5, "1.5 MB / 2 MB"))
        self.assertFalse(item["pode_parar"], "sem parar=, não há como parar")
        self.assertFalse(item["registro"], "download que não escreveu nada não tem registro para ver")
        tf.atualizar(progresso=None)
        self.assertIsNone(tf.item()["progresso"], "None diz que não dá para saber o progresso")
        tf.atualizar(progresso=7)
        self.assertEqual(tf.progresso, 1.0)
        self.assertIn(tf.id, [i["id"] for i in tarefas.listar()["rodando"]])
        tf.terminar("concluida", "Pronto")
        tf.terminar("erro")  # a primeira palavra vale
        lista = tarefas.listar()
        self.assertNotIn(tf.id, [i["id"] for i in lista["rodando"]])
        item = next(i for i in lista["terminadas"] if i["id"] == tf.id)
        self.assertEqual((item["status"], item["detalhe"]), ("concluida", "Pronto"))
        self.assertIsNotNone(item["fim"])
        with self.assertRaises(ValueError):
            tarefas.registrar("outra coisa", "x")

    def test_registro_limitado_e_espelhado_no_arquivo(self):
        tf = tarefas.registrar("comando", "barulhento")
        linha = "x" * 99 + "\n"
        for i in range(3000):  # 300 KB
            tf.saida(f"{i:05d}" + linha)
        texto = tf.registro()
        self.assertLessEqual(len(texto), tarefas.LIMITE_REGISTRO)
        self.assertTrue(tf.cortado)
        self.assertTrue(texto.rstrip().endswith("x"))
        self.assertIn("02999", tf.registro(1))
        arq = config.DADOS / "tarefas" / f"{tf.id}.log"
        self.assertTrue(arq.is_file())
        self.assertIn("02999", arq.read_text(encoding="utf-8")[-200:])
        tf.terminar("concluida")

    def test_enderecos_locais(self):
        tf = tarefas.registrar("comando", "vite")
        tf.saida("  \x1b[32m>\x1b[39m  Local:   \x1b[36mhttp://localhost:\x1b[1m51")  # o endereço chega em pedaços
        self.assertEqual(tf.urls, [])
        tf.saida("73\x1b[22m/\x1b[3")  # e o código de cor também chega partido
        tf.saida("9m\r")
        tf.saida("\n")
        tf.saida("Serving HTTP on :: port 8000 (http://[::]:8000/) ...\n")
        tf.saida("também em http://127.0.0.1:3000. e https://0.0.0.0:8443/api fora http://exemplo.com:80/\n")
        self.assertEqual(tf.urls, ["http://localhost:5173/", "http://localhost:8000/", "http://127.0.0.1:3000/",
                                   "https://localhost:8443/api"])
        self.assertIn("http://localhost:5173/", tarefas.urls_locais())
        self.assertTrue(any(d["tarefa"] == tf.id for d in tarefas.urls_locais(detalhes=True)))
        self.assertNotIn("\x1b", tf.registro(), "o registro sai sem os códigos de cor")
        self.assertTrue(tf.registro().startswith("  >  Local:   http://localhost:5173/\nServing"), repr(tf.registro()[:80]))
        tf.terminar("parada")
        self.assertNotIn("http://localhost:5173/", tarefas.urls_locais(), "só os comandos que ainda rodam")

    def test_terminadas_saem_depois_de_30_minutos(self):
        tf = tarefas.registrar("comando", "velho")
        tf.saida("oi\n")
        tf.terminar("concluida")
        arq = config.DADOS / "tarefas" / f"{tf.id}.log"
        self.assertTrue(arq.is_file())
        tf.fim = time.time() - 31 * 60
        self.assertNotIn(tf.id, [i["id"] for i in tarefas.listar()["terminadas"]])
        self.assertIsNone(tarefas.pegar(tf.id))
        self.assertFalse(arq.exists())

    def test_parar_pela_lista(self):
        chamadas = []
        tf = tarefas.registrar("download", "parável", parar=lambda: (chamadas.append(1), tf.terminar("parada")))
        self.assertTrue(tf.item()["pode_parar"])
        self.assertEqual(tarefas.parar(tf.id), {"ok": True, "ja_terminou": False})
        self.assertEqual((chamadas, tf.status), ([1], "parada"))
        self.assertTrue(tarefas.parar(tf.id)["ja_terminou"])
        teimoso = tarefas.registrar("download", "sem parar")
        with self.assertRaises(Erro) as e:
            tarefas.parar(teimoso.id)
        self.assertEqual(e.exception.status, 409)
        with self.assertRaises(Erro) as e:
            tarefas.parar("comando-naoexiste")
        self.assertEqual(e.exception.status, 404)
        teimoso.terminar("concluida")

    def test_varias_threads_ao_mesmo_tempo(self):
        tf = tarefas.registrar("comando", "concorrente")
        erros = []

        def escrever(n):
            try:
                for i in range(300):
                    tf.saida(f"t{n} {i} http://localhost:{4000 + n}/\n")
                    tf.item()
                    tarefas.listar()
            except Exception as e:  # noqa: BLE001
                erros.append(e)
        ths = [threading.Thread(target=escrever, args=(n,)) for n in range(6)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        self.assertEqual(erros, [])
        self.assertEqual(len(tf.urls), 6)
        self.assertEqual(tf.registro().count("\n"), 1800)
        tf.terminar("concluida")


class TestRespostasNaLista(unittest.TestCase):
    """As respostas, rotinas e ajudantes lidos de execucao._execucoes."""

    def setUp(self):
        self.criadas = []

    def tearDown(self):
        for ex in self.criadas:
            execucao._execucoes.pop(ex.id, None)

    def execucao(self, modo, status, duracao=None, op=None, titulo="Conversa de teste", ajustes=None):
        conv = banco.criar_conversa(modo, titulo=titulo, ajustes=ajustes or {})
        ex = execucao.Execucao(conv["id"], op or {})
        ex.status = status
        if duracao is not None:
            ex.fim_em = time.time() - 2
            ex.inicio = ex.fim_em - duracao
        execucao.registrar(ex)
        self.criadas.append(ex)
        return ex

    def ids(self):
        lista = tarefas.listar()
        return {i["id"]: i for i in lista["rodando"]}, {i["id"]: i for i in lista["terminadas"]}

    def test_quais_entram(self):
        rodando = self.execucao("chat", "esperando")
        rodando.custo_total = 0.012
        curta = self.execucao("chat", "concluida", duracao=5)
        longa = self.execucao("code", "concluida", duracao=45)
        ajudante = self.execucao("tutor", "rodando")
        rot = self.execucao("chat", "rodando", op={"rotina": True}, titulo="Rotina: Resumo · 15/10 08:00",
                            ajustes={"rotina": "nao-existe"})
        r, f = self.ids()
        item = r[f"resposta-{rodando.id}"]
        self.assertEqual((item["tipo"], item["status"], item["titulo"], item["custo"]),
                         ("resposta", "esperando", "Conversa de teste", 0.012))
        self.assertEqual(item["conversa_id"], rodando.conversa_id)
        self.assertTrue(item["pode_parar"])
        self.assertNotIn(f"resposta-{curta.id}", f, "resposta curta que terminou não é segundo plano")
        self.assertEqual(f[f"resposta-{longa.id}"]["status"], "concluida")
        self.assertFalse(any(ajudante.id in k for k in list(r) + list(f)), "ajudante de lição fica de fora")
        self.assertEqual(r[f"rotina-{rot.id}"]["tipo"], "rotina")
        self.assertNotIn(f"resposta-{rot.id}", r)

    def test_parar_uma_resposta(self):
        ex = self.execucao("chat", "rodando")
        self.assertEqual(tarefas.parar(f"resposta-{ex.id}"), {"ok": True, "ja_terminou": False})
        self.assertTrue(ex.parar.is_set())
        d = tarefas.detalhes(f"resposta-{ex.id}")
        self.assertEqual(d["tarefa"]["tipo"], "resposta")


class TestComandoEmSegundoPlano(Base):
    def test_endereco_ver_e_parar_mata_a_arvore(self):
        inicio = time.time()
        r = self.em_segundo_plano(f"& '{PY}' srv.py 8765")
        self.assertLess(time.time() - inicio, 9, "devolve em poucos segundos")
        self.assertIn("segundo plano", r)
        self.assertIn("http://localhost:8765/", r)
        tid = re.search(r"\(id (comando-\w+)\)", r).group(1)
        pids = pids_de(r)
        self.assertEqual(len(pids), 3, r)
        self.pids += pids
        self.assertTrue(all(vivo(p) for p in pids))
        tf = tarefas.pegar(tid)
        self.assertEqual((tf.conversa_id, tf.tipo, tf.titulo), (self.ctx.conversa_id, "comando", "servidor de teste"))
        self.assertEqual(tarefas.urls_locais()[0] if tarefas.urls_locais() else None, "http://localhost:8765/")
        self.assertTrue(esperar(lambda: "linha 3" in tf.registro(), 10))
        visto = fc.executar("ver_comando", {"id": tid, "linhas": 3}, self.ctx)
        self.assertIn("ainda rodando", visto)
        self.assertIn("http://localhost:8765/", visto)
        self.assertRegex(visto, r"linha \d+")
        self.assertTrue((config.DADOS / "tarefas" / f"{tid}.log").is_file())
        parou = fc.executar("parar_comando", {"id": tid}, self.ctx)
        self.assertIn("Parei", parou)
        self.assertTrue(esperar(lambda: not any(vivo(p) for p in pids), 8), "o comando, o filho e o neto morrem")
        self.assertEqual(tf.status, "parada")
        self.assertIn("já tinha terminado", fc.executar("parar_comando", {"id": tid}, self.ctx))
        self.assertIn("parado", fc.executar("ver_comando", {"id": tid}, self.ctx))

    def test_outra_conversa_nao_ve_nem_para(self):
        r = self.em_segundo_plano(f"& '{PY}' srv.py 8766")
        self.pids += pids_de(r)
        tid = re.search(r"\(id (comando-\w+)\)", r).group(1)
        outra = self.contexto()
        for nome in ("ver_comando", "parar_comando"):
            with self.assertRaises(fc.ErroFerramenta):
                fc.executar(nome, {"id": tid}, outra)
        self.assertTrue(tarefas.pegar(tid).rodando)
        with self.assertRaises(fc.ErroFerramenta) as e:
            fc.executar("ver_comando", {"id": "comando-errado"}, self.ctx)
        self.assertIn(tid, str(e.exception), "o erro lista os comandos desta conversa")

    def test_no_maximo_5_por_conversa(self):
        for i in range(5):
            r = self.em_segundo_plano(f"& '{PY}' srv.py {9100 + i}")
            self.pids += pids_de(r)
        with self.assertRaises(fc.ErroFerramenta) as e:
            self.em_segundo_plano(f"& '{PY}' srv.py 9199")
        self.assertIn("máximo", str(e.exception))
        r = self.em_segundo_plano(f"& '{PY}' srv.py 9198", ctx=self.contexto())  # outra conversa pode
        self.pids += pids_de(r)
        self.assertIn("segundo plano", r)
        # parou um, abre vaga
        primeiro = next(f for f in fc._fundos.values() if f.conversa_id == self.ctx.conversa_id and f.rodando)
        fc.executar("parar_comando", {"id": primeiro.tarefa.id}, self.ctx)
        r = self.em_segundo_plano(f"& '{PY}' srv.py 9197")
        self.pids += pids_de(r)
        self.assertIn("segundo plano", r)

    def test_comando_que_termina_logo(self):
        r = self.em_segundo_plano("Write-Output 'pronto'", descricao="eco")
        self.assertIn("terminou logo", r)
        self.assertIn("código 0", r)
        self.assertIn("pronto", r)
        tid = re.search(r"\(id (comando-\w+)\)", r).group(1)
        self.assertEqual(tarefas.pegar(tid).status, "concluida")

    def test_permissao_e_a_mesma_de_qualquer_comando(self):
        e = {"comando": "npm run dev", "descricao": "sobe o site", "em_segundo_plano": True}
        esperado = {"perguntar": "perguntar", "aceitar_edicoes": "perguntar", "plano": "negar", "livre": "auto"}
        for modo, decisao in esperado.items():
            self.assertEqual(fc.classificar("rodar_comando", e, self.ctx, modo, set())[0], decisao, modo)
        perigoso = {**e, "comando": "npm run dev; Remove-Item build -Recurse"}
        self.assertEqual(fc.classificar("rodar_comando", perigoso, self.ctx, "livre", set())[0], "perguntar")
        for nome in ("ver_comando", "parar_comando"):
            for modo in ("perguntar", "plano"):
                self.assertEqual(fc.classificar(nome, {"id": "comando-x"}, self.ctx, modo, set())[0], "auto")
        self.assertIn("tipo", fc.validar("rodar_comando", {**e, "em_segundo_plano": "sim"}))
        nomes = {d["name"] for d in fc.definicoes(com_skills=False)}
        self.assertTrue({"ver_comando", "parar_comando"} <= nomes)
        props = next(d for d in fc.definicoes(False) if d["name"] == "rodar_comando")["input_schema"]["properties"]
        self.assertEqual(props["em_segundo_plano"]["type"], "boolean")

    def test_encerrar_tudo_ao_fechar(self):
        r = self.em_segundo_plano(f"& '{PY}' srv.py 8767")
        pids = pids_de(r)
        self.pids += pids
        tid = re.search(r"\(id (comando-\w+)\)", r).group(1)
        fc.encerrar_segundo_plano()  # o que o atexit chama
        self.assertTrue(esperar(lambda: not any(vivo(p) for p in pids), 8))
        self.assertTrue(esperar(lambda: tarefas.pegar(tid).status == "parada", 5))

    def test_clave_morto_a_forca_leva_o_comando_junto(self):
        """Sem atexit (o processo do Clave morre de repente): o Windows fecha o handle do job e mata a árvore."""
        script = self.pasta / "clave_falso.py"
        script.write_text(
            "import os, sys\n"
            f"sys.path.insert(0, r'{SERVIDOR}')\n"
            "from pathlib import Path\n"
            "import banco\n"
            "from ferramentas import code as fc\n"
            "ctx = fc.Contexto(raiz=Path(sys.argv[1]).resolve(), protegidos=[], execucao_id=banco.novo_id(), conversa_id='c')\n"
            "r = fc.executar('rodar_comando', {'comando': sys.argv[2], 'descricao': 'x', 'em_segundo_plano': True}, ctx)\n"
            "print(r, flush=True)\n"
            "os._exit(0)\n", encoding="utf-8")
        dados = tempfile.mkdtemp(prefix="clave-testes-morte-")
        env = {**os.environ, "CLAVE_DADOS": dados, "PYTHONIOENCODING": "utf-8"}
        try:
            r = subprocess.run([sys.executable, str(script), str(self.pasta), f"& '{PY}' srv.py 8768"], env=env,
                               capture_output=True, timeout=60, encoding="utf-8", creationflags=0x08000000)
            pids = pids_de(r.stdout)
            self.pids += pids
            self.assertEqual(len(pids), 3, r.stdout + r.stderr)
            self.assertTrue(esperar(lambda: not any(vivo(p) for p in pids), 10), "a árvore morreu junto com o Clave")
        finally:
            shutil.rmtree(dados, ignore_errors=True)


class TestComandoNormal(Base):
    def test_neto_que_segura_a_saida_nao_vaza_mais(self):
        antes = threading.active_count()
        inicio = time.time()
        r = fc.executar("rodar_comando", {"comando": f"& '{PY}' pai.py", "descricao": "pai e neto",
                                          "tempo_limite_s": 60}, self.ctx)
        self.assertLess(time.time() - inicio, 20)
        self.assertIn("Código de saída: 0", r)
        self.assertIn("PAI saindo", r)
        self.assertIn("encerrou esse processo junto", r)
        neto = int(re.search(r"NETO (\d+)", r).group(1))
        self.pids.append(neto)
        self.assertTrue(esperar(lambda: not vivo(neto), 5), "o neto morreu junto")
        self.assertTrue(esperar(lambda: threading.active_count() <= antes, 5), "a thread de leitura terminou")
        self.assertIsNone(self.ctx.processo)

    def test_tempo_limite_mata_a_arvore(self):
        r = fc.executar("rodar_comando", {"comando": f"& '{PY}' srv.py 8769", "descricao": "lento",
                                          "tempo_limite_s": 5}, self.ctx)
        self.assertIn("tempo limite", r)
        pids = pids_de(r)
        self.pids += pids
        self.assertEqual(len(pids), 3, r)
        self.assertTrue(esperar(lambda: not any(vivo(p) for p in pids), 8))

    def test_programa_aberto_de_proposito_continua(self):
        r = fc.executar("rodar_comando", {"comando": f"Start-Process -WindowStyle Hidden -FilePath '{PY}' "
                                                     "-ArgumentList 'janela.py'", "descricao": "abre"}, self.ctx)
        self.assertIn("Código de saída: 0", r)
        marca = self.pasta / "janela.pid"
        self.assertTrue(esperar(lambda: marca.exists() and marca.read_text().strip(), 10))
        pid = int(marca.read_text())
        self.pids.append(pid)
        time.sleep(1.5)
        self.assertTrue(vivo(pid), "quem não segura a saída (Start-Process) continua rodando")
        self.assertNotIn("encerrou esse processo", r)


class TestJanelasEProcessosQueSobram(Base):
    """Programas com janela sobrevivem ao parar e ao Clave fechar normal; o que um Start-Process escondido deixa
    rodando continua acompanhado; Parar durante a espera para o comando."""

    def setUp(self):
        super().setUp()
        (self.pasta / "janela_visivel.py").write_text(JANELA_VISIVEL, encoding="utf-8")
        (self.pasta / "dorme.py").write_text(DORME, encoding="utf-8")

    def janela_e_servidor(self, porta):
        import console
        marca = self.pasta / "janela.pid"
        r = self.em_segundo_plano(f"& '{PYW}' janela_visivel.py '{marca}' 90; & '{PY}' srv.py {porta}")
        janela = pid_no_arquivo(marca)
        self.assertTrue(janela, r)
        self.pids.append(janela)
        self.assertTrue(esperar(lambda: janela in console.pids_com_janela(), 10), "a janela de teste não apareceu")
        pids = pids_de(r)
        self.assertEqual(len(pids), 3, r)
        self.pids += pids
        return re.search(r"\(id (comando-\w+)\)", r).group(1), janela, pids

    def test_parar_deixa_a_janela_e_derruba_o_servidor(self):
        tid, janela, pids = self.janela_e_servidor(8774)
        parou = fc.executar("parar_comando", {"id": tid}, self.ctx)
        self.assertIn("1 programa(s) com janela", parou)
        self.assertTrue(esperar(lambda: not any(vivo(p) for p in pids), 8), "o servidor (sem janela) morre")
        time.sleep(1.5)
        self.assertTrue(vivo(janela), "o programa com janela continua aberto")
        tf = tarefas.pegar(tid)
        self.assertEqual(tf.status, "parada")
        self.assertIn("com janela continuam abertos", tf.detalhe)

    def test_clave_fechando_normal_deixa_a_janela(self):
        tid, janela, pids = self.janela_e_servidor(8779)
        fc.encerrar_segundo_plano()
        self.assertTrue(esperar(lambda: not any(vivo(p) for p in pids), 8))
        self.assertTrue(esperar(lambda: tarefas.pegar(tid).status == "parada", 5))
        time.sleep(1.5)
        self.assertTrue(vivo(janela), "o programa com janela fechou junto com o Clave")

    def test_comando_normal_que_abre_uma_janela_nao_fecha_ela(self):
        """O programa com janela herda o cano da saída do PowerShell: antes, o Clave matava ele 3 s depois do comando
        acabar, achando que era um processo esquecido segurando a saída."""
        import console
        marca = self.pasta / "janela.pid"
        inicio = time.time()
        r = fc.executar("rodar_comando", {"comando": f"& '{PYW}' janela_visivel.py '{marca}' 90; Write-Output pronto",
                                          "descricao": "abre uma janela", "tempo_limite_s": 60}, self.ctx)
        self.assertLess(time.time() - inicio, 20)
        janela = pid_no_arquivo(marca)
        self.assertTrue(janela, r)
        self.pids.append(janela)
        self.assertIn("Código de saída: 0", r)
        self.assertIn("pronto", r)
        self.assertNotIn("encerrou esse processo", r)
        time.sleep(1.5)
        self.assertTrue(vivo(janela), "a janela que o comando abriu continua aberta")
        self.assertIn(janela, console.pids_com_janela())
        self.assertIsNone(self.ctx.processo)

    def test_start_process_escondido_continua_acompanhado(self):
        r = self.em_segundo_plano(f"Start-Process -WindowStyle Hidden -FilePath '{PY}' -ArgumentList 'srv.py','8775'")
        tid = re.search(r"\(id (comando-\w+)\)", r).group(1)
        self.assertNotIn("nada ficou rodando", r)
        self.assertIn("continuam rodando dentro dele", r)
        tf = tarefas.pegar(tid)
        self.assertTrue(tf.rodando, "o terminal saiu, mas o servidor que ele escondeu ainda roda")
        self.assertTrue(esperar(lambda: list(self.pasta.glob("filho-*.pid")), 10))
        marca = next(self.pasta.glob("filho-*.pid"))
        srv, filho = int(marca.stem.split("-")[1]), pid_no_arquivo(marca)
        self.pids += [srv, filho]
        self.assertTrue(vivo(srv) and vivo(filho))
        self.assertIn("[O terminal do comando saiu com o código 0", tf.registro())
        self.assertIn("processo(s) que o comando abriu continuam rodando", tf.detalhe)
        self.assertIn("o terminal saiu", fc.executar("ver_comando", {"id": tid}, self.ctx))
        self.assertIn("Parei", fc.executar("parar_comando", {"id": tid}, self.ctx))
        self.assertTrue(esperar(lambda: not vivo(srv) and not vivo(filho), 8), "o servidor escondido morre ao parar")
        self.assertEqual(tf.status, "parada")

    def test_processo_que_sobrou_terminando_sozinho_fecha_a_tarefa(self):
        r = self.em_segundo_plano("Start-Process -WindowStyle Hidden -FilePath powershell -ArgumentList "
                                  "'-NoProfile','-Command','Start-Sleep -Seconds 3'")
        tid = re.search(r"\(id (comando-\w+)\)", r).group(1)
        tf = tarefas.pegar(tid)
        self.assertTrue(tf.rodando, r)
        self.assertTrue(esperar(lambda: not tf.rodando, 15), "a tarefa acaba quando o que sobrou termina")
        self.assertEqual(tf.status, "concluida")

    def test_parar_durante_a_espera_para_o_comando(self):
        marca = self.pasta / "dorme.pid"

        def apertar_parar():
            pid_no_arquivo(marca, 10)
            self.ctx.parar.set()
        threading.Thread(target=apertar_parar, daemon=True).start()
        r = self.em_segundo_plano(f"& '{PY}' dorme.py", descricao="dorme")
        self.assertIn("interrompida", r)
        pid = pid_no_arquivo(marca)
        self.assertTrue(pid)
        self.pids.append(pid)
        self.assertTrue(esperar(lambda: not vivo(pid), 8), "o comando não fica rodando depois do Parar")
        tid = re.search(r"comando-\w+", r).group(0)
        self.assertEqual(tarefas.pegar(tid).status, "parada")

    def test_comando_que_terminou_sem_saida(self):
        r = self.em_segundo_plano("$null = 1", descricao="nada")
        self.assertIn("terminou logo", r)
        self.assertIn("terminou sem nenhuma saída", r)
        self.assertNotIn("ainda sem saída", r)


class TestConversas(Base):
    """A etapa de um fluxo trabalha para a conversa principal; apagar uma conversa para o que é dela."""

    def test_comando_da_etapa_e_da_conversa_principal(self):
        mae = banco.criar_conversa("code", pasta=str(self.pasta), titulo="Conversa principal")
        etapa = banco.criar_conversa("etapa", pasta=str(self.pasta), titulo="Fluxo · etapa 1",
                                     ajustes={"fluxo": "f1", "etapa": 0, "modo_base": "code", "conversa_mae": mae["id"]})
        ctx_etapa, ctx_mae = self.contexto(etapa["id"]), self.contexto(mae["id"])
        r = self.em_segundo_plano(f"& '{PY}' srv.py 8776", ctx=ctx_etapa)
        self.pids += pids_de(r)
        tid = re.search(r"\(id (comando-\w+)\)", r).group(1)
        self.assertEqual(tarefas.pegar(tid).conversa_id, mae["id"])
        self.assertIn("ainda rodando", fc.executar("ver_comando", {"id": tid}, ctx_mae))
        item = next(i for i in tarefas.listar()["rodando"] if i["id"] == tid)
        self.assertEqual((item["conversa_id"], item["conversa_existe"], item["conversa_titulo"]),
                         (mae["id"], True, "Conversa principal"))
        self.assertIn("Parei", fc.executar("parar_comando", {"id": tid}, ctx_mae))

    def test_parar_da_conversa(self):
        a = banco.criar_conversa("code", pasta=str(self.pasta), titulo="A")
        b = banco.criar_conversa("code", pasta=str(self.pasta), titulo="B")
        ra = self.em_segundo_plano(f"& '{PY}' srv.py 8777", ctx=self.contexto(a["id"]))
        rb = self.em_segundo_plano(f"& '{PY}' srv.py 8778", ctx=self.contexto(b["id"]))
        pa, pb = pids_de(ra), pids_de(rb)
        self.pids += pa + pb
        tb = re.search(r"\(id (comando-\w+)\)", rb).group(1)
        baixando = tarefas.registrar("download", "Vídeo", conversa_id=a["id"],
                                     parar=lambda: baixando.terminar("parada"))
        ex = execucao.Execucao(a["id"], {})
        execucao.registrar(ex)
        try:
            r = tarefas.parar_da_conversa(a["id"])
        finally:
            execucao._execucoes.pop(ex.id, None)
        self.assertEqual(r, {"tarefas": 2, "respostas": 1, "ainda_rodando": True})
        self.assertTrue(ex.parar.is_set())
        self.assertEqual(baixando.status, "parada")
        self.assertTrue(esperar(lambda: not any(vivo(p) for p in pa), 8), "os comandos da conversa A param")
        self.assertTrue(all(vivo(p) for p in pb), "os da conversa B continuam")
        self.assertTrue(tarefas.pegar(tb).rodando)

    def test_conversa_apagada_some_do_ir_para_a_conversa(self):
        conv = banco.criar_conversa("chat", titulo="Vai sumir")
        tf = tarefas.registrar("download", "Vídeo", conversa_id=conv["id"])

        def item():
            return next(i for i in tarefas.listar()["rodando"] if i["id"] == tf.id)
        self.assertEqual((item()["conversa_existe"], item()["conversa_titulo"]), (True, "Vai sumir"))
        banco.apagar_conversa(conv["id"])
        self.assertEqual((item()["conversa_existe"], item()["conversa_titulo"]), (False, None))
        self.assertIs(tarefas.detalhes(tf.id)["tarefa"]["conversa_existe"], False)
        tf.terminar("concluida")


class TestOQueEspera(unittest.TestCase):
    """A linha do cartão de uma resposta esperando a pessoa diz o que espera (o selo já diz "Esperando o seu OK")."""

    class Ex:
        def __init__(self, *pedidos, decidido=False):
            self.filhos = []
            self.aprovacoes = {}
            for i, p in enumerate(pedidos):
                ev = threading.Event()
                if decidido:
                    ev.set()
                self.aprovacoes[f"t{i}"] = {"evento": ev, "pedido": p}

    def test_cada_pedido(self):
        casos = [
            ({"tipo": "plano_proposto", "nome": "apresentar_plano"}, "Um plano para você aprovar"),
            ({"tipo": "fluxo_proposta", "nome": "executar_fluxo"}, "Um fluxo para você aprovar"),
            ({"tipo": "pergunta", "nome": "perguntar"}, "Uma pergunta para você responder"),
            ({"tipo": "aprovacao", "nome": "rodar_comando", "entrada": {"comando": "npm  run\ndev"}},
             "O Claude quer rodar: npm run dev"),
            ({"tipo": "aprovacao", "nome": "navegador_abrir", "entrada": {"url": "https://exemplo.com/"}},
             "O Claude quer abrir: https://exemplo.com/"),
            ({"tipo": "aprovacao", "nome": "escrever_arquivo", "entrada": {"caminho": "a/b.txt"}},
             "O Claude quer mexer em: a/b.txt"),
            ({"tipo": "aprovacao", "nome": "github_criar_issue", "entrada": {}}, "O Claude quer usar: github_criar_issue"),
        ]
        for pedido, esperado in casos:
            self.assertEqual(tarefas._o_que_espera(self.Ex(pedido)), esperado)
            self.assertNotIn("Esperando o seu OK", esperado)

    def test_pedido_de_uma_etapa_e_nada_pendente(self):
        pai = self.Ex({"tipo": "plano_proposto"}, decidido=True)
        pai.filhos.append(self.Ex({"tipo": "aprovacao", "nome": "rodar_comando", "entrada": {"comando": "dir"}}))
        self.assertEqual(tarefas._o_que_espera(pai), "O Claude quer rodar: dir")
        self.assertEqual(tarefas._o_que_espera(self.Ex({"tipo": "pergunta"}, decidido=True)), "Abra a conversa para continuar")


class TestDemoDaApiFalsa(unittest.TestCase):
    """A API de mentira: "segundo plano" tem "plano" dentro, mas o pedido de um servidor em segundo plano vira o
    comando em segundo plano (é o que os prints da aba Tarefas mostram); pedir um plano continua mostrando o plano."""

    def ferramentas_pedidas(self, texto, modo_plano=False):
        import api_falsa
        conteudo = [{"type": "text", "text": texto}]
        if modo_plano:
            conteudo.insert(0, {"type": "text", "text": "<modo-do-clave>Modo Plano ligado.</modo-do-clave>"})
        corpo = {"messages": [{"role": "user", "content": conteudo}],
                 "tools": [{"name": n} for n in ("rodar_comando", "apresentar_plano", "escrever_arquivo")]}
        blocos, _ = api_falsa.planejar(corpo)
        return [b.get("name") for b in blocos if b.get("type") == "tool_use"]

    def test_segundo_plano_ganha_do_plano(self):
        self.assertEqual(self.ferramentas_pedidas("deixe um servidor de teste em segundo plano"), ["rodar_comando"])
        self.assertEqual(self.ferramentas_pedidas("leave a test server in the background"), ["rodar_comando"])

    def test_plano_continua_plano(self):
        self.assertEqual(self.ferramentas_pedidas("planeje e organize"), ["apresentar_plano"])
        self.assertEqual(self.ferramentas_pedidas("make a plan"), ["apresentar_plano"])
        # no modo Plano nada roda: o mesmo pedido mostra o plano
        self.assertEqual(self.ferramentas_pedidas("deixe um servidor de teste em segundo plano", modo_plano=True),
                         ["apresentar_plano"])


class ServidorComTarefas(Servidor):
    """O servidor de verdade com as rotas da aba Tarefas carregadas (antes do integrador pôr o import no
    servidor.py) e um download de mentira registrado, que aceita parar."""

    def __init__(self):
        self.dados = tempfile.mkdtemp(prefix="clave-srv-")
        self.porta = porta_livre()
        self.lancador = Path(self.dados) / "lancar.py"
        self.lancador.write_text(
            "import os, runpy, sys\n"
            "os.environ['CLAVE_DADOS'] = sys.argv[sys.argv.index('--dados') + 1]\n"
            f"sys.path.insert(0, r'{SERVIDOR}')\n"
            "import tarefas\n"
            "tf = tarefas.registrar('download', 'Download de teste', detalhe='1 MB de 3 MB',\n"
            "                       parar=lambda: tf.terminar('parada', 'Parado'))\n"
            "tf.atualizar(progresso=1 / 3)\n"
            "tf.saida('baixando o pedaço 1\\n')\n"
            f"sys.argv = [r'{SERVIDOR / 'servidor.py'}'] + sys.argv[1:]\n"
            f"runpy.run_path(r'{SERVIDOR / 'servidor.py'}', run_name='__main__')\n", encoding="utf-8")
        args = [sys.executable, str(self.lancador), "--porta", str(self.porta), "--demo", "--dados", self.dados,
                "--sem-senha"]
        env = {k: v for k, v in os.environ.items() if k not in ("CLAVE_DADOS", "CLAVE_SEM_SENHA", "CLAVE_API_FALSA")}
        self.proc = subprocess.Popen(args, cwd=str(base.RAIZ), env=env, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, creationflags=0x08000000)
        for _ in range(150):
            try:
                urllib.request.urlopen(self.url("/api/saude"), timeout=1)
                break
            except OSError:
                time.sleep(0.1)

    def fechar(self):
        matar_pid(self.proc.pid)
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        shutil.rmtree(self.dados, ignore_errors=True)


class TestRotas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = ServidorComTarefas()

    @classmethod
    def tearDownClass(cls):
        cls.s.fechar()

    def lista(self):
        st, d = self.s.pedir("GET", "/api/tarefas")
        self.assertEqual(st, 200, d)
        return d

    def test_tarefa_registrada_aparece_mostra_registro_e_para(self):
        d = self.lista()
        item = next(i for i in d["rodando"] if i["titulo"] == "Download de teste")
        self.assertEqual((item["tipo"], item["detalhe"], item["pode_parar"]), ("download", "1 MB de 3 MB", True))
        self.assertAlmostEqual(item["progresso"], 1 / 3, places=3)
        self.assertGreater(d["agora"], item["inicio"])
        st, det = self.s.pedir("GET", f"/api/tarefas/{item['id']}?linhas=10")
        self.assertEqual(st, 200)
        self.assertIn("baixando o pedaço 1", det["registro"])
        st, r = self.s.pedir("POST", f"/api/tarefas/{item['id']}/parar")
        self.assertEqual((st, r), (200, {"ok": True, "ja_terminou": False}))
        d = self.lista()
        self.assertFalse(any(i["id"] == item["id"] for i in d["rodando"]))
        self.assertEqual(next(i for i in d["terminadas"] if i["id"] == item["id"])["status"], "parada")
        st, _ = self.s.pedir("GET", "/api/tarefas/download-naoexiste")
        self.assertEqual(st, 404)

    def test_resposta_esperando_aparece_e_para_pela_rota(self):
        _, r = self.s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        _, r = self.s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "faça o relatório, mas pergunte antes"})
        tid = f"resposta-{r['execucao']}"
        achou = {}

        def esperando():
            achou.update({i["id"]: i for i in self.lista()["rodando"]})
            return achou.get(tid, {}).get("status") == "esperando"
        self.assertTrue(esperar(esperando, 30, 0.3), achou)
        item = achou[tid]
        self.assertEqual((item["tipo"], item["conversa_id"], item["modo"]), ("resposta", cid, "chat"))
        self.assertTrue(item["pode_parar"])
        self.assertEqual(item["detalhe"], "Uma pergunta para você responder", "a linha diz o que espera, sem repetir o selo")
        _, det = self.s.pedir("GET", f"/api/tarefas/{tid}")
        self.assertIn("Esperando você responder uma pergunta", det["registro"])
        st, res = self.s.pedir("POST", f"/api/tarefas/{tid}/parar")
        self.assertEqual((st, res["ok"]), (200, True))
        evs = self.s.eventos(r["execucao"])
        self.assertEqual(evs[-1]["status"], "parada")
        self.assertFalse(any(i["id"] == tid for i in self.lista()["rodando"]))

    def test_fluxo_aparece_com_as_etapas(self):
        _, r = self.s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        _, r = self.s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "faça um fluxo"})
        evs = self.s.eventos(r["execucao"], decidir=lambda ev: "permitir" if ev["tipo"] == "fluxo_proposta" else "recusar")
        self.assertEqual(evs[-1]["status"], "concluida")
        fid = next(e["fluxo"] for e in evs if e["tipo"] == "fluxo_inicio")
        item = next((i for i in self.lista()["terminadas"] if i["id"] == f"fluxo-{fid}"), None)
        self.assertIsNotNone(item, "o fluxo que terminou fica em Terminadas há pouco")
        self.assertEqual((item["tipo"], item["status"], item["passos"]), ("fluxo", "concluida", {"feitos": 4, "total": 4}))
        self.assertEqual(item["conversa_id"], cid)
        _, det = self.s.pedir("GET", f"/api/tarefas/fluxo-{fid}")
        self.assertIn("Etapa 1", det["registro"])


if __name__ == "__main__":
    unittest.main()
