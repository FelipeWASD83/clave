"""Memória entre conversas, no mesmo esquema do Claude Code: vários .md, um por assunto, e um índice.

O Claude enxerga a pasta dados/memoria como /memories (ferramenta memory_20250818
da Anthropic). O índice /memories/MEMORY.md entra sozinho no começo de cada
conversa; os arquivos de assunto ele lê quando o assunto aparece. Tudo é texto
que a pessoa vê, edita e apaga em Configurações > Memória.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from config import DADOS
from i18n import t

DEFINICAO = {"type": "memory_20250818", "name": "memory"}
INDICE = "MEMORY.md"
LIMITE_INDICE = 12_000

def instrucoes() -> str:
    """Como usar a memória (vai no prompt de sistema), no idioma escolhido. Os nomes dos campos do cabeçalho e os
    tipos ficam iguais nos dois idiomas: são o formato que a tela de Memória lê."""
    return "\n".join([
        t("Você tem uma memória que dura entre conversas, guardada em arquivos Markdown no diretório /memories (ferramenta memory). Funciona assim:"),
        t("- /memories/MEMORY.md é o índice: uma linha por arquivo, no formato `- [Título](arquivo.md): resumo de uma linha`. O conteúdo atual dele está logo abaixo; não precisa ler de novo."),
        t("- Cada assunto fica num arquivo próprio, /memories/<assunto-em-minusculas-com-hifen>.md, que começa com este cabeçalho e depois traz o conteúdo, curto e direto:"),
        "  ---",
        t("  nome: título curto"),
        t("  descricao: uma linha dizendo quando esta memória é útil"),
        "  tipo: sobre-voce | preferencia | projeto | referencia",
        "  ---",
        t("- Quando o assunto da conversa tiver um arquivo no índice, leia o arquivo antes de responder."),
        t("- Guarde o que vai ser útil em conversas futuras: quem a pessoa é, como ela gosta que você trabalhe (inclusive correções que ela fez), projetos, decisões e onde achar as coisas. Não guarde o que só importa nesta conversa."),
        t("- Antes de criar um arquivo, confira se já existe um sobre o mesmo assunto e atualize esse. Informação nova que contradiz a antiga substitui a antiga; memória que se mostrou errada é apagada. Sempre que criar, renomear ou apagar um arquivo, atualize o MEMORY.md."),
        t("- Se a pessoa pedir para lembrar ou esquecer algo, faça na hora e confirme."),
        t("- Nunca guarde senhas, chaves, tokens, números de documento ou de cartão."),
        t("- Consultar e atualizar a memória é rotina silenciosa: não diga que vai olhar a memória nem que olhou. Só comente quando a pessoa pedir para lembrar ou esquecer algo, ou quando perguntar o que você sabe sobre ela."),
    ])


class ErroMemoria(Exception):
    pass


def raiz() -> Path:
    p = DADOS / "memoria"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _resolver(caminho: str) -> Path:
    c = (caminho or "").replace("\\", "/").strip()
    if not c.startswith("/memories"):
        raise ErroMemoria(t("O caminho precisa começar com /memories"))
    rel = c[len("/memories"):].lstrip("/")
    base = raiz().resolve()
    alvo = (base / rel).resolve()
    if alvo != base and not alvo.is_relative_to(base):
        raise ErroMemoria(t("Caminho fora de /memories"))
    return alvo


def _virtual(p: Path) -> str:
    rel = p.resolve().relative_to(raiz().resolve()).as_posix()
    return "/memories" + ("/" + rel if rel and rel != "." else "")


def texto_indice() -> str:
    arq = raiz() / INDICE
    try:
        texto = arq.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if len(texto) > LIMITE_INDICE:
        texto = texto[:LIMITE_INDICE] + "\n" + t("[... índice cortado: está grande demais, resuma-o ...]")
    return texto


def instrucoes_completas() -> str:
    indice = texto_indice()
    return instrucoes() + t("\n\nÍndice atual da memória (/memories/MEMORY.md):\n{indice}",
                            indice=indice or t("(vazio: nada guardado ainda)"))


def executar(entrada: dict) -> str:
    cmd = entrada.get("command")
    if cmd == "view":
        p = _resolver(entrada.get("path", "/memories"))
        if p.is_dir():
            itens = sorted(p.rglob("*"))
            linhas = [t("Conteúdo de {caminho}:", caminho=_virtual(p))]
            for i in itens:
                if i.is_file():
                    linhas.append(f"- {_virtual(i)} ({i.stat().st_size} bytes)")
            if len(linhas) == 1:
                linhas.append(t("(vazio)"))
            return "\n".join(linhas)
        if not p.is_file():
            raise ErroMemoria(t("Não existe: {caminho}", caminho=entrada.get("path")))
        linhas = p.read_text(encoding="utf-8").splitlines()
        faixa = entrada.get("view_range")
        ini = 1
        if isinstance(faixa, list) and len(faixa) == 2:
            ini = max(1, int(faixa[0]))
            fim = len(linhas) if int(faixa[1]) == -1 else int(faixa[1])
            linhas = linhas[ini - 1:fim]
        return "\n".join(f"{n:>6}\t{l}" for n, l in enumerate(linhas, ini)) or t("(arquivo vazio)")
    if cmd == "create":
        p = _resolver(entrada.get("path", ""))
        if p == raiz().resolve():
            raise ErroMemoria(t("Informe um arquivo dentro de /memories"))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(entrada.get("file_text", ""), encoding="utf-8")
        return t("Arquivo criado: {caminho}", caminho=_virtual(p))
    if cmd == "str_replace":
        p = _resolver(entrada.get("path", ""))
        if not p.is_file():
            raise ErroMemoria(t("Não existe: {caminho}", caminho=entrada.get("path")))
        texto = p.read_text(encoding="utf-8")
        velho = entrada.get("old_str", "")
        n = texto.count(velho) if velho else 0
        if n != 1:
            raise ErroMemoria(t("O texto a trocar precisa aparecer exatamente uma vez") +
                              (t(" (aparece {n})", n=n) if n else ""))
        p.write_text(texto.replace(velho, entrada.get("new_str", ""), 1), encoding="utf-8")
        return t("Arquivo editado: {caminho}", caminho=_virtual(p))
    if cmd == "insert":
        p = _resolver(entrada.get("path", ""))
        if not p.is_file():
            raise ErroMemoria(t("Não existe: {caminho}", caminho=entrada.get("path")))
        linhas = p.read_text(encoding="utf-8").splitlines()
        pos = max(0, min(len(linhas), int(entrada.get("insert_line", 0))))
        linhas[pos:pos] = str(entrada.get("insert_text", "")).splitlines()
        p.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        return t("Texto inserido em {caminho}", caminho=_virtual(p))
    if cmd == "delete":
        p = _resolver(entrada.get("path", ""))
        if p == raiz().resolve():
            raise ErroMemoria(t("Não dá para apagar a pasta /memories inteira"))
        if p.is_dir():
            shutil.rmtree(p)
        elif p.is_file():
            p.unlink()
        else:
            raise ErroMemoria(t("Não existe: {caminho}", caminho=entrada.get("path")))
        return t("Apagado: {caminho}", caminho=entrada.get("path"))
    if cmd == "rename":
        de = _resolver(entrada.get("old_path", ""))
        para = _resolver(entrada.get("new_path", ""))
        if not de.exists():
            raise ErroMemoria(t("Não existe: {caminho}", caminho=entrada.get("old_path")))
        if para.exists():
            raise ErroMemoria(t("Já existe: {caminho}", caminho=entrada.get("new_path")))
        para.parent.mkdir(parents=True, exist_ok=True)
        de.rename(para)
        return t("Renomeado para {caminho}", caminho=_virtual(para))
    raise ErroMemoria(t("Comando desconhecido: {cmd}", cmd=cmd))


_FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def _cabecalho(texto: str) -> tuple[dict, str]:
    m = _FRONT.match(texto)
    if not m:
        return {}, texto
    dados = {}
    for linha in m.group(1).splitlines():
        if ":" in linha:
            k, v = linha.split(":", 1)
            dados[k.strip().lower()] = v.strip()
    return dados, texto[m.end():]


def listar() -> list[dict]:
    saida = []
    for p in sorted(raiz().rglob("*")):
        if not p.is_file():
            continue
        texto = p.read_text(encoding="utf-8", errors="replace")
        cab, corpo = _cabecalho(texto)
        saida.append({
            "caminho": _virtual(p), "texto": texto, "tamanho": p.stat().st_size,
            "indice": p.name == INDICE and p.parent.resolve() == raiz().resolve(),
            "nome": cab.get("nome") or cab.get("name") or p.stem, "descricao": cab.get("descricao") or cab.get("description") or "",
            "tipo": cab.get("tipo") or cab.get("type") or "", "corpo": corpo.strip(),
        })
    saida.sort(key=lambda a: (not a["indice"], a["tipo"], a["nome"].lower()))
    return saida


def gravar(caminho: str, texto: str) -> None:
    p = _resolver(caminho)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texto, encoding="utf-8")


def apagar(caminho: str) -> None:
    p = _resolver(caminho)
    if p.is_file():
        p.unlink()
