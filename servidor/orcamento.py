"""Teto de gasto mensal: ciclo, quanto já foi, alertas e bloqueio."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import banco
import config
from i18n import t

ALERTAS = (50, 80, 95, 100)


def _data_virada(ano: int, mes: int, dia: int) -> date:
    # dia 29, 30 e 31 viram o último dia do mês quando o mês é curto
    while True:
        try:
            return date(ano, mes, dia)
        except ValueError:
            dia -= 1


def ciclo(hoje: date | None = None, dia_virada: int | None = None) -> tuple[datetime, datetime]:
    hoje = hoje or date.today()
    dia = max(1, min(31, int(dia_virada or config.carregar().get("dia_virada") or 1)))
    esta = _data_virada(hoje.year, hoje.month, dia)
    if hoje >= esta:
        inicio = esta
        ano, mes = (hoje.year + 1, 1) if hoje.month == 12 else (hoje.year, hoje.month + 1)
        fim = _data_virada(ano, mes, dia)
    else:
        fim = esta
        ano, mes = (hoje.year - 1, 12) if hoje.month == 1 else (hoje.year, hoje.month - 1)
        inicio = _data_virada(ano, mes, dia)
    return datetime.combine(inicio, datetime.min.time()), datetime.combine(fim, datetime.min.time())


def chave_ciclo(inicio: datetime) -> str:
    return inicio.strftime("%Y-%m-%d")


def situacao() -> dict:
    cfg = config.carregar()
    inicio, fim = ciclo(dia_virada=cfg.get("dia_virada"))
    chave = chave_ciclo(inicio)
    no_app = banco.gasto_entre(inicio.timestamp(), fim.timestamp())
    ajuste = float((cfg.get("ajustes") or {}).get(chave, 0) or 0)
    gasto = no_app + ajuste
    teto = cfg.get("teto_mensal_usd")
    teto = float(teto) if teto not in (None, "", 0) else None
    pct = (gasto / teto * 100) if teto else 0.0
    return {
        "inicio": inicio.date().isoformat(),
        "fim": (fim - timedelta(days=1)).date().isoformat(),
        "chave": chave,
        "gasto_app": round(no_app, 6),
        "ajuste": ajuste,
        "gasto": round(gasto, 6),
        "teto": teto,
        "restante": round(teto - gasto, 6) if teto else None,
        "porcentagem": round(pct, 2),
        "ao_atingir": cfg.get("ao_atingir", "bloquear"),
        "bloqueado": bool(teto and gasto >= teto and cfg.get("ao_atingir", "bloquear") == "bloquear"),
    }


def pode_gastar() -> tuple[bool, str]:
    s = situacao()
    if s["bloqueado"]:
        return False, t("O teto de gasto deste mês foi atingido (US$ {gasto} de US$ {teto}). Ele volta a zerar em {data}. Dá para aumentar o teto em Configurações > Limite de gasto.",
                        gasto=f"{s['gasto']:.2f}", teto=f"{s['teto']:.2f}", data=_br(s["fim"], mais_um=True))
    return True, ""


def novo_alerta() -> int | None:
    """Devolve o maior alerta (50/80/95/100) cruzado e ainda não mostrado neste ciclo."""
    s = situacao()
    if not s["teto"]:
        return None
    cfg = config.carregar()
    vistos = dict(cfg.get("alertas_vistos") or {})
    ja = int(vistos.get(s["chave"], 0) or 0)
    cruzado = max((a for a in ALERTAS if s["porcentagem"] >= a), default=0)
    if cruzado > ja:
        vistos = {s["chave"]: cruzado}
        config.salvar({"alertas_vistos": vistos})
        return cruzado
    return None


def _br(iso: str, mais_um=False) -> str:
    d = date.fromisoformat(iso)
    if mais_um:
        d += timedelta(days=1)
    return t("{dia}/{mes}/{ano}", dia=f"{d.day:02d}", mes=f"{d.month:02d}", ano=d.year)
