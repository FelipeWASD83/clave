"""O jeito de falar do Claude: tom básico e os controles de Menos, Padrão e Mais (como na personalização do ChatGPT).

Cada escolha diferente de "padrao" vira uma frase no prompt de sistema das conversas novas (sistema._personalizacao).
Tudo em "padrao" não acrescenta nada, então quem nunca mexeu recebe o mesmo prompt de antes.
A configuração guarda só {controle: valor}; valor desconhecido conta como "padrao".

Os estilos (Normal, Conciso, Explicativo, Formal) continuam à parte: eles cuidam do tamanho e da formalidade da
escrita, e por isso o tom básico não tem Profissional nem Eficiente.
"""
from __future__ import annotations

import banco
import config
import orcamento
from i18n import t

MODELO_EXEMPLO = "claude-haiku-5-5"


def _menos_mais(menos: str, mais: str) -> list[tuple]:
    return [("menos", t("Menos"), menos), ("padrao", t("Padrão"), ""), ("mais", t("Mais"), mais)]


def _controles() -> list[dict]:
    """Cada controle: id, nome, ajuda e as opções (valor, rótulo, frase para o prompt; o padrão não tem frase)."""
    menos_mais = _menos_mais
    return [
        {"id": "base", "nome": t("Estilo e tom básicos"),
         "ajuda": t("A personalidade das respostas."),
         "opcoes": [
             ("padrao", t("Padrão"), ""),
             ("amigavel", t("Amigável"), t("Tom amigável: converse como alguém próximo e caloroso, com naturalidade e sem formalidade.")),
             ("sincero", t("Sincero"), t("Tom sincero: seja direto e honesto, diga com clareza quando algo está errado ou é má ideia e não amacie a verdade, sempre com respeito.")),
             ("divertido", t("Divertido"), t("Tom divertido: use humor leve e um jeito descontraído quando couber, sem atrapalhar a resposta e sem piada em assunto sério.")),
             ("nerd", t("Nerd"), t("Tom nerd: mostre curiosidade e gosto pelo assunto, traga detalhes interessantes e o porquê das coisas, com os termos certos (explicando os difíceis).")),
             ("cetico", t("Cético"), t("Tom cético: questione as premissas, aponte furos, riscos e exageros e não aceite afirmação sem motivo; ironia leve é bem-vinda, grosseria não.")),
         ]},
        {"id": "cordialidade", "nome": t("Cordialidade"), "ajuda": t("O quanto ele é caloroso e gentil."),
         "opcoes": menos_mais(
             t("Cordialidade: menos. Seja neutro e objetivo, sem gentilezas, elogios nem frases de cortesia."),
             t("Cordialidade: mais. Seja caloroso e acolhedor, mostre que se importa e reconheça o esforço da pessoa."))},
        {"id": "entusiasmo", "nome": t("Entusiasmo"), "ajuda": t("O quanto ele se empolga."),
         "opcoes": menos_mais(
             t("Entusiasmo: menos. Tom calmo e contido, sem exclamações nem empolgação."),
             t("Entusiasmo: mais. Mostre energia e empolgação de verdade, com exclamações quando couber."))},
        {"id": "emoji", "nome": t("Emoji"), "ajuda": t("Quantos emojis aparecem."),
         "opcoes": [
             ("nenhum", t("Nenhum"), t("Emoji: nenhum. Não use emoji.")),
             ("padrao", t("Padrão"), ""),
             ("mais", t("Mais"), t("Emoji: mais. Use emojis com frequência para dar expressão, mais ou menos um por parágrafo.")),
         ]},
        {"id": "titulos", "nome": t("Títulos e listas"), "ajuda": t("Texto corrido ou tudo em tópicos."),
         "opcoes": menos_mais(
             t("Títulos e listas: menos. Prefira texto corrido em parágrafos; use lista ou título só quando o conteúdo pedir de verdade (passos numerados, por exemplo)."),
             t("Títulos e listas: mais. Organize as respostas com títulos curtos e listas sempre que houver mais de uma ideia, para dar para bater o olho."))},
        {"id": "visual", "nome": t("Negrito e tabelas"), "ajuda": t("Destaques, tabelas e outros elementos visuais."),
         "opcoes": menos_mais(
             t("Elementos visuais: menos. Quase sem negrito, sem tabelas e sem enfeites; texto limpo."),
             t("Elementos visuais: mais. Use negrito nos pontos principais, tabelas para comparar e citações ou blocos de código quando ajudarem."))},
        {"id": "linguagem", "nome": t("Linguagem"), "ajuda": t("Palavras do dia a dia ou termos técnicos."),
         "opcoes": [
             ("simples", t("Simples"), t("Linguagem: simples. Escreva para quem não é da área: palavras do dia a dia, sem jargão, e explique com um exemplo qualquer termo técnico que não der para evitar.")),
             ("padrao", t("Padrão"), ""),
             ("tecnica", t("Técnica"), t("Linguagem: técnica. A pessoa entende do assunto: use os termos técnicos certos sem explicar o básico.")),
         ]},
        {"id": "duvida", "nome": t("Quando faltar informação"), "ajuda": t("Perguntar antes ou seguir com uma suposição."),
         "opcoes": [
             ("perguntar", t("Perguntar antes"), t("Quando faltar informação importante para fazer o pedido, pergunte antes de começar, com poucas perguntas objetivas.")),
             ("padrao", t("Padrão"), ""),
             ("supor", t("Supor e avisar"), t("Quando faltar informação, não pare para perguntar: faça a suposição mais razoável, diga qual foi e siga.")),
         ]},
        {"id": "sugestao", "nome": t("Sugestão no fim"), "ajuda": t("O \"quer que eu...?\" no fim das respostas."),
         "opcoes": [
             ("nunca", t("Nunca"), t("Não termine as respostas oferecendo mais ajuda nem sugerindo próximos passos (\"quer que eu...?\"): termine quando a resposta acabar.")),
             ("padrao", t("Padrão"), ""),
             ("sempre", t("Sempre"), t("No fim de cada resposta, sugira em uma frase um próximo passo útil que você pode fazer.")),
         ]},
    ]


def opcoes() -> list[dict]:
    """Para a tela de Configurações (sem as frases do prompt)."""
    return [{"id": c["id"], "nome": c["nome"], "ajuda": c["ajuda"],
             "opcoes": [{"valor": v, "rotulo": r} for v, r, _ in c["opcoes"]]} for c in _controles()]


def limpar(tom) -> dict:
    """Só controles e valores que existem; o padrão não é guardado."""
    if not isinstance(tom, dict):
        return {}
    validos = {c["id"]: {v for v, _r, _f in c["opcoes"]} for c in _controles()}
    return {k: v for k, v in tom.items() if k in validos and v in validos[k] and v != "padrao"}


def frases(tom: dict | None) -> list[str]:
    tom = tom if isinstance(tom, dict) else {}
    saida = []
    for c in _controles():
        escolhido = tom.get(c["id"])
        for valor, _rotulo, frase in c["opcoes"]:
            if valor == escolhido and frase:
                saida.append(frase)
    return saida


def bloco(tom: dict | None) -> str:
    """O trecho do prompt de sistema; vazio quando está tudo no padrão."""
    linhas = frases(tom)
    if not linhas:
        return ""
    return t("<jeito_de_falar>\n{intro}\n{linhas}\n</jeito_de_falar>",
             intro=" ".join([
                 t("Quem usa escolheu como você conversa. Isto muda o jeito de falar, não a qualidade: continue correto e completo."),
                 t("Se algo aqui contradizer o que a pessoa escreveu em \"Como você quer as respostas\", vale o que ela escreveu."),
             ]),
             linhas="\n".join(f"- {l}" for l in linhas))


def pergunta_exemplo() -> str:
    return t("Me explica rapidinho o que é backup e se eu preciso me preocupar com isso.")


def exemplo(tom: dict | None, pergunta: str = "") -> dict:
    """Uma resposta curta do Haiku com o tom escolhido (e o resto da personalização), para ver antes de usar."""
    import execucao
    import sistema

    ok, motivo = orcamento.pode_gastar()
    if not ok:
        raise ValueError(motivo)
    cfg = config.carregar()
    cfg["tom"] = tom if isinstance(tom, dict) else {}
    pergunta = (pergunta or "").strip()[:500] or pergunta_exemplo()
    partes = [" ".join([t("Você é o Claude, um assistente de IA feito pela Anthropic."),
                        t("Responda no idioma em que a pessoa escrever.")])]
    partes += sistema._personalizacao(cfg)
    r = execucao.cliente().messages.create(
        model=MODELO_EXEMPLO, max_tokens=700, thinking={"type": "disabled"}, output_config={"effort": "low"},
        system="\n\n".join(partes), messages=[{"role": "user", "content": pergunta}])
    texto = "".join(b.text for b in r.content if b.type == "text").strip()
    c = execucao._custo(MODELO_EXEMPLO, r.usage.model_dump(mode="json", exclude_none=True))
    banco.registrar_uso(None, None, MODELO_EXEMPLO, "exemplo_tom", c)
    return {"pergunta": pergunta, "resposta": texto, "custo_usd": c["usd"]}
