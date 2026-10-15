"""Conector de e-mail: ler, enviar e salvar anexos.

Dois jeitos de ligar (Configurações > Conectores > E-mail):
- IMAP e SMTP com senha de app (Gmail, Yahoo, Zoho e provedores de hospedagem). A senha fica no segredos (DPAPI).
- O Outlook clássico instalado no computador, por automação do Windows (COM): serve para Outlook.com e
  Microsoft 365, que não aceitam mais senha por IMAP. O Outlook novo não tem essa automação.

Ler é livre; enviar sempre pede o OK de quem usa (a não ser uma regra de permitir escrita para isso:
Email(enviar)). Os ids das mensagens são o UID do IMAP ou o EntryID do Outlook.
"""
from __future__ import annotations

import email
import email.policy
import imaplib
import json
import os
import re
import smtplib
import subprocess
import sys
import tempfile
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.utils import parseaddr
from pathlib import Path

import config
import segredos
from i18n import t

NOMES = ("email_ler", "email_enviar")
SEGREDO = "email:senha"
LIMITE_CORPO = 20_000
PROVEDORES = {
    "gmail": {"imap": "imap.gmail.com", "imap_porta": 993, "smtp": "smtp.gmail.com", "smtp_porta": 465},
    "yahoo": {"imap": "imap.mail.yahoo.com", "imap_porta": 993, "smtp": "smtp.mail.yahoo.com", "smtp_porta": 465},
    "zoho": {"imap": "imap.zoho.com", "imap_porta": 993, "smtp": "smtp.zoho.com", "smtp_porta": 465},
}


class ErroEmail(Exception):
    pass


def configuracao() -> dict:
    return dict(config.carregar().get("email") or {})


def ligado() -> bool:
    c = configuracao()
    return bool(c.get("ligado")) and (c.get("tipo") == "outlook" or (c.get("endereco") and segredos.existe(SEGREDO)))


def outlook_instalado() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg
        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Outlook.Application"))
        return True
    except OSError:
        return False


def definicoes() -> list[dict]:
    return [
        {"name": "email_ler", "eager_input_streaming": True,
         "description": "Lê o e-mail da pessoa (a caixa que ela ligou no Clave). Sem id, lista as mensagens mais novas (remetente, assunto, data e um trecho), com filtros; com id, traz a mensagem inteira e a lista de anexos. Ler não marca como lida.",
         "input_schema": {"type": "object", "properties": {
             "id": {"type": "string", "description": "O id de uma mensagem da lista, para ler inteira."},
             "buscar": {"type": "string", "description": "Texto para procurar no assunto ou no corpo."},
             "remetente": {"type": "string", "description": "Só de quem tem este endereço ou nome."},
             "nao_lidas": {"type": "boolean", "description": "Só as não lidas."},
             "desde": {"type": "string", "description": "Só a partir desta data (AAAA-MM-DD)."},
             "limite": {"type": "integer", "description": "Quantas trazer (padrão 15, máximo 50)."}}}},
        {"name": "email_enviar", "eager_input_streaming": True,
         "description": "Envia um e-mail pela conta da pessoa. Ela sempre vê o e-mail inteiro e aprova antes de sair. Escreva o texto pronto, no tom certo, sem inventar fatos, preços ou prazos.",
         "input_schema": {"type": "object", "properties": {
             "para": {"type": "string", "description": "Destinatários, separados por vírgula."},
             "cc": {"type": "string"},
             "assunto": {"type": "string"},
             "corpo": {"type": "string", "description": "O texto do e-mail."},
             "anexos": {"type": "array", "items": {"type": "string"}, "description": "Caminhos de arquivos da pasta de trabalho (só no modo Code)."},
             "responder_a": {"type": "string", "description": "O id da mensagem que este e-mail responde (opcional)."}},
             "required": ["para", "assunto", "corpo"]}},
    ]


# ---------------- IMAP e SMTP ----------------

def _dec(valor) -> str:
    try:
        return str(make_header(decode_header(valor or "")))
    except Exception:
        return str(valor or "")


def _imap(c: dict) -> imaplib.IMAP4_SSL:
    senha = segredos.ler(SEGREDO)
    if not senha:
        raise ErroEmail(t("A senha do e-mail não está salva. Vá em Configurações > Conectores > E-mail."))
    try:
        m = imaplib.IMAP4_SSL(c.get("imap") or "", int(c.get("imap_porta") or 993), timeout=30)
        m.login(c.get("endereco") or "", senha)
    except imaplib.IMAP4.error as e:
        raise ErroEmail(t("O servidor de e-mail recusou o login ({erro}). Confira o endereço e a senha de app.", erro=str(e)[:200]))
    except OSError as e:
        raise ErroEmail(t("Não deu para falar com o servidor de e-mail ({erro}).", erro=str(e)[:200]))
    return m


def _texto(msg: email.message.EmailMessage) -> str:
    corpo = msg.get_body(preferencelist=("plain", "html"))
    if corpo is None:
        return ""
    texto = corpo.get_content()
    if corpo.get_content_type() == "text/html":
        texto = re.sub(r"(?is)<(script|style).*?</\1>", "", texto)
        texto = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>", "\n", texto)
        texto = re.sub(r"<[^>]+>", "", texto)
        texto = re.sub(r"&nbsp;", " ", texto)
        texto = re.sub(r"\n\s*\n+", "\n\n", texto)
    return texto.strip()


def _anexos(msg: email.message.EmailMessage) -> list[dict]:
    saida = []
    for parte in msg.iter_attachments():
        nome = parte.get_filename()
        if nome:
            dados = parte.get_payload(decode=True) or b""
            saida.append({"nome": _dec(nome), "tamanho": len(dados), "tipo": parte.get_content_type()})
    return saida


def _criterios(e: dict) -> list:
    crit = []
    if e.get("nao_lidas"):
        crit.append("UNSEEN")
    if e.get("desde"):
        import datetime
        try:
            d = datetime.date.fromisoformat(str(e["desde"]))
            crit += ["SINCE", d.strftime("%d-%b-%Y")]
        except ValueError:
            raise ErroEmail(t("Data inválida em desde (use AAAA-MM-DD)."))
    if e.get("remetente"):
        crit += ["FROM", str(e["remetente"])]
    if e.get("buscar"):
        crit += ["TEXT", str(e["buscar"])]
    return crit or ["ALL"]


def _imap_ler(c: dict, e: dict) -> str:
    m = _imap(c)
    try:
        m.select("INBOX", readonly=True)
        if e.get("id"):
            tipo, dados = m.uid("fetch", str(e["id"]), "(BODY.PEEK[])")
            if tipo != "OK" or not dados or not isinstance(dados[0], tuple):
                raise ErroEmail(t("Mensagem não encontrada: {id}", id=e["id"]))
            msg = email.message_from_bytes(dados[0][1], policy=email.policy.default)
            return json.dumps({"id": str(e["id"]), "de": _dec(msg["From"]), "para": _dec(msg["To"]), "cc": _dec(msg["Cc"]),
                               "data": str(msg["Date"] or ""), "assunto": _dec(msg["Subject"]),
                               "texto": _texto(msg)[:LIMITE_CORPO], "anexos": _anexos(msg)}, ensure_ascii=False, indent=1)
        crit = _criterios(e)
        try:
            tipo, dados = m.uid("search", "CHARSET", "UTF-8", *[x.encode("utf-8") if isinstance(x, str) else x for x in crit])
        except imaplib.IMAP4.error:
            tipo, dados = m.uid("search", None, *crit)
        uids = (dados[0] or b"").split() if tipo == "OK" else []
        limite = max(1, min(50, int(e.get("limite") or 15)))
        lista = []
        for uid in reversed(uids[-limite:]):
            tipo, d = m.uid("fetch", uid, "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)] BODY.PEEK[TEXT]<0.600>)")
            if tipo != "OK":
                continue
            cab, trecho, lida = b"", b"", False
            for parte in d:
                if isinstance(parte, tuple):
                    rotulo = parte[0].decode("ascii", "replace")
                    if "HEADER" in rotulo:
                        cab = parte[1]
                    else:
                        trecho = parte[1]
                    lida = lida or "\\Seen" in rotulo
            h = email.message_from_bytes(cab, policy=email.policy.default)
            resumo = re.sub(r"\s+", " ", trecho.decode("utf-8", "replace"))[:200]
            lista.append({"id": uid.decode(), "de": _dec(h["From"]), "assunto": _dec(h["Subject"]), "data": str(h["Date"] or ""),
                          "lida": lida, "trecho": resumo})
        return json.dumps({"total_encontradas": len(uids), "mensagens": lista}, ensure_ascii=False, indent=1)
    finally:
        try:
            m.logout()
        except Exception:
            pass


def _imap_mensagem(c: dict, uid: str) -> email.message.EmailMessage:
    m = _imap(c)
    try:
        m.select("INBOX", readonly=True)
        tipo, dados = m.uid("fetch", str(uid), "(BODY.PEEK[])")
        if tipo != "OK" or not dados or not isinstance(dados[0], tuple):
            raise ErroEmail(t("Mensagem não encontrada: {id}", id=uid))
        return email.message_from_bytes(dados[0][1], policy=email.policy.default)
    finally:
        try:
            m.logout()
        except Exception:
            pass


def _smtp_enviar(c: dict, e: dict, anexos: list[Path]) -> str:
    senha = segredos.ler(SEGREDO)
    msg = EmailMessage()
    msg["From"] = c.get("endereco")
    msg["To"] = e["para"]
    if e.get("cc"):
        msg["Cc"] = e["cc"]
    msg["Subject"] = e["assunto"]
    if e.get("responder_a"):
        try:
            original = _imap_mensagem(c, e["responder_a"])
            if original["Message-ID"]:
                msg["In-Reply-To"] = original["Message-ID"]
                msg["References"] = original["Message-ID"]
        except ErroEmail:
            pass
    msg.set_content(e["corpo"])
    for p in anexos:
        import mimetypes
        tipo = (mimetypes.guess_type(p.name)[0] or "application/octet-stream").split("/", 1)
        msg.add_attachment(p.read_bytes(), maintype=tipo[0], subtype=tipo[1], filename=p.name)
    porta = int(c.get("smtp_porta") or 465)
    try:
        if porta == 465:
            s = smtplib.SMTP_SSL(c.get("smtp") or "", porta, timeout=30)
        else:
            s = smtplib.SMTP(c.get("smtp") or "", porta, timeout=30)
            s.starttls()
        with s:
            s.login(c.get("endereco") or "", senha or "")
            s.send_message(msg)
    except smtplib.SMTPAuthenticationError as erro:
        raise ErroEmail(t("O servidor recusou o login para enviar ({erro}). Confira a senha de app.", erro=str(erro)[:200]))
    except (smtplib.SMTPException, OSError) as erro:
        raise ErroEmail(t("Não deu para enviar ({erro}).", erro=str(erro)[:200]))
    return t("E-mail enviado para {para}.", para=e["para"])


# ---------------- Outlook clássico (COM) ----------------

_PS_OUTLOOK = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$p = Get-Content -LiteralPath $env:CLAVE_EMAIL_PEDIDO -Raw -Encoding UTF8 | ConvertFrom-Json
$o = New-Object -ComObject Outlook.Application
$ns = $o.GetNamespace('MAPI')
function Resumo($m, $n) { $t = [string]$m.Body; if ($t.Length -gt $n) { $t = $t.Substring(0, $n) }; return ($t -replace '\s+', ' ') }
if ($p.acao -eq 'ler') {
  if ($p.id) {
    $m = $ns.GetItemFromID($p.id)
    $anexos = @(); foreach ($a in $m.Attachments) { $anexos += @{ nome = $a.FileName; tamanho = $a.Size } }
    $corpo = [string]$m.Body; if ($corpo.Length -gt 20000) { $corpo = $corpo.Substring(0, 20000) }
    @{ id = $m.EntryID; de = "$($m.SenderName) <$($m.SenderEmailAddress)>"; para = $m.To; cc = $m.CC; data = $m.ReceivedTime.ToString('s'); assunto = $m.Subject; texto = $corpo; anexos = $anexos } | ConvertTo-Json -Depth 4
    exit 0
  }
  $itens = $ns.GetDefaultFolder(6).Items
  $itens.Sort('[ReceivedTime]', $true)
  $filtro = @()
  if ($p.nao_lidas) { $filtro += '[Unread] = true' }
  if ($p.desde) { $filtro += "[ReceivedTime] >= '" + ([datetime]$p.desde).ToString('g') + "'" }
  if ($filtro.Count) { $itens = $itens.Restrict(($filtro -join ' AND ')) }
  $lista = @(); $total = 0
  foreach ($m in $itens) {
    if ($m.Class -ne 43) { continue }
    if ($p.remetente -and ("$($m.SenderName) $($m.SenderEmailAddress)" -notlike "*$($p.remetente)*")) { continue }
    if ($p.buscar -and ("$($m.Subject) $($m.Body)" -notlike "*$($p.buscar)*")) { continue }
    $total++
    if ($lista.Count -lt $p.limite) { $lista += @{ id = $m.EntryID; de = "$($m.SenderName) <$($m.SenderEmailAddress)>"; assunto = $m.Subject; data = $m.ReceivedTime.ToString('s'); lida = -not $m.UnRead; trecho = (Resumo $m 200) } }
    if ($total -ge 500) { break }
  }
  @{ total_encontradas = $total; mensagens = $lista } | ConvertTo-Json -Depth 4
  exit 0
}
if ($p.acao -eq 'enviar') {
  if ($p.responder_a) { $m = $ns.GetItemFromID($p.responder_a).Reply() } else { $m = $o.CreateItem(0) }
  $m.To = $p.para
  if ($p.cc) { $m.CC = $p.cc }
  $m.Subject = $p.assunto
  $m.Body = $p.corpo
  foreach ($a in $p.anexos) { [void]$m.Attachments.Add($a) }
  $m.Send()
  'ok'
  exit 0
}
if ($p.acao -eq 'salvar_anexo') {
  $m = $ns.GetItemFromID($p.id)
  foreach ($a in $m.Attachments) { if ($a.FileName -eq $p.anexo) { $a.SaveAsFile($p.destino); 'ok'; exit 0 } }
  throw "anexo nao encontrado"
}
if ($p.acao -eq 'testar') { $n = $ns.GetDefaultFolder(6).Items.Count; "ok $n"; exit 0 }
"""


def _outlook(pedido: dict, tempo: int = 120) -> str:
    if not outlook_instalado():
        raise ErroEmail(t("O Outlook clássico não está instalado neste computador (o Outlook novo não deixa outros programas usarem o e-mail)."))
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(pedido, f, ensure_ascii=False)
        arq_pedido = f.name
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8-sig") as f:
        f.write(_PS_OUTLOOK)
        script = f.name
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", script],
                           capture_output=True, timeout=tempo, env=dict(os.environ, CLAVE_EMAIL_PEDIDO=arq_pedido),
                           creationflags=0x08000000)
    except subprocess.TimeoutExpired:
        raise ErroEmail(t("O Outlook demorou demais para responder (ele pode estar esperando alguma janela aberta)."))
    finally:
        for a in (arq_pedido, script):
            try:
                os.unlink(a)
            except OSError:
                pass
    saida = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        erro = (r.stderr.decode("utf-8", "replace") or saida).strip().splitlines()
        raise ErroEmail(t("O Outlook não conseguiu: {erro}", erro=(erro[0] if erro else t("erro desconhecido"))[:300]))
    return saida


# ---------------- o que as ferramentas chamam ----------------

def ler(e: dict) -> str:
    c = configuracao()
    if c.get("tipo") == "outlook":
        return _outlook({"acao": "ler", "id": e.get("id") or "", "buscar": e.get("buscar") or "",
                         "remetente": e.get("remetente") or "", "nao_lidas": bool(e.get("nao_lidas")),
                         "desde": e.get("desde") or "", "limite": max(1, min(50, int(e.get("limite") or 15)))})
    return _imap_ler(c, e)


def enviar(e: dict, anexos: list[Path] | None = None) -> str:
    for campo in ("para", "assunto", "corpo"):
        if not str(e.get(campo) or "").strip():
            raise ErroEmail(t("Falta o campo {campo}.", campo=campo))
    c = configuracao()
    anexos = anexos or []
    if c.get("tipo") == "outlook":
        _outlook({"acao": "enviar", "para": e["para"], "cc": e.get("cc") or "", "assunto": e["assunto"],
                  "corpo": e["corpo"], "anexos": [str(p) for p in anexos], "responder_a": e.get("responder_a") or ""})
        return t("E-mail enviado para {para}.", para=e["para"])
    return _smtp_enviar(c, e, anexos)


def salvar_anexo(id_msg: str, nome: str, destino: Path) -> str:
    c = configuracao()
    if c.get("tipo") == "outlook":
        _outlook({"acao": "salvar_anexo", "id": id_msg, "anexo": nome, "destino": str(destino)})
        return t("Anexo salvo em {caminho}.", caminho=destino)
    msg = _imap_mensagem(c, id_msg)
    for parte in msg.iter_attachments():
        if _dec(parte.get_filename()) == nome:
            destino.write_bytes(parte.get_payload(decode=True) or b"")
            return t("Anexo salvo em {caminho}.", caminho=destino)
    raise ErroEmail(t("Anexo não encontrado nessa mensagem: {nome}", nome=nome))


def testar() -> str:
    c = configuracao()
    if c.get("tipo") == "outlook":
        saida = _outlook({"acao": "testar"}, tempo=60)
        n = saida.split()[-1] if saida.startswith("ok") else "?"
        return t("Funcionou: o Outlook respondeu e a caixa de entrada tem {n} itens.", n=n)
    m = _imap(c)
    try:
        tipo, dados = m.select("INBOX", readonly=True)
        n = (dados[0] or b"0").decode() if tipo == "OK" else "?"
    finally:
        try:
            m.logout()
        except Exception:
            pass
    return t("Funcionou: a caixa de entrada tem {n} mensagens.", n=n)


def previa(e: dict) -> str:
    """O e-mail inteiro, para a pessoa aprovar antes de enviar."""
    linhas = [t("Para: {para}", para=e.get("para", ""))]
    if e.get("cc"):
        linhas.append(t("Cc: {cc}", cc=e["cc"]))
    linhas.append(t("Assunto: {assunto}", assunto=e.get("assunto", "")))
    if e.get("anexos"):
        linhas.append(t("Anexos: {lista}", lista=", ".join(map(str, e["anexos"]))))
    return "\n".join(linhas) + "\n\n" + str(e.get("corpo", ""))


def endereco_de(texto: str) -> str:
    return parseaddr(texto or "")[1]
