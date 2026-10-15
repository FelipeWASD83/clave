"""Fluxos: uma tarefa dividida em etapas, cada uma num modelo (ex.: Opus planeja, Sonnet faz e testa).

O Claude propõe o fluxo com a ferramenta executar_fluxo. O app mostra as etapas, os modelos e a
estimativa de custo, e só roda depois do OK de quem usa: fluxo gasta bem mais que uma resposta, então
ele sempre pergunta (não existe "permitir sempre" para fluxo). Cada etapa é uma conversa escondida com
o modelo dela, que recebe o objetivo, a tarefa da etapa e o resultado das etapas anteriores. Etapas
marcadas como paralelas rodam ao mesmo tempo. As aprovações de arquivo e comando das etapas aparecem na
mesma conversa, e o teto do fluxo vale para a soma das etapas.
"""
from __future__ import annotations

import json
import math
import re
import threading
import time
from pathlib import Path

import agentes
import banco
import config
import modelos
import sistema
import i18n
from i18n import t

MAX_ETAPAS = 8
MAX_PARALELO = 4
LIMITE_RESULTADO = 20_000  # caracteres do relatório de cada etapa que seguem adiante
ESFORCOS = ["low", "medium", "high", "xhigh", "max"]
NOMES_PODE = {"ler": "ler arquivos", "editar": "criar e mudar arquivos", "comandos": "rodar comandos",
              "web": "pesquisar na web"}  # mostrar com t()

DEFINICAO = {
    "name": "executar_fluxo",
    "description": (
        "Propõe um fluxo: divide uma tarefa grande em etapas, cada uma feita por um agente ou modelo diferente "
        "(por exemplo: Opus 5.5 planeja, Sonnet 5.5 faz e testa, Opus revisa; ou três Haiku pesquisam em paralelo "
        "e um Sonnet junta). Quem usa vê as etapas, os modelos e a estimativa de custo e decide se roda: nada "
        "roda sem o OK. Use quando a tarefa for grande o bastante para valer o custo extra, ou quando a pessoa "
        "pedir um fluxo; para tarefa pequena, faça você mesmo. As etapas não veem esta conversa: ponha no "
        "objetivo e em cada tarefa tudo o que elas precisam saber. O resultado volta com o relatório de cada "
        "etapa; depois, resuma para a pessoa o que foi feito. Escreva o título, o objetivo, os nomes das etapas "
        "e as tarefas no idioma em que a pessoa escreve."),
    "eager_input_streaming": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "titulo": {"type": "string", "description": "Nome curto do fluxo, no idioma em que a pessoa escreve"},
            "objetivo": {"type": "string", "description": "O que o fluxo deve entregar, com o contexto necessário"},
            "etapas": {
                "type": "array", "minItems": 1, "maxItems": MAX_ETAPAS,
                "items": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string", "description": "Nome curto da etapa, no idioma em que a pessoa escreve"},
                        "agente": {"type": "string", "description": "Nome de um agente da lista (opcional)"},
                        "modelo": {"type": "string", "enum": ["opus", "sonnet", "haiku", "fable", "inherit"]},
                        "esforco": {"type": "string", "enum": ESFORCOS},
                        "tarefa": {"type": "string", "description": "O que esta etapa faz e o que deve entregar"},
                        "pode": {"type": "array", "items": {"type": "string", "enum": list(NOMES_PODE)}},
                        "paralelo": {"type": "boolean",
                                     "description": "true = roda ao mesmo tempo que a etapa anterior"},
                    },
                    "required": ["nome", "tarefa"],
                },
            },
            "teto_usd": {"type": "number", "description": "Gasto máximo sugerido para o fluxo inteiro"},
        },
        "required": ["titulo", "objetivo", "etapas"],
    },
}


class ErroFluxo(Exception):
    pass


def definicao(pasta: str | None) -> dict:
    """A ferramenta executar_fluxo com a lista de agentes que existem agora (da pasta, pessoais, plugins e do app).

    A descrição de cima muda com os agentes, então o catálogo das ferramentas (i18n.traduzir_ferramentas, que só troca
    texto idêntico) não a acharia inteira: os pedaços fixos são traduzidos aqui. As descrições das propriedades
    continuam com o catálogo."""
    d = json.loads(json.dumps(DEFINICAO))
    d["description"] = t(DEFINICAO["description"])
    linhas = []
    for a in agentes.listar(pasta)[:30]:
        pode = ", ".join(a["pode"]) or t("nada")
        modelo = agentes.NOME_MODELO.get(a["modelo"], a["modelo"])
        linhas.append(t("- {nome} (modelo: {modelo}; pode: {pode}): {descricao}", nome=a["nome"], modelo=modelo,
                        pode=pode, descricao=a["descricao"][:160]))
    if linhas:
        d["description"] += t("\n\nAgentes disponíveis (use o nome no campo agente):\n{lista}", lista="\n".join(linhas))
    if not pasta:
        d["description"] += t("\n\nAqui é o chat, sem pasta de trabalho: as etapas só podem pesquisar na web e escrever. Para mexer em arquivos, a pessoa precisa usar o modo Code.")
    return d


# ---------------- proposta ----------------

# (tokens novos de entrada, tokens de entrada vindos do cache, tokens de saída, buscas): mínimo e máximo
_PERFIS = {
    "pensar": ((6_000, 0, 2_000, 0), (30_000, 30_000, 12_000, 0)),
    "ler": ((10_000, 20_000, 2_000, 0), (60_000, 300_000, 10_000, 0)),
    "web": ((15_000, 20_000, 3_000, 3), (90_000, 250_000, 12_000, 12)),
    "fazer": ((30_000, 100_000, 6_000, 0), (160_000, 1_500_000, 40_000, 0)),
}
_FATOR_ESFORCO = {"low": 0.6, "medium": 1.0, "high": 1.5, "xhigh": 2.0, "max": 3.0}


def estimar_etapa(modelo: str, esforco: str, pode: list[str]) -> tuple[float, float]:
    perfil = "fazer" if ("editar" in pode or "comandos" in pode) else "web" if "web" in pode else \
        "ler" if "ler" in pode else "pensar"
    info = modelos.info(modelo)
    f = _FATOR_ESFORCO.get(esforco or "medium", 1.0)
    saida = []
    for novos, cache, out, buscas in _PERFIS[perfil]:
        usd = (novos * info["entrada"] * 1.25 + cache * info["cache_leitura"] + out * f * info["saida"]) / 1e6
        usd += buscas * modelos.BUSCA_WEB_USD
        saida.append(usd)
    return round(saida[0], 4), round(saida[1], 4)


def _teto_sugerido(maximo: float) -> float:
    return max(0.5, math.ceil(maximo * 1.2 * 2) / 2)


def normalizar(entrada: dict, *, fid: str, pasta: str | None, modelo_padrao: str, regras=None) -> dict:
    """Confere o que o Claude propôs e monta a proposta que vai para o cartão de aprovação."""
    if not isinstance(entrada, dict):
        raise ErroFluxo(t("a entrada não é um objeto"))
    etapas_in = entrada.get("etapas")
    if not isinstance(etapas_in, list) or not etapas_in:
        raise ErroFluxo(t("o fluxo precisa de pelo menos uma etapa"))
    if len(etapas_in) > MAX_ETAPAS:
        raise ErroFluxo(t("no máximo {n} etapas", n=MAX_ETAPAS))
    import permissoes
    etapas, grupo, no_grupo = [], -1, 0
    for i, e in enumerate(etapas_in):
        if not isinstance(e, dict) or not str(e.get("tarefa") or "").strip():
            raise ErroFluxo(t("a etapa {n} não tem tarefa", n=i + 1))
        ag = agentes.pegar(str(e.get("agente") or ""), pasta) if e.get("agente") else None
        aviso = ""
        if e.get("agente") and not ag:
            aviso = t("O agente \"{nome}\" não existe; a etapa roda sem instruções de agente.", nome=e["agente"])
        if ag and regras and permissoes.nega(regras, "Agent", ag["nome"]):
            raise ErroFluxo(t("o agente \"{nome}\" está bloqueado por uma regra de permissão", nome=ag["nome"]))
        modelo = agentes.resolver_modelo(str(e.get("modelo") or (ag or {}).get("modelo") or "inherit"), modelo_padrao)
        esforco = str(e.get("esforco") or (ag or {}).get("esforco") or "medium")
        if esforco not in ESFORCOS:
            esforco = "medium"
        pode = [p for p in (e.get("pode") or (ag or {}).get("pode") or ["ler"]) if p in NOMES_PODE]
        if not pasta:
            pode = [p for p in pode if p == "web"]  # no chat não tem pasta: só pesquisa
        paralelo = bool(e.get("paralelo")) and i > 0 and no_grupo < MAX_PARALELO
        if not paralelo:
            grupo += 1
            no_grupo = 0
        no_grupo += 1
        mn, mx = estimar_etapa(modelo, esforco, pode)
        etapas.append({
            "i": i, "nome": str(e.get("nome") or t("Etapa {n}", n=i + 1))[:80], "agente": (ag or {}).get("nome"),
            "modelo": modelo, "modelo_nome": modelos.info(modelo).get("nome") or modelo, "esforco": esforco,
            "tarefa": str(e["tarefa"]).strip(), "pode": pode, "grupo": grupo, "aviso": aviso,
            "estimativa": {"min": mn, "max": mx}, "status": "esperando", "custo_usd": 0.0,
        })
    mn = round(sum(x["estimativa"]["min"] for x in etapas), 4)
    mx = round(sum(x["estimativa"]["max"] for x in etapas), 4)
    teto = entrada.get("teto_usd")
    try:
        teto = float(teto) if teto is not None else None
    except (TypeError, ValueError):
        teto = None
    return {
        "id": fid, "titulo": str(entrada.get("titulo") or t("Fluxo"))[:100],
        "objetivo": str(entrada.get("objetivo") or "").strip(), "etapas": etapas,
        "estimativa": {"min": mn, "max": mx}, "teto_usd": teto if teto and teto > 0 else _teto_sugerido(mx),
        "pasta": pasta, "status": "proposto", "custo_usd": 0.0, "criado_em": time.time(),
    }


def aplicar_ajustes(proposta: dict, ajustes: dict | None) -> dict:
    """O que a pessoa mudou no cartão: modelo e esforço de cada etapa, etapas tiradas e o teto."""
    if not ajustes:
        return proposta
    por_i = {int(a.get("i")): a for a in (ajustes.get("etapas") or []) if isinstance(a, dict) and "i" in a}
    novas = []
    for e in proposta["etapas"]:
        a = por_i.get(e["i"], {})
        if a.get("tirar"):
            continue
        if a.get("modelo"):
            e["modelo"] = agentes.resolver_modelo(str(a["modelo"]), e["modelo"])
            e["modelo_nome"] = modelos.info(e["modelo"]).get("nome") or e["modelo"]
        if a.get("esforco") in ESFORCOS:
            e["esforco"] = a["esforco"]
        mn, mx = estimar_etapa(e["modelo"], e["esforco"], e["pode"])
        e["estimativa"] = {"min": mn, "max": mx}
        novas.append(e)
    if not novas:
        raise ErroFluxo(t("todas as etapas foram tiradas"))
    proposta["etapas"] = novas
    proposta["estimativa"] = {"min": round(sum(x["estimativa"]["min"] for x in novas), 4),
                              "max": round(sum(x["estimativa"]["max"] for x in novas), 4)}
    try:
        teto = float(ajustes.get("teto_usd")) if ajustes.get("teto_usd") is not None else None
    except (TypeError, ValueError):
        teto = None
    if teto and teto > 0:
        proposta["teto_usd"] = teto
    return proposta


# ---------------- execução ----------------

class Cofre:
    """O gasto somado das etapas, para o teto do fluxo valer para todas juntas (inclusive em paralelo)."""

    def __init__(self, limite: float, rotulo: str = "O fluxo"):  # rotulo: chave de t(), traduzida ao mostrar
        self.rotulo = rotulo
        self.limite = float(limite or 0)
        self.gasto = 0.0
        self._trava = threading.Lock()

    def somar(self, usd: float) -> None:
        with self._trava:
            self.gasto += float(usd or 0)

    def estourou(self) -> bool:
        return bool(self.limite) and self.gasto >= self.limite


def _texto_final(conversa_id: str) -> str:
    for m in reversed(banco.caminho(conversa_id)):
        if m["papel"] == "assistant" and isinstance(m["conteudo"], list):
            t = "\n".join(b.get("text", "") for b in m["conteudo"] if b.get("type") == "text").strip()
            if t:
                return t
    return ""


def _sistema_etapa(cfg: dict, pasta: str | None, etapa: dict, agente: dict | None, total: int) -> str:
    base = sistema.code(cfg, pasta) if pasta else sistema.chat(cfg)
    partes = [base, " ".join([
        t("Você está rodando a etapa {n} de {total} de um fluxo (\"{nome}\").", n=etapa["i"] + 1, total=total,
          nome=etapa["nome"]),
        t("Outras etapas, feitas por outros modelos, vêm antes ou depois de você."),
        t("Ninguém acompanha esta etapa ao vivo para responder perguntas: se faltar informação, faça a suposição mais razoável e diga qual foi."),
        t("Faça só a sua parte."),
        t("Termine com um relatório claro do que fez, do que encontrou e do que ficou pendente: ele é o que segue para as próximas etapas."),
        t("Escreva em português do Brasil (as instruções do agente podem vir em inglês)."),
    ])]
    pode = etapa["pode"]
    partes.append(t("Nesta etapa você pode: {lista}. O resto fica bloqueado.",
                    lista=", ".join(t(NOMES_PODE[p]) for p in pode) if pode else
                    t("só pensar e escrever (sem ferramentas de arquivo, comando ou web)")))
    if agente and agente.get("instrucoes"):
        partes.append(t("<agente nome=\"{nome}\">\n{instrucoes}\n</agente>", nome=agente["nome"],
                        instrucoes=agente["instrucoes"]))
    return "\n\n".join(partes)


def _mensagem_etapa(proposta: dict, etapa: dict, anteriores: list[dict]) -> str:
    partes = [t("<objetivo_do_fluxo titulo=\"{titulo}\">\n{objetivo}\n</objetivo_do_fluxo>", titulo=proposta["titulo"],
                objetivo=proposta["objetivo"]),
              t("<sua_etapa nome=\"{nome}\">\n{tarefa}\n</sua_etapa>", nome=etapa["nome"], tarefa=etapa["tarefa"])]
    if anteriores:
        blocos = []
        for a in anteriores:
            texto = (a.get("resultado") or t("(sem relatório)"))[:LIMITE_RESULTADO]
            blocos.append(t("<etapa nome=\"{nome}\" modelo=\"{modelo}\" status=\"{status}\">\n{conteudo}\n</etapa>",
                            nome=a["nome"], modelo=a["modelo_nome"], status=t(a["status"]), conteudo=texto))
        partes.append(t("<resultados_das_etapas_anteriores>\n{blocos}\n</resultados_das_etapas_anteriores>",
                        blocos="\n".join(blocos)))
    return "\n\n".join(partes)


class Rodada:
    """Roda um fluxo aprovado dentro da execução principal (a "mãe")."""

    def __init__(self, mae, proposta: dict, cfg: dict):
        self.mae = mae
        self.p = proposta
        self.cfg = cfg
        self.cofre = Cofre(proposta.get("teto_usd") or 0)
        self.trava = threading.Lock()

    def _salvar(self) -> None:
        with self.trava:
            self.p["custo_usd"] = round(sum(e.get("custo_usd", 0) for e in self.p["etapas"]), 6)
            banco.salvar_fluxo({**self.p, "conversa_id": self.mae.conversa_id, "execucao_id": self.mae.id})

    def _emitir(self, ev: dict) -> None:
        self.mae.emitir({**ev, "fluxo": self.p["id"]})

    def rodar(self) -> str:
        import execucao
        p = self.p
        p["status"] = "rodando"
        self._salvar()
        self._emitir({"tipo": "fluxo_inicio", "proposta": p})
        grupos: dict[int, list[dict]] = {}
        for e in p["etapas"]:
            grupos.setdefault(e["grupo"], []).append(e)
        feitas: list[dict] = []
        for g in sorted(grupos):
            if self.mae.parar.is_set() or self.cofre.estourou():
                break
            lote = grupos[g]
            anteriores = list(feitas)
            threads = [threading.Thread(target=self._etapa, args=(e, anteriores, execucao), daemon=True)
                       for e in lote]
            for th in threads:
                th.start()
            for th in threads:
                th.join()
            feitas += lote
            if any(e["status"] == "erro" for e in lote):
                break
        for e in p["etapas"]:
            if e["status"] in ("esperando", "rodando"):
                e["status"] = "parada" if self.mae.parar.is_set() else "pulada"
        if self.mae.parar.is_set():
            p["status"] = "parado"
        elif self.cofre.estourou():
            p["status"] = "teto"
        elif any(e["status"] == "erro" for e in p["etapas"]):
            p["status"] = "erro"
        else:
            p["status"] = "concluido"
        self._salvar()
        self._emitir({"tipo": "fluxo_fim", "status": p["status"], "custo_usd": p["custo_usd"]})
        return self.relatorio()

    def _etapa(self, e: dict, anteriores: list[dict], execucao) -> None:
        p = self.p
        mae = self.mae
        pasta = p.get("pasta")
        ag = agentes.pegar(e["agente"], pasta) if e.get("agente") else None
        conv = banco.criar_conversa(modo="etapa", pasta=pasta, titulo=f"{p['titulo']} · {e['nome']}",
                                    ajustes={"fluxo": p["id"], "etapa": e["i"], "modo_base": "code" if pasta else "chat",
                                             "conversa_mae": mae.conversa_id})
        banco.atualizar_conversa(conv["id"], sistema=_sistema_etapa(self.cfg, pasta, e, ag, len(p["etapas"])))
        banco.adicionar_mensagem(conv["id"], None, "user",
                                 [{"type": "text", "text": _mensagem_etapa(p, e, anteriores)}])
        permissao = mae.op.get("permissao") or self.cfg.get("permissao_code") or "perguntar"
        if permissao == "plano":
            permissao = "perguntar"  # aprovar o fluxo já é decidir executar; cada mudança ainda pede OK
        op = {"modelo": e["modelo"], "esforco": e["esforco"], "pensar": True, "mostrar_raciocinio": True,
              "busca_web": "web" in e["pode"], "github": False, "rapido": False,
              "permissao": permissao,
              "pode": e["pode"], "etapa_de_fluxo": True, "rotina": mae.op.get("rotina")}
        filho = execucao.Execucao(conv["id"], op)
        filho.mae = mae
        filho.cofre = self.cofre
        filho.liberados = mae.liberados          # "nesta tarefa" vale para o fluxo inteiro
        filho.regras_tarefa = mae.regras_tarefa
        filho.repassar = lambda ev, i=e["i"], eid=filho.id: self._emitir(
            {"tipo": "etapa_evento", "etapa": i, "execucao": eid, "ev": ev})
        execucao.registrar(filho)
        mae.filhos.append(filho)
        e.update({"status": "rodando", "conversa_id": conv["id"], "execucao_id": filho.id, "inicio": time.time()})
        self._salvar()
        self._emitir({"tipo": "etapa_inicio", "etapa": e["i"], "execucao": filho.id, "conversa": conv["id"],
                      "modelo": e["modelo"], "modelo_nome": e["modelo_nome"]})
        try:
            filho.rodar()
        finally:
            e["custo_usd"] = round(filho.custo_total, 6)
            e["fim"] = time.time()
            if filho.status == "concluida":
                e["status"] = "concluida"
            elif filho.status == "parada":
                e["status"] = "parada"
            else:
                e["status"] = "erro"
                e["erro"] = filho.ultimo_erro or t("a etapa não terminou")
            if filho.mudou_arquivos:
                mae.mudou_arquivos = True
            e["resultado"] = _texto_final(conv["id"])
            self._salvar()
            self._emitir({"tipo": "etapa_fim", "etapa": e["i"], "status": e["status"], "custo_usd": e["custo_usd"],
                          "resumo": (e.get("resultado") or e.get("erro") or "")[:600]})

    def relatorio(self) -> str:
        p = self.p
        linhas = [t("Fluxo \"{titulo}\": {status}. Gasto: US$ {gasto} (teto US$ {teto}).", titulo=p["titulo"],
                    status=t(p["status"]), gasto=f"{p['custo_usd']:.4f}", teto=f"{p['teto_usd']:.2f}")]
        if p["status"] == "teto":
            linhas.append(t("O fluxo parou porque chegou ao teto de gasto aprovado."))
        if p["status"] == "parado":
            linhas.append(t("Quem usa parou o fluxo antes do fim."))
        for e in p["etapas"]:
            cab = "\n" + t("## Etapa {n}: {nome} ({modelo}, {status}, US$ {custo})", n=e["i"] + 1, nome=e["nome"],
                           modelo=e["modelo_nome"], status=t(e["status"]), custo=f"{e['custo_usd']:.4f}")
            corpo = (e.get("resultado") or e.get("erro") or t("(sem relatório)"))[:LIMITE_RESULTADO]
            linhas.append(cab + "\n" + corpo)
        linhas.append("\n" + t("Resuma para a pessoa, em linguagem simples, o que o fluxo fez, o que mudou e o que ficou pendente. Não repita o relatório inteiro."))
        return "\n".join(linhas)


# ---------------- modelos de fluxo ----------------

def _dirs_modelos() -> list[tuple[str, Path]]:
    import plugins
    dirs = [("meus", config.DADOS / "fluxos")]
    for nome_plugin, d in plugins.partes("fluxos"):
        dirs.append((f"plugin:{nome_plugin}", d))
    dirs.append(("clave", config.RAIZ / "fluxos"))
    return dirs


def _no_idioma(dados: dict) -> dict:
    """Os fluxos do app vêm em inglês, com o português em "i18n" > "pt-BR" (nome, descrição, pedido e etapas)."""
    pt = (dados.get("i18n") or {}).get("pt-BR") if i18n.idioma() == "pt-BR" else None
    dados = {k: v for k, v in dados.items() if k != "i18n"}
    if not pt:
        return dados
    for campo in ("nome", "descricao", "pede"):
        if pt.get(campo):
            dados[campo] = pt[campo]
    etapas_pt = pt.get("etapas") or []
    dados["etapas"] = [{**e, **{k: v for k, v in (etapas_pt[i] if i < len(etapas_pt) else {}).items() if v}}
                       for i, e in enumerate(dados.get("etapas") or [])]
    return dados


def listar_modelos() -> list[dict]:
    vistos: dict[str, dict] = {}
    for origem, d in _dirs_modelos():
        if not d.is_dir():
            continue
        for arq in sorted(d.glob("*.json")):
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            ident = arq.stem
            if ident in vistos or not isinstance(dados.get("etapas"), list):
                continue
            vistos[ident] = {**_no_idioma(dados), "id": ident, "origem": origem, "editavel": origem == "meus"}
    return sorted(vistos.values(), key=lambda m: (m["origem"] != "meus", m.get("nome", m["id"])))


def modelo(ident: str) -> dict | None:
    import comandos  # o id em inglês de um fluxo pronto (/workflow deep-research) também vale
    lista = listar_modelos()
    return (next((m for m in lista if m["id"] == ident), None)
            or next((m for m in lista if m["id"] == comandos.canonico(ident)), None))


def salvar_modelo(dados: dict) -> dict:
    nome = str(dados.get("nome") or "").strip()
    if not nome:
        raise ErroFluxo(t("Dê um nome ao fluxo."))
    etapas = dados.get("etapas")
    if not isinstance(etapas, list) or not etapas or len(etapas) > MAX_ETAPAS:
        raise ErroFluxo(t("O fluxo precisa de 1 a {n} etapas.", n=MAX_ETAPAS))
    limpas = []
    for e in etapas:
        if not isinstance(e, dict) or not str(e.get("nome") or "").strip():
            raise ErroFluxo(t("Toda etapa precisa de nome."))
        limpas.append({k: e[k] for k in ("nome", "agente", "modelo", "esforco", "tarefa", "pode", "paralelo")
                       if k in e and e[k] not in (None, "")})
    ident = str(dados.get("id") or "") or re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-") or "fluxo"
    if not re.fullmatch(r"[a-z0-9-]{1,60}", ident):
        raise ErroFluxo(t("Identificador inválido."))
    d = config.DADOS / "fluxos"
    d.mkdir(parents=True, exist_ok=True)
    corpo = {"nome": nome, "descricao": str(dados.get("descricao") or ""), "pede": str(dados.get("pede") or ""),
             "etapas": limpas}
    (d / f"{ident}.json").write_text(json.dumps(corpo, ensure_ascii=False, indent=2), encoding="utf-8")
    return {**corpo, "id": ident, "origem": "meus", "editavel": True}


def apagar_modelo(ident: str) -> None:
    if not re.fullmatch(r"[a-z0-9-]{1,60}", ident or ""):
        raise ErroFluxo(t("Identificador inválido."))
    arq = config.DADOS / "fluxos" / f"{ident}.json"
    if not arq.is_file():
        raise ErroFluxo(t("Só dá para apagar fluxo seu."))
    arq.unlink()


def texto_para_comando(m: dict, pedido: str) -> str:
    """O que vai para o Claude quando a pessoa escolhe um modelo de fluxo (/fluxo nome tarefa)."""
    etapas = json.dumps(m["etapas"], ensure_ascii=False, indent=1)
    return (t("Quero rodar o fluxo \"{nome}\" para este pedido:", nome=m.get("nome", m["id"])) + "\n\n"
            + (pedido or t("(sem pedido escrito)")) + "\n\n"
            + t("Etapas do modelo (adapte as tarefas ao pedido, mantendo os agentes e os modelos):")
            + f"\n```json\n{etapas}\n```\n\n"
            + t("Se o pedido estiver claro, proponha o fluxo com executar_fluxo; se faltar algo essencial, pergunte antes."))
