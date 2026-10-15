"""5.0: a aba Console, um PowerShell de verdade (ConPTY) dentro do modo Code.

Os testes abrem shells de verdade numa pasta temporária: escrevem um comando, leem a saída, mudam o tamanho, fecham e
conferem que o processo (e o que ele abriu) morreu, inclusive quando o servidor morre de repente.
"""
import ctypes
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from ctypes import wintypes
from pathlib import Path
from unittest import mock

import base
import console
from rotas import Erro
from test_servidor import Servidor, porta_livre

PRAZO = 20  # segundos para o PowerShell mostrar o que se pediu
_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_k32.OpenProcess.restype = wintypes.HANDLE
_k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_k32.WaitForSingleObject.restype = wintypes.DWORD
_k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_k32.CloseHandle.argtypes = [wintypes.HANDLE]
_k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
_k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]


_k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
_k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]


def vivo(pid: int) -> bool:
    h = _k32.OpenProcess(0x00100000 | 0x1000, False, pid)  # SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    try:
        return _k32.WaitForSingleObject(h, 0) == 0x102  # WAIT_TIMEOUT: ainda rodando
    finally:
        _k32.CloseHandle(h)


def esperar_morrer(pid: int, prazo: float = 10) -> bool:
    fim = time.time() + prazo
    while time.time() < fim:
        if not vivo(pid):
            return True
        time.sleep(0.1)
    return not vivo(pid)


def processos() -> list[tuple[int, int, str]]:
    """(pid, pid do pai, nome do executável) de todos os processos."""
    snap = _k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    lista = []
    try:
        e = PROCESSENTRY32W()
        e.dwSize = ctypes.sizeof(e)
        ok = _k32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            lista.append((e.th32ProcessID, e.th32ParentProcessID, e.szExeFile))
            ok = _k32.Process32NextW(snap, ctypes.byref(e))
    finally:
        _k32.CloseHandle(snap)
    return lista


def filhos(pid: int, nome: str) -> list[int]:
    """Os processos com este nome cujo pai é pid (o ping que o shell abriu)."""
    return [p for p, pai, exe in processos() if pai == pid and exe.lower() == nome.lower()]


def pai(pid: int) -> int:
    return next((pp for p, pp, _ in processos() if p == pid), 0)


def esperar_filho(pid: int, nome: str, prazo: float = PRAZO) -> int:
    fim = time.time() + prazo
    while time.time() < fim:
        achados = [p for p in filhos(pid, nome) if vivo(p)]
        if achados:
            return achados[0]
        time.sleep(0.2)
    return 0


def esperar_texto(c: "console.Console", quantas: int, prazo: float = PRAZO, texto: str = "clave-teste-123") -> str:
    """Espera o texto aparecer `quantas` vezes na saída (o eco do comando conta uma, a saída dele outra)."""
    fim = time.time() + prazo
    while time.time() < fim:
        s = c.texto()
        if s.count(texto) >= quantas:
            return s
        time.sleep(0.1)
    return c.texto()


class TestEstruturas(unittest.TestCase):
    def test_layout_64_bits(self):
        self.assertEqual(ctypes.sizeof(ctypes.c_void_p), 8)
        self.assertEqual(ctypes.sizeof(console.STARTUPINFOW), 104)
        self.assertEqual(ctypes.sizeof(console.STARTUPINFOEXW), 112)
        self.assertEqual(ctypes.sizeof(console.PROCESS_INFORMATION), 24)
        self.assertEqual(ctypes.sizeof(console.JOBOBJECT_EXTENDED_LIMIT_INFORMATION), 144)
        self.assertEqual(ctypes.sizeof(console.JOBOBJECT_BASIC_PROCESS_ID_LIST), 8 + 64 * 8)
        self.assertEqual(ctypes.sizeof(console.COORD), 4)

    def test_conpty_existe_neste_windows(self):
        self.assertTrue(console.conpty_disponivel())

    def test_ambiente_sem_as_variaveis_do_clave(self):
        with mock.patch.dict(os.environ, {"CLAVE_DADOS": "x", "CLAVE_LANCADOR": "1", "ELECTRON_RUN_AS_NODE": "1",
                                          "CLAVE_PONTE_TOKEN": "segredo", "CLAVE_PONTE_URL": "http://127.0.0.1:1",
                                          "OUTRA_COISA": "fica"}):
            amb = console._ambiente()
        self.assertNotIn("CLAVE_DADOS", amb)
        self.assertNotIn("CLAVE_LANCADOR", amb)
        self.assertNotIn("CLAVE_PONTE_TOKEN", amb)
        self.assertNotIn("CLAVE_PONTE_URL", amb)
        self.assertNotIn("ELECTRON_RUN_AS_NODE", amb)
        self.assertEqual(amb.get("OUTRA_COISA"), "fica")

    def test_pythonutf8_do_electron_nao_chega_ao_console(self):
        """O Electron liga PYTHONUTF8=1 para o servidor; no console vale o que a pessoa tem no Windows."""
        with mock.patch.dict(os.environ, {"PYTHONUTF8": "1"}):
            with mock.patch.object(console, "_variavel_do_windows", return_value=None):
                self.assertNotIn("PYTHONUTF8", console._ambiente())
            with mock.patch.object(console, "_variavel_do_windows", return_value="0"):
                self.assertEqual(console._ambiente()["PYTHONUTF8"], "0")

    def test_redimensionar_com_a_trava_de_quem_fecha(self):
        """ResizePseudoConsole roda com a trava que o _fechar_pty usa: nunca num HPCON que já foi liberado."""
        c = console.Console(tempfile.gettempdir(), 80, 24, 99)
        c._hpc = wintypes.HANDLE(1234)  # de mentira: o kernel falso só anota
        chamadas = []

        class Kernel:
            def ResizePseudoConsole(self, hpc, coord):
                chamadas.append((c._liberar.locked(), coord.X, coord.Y))
                return 0
        with mock.patch.object(console, "_kernel", lambda: Kernel()):
            c.redimensionar(90, 30)
            c._hpc = None  # o pseudo console fechou
            c.redimensionar(91, 31)
        self.assertEqual(chamadas, [(True, 90, 30)])
        self.assertEqual((c.cols, c.rows), (91, 31))


class _Manipulador:
    """O bastante de um BaseHTTPRequestHandler para chamar a rota do SSE direto."""

    def __init__(self, desde):
        self.wfile = io.BytesIO()
        self._q = {"desde": str(desde)}
        self.close_connection = False

    def query(self):
        return self._q

    def send_response(self, *_):
        pass

    def send_header(self, *_):
        pass

    def end_headers(self):
        pass

    def eventos(self):
        return [json.loads(l[6:]) for l in self.wfile.getvalue().decode("utf-8").splitlines() if l.startswith("data: ")]


class TestSaidaCortada(unittest.TestCase):
    def test_aviso_de_corte_no_meio_da_conexao(self):
        """Um buraco no meio da conexão (a saída passou de ~2 MB entre duas leituras) também avisa a tela."""
        c = console.Console(tempfile.gettempdir(), 80, 24, 97)
        respostas = iter([([(0, "a"), (1, "b")], False), ([(5, "f")], False), ([], True)])
        c.desde = lambda n, espera=15: next(respostas)
        console._consoles[c.id] = c
        try:
            h = _Manipulador(0)
            console.r_saida(h, c.id)
        finally:
            console._consoles.pop(c.id, None)
        evs = h.eventos()
        self.assertEqual(evs[0], {"seq": 1, "dados": "ab"})
        self.assertEqual(evs[1], {"cortado": 3})
        self.assertEqual(evs[2], {"seq": 5, "dados": "f"})
        self.assertTrue(evs[3]["fim"])

    def test_aviso_de_corte_no_comeco(self):
        c = console.Console(tempfile.gettempdir(), 80, 24, 96)
        with mock.patch.object(console, "LIMITE_SAIDA", 1000):
            for i in range(30):
                c._guardar(f"{i:03d}" + "x" * 97)
        c.fechado = True
        console._consoles[c.id] = c
        try:
            h = _Manipulador(2)
            console.r_saida(h, c.id)
        finally:
            console._consoles.pop(c.id, None)
        evs = h.eventos()
        self.assertEqual(evs[0], {"cortado": c.primeiro() - 2})
        self.assertEqual(evs[1]["seq"], 29)
        self.assertTrue(evs[-1]["fim"])


class _ComPasta(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="clave-console-")
        self.abertos = []

    def tearDown(self):
        for c in self.abertos:
            console.fechar(c.id)
        shutil.rmtree(self.pasta, ignore_errors=True)

    def abrir(self, **kw):
        c = console.abrir(self.pasta, 100, 30, **kw)
        self.abertos.append(c)
        return c


class TestConsoleDeVerdade(_ComPasta):
    def test_echo_tamanho_e_fechar(self):
        c = self.abrir()
        self.assertEqual(c.modo, "conpty")
        self.assertTrue(vivo(c.pid))
        c.escrever("echo clave-teste-123\r")
        saida = esperar_texto(c, 2)
        self.assertGreaterEqual(saida.count("clave-teste-123"), 2, saida[-800:])
        self.assertIn(os.path.basename(self.pasta), saida)  # o prompt mostra a pasta: abriu onde devia
        self.assertFalse(c.ocupado())  # parado no prompt: fechar não precisa perguntar
        c.redimensionar(80, 20)
        self.assertEqual((c.cols, c.rows), (80, 20))
        pid = c.pid
        self.assertTrue(console.fechar(c.id))
        self.assertTrue(esperar_morrer(pid), "o PowerShell continuou vivo depois de fechar o console")
        self.assertTrue(c.terminou)
        with self.assertRaises(Erro):
            console.pegar(c.id)

    def test_acentos_chegam_inteiros(self):
        c = self.abrir()
        c.escrever("echo 'clave-teste-123 ação ✓'\r")
        saida = esperar_texto(c, 2)
        self.assertIn("ação ✓", saida.split("clave-teste-123", 2)[-1])

    def test_saida_do_shell_e_o_codigo(self):
        c = self.abrir()
        c.escrever("exit 7\r")
        fim = time.time() + PRAZO
        while not c.terminou and time.time() < fim:
            time.sleep(0.1)
        self.assertTrue(c.terminou)
        self.assertEqual(c.codigo, 7)
        itens, acabou = c.desde(c.proximo, espera=0.1)
        self.assertEqual(itens, [])
        self.assertTrue(acabou)
        with self.assertRaises(Erro):
            c.escrever("echo depois\r")

    def test_job_mata_o_que_o_shell_abriu(self):
        c = self.abrir()
        c.escrever("ping -n 30 127.0.0.1\r")
        ping = esperar_filho(c.pid, "PING.EXE")
        self.assertTrue(ping, "o ping não apareceu como filho do PowerShell")
        self.assertTrue(c.ocupado())
        console.fechar(c.id)
        self.assertTrue(esperar_morrer(ping), "o ping sobreviveu ao console fechado")

    def test_modo_simples_por_pipes(self):
        c = self.abrir(simples=True)
        self.assertEqual(c.modo, "simples")
        c.escrever("echo clave-teste-123\r\n")
        saida = esperar_texto(c, 2)
        self.assertGreaterEqual(saida.count("clave-teste-123"), 2, saida[-800:])
        c.escrever("echo 'clave-teste-123 ação'\r\n")
        self.assertIn("ação", esperar_texto(c, 4))
        self.assertFalse(c.ocupado())  # o conhost escondido do modo simples fica no job, mas não conta
        c.escrever("ping -n 30 127.0.0.1\r\n")
        ping = esperar_filho(c.pid, "PING.EXE")
        self.assertTrue(ping)
        self.assertTrue(c.ocupado())
        pid = c.pid
        console.fechar(c.id)
        self.assertTrue(esperar_morrer(pid))
        self.assertTrue(esperar_morrer(ping))

    def test_filho_que_segura_a_saida_nao_trava_o_fechar(self):
        """Modo simples: o shell sai, mas um ping que ele abriu continua com a ponta da saída. O console termina
        mesmo assim e fechar não trava esperando a leitura; o ping morre junto com o job."""
        c = self.abrir(simples=True)
        c.escrever("Start-Process ping -ArgumentList '-n','30','127.0.0.1' -NoNewWindow\r\n")
        ping = esperar_filho(c.pid, "PING.EXE")
        self.assertTrue(ping)
        c.escrever("exit 0\r\n")
        fim = time.time() + PRAZO
        while not c.terminou and time.time() < fim:
            time.sleep(0.1)
        self.assertTrue(c.terminou)
        self.assertTrue(vivo(ping))  # o shell saiu sozinho: o que ele abriu fica até o console fechar
        inicio = time.time()
        console.fechar(c.id)
        self.assertLess(time.time() - inicio, 8)
        self.assertTrue(esperar_morrer(ping))

    def test_cai_no_simples_quando_o_conpty_falha(self):
        def falha(*a, **kw):
            raise OSError(5, "CreatePseudoConsole: teste")
        with mock.patch.object(console.Console, "_abrir_conpty", falha):
            c = self.abrir()
        self.assertEqual(c.modo, "simples")
        c.escrever("echo clave-teste-123\r\n")
        self.assertGreaterEqual(esperar_texto(c, 2).count("clave-teste-123"), 2)

    def test_pasta_que_nao_existe_e_limite(self):
        with self.assertRaises(Erro) as e:
            console.abrir(os.path.join(self.pasta, "nao-existe"))
        self.assertEqual(e.exception.status, 400)
        with self.assertRaises(Erro):
            console.abrir("pasta-relativa")
        with mock.patch.object(console, "MAX_CONSOLES", 1):
            self.abrir()
            with self.assertRaises(Erro) as e:
                console.abrir(self.pasta)
            self.assertEqual(e.exception.status, 409)

    def test_numeros_reaproveitados(self):
        a, b = self.abrir(), self.abrir()
        self.assertEqual((a.numero, b.numero), (1, 2))
        console.fechar(a.id)
        c = self.abrir()
        self.assertEqual(c.numero, 1)
        self.assertEqual(c.titulo, "PowerShell 1")

    def test_guarda_so_o_fim_da_saida(self):
        c = console.Console(self.pasta, 80, 24, 1)
        with mock.patch.object(console, "LIMITE_SAIDA", 1000):
            for i in range(50):
                c._guardar(f"{i:03d}" + "x" * 97)
        self.assertLessEqual(len(c.texto()), 1000)
        self.assertTrue(c.texto().endswith("049" + "x" * 97))
        self.assertEqual(c.proximo, 50)
        itens, _ = c.desde(0, espera=0)
        self.assertEqual(itens[0][0], c.primeiro())  # quem pede o que já saiu recebe a partir do que ficou


# Um programa com janela de verdade: o pythonw da instalação do Python (subsistema gráfico: o PowerShell não espera
# por ele, como não espera pelo Bloco de Notas) abre uma janela visível fora da tela, sem foco e fora da barra de
# tarefas, grava o próprio pid e fica vivo até o prazo. É o pythonw da instalação, não o do .venv: o lançador do
# .venv mata o filho quando morre, e o teste quer só o dono da janela.
PYTHONW = str(Path(getattr(sys, "_base_executable", sys.executable)).with_name("pythonw.exe"))
JANELA = r'''
import ctypes, os, sys, time
from ctypes import wintypes
u = ctypes.WinDLL("user32", use_last_error=True)
u.CreateWindowExW.restype = wintypes.HWND
u.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_int,
                              ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.HMENU,
                              wintypes.HINSTANCE, wintypes.LPVOID]
h = u.CreateWindowExW(0x80 | 0x08000000, "STATIC", "clave-teste-janela", 0x80000000 | 0x10000000,
                      -3000, -3000, 120, 80, None, None, None, None)
open(sys.argv[1] + ".tmp", "w").write(str(os.getpid()))
os.replace(sys.argv[1] + ".tmp", sys.argv[1])
msg = wintypes.MSG()
fim = time.time() + float(sys.argv[2])
while time.time() < fim:
    while u.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
        u.TranslateMessage(ctypes.byref(msg))
        u.DispatchMessageW(ctypes.byref(msg))
    time.sleep(0.05)
'''


def esperar_pid_no_arquivo(arq: Path, prazo: float = PRAZO) -> int:
    fim = time.time() + prazo
    while time.time() < fim:
        try:
            return int(arq.read_text().strip())
        except (OSError, ValueError):
            time.sleep(0.1)
    return 0


def matar(pid: int) -> None:
    if pid and vivo(pid):
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)


class TestJanelasFicamAbertas(_ComPasta):
    """Regra do produto: programas com janela abertos pelo console (Bloco de Notas, VS Code, Excel, o navegador de um
    npm start) continuam abertos quando o console fecha ou o Clave fecha do jeito normal. Só um encerramento à força
    (testado em TestJobSemTaskkill e test_servidor_que_morre_leva_os_shells_junto) derruba tudo."""

    def setUp(self):
        super().setUp()
        Path(self.pasta, "janela.py").write_text(JANELA, encoding="utf-8")
        self.janelas: list[int] = []

    def tearDown(self):
        for pid in self.janelas:
            matar(pid)
        super().tearDown()

    def abrir_janela(self, c, nl):
        marca = Path(self.pasta) / f"janela-{len(self.janelas)}.pid"
        c.escrever(f"& '{PYTHONW}' janela.py '{marca}' 90{nl}")
        if c.modo == "simples":
            # Sem pseudo console, o Python que acabou de abrir consulta a entrada herdada (o cano do shell) enquanto
            # o PowerShell espera a próxima linha nela, e o Windows enfileira as duas coisas no mesmo cano: o
            # programa só segue quando chega uma linha. É do modo simples (a reserva sem ConPTY), não do fechar.
            time.sleep(1)
            c.escrever(nl)
        pid = esperar_pid_no_arquivo(marca)
        self.assertTrue(pid, c.texto()[-800:])
        self.janelas.append(pid)
        fim = time.time() + 10
        while pid not in console.pids_com_janela() and time.time() < fim:
            time.sleep(0.1)
        self.assertIn(pid, console.pids_com_janela(), "a janela de teste não ficou visível")
        return pid

    def fechar_com_janela(self, simples):
        c = self.abrir(simples=simples)
        nl = "\r\n" if simples else "\r"
        janela = self.abrir_janela(c, nl)
        time.sleep(0.5)
        self.assertFalse(c.ocupado(), "só um programa com janela aberto: fechar não para nada no meio")
        c.escrever(f"Start-Process -WindowStyle Hidden ping -ArgumentList '-n','40','127.0.0.1'{nl}")
        ping = esperar_filho(c.pid, "PING.EXE")
        self.assertTrue(ping, "o ping escondido não apareceu")
        self.assertTrue(c.ocupado(), "o ping escondido para se o console fechar")
        shell = c.pid
        console.fechar(c.id)
        self.assertTrue(esperar_morrer(shell), "o PowerShell continuou vivo")
        self.assertTrue(esperar_morrer(ping), "o programa sem janela continuou vivo")
        time.sleep(1.5)
        self.assertTrue(vivo(janela), "o programa com janela fechou junto com o console")

    def test_fechar_o_console_deixa_a_janela(self):
        self.fechar_com_janela(simples=False)

    def test_fechar_o_console_simples_deixa_a_janela(self):
        self.fechar_com_janela(simples=True)

    def test_clave_fechando_normal_deixa_a_janela(self):
        """O atexit do servidor (fechar_todos) também só derruba o que não tem janela."""
        c = self.abrir()
        janela = self.abrir_janela(c, "\r")
        c.escrever("ping -n 40 127.0.0.1\r")
        ping = esperar_filho(c.pid, "PING.EXE")
        self.assertTrue(ping)
        shell = c.pid
        console.fechar_todos()
        self.assertTrue(esperar_morrer(shell))
        self.assertTrue(esperar_morrer(ping))
        time.sleep(1.5)
        self.assertTrue(vivo(janela), "o programa com janela fechou junto com o Clave")

    def test_o_que_fica(self):
        """As regras de quem fica, sem processos de verdade: a janela, o que ela abriu e quem a lançou ficam; o shell
        (a raiz), um servidor irmão e o console de quem morre saem."""
        procs = {10: (1, "powershell.exe"), 11: (10, "conhost.exe"), 20: (10, "python.exe"),  # lançador do .venv
                 21: (20, "pythonw.exe"), 22: (21, "helper.exe"), 30: (10, "node.exe"), 31: (30, "conhost.exe")}
        fica = console._o_que_fica(set(procs), procs, {21, 10}, {10})
        self.assertEqual(fica, {20, 21, 22})
        # a janela do console aparece como do conhost: quem fica é o programa que roda nele
        procs2 = {10: (1, "powershell.exe"), 40: (10, "cmd.exe"), 41: (40, "conhost.exe")}
        self.assertEqual(console._o_que_fica(set(procs2), procs2, {41}, {10}), {40, 41})


_ABRIR_SERVIDOR = (
    "import sys\n"
    "sys.argv = ['servidor.py'] + sys.argv[1:]\n"
    "sys.path.insert(0, {pasta!r})\n"
    "import servidor\n"
    "import console  # o servidor.py ganha este import na integração; aqui ele entra antes\n"
    "sys.exit(servidor.main())\n"
)


class ServidorComConsole(Servidor):
    """O servidor de verdade (API de mentira, dados temporários) com as rotas do console registradas."""

    def __init__(self):
        self.dados = tempfile.mkdtemp(prefix="clave-srv-")
        self.porta = porta_livre()
        codigo = _ABRIR_SERVIDOR.format(pasta=str(base.RAIZ / "servidor"))
        args = [sys.executable, "-c", codigo, "--porta", str(self.porta), "--demo", "--dados", self.dados, "--sem-senha"]
        env = {k: v for k, v in os.environ.items() if k not in ("CLAVE_DADOS", "CLAVE_SEM_SENHA", "CLAVE_API_FALSA",
                                                                 "CLAVE_CONSOLE_SIMPLES")}
        self.proc = subprocess.Popen(args, cwd=str(base.RAIZ), env=env, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        for _ in range(150):
            try:
                urllib.request.urlopen(self.url("/api/saude"), timeout=1)
                break
            except urllib.error.HTTPError:
                break
            except OSError:
                time.sleep(0.1)

    def fechar(self):
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(self.proc.pid)], capture_output=True)
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        shutil.rmtree(self.dados, ignore_errors=True)


class LeitorSSE(threading.Thread):
    def __init__(self, url):
        super().__init__(daemon=True)
        self.url, self.eventos, self.status, self.erro = url, [], None, None
        self.acabou = threading.Event()

    def run(self):
        try:
            with urllib.request.urlopen(self.url, timeout=60) as r:
                self.status = r.status
                for linha in r:
                    linha = linha.decode("utf-8").strip()
                    if linha.startswith("data: "):
                        ev = json.loads(linha[6:])
                        self.eventos.append(ev)
                        if ev.get("fim"):
                            break
        except Exception as e:  # noqa: BLE001 (o teste mostra o que deu errado)
            self.erro = e
        finally:
            self.acabou.set()

    def texto(self):
        return "".join(e.get("dados", "") for e in list(self.eventos))

    def esperar(self, quantas, texto="clave-teste-123", prazo=PRAZO):
        fim = time.time() + prazo
        while time.time() < fim:
            if self.texto().count(texto) >= quantas:
                return True
            time.sleep(0.1)
        return False


class TestRotas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = ServidorComConsole()
        cls.pasta = tempfile.mkdtemp(prefix="clave-console-srv-")

    @classmethod
    def tearDownClass(cls):
        cls.s.fechar()
        shutil.rmtree(cls.pasta, ignore_errors=True)

    def test_abrir_ler_escrever_e_fechar(self):
        s = self.s
        status, d = s.pedir("POST", "/api/consoles", {"pasta": self.pasta, "cols": 90, "rows": 25})
        self.assertEqual(status, 200, d)
        cid = d["id"]
        self.assertEqual(d["modo"], "conpty")
        self.assertTrue(d["titulo"].startswith("PowerShell "))
        self.assertEqual(d["console"]["pasta"], self.pasta)
        self.assertEqual((d["console"]["cols"], d["console"]["rows"]), (90, 25))
        pid = d["console"]["pid"]
        self.assertTrue(vivo(pid))

        sse = LeitorSSE(s.url(f"/api/consoles/{cid}/saida?desde=0"))
        sse.start()
        status, d = s.pedir("POST", f"/api/consoles/{cid}/entrada", {"dados": "echo clave-teste-123\r"})
        self.assertEqual(status, 200, d)
        self.assertTrue(sse.esperar(2), sse.texto()[-800:])
        self.assertEqual(sse.status, 200)
        seqs = [e["seq"] for e in sse.eventos if "seq" in e]
        self.assertEqual(seqs, sorted(set(seqs)))

        # reconectar a partir de um número continua dali, sem repetir; do zero repete tudo o que está guardado
        meio = seqs[-1] + 1
        s.pedir("POST", f"/api/consoles/{cid}/entrada", {"dados": "echo clave-teste-456\r"})
        segunda = LeitorSSE(s.url(f"/api/consoles/{cid}/saida?desde={meio}"))
        segunda.start()
        self.assertTrue(segunda.esperar(2, "clave-teste-456"), segunda.texto()[-500:])
        self.assertNotIn("clave-teste-123", segunda.texto())
        self.assertTrue(all(e["seq"] >= meio for e in segunda.eventos if "seq" in e))
        replay = LeitorSSE(s.url(f"/api/consoles/{cid}/saida?desde=0"))
        replay.start()
        self.assertTrue(replay.esperar(2, "clave-teste-456"))
        self.assertGreaterEqual(replay.texto().count("clave-teste-123"), 2)

        status, d = s.pedir("POST", f"/api/consoles/{cid}/tamanho", {"cols": 120, "rows": 40})
        self.assertEqual(status, 200, d)
        status, lista = s.pedir("GET", "/api/consoles")
        self.assertEqual(status, 200)
        meu = [c for c in lista["consoles"] if c["id"] == cid][0]
        self.assertEqual((meu["cols"], meu["rows"]), (120, 40))
        self.assertFalse(meu["terminou"])
        self.assertGreater(meu["proximo"], 0)
        self.assertEqual(lista["maximo"], console.MAX_CONSOLES)

        status, d = s.pedir("DELETE", f"/api/consoles/{cid}")
        self.assertEqual(status, 200, d)
        for leitor in (sse, segunda, replay):
            self.assertTrue(leitor.acabou.wait(10), "o SSE não terminou depois de fechar o console")
            self.assertTrue(leitor.eventos and leitor.eventos[-1].get("fim"), leitor.eventos[-1:])
        self.assertTrue(esperar_morrer(pid))
        status, lista = s.pedir("GET", "/api/consoles")
        self.assertNotIn(cid, [c["id"] for c in lista["consoles"]])
        status, d = s.pedir("DELETE", f"/api/consoles/{cid}")
        self.assertEqual(status, 404)

    def test_erros_em_portugues(self):
        s = self.s
        status, d = s.pedir("POST", "/api/consoles", {"pasta": os.path.join(self.pasta, "sumiu")})
        self.assertEqual(status, 400)
        self.assertIn("não existe", d["erro"])
        status, d = s.pedir("POST", "/api/consoles", {})
        self.assertEqual(status, 400)
        self.assertIn("pasta", d["erro"])
        status, d = s.pedir("POST", "/api/consoles/naoexiste/entrada", {"dados": "x"})
        self.assertEqual(status, 404)
        self.assertIn("Console não encontrado", d["erro"])
        status, d = s.pedir("GET", "/api/consoles/naoexiste/saida")
        self.assertEqual(status, 404)

        status, d = s.pedir("POST", "/api/consoles", {"pasta": self.pasta})
        cid = d["id"]
        try:
            status, d = s.pedir("POST", f"/api/consoles/{cid}/entrada", {"dados": 123})
            self.assertEqual(status, 400)
            status, d = s.pedir("POST", f"/api/consoles/{cid}/entrada", {"dados": "x" * (console.LIMITE_ENTRADA + 1)})
            self.assertEqual(status, 413)
            for ruim in ({"cols": 0, "rows": 10}, {"cols": 80, "rows": 9999}, {"cols": "a", "rows": 2}, {}):
                status, d = s.pedir("POST", f"/api/consoles/{cid}/tamanho", ruim)
                self.assertEqual(status, 400, ruim)
                self.assertIn("Tamanho", d["erro"])
        finally:
            s.pedir("DELETE", f"/api/consoles/{cid}")

    def test_servidor_que_morre_leva_os_shells_junto(self):
        """Só o processo do servidor morto à força (TerminateProcess, sem /T e sem atexit): o Windows fecha o handle
        do job e mata o shell e o ping, que não estão na lista de quem foi morto."""
        outro = ServidorComConsole()
        try:
            status, d = outro.pedir("POST", "/api/consoles", {"pasta": self.pasta})
            self.assertEqual(status, 200, d)
            shell = d["console"]["pid"]
            outro.pedir("POST", f"/api/consoles/{d['id']}/entrada", {"dados": "ping -n 30 127.0.0.1\r"})
            ping = esperar_filho(shell, "PING.EXE")
            self.assertTrue(ping, "o ping não apareceu")
            servidor = pai(shell)
            self.assertTrue(servidor)
            subprocess.run(["taskkill", "/F", "/PID", str(servidor)], capture_output=True)
            self.assertTrue(esperar_morrer(servidor))
            self.assertTrue(esperar_morrer(shell), "o PowerShell sobreviveu ao servidor")
            self.assertTrue(esperar_morrer(ping), "o ping sobreviveu ao servidor")
        finally:
            outro.fechar()


class TestJobSemTaskkill(unittest.TestCase):
    def test_os_exit_do_servidor_mata_o_shell(self):
        """Sem taskkill na árvore: o processo que abriu o console sai por os._exit (como o servidor quando a janela
        some) e mesmo assim o shell e o ping morrem, porque o último handle do job fechou."""
        pasta = tempfile.mkdtemp(prefix="clave-console-exit-")
        codigo = (
            "import os, sys, time\n"
            f"sys.path.insert(0, {str(base.RAIZ / 'servidor')!r})\n"
            "import console\n"
            f"c = console.abrir({pasta!r}, 80, 24)\n"
            "c.escrever('ping -n 30 127.0.0.1\\r')\n"
            "print(c.pid, flush=True)\n"
            "time.sleep(float(sys.argv[1]))\n"
            "os._exit(0)\n"
        )
        try:
            p = subprocess.Popen([sys.executable, "-c", codigo, "4"], stdout=subprocess.PIPE, text=True,
                                 cwd=str(base.RAIZ), env={**os.environ, "CLAVE_DADOS": str(base.DADOS)})
            shell = int(p.stdout.readline().strip())
            ping = esperar_filho(shell, "PING.EXE", prazo=4)
            self.assertTrue(ping, "o ping não apareceu antes de o processo sair")
            p.wait(timeout=30)
            p.stdout.close()
            self.assertTrue(esperar_morrer(shell), "o PowerShell sobreviveu ao os._exit")
            self.assertTrue(esperar_morrer(ping), "o ping sobreviveu ao os._exit")
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
