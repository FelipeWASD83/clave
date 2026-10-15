"""Importar do Claude (claude.ai) ou do ChatGPT: um pedido para colar lá, a leitura da resposta e a aplicação.

A pessoa cola o pedido no outro app, que devolve memórias, projetos e automações num formato fixo (seções com
título e uma entrada por linha). Aqui a resposta vira itens com caixinha; os marcados vão para o lugar certo:
instruções e estilo para "Como você quer as respostas", identidade e carreira para "Sobre você", preferências e
ferramentas para a memória, projetos para Projetos e automações para Rotinas (desligadas, no Haiku, para a pessoa
conferir antes de gastar).
"""
from __future__ import annotations

import re

import banco
import config
import rotinas
from ferramentas import memoria
from i18n import t

CATEGORIAS = ("instrucoes", "identidade", "carreira", "projetos", "preferencias", "estilo", "rotinas", "ferramentas")
# palavras do título de cada seção, nos dois idiomas (a resposta pode vir em qualquer um)
_CHAVES = [
    ("rotinas", ("automa", "rotina", "routine", "schedul", "agend", "recorr")),
    ("ferramentas", ("ferrament", "conector", "tool", "connector", "integra", "apps")),
    ("instrucoes", ("instru",)),
    ("identidade", ("identi",)),
    ("carreira", ("carreira", "career", "trabalho", "profiss")),
    ("projetos", ("projet", "project")),
    ("estilo", ("estilo", "style", "resposta", "writing")),
    ("preferencias", ("prefer",)),
]
_TITULO = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\d+[.)]\s*)?\**\s*([^*:\n]{2,60}?)\s*\**\s*:?\s*(?:\(.*\))?\s*$")
_TITULO_NUMERADO = re.compile(r"^\s*(?:#{1,6}\s*)?\d+[.)]\s*\**\s*([^*:\n]{2,60}?)\s*\**\s*:")
_ENTRADA = re.compile(r"^\s*(?:[-*•]\s*)?\[([^\]]{0,20})\]\s*[-–:]?\s*(.+)$")
_VAZIO = {"(nada)", "(none)", "nada", "none", "(nenhum)", "(nenhuma)", "n/a", "-"}


def pedido() -> str:
    """O pedido que a pessoa cola no Claude ou no ChatGPT."""
    return "\n".join([
        t("Exporte tudo o que você tem guardado sobre mim (memórias) e o que aprendeu sobre mim em conversas passadas, e também os meus projetos e as minhas automações. Preserve as minhas palavras ao pé da letra sempre que der, principalmente nas instruções e preferências."),
        "",
        t("## Categorias (nesta ordem, com estes títulos):"),
        "",
        t("1. **Instruções**: regras que eu pedi explicitamente para você seguir daqui em diante: tom, formato, estilo, \"sempre faça X\", \"nunca faça Y\" e correções do seu comportamento. Só o que está nas memórias guardadas, não o que veio de conversas."),
        t("2. **Identidade**: nome, idade, cidade, formação, família, idiomas e interesses."),
        t("3. **Carreira**: trabalho atual e anteriores, empresas e áreas de conhecimento."),
        t("4. **Projetos**: projetos que eu construí ou assumi de verdade, um por linha, no formato `Nome | o que é | situação atual | decisões importantes`. Se for um Projeto do Claude (ou um GPT personalizado) com instruções próprias, coloque as instruções na última parte."),
        t("5. **Preferências**: opiniões, gostos e jeito de trabalhar que valem em geral."),
        t("6. **Estilo de resposta**: como eu gosto das respostas (tamanho, tom, formato, idioma)."),
        t("7. **Automações e rotinas**: tarefas agendadas, rotinas e pedidos que você faz para mim de tempos em tempos, um por linha, no formato `Nome | quando roda (ex.: todo dia 08:00; seg a sex 09:30; a cada 2 horas) | o pedido completo, palavra por palavra`."),
        t("8. **Ferramentas e conectores**: apps e serviços que eu uso com você (Gmail, Google Drive, Notion, Excel, WhatsApp...) e para quê."),
        "",
        t("## Formato:"),
        "",
        t("Use um título por categoria. Dentro de cada categoria, uma entrada por linha, da mais antiga para a mais nova, assim:"),
        "",
        t("[AAAA-MM-DD] - Conteúdo da entrada."),
        "",
        t("Sem data conhecida, use [desconhecida]. Categoria sem nada: escreva (nada)."),
        "",
        t("## Saída:"),
        t("- Coloque a exportação inteira num único bloco de código, para eu copiar fácil."),
        t("- Depois do bloco, diga se é tudo ou se ainda falta alguma coisa."),
    ])


def _categoria(titulo: str) -> str | None:
    s = titulo.lower()
    for cat, chaves in _CHAVES:
        if any(c in s for c in chaves):
            return cat
    return None


def _quando(texto: str) -> tuple[dict, bool]:
    """Traduz "todo dia 08:00", "seg a sex 9h30", "a cada 2 horas", "weekdays at 9am"... Devolve (quando, certo)."""
    s = (texto or "").lower()
    m = re.search(r"(?:a cada|every)\s*(\d{1,2})\s*(?:h\b|hora|hour)", s)
    if m:
        return {"tipo": "horas", "a_cada": max(1, min(24, int(m.group(1))))}, True
    if re.search(r"de hora em hora|hourly|every hour|a cada hora", s):
        return {"tipo": "horas", "a_cada": 1}, True
    hora, certo = "09:00", False
    m = re.search(r"\b(\d{1,2})\s*(?::|h)\s*(\d{2})?\s*(am|pm)?\b|\b(\d{1,2})\s*(am|pm)\b", s)
    if m:
        h = int(m.group(1) or m.group(4))
        minutos = int(m.group(2) or 0)
        ampm = m.group(3) or m.group(5)
        if ampm == "pm" and h < 12:
            h += 12
        if ampm == "am" and h == 12:
            h = 0
        if 0 <= h < 24 and 0 <= minutos < 60:
            hora, certo = f"{h:02d}:{minutos:02d}", True
    if re.search(r"seg(?:unda)?\.?\s*(?:a|à|-)\s*sex|dias úteis|dia útil|weekdays?|mon(?:day)?\s*(?:-|to|through)\s*fri", s):
        return {"tipo": "semanal", "hora": hora, "dias": [0, 1, 2, 3, 4]}, certo
    nomes = [("seg", "mon"), ("ter", "tue"), ("qua", "wed"), ("qui", "thu"), ("sex", "fri"), ("sáb", "sat"), ("dom", "sun")]
    dias = [i for i, (pt, en) in enumerate(nomes) if re.search(rf"\b{pt}|\b{en}", s)]
    if dias and not re.search(r"todo dia|todos os dias|diariamente|daily|every day", s):
        return {"tipo": "semanal", "hora": hora, "dias": dias}, certo
    return {"tipo": "diaria", "hora": hora}, certo and bool(re.search(r"todo dia|todos os dias|diari|daily|every day|\d", s))


def ler(texto: str) -> dict:
    """Lê a resposta colada. Devolve {"itens": [...], "ignoradas": n}."""
    texto = (texto or "").replace("\r\n", "\n")
    cat = None
    itens, ignoradas = [], 0
    for linha in texto.split("\n"):
        bruta = linha.strip()
        if not bruta or bruta.startswith("```"):
            continue
        entrada = _ENTRADA.match(bruta)
        if not entrada:
            titulo = _TITULO_NUMERADO.match(bruta) or (_TITULO.match(bruta) if bruta.startswith(("#", "*")) or len(bruta) < 60 else None)
            achada = _categoria(titulo.group(1)) if titulo else None
            if achada:
                cat = achada
                continue
            if cat and bruta.startswith(("-", "*", "•")) and bruta.lstrip("-*• ").strip().lower() not in _VAZIO:
                conteudo, data = bruta.lstrip("-*• ").strip(), ""
            else:
                ignoradas += 1 if bruta.lower() not in _VAZIO else 0
                continue
        else:
            data, conteudo = entrada.group(1).strip(), entrada.group(2).strip()
        if not cat or conteudo.lower() in _VAZIO:
            continue
        item = {"id": f"{cat}-{len(itens)}", "categoria": cat, "texto": conteudo[:2000],
                "data": data if re.match(r"\d{4}-\d{2}-\d{2}$", data) else ""}
        partes = [p.strip() for p in conteudo.split("|")]
        if cat == "projetos":
            item["nome"] = (partes[0] or conteudo)[:80]
            item["detalhes"] = " | ".join(p for p in partes[1:] if p)
        elif cat == "rotinas":
            item["nome"] = (partes[0] or t("Rotina importada"))[:80]
            item["quando_texto"] = partes[1] if len(partes) > 2 else ""
            item["prompt"] = " | ".join(partes[2:]) if len(partes) > 2 else (partes[1] if len(partes) > 1 else conteudo)
            item["quando"], item["horario_certo"] = _quando(item["quando_texto"])
        itens.append(item)
    return {"itens": itens, "ignoradas": ignoradas}


def _juntar(atual: str, novas: list[str]) -> str:
    linhas = [x for x in (atual or "").splitlines()]
    existentes = {x.strip().lstrip("- ").strip().lower() for x in linhas}
    for n in novas:
        if n.strip().lower() not in existentes:
            linhas.append(f"- {n.strip()}")
            existentes.add(n.strip().lower())
    return "\n".join(linhas).strip()


def _memoria(arquivo: str, nome: str, descricao: str, tipo: str, entradas: list[str]) -> None:
    caminho = f"/memories/{arquivo}"
    try:
        atual = memoria._resolver(caminho).read_text(encoding="utf-8")
    except OSError:
        atual = f"---\nnome: {nome}\ndescricao: {descricao}\ntipo: {tipo}\n---\n"
    corpo = atual.rstrip() + "\n" + "\n".join(f"- {e}" for e in entradas if f"- {e}" not in atual) + "\n"
    memoria.gravar(caminho, corpo)
    indice = memoria.raiz() / memoria.INDICE
    try:
        texto_indice = indice.read_text(encoding="utf-8")
    except OSError:
        texto_indice = ""
    if f"]({arquivo})" not in texto_indice:
        indice.write_text((texto_indice.rstrip() + f"\n- [{nome}]({arquivo}): {descricao}\n").lstrip(), encoding="utf-8")


def aplicar(itens: list[dict]) -> dict:
    """Aplica os itens marcados. Devolve quantos foram para cada lugar."""
    por = {c: [i for i in itens if i.get("categoria") == c] for c in CATEGORIAS}
    feito = {"respostas": 0, "sobre_voce": 0, "memoria": 0, "projetos": 0, "rotinas": 0}
    cfg = config.carregar()
    alt = {}
    regras = [i["texto"] for i in por["instrucoes"] + por["estilo"]]
    if regras:
        alt["como_responder"] = _juntar(cfg.get("como_responder", ""), regras)
        feito["respostas"] = len(regras)
    sobre = [i["texto"] for i in por["identidade"] + por["carreira"]]
    if sobre:
        alt["sobre_voce"] = _juntar(cfg.get("sobre_voce", ""), sobre)
        feito["sobre_voce"] = len(sobre)
    if alt:
        config.salvar(alt)
    if por["preferencias"]:
        _memoria("preferencias-importadas.md", t("Preferências (importadas)"),
                 t("Gostos e jeito de trabalhar da pessoa, trazidos de outro assistente"), "preferencia",
                 [i["texto"] for i in por["preferencias"]])
        feito["memoria"] += len(por["preferencias"])
    if por["ferramentas"]:
        _memoria("ferramentas-e-conectores.md", t("Ferramentas e conectores"),
                 t("Apps e serviços que a pessoa usa e para quê"), "referencia", [i["texto"] for i in por["ferramentas"]])
        feito["memoria"] += len(por["ferramentas"])
    nomes = {p["nome"].strip().lower() for p in banco.listar_projetos()}
    for p in por["projetos"]:
        nome = str(p.get("nome") or p["texto"])[:80].strip()
        if not nome or nome.lower() in nomes:
            continue
        banco.criar_projeto(nome, descricao=str(p.get("detalhes") or "")[:300], instrucoes=str(p.get("detalhes") or p["texto"]))
        nomes.add(nome.lower())
        feito["projetos"] += 1
    for r in por["rotinas"]:
        dados = {"prompt": r.get("prompt") or r["texto"], "modo": "chat", "quando": r.get("quando") or {"tipo": "diaria", "hora": "09:00"},
                 "teto_usd": 0.5, "modelo": "claude-haiku-5-5", "esforco": "low"}
        try:
            rotinas.salvar(None, r.get("nome") or t("Rotina importada"), dados, ligada=False)
            feito["rotinas"] += 1
        except rotinas.ErroRotina:
            continue
    return feito
