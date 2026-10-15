"""Ferramentas do modo Code: ler, buscar, escrever, editar e rodar comando na pasta de trabalho.

Cada ferramenta diz o próprio risco ("leitura", "escrita", "comando"); quem
decide se roda sozinha, se pergunta ou se recusa é `classificar`, a partir do
modo de permissão escolhido na conversa.
"""
from __future__ import annotations

import atexit
import base64
import codecs
import difflib
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import anexos
import banco
import contexto_pasta
import permissoes
import tarefas
from ferramentas import email as femail, excel, word
from i18n import t

IGNORAR_PASTAS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
                  ".next", ".cache", ".idea", ".vs"}
IMAGENS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
           ".webp": "image/webp"}
LIMITE_SAIDA = 30_000

# Comandos que apagam, sobrescrevem em massa ou publicam algo: sempre pedem OK, em qualquer modo.
# Comparados com o comando em minúsculas.
PERIGOSOS = [
    # apagar arquivos e pastas (PowerShell, cmd, bash, Python)
    r"\bremove-item\b", r"\bri\s", r"(^|[\s;|&(])(rm|del|erase|rd|rmdir)(\s|$)", r"\bclear-content\b",
    r"\bclear-recyclebin\b", r"\bshutil\.rmtree\b", r"\bos\.(remove|unlink|rmdir|removedirs)\b", r"\.unlink\(",
    r"\brmtree\b", r"\bsend2trash\b",
    # git e publicação
    r"\bgit\s+push\b", r"\bgit\s+reset\s+--hard\b", r"\bgit\s+clean\b", r"\bgit\s+checkout\s+--\s",
    r"\bgit\s+branch\s+-d\b", r"\bgit\s+rebase\b", r"--force\b", r"\bnpm\s+publish\b",
    r"\bgh\s+(repo\s+delete|release\s+delete|release\s+create|repo\s+create)\b", r"\bwrangler\s+(deploy|publish)\b",
    # sistema
    r"\bformat(-volume)?\b\s", r"\bdiskpart\b", r"\bshutdown\b", r"\bstop-computer\b", r"\brestart-computer\b",
    r"\breg\s+(delete|add)\b", r"\bremove-itemproperty\b", r"\bset-itemproperty\b.*hk(lm|cu)", r"\bset-executionpolicy\b",
    r"\bcipher\s+/w\b", r"\bbcdedit\b", r"\bvssadmin\b", r"\bmkfs\b", r"\bdd\s+if=", r"\bchmod\s+-r\b",
    r"\bschtasks\b.*/delete", r"\bunregister-scheduledtask\b",
    # baixar e executar direto
    r"\b(iwr|irm|invoke-webrequest|invoke-restmethod|curl|wget)\b.*\|\s*(iex|invoke-expression|sh|bash|python)\b",
]


def perigoso(comando: str) -> bool:
    c = comando.lower()
    return any(re.search(p, c) for p in PERIGOSOS)


# o que excel_abrir pode abrir: nada que execute (sem .bat, .exe, .lnk, nem planilha com macro)
ABRIVEIS = {".xlsx", ".csv", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".txt", ".md"}


def _cita_protegido(comando: str, protegidos: list[str]) -> str | None:
    """Comando que menciona um arquivo protegido pede OK (as ferramentas de arquivo negam; o terminal não tem como saber ao certo)."""
    c = comando.lower()
    for padrao in protegidos:
        p = padrao.strip().replace("\\", "/").lower()
        if p in (".git/**", ".git"):
            continue  # todo comando git citaria .git
        token = p[:-3] if p.endswith("/**") else p
        token = token.replace("*", "").strip("/")
        if len(token) >= 3 and token in c:
            return padrao
    return None


@dataclass
class Contexto:
    raiz: Path
    protegidos: list[str]
    execucao_id: str
    conversa_id: str
    emitir: callable = lambda evento: None
    parar: threading.Event = field(default_factory=threading.Event)
    lidos: set = field(default_factory=set)
    criados: set = field(default_factory=set)
    tarefas: list = field(default_factory=list)
    ferramenta_id: str = ""  # o tool_use que está rodando agora
    skills: list = field(default_factory=list)
    regras: list = field(default_factory=list)
    processo: subprocess.Popen | None = None

    def resolver(self, caminho: str) -> Path:
        p = Path(os.path.expandvars(os.path.expanduser(caminho or ".")))
        if not p.is_absolute():
            p = self.raiz / p
        return p.resolve()

    def dentro(self, p: Path) -> bool:
        try:
            return p == self.raiz or p.is_relative_to(self.raiz)
        except ValueError:
            return False

    def relativo(self, p: Path) -> str:
        try:
            return p.relative_to(self.raiz).as_posix() or "."
        except ValueError:
            return str(p)

    def protegido(self, p: Path) -> str | None:
        rel = self.relativo(p) if self.dentro(p) else p.as_posix()
        nome = p.name
        for padrao in self.protegidos:
            padrao = padrao.strip().replace("\\", "/")
            if not padrao:
                continue
            if padrao.endswith("/**"):
                base = padrao[:-3]
                if rel == base or rel.startswith(base + "/") or f"/{base}/" in f"/{rel}/":
                    return padrao
            elif fnmatch.fnmatch(nome, padrao) or fnmatch.fnmatch(rel, padrao):
                return padrao
        return None


class ErroFerramenta(Exception):
    pass


def _ferramenta(nome, descricao, propriedades, obrigatorios, risco):
    return {
        "def": {
            "name": nome,
            "description": descricao,
            "eager_input_streaming": True,
            "input_schema": {"type": "object", "properties": propriedades, "required": obrigatorios},
        },
        "risco": risco,
    }


FERRAMENTAS = {
    "listar_pasta": _ferramenta(
        "listar_pasta",
        "Lista arquivos e subpastas. Use para se orientar numa pasta antes de ler ou mudar algo. "
        "Caminhos relativos partem da pasta de trabalho.",
        {"caminho": {"type": "string", "description": "Pasta a listar (padrão: a pasta de trabalho)."},
         "profundidade": {"type": "integer", "description": "Quantos níveis descer (1 a 3, padrão 1)."}},
        [], "leitura"),
    "ler_arquivo": _ferramenta(
        "ler_arquivo",
        "Lê um arquivo. Texto volta com o número de cada linha; imagens (PNG, JPG, GIF, WebP) e PDFs voltam para "
        "você ver. Leia sempre o arquivo antes de editá-lo ou sobrescrevê-lo.",
        {"caminho": {"type": "string"},
         "linha_inicial": {"type": "integer", "description": "Primeira linha (começa em 1)."},
         "num_linhas": {"type": "integer", "description": "Quantas linhas ler (padrão 2000)."}},
        ["caminho"], "leitura"),
    "buscar_texto": _ferramenta(
        "buscar_texto",
        "Procura um padrão (expressão regular) dentro dos arquivos e devolve arquivo:linha: trecho. "
        "Use para achar onde algo está definido ou usado.",
        {"padrao": {"type": "string", "description": "Expressão regular (sintaxe do Python)."},
         "caminho": {"type": "string", "description": "Pasta ou arquivo onde procurar (padrão: pasta de trabalho)."},
         "filtro": {"type": "string", "description": "Filtro de nome de arquivo, como *.py ou *.{js,css}."},
         "ignorar_maiusculas": {"type": "boolean"},
         "max_resultados": {"type": "integer"}},
        ["padrao"], "leitura"),
    "achar_arquivos": _ferramenta(
        "achar_arquivos",
        "Acha arquivos pelo nome com um padrão glob, como **/*.py ou src/**/*.html. Mais novos primeiro.",
        {"padrao": {"type": "string"}, "caminho": {"type": "string"}},
        ["padrao"], "leitura"),
    "escrever_arquivo": _ferramenta(
        "escrever_arquivo",
        "Cria um arquivo novo ou substitui um arquivo inteiro. Para mudar parte de um arquivo que já existe, "
        "prefira editar_arquivo. Para substituir um arquivo existente, leia-o antes.",
        {"caminho": {"type": "string"}, "conteudo": {"type": "string", "description": "O conteúdo completo."}},
        ["caminho", "conteudo"], "escrita"),
    "editar_arquivo": _ferramenta(
        "editar_arquivo",
        "Troca um trecho exato de um arquivo por outro. O trecho_atual precisa aparecer uma vez só no arquivo "
        "(inclua linhas em volta para ficar único) ou use trocar_todos. Leia o arquivo antes.",
        {"caminho": {"type": "string"},
         "trecho_atual": {"type": "string", "description": "Texto exato que está no arquivo hoje."},
         "trecho_novo": {"type": "string", "description": "Texto que entra no lugar."},
         "trocar_todos": {"type": "boolean", "description": "Trocar todas as ocorrências."}},
        ["caminho", "trecho_atual", "trecho_novo"], "escrita"),
    "rodar_comando": _ferramenta(
        "rodar_comando",
        "Roda um comando no terminal do computador (PowerShell no Windows) dentro da pasta de trabalho e devolve "
        "a saída. Use para rodar scripts, testes, git, instalar dependências e automatizar tarefas. "
        "Não use para ler ou editar arquivos: para isso existem ferramentas próprias. "
        "Para servidores e programas que ficam rodando (como npm run dev ou python -m http.server), use "
        "em_segundo_plano: o comando continua rodando depois da resposta, você acompanha com ver_comando e "
        "encerra com parar_comando. Não use Start-Process para deixar um servidor rodando: a saída dele não chega "
        "até você; use em_segundo_plano.",
        {"comando": {"type": "string"},
         "descricao": {"type": "string", "description": "Uma frase curta, em português simples, do que o comando faz."},
         "tempo_limite_s": {"type": "integer", "description": "Segundos até desistir (padrão 120, máximo 600)."},
         "em_segundo_plano": {"type": "boolean", "description": (
             "true para servidores e programas que continuam rodando (npm run dev, python -m http.server, um "
             "watch). Devolve em poucos segundos com o id, a primeira saída e o endereço local, se aparecer; o "
             "comando segue rodando até alguém parar ou o Clave fechar (no máximo 5 por conversa). O tempo "
             "limite não vale aqui. Programas com janela que ele abrir (o navegador, um editor) continuam abertos "
             "quando ele para.")}},
        ["comando", "descricao"], "comando"),
    "ver_comando": _ferramenta(
        "ver_comando",
        "Mostra a saída mais recente de um comando que você deixou rodando em segundo plano nesta conversa "
        "(rodar_comando com em_segundo_plano) e diz se ele ainda está rodando.",
        {"id": {"type": "string", "description": "O id que rodar_comando devolveu (comando-...)."},
         "linhas": {"type": "integer", "description": "Quantas linhas do fim da saída mostrar (padrão 60, máximo 400)."}},
        ["id"], "leitura"),
    "parar_comando": _ferramenta(
        "parar_comando",
        "Encerra um comando que você deixou rodando em segundo plano nesta conversa, junto com os processos sem "
        "janela que ele abriu; programas com janela (o navegador, um editor) continuam abertos. Pare quando não "
        "precisar mais dele (um servidor de teste, por exemplo).",
        {"id": {"type": "string", "description": "O id que rodar_comando devolveu (comando-...)."}},
        ["id"], "leitura"),
    "mostrar_arquivo": _ferramenta(
        "mostrar_arquivo",
        "Mostra um arquivo da pasta para a pessoa, dentro da conversa: imagens (prints, gráficos, fotos), víd"
        "eos e áudios aparecem ali mesmo; PDF, planilha, documento e outros viram um cartão para abrir ou bai"
        "xar. Use sempre que gerar ou achar algo que a pessoa precisa ver (por exemplo: tirou um print de um "
        "site, mostre o print; gerou um gráfico, mostre o gráfico). Até 100 MB por arquivo.",
        {"caminho": {"type": "string"},
         "legenda": {"type": "string", "description": "Uma frase sobre o que é o arquivo, no idioma da pessoa."}},
        ["caminho"], "leitura"),
    "word_ler": _ferramenta(
        "word_ler",
        "Lê um documento do Word (.docx): o texto com os títulos marcados (#) e as tabelas. Use antes de mudar um documento.",
        {"caminho": {"type": "string"}},
        ["caminho"], "leitura"),
    "word_criar": _ferramenta(
        "word_criar",
        "Cria um documento do Word (.docx) a partir de um texto em Markdown simples: títulos (#, ##, ###), parágrafos, listas (- ou 1.), tabelas (| a | b |), **negrito** e *itálico*; uma linha só com --- vira quebra de página. Bom para propostas, contratos, relatórios e cartas.",
        {"caminho": {"type": "string", "description": "Arquivo .docx a criar (substitui se existir)."},
         "conteudo": {"type": "string", "description": "O documento em Markdown simples."}},
        ["caminho", "conteudo"], "escrita"),
    "word_alterar": _ferramenta(
        "word_alterar",
        "Troca trechos de texto num documento do Word existente, mantendo a formatação (bom para preencher modelos: nome do cliente, valores, datas). Leia antes com word_ler e copie o trecho exato. Para salvar numa cópia, use saida.",
        {"caminho": {"type": "string"},
         "trocas": {"type": "array", "description": "Lista de trocas: cada uma com de (o trecho exato) e para (o texto novo).", "items": {"type": "object", "properties": {
             "de": {"type": "string"}, "para": {"type": "string"}}, "required": ["de", "para"]}},
         "saida": {"type": "string", "description": "Salvar o resultado em outro arquivo, deixando o original intacto."}},
        ["caminho", "trocas"], "escrita"),
    "word_no_app": _ferramenta(
        "word_no_app",
        "Exporta um documento do Word para PDF usando o Microsoft Word instalado no computador.",
        {"caminho": {"type": "string"}, "saida": {"type": "string", "description": "Arquivo PDF de saída (opcional)."}},
        ["caminho"], "escrita"),
    "email_salvar_anexo": _ferramenta(
        "email_salvar_anexo",
        "Salva na pasta de trabalho um anexo de um e-mail (use o id e o nome do anexo que o email_ler mostrou).",
        {"id": {"type": "string"}, "anexo": {"type": "string"}, "caminho": {"type": "string", "description": "Onde salvar (padrão: o nome do anexo na pasta de trabalho)."}},
        ["id", "anexo"], "escrita"),
    "atualizar_tarefas": _ferramenta(
        "atualizar_tarefas",
        "Mostra ao usuário a sua lista de passos da tarefa atual. Use em tarefas com 3 passos ou mais: crie a "
        "lista no começo e atualize conforme avança (só um passo 'fazendo' por vez). Antes de terminar a resposta, "
        "chame de novo com todos os passos 'feito' (ou tire os que você não fez e diga por quê no texto): a lista "
        "fica na tela de quem usa.",
        {"tarefas": {"type": "array", "items": {"type": "object", "properties": {
            "texto": {"type": "string"},
            "estado": {"type": "string", "enum": ["pendente", "fazendo", "feito"]}},
            "required": ["texto", "estado"]}}},
        ["tarefas"], "leitura"),
    "excel_ler": _ferramenta(
        "excel_ler",
        "Lê uma planilha do Excel (.xlsx/.xlsm) da pasta: abas, valores e fórmulas (com o valor calculado, quando o "
        "arquivo tem). Use em vez de ler_arquivo para planilhas.",
        {"caminho": {"type": "string"}, "aba": {"type": "string"},
         "intervalo": {"type": "string", "description": "Ex.: A1:H40 (padrão: a parte usada da aba)."},
         "max_linhas": {"type": "integer", "description": "Padrão 100."}},
        ["caminho"], "leitura"),
    "excel_alterar": _ferramenta(
        "excel_alterar",
        "Cria ou altera uma planilha do Excel (.xlsx/.xlsm) na pasta: escrever dados e fórmulas, formatar, "
        "tabelas, gráficos, filtros, abas, formatação condicional, listas de opção. Feche o arquivo no Excel antes. "
        "Atenção: ao salvar um arquivo que já existe, imagens, formas, segmentações e macros podem se perder; se a "
        "planilha tiver isso, crie uma cópia com outro nome em vez de alterar o original. "
        "Para conferir o resultado das fórmulas, use excel_no_app com acao recalcular e leia de novo.",
        {"caminho": {"type": "string", "description": "Arquivo .xlsx (é criado se não existir)."},
         "saida": {"type": "string", "description": "Salvar o resultado em outro arquivo, deixando o original intacto (recomendado quando a planilha é da pessoa)."},
         "operacoes": excel.ESQUEMA_OPERACOES},
        ["caminho", "operacoes"], "escrita"),
    "excel_no_app": _ferramenta(
        "excel_no_app",
        "Usa o Microsoft Excel instalado no computador para: recalcular (calcula todas as fórmulas e salva), "
        "pdf (exporta a planilha para PDF) ou converter_xlsx (converte .xls ou .csv em .xlsx).",
        {"caminho": {"type": "string"}, "acao": {"type": "string", "enum": ["recalcular", "pdf", "converter_xlsx"]},
         "saida": {"type": "string", "description": "Arquivo de saída (para pdf e converter_xlsx; opcional)."}},
        ["caminho", "acao"], "escrita"),
    "excel_abrir": _ferramenta(
        "excel_abrir",
        "Abre uma planilha (ou outro arquivo) no programa do computador, como o Excel, para a pessoa ver. Use no "
        "fim, quando ela quiser conferir o resultado.",
        {"caminho": {"type": "string"}},
        ["caminho"], "leitura"),
    "usar_skill": _ferramenta(
        "usar_skill",
        "Carrega as instruções completas de uma skill (procedimento salvo na pasta). Use quando a tarefa "
        "combinar com a descrição de uma skill da lista do sistema, antes de começar a tarefa.",
        {"nome": {"type": "string"}},
        ["nome"], "leitura"),
}


def definicoes(com_skills: bool) -> list[dict]:
    defs = [f["def"] for nome, f in FERRAMENTAS.items() if nome != "usar_skill"
            and (nome != "email_salvar_anexo" or femail.ligado())]
    if com_skills:
        defs.append(FERRAMENTAS["usar_skill"]["def"])
    return defs


# ---------------- permissão ----------------

def classificar(nome: str, entrada: dict, ctx: Contexto, modo: str, liberados: set) -> tuple[str, str]:
    """Devolve ("auto" | "perguntar" | "negar", motivo)."""
    d = decidir(nome, entrada, ctx, modo, liberados)
    return d["decisao"], d["motivo"]


def decidir(nome: str, entrada: dict, ctx: Contexto, modo: str, liberados: set) -> dict:
    """Decide se a ferramenta roda sozinha, pergunta ou é recusada, e por quê.

    Ordem: arquivo protegido (sempre recusado), regra de negar, modo Plano, regra de perguntar, comando
    perigoso ou que cita protegido (pergunta, a não ser que uma regra escrita para ele permita), regra de
    permitir, "nesta tarefa", e por fim o modo de permissão. Devolve {decisao, motivo, origem, regra}.
    """
    def r(decisao, motivo="", origem="modo", regra=None):
        return {"decisao": decisao, "motivo": motivo, "origem": origem, "regra": regra.texto if regra else None,
                "escopo": regra.escopo if regra else None}

    f = FERRAMENTAS.get(nome)
    if not f:
        return r("negar", t("ferramenta desconhecida"), "clave")
    risco = f["risco"]
    if nome in ("atualizar_tarefas", "usar_skill"):
        return r("auto")

    alvos = []
    for campo in ("caminho", "saida"):
        if isinstance(entrada.get(campo), str) and entrada.get(campo):
            alvo = ctx.resolver(entrada[campo])
            prot = ctx.protegido(alvo)
            if prot:
                return r("negar", t("o caminho está na lista de arquivos protegidos ({padrao})", padrao=prot), "protegido")
            alvos.append(alvo)

    if nome == "excel_abrir" and alvos and alvos[0].suffix.lower() not in ABRIVEIS:
        return r("negar", t("só dá para abrir planilha (.xlsx, .csv), PDF, imagem ou texto; outros tipos podem executar programas"), "clave")

    acao, regra = permissoes.avaliar(ctx.regras, permissoes.alvos(nome, entrada, ctx.resolver), ctx.raiz)
    if acao == "deny":
        return r("negar", t("bloqueado pela {regra}", regra=regra.descrever()), "regra", regra)

    if risco == "comando":
        cmd = str(entrada.get("comando", ""))
        if modo == "plano":
            return r("negar", t("o modo Plano só lê; termine de investigar e apresente o plano com apresentar_plano (aprovado, o modo muda)"))
        if acao == "ask":
            return r("perguntar", t("pedido pela {regra}", regra=regra.descrever()), "regra", regra)
        especifica = acao == "allow" and not permissoes.generica(regra)
        if perigoso(cmd) and not especifica:
            return r("perguntar", t("comando que pode apagar ou publicar algo"), "perigoso")
        citado = _cita_protegido(cmd, ctx.protegidos)
        if citado and not especifica:
            return r("perguntar", t("o comando cita um arquivo protegido ({padrao})", padrao=citado), "protegido")
        if acao == "allow":
            return r("auto", "", "regra", regra)
        if modo == "livre" or "comando" in liberados:
            return r("auto", "", "tarefa" if "comando" in liberados else "modo")
        return r("perguntar", t("rodar comando"))

    fora = any(not ctx.dentro(a) for a in alvos)
    if risco == "escrita" and modo == "plano":
        return r("negar", t("o modo Plano só lê") + ("" if fora else t("; termine de investigar e apresente o plano com apresentar_plano (aprovado, o modo muda)")))
    if acao == "ask":
        return r("perguntar", t("pedido pela {regra}", regra=regra.descrever()), "regra", regra)
    if acao == "allow":
        return r("auto", "", "regra", regra)
    if fora:
        return r("perguntar", t("caminho fora da pasta de trabalho"))
    if risco == "leitura":
        return r("auto")
    if modo in ("aceitar_edicoes", "livre") or "escrita" in liberados:
        return r("auto", "", "tarefa" if "escrita" in liberados and modo not in ("aceitar_edicoes", "livre") else "modo")
    return r("perguntar", t("mudar arquivo"))


# ---------------- execução ----------------

def _numerar(linhas: list[str], inicio: int) -> str:
    saida = []
    for i, linha in enumerate(linhas, start=inicio):
        if len(linha) > 2000:
            linha = linha[:2000] + t("… [linha cortada]")
        saida.append(f"{i:>6}\t{linha}")
    return "\n".join(saida)


def _ler_texto(p: Path) -> tuple[str, str]:
    dados = p.read_bytes()
    if b"\x00" in dados[:8192]:
        raise ErroFerramenta(t("O arquivo parece binário; não dá para ler como texto."))
    for cod in ("utf-8-sig", "utf-8"):
        try:
            return dados.decode(cod), cod
        except UnicodeDecodeError:
            continue
    return dados.decode("latin-1"), "latin-1"


def _limitar(texto: str) -> str:
    if len(texto) <= LIMITE_SAIDA:
        return texto
    meio = LIMITE_SAIDA // 2
    return texto[:meio] + "\n\n" + t("[... {n} caracteres cortados ...]", n=len(texto) - LIMITE_SAIDA) + "\n\n" + texto[-meio:]


def _diff(antes: str, depois: str, rel: str) -> str:
    linhas = difflib.unified_diff(antes.splitlines(), depois.splitlines(), f"a/{rel}", f"b/{rel}", lineterm="", n=3)
    return "\n".join(list(linhas)[:600])


def _checkpoint(ctx: Contexto, p: Path) -> None:
    existia = p.exists()
    conteudo = p.read_bytes() if existia and p.is_file() else None
    banco.guardar_checkpoint(ctx.execucao_id, ctx.conversa_id, str(p), existia, conteudo)


def executar(nome: str, entrada: dict, ctx: Contexto):
    """Roda a ferramenta. Devolve o conteúdo do tool_result (texto ou lista de blocos)."""
    fn = globals().get("_f_" + nome)
    if fn is None:
        raise ErroFerramenta(t("Ferramenta desconhecida: {nome}", nome=nome))
    return fn(entrada, ctx)


def _f_listar_pasta(e, ctx: Contexto):
    base = ctx.resolver(e.get("caminho") or ".")
    if not base.is_dir():
        raise ErroFerramenta(t("Não é uma pasta: {caminho}", caminho=base))
    prof = max(1, min(3, int(e.get("profundidade") or 1)))
    linhas, total = [], 0

    def andar(d: Path, nivel: int, prefixo: str):
        nonlocal total
        try:
            itens = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except OSError as erro:
            linhas.append(prefixo + t("[sem acesso: {erro}]", erro=erro.strerror))
            return
        for item in itens:
            if total >= 400:
                return
            total += 1
            if item.is_dir():
                pulada = item.name in IGNORAR_PASTAS
                linhas.append(f"{prefixo}{item.name}/" + (t("  (ignorada)") if pulada else ""))
                if nivel < prof and not pulada:
                    andar(item, nivel + 1, prefixo + "  ")
            else:
                try:
                    tam = item.stat().st_size
                except OSError:
                    tam = 0
                linhas.append(f"{prefixo}{item.name}  ({_tam(tam)})")

    andar(base, 1, "")
    if total >= 400:
        linhas.append(t("[... lista cortada em 400 itens ...]"))
    return f"{base}\n" + ("\n".join(linhas) if linhas else t("(pasta vazia)"))


def _tam(n: int) -> str:
    for un in ("B", "KB", "MB", "GB"):
        if n < 1024 or un == "GB":
            return f"{n:.0f} {un}" if un == "B" else f"{n:.1f} {un}"
        n /= 1024
    return str(n)


def _f_ler_arquivo(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if not p.is_file():
        raise ErroFerramenta(t("Arquivo não encontrado: {caminho}", caminho=p))
    ext = p.suffix.lower()
    if ext in IMAGENS:
        dados = p.read_bytes()
        if len(dados) > 5 * 1024 * 1024:
            raise ErroFerramenta(t("Imagem maior que 5 MB; reduza antes (por exemplo, com um script Python)."))
        ctx.lidos.add(str(p))
        return [{"type": "text", "text": t("Imagem: {caminho}", caminho=p)},
                {"type": "image", "source": {"type": "base64", "media_type": IMAGENS[ext],
                                             "data": base64.b64encode(dados).decode("ascii")}}]
    if ext == ".pdf":
        dados = p.read_bytes()
        if len(dados) > 30 * 1024 * 1024:
            raise ErroFerramenta(t("PDF maior que 30 MB."))
        ctx.lidos.add(str(p))
        return [{"type": "text", "text": f"PDF: {p}"},
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                                "data": base64.b64encode(dados).decode("ascii")}}]
    texto, _ = _ler_texto(p)
    linhas = texto.splitlines()
    inicio = max(1, int(e.get("linha_inicial") or 1))
    qtd = max(1, min(5000, int(e.get("num_linhas") or 2000)))
    trecho = linhas[inicio - 1: inicio - 1 + qtd]
    ctx.lidos.add(str(p))
    if not linhas:
        return f"{p}\n" + t("(arquivo vazio)")
    rodape = ""
    if inicio - 1 + qtd < len(linhas):
        rodape = "\n\n" + t("[o arquivo tem {n} linhas; leia o resto com linha_inicial={proxima}]", n=len(linhas),
                               proxima=inicio + qtd)
    return _limitar(_numerar(trecho, inicio)) + rodape


def _arquivos_em(base: Path, filtro: str | None, limite_tempo: float):
    padroes = _expandir_chaves(filtro) if filtro else None
    inicio = time.time()
    if base.is_file():
        yield base
        return
    for raiz, pastas, arquivos in os.walk(base):
        pastas[:] = [d for d in pastas if d not in IGNORAR_PASTAS]
        for a in arquivos:
            if time.time() - inicio > limite_tempo:
                return
            if padroes and not any(fnmatch.fnmatch(a, pd) for pd in padroes):
                continue
            yield Path(raiz) / a


def _expandir_chaves(padrao: str) -> list[str]:
    m = re.search(r"\{([^}]*)\}", padrao)
    if not m:
        return [padrao]
    return [padrao[:m.start()] + op + padrao[m.end():] for op in m.group(1).split(",")]


def _f_buscar_texto(e, ctx: Contexto):
    base = ctx.resolver(e.get("caminho") or ".")
    try:
        rx = re.compile(e["padrao"], re.I if e.get("ignorar_maiusculas") else 0)
    except re.error as erro:
        raise ErroFerramenta(t("Expressão regular inválida: {erro}", erro=erro))
    limite = max(1, min(500, int(e.get("max_resultados") or 150)))
    achados = []
    for arq in _arquivos_em(base, e.get("filtro"), 25):
        if ctx.protegido(arq):
            continue
        try:
            if arq.stat().st_size > 2_000_000:
                continue
            dados = arq.read_bytes()
        except OSError:
            continue
        if b"\x00" in dados[:4096]:
            continue
        texto = dados.decode("utf-8", errors="replace")
        for n, linha in enumerate(texto.splitlines(), 1):
            if rx.search(linha):
                achados.append(f"{ctx.relativo(arq)}:{n}: {linha.strip()[:300]}")
                if len(achados) >= limite:
                    break
        if len(achados) >= limite:
            achados.append(t("[... parei em {n} resultados ...]", n=limite))
            break
    return "\n".join(achados) if achados else t("Nenhum resultado.")


def _f_achar_arquivos(e, ctx: Contexto):
    base = ctx.resolver(e.get("caminho") or ".")
    padrao = e["padrao"].replace("\\", "/")
    resultados = []
    if ".." in padrao.split("/"):
        raise ErroFerramenta(t("O padrão não pode subir de pasta (..). Use o parâmetro caminho para procurar em outro lugar."))
    for pd in _expandir_chaves(padrao):
        try:
            for p in base.glob(pd):
                if not p.resolve().is_relative_to(base.resolve()):
                    continue
                if any(parte in IGNORAR_PASTAS for parte in p.relative_to(base).parts):
                    continue
                if p.is_file():
                    resultados.append(p)
                if len(resultados) > 2000:
                    break
        except (ValueError, OSError) as erro:
            raise ErroFerramenta(t("Padrão inválido: {erro}", erro=erro))
    resultados = sorted(set(resultados), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    linhas = [ctx.relativo(p) for p in resultados[:500]]
    if len(resultados) > 500:
        linhas.append(t("[... mais {n} arquivos ...]", n=len(resultados) - 500))
    return "\n".join(linhas) if linhas else t("Nenhum arquivo encontrado.")


def _f_escrever_arquivo(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if p.is_dir():
        raise ErroFerramenta(t("O caminho é uma pasta."))
    antes = ""
    existia = p.exists()
    if existia:
        if str(p) not in ctx.lidos and str(p) not in ctx.criados and p.stat().st_size > 0:
            raise ErroFerramenta(t("Esse arquivo já existe e você ainda não o leu nesta tarefa. Leia antes de substituir."))
        try:
            antes, _ = _ler_texto(p)
        except ErroFerramenta:
            antes = ""
    _checkpoint(ctx, p)
    p.parent.mkdir(parents=True, exist_ok=True)
    conteudo = e["conteudo"]
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(conteudo)
    novo = not existia
    ctx.criados.add(str(p))
    ctx.lidos.add(str(p))
    rel = ctx.relativo(p)
    ctx.emitir({"tipo": "arquivo_mudou", "caminho": rel, "acao": "criou" if novo else "substituiu",
                "diff": _diff(antes, conteudo, rel)})
    linhas = conteudo.count("\n") + (1 if conteudo and not conteudo.endswith("\n") else 0)
    return (t("Criado: {caminho} ({n} linhas).", caminho=p, n=linhas) if novo
            else t("Substituído: {caminho} ({n} linhas).", caminho=p, n=linhas))


def _f_editar_arquivo(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if not p.is_file():
        raise ErroFerramenta(t("Arquivo não encontrado: {caminho}", caminho=p))
    if str(p) not in ctx.lidos and str(p) not in ctx.criados:
        raise ErroFerramenta(t("Leia o arquivo com ler_arquivo antes de editar."))
    texto, cod = _ler_texto(p)
    crlf = "\r\n" in texto
    base = texto.replace("\r\n", "\n") if crlf else texto
    atual = e["trecho_atual"].replace("\r\n", "\n") if crlf else e["trecho_atual"]
    novo = e["trecho_novo"].replace("\r\n", "\n") if crlf else e["trecho_novo"]
    if atual == novo:
        raise ErroFerramenta(t("trecho_atual e trecho_novo são iguais."))
    n = base.count(atual) if atual else 0
    if n == 0:
        raise ErroFerramenta(t("O trecho_atual não foi encontrado no arquivo. Confira espaços, acentos e quebras de linha (leia o arquivo de novo se ele pode ter mudado)."))
    if n > 1 and not e.get("trocar_todos"):
        raise ErroFerramenta(t("O trecho_atual aparece {n} vezes. Inclua mais linhas em volta para ele ficar único, ou use trocar_todos.", n=n))
    depois = base.replace(atual, novo) if e.get("trocar_todos") else base.replace(atual, novo, 1)
    _checkpoint(ctx, p)
    final = depois.replace("\n", "\r\n") if crlf else depois
    with open(p, "w", encoding="utf-8" if cod.startswith("utf-8") else cod, newline="") as f:
        f.write(final)
    rel = ctx.relativo(p)
    ctx.emitir({"tipo": "arquivo_mudou", "caminho": rel, "acao": "editou", "diff": _diff(base, depois, rel)})
    return t("Editado: {caminho} ({n} troca(s)).", caminho=p, n=n if e.get("trocar_todos") else 1)


def _shell() -> list[str]:
    if sys.platform == "win32":
        exe = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
        return [exe, "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command"]
    return [shutil.which("bash") or "/bin/sh", "-lc"]


_PREFIXO_PS = ("$ProgressPreference='SilentlyContinue';"
               "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false);"
               "$OutputEncoding=[System.Text.UTF8Encoding]::new($false);")


# ---------------- Job Object: a árvore inteira de um comando morre junto ----------------
# Todo comando roda dentro de um Job Object do Windows com KILL_ON_JOB_CLOSE: parar, estourar o tempo ou o Clave
# morrer à força (o Windows fecha o handle e mata o job) derruba o comando e tudo o que ele abriu, inclusive o neto
# que segurava a saída e deixava a thread de leitura presa para sempre. Parar um comando em segundo plano e o Clave
# fechar do jeito normal são com cuidado (console.encerrar_job_com_cuidado): morre o que não tem janela, e programas
# com janela que o comando abriu (o navegador de um vite --open, um editor) continuam abertos. BREAKAWAY_OK deixa sair
# do job só quem pede isso explicitamente ao criar o processo (sem ele, esse programa nem abriria).
_JOB_KILL_ON_CLOSE = 0x2000
_JOB_BREAKAWAY_OK = 0x0800

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)  # instância própria: os argtypes não vazam para outros módulos

    class _IoCounters(ctypes.Structure):
        _fields_ = [(n, ctypes.c_ulonglong) for n in ("ReadOperationCount", "WriteOperationCount",
                                                      "OtherOperationCount", "ReadTransferCount",
                                                      "WriteTransferCount", "OtherTransferCount")]

    class _LimitesBasicos(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class _LimitesEstendidos(ctypes.Structure):
        _fields_ = [("BasicLimitInformation", _LimitesBasicos), ("IoInfo", _IoCounters),
                    ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                    ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

    class _ListaPids(ctypes.Structure):
        _fields_ = [("NumberOfAssignedProcesses", wintypes.DWORD), ("NumberOfProcessIdsInList", wintypes.DWORD),
                    ("ProcessIdList", ctypes.c_size_t * 1024)]

    _k32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    _k32.CreateJobObjectW.restype = wintypes.HANDLE
    _k32.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
    _k32.SetInformationJobObject.restype = wintypes.BOOL
    _k32.QueryInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
                                               ctypes.POINTER(wintypes.DWORD))
    _k32.QueryInformationJobObject.restype = wintypes.BOOL
    _k32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _k32.AssignProcessToJobObject.restype = wintypes.BOOL
    _k32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _k32.TerminateJobObject.restype = wintypes.BOOL
    _k32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _k32.CloseHandle.restype = wintypes.BOOL
    _k32.OpenThread.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _k32.OpenThread.restype = wintypes.HANDLE
    _k32.CancelSynchronousIo.argtypes = (wintypes.HANDLE,)
    _k32.CancelSynchronousIo.restype = wintypes.BOOL


def _cancelar_leitura(leitor: threading.Thread, prazo: float = 3.0) -> bool:
    """Destrava a thread que lê a saída de um comando quando quem segura o cano é um programa com janela que fica
    aberto (o PowerShell passa a saída adiante para o que ele abre): o CancelSynchronousIo faz o ReadFile dela voltar
    com erro e a leitura acaba. Devolve se a thread terminou."""
    if not leitor.is_alive():
        return True
    if sys.platform != "win32" or not getattr(leitor, "native_id", None):
        return False
    h = _k32.OpenThread(0x0001, False, leitor.native_id)  # THREAD_TERMINATE: o que o CancelSynchronousIo pede
    if not h:
        return False
    try:
        fim = time.time() + prazo
        while leitor.is_alive() and time.time() < fim:
            _k32.CancelSynchronousIo(h)  # sem leitura pendente agora, não faz nada: tenta de novo
            leitor.join(0.1)
    finally:
        _k32.CloseHandle(h)
    return not leitor.is_alive()


class _Job:
    """Um Job Object do Windows. Fora do Windows (ou se a criação falhar) criar() devolve None e vale o taskkill."""

    def __init__(self, handle):
        self.h = handle
        self._trava = threading.Lock()

    @classmethod
    def criar(cls) -> "_Job | None":
        if sys.platform != "win32":
            return None
        h = _k32.CreateJobObjectW(None, None)
        if not h:
            return None
        job = cls(h)
        if not job._limites(_JOB_KILL_ON_CLOSE | _JOB_BREAKAWAY_OK):
            _k32.CloseHandle(h)
            return None
        return job

    def _limites(self, flags: int) -> bool:
        info = _LimitesEstendidos()
        info.BasicLimitInformation.LimitFlags = flags
        return bool(_k32.SetInformationJobObject(self.h, 9, ctypes.byref(info), ctypes.sizeof(info)))

    def colocar(self, proc: subprocess.Popen) -> bool:
        """Põe o processo no job. Chamado logo depois do Popen: o PowerShell leva uns décimos de segundo para
        carregar antes de rodar o comando, então nada que o comando abre nasce fora do job."""
        with self._trava:
            return bool(self.h) and bool(_k32.AssignProcessToJobObject(self.h, int(proc._handle)))

    def matar(self) -> None:
        with self._trava:
            if self.h:
                _k32.TerminateJobObject(self.h, 1)

    def encerrar_com_cuidado(self, raizes=()) -> list[int]:
        """Mata o que não tem janela (o terminal, um servidor) e deixa as janelas que o comando abriu; fechar o job
        depois não leva as janelas junto. Devolve os pids dos donos de janela que ficaram."""
        import console
        with self._trava:
            if not self.h:
                return []
            try:
                return console.encerrar_job_com_cuidado(self.h, raizes)
            except Exception:  # noqa: BLE001 (o cuidado falhou: tudo morre, como antes)
                _k32.TerminateJobObject(self.h, 1)
                return []

    def pids(self) -> list[int]:
        with self._trava:
            if not self.h:
                return []
            lista = _ListaPids()
            if not _k32.QueryInformationJobObject(self.h, 3, ctypes.byref(lista), ctypes.sizeof(lista), None):
                return []
            return [int(lista.ProcessIdList[i]) for i in range(min(lista.NumberOfProcessIdsInList, 1024))]

    def restantes(self, raizes=()) -> list[int]:
        """Os processos que ainda estão no job, fora o terminal e os consoles escondidos (que saem sozinhos)."""
        import console
        raizes = {int(r) for r in raizes if r}
        return [p for p in self.pids() if p not in raizes
                and console._nome_do_processo(p) not in console.AJUDANTES_DE_CONSOLE]

    def soltar(self) -> None:
        """Fecha o job sem matar quem sobrou (uma janela que o comando abriu de propósito, com Start-Process)."""
        with self._trava:
            if self.h:
                self._limites(_JOB_BREAKAWAY_OK)
                _k32.CloseHandle(self.h)
                self.h = None

    def fechar(self) -> None:
        """Fecha o job: o que ainda estiver nele morre (KILL_ON_JOB_CLOSE)."""
        with self._trava:
            if self.h:
                _k32.CloseHandle(self.h)
                self.h = None


def _matar(proc: subprocess.Popen, cuidado: bool = False) -> list[int]:
    """Derruba o comando e tudo o que ele abriu (pelo job; sem job, pelo taskkill da árvore). Com cuidado, os
    programas com janela que ele abriu ficam abertos; devolve os pids dos donos dessas janelas."""
    job = getattr(proc, "_clave_job", None)
    if job is not None:
        if cuidado:
            return job.encerrar_com_cuidado({proc.pid})
        job.matar()
        return []
    if proc.poll() is not None:
        return []
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True,
                           creationflags=0x08000000)
        else:
            proc.kill()
    except OSError:
        pass
    return []


# variáveis que não chegam aos comandos: as do Clave (CLAVE_*: a pasta de dados, o lançador e o token da ponte do
# navegador, que daria a qualquer comando o controle do navegador do app) e as que mudariam um programa do Electron
# aberto dali (o VS Code de um "code .", por exemplo); o mesmo filtro do console (console._ambiente)
_FORA_DO_AMBIENTE = ("ELECTRON_RUN_AS_NODE", "ELECTRON_NO_ATTACH_CONSOLE", "__PYVENV_LAUNCHER__")


def _ambiente_comando(sem_buffer: bool = False) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith("CLAVE_") and k.upper() not in _FORA_DO_AMBIENTE}
    # A saída do comando é lida como UTF-8 (o _PREFIXO_PS faz o mesmo com o PowerShell): sem isto, um script de
    # Python escrevendo num cano usa a página de código do Windows e os acentos chegam trocados ao Claude
    # (test_code.TestAmbiente confere). Diferente do console, que é da pessoa e não lê nada.
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if sem_buffer:  # o Python segura a saída quando ela vai para um cano: em segundo plano ela tem de chegar já
        env["PYTHONUNBUFFERED"] = "1"
    return env


def _iniciar_shell(comando: str, ctx: Contexto, *, sem_buffer: bool = False, **extra) -> subprocess.Popen:
    args = _shell()
    args.append((_PREFIXO_PS + comando) if sys.platform == "win32" else comando)
    env = _ambiente_comando(sem_buffer)
    flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
    try:
        proc = subprocess.Popen(args, cwd=str(ctx.raiz), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, env=env, creationflags=flags, **extra)
    except OSError as erro:
        raise ErroFerramenta(t("Não deu para iniciar o terminal: {erro}", erro=erro))
    job = _Job.criar()
    if job is not None and not job.colocar(proc):
        job.fechar()  # o processo já tinha terminado (ou não deu): sem job, vale o taskkill
        job = None
    proc._clave_job = job
    return proc


def _f_rodar_comando(e, ctx: Contexto):
    if e.get("em_segundo_plano"):
        return _rodar_em_segundo_plano(e, ctx)
    comando = e["comando"]
    limite = max(5, min(600, int(e.get("tempo_limite_s") or 120)))
    proc = _iniciar_shell(comando, ctx)
    job = proc._clave_job
    ctx.processo = proc
    partes: list[bytes] = []

    cano = getattr(proc.stdout, "raw", proc.stdout)  # leitura crua: destravar no meio não perde o que já veio

    def ler():
        try:
            for bloco in iter(lambda: cano.read(65536), b""):
                partes.append(bloco)
        except (OSError, ValueError):  # a leitura foi destravada (_cancelar_leitura): o que veio até aqui fica
            pass

    leitor = threading.Thread(target=ler, daemon=True)
    leitor.start()
    inicio = time.time()
    motivo = ""
    sobrou = ""
    while proc.poll() is None:
        if ctx.parar.is_set():
            motivo = t("parado pelo usuário")
            _matar(proc)
            break
        if time.time() - inicio > limite:
            motivo = t("passou do tempo limite de {n} s", n=limite)
            _matar(proc)
            break
        time.sleep(0.1)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _matar(proc)
    leitor.join(timeout=3)
    if leitor.is_alive() and job is not None:
        # O comando acabou, mas deixou um processo segurando a saída. Sem janela (um servidor, um neto), ele morre
        # junto (antes a leitura ficava presa para sempre). Com janela (um programa que o comando abriu para a
        # pessoa usar), ele continua aberto e quem para é a leitura.
        job.encerrar_com_cuidado({proc.pid})
        leitor.join(timeout=5)
        if leitor.is_alive():
            _cancelar_leitura(leitor)
        elif not motivo:
            sobrou = t("Aviso: o comando deixou um processo rodando que segurava a saída, e o Clave encerrou esse processo junto. Para deixar um servidor ou programa rodando, use em_segundo_plano.")
    if not leitor.is_alive():
        proc.stdout.close()
    elif not motivo:
        # sem job (fora do Windows): devolve o que veio até aqui
        motivo = t("o comando deixou um processo rodando em segundo plano")
    if job is not None:
        job.soltar()  # quem não segurava a saída (uma janela aberta com Start-Process) continua aberto
    ctx.processo = None
    saida = b"".join(partes).decode("utf-8", errors="replace").replace("\r\n", "\n")
    cab = t("Código de saída: {codigo}", codigo=proc.returncode)
    if motivo:
        cab += t(" (interrompido: {motivo})", motivo=motivo)
    corpo = _limitar(saida.strip()) if saida.strip() else t("(sem saída)")
    return f"{cab}\n{corpo}" + (f"\n\n{sobrou}" if sobrou else "")


# ---------------- comandos em segundo plano ----------------

MAX_SEGUNDO_PLANO = 5        # por conversa
ESPERA_SEGUNDO_PLANO = 6.0   # segundos que a ferramenta espera a saída assentar ou um endereço aparecer
VER_RESTANTES = 1.0          # segundos entre uma olhada e outra nos processos que sobraram depois do terminal sair


@dataclass
class _Fundo:
    tarefa: object
    proc: subprocess.Popen
    job: object
    conversa_id: str
    parado: bool = False
    leitor: threading.Thread | None = None
    terminal_saiu: bool = False   # o terminal saiu, mas sobraram processos no job (um Start-Process, por exemplo)
    restantes: int = 0            # quantos processos sobraram (fora os consoles escondidos)
    janelas: list = field(default_factory=list)   # os programas com janela que ficaram abertos ao parar
    acordar: threading.Event = field(default_factory=threading.Event)

    @property
    def rodando(self) -> bool:
        return self.tarefa.rodando


_fundos: dict[str, _Fundo] = {}
_trava_fundos = threading.Lock()
_atexit_registrado = [False]


def _acompanhar_restantes(f: _Fundo, codigo) -> None:
    """O terminal saiu, mas pode ter deixado processos no job (Start-Process -WindowStyle Hidden escapa da saída):
    a tarefa continua aberta, avisa no registro quantos são e espera eles terminarem ou alguém parar."""
    if f.job is None or f.parado:
        return
    restantes = f.job.restantes({f.proc.pid})
    if not restantes:
        return
    f.restantes = len(restantes)
    f.terminal_saiu = True
    f.tarefa.saida("\n" + t("[O terminal do comando saiu com o código {codigo}, mas {n} processo(s) que ele abriu continuam rodando. A tarefa segue aberta até eles terminarem ou alguém parar.]",
                            codigo=codigo, n=len(restantes)) + "\n")
    f.tarefa.atualizar(detalhe=t("{n} processo(s) que o comando abriu continuam rodando", n=len(restantes)))
    while not f.parado:
        f.acordar.wait(VER_RESTANTES)
        if f.parado:
            break
        restantes = f.job.restantes({f.proc.pid})
        if not restantes:
            break
        if len(restantes) != f.restantes:
            f.restantes = len(restantes)
            f.tarefa.atualizar(detalhe=t("{n} processo(s) que o comando abriu continuam rodando", n=len(restantes)))
    f.restantes = 0


def _ler_fundo(f: _Fundo) -> None:
    dec = codecs.getincrementaldecoder("utf-8")(errors="replace")
    try:
        while True:
            bloco = f.proc.stdout.read(65536)
            if not bloco:
                break
            f.tarefa.saida(dec.decode(bloco))
        f.tarefa.saida(dec.decode(b"", final=True))
    except (OSError, ValueError):
        pass
    finally:
        try:
            codigo = f.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # a saída fechou mas o terminal não: derruba (as janelas ficam)
            _matar(f.proc, cuidado=True)
            try:
                codigo = f.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                codigo = None
        try:
            f.proc.stdout.close()
        except OSError:
            pass
        f.tarefa.codigo = codigo
        try:
            _acompanhar_restantes(f, codigo)
        except Exception:  # noqa: BLE001 (acompanhar é extra: a tarefa termina de qualquer jeito)
            import traceback
            traceback.print_exc()
        if f.parado:
            detalhe = t("Parado antes de terminar")
            if f.janelas:
                detalhe += " " + t("({n} programa(s) com janela continuam abertos)", n=len(f.janelas))
            f.tarefa.terminar("parada", detalhe)
        else:
            f.tarefa.terminar("concluida" if codigo == 0 else "erro", t("Terminou com o código {codigo}", codigo=codigo))
        if f.job is not None:
            if f.parado:
                f.job.fechar()  # o encerramento com cuidado já tirou o KILL_ON_JOB_CLOSE: as janelas ficam
            else:
                f.job.soltar()


def _destravar_depois(f: _Fundo, espera: float = 1.5) -> None:
    """Depois de parar: se um programa com janela que ficou aberto herdou o cano da saída, a leitura não vê o fim
    sozinha. Espera um pouco e destrava, para a tarefa terminar como parada (num fio à parte: quem para não espera)."""
    leitor = f.leitor
    if leitor is None:
        return

    def destravar():
        leitor.join(espera)
        if leitor.is_alive():
            _cancelar_leitura(leitor)
    threading.Thread(target=destravar, daemon=True, name=f"destravar-{f.tarefa.id}").start()


def _parar_fundo(tid: str) -> bool:
    """Para um comando em segundo plano: o terminal e o que ele abriu sem janela morrem; janelas ficam abertas."""
    f = _fundos.get(tid)
    if f is None or not f.rodando:
        return False
    f.parado = True
    f.janelas = list(_matar(f.proc, cuidado=True) or [])
    f.acordar.set()
    _destravar_depois(f)
    return True


def encerrar_segundo_plano() -> None:
    """Para todos os comandos em segundo plano (o Clave fechando do jeito normal), com o mesmo cuidado de parar_comando:
    as janelas que eles abriram ficam abertas. Fechar à força derruba tudo: o Windows fecha o handle do job quando o
    processo do Clave morre, e o KILL_ON_JOB_CLOSE ainda está lá."""
    with _trava_fundos:
        fundos = list(_fundos.values())
    for f in fundos:
        if f.rodando:
            f.parado = True
            try:
                f.janelas = list(_matar(f.proc, cuidado=True) or [])
            except Exception:  # noqa: BLE001 (na saída do Clave, um comando não pode impedir o resto)
                pass
            f.acordar.set()
            _destravar_depois(f)


def _rodar_em_segundo_plano(e, ctx: Contexto):
    comando = e["comando"]
    dono = tarefas.conversa_dona(ctx.conversa_id)  # a etapa de um fluxo trabalha para a conversa principal
    with _trava_fundos:
        for tid in [k for k, f in _fundos.items() if not f.rodando and tarefas.pegar(k) is None]:
            _fundos.pop(tid, None)  # a tarefa já saiu da lista: esquece o processo
        ativos = [f for f in _fundos.values() if f.conversa_id == dono and f.rodando]
        if len(ativos) >= MAX_SEGUNDO_PLANO:
            lista = ", ".join(f.tarefa.id for f in ativos)
            raise ErroFerramenta(t("Esta conversa já tem {n} comandos rodando em segundo plano, o máximo. Pare um com parar_comando antes de começar outro ({lista}).",
                                   n=len(ativos), lista=lista))
        proc = _iniciar_shell(comando, ctx, sem_buffer=True, bufsize=0)
        holder = {}
        titulo = " ".join(str(e.get("descricao") or "").split()) or comando
        tarefa = tarefas.registrar("comando", titulo[:120], conversa_id=dono,
                                   parar=lambda: _parar_fundo(holder["id"]))
        holder["id"] = tarefa.id
        tarefa.comando = comando
        tarefa.pasta = str(ctx.raiz)
        f = _Fundo(tarefa=tarefa, proc=proc, job=proc._clave_job, conversa_id=dono)
        _fundos[tarefa.id] = f
    if not _atexit_registrado[0]:
        _atexit_registrado[0] = True
        atexit.register(encerrar_segundo_plano)
    f.leitor = threading.Thread(target=_ler_fundo, args=(f,), daemon=True, name=f"fundo-{tarefa.id}")
    f.leitor.start()

    # espera a saída assentar, um endereço aparecer ou o comando terminar (o que vier primeiro)
    inicio = time.time()
    while time.time() - inicio < ESPERA_SEGUNDO_PLANO:
        if not tarefa.rodando or ctx.parar.is_set():
            break
        if tarefa.urls:
            time.sleep(0.3)  # o resto da linha e as linhas logo depois do endereço
            break
        if f.terminal_saiu:  # o terminal já saiu: a saída do que sobrou não passa por aqui
            break
        if tarefa.bytes_saida and time.time() - tarefa.ultima_saida >= 1.5:
            break
        time.sleep(0.1)
    if ctx.parar.is_set() and tarefa.rodando:
        # a pessoa apertou Parar enquanto o comando começava: ele não fica rodando sozinho depois da resposta
        _parar_fundo(tarefa.id)
        f.leitor.join(timeout=8)
        return t("A resposta foi interrompida enquanto o comando começava, então parei o comando {id}.", id=tarefa.id)
    if not tarefa.rodando:
        f.leitor.join(timeout=2)
    saida = tarefa.registro(80).strip()
    if not tarefa.rodando:
        corpo = _limitar(saida) if saida else t("(o comando terminou sem nenhuma saída)")
        return (t("O comando terminou logo, com o código {codigo}; nada ficou rodando (id {id}).",
                  codigo=tarefa.codigo, id=tarefa.id) + "\n" + t("Saída:") + "\n" + corpo)
    corpo = _limitar(saida) if saida else t("(ainda sem saída)")
    partes = [t("Comando rodando em segundo plano (id {id}). Ele continua rodando depois desta resposta, aparece na aba Tarefas e o Clave encerra ele quando fechar.",
                id=tarefa.id)]
    if f.terminal_saiu:
        partes.append(t("O terminal do comando já saiu, mas {n} processo(s) que ele abriu continuam rodando dentro dele (um Start-Process, por exemplo). A saída deles não chega aqui; o Clave acompanha esses processos e encerra eles com parar_comando.",
                        n=f.restantes))
    if tarefa.urls:
        partes.append(t("Endereço local encontrado na saída: {urls}", urls=", ".join(tarefa.urls)))
    partes.append(t("Saída até agora:") + "\n" + corpo)
    partes.append(t("Para ver a saída mais recente, use ver_comando com este id; para encerrar, parar_comando."))
    return "\n".join(partes)


def _fundo_da_conversa(e, ctx: Contexto) -> _Fundo:
    tid = str(e.get("id") or "").strip()
    dono = tarefas.conversa_dona(ctx.conversa_id)
    f = _fundos.get(tid)
    if f is None or f.conversa_id != dono:
        with _trava_fundos:
            meus = [x.tarefa for x in _fundos.values() if x.conversa_id == dono]
        lista = ", ".join(f"{x.id} ({t('rodando') if x.rodando else t('terminado')})" for x in meus) or t("nenhum")
        raise ErroFerramenta(t("Não achei um comando em segundo plano com o id \"{id}\" nesta conversa. Os desta conversa: {lista}.",
                               id=tid, lista=lista))
    return f


def _duracao(segundos: float) -> str:
    s = int(max(0, segundos))
    if s < 60:
        return t("{n} s", n=s)
    if s < 3600:
        return t("{m} min {s} s", m=s // 60, s=f"{s % 60:02d}")
    return t("{h} h {m} min", h=s // 3600, m=f"{(s % 3600) // 60:02d}")


def _f_ver_comando(e, ctx: Contexto):
    f = _fundo_da_conversa(e, ctx)
    tf = f.tarefa
    linhas = max(1, min(400, int(e.get("linhas") or 60)))
    if tf.rodando and f.terminal_saiu:
        estado = t("o terminal saiu, mas {n} processo(s) que ele abriu continuam rodando, há {tempo}",
                   n=f.restantes, tempo=_duracao(time.time() - tf.inicio))
    elif tf.rodando:
        estado = t("ainda rodando, há {tempo}", tempo=_duracao(time.time() - tf.inicio))
    elif tf.status == "parada":
        estado = t("parado")
    else:
        estado = t("terminou com o código {codigo}", codigo=tf.codigo)
    partes = [t("Comando {id}: {estado}.", id=tf.id, estado=estado), t("Comando: {comando}", comando=tf.comando)]
    if tf.urls:
        partes.append(t("Endereço local: {urls}", urls=", ".join(tf.urls)))
    saida = tf.registro(linhas).strip()
    partes.append(t("Últimas {n} linhas da saída:", n=linhas) + "\n" + (_limitar(saida) if saida else t("(sem saída)")))
    return "\n".join(partes)


def _f_parar_comando(e, ctx: Contexto):
    f = _fundo_da_conversa(e, ctx)
    if not f.rodando:
        return t("O comando {id} já tinha terminado.", id=f.tarefa.id)
    _parar_fundo(f.tarefa.id)
    if f.leitor is not None:
        f.leitor.join(timeout=8)
    if f.rodando:
        return t("Pedi para o comando {id} parar, mas ele ainda não terminou. Confira com ver_comando.", id=f.tarefa.id)
    if f.janelas:
        return t("Parei o comando {id} e o que ele abriu sem janela; {n} programa(s) com janela que ele abriu continuam abertos.",
                 id=f.tarefa.id, n=len(f.janelas))
    return t("Parei o comando {id} e tudo o que ele abriu.", id=f.tarefa.id)


def _f_excel_ler(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    try:
        texto = excel.ler(p, e.get("aba"), e.get("intervalo"), int(e.get("max_linhas") or 100))
    except excel.ErroExcel as erro:
        raise ErroFerramenta(str(erro))
    ctx.lidos.add(str(p))
    return _limitar(texto)


def _f_excel_alterar(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if e.get("saida"):  # trabalha numa cópia: a original fica intacta
        saida = ctx.resolver(e["saida"])
        if ctx.protegido(saida):
            raise ErroFerramenta(t("O arquivo de saída está na lista de protegidos."))
        _checkpoint(ctx, saida)
        if p.is_file():
            shutil.copy2(p, saida)
        p = saida
    existia = p.exists()
    _checkpoint(ctx, p)
    try:
        resumo = excel.aplicar(p, e.get("operacoes") or [], criar=True)
    except excel.ErroExcel as erro:
        raise ErroFerramenta(str(erro))
    ctx.criados.add(str(p))
    ctx.lidos.add(str(p))
    ctx.emitir({"tipo": "arquivo_mudou", "caminho": ctx.relativo(p), "acao": "editou" if existia else "criou",
                "diff": "\n".join("+ " + l for l in resumo.splitlines()[1:])})
    return resumo


def _f_excel_no_app(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    saida = ctx.resolver(e["saida"]) if e.get("saida") else None
    if saida is not None:
        if ctx.protegido(saida):
            raise ErroFerramenta(t("O arquivo de saída está na lista de protegidos."))
        _checkpoint(ctx, saida)
    if e.get("acao") == "recalcular":
        _checkpoint(ctx, p)
    elif saida is None:
        _checkpoint(ctx, p.with_suffix(".pdf" if e.get("acao") == "pdf" else ".xlsx"))
    try:
        return excel.no_excel(p, e.get("acao", ""), saida)
    except excel.ErroExcel as erro:
        raise ErroFerramenta(str(erro))


def _f_excel_abrir(e, ctx: Contexto):
    try:
        return excel.abrir_no_excel(ctx.resolver(e["caminho"]))
    except (excel.ErroExcel, OSError) as erro:
        raise ErroFerramenta(str(erro))


def _f_mostrar_arquivo(e, ctx: Contexto):
    p = ctx.resolver(e.get("caminho", ""))
    if not p.is_file():
        raise ErroFerramenta(t("Arquivo não encontrado: {caminho}", caminho=ctx.relativo(p)))
    if p.stat().st_size > anexos.LIMITE_MOSTRAR:
        raise ErroFerramenta(t("Arquivo grande demais para mostrar na conversa (o limite é 100 MB)."))
    reg = anexos.salvar_mostrado(p.name, p.read_bytes(), origem=f"mostrado:{ctx.ferramenta_id}")
    # a tela acha o arquivo pelo id no resultado (como nas planilhas geradas)
    return t("Mostrei {nome} para a pessoa na conversa (id {id}).", nome=p.name, id=reg["id"])


def _f_word_ler(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if not p.is_file():
        raise ErroFerramenta(t("Arquivo não encontrado: {caminho}", caminho=ctx.relativo(p)))
    try:
        texto = word.ler(p)
    except word.ErroWord as erro:
        raise ErroFerramenta(str(erro))
    ctx.lidos.add(str(p))
    return texto


def _f_word_criar(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if p.suffix.lower() != ".docx":
        raise ErroFerramenta(t("Use um nome terminado em .docx."))
    existia = p.exists()
    _checkpoint(ctx, p)
    resumo = word.criar(p, str(e.get("conteudo") or ""))
    ctx.criados.add(str(p))
    ctx.lidos.add(str(p))
    ctx.emitir({"tipo": "arquivo_mudou", "caminho": ctx.relativo(p), "acao": "editou" if existia else "criou", "diff": ""})
    return resumo


def _f_word_alterar(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if not p.is_file():
        raise ErroFerramenta(t("Arquivo não encontrado: {caminho}", caminho=ctx.relativo(p)))
    if e.get("saida"):
        saida = ctx.resolver(e["saida"])
        if ctx.protegido(saida):
            raise ErroFerramenta(t("O arquivo de saída está na lista de protegidos."))
        _checkpoint(ctx, saida)
        shutil.copy2(p, saida)
        p = saida
    else:
        _checkpoint(ctx, p)
    try:
        resumo = word.trocar(p, [x for x in (e.get("trocas") or []) if isinstance(x, dict)])
    except word.ErroWord as erro:
        raise ErroFerramenta(str(erro))
    ctx.emitir({"tipo": "arquivo_mudou", "caminho": ctx.relativo(p), "acao": "editou",
                "diff": "\n".join(f"- {x.get('de', '')}\n+ {x.get('para', '')}" for x in (e.get("trocas") or []) if isinstance(x, dict))})
    return resumo


def _f_word_no_app(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if not p.is_file():
        raise ErroFerramenta(t("Arquivo não encontrado: {caminho}", caminho=ctx.relativo(p)))
    saida = ctx.resolver(e["saida"]) if e.get("saida") else p.with_suffix(".pdf")
    if ctx.protegido(saida):
        raise ErroFerramenta(t("O arquivo de saída está na lista de protegidos."))
    _checkpoint(ctx, saida)
    try:
        return word.para_pdf(p, saida)
    except word.ErroWord as erro:
        raise ErroFerramenta(str(erro))


def _f_email_salvar_anexo(e, ctx: Contexto):
    nome = Path(str(e.get("anexo") or "")).name
    if not nome:
        raise ErroFerramenta(t("Diga o nome do anexo."))
    destino = ctx.resolver(e.get("caminho") or nome)
    if destino.is_dir():
        destino = destino / nome
    _checkpoint(ctx, destino)
    try:
        return femail.salvar_anexo(str(e.get("id") or ""), nome, destino)
    except femail.ErroEmail as erro:
        raise ErroFerramenta(str(erro))


def _f_atualizar_tarefas(e, ctx: Contexto):
    tarefas = []
    for tf in e.get("tarefas") or []:
        if isinstance(tf, dict) and tf.get("texto"):
            estado = tf.get("estado") if tf.get("estado") in ("pendente", "fazendo", "feito") else "pendente"
            tarefas.append({"texto": str(tf["texto"])[:200], "estado": estado})
    ctx.tarefas = tarefas
    ctx.emitir({"tipo": "tarefas", "tarefas": tarefas})
    return t("Lista de tarefas atualizada.")


def _f_usar_skill(e, ctx: Contexto):
    s = contexto_pasta.conteudo_skill(ctx.skills, str(e.get("nome", "")).strip().lstrip("/"))
    if not s:
        nomes = ", ".join(x["nome"] for x in ctx.skills) or t("nenhuma")
        raise ErroFerramenta(t("Skill não encontrada. Disponíveis: {nomes}", nomes=nomes))
    return t("Skill \"{nome}\" (arquivos da skill em {pasta}; caminhos relativos citados nela partem de lá ou da raiz da pasta onde ela mora).\n\n{conteudo}", nome=s["nome"], pasta=s["pasta"], conteudo=s["texto"])


def validar(nome: str, entrada) -> str | None:
    """Confere a entrada contra o esquema da ferramenta. Devolve o erro, ou None se estiver certa."""
    f = FERRAMENTAS.get(nome)
    if not f:
        return t("ferramenta desconhecida")
    if not isinstance(entrada, dict):
        return t("a entrada não é um objeto")
    esquema = f["def"]["input_schema"]
    for campo in esquema.get("required", []):
        if campo not in entrada:
            return t("faltou o campo obrigatório '{campo}'", campo=campo)
    tipos = {"string": str, "integer": int, "boolean": bool, "array": list, "object": dict}
    for campo, valor in entrada.items():
        spec = esquema["properties"].get(campo)
        if spec is None:
            continue
        esperado = tipos.get(spec.get("type"))
        if esperado is int and isinstance(valor, bool):
            return t("o campo '{campo}' devia ser número", campo=campo)
        if esperado and not isinstance(valor, esperado):
            if esperado is int and isinstance(valor, str) and valor.isdigit():
                entrada[campo] = int(valor)
                continue
            return t("o campo '{campo}' veio com o tipo errado", campo=campo)
    return None
