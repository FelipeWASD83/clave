"""Cria uma pasta de trabalho a partir do modelo que vem com o Clave (modelo-de-pasta/)."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from config import MODELO_DE_PASTA

MARCADOR = "<!-- SOBRE-MIM -->"


def _texto_sobre(r: dict) -> str:
    linhas = []
    if r.get("nome"):
        linhas.append(f"- **Nome:** {r['nome'].strip()}")
    if r.get("ocupacao"):
        linhas.append(f"- **O que eu faço:** {r['ocupacao'].strip()}")
    exp = {
        "nenhuma": "Não sei programar. Explique o que você fez e como usar, não como o código funciona por dentro.",
        "pouca": "Sei o básico de computador e um pouco de programação. Explique termos técnicos quando aparecerem.",
        "programo": "Sei programar. Pode usar termos técnicos normalmente.",
    }.get(r.get("experiencia") or "", "")
    if exp:
        linhas.append(f"- **Experiência com programação:** {exp}")
    if r.get("linguagens"):
        linhas.append(f"- **Linguagens e programas que uso:** {r['linguagens'].strip()}")
    if r.get("sistema"):
        linhas.append(f"- **Meu computador:** {r['sistema'].strip()}")
    if r.get("preferencias"):
        linhas.append(f"- **Como prefiro as respostas:** {r['preferencias'].strip()}")
    return "\n".join(linhas) if linhas else "- (preencha aqui quem você é e como prefere as respostas)"


def criar(destino: str, nome: str, respostas: dict | None = None, iniciar_git: bool = True) -> dict:
    if not MODELO_DE_PASTA.is_dir():
        raise ValueError("O modelo de pasta não veio junto com esta cópia do Clave.")
    base = Path(destino).expanduser()
    if not base.is_dir():
        raise ValueError("A pasta escolhida para criar o modelo não existe.")
    nome = (nome or "").strip()
    if not nome or re.search(r'[<>:"/\\|?*]', nome) or nome in (".", ".."):
        raise ValueError("Nome de pasta inválido.")
    alvo = base / nome
    if alvo.exists():
        raise ValueError("Já existe uma pasta com esse nome aí.")
    shutil.copytree(MODELO_DE_PASTA, alvo)
    claude_md = alvo / "CLAUDE.md"
    if claude_md.is_file():
        texto = claude_md.read_text(encoding="utf-8")
        if MARCADOR in texto:
            texto = texto.replace(MARCADOR, _texto_sobre(respostas or {}), 1)
            claude_md.write_text(texto, encoding="utf-8")
    git = None
    if iniciar_git and shutil.which("git"):
        r = subprocess.run(["git", "init"], cwd=str(alvo), capture_output=True, text=True,
                           creationflags=0x08000000 if sys.platform == "win32" else 0)
        git = r.returncode == 0
    return {"caminho": str(alvo), "git": git}
