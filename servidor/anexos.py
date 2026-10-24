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


# A API só aceita imagem de até 8000 px, e de até 2000 px quando o pedido tem mais de 20 imagens (as de resultados de
# ferramenta e as de turnos antigos contam). Passou disso, ela recusa o pedido inteiro, em toda mensagem seguinte.
MUITAS_IMAGENS = 20
LADO_MAXIMO_COM_MUITAS = 2000


def dimensoes(dados: bytes) -> tuple[int, int] | None:
    """(largura, altura) de PNG, JPEG, GIF ou WebP lidas do cabeçalho; None se não deu para saber."""
    try:
        if dados[:8] == b"\x89PNG\r\n\x1a\n":
            return int.from_bytes(dados[16:20], "big"), int.from_bytes(dados[20:24], "big")
        if dados[:6] in (b"GIF87a", b"GIF89a"):
            return int.from_bytes(dados[6:8], "little"), int.from_bytes(dados[8:10], "little")
        if dados[:4] == b"RIFF" and dados[8:12] == b"WEBP":
            tipo = dados[12:16]
            if tipo == b"VP8X":
                return 1 + int.from_bytes(dados[24:27], "little"), 1 + int.from_bytes(dados[27:30], "little")
            if tipo == b"VP8L":
                bits = int.from_bytes(dados[21:25], "little")
                return 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF)
            if tipo == b"VP8 ":
                return int.from_bytes(dados[26:28], "little") & 0x3FFF, int.from_bytes(dados[28:30], "little") & 0x3FFF
        if dados[:3] == b"\xff\xd8\xff":
            i = 2
            while i + 9 < len(dados):
                if dados[i] != 0xFF:
                    i += 1
                    continue
                marca = dados[i + 1]
                if marca in (0xD8, 0x01) or 0xD0 <= marca <= 0xD7 or marca == 0xFF:
                    i += 1 if marca == 0xFF else 2
                    continue
                tam = int.from_bytes(dados[i + 2:i + 4], "big")
                if 0xC0 <= marca <= 0xCF and marca not in (0xC4, 0xC8, 0xCC):
                    return int.from_bytes(dados[i + 7:i + 9], "big"), int.from_bytes(dados[i + 5:i + 7], "big")
                i += 2 + tam
    except (IndexError, ValueError):
        pass
    return None


def _dimensoes_do_base64(dados_b64: str) -> tuple[int, int] | None:
    for pedaco in (400_000, len(dados_b64)):  # o JPEG guarda o tamanho depois de blocos que podem ser grandes
        trecho = dados_b64[:pedaco]
        try:
            d = dimensoes(base64.b64decode(trecho[:len(trecho) // 4 * 4]))
        except ValueError:
            return None
        if d:
            return d
        if pedaco >= len(dados_b64):
            break
    return None


def _contar_imagens(blocos) -> int:
    n = 0
    for b in blocos if isinstance(blocos, list) else []:
        if isinstance(b, dict):
            if b.get("type") == "image":
                n += 1
            elif b.get("type") == "tool_result":
                n += _contar_imagens(b.get("content"))
    return n


def _tirar_grandes(blocos):
    saida = []
    for b in blocos:
        if isinstance(b, dict) and b.get("type") == "image" and isinstance(b.get("source"), dict) \
                and b["source"].get("type") == "base64":
            d = _dimensoes_do_base64(str(b["source"].get("data") or ""))
            if d is None or max(d) > LADO_MAXIMO_COM_MUITAS:
                tam = f"{d[0]} x {d[1]}" if d else "?"
                saida.append({"type": "text", "text": t("[Imagem antiga de {tamanho} px tirada daqui: a API só aceita imagem de até {limite} px quando a conversa tem mais de {n} imagens. Se precisar dela, leia o arquivo de novo.]",
                                                         tamanho=tam, limite=LADO_MAXIMO_COM_MUITAS, n=MUITAS_IMAGENS)})
            else:
                saida.append(b)
        elif isinstance(b, dict) and b.get("type") == "tool_result" and isinstance(b.get("content"), list):
            saida.append({**b, "content": _tirar_grandes(b["content"])})
        else:
            saida.append(b)
    return saida


def limitar_imagens_grandes(mensagens: list[dict]) -> list[dict]:
    """Com mais de 20 imagens no pedido, troca por um aviso de texto as que passam de 2000 px de lado.

    Só olha o tamanho quando passa de 20 imagens; o que foi guardado não é mexido (devolve cópias)."""
    if sum(_contar_imagens(m.get("content")) for m in mensagens) <= MUITAS_IMAGENS:
        return mensagens
    return [{**m, "content": _tirar_grandes(m["content"])} if isinstance(m.get("content"), list) else m
            for m in mensagens]


def reduzir_imagem(dados: bytes, lado: int = LADO_MAXIMO_COM_MUITAS) -> bytes:
    """Imagem com lado maior que `lado` volta menor (mesmo formato, PNG para GIF), pelo System.Drawing do Windows.

    Se não der para reduzir (sem Windows, WebP, arquivo estranho), devolve os bytes como vieram."""
    import subprocess
    import tempfile
    d = dimensoes(dados)
    tipo = tipo_imagem(dados)
    if not d or max(d) <= lado or tipo in (None, "image/webp"):
        return dados
    jpeg = tipo == "image/jpeg"
    with tempfile.TemporaryDirectory() as tmp:
        entrada, saida = Path(tmp) / "entrada", Path(tmp) / "saida"
        entrada.write_bytes(dados)
        def q(x):
            return "'" + str(x).replace("'", "''") + "'"
        roteiro = (
            "Add-Type -AssemblyName System.Drawing;"
            f"$i=[System.Drawing.Image]::FromFile({q(entrada)});$e=[Math]::Min(1.0,{int(lado)}/[Math]::Max($i.Width,$i.Height));"
            "$w=[int][Math]::Max(1,[Math]::Floor($i.Width*$e));$h=[int][Math]::Max(1,[Math]::Floor($i.Height*$e));"
            "$b=New-Object System.Drawing.Bitmap $w,$h;$g=[System.Drawing.Graphics]::FromImage($b);"
            "$g.InterpolationMode='HighQualityBicubic';$g.DrawImage($i,0,0,$w,$h);"
            f"$b.Save({q(saida)},[System.Drawing.Imaging.ImageFormat]::{'Jpeg' if jpeg else 'Png'});"
            "$g.Dispose();$b.Dispose();$i.Dispose()")
        try:
            r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", roteiro],
                               capture_output=True, timeout=40, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            novo = saida.read_bytes() if r.returncode == 0 and saida.is_file() else b""
        except (OSError, subprocess.SubprocessError):
            return dados
    return novo if novo and len(novo) <= 5 * 1024 * 1024 and tipo_imagem(novo) else dados


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
