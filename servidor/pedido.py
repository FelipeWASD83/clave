"""Monta os parâmetros do pedido à API para cada modelo.

Recursos opcionais (troca de modelo se recusar, compactação, cache automático,
notas de progresso etc.) entram quando o modelo aceita. Se a API recusar um
deles com erro 400, `desligar_por_erro` descobre qual foi, desliga só ele para
aquele modelo (fica salvo em dados/compat.json) e o pedido é refeito sem ele.
"""
from __future__ import annotations

import json
import threading

import modelos
from config import DADOS
from ferramentas import memoria

OPCIONAIS = ("fallbacks", "updates", "block_binding", "compactacao", "cache", "eager", "web_novo", "rapido")
_trava = threading.Lock()


def _arq():
    return DADOS / "compat.json"


def desligados(modelo: str) -> set:
    try:
        return set(json.loads(_arq().read_text(encoding="utf-8")).get(modelo, []))
    except (OSError, ValueError):
        return set()


def _salvar_desligado(modelo: str, recursos: set) -> None:
    with _trava:
        try:
            dados = json.loads(_arq().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            dados = {}
        atual = set(dados.get(modelo, []))
        atual |= recursos
        dados[modelo] = sorted(atual)
        DADOS.mkdir(parents=True, exist_ok=True)
        _arq().write_text(json.dumps(dados, indent=2), encoding="utf-8")


def desligar_por_erro(modelo: str, mensagem: str, usados: set) -> set:
    """Decide quais recursos opcionais desligar depois de um 400. Devolve o que foi desligado."""
    m = mensagem.lower()
    pistas = {
        "fallbacks": ("fallback",),
        "updates": ("display", "updates"),
        "block_binding": ("block_binding", "binding"),
        "compactacao": ("context_management", "compact"),
        "cache": ("cache_control",),
        "eager": ("eager_input_streaming",),
        "web_novo": ("web_search_2026", "web_fetch_2026", "web_search", "web_fetch"),
        "rapido": ("speed", "fast"),
    }
    # só desliga o recurso que a mensagem de erro cita: erro de outra natureza (crédito, conversa grande
    # demais, conector fora do ar) não pode desligar o cache nem o resumo para sempre
    alvo = {r for r, chaves in pistas.items() if r in usados and any(c in m for c in chaves)}
    if alvo:
        _salvar_desligado(modelo, alvo)
    return alvo


def religar_tudo() -> None:
    with _trava:
        try:
            _arq().unlink()
        except OSError:
            pass


def ferramentas_web(modelo: str, desl: set) -> list[dict]:
    if modelos.info(modelo).get("web_novo") and "web_novo" not in desl:
        return [{"type": "web_search_20260209", "name": "web_search"},
                {"type": "web_fetch_20260209", "name": "web_fetch"}]
    return [{"type": "web_search_20250305", "name": "web_search"},
            {"type": "web_fetch_20250910", "name": "web_fetch"}]


def montar(*, modelo: str, esforco: str, pensar: bool, mostrar_raciocinio: bool, modo: str, sistema: str,
           mensagens: list, ferramentas_cliente: list, cfg: dict, busca_web=False, memoria_ligada=False,
           mcp: list | None = None, rapido=False, extra_desligados: set | None = None) -> tuple[dict, set]:
    """Devolve (kwargs para client.beta.messages.stream, recursos opcionais usados)."""
    info = modelos.info(modelo)
    desl = desligados(modelo) | (extra_desligados or set())
    usados: set = set()
    betas: list[str] = []

    kw: dict = {"model": modelo, "messages": mensagens}
    teto_saida = 128_000 if info.get("atual") or info["pensamento"] in ("sempre", "between_tools") else 64_000
    if info.get("desconhecido"):
        teto_saida = 16_000
    kw["max_tokens"] = min(teto_saida, 64_000 if modo == "code" else 32_000)
    if sistema:
        kw["system"] = sistema

    # raciocínio
    p = info["pensamento"]
    quer_pensar = pensar or p == "sempre"
    thinking = None
    if p != "nenhum":
        if quer_pensar:
            thinking = {"type": "adaptive"}
            if mostrar_raciocinio:
                thinking["display"] = "summarized"
            elif modo == "code" and info.get("updates") and "updates" not in desl:
                thinking["display"] = "updates"
                betas.append("thinking-display-updates-2026-08-18")
                usados.add("updates")
            if info.get("atual") and "block_binding" not in desl:
                thinking["block_binding"] = {"prefix_mismatch_behavior": "drop_block"}
                betas.append("thinking-binding-controls-2026-08-01")
                usados.add("block_binding")
        elif p == "disabled":
            thinking = {"type": "disabled"}
        elif p == "between_tools":
            thinking = {"type": "between_tools"}
    if thinking:
        kw["thinking"] = thinking

    esf = modelos.esforco_valido(modelo, esforco, quer_pensar)
    if esf:
        kw["output_config"] = {"effort": esf}

    if cfg.get("cache_automatico", True) and "cache" not in desl:
        kw["cache_control"] = {"type": "ephemeral"}
        usados.add("cache")

    if (cfg.get("compactacao", True) and info.get("atual") and "compactacao" not in desl):
        limite = max(50_000, min(900_000, int(cfg.get("compactar_em") or 150_000)))
        kw["context_management"] = {"edits": [{"type": "compact_20260112",
                                              "trigger": {"type": "input_tokens", "value": limite}}]}
        betas.append("compact-2026-01-12")
        usados.add("compactacao")

    if cfg.get("troca_se_recusar", True) and info.get("fallback") and "fallbacks" not in desl:
        kw["fallbacks"] = "default"
        betas.append("server-side-fallback-2026-07-01")
        usados.add("fallbacks")

    if rapido and info.get("rapido") and "rapido" not in desl:
        kw["speed"] = "fast"
        betas.append("fast-mode-2026-02-01")
        usados.add("rapido")

    tools = []
    for t in ferramentas_cliente:
        t = dict(t)
        if "eager" in desl:
            t.pop("eager_input_streaming", None)
        elif t.get("eager_input_streaming"):
            usados.add("eager")
        tools.append(t)
    if memoria_ligada:
        tools.append(dict(memoria.DEFINICAO))
    if busca_web:
        web = ferramentas_web(modelo, desl)
        if web[0]["type"].endswith("20260209"):
            usados.add("web_novo")
        tools += web
    if mcp:
        servidores = []
        for m in mcp:
            srv = {"type": "url", "url": m["url"], "name": m["nome"]}
            if m.get("token"):
                srv["authorization_token"] = m["token"]
            servidores.append(srv)
            tools.append({"type": "mcp_toolset", "mcp_server_name": m["nome"]})
        kw["mcp_servers"] = servidores
        betas.append("mcp-client-2025-11-20")
    if tools:
        kw["tools"] = tools

    if betas:
        kw["betas"] = list(dict.fromkeys(betas))
    return kw, usados


def sem_pensamento(mensagens: list) -> list:
    """Cópia do histórico sem os blocos de raciocínio (recuperação quando a API recusa um bloco antigo)."""
    saida = []
    for m in mensagens:
        c = m["content"]
        if isinstance(c, list):
            c = [b for b in c if not (isinstance(b, dict) and b.get("type") in ("thinking", "redacted_thinking"))]
            if not c:
                continue
        saida.append({**m, "content": c})
    return saida
