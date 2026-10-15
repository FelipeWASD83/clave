"""Word (.docx) sem dependência: ler, criar, trocar texto e exportar PDF pelo Word instalado.

Um .docx é um zip com XML. Ler e criar usam só a biblioteca padrão (zipfile e xml), de propósito: a biblioteca
python-docx precisa do lxml, que tem parte nativa e pode ser barrada pelo Smart App Control. O PDF sai pelo Word
instalado (automação do Windows, como o Excel em excel.py).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from i18n import t

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS = {"w": W}
LIMITE_LEITURA = 60_000


class ErroWord(Exception):
    pass


def word_instalado() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application"))
        return True
    except OSError:
        return False


# ---------------- ler ----------------

def _texto_paragrafo(p) -> str:
    partes = []
    for no in p.iter():
        if no.tag == f"{{{W}}}t":
            partes.append(no.text or "")
        elif no.tag == f"{{{W}}}tab":
            partes.append("\t")
        elif no.tag in (f"{{{W}}}br", f"{{{W}}}cr"):
            partes.append("\n")
    return "".join(partes)


def ler(caminho: Path) -> str:
    try:
        with zipfile.ZipFile(caminho) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError):
        raise ErroWord(t("Este arquivo não é um .docx válido (se for .doc antigo, abra no Word e salve como .docx)."))
    corpo = ET.fromstring(xml).find("w:body", _NS)
    linhas = []
    for bloco in corpo:
        if bloco.tag == f"{{{W}}}p":
            estilo = bloco.find("w:pPr/w:pStyle", _NS)
            nome = (estilo.get(f"{{{W}}}val") or "") if estilo is not None else ""
            texto = _texto_paragrafo(bloco)
            m = re.match(r"(?:Heading|Ttulo|T[ií]tulo)(\d)", nome)
            linhas.append(("#" * int(m.group(1)) + " " + texto) if m and texto else texto)
        elif bloco.tag == f"{{{W}}}tbl":
            for i, tr in enumerate(bloco.findall("w:tr", _NS)):
                celulas = [_texto_paragrafo(tc).replace("\n", " ").strip() for tc in tr.findall("w:tc", _NS)]
                linhas.append("| " + " | ".join(celulas) + " |")
                if i == 0:
                    linhas.append("|" + "---|" * len(celulas))
            linhas.append("")
    texto = "\n".join(linhas).strip()
    if len(texto) > LIMITE_LEITURA:
        texto = texto[:LIMITE_LEITURA] + "\n" + t("[... cortado: o documento é longo ...]")
    return texto or t("(documento vazio)")


# ---------------- criar ----------------

def _runs(texto: str) -> str:
    """Texto com **negrito** e *itálico* em runs do Word."""
    saida = []
    for parte in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", texto):
        if not parte:
            continue
        if parte.startswith("**") and parte.endswith("**"):
            saida.append(f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{escape(parte[2:-2])}</w:t></w:r>')
        elif parte.startswith("*") and parte.endswith("*") and len(parte) > 2:
            saida.append(f'<w:r><w:rPr><w:i/></w:rPr><w:t xml:space="preserve">{escape(parte[1:-1])}</w:t></w:r>')
        else:
            saida.append(f'<w:r><w:t xml:space="preserve">{escape(parte)}</w:t></w:r>')
    return "".join(saida)


def _p(texto: str, estilo: str | None = None, alinhar: str | None = None) -> str:
    ppr = ""
    if estilo or alinhar:
        ppr = "<w:pPr>" + (f'<w:pStyle w:val="{estilo}"/>' if estilo else "") + (f'<w:jc w:val="{alinhar}"/>' if alinhar else "") + "</w:pPr>"
    return f"<w:p>{ppr}{_runs(texto)}</w:p>"


def _tabela(linhas: list[list[str]]) -> str:
    borda = '<w:top w:val="single" w:sz="4" w:color="999999"/><w:left w:val="single" w:sz="4" w:color="999999"/><w:bottom w:val="single" w:sz="4" w:color="999999"/><w:right w:val="single" w:sz="4" w:color="999999"/><w:insideH w:val="single" w:sz="4" w:color="999999"/><w:insideV w:val="single" w:sz="4" w:color="999999"/>'
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>{borda}</w:tblBorders></w:tblPr>']
    for i, linha in enumerate(linhas):
        xml.append("<w:tr>")
        for c in linha:
            txt = f"**{c}**" if i == 0 and c else c
            xml.append(f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>{_p(txt)}</w:tc>')
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    return "".join(xml)


def _corpo(conteudo: str) -> str:
    """Markdown simples (títulos #, listas - e 1., tabelas |, **negrito**) em XML do Word."""
    xml, tabela = [], []
    for linha in (conteudo or "").replace("\r\n", "\n").split("\n"):
        s = linha.rstrip()
        if s.strip().startswith("|") and s.strip().endswith("|"):
            celulas = [c.strip() for c in s.strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in celulas):
                tabela.append(celulas)
            continue
        if tabela:
            xml.append(_tabela(tabela))
            tabela = []
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            xml.append(_p(m.group(2), f"Heading{len(m.group(1))}"))
        elif re.match(r"^\s*[-*•]\s+", s):
            xml.append(_p("•\t" + re.sub(r"^\s*[-*•]\s+", "", s), "Lista"))
        elif re.match(r"^\s*\d+[.)]\s+", s):
            xml.append(_p(s.strip(), "Lista"))
        elif s.strip() == "---":
            xml.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        else:
            xml.append(_p(s))
    if tabela:
        xml.append(_tabela(tabela))
    return "".join(xml)


_ESTILOS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="22"/><w:lang w:val="pt-BR"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/><w:color w:val="1F3B57"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="80"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="1F3B57"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:keepNext/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:sz w:val="23"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Lista"><w:name w:val="Lista"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="60"/><w:ind w:left="360" w:hanging="360"/></w:pPr></w:style>
</w:styles>"""

_TIPOS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""

_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

_DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def criar(caminho: Path, conteudo: str) -> str:
    documento = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}"><w:body>'
                 + _corpo(conteudo)
                 + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1418" w:right="1418" w:bottom="1418" '
                   'w:left="1418" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr></w:body></w:document>')
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _TIPOS)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/_rels/document.xml.rels", _DOC_RELS)
        z.writestr("word/document.xml", documento)
        z.writestr("word/styles.xml", _ESTILOS)
    return t("Documento do Word criado: {caminho}", caminho=caminho)


# ---------------- trocar texto ----------------

def trocar(caminho: Path, trocas: list[dict]) -> str:
    """Troca trechos de texto mantendo a formatação. Cada troca procura dentro de um parágrafo: junta o texto dos
    pedaços (runs), troca e devolve o resultado ao primeiro pedaço que tinha o trecho."""
    try:
        with zipfile.ZipFile(caminho) as z:
            partes = {n: z.read(n) for n in z.namelist()}
    except zipfile.BadZipFile:
        raise ErroWord(t("Este arquivo não é um .docx válido."))
    ET.register_namespace("w", W)
    contagem = {}
    for nome in [n for n in partes if re.fullmatch(r"word/(document|header\d*|footer\d*)\.xml", n)]:
        texto_xml = partes[nome].decode("utf-8")
        for tr in trocas:
            de, para = str(tr.get("de") or ""), str(tr.get("para") or "")
            if not de:
                continue
            # caso simples: o trecho inteiro dentro de um <w:t>
            n_antes = texto_xml.count(escape(de))
            texto_xml = texto_xml.replace(escape(de), escape(para))
            contagem[de] = contagem.get(de, 0) + n_antes
        partes[nome] = texto_xml.encode("utf-8")
    faltou = [de for de, n in contagem.items() if n == 0]
    if contagem and len(faltou) == len(contagem):
        raise ErroWord(t("Nenhum trecho encontrado. Leia o documento com word_ler e copie o trecho exato (o Word às vezes quebra uma frase em pedaços com formatação diferente)."))
    tmp = caminho.with_suffix(".tmp.docx")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, dados in partes.items():
            z.writestr(n, dados)
    os.replace(tmp, caminho)
    feitas = sum(n for n in contagem.values())
    aviso = t(" Não achados (copie o trecho exato do word_ler): {lista}", lista="; ".join(faltou)) if faltou else ""
    return t("{n} troca(s) feita(s) em {caminho}.", n=feitas, caminho=caminho) + aviso


# ---------------- PDF pelo Word ----------------

_PS = r"""
$ErrorActionPreference = 'Stop'
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
  $d = $w.Documents.Open($env:CLAVE_WORD_ENTRADA, $false, $true)
  $d.ExportAsFixedFormat($env:CLAVE_WORD_SAIDA, 17)
  $d.Close($false)
  'ok'
} finally { $w.Quit() }
"""


def para_pdf(caminho: Path, saida: Path | None = None, tempo: int = 180) -> str:
    if not word_instalado():
        raise ErroWord(t("O Microsoft Word não está instalado neste computador, então não dá para exportar PDF por ele."))
    saida = saida or caminho.with_suffix(".pdf")
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8-sig") as f:
        f.write(_PS)
        script = f.name
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", script],
                           capture_output=True, text=True, timeout=tempo, creationflags=0x08000000,
                           env=dict(os.environ, CLAVE_WORD_ENTRADA=str(caminho), CLAVE_WORD_SAIDA=str(saida)))
    except subprocess.TimeoutExpired:
        raise ErroWord(t("O Word demorou demais para responder (ele pode estar esperando alguma janela aberta)."))
    finally:
        os.unlink(script)
    if r.returncode != 0 or "ok" not in r.stdout:
        erro = (r.stderr or r.stdout).strip().splitlines()
        raise ErroWord(t("O Word não conseguiu: {erro}", erro=(erro[0] if erro else t("erro desconhecido"))[:300]))
    return t("PDF exportado: {caminho}", caminho=saida)
