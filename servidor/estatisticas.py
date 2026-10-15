"""O painel de uso do início: tokens, dias seguidos, mapa de calor, modelo favorito e os últimos 7 dias."""
from __future__ import annotations

import time
from datetime import date, timedelta

import banco
import modelos
import precos

SEMANAS_DO_MAPA = 20


def sequencias(dias: list[str], hoje: date) -> tuple[int, int]:
    """(dias seguidos até hoje, maior sequência de todas). Hoje ainda sem uso não quebra a sequência de ontem."""
    usados = {date.fromisoformat(d) for d in dias}
    recorde, corrida, anterior = 0, 0, None
    for d in sorted(usados):
        corrida = corrida + 1 if anterior and d - anterior == timedelta(days=1) else 1
        recorde = max(recorde, corrida)
        anterior = d
    atual = 0
    d = hoje if hoje in usados else hoje - timedelta(days=1)
    while d in usados:
        atual += 1
        d -= timedelta(days=1)
    return atual, recorde


def _nome(mid: str) -> str:
    return modelos.info(mid).get("nome") or mid


def painel(hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    agora = time.time()
    totais = banco.totais_uso()
    dias = banco.dias_com_uso()
    seguidos, recorde = sequencias(dias, hoje)

    # mapa de calor: semanas inteiras (segunda a domingo) terminando na semana de hoje
    inicio_mapa = hoje - timedelta(days=hoje.weekday()) - timedelta(weeks=SEMANAS_DO_MAPA - 1)
    desde_mapa = time.mktime(inicio_mapa.timetuple())
    por_dia = {r["dia"]: r for r in banco.uso_por_dia(desde_mapa)}
    mapa = []
    d = inicio_mapa
    while d <= hoje:
        r = por_dia.get(d.isoformat())
        mapa.append({"dia": d.isoformat(), "tokens": int(r["tokens"] or 0) if r else 0,
                     "usd": round(r["usd"] or 0, 4) if r else 0, "pedidos": r["pedidos"] if r else 0})
        d += timedelta(days=1)

    # últimos 7 dias por modelo, e o favorito dos últimos 30
    sete = [(hoje - timedelta(days=6 - i)).isoformat() for i in range(7)]
    desde_7 = time.mktime((hoje - timedelta(days=6)).timetuple())
    por_modelo: dict[str, dict] = {}
    for r in banco.uso_por_modelo_e_dia(desde_7):
        m = por_modelo.setdefault(r["modelo"], {"modelo": r["modelo"], "nome": _nome(r["modelo"]),
                                                "tokens": [0] * 7, "usd": 0.0, "pedidos": 0})
        if r["dia"] in sete:
            m["tokens"][sete.index(r["dia"])] += int(r["tokens"] or 0)
        m["usd"] = round(m["usd"] + (r["usd"] or 0), 4)
        m["pedidos"] += r["pedidos"]
    ultimos7 = sorted(por_modelo.values(), key=lambda m: -sum(m["tokens"]))

    contagem: dict[str, int] = {}
    for r in banco.uso_por_modelo_e_dia(agora - 30 * 86400):
        contagem[r["modelo"]] = contagem.get(r["modelo"], 0) + r["pedidos"]
    favorito = None
    if contagem:
        mid = max(contagem, key=contagem.get)
        favorito = {"modelo": mid, "nome": _nome(mid), "pedidos": contagem[mid],
                    "porcentagem": round(contagem[mid] / sum(contagem.values()) * 100)}

    return {
        "tokens_total": int(totais["tokens"] or 0),
        "saida_total": int(totais["saida"] or 0),
        "gasto_total": round(totais["usd"] or 0, 4),
        "pedidos_total": totais["pedidos"] or 0,
        "dias_usados": len(dias),
        "dias_seguidos": seguidos,
        "recorde": recorde,
        "mapa": mapa,
        "dias7": sete,
        "ultimos7": ultimos7,
        "favorito": favorito,
        "projecao": precos.projecao(agora),
    }
