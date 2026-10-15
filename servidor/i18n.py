"""Tradução dos textos do servidor (avisos, erros, prompts e descrições das ferramentas).

O texto em português fica no código, dentro de t("..."), e é a chave. O inglês mora nos catálogos
servidor/i18n/en/*.json ({"texto em português": "English text"}), um arquivo por módulo para ninguém pisar no
arquivo do outro. Variáveis vão entre chaves: t("Gastou {valor}.", valor="US$ 1") → "Spent US$ 1.".
Texto sem tradução cai no português (o teste test_i18n acusa quando falta).
"""
from __future__ import annotations

import copy
import json
import re
import threading
from pathlib import Path

import config

PASTA = Path(__file__).resolve().parent / "i18n"
_trava = threading.Lock()
_catalogos: dict[str, dict] = {}
_VAR = re.compile(r"\{(\w+)\}")


def idioma() -> str:
    return "en" if config.carregar().get("idioma") == "en" else "pt-BR"


def catalogo(lingua: str = "en") -> dict:
    with _trava:
        if lingua not in _catalogos:
            junto: dict[str, str] = {}
            for arq in sorted((PASTA / lingua).glob("*.json")):
                try:
                    junto.update(json.loads(arq.read_text(encoding="utf-8")))
                except (OSError, ValueError):
                    pass
            _catalogos[lingua] = junto
        return _catalogos[lingua]


def recarregar() -> None:
    with _trava:
        _catalogos.clear()


def _preencher(s: str, vars: dict) -> str:
    return _VAR.sub(lambda m: str(vars[m.group(1)]) if m.group(1) in vars else m.group(0), s) if vars else s


def t(texto: str, lingua: str | None = None, **vars) -> str:
    lingua = lingua or idioma()
    s = catalogo(lingua).get(texto, texto) if lingua != "pt-BR" else texto
    return _preencher(s, vars)


_guardados: dict[str, tuple[float, dict]] = {}


def guardado_pt(raiz) -> dict:
    """O português guardado de um pacote que vem em inglês (<raiz>/i18n/pt-BR.json): os plugins e os agentes do
    app trazem as instruções em inglês e, ao lado, o nome e a descrição em português que a tela mostra.
    Vazio para quem usa em inglês ou quando o pacote não tem o arquivo."""
    if idioma() != "pt-BR":
        return {}
    arq = Path(raiz) / "i18n" / "pt-BR.json"
    try:
        quando = arq.stat().st_mtime
    except OSError:
        return {}
    chave = str(arq)
    if chave not in _guardados or _guardados[chave][0] != quando:
        try:
            _guardados[chave] = (quando, json.loads(arq.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            _guardados[chave] = (quando, {})
    return _guardados[chave][1]


def traduzir_ferramentas(defs: list[dict], lingua: str | None = None) -> list[dict]:
    """As descrições das ferramentas (e das propriedades delas) no idioma de quem usa."""
    lingua = lingua or idioma()
    if lingua == "pt-BR":
        return defs
    cat = catalogo(lingua)

    def passar(no):
        if isinstance(no, dict):
            return {k: (cat.get(v, v) if k == "description" and isinstance(v, str) else passar(v)) for k, v in no.items()}
        if isinstance(no, list):
            return [passar(x) for x in no]
        return no
    return [passar(copy.deepcopy(d)) for d in defs]
