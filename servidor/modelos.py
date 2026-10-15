"""Catálogo dos modelos: nome, preço e o que cada um aceita.

Preços em US$ por milhão de tokens, conferidos na página oficial em 14/10/2026.
Escrita de cache: 1,25x a entrada (5 min) ou 2x (1 h). Modelo que não está aqui
é cobrado pelo preço mais alto conhecido e a conta é marcada como estimada.
"""
from __future__ import annotations

from i18n import t

ESFORCOS = ["low", "medium", "high", "xhigh", "max"]
NOMES_ESFORCO = {"low": "Baixo", "medium": "Médio", "high": "Alto", "xhigh": "Muito alto", "max": "Máximo"}  # mostrar com t()

# pensamento: "sempre" (não desliga), "disabled" (desliga com type disabled, esforço até high),
# "between_tools" (o jeito do Sonnet 5.5 de desligar), "adaptativo_opcional" (sem thinking = desligado),
# "nenhum" (modelo sem pensamento adaptativo; não manda nada)
MODELOS: dict[str, dict] = {
    "claude-opus-5-5": {
        "nome": "Opus 5.5", "atual": True, "ordem": 1,
        "resumo": "O mais inteligente para o dia a dia. Bom para tudo, inclusive código.",
        "entrada": 4.0, "saida": 20.0, "cache_leitura": 0.20,
        "pensamento": "sempre", "esforco_padrao": "medium", "esforco": True,
        "fallback": True, "rapido": True, "web_novo": True, "updates": True,
    },
    "claude-sonnet-5-5": {
        "nome": "Sonnet 5.5", "atual": True, "ordem": 2,
        "resumo": "Quase tão bom quanto o Opus, pela metade do preço. Rápido.",
        "entrada": 2.0, "saida": 10.0, "cache_leitura": 0.10,  # 0,05x da entrada (página oficial de preços, conferida em 15/10/2026)
        "pensamento": "between_tools", "esforco_padrao": "high", "esforco": True,
        "fallback": True, "rapido": False, "web_novo": True, "updates": True,
    },
    "claude-haiku-5-5": {
        "nome": "Haiku 5.5", "atual": True, "ordem": 3,
        "resumo": "O mais rápido e muito barato. Ótimo para tarefas simples e para aprender.",
        "entrada": 0.10, "saida": 0.50, "cache_leitura": 0.01,
        "longo": {"acima_de": 100_000, "multiplicador": 5},
        "pensamento": "disabled", "esforco_padrao": "medium", "esforco": True,
        "fallback": False, "rapido": False, "web_novo": False, "updates": True,
    },
    "claude-fable-5-1": {
        "nome": "Fable 5.1", "atual": True, "ordem": 4,
        "resumo": "Para raciocínio muito longo e escrita criativa. O mais caro.",
        "entrada": 10.0, "saida": 50.0, "cache_leitura": 0.25,
        "pensamento": "sempre", "esforco_padrao": "high", "esforco": True,
        "fallback": True, "rapido": False, "web_novo": True, "updates": True,
    },
    # anteriores, ainda à venda (aparecem com "mostrar modelos antigos")
    "claude-opus-5": {"nome": "Opus 5", "entrada": 5.0, "saida": 25.0, "cache_leitura": 0.50,
                      "pensamento": "sempre", "esforco_padrao": "high", "esforco": True, "rapido": True,
                      "web_novo": True},
    "claude-sonnet-5": {"nome": "Sonnet 5", "entrada": 2.0, "saida": 10.0, "cache_leitura": 0.20,
                        "pensamento": "disabled", "esforco_padrao": "high", "esforco": True, "web_novo": True},
    "claude-fable-5": {"nome": "Fable 5", "entrada": 10.0, "saida": 50.0, "cache_leitura": 1.0,
                       "pensamento": "sempre", "esforco_padrao": "high", "esforco": True, "web_novo": True},
    "claude-opus-4-8": {"nome": "Opus 4.8", "entrada": 5.0, "saida": 25.0, "cache_leitura": 0.50,
                        "pensamento": "adaptativo_opcional", "esforco_padrao": "high", "esforco": True,
                        "rapido": True, "web_novo": True},
    "claude-opus-4-7": {"nome": "Opus 4.7", "entrada": 5.0, "saida": 25.0, "cache_leitura": 0.50,
                        "pensamento": "adaptativo_opcional", "esforco_padrao": "high", "esforco": True,
                        "web_novo": True},
    "claude-opus-4-6": {"nome": "Opus 4.6", "entrada": 5.0, "saida": 25.0, "cache_leitura": 0.50,
                        "pensamento": "adaptativo_opcional", "esforco_padrao": "high", "esforco": True,
                        "web_novo": True},
    "claude-sonnet-4-6": {"nome": "Sonnet 4.6", "entrada": 3.0, "saida": 15.0, "cache_leitura": 0.30,
                          "pensamento": "adaptativo_opcional", "esforco_padrao": "high", "esforco": True,
                          "web_novo": True},
    "claude-opus-4-5-20251101": {"nome": "Opus 4.5", "entrada": 5.0, "saida": 25.0, "cache_leitura": 0.50,
                                 "pensamento": "nenhum", "esforco": False},
    "claude-sonnet-4-5-20250929": {"nome": "Sonnet 4.5", "entrada": 3.0, "saida": 15.0, "cache_leitura": 0.30,
                                   "pensamento": "nenhum", "esforco": False},
    "claude-haiku-4-5-20251001": {"nome": "Haiku 4.5", "entrada": 1.0, "saida": 5.0, "cache_leitura": 0.10,
                                  "pensamento": "nenhum", "esforco": False},
}

_DESCONHECIDO = {
    "nome": "", "entrada": 10.0, "saida": 50.0, "cache_leitura": 1.0,
    "pensamento": "nenhum", "esforco": False, "desconhecido": True,
}

BUSCA_WEB_USD = 10.0 / 1000  # por busca


def info(modelo: str) -> dict:
    base = MODELOS.get(modelo)
    if base is None:
        d = dict(_DESCONHECIDO)
        d["nome"] = modelo
        return d
    d = {"atual": False, "fallback": False, "rapido": False, "web_novo": False, "updates": False}
    d.update(base)
    return d


def pode_desligar_pensamento(modelo: str) -> bool:
    return info(modelo)["pensamento"] in ("disabled", "between_tools", "adaptativo_opcional")


def esforco_valido(modelo: str, esforco: str, pensar: bool) -> str | None:
    """Devolve o esforço que pode ser mandado (ou None se o modelo não aceita esforço)."""
    i = info(modelo)
    if not i.get("esforco"):
        return None
    esf = esforco if esforco in ESFORCOS else i.get("esforco_padrao", "medium")
    if not pensar and i["pensamento"] in ("disabled", "between_tools"):
        # com o pensamento desligado esses modelos só aceitam até "high"
        if ESFORCOS.index(esf) > ESFORCOS.index("high"):
            esf = "high"
    return esf


def lista_publica(antigos: bool = False, disponiveis: list[str] | None = None) -> list[dict]:
    """Modelos para mostrar na interface."""
    saida = []
    ids = list(MODELOS)
    for extra in disponiveis or []:
        if extra not in ids:
            ids.append(extra)
    for mid in ids:
        i = info(mid)
        if not i.get("atual") and not antigos:
            continue
        if disponiveis is not None and mid not in disponiveis and not i.get("atual"):
            continue
        saida.append({
            "id": mid,
            "nome": i["nome"],
            "resumo": t(i["resumo"]) if i.get("resumo") else "",
            "atual": bool(i.get("atual")),
            "ordem": i.get("ordem", 50),
            "entrada": i["entrada"],
            "saida": i["saida"],
            "cache_leitura": i["cache_leitura"],
            "desliga_pensamento": pode_desligar_pensamento(mid),
            "pensamento_sempre": i["pensamento"] == "sempre",
            "esforco": bool(i.get("esforco")),
            "esforco_padrao": i.get("esforco_padrao"),
            "rapido": bool(i.get("rapido")),
            "desconhecido": bool(i.get("desconhecido")),
        })
    saida.sort(key=lambda m: (m["ordem"], m["nome"]))
    return saida
