"""Cria uma pasta de trabalho a partir do modelo que vem com o Clave (modelo-de-pasta/; em inglês, modelo-de-pasta-en/)."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

from config import MODELO_DE_PASTA
from i18n import idioma, t

MARCADOR = "<!-- SOBRE-MIM -->"


def _modelo_en() -> Path | None:
    """Os textos do modelo em inglês (só os traduzidos; prints e scripts vêm do português), se for o caso."""
    en = MODELO_DE_PASTA.with_name(MODELO_DE_PASTA.name + "-en")
    return en if idioma() == "en" and en.is_dir() else None


def _texto_sobre(r: dict) -> str:
    linhas = []
    if r.get("nome"):
        linhas.append(t("- **Nome:** {valor}", valor=r["nome"].strip()))
    if r.get("ocupacao"):
        linhas.append(t("- **O que eu faço:** {valor}", valor=r["ocupacao"].strip()))
    exp = {
        "nenhuma": "Não sei programar. Explique o que você fez e como usar, não como o código funciona por dentro.",
        "pouca": "Sei o básico de computador e um pouco de programação. Explique termos técnicos quando aparecerem.",
        "programo": "Sei programar. Pode usar termos técnicos normalmente.",
    }.get(r.get("experiencia") or "", "")
    if exp:
        linhas.append(t("- **Experiência com programação:** {valor}", valor=t(exp)))
    if r.get("linguagens"):
        linhas.append(t("- **Linguagens e programas que uso:** {valor}", valor=r["linguagens"].strip()))
    if r.get("sistema"):
        linhas.append(t("- **Meu computador:** {valor}", valor=r["sistema"].strip()))
    if r.get("preferencias"):
        linhas.append(t("- **Como prefiro as respostas:** {valor}", valor=r["preferencias"].strip()))
    return "\n".join(linhas) if linhas else t("- (preencha aqui quem você é e como prefere as respostas)")


def criar(destino: str, nome: str, respostas: dict | None = None, iniciar_git: bool = True) -> dict:
    modelo = MODELO_DE_PASTA
    if not modelo.is_dir():
        raise ValueError(t("O modelo de pasta não veio junto com esta cópia do Clave."))
    base = Path(destino).expanduser()
    if not base.is_dir():
        raise ValueError(t("A pasta escolhida para criar o modelo não existe."))
    nome = (nome or "").strip()
    if not nome or re.search(r'[<>:"/\\|?*]', nome) or nome in (".", ".."):
        raise ValueError(t("Nome de pasta inválido."))
    alvo = base / nome
    if alvo.exists():
        raise ValueError(t("Já existe uma pasta com esse nome aí."))
    shutil.copytree(modelo, alvo, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    en = _modelo_en()
    if en:
        shutil.copytree(en, alvo, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if (alvo / "READ-ME-FIRST.md").is_file():
            (alvo / "LEIA-PRIMEIRO.md").unlink(missing_ok=True)
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
