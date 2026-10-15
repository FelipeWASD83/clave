"""A aba Console do modo Code: um PowerShell de verdade dentro do Clave.

Cada console é um pseudo console do Windows (ConPTY: CreatePseudoConsole e CreateProcessW com o atributo
PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE), então cores, o PSReadLine e programas interativos funcionam como no Terminal
do Windows. O shell nasce suspenso, entra num Job Object com JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE e só então começa a
rodar. Fechar o console (ou o Clave fechar do jeito normal) é com cuidado (encerrar_job_com_cuidado): morrem o shell e
o que ele abriu sem janela; programas com janela (o Bloco de Notas, o VS Code, o Excel, o navegador que um npm start
abriu) continuam abertos, como quando se fecha uma aba do Terminal do Windows. Se o servidor do Clave morrer de
repente (os._exit, taskkill), o Windows fecha o último handle do job e mata tudo, janelas inclusive. Sem ConPTY
(Windows antigo, ou a criação falhou), cai num shell por pipes, o modo "simples": sem TTY e sem cores, mas dá para
rodar comandos.

Uma thread por console lê a saída, decodifica sem partir caracteres (decodificador incremental) e guarda pedaços
numerados, só os últimos ~2 MB. A tela lê por SSE a partir de um número (desde=N): reconectar não perde nada.
"""
from __future__ import annotations

import atexit
import codecs
import ctypes
import json
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path

from i18n import t
from rotas import Erro, rota

MAX_CONSOLES = 6
LIMITE_SAIDA = 2 * 1024 * 1024      # caracteres guardados por console (os mais antigos saem primeiro)
LIMITE_ENTRADA = 256 * 1024         # caracteres por pedido de entrada (a tela manda colagens grandes em partes)
PEDACO_SSE = 256 * 1024             # junta pedaços seguidos num evento só até este tamanho
MAX_COLUNAS, MAX_LINHAS = 500, 300

_consoles: dict[str, "Console"] = {}
_trava = threading.Lock()

# ---------- a API do Windows (ctypes) ----------
INFINITE = 0xFFFFFFFF
WAIT_OBJECT_0 = 0
STILL_ACTIVE = 259
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
CREATE_UNICODE_ENVIRONMENT = 0x00000400
CREATE_SUSPENDED = 0x00000004
CREATE_NO_WINDOW = 0x08000000
STARTF_USESTDHANDLES = 0x00000100
PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE = 0x00020016
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
JOB_OBJECT_BASIC_PROCESS_ID_LIST_CLASS = 3
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_TERMINATE = 0x0001
SYNCHRONIZE = 0x00100000
TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
WAIT_TIMEOUT = 0x102
ERROR_MORE_DATA = 234
# o console de um processo (o conhost do console escondido, o OpenConsole): sai sozinho quando os clientes saem
AJUDANTES_DE_CONSOLE = {"conhost.exe", "openconsole.exe"}


class COORD(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR), ("lpDesktop", wintypes.LPWSTR),
                ("lpTitle", wintypes.LPWSTR), ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD), ("dwXCountChars", wintypes.DWORD),
                ("dwYCountChars", wintypes.DWORD), ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD), ("lpReserved2", ctypes.c_void_p),
                ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]


class IO_COUNTERS(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                                                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION), ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]


class JOBOBJECT_BASIC_PROCESS_ID_LIST(ctypes.Structure):
    _fields_ = [("NumberOfAssignedProcesses", wintypes.DWORD), ("NumberOfProcessIdsInList", wintypes.DWORD),
                ("ProcessIdList", ctypes.c_size_t * 64)]


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]


ENUM_JANELAS = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM) if sys.platform == "win32" else None


class _Kernel:
    """As funções do kernel32 com argtypes e restype certos (64 bits: HANDLE é ponteiro, SIZE_T é 8 bytes)."""

    def __init__(self):
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        H, B, D = wintypes.HANDLE, wintypes.BOOL, wintypes.DWORD
        PH = ctypes.POINTER(wintypes.HANDLE)

        def f(nome, res, *args, dll=k, opcional=False):
            try:
                fn = getattr(dll, nome)
            except AttributeError:
                if opcional:
                    return None
                raise
            fn.restype = res
            fn.argtypes = list(args)
            return fn

        self.CreatePipe = f("CreatePipe", B, PH, PH, ctypes.c_void_p, D)
        self.CloseHandle = f("CloseHandle", B, H)
        # o ConPTY existe a partir do Windows 10 1809; sem ele, o console cai no modo simples
        self.CreatePseudoConsole = f("CreatePseudoConsole", ctypes.c_long, COORD, H, H, D, PH, opcional=True)
        self.ResizePseudoConsole = f("ResizePseudoConsole", ctypes.c_long, H, COORD, opcional=True)
        self.ClosePseudoConsole = f("ClosePseudoConsole", None, H, opcional=True)
        self.InitializeProcThreadAttributeList = f("InitializeProcThreadAttributeList", B, ctypes.c_void_p, D, D,
                                                   ctypes.POINTER(ctypes.c_size_t))
        self.UpdateProcThreadAttribute = f("UpdateProcThreadAttribute", B, ctypes.c_void_p, D, ctypes.c_size_t,
                                           ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p)
        self.DeleteProcThreadAttributeList = f("DeleteProcThreadAttributeList", None, ctypes.c_void_p)
        self.CreateProcessW = f("CreateProcessW", B, wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p,
                                ctypes.c_void_p, B, D, ctypes.c_void_p, wintypes.LPCWSTR,
                                ctypes.POINTER(STARTUPINFOEXW), ctypes.POINTER(PROCESS_INFORMATION))
        self.CreateJobObjectW = f("CreateJobObjectW", H, ctypes.c_void_p, wintypes.LPCWSTR)
        self.SetInformationJobObject = f("SetInformationJobObject", B, H, ctypes.c_int, ctypes.c_void_p, D)
        self.AssignProcessToJobObject = f("AssignProcessToJobObject", B, H, H)
        self.QueryInformationJobObject = f("QueryInformationJobObject", B, H, ctypes.c_int, ctypes.c_void_p, D,
                                           ctypes.POINTER(D))
        self.TerminateJobObject = f("TerminateJobObject", B, H, wintypes.UINT)
        self.ResumeThread = f("ResumeThread", D, H)
        self.WaitForSingleObject = f("WaitForSingleObject", D, H, D)
        self.GetExitCodeProcess = f("GetExitCodeProcess", B, H, ctypes.POINTER(D))
        self.TerminateProcess = f("TerminateProcess", B, H, wintypes.UINT)
        self.GetOEMCP = f("GetOEMCP", wintypes.UINT)
        self.OpenProcess = f("OpenProcess", H, D, B, D)
        self.QueryFullProcessImageNameW = f("QueryFullProcessImageNameW", B, H, D, wintypes.LPWSTR, ctypes.POINTER(D))
        self.IsProcessInJob = f("IsProcessInJob", B, H, H, ctypes.POINTER(B))
        self.CreateToolhelp32Snapshot = f("CreateToolhelp32Snapshot", H, D, D)
        self.Process32FirstW = f("Process32FirstW", B, H, ctypes.POINTER(PROCESSENTRY32W))
        self.Process32NextW = f("Process32NextW", B, H, ctypes.POINTER(PROCESSENTRY32W))
        u32 = ctypes.WinDLL("user32", use_last_error=True)
        self.EnumWindows = f("EnumWindows", B, ENUM_JANELAS, wintypes.LPARAM, dll=u32)
        self.GetWindowThreadProcessId = f("GetWindowThreadProcessId", D, wintypes.HWND, ctypes.POINTER(D), dll=u32)
        self.IsWindowVisible = f("IsWindowVisible", B, wintypes.HWND, dll=u32)
        ntdll = ctypes.WinDLL("ntdll")
        # o processo do modo simples nasce suspenso pelo subprocess, que não devolve o handle da thread
        self.NtResumeProcess = f("NtResumeProcess", ctypes.c_long, H, dll=ntdll, opcional=True)

    def erro(self, onde: str) -> OSError:
        n = ctypes.get_last_error()
        return OSError(n, f"{onde}: {ctypes.FormatError(n).strip()}")


_k: _Kernel | None = None


def _kernel() -> _Kernel:
    global _k
    if _k is None:
        if sys.platform != "win32":
            raise Erro(501, t("O console só funciona no Windows."))
        _k = _Kernel()
    return _k


def conpty_disponivel() -> bool:
    return sys.platform == "win32" and _kernel().CreatePseudoConsole is not None


def versao_windows() -> int:
    """O número da compilação do Windows: a tela passa para o xterm.js, que ajusta o jeito de quebrar linhas do ConPTY."""
    try:
        return int(sys.getwindowsversion().build)
    except (AttributeError, ValueError):
        return 0


def _nome_do_processo(pid: int) -> str:
    k = _kernel()
    h = k.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        n = wintypes.DWORD(len(buf))
        if not k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
            return ""
        return Path(buf.value).name.lower()
    finally:
        k.CloseHandle(h)


# ---------- os processos de um job e quem tem janela ----------
def pids_do_job(job) -> list[int]:
    """Todos os processos vivos dentro do job (a lista cresce até caber)."""
    k = _kernel()
    n = 256
    while True:
        tamanho = 8 + n * ctypes.sizeof(ctypes.c_size_t)
        buf = ctypes.create_string_buffer(tamanho)
        if k.QueryInformationJobObject(job, JOB_OBJECT_BASIC_PROCESS_ID_LIST_CLASS, ctypes.byref(buf), tamanho, None):
            qtd = min(ctypes.c_uint32.from_buffer(buf, 4).value, n)  # NumberOfProcessIdsInList
            ids = (ctypes.c_size_t * n).from_buffer(buf, 8)
            return [int(ids[i]) for i in range(qtd)]
        if ctypes.get_last_error() != ERROR_MORE_DATA or n >= 65536:
            return []
        n *= 4


def _processos() -> dict[int, tuple[int, str]]:
    """pid -> (pid do pai, nome do executável em minúsculas) de todos os processos da máquina."""
    k = _kernel()
    snap = k.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snap or snap == INVALID_HANDLE_VALUE:
        return {}
    saida = {}
    try:
        e = PROCESSENTRY32W()
        e.dwSize = ctypes.sizeof(e)
        ok = k.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            saida[int(e.th32ProcessID)] = (int(e.th32ParentProcessID), e.szExeFile.lower())
            ok = k.Process32NextW(snap, ctypes.byref(e))
    finally:
        k.CloseHandle(snap)
    return saida


def pids_com_janela() -> set[int]:
    """Os processos donos de alguma janela de primeiro nível visível (a janela de um console conta para o programa
    que roda nele: o Windows atribui a janela do conhost ao cliente)."""
    k = _kernel()
    donos: set[int] = set()

    def visitar(hwnd, _):
        if k.IsWindowVisible(hwnd):
            pid = wintypes.DWORD()
            k.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value:
                donos.add(int(pid.value))
        return True

    k.EnumWindows(ENUM_JANELAS(visitar), 0)
    return donos


def _no_job(k: _Kernel, h, job) -> bool:
    dentro = wintypes.BOOL()
    return bool(k.IsProcessInJob(h, job, ctypes.byref(dentro))) and bool(dentro.value)


def _flags_do_job(k: _Kernel, job) -> int | None:
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    if not k.QueryInformationJobObject(job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS, ctypes.byref(info),
                                       ctypes.sizeof(info), None):
        return None
    return int(info.BasicLimitInformation.LimitFlags)


def tirar_kill_on_close(job) -> bool:
    """Tira o JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: fechar o último handle do job deixa de matar quem está nele."""
    k = _kernel()
    info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    flags = _flags_do_job(k, job)
    info.BasicLimitInformation.LimitFlags = (flags if flags is not None else 0) & ~JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    return bool(k.SetInformationJobObject(job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS, ctypes.byref(info),
                                          ctypes.sizeof(info)))


def _o_que_fica(pids: set[int], procs: dict, janelas: set[int], raizes: set[int]) -> set[int]:
    """Quem sobrevive a um encerramento com cuidado: os donos de janela visível (fora as raízes, o shell), tudo o
    que eles abriram (o VS Code e o navegador vivem de processos auxiliares sem janela) e os antepassados deles até
    a raiz (o lançador do Python de um .venv, por exemplo, mata o filho quando morre)."""
    pai = {p: procs.get(p, (0, ""))[0] for p in pids}
    com_janela = {p for p in pids if p in janelas and p not in raizes}
    # a janela de console pode aparecer como do conhost: então quem fica é o cliente, que abriu o conhost
    for p in list(com_janela):
        if procs.get(p, (0, ""))[1] in AJUDANTES_DE_CONSOLE and pai[p] in pids and pai[p] not in raizes:
            com_janela.add(pai[p])
    fica = set(com_janela)
    filhos: dict[int, list[int]] = {}
    for p in pids:
        filhos.setdefault(pai[p], []).append(p)
    fila = list(com_janela)
    while fila:
        for f in filhos.get(fila.pop(), []):
            if f not in fica and f not in raizes:
                fica.add(f)
                fila.append(f)
    for p in com_janela:
        a = pai.get(p)
        while a in pids and a not in raizes and a not in fica:
            fica.add(a)
            a = pai.get(a)
    return fica


def encerrar_job_com_cuidado(job, raizes=(), prazo: float = 2.0) -> list[int]:
    """Fecha um trabalho do jeito normal: mata no job o que não tem janela (o shell, um servidor, um ping) e o
    console escondido deles, deixa vivos os programas com janela (e o que eles abriram) e tira o KILL_ON_JOB_CLOSE,
    para que fechar o handle do job depois não leve as janelas junto. Devolve os pids dos donos de janela que ficaram.
    Só um encerramento de verdade (os._exit, o processo morto à força) ainda derruba tudo, pelo handle que fecha."""
    k = _kernel()
    raizes = {int(r) for r in raizes if r}
    fim = time.time() + prazo
    for _ in range(4):  # um processo que morre pode ter aberto outro no meio: confere de novo
        pids = set(pids_do_job(job))
        if not pids:
            break
        procs = _processos()
        fica = _o_que_fica(pids, procs, pids_com_janela(), raizes)
        antepassados_de_quem_fica: set[int] = set()
        for p in fica:
            a = procs.get(p, (0, ""))[0]
            while a and a not in antepassados_de_quem_fica and len(antepassados_de_quem_fica) < 4096:
                antepassados_de_quem_fica.add(a)
                a = procs.get(a, (0, ""))[0]
        matar = []
        for p in pids - fica:
            if procs.get(p, (0, ""))[1] in AJUDANTES_DE_CONSOLE:
                # o console de quem morre morre junto; o de uma família que fica (um programa com janela que roda
                # nele) fica e sai sozinho quando o último cliente sair
                if procs.get(p, (0, ""))[0] in antepassados_de_quem_fica:
                    continue
            matar.append(p)
        if not matar:
            break
        handles = []
        for p in matar:
            h = k.OpenProcess(PROCESS_TERMINATE | SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, False, p)
            if not h:
                continue
            if _no_job(k, h, job):  # o pid pode ter sido reaproveitado: nunca mata quem não é do job
                k.TerminateProcess(h, 1)
                handles.append(h)
            else:
                k.CloseHandle(h)
        for h in handles:
            k.WaitForSingleObject(h, max(0, int((fim - time.time()) * 1000)))
            k.CloseHandle(h)
        if time.time() >= fim:
            break
    tirar_kill_on_close(job)
    vivos = set(pids_do_job(job))
    return sorted(vivos & pids_com_janela())


def processos_restantes(job, raizes=()) -> list[int]:
    """Os processos que ainda estão no job, fora as raízes e os consoles escondidos (que saem sozinhos)."""
    raizes = {int(r) for r in raizes if r}
    return [p for p in pids_do_job(job) if p not in raizes and _nome_do_processo(p) not in AJUDANTES_DE_CONSOLE]


# ---------- o shell ----------
def _windows_powershell() -> str | None:
    raiz = os.environ.get("SystemRoot") or r"C:\Windows"
    caminho = Path(raiz) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    return str(caminho) if caminho.is_file() else shutil.which("powershell.exe")


def escolher_shell(simples: bool = False) -> tuple[str, list[str]]:
    """O PowerShell 7 (pwsh.exe) se estiver no PATH; senão o Windows PowerShell. O modo simples usa sempre o
    Windows PowerShell: é o que foi conferido lendo comandos por pipe (mostra o prompt e repete a linha)."""
    if not simples:
        pwsh = shutil.which("pwsh.exe")
        if pwsh:
            return pwsh, ["-NoLogo"]
    ps = _windows_powershell()
    if not ps:
        raise Erro(500, t("Não achei o PowerShell neste computador."))
    return ps, ["-NoLogo"]


def _linha_de_comando(exe: str, args: list[str]) -> str:
    return subprocess.list2cmdline([exe, *args])


FORA_DO_AMBIENTE = ("ELECTRON_RUN_AS_NODE", "ELECTRON_NO_ATTACH_CONSOLE", "__PYVENV_LAUNCHER__")
# o Electron liga estas para o servidor do Clave; no console vale o que a pessoa tem no Windows
DO_WINDOWS = ("PYTHONUTF8",)


def _variavel_do_windows(nome: str) -> str | None:
    """O valor que a pessoa deu à variável no Windows (a do usuário vale mais que a da máquina), ou None."""
    if sys.platform != "win32":
        return None
    import winreg
    lugares = ((winreg.HKEY_CURRENT_USER, r"Environment"),
               (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"))
    for raiz, chave in lugares:
        try:
            with winreg.OpenKey(raiz, chave) as k:
                valor, tipo = winreg.QueryValueEx(k, nome)
        except OSError:
            continue
        valor = str(valor)
        return winreg.ExpandEnvironmentStrings(valor) if tipo == winreg.REG_EXPAND_SZ else valor
    return None


def _ambiente() -> dict[str, str]:
    """O ambiente do shell: o do Clave sem as variáveis que só o Clave usa (o lançador, a pasta de dados, a API de
    demonstração, o token da ponte do navegador) e sem as que mudariam programas do Electron que a pessoa abrir dali
    (VS Code, por exemplo). O PYTHONUTF8 que o Electron liga para o servidor também sai: os scripts de Python da
    pessoa rodam aqui como no Terminal do Windows (com o valor dela, se ela tiver um)."""
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith("CLAVE_") and k.upper() not in FORA_DO_AMBIENTE and k.upper() not in DO_WINDOWS}
    for nome in DO_WINDOWS:
        valor = _variavel_do_windows(nome)
        if valor is not None:
            env[nome] = valor
    return env


def _bloco_ambiente(env: dict[str, str]) -> ctypes.Array:
    texto = "".join(f"{k}={v}\0" for k, v in sorted(env.items(), key=lambda kv: kv[0].upper()) if "=" not in k[1:])
    return ctypes.create_unicode_buffer(texto + "\0")


# ---------- um console ----------
class Console:
    def __init__(self, pasta: str, cols: int, rows: int, numero: int, *, simples: bool = False):
        self.id = secrets.token_hex(8)
        self.numero = numero
        self.pasta = pasta
        self.cols, self.rows = cols, rows
        self.criado = time.time()
        self.modo = "simples" if simples else "conpty"
        self.shell = ""
        self.pid = 0
        self.terminou = False
        self.fechado = False
        self.codigo: int | None = None
        self._cond = threading.Condition()
        self._pedacos: list[str] = []
        self._primeiro = 0          # o número do primeiro pedaço ainda guardado
        self._guardado = 0          # quantos caracteres estão guardados
        self._escrita = threading.Lock()
        self._liberar = threading.Lock()
        self._job = None
        self._hproc = None
        self._hthread = None
        self._hpc = None
        self._fd_entrada = None
        self._fd_saida = None
        self._popen: subprocess.Popen | None = None
        self._codec = "utf-8"
        self._leitor: threading.Thread | None = None
        self._leitura_acabou = False
        self._fechar_no_fim = False

    @property
    def titulo(self) -> str:
        return t("PowerShell {numero}", numero=self.numero)

    def resumo(self) -> dict:
        return {"id": self.id, "titulo": self.titulo, "numero": self.numero, "modo": self.modo, "pasta": self.pasta,
                "shell": Path(self.shell).name if self.shell else "", "pid": self.pid, "cols": self.cols,
                "rows": self.rows, "terminou": self.terminou, "codigo": self.codigo, "criado": self.criado,
                "proximo": self.proximo, "ocupado": self.ocupado(), "build": versao_windows()}

    def ocupado(self) -> bool:
        """Tem algum programa rodando dentro do shell que pararia se o console fechasse? Algum processo vivo no job
        além do próprio shell, do conhost (no modo simples o console escondido do shell nasce dentro do job) e dos
        programas com janela, que continuam abertos quando o console fecha. A tela usa para perguntar antes de fechar
        ou reiniciar um console no meio de um trabalho."""
        if self.terminou or sys.platform != "win32":
            return False
        with self._liberar:
            if not self._job:
                return False
            pids = set(pids_do_job(self._job))
        outros = {p for p in pids if p != self.pid and _nome_do_processo(p) not in AJUDANTES_DE_CONSOLE}
        if not outros:
            return False
        fica = _o_que_fica(pids, _processos(), pids_com_janela(), {self.pid})
        return any(p not in fica for p in outros)

    # ----- abrir -----
    def abrir(self) -> None:
        k = _kernel()
        job = k.CreateJobObjectW(None, None)
        if not job:
            raise k.erro("CreateJobObjectW")
        self._job = job
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k.SetInformationJobObject(job, JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS, ctypes.byref(info),
                                         ctypes.sizeof(info)):
            raise k.erro("SetInformationJobObject")
        if self.modo == "conpty":
            self._abrir_conpty(k)
        else:
            self._abrir_simples(k)
        self._leitor = threading.Thread(target=self._ler, name=f"console-ler-{self.id}", daemon=True)
        self._leitor.start()
        threading.Thread(target=self._esperar, name=f"console-esperar-{self.id}", daemon=True).start()

    def _abrir_conpty(self, k: _Kernel) -> None:
        if k.CreatePseudoConsole is None:
            raise OSError(0, "CreatePseudoConsole")
        exe, args = escolher_shell()
        self.shell = exe
        H = wintypes.HANDLE
        entrada_pty, entrada_nossa = H(), H()     # a pessoa digita: nós escrevemos, o pseudo console lê
        saida_nossa, saida_pty = H(), H()         # o shell escreve no pseudo console, nós lemos
        if not k.CreatePipe(ctypes.byref(entrada_pty), ctypes.byref(entrada_nossa), None, 0):
            raise k.erro("CreatePipe")
        if not k.CreatePipe(ctypes.byref(saida_nossa), ctypes.byref(saida_pty), None, 0):
            e = k.erro("CreatePipe")
            k.CloseHandle(entrada_pty)
            k.CloseHandle(entrada_nossa)
            raise e
        import msvcrt
        hpc = H()
        hr = k.CreatePseudoConsole(COORD(self.cols, self.rows), entrada_pty, saida_pty, 0, ctypes.byref(hpc))
        # as pontas do pseudo console são dele agora: fechar as nossas cópias é o que faz a leitura ver o fim
        k.CloseHandle(entrada_pty)
        k.CloseHandle(saida_pty)
        if hr < 0:
            k.CloseHandle(entrada_nossa)
            k.CloseHandle(saida_nossa)
            raise OSError(hr & 0xFFFFFFFF, f"CreatePseudoConsole: HRESULT 0x{hr & 0xFFFFFFFF:08X}")
        self._hpc = hpc
        self._fd_entrada = msvcrt.open_osfhandle(entrada_nossa.value, os.O_WRONLY | os.O_BINARY)
        self._fd_saida = msvcrt.open_osfhandle(saida_nossa.value, os.O_RDONLY | os.O_BINARY)

        tamanho = ctypes.c_size_t(0)
        k.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(tamanho))  # só pergunta o tamanho
        lista = ctypes.create_string_buffer(tamanho.value)
        if not k.InitializeProcThreadAttributeList(lista, 1, 0, ctypes.byref(tamanho)):
            raise k.erro("InitializeProcThreadAttributeList")
        try:
            # o valor do atributo é o próprio HPCON (não um ponteiro para ele), com o tamanho de um HANDLE
            if not k.UpdateProcThreadAttribute(lista, 0, PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE, hpc.value,
                                               ctypes.sizeof(wintypes.HANDLE), None, None):
                raise k.erro("UpdateProcThreadAttribute")
            si = STARTUPINFOEXW()
            si.StartupInfo.cb = ctypes.sizeof(STARTUPINFOEXW)
            # handles nulos de propósito: sem isso, quando a saída do servidor está redirecionada (Electron, testes),
            # o shell herda esses handles e escreve neles em vez de no pseudo console
            si.StartupInfo.dwFlags = STARTF_USESTDHANDLES
            si.lpAttributeList = ctypes.addressof(lista)
            pi = PROCESS_INFORMATION()
            cmd = ctypes.create_unicode_buffer(_linha_de_comando(exe, args))
            amb = _bloco_ambiente(_ambiente())
            if not k.CreateProcessW(None, cmd, None, None, False,
                                    EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT | CREATE_SUSPENDED,
                                    amb, self.pasta, ctypes.byref(si), ctypes.byref(pi)):
                raise k.erro("CreateProcessW")
        finally:
            k.DeleteProcThreadAttributeList(lista)
        self._hproc, self._hthread, self.pid = pi.hProcess, pi.hThread, pi.dwProcessId
        if not k.AssignProcessToJobObject(self._job, pi.hProcess):
            e = k.erro("AssignProcessToJobObject")
            k.TerminateProcess(pi.hProcess, 1)
            raise e
        k.ResumeThread(pi.hThread)

    def _abrir_simples(self, k: _Kernel) -> None:
        exe, args = escolher_shell(simples=True)
        self.shell = exe
        oem = k.GetOEMCP()
        try:
            codecs.lookup(f"cp{oem}")
            self._codec = f"cp{oem}"   # sem pseudo console, o PowerShell lê e escreve na página de código OEM
        except LookupError:
            self._codec = "utf-8"
        p = subprocess.Popen([exe, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             cwd=self.pasta, env=_ambiente(), creationflags=CREATE_NO_WINDOW | CREATE_SUSPENDED)
        self._popen = p
        self.pid = p.pid
        hproc = wintypes.HANDLE(int(p._handle))
        if not k.AssignProcessToJobObject(self._job, hproc):
            e = k.erro("AssignProcessToJobObject")
            p.kill()
            raise e
        if k.NtResumeProcess is None or k.NtResumeProcess(hproc) < 0:
            p.kill()
            raise OSError(0, "NtResumeProcess")
        self._fd_entrada = p.stdin.fileno()
        self._fd_saida = p.stdout.fileno()

    # ----- saída -----
    def _ler(self) -> None:
        dec = codecs.getincrementaldecoder(self._codec)(errors="replace")
        fd = self._fd_saida
        arquivo = self._popen.stdout if self._popen is not None else None
        while True:
            try:
                bruto = os.read(fd, 65536)
            except OSError:
                bruto = b""
            if not bruto:
                break
            texto = dec.decode(bruto)
            if texto:
                self._guardar(texto)
        resto = dec.decode(b"", final=True)
        if resto:
            self._guardar(resto)
        with self._liberar:
            self._leitura_acabou = True
            fechar = self._fechar_no_fim
        if fechar:  # o console já foi solto enquanto esta leitura esperava: a ponta de leitura fecha aqui
            try:
                arquivo.close() if arquivo is not None else os.close(fd)
            except (OSError, ValueError):
                pass

    def _guardar(self, texto: str) -> None:
        with self._cond:
            self._pedacos.append(texto)
            self._guardado += len(texto)
            while self._guardado > LIMITE_SAIDA and len(self._pedacos) > 1:
                self._guardado -= len(self._pedacos.pop(0))
                self._primeiro += 1
            self._cond.notify_all()

    @property
    def proximo(self) -> int:
        return self._primeiro + len(self._pedacos)

    def desde(self, n: int, espera: float = 15.0) -> tuple[list[tuple[int, str]], bool]:
        """Os pedaços a partir do número n (espera até `espera` segundos se ainda não chegou nada) e se o console
        acabou e não tem mais nada para mandar."""
        with self._cond:
            if n >= self.proximo and not (self.terminou or self.fechado):
                self._cond.wait(espera)
            i = max(0, n - self._primeiro)
            itens = [(self._primeiro + j, self._pedacos[j]) for j in range(i, len(self._pedacos))]
            acabou = (self.terminou or self.fechado) and not itens
            return itens, acabou

    def texto(self) -> str:
        with self._cond:
            return "".join(self._pedacos)

    def primeiro(self) -> int:
        with self._cond:
            return self._primeiro

    # ----- entrada e tamanho -----
    def escrever(self, dados: str) -> None:
        if self.terminou or self.fechado or self._fd_entrada is None:
            raise Erro(409, t("Este console já terminou. Abra de novo para continuar."))
        bruto = dados.encode(self._codec, errors="replace")
        with self._escrita:
            try:
                while bruto:
                    n = os.write(self._fd_entrada, bruto)
                    bruto = bruto[n:]
            except OSError:
                raise Erro(409, t("Este console já terminou. Abra de novo para continuar."))

    def redimensionar(self, cols: int, rows: int) -> None:
        self.cols, self.rows = cols, rows
        if self.modo != "conpty" or self.terminou:
            return
        # com a mesma trava de quem fecha o pseudo console: nunca um ResizePseudoConsole num HPCON já liberado
        with self._liberar:
            if self._hpc is None:
                return
            hr = _kernel().ResizePseudoConsole(self._hpc, COORD(cols, rows))
        if hr < 0:
            raise Erro(500, t("Não deu para mudar o tamanho do console."))

    # ----- fim -----
    def _esperar(self) -> None:
        k = _kernel()
        codigo = None
        if self._popen is not None:
            codigo = self._popen.wait()
        elif self._hproc:
            k.WaitForSingleObject(self._hproc, INFINITE)
            c = wintypes.DWORD()
            if k.GetExitCodeProcess(self._hproc, ctypes.byref(c)):
                codigo = c.value if c.value < 0x80000000 else c.value - 0x100000000
        time.sleep(0.25)  # deixa a última saída do shell chegar antes de fechar o pseudo console
        self._fechar_pty()
        if self._leitor:
            self._leitor.join(5)
        with self._cond:
            self.codigo = codigo
            self.terminou = True
            self._cond.notify_all()

    def _fechar_pty(self) -> None:
        """Fecha o pseudo console uma vez só. A leitura continua drenando a saída enquanto ele fecha (sem isso o
        ClosePseudoConsole pode esperar para sempre), e o conhost sai fechando a ponta dele: a leitura vê o fim."""
        with self._liberar:
            hpc, self._hpc = self._hpc, None
        if hpc is not None:
            _kernel().ClosePseudoConsole(hpc)
        if self._popen is not None:
            for arq in (self._popen.stdin,):
                try:
                    arq.close()
                except OSError:
                    pass

    def _encerrar_job(self) -> list[int]:
        """Mata o shell e o que ele abriu sem janela; os programas com janela ficam (encerrar_job_com_cuidado)."""
        with self._liberar:
            job = self._job
        if not job:
            return []
        try:
            return encerrar_job_com_cuidado(job, {self.pid})
        except Exception:  # noqa: BLE001 (o cuidado falhou: melhor fechar tudo do que deixar o shell vivo)
            _kernel().TerminateJobObject(job, 1)
            return []

    def fechar(self, espera: float = 5.0) -> list[int]:
        """Fecha o console: o shell e o que ele abriu sem janela morrem; programas com janela continuam abertos.
        Solta os handles e devolve os pids das janelas que ficaram."""
        self.fechado = True
        abertos = self._encerrar_job()
        if self._popen is not None:
            try:
                self._popen.kill()
            except OSError:
                pass
        fim = time.time() + espera
        with self._cond:
            while not self.terminou and time.time() < fim:
                self._cond.wait(0.2)
            self._cond.notify_all()
        if not self.terminou:
            self._fechar_pty()  # a espera não terminou (não devia acontecer): fecha daqui mesmo
        self._soltar()
        return abertos

    def _soltar(self) -> None:
        """Solta tudo o que o console segura. Também serve para limpar uma abertura que falhou no meio."""
        k = _kernel()
        with self._liberar:
            # a leitura ainda presa num read (um filho do shell segurando a saída, por exemplo) segura a trava do
            # descritor no CRT: fechar por baixo dela travaria aqui, então quem fecha a ponta de leitura é ela, no fim
            lendo = self._leitor is not None and not self._leitura_acabou
            if lendo:
                self._fechar_no_fim = True
            job, self._job = self._job, None
            hproc, self._hproc = self._hproc, None
            hthread, self._hthread = self._hthread, None
            hpc, self._hpc = self._hpc, None
            popen, self._popen = self._popen, None
            fds = []
            if popen is None:
                fds = [self._fd_entrada] + ([] if lendo else [self._fd_saida])
            self._fd_entrada = self._fd_saida = None
        for fd in fds:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if hpc is not None:  # só sobra aberto quando a abertura falhou: sem leitura, mas a ponta já foi fechada
            k.ClosePseudoConsole(hpc)
        if popen is not None:
            if popen.poll() is None:
                try:
                    popen.kill()
                except OSError:
                    pass
            for arq in (popen.stdin, None if lendo else popen.stdout):
                try:
                    if arq:
                        arq.close()
                except (OSError, ValueError):
                    pass
        # o job por último: com o KILL_ON_JOB_CLOSE ainda ligado (uma abertura que falhou), fechar o handle mata quem
        # sobrou; depois de um encerramento com cuidado ele já saiu, e as janelas continuam abertas
        for h in (hthread, hproc, job):
            if h:
                k.CloseHandle(h)

    def matar_rapido(self) -> None:
        """Na saída normal do servidor: o shell e o que não tem janela morrem na hora, as janelas ficam (sem esperar
        a saída do shell nem fechar o pseudo console: o processo do servidor está acabando e leva os dois)."""
        try:
            k = _kernel()
            with self._liberar:
                job, self._job = self._job, None
            if job:
                try:
                    encerrar_job_com_cuidado(job, {self.pid}, prazo=1.0)
                except Exception:  # noqa: BLE001
                    k.TerminateJobObject(job, 1)
                k.CloseHandle(job)
        except Exception:  # noqa: BLE001 (na saída do processo, nada pode parar o resto)
            pass


# ---------- o registro de consoles ----------
def _numero_livre() -> int:
    usados = {c.numero for c in _consoles.values()}
    n = 1
    while n in usados:
        n += 1
    return n


def _inteiro(valor, padrao: int, minimo: int, maximo: int) -> int:
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, n))


def _tamanho(d: dict, padrao=(100, 30)) -> tuple[int, int]:
    return (_inteiro(d.get("cols"), padrao[0], 2, MAX_COLUNAS), _inteiro(d.get("rows"), padrao[1], 1, MAX_LINHAS))


def abrir(pasta: str, cols: int = 100, rows: int = 30, *, simples: bool | None = None) -> Console:
    """Abre um console na pasta. Tenta o ConPTY; se ele não existir ou falhar, abre no modo simples."""
    if sys.platform != "win32":
        raise Erro(501, t("O console só funciona no Windows."))
    if not isinstance(pasta, str) or not pasta.strip():
        raise Erro(400, t("Escolha uma pasta para abrir o console."))
    caminho = Path(pasta.strip())
    if not caminho.is_absolute() or not caminho.is_dir():
        raise Erro(400, t("A pasta {pasta} não existe mais. Escolha outra pasta.", pasta=pasta.strip()))
    if simples is None:
        simples = os.environ.get("CLAVE_CONSOLE_SIMPLES") == "1" or not conpty_disponivel()
    with _trava:
        if len(_consoles) >= MAX_CONSOLES:
            raise Erro(409, t("Já tem {n} consoles abertos. Feche um para abrir outro.", n=MAX_CONSOLES))
        c = Console(str(caminho), cols, rows, _numero_livre(), simples=simples)
        _consoles[c.id] = c  # reserva o número enquanto abre
    try:
        _abrir_ou_simples(c)
    except Erro:
        with _trava:
            _consoles.pop(c.id, None)
        raise
    except OSError as e:
        with _trava:
            _consoles.pop(c.id, None)
        raise Erro(500, t("Não foi possível abrir o PowerShell: {erro}", erro=e.strerror or e))
    return c


def _abrir_ou_simples(c: Console) -> None:
    """Abre pelo ConPTY; se o Windows recusar, solta o que ficou pela metade e abre o mesmo console por pipes."""
    try:
        c.abrir()
        return
    except Erro:
        c._soltar()
        raise
    except OSError:
        c._soltar()
        if c.modo != "conpty":
            raise
    c.modo = "simples"
    try:
        c.abrir()
    except (Erro, OSError):
        c._soltar()
        raise


def pegar(cid: str) -> Console:
    with _trava:
        c = _consoles.get(cid)
    if not c:
        raise Erro(404, t("Console não encontrado. Ele pode ter sido fechado."))
    return c


def listar() -> list[dict]:
    with _trava:
        lista = sorted(_consoles.values(), key=lambda c: c.criado)
    return [c.resumo() for c in lista]


def fechar(cid: str) -> bool:
    with _trava:
        c = _consoles.pop(cid, None)
    if not c:
        return False
    c.fechar()
    return True


def fechar_todos() -> None:
    with _trava:
        todos = list(_consoles.values())
        _consoles.clear()
    for c in todos:
        c.matar_rapido()


atexit.register(fechar_todos)


# ---------- as rotas ----------
@rota("POST", "/api/consoles")
def r_abrir(h, **_):
    d = h.corpo()
    cols, rows = _tamanho(d)
    c = abrir(d.get("pasta") or "", cols, rows)
    h._json({"id": c.id, "titulo": c.titulo, "modo": c.modo, "console": c.resumo()})


@rota("GET", "/api/consoles")
def r_listar(h, **_):
    h._json({"consoles": listar(), "maximo": MAX_CONSOLES})


@rota("GET", "/api/consoles/<cid>/saida")
def r_saida(h, cid):
    c = pegar(cid)
    try:
        desde = max(0, int(h.query().get("desde") or 0))
    except ValueError:
        raise Erro(400, t("Pedido inválido."))
    h.send_response(200)
    h.send_header("Content-Type", "text/event-stream; charset=utf-8")
    h.send_header("Cache-Control", "no-store, no-transform")
    h.send_header("X-Content-Type-Options", "nosniff")
    h.send_header("X-Accel-Buffering", "no")
    h.send_header("Connection", "close")
    h.end_headers()
    h.close_connection = True
    # o mesmo preenchimento inicial do /eventos: há quem segure o começo de uma resposta até passar de alguns KB
    h.wfile.write(b": " + b" " * 4096 + b"\n\n")

    def cortado(n: int) -> None:
        h.wfile.write(f"data: {json.dumps({'cortado': n})}\n\n".encode("utf-8"))

    primeiro = c.primeiro()
    if desde < primeiro:  # a tela ficou longe enquanto saíam mais de ~2 MB: o começo não existe mais
        cortado(primeiro - desde)
        desde = primeiro
    h.wfile.flush()
    while True:
        itens, acabou = c.desde(desde, espera=15)
        if itens:
            if itens[0][0] > desde:  # no meio da conexão (rede lenta, saída enorme) também pode sobrar um buraco
                cortado(itens[0][0] - desde)
            grupo, tam = [], 0
            for seq, dados in itens:
                grupo.append(dados)
                tam += len(dados)
                if tam >= PEDACO_SSE or seq == itens[-1][0]:
                    ev = {"seq": seq, "dados": "".join(grupo)}
                    h.wfile.write(f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode("utf-8"))
                    grupo, tam = [], 0
            desde = itens[-1][0] + 1
            h.wfile.flush()
            continue
        if acabou:
            fim = {"fim": True, "codigo": c.codigo, "fechado": c.fechado}
            h.wfile.write(f"data: {json.dumps(fim)}\n\n".encode("utf-8"))
            h.wfile.flush()
            return
        h.wfile.write(b": ping\n\n")
        h.wfile.flush()


@rota("POST", "/api/consoles/<cid>/entrada")
def r_entrada(h, cid):
    c = pegar(cid)
    dados = h.corpo().get("dados")
    if not isinstance(dados, str):
        raise Erro(400, t("Pedido inválido."))
    if len(dados) > LIMITE_ENTRADA:
        raise Erro(413, t("Texto grande demais para mandar ao console de uma vez."))
    if dados:
        c.escrever(dados)
    h._json({"ok": True})


@rota("POST", "/api/consoles/<cid>/tamanho")
def r_tamanho(h, cid):
    c = pegar(cid)
    d = h.corpo()
    try:
        cols, rows = int(d.get("cols")), int(d.get("rows"))
    except (TypeError, ValueError):
        raise Erro(400, t("Tamanho de console inválido."))
    if not (2 <= cols <= MAX_COLUNAS and 1 <= rows <= MAX_LINHAS):
        raise Erro(400, t("Tamanho de console inválido."))
    c.redimensionar(cols, rows)
    h._json({"ok": True})


@rota("DELETE", "/api/consoles/<cid>")
def r_fechar(h, cid):
    if not fechar(cid):
        raise Erro(404, t("Console não encontrado. Ele pode ter sido fechado."))
    h._json({"ok": True})
