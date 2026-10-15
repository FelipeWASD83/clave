"""O registro das rotas da API. O servidor.py e os módulos de cada parte (console, arquivos, navegador, widgets,
tarefas...) registram as suas aqui com @rota, e o servidor.py importa esses módulos para elas existirem.

Cada função recebe o manipulador da requisição (h) e os pedaços do caminho: h.corpo() lê o JSON, h.query() a
query string, h._json(dados) responde, h._bytes(dados, tipo, cab=...) responde bytes. Erro(status, mensagem)
vira {"erro": mensagem} com aquele status.
"""
from __future__ import annotations

import re


class Erro(Exception):
    def __init__(self, status: int, mensagem: str):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


ROTAS: list[tuple[str, re.Pattern, callable]] = []


def rota(metodo: str, padrao: str):
    rx = re.compile("^" + re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", padrao) + "$")

    def deco(fn):
        ROTAS.append((metodo, rx, fn))
        return fn
    return deco
