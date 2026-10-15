"""Ferramentas que moram em módulos próprios (os widgets e o navegador, por exemplo), fora do execucao.py.

Cada módulo listado em MODULOS expõe:
- NOMES: set com os nomes das ferramentas que ele executa;
- oferecer(ex, *, modo, op, cfg, etapa, pasta) -> list[dict]: as definições (em português; o execucao.py traduz) que
  valem nesta resposta. Devolve [] quando não se aplica (rotina, etapa de fluxo, modo errado, recurso desligado);
- executar(ex, tid, nome, entrada, cfg, modo) -> dict: roda uma chamada e devolve ex.resultado(tid, conteudo, erro).
  Ele mesmo emite os eventos "ferramenta_rodando"/"ferramenta_fim" e, se precisar de OK, usa ex._pedir_aprovacao,
  ex._aplicar_escopo, ex._rotina_parou, ex._log e ex._recusado como as outras ferramentas fazem;
- opcional: definicoes_para_teste() -> list[dict], todas as definições, para o teste de tradução conferir.
"""
from __future__ import annotations

import importlib

MODULOS = ("widgets", "navegador")
_carregados: list | None = None


def todos() -> list:
    global _carregados
    if _carregados is None:
        mods = []
        for nome in MODULOS:
            try:
                mods.append(importlib.import_module(nome))
            except ModuleNotFoundError as e:
                if e.name != nome:  # o módulo existe e quebrou por dentro: isso tem que aparecer
                    raise
        _carregados = mods
    return _carregados


def dono(nome_ferramenta: str):
    return next((m for m in todos() if nome_ferramenta in getattr(m, "NOMES", ())), None)
