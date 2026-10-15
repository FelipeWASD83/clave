"""Banco SQLite do Clave (dados/clave.db): conversas, mensagens, projetos, uso e anexos.

As mensagens formam uma árvore: editar uma mensagem ou pedir outra resposta cria
um irmão, e a conversa guarda qual folha está ativa. O caminho da raiz até a
folha é o histórico que vai para a API.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone

from config import DADOS

_local = threading.local()
_trava_escrita = threading.RLock()

ESQUEMA = """
CREATE TABLE IF NOT EXISTS conversas (
    id TEXT PRIMARY KEY,
    titulo TEXT NOT NULL DEFAULT '',
    modo TEXT NOT NULL DEFAULT 'chat',
    projeto_id TEXT,
    pasta TEXT,
    folha_id TEXT,
    fixada INTEGER NOT NULL DEFAULT 0,
    arquivada INTEGER NOT NULL DEFAULT 0,
    sistema TEXT,
    contexto_json TEXT,
    ajustes_json TEXT,
    criada_em REAL NOT NULL,
    atualizada_em REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS mensagens (
    id TEXT PRIMARY KEY,
    conversa_id TEXT NOT NULL,
    pai_id TEXT,
    papel TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'normal',
    conteudo_json TEXT NOT NULL,
    modelo TEXT,
    uso_json TEXT,
    custo_usd REAL NOT NULL DEFAULT 0,
    meta_json TEXT,
    execucao_id TEXT,
    criada_em REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_msg_conversa ON mensagens(conversa_id);
CREATE INDEX IF NOT EXISTS ix_msg_pai ON mensagens(pai_id);
CREATE TABLE IF NOT EXISTS uso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criado_em REAL NOT NULL,
    conversa_id TEXT,
    mensagem_id TEXT,
    modelo TEXT,
    origem TEXT NOT NULL DEFAULT 'chat',
    entrada INTEGER NOT NULL DEFAULT 0,
    cache_escrita INTEGER NOT NULL DEFAULT 0,
    cache_leitura INTEGER NOT NULL DEFAULT 0,
    saida INTEGER NOT NULL DEFAULT 0,
    buscas INTEGER NOT NULL DEFAULT 0,
    custo_usd REAL NOT NULL DEFAULT 0,
    estimado INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_uso_data ON uso(criado_em);
CREATE TABLE IF NOT EXISTS projetos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT NOT NULL DEFAULT '',
    instrucoes TEXT NOT NULL DEFAULT '',
    criado_em REAL NOT NULL,
    atualizado_em REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS anexos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    tipo TEXT NOT NULL,
    tamanho INTEGER NOT NULL,
    projeto_id TEXT,
    origem TEXT NOT NULL DEFAULT 'upload',
    criado_em REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_anexo_projeto ON anexos(projeto_id);
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execucao_id TEXT NOT NULL,
    conversa_id TEXT NOT NULL,
    caminho TEXT NOT NULL,
    existia INTEGER NOT NULL,
    conteudo BLOB,
    desfeito INTEGER NOT NULL DEFAULT 0,
    criado_em REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_ck_exec ON checkpoints(execucao_id);
CREATE TABLE IF NOT EXISTS permissoes_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criado_em REAL NOT NULL,
    conversa_id TEXT,
    execucao_id TEXT,
    ferramenta TEXT NOT NULL,
    alvo TEXT,
    decisao TEXT NOT NULL,
    origem TEXT,
    regra TEXT
);
CREATE INDEX IF NOT EXISTS ix_plog_data ON permissoes_log(criado_em);
CREATE TABLE IF NOT EXISTS fluxos (
    id TEXT PRIMARY KEY,
    conversa_id TEXT,
    execucao_id TEXT,
    titulo TEXT NOT NULL DEFAULT '',
    dados_json TEXT NOT NULL,
    status TEXT NOT NULL,
    custo_usd REAL NOT NULL DEFAULT 0,
    criado_em REAL NOT NULL,
    atualizado_em REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_fluxo_conv ON fluxos(conversa_id);
CREATE TABLE IF NOT EXISTS rotinas (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    dados_json TEXT NOT NULL,
    ligada INTEGER NOT NULL DEFAULT 1,
    proxima REAL,
    ultima REAL,
    ultimo_status TEXT,
    ultima_conversa TEXT,
    criado_em REAL NOT NULL,
    atualizado_em REAL NOT NULL
);
"""


def novo_id() -> str:
    return uuid.uuid4().hex[:16]


def agora() -> float:
    return time.time()


def conexao() -> sqlite3.Connection:
    con = getattr(_local, "con", None)
    if con is None:
        DADOS.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(DADOS / "clave.db", timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript(ESQUEMA)
        _local.con = con
    return con


def _j(texto):
    return json.loads(texto) if texto else None


# ---------- conversas ----------

def criar_conversa(modo="chat", projeto_id=None, pasta=None, titulo="", ajustes=None) -> dict:
    cid = novo_id()
    t = agora()
    with _trava_escrita:
        con = conexao()
        con.execute(
            "INSERT INTO conversas (id, titulo, modo, projeto_id, pasta, ajustes_json, criada_em, atualizada_em) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (cid, titulo, modo, projeto_id, pasta, json.dumps(ajustes or {}, ensure_ascii=False), t, t),
        )
        con.commit()
    return conversa(cid)


def conversa(cid: str) -> dict | None:
    r = conexao().execute("SELECT * FROM conversas WHERE id=?", (cid,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["contexto"] = _j(d.pop("contexto_json")) or []
    d["ajustes"] = _j(d.pop("ajustes_json")) or {}
    return d


def listar_conversas(busca: str = "", projeto_id: str | None = None, arquivadas=False, limite=500) -> list[dict]:
    sql = ("SELECT id, titulo, modo, projeto_id, pasta, fixada, arquivada, criada_em, atualizada_em FROM conversas "
           "WHERE arquivada=? AND modo IN ('chat', 'code')")
    args: list = [1 if arquivadas else 0]
    if projeto_id:
        sql += " AND projeto_id=?"
        args.append(projeto_id)
    if busca:
        sql += (" AND (titulo LIKE ? OR id IN (SELECT conversa_id FROM mensagens WHERE tipo='normal' "
                "AND conteudo_json LIKE ?))")
        args += [f"%{busca}%", f"%{busca}%"]
    sql += " ORDER BY fixada DESC, atualizada_em DESC LIMIT ?"
    args.append(limite)
    return [dict(r) for r in conexao().execute(sql, args).fetchall()]


def atualizar_conversa(cid: str, **campos) -> None:
    mapa = {}
    for k, v in campos.items():
        if k == "contexto":
            mapa["contexto_json"] = json.dumps(v, ensure_ascii=False)
        elif k == "ajustes":
            mapa["ajustes_json"] = json.dumps(v, ensure_ascii=False)
        elif k in ("titulo", "modo", "projeto_id", "pasta", "folha_id", "fixada", "arquivada", "sistema"):
            mapa[k] = v
    if not mapa:
        return
    mapa["atualizada_em"] = agora()
    cols = ", ".join(f"{k}=?" for k in mapa)
    with _trava_escrita:
        con = conexao()
        con.execute(f"UPDATE conversas SET {cols} WHERE id=?", (*mapa.values(), cid))
        con.commit()


def apagar_conversa(cid: str) -> None:
    with _trava_escrita:
        con = conexao()
        con.execute("DELETE FROM mensagens WHERE conversa_id=?", (cid,))
        con.execute("DELETE FROM checkpoints WHERE conversa_id=?", (cid,))
        con.execute("DELETE FROM conversas WHERE id=?", (cid,))
        con.commit()


# ---------- mensagens ----------

def adicionar_mensagem(cid: str, pai_id: str | None, papel: str, conteudo, tipo="normal", modelo=None,
                       uso=None, custo_usd=0.0, meta=None, execucao_id=None, virar_folha=True) -> dict:
    mid = novo_id()
    with _trava_escrita:
        con = conexao()
        con.execute(
            "INSERT INTO mensagens (id, conversa_id, pai_id, papel, tipo, conteudo_json, modelo, uso_json, custo_usd, "
            "meta_json, execucao_id, criada_em) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (mid, cid, pai_id, papel, tipo, json.dumps(conteudo, ensure_ascii=False), modelo,
             json.dumps(uso) if uso else None, custo_usd, json.dumps(meta, ensure_ascii=False) if meta else None,
             execucao_id, agora()),
        )
        if virar_folha:
            con.execute("UPDATE conversas SET folha_id=?, atualizada_em=? WHERE id=?", (mid, agora(), cid))
        con.commit()
    return mensagem(mid)


def atualizar_meta(mid: str, meta: dict) -> None:
    with _trava_escrita:
        con = conexao()
        con.execute("UPDATE mensagens SET meta_json=? WHERE id=?", (json.dumps(meta, ensure_ascii=False), mid))
        con.commit()


def mensagem(mid: str) -> dict | None:
    r = conexao().execute("SELECT * FROM mensagens WHERE id=?", (mid,)).fetchone()
    return _msg(r) if r else None


def _msg(r) -> dict:
    d = dict(r)
    d["conteudo"] = _j(d.pop("conteudo_json"))
    d["uso"] = _j(d.pop("uso_json"))
    d["meta"] = _j(d.pop("meta_json")) or {}
    return d


def caminho(cid: str, folha_id: str | None = None) -> list[dict]:
    """Mensagens da raiz até a folha (inclusive)."""
    if folha_id is None:
        c = conversa(cid)
        folha_id = c and c.get("folha_id")
    if not folha_id:
        return []
    todas = {r["id"]: r for r in conexao().execute("SELECT * FROM mensagens WHERE conversa_id=?", (cid,)).fetchall()}
    saida = []
    atual = todas.get(folha_id)
    vistos = set()
    while atual is not None and atual["id"] not in vistos:
        vistos.add(atual["id"])
        saida.append(_msg(atual))
        atual = todas.get(atual["pai_id"]) if atual["pai_id"] else None
    saida.reverse()
    return saida


def filhos(cid: str, pai_id: str | None) -> list[dict]:
    if pai_id is None:
        rs = conexao().execute(
            "SELECT id, papel, tipo, criada_em FROM mensagens WHERE conversa_id=? AND pai_id IS NULL ORDER BY criada_em",
            (cid,)).fetchall()
    else:
        rs = conexao().execute(
            "SELECT id, papel, tipo, criada_em FROM mensagens WHERE conversa_id=? AND pai_id=? ORDER BY criada_em",
            (cid, pai_id)).fetchall()
    return [dict(r) for r in rs]


def folha_mais_recente(cid: str, a_partir_de: str) -> str:
    """Desce pela árvore a partir de uma mensagem, sempre pelo filho mais novo."""
    atual = a_partir_de
    while True:
        r = conexao().execute(
            "SELECT id FROM mensagens WHERE conversa_id=? AND pai_id=? ORDER BY criada_em DESC LIMIT 1",
            (cid, atual)).fetchone()
        if not r:
            return atual
        atual = r["id"]


# ---------- uso (gasto) ----------

def registrar_uso(conversa_id, mensagem_id, modelo, origem, c: dict) -> None:
    with _trava_escrita:
        con = conexao()
        con.execute(
            "INSERT INTO uso (criado_em, conversa_id, mensagem_id, modelo, origem, entrada, cache_escrita, cache_leitura, "
            "saida, buscas, custo_usd, estimado) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (agora(), conversa_id, mensagem_id, modelo, origem, c.get("entrada", 0), c.get("cache_escrita", 0),
             c.get("cache_leitura", 0), c.get("saida", 0), c.get("buscas", 0), c.get("usd", 0.0),
             1 if c.get("estimado") else 0),
        )
        con.commit()


def gasto_entre(inicio: float, fim: float) -> float:
    r = conexao().execute("SELECT COALESCE(SUM(custo_usd),0) AS s FROM uso WHERE criado_em>=? AND criado_em<?",
                          (inicio, fim)).fetchone()
    return float(r["s"])


def uso_detalhado(inicio: float, fim: float) -> dict:
    con = conexao()
    por_dia = [dict(r) for r in con.execute(
        "SELECT date(criado_em,'unixepoch','localtime') AS dia, SUM(custo_usd) AS usd, COUNT(*) AS pedidos "
        "FROM uso WHERE criado_em>=? AND criado_em<? GROUP BY dia ORDER BY dia", (inicio, fim))]
    por_modelo = [dict(r) for r in con.execute(
        "SELECT modelo, SUM(custo_usd) AS usd, COUNT(*) AS pedidos, SUM(entrada) AS entrada, SUM(saida) AS saida, "
        "SUM(cache_leitura) AS cache_leitura, SUM(cache_escrita) AS cache_escrita, SUM(buscas) AS buscas "
        "FROM uso WHERE criado_em>=? AND criado_em<? GROUP BY modelo ORDER BY usd DESC", (inicio, fim))]
    por_conversa = [dict(r) for r in con.execute(
        "SELECT u.conversa_id, COALESCE(c.titulo,'') AS titulo, c.modo AS modo, SUM(u.custo_usd) AS usd, COUNT(*) AS pedidos "
        "FROM uso u LEFT JOIN conversas c ON c.id=u.conversa_id WHERE u.criado_em>=? AND u.criado_em<? "
        "GROUP BY u.conversa_id ORDER BY usd DESC LIMIT 30", (inicio, fim))]
    por_origem = [dict(r) for r in con.execute(
        "SELECT origem, SUM(custo_usd) AS usd, COUNT(*) AS pedidos FROM uso WHERE criado_em>=? AND criado_em<? "
        "GROUP BY origem ORDER BY usd DESC", (inicio, fim))]
    return {"por_dia": por_dia, "por_modelo": por_modelo, "por_conversa": por_conversa, "por_origem": por_origem}


def gasto_conversa(cid: str) -> float:
    r = conexao().execute("SELECT COALESCE(SUM(custo_usd),0) AS s FROM uso WHERE conversa_id=?", (cid,)).fetchone()
    return float(r["s"])


# ---------- projetos ----------

def criar_projeto(nome: str, descricao="", instrucoes="") -> dict:
    pid = novo_id()
    t = agora()
    with _trava_escrita:
        con = conexao()
        con.execute("INSERT INTO projetos (id, nome, descricao, instrucoes, criado_em, atualizado_em) VALUES (?,?,?,?,?,?)",
                    (pid, nome, descricao, instrucoes, t, t))
        con.commit()
    return projeto(pid)


def projeto(pid: str) -> dict | None:
    r = conexao().execute("SELECT * FROM projetos WHERE id=?", (pid,)).fetchone()
    if not r:
        return None
    d = dict(r)
    d["arquivos"] = [dict(a) for a in conexao().execute(
        "SELECT id, nome, tipo, tamanho, criado_em FROM anexos WHERE projeto_id=? ORDER BY criado_em", (pid,))]
    return d


def listar_projetos() -> list[dict]:
    return [dict(r) for r in conexao().execute(
        "SELECT p.*, (SELECT COUNT(*) FROM conversas c WHERE c.projeto_id=p.id AND c.arquivada=0) AS conversas "
        "FROM projetos p ORDER BY atualizado_em DESC")]


def atualizar_projeto(pid: str, **campos) -> None:
    mapa = {k: v for k, v in campos.items() if k in ("nome", "descricao", "instrucoes")}
    if not mapa:
        return
    mapa["atualizado_em"] = agora()
    cols = ", ".join(f"{k}=?" for k in mapa)
    with _trava_escrita:
        con = conexao()
        con.execute(f"UPDATE projetos SET {cols} WHERE id=?", (*mapa.values(), pid))
        con.commit()


def apagar_projeto(pid: str) -> list[str]:
    """Apaga o projeto; as conversas dele ficam, soltas. Devolve os ids dos arquivos para apagar do disco."""
    with _trava_escrita:
        con = conexao()
        ids = [r["id"] for r in con.execute("SELECT id FROM anexos WHERE projeto_id=?", (pid,))]
        con.execute("DELETE FROM anexos WHERE projeto_id=?", (pid,))
        con.execute("UPDATE conversas SET projeto_id=NULL WHERE projeto_id=?", (pid,))
        con.execute("DELETE FROM projetos WHERE id=?", (pid,))
        con.commit()
    return ids


# ---------- anexos ----------

def registrar_anexo(nome: str, tipo: str, tamanho: int, projeto_id=None, origem="upload") -> dict:
    aid = novo_id()
    with _trava_escrita:
        con = conexao()
        con.execute("INSERT INTO anexos (id, nome, tipo, tamanho, projeto_id, origem, criado_em) VALUES (?,?,?,?,?,?,?)",
                    (aid, nome, tipo, tamanho, projeto_id, origem, agora()))
        con.commit()
    return anexo(aid)


def anexo(aid: str) -> dict | None:
    r = conexao().execute("SELECT * FROM anexos WHERE id=?", (aid,)).fetchone()
    return dict(r) if r else None


def apagar_anexo(aid: str) -> None:
    with _trava_escrita:
        con = conexao()
        con.execute("DELETE FROM anexos WHERE id=?", (aid,))
        con.commit()


# ---------- checkpoints do modo Code ----------

def guardar_checkpoint(execucao_id, conversa_id, caminho_arquivo: str, existia: bool, conteudo: bytes | None) -> None:
    with _trava_escrita:
        con = conexao()
        ja = con.execute("SELECT 1 FROM checkpoints WHERE execucao_id=? AND caminho=?",
                         (execucao_id, caminho_arquivo)).fetchone()
        if ja:
            return  # só a versão de antes da primeira mudança importa
        con.execute("INSERT INTO checkpoints (execucao_id, conversa_id, caminho, existia, conteudo, criado_em) "
                    "VALUES (?,?,?,?,?,?)", (execucao_id, conversa_id, caminho_arquivo, 1 if existia else 0,
                                             conteudo, agora()))
        con.commit()


def checkpoints(execucao_id: str) -> list[dict]:
    return [dict(r) for r in conexao().execute(
        "SELECT id, caminho, existia, desfeito, conteudo FROM checkpoints WHERE execucao_id=? ORDER BY id",
        (execucao_id,))]


def marcar_desfeito(execucao_id: str) -> None:
    with _trava_escrita:
        con = conexao()
        con.execute("UPDATE checkpoints SET desfeito=1 WHERE execucao_id=?", (execucao_id,))
        con.commit()


# ---------- exportar ----------

def exportar_tudo() -> dict:
    con = conexao()
    return {
        "formato": "clave-backup-1",
        "exportado_em": datetime.now(timezone.utc).isoformat(),
        "conversas": [dict(r) for r in con.execute("SELECT * FROM conversas")],
        "mensagens": [dict(r) for r in con.execute("SELECT * FROM mensagens")],
        "projetos": [dict(r) for r in con.execute("SELECT * FROM projetos")],
        "uso": [dict(r) for r in con.execute("SELECT * FROM uso")],
        "rotinas": [dict(r) for r in con.execute("SELECT * FROM rotinas")],
    }


def importar_tudo(dados: dict) -> dict:
    if dados.get("formato") != "clave-backup-1":
        raise ValueError("Arquivo não é um backup do Clave.")
    cont = {}
    with _trava_escrita:
        con = conexao()
        for tabela in ("conversas", "mensagens", "projetos", "uso", "rotinas"):
            linhas = dados.get(tabela) or []
            colunas = {r["name"] for r in con.execute(f"PRAGMA table_info({tabela})")}
            n = 0
            for linha in linhas:
                if not isinstance(linha, dict):
                    continue
                # só colunas que existem: nome de coluna vindo do arquivo nunca vai cru para o SQL
                linha = {k: v for k, v in linha.items() if k in colunas}
                if not linha:
                    continue
                if tabela == "uso":
                    linha = {k: v for k, v in linha.items() if k != "id"}
                    if con.execute("SELECT 1 FROM uso WHERE criado_em=? AND COALESCE(mensagem_id,'')=?",
                                   (linha.get("criado_em"), linha.get("mensagem_id") or "")).fetchone():
                        continue
                cols = ", ".join(linha)
                marc = ", ".join("?" for _ in linha)
                cur = con.execute(f"INSERT OR IGNORE INTO {tabela} ({cols}) VALUES ({marc})", tuple(linha.values()))
                n += cur.rowcount
            cont[tabela] = n
        con.commit()
    return cont


# ---------- histórico de permissões ----------

def registrar_permissao(conversa_id, execucao_id, ferramenta: str, alvo: str, decisao: str, origem: str = "",
                        regra: str | None = None) -> None:
    with _trava_escrita:
        con = conexao()
        con.execute("INSERT INTO permissoes_log (criado_em, conversa_id, execucao_id, ferramenta, alvo, decisao, "
                    "origem, regra) VALUES (?,?,?,?,?,?,?,?)",
                    (agora(), conversa_id, execucao_id, ferramenta, (alvo or "")[:500], decisao, origem, regra))
        # guarda só os últimos 5 mil registros
        con.execute("DELETE FROM permissoes_log WHERE id <= (SELECT MAX(id) - 5000 FROM permissoes_log)")
        con.commit()


def log_permissoes(limite: int = 300, decisao: str = "") -> list[dict]:
    sql = "SELECT * FROM permissoes_log"
    args: list = []
    if decisao:
        sql += " WHERE decisao=?"
        args.append(decisao)
    sql += " ORDER BY id DESC LIMIT ?"
    args.append(limite)
    return [dict(r) for r in conexao().execute(sql, args).fetchall()]


def limpar_log_permissoes() -> None:
    with _trava_escrita:
        con = conexao()
        con.execute("DELETE FROM permissoes_log")
        con.commit()


# ---------- fluxos ----------

def salvar_fluxo(f: dict) -> None:
    t = agora()
    with _trava_escrita:
        con = conexao()
        con.execute(
            "INSERT INTO fluxos (id, conversa_id, execucao_id, titulo, dados_json, status, custo_usd, criado_em, "
            "atualizado_em) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET dados_json=excluded.dados_json, "
            "status=excluded.status, custo_usd=excluded.custo_usd, titulo=excluded.titulo, "
            "atualizado_em=excluded.atualizado_em",
            (f["id"], f.get("conversa_id"), f.get("execucao_id"), f.get("titulo") or "",
             json.dumps(f, ensure_ascii=False, default=str), f.get("status") or "proposto",
             float(f.get("custo_usd") or 0), f.get("criado_em") or t, t))
        con.commit()


def fluxo(fid: str) -> dict | None:
    r = conexao().execute("SELECT dados_json FROM fluxos WHERE id=?", (fid,)).fetchone()
    return _j(r["dados_json"]) if r else None


def listar_fluxos(limite: int = 100) -> list[dict]:
    rows = conexao().execute("SELECT id, conversa_id, titulo, status, custo_usd, criado_em FROM fluxos "
                             "ORDER BY criado_em DESC LIMIT ?", (limite,)).fetchall()
    return [dict(r) for r in rows]


# ---------- rotinas ----------

def _rotina(r) -> dict:
    d = dict(r)
    d.update(_j(d.pop("dados_json")) or {})
    d["ligada"] = bool(d["ligada"])
    return d


def salvar_rotina(rid: str | None, nome: str, dados: dict, ligada: bool = True, proxima: float | None = None) -> dict:
    rid = rid or novo_id()
    t = agora()
    with _trava_escrita:
        con = conexao()
        con.execute(
            "INSERT INTO rotinas (id, nome, dados_json, ligada, proxima, criado_em, atualizado_em) "
            "VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET nome=excluded.nome, dados_json=excluded.dados_json, "
            "ligada=excluded.ligada, proxima=excluded.proxima, atualizado_em=excluded.atualizado_em",
            (rid, nome, json.dumps(dados, ensure_ascii=False), 1 if ligada else 0, proxima, t, t))
        con.commit()
    return rotina(rid)


def rotina(rid: str) -> dict | None:
    r = conexao().execute("SELECT * FROM rotinas WHERE id=?", (rid,)).fetchone()
    return _rotina(r) if r else None


def listar_rotinas() -> list[dict]:
    return [_rotina(r) for r in conexao().execute("SELECT * FROM rotinas ORDER BY nome").fetchall()]


def marcar_rotina(rid: str, **campos) -> None:
    ok = {k: v for k, v in campos.items() if k in ("proxima", "ultima", "ultimo_status", "ultima_conversa", "ligada")}
    if not ok:
        return
    ok["atualizado_em"] = agora()
    cols = ", ".join(f"{k}=?" for k in ok)
    with _trava_escrita:
        con = conexao()
        con.execute(f"UPDATE rotinas SET {cols} WHERE id=?", (*ok.values(), rid))
        con.commit()


def apagar_rotina(rid: str) -> None:
    with _trava_escrita:
        con = conexao()
        con.execute("DELETE FROM rotinas WHERE id=?", (rid,))
        con.commit()
