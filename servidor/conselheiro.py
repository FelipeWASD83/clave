"""O conselheiro de modelo: o Haiku olha a conversa e diz qual modelo faz a tarefa pelo menor preço.

Roda na 1ª mensagem de cada conversa (é ali que a tarefa aparece) e depois a cada 5 (6ª, 11ª...), antes da resposta.
Se quem usa deixou (trocar_modelo_sozinho), o Clave troca o modelo da conversa e avisa com um "Voltar"; senão, só
mostra a sugestão. Fica de fora: rotina, etapa de fluxo, os ajudantes das lições, comando ou skill que fixa o
modelo, gerar outra resposta (quem escolhe ali é a pessoa) e conversa em que a pessoa já disse para não trocar mais.
Cada avaliação é uma chamada curta ao Haiku, sem raciocínio, e o custo entra na conversa como "conselheiro".
"""
from __future__ import annotations

import banco
import modelos
from i18n import t

A_CADA = 5
MODELO = "claude-haiku-5-5"
_CORTE = 700  # caracteres de cada mensagem que o conselheiro lê


def _quando_usar() -> dict:
    return {
        "claude-haiku-5-5": t("perguntas e conversas do dia a dia, textos curtos, resumos, traduções, e-mails, explicar algo, tarefas de rotina e arquivos pequenos"),
        "claude-sonnet-5-5": t("textos longos ou caprichados, documentos e planilhas grandes, código de tamanho médio, análises com vários passos, ou quando o Haiku já errou ou se perdeu"),
        "claude-opus-5-5": t("tarefas difíceis e importantes: código grande ou com muitos arquivos, decisões com muito em jogo, raciocínio longo, revisar algo com olho crítico"),
        "claude-fable-5-1": t("só raciocínio muito longo ou escrita criativa longa, quando vale pagar bem mais"),
    }


def candidatos(atual: str = "") -> list[str]:
    """Os modelos atuais e, se a conversa usa um modelo antigo, ele também (para dar para recomendar mantê-lo)."""
    lista = [mid for mid in _quando_usar() if mid in modelos.MODELOS and modelos.MODELOS[mid].get("atual")]
    if atual in modelos.MODELOS and atual not in lista:
        lista.append(atual)
    return lista


def deve_avaliar(n_pedidos: int) -> bool:
    """n_pedidos: quantas mensagens de quem usa a conversa tem, contando a que acabou de chegar."""
    return n_pedidos >= 1 and (n_pedidos - 1) % A_CADA == 0


def contar_pedidos(caminho: list[dict]) -> int:
    return sum(1 for m in caminho if m["papel"] == "user" and m["tipo"] == "normal")


def _texto(m: dict) -> str:
    c = m.get("conteudo")
    if isinstance(c, str):
        return c
    partes, anexos, ferramentas = [], 0, 0
    for b in c or []:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text" and not str(b.get("text", "")).startswith("<modo-do-clave>"):
            partes.append(b.get("text", ""))
        elif b.get("type") in ("clave_anexo", "image", "document"):
            anexos += 1
        elif b.get("type") in ("tool_use", "server_tool_use", "mcp_tool_use"):
            ferramentas += 1
    texto = " ".join(" ".join(partes).split())
    if (m.get("meta") or {}).get("exibir"):
        texto = m["meta"]["exibir"]
    if anexos:
        texto += " " + t("(com {n} anexo(s))", n=anexos)
    if ferramentas:
        texto += " " + t("(usou {n} ferramenta(s))", n=ferramentas)
    return texto


def _pedido(caminho: list[dict], modelo_atual: str, modo: str) -> str:
    normais = [m for m in caminho if m["tipo"] == "normal"][-8:]
    linhas = []
    for m in normais:
        quem = t("Pessoa") if m["papel"] == "user" else "Claude"
        txt = _texto(m)
        if len(txt) > _CORTE:
            txt = txt[:_CORTE] + "…"
        linhas.append(f"[{quem}] {txt}")
    nome = (modelos.MODELOS.get(modelo_atual) or {}).get("nome", modelo_atual)
    return "\n".join([
        t("Modelo atual: {nome} ({id}). Modo: {modo}.", nome=nome, id=modelo_atual,
          modo=t("Code (trabalha numa pasta do computador)") if modo == "code" else t("chat")),
        t("A conversa até agora (as últimas mensagens, cortadas; a última é o pedido novo):"),
        *linhas,
    ])


def _sistema(atual: str) -> str:
    linhas = [t("Você escolhe qual modelo do Claude responde a uma conversa no Clave. Quem usa paga cada token do próprio bolso, então escolha o modelo mais barato que faz a tarefa bem."),
              t("Modelos (preço por milhão de tokens, entrada e saída) e quando usar:")]
    for mid, quando in _quando_usar().items():
        info = modelos.MODELOS.get(mid)
        if info and info.get("atual"):
            linhas.append(f"- {mid} ({info['nome']}, US$ {info['entrada']:g} / {info['saida']:g}): {quando}")
    info = modelos.MODELOS.get(atual)
    if info and not info.get("atual"):  # um modelo antigo escolhido pela pessoa também pode ficar
        linhas.append(f"- {atual} ({info['nome']}, US$ {info['entrada']:g} / {info['saida']:g}): "
                      + t("o modelo antigo que a pessoa escolheu"))
    linhas += [t("Na dúvida entre dois, fique com o mais barato. Só recomende um modelo diferente do atual quando a diferença for clara; senão, recomende o atual."),
               t("Responda chamando recomendar_modelo. O motivo é uma frase curta para quem usa, sem jargão, no idioma em que a pessoa escreve, dizendo o que na tarefa pede esse modelo.")]
    return "\n".join(linhas)


def _ferramenta(atual: str) -> dict:
    return {"name": "recomendar_modelo", "description": t("Diz qual modelo deve responder esta conversa."),
            "input_schema": {"type": "object", "properties": {
                "modelo": {"type": "string", "enum": candidatos(atual), "description": t("O id do modelo")},
                "motivo": {"type": "string", "description": t("Uma frase curta para quem usa")}},
                "required": ["modelo", "motivo"]}}


def avaliar(conversa_id: str, modelo_atual: str, modo: str) -> dict | None:
    """{"modelo", "motivo", "custo_usd"} ou None quando não deu para avaliar (o Clave segue sem conselho)."""
    import execucao

    caminho = banco.caminho(conversa_id)
    if not caminho or modelo_atual not in modelos.MODELOS:
        return None
    # roda antes da resposta: com a API lenta, melhor desistir do conselho do que segurar a conversa
    cli = execucao.cliente().with_options(timeout=20, max_retries=1)
    r = cli.messages.create(
        model=MODELO, max_tokens=300, thinking={"type": "disabled"}, output_config={"effort": "low"},
        system=_sistema(modelo_atual), tools=[_ferramenta(modelo_atual)],
        tool_choice={"type": "tool", "name": "recomendar_modelo"},
        messages=[{"role": "user", "content": _pedido(caminho, modelo_atual, modo)}])
    c = execucao._custo(MODELO, r.usage.model_dump(mode="json", exclude_none=True))
    banco.registrar_uso(conversa_id, None, MODELO, "conselheiro", c)
    uso = next((b for b in r.content if b.type == "tool_use" and b.name == "recomendar_modelo"), None)
    if uso is None:
        return None
    escolha = str((uso.input or {}).get("modelo") or "")
    if escolha not in candidatos(modelo_atual):
        return None
    motivo = " ".join(str((uso.input or {}).get("motivo") or "").split())[:300]
    return {"modelo": escolha, "motivo": motivo, "custo_usd": c["usd"]}
