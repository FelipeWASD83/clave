"""Ferramentas do modo Code: ler, buscar, escrever, editar e rodar comando na pasta de trabalho.

Cada ferramenta diz o próprio risco ("leitura", "escrita", "comando"); quem
decide se roda sozinha, se pergunta ou se recusa é `classificar`, a partir do
modo de permissão escolhido na conversa.
"""
from __future__ import annotations

import base64
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

import banco
import contexto_pasta
from ferramentas import excel

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
    skills: list = field(default_factory=list)
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
        "Não use para ler ou editar arquivos: para isso existem ferramentas próprias.",
        {"comando": {"type": "string"},
         "descricao": {"type": "string", "description": "Uma frase curta, em português simples, do que o comando faz."},
         "tempo_limite_s": {"type": "integer", "description": "Segundos até desistir (padrão 120, máximo 600)."}},
        ["comando", "descricao"], "comando"),
    "atualizar_tarefas": _ferramenta(
        "atualizar_tarefas",
        "Mostra ao usuário a sua lista de passos da tarefa atual. Use em tarefas com 3 passos ou mais: crie a "
        "lista no começo e atualize conforme avança (só um passo 'fazendo' por vez).",
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
    defs = [f["def"] for nome, f in FERRAMENTAS.items() if nome != "usar_skill"]
    if com_skills:
        defs.append(FERRAMENTAS["usar_skill"]["def"])
    return defs


# ---------------- permissão ----------------

def classificar(nome: str, entrada: dict, ctx: Contexto, modo: str, liberados: set) -> tuple[str, str]:
    """Devolve ("auto" | "perguntar" | "negar", motivo)."""
    f = FERRAMENTAS.get(nome)
    if not f:
        return "negar", "ferramenta desconhecida"
    risco = f["risco"]
    if nome in ("atualizar_tarefas", "usar_skill"):
        return "auto", ""

    alvos = []
    for campo in ("caminho", "saida"):
        if isinstance(entrada.get(campo), str) and entrada.get(campo):
            alvo = ctx.resolver(entrada[campo])
            regra = ctx.protegido(alvo)
            if regra:
                return "negar", f"o caminho está na lista de arquivos protegidos ({regra})"
            alvos.append(alvo)

    if nome == "excel_abrir" and alvos and alvos[0].suffix.lower() not in ABRIVEIS:
        return "negar", "só dá para abrir planilha (.xlsx, .csv), PDF, imagem ou texto; outros tipos podem executar programas"

    if risco == "comando":
        cmd = str(entrada.get("comando", ""))
        if modo == "plano":
            return "negar", "o modo Plano só lê; troque o modo para rodar comandos"
        if perigoso(cmd):
            return "perguntar", "comando que pode apagar ou publicar algo"
        citado = _cita_protegido(cmd, ctx.protegidos)
        if citado:
            return "perguntar", f"o comando cita um arquivo protegido ({citado})"
        if modo == "livre" or "comando" in liberados:
            return "auto", ""
        return "perguntar", "rodar comando"

    if any(not ctx.dentro(a) for a in alvos):
        if risco == "escrita" and modo == "plano":
            return "negar", "o modo Plano só lê"
        return "perguntar", "caminho fora da pasta de trabalho"

    if risco == "leitura":
        return "auto", ""
    if modo == "plano":
        return "negar", "o modo Plano só lê; troque o modo para editar arquivos"
    if modo in ("aceitar_edicoes", "livre") or "escrita" in liberados:
        return "auto", ""
    return "perguntar", "mudar arquivo"


# ---------------- execução ----------------

def _numerar(linhas: list[str], inicio: int) -> str:
    saida = []
    for i, linha in enumerate(linhas, start=inicio):
        if len(linha) > 2000:
            linha = linha[:2000] + "… [linha cortada]"
        saida.append(f"{i:>6}\t{linha}")
    return "\n".join(saida)


def _ler_texto(p: Path) -> tuple[str, str]:
    dados = p.read_bytes()
    if b"\x00" in dados[:8192]:
        raise ErroFerramenta("O arquivo parece binário; não dá para ler como texto.")
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
    return texto[:meio] + f"\n\n[... {len(texto) - LIMITE_SAIDA} caracteres cortados ...]\n\n" + texto[-meio:]


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
        raise ErroFerramenta(f"Ferramenta desconhecida: {nome}")
    return fn(entrada, ctx)


def _f_listar_pasta(e, ctx: Contexto):
    base = ctx.resolver(e.get("caminho") or ".")
    if not base.is_dir():
        raise ErroFerramenta(f"Não é uma pasta: {base}")
    prof = max(1, min(3, int(e.get("profundidade") or 1)))
    linhas, total = [], 0

    def andar(d: Path, nivel: int, prefixo: str):
        nonlocal total
        try:
            itens = sorted(d.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except OSError as erro:
            linhas.append(f"{prefixo}[sem acesso: {erro.strerror}]")
            return
        for item in itens:
            if total >= 400:
                return
            total += 1
            if item.is_dir():
                pulada = item.name in IGNORAR_PASTAS
                linhas.append(f"{prefixo}{item.name}/" + ("  (ignorada)" if pulada else ""))
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
        linhas.append("[... lista cortada em 400 itens ...]")
    return f"{base}\n" + ("\n".join(linhas) if linhas else "(pasta vazia)")


def _tam(n: int) -> str:
    for un in ("B", "KB", "MB", "GB"):
        if n < 1024 or un == "GB":
            return f"{n:.0f} {un}" if un == "B" else f"{n:.1f} {un}"
        n /= 1024
    return str(n)


def _f_ler_arquivo(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if not p.is_file():
        raise ErroFerramenta(f"Arquivo não encontrado: {p}")
    ext = p.suffix.lower()
    if ext in IMAGENS:
        dados = p.read_bytes()
        if len(dados) > 5 * 1024 * 1024:
            raise ErroFerramenta("Imagem maior que 5 MB; reduza antes (por exemplo, com um script Python).")
        ctx.lidos.add(str(p))
        return [{"type": "text", "text": f"Imagem: {p}"},
                {"type": "image", "source": {"type": "base64", "media_type": IMAGENS[ext],
                                             "data": base64.b64encode(dados).decode("ascii")}}]
    if ext == ".pdf":
        dados = p.read_bytes()
        if len(dados) > 30 * 1024 * 1024:
            raise ErroFerramenta("PDF maior que 30 MB.")
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
        return f"{p}\n(arquivo vazio)"
    rodape = ""
    if inicio - 1 + qtd < len(linhas):
        rodape = f"\n\n[o arquivo tem {len(linhas)} linhas; leia o resto com linha_inicial={inicio + qtd}]"
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
        raise ErroFerramenta(f"Expressão regular inválida: {erro}")
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
            achados.append(f"[... parei em {limite} resultados ...]")
            break
    return "\n".join(achados) if achados else "Nenhum resultado."


def _f_achar_arquivos(e, ctx: Contexto):
    base = ctx.resolver(e.get("caminho") or ".")
    padrao = e["padrao"].replace("\\", "/")
    resultados = []
    if ".." in padrao.split("/"):
        raise ErroFerramenta("O padrão não pode subir de pasta (..). Use o parâmetro caminho para procurar em outro lugar.")
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
            raise ErroFerramenta(f"Padrão inválido: {erro}")
    resultados = sorted(set(resultados), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    linhas = [ctx.relativo(p) for p in resultados[:500]]
    if len(resultados) > 500:
        linhas.append(f"[... mais {len(resultados) - 500} arquivos ...]")
    return "\n".join(linhas) if linhas else "Nenhum arquivo encontrado."


def _f_escrever_arquivo(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if p.is_dir():
        raise ErroFerramenta("O caminho é uma pasta.")
    antes = ""
    existia = p.exists()
    if existia:
        if str(p) not in ctx.lidos and str(p) not in ctx.criados and p.stat().st_size > 0:
            raise ErroFerramenta("Esse arquivo já existe e você ainda não o leu nesta tarefa. Leia antes de substituir.")
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
    return f"{'Criado' if novo else 'Substituído'}: {p} ({linhas} linhas)."


def _f_editar_arquivo(e, ctx: Contexto):
    p = ctx.resolver(e["caminho"])
    if not p.is_file():
        raise ErroFerramenta(f"Arquivo não encontrado: {p}")
    if str(p) not in ctx.lidos and str(p) not in ctx.criados:
        raise ErroFerramenta("Leia o arquivo com ler_arquivo antes de editar.")
    texto, cod = _ler_texto(p)
    crlf = "\r\n" in texto
    base = texto.replace("\r\n", "\n") if crlf else texto
    atual = e["trecho_atual"].replace("\r\n", "\n") if crlf else e["trecho_atual"]
    novo = e["trecho_novo"].replace("\r\n", "\n") if crlf else e["trecho_novo"]
    if atual == novo:
        raise ErroFerramenta("trecho_atual e trecho_novo são iguais.")
    n = base.count(atual) if atual else 0
    if n == 0:
        raise ErroFerramenta("O trecho_atual não foi encontrado no arquivo. Confira espaços, acentos e quebras de "
                             "linha (leia o arquivo de novo se ele pode ter mudado).")
    if n > 1 and not e.get("trocar_todos"):
        raise ErroFerramenta(f"O trecho_atual aparece {n} vezes. Inclua mais linhas em volta para ele ficar único, "
                             "ou use trocar_todos.")
    depois = base.replace(atual, novo) if e.get("trocar_todos") else base.replace(atual, novo, 1)
    _checkpoint(ctx, p)
    final = depois.replace("\n", "\r\n") if crlf else depois
    with open(p, "w", encoding="utf-8" if cod.startswith("utf-8") else cod, newline="") as f:
        f.write(final)
    rel = ctx.relativo(p)
    ctx.emitir({"tipo": "arquivo_mudou", "caminho": rel, "acao": "editou", "diff": _diff(base, depois, rel)})
    return f"Editado: {p} ({n if e.get('trocar_todos') else 1} troca(s))."


def _shell() -> list[str]:
    if sys.platform == "win32":
        exe = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
        return [exe, "-NoLogo", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command"]
    return [shutil.which("bash") or "/bin/sh", "-lc"]


_PREFIXO_PS = ("$ProgressPreference='SilentlyContinue';"
               "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false);"
               "$OutputEncoding=[System.Text.UTF8Encoding]::new($false);")


def _matar(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True,
                           creationflags=0x08000000)
        else:
            proc.kill()
    except OSError:
        pass


def _f_rodar_comando(e, ctx: Contexto):
    comando = e["comando"]
    limite = max(5, min(600, int(e.get("tempo_limite_s") or 120)))
    args = _shell()
    if sys.platform == "win32":
        args.append(_PREFIXO_PS + comando)
    else:
        args.append(comando)
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
    try:
        proc = subprocess.Popen(args, cwd=str(ctx.raiz), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, env=env, creationflags=flags)
    except OSError as erro:
        raise ErroFerramenta(f"Não deu para iniciar o terminal: {erro}")
    ctx.processo = proc
    partes: list[bytes] = []

    def ler():
        for bloco in iter(lambda: proc.stdout.read(4096), b""):
            partes.append(bloco)

    leitor = threading.Thread(target=ler, daemon=True)
    leitor.start()
    inicio = time.time()
    motivo = ""
    while proc.poll() is None:
        if ctx.parar.is_set():
            motivo = "parado pelo usuário"
            _matar(proc)
            break
        if time.time() - inicio > limite:
            motivo = f"passou do tempo limite de {limite} s"
            _matar(proc)
            break
        time.sleep(0.1)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        _matar(proc)
    leitor.join(timeout=3)
    if not leitor.is_alive():
        proc.stdout.close()
    elif not motivo:
        # um processo que o comando deixou em segundo plano segura a saída: devolve o que veio até aqui
        motivo = "o comando deixou um processo rodando em segundo plano"
    ctx.processo = None
    saida = b"".join(partes).decode("utf-8", errors="replace").replace("\r\n", "\n")
    cab = f"Código de saída: {proc.returncode}"
    if motivo:
        cab += f" (interrompido: {motivo})"
    corpo = _limitar(saida.strip()) if saida.strip() else "(sem saída)"
    return f"{cab}\n{corpo}"


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
            raise ErroFerramenta("O arquivo de saída está na lista de protegidos.")
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


def _f_atualizar_tarefas(e, ctx: Contexto):
    tarefas = []
    for t in e.get("tarefas") or []:
        if isinstance(t, dict) and t.get("texto"):
            estado = t.get("estado") if t.get("estado") in ("pendente", "fazendo", "feito") else "pendente"
            tarefas.append({"texto": str(t["texto"])[:200], "estado": estado})
    ctx.tarefas = tarefas
    ctx.emitir({"tipo": "tarefas", "tarefas": tarefas})
    return "Lista de tarefas atualizada."


def _f_usar_skill(e, ctx: Contexto):
    s = contexto_pasta.conteudo_skill(ctx.skills, str(e.get("nome", "")).strip().lstrip("/"))
    if not s:
        nomes = ", ".join(x["nome"] for x in ctx.skills) or "nenhuma"
        raise ErroFerramenta(f"Skill não encontrada. Disponíveis: {nomes}")
    return (f"Skill \"{s['nome']}\" (arquivos da skill em {s['pasta']}; caminhos relativos citados nela partem de lá "
            f"ou da raiz da pasta onde ela mora).\n\n{s['texto']}")


def validar(nome: str, entrada) -> str | None:
    """Confere a entrada contra o esquema da ferramenta. Devolve o erro, ou None se estiver certa."""
    f = FERRAMENTAS.get(nome)
    if not f:
        return "ferramenta desconhecida"
    if not isinstance(entrada, dict):
        return "a entrada não é um objeto"
    esquema = f["def"]["input_schema"]
    for campo in esquema.get("required", []):
        if campo not in entrada:
            return f"faltou o campo obrigatório '{campo}'"
    tipos = {"string": str, "integer": int, "boolean": bool, "array": list, "object": dict}
    for campo, valor in entrada.items():
        spec = esquema["properties"].get(campo)
        if spec is None:
            continue
        esperado = tipos.get(spec.get("type"))
        if esperado is int and isinstance(valor, bool):
            return f"o campo '{campo}' devia ser número"
        if esperado and not isinstance(valor, esperado):
            if esperado is int and isinstance(valor, str) and valor.isdigit():
                entrada[campo] = int(valor)
                continue
            return f"o campo '{campo}' veio com o tipo errado"
    return None
