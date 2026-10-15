"""Servidor local do Clave: entrega a interface (app/) e a API que ela usa.

Só escuta em 127.0.0.1. Toda rota /api pede o cookie de sessão, que o atalho do
Clave grava ao abrir a janela (o endereço leva ?t=<segredo>); sem ele, nenhuma
página de fora consegue mandar o Claude rodar comandos no computador.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import secrets
import string
import sys
import threading
import time
import traceback
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _pre_argumentos() -> None:
    """Opções que precisam valer antes de carregar o resto (a pasta de dados e o modo demonstração)."""
    import tempfile
    argv = sys.argv[1:]
    if "--dados" in argv and argv.index("--dados") + 1 < len(argv):
        os.environ["CLAVE_DADOS"] = argv[argv.index("--dados") + 1]
    if "--sem-senha" in argv:
        os.environ["CLAVE_SEM_SENHA"] = "1"
    if "--demo" in argv:
        os.environ.setdefault("CLAVE_DADOS", str(Path(tempfile.gettempdir()) / "clave-demo"))
        import api_falsa
        os.environ["CLAVE_API_FALSA"] = api_falsa.iniciar()


_pre_argumentos()

import agentes  # noqa: E402
import anexos  # noqa: E402
import atualizador  # noqa: E402
import banco  # noqa: E402
import comandos  # noqa: E402
import config  # noqa: E402
import contexto_pasta  # noqa: E402
import execucao  # noqa: E402
import estatisticas  # noqa: E402
import fluxos  # noqa: E402
import github_api  # noqa: E402
import modelo_pasta  # noqa: E402
import lancamentos  # noqa: E402
import modelos  # noqa: E402
import orcamento  # noqa: E402
import permissoes  # noqa: E402
import plugins  # noqa: E402
import precos  # noqa: E402
import rotinas  # noqa: E402
import segredos  # noqa: E402
import sistema  # noqa: E402
import tom  # noqa: E402
import tutoriais  # noqa: E402
from ferramentas import memoria  # noqa: E402
from i18n import t  # noqa: E402

SEM_SENHA = os.environ.get("CLAVE_SEM_SENHA") == "1"
DEMO = bool(os.environ.get("CLAVE_API_FALSA"))
COOKIE = "clave_sessao"
_ultimo_sinal = time.time()
_previas: dict[str, tuple[float, str]] = {}
_modelos_cache: dict = {"em": 0, "lista": None}
_codigo_saida = {"valor": 0}

mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("image/svg+xml", ".svg")

CSP_APP = ("default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; "
           "script-src 'self'; connect-src 'self'; font-src 'self' data:; frame-src 'self'; "
           "object-src 'none'; base-uri 'none'; form-action 'self'")
CSP_PREVIA = ("sandbox allow-scripts allow-forms allow-popups allow-modals allow-downloads; "
              "default-src * data: blob: 'unsafe-inline' 'unsafe-eval'")


def segredo_sessao() -> str:
    arq = config.DADOS / "sessao.key"
    try:
        valor = arq.read_text(encoding="ascii").strip()
        if len(valor) >= 32:
            return valor
    except OSError:
        pass
    config.DADOS.mkdir(parents=True, exist_ok=True)
    valor = secrets.token_hex(24)
    arq.write_text(valor, encoding="ascii")
    return valor


SEGREDO = segredo_sessao()


from rotas import ROTAS, Erro, rota  # noqa: E402  (as partes novas registram as rotas delas no mesmo lugar)
# as partes da 5.0 registram as rotas delas ao carregar: abas Arquivos e Visualizador, Console, Navegador e
# Tarefas, e os widgets (com os mapas)
import console  # noqa: E402,F401
import explorador  # noqa: E402,F401
import navegador  # noqa: E402,F401
import tarefas  # noqa: E402,F401
import widgets  # noqa: E402,F401


class Manipulador(BaseHTTPRequestHandler):
    server_version = "Clave"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # silencioso; erros vão para o log pelo traceback
        pass

    # ---------- utilidades ----------
    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").lower()
        porta = self.server.server_address[1]
        return host in (f"127.0.0.1:{porta}", f"localhost:{porta}", f"[::1]:{porta}")

    def _sessao_ok(self) -> bool:
        if SEM_SENHA:
            return True
        cookies = self.headers.get("Cookie") or ""
        for parte in cookies.split(";"):
            k, _, v = parte.strip().partition("=")
            if k == COOKIE and secrets.compare_digest(v, SEGREDO):
                return True
        return False

    def _origem_ok(self) -> bool:
        origem = self.headers.get("Origin")
        if not origem:
            return True
        porta = self.server.server_address[1]
        return origem in (f"http://127.0.0.1:{porta}", f"http://localhost:{porta}")

    def _json(self, dados, status=200, extra_cab=None):
        corpo = json.dumps(dados, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra_cab or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def _bytes(self, dados: bytes, tipo: str, status=200, cab=None):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        for k, v in (cab or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(dados)

    def corpo_bruto(self, limite=40 * 1024 * 1024) -> bytes:
        n = int(self.headers.get("Content-Length") or 0)
        if n > limite:
            raise Erro(413, t("Arquivo grande demais."))
        return self.rfile.read(n) if n else b""

    def corpo(self) -> dict:
        bruto = self.corpo_bruto(5 * 1024 * 1024)
        if not bruto:
            return {}
        try:
            d = json.loads(bruto)
        except ValueError:
            raise Erro(400, t("JSON inválido."))
        if not isinstance(d, dict):
            raise Erro(400, t("JSON inválido."))
        return d

    def query(self) -> dict:
        q = urllib.parse.urlparse(self.path).query
        return {k: v[-1] for k, v in urllib.parse.parse_qs(q).items()}

    # ---------- despacho ----------
    def do_GET(self):
        self._despachar("GET")

    def do_HEAD(self):
        self._despachar("GET")

    def do_POST(self):
        self._despachar("POST")

    def do_PATCH(self):
        self._despachar("PATCH")

    def do_DELETE(self):
        self._despachar("DELETE")

    def _despachar(self, metodo: str):
        global _ultimo_sinal
        try:
            if not self._host_ok():
                return self._json({"erro": t("Host não permitido.")}, 403)
            caminho = urllib.parse.urlparse(self.path).path
            if caminho.startswith("/api/"):
                if not self._sessao_ok():
                    return self._json({"erro": t("Sessão inválida. Abra o Clave pelo atalho Clave.bat."),
                                       "codigo": "sessao"}, 401)
                if metodo != "GET" and not self._origem_ok():
                    return self._json({"erro": t("Origem não permitida.")}, 403)
                _ultimo_sinal = time.time()
                for m, rx, fn in ROTAS:
                    if m == metodo:
                        achou = rx.match(caminho)
                        if achou:
                            return fn(self, **achou.groupdict())
                return self._json({"erro": t("Rota não encontrada.")}, 404)
            if caminho.startswith("/previa/") and metodo == "GET":
                return self._previa(caminho.rsplit("/", 1)[-1])
            if metodo != "GET":
                return self._json({"erro": t("Método não permitido.")}, 405)
            return self._estatico(caminho)
        except Erro as e:
            self._json({"erro": e.mensagem}, e.status)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:
            traceback.print_exc()
            try:
                self._json({"erro": t("Erro interno: {erro}", erro=e)}, 500)
            except OSError:
                pass

    def _estatico(self, caminho: str):
        q = self.query()
        if caminho == "/" and q.get("t"):
            if secrets.compare_digest(q["t"], SEGREDO):
                self.send_response(302)
                self.send_header("Location", "/")
                self.send_header("Set-Cookie", f"{COOKIE}={SEGREDO}; Path=/; HttpOnly; SameSite=Strict; "
                                                "Max-Age=31536000")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        if caminho == "/i18n/en.json":  # o catálogo em inglês da interface: um arquivo por tela, juntado aqui
            junto: dict = {}
            for arq in sorted((config.APP / "i18n" / "en").glob("*.json")):
                try:
                    junto.update(json.loads(arq.read_text(encoding="utf-8")))
                except (OSError, ValueError):
                    pass
            return self._bytes(json.dumps(junto, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8",
                               cab={"Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff"})
        rel = "index.html" if caminho in ("/", "") else urllib.parse.unquote(caminho.lstrip("/"))
        base = config.APP.resolve()
        alvo = (base / rel).resolve()
        if not alvo.is_relative_to(base) or not alvo.is_file():
            return self._bytes(b"Nao encontrado", "text/plain; charset=utf-8", 404)
        tipo = mimetypes.guess_type(str(alvo))[0] or "application/octet-stream"
        if tipo.startswith("text/") or tipo in ("application/json", "image/svg+xml"):
            tipo += "; charset=utf-8"
        cab = {"X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer"}
        if alvo.suffix in (".html", ".js", ".css", ".json"):
            cab["Cache-Control"] = "no-cache"
        else:
            cab["Cache-Control"] = "max-age=86400"
        if alvo.suffix == ".html":
            cab["Content-Security-Policy"] = CSP_APP
            cab["X-Frame-Options"] = "DENY"
        self._bytes(alvo.read_bytes(), tipo, cab=cab)

    def _previa(self, pid: str):
        item = _previas.get(pid)
        if not item:
            return self._bytes(t("Prévia expirada. Abra de novo pela conversa.").encode(), "text/plain; charset=utf-8",
                               404)
        self._bytes(item[1].encode("utf-8"), "text/html; charset=utf-8",
                    cab={"Content-Security-Policy": CSP_PREVIA, "Cache-Control": "no-store",
                         "X-Content-Type-Options": "nosniff"})


# ======================= rotas =======================

def _cfg_publica(cfg: dict) -> dict:
    return {k: v for k, v in cfg.items() if k not in ("alertas_vistos",)}


@rota("GET", "/api/saude")
def r_saude(h: Manipulador):
    h._json({"ok": True, "versao": config.VERSAO, "rodando": execucao.alguma_rodando()})


@rota("GET", "/api/estado")
def r_estado(h: Manipulador):
    cfg = config.carregar()
    chave = segredos.ler("anthropic")
    atual = {}
    try:
        cache = json.loads((atualizador.PASTA / "checagem.json").read_text(encoding="utf-8"))
        if cache.get("atual") == config.VERSAO:
            atual = {"nova": cache.get("nova"), "ultima": cache.get("ultima")}
    except (OSError, ValueError):
        pass
    h._json({
        "versao": config.VERSAO,
        "demo": DEMO,
        "plataforma": sys.platform,
        "pasta_pessoal": str(Path.home()),
        "tem_chave": bool(chave) or DEMO,
        "chave": segredos.mascarar(chave) if chave else "",
        "cfg": _cfg_publica(cfg),
        "estilos": config.estilos(cfg),
        "tom": tom.opcoes(),
        "nomes_en": comandos.NOMES_EN,  # o nome em inglês dos comandos, plugins, skills e fluxos que vêm com o Clave
        "orcamento": orcamento.situacao(),
        "modelos": modelos.lista_publica(cfg.get("modelos_antigos"), _modelos_cache["lista"]),
        "esforcos": [{"id": e, "nome": t(modelos.NOMES_ESFORCO[e])} for e in modelos.ESFORCOS],
        "github": {"origem": cfg.get("github_origem"), "gh_instalado": github_api.gh_instalado(),
                   "tem_token": segredos.existe("github_token")},
        "atualizacao": atual,
        "dev": atualizador.copia_de_desenvolvimento(),
        "modelo_de_pasta": config.MODELO_DE_PASTA.is_dir(),
    })


@rota("POST", "/api/chave")
def r_chave(h: Manipulador):
    chave = (h.corpo().get("chave") or "").strip()
    if not chave.startswith("sk-ant-"):
        raise Erro(400, t("Essa não parece uma chave da API da Anthropic (ela começa com sk-ant-)."))
    import anthropic
    try:
        cli = anthropic.Anthropic(api_key=chave, max_retries=1, timeout=30)
        ids = [m.id for m in cli.models.list(limit=100).data]
    except anthropic.AuthenticationError:
        raise Erro(400, t("A Anthropic recusou essa chave. Confira se copiou inteira e se ela não foi apagada."))
    except anthropic.APIConnectionError:
        raise Erro(400, t("Sem conexão com a Anthropic para conferir a chave. Confira a internet."))
    except anthropic.APIStatusError as e:
        raise Erro(400, t("A Anthropic respondeu {codigo} ao conferir a chave.", codigo=e.status_code))
    segredos.guardar("anthropic", chave)
    _modelos_cache.update(em=time.time(), lista=ids)
    h._json({"ok": True, "modelos": ids, "chave": segredos.mascarar(chave)})


@rota("DELETE", "/api/chave")
def r_chave_apagar(h: Manipulador):
    segredos.apagar("anthropic")
    h._json({"ok": True})


CAMPOS_NUMERICOS = {"teto_mensal_usd": (0, 100000), "dia_virada": (1, 28), "teto_tarefa_code_usd": (0, 10000),
                    "compactar_em": (50000, 900000), "tamanho_letra": (12, 24)}


@rota("POST", "/api/config")
def r_config(h: Manipulador):
    d = h.corpo()
    limpo = {}
    for k, v in d.items():
        if k not in config.PADRAO or k in ("alertas_vistos",):
            continue
        if k in CAMPOS_NUMERICOS:
            if v in (None, ""):
                if k == "teto_mensal_usd":
                    limpo[k] = None
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                raise Erro(400, t("Valor inválido em {campo}.", campo=k))
            lo, hi = CAMPOS_NUMERICOS[k]
            v = max(lo, min(hi, v))
            if k in ("dia_virada", "compactar_em", "tamanho_letra"):
                v = int(v)
        if k == "idioma" and v not in config.IDIOMAS:
            raise Erro(400, t("Valor inválido em {campo}.", campo=k))
        if k == "tom":
            v = tom.limpar(v)
        limpo[k] = v
    antes = config.carregar()
    cfg = config.salvar(limpo)
    if (cfg.get("idioma") != antes.get("idioma")
            or (cfg.get("baixar_videos") and not antes.get("baixar_videos"))):
        import videos
        videos.baixar_todos(cfg.get("idioma"))  # os vídeos das lições no idioma novo, em segundo plano
    h._json({"cfg": _cfg_publica(cfg), "estilos": config.estilos(cfg), "orcamento": orcamento.situacao()})


@rota("DELETE", "/api/compat")
def r_compat(h: Manipulador):
    """Religa os recursos opcionais que foram desligados depois de um erro da API."""
    import pedido
    pedido.religar_tudo()
    h._json({"ok": True})


@rota("POST", "/api/email/salvar")
def r_email_salvar(h: Manipulador):
    """Liga o conector de e-mail, guarda a senha de app (criptografada) e testa na hora."""
    from ferramentas import email as femail
    d = h.corpo()
    tipo = str(d.get("tipo") or "gmail")
    if tipo not in (*femail.PROVEDORES, "imap", "outlook"):
        raise Erro(400, t("Tipo de e-mail inválido."))
    c = {"tipo": tipo, "ligado": True, "endereco": str(d.get("endereco") or "").strip()}
    if tipo != "outlook":
        if "@" not in c["endereco"]:
            raise Erro(400, t("Escreva o endereço de e-mail."))
        hosts = femail.PROVEDORES.get(tipo) or {}
        try:
            c.update({"imap": str(d.get("imap") or hosts.get("imap") or "").strip(),
                      "imap_porta": int(d.get("imap_porta") or hosts.get("imap_porta") or 993),
                      "smtp": str(d.get("smtp") or hosts.get("smtp") or "").strip(),
                      "smtp_porta": int(d.get("smtp_porta") or hosts.get("smtp_porta") or 465)})
        except (TypeError, ValueError):
            raise Erro(400, t("Porta inválida."))
        if not c["imap"] or not c["smtp"]:
            raise Erro(400, t("Preencha os servidores IMAP e SMTP (o seu provedor informa na página de ajuda)."))
        senha = str(d.get("senha") or "").strip()
        if senha:
            segredos.guardar(femail.SEGREDO, senha.replace(" ", ""))
        elif not segredos.existe(femail.SEGREDO):
            raise Erro(400, t("Cole a senha de app."))
    config.salvar({"email": c})
    try:
        h._json({"ok": True, "mensagem": femail.testar()})
    except femail.ErroEmail as e:
        h._json({"ok": False, "mensagem": str(e)})


@rota("POST", "/api/email/desligar")
def r_email_desligar(h: Manipulador):
    from ferramentas import email as femail
    config.salvar({"email": {**(config.carregar().get("email") or {}), "ligado": False}})
    segredos.apagar(femail.SEGREDO)
    h._json({"ok": True})


@rota("POST", "/api/conectores/token")
def r_conector_token(h: Manipulador):
    d = h.corpo()
    nome = re.sub(r"[^\w-]", "-", str(d.get("nome") or ""))
    if not nome:
        raise Erro(400, t("Conector sem nome."))
    token = str(d.get("token") or "").strip()
    if token:
        segredos.guardar(f"mcp:{nome}", token)
    else:
        segredos.apagar(f"mcp:{nome}")
    h._json({"ok": True, "tem_token": bool(token)})


@rota("GET", "/api/modelos")
def r_modelos(h: Manipulador):
    if DEMO:
        _modelos_cache["lista"] = None
    elif time.time() - _modelos_cache["em"] > 3600 or _modelos_cache["lista"] is None:
        lista = execucao.modelos_disponiveis()
        if lista:
            _modelos_cache.update(em=time.time(), lista=lista)
    cfg = config.carregar()
    h._json({"modelos": modelos.lista_publica(cfg.get("modelos_antigos"), _modelos_cache["lista"])})


# ---------- conversas ----------

@rota("GET", "/api/conversas")
def r_conversas(h: Manipulador):
    q = h.query()
    h._json({"conversas": banco.listar_conversas(q.get("busca", "")[:200], q.get("projeto") or None,
                                                  q.get("arquivadas") == "1")})


@rota("POST", "/api/conversas")
def r_conversa_nova(h: Manipulador):
    d = h.corpo()
    modo = "code" if d.get("modo") == "code" else "chat"
    pasta = None
    if modo == "code":
        pasta = str(Path(d.get("pasta") or "").expanduser())
        if not d.get("pasta") or not Path(pasta).is_dir():
            raise Erro(400, t("Escolha uma pasta que exista para o modo Code."))
        pasta = str(Path(pasta).resolve())
        cfg = config.carregar()
        recentes = [pasta] + [p for p in cfg.get("pastas_recentes") or [] if p != pasta]
        config.salvar({"pastas_recentes": recentes[:12]})
    projeto_id = d.get("projeto_id") or None
    if projeto_id and not banco.projeto(projeto_id):
        raise Erro(404, t("Projeto não encontrado."))
    c = banco.criar_conversa(modo=modo, projeto_id=projeto_id, pasta=pasta)
    h._json({"conversa": c})


def _montar_visao(cid: str) -> dict:
    conv = banco.conversa(cid)
    if not conv:
        raise Erro(404, t("Conversa não encontrada."))
    caminho = banco.caminho(cid)
    for m in caminho:
        if m["papel"] == "user" and m["tipo"] == "normal" or m["papel"] == "assistant":
            irmaos = [f for f in banco.filhos(cid, m["pai_id"]) if f["papel"] == m["papel"] and f["tipo"] == m["tipo"]]
            m["irmaos"] = [f["id"] for f in irmaos]
    ex = execucao.ativa(cid)
    projeto = banco.projeto(conv["projeto_id"]) if conv.get("projeto_id") else None
    pendentes = []
    if ex:
        for dono in [ex, *ex.filhos]:
            for tid, a in list(dono.aprovacoes.items()):
                if not a["evento"].is_set() and a.get("pedido"):
                    pendentes.append({**a["pedido"], "execucao": dono.id, "de_etapa": dono is not ex})
    return {"conversa": conv, "mensagens": caminho, "execucao": ex.id if ex else None,
            "execucao_desde": ex.seq_salvo if ex else 0, "aprovacoes_pendentes": pendentes,
            "tarefas": (ex.ctx.tarefas if ex and ex.ctx else []),
            "gasto": banco.gasto_conversa(cid), "projeto": projeto}


@rota("GET", "/api/conversas/<cid>")
def r_conversa(h: Manipulador, cid):
    h._json(_montar_visao(cid))


@rota("PATCH", "/api/conversas/<cid>")
def r_conversa_editar(h: Manipulador, cid):
    d = h.corpo()
    if not banco.conversa(cid):
        raise Erro(404, t("Conversa não encontrada."))
    campos = {}
    if "titulo" in d:
        campos["titulo"] = str(d["titulo"])[:120]
    for k in ("fixada", "arquivada"):
        if k in d:
            campos[k] = 1 if d[k] else 0
    if "projeto_id" in d:
        campos["projeto_id"] = d["projeto_id"] or None
    if "ajustes" in d and isinstance(d["ajustes"], dict):
        campos["ajustes"] = d["ajustes"]
    if isinstance(d.get("ajustes_mesclar"), dict):  # muda só as chaves mandadas (ex.: modelo_fixo do conselheiro)
        campos["ajustes"] = {**(banco.conversa(cid).get("ajustes") or {}), **campos.get("ajustes", {}),
                             **{k: v for k, v in d["ajustes_mesclar"].items() if k in ("modelo", "modelo_fixo", "conselho_visto")}}
    banco.atualizar_conversa(cid, **campos)
    h._json({"conversa": banco.conversa(cid)})


@rota("DELETE", "/api/conversas/<cid>")
def r_conversa_apagar(h: Manipulador, cid):
    # para o que roda por ela (a resposta, os comandos em segundo plano, os downloads) antes de apagar
    parou = tarefas.parar_da_conversa(cid, esperar=5)
    if parou.get("ainda_rodando"):
        raise Erro(409, t("Pare a resposta antes de apagar a conversa."))
    banco.apagar_conversa(cid)
    h._json({"ok": True})


def _preparar_sistema(conv: dict) -> None:
    if conv.get("sistema"):
        return
    cfg = config.carregar()
    if conv["modo"] == "tutor":
        licao = tutoriais.ler((conv.get("ajustes") or {}).get("licao") or "")
        banco.atualizar_conversa(conv["id"], sistema=sistema.tutor(licao))
        return
    if conv["modo"] == "memoria":
        banco.atualizar_conversa(conv["id"], sistema=sistema.editor_memoria())
        return
    if conv["modo"] == "code":
        texto = sistema.code(cfg, conv["pasta"])
        banco.atualizar_conversa(conv["id"], sistema=texto)
        return
    projeto = banco.projeto(conv["projeto_id"]) if conv.get("projeto_id") else None
    texto = sistema.chat(cfg, projeto)
    contexto = []
    if projeto:
        for a in projeto.get("arquivos") or []:
            contexto.append({"type": "clave_anexo", "id": a["id"], "nome": a["nome"], "tipo": a["tipo"]})
    banco.atualizar_conversa(conv["id"], sistema=texto, contexto=contexto)


def _conteudo_usuario(conv: dict, texto: str, ids_anexos: list) -> tuple[list, dict, dict]:
    """Blocos da mensagem, meta para a tela e opções que o comando de barra traz (modelo, ferramentas liberadas)."""
    blocos = []
    for aid in ids_anexos or []:
        reg = banco.anexo(aid)
        if reg:
            blocos.append(anexos.referencia(reg))
    meta, extras = {}, {}
    texto = texto or ""
    pasta = conv.get("pasta") if conv["modo"] == "code" else None
    sep = comandos.separar(texto)
    # /fluxo, ou /workflow quando a pessoa não tem um comando ou skill dela com esse nome
    if sep and (sep[0] == "fluxo" or (comandos.canonico(sep[0]) == "fluxo" and not comandos.expandir(texto, pasta))):
        ident, _, pedido_fluxo = sep[1].partition(" ")
        m = fluxos.modelo(ident) if ident else None
        meta["exibir"] = texto
        meta["comando"] = sep[0]  # o balão mostra o nome que a pessoa digitou
        if m:
            texto = fluxos.texto_para_comando(m, pedido_fluxo.strip())
        else:
            texto = (t("Quero que esta tarefa rode como um fluxo, com etapas em modelos diferentes (proponha as etapas, os agentes e os modelos que fizerem sentido e mostre com executar_fluxo):")
                     + "\n\n" + (sep[1] or t("(ainda não disse a tarefa: pergunte qual é)")))
    elif sep:
        exp = comandos.expandir(texto, pasta)
        if exp:
            meta["exibir"] = texto
            meta["comando"] = sep[0]  # o balão mostra o nome que a pessoa digitou (/sales:proposal ou /vendas:proposta)
            meta["tipo_comando"] = exp["tipo"]
            if exp["tipo"] == "skill":
                meta["skill"] = exp["nome"]
            texto = (t("Quem usa chamou /{nome}.", nome=exp["nome"]) + "\n\n" + exp["texto"]) if exp["tipo"] == "comando" \
                else exp["texto"]
            if exp.get("modelo"):
                import agentes as _ag
                extras["modelo"] = _ag.resolver_modelo(exp["modelo"], "")
                extras["modelo_do_comando"] = True  # o conselheiro de modelo não mexe
            if exp.get("ferramentas_permitidas"):
                extras["regras_tarefa"] = exp["ferramentas_permitidas"]
    if texto.strip():
        blocos.append({"type": "text", "text": texto})
    if not blocos:
        raise Erro(400, t("Mensagem vazia."))
    return blocos, meta, {k: v for k, v in extras.items() if v}


def _nota_de_modo(conv: dict, opcoes: dict) -> str:
    """Aviso escondido sobre o modo Plano. O prompt de sistema é congelado por conversa, então o modelo só fica
    sabendo do modo atual por aqui (como o lembrete do modo Plano do Claude Code). Vai gravado na mensagem, para o
    começo da conversa não mudar entre um pedido e outro."""
    if conv["modo"] != "code":
        return ""
    antes = (conv.get("ajustes") or {}).get("permissao") or "perguntar"
    agora = opcoes.get("permissao") or antes
    if agora == "plano":
        return (execucao.MARCA_MODO + " ".join([
            t("Modo Plano ligado: investigue só lendo (não crie, não edite e não rode comandos) e, quando o plano estiver pronto, apresente com a ferramenta apresentar_plano."),
            t("Quem usa aprova e você segue executando na mesma resposta."),
        ]) + execucao.FIM_MARCA_MODO)
    if antes == "plano":
        nome_modo = t(execucao.NOMES_MODO[agora]) if agora in execucao.NOMES_MODO else agora
        return (execucao.MARCA_MODO + t("O modo Plano foi desligado; o modo agora é {modo}. Pode executar normalmente.",
                                        modo=nome_modo) + execucao.FIM_MARCA_MODO)
    return ""


def _opcoes(d: dict) -> dict:
    o = d.get("opcoes") or {}
    permitido = {"modelo", "esforco", "pensar", "mostrar_raciocinio", "busca_web", "github", "rapido", "permissao"}
    return {k: v for k, v in o.items() if k in permitido}


@rota("POST", "/api/tom/exemplo")
def r_tom_exemplo(h: Manipulador):
    """Uma resposta curta do Haiku com o jeito de falar escolhido, para ver antes de usar."""
    d = h.corpo()
    try:
        h._json(tom.exemplo(tom.limpar(d.get("tom")), str(d.get("pergunta") or "")))
    except ValueError as e:
        raise Erro(400, str(e))
    except execucao.anthropic.APIStatusError as e:
        raise Erro(502, execucao._mensagem_api(e))
    except execucao.anthropic.APIConnectionError:
        raise Erro(502, t("Sem conexão com a Anthropic. Confira a internet."))


@rota("POST", "/api/conversas/<cid>/compactar")
def r_compactar(h: Manipulador, cid):
    """/compact: resume a conversa agora; as próximas mensagens partem do resumo."""
    import compactar
    try:
        h._json(compactar.compactar(cid))
    except ValueError as e:
        raise Erro(400, str(e))
    except execucao.anthropic.APIStatusError as e:
        raise Erro(502, execucao._mensagem_api(e))


@rota("POST", "/api/conversas/<cid>/enviar")
def r_enviar(h: Manipulador, cid):
    d = h.corpo()
    conv = banco.conversa(cid)
    if not conv:
        raise Erro(404, t("Conversa não encontrada."))
    if execucao.ativa(cid):
        raise Erro(409, t("Esta conversa ainda está respondendo."))
    ok, motivo = orcamento.pode_gastar()
    if not ok:
        raise Erro(402, motivo)
    if not segredos.existe("anthropic") and not DEMO:
        raise Erro(400, t("Falta a chave da API. Cole a sua em Configurações > Conta e chave."))
    _preparar_sistema(conv)
    conv = banco.conversa(cid)
    conteudo, meta, extras = _conteudo_usuario(conv, d.get("texto", ""), d.get("anexos") or [])
    nota = _nota_de_modo(conv, _opcoes(d))
    if nota:
        conteudo.append({"type": "text", "text": nota})
    pai = conv.get("folha_id")
    if d.get("editar_de"):
        original = banco.mensagem(d["editar_de"])
        if not original or original["conversa_id"] != cid:
            raise Erro(404, t("Mensagem não encontrada."))
        pai = original["pai_id"]
    msg = banco.adicionar_mensagem(cid, pai, "user", conteudo, meta=meta)
    # antes de começar: o conselheiro de modelo pode gravar o modelo novo nos ajustes enquanto a resposta roda
    banco.atualizar_conversa(cid, ajustes={**(conv.get("ajustes") or {}), **_opcoes(d)})
    ex = execucao.iniciar(cid, {**_opcoes(d), **extras})
    h._json({"execucao": ex.id, "mensagem": msg["id"]})


@rota("POST", "/api/conversas/<cid>/regenerar")
def r_regenerar(h: Manipulador, cid):
    d = h.corpo()
    if execucao.ativa(cid):
        raise Erro(409, t("Esta conversa ainda está respondendo."))
    ok, motivo = orcamento.pode_gastar()
    if not ok:
        raise Erro(402, motivo)
    m = banco.mensagem(d.get("mensagem_id") or "")
    if not m or m["conversa_id"] != cid:
        raise Erro(404, t("Mensagem não encontrada."))
    while m and not (m["papel"] == "user" and m["tipo"] == "normal"):
        m = banco.mensagem(m["pai_id"]) if m["pai_id"] else None
    if not m:
        raise Erro(400, t("Não achei a pergunta dessa resposta."))
    banco.atualizar_conversa(cid, folha_id=m["id"])
    ex = execucao.iniciar(cid, {**_opcoes(d), "sem_conselheiro": True})  # ao gerar outra resposta, quem escolhe é a pessoa
    h._json({"execucao": ex.id})


@rota("POST", "/api/conversas/<cid>/folha")
def r_folha(h: Manipulador, cid):
    d = h.corpo()
    m = banco.mensagem(d.get("mensagem_id") or "")
    if not m or m["conversa_id"] != cid:
        raise Erro(404, t("Mensagem não encontrada."))
    if execucao.ativa(cid):
        raise Erro(409, t("Espere a resposta terminar para trocar de versão."))
    banco.atualizar_conversa(cid, folha_id=banco.folha_mais_recente(cid, m["id"]))
    h._json(_montar_visao(cid))


@rota("GET", "/api/conversas/<cid>/exportar")
def r_exportar(h: Manipulador, cid):
    v = _montar_visao(cid)
    linhas = [f"# {v['conversa'].get('titulo') or t('Conversa')}", ""]
    for m in v["mensagens"]:
        if m["tipo"] != "normal":
            continue
        quem = t("Você") if m["papel"] == "user" else "Claude"
        partes = []
        if (m.get("meta") or {}).get("exibir"):
            partes.append(m["meta"]["exibir"])
        elif isinstance(m["conteudo"], list):
            for b in m["conteudo"]:
                if b.get("type") == "text" and not b["text"].startswith(execucao.MARCA_MODO):
                    partes.append(b["text"])
                elif b.get("type") == "clave_anexo":
                    partes.append(t("[anexo: {nome}]", nome=b.get("nome")))
                elif b.get("type") == "tool_use" and b.get("name") == "mostrar_widget":
                    md = widgets.texto_para_exportar(b.get("id", ""))  # o Claude não repete no texto o que o cartão mostra
                    if md:
                        partes.append(md)
        if partes:
            linhas += [f"## {quem}", "", "\n\n".join(partes), ""]
    corpo = "\n".join(linhas).encode("utf-8")
    nome = re.sub(r"[^\w\- ]", "", v["conversa"].get("titulo") or t("conversa"))[:60] or t("conversa")
    h._bytes(corpo, "text/markdown; charset=utf-8",
             cab={"Content-Disposition": f"attachment; filename*=UTF-8''{urllib.parse.quote(nome)}.md"})


# ---------- ajudantes (lições no Haiku, editor de memória no Sonnet) ----------

@rota("POST", "/api/ajudantes/<tipo>")
def r_ajudante(h: Manipulador, tipo):
    d = h.corpo()
    if tipo == "tutor":
        slug = str(d.get("licao") or "")
        lic = tutoriais.ler(slug)
        if not lic:
            raise Erro(404, t("Lição não encontrada."))
        chave, titulo, ajustes = f"tutor:{slug}", t("Dúvidas: {titulo}", titulo=lic["titulo"]), {"licao": slug}
    elif tipo == "memoria":
        chave, titulo, ajustes = "memoria", t("Editor de memória"), {}
    else:
        raise Erro(404, t("Ajudante desconhecido."))
    cfg = config.carregar()
    mapa = dict(cfg.get("ajudantes") or {})
    cid = mapa.get(chave)
    if cid and (d.get("nova") or not banco.conversa(cid)):
        if cid and banco.conversa(cid) and not execucao.ativa(cid):
            banco.apagar_conversa(cid)
        cid = None
    if not cid:
        cid = banco.criar_conversa(modo=tipo, titulo=titulo, ajustes=ajustes)["id"]
        mapa[chave] = cid
        config.salvar({"ajudantes": mapa})
    h._json(_montar_visao(cid))


# ---------- execuções ----------

@rota("GET", "/api/execucoes/<eid>/eventos")
def r_eventos(h: Manipulador, eid):
    ex = execucao.pegar(eid)
    if not ex:
        raise Erro(404, t("Execução não encontrada."))
    desde = int(h.query().get("desde") or 0)
    h.send_response(200)
    h.send_header("Content-Type", "text/event-stream; charset=utf-8")
    h.send_header("Cache-Control", "no-store, no-transform")
    h.send_header("X-Content-Type-Options", "nosniff")
    h.send_header("X-Accel-Buffering", "no")
    h.send_header("Connection", "close")
    h.end_headers()
    h.close_connection = True
    # preenchimento inicial: navegador (e antivírus que filtra a web) que segura o começo da resposta antes de
    # entregar solta assim que passa de alguns KB. Sem isso, uma resposta parada esperando o seu OK não aparecia.
    h.wfile.write(b": " + b" " * 4096 + b"\n\n")
    h.wfile.flush()
    while True:
        evs = ex.eventos_desde(desde, espera=15)
        if evs:
            for ev in evs:
                h.wfile.write(f"data: {json.dumps(ev, ensure_ascii=False, default=str)}\n\n".encode("utf-8"))
            desde = evs[-1]["seq"] + 1
            h.wfile.flush()
            if any(ev["tipo"] == "fim" for ev in evs):
                return
        else:
            h.wfile.write(b": ping\n\n")
            h.wfile.flush()
            if ex.status not in ("rodando", "esperando") and desde >= len(ex.eventos):
                return


@rota("POST", "/api/execucoes/<eid>/parar")
def r_parar(h: Manipulador, eid):
    ex = execucao.pegar(eid)
    if ex:
        ex.interromper()
    h._json({"ok": True})


@rota("POST", "/api/execucoes/<eid>/aprovar")
def r_aprovar(h: Manipulador, eid):
    d = h.corpo()
    ex = execucao.pegar(eid)
    if not ex:
        raise Erro(404, t("Execução não encontrada."))
    decisao = d.get("decisao")
    validas = ("permitir", "permitir_sempre", "permitir_tarefa", "permitir_pasta", "permitir_app", "recusar",
               "executar_perguntar", "executar_aceitar", "executar_livre",
               "pode_ir", "mudar", "nao_fazer",  # o plano fora do modo Plano
               "responder", "pular")  # o cartão de perguntas
    if decisao not in validas:
        raise Erro(400, t("Decisão inválida."))
    bruto = d.get("dados") if isinstance(d.get("dados"), dict) else {}
    dados = {}
    if isinstance(bruto.get("regra"), str):
        dados["regra"] = bruto["regra"].strip()[:300]
        if decisao in ("permitir_pasta", "permitir_app") and permissoes.validar(dados["regra"]):
            raise Erro(400, permissoes.validar(dados["regra"]))
    if isinstance(bruto.get("etapas"), list):
        dados["etapas"] = [{k: e[k] for k in ("i", "modelo", "esforco", "tirar") if k in e}
                           for e in bruto["etapas"][:fluxos.MAX_ETAPAS] if isinstance(e, dict)]
    if isinstance(bruto.get("teto_usd"), (int, float)):
        dados["teto_usd"] = float(bruto["teto_usd"])
    if isinstance(bruto.get("respostas"), list):
        dados["respostas"] = [{"escolhas": [e[:100] for e in (r.get("escolhas") if isinstance(r.get("escolhas"), list) else [])[:4]
                                            if isinstance(e, str)],
                               "outra": str(r.get("outra") or "")[:1000]}
                              for r in bruto["respostas"][:4] if isinstance(r, dict)]
    if not ex.decidir(str(d.get("id")), decisao, str(d.get("texto") or "")[:2000], dados):
        raise Erro(409, t("Essa ação não está mais esperando resposta."))
    h._json({"ok": True})


@rota("POST", "/api/execucoes/<eid>/desfazer")
def r_desfazer(h: Manipulador, eid):
    if execucao.pegar(eid) and execucao.pegar(eid).status in ("rodando", "esperando"):
        raise Erro(409, t("Pare a tarefa antes de desfazer."))
    h._json({"arquivos": execucao.desfazer(eid)})


# ---------- anexos ----------

def _receber_arquivo(h: Manipulador, projeto_id=None):
    nome = urllib.parse.unquote(h.headers.get("X-Nome-Arquivo") or "arquivo")
    dados = h.corpo_bruto()
    if not dados:
        raise Erro(400, t("Arquivo vazio."))
    try:
        return anexos.salvar(Path(nome).name, dados, projeto_id=projeto_id)
    except ValueError as e:
        raise Erro(400, str(e))


@rota("POST", "/api/anexos")
def r_anexo_novo(h: Manipulador):
    h._json({"anexo": _receber_arquivo(h)})


@rota("GET", "/api/anexos/<aid>")
def r_anexo(h: Manipulador, aid):
    reg = banco.anexo(aid)
    if not reg:
        raise Erro(404, t("Anexo não encontrado."))
    try:
        dados = anexos.caminho(aid).read_bytes()
    except OSError:
        raise Erro(404, t("O arquivo do anexo sumiu."))
    cab = {"Cache-Control": "max-age=86400", "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"}
    if h.query().get("baixar") == "1":
        cab["Content-Disposition"] = f"attachment; filename*=UTF-8''{urllib.parse.quote(reg['nome'])}"
        return h._bytes(dados, reg["tipo"], cab=cab)
    if reg["tipo"].startswith(("video/", "audio/")):
        cab["Accept-Ranges"] = "bytes"
        m = re.match(r"bytes=(\d*)-(\d*)$", h.headers.get("Range") or "")
        if m and (m.group(1) or m.group(2)):
            total = len(dados)
            if m.group(1):
                ini, fim = int(m.group(1)), min(int(m.group(2) or total - 1), total - 1)
            else:  # bytes=-N: os últimos N
                ini, fim = max(0, total - int(m.group(2))), total - 1
            if ini > fim or ini >= total:
                return h._bytes(b"", reg["tipo"], status=416, cab={**cab, "Content-Range": f"bytes */{total}"})
            return h._bytes(dados[ini:fim + 1], reg["tipo"], status=206,
                            cab={**cab, "Content-Range": f"bytes {ini}-{fim}/{total}"})
        return h._bytes(dados, reg["tipo"], cab=cab)
    tipo = reg["tipo"] if reg["tipo"].startswith("image/") else "text/plain; charset=utf-8"
    if reg["tipo"] == "application/pdf":
        tipo = "application/pdf"
    h._bytes(dados, tipo, cab=cab)


@rota("GET", "/api/videos/<vid>/estado")
def r_video_estado(h: Manipulador, vid):
    import videos
    try:
        h._json(videos.estado(vid, h.query().get("lingua")))
    except ValueError as e:
        raise Erro(400, str(e))


@rota("POST", "/api/videos/<vid>/baixar")
def r_video_baixar(h: Manipulador, vid):
    """Baixa o vídeo da lição da release "videos" do GitHub, uma vez só."""
    import videos
    try:
        videos.baixar(vid, h.query().get("lingua"))
    except ValueError as e:
        raise Erro(502, str(e))
    h._json({"pronto": True})


@rota("GET", "/api/videos/<vid>")
def r_video(h: Manipulador, vid):
    import videos
    try:
        arq = videos.local(vid, h.query().get("lingua"))
    except ValueError as e:
        raise Erro(400, str(e))
    if not arq:
        raise Erro(404, t("Este vídeo ainda não foi baixado."))
    total = arq.stat().st_size
    cab = {"Cache-Control": "max-age=86400", "X-Content-Type-Options": "nosniff", "Accept-Ranges": "bytes"}
    m = re.match(r"bytes=(\d*)-(\d*)$", h.headers.get("Range") or "")
    ini, fim, status = 0, total - 1, 200
    if m and (m.group(1) or m.group(2)):
        if m.group(1):
            ini, fim = int(m.group(1)), min(int(m.group(2) or total - 1), total - 1)
        else:  # bytes=-N: os últimos N
            ini = max(0, total - int(m.group(2)))
        if ini > fim or ini >= total:
            return h._bytes(b"", "video/mp4", status=416, cab={**cab, "Content-Range": f"bytes */{total}"})
        status = 206
        cab["Content-Range"] = f"bytes {ini}-{fim}/{total}"
    with open(arq, "rb") as f:
        f.seek(ini)
        dados = f.read(fim - ini + 1)
    h._bytes(dados, "video/mp4", status=status, cab=cab)


@rota("POST", "/api/anexos/<aid>/abrir")
def r_anexo_abrir(h: Manipulador, aid):
    """Abre uma cópia do arquivo (planilha, PDF) no programa do computador."""
    reg = banco.anexo(aid)
    if not reg:
        raise Erro(404, t("Arquivo não encontrado."))
    # a extensão vem do tipo conferido, nunca do nome: um "texto" chamado x.bat não pode virar programa
    extensao = {anexos.MIME_XLSX: ".xlsx", "application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg",
                "image/gif": ".gif", "image/webp": ".webp", "text/plain": ".txt",
                **{v: k for k, v in anexos.MIDIA.items() if k not in (".m4v",)}}.get(reg["tipo"])
    if not extensao:
        raise Erro(400, t("Esse tipo de arquivo não é aberto pelo Clave."))
    pasta = config.DADOS / "abertos" / aid
    pasta.mkdir(parents=True, exist_ok=True)
    alvo = pasta / (Path(reg["nome"]).stem[:80] + extensao)
    alvo.write_bytes(anexos.caminho(aid).read_bytes())
    try:
        if sys.platform == "win32":
            os.startfile(str(alvo))
        else:
            import subprocess
            subprocess.Popen(["xdg-open", str(alvo)])
    except OSError as e:
        raise Erro(400, t("Não deu para abrir: {erro}", erro=e))
    h._json({"ok": True, "caminho": str(alvo)})


# ---------- projetos ----------

@rota("GET", "/api/projetos")
def r_projetos(h: Manipulador):
    h._json({"projetos": banco.listar_projetos()})


@rota("POST", "/api/projetos")
def r_projeto_novo(h: Manipulador):
    d = h.corpo()
    nome = (d.get("nome") or "").strip()
    if not nome:
        raise Erro(400, t("Dê um nome ao projeto."))
    h._json({"projeto": banco.criar_projeto(nome[:80], (d.get("descricao") or "")[:2000],
                                            (d.get("instrucoes") or "")[:50000])})


@rota("GET", "/api/projetos/<pid>")
def r_projeto(h: Manipulador, pid):
    p = banco.projeto(pid)
    if not p:
        raise Erro(404, t("Projeto não encontrado."))
    h._json({"projeto": p, "conversas": banco.listar_conversas(projeto_id=pid)})


@rota("PATCH", "/api/projetos/<pid>")
def r_projeto_editar(h: Manipulador, pid):
    d = h.corpo()
    banco.atualizar_projeto(pid, **{k: d[k] for k in ("nome", "descricao", "instrucoes") if k in d})
    h._json({"projeto": banco.projeto(pid)})


@rota("DELETE", "/api/projetos/<pid>")
def r_projeto_apagar(h: Manipulador, pid):
    for aid in banco.apagar_projeto(pid):
        try:
            anexos.caminho(aid).unlink()
        except OSError:
            pass
    h._json({"ok": True})


@rota("POST", "/api/projetos/<pid>/arquivos")
def r_projeto_arquivo(h: Manipulador, pid):
    if not banco.projeto(pid):
        raise Erro(404, t("Projeto não encontrado."))
    h._json({"anexo": _receber_arquivo(h, projeto_id=pid)})


@rota("DELETE", "/api/projetos/<pid>/arquivos/<aid>")
def r_projeto_arquivo_apagar(h: Manipulador, pid, aid):
    reg = banco.anexo(aid)
    if reg and reg.get("projeto_id") == pid:
        anexos.apagar(aid)
    h._json({"projeto": banco.projeto(pid)})


# ---------- uso ----------

@rota("GET", "/api/uso")
def r_uso(h: Manipulador):
    s = orcamento.situacao()
    ini, fim = orcamento.ciclo()
    h._json({"orcamento": s, **banco.uso_detalhado(ini.timestamp(), fim.timestamp())})


@rota("POST", "/api/uso/ajuste")
def r_uso_ajuste(h: Manipulador):
    d = h.corpo()
    try:
        valor = float(d.get("valor") or 0)
    except (TypeError, ValueError):
        raise Erro(400, t("Valor inválido."))
    cfg = config.carregar()
    ajustes = dict(cfg.get("ajustes") or {})
    ajustes[orcamento.situacao()["chave"]] = max(0.0, valor)
    config.salvar({"ajustes": ajustes})
    h._json({"orcamento": orcamento.situacao()})


@rota("GET", "/api/modelos/lancamentos")
def r_modelos_lancamentos(h: Manipulador):
    """As fichas dos modelos (cartões de Preços e planos), os lançados há menos de 14 dias que a pessoa não fechou
    (banner do início) e os que a conta já tem e o Clave ainda não conhece."""
    cfg = config.carregar()
    h._json({"fichas": lancamentos.lista(), "novos": lancamentos.novidades(cfg),
             "desconhecidos": lancamentos.desconhecidos(cfg), "inteligencia": lancamentos.fonte_inteligencia()})


@rota("GET", "/api/uso/painel")
def r_uso_painel(h: Manipulador):
    h._json({"painel": estatisticas.painel(), "orcamento": orcamento.situacao()})


# ---------- sugestões de outra conversa ----------

@rota("GET", "/api/sugestoes/<sid>")
def r_sugestao(h: Manipulador, sid):
    s = banco.sugestao(sid) or {"estado": "nova", "nova_conversa_id": None}
    nova = banco.conversa(s.get("nova_conversa_id") or "") if s.get("nova_conversa_id") else None
    h._json({"estado": s["estado"], "conversa": {"id": nova["id"], "titulo": nova.get("titulo") or ""} if nova else None})


@rota("POST", "/api/sugestoes/<sid>/dispensar")
def r_sugestao_dispensar(h: Manipulador, sid):
    origem = banco.conversa(str(h.corpo().get("conversa_id") or ""))
    if not origem:
        raise Erro(404, t("Conversa não encontrada."))
    banco.marcar_sugestao(sid, origem["id"], "dispensada")
    h._json({"ok": True})


@rota("POST", "/api/sugestoes/<sid>/abrir")
def r_sugestao_abrir(h: Manipulador, sid):
    """Abre a conversa que o Claude sugeriu e já manda o pedido dela. Só acontece com o clique de quem usa."""
    origem = banco.conversa(str(h.corpo().get("conversa_id") or ""))
    if not origem:
        raise Erro(404, t("Conversa não encontrada."))
    ja = banco.sugestao(sid)
    if ja and ja["estado"] == "aberta" and ja.get("nova_conversa_id") and banco.conversa(ja["nova_conversa_id"]):
        h._json({"conversa": banco.conversa(ja["nova_conversa_id"]), "ja_aberta": True})
        return
    b = banco.bloco_ferramenta(origem["id"], sid)
    if not b or b.get("name") != "sugerir_conversa":
        raise Erro(404, t("Sugestão não encontrada."))
    entrada = b.get("input") or {}
    titulo = " ".join(str(entrada.get("titulo") or "").split())[:80]
    pedido = str(entrada.get("pedido") or "").strip()
    if not titulo or not pedido:
        raise Erro(400, t("A sugestão veio sem título ou sem pedido."))
    ok, motivo = orcamento.pode_gastar()
    if not ok:
        raise Erro(402, motivo)
    if not segredos.existe("anthropic") and not DEMO:
        raise Erro(400, t("Falta a chave da API. Cole a sua em Configurações > Conta e chave."))
    modo = origem["modo"] if origem["modo"] in ("chat", "code") else "chat"
    pasta = origem.get("pasta") if modo == "code" else None
    if modo == "code" and not (pasta and Path(pasta).is_dir()):
        raise Erro(400, t("A pasta desta conversa não existe mais."))
    ajustes = _opcoes({"opcoes": origem.get("ajustes") or {}})
    conv = banco.criar_conversa(modo=modo, projeto_id=origem.get("projeto_id"), pasta=pasta, titulo=titulo, ajustes=ajustes)
    _preparar_sistema(conv)
    conv = banco.conversa(conv["id"])
    conteudo, meta, extras = _conteudo_usuario(conv, pedido, [])
    nota = _nota_de_modo(conv, ajustes)
    if nota:
        conteudo.append({"type": "text", "text": nota})
    banco.adicionar_mensagem(conv["id"], None, "user", conteudo, meta={**meta, "sugestao_de": origem["id"]})
    ex = execucao.iniciar(conv["id"], {**ajustes, **extras})
    banco.marcar_sugestao(sid, origem["id"], "aberta", conv["id"])
    h._json({"conversa": banco.conversa(conv["id"]), "execucao": ex.id})


# ---------- preços e planos ----------

@rota("GET", "/api/precos")
def r_precos(h: Manipulador):
    h._json({"modelos": precos.tabela_modelos(), "planos": precos.planos(), "perfis": precos.perfis(),
             "reais": precos.medias_reais(), "projecao": precos.projecao(),
             "mensagens_por_janela": precos.MENSAGENS_POR_JANELA_PRO})


@rota("POST", "/api/precos/estimar")
def r_precos_estimar(h: Manipulador):
    try:
        h._json(precos.estimar(h.corpo()))
    except (TypeError, ValueError):
        raise Erro(400, t("Algum número da estimativa está inválido."))


# ---------- memória ----------

@rota("GET", "/api/importar/pedido")
def r_importar_pedido(h: Manipulador):
    import importar
    h._json({"pedido": importar.pedido()})


@rota("POST", "/api/importar/ler")
def r_importar_ler(h: Manipulador):
    import importar
    texto = str(h.corpo().get("texto") or "")
    if not texto.strip():
        raise Erro(400, t("Cole a resposta inteira do Claude ou do ChatGPT."))
    r = importar.ler(texto)
    if not r["itens"]:
        raise Erro(400, t("Não achei nenhuma categoria na resposta. Confira se colou o bloco inteiro (com os títulos das seções)."))
    h._json(r)


@rota("POST", "/api/importar/aplicar")
def r_importar_aplicar(h: Manipulador):
    import importar
    itens = [i for i in (h.corpo().get("itens") or []) if isinstance(i, dict)]
    h._json({"feito": importar.aplicar(itens)})


@rota("GET", "/api/memoria")
def r_memoria(h: Manipulador):
    h._json({"arquivos": memoria.listar()})


@rota("POST", "/api/memoria")
def r_memoria_gravar(h: Manipulador):
    d = h.corpo()
    try:
        memoria.gravar(d.get("caminho") or "", d.get("texto") or "")
    except memoria.ErroMemoria as e:
        raise Erro(400, str(e))
    h._json({"arquivos": memoria.listar()})


@rota("DELETE", "/api/memoria")
def r_memoria_apagar(h: Manipulador):
    try:
        memoria.apagar(h.query().get("caminho") or "")
    except memoria.ErroMemoria as e:
        raise Erro(400, str(e))
    h._json({"arquivos": memoria.listar()})


# ---------- pastas (escolha da pasta do modo Code) ----------

@rota("GET", "/api/pastas")
def r_pastas(h: Manipulador):
    q = h.query()
    caminho = q.get("caminho") or str(Path.home())
    if caminho == "::discos" and sys.platform == "win32":
        discos = [f"{l}:\\" for l in string.ascii_uppercase if Path(f"{l}:\\").exists()]
        return h._json({"caminho": "", "pai": None, "pastas": [{"nome": d, "caminho": d} for d in discos]})
    p = Path(caminho).expanduser()
    if not p.is_dir():
        raise Erro(404, t("Pasta não encontrada."))
    p = p.resolve()
    pastas = []
    try:
        for item in sorted(p.iterdir(), key=lambda x: x.name.lower()):
            try:
                if item.is_dir() and not item.name.startswith(("$", ".")):
                    pastas.append({"nome": item.name, "caminho": str(item)})
            except OSError:
                continue
    except OSError as e:
        raise Erro(403, t("Sem acesso a essa pasta ({erro}).", erro=e.strerror))
    pai = str(p.parent) if p.parent != p else ("::discos" if sys.platform == "win32" else None)
    atalhos = [{"nome": t("Pasta pessoal"), "caminho": str(Path.home())}]
    for nome in ("Desktop", "Documents", "Downloads", "Área de Trabalho", "Documentos"):
        alvo = Path.home() / nome
        if alvo.is_dir():
            atalhos.append({"nome": nome, "caminho": str(alvo)})
    h._json({"caminho": str(p), "pai": pai, "pastas": pastas[:500], "atalhos": atalhos})


@rota("GET", "/api/pasta-info")
def r_pasta_info(h: Manipulador):
    caminho = h.query().get("caminho") or ""
    if not caminho or not Path(caminho).is_dir():
        raise Erro(404, t("Pasta não encontrada."))
    inst = [{"caminho": a["caminho"], "escopo": a["escopo"], "tamanho": len(a.get("texto", ""))}
            for a in contexto_pasta.instrucoes(caminho)]
    h._json({"instrucoes": inst, "skills": contexto_pasta.skills(caminho)})


# ---------- GitHub ----------

@rota("GET", "/api/github/estado")
def r_gh_estado(h: Manipulador):
    cfg = config.carregar()
    info = {"origem": cfg.get("github_origem"), "gh_instalado": github_api.gh_instalado(),
            "tem_token": segredos.existe("github_token"), "usuario": None}
    if cfg.get("github_origem"):
        try:
            u = github_api.usuario()
            info["usuario"] = {"login": u.get("login"), "nome": u.get("name"), "avatar": u.get("avatar_url")}
        except github_api.ErroGitHub as e:
            info["erro"] = str(e)
    h._json(info)


@rota("POST", "/api/github/conectar")
def r_gh_conectar(h: Manipulador):
    d = h.corpo()
    origem = d.get("origem")
    if origem == "gh":
        tok = github_api.token_do_gh()
        if not tok:
            raise Erro(400, t("O gh não está instalado ou não está logado. Rode 'gh auth login' no terminal, ou use um token pessoal."))
    elif origem == "token":
        tok = (d.get("token") or "").strip()
        if not tok:
            raise Erro(400, t("Cole o token."))
    elif origem in ("", None):
        config.salvar({"github_origem": "", "github_ferramentas": False})
        segredos.apagar("github_token")
        return h._json({"ok": True})
    else:
        raise Erro(400, t("Origem inválida."))
    try:
        u = github_api.pedir("GET", "/user", tok=tok)
    except github_api.ErroGitHub as e:
        raise Erro(400, str(e))
    if origem == "token":
        segredos.guardar("github_token", tok)
    config.salvar({"github_origem": origem})
    h._json({"ok": True, "usuario": {"login": u.get("login"), "nome": u.get("name")}})


@rota("GET", "/api/github/repos")
def r_gh_repos(h: Manipulador):
    try:
        h._json({"repos": github_api.repos(int(h.query().get("pagina") or 1))})
    except github_api.ErroGitHub as e:
        raise Erro(400, str(e))


@rota("GET", "/api/github/arvore")
def r_gh_arvore(h: Manipulador):
    q = h.query()
    try:
        h._json(github_api.arvore(q.get("repo", ""), q.get("ref") or None))
    except github_api.ErroGitHub as e:
        raise Erro(400, str(e))


@rota("POST", "/api/github/anexar")
def r_gh_anexar(h: Manipulador):
    d = h.corpo()
    repo, ref = d.get("repo", ""), d.get("ref") or None
    caminhos = list(d.get("caminhos") or [])[:80]
    feitos, erros = [], []
    for c in caminhos:
        try:
            r = github_api.conteudo(repo, c, ref)
            if r["tipo"] != "arquivo":
                continue
            reg = anexos.salvar(f"{repo}/{c}", r["bytes"], projeto_id=d.get("projeto_id"), origem="github")
            feitos.append(reg)
        except (github_api.ErroGitHub, ValueError) as e:
            erros.append(f"{c}: {e}")
    h._json({"anexos": feitos, "erros": erros})


# ---------- tutoriais e modelo de pasta ----------

@rota("GET", "/api/tutoriais")
def r_tutoriais(h: Manipulador):
    h._json({"tutoriais": tutoriais.listar(), "feitos": config.carregar().get("tutoriais_feitos") or []})


@rota("GET", "/api/tutoriais/<slug>")
def r_tutorial(h: Manipulador, slug):
    lic = tutoriais.ler(slug)
    if not lic:
        raise Erro(404, t("Tutorial não encontrado."))
    h._json(lic)


@rota("POST", "/api/tutoriais/<slug>/feito")
def r_tutorial_feito(h: Manipulador, slug):
    feitos = list(config.carregar().get("tutoriais_feitos") or [])
    if slug not in feitos:
        feitos.append(slug)
    config.salvar({"tutoriais_feitos": feitos})
    h._json({"feitos": feitos})


@rota("POST", "/api/modelo-de-pasta")
def r_modelo_pasta(h: Manipulador):
    d = h.corpo()
    try:
        r = modelo_pasta.criar(d.get("destino") or "", d.get("nome") or "", d.get("respostas") or {},
                               bool(d.get("git", True)))
    except ValueError as e:
        raise Erro(400, str(e))
    h._json(r)


# ---------- atualização ----------

@rota("GET", "/api/atualizacao")
def r_atualizacao(h: Manipulador):
    forcar = h.query().get("forcar") == "1"
    info = atualizador.checar(forcar=forcar)
    config.salvar({"ultima_checagem": time.strftime("%Y-%m-%d %H:%M")})
    h._json(info)


@rota("POST", "/api/atualizacao/aplicar")
def r_atualizacao_aplicar(h: Manipulador):
    if execucao.alguma_rodando():
        raise Erro(409, t("Espere as respostas em andamento terminarem antes de atualizar."))
    if os.environ.get("CLAVE_LANCADOR") != "1":
        raise Erro(400, t("Para atualizar, abra o Clave pelo atalho Clave.bat (ele reinicia o app depois)."))
    try:
        r = atualizador.baixar_e_preparar()
    except atualizador.ErroAtualizacao as e:
        raise Erro(400, str(e))
    h._json({"ok": True, **r})
    _desligar(3)


@rota("POST", "/api/sair")
def r_sair(h: Manipulador):
    h._json({"ok": True})
    _desligar(0)


@rota("POST", "/api/sair-da-conta")
def r_sair_da_conta(h: Manipulador):
    """Logout: apaga a chave e as senhas, volta todas as configurações ao padrão e desliga as rotinas. Conversas,
    projetos, memória e anexos ficam. A tela recarrega e mostra a apresentação e os tours de novo."""
    if execucao.alguma_rodando():
        raise Erro(409, t("Espere as respostas em andamento terminarem."))
    desligadas = rotinas.desligar_todas()
    segredos.apagar_tudo()
    config.resetar()
    _modelos_cache.update(em=0, lista=None)
    lancamentos._CACHE_CONTA.unlink(missing_ok=True)  # os modelos da conta da chave antiga
    # os logins e cookies do navegador do Code também são credenciais (sem a janela do Clave, não há o que limpar)
    threading.Thread(target=navegador.limpar_dados, daemon=True).start()
    h._json({"ok": True, "rotinas_desligadas": desligadas})


@rota("POST", "/api/desinstalar")
def r_desinstalar(h: Manipulador):
    """Tira as tarefas das rotinas do Agendador e entrega o resto a ferramentas/desinstalar.ps1, que roda do %TEMP%
    depois que o app fecha: atalhos que apontam para esta pasta, %APPDATA%\\Clave e a pasta do Clave inteira."""
    import desinstalador
    if DEMO:  # a demonstração e os testes rodam o servidor de verdade a partir da pasta do Clave: nunca desinstalar
        raise Erro(400, t("Na demonstração não dá para desinstalar."))
    motivo = desinstalador.motivo_para_nao(config.RAIZ)
    if motivo:
        raise Erro(400, motivo)
    if os.environ.get("CLAVE_LANCADOR") != "1":
        raise Erro(400, t("Para desinstalar pelo app, abra o Clave pelo atalho (ou Clave.bat). Ou apague a pasta à mão."))
    if execucao.alguma_rodando():
        raise Erro(409, t("Espere as respostas em andamento terminarem."))
    rotinas.desagendar_todas()
    desinstalador.lancar(config.RAIZ, os.getpid())  # o script fica esperando este processo acabar
    h._json({"ok": True})
    _desligar(0)


# ---------- prévia e backup ----------

@rota("POST", "/api/previa")
def r_previa(h: Manipulador):
    d = h.corpo()
    html = str(d.get("html") or "")
    if d.get("tipo") == "svg":
        html = ("<!doctype html><meta charset=utf-8><style>html,body{margin:0;height:100%;display:grid;"
                "place-items:center;background:#fff}svg{max-width:100%;max-height:100vh}</style>" + html)
    agora = time.time()
    for k, (em, _) in list(_previas.items()):
        if agora - em > 3600:
            _previas.pop(k, None)
    pid = secrets.token_urlsafe(12)
    _previas[pid] = (agora, html)
    h._json({"url": f"/previa/{pid}"})


@rota("GET", "/api/backup")
def r_backup(h: Manipulador):
    corpo = json.dumps(banco.exportar_tudo(), ensure_ascii=False, default=str).encode("utf-8")
    h._bytes(corpo, "application/json; charset=utf-8",
             cab={"Content-Disposition": f"attachment; filename=clave-backup-{time.strftime('%Y-%m-%d')}.json"})


@rota("POST", "/api/backup")
def r_backup_importar(h: Manipulador):
    try:
        dados = json.loads(h.corpo_bruto(200 * 1024 * 1024) or b"{}")
        h._json({"importado": banco.importar_tudo(dados)})
    except ValueError as e:
        raise Erro(400, str(e))


# ---------- permissões ----------

def _pasta_param(valor) -> Path | None:
    if not valor:
        return None
    p = Path(str(valor)).expanduser()
    if not p.is_dir():
        raise Erro(400, t("Pasta não encontrada."))
    return p.resolve()


@rota("GET", "/api/permissoes")
def r_permissoes(h: Manipulador):
    q = h.query()
    pasta = _pasta_param(q.get("pasta"))
    cfg = config.carregar()
    app = {a: list((cfg.get("permissoes") or {}).get(a) or []) for a in permissoes.ACOES}
    resp = {"app": app, "protegidos": cfg.get("protegidos") or [], "pasta": None}
    if pasta:
        regras, avisos = permissoes.ler_pasta(pasta)
        resp["pasta"] = {"caminho": str(pasta), "avisos": avisos,
                         "arquivos": [str(a) for a in permissoes.arquivos_da_pasta(pasta)],
                         "regras": [{"acao": r.acao, "texto": r.texto, "origem": r.origem} for r in regras]}
    h._json(resp)


@rota("POST", "/api/permissoes")
def r_permissao_nova(h: Manipulador):
    d = h.corpo()
    acao, texto = d.get("acao"), str(d.get("regra") or "").strip()
    if acao not in permissoes.ACOES:
        raise Erro(400, t("Ação inválida."))
    erro = permissoes.validar(texto)
    if erro:
        raise Erro(400, erro)
    try:
        if d.get("escopo") == "pasta":
            pasta = _pasta_param(d.get("pasta"))
            if not pasta:
                raise Erro(400, t("Escolha a pasta."))
            permissoes.salvar_na_pasta(pasta, acao, texto)
        else:
            permissoes.salvar_no_app(acao, texto)
    except ValueError as e:
        raise Erro(400, str(e))
    h._json({"ok": True})


@rota("DELETE", "/api/permissoes")
def r_permissao_apagar(h: Manipulador):
    d = h.corpo()
    acao, texto = d.get("acao"), str(d.get("regra") or "")
    if d.get("escopo") == "pasta":
        ok = permissoes.remover_da_pasta(_pasta_param(d.get("pasta")), acao, texto)
    else:
        ok = permissoes.remover_do_app(acao, texto)
    if not ok:
        raise Erro(404, t("Regra não encontrada."))
    h._json({"ok": True})


@rota("POST", "/api/permissoes/testar")
def r_permissao_testar(h: Manipulador):
    """Responde "esse comando (ou arquivo) passaria?" sem rodar nada."""
    from ferramentas import code as fcode
    d = h.corpo()
    pasta = _pasta_param(d.get("pasta")) or Path.home()
    ferr = str(d.get("ferramenta") or "Bash")
    valor = str(d.get("valor") or "").strip()
    if not valor:
        raise Erro(400, t("Escreva o comando ou o caminho."))
    modo = d.get("modo") if d.get("modo") in ("perguntar", "aceitar_edicoes", "plano", "livre") else "perguntar"
    cfg = config.carregar()
    ctx = fcode.Contexto(raiz=pasta, protegidos=list(cfg.get("protegidos") or []), execucao_id="teste",
                         conversa_id="teste")
    ctx.regras = permissoes.coletar(cfg, pasta)
    nome, entrada = {"Bash": ("rodar_comando", {"comando": valor, "descricao": "teste"}),
                     "Read": ("ler_arquivo", {"caminho": valor}),
                     "Edit": ("escrever_arquivo", {"caminho": valor, "conteudo": ""})}.get(ferr, (None, None))
    if nome is None:
        if ferr == "Navegador":  # "clicar https://site.com" ou só o endereço (vale abrir)
            h._json(navegador.testar_regra(ctx.regras, valor, modo))
            return
        if ferr in ("WebFetch", "WebSearch"):
            r = permissoes.nega(ctx.regras, ferr, valor)
            h._json({"decisao": "negar" if r else "auto", "motivo": r.descrever() if r else
                     t("a web segue o botão de busca da conversa"), "origem": "regra" if r else "modo"})
            return
        raise Erro(400, t("Ferramenta inválida."))
    det = fcode.decidir(nome, entrada, ctx, modo, set())
    det["sugestao"] = permissoes.sugerir(nome, entrada, ctx)
    h._json(det)


@rota("GET", "/api/permissoes/historico")
def r_permissoes_historico(h: Manipulador):
    q = h.query()
    h._json({"registros": banco.log_permissoes(min(1000, int(q.get("limite") or 300)), q.get("decisao") or "")})


@rota("DELETE", "/api/permissoes/historico")
def r_permissoes_historico_limpar(h: Manipulador):
    banco.limpar_log_permissoes()
    h._json({"ok": True})


# ---------- agentes, comandos e fluxos ----------

@rota("GET", "/api/agentes")
def r_agentes(h: Manipulador):
    pasta = _pasta_param(h.query().get("pasta"))
    h._json({"agentes": agentes.listar(pasta)})


@rota("POST", "/api/agentes")
def r_agente_salvar(h: Manipulador):
    d = h.corpo()
    try:
        a = agentes.salvar(d, "pasta" if d.get("onde") == "pasta" else "pessoal", _pasta_param(d.get("pasta")))
    except ValueError as e:
        raise Erro(400, str(e))
    h._json({"agente": a})


@rota("DELETE", "/api/agentes")
def r_agente_apagar(h: Manipulador):
    d = h.corpo()
    try:
        agentes.apagar(str(d.get("caminho") or ""), _pasta_param(d.get("pasta")))
    except (ValueError, OSError) as e:
        raise Erro(400, str(e))
    h._json({"ok": True})


@rota("GET", "/api/comandos")
def r_comandos(h: Manipulador):
    q = h.query()
    pasta = _pasta_param(q.get("pasta"))
    lista = comandos.listar(pasta)
    modelos_fluxo = fluxos.listar_modelos()
    ids = {m["id"] for m in modelos_fluxo}
    for m in modelos_fluxo:
        # o id em inglês só para os fluxos que vêm com o Clave, e só se não for o id de outro fluxo (um da pessoa)
        en = comandos.nome_en(m["id"]) if m["origem"] == "clave" or str(m["origem"]).startswith("plugin:") else m["id"]
        if en != m["id"] and en in ids:
            en = m["id"]
        lista.append({"nome": f"fluxo {m['id']}", "nome_en": f"workflow {en}",
                      "descricao": m.get("descricao") or m.get("nome", ""),
                      "tipo": "fluxo", "origem": m["origem"], "argumentos": m.get("pede", "")})
    h._json({"comandos": lista})


@rota("GET", "/api/fluxos")
def r_fluxos(h: Manipulador):
    h._json({"modelos": fluxos.listar_modelos(), "historico": banco.listar_fluxos(),
             "ligados": bool(config.carregar().get("fluxos_ligados", True))})


@rota("GET", "/api/fluxos/<fid>")
def r_fluxo(h: Manipulador, fid):
    f = banco.fluxo(fid)
    if not f:
        raise Erro(404, t("Fluxo não encontrado."))
    h._json({"fluxo": f})


@rota("POST", "/api/fluxos/modelos")
def r_fluxo_modelo_salvar(h: Manipulador):
    try:
        h._json({"modelo": fluxos.salvar_modelo(h.corpo())})
    except fluxos.ErroFluxo as e:
        raise Erro(400, str(e))


@rota("DELETE", "/api/fluxos/modelos/<ident>")
def r_fluxo_modelo_apagar(h: Manipulador, ident):
    try:
        fluxos.apagar_modelo(ident)
    except fluxos.ErroFluxo as e:
        raise Erro(400, str(e))
    h._json({"ok": True})


@rota("POST", "/api/fluxos/estimar")
def r_fluxo_estimar(h: Manipulador):
    """Estimativa de custo de um modelo de fluxo, para a página de fluxos."""
    d = h.corpo()
    cfg = config.carregar()
    try:
        p = fluxos.normalizar({"titulo": "x", "objetivo": "x", "etapas": d.get("etapas") or []}, fid="estimativa",
                              pasta=str(_pasta_param(d.get("pasta")) or "") or None if d.get("pasta") else
                              ("." if d.get("modo") == "code" else None),
                              modelo_padrao=cfg.get("modelo_code") or "claude-haiku-5-5")
    except fluxos.ErroFluxo as e:
        raise Erro(400, str(e))
    h._json({"estimativa": p["estimativa"], "etapas": [{"i": e["i"], "estimativa": e["estimativa"],
                                                        "modelo_nome": e["modelo_nome"]} for e in p["etapas"]]})


# ---------- plugins ----------

@rota("GET", "/api/plugins")
def r_plugins(h: Manipulador):
    plugins.limpar_baixados()
    h._json({"plugins": plugins.listar()})


@rota("POST", "/api/plugins/<nome>/ligar")
def r_plugin_ligar(h: Manipulador, nome):
    plugins.ligar(nome, bool(h.corpo().get("ligado")))
    h._json({"ok": True})


@rota("DELETE", "/api/plugins/<nome>")
def r_plugin_remover(h: Manipulador, nome):
    try:
        plugins.remover(nome)
    except plugins.ErroPlugin as e:
        raise Erro(400, str(e))
    h._json({"ok": True})


@rota("POST", "/api/plugins/analisar-pasta")
def r_plugin_analisar(h: Manipulador):
    pasta = _pasta_param(h.corpo().get("pasta"))
    try:
        h._json({"plugin": plugins.analisar(pasta)})
    except plugins.ErroPlugin as e:
        raise Erro(400, str(e))


@rota("POST", "/api/plugins/instalar-pasta")
def r_plugin_instalar_pasta(h: Manipulador):
    pasta = _pasta_param(h.corpo().get("pasta"))
    try:
        h._json({"plugin": plugins.instalar_de_pasta(pasta)})
    except (plugins.ErroPlugin, OSError) as e:
        raise Erro(400, str(e))


@rota("POST", "/api/plugins/github")
def r_plugin_github(h: Manipulador):
    try:
        h._json(plugins.preparar_github(str(h.corpo().get("repositorio") or "")))
    except plugins.ErroPlugin as e:
        raise Erro(400, str(e))


@rota("POST", "/api/plugins/github/instalar")
def r_plugin_github_instalar(h: Manipulador):
    d = h.corpo()
    nomes = [str(n) for n in (d.get("nomes") or []) if isinstance(n, str)]
    if not nomes:
        raise Erro(400, t("Escolha pelo menos um plugin."))
    try:
        h._json({"instalados": plugins.instalar_preparado(str(d.get("id") or ""), nomes)})
    except (plugins.ErroPlugin, OSError) as e:
        raise Erro(400, str(e))


# ---------- rotinas ----------

def _rotina_publica(r: dict) -> dict:
    return {**r, "quando_texto": rotinas.descrever(r.get("quando") or {}), "rodando": rotinas.rodando(r["id"])}


@rota("GET", "/api/rotinas")
def r_rotinas(h: Manipulador):
    h._json({"rotinas": [_rotina_publica(r) for r in banco.listar_rotinas()],
             "windows": sys.platform == "win32"})


@rota("POST", "/api/rotinas")
def r_rotina_salvar(h: Manipulador):
    d = h.corpo()
    try:
        r = rotinas.salvar(d.get("id") or None, str(d.get("nome") or ""), d, bool(d.get("ligada", True)))
    except rotinas.ErroRotina as e:
        raise Erro(400, str(e))
    h._json({"rotina": _rotina_publica(r)})


@rota("DELETE", "/api/rotinas/<rid>")
def r_rotina_apagar(h: Manipulador, rid):
    rotinas.apagar(rid)
    h._json({"ok": True})


@rota("POST", "/api/rotinas/<rid>/rodar")
def r_rotina_rodar(h: Manipulador, rid):
    try:
        h._json(rotinas.rodar(rid, "manual"))
    except rotinas.ErroRotina as e:
        raise Erro(400, str(e))


@rota("GET", "/api/avisos")
def r_avisos(h: Manipulador):
    lista, total = rotinas.avisos_desde(int(h.query().get("desde") or 0))
    h._json({"avisos": lista, "total": total})


# ======================= principal =======================

_servidor: ThreadingHTTPServer | None = None


def _desligar(codigo: int) -> None:
    _codigo_saida["valor"] = codigo

    def parar():
        time.sleep(0.4)
        if _servidor:
            _servidor.shutdown()
    threading.Thread(target=parar, daemon=True).start()


def _vigia_inatividade(minutos: int) -> None:
    while True:
        time.sleep(30)
        if time.time() - _ultimo_sinal > minutos * 60 and not execucao.alguma_rodando():
            print("Sem a janela do Clave aberta há um tempo; fechando o servidor.", flush=True)
            _desligar(0)
            return


def _vigiar_janela(pid: int) -> None:
    """A janela do Electron morreu (fechada à força, travou)? Então o servidor fecha também."""
    import iniciar
    while True:
        time.sleep(3)
        if not iniciar.processo_vivo(pid):
            print("A janela do Clave não existe mais; fechando o servidor.", flush=True)
            for ex in list(execucao._execucoes.values()):
                ex.interromper()
            _desligar(0)
            time.sleep(5)
            os._exit(0)


def migrar_web_por_padrao() -> None:
    """3.1.0: a busca na web passou a vir ligada (o Claude decide quando pesquisar). Uma vez só, liga para quem já
    usava e tira o "desligado" que as conversas antigas gravaram junto das outras opções: era o padrão de antes,
    não uma escolha de quem usa."""
    if config.carregar().get("web_por_padrao_migrada"):
        return
    banco.tirar_ajuste("busca_web")
    config.salvar({"busca_web": True, "web_por_padrao_migrada": True})


def migrar_haiku_padrao() -> None:
    """5.0: o Haiku (o mais barato) vira o padrão também de quem já usava. A configuração antiga não diz se o modelo
    foi escolhido ou só ficou o padrão de antes, então os modelos anteriores ficam em aviso_haiku e a tela pergunta
    uma vez se a pessoa quer manter o Haiku ou voltar. Conversas e rotinas com modelo próprio não mudam."""
    cfg = config.carregar()
    if cfg.get("padrao_haiku_migrado"):
        return
    haiku = "claude-haiku-5-5"
    antes = {k: cfg.get(k) for k in ("modelo_chat", "modelo_code")}
    novo = {"padrao_haiku_migrado": True}
    if any(v and v != haiku for v in antes.values()):
        novo.update({"modelo_chat": haiku, "modelo_code": haiku})
        if cfg.get("configurado"):  # quem nunca terminou as boas-vindas não escolheu modelo nenhum: sem aviso
            novo["aviso_haiku"] = antes
    config.salvar(novo)


def main() -> int:
    global _servidor
    ap = argparse.ArgumentParser()
    ap.add_argument("--pai", type=int, default=0, help="PID da janela do Electron; se ela morrer, o servidor fecha")
    ap.add_argument("--porta", type=int, default=config.PORTA_PADRAO)
    ap.add_argument("--dados", help="pasta de dados (padrão: dados/ ao lado do app)")
    ap.add_argument("--demo", action="store_true", help="usa uma API de mentira, sem gastar nada")
    ap.add_argument("--sem-senha", action="store_true", help="dispensa o cookie de sessão (só para testes)")
    ap.add_argument("--fechar-sem-janela", type=int, default=0,
                    help="minutos sem a janela aberta até o servidor fechar sozinho (0 = nunca)")
    a = ap.parse_args()
    config.DADOS.mkdir(parents=True, exist_ok=True)
    banco.conexao()
    migrar_web_por_padrao()
    migrar_haiku_padrao()
    import videos
    videos.baixar_todos()  # os vídeos das lições que faltam, em segundo plano (aparecem na aba Tarefas)
    import mapas
    threading.Thread(target=lambda: (mapas.podar_tiles(), widgets.podar_imagens()), daemon=True).start()  # faxina dos caches
    _servidor = ThreadingHTTPServer(("127.0.0.1", a.porta), Manipulador)
    _servidor.daemon_threads = True
    print(f"Clave {config.VERSAO} em http://127.0.0.1:{a.porta}" + (" (modo demonstração)" if DEMO else ""),
          flush=True)
    if a.fechar_sem_janela:
        threading.Thread(target=_vigia_inatividade, args=(a.fechar_sem_janela,), daemon=True).start()
    if a.pai:
        threading.Thread(target=_vigiar_janela, args=(a.pai,), daemon=True).start()
    relogio = rotinas.Relogio()
    relogio.start()
    marca = config.DADOS / "servidor.json"  # o rodar_rotina.py do Agendador acha o app aberto por aqui
    try:
        marca.write_text(json.dumps({"porta": a.porta, "pid": os.getpid()}), encoding="utf-8")
    except OSError:
        pass
    try:
        _servidor.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        relogio.parar.set()
        _servidor.server_close()
        try:
            if json.loads(marca.read_text(encoding="utf-8")).get("pid") == os.getpid():
                marca.unlink()
        except (OSError, ValueError):
            pass
    return _codigo_saida["valor"]


if __name__ == "__main__":
    sys.exit(main())
