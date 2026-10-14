"""Quanto custou cada resposta, a partir do campo `usage` da API."""
from __future__ import annotations

import modelos

M = 1_000_000


def _tokens_cache_escrita(uso: dict) -> tuple[int, int]:
    """(5 min, 1 h). Sem o detalhamento, conta tudo como 5 min."""
    det = uso.get("cache_creation") or {}
    cinco = det.get("ephemeral_5m_input_tokens")
    uma = det.get("ephemeral_1h_input_tokens")
    if cinco is None and uma is None:
        return int(uso.get("cache_creation_input_tokens") or 0), 0
    return int(cinco or 0), int(uma or 0)


def _custo_parcela(modelo: str, uso: dict, rapido: bool) -> tuple[float, dict]:
    i = modelos.info(modelo)
    entrada = int(uso.get("input_tokens") or 0)
    leitura = int(uso.get("cache_read_input_tokens") or 0)
    esc5, esc1h = _tokens_cache_escrita(uso)
    saida = int(uso.get("output_tokens") or 0)

    mult = 1.0
    longo = i.get("longo")
    if longo and (entrada + leitura + esc5 + esc1h) > longo["acima_de"]:
        mult = float(longo["multiplicador"])
    if rapido:
        mult *= 2.0

    p_in = i["entrada"] * mult
    usd = (
        entrada * p_in
        + esc5 * p_in * 1.25
        + esc1h * p_in * 2.0
        + leitura * i["cache_leitura"] * mult
        + saida * i["saida"] * mult
    ) / M
    return usd, {
        "entrada": entrada, "cache_leitura": leitura, "cache_escrita": esc5 + esc1h,
        "saida": saida, "multiplicador": mult,
    }


def custo_uso(modelo: str, uso: dict | None) -> dict:
    """Recebe o `usage` (dict) de uma resposta e devolve o custo em dólar."""
    uso = uso or {}
    rapido = uso.get("speed") == "fast"
    iteracoes = uso.get("iterations") or []
    total = 0.0
    soma = {"entrada": 0, "cache_leitura": 0, "cache_escrita": 0, "saida": 0}
    if iteracoes:
        for it in iteracoes:
            usd, det = _custo_parcela(it.get("model") or modelo, it, rapido)
            total += usd
            for k in soma:
                soma[k] += det[k]
    else:
        usd, det = _custo_parcela(modelo, uso, rapido)
        total += usd
        for k in soma:
            soma[k] += det[k]

    buscas = int(((uso.get("server_tool_use") or {}).get("web_search_requests")) or 0)
    total += buscas * modelos.BUSCA_WEB_USD
    soma["buscas"] = buscas
    return {
        "usd": round(total, 8),
        "estimado": bool(modelos.info(modelo).get("desconhecido")),
        **soma,
    }


def contexto_usado(uso: dict | None) -> int:
    """Tamanho do pedido (o que ocupou a janela de contexto) na última chamada."""
    uso = uso or {}
    iteracoes = uso.get("iterations") or []
    ref = iteracoes[-1] if iteracoes else uso
    esc5, esc1h = _tokens_cache_escrita(ref)
    return int(ref.get("input_tokens") or 0) + int(ref.get("cache_read_input_tokens") or 0) + esc5 + esc1h


def formatar_usd(v: float) -> str:
    if v < 0.01:
        return f"US$ {v:.4f}".replace(".", ",")
    return f"US$ {v:.2f}".replace(".", ",")
