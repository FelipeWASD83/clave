"""Supervisor do Clave: aplica a atualização baixada, sobe o servidor e reinicia quando ele pede.

Quem chama é a janela do Electron (com --sem-janela) ou o Clave.bat quando o
Electron não está disponível (aí ele mesmo abre a interface numa janela do Edge
ou do navegador padrão). Código de saída 3 do servidor = "acabei de baixar uma
atualização, me suba de novo"; se a versão nova não conseguir subir, a anterior
volta sozinha.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import atualizador  # noqa: E402
import config  # noqa: E402

LOG = config.DADOS / "logs"


def log(msg: str) -> None:
    LOG.mkdir(parents=True, exist_ok=True)
    linha = time.strftime("%Y-%m-%d %H:%M:%S ") + msg
    print(linha, flush=True)
    with open(LOG / "supervisor.log", "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def porta_livre(p: int) -> bool:
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", p))
            return True
        except OSError:
            return False


def clave_respondendo(p: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/saude", timeout=1.5):
            return True
    except urllib.error.HTTPError as e:
        return e.code == 401  # é o Clave, só sem a sessão
    except OSError:
        return False


def instalar_dependencias() -> None:
    log("As dependências mudaram: instalando com o pip.")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-q", "-r",
                        str(config.RAIZ / "requirements.txt")], capture_output=True, text=True)
    if r.returncode != 0:
        log("pip falhou: " + (r.stderr or r.stdout)[-1500:])


def aplicar_atualizacao() -> bool:
    try:
        r = atualizador.aplicar_pendente()
    except atualizador.ErroAtualizacao as e:
        log(f"Atualização não aplicada: {e}")
        return False
    if not r:
        return False
    log(f"Atualização para a versão {r['versao']} aplicada.")
    if r.get("dependencias_mudaram"):
        instalar_dependencias()
    return True


def processo_vivo(pid: int) -> bool:
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes
    h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    codigo = ctypes.c_ulong()
    ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(codigo))
    ctypes.windll.kernel32.CloseHandle(h)
    return codigo.value == 259  # STILL_ACTIVE


def vigiar_pai(pid: int, filho: dict) -> None:
    """Se a janela do Electron morrer sem avisar, derruba o servidor e sai (nada fica rodando escondido)."""
    import threading

    def laco():
        while True:
            time.sleep(3)
            if not processo_vivo(pid):
                log("A janela do Clave fechou: encerrando o servidor.")
                p = filho.get("proc")
                if p and p.poll() is None:
                    if sys.platform == "win32":  # o python do .venv abre outro processo: derruba a árvore toda
                        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
                    else:
                        p.terminate()
                os._exit(0)
    threading.Thread(target=laco, daemon=True).start()


def abrir_janela(url: str) -> None:
    """Sem Electron: abre a interface numa janela de app do Edge (sem barra do navegador), ou no navegador padrão."""
    edge = None
    if sys.platform == "win32":
        for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
            if base and Path(base, "Microsoft", "Edge", "Application", "msedge.exe").is_file():
                edge = str(Path(base, "Microsoft", "Edge", "Application", "msedge.exe"))
                break
    if edge:
        perfil = config.DADOS / "janela-edge"
        subprocess.Popen([edge, f"--app={url}", f"--user-data-dir={perfil}", "--no-first-run",
                          "--no-default-browser-check", "--window-size=1280,860"])
    else:
        webbrowser.open(url)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--porta", type=int, default=config.PORTA_PADRAO)
    ap.add_argument("--sem-janela", action="store_true", help="não abrir janela (o Electron cuida dela)")
    ap.add_argument("--pai", type=int, default=0, help="PID da janela do Electron; se ela morrer, tudo fecha")
    a = ap.parse_args()
    os.environ["CLAVE_LANCADOR"] = "1"
    porta = a.porta
    filho: dict = {}
    if a.pai:
        vigiar_pai(a.pai, filho)

    if not a.sem_janela:
        if not porta_livre(porta):
            if clave_respondendo(porta):
                log("O Clave já está aberto: só abrindo a janela.")
                segredo = (config.DADOS / "sessao.key").read_text(encoding="ascii").strip()
                abrir_janela(f"http://127.0.0.1:{porta}/?t={segredo}")
                return 0
            porta = next((p for p in range(porta + 1, porta + 30) if porta_livre(p)), porta)

    janela_aberta = a.sem_janela
    while True:
        acabou_de_atualizar = aplicar_atualizacao()
        args = [sys.executable, str(config.RAIZ / "servidor" / "servidor.py"), "--porta", str(porta),
                "--fechar-sem-janela", "10"]
        if a.pai:
            args += ["--pai", str(a.pai)]
        inicio = time.time()
        log(f"Subindo o servidor na porta {porta}.")
        proc = subprocess.Popen(args, cwd=str(config.RAIZ))
        filho["proc"] = proc
        if not janela_aberta:
            for _ in range(120):
                if proc.poll() is not None or clave_respondendo(porta):
                    break
                time.sleep(0.25)
            if proc.poll() is None:
                segredo = (config.DADOS / "sessao.key").read_text(encoding="ascii").strip()
                abrir_janela(f"http://127.0.0.1:{porta}/?t={segredo}")
                janela_aberta = True
        codigo = proc.wait()
        durou = time.time() - inicio
        log(f"O servidor saiu com o código {codigo} depois de {durou:.0f} s.")
        if codigo == 3:
            continue
        if acabou_de_atualizar and codigo != 0 and durou < 30:
            log("A versão nova não subiu: voltando para a anterior.")
            if atualizador.reverter():
                continue
        return codigo


if __name__ == "__main__":
    sys.exit(main())
