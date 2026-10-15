"""/compact: resume a conversa na hora, pela compactação sob demanda da API (beta compact-2026-09-04).

A API devolve um bloco `compaction` assinado. Ele vira uma mensagem do Claude (tipo "compactacao") no fim do
ramo, e dali em diante o histórico enviado começa nele: o que veio antes sai do pedido (execucao._para_api).
Esse bloco não convive com a compactação automática por limite no mesmo pedido (pedido.montar a desliga).
"""
from __future__ import annotations

import os

import banco
import config
import execucao
import orcamento
import pedido
from i18n import t

BETA = "compact-2026-09-04"


def _instrucoes() -> str:
    return t("Resuma esta conversa para ela continuar a partir do resumo. Guarde: o que a pessoa pediu e como gosta das coisas, as decisões tomadas, os arquivos e pastas mexidos (com o caminho), números e nomes que importam, o que foi feito, o que deu errado e o que ficou pendente, e o último pedido em aberto. Escreva no idioma da conversa. Não chame ferramentas: responda só com o resumo.")


def compactar(conversa_id: str) -> dict:
    conv = banco.conversa(conversa_id)
    if not conv:
        raise ValueError(t("Conversa não encontrada."))
    if execucao.ativa(conversa_id):
        raise ValueError(t("Espere a resposta terminar para compactar."))
    ok, motivo = orcamento.pode_gastar()
    if not ok:
        raise ValueError(motivo)
    caminho = banco.caminho(conversa_id)
    mensagens = pedido.sem_pensamento(execucao._para_api(conv, caminho))
    if sum(1 for m in mensagens if m["role"] == "user") < 2:
        raise ValueError(t("A conversa ainda é curta demais para compactar."))
    cfg = config.carregar()
    modo = conv["modo"] if conv["modo"] in ("chat", "code") else "chat"
    modelo = ((conv.get("ajustes") or {}).get("modelo")
              or cfg.get("modelo_code" if modo == "code" else "modelo_chat"))
    if os.environ.get("CLAVE_FORCAR_MODELO"):  # só para testes
        modelo = os.environ["CLAVE_FORCAR_MODELO"]
    kw = {"model": modelo, "max_tokens": 8192, "messages": mensagens, "betas": [BETA],
          "compaction": {"type": "summarize", "instructions": _instrucoes()}}
    if conv.get("sistema"):
        kw["system"] = conv["sistema"]
    resposta = execucao.cliente().beta.messages.create(**kw)
    uso = resposta.usage.model_dump(exclude_none=True) if resposta.usage else {}
    c = execucao._custo(modelo, uso)
    if resposta.stop_reason != "compaction" or not resposta.content:
        banco.registrar_uso(conversa_id, None, modelo, "compactacao", c)
        raise ValueError(t("O resumo não veio ({motivo}). A conversa ficou como estava.",
                           motivo=resposta.stop_reason or "?"))
    # o bloco volta exatamente como veio (com a assinatura); model_dump() puro acrescentaria campos nulos
    blocos = [b.model_dump(exclude_none=True) for b in resposta.content]
    msg = banco.adicionar_mensagem(conversa_id, caminho[-1]["id"] if caminho else None, "assistant", blocos,
                                   tipo="compactacao", modelo=modelo, uso=uso, custo_usd=c["usd"])
    banco.registrar_uso(conversa_id, msg["id"], modelo, "compactacao", c)
    return {"mensagem_id": msg["id"], "resumo": blocos[0].get("content", ""), "custo_usd": c["usd"]}


def comeca_com_resumo(mensagens: list[dict]) -> bool:
    """O histórico começa num bloco de compactação sob demanda (o /compact)."""
    if not mensagens or mensagens[0].get("role") != "assistant":
        return False
    c = mensagens[0].get("content")
    return isinstance(c, list) and bool(c) and isinstance(c[0], dict) and c[0].get("type") == "compaction"
