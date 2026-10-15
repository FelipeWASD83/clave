"""Preços e planos: a página "Preços e planos" e a projeção do gasto.

Os preços por token vêm de `modelos.MODELOS` (página oficial da Anthropic, 14/10/2026). Os planos de assinatura
foram conferidos em claude.com/pricing na mesma data: Pro US$ 20 por mês (US$ 17 no anual) e Max "a partir de
US$ 100", com 5x ou 20x o uso do Pro e US$ 100 ou 200 de crédito de API por mês. O preço do Max 20x (US$ 200)
só aparece em guias de terceiros; por isso os preços são editáveis na tela.

A Anthropic não publica o limite das assinaturas em tokens. O único número que ela dá é um piso: no Pro, pelo
menos 45 mensagens curtas a cada janela de 5 horas (central de ajuda). As estimativas partem dele e dizem isso.
"""
from __future__ import annotations

import math
import time
from datetime import date, datetime, timedelta

import banco
import modelos
import orcamento

PLANOS = [
    {"id": "pro", "nome": "Pro", "preco": 20.0, "preco_anual": 17.0, "multiplicador": 1, "credito_api": 0,
     "fonte": "claude.com/pricing, 14/10/2026"},
    {"id": "max5", "nome": "Max 5x", "preco": 100.0, "multiplicador": 5, "credito_api": 100,
     "fonte": "claude.com/pricing, 14/10/2026 (\"a partir de US$ 100\")"},
    {"id": "max20", "nome": "Max 20x", "preco": 200.0, "multiplicador": 20, "credito_api": 200,
     "fonte": "guias de terceiros; a página oficial só diz \"a partir de US$ 100\""},
]

MENSAGENS_POR_JANELA_PRO = 45  # piso divulgado pela Anthropic: mensagens curtas por janela de 5 h no Pro
SEMANAS_POR_MES = 52 / 12
DIAS_POR_MES = 365 / 12

# Uma mensagem típica, em tokens: o que entra novo, o que vem do cache (instruções e histórico), o que é escrito
# no cache, a resposta e o raciocínio. Suposições do Clave, ditas na tela.
PERFIS = {
    "curta": {"nome": "Conversas curtas", "descricao": "perguntas rápidas, poucas trocas",
              "entrada": 400, "cache_lido": 3_000, "cache_escrito": 500, "saida": 400, "raciocinio": 300},
    "media": {"nome": "Conversas médias", "descricao": "várias trocas, textos de uma página",
              "entrada": 800, "cache_lido": 15_000, "cache_escrito": 1_000, "saida": 800, "raciocinio": 900},
    "longa": {"nome": "Conversas longas", "descricao": "documentos anexados, código, conversas compridas",
              "entrada": 2_000, "cache_lido": 60_000, "cache_escrito": 3_000, "saida": 1_200, "raciocinio": 1_800},
}


def plano(pid: str) -> dict:
    return next((p for p in PLANOS if p["id"] == pid), PLANOS[0])


def custo_mensagem(modelo: str, perfil: str = "curta", raciocinio: bool = True) -> float:
    """Quanto custa uma mensagem típica do perfil nesse modelo, em US$."""
    i = modelos.info(modelo)
    p = PERFIS.get(perfil, PERFIS["curta"])
    total_prompt = p["entrada"] + p["cache_lido"] + p["cache_escrito"]
    mult = 1.0
    longo = i.get("longo")
    if longo and total_prompt > longo["acima_de"]:
        mult = longo["multiplicador"]
    saida = p["saida"] + (p["raciocinio"] if raciocinio or i.get("pensamento") == "sempre" else 0)
    usd = (p["entrada"] * i["entrada"] + p["cache_lido"] * i["cache_leitura"]
           + p["cache_escrito"] * i["entrada"] * 1.25 + saida * i["saida"]) * mult / 1_000_000
    return round(usd, 6)


def tabela_modelos() -> list[dict]:
    """Todos os modelos à venda, com o preço por milhão de tokens e o custo de uma mensagem de cada perfil."""
    saida = []
    for m in modelos.lista_publica(antigos=True):
        i = modelos.info(m["id"])
        saida.append({
            "id": m["id"], "nome": m["nome"], "atual": m["atual"], "resumo": m.get("resumo", ""),
            "entrada": i["entrada"], "cache_escrita": round(i["entrada"] * 1.25, 4),
            "cache_escrita_1h": round(i["entrada"] * 2, 4), "cache_leitura": i["cache_leitura"], "saida": i["saida"],
            "longo": i.get("longo"),
            "por_mensagem": {p: custo_mensagem(m["id"], p) for p in PERFIS},
        })
    saida.sort(key=lambda m: (not m["atual"], modelos.info(m["id"]).get("ordem", 50), -m["saida"]))
    return saida


def medias_reais(dias: int = 60) -> dict[str, dict]:
    """O custo médio de verdade de uma resposta no chat do Clave, por modelo (só com 10 respostas ou mais)."""
    desde = time.time() - dias * 86400
    return {mid: {"usd": round(r["usd"], 6), "respostas": r["pedidos"]}
            for mid, r in banco.media_por_resposta(desde).items() if r["pedidos"] >= 10 and r["usd"]}


def estimar(d: dict) -> dict:
    """Quanto o uso que a pessoa faz da assinatura custaria na API.

    d: plano, janelas (janelas de 5 h por semana em que usa o Claude), porcentagem (quanto do limite de cada
    janela ela gasta), perfil, raciocinio, e opcionalmente mensagens_dia (substitui a conta pelas janelas) e
    preco (o preço do plano que ela paga, se for diferente do da tabela)."""
    p = dict(plano(str(d.get("plano") or "pro")))
    if d.get("preco") not in (None, ""):
        p["preco"] = max(0.0, float(d["preco"]))
    perfil = d.get("perfil") if d.get("perfil") in PERFIS else "curta"
    raciocinio = bool(d.get("raciocinio", True))
    if d.get("mensagens_dia") not in (None, ""):
        por_dia = max(0.0, float(d["mensagens_dia"]))
        mensagens_mes = por_dia * DIAS_POR_MES
        base = "mensagens por dia"
    else:
        janelas = min(42.0, max(0.0, float(d.get("janelas") or 0)))
        pct = min(100.0, max(0.0, float(d.get("porcentagem") or 0)))
        por_semana = janelas * pct / 100 * MENSAGENS_POR_JANELA_PRO * p["multiplicador"]
        mensagens_mes = por_semana * SEMANAS_POR_MES
        base = "janelas de 5 h"
    reais = medias_reais()
    linhas = []
    for m in modelos.lista_publica():
        estimado = mensagens_mes * custo_mensagem(m["id"], perfil, raciocinio)
        real = reais.get(m["id"])
        linhas.append({
            "id": m["id"], "nome": m["nome"],
            "custo_mes": round(estimado, 2),
            "custo_mes_real": round(mensagens_mes * real["usd"], 2) if real else None,
            "respostas_reais": real["respostas"] if real else 0,
            "mais_barato": estimado < p["preco"],
        })
    return {"plano": p, "perfil": perfil, "base": base, "mensagens_mes": round(mensagens_mes),
            "mensagens_semana": round(mensagens_mes / SEMANAS_POR_MES), "modelos": linhas}


def projecao(agora: float | None = None, janela_dias: int = 14) -> dict:
    """O gasto do ciclo no ritmo dos últimos dias e em que dia o teto do mês acaba."""
    agora = agora or time.time()
    s = orcamento.situacao()
    ini, fim = orcamento.ciclo()
    primeiro = banco.totais_uso().get("primeiro")
    desde = agora - janela_dias * 86400
    if primeiro:
        desde = max(desde, float(primeiro))
    dias_base = max(1.0, (agora - desde) / 86400)
    gasto_janela = banco.gasto_entre(desde, agora) if primeiro else 0.0
    ritmo = gasto_janela / dias_base
    dias_restantes = max(0.0, (fim.timestamp() - agora) / 86400)
    previsto = s["gasto"] + ritmo * dias_restantes
    r = {"ritmo_dia": round(ritmo, 4), "dias_base": round(dias_base, 1), "previsto_ciclo": round(previsto, 2),
         "previsto_mes": round(ritmo * DIAS_POR_MES, 2), "gasto": s["gasto"], "teto": s["teto"],
         "fim_ciclo": s["fim"], "pouco_dado": dias_base < 3 or not primeiro, "acaba": None}
    teto = s["teto"]
    if teto:
        if s["gasto"] >= teto:
            r["acaba"] = {"situacao": "ja", "data": date.fromtimestamp(agora).isoformat()}
        elif ritmo > 0:
            dias = (teto - s["gasto"]) / ritmo
            quando = datetime.fromtimestamp(agora) + timedelta(days=dias)
            r["acaba"] = {"situacao": "neste_ciclo" if quando <= fim else "depois",
                          "data": quando.date().isoformat(), "dias": math.ceil(dias)}
        else:
            r["acaba"] = {"situacao": "sem_ritmo"}
    return r
