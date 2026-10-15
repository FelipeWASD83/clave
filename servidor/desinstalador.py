"""Desinstalar o Clave pelo app (Configurações > Atualizações e sobre).

O trabalho de verdade é do ferramentas/desinstalar.ps1, que precisa sobreviver ao fim do app:
- ele é copiado para o %TEMP% (a pasta dele vai ser apagada) e lê os parâmetros de um .json ao lado (sem briga de
  aspas na linha de comando);
- é lançado por um PowerShell intermediário que termina na hora (Start-Process), então o desinstalador fica sem pai:
  o Electron, ao fechar, derruba a árvore do servidor com `taskkill /T`, e um filho do servidor morreria junto;
- nada de DETACHED_PROCESS: o powershell.exe 5.1 lançado assim sai com código 0 sem rodar o script.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import config
from i18n import t


def motivo_para_nao(raiz: Path) -> str | None:
    """Por que esta pasta não pode se desinstalar sozinha (None quando pode). O script confere tudo de novo."""
    raiz = raiz.resolve()
    if (raiz / ".git").exists():
        return t("Esta é uma cópia de desenvolvimento (tem a pasta .git): o Clave não se apaga sozinho aqui. Apague a pasta à mão, se quiser.")
    if sys.platform != "win32":
        return t("Desinstalar pelo app só funciona no Windows. Apague a pasta do Clave à mão.")
    perigosas = {Path(p).resolve() for p in (os.environ.get("USERPROFILE"), os.environ.get("SystemRoot"),
                                              os.environ.get("ProgramFiles"), os.environ.get("APPDATA"),
                                              os.environ.get("LOCALAPPDATA")) if p}
    if len(str(raiz)) < 8 or raiz.parent == raiz or raiz in perigosas \
            or not (raiz / "versao.json").is_file() or not (raiz / "servidor" / "servidor.py").is_file():
        return t("O Clave não conseguiu confirmar que a pasta {pasta} é só dele. Apague à mão, se quiser.", pasta=str(raiz))
    return None


def lancar(raiz: Path, processo: int, *, sem_janela: bool = False, atalhos: list[str] | None = None,
           dados_electron: str = "") -> Path:
    """Copia o script para o %TEMP%, grava os parâmetros e lança sem pai. Devolve o .json dos parâmetros."""
    tmp = Path(tempfile.mkdtemp(prefix="clave-desinstalar-"))
    script = tmp / "desinstalar.ps1"
    shutil.copy2(config.RAIZ / "ferramentas" / "desinstalar.ps1", script)
    params = tmp / "parametros.json"
    params.write_text(json.dumps({
        "Pasta": str(raiz), "Processo": processo, "SemJanela": sem_janela, "Atalhos": atalhos or [],
        "DadosElectron": dados_electron,
        "Mensagem": t("O Clave foi desinstalado."),
        "MensagemSobrou": t("O Clave foi desinstalado, mas a pasta {pasta} não saiu inteira (algum arquivo estava em uso). Apague o que sobrou à mão.", pasta=str(raiz)),
        "MensagemParou": t("O Clave não foi desinstalado: não deu para confirmar que a pasta {pasta} é só dele. Apague à mão, se quiser.", pasta=str(raiz)),
    }, ensure_ascii=False), encoding="utf-8")

    def aspas(p: Path) -> str:  # dentro de uma string de aspas simples do PowerShell
        return str(p).replace("'", "''")
    comando = (f"Start-Process -FilePath powershell -WindowStyle Hidden -ArgumentList "
               f"'-NoProfile -ExecutionPolicy Bypass -File \"{aspas(script)}\" -Config \"{aspas(params)}\"'")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", comando],
                   capture_output=True, timeout=60,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return params
