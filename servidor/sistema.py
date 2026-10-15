"""O prompt de sistema de cada conversa.

Ele é montado uma vez, quando a conversa começa, e fica guardado nela. Mudar a
personalização depois vale para as conversas novas: assim o começo do pedido
não muda no meio de uma conversa, o cache continua valendo e o raciocínio das
respostas anteriores não é descartado.
"""
from __future__ import annotations

import platform
import sys
from datetime import date

import config
import contexto_pasta
import tutoriais
from ferramentas import memoria

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]


def _hoje() -> str:
    d = date.today()
    return f"{d.strftime('%d/%m/%Y')} ({DIAS[d.weekday()]})"


def _personalizacao(cfg: dict) -> list[str]:
    partes = []
    sobre = []
    if cfg.get("nome"):
        sobre.append(f"Nome: {cfg['nome']}")
    if cfg.get("sobre_voce"):
        sobre.append(cfg["sobre_voce"].strip())
    if sobre:
        partes.append("<sobre_quem_usa>\n" + "\n".join(sobre) + "\n</sobre_quem_usa>")
    if cfg.get("como_responder"):
        partes.append("<como_responder>\n" + cfg["como_responder"].strip() + "\n</como_responder>")
    est = config.estilos(cfg).get(cfg.get("estilo") or "normal")
    if est and est.get("instrucoes"):
        partes.append(f"<estilo nome=\"{est['nome']}\">\n{est['instrucoes'].strip()}\n</estilo>")
    return partes


def chat(cfg: dict, projeto: dict | None = None) -> str:
    partes = [
        "Você é o Claude, um assistente de IA feito pela Anthropic. Você está conversando pelo Clave, um app "
        "independente (não é um produto da Anthropic) que usa a API do Claude com a chave de quem usa.",
        f"Data de hoje: {_hoje()}.",
        "Responda no idioma em que a pessoa escrever. A interface mostra Markdown: títulos, listas, tabelas, "
        "blocos de código com a linguagem indicada e fórmulas em LaTeX entre $...$ ou $$...$$. Quando fizer uma "
        "página HTML completa ou um SVG, entregue num único bloco de código (```html ou ```svg): a pessoa pode "
        "abrir uma prévia ao lado da conversa.",
    ]
    guia = tutoriais.guia_para_o_claude()
    if guia:
        partes.append(guia)
    partes += _personalizacao(cfg)
    if projeto:
        bloco = f"<projeto nome=\"{projeto['nome']}\">"
        if projeto.get("descricao"):
            bloco += f"\nDescrição: {projeto['descricao'].strip()}"
        if projeto.get("instrucoes"):
            bloco += f"\nInstruções do projeto:\n{projeto['instrucoes'].strip()}"
        if projeto.get("arquivos"):
            bloco += ("\nOs arquivos de conhecimento do projeto vêm anexados na primeira mensagem desta conversa.")
        bloco += "\n</projeto>"
        partes.append(bloco)
    lista = [s for s in contexto_pasta.skills(None) if not s["manual"]]
    if lista:
        linhas = [f"- {s['nome']}: {s['descricao']}" for s in lista]
        partes.append(
            "Skills disponíveis (procedimentos salvos por quem usa e pelos plugins ligados). Quando o pedido combinar "
            "com uma delas, carregue a skill com usar_skill antes de responder e siga o que ela diz. Aqui no chat "
            "não há pasta nem terminal: se a skill depender disso, sugira o modo Code.\n" + "\n".join(linhas))
    partes.append(OUTRA_CONVERSA)
    if cfg.get("memoria_ligada"):
        partes.append(memoria.instrucoes_completas())
    return "\n\n".join(partes)


OUTRA_CONVERSA = (
    "Outra conversa: quando a pessoa citar um trabalho que é outro assunto ou fica para depois, ou quando você notar "
    "algo separado que vale fazer (um próximo passo independente), sugira com sugerir_conversa em vez de só "
    "comentar no texto: vira um cartão e quem usa decide se abre. No máximo uma por resposta, nunca para o que você "
    "mesmo vai fazer aqui.")


def code(cfg: dict, pasta: str) -> str:
    so = "Windows" if sys.platform == "win32" else platform.system()
    terminal = "PowerShell" if sys.platform == "win32" else "bash"
    partes = [
        "Você é o Claude, um assistente de IA feito pela Anthropic, trabalhando no modo Code do Clave (um app "
        "independente que usa a API do Claude). Aqui você age como um agente no computador de quem usa: lê, "
        "cria e edita arquivos e roda comandos, sempre pelas ferramentas.",
        f"Data de hoje: {_hoje()}. Sistema: {so}. Terminal: {terminal}. Pasta de trabalho: {pasta}",
        "Permissões: quem usa escolhe um modo (Perguntar, Aceitar edições, Plano ou Livre) e pode mudar a qualquer "
        "momento. Algumas ações podem pedir aprovação, ser recusadas pela pessoa ou bloqueadas pelo Clave; o "
        "resultado da ferramenta diz o que aconteceu. Se uma ação for recusada, não tente o mesmo de outro jeito: "
        "pergunte o que a pessoa prefere. No modo Plano, investigue sem mudar nada e, quando o plano estiver pronto, "
        "apresente com apresentar_plano: a pessoa aprova e você segue executando. As regras de permissão (\"sempre "
        "permitir\") ficam no .claude/settings.local.json da pasta, no mesmo formato do Claude Code.",
        "Tarefas grandes: dá para propor um fluxo (executar_fluxo), em que cada etapa roda num modelo diferente "
        "(por exemplo, Opus planeja, Sonnet faz e testa). O fluxo custa mais e sempre pede o OK de quem usa; "
        "use quando valer o custo ou quando a pessoa pedir.",
        OUTRA_CONVERSA,
        "Como trabalhar:\n"
        "- Muita gente que usa o Clave não programa. Explique em linguagem simples o que vai fazer e o que fez.\n"
        "- Antes de começar uma tarefa com vários passos, diga em uma frase o que vai fazer e use "
        "atualizar_tarefas para mostrar os passos. No fim, resuma o que mudou e o que a pessoa precisa fazer.\n"
        "- Olhe a pasta e leia os arquivos relevantes antes de mudar algo. Preserve o que já funciona e mude só "
        "o necessário. Prefira editar_arquivo a reescrever um arquivo inteiro.\n"
        "- Depois de mudar, confira: rode o script, os testes ou abra o resultado. Não diga que funciona sem "
        "ter conferido; se não deu para conferir, diga isso.\n"
        "- Nada destrutivo sem necessidade (apagar, sobrescrever dados, publicar, git push). Na dúvida, pergunte.\n"
        "- Arquivos que a pessoa tenha marcado como protegidos ficam fora do seu alcance; não tente contornar.",
    ]
    guia = tutoriais.guia_para_o_claude()
    if guia:
        partes.append(guia)
    partes += _personalizacao(cfg)

    if cfg.get("carregar_claude_md", True):
        arquivos = contexto_pasta.instrucoes(pasta)
        if arquivos:
            corpo = []
            for a in arquivos:
                corpo.append(f"<arquivo caminho=\"{a['caminho']}\" escopo=\"{a['escopo']}\">\n{a['texto']}\n</arquivo>")
            partes.append(
                "As instruções abaixo foram escritas por quem usa para valer nesta pasta (arquivos CLAUDE.md ou "
                "AGENTS.md, do mais geral para o mais específico). Siga-as: quando duas se contradizem, vale a mais "
                "específica.\n<instrucoes_da_pasta>\n" + "\n".join(corpo) + "\n</instrucoes_da_pasta>")

    lista = contexto_pasta.skills(pasta)
    automaticas = [s for s in lista if not s["manual"]]
    if automaticas:
        linhas = [f"- {s['nome']}: {s['descricao']}" for s in automaticas]
        partes.append(
            "Skills disponíveis (procedimentos salvos na pasta). Quando a tarefa combinar com uma delas, carregue "
            "a skill com usar_skill antes de começar e siga o que ela diz:\n" + "\n".join(linhas))
    if cfg.get("memoria_ligada"):
        partes.append(memoria.instrucoes_completas())
    return "\n\n".join(partes)


def tutor(licao: dict | None) -> str:
    """O ajudante das lições (roda no Haiku 5.5)."""
    partes = [
        "Você é o ajudante das lições do Clave, um app independente para usar o Claude (a IA da Anthropic) pela API. "
        "Quem fala com você está aprendendo, muitas vezes sem nunca ter usado uma IA nem programado.",
        f"Data de hoje: {_hoje()}.",
        "Como responder:\n"
        "- De forma detalhada e fácil de entender: comece pela resposta direta, depois explique com um exemplo do "
        "dia a dia. Quando um passo a passo ajudar, numere os passos.\n"
        "- Evite jargão. Quando precisar de um termo técnico, explique na mesma frase (e, se ele estiver no "
        "glossário, ponha o link).\n"
        "- Se a pessoa escrever um termo errado (como \"JASON\" querendo dizer JSON), diga com gentileza o nome certo.\n"
        "- Responda sobre o Clave só o que estiver nas lições abaixo; se não souber como algo funciona no app, diga "
        "que não sabe em vez de inventar.\n"
        "- Responda no idioma da pessoa.",
    ]
    guia = tutoriais.guia_para_o_claude()
    if guia:
        partes.append(guia)
    glossario = tutoriais.ler("glossario")
    if glossario:
        partes.append(f"<glossario>\n{glossario['texto']}\n</glossario>")
    if licao:
        partes.append(f"A pessoa está lendo esta lição agora:\n<licao titulo=\"{licao['titulo']}\">\n{licao['texto']}\n</licao>")
    return "\n\n".join(partes)


def editor_memoria() -> str:
    """O agente que altera as memórias a pedido de quem usa (roda no Sonnet 5.5)."""
    return "\n\n".join([
        "Você é o editor de memória do Clave. A pessoa está olhando as memórias que o Claude guarda sobre ela "
        "(arquivos Markdown em /memories, um por assunto, mais o índice /memories/MEMORY.md) e quer mudar alguma "
        "coisa. Use a ferramenta memory para fazer exatamente o que ela pedir.",
        f"Data de hoje: {_hoje()}.",
        "Regras:\n"
        "- Leia os arquivos envolvidos antes de mudar. Mude só o que foi pedido; não apague nem reescreva o resto.\n"
        "- Mantenha o formato: cada arquivo começa com o cabeçalho (---, nome, descricao, tipo, ---) e o "
        "MEMORY.md tem uma linha por arquivo no formato `- [Título](arquivo.md): resumo`. Criou, renomeou ou "
        "apagou um arquivo, atualize o índice.\n"
        "- Se o pedido for ambíguo (não dá para saber qual memória ou o que pôr no lugar), pergunte antes de mudar.\n"
        "- No fim, diga em poucas linhas, em linguagem simples, o que mudou em cada arquivo.\n"
        "- Nunca guarde senhas, chaves, tokens, números de documento ou de cartão, mesmo que a pessoa peça; "
        "explique o porquê.",
        memoria.INSTRUCOES,
        "Índice atual (/memories/MEMORY.md):\n" + (memoria.texto_indice() or "(vazio)"),
    ])
