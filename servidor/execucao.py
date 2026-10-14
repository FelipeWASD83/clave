"""O motor de cada resposta: chama a API em streaming, roda as ferramentas e conta o gasto.

Cada envio vira uma Execucao numa thread própria. A interface acompanha pelos
eventos (texto chegando, ferramenta pedindo aprovação, custo) e pode reconectar
no meio sem perder nada, porque a execução guarda a lista de eventos.
"""
from __future__ import annotations

import os
import threading
import time
import traceback
from pathlib import Path

import anthropic

import anexos
import banco
import config
import contexto_pasta
import custo
import modelos
import orcamento
import pedido
import segredos
from ferramentas import code as fcode
from ferramentas import github as fgithub
from ferramentas import memoria as fmemoria
from ferramentas import excel as fexcel
from ferramentas import planilhas as fplanilhas

MAX_VOLTAS = 60          # chamadas à API por envio (ferramentas incluídas)
MUDAM_ARQUIVOS = ("escrever_arquivo", "editar_arquivo", "excel_alterar", "excel_no_app")


def _custo(modelo: str, uso: dict) -> dict:
    c = custo.custo_uso(modelo, uso)
    if os.environ.get("CLAVE_API_FALSA"):
        c["usd"] = 0.0  # demonstração: nada é cobrado de verdade
    return c

# Os ajudantes rodam sempre no mesmo modelo, sem web nem GitHub.
AJUDANTES = {
    "tutor": {"modelo": "claude-haiku-5-5", "esforco": "medium", "pensar": False, "mostrar_raciocinio": False,
              "busca_web": False, "github": False, "rapido": False},
    "memoria": {"modelo": "claude-sonnet-5-5", "esforco": "medium", "pensar": True, "mostrar_raciocinio": False,
                "busca_web": False, "github": False, "rapido": False},
}
MAX_PAUSAS = 5

_execucoes: dict[str, "Execucao"] = {}
_por_conversa: dict[str, str] = {}
_trava = threading.Lock()


class SemChave(Exception):
    pass


def cliente() -> anthropic.Anthropic:
    falsa = os.environ.get("CLAVE_API_FALSA")
    if falsa:
        return anthropic.Anthropic(api_key="chave-falsa", base_url=falsa, max_retries=0)
    chave = segredos.ler("anthropic")
    if not chave:
        raise SemChave("Falta a chave da API. Cole a sua em Configurações > Conta e chave.")
    return anthropic.Anthropic(api_key=chave, max_retries=2,
                               timeout=anthropic.Timeout(900.0, connect=20.0))


def ativa(conversa_id: str) -> "Execucao | None":
    with _trava:
        eid = _por_conversa.get(conversa_id)
        e = _execucoes.get(eid) if eid else None
    return e if e and e.status in ("rodando", "esperando") else None


def pegar(eid: str) -> "Execucao | None":
    return _execucoes.get(eid)


def alguma_rodando() -> bool:
    return any(e.status in ("rodando", "esperando") for e in list(_execucoes.values()))


def _limpar_antigas() -> None:
    agora = time.time()
    with _trava:
        for eid, e in list(_execucoes.items()):
            if e.status not in ("rodando", "esperando") and agora - e.fim_em > 1800:
                _execucoes.pop(eid, None)


class Execucao:
    def __init__(self, conversa_id: str, opcoes: dict):
        self.id = banco.novo_id()
        self.conversa_id = conversa_id
        self.op = opcoes
        self.status = "rodando"
        self.eventos: list[dict] = []
        self.cond = threading.Condition()
        self.parar = threading.Event()
        self.aprovacoes: dict[str, dict] = {}
        self.liberados: set = set()
        self.custo_total = 0.0
        self.fim_em = 0.0
        self.mudou_arquivos = False
        self.ctx: fcode.Contexto | None = None
        self.seq_salvo = 0  # eventos até aqui já viraram mensagens salvas no banco

    # ---- eventos ----
    def emitir(self, ev: dict) -> None:
        with self.cond:
            ev["seq"] = len(self.eventos)
            self.eventos.append(ev)
            self.cond.notify_all()

    def eventos_desde(self, desde: int, espera: float = 15.0) -> list[dict]:
        with self.cond:
            if len(self.eventos) <= desde and self.status in ("rodando", "esperando"):
                self.cond.wait(timeout=espera)
            return self.eventos[desde:]

    def decidir(self, tool_id: str, decisao: str, texto: str = "") -> bool:
        a = self.aprovacoes.get(tool_id)
        if not a or a["evento"].is_set():
            return False
        a["decisao"] = decisao
        a["texto"] = texto
        a["evento"].set()
        return True

    def interromper(self) -> None:
        self.parar.set()
        for a in self.aprovacoes.values():
            a["evento"].set()
        if self.ctx and self.ctx.processo:
            fcode._matar(self.ctx.processo)
        s = getattr(self, "_stream", None)
        if s is not None:
            try:
                s.close()
            except Exception:
                pass

    # ---- principal ----
    def rodar(self) -> None:
        conv = banco.conversa(self.conversa_id)
        if conv and not conv.get("titulo"):
            threading.Thread(target=gerar_titulo, args=(self.conversa_id,), daemon=True).start()
        try:
            self._loop()
            if self.status == "rodando":
                self.status = "concluida"
        except SemChave as e:
            self._erro(str(e), "sem_chave")
        except Exception as e:  # o motivo vai para a tela e para o log
            traceback.print_exc()
            self._erro(_explicar_erro(e), "erro")
        finally:
            if self.parar.is_set() and self.status in ("rodando", "esperando", "concluida"):
                self.status = "parada"
            self.fim_em = time.time()
            self.emitir({"tipo": "fim", "status": self.status, "custo": round(self.custo_total, 6),
                         "mudou_arquivos": self.mudou_arquivos})
            _limpar_antigas()

    def _erro(self, mensagem: str, codigo: str) -> None:
        self.status = "erro"
        self.emitir({"tipo": "erro", "mensagem": mensagem, "codigo": codigo})
        conv = banco.conversa(self.conversa_id)
        if conv and conv.get("folha_id"):
            m = banco.mensagem(conv["folha_id"])
            if m:
                meta = dict(m.get("meta") or {})
                meta["erro"] = mensagem
                banco.atualizar_meta(m["id"], meta)

    def _loop(self) -> None:
        cfg = config.carregar()
        conv = banco.conversa(self.conversa_id)
        modo = conv["modo"]
        op = {**self.op, **AJUDANTES.get(modo, {})}
        if os.environ.get("CLAVE_FORCAR_MODELO"):  # só para testes: tudo num modelo barato
            op["modelo"] = os.environ["CLAVE_FORCAR_MODELO"]
        self.op = op
        modelo = op.get("modelo") or cfg.get("modelo_code" if modo == "code" else "modelo_chat")
        cli = cliente()

        ferramentas_cliente: list[dict] = []
        if modo == "code":
            pasta = Path(conv["pasta"])
            if not pasta.is_dir():
                raise RuntimeError(f"A pasta de trabalho não existe mais: {pasta}")
            skills = contexto_pasta.skills(pasta)
            self.ctx = fcode.Contexto(raiz=pasta.resolve(), protegidos=list(cfg.get("protegidos") or []),
                                      execucao_id=self.id, conversa_id=self.conversa_id, emitir=self.emitir,
                                      parar=self.parar, skills=skills)
            self.ctx.lidos |= _lidos_antes(self.conversa_id)
            ferramentas_cliente += fcode.definicoes(com_skills=bool(skills))
        if modo in ("chat", "code"):
            ferramentas_cliente += fplanilhas.definicoes()
        if modo in ("chat", "code") and op.get("github") and cfg.get("github_origem"):
            ferramentas_cliente += fgithub.definicoes(escrita=bool(cfg.get("github_escrita")))
        mcp = []
        for m in (cfg.get("conectores_mcp") or []) if modo in ("chat", "code") else []:
            if m.get("ligado") and m.get("url") and m.get("nome"):
                mcp.append({"nome": m["nome"], "url": m["url"], "token": segredos.ler(f"mcp:{m['nome']}")})

        pausas = 0
        extra_desligados: set = set()
        tentou_sem_pensamento = False
        for _volta in range(MAX_VOLTAS):
            if self.parar.is_set():
                break
            ok, motivo = orcamento.pode_gastar()
            if not ok:
                self._erro(motivo, "teto")
                return
            teto_tarefa = float(cfg.get("teto_tarefa_code_usd") or 0)
            if modo == "code" and teto_tarefa and self.custo_total >= teto_tarefa:
                self.emitir({"tipo": "aviso", "mensagem": (
                    f"Esta tarefa chegou ao teto por tarefa (US$ {teto_tarefa:.2f}) e foi pausada. Mande "
                    "\"continue\" para seguir, ou aumente o teto em Configurações > Limite de gasto.")})
                return

            caminho = banco.caminho(self.conversa_id)
            mensagens = _para_api(conv, caminho)
            if tentou_sem_pensamento:
                mensagens = pedido.sem_pensamento(mensagens)
            kw, usados = pedido.montar(
                modelo=modelo, esforco=op.get("esforco") or "", pensar=bool(op.get("pensar", True)),
                mostrar_raciocinio=bool(op.get("mostrar_raciocinio", cfg.get("mostrar_raciocinio", True))),
                modo=modo, sistema=conv.get("sistema") or "", mensagens=mensagens,
                ferramentas_cliente=ferramentas_cliente, cfg=cfg, busca_web=bool(op.get("busca_web")),
                memoria_ligada=(modo == "memoria") or (modo in ("chat", "code") and bool(cfg.get("memoria_ligada"))),
                mcp=mcp, rapido=bool(op.get("rapido")),
                extra_desligados=extra_desligados)
            try:
                final = self._chamar(cli, kw)
            except anthropic.BadRequestError as e:
                texto = _mensagem_api(e)
                baixo = texto.lower()
                if ("signature" in baixo or "thinking" in baixo and "block" in baixo) and not tentou_sem_pensamento:
                    tentou_sem_pensamento = True
                    self.emitir({"tipo": "aviso", "mensagem": "O raciocínio das respostas anteriores não pôde ser "
                                 "reaproveitado; a conversa segue sem ele."})
                    continue
                if usados - extra_desligados:
                    desl = pedido.desligar_por_erro(modelo, texto, usados - extra_desligados)
                    if desl:
                        extra_desligados |= desl
                        continue
                raise
            if final is None:  # interrompida no meio
                return

            conteudo = [b.model_dump(mode="json", exclude_none=True) for b in final.content]
            uso = final.usage.model_dump(mode="json", exclude_none=True) if final.usage else {}
            modelo_resp = final.model or modelo
            c = _custo(modelo_resp, uso)
            self.custo_total += c["usd"]
            pai = caminho[-1]["id"] if caminho else None
            meta = {"stop": final.stop_reason}
            if final.stop_reason == "refusal":
                det = getattr(final, "stop_details", None)
                meta["recusa"] = (det.model_dump(mode="json", exclude_none=True) if det else {})
            if modelo_resp != modelo:
                meta["respondido_por"] = modelo_resp
            msg = None
            if conteudo:
                msg = banco.adicionar_mensagem(self.conversa_id, pai, "assistant", conteudo, modelo=modelo_resp,
                                               uso=uso, custo_usd=c["usd"], meta=meta, execucao_id=self.id)
                self.seq_salvo = len(self.eventos)
            elif caminho:
                m0 = caminho[-1]
                banco.atualizar_meta(m0["id"], {**(m0.get("meta") or {}), **meta})
            banco.registrar_uso(self.conversa_id, msg["id"] if msg else None, modelo_resp, modo, c)
            sit = orcamento.situacao()
            self.emitir({"tipo": "uso", "custo": c, "custo_execucao": round(self.custo_total, 6),
                         "contexto": custo.contexto_usado(uso) + int(uso.get("output_tokens") or 0),
                         "orcamento": sit, "mensagem_id": msg["id"] if msg else None, "modelo": modelo_resp})
            alerta = orcamento.novo_alerta()
            if alerta:
                self.emitir({"tipo": "alerta_orcamento", "porcentagem": alerta, "orcamento": sit})

            stop = final.stop_reason
            if stop == "refusal":
                self.emitir({"tipo": "aviso", "mensagem": _texto_recusa(meta.get("recusa") or {})})
                return
            if stop == "pause_turn":
                pausas += 1
                if pausas <= MAX_PAUSAS:
                    continue
                return
            if stop == "max_tokens":
                if any(b.get("type") == "tool_use" for b in conteudo):
                    self.emitir({"tipo": "aviso", "mensagem": "A resposta passou do tamanho máximo no meio de uma "
                                 "ação. Peça para ele continuar em partes menores."})
                else:
                    self.emitir({"tipo": "aviso", "mensagem": "A resposta chegou ao tamanho máximo e foi cortada. "
                                 "Mande \"continue\" para ele seguir."})
                return
            if stop == "model_context_window_exceeded":
                self.emitir({"tipo": "aviso", "mensagem": "A conversa encheu a memória do modelo. Comece uma "
                             "conversa nova (ou ligue a compactação nas configurações)."})
                return
            if stop == "tool_use":
                usos = [b for b in conteudo if b.get("type") == "tool_use"]
                if not usos:
                    return
                resultados = self._ferramentas(usos, cfg, modo)
                banco.adicionar_mensagem(self.conversa_id, msg["id"] if msg else pai, "user", resultados,
                                         tipo="resultado_ferramenta", execucao_id=self.id)
                self.seq_salvo = len(self.eventos)
                if self.parar.is_set():
                    return
                continue
            return
        else:
            self.emitir({"tipo": "aviso", "mensagem": "Parei depois de muitas voltas seguidas. Mande \"continue\" "
                         "se quiser que ele siga."})

    def _chamar(self, cli: anthropic.Anthropic, kw: dict):
        self.emitir({"tipo": "chamando", "modelo": kw["model"]})
        with cli.beta.messages.stream(**kw) as s:
            self._stream = s
            try:
                return self._consumir(s, kw)
            except Exception:
                if self.parar.is_set():
                    self._salvar_parcial(getattr(s, "current_message_snapshot", None), kw["model"])
                    return None
                raise
            finally:
                self._stream = None

    def _consumir(self, s, kw: dict):
        for ev in s:
            if self.parar.is_set():
                self._salvar_parcial(getattr(s, "current_message_snapshot", None), kw["model"])
                return None
            t = ev.type
            if t == "message_start":
                self.emitir({"tipo": "inicio", "modelo": ev.message.model})
            elif t == "content_block_start":
                b = ev.content_block
                info = {"type": b.type}
                for campo in ("id", "name"):
                    if getattr(b, campo, None):
                        info[campo] = getattr(b, campo)
                self.emitir({"tipo": "bloco_inicio", "indice": ev.index, "bloco": info})
            elif t == "content_block_delta":
                d = ev.delta
                if d.type == "text_delta":
                    self.emitir({"tipo": "texto", "indice": ev.index, "texto": d.text})
                elif d.type == "thinking_delta":
                    self.emitir({"tipo": "pensamento", "indice": ev.index, "texto": d.thinking})
                elif d.type == "input_json_delta":
                    self.emitir({"tipo": "entrada", "indice": ev.index, "parcial": d.partial_json})
            elif t == "content_block_stop":
                b = getattr(ev, "content_block", None)
                if b is None:
                    snap = getattr(s, "current_message_snapshot", None)
                    b = snap.content[ev.index] if snap and len(snap.content) > ev.index else None
                if b is not None:
                    self.emitir({"tipo": "bloco_fim", "indice": ev.index,
                                 "bloco": b.model_dump(mode="json", exclude_none=True)})
        return s.get_final_message()

    def _salvar_parcial(self, snap, modelo: str) -> None:
        if snap is None:
            return
        textos = []
        for b in snap.content:
            if b.type == "text" and (b.text or "").strip():
                textos.append({"type": "text", "text": b.text})
        if not textos:
            return
        conv = banco.conversa(self.conversa_id)
        textos[-1]["text"] += "\n\n[resposta interrompida]"
        uso = snap.usage.model_dump(mode="json", exclude_none=True) if snap.usage else {}
        c = _custo(modelo, uso)
        msg = banco.adicionar_mensagem(self.conversa_id, conv.get("folha_id"), "assistant", textos, modelo=modelo,
                                       uso=uso, custo_usd=c["usd"], meta={"interrompida": True},
                                       execucao_id=self.id)
        banco.registrar_uso(self.conversa_id, msg["id"], modelo, "chat", c)
        self.custo_total += c["usd"]

    # ---- ferramentas ----
    def _ferramentas(self, usos: list[dict], cfg: dict, modo: str) -> list[dict]:
        resultados = []
        for u in usos:
            tid, nome, entrada = u["id"], u["name"], u.get("input")
            if self.parar.is_set():
                resultados.append(_res(tid, "Interrompido por quem usa antes de rodar.", True))
                continue
            try:
                resultados.append(self._uma(tid, nome, entrada, cfg, modo))
            except Exception as e:  # erro da ferramenta volta para o Claude, não derruba a conversa
                traceback.print_exc()
                resultados.append(_res(tid, f"Erro: {e}", True))
                self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": str(e)})
        return resultados

    def _uma(self, tid: str, nome: str, entrada, cfg: dict, modo: str) -> dict:
        if nome == "memory":
            try:
                saida = fmemoria.executar(entrada or {})
                self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False, "resumo": saida[:300]})
                return _res(tid, saida)
            except fmemoria.ErroMemoria as e:
                self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": str(e)})
                return _res(tid, str(e), True)

        if nome in fplanilhas.NOMES:
            self.emitir({"tipo": "ferramenta_rodando", "id": tid, "nome": nome})
            try:
                saida = fplanilhas.executar(nome, entrada or {})
            except fexcel.ErroExcel as e:
                self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": str(e)})
                return _res(tid, str(e), True)
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False, "resumo": saida[:4000]})
            return _res(tid, saida)

        if nome in fgithub.FERRAMENTAS:
            risco = fgithub.FERRAMENTAS[nome]["risco"]
            if risco == "github_escrita":
                decisao = self._pedir_aprovacao(tid, nome, entrada, "publica algo no GitHub", None)
                if decisao != "permitir":
                    return self._recusado(tid, nome)
            saida = fgithub.executar(nome, entrada or {})
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False, "resumo": saida[:300]})
            return _res(tid, saida)

        if modo != "code" or self.ctx is None or nome not in fcode.FERRAMENTAS:
            return _res(tid, f"Ferramenta não disponível aqui: {nome}", True)

        erro = fcode.validar(nome, entrada)
        if erro:
            import json as _json
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": erro})
            return _res(tid, _json.dumps({"INVALID_JSON": _json.dumps(entrada, ensure_ascii=False), "erro": erro},
                                         ensure_ascii=False), True)

        permissao = self.op.get("permissao") or cfg.get("permissao_code") or "perguntar"
        decisao, motivo = fcode.classificar(nome, entrada, self.ctx, permissao, self.liberados)
        if decisao == "negar":
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": f"Bloqueado: {motivo}"})
            return _res(tid, f"Bloqueado pelo Clave: {motivo}.", True)
        if decisao == "perguntar":
            previa = _previa(nome, entrada, self.ctx)
            d = self._pedir_aprovacao(tid, nome, entrada, motivo, previa)
            if d == "permitir_sempre":
                # "nesta tarefa" vale só para editar dentro da pasta e para comandos comuns: fora da pasta,
                # comando perigoso e comando que cita protegido continuam perguntando um por um
                risco = fcode.FERRAMENTAS[nome]["risco"]
                if motivo in ("mudar arquivo", "rodar comando"):
                    self.liberados.add(risco)
            elif d != "permitir":
                return self._recusado(tid, nome)

        self.emitir({"tipo": "ferramenta_rodando", "id": tid, "nome": nome})
        try:
            saida = fcode.executar(nome, entrada, self.ctx)
            erro_flag = False
        except fcode.ErroFerramenta as e:
            saida, erro_flag = str(e), True
        if nome in MUDAM_ARQUIVOS and not erro_flag:
            self.mudou_arquivos = True
        resumo = saida if isinstance(saida, str) else " ".join(
            b.get("text", "") for b in saida if isinstance(b, dict) and b.get("type") == "text")
        self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": erro_flag,
                     "resumo": resumo[:4000]})
        return _res(tid, saida, erro_flag)

    def _pedir_aprovacao(self, tid, nome, entrada, motivo, previa) -> str:
        ev = threading.Event()
        self.aprovacoes[tid] = {"evento": ev, "decisao": None, "texto": ""}
        self.status = "esperando"
        self.emitir({"tipo": "aprovacao", "id": tid, "nome": nome, "entrada": entrada, "motivo": motivo,
                     "previa": previa})
        ev.wait()
        self.status = "rodando"
        a = self.aprovacoes[tid]
        if self.parar.is_set():
            a["decisao"] = "recusar"
            a["texto"] = "A tarefa foi interrompida."
        self.emitir({"tipo": "aprovacao_decidida", "id": tid, "decisao": a["decisao"]})
        return a["decisao"] or "recusar"

    def _recusado(self, tid, nome) -> dict:
        texto = (self.aprovacoes.get(tid) or {}).get("texto") or ""
        msg = "Quem usa recusou esta ação." + (f" Comentário: {texto}" if texto else "")
        self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": msg})
        return _res(tid, msg, True)


def _res(tid: str, conteudo, erro=False) -> dict:
    r = {"type": "tool_result", "tool_use_id": tid, "content": conteudo if conteudo else "(vazio)"}
    if erro:
        r["is_error"] = True
    return r


def _previa(nome: str, e: dict, ctx: fcode.Contexto) -> str | None:
    try:
        if nome == "editar_arquivo":
            return fcode._diff(e.get("trecho_atual", ""), e.get("trecho_novo", ""), e.get("caminho", ""))
        if nome == "escrever_arquivo":
            p = ctx.resolver(e["caminho"])
            antes = fcode._ler_texto(p)[0] if p.is_file() else ""
            return fcode._diff(antes, e.get("conteudo", ""), ctx.relativo(p))
    except Exception:
        return None
    return None


def _lidos_antes(conversa_id: str) -> set:
    """Arquivos lidos ou criados em envios anteriores da mesma conversa continuam valendo como lidos."""
    lidos = set()
    conv = banco.conversa(conversa_id)
    for m in banco.caminho(conversa_id):
        if m["papel"] != "assistant" or not isinstance(m["conteudo"], list):
            continue
        for b in m["conteudo"]:
            if b.get("type") == "tool_use" and b.get("name") in ("ler_arquivo", "escrever_arquivo", "editar_arquivo"):
                cam = (b.get("input") or {}).get("caminho")
                if cam:
                    p = Path(cam)
                    if not p.is_absolute():
                        p = Path(conv["pasta"]) / p
                    lidos.add(str(p.resolve()))
    return lidos


def _para_api(conv: dict, caminho: list[dict]) -> list[dict]:
    msgs = []
    contexto = conv.get("contexto") or []
    for i, m in enumerate(caminho):
        conteudo = m["conteudo"]
        if i == 0 and contexto and m["papel"] == "user":
            base = conteudo if isinstance(conteudo, list) else [{"type": "text", "text": conteudo}]
            conteudo = list(contexto) + base
        msgs.append({"role": m["papel"], "content": anexos.expandir_conteudo(conteudo)})
    return msgs


def _mensagem_api(e: anthropic.APIStatusError) -> str:
    try:
        corpo = e.body if isinstance(e.body, dict) else {}
        return (corpo.get("error") or {}).get("message") or e.message
    except Exception:
        return str(e)


def _texto_recusa(det: dict) -> str:
    cat = det.get("category")
    nomes = {"cyber": "segurança digital", "bio": "biologia de risco", "reasoning_extraction":
             "pedido para mostrar o raciocínio interno", "frontier_llm": "desenvolvimento de modelos de IA",
             "general_harms": "política de uso"}
    base = "O Claude recusou este pedido pelas regras de segurança da Anthropic"
    if cat:
        base += f" (categoria: {nomes.get(cat, cat)})"
    return base + ". Reformule o pedido ou tente outro modelo."


def _explicar_erro(e: Exception) -> str:
    if isinstance(e, anthropic.AuthenticationError):
        return "A chave da API foi recusada. Confira em Configurações > Conta e chave."
    if isinstance(e, anthropic.PermissionDeniedError):
        return "A chave não tem permissão para isso (ou o modelo não está liberado na sua conta). " + _mensagem_api(e)
    if isinstance(e, anthropic.NotFoundError):
        return "Modelo não encontrado na sua conta. Escolha outro modelo. " + _mensagem_api(e)
    if isinstance(e, anthropic.RateLimitError):
        return "A API pediu para esperar (limite de pedidos por minuto). Tente de novo daqui a pouco."
    if isinstance(e, anthropic.BadRequestError):
        msg = _mensagem_api(e)
        if "credit balance" in msg.lower():
            return ("Acabou o crédito da sua conta na API da Anthropic. Recarregue no Console "
                    "(platform.claude.com) ou espere o crédito do mês seguinte.")
        if "prompt is too long" in msg.lower() or "too long" in msg.lower():
            return "A conversa ficou grande demais para o modelo. Comece uma conversa nova. (" + msg + ")"
        return "A API recusou o pedido: " + msg
    if isinstance(e, anthropic.APIStatusError):
        if e.status_code in (500, 529) or e.status_code >= 500:
            return "Os servidores da Anthropic estão sobrecarregados ou com problema agora. Tente de novo em instantes."
        return f"Erro da API ({e.status_code}): {_mensagem_api(e)}"
    if isinstance(e, anthropic.APIConnectionError):
        return "Sem conexão com a API da Anthropic. Confira a internet."
    return f"Erro inesperado: {e}"


def iniciar(conversa_id: str, opcoes: dict) -> Execucao:
    with _trava:
        atual = _por_conversa.get(conversa_id)
        if atual and _execucoes.get(atual) and _execucoes[atual].status in ("rodando", "esperando"):
            raise RuntimeError("Esta conversa já está respondendo. Espere terminar ou aperte Parar.")
        ex = Execucao(conversa_id, opcoes)
        _execucoes[ex.id] = ex
        _por_conversa[conversa_id] = ex.id
    threading.Thread(target=ex.rodar, name=f"execucao-{ex.id}", daemon=True).start()
    return ex


# ---------- títulos ----------

def gerar_titulo(conversa_id: str) -> None:
    conv = banco.conversa(conversa_id)
    if not conv or conv.get("titulo"):
        return
    caminho = banco.caminho(conversa_id)
    primeira = next((m for m in caminho if m["papel"] == "user" and m["tipo"] == "normal"), None)
    if not primeira:
        return
    texto = _texto_puro(primeira)
    padrao = (texto.strip().splitlines() or ["Conversa"])[0][:60] or "Conversa"
    cfg = config.carregar()
    if not cfg.get("titulos_automaticos", True) or not orcamento.pode_gastar()[0]:
        banco.atualizar_conversa(conversa_id, titulo=padrao)
        return
    try:
        cli = cliente()
        r = cli.messages.create(
            model="claude-haiku-5-5", max_tokens=60, thinking={"type": "disabled"},
            output_config={"effort": "low"},
            system="Crie um título curto (no máximo 6 palavras, sem aspas e sem ponto final) para uma conversa que "
                   "começa com a mensagem abaixo, no mesmo idioma dela. Responda só com o título.",
            messages=[{"role": "user", "content": texto[:4000] or "Conversa"}])
        titulo = "".join(b.text for b in r.content if b.type == "text").strip().strip('"').strip()[:80]
        uso = r.usage.model_dump(mode="json", exclude_none=True)
        c = _custo("claude-haiku-5-5", uso)
        banco.registrar_uso(conversa_id, None, "claude-haiku-5-5", "titulo", c)
        banco.atualizar_conversa(conversa_id, titulo=titulo or padrao)
    except Exception:
        banco.atualizar_conversa(conversa_id, titulo=padrao)


def _texto_puro(m: dict) -> str:
    if (m.get("meta") or {}).get("exibir"):
        return m["meta"]["exibir"]
    c = m["conteudo"]
    if isinstance(c, str):
        return c
    return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")


# ---------- desfazer (modo Code) ----------

def desfazer(execucao_id: str) -> list[str]:
    feitos = []
    for ck in reversed(banco.checkpoints(execucao_id)):
        if ck["desfeito"]:
            continue
        p = Path(ck["caminho"])
        try:
            if ck["existia"]:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(ck["conteudo"] or b"")
            elif p.exists():
                p.unlink()
            feitos.append(str(p))
        except OSError as e:
            feitos.append(f"{p} (falhou: {e})")
    banco.marcar_desfeito(execucao_id)
    return feitos


def modelos_disponiveis() -> list[str] | None:
    try:
        cli = cliente()
        return [m.id for m in cli.models.list(limit=100).data]
    except Exception:
        return None
