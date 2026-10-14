"""Abre o Clave sem janela de console (é o que os atalhos chamam).

Antes de abrir, garante que o Electron é o da versão pedida em versao.json: depois
de uma atualização que troca o Electron, o download acontece aqui, com uma janelinha
de progresso. Se não der para ter o Electron, abre pelo supervisor no navegador.
"""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import preparar  # noqa: E402

RAIZ = preparar.RAIZ
SEM_CONSOLE = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _baixar_com_janela() -> None:
    erro: list[BaseException] = []

    def trabalho():
        try:
            preparar.baixar_electron()
        except BaseException as e:  # SystemExit também: o preparar usa para dar o motivo
            erro.append(e)

    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        trabalho()
    else:
        raiz = tk.Tk()
        raiz.title("Clave")
        raiz.resizable(False, False)
        quadro = ttk.Frame(raiz, padding=20)
        quadro.pack()
        ttk.Label(quadro, text="Preparando a janela do Clave (uns 110 MB, só desta vez)...").pack(anchor="w")
        barra = ttk.Progressbar(quadro, mode="indeterminate", length=360)
        barra.pack(pady=(12, 0))
        barra.start(12)
        t = threading.Thread(target=trabalho, daemon=True)
        t.start()

        def conferir():
            if t.is_alive():
                raiz.after(200, conferir)
            else:
                raiz.destroy()

        raiz.after(200, conferir)
        raiz.mainloop()
        t.join()
    if erro:
        raise RuntimeError(str(erro[0]))


def main() -> int:
    if not preparar.runtime_ok() and not (RAIZ / "node_modules" / "electron" / "dist" / "electron.exe").is_file():
        try:
            _baixar_com_janela()
        except (OSError, RuntimeError):
            pass  # segue com o Electron antigo, se houver, ou com o navegador
    exe = preparar.executavel()
    if exe:
        subprocess.Popen([str(exe), str(RAIZ)], cwd=RAIZ, creationflags=SEM_CONSOLE)
    else:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        py = pythonw if pythonw.is_file() else Path(sys.executable)
        subprocess.Popen([str(py), str(RAIZ / "servidor" / "iniciar.py")], cwd=RAIZ, creationflags=SEM_CONSOLE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
