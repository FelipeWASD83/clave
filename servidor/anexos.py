"""Arquivos anexados (no chat ou nos projetos) e como eles viram blocos da API.

O arquivo fica em dados/anexos/<id> e a mensagem guarda só uma referência
({"type": "clave_anexo", "id": ...}). Na hora do pedido a referência vira o
bloco de verdade (imagem, PDF ou texto) com os mesmos bytes de sempre, o que
mantém o cache e o raciocínio das respostas anteriores válidos.
"""
from __future__ import annotations

import base64
import mimetypes
from pathlib import Path

import banco
from config import DADOS
from i18n import t

IMAGENS = {"image/png", "image/jpeg", "image/gif", "image/webp"}
MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
LIMITE_BYTES = 30 * 1024 * 1024
LIMITE_MOSTRAR = 100 * 1024 * 1024  # o que o Claude mostra na conversa (vídeo pesa mais)
MIDIA = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".m4v": "video/mp4",
         ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg", ".m4a": "audio/mp4",
         ".flac": "audio/flac", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
         ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
EXT_TEXTO = {
    ".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".jsonl", ".xml", ".html", ".htm", ".css", ".js", ".mjs",
    ".ts", ".tsx", ".jsx", ".py", ".gml", ".java", ".c", ".h", ".cpp", ".hpp", ".cs", ".go", ".rs", ".rb", ".php",
    ".sh", ".ps1", ".bat", ".cmd", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".sql", ".log", ".srt",
    ".vtt", ".tex", ".svg", ".kt", ".swift", ".lua", ".r", ".m", ".vue", ".svelte", ".env.example",
}


def pasta() -> Path:
    p = DADOS / "anexos"
    p.mkdir(parents=True, exist_ok=True)
    return p


def caminho(aid: str) -> Path:
    return pasta() / aid


def tipo_de(nome: str, dados: bytes) -> str:
    if dados[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if dados[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if dados[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
        return "image/webp"
    if dados[:5] == b"%PDF-":
        return "application/pdf"
    ext = Path(nome).suffix.lower()
    if dados[:4] == b"PK\x03\x04" and ext in (".xlsx", ".xlsm"):
        return MIME_XLSX
    if ext == ".xls" and dados[:8] == bytes.fromhex("d0cf11e0a1b11ae1"):
        return "application/vnd.ms-excel"
    if ext in EXT_TEXTO or _parece_texto(dados):
        return "text/plain"
    return mimetypes.guess_type(nome)[0] or "application/octet-stream"


def _parece_texto(dados: bytes) -> bool:
    amostra = dados[:4096]
    if b"\x00" in amostra:
        return False
    try:
        amostra.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def salvar(nome: str, dados: bytes, projeto_id=None, origem="upload") -> dict:
    if len(dados) > LIMITE_BYTES:
        raise ValueError(t("Arquivo grande demais (o limite é 30 MB)."))
    tipo = tipo_de(nome, dados)
    if tipo == "application/vnd.ms-excel":
        nome, dados = _converter_xls(nome, dados)
        tipo = MIME_XLSX
    if tipo not in IMAGENS and tipo not in ("application/pdf", "text/plain", MIME_XLSX):
        raise ValueError(t("Esse tipo de arquivo não dá para mandar ao Claude. Mande imagem (PNG, JPG, GIF, WebP), PDF, planilha do Excel (.xlsx) ou arquivo de texto e código."))
    reg = banco.registrar_anexo(nome, tipo, len(dados), projeto_id=projeto_id, origem=origem)
    caminho(reg["id"]).write_bytes(dados)
    return reg


def _converter_xls(nome: str, dados: bytes) -> tuple[str, bytes]:
    """Planilha .xls antiga vira .xlsx pelo Excel do computador (o openpyxl não lê .xls)."""
    import tempfile
    from ferramentas import excel
    if not excel.excel_instalado():
        raise ValueError(t("Planilha .xls (formato antigo): abra no Excel e salve como .xlsx antes de mandar."))
    with tempfile.TemporaryDirectory() as tmp:
        entrada = Path(tmp) / "planilha.xls"
        entrada.write_bytes(dados)
        saida = entrada.with_suffix(".xlsx")
        try:
            excel.no_excel(entrada, "converter_xlsx", saida)
        except excel.ErroExcel as e:
            raise ValueError(t("Não deu para converter a planilha .xls: {erro}", erro=e))
        return Path(nome).with_suffix(".xlsx").name, saida.read_bytes()


def salvar_mostrado(nome: str, dados: bytes, origem: str = "mostrado") -> dict:
    """Uma cópia do arquivo que o Claude mostrou na conversa. Não vai para o Claude: aceita qualquer tipo."""
    if len(dados) > LIMITE_MOSTRAR:
        raise ValueError(t("Arquivo grande demais para mostrar na conversa (o limite é 100 MB)."))
    tipo = MIDIA.get(Path(nome).suffix.lower()) or tipo_de(nome, dados)
    reg = banco.registrar_anexo(nome, tipo, len(dados), origem=origem)
    caminho(reg["id"]).write_bytes(dados)
    return reg


def apagar(aid: str) -> None:
    try:
        caminho(aid).unlink()
    except OSError:
        pass
    banco.apagar_anexo(aid)


def referencia(reg: dict) -> dict:
    return {"type": "clave_anexo", "id": reg["id"], "nome": reg["nome"], "tipo": reg["tipo"]}


def expandir(bloco: dict) -> dict:
    """Troca a referência pelo bloco que a API entende."""
    aid = bloco["id"]
    reg = banco.anexo(aid) or {"nome": bloco.get("nome", "arquivo"), "tipo": bloco.get("tipo", "text/plain")}
    try:
        dados = caminho(aid).read_bytes()
    except OSError:
        return {"type": "text", "text": t("[O anexo \"{nome}\" não existe mais no computador.]", nome=reg["nome"])}
    tipo = reg["tipo"]
    if tipo in IMAGENS:
        return {"type": "image", "source": {"type": "base64", "media_type": tipo,
                                             "data": base64.b64encode(dados).decode("ascii")}}
    if tipo == "application/pdf":
        return {"type": "document", "title": reg["nome"],
                "source": {"type": "base64", "media_type": "application/pdf",
                           "data": base64.b64encode(dados).decode("ascii")}}
    if tipo == MIME_XLSX:
        return {"type": "text", "text": _planilha_como_texto(aid, reg, dados)}
    texto = dados.decode("utf-8", errors="replace")
    return {"type": "document", "title": reg["nome"],
            "source": {"type": "text", "media_type": "text/plain", "data": texto or " "}}


def tipo_imagem(dados: bytes) -> str | None:
    """O tipo de verdade de uma imagem, lido dos primeiros bytes (a extensão do arquivo pode mentir)."""
    tipo = tipo_de("", dados[:16])
    return tipo if tipo in IMAGENS else None


def _tipo_do_base64(dados_b64: str) -> str | None:
    try:
        return tipo_imagem(base64.b64decode(dados_b64[:24] + "=" * (-len(dados_b64[:24]) % 4)))
    except (ValueError, TypeError):
        return None


def corrigir_imagens(blocos):
    """Acerta o media_type de cada imagem pelo conteúdo, inclusive dentro de resultados de ferramenta.

    A API recusa o pedido inteiro quando o tipo declarado não bate com a imagem (um JPEG salvo como .png, por
    exemplo), e como a imagem fica no histórico o erro se repetia a cada mensagem. Imagem que não é imagem de
    verdade vira um aviso de texto. Não mexe no que foi guardado: devolve cópias."""
    if not isinstance(blocos, list):
        return blocos
    saida = []
    for b in blocos:
        if isinstance(b, dict) and b.get("type") == "image" and isinstance(b.get("source"), dict) \
                and b["source"].get("type") == "base64":
            tipo = _tipo_do_base64(str(b["source"].get("data") or ""))
            if tipo is None:
                saida.append({"type": "text", "text": t("[Uma imagem que a API não aceitaria foi tirada daqui.]")})
            elif tipo != b["source"].get("media_type"):
                saida.append({**b, "source": {**b["source"], "media_type": tipo}})
            else:
                saida.append(b)
        elif isinstance(b, dict) and b.get("type") == "tool_result" and isinstance(b.get("content"), list):
            saida.append({**b, "content": corrigir_imagens(b["content"])})
        else:
            saida.append(b)
    return saida


def expandir_conteudo(conteudo) -> list | str:
    if isinstance(conteudo, str):
        return conteudo
    saida = []
    for b in conteudo:
        if isinstance(b, dict) and b.get("type") == "clave_anexo":
            saida.append(expandir(b))
        else:
            saida.append(b)
    return corrigir_imagens(saida)


def _planilha_como_texto(aid: str, reg: dict, dados: bytes) -> str:
    import tempfile
    from ferramentas import excel
    with tempfile.TemporaryDirectory() as tmp:
        arq = Path(tmp) / (Path(reg["nome"]).stem + ".xlsx")
        arq.write_bytes(dados)
        try:
            conteudo = excel.ler(arq, max_linhas=60)
        except excel.ErroExcel as e:
            conteudo = t("(não deu para ler: {erro})", erro=e)
    return (t("<planilha anexada id=\"{id}\" nome=\"{nome}\">\n{conteudo}\n</planilha>", id=aid, nome=reg["nome"],
              conteudo=conteudo) + "\n"
            + t("(Para ver outras abas ou mais linhas, use planilha_ler com anexo_id \"{id}\". Para devolver uma versão alterada, use planilha_criar com base_anexo_id \"{id}\".)", id=aid))
