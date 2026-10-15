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
import fluxos
import i18n
import orcamento
import pedido
import permissoes
import segredos
from ferramentas import code as fcode
from ferramentas import email as femail
from ferramentas import github as fgithub
from ferramentas import memoria as fmemoria
from ferramentas import excel as fexcel
from ferramentas import planilhas as fplanilhas
from i18n import t

MAX_VOLTAS = 60          # chamadas à API por envio (ferramentas incluídas)
MUDAM_ARQUIVOS = ("escrever_arquivo", "editar_arquivo", "excel_alterar", "excel_no_app", "word_criar", "word_alterar",
                  "word_no_app", "email_salvar_anexo")
# o que cada etapa de fluxo pode usar, conforme o "pode" dela
POR_CAPACIDADE = {
    "ler": {"listar_pasta", "ler_arquivo", "buscar_texto", "achar_arquivos", "excel_ler", "excel_abrir", "word_ler",
            "mostrar_arquivo"},
    "editar": {"escrever_arquivo", "editar_arquivo", "excel_alterar", "excel_no_app", "word_criar", "word_alterar",
               "word_no_app"},
    "comandos": {"rodar_comando"},
}
SEMPRE = {"atualizar_tarefas", "usar_skill"}
MODOS_PERMISSAO = {"executar_perguntar": "perguntar", "executar_aceitar": "aceitar_edicoes",
                   "executar_livre": "livre"}
NOMES_MODO = {"perguntar": "Perguntar", "aceitar_edicoes": "Aceitar edições", "plano": "Plano", "livre": "Livre"}  # mostrar com t()
# Aviso de modo que vai junto da mensagem para o modelo e não aparece na tela (servidor._nota_de_modo).
MARCA_MODO, FIM_MARCA_MODO = "<modo-do-clave>", "</modo-do-clave>"

PLANO = {
    "name": "apresentar_plano",
    "description": ("Apresenta o plano a quem usa quando ele estiver pronto, no modo Plano. A pessoa vê um "
                    "cartão com o plano e escolhe executar (e com qual permissão) ou continuar planejando. "
                    "Se aprovar, o modo muda e você segue executando o plano na mesma resposta."),
    "eager_input_streaming": True,
    "input_schema": {"type": "object", "properties": {
        "plano": {"type": "string", "description": "O plano em Markdown: o que vai mudar, em quais arquivos, em que ordem, e como vai conferir, no idioma em que a pessoa escreve"}},
        "required": ["plano"]},
}


SUGERIR = {
    "name": "sugerir_conversa",
    "description": ("Sugere a quem usa abrir OUTRA conversa para um trabalho separado deste: algo que você notou e vale "
                    "fazer, ou um próximo passo independente que fica melhor começando do zero. Vira um cartão com o "
                    "título e o pedido; nada roda sem quem usa clicar, e a conversa nova não vê esta. Use só para "
                    "trabalho de verdade e separado (nunca para o que você mesmo vai fazer aqui), no máximo uma vez "
                    "por resposta, e não repita a sugestão no texto."),
    "eager_input_streaming": True,
    "input_schema": {"type": "object", "properties": {
        "titulo": {"type": "string", "description": "Nome curto da tarefa, até 60 caracteres, no idioma em que a pessoa escreve"},
        "pedido": {"type": "string", "description": "O pedido completo para a conversa nova, como quem usa mandaria: "
                                                    "o que fazer, onde, o que já se sabe e como saber que terminou"},
        "por_que": {"type": "string", "description": "Uma frase dizendo por que vale fazer isso, no idioma em que a pessoa escreve"}},
        "required": ["titulo", "pedido"]},
}

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
        raise SemChave(t("Falta a chave da API. Cole a sua em Configurações > Conta e chave."))
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


def registrar(ex: "Execucao") -> None:
    """Põe na lista uma execução que roda dentro de outra (etapa de fluxo), para a interface achar e aprovar."""
    with _trava:
        _execucoes[ex.id] = ex


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
        self.custo_fluxos = 0.0
        self.ultimo_erro = ""
        self.filhos: list["Execucao"] = []      # etapas de fluxo rodando dentro desta resposta
        self.mae: "Execucao | None" = None      # quando esta é uma etapa de fluxo
        self.cofre = None                       # teto do fluxo (só nas etapas)
        self.repassar = None                    # manda os eventos da etapa para a conversa principal
        self.regras: list = []
        self.regras_tarefa: list = [permissoes.Regra("allow", r, "comando")
                                    for r in (opcoes.get("regras_tarefa") or []) if not permissoes.validar(r)]
        self.skills_chat: list = []
        self.pediu_ok: dict | None = None       # rotina que parou porque precisaria de OK

    # ---- eventos ----
    def emitir(self, ev: dict) -> None:
        with self.cond:
            ev["seq"] = len(self.eventos)
            self.eventos.append(ev)
            self.cond.notify_all()
        if self.repassar:
            try:
                self.repassar(dict(ev))
            except Exception:
                traceback.print_exc()

    def eventos_desde(self, desde: int, espera: float = 15.0) -> list[dict]:
        with self.cond:
            if len(self.eventos) <= desde and self.status in ("rodando", "esperando"):
                self.cond.wait(timeout=espera)
            return self.eventos[desde:]

    def decidir(self, tool_id: str, decisao: str, texto: str = "", dados: dict | None = None) -> bool:
        a = self.aprovacoes.get(tool_id)
        if not a or a["evento"].is_set():
            return False
        a["decisao"] = decisao
        a["texto"] = texto
        a["dados"] = dados or {}
        a["evento"].set()
        return True

    def interromper(self) -> None:
        self.parar.set()
        for f in list(self.filhos):
            f.interromper()
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
            self.emitir({"tipo": "fim", "status": self.status, "custo": round(self.custo_total + self.custo_fluxos, 6),
                         "mudou_arquivos": self.mudou_arquivos, "pediu_ok": self.pediu_ok})
            _limpar_antigas()

    def _erro(self, mensagem: str, codigo: str) -> None:
        self.status = "erro"
        self.ultimo_erro = mensagem
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
        if modo == "etapa":  # etapa de fluxo: trabalha como o modo da conversa principal
            modo = (conv.get("ajustes") or {}).get("modo_base") or "chat"
        op = {**self.op, **AJUDANTES.get(modo, {})}
        if os.environ.get("CLAVE_FORCAR_MODELO"):  # só para testes: tudo num modelo barato
            op["modelo"] = os.environ["CLAVE_FORCAR_MODELO"]
        self.op = op
        modelo = op.get("modelo") or cfg.get("modelo_code" if modo == "code" else "modelo_chat")
        cli = cliente()

        etapa = bool(op.get("etapa_de_fluxo"))
        pode = set(op.get("pode") or []) if etapa else None
        ferramentas_cliente: list[dict] = []
        pasta = Path(conv["pasta"]) if modo == "code" and conv.get("pasta") else None
        self.regras = permissoes.coletar(cfg, pasta, self.regras_tarefa)
        if modo == "code":
            if not pasta or not pasta.is_dir():
                raise RuntimeError(t("A pasta de trabalho não existe mais: {pasta}", pasta=pasta))
            skills = contexto_pasta.skills(pasta)
            mae = self.mae
            self.ctx = fcode.Contexto(raiz=pasta.resolve(), protegidos=list(cfg.get("protegidos") or []),
                                      execucao_id=mae.id if mae else self.id,  # o Desfazer da conversa cobre as etapas
                                      conversa_id=mae.conversa_id if mae else self.conversa_id,
                                      emitir=self.emitir, parar=self.parar, skills=skills)
            self.ctx.regras = self.regras
            if not etapa:
                self.ctx.lidos |= _lidos_antes(self.conversa_id)
            defs = fcode.definicoes(com_skills=bool(skills))
            if pode is not None:
                liberadas = set(SEMPRE).union(*(POR_CAPACIDADE[c] for c in pode if c in POR_CAPACIDADE))
                defs = [d for d in defs if d["name"] in liberadas]
            ferramentas_cliente += defs
            if op.get("permissao") == "plano" and not etapa and not op.get("rotina"):
                ferramentas_cliente.append(dict(PLANO))
        elif modo == "chat":
            self.skills_chat = [s for s in contexto_pasta.skills(None)]
            if self.skills_chat:
                ferramentas_cliente.append(fcode.FERRAMENTAS["usar_skill"]["def"])
        if modo in ("chat", "code") and not etapa:
            ferramentas_cliente += fplanilhas.definicoes()
        if modo in ("chat", "code") and not etapa and femail.ligado() and not permissoes.nega(self.regras, "Email"):
            ferramentas_cliente += femail.definicoes()
        if modo in ("chat", "code") and op.get("github") and cfg.get("github_origem") and not etapa:
            ferramentas_cliente += fgithub.definicoes(escrita=bool(cfg.get("github_escrita")))
        if (modo in ("chat", "code") and not etapa and not op.get("rotina") and cfg.get("fluxos_ligados", True)
                and not permissoes.nega(self.regras, "Fluxo")):
            ferramentas_cliente.append(fluxos.definicao(str(pasta) if pasta else None))
        if modo in ("chat", "code") and not etapa and not op.get("rotina"):
            ferramentas_cliente.append(dict(SUGERIR))
        ferramentas_cliente = i18n.traduzir_ferramentas(ferramentas_cliente)
        mcp = []
        for m in (cfg.get("conectores_mcp") or []) if modo in ("chat", "code") and not etapa else []:
            if m.get("ligado") and m.get("url") and m.get("nome"):
                liberado, desligadas = permissoes.mcp_filtrado(self.regras, m["nome"])
                if liberado:
                    mcp.append({"nome": m["nome"], "url": m["url"], "token": segredos.ler(f"mcp:{m['nome']}"),
                                "desligadas": desligadas})
        # sem a opção no pedido (conversa aberta por uma sugestão, por exemplo), o chat e o Code seguem o padrão das
        # Configurações; etapa, rotina e ajudante sempre mandam a deles
        web_padrao = modo in ("chat", "code") and not etapa and not op.get("rotina") and cfg.get("busca_web", True)
        busca_web = bool(op.get("busca_web", web_padrao)) and not permissoes.web_negada(self.regras)
        bloqueados = permissoes.dominios_bloqueados(self.regras)

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
            if self.cofre is not None and self.cofre.estourou():
                self.emitir({"tipo": "aviso", "mensagem": t("{rotulo} chegou ao teto de gasto aprovado e parou.",
                                                        rotulo=t(self.cofre.rotulo))})
                return
            teto_tarefa = float(cfg.get("teto_tarefa_code_usd") or 0)
            if modo == "code" and not etapa and teto_tarefa and self.custo_total >= teto_tarefa:
                self.emitir({"tipo": "aviso", "mensagem": t(
                    "Esta tarefa chegou ao teto por tarefa (US$ {teto}) e foi pausada. Mande \"continue\" para seguir, ou aumente o teto em Configurações > Limite de gasto.",
                    teto=f"{teto_tarefa:.2f}")})
                return

            caminho = banco.caminho(self.conversa_id)
            mensagens = _para_api(conv, caminho)
            if tentou_sem_pensamento:
                mensagens = pedido.sem_pensamento(mensagens)
            kw, usados = pedido.montar(
                modelo=modelo, esforco=op.get("esforco") or "", pensar=bool(op.get("pensar", True)),
                mostrar_raciocinio=bool(op.get("mostrar_raciocinio", cfg.get("mostrar_raciocinio", True))),
                modo=modo, sistema=conv.get("sistema") or "", mensagens=mensagens,
                ferramentas_cliente=ferramentas_cliente, cfg=cfg, busca_web=busca_web,
                dominios_bloqueados=bloqueados,
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
                    self.emitir({"tipo": "aviso", "mensagem": t("O raciocínio das respostas anteriores não pôde ser reaproveitado; a conversa segue sem ele.")})
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
            if self.cofre is not None:
                self.cofre.somar(c["usd"])
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
            if self.mae is not None:  # o gasto da etapa conta na conversa principal, como "fluxo"
                banco.registrar_uso(self.mae.conversa_id, None, modelo_resp, "fluxo", c)
            else:
                banco.registrar_uso(self.conversa_id, msg["id"] if msg else None, modelo_resp,
                                    "rotina" if op.get("rotina") else modo, c)
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
                    self.emitir({"tipo": "aviso", "mensagem": t("A resposta passou do tamanho máximo no meio de uma ação. Peça para ele continuar em partes menores.")})
                else:
                    self.emitir({"tipo": "aviso", "mensagem": t("A resposta chegou ao tamanho máximo e foi cortada. Mande \"continue\" para ele seguir.")})
                return
            if stop == "model_context_window_exceeded":
                self.emitir({"tipo": "aviso", "mensagem": t("A conversa encheu a memória do modelo. Comece uma conversa nova (ou ligue a compactação nas configurações).")})
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
            self.emitir({"tipo": "aviso", "mensagem": t("Parei depois de muitas voltas seguidas. Mande \"continue\" se quiser que ele siga.")})

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
        textos[-1]["text"] += "\n\n" + t("[resposta interrompida]")
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
                resultados.append(_res(tid, t("Interrompido por quem usa antes de rodar."), True))
                continue
            try:
                resultados.append(self._uma(tid, nome, entrada, cfg, modo))
            except Exception as e:  # erro da ferramenta volta para o Claude, não derruba a conversa
                traceback.print_exc()
                resultados.append(_res(tid, t("Erro: {erro}", erro=e), True))
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

        if nome == "executar_fluxo":
            return self._fluxo(tid, entrada or {}, cfg, modo)

        if nome == "apresentar_plano":
            return self._plano(tid, entrada or {})

        if nome == "sugerir_conversa":
            return self._sugerir(tid, entrada or {}, modo)

        if nome == "usar_skill" and self.ctx is None:
            s = contexto_pasta.conteudo_skill(self.skills_chat, str((entrada or {}).get("nome", "")).strip().lstrip("/"))
            if not s:
                nomes = ", ".join(x["nome"] for x in self.skills_chat) or t("nenhuma")
                self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True,
                             "resumo": t("skill não encontrada")})
                return _res(tid, t("Skill não encontrada. Disponíveis: {nomes}", nomes=nomes), True)
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False, "resumo": s["nome"]})
            return _res(tid, t("Skill \"{nome}\" (aqui no chat não há pasta nem terminal: siga as partes que não dependem deles).\n\n{conteudo}", nome=s["nome"], conteudo=s["texto"]))

        if nome in femail.NOMES:
            return self._email(tid, nome, entrada or {})

        if nome in fgithub.FERRAMENTAS:
            risco = fgithub.FERRAMENTAS[nome]["risco"]
            if risco == "github_escrita":
                acao, regra = permissoes.avaliar(self.regras, [("GitHub", nome)], None)
                if acao == "deny":
                    self._log(nome, nome, "negar", "regra", regra)
                    return _res(tid, t("Bloqueado pelo Clave: {motivo}.", motivo=regra.descrever()), True)
                if acao != "allow" or permissoes.generica(regra):
                    motivo_gh = t("publica algo no GitHub")
                    if self.op.get("rotina"):
                        return self._rotina_parou(tid, nome, nome, motivo_gh, f"GitHub({nome})")
                    decisao = self._pedir_aprovacao(tid, nome, entrada, motivo_gh, None,
                                                    extra={"sugestao": f"GitHub({nome})", "pode_sempre": True})
                    if not self._aplicar_escopo(decisao, tid, nome, motivo_gh):
                        self._log(nome, nome, "recusar", "voce")
                        return self._recusado(tid, nome)
                    self._log(nome, nome, "permitir", "voce")
                else:
                    self._log(nome, nome, "auto", "regra", regra)
            saida = fgithub.executar(nome, entrada or {})
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False, "resumo": saida[:300]})
            return _res(tid, saida)

        if modo != "code" or self.ctx is None or nome not in fcode.FERRAMENTAS:
            return _res(tid, t("Ferramenta não disponível aqui: {nome}", nome=nome), True)
        pode = self.op.get("pode") if self.op.get("etapa_de_fluxo") else None
        if pode is not None and nome not in SEMPRE and not any(nome in POR_CAPACIDADE.get(c, ()) for c in pode):
            return _res(tid, t("Esta etapa do fluxo não pode usar esta ferramenta."), True)

        erro = fcode.validar(nome, entrada)
        if erro:
            import json as _json
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": erro})
            return _res(tid, _json.dumps({"INVALID_JSON": _json.dumps(entrada, ensure_ascii=False), "erro": erro},
                                         ensure_ascii=False), True)

        permissao = self.op.get("permissao") or cfg.get("permissao_code") or "perguntar"
        det = fcode.decidir(nome, entrada, self.ctx, permissao, self.liberados)
        decisao, motivo = det["decisao"], det["motivo"]
        alvo = _resumo_alvo(nome, entrada, self.ctx)
        if decisao == "negar":
            self._log(nome, alvo, "negar", det["origem"], det.get("regra"))
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True,
                         "resumo": t("Bloqueado: {motivo}", motivo=motivo)})
            return _res(tid, t("Bloqueado pelo Clave: {motivo}.", motivo=motivo), True)
        if decisao == "perguntar":
            sugestao = permissoes.sugerir(nome, entrada, self.ctx)
            if self.op.get("rotina"):
                return self._rotina_parou(tid, nome, alvo, motivo, sugestao)
            previa = _previa(nome, entrada, self.ctx)
            # perigoso e arquivo protegido não ganham "sempre": cada um pede OK de novo
            pode_sempre = det["origem"] not in ("perigoso", "protegido") and sugestao is not None
            d = self._pedir_aprovacao(tid, nome, entrada, motivo, previa,
                                      extra={"sugestao": sugestao, "pode_sempre": pode_sempre,
                                             "pode_tarefa": det["origem"] not in ("perigoso", "protegido")})
            if not self._aplicar_escopo(d, tid, nome, motivo):
                self._log(nome, alvo, "recusar", "voce")
                return self._recusado(tid, nome)
            self._log(nome, alvo, "permitir", "voce", (self.aprovacoes[tid].get("dados") or {}).get("regra"))
        else:
            self._log(nome, alvo, "auto", det["origem"], det.get("regra"))

        self.emitir({"tipo": "ferramenta_rodando", "id": tid, "nome": nome})
        self.ctx.ferramenta_id = tid
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

    def _pedir_aprovacao(self, tid, nome, entrada, motivo, previa, extra: dict | None = None,
                         tipo: str = "aprovacao") -> str:
        ev = threading.Event()
        self.aprovacoes[tid] = {"evento": ev, "decisao": None, "texto": "", "dados": {}, "tipo": tipo,
                                "pedido": {"tipo": tipo, "id": tid, "nome": nome, "entrada": entrada, "motivo": motivo,
                                           "previa": previa, **(extra or {})}}
        self.status = "esperando"
        self.emitir(dict(self.aprovacoes[tid]["pedido"]))
        ev.wait()
        self.status = "rodando"
        a = self.aprovacoes[tid]
        if self.parar.is_set():
            a["decisao"] = "recusar"
            a["texto"] = t("A tarefa foi interrompida.")
        self.emitir({"tipo": "aprovacao_decidida", "id": tid, "decisao": a["decisao"]})
        return a["decisao"] or "recusar"

    def _aplicar_escopo(self, decisao: str, tid: str, nome: str, motivo: str) -> bool:
        """Aplica o "nesta tarefa / sempre nesta pasta / sempre" do cartão. Devolve se a ação foi permitida."""
        if decisao == "permitir":
            return True
        if decisao not in ("permitir_sempre", "permitir_tarefa", "permitir_pasta", "permitir_app"):
            return False
        dados = (self.aprovacoes.get(tid) or {}).get("dados") or {}
        texto_regra = str(dados.get("regra") or "").strip()
        if decisao in ("permitir_sempre", "permitir_tarefa"):
            risco = (fcode.FERRAMENTAS.get(nome) or {}).get("risco")
            if _motivo_e(motivo, "mudar arquivo", "rodar comando") and risco:
                self.liberados.add(risco)
            elif texto_regra and not permissoes.validar(texto_regra):
                self._nova_regra(permissoes.Regra("allow", texto_regra, "tarefa"))
            return True
        if not texto_regra or permissoes.validar(texto_regra):
            self.emitir({"tipo": "aviso", "mensagem": t("A regra não foi salva ({motivo}); a ação foi permitida só desta vez.",
                                                        motivo=permissoes.validar(texto_regra) or t("vazia"))})
            return True
        try:
            if decisao == "permitir_pasta":
                if not self.ctx:
                    raise ValueError(t("não há pasta de trabalho"))
                arq = permissoes.salvar_na_pasta(self.ctx.raiz, "allow", texto_regra)
                self._nova_regra(permissoes.Regra("allow", texto_regra, "pasta", str(arq)))
            else:
                permissoes.salvar_no_app("allow", texto_regra)
                self._nova_regra(permissoes.Regra("allow", texto_regra, "app"))
            self.emitir({"tipo": "regra_salva", "regra": texto_regra,
                         "escopo": "pasta" if decisao == "permitir_pasta" else "app"})
        except (ValueError, OSError) as e:
            self.emitir({"tipo": "aviso", "mensagem": t("A regra não foi salva ({motivo}); a ação foi permitida só desta vez.",
                                                        motivo=e)})
        return True

    def _nova_regra(self, regra) -> None:
        alvo = self.mae if self.mae is not None else self
        for ex in [alvo, *alvo.filhos]:
            if regra not in ex.regras:
                ex.regras.append(regra)
        if regra.escopo == "tarefa" and regra not in alvo.regras_tarefa:
            alvo.regras_tarefa.append(regra)

    def _log(self, nome, alvo, decisao, origem, regra=None) -> None:
        try:
            banco.registrar_permissao(self.mae.conversa_id if self.mae else self.conversa_id, self.id, nome,
                                      str(alvo or ""), decisao, origem or "", regra if isinstance(regra, str) or regra
                                      is None else getattr(regra, "texto", None))
        except Exception:
            traceback.print_exc()

    def _rotina_parou(self, tid, nome, alvo, motivo, sugestao) -> dict:
        """Numa rotina ninguém responde: em vez de perguntar, ela para e conta o que precisaria de OK."""
        self.pediu_ok = {"ferramenta": nome, "alvo": str(alvo or "")[:300], "motivo": motivo, "sugestao": sugestao}
        self._log(nome, alvo, "negar", "rotina")
        self.emitir({"tipo": "rotina_parou", **self.pediu_ok})
        self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True,
                     "resumo": t("A rotina parou: precisaria do seu OK ({motivo})", motivo=motivo)})
        self.parar.set()
        return _res(tid, t("A rotina parou: esta ação precisaria do OK de quem usa, e numa rotina ninguém responde. Crie uma regra de permissão para ela, se quiser que a rotina faça isso sozinha."), True)

    def _fluxo(self, tid: str, entrada: dict, cfg: dict, modo: str) -> dict:
        nome = "executar_fluxo"
        if self.op.get("rotina") or self.op.get("etapa_de_fluxo"):
            return _res(tid, t("Fluxo não roda aqui (rotina ou dentro de outro fluxo)."), True)
        regra = permissoes.nega(self.regras, "Fluxo")
        if regra:
            self._log(nome, "fluxo", "negar", "regra", regra)
            return _res(tid, t("Bloqueado pelo Clave: {motivo}.", motivo=regra.descrever()), True)
        conv = banco.conversa(self.conversa_id)
        pasta = conv.get("pasta") if modo == "code" else None
        modelo = self.op.get("modelo") or cfg.get("modelo_code" if modo == "code" else "modelo_chat")
        try:
            proposta = fluxos.normalizar(entrada, fid=tid, pasta=pasta, modelo_padrao=modelo, regras=self.regras)
        except fluxos.ErroFluxo as e:
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": str(e)})
            return _res(tid, t("Fluxo inválido: {erro}. Corrija e proponha de novo.", erro=e), True)
        banco.salvar_fluxo({**proposta, "conversa_id": self.conversa_id, "execucao_id": self.id})
        d = self._pedir_aprovacao(tid, nome, entrada, "fluxo", None, extra={"proposta": proposta},
                                  tipo="fluxo_proposta")
        if d != "permitir":
            proposta["status"] = "recusado"
            banco.salvar_fluxo({**proposta, "conversa_id": self.conversa_id, "execucao_id": self.id})
            self._log(nome, proposta["titulo"], "recusar", "voce")
            return self._recusado(tid, nome)
        try:
            proposta = fluxos.aplicar_ajustes(proposta, (self.aprovacoes[tid].get("dados") or {}))
        except fluxos.ErroFluxo as e:
            return _res(tid, t("O fluxo não rodou: {erro}.", erro=e), True)
        self._log(nome, proposta["titulo"], "permitir", "voce")
        rodada = fluxos.Rodada(self, proposta, cfg)
        relatorio = rodada.rodar()
        self.custo_fluxos += float(proposta.get("custo_usd") or 0)
        self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": proposta["status"] == "erro",
                     "resumo": t("Fluxo {status}: US$ {custo}", status=t(proposta["status"]),
                                 custo=f"{proposta['custo_usd']:.4f}")})
        return _res(tid, relatorio, proposta["status"] == "erro")

    def _plano(self, tid: str, entrada: dict) -> dict:
        nome = "apresentar_plano"
        d = self._pedir_aprovacao(tid, nome, entrada, "plano", None, extra={"plano": str(entrada.get("plano") or "")},
                                  tipo="plano_proposto")
        novo = MODOS_PERMISSAO.get(d or "")
        if not novo:
            texto = (self.aprovacoes.get(tid) or {}).get("texto") or ""
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False,
                         "resumo": t("continuar planejando")})
            return _res(tid, t("Quem usa quer continuar planejando antes de executar.") +
                        (t(" Comentário: {comentario}", comentario=texto) if texto else t(" Pergunte o que mudar no plano.")))
        self.op["permissao"] = novo
        if self.ctx is not None:
            self._log(nome, "plano", "permitir", "voce")
        self.emitir({"tipo": "modo_mudou", "permissao": novo})
        self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False,
                     "resumo": t("plano aprovado ({modo})", modo=t(NOMES_MODO[novo]))})
        return _res(tid, t("Plano aprovado por quem usa. O modo de permissão agora é {modo}: execute o plano, passo a passo, conferindo o resultado no fim.", modo=t(NOMES_MODO[novo])))

    def _sugerir(self, tid: str, entrada: dict, modo: str) -> dict:
        nome = "sugerir_conversa"
        titulo = " ".join(str(entrada.get("titulo") or "").split())[:80]
        pedido = str(entrada.get("pedido") or "").strip()[:8000]
        if not titulo or not pedido:
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True,
                         "resumo": t("faltou título ou pedido")})
            return _res(tid, t("Faltou o título ou o pedido da sugestão."), True)
        self.emitir({"tipo": "sugestao_conversa", "id": tid, "titulo": titulo, "pedido": pedido,
                     "por_que": str(entrada.get("por_que") or "").strip()[:400], "modo": modo})
        self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False,
                     "resumo": t("sugeriu: {titulo}", titulo=titulo)})
        return _res(tid, t("A sugestão apareceu para quem usa como um cartão; é ele que decide se abre a outra conversa. Não repita no texto a sugestão nem o que você já escreveu: se a resposta já foi dada, termine aqui."))

    def _email(self, tid: str, nome: str, entrada: dict) -> dict:
        """Ler é livre (a não ser regra de negar); enviar sempre mostra o e-mail e pede OK, menos com uma regra de
        permitir escrita para isso: Email(enviar). Rotina para no envio sem essa regra."""
        acao = "enviar" if nome == "email_enviar" else "ler"
        decisao_regra, regra = permissoes.avaliar(self.regras, [("Email", acao)], None)
        if decisao_regra == "deny":
            self._log(nome, acao, "negar", "regra", regra)
            return _res(tid, t("Bloqueado pelo Clave: {motivo}.", motivo=regra.descrever()), True)
        anexos: list[Path] = []
        if acao == "enviar":
            for c in entrada.get("anexos") or []:
                if self.ctx is None:
                    return _res(tid, t("Anexo só dá para mandar no modo Code (no chat não há pasta)."), True)
                p = self.ctx.resolver(str(c))
                if not self.ctx.dentro(p) or not p.is_file():
                    return _res(tid, t("Anexo fora da pasta de trabalho ou inexistente: {caminho}", caminho=c), True)
                if self.ctx.protegido(p):
                    return _res(tid, t("Anexo protegido não sai por e-mail: {caminho}", caminho=c), True)
                anexos.append(p)
            if decisao_regra != "allow" or permissoes.generica(regra):
                motivo = t("envia um e-mail")
                if self.op.get("rotina"):
                    return self._rotina_parou(tid, nome, entrada.get("para", ""), motivo, "Email(enviar)")
                d = self._pedir_aprovacao(tid, nome, entrada, motivo, femail.previa(entrada),
                                          extra={"sugestao": "Email(enviar)", "pode_sempre": False})
                if d not in ("permitir", "permitir_tarefa"):
                    self._log(nome, entrada.get("para", ""), "recusar", "voce")
                    return self._recusado(tid, nome)
                self._log(nome, entrada.get("para", ""), "permitir", "voce")
            else:
                self._log(nome, entrada.get("para", ""), "auto", "regra", regra)
        self.emitir({"tipo": "ferramenta_rodando", "id": tid, "nome": nome})
        try:
            saida = femail.enviar(entrada, anexos) if acao == "enviar" else femail.ler(entrada)
        except femail.ErroEmail as e:
            self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": str(e)})
            return _res(tid, str(e), True)
        self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False, "resumo": saida[:4000]})
        return _res(tid, saida)

    def _recusado(self, tid, nome) -> dict:
        texto = (self.aprovacoes.get(tid) or {}).get("texto") or ""
        msg = t("Quem usa recusou esta ação.") + (t(" Comentário: {comentario}", comentario=texto) if texto else "")
        self.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": msg})
        return _res(tid, msg, True)


def _motivo_e(motivo: str, *chaves: str) -> bool:
    """O motivo de fcode.decidir vem traduzido: compara com a chave em português e com as traduções dela
    (o idioma pode ter mudado enquanto o cartão esperava a resposta)."""
    return any(motivo in (c, t(c), t(c, "en")) for c in chaves)


def _res(tid: str, conteudo, erro=False) -> dict:
    r = {"type": "tool_result", "tool_use_id": tid, "content": conteudo if conteudo else t("(vazio)")}
    if erro:
        r["is_error"] = True
    return r


def _resumo_alvo(nome: str, e: dict, ctx: fcode.Contexto) -> str:
    e = e or {}
    if nome == "rodar_comando":
        return str(e.get("comando", ""))[:500]
    partes = []
    for campo in ("caminho", "saida"):
        if isinstance(e.get(campo), str) and e.get(campo):
            p = ctx.resolver(e[campo])
            partes.append(ctx.relativo(p) if ctx.dentro(p) else str(p))
    return " → ".join(partes) or nome


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
    # depois de um /compact, o pedido começa no bloco do resumo: o que veio antes não vai mais (regra da API)
    ultimo = max((i for i, m in enumerate(caminho) if m.get("tipo") == "compactacao"), default=None)
    if ultimo is not None:
        caminho = caminho[ultimo:]
    msgs = []
    contexto = conv.get("contexto") or []
    primeira_da_pessoa = True
    for m in caminho:
        conteudo = m["conteudo"]
        if m["papel"] == "user" and primeira_da_pessoa:
            primeira_da_pessoa = False
            if contexto:
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
    base = t("O Claude recusou este pedido pelas regras de segurança da Anthropic")
    if cat:
        base += t(" (categoria: {categoria})", categoria=t(nomes[cat]) if cat in nomes else cat)
    return base + t(". Reformule o pedido ou tente outro modelo.")


def _explicar_erro(e: Exception) -> str:
    if isinstance(e, anthropic.AuthenticationError):
        return t("A chave da API foi recusada. Confira em Configurações > Conta e chave.")
    if isinstance(e, anthropic.PermissionDeniedError):
        return t("A chave não tem permissão para isso (ou o modelo não está liberado na sua conta). ") + _mensagem_api(e)
    if isinstance(e, anthropic.NotFoundError):
        return t("Modelo não encontrado na sua conta. Escolha outro modelo. ") + _mensagem_api(e)
    if isinstance(e, anthropic.RateLimitError):
        return t("A API pediu para esperar (limite de pedidos por minuto). Tente de novo daqui a pouco.")
    if isinstance(e, anthropic.BadRequestError):
        msg = _mensagem_api(e)
        if "credit balance" in msg.lower():
            return t("Acabou o crédito da sua conta na API da Anthropic. Recarregue no Console (platform.claude.com) ou espere o crédito do mês seguinte.")
        if "prompt is too long" in msg.lower() or "too long" in msg.lower():
            return t("A conversa ficou grande demais para o modelo. Comece uma conversa nova. ({erro})", erro=msg)
        return t("A API recusou o pedido: {erro}", erro=msg)
    if isinstance(e, anthropic.APIStatusError):
        if e.status_code in (500, 529) or e.status_code >= 500:
            return t("Os servidores da Anthropic estão sobrecarregados ou com problema agora. Tente de novo em instantes.")
        return t("Erro da API ({status}): {erro}", status=e.status_code, erro=_mensagem_api(e))
    if isinstance(e, anthropic.APIConnectionError):
        return t("Sem conexão com a API da Anthropic. Confira a internet.")
    return t("Erro inesperado: {erro}", erro=e)


def iniciar(conversa_id: str, opcoes: dict) -> Execucao:
    with _trava:
        atual = _por_conversa.get(conversa_id)
        if atual and _execucoes.get(atual) and _execucoes[atual].status in ("rodando", "esperando"):
            raise RuntimeError(t("Esta conversa já está respondendo. Espere terminar ou aperte Parar."))
        ex = Execucao(conversa_id, opcoes)
        _execucoes[ex.id] = ex
        _por_conversa[conversa_id] = ex.id
    threading.Thread(target=ex.rodar, name=f"execucao-{ex.id}", daemon=True).start()
    return ex


def iniciar_sem_thread(conversa_id: str, opcoes: dict) -> Execucao:
    """Registra a execução mas deixa quem chamou decidir onde rodar (as rotinas acompanham o fim)."""
    with _trava:
        ex = Execucao(conversa_id, opcoes)
        _execucoes[ex.id] = ex
        _por_conversa[conversa_id] = ex.id
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
    padrao = (texto.strip().splitlines() or [t("Conversa")])[0][:60] or t("Conversa")
    cfg = config.carregar()
    if not cfg.get("titulos_automaticos", True) or not orcamento.pode_gastar()[0]:
        banco.atualizar_conversa(conversa_id, titulo=padrao)
        return
    try:
        cli = cliente()
        r = cli.messages.create(
            model="claude-haiku-5-5", max_tokens=60, thinking={"type": "disabled"},
            output_config={"effort": "low"},
            system=t("Crie um título curto (no máximo 6 palavras, sem aspas e sem ponto final) para uma conversa que começa com a mensagem abaixo, no mesmo idioma dela. Responda só com o título."),
            messages=[{"role": "user", "content": texto[:4000] or t("Conversa")}])
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
    return "\n".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"
                     and not b.get("text", "").startswith(MARCA_MODO))


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
            feitos.append(t("{caminho} (falhou: {erro})", caminho=p, erro=e))
    banco.marcar_desfeito(execucao_id)
    return feitos


def modelos_disponiveis() -> list[str] | None:
    try:
        cli = cliente()
        return [m.id for m in cli.models.list(limit=100).data]
    except Exception:
        return None
