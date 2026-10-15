"""Trabalho em segundo plano: o registro que a aba Tarefas mostra.

Duas fontes entram na lista:
- o que se registra aqui com registrar(): os comandos que o Claude deixou rodando (ferramentas/code.py) e os
  downloads (videos.py). Cada tarefa guarda o registro da saída (até uns 200 KB na memória, também em
  <dados>/tarefas/<id>.log), os endereços locais que apareceram nela e, se quem registrou deixou, como parar;
- o que já existe em outros módulos e é só lido daqui: as respostas rodando agora (execucao._execucoes), os fluxos
  dessas respostas (os eventos fluxo_inicio/fluxo_fim da resposta e a proposta salva no banco) e as rotinas.

As terminadas ficam na lista por 30 minutos. Rotas: GET /api/tarefas, GET /api/tarefas/<id> (detalhes e o fim do
registro) e POST /api/tarefas/<id>/parar. Apagar uma conversa chama parar_da_conversa() antes: os comandos dela e a
resposta rodando param junto, e o que já terminou continua na lista sem o "Ir para a conversa" (conversa_existe).
"""
from __future__ import annotations

import re
import threading
import time
import uuid

import config
from i18n import t
from rotas import Erro, rota

LIMITE_REGISTRO = 200 * 1024          # caracteres do registro guardados na memória por tarefa
LIMITE_ARQUIVO = 2 * 1024 * 1024      # passou disso, o .log é regravado só com o fim do registro
GUARDAR_TERMINADAS = 30 * 60          # segundos que uma tarefa terminada continua na lista
MAX_TERMINADAS = 100                  # e no máximo tantas terminadas do registro
RESPOSTA_LONGA = 30                   # resposta terminada só entra na lista se levou pelo menos isto (segundos)
TIPOS = ("comando", "download")
FINAIS = ("concluida", "erro", "parada")

# códigos de cor e de cursor do terminal (npm e vite colorem a saída, às vezes no meio do endereço)
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")
# endereço local com porta: localhost, 127.0.0.1, 0.0.0.0, [::1] e [::] (o python -m http.server mostra este)
_URL = re.compile(r"https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1?\]):(\d{1,5})(/[^\s'\"<>`|]*)?", re.I)
_FIM_PARTIDO = re.compile(r"(?:\x1b(?:\[[0-9;?]*[ -/]*|\][^\x07\x1b]*)?|\r)$")
_SEM = object()


def limpar_terminal(texto: str) -> str:
    """Tira os códigos de cor e transforma o \\r de barra de progresso em quebra de linha."""
    return _ANSI.sub("", texto).replace("\r\n", "\n").replace("\r", "\n")


def achar_urls(texto: str) -> list[str]:
    """Os endereços locais de um trecho de saída, prontos para abrir (0.0.0.0 e [::] viram localhost)."""
    achados = []
    for m in _URL.finditer(limpar_terminal(texto)):
        porta = int(m.group(1))
        if not 0 < porta < 65536:
            continue
        caminho = (m.group(2) or "/").rstrip(".,;:!?'\")]}") or "/"
        esquema, resto = m.group(0).split("://", 1)
        host = (resto.split("]", 1)[0] + "]") if resto.startswith("[") else resto.split(":", 1)[0]
        host = host.lower()
        if host in ("0.0.0.0", "[::]"):  # escutando em todas as placas: no navegador, é o localhost
            host = "localhost"
        url = f"{esquema.lower()}://{host}:{porta}{caminho}"
        if url not in achados:
            achados.append(url)
    return achados


class Tarefa:
    """Uma tarefa registrada (comando em segundo plano ou download). Os métodos podem ser chamados de qualquer thread."""

    def __init__(self, tipo: str, titulo: str, conversa_id: str | None, detalhe: str, parar):
        self.id = f"{tipo}-{uuid.uuid4().hex[:12]}"
        self.tipo = tipo
        self.titulo = str(titulo or "")[:200]
        self.conversa_id = conversa_id
        self.detalhe = str(detalhe or "")[:600]
        self.status = "rodando"
        self.inicio = time.time()
        self.fim: float | None = None
        self.progresso: float | None = None
        self.urls: list[str] = []
        self.comando: str | None = None    # o comando de verdade (a aba mostra em fonte de código)
        self.pasta: str | None = None
        self.codigo: int | None = None     # código de saída de um comando que terminou
        self.parando = False
        self.ultima_saida = 0.0
        self.bytes_saida = 0
        self._parar = parar
        self._trava = threading.Lock()
        self._pedacos: list[str] = []
        self._tamanho = 0
        self._cortado = False
        self._parcial = ""                 # linha ainda sem \n (o endereço só é procurado em linha inteira)
        self._resto = ""                   # pedaço de código de cor que ficou partido no fim do último pedaço
        self._arquivo = None
        self._caminho = config.DADOS / "tarefas" / f"{self.id}.log"

    # ---- o que quem registrou chama ----
    def atualizar(self, progresso=_SEM, detalhe=None) -> None:
        """progresso de 0 a 1 (None quando não dá para saber); detalhe é a linha de baixo do título."""
        with self._trava:
            if progresso is not _SEM:
                self.progresso = None if progresso is None else max(0.0, min(1.0, float(progresso)))
            if detalhe is not None:
                self.detalhe = str(detalhe)[:600]

    def saida(self, texto: str) -> None:
        """Acrescenta um pedaço ao registro (e procura nele os endereços locais)."""
        if not texto:
            return
        with self._trava:
            self.ultima_saida = time.time()
            self.bytes_saida += len(texto)
            # um código de cor (ou um \r\n) partido entre dois pedaços espera o resto chegar
            texto = self._resto + texto
            m = _FIM_PARTIDO.search(texto)
            if m and len(texto) - m.start() > 64:  # não é um código partido, é texto solto depois de um ESC
                m = None
            self._resto, texto = (texto[m.start():], texto[:m.start()]) if m else ("", texto)
            limpo = limpar_terminal(texto)
            if not limpo:
                return
            self._pedacos.append(limpo)
            self._tamanho += len(limpo)
            while self._tamanho > LIMITE_REGISTRO and self._pedacos:
                excesso = self._tamanho - LIMITE_REGISTRO
                primeiro = self._pedacos[0]
                if len(primeiro) <= excesso:
                    self._pedacos.pop(0)
                    self._tamanho -= len(primeiro)
                else:
                    self._pedacos[0] = primeiro[excesso:]
                    self._tamanho -= excesso
                self._cortado = True
            junto = self._parcial + limpo
            linhas, _, self._parcial = junto.rpartition("\n")
            procurar = linhas
            # a linha sem \n também vale quando o endereço já terminou nela (tem algo depois dele)
            for m in _URL.finditer(self._parcial):
                if m.end() < len(self._parcial):
                    procurar += "\n" + m.group(0) + " "
            if len(self._parcial) > 4000:
                self._parcial = self._parcial[-4000:]
            for url in achar_urls(procurar):
                if url not in self.urls and len(self.urls) < 10:
                    self.urls.append(url)
            self._gravar(limpo)

    def terminar(self, status: str = "concluida", detalhe: str | None = None) -> None:
        with self._trava:
            if self.status in FINAIS:
                return
            self.status = status if status in FINAIS else "concluida"
            self.fim = time.time()
            if detalhe is not None:
                self.detalhe = str(detalhe)[:600]
            if self.status == "concluida" and self.progresso is not None:
                self.progresso = 1.0
            if self._parcial:
                for url in achar_urls(self._parcial):
                    if url not in self.urls and len(self.urls) < 10:
                        self.urls.append(url)
            if self._arquivo:
                try:
                    self._arquivo.close()
                except OSError:
                    pass
                self._arquivo = None

    # ---- o que a aba e as rotas usam ----
    @property
    def rodando(self) -> bool:
        return self.status == "rodando"

    @property
    def pode_parar(self) -> bool:
        return self.rodando and self._parar is not None

    def parar(self) -> bool:
        """Pede para parar (quem registrou decide como). Devolve se havia como pedir."""
        if not self.pode_parar:
            return False
        self.parando = True
        try:
            self._parar()
        except Exception:  # parar é melhor esforço: a tarefa segue na lista com o que aconteceu
            import traceback
            traceback.print_exc()
            return False
        return True

    def registro(self, linhas: int | None = None) -> str:
        with self._trava:
            texto = "".join(self._pedacos)
        if linhas:
            partes = texto.rstrip("\n").split("\n")
            if len(partes) > linhas:
                texto = "\n".join(partes[-linhas:])
        return texto

    @property
    def cortado(self) -> bool:
        return self._cortado

    def item(self) -> dict:
        with self._trava:
            return {
                "id": self.id, "tipo": self.tipo, "titulo": self.titulo, "detalhe": self.detalhe,
                "status": "rodando" if self.rodando else self.status, "inicio": self.inicio, "fim": self.fim,
                "custo": None, "progresso": self.progresso, "passos": None, "conversa_id": self.conversa_id,
                "conversa_titulo": None, "modo": None, "urls": list(self.urls), "comando": self.comando,
                "pode_parar": self.pode_parar, "parando": self.parando and self.rodando,
                "registro": self.tipo == "comando" or self.bytes_saida > 0,  # download que não escreve nada não tem registro
                "codigo": self.codigo, "conversa_existe": None,  # listar() e detalhes() conferem no banco
            }

    def _gravar(self, texto: str) -> None:
        """Espelha o registro no .log (chamado com a trava pega). Erro de disco não atrapalha a tarefa."""
        try:
            if self._arquivo is None:
                if self.status in FINAIS:
                    return
                self._caminho.parent.mkdir(parents=True, exist_ok=True)
                self._arquivo = open(self._caminho, "a", encoding="utf-8", newline="")
            self._arquivo.write(texto)
            self._arquivo.flush()
            if self._arquivo.tell() > LIMITE_ARQUIVO:
                self._arquivo.close()
                self._arquivo = open(self._caminho, "w", encoding="utf-8", newline="")
                self._arquivo.write("".join(self._pedacos))
                self._arquivo.flush()
        except (OSError, ValueError):
            self._arquivo = None

    def _apagar_arquivo(self) -> None:
        try:
            self._caminho.unlink(missing_ok=True)
        except OSError:
            pass


_tarefas: dict[str, Tarefa] = {}
_trava = threading.Lock()


def conversa_dona(conversa_id: str | None) -> str | None:
    """A conversa que responde por uma tarefa: a de uma etapa de fluxo (conversa escondida, modo "etapa") é a
    conversa principal que rodou o fluxo (ajustes.conversa_mae, que fluxos.py grava). Assim a conversa principal vê
    e para o que a etapa deixou rodando, e o "Ir para a conversa" leva a ela."""
    vistos = set()
    while conversa_id and conversa_id not in vistos:
        vistos.add(conversa_id)
        try:
            import banco
            conv = banco.conversa(conversa_id)
        except Exception:  # sem banco (um teste isolado): fica a que veio
            return conversa_id
        mae = (conv.get("ajustes") or {}).get("conversa_mae") if conv and conv.get("modo") == "etapa" else None
        if not mae:
            return conversa_id
        conversa_id = mae
    return conversa_id


def registrar(tipo: str, titulo: str, *, conversa_id: str | None = None, detalhe: str = "", parar=None) -> Tarefa:
    """Põe uma tarefa na lista. tipo é "comando" ou "download"; parar, se vier, é chamado sem argumentos quando
    alguém aperta Parar (quem registrou continua responsável por chamar terminar, com status "parada"). Os
    downloads também aceitam parar: sem ele, a tarefa não mostra o botão Parar. A conversa de uma etapa de fluxo vira
    a conversa principal (conversa_dona)."""
    if tipo not in TIPOS:
        raise ValueError(f"tipo de tarefa desconhecido: {tipo}")
    tf = Tarefa(tipo, titulo, conversa_dona(conversa_id), detalhe, parar)
    with _trava:
        _tarefas[tf.id] = tf
    _limpar()
    return tf


def pegar(tid: str) -> Tarefa | None:
    with _trava:
        return _tarefas.get(tid)


def registradas() -> list[Tarefa]:
    with _trava:
        return list(_tarefas.values())


def urls_locais(detalhes: bool = False) -> list:
    """Os endereços locais que apareceram na saída dos comandos em segundo plano que ainda estão rodando (para o
    navegador do app sugerir). Com detalhes=True, uma lista de {url, tarefa, titulo, conversa_id}."""
    saida, vistos = [], set()
    for tf in sorted(registradas(), key=lambda x: x.inicio, reverse=True):
        if tf.tipo != "comando" or not tf.rodando:
            continue
        for u in list(tf.urls):
            if u in vistos:
                continue
            vistos.add(u)
            saida.append({"url": u, "tarefa": tf.id, "titulo": tf.titulo, "conversa_id": tf.conversa_id} if detalhes else u)
    return saida


def _limpar(agora: float | None = None) -> None:
    agora = agora or time.time()
    with _trava:
        terminadas = sorted((tf for tf in _tarefas.values() if not tf.rodando), key=lambda x: x.fim or 0, reverse=True)
        sair = [tf for i, tf in enumerate(terminadas)
                if i >= MAX_TERMINADAS or agora - (tf.fim or agora) > GUARDAR_TERMINADAS]
        for tf in sair:
            _tarefas.pop(tf.id, None)
    for tf in sair:
        tf._apagar_arquivo()
    _limpar_arquivos_velhos(agora)


_ultima_faxina = [0.0]


def _limpar_arquivos_velhos(agora: float) -> None:
    """Os .log de tarefas que não estão mais na lista (de uma vez em que o app fechou) somem depois de um dia."""
    if agora - _ultima_faxina[0] < 600:
        return
    _ultima_faxina[0] = agora
    pasta = config.DADOS / "tarefas"
    if not pasta.is_dir():
        return
    with _trava:
        vivos = set(_tarefas)
    for arq in pasta.glob("*.log"):
        try:
            if arq.stem not in vivos and agora - arq.stat().st_mtime > 86400:
                arq.unlink()
        except OSError:
            pass


# ---------------- as respostas, fluxos e rotinas (lidos de execucao.py) ----------------

_fluxos_vistos: dict[str, list] = {}   # execução -> [eventos já lidos, {fluxo: {"fim": bool, "status": str}}]
_trava_vistos = threading.Lock()


def _fluxos_da(ex) -> dict:
    """Os fluxos que uma resposta começou, lendo só os eventos novos desde a última vez."""
    with _trava_vistos:
        reg = _fluxos_vistos.setdefault(ex.id, [0, {}])
        novos = ex.eventos[reg[0]:]
        reg[0] += len(novos)
        for ev in novos:
            tipo, fid = ev.get("tipo"), ev.get("fluxo")
            if tipo == "fluxo_inicio" and fid:
                reg[1][fid] = {"fim": False, "status": "rodando"}
            elif tipo == "fluxo_fim" and fid in reg[1]:
                reg[1][fid] = {"fim": True, "status": ev.get("status") or "concluido"}
        return dict(reg[1])


def _esquecer_execucoes(vivas: set) -> None:
    with _trava_vistos:
        for eid in [e for e in _fluxos_vistos if e not in vivas]:
            _fluxos_vistos.pop(eid, None)


def _nome_status(s: str) -> str:
    return {"rodando": t("rodando"), "esperando": t("esperando o seu OK"), "concluida": t("concluída"),
            "erro": t("deu erro"), "parada": t("parada")}.get(s, s)


def _status_fluxo(s: str) -> str:
    return {"rodando": "rodando", "concluido": "concluida", "erro": "erro", "parado": "parada", "teto": "erro"}.get(s, "concluida")


def _o_que_espera(ex) -> str:
    """A linha do cartão de uma resposta parada à espera da pessoa: o que está esperando. O selo do cartão já diz
    "Esperando o seu OK", então a linha não repete isso."""
    pedido = None
    for e in [ex, *list(getattr(ex, "filhos", None) or [])]:
        for a in list((getattr(e, "aprovacoes", None) or {}).values()):
            ev = a.get("evento") if isinstance(a, dict) else None
            if ev is not None and not ev.is_set():
                pedido = a.get("pedido") or {}
    if pedido is None:
        return t("Abra a conversa para continuar")
    tipo = pedido.get("tipo")
    if tipo == "plano_proposto":
        return t("Um plano para você aprovar")
    if tipo == "fluxo_proposta":
        return t("Um fluxo para você aprovar")
    if tipo == "pergunta":
        return t("Uma pergunta para você responder")
    entrada = pedido.get("entrada") if isinstance(pedido.get("entrada"), dict) else {}

    def curto(v) -> str:
        return " ".join(str(v).split())[:160]
    if entrada.get("comando"):
        return t("O Claude quer rodar: {comando}", comando=curto(entrada["comando"]))
    if entrada.get("url"):
        return t("O Claude quer abrir: {url}", url=curto(entrada["url"]))
    if entrada.get("para"):
        return t("O Claude quer mandar um e-mail para {para}", para=curto(entrada["para"]))
    if entrada.get("caminho"):
        return t("O Claude quer mexer em: {caminho}", caminho=curto(entrada["caminho"]))
    return t("O Claude quer usar: {ferramenta}", ferramenta=curto(pedido.get("nome") or ""))


def _item_resposta(ex, conv: dict, agora: float) -> dict:
    rodando = ex.status in ("rodando", "esperando")
    status = ex.status if rodando or ex.status in FINAIS else "concluida"
    if status == "esperando":
        detalhe = _o_que_espera(ex)
    elif status == "rodando":
        detalhe = t("Respondendo")
    elif status == "erro":
        detalhe = ex.ultimo_erro or t("A resposta parou com um erro")
    elif status == "parada":
        detalhe = t("Parada antes do fim")
    else:
        detalhe = t("Resposta pronta")
    return {
        "id": f"resposta-{ex.id}", "tipo": "resposta", "titulo": conv.get("titulo") or t("Conversa sem título"),
        "detalhe": detalhe, "status": status, "inicio": getattr(ex, "inicio", None) or agora,
        "fim": None if rodando else (ex.fim_em or agora), "custo": round(ex.custo_total + ex.custo_fluxos, 6),
        "progresso": None, "passos": None, "conversa_id": ex.conversa_id, "conversa_titulo": conv.get("titulo"),
        "modo": conv.get("modo"), "urls": [], "comando": None, "pode_parar": rodando, "parando": rodando and ex.parar.is_set(),
        "registro": True, "codigo": None, "conversa_existe": True,
    }


def _item_rotina(ex, conv: dict, agora: float) -> dict:
    import banco
    item = _item_resposta(ex, conv, agora)
    rid = (conv.get("ajustes") or {}).get("rotina")
    r = banco.rotina(rid) if rid else None
    item.update(id=f"rotina-{ex.id}", tipo="rotina", titulo=(r or {}).get("nome") or item["titulo"],
                custo=round(ex.custo_total, 6))
    if item["status"] == "rodando":
        item["detalhe"] = t("Rodando sozinha, sem ninguém olhando")
    elif getattr(ex, "pediu_ok", None):
        item["detalhe"] = t("Parou: precisaria do seu OK para {acao}",
                            acao=ex.pediu_ok.get("sugestao") or ex.pediu_ok.get("ferramenta") or "")
    elif ex.cofre is not None and ex.cofre.estourou():
        item["detalhe"] = t("Parou no teto de gasto da rotina")
    return item


def _item_fluxo(ex, fid: str, info: dict, conv: dict, agora: float) -> dict | None:
    import banco
    p = banco.fluxo(fid)
    if not p:
        return None
    etapas = [e for e in (p.get("etapas") or []) if isinstance(e, dict)]
    total = len(etapas)
    feitas = sum(1 for e in etapas if e.get("status") in ("concluida", "erro", "parada", "pulada"))
    ids_rodando = {e.get("execucao_id") for e in etapas if e.get("status") == "rodando"}
    filhos = [f for f in list(getattr(ex, "filhos", [])) if f.id in ids_rodando]
    rodando = not info.get("fim") and ex.status in ("rodando", "esperando")
    if rodando:
        status = "esperando" if any(f.status == "esperando" for f in filhos) else "rodando"
        em_curso = [e for e in etapas if e.get("status") == "rodando"]
        if status == "esperando":
            detalhe = t("Uma etapa espera o seu OK na conversa")
        elif len(em_curso) == 1:
            detalhe = t("Etapa {n} de {total}: {nome}", n=em_curso[0].get("i", 0) + 1, total=total,
                        nome=em_curso[0].get("nome") or "")
        elif em_curso:
            detalhe = t("{n} etapas ao mesmo tempo: {nomes}", n=len(em_curso),
                        nomes=", ".join(str(e.get("nome") or "") for e in em_curso))
        else:
            detalhe = t("{feitas} de {total} etapas prontas", feitas=feitas, total=total)
    else:
        bruto = info.get("status") if info.get("fim") else p.get("status")
        status = _status_fluxo(bruto or "concluido")
        if status == "rodando":  # a resposta acabou sem o fluxo avisar o fim
            status = "parada"
        # a barra já mostra quantas etapas ficaram prontas: o detalhe só conta o que deu diferente
        detalhe = {"teto": t("Parou no teto de gasto aprovado"), "erro": t("Uma etapa deu erro"),
                   "parado": t("Parado antes do fim")}.get(bruto or "", "")
        if status == "parada" and not detalhe:
            detalhe = t("Parado antes do fim")
    inicios = [e["inicio"] for e in etapas if isinstance(e.get("inicio"), (int, float))]
    fins = [e["fim"] for e in etapas if isinstance(e.get("fim"), (int, float))]
    custo = float(p.get("custo_usd") or 0) + sum(f.custo_total for f in filhos)
    return {
        "id": f"fluxo-{fid}", "tipo": "fluxo", "titulo": p.get("titulo") or t("Fluxo"), "detalhe": detalhe,
        "status": status, "inicio": min(inicios) if inicios else (getattr(ex, "inicio", None) or agora),
        "fim": None if rodando else (max(fins) if fins else (ex.fim_em or agora)), "custo": round(custo, 6),
        "progresso": (feitas / total) if total else None, "passos": {"feitos": feitas, "total": total},
        "conversa_id": ex.conversa_id, "conversa_titulo": conv.get("titulo"), "modo": conv.get("modo"), "urls": [],
        "comando": None, "pode_parar": rodando, "parando": rodando and ex.parar.is_set(), "registro": True,
        "codigo": None, "conversa_existe": True,
    }


def _das_execucoes(agora: float, conversas: dict) -> list[dict]:
    try:
        import execucao
    except Exception:  # sem o motor (um teste isolado, por exemplo) a lista fica só com as registradas
        return []
    saida = []
    todas = list(execucao._execucoes.values())
    _esquecer_execucoes({ex.id for ex in todas})
    for ex in todas:
        if getattr(ex, "mae", None) is not None or ex.op.get("etapa_de_fluxo"):
            continue  # etapa de fluxo: aparece dentro do fluxo
        rodando = ex.status in ("rodando", "esperando")
        inicio = getattr(ex, "inicio", None) or agora
        fim = None if rodando else (ex.fim_em or agora)
        if fim is not None and agora - fim > GUARDAR_TERMINADAS:
            continue
        fluxos = _fluxos_da(ex)
        rotina = bool(ex.op.get("rotina"))
        if not rodando and not rotina and not fluxos and fim - inicio < RESPOSTA_LONGA:
            continue  # resposta curta que já terminou não é trabalho em segundo plano
        conv = _conversa(ex.conversa_id, conversas)
        if not conv or conv.get("modo") not in ("chat", "code"):
            continue  # ajudantes (lição, memória) ficam de fora
        fluxo_rodando = False
        for fid, info in fluxos.items():
            item = _item_fluxo(ex, fid, info, conv, agora)
            if item and (item["fim"] is None or agora - item["fim"] <= GUARDAR_TERMINADAS):
                saida.append(item)
                fluxo_rodando = fluxo_rodando or item["fim"] is None
        if rotina:
            saida.append(_item_rotina(ex, conv, agora))
        elif not fluxo_rodando and (rodando or fim - inicio >= RESPOSTA_LONGA):
            # enquanto um fluxo roda, a resposta que o começou só espera por ele: aparece só o fluxo
            saida.append(_item_resposta(ex, conv, agora))
    return saida


def _conversa(cid: str | None, cache: dict) -> dict | None:
    if not cid:
        return None
    if cid not in cache:
        import banco
        try:
            cache[cid] = banco.conversa(cid)
        except Exception:
            cache[cid] = None
    return cache[cid]


def _completar_conversa(it: dict, conv: dict | None) -> None:
    """O título e o modo da conversa de uma tarefa registrada; conversa_existe=False quando ela foi apagada (a aba
    esconde o "Ir para a conversa")."""
    if not it.get("conversa_id"):
        return
    it["conversa_existe"] = bool(conv)
    if conv:
        it["conversa_titulo"] = conv.get("titulo") or t("Conversa sem título")
        it["modo"] = conv.get("modo")


def listar() -> dict:
    """Tudo o que a aba mostra: {"rodando": [...], "terminadas": [...], "agora": hora do servidor}."""
    agora = time.time()
    _limpar(agora)
    conversas: dict = {}
    itens = [tf.item() for tf in registradas()]
    for it in itens:
        _completar_conversa(it, _conversa(it["conversa_id"], conversas))
    itens += _das_execucoes(agora, conversas)
    rodando = sorted((i for i in itens if i["status"] in ("rodando", "esperando")), key=lambda i: i["inicio"], reverse=True)
    terminadas = sorted((i for i in itens if i["status"] not in ("rodando", "esperando")
                         and agora - (i["fim"] or agora) <= GUARDAR_TERMINADAS),
                        key=lambda i: i["fim"] or 0, reverse=True)[:60]
    return {"rodando": rodando, "terminadas": terminadas, "agora": agora}


def _achar(tid: str) -> tuple[dict | None, object]:
    """O item da lista e o objeto por trás dele (Tarefa ou Execucao)."""
    tf = pegar(tid)
    if tf:
        return tf.item(), tf
    lista = listar()
    item = next((i for i in lista["rodando"] + lista["terminadas"] if i["id"] == tid), None)
    if not item:
        return None, None
    import execucao
    if item["tipo"] in ("resposta", "rotina"):
        return item, execucao.pegar(tid.split("-", 1)[1])
    if item["tipo"] == "fluxo":
        fid = tid.split("-", 1)[1]
        with _trava_vistos:
            eid = next((e for e, reg in _fluxos_vistos.items() if fid in reg[1]), None)
        return item, execucao.pegar(eid) if eid else None
    return item, None


def parar(tid: str) -> dict:
    """Para uma tarefa: comando (com tudo o que ele abriu), download que aceita parar, resposta, rotina ou fluxo
    (o fluxo para junto com a resposta que o rodou). Devolve {"ok", "ja_terminou"}; Erro quando não existe."""
    item, obj = _achar(tid)
    if not item:
        raise Erro(404, t("Esta tarefa não existe mais (as terminadas saem da lista depois de 30 minutos)."))
    if item["status"] not in ("rodando", "esperando"):
        return {"ok": True, "ja_terminou": True}
    if isinstance(obj, Tarefa):
        if not obj.pode_parar:
            raise Erro(409, t("Esta tarefa não tem como ser parada; ela termina sozinha."))
        if not obj.parar():
            raise Erro(500, t("Não deu para parar esta tarefa. Tente de novo."))
        return {"ok": True, "ja_terminou": False}
    if obj is None:
        raise Erro(404, t("Esta tarefa não existe mais (as terminadas saem da lista depois de 30 minutos)."))
    obj.interromper()
    return {"ok": True, "ja_terminou": False}


def parar_da_conversa(conversa_id: str, esperar: float = 0.0) -> dict:
    """Para tudo o que roda por uma conversa: os comandos em segundo plano dela (e os das etapas dos fluxos dela), os
    downloads registrados nela que aceitam parar e a resposta rodando (que leva junto os fluxos e as etapas). Para
    chamar antes de apagar a conversa. Com esperar, espera até tantos segundos as respostas saírem de rodando.
    Devolve {"tarefas": quantas pediram para parar, "respostas": quantas, "ainda_rodando": alguma resposta segue}."""
    n_tarefas = 0
    for tf in registradas():
        if tf.conversa_id == conversa_id and tf.pode_parar:
            n_tarefas += 1 if tf.parar() else 0
    vivas = []
    try:
        import execucao
        todas = list(execucao._execucoes.values())
    except Exception:  # sem o motor (um teste isolado)
        todas = []
    for ex in todas:
        if ex.status not in ("rodando", "esperando"):
            continue
        if ex.conversa_id == conversa_id or conversa_dona(ex.conversa_id) == conversa_id:
            ex.interromper()
            vivas.append(ex)
    n_respostas = len(vivas)
    fim = time.time() + max(0.0, esperar)
    while True:
        vivas = [ex for ex in vivas if ex.status in ("rodando", "esperando")]
        if not vivas or time.time() >= fim:
            break
        time.sleep(0.1)
    return {"tarefas": n_tarefas, "respostas": n_respostas, "ainda_rodando": bool(vivas)}


def _linhas_eventos(evs: list[dict], prefixo: str = "") -> list[str]:
    linhas = []
    for ev in evs:
        tipo = ev.get("tipo")
        if tipo == "ferramenta_fim":
            resumo = " ".join(str(ev.get("resumo") or "").split())[:160]
            linhas.append(f"{prefixo}{'x' if ev.get('erro') else '+'} {ev.get('nome')}" + (f": {resumo}" if resumo else ""))
        elif tipo == "pergunta":
            linhas.append(prefixo + t("Esperando você responder uma pergunta"))
        elif tipo == "plano_proposto":
            linhas.append(prefixo + t("Esperando você aprovar o plano"))
        elif tipo == "fluxo_proposta":
            linhas.append(prefixo + t("Esperando você aprovar o fluxo"))
        elif tipo == "aprovacao":
            entrada = ev.get("entrada") if isinstance(ev.get("entrada"), dict) else {}
            alvo = " ".join(str(entrada.get("comando") or entrada.get("caminho") or entrada.get("para") or "").split())[:160]
            linhas.append(prefixo + t("Esperando o seu OK: {acao}", acao=f"{ev.get('nome')}: {alvo}" if alvo else ev.get("nome") or ""))
        elif tipo == "erro":
            linhas.append(prefixo + t("Erro: {erro}", erro=ev.get("mensagem") or ""))
        elif tipo == "aviso":
            linhas.append(prefixo + t("Aviso: {aviso}", aviso=ev.get("mensagem") or ""))
        elif tipo == "fim":
            linhas.append(prefixo + t("Fim: {status}", status=_nome_status(ev.get("status") or "")))
    return linhas


def _registro_sintetico(item: dict, obj) -> str:
    """Para respostas, rotinas e fluxos o registro é montado dos eventos: as ferramentas usadas, os pedidos de OK e
    as etapas, uma linha cada."""
    if obj is None:
        return ""
    evs = list(obj.eventos)
    if item["tipo"] != "fluxo":
        return "\n".join(_linhas_eventos(evs))
    fid = item["id"].split("-", 1)[1]
    linhas = []
    for ev in evs:
        if ev.get("fluxo") != fid:
            continue
        tipo = ev.get("tipo")
        if tipo == "fluxo_inicio":
            linhas.append(t("Fluxo começou: {titulo}", titulo=(ev.get("proposta") or {}).get("titulo") or ""))
        elif tipo == "etapa_inicio":
            linhas.append(t("Etapa {n} começou ({modelo})", n=int(ev.get("etapa") or 0) + 1,
                            modelo=ev.get("modelo_nome") or ev.get("modelo") or ""))
        elif tipo == "etapa_fim":
            linhas.append(t("Etapa {n} terminou: {status}, US$ {custo}", n=int(ev.get("etapa") or 0) + 1,
                            status=_nome_status(ev.get("status") or ""), custo=f"{float(ev.get('custo_usd') or 0):.4f}"))
        elif tipo == "etapa_evento" and isinstance(ev.get("ev"), dict):
            linhas += _linhas_eventos([ev["ev"]], f"  [{int(ev.get('etapa') or 0) + 1}] ")
        elif tipo == "fluxo_fim":
            linhas.append(t("Fluxo terminou: {status}", status=_nome_status(_status_fluxo(ev.get("status") or ""))))
    return "\n".join(linhas)


def detalhes(tid: str, linhas: int = 400) -> dict:
    item, obj = _achar(tid)
    if not item:
        raise Erro(404, t("Esta tarefa não existe mais (as terminadas saem da lista depois de 30 minutos)."))
    linhas = max(1, min(5000, int(linhas or 400)))
    if isinstance(obj, Tarefa):
        texto, cortado = obj.registro(linhas), obj.cortado
        _completar_conversa(item, _conversa(item.get("conversa_id"), {}))
    else:
        texto = _registro_sintetico(item, obj)
        partes = texto.split("\n")
        cortado = len(partes) > linhas
        texto = "\n".join(partes[-linhas:])
    return {"tarefa": item, "registro": texto, "cortado": cortado}


# ---------------- rotas ----------------

@rota("GET", "/api/tarefas")
def r_tarefas(h):
    h._json(listar())


@rota("GET", "/api/tarefas/<tid>")
def r_tarefa(h, tid):
    try:
        linhas = int(h.query().get("linhas") or 400)
    except ValueError:
        linhas = 400
    h._json(detalhes(tid, linhas))


@rota("POST", "/api/tarefas/<tid>/parar")
def r_parar_tarefa(h, tid):
    h._json(parar(tid))


# ---------------- demonstração ----------------

def demo_bloco(texto: str, nomes: set) -> dict | None:
    """Para a API de mentira: pedido que fala em servidor ou segundo plano, no modo Code, vira um rodar_comando em
    segundo plano com um servidor de arquivos de verdade (só nesta máquina, porta escolhida pelo sistema)."""
    import sys
    baixo = (texto or "").lower()
    if "rodar_comando" not in nomes or not any(p in baixo for p in ("segundo plano", "background", "servidor de teste",
                                                                     "test server")):
        return None
    python = sys.executable.replace("'", "''")
    return {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "rodar_comando",
            "input": {"comando": f"& '{python}' -m http.server 0 --bind 127.0.0.1",
                      "descricao": t("Sobe um servidor de teste com os arquivos desta pasta"),
                      "em_segundo_plano": True}}
