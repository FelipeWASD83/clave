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

import anexos  # noqa: E402
import atualizador  # noqa: E402
import banco  # noqa: E402
import config  # noqa: E402
import contexto_pasta  # noqa: E402
import execucao  # noqa: E402
import github_api  # noqa: E402
import modelo_pasta  # noqa: E402
import modelos  # noqa: E402
import orcamento  # noqa: E402
import segredos  # noqa: E402
import sistema  # noqa: E402
import tutoriais  # noqa: E402
from ferramentas import memoria  # noqa: E402

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


class Erro(Exception):
    def __init__(self, status: int, mensagem: str):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


ROTAS: list[tuple[str, re.Pattern, callable]] = []


def rota(metodo: str, padrao: str):
    rx = re.compile("^" + re.sub(r"<(\w+)>", r"(?P<\1>[^/]+)", padrao) + "$")

    def deco(fn):
        ROTAS.append((metodo, rx, fn))
        return fn
    return deco


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
            raise Erro(413, "Arquivo grande demais.")
        return self.rfile.read(n) if n else b""

    def corpo(self) -> dict:
        bruto = self.corpo_bruto(5 * 1024 * 1024)
        if not bruto:
            return {}
        try:
            d = json.loads(bruto)
        except ValueError:
            raise Erro(400, "JSON inválido.")
        if not isinstance(d, dict):
            raise Erro(400, "JSON inválido.")
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
                return self._json({"erro": "Host não permitido."}, 403)
            caminho = urllib.parse.urlparse(self.path).path
            if caminho.startswith("/api/"):
                if not self._sessao_ok():
                    return self._json({"erro": "Sessão inválida. Abra o Clave pelo atalho Clave.bat.",
                                       "codigo": "sessao"}, 401)
                if metodo != "GET" and not self._origem_ok():
                    return self._json({"erro": "Origem não permitida."}, 403)
                _ultimo_sinal = time.time()
                for m, rx, fn in ROTAS:
                    if m == metodo:
                        achou = rx.match(caminho)
                        if achou:
                            return fn(self, **achou.groupdict())
                return self._json({"erro": "Rota não encontrada."}, 404)
            if caminho.startswith("/previa/") and metodo == "GET":
                return self._previa(caminho.rsplit("/", 1)[-1])
            if metodo != "GET":
                return self._json({"erro": "Método não permitido."}, 405)
            return self._estatico(caminho)
        except Erro as e:
            self._json({"erro": e.mensagem}, e.status)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception as e:
            traceback.print_exc()
            try:
                self._json({"erro": f"Erro interno: {e}"}, 500)
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
            return self._bytes("Prévia expirada. Abra de novo pela conversa.".encode(), "text/plain; charset=utf-8",
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
        "orcamento": orcamento.situacao(),
        "modelos": modelos.lista_publica(cfg.get("modelos_antigos"), _modelos_cache["lista"]),
        "esforcos": [{"id": e, "nome": modelos.NOMES_ESFORCO[e]} for e in modelos.ESFORCOS],
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
        raise Erro(400, "Essa não parece uma chave da API da Anthropic (ela começa com sk-ant-).")
    import anthropic
    try:
        cli = anthropic.Anthropic(api_key=chave, max_retries=1, timeout=30)
        ids = [m.id for m in cli.models.list(limit=100).data]
    except anthropic.AuthenticationError:
        raise Erro(400, "A Anthropic recusou essa chave. Confira se copiou inteira e se ela não foi apagada.")
    except anthropic.APIConnectionError:
        raise Erro(400, "Sem conexão com a Anthropic para conferir a chave. Confira a internet.")
    except anthropic.APIStatusError as e:
        raise Erro(400, f"A Anthropic respondeu {e.status_code} ao conferir a chave.")
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
                raise Erro(400, f"Valor inválido em {k}.")
            lo, hi = CAMPOS_NUMERICOS[k]
            v = max(lo, min(hi, v))
            if k in ("dia_virada", "compactar_em", "tamanho_letra"):
                v = int(v)
        limpo[k] = v
    cfg = config.salvar(limpo)
    h._json({"cfg": _cfg_publica(cfg), "estilos": config.estilos(cfg), "orcamento": orcamento.situacao()})


@rota("DELETE", "/api/compat")
def r_compat(h: Manipulador):
    """Religa os recursos opcionais que foram desligados depois de um erro da API."""
    import pedido
    pedido.religar_tudo()
    h._json({"ok": True})


@rota("POST", "/api/conectores/token")
def r_conector_token(h: Manipulador):
    d = h.corpo()
    nome = re.sub(r"[^\w-]", "-", str(d.get("nome") or ""))
    if not nome:
        raise Erro(400, "Conector sem nome.")
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
            raise Erro(400, "Escolha uma pasta que exista para o modo Code.")
        pasta = str(Path(pasta).resolve())
        cfg = config.carregar()
        recentes = [pasta] + [p for p in cfg.get("pastas_recentes") or [] if p != pasta]
        config.salvar({"pastas_recentes": recentes[:12]})
    projeto_id = d.get("projeto_id") or None
    if projeto_id and not banco.projeto(projeto_id):
        raise Erro(404, "Projeto não encontrado.")
    c = banco.criar_conversa(modo=modo, projeto_id=projeto_id, pasta=pasta)
    h._json({"conversa": c})


def _montar_visao(cid: str) -> dict:
    conv = banco.conversa(cid)
    if not conv:
        raise Erro(404, "Conversa não encontrada.")
    caminho = banco.caminho(cid)
    for m in caminho:
        if m["papel"] == "user" and m["tipo"] == "normal" or m["papel"] == "assistant":
            irmaos = [f for f in banco.filhos(cid, m["pai_id"]) if f["papel"] == m["papel"] and f["tipo"] == m["tipo"]]
            m["irmaos"] = [f["id"] for f in irmaos]
    ex = execucao.ativa(cid)
    projeto = banco.projeto(conv["projeto_id"]) if conv.get("projeto_id") else None
    pendentes = []
    if ex:
        for ev in list(ex.eventos):
            if ev["tipo"] == "aprovacao" and not ex.aprovacoes.get(ev["id"], {}).get("evento").is_set():
                pendentes.append(ev)
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
        raise Erro(404, "Conversa não encontrada.")
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
    banco.atualizar_conversa(cid, **campos)
    h._json({"conversa": banco.conversa(cid)})


@rota("DELETE", "/api/conversas/<cid>")
def r_conversa_apagar(h: Manipulador, cid):
    if execucao.ativa(cid):
        raise Erro(409, "Pare a resposta antes de apagar a conversa.")
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


def _conteudo_usuario(conv: dict, texto: str, ids_anexos: list) -> tuple[list, dict]:
    blocos = []
    for aid in ids_anexos or []:
        reg = banco.anexo(aid)
        if reg:
            blocos.append(anexos.referencia(reg))
    meta = {}
    texto = texto or ""
    m = re.match(r"^/([\w.-]+)\s*(.*)$", texto.strip(), re.S)
    if conv["modo"] == "code" and m:
        lista = contexto_pasta.skills(conv["pasta"])
        s = contexto_pasta.conteudo_skill(lista, m.group(1))
        if s:
            meta["exibir"] = texto
            meta["skill"] = s["nome"]
            texto = (f"Quem usa chamou a skill /{s['nome']}. Siga as instruções dela.\n"
                     f"<skill nome=\"{s['nome']}\" pasta=\"{s['pasta']}\">\n{s['texto']}\n</skill>\n\n"
                     f"Pedido: {m.group(2).strip() or '(nenhum detalhe extra; siga a skill)'}")
    if texto.strip():
        blocos.append({"type": "text", "text": texto})
    if not blocos:
        raise Erro(400, "Mensagem vazia.")
    return blocos, meta


def _opcoes(d: dict) -> dict:
    o = d.get("opcoes") or {}
    permitido = {"modelo", "esforco", "pensar", "mostrar_raciocinio", "busca_web", "github", "rapido", "permissao"}
    return {k: v for k, v in o.items() if k in permitido}


@rota("POST", "/api/conversas/<cid>/enviar")
def r_enviar(h: Manipulador, cid):
    d = h.corpo()
    conv = banco.conversa(cid)
    if not conv:
        raise Erro(404, "Conversa não encontrada.")
    if execucao.ativa(cid):
        raise Erro(409, "Esta conversa ainda está respondendo.")
    ok, motivo = orcamento.pode_gastar()
    if not ok:
        raise Erro(402, motivo)
    if not segredos.existe("anthropic") and not DEMO:
        raise Erro(400, "Falta a chave da API. Cole a sua em Configurações > Conta e chave.")
    _preparar_sistema(conv)
    conv = banco.conversa(cid)
    conteudo, meta = _conteudo_usuario(conv, d.get("texto", ""), d.get("anexos") or [])
    pai = conv.get("folha_id")
    if d.get("editar_de"):
        original = banco.mensagem(d["editar_de"])
        if not original or original["conversa_id"] != cid:
            raise Erro(404, "Mensagem não encontrada.")
        pai = original["pai_id"]
    msg = banco.adicionar_mensagem(cid, pai, "user", conteudo, meta=meta)
    ex = execucao.iniciar(cid, _opcoes(d))
    banco.atualizar_conversa(cid, ajustes={**(conv.get("ajustes") or {}), **_opcoes(d)})
    h._json({"execucao": ex.id, "mensagem": msg["id"]})


@rota("POST", "/api/conversas/<cid>/regenerar")
def r_regenerar(h: Manipulador, cid):
    d = h.corpo()
    if execucao.ativa(cid):
        raise Erro(409, "Esta conversa ainda está respondendo.")
    ok, motivo = orcamento.pode_gastar()
    if not ok:
        raise Erro(402, motivo)
    m = banco.mensagem(d.get("mensagem_id") or "")
    if not m or m["conversa_id"] != cid:
        raise Erro(404, "Mensagem não encontrada.")
    while m and not (m["papel"] == "user" and m["tipo"] == "normal"):
        m = banco.mensagem(m["pai_id"]) if m["pai_id"] else None
    if not m:
        raise Erro(400, "Não achei a pergunta dessa resposta.")
    banco.atualizar_conversa(cid, folha_id=m["id"])
    ex = execucao.iniciar(cid, _opcoes(d))
    h._json({"execucao": ex.id})


@rota("POST", "/api/conversas/<cid>/folha")
def r_folha(h: Manipulador, cid):
    d = h.corpo()
    m = banco.mensagem(d.get("mensagem_id") or "")
    if not m or m["conversa_id"] != cid:
        raise Erro(404, "Mensagem não encontrada.")
    if execucao.ativa(cid):
        raise Erro(409, "Espere a resposta terminar para trocar de versão.")
    banco.atualizar_conversa(cid, folha_id=banco.folha_mais_recente(cid, m["id"]))
    h._json(_montar_visao(cid))


@rota("GET", "/api/conversas/<cid>/exportar")
def r_exportar(h: Manipulador, cid):
    v = _montar_visao(cid)
    linhas = [f"# {v['conversa'].get('titulo') or 'Conversa'}", ""]
    for m in v["mensagens"]:
        if m["tipo"] != "normal":
            continue
        quem = "Você" if m["papel"] == "user" else "Claude"
        partes = []
        if (m.get("meta") or {}).get("exibir"):
            partes.append(m["meta"]["exibir"])
        elif isinstance(m["conteudo"], list):
            for b in m["conteudo"]:
                if b.get("type") == "text":
                    partes.append(b["text"])
                elif b.get("type") == "clave_anexo":
                    partes.append(f"[anexo: {b.get('nome')}]")
        if partes:
            linhas += [f"## {quem}", "", "\n\n".join(partes), ""]
    corpo = "\n".join(linhas).encode("utf-8")
    nome = re.sub(r"[^\w\- ]", "", v["conversa"].get("titulo") or "conversa")[:60] or "conversa"
    h._bytes(corpo, "text/markdown; charset=utf-8",
             cab={"Content-Disposition": f"attachment; filename*=UTF-8''{urllib.parse.quote(nome)}.md"})


# ---------- ajudantes (lições no Haiku, editor de memória no Sonnet) ----------

@rota("POST", "/api/ajudantes/<tipo>")
def r_ajudante(h: Manipulador, tipo):
    d = h.corpo()
    if tipo == "tutor":
        slug = str(d.get("licao") or "")
        t = tutoriais.ler(slug)
        if not t:
            raise Erro(404, "Lição não encontrada.")
        chave, titulo, ajustes = f"tutor:{slug}", f"Dúvidas: {t['titulo']}", {"licao": slug}
    elif tipo == "memoria":
        chave, titulo, ajustes = "memoria", "Editor de memória", {}
    else:
        raise Erro(404, "Ajudante desconhecido.")
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
        raise Erro(404, "Execução não encontrada.")
    desde = int(h.query().get("desde") or 0)
    h.send_response(200)
    h.send_header("Content-Type", "text/event-stream; charset=utf-8")
    h.send_header("Cache-Control", "no-store")
    h.send_header("Connection", "close")
    h.end_headers()
    h.close_connection = True
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
        raise Erro(404, "Execução não encontrada.")
    decisao = d.get("decisao")
    if decisao not in ("permitir", "permitir_sempre", "recusar"):
        raise Erro(400, "Decisão inválida.")
    if not ex.decidir(str(d.get("id")), decisao, str(d.get("texto") or "")[:2000]):
        raise Erro(409, "Essa ação não está mais esperando resposta.")
    h._json({"ok": True})


@rota("POST", "/api/execucoes/<eid>/desfazer")
def r_desfazer(h: Manipulador, eid):
    if execucao.pegar(eid) and execucao.pegar(eid).status in ("rodando", "esperando"):
        raise Erro(409, "Pare a tarefa antes de desfazer.")
    h._json({"arquivos": execucao.desfazer(eid)})


# ---------- anexos ----------

def _receber_arquivo(h: Manipulador, projeto_id=None):
    nome = urllib.parse.unquote(h.headers.get("X-Nome-Arquivo") or "arquivo")
    dados = h.corpo_bruto()
    if not dados:
        raise Erro(400, "Arquivo vazio.")
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
        raise Erro(404, "Anexo não encontrado.")
    try:
        dados = anexos.caminho(aid).read_bytes()
    except OSError:
        raise Erro(404, "O arquivo do anexo sumiu.")
    cab = {"Cache-Control": "max-age=86400", "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "sandbox"}
    if h.query().get("baixar") == "1":
        cab["Content-Disposition"] = f"attachment; filename*=UTF-8''{urllib.parse.quote(reg['nome'])}"
        return h._bytes(dados, reg["tipo"], cab=cab)
    tipo = reg["tipo"] if reg["tipo"].startswith("image/") else "text/plain; charset=utf-8"
    if reg["tipo"] == "application/pdf":
        tipo = "application/pdf"
    h._bytes(dados, tipo, cab=cab)


@rota("POST", "/api/anexos/<aid>/abrir")
def r_anexo_abrir(h: Manipulador, aid):
    """Abre uma cópia do arquivo (planilha, PDF) no programa do computador."""
    reg = banco.anexo(aid)
    if not reg:
        raise Erro(404, "Arquivo não encontrado.")
    # a extensão vem do tipo conferido, nunca do nome: um "texto" chamado x.bat não pode virar programa
    extensao = {anexos.MIME_XLSX: ".xlsx", "application/pdf": ".pdf", "image/png": ".png", "image/jpeg": ".jpg",
                "image/gif": ".gif", "image/webp": ".webp", "text/plain": ".txt"}.get(reg["tipo"])
    if not extensao:
        raise Erro(400, "Esse tipo de arquivo não é aberto pelo Clave.")
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
        raise Erro(400, f"Não deu para abrir: {e}")
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
        raise Erro(400, "Dê um nome ao projeto.")
    h._json({"projeto": banco.criar_projeto(nome[:80], (d.get("descricao") or "")[:2000],
                                            (d.get("instrucoes") or "")[:50000])})


@rota("GET", "/api/projetos/<pid>")
def r_projeto(h: Manipulador, pid):
    p = banco.projeto(pid)
    if not p:
        raise Erro(404, "Projeto não encontrado.")
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
        raise Erro(404, "Projeto não encontrado.")
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
        raise Erro(400, "Valor inválido.")
    cfg = config.carregar()
    ajustes = dict(cfg.get("ajustes") or {})
    ajustes[orcamento.situacao()["chave"]] = max(0.0, valor)
    config.salvar({"ajustes": ajustes})
    h._json({"orcamento": orcamento.situacao()})


# ---------- memória ----------

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
        raise Erro(404, "Pasta não encontrada.")
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
        raise Erro(403, f"Sem acesso a essa pasta ({e.strerror}).")
    pai = str(p.parent) if p.parent != p else ("::discos" if sys.platform == "win32" else None)
    atalhos = [{"nome": "Pasta pessoal", "caminho": str(Path.home())}]
    for nome in ("Desktop", "Documents", "Downloads", "Área de Trabalho", "Documentos"):
        alvo = Path.home() / nome
        if alvo.is_dir():
            atalhos.append({"nome": nome, "caminho": str(alvo)})
    h._json({"caminho": str(p), "pai": pai, "pastas": pastas[:500], "atalhos": atalhos})


@rota("GET", "/api/pasta-info")
def r_pasta_info(h: Manipulador):
    caminho = h.query().get("caminho") or ""
    if not caminho or not Path(caminho).is_dir():
        raise Erro(404, "Pasta não encontrada.")
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
            raise Erro(400, "O gh não está instalado ou não está logado. Rode 'gh auth login' no terminal, "
                            "ou use um token pessoal.")
    elif origem == "token":
        tok = (d.get("token") or "").strip()
        if not tok:
            raise Erro(400, "Cole o token.")
    elif origem in ("", None):
        config.salvar({"github_origem": "", "github_ferramentas": False})
        segredos.apagar("github_token")
        return h._json({"ok": True})
    else:
        raise Erro(400, "Origem inválida.")
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
    t = tutoriais.ler(slug)
    if not t:
        raise Erro(404, "Tutorial não encontrado.")
    h._json(t)


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
        raise Erro(409, "Espere as respostas em andamento terminarem antes de atualizar.")
    if os.environ.get("CLAVE_LANCADOR") != "1":
        raise Erro(400, "Para atualizar, abra o Clave pelo atalho Clave.bat (ele reinicia o app depois).")
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


# ---------- prévia e backup ----------

@rota("POST", "/api/previa")
def r_previa(h: Manipulador):
    d = h.corpo()
    html = str(d.get("html") or "")
    if d.get("tipo") == "svg":
        html = ("<!doctype html><meta charset=utf-8><style>html,body{margin:0;height:100%;display:grid;"
                "place-items:center;background:#fff}svg{max-width:100%;max-height:100vh}</style>" + html)
    agora = time.time()
    for k, (t, _) in list(_previas.items()):
        if agora - t > 3600:
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
    _servidor = ThreadingHTTPServer(("127.0.0.1", a.porta), Manipulador)
    _servidor.daemon_threads = True
    print(f"Clave {config.VERSAO} em http://127.0.0.1:{a.porta}" + (" (modo demonstração)" if DEMO else ""),
          flush=True)
    if a.fechar_sem_janela:
        threading.Thread(target=_vigia_inatividade, args=(a.fechar_sem_janela,), daemon=True).start()
    if a.pai:
        threading.Thread(target=_vigiar_janela, args=(a.pai,), daemon=True).start()
    try:
        _servidor.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        _servidor.server_close()
    return _codigo_saida["valor"]


if __name__ == "__main__":
    sys.exit(main())
