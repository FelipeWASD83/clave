"""Comandos de barra no formato do Claude Code.

Um comando é um .md em .claude/commands/ (o nome do arquivo vira /nome; subpasta vira prefixo,
como /frontend:componente), nos pessoais (~/.claude/commands) ou num plugin (/plugin:nome). Toda
skill também é um comando: /nome-da-skill carrega a skill. O texto pode usar $ARGUMENTS (tudo o que
veio depois do comando), $0, $1... (cada argumento) e $ARGUMENTS[N].

Os comandos do próprio app (/novo, /modelo, /fluxo...) são resolvidos na interface.
"""
from __future__ import annotations

import re
import shlex
from pathlib import Path

import contexto_pasta
import i18n
from i18n import t

# as descrições são mostradas com t() (em listar)
EMBUTIDOS_APP = [
    ("novo", "Começa uma conversa nova"),
    ("modelo", "Troca o modelo desta conversa (opus, sonnet, haiku, fable)"),
    ("esforco", "Troca o nível de raciocínio (baixo, medio, alto, muito-alto, maximo)"),
    ("plano", "Modo Plano: o Claude investiga e propõe um plano antes de mudar qualquer coisa"),
    ("fluxo", "Roda um fluxo com vários modelos (pede o seu OK e mostra o custo antes)"),
    ("custo", "Mostra quanto esta conversa e o mês já gastaram"),
    ("compact", "Resume a conversa agora para gastar menos nas próximas mensagens"),
    ("web", "Liga ou desliga a busca na web nesta conversa (on ou off)"),
    ("resumo", "Pede ao Claude um resumo do que foi decidido, feito e o que falta"),
    ("exportar", "Baixa a conversa em Markdown"),
    ("economia", "Dicas para esta conversa gastar menos"),
    ("importar", "Traz memórias, projetos e rotinas do Claude ou do ChatGPT"),
    ("memoria", "Abre as memórias que o Claude guarda sobre você"),
    ("permissoes", "Abre as regras de permissão"),
    ("plugins", "Abre os plugins"),
    ("ajuda", "Lista os comandos"),
]


# O nome em inglês de cada comando, plugin, skill e fluxo que vem com o Clave (o português é o nome dos arquivos).
# Os dois funcionam em qualquer idioma; o menu mostra o do idioma da interface. Comando e skill que a pessoa cria ou
# instala de fora ficam só com o nome que têm. Num nome com prefixo ("vendas:proposta"), cada parte é traduzida.
NOMES_EN = {
    # do próprio app
    "novo": "new", "modelo": "model", "esforco": "effort", "plano": "plan", "fluxo": "workflow", "custo": "cost",
    "resumo": "summary", "exportar": "export", "economia": "savings", "importar": "import", "memoria": "memory",
    "permissoes": "permissions", "ajuda": "help", "compactar": "compact",
    # plugins que vêm com o Clave e os comandos deles
    "automacao-windows": "windows-automation", "crie-o-seu": "make-your-own", "escrita": "writing",
    "escritorio": "office", "pesquisa": "research", "programacao": "programming", "sites-e-apps": "sites-and-apps",
    "vendas": "sales", "organizar": "organize", "nova-skill": "new-skill", "revisar": "review",
    "resumir-planilha": "summarize-spreadsheet", "pesquisar": "search", "explicar": "explain", "pagina": "page",
    "automatizar": "automate", "pedidos": "orders", "proposta": "proposal", "relatorio": "report",
    # skills dos plugins
    "agendar-tarefa": "schedule-task", "organizar-arquivos": "organize-files", "renomear-em-lote": "batch-rename",
    "script-powershell-seguro": "safe-powershell-script", "criar-agente": "create-agent",
    "criar-comando": "create-command", "criar-plugin": "create-plugin", "criar-skill": "create-skill",
    "ata-de-reuniao": "meeting-minutes", "email-profissional": "professional-email",
    "resumir-documento": "summarize-document", "revisar-texto": "proofread-text",
    "comparar-planilhas": "compare-spreadsheets", "excel-avancado": "advanced-excel", "limpar-dados": "clean-data",
    "relatorio-em-pdf": "pdf-report", "comparar-opcoes": "compare-options", "pesquisa-com-fontes": "sourced-research",
    "depurar-erro": "debug-error", "escrever-testes": "write-tests", "explicar-codigo": "explain-code",
    "revisar-codigo": "code-review", "checklist-web": "web-checklist", "pagina-simples": "simple-page",
    "publicar-site": "publish-site", "automacao-sem-ia": "automation-without-ai",
    "follow-up-de-cliente": "client-follow-up", "pedido-para-planilha": "orders-to-spreadsheet",
    "proposta-comercial": "sales-proposal", "relatorio-de-vendas": "sales-report", "responder-cliente": "answer-client",
    # fluxos prontos (/fluxo <id>)
    "escrever-e-revisar": "write-and-review", "pesquisa-profunda": "deep-research",
    "planejar-fazer-testar": "plan-build-test", "planilha-grande": "big-spreadsheet",
    "revisao-em-paralelo": "parallel-review",
    # skills que vêm na pasta skills/ do Clave
    "ver-video": "watch-video",
}
_PT = {en: pt for pt, en in NOMES_EN.items() if en != pt and pt != "compactar"}


def nome_en(nome: str) -> str:
    """'vendas:proposta' -> 'sales:proposal'."""
    return ":".join(NOMES_EN.get(p, p) for p in nome.split(":"))


def canonico(nome: str) -> str:
    """O nome em português (o dos arquivos), venha ele em português ou em inglês."""
    return ":".join(_PT.get(p, p) for p in nome.split(":"))


def nome_na_tela(nome: str) -> str:
    return nome_en(nome) if i18n.idioma() == "en" else nome


def _bases(pasta: str | Path | None) -> list[tuple[str, str, Path]]:
    bases = []
    if pasta:
        bases.append(("pasta", "", Path(pasta) / ".claude" / "commands"))
    bases.append(("pessoal", "", Path.home() / ".claude" / "commands"))
    import plugins
    for nome_plugin, d in plugins.partes("commands"):
        bases.append((f"plugin:{nome_plugin}", nome_plugin, d))
    return bases


def listar(pasta: str | Path | None = None, com_skills: bool = True) -> list[dict]:
    vistos: dict[str, dict] = {nome: {"nome": nome, "descricao": t(desc), "origem": "app", "tipo": "app"}
                               for nome, desc in EMBUTIDOS_APP}
    if com_skills:
        for s in contexto_pasta.skills(pasta):
            if s.get("invocavel", True) and s["nome"] not in vistos:
                vistos[s["nome"]] = {"nome": s["nome"], "descricao": s["descricao"], "origem": s.get("origem", ""),
                                     "tipo": "skill", "argumentos": s.get("argumentos", "")}
    for origem, prefixo, base in _bases(pasta):
        if not base.is_dir():
            continue
        for arq in sorted(base.rglob("*.md")):
            rel = arq.relative_to(base).with_suffix("").as_posix().replace("/", ":")
            nome = f"{prefixo}:{rel}" if prefixo else rel
            if nome in vistos:
                continue  # skill com o mesmo nome vence (como no Claude Code)
            try:
                fm = contexto_pasta._frontmatter(arq.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            pt = (i18n.guardado_pt(base.parent).get("commands", {}).get(rel) or {}) if origem.startswith("plugin:") else {}
            vistos[nome] = {"nome": nome, "descricao": pt.get("description") or str(fm.get("description") or "").strip(),
                            "origem": origem, "tipo": "comando",
                            "argumentos": pt.get("argument-hint") or str(fm.get("argument-hint") or ""), "caminho": str(arq)}
    for c in vistos.values():  # o nome em inglês só para o que vem com o Clave (app, plugins e a pasta skills/)
        origem = str(c.get("origem", ""))
        traduz = c["tipo"] == "app" or origem.startswith("plugin:") or origem == "clave"
        c["nome_en"] = nome_en(c["nome"]) if traduz else c["nome"]
    # um comando ou skill da pessoa com o mesmo nome da tradução de um comando do app (ex.: plan.md do Claude Code)
    # continua sendo dela: o comando do app fica só com o nome em português no menu
    da_pessoa = {c["nome"] for c in vistos.values() if c["tipo"] != "app"}
    for c in vistos.values():
        if c["tipo"] == "app" and c["nome_en"] != c["nome"] and c["nome_en"] in da_pessoa:
            c["nome_en"] = c["nome"]
    return sorted(vistos.values(), key=lambda c: ({"app": 0, "comando": 1, "skill": 2}[c["tipo"]], c["nome"]))


_COMANDO = re.compile(r"^/([A-Za-z0-9][\w:.-]*)(?:[ \t]+(.*))?$", re.S)


def separar(texto: str) -> tuple[str, str] | None:
    """'/revisar arquivo.txt' -> ('revisar', 'arquivo.txt'); None se não começa com comando."""
    m = _COMANDO.match((texto or "").strip())
    if not m:
        return None
    return m.group(1), (m.group(2) or "").strip()


def argumentos(texto: str) -> list[str]:
    try:
        return shlex.split(texto, posix=True)
    except ValueError:
        return texto.split()


def substituir(corpo: str, args_texto: str) -> str:
    args = argumentos(args_texto)

    def idx(n: int) -> str:
        return args[n] if 0 <= n < len(args) else ""

    usou = bool(re.search(r"\$ARGUMENTS|\$\d", corpo))
    corpo = re.sub(r"\$ARGUMENTS\[(\d+)\]", lambda m: idx(int(m.group(1))), corpo)
    corpo = corpo.replace("$ARGUMENTS", args_texto)
    corpo = re.sub(r"\$(\d+)", lambda m: idx(int(m.group(1))), corpo)
    if not usou and args_texto:
        corpo = corpo.rstrip() + f"\n\nARGUMENTS: {args_texto}"
    return corpo


def expandir(texto: str, pasta: str | Path | None = None) -> dict | None:
    """Transforma '/nome args' no texto que vai para o Claude.

    Devolve {texto, nome, tipo, modelo, ferramentas_permitidas} ou None se não é comando conhecido
    (comando do próprio app também volta None: quem trata é a interface).
    """
    sep = separar(texto)
    if not sep:
        return None
    digitado, args = sep
    if digitado in dict(EMBUTIDOS_APP):
        return None
    # o nome exato primeiro: um comando ou skill da pessoa chamado "plan" ou "review" vence a tradução do Clave
    exp = _expandir_nome(digitado, args, pasta)
    if exp:
        return exp
    pt = canonico(digitado)
    if pt in dict(EMBUTIDOS_APP) or pt == digitado:
        return None
    return _expandir_nome(pt, args, pasta)


def _expandir_nome(nome: str, args: str, pasta: str | Path | None) -> dict | None:
    for s in contexto_pasta.skills(pasta):
        if s["nome"] == nome and s.get("invocavel", True):
            c = contexto_pasta.conteudo_skill([s], nome)
            if not c:
                return None
            corpo = substituir(c["texto"].replace("${CLAUDE_SKILL_DIR}", c["pasta"]), args)
            return {"texto": (t("<skill nome=\"{nome}\" pasta=\"{pasta}\">\n{corpo}\n</skill>", nome=nome, pasta=c["pasta"],
                                corpo=corpo.strip()) + "\n\n"
                              + (t("Pedido: {pedido}", pedido=args) if args else t("Siga a skill acima."))
                              + ("\n" + t("(Responda em português do Brasil.)") if str(s.get("origem", "")).startswith("plugin") else "")),
                    "nome": nome, "tipo": "skill", "modelo": c.get("modelo") or "", "ferramentas_permitidas": []}
    for cmd in listar(pasta, com_skills=False):
        if cmd["nome"] == nome and cmd["tipo"] == "comando":
            arq = Path(cmd["caminho"])
            bruto = arq.read_text(encoding="utf-8", errors="replace")
            fm = contexto_pasta._frontmatter(bruto)
            corpo = contexto_pasta._FRONT.sub("", bruto, count=1)
            permitidas = [f for f in _lista_ferramentas(fm.get("allowed-tools")) if f]
            if cmd["origem"].startswith("plugin:"):
                # comando de plugin não libera terminal sozinho: só leitura e edição
                permitidas = [f for f in permitidas if not f.startswith(("Bash", "PowerShell"))]
            idioma = "\n\n" + t("(Responda em português do Brasil.)") if cmd["origem"].startswith("plugin:") else ""
            return {"texto": substituir(corpo.strip(), args) + idioma, "nome": nome, "tipo": "comando",
                    "modelo": str(fm.get("model") or ""), "ferramentas_permitidas": permitidas}
    return None


def _lista_ferramentas(valor) -> list[str]:
    """'Bash(gh *) Read' ou 'Read, Grep' -> ['Bash(gh *)', 'Read']."""
    if isinstance(valor, list):
        return [str(v).strip() for v in valor]
    texto = str(valor or "")
    saida, atual, nivel = [], "", 0
    for ch in texto:
        if ch == "(":
            nivel += 1
        elif ch == ")":
            nivel = max(0, nivel - 1)
        if nivel == 0 and ch in ", \t":
            if atual.strip():
                saida.append(atual.strip())
            atual = ""
        else:
            atual += ch
    if atual.strip():
        saida.append(atual.strip())
    return [s for s in saida if s != "-"]
