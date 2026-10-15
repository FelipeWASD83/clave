"""Widgets: os cartões visuais que o Claude desenha na conversa (produtos com preço, mapa, recomendações, desenho,
gráfico, comparação, linha do tempo e checklist).

Uma ferramenta só, mostrar_widget {tipo, titulo, dados}, oferecida no chat e no Code (nunca numa etapa de fluxo nem
numa rotina, onde ninguém vê) enquanto cfg["widgets_ligados"] estiver ligado. normalizar() confere e arruma os dados
de cada tipo: erro claro para o Claude corrigir, limite de quantidade e de tamanho, número como número, cor só da
paleta e link só https. O widget pronto fica em <dados>/widgets/<id da chamada>.json, que a tela lê de novo ao
reabrir a conversa (e onde o checklist guarda o que foi marcado).

Imagem de fora (foto de produto, capa) só passa pelo /api/widgets/imagem: https, endereço público (cada IP
resolvido é conferido, de novo a cada redirecionamento, e a conexão vai para o IP conferido), até 5 MB, só PNG, JPEG,
WebP e GIF (nunca SVG) e guardada 7 dias em disco. Os mapas usam o mapas.py.
"""
from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import math
import os
import re
import socket
import ssl
import threading
import time
import unicodedata
import urllib.parse
from datetime import date, datetime

import config
import mapas
from i18n import idioma, t
from rotas import Erro, rota

NOMES = {"mostrar_widget"}
TIPOS = ("produtos", "mapa", "recomendacoes", "desenho", "grafico", "comparacao", "linha_do_tempo", "checklist")
PALETA = ("acao", "azul", "verde", "vermelho", "laranja", "amarelo", "roxo", "rosa", "marrom", "cinza", "preto")
TIPOS_RECOMENDACAO = ("serie", "filme", "jogo", "anime", "livro", "musica", "podcast", "outro")
TIPOS_GRAFICO = ("barras", "linhas", "pizza", "area")
FORMAS = ("retangulo", "circulo", "linha", "seta", "texto", "poligono", "cota")
UNIDADES = ("m", "cm", "px")
MAX_ENDERECOS = 15          # endereços sem coordenada por mapa (cada um leva 1 s, pela regra do Nominatim)
MAX_JSON = 300_000          # tamanho máximo de um widget salvo

_ALIAS_TIPO = {"products": "produtos", "produto": "produtos", "precos": "produtos", "prices": "produtos",
               "shopping": "produtos", "map": "mapa", "mapas": "mapa", "recommendations": "recomendacoes",
               "recomendacao": "recomendacoes", "picks": "recomendacoes", "drawing": "desenho", "planta": "desenho",
               "floor_plan": "desenho", "diagram": "desenho", "chart": "grafico", "graph": "grafico",
               "graficos": "grafico", "comparison": "comparacao", "compare": "comparacao", "timeline": "linha_do_tempo",
               "linha_tempo": "linha_do_tempo", "cronologia": "linha_do_tempo", "lista": "checklist",
               "todo": "checklist", "to_do": "checklist"}
_ALIAS_COR = {"teal": "acao", "petroleo": "acao", "padrao": "acao", "default": "acao", "blue": "azul",
              "green": "verde", "red": "vermelho", "orange": "laranja", "yellow": "amarelo", "purple": "roxo",
              "violet": "roxo", "violeta": "roxo", "lilas": "roxo", "pink": "rosa", "brown": "marrom",
              "gray": "cinza", "grey": "cinza", "cinzento": "cinza", "black": "preto", "ink": "preto"}
_ALIAS_RECOMENDACAO = {"series": "serie", "tv": "serie", "show": "serie", "tv_show": "serie", "novela": "serie",
                       "movie": "filme", "film": "filme", "documentario": "filme", "documentary": "filme",
                       "game": "jogo", "video_game": "jogo", "videogame": "jogo", "jogos": "jogo", "book": "livro",
                       "manga": "livro", "hq": "livro", "comic": "livro", "music": "musica", "album": "musica",
                       "song": "musica", "artist": "musica", "artista": "musica", "banda": "musica", "band": "musica",
                       "other": "outro"}
_ALIAS_GRAFICO = {"bar": "barras", "bars": "barras", "barra": "barras", "colunas": "barras", "column": "barras",
                  "columns": "barras", "line": "linhas", "lines": "linhas", "linha": "linhas", "pie": "pizza",
                  "donut": "pizza", "rosca": "pizza", "areas": "area"}
_ALIAS_FORMA = {"rect": "retangulo", "rectangle": "retangulo", "retangulos": "retangulo", "quadrado": "retangulo",
                "square": "retangulo", "circle": "circulo", "line": "linha", "arrow": "seta", "text": "texto",
                "label": "texto", "polygon": "poligono", "dimension": "cota", "medida": "cota", "measure": "cota"}
_ALIAS_UNIDADE = {"metro": "m", "metros": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
                  "centimetro": "cm", "centimetros": "cm", "centimeter": "cm", "centimeters": "cm", "pixel": "px",
                  "pixels": "px"}
_ALIAS_TAMANHO = {"small": "pequeno", "p": "pequeno", "medium": "medio", "m": "medio", "large": "grande",
                  "g": "grande", "big": "grande"}
_SIMBOLOS_MOEDA = {"R$": "BRL", "US$": "USD", "$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
# códigos que valem como moeda escrita junto do preço ("1.299 EUR", "USD 1,299"); três letras soltas como "por"
# não podem virar moeda
_CODIGOS_MOEDA = {"BRL", "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "NZD", "CHF", "CNY", "HKD", "ARS", "MXN", "CLP",
                  "COP", "PEN", "UYU", "PYG", "BOB", "INR", "KRW", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "TRY",
                  "ZAR", "SGD", "AOA", "MZN", "CVE", "ILS", "AED", "SAR", "RUB", "UAH", "TWD", "THB", "PHP", "IDR",
                  "VND", "MYR", "KWD", "BHD", "OMR", "JOD", "TND", "IQD", "LYD"}
# moedas com três casas depois da vírgula: nelas "1.299" pode ser um preço com centavos de verdade
_MOEDAS_3_CASAS = {"BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"}
# moedas sem centavos (o texto exportado não mostra casas)
_MOEDAS_SEM_CASAS = {"JPY", "KRW", "CLP", "PYG", "VND", "IDR", "HUF", "ISK", "UGX"}
_SIM = {"true", "sim", "yes", "y", "s", "1", "x", "v", "ok", "feito", "feita", "done", "verdadeiro", "on", "checked",
        "marcado", "marcada", "concluido", "concluida", "completo", "completed"}
_NAO = {"false", "nao", "no", "n", "0", "off", "falso", "f", "pendente", "pending", "todo", "to_do", "unchecked",
        "desmarcado", "desmarcada", "null", "none", "nenhum", "-"}


class ErroWidget(ValueError):
    pass


# ======================= a ferramenta =======================

DESCRICAO = ("Mostra um cartão visual (widget) na conversa. Use quando ele ajuda mais que texto: preços para "
             "comparar, lugares num mapa, a planta de um cômodo ou um diagrama simples, um gráfico, indicações de "
             "séries, filmes, jogos ou livros, uma comparação lado a lado, uma linha do tempo ou um checklist. Preços, "
             "notas e dados precisam vir do que você achou de verdade (pesquise na web antes) e dizer a data em que "
             "viu; nunca invente link de produto: sem o link certo, deixe sem link. Depois do widget, não repita no "
             "texto o que ele já mostra; comente só o que ajuda a decidir.")

DESCRICAO_DADOS = (
    "Os dados, no formato do tipo. "
    "produtos: {itens: [{nome, preco (número), moeda (padrão BRL), loja, link?, nota? (0 a 5), observacao?, "
    "imagem? (https)}], visto_em: \"AAAA-MM-DD\"}. "
    "mapa: {pontos: [{nome, descricao?, lat, lon} ou {nome, descricao?, endereco}], rota?: true para ligar os "
    "pontos na ordem}. "
    "recomendacoes: {itens: [{titulo, tipo (serie, filme, jogo, anime, livro, musica, podcast ou outro), ano?, "
    "generos: [], onde? (onde ver, jogar ou ouvir), duracao?, nota?: {valor, fonte}, por_que, imagem?}]}. "
    "desenho: {largura, altura, unidade (m, cm ou px), formas: [{tipo, coordenadas, rotulo?, cor?, preenchido?}], "
    "legenda?: [{cor, rotulo}]}, com a origem no canto de cima à esquerda, y para baixo e tudo na unidade escolhida; "
    "coordenadas de cada tipo de forma: retangulo x, y, largura, altura, rotacao?; circulo x, y, raio; linha e seta "
    "x1, y1, x2, y2; texto x, y, texto; poligono pontos: [[x, y], ...]; cota x1, y1, x2, y2, deslocamento? (quanto "
    "afastar a linha da cota para fora do desenho; a medida aparece sozinha). "
    "grafico: {tipo_grafico (barras, linhas, pizza ou area), rotulos: [], series: [{nome, valores: []}], "
    "unidade?}. "
    "comparacao: {colunas: [], linhas: [{criterio, valores: [], melhor?: índice da melhor coluna}]}. "
    "linha_do_tempo: {eventos: [{data, titulo, descricao?}]}. "
    "checklist: {itens: [{texto, feito?}]}. "
    "Cores: acao, azul, verde, vermelho, laranja, amarelo, roxo, rosa, marrom, cinza e preto.")

DEFINICAO = {
    "name": "mostrar_widget",
    "description": DESCRICAO,
    "input_schema": {"type": "object", "properties": {
        "tipo": {"type": "string", "enum": list(TIPOS), "description": "Qual widget mostrar"},
        "titulo": {"type": "string",
                   "description": "Título curto do cartão (até 80 caracteres), no idioma em que a pessoa escreve"},
        "dados": {"type": "object", "description": DESCRICAO_DADOS}},
        "required": ["tipo", "titulo", "dados"]},
}


def definicoes_para_teste() -> list[dict]:
    return [DEFINICAO]


def _por_que_nao(modo, op, cfg, etapa=False) -> str | None:
    """None quando o widget vale nesta resposta; senão, o motivo (o mesmo critério de oferecer e de executar)."""
    op = op or {}
    if modo not in ("chat", "code") or etapa or op.get("rotina") or op.get("etapa_de_fluxo"):
        return t("Widgets não aparecem aqui (rotina, etapa de fluxo ou ajudante de lição): ninguém veria o cartão. Responda só com texto.")
    if not (cfg or {}).get("widgets_ligados", True):
        return t("Os widgets estão desligados nas Configurações: responda só com texto.")
    return None


def oferecer(ex, *, modo, op, cfg, etapa, pasta) -> list[dict]:
    if _por_que_nao(modo, op, cfg, etapa):
        return []
    return [dict(DEFINICAO)]


def executar(ex, tid, nome, entrada, cfg, modo) -> dict:
    ex.emitir({"tipo": "ferramenta_rodando", "id": tid, "nome": nome})
    # a ferramenta só roda onde foi oferecida: um nome chamado mesmo assim (de uma resposta antiga, numa rotina ou com
    # os widgets desligados) não busca endereço nem desenha nada
    motivo = _por_que_nao(modo, getattr(ex, "op", None), cfg)
    if motivo:
        ex.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": motivo})
        return ex.resultado(tid, motivo, True)
    try:
        widget, avisos = normalizar(entrada)
        salvar(tid, widget)
    except ErroWidget as e:
        ex.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": str(e)})
        return ex.resultado(tid, t("Widget inválido: {erro} Corrija e mande de novo.", erro=e), True)
    except OSError as e:
        ex.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": True, "resumo": str(e)})
        return ex.resultado(tid, t("Não deu para guardar o widget: {erro}", erro=e), True)
    ex.emitir({"tipo": "widget", "id": tid, "widget": widget})
    texto = resumo_para_o_claude(widget, avisos)
    ex.emitir({"tipo": "ferramenta_fim", "id": tid, "nome": nome, "erro": False, "resumo": texto[:300]})
    return ex.resultado(tid, texto)


def _quantos(widget: dict) -> int:
    d = widget["dados"]
    return len(d.get("itens") or d.get("pontos") or d.get("formas") or d.get("linhas") or d.get("eventos")
               or d.get("rotulos") or [])


def resumo_para_o_claude(widget: dict, avisos: list[str]) -> str:
    partes = [t("O widget \"{titulo}\" ({tipo}, {quantos} itens) apareceu para quem usa na conversa.",
                titulo=widget["titulo"], tipo=widget["tipo"], quantos=_quantos(widget))]
    if avisos:
        partes.append(t("Ajustes feitos: {lista}", lista=" ".join(avisos)))
    if widget["tipo"] == "mapa":
        # onde cada endereço caiu: sem isso, "Rua das Flores, 10" numa cidade errada passaria sem ninguém notar
        # (só os que foram procurados: ponto com lat e lon já veio no lugar certo)
        achados = [p for p in widget["dados"].get("pontos") or [] if p.get("endereco") and p.get("achado")]
        if achados:
            partes.append(t("Onde cada endereço caiu no mapa (confira a cidade e o bairro; se algum estiver errado, mande o widget de novo com lat e lon ou com o endereço completo):"))
            for p in achados:
                partes.append(f"- {p['endereco']} -> {p['achado']} ({_fmt(p['lat'])}, {_fmt(p['lon'])})")
    partes.append(t("Não repita no texto o que o widget já mostra."))
    return "\n".join(partes)


# ======================= guardar e ler =======================

_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
_trava_arquivos = threading.Lock()


def _pasta():
    return config.DADOS / "widgets"


def _arquivo(tid: str):
    if not _ID.match(str(tid or "")):
        raise Erro(400, t("Identificador de widget inválido."))
    return _pasta() / f"{tid}.json"


def salvar(tid: str, widget: dict) -> None:
    arq = _arquivo(tid)
    with _trava_arquivos:
        arq.parent.mkdir(parents=True, exist_ok=True)
        tmp = arq.with_suffix(".tmp")
        tmp.write_text(json.dumps(widget, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, arq)


def ler(tid: str) -> dict | None:
    try:
        w = json.loads(_arquivo(tid).read_text(encoding="utf-8"))
        return w if isinstance(w, dict) else None
    except (OSError, ValueError):
        return None


def marcar(tid: str, marcados) -> dict:
    """O checklist com os itens marcados (a lista de índices é o estado inteiro: o que não está nela fica desmarcado)."""
    if not isinstance(marcados, list) or any(isinstance(i, bool) or not isinstance(i, int) for i in marcados):
        raise Erro(400, t("Mande em marcados a lista dos números dos itens marcados."))
    arq = _arquivo(tid)
    with _trava_arquivos:
        try:
            w = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise Erro(404, t("Este widget não existe mais."))
        if w.get("tipo") != "checklist":
            raise Erro(400, t("Só dá para marcar itens de um checklist."))
        itens = w["dados"]["itens"]
        if any(not 0 <= i < len(itens) for i in marcados):
            raise Erro(400, t("Item inexistente no checklist."))
        escolhidos = set(marcados)
        for i, item in enumerate(itens):
            item["feito"] = i in escolhidos
        tmp = arq.with_suffix(".tmp")
        tmp.write_text(json.dumps(w, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, arq)
    return w


# ======================= conferir os dados =======================

def _chave(v) -> str:
    s = unicodedata.normalize("NFKD", str(v or "")).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[\s-]+", "_", s.strip().lower())


def _texto(v, maximo: int) -> str:
    if v is None or isinstance(v, (dict, list)):
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = " ".join(str(v).split())
    return s if len(s) <= maximo else s[:maximo - 1].rstrip() + "…"


def _ler_numero(s: str) -> float | None:
    s = re.sub(r"[^\d,.\-+eE]", "", s.strip())
    s = re.sub(r"[eE](?![\d+-])", "", s)
    if not re.search(r"\d", s):
        return None
    tem_ponto, tem_virgula = "." in s, "," in s
    if tem_ponto and tem_virgula:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif tem_virgula:
        s = s.replace(",", "") if re.fullmatch(r"[+-]?\d{1,3}(,\d{3}){2,}", s) else s.replace(",", ".")
    elif tem_ponto and re.fullmatch(r"[+-]?\d{1,3}(\.\d{3}){2,}", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def _ler_preco(s: str, moeda: str) -> float | None:
    """Um preço escrito como texto. Com os dois separadores, o último é o dos centavos ("R$ 1.299,90", "US$ 1,299.90").
    Com um só, ele separa milhar quando vem seguido de exatamente 3 dígitos depois de 1 a 3 dígitos ("R$ 1.299",
    "US$ 1,299", "R$ 12.499"): preço com 3 casas de centavos não existe, a não ser nas moedas de _MOEDAS_3_CASAS. Isso
    vale nas duas convenções (BRL e EUR com "." de milhar, USD e GBP com ","), porque em ambas um "1.299" de preço é mil
    duzentos e noventa e nove. Repetido ("1.299.000"), é sempre milhar."""
    s = re.sub(r"[^\d,.\-+]", "", s.strip())  # tira símbolo, espaço (inclusive o fino) e o ' do franco suíço
    if not re.search(r"\d", s):
        return None
    tem_ponto, tem_virgula = "." in s, "," in s
    if tem_ponto and tem_virgula:
        decimal = "," if s.rfind(",") > s.rfind(".") else "."
        milhar = "." if decimal == "," else ","
        s = s.replace(milhar, "").replace(decimal, ".")
    elif tem_ponto or tem_virgula:
        sep = "." if tem_ponto else ","
        if s.count(sep) > 1:
            if not re.fullmatch(rf"[+-]?\d{{1,3}}(?:\{sep}\d{{3}})+", s):
                return None
            s = s.replace(sep, "")
        else:
            inteiro, frac = s.split(sep)
            if (len(frac) == 3 and re.fullmatch(r"[+-]?[1-9]\d{0,2}", inteiro)
                    and moeda.upper() not in _MOEDAS_3_CASAS):
                s = inteiro + frac
            else:
                s = f"{inteiro}.{frac}"
    try:
        return float(s)
    except ValueError:
        return None


def _moeda_no_texto(v) -> str | None:
    """A moeda escrita junto do preço ("US$ 1,299", "1.299,90 €", "EUR 12"), para quando o item não diz a moeda."""
    if not isinstance(v, str):
        return None
    s = v.strip()
    m = re.match(r"^(R\$|US\$|€|£|¥|\$)", s) or re.search(r"(R\$|US\$|€|£|¥|\$)$", s)
    if m:
        return _SIMBOLOS_MOEDA[m.group(1)]
    m = re.match(r"^([A-Za-z]{3})(?=[\s\d$])", s) or re.search(r"[\d\s]([A-Za-z]{3})$", s)
    if m and m.group(1).upper() in _CODIGOS_MOEDA:
        return m.group(1).upper()
    return None


def _numero(v, campo: str, *, minimo=None, maximo=None, obrigatorio=True, moeda: str | None = None):
    """Um número (de texto também: "1.299,90", "-23,58"). Com moeda, o texto é lido como preço (_ler_preco)."""
    if v is None or (isinstance(v, str) and not v.strip()):
        if obrigatorio:
            raise ErroWidget(t("Falta o número em {campo}.", campo=campo))
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float, str)):
        raise ErroWidget(t("{campo} precisa ser um número.", campo=campo))
    if not isinstance(v, str):
        n = float(v)
    else:
        n = _ler_preco(v, moeda) if moeda else _ler_numero(v)
    if n is None or not math.isfinite(n):
        raise ErroWidget(t("{campo} precisa ser um número (veio \"{valor}\").", campo=campo, valor=str(v)[:40]))
    if (minimo is not None and n < minimo) or (maximo is not None and n > maximo):
        raise ErroWidget(t("{campo} está fora do intervalo aceito ({minimo} a {maximo}).", campo=campo,
                           minimo=_fmt(minimo), maximo=_fmt(maximo)))
    n = round(n, 6)
    return int(n) if n.is_integer() and abs(n) < 1e15 else n


def _fmt(n) -> str:
    if n is None:
        return "?"
    n = float(n)
    return str(int(n)) if n.is_integer() else f"{n:g}"


def _lista(v, campo: str, minimo: int, maximo: int, avisos: list[str]) -> list:
    if isinstance(v, (dict, str)) and v:
        v = [v]
    if not isinstance(v, list) or len(v) < minimo:
        raise ErroWidget(t("Mande em {campo} uma lista com pelo menos {minimo}.", campo=campo, minimo=minimo))
    if len(v) > maximo:
        avisos.append(t("{campo} tinha {quantos}; ficaram os primeiros {maximo}.", campo=campo, quantos=len(v),
                        maximo=maximo))
        v = v[:maximo]
    return v


def _url_https(v, campo: str, avisos: list[str]) -> str | None:
    if v in (None, ""):
        return None
    s = str(v).strip()
    try:
        p = urllib.parse.urlsplit(s)
        ok = (p.scheme.lower() == "https" and bool(p.hostname) and len(s) <= 2048
              and not re.search(r"[\s<>\"'`\\]", s) and not p.username)
    except ValueError:
        ok = False
    if not ok:
        avisos.append(t("{campo} ficou de fora: só vale link https completo.", campo=campo))
        return None
    return s


def _cor(v, campo: str, avisos: list[str]) -> str | None:
    if v in (None, ""):
        return None
    c = _chave(v)
    c = _ALIAS_COR.get(c, c)
    if c in PALETA:
        return c
    avisos.append(t("A cor \"{cor}\" ({campo}) não está na paleta; usei a padrão.", cor=str(v)[:30], campo=campo))
    return None


def _escolha(v, opcoes: tuple, aliases: dict, padrao=None):
    c = _chave(v)
    c = aliases.get(c, c)
    return c if c in opcoes else padrao


def _moeda(v, padrao: str, avisos: list[str], campo: str) -> str:
    if v in (None, ""):
        return padrao
    s = str(v).strip()
    if s in _SIMBOLOS_MOEDA:
        return _SIMBOLOS_MOEDA[s]
    if re.fullmatch(r"[A-Za-z]{3}", s):
        return s.upper()
    avisos.append(t("Moeda \"{moeda}\" ({campo}) não é um código de 3 letras como BRL ou USD; usei {padrao}.",
                    moeda=s[:12], campo=campo, padrao=padrao))
    return padrao


def _booleano(v, campo: str, avisos: list[str]) -> bool:
    """Sim ou não de verdade: "false", "não", "0" e "no" são não (bool("false") seria sim)."""
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    if isinstance(v, (int, float)):
        return math.isfinite(v) and v != 0
    if isinstance(v, str):
        c = _chave(v)
        if c in _SIM:
            return True
        if c in _NAO or not c:
            return False
    avisos.append(t("{campo} precisa ser true ou false (veio \"{valor}\"); ficou como false.", campo=campo,
                    valor=str(v)[:30]))
    return False


def _nota(v, campo: str, avisos: list[str]) -> dict | None:
    """{valor, fonte} e, quando a nota vem com escala ("8/10", "85%", {valor, escala}), a escala também: 8 de 10 não
    pode virar 8 estrelas."""
    if v in (None, "", {}):
        return None
    fonte, escala = "", None
    if isinstance(v, dict):
        fonte = _texto(v.get("fonte") or v.get("source"), 40)
        for k in ("escala", "maximo", "max", "de", "scale", "out_of"):
            if v.get(k) not in (None, ""):
                escala = v.get(k)
                break
        v = v.get("valor", v.get("value"))
    if isinstance(v, str):
        s = v.strip()
        m = re.fullmatch(r"(.*?\d)\s*(?:/|\bde\b|\bem\b|\bout of\b|\bof\b)\s*(\d+(?:[.,]\d+)?)", s, re.I)
        if m:
            v, escala = m.group(1), m.group(2)
        elif s.endswith("%"):
            v, escala = s[:-1], 100
    try:
        valor = _numero(v, campo, minimo=0, maximo=1000)
    except ErroWidget:
        avisos.append(t("{campo} ficou de fora: a nota precisa ser um número.", campo=campo))
        return None
    if escala is not None:
        try:
            escala = _numero(escala, campo, minimo=1, maximo=1000)
        except ErroWidget:
            escala = None
        if escala is not None and valor > escala:
            avisos.append(t("{campo} ficou de fora: a nota {valor} passa da escala {escala}.", campo=campo,
                            valor=_fmt(valor), escala=_fmt(escala)))
            return None
    elif valor > 100:
        avisos.append(t("{campo} ficou de fora: a nota precisa ser um número.", campo=campo))
        return None
    nota = {"valor": valor, "fonte": fonte}
    if escala is not None:
        nota["escala"] = escala
    return nota


def _data_vista(v) -> str:
    if v in (None, ""):
        raise ErroWidget(t("Diga em visto_em a data em que viu os preços (AAAA-MM-DD)."))
    s = _texto(v, 40)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        except ValueError:
            pass
    return s


def _produtos(d: dict, avisos: list[str]) -> dict:
    itens = _lista(d.get("itens"), "itens", 1, 24, avisos)
    moeda_padrao = _moeda(d.get("moeda"), "BRL", avisos, "moeda")
    saida = []
    for i, it in enumerate(itens, 1):
        if not isinstance(it, dict):
            raise ErroWidget(t("O item {n} precisa ser um objeto com nome e preco.", n=i))
        nome = _texto(it.get("nome"), 140)
        if not nome:
            raise ErroWidget(t("O item {n} está sem nome.", n=i))
        # "US$ 1,299" sem o campo moeda: a moeda escrita no preço vale mais que a padrão do widget
        moeda = _moeda(it.get("moeda"), _moeda_no_texto(it.get("preco")) or moeda_padrao, avisos, f"itens[{i}].moeda")
        p = {"nome": nome,
             "preco": _numero(it.get("preco"), f"itens[{i}].preco", minimo=0, maximo=1e12, moeda=moeda),
             "moeda": moeda,
             "loja": _texto(it.get("loja"), 80)}
        link = _url_https(it.get("link"), f"itens[{i}].link", avisos)
        if link:
            p["link"] = link
        nota = _nota(it.get("nota"), f"itens[{i}].nota", avisos)
        if nota:
            p["nota"] = nota
        obs = _texto(it.get("observacao"), 280)
        if obs:
            p["observacao"] = obs
        img = _url_https(it.get("imagem"), f"itens[{i}].imagem", avisos)
        if img:
            p["imagem"] = img
        saida.append(p)
    return {"itens": saida, "visto_em": _data_vista(d.get("visto_em"))}


MOTIVOS_FORA = ("nao_achado", "limite", "sem_conexao")


def _mapa(d: dict, avisos: list[str], geocodificar) -> dict:
    pontos = _lista(d.get("pontos"), "pontos", 1, 30, avisos)
    saida, fora = [], []   # fora: [{nome, motivo}] os pontos que não entraram, para o cartão mostrar também
    buscas, sem_conexao = 0, ""
    for i, p in enumerate(pontos, 1):
        if not isinstance(p, dict):
            raise ErroWidget(t("O ponto {n} precisa ser um objeto com nome e lat/lon ou endereco.", n=i))
        endereco = _texto(p.get("endereco") or p.get("address"), 200)
        nome = _texto(p.get("nome"), 100) or endereco
        if not nome:
            raise ErroWidget(t("O ponto {n} está sem nome.", n=i))
        lat = p.get("lat", p.get("latitude"))
        lon = p.get("lon", p.get("lng", p.get("longitude")))
        achado_nome = ""
        if lat not in (None, "") and lon not in (None, ""):
            lat = _numero(lat, f"pontos[{i}].lat", minimo=-90, maximo=90)
            lon = _numero(lon, f"pontos[{i}].lon", minimo=-180, maximo=180)
        elif endereco:
            rotulo = nome if nome == endereco else f"{nome} ({endereco})"
            if sem_conexao:
                fora.append({"nome": rotulo, "motivo": "sem_conexao"})
                continue
            if buscas >= MAX_ENDERECOS:
                fora.append({"nome": rotulo, "motivo": "limite"})
                continue
            buscas += 1
            try:
                achado = geocodificar(endereco)
            except mapas.SemConexao as e:
                sem_conexao = str(e)
                fora.append({"nome": rotulo, "motivo": "sem_conexao"})
                continue
            if not achado:
                fora.append({"nome": rotulo, "motivo": "nao_achado"})
                continue
            lat, lon = achado["lat"], achado["lon"]
            achado_nome = _texto(achado.get("nome"), 300)
        else:
            raise ErroWidget(t("O ponto {n} ({nome}) precisa de lat e lon, ou de um endereco.", n=i, nome=nome))
        item = {"nome": nome, "lat": round(float(lat), 6), "lon": round(float(lon), 6)}
        desc = _texto(p.get("descricao"), 300)
        if desc:
            item["descricao"] = desc
        if endereco:
            item["endereco"] = endereco
        if achado_nome:
            item["achado"] = achado_nome  # o lugar que o serviço de endereços achou (a cidade errada aparece aqui)
        saida.append(item)
    por_motivo = {m: [f["nome"] for f in fora if f["motivo"] == m] for m in MOTIVOS_FORA}
    if sem_conexao:
        avisos.append(t("A busca de endereços falhou ({motivo}).", motivo=sem_conexao))
        avisos.append(t("Ficaram de fora por falta de conexão: {lugares}.", lugares="; ".join(por_motivo["sem_conexao"])))
    if por_motivo["limite"]:
        avisos.append(t("Só procuro até {maximo} endereços por mapa; para mais pontos, mande lat e lon.",
                        maximo=MAX_ENDERECOS))
        avisos.append(t("Ficaram de fora por passar do limite: {lugares}.", lugares="; ".join(por_motivo["limite"])))
    if por_motivo["nao_achado"]:
        avisos.append(t("Ficaram de fora (não achei no mapa): {lugares}.", lugares="; ".join(por_motivo["nao_achado"])))
    if not saida:
        raise ErroWidget(t("Nenhum ponto do mapa foi encontrado. Mande lat e lon, ou endereços mais completos (rua, número, cidade)."))
    resultado = {"pontos": saida, "rota": _booleano(d.get("rota"), "rota", avisos) and len(saida) > 1}
    if fora:
        resultado["fora"] = fora
    return resultado


def _recomendacoes(d: dict, avisos: list[str]) -> dict:
    itens = _lista(d.get("itens"), "itens", 1, 12, avisos)
    saida = []
    for i, it in enumerate(itens, 1):
        if not isinstance(it, dict):
            raise ErroWidget(t("A recomendação {n} precisa ser um objeto com titulo e por_que.", n=i))
        titulo = _texto(it.get("titulo"), 120)
        por_que = _texto(it.get("por_que") or it.get("porque"), 400)
        if not titulo or not por_que:
            raise ErroWidget(t("A recomendação {n} precisa de titulo e de por_que (o motivo da indicação).", n=i))
        r = {"titulo": titulo, "tipo": _escolha(it.get("tipo"), TIPOS_RECOMENDACAO, _ALIAS_RECOMENDACAO, "outro"),
             "por_que": por_que}
        if it.get("ano") not in (None, ""):
            try:
                r["ano"] = int(_numero(it.get("ano"), f"itens[{i}].ano", minimo=1000, maximo=2200))
            except ErroWidget:
                avisos.append(t("{campo} ficou de fora: o ano precisa ser um número como 2019.", campo=f"itens[{i}].ano"))
        generos = it.get("generos") or []
        if isinstance(generos, str):
            generos = generos.split(",")
        generos = [g for g in (_texto(g, 30) for g in generos if isinstance(g, (str, int, float))) if g][:6]
        if generos:
            r["generos"] = generos
        onde = it.get("onde")
        if isinstance(onde, list):
            onde = ", ".join(str(x) for x in onde if isinstance(x, (str, int, float)))
        onde = _texto(onde, 120)
        if onde:
            r["onde"] = onde
        duracao = it.get("duracao")
        if isinstance(duracao, (int, float)) and not isinstance(duracao, bool):
            duracao = f"{_fmt(duracao)} min"
        duracao = _texto(duracao, 60)
        if duracao:
            r["duracao"] = duracao
        nota = _nota(it.get("nota"), f"itens[{i}].nota", avisos)
        if nota:
            r["nota"] = nota
        img = _url_https(it.get("imagem"), f"itens[{i}].imagem", avisos)
        if img:
            r["imagem"] = img
        saida.append(r)
    return {"itens": saida}


def _ponto_xy(v, campo: str) -> list:
    if isinstance(v, dict):
        v = [v.get("x"), v.get("y")]
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise ErroWidget(t("{campo} precisa ser um par [x, y].", campo=campo))
    return [_numero(v[0], campo + ".x"), _numero(v[1], campo + ".y")]


def _desenho(d: dict, avisos: list[str]) -> dict:
    largura = _numero(d.get("largura"), "largura", minimo=0.001, maximo=100000)
    altura = _numero(d.get("altura"), "altura", minimo=0.001, maximo=100000)
    unidade = _escolha(d.get("unidade") or "m", UNIDADES, _ALIAS_UNIDADE)
    if not unidade:
        raise ErroWidget(t("unidade precisa ser m, cm ou px."))
    formas = _lista(d.get("formas"), "formas", 1, 200, avisos)
    saida = []

    def dentro(valor, total, campo, n, tipo):
        if not -0.5 * total <= valor <= 1.5 * total:
            raise ErroWidget(t("A forma {n} ({forma}) sai muito do desenho: {campo} = {valor}, mas o desenho tem {largura} × {altura} {unidade}. Confira a unidade.",
                               n=n, forma=tipo, campo=campo, valor=_fmt(valor), largura=_fmt(largura),
                               altura=_fmt(altura), unidade=unidade))

    for i, f in enumerate(formas, 1):
        if not isinstance(f, dict):
            raise ErroWidget(t("A forma {n} precisa ser um objeto com tipo e coordenadas.", n=i))
        tipo = _escolha(f.get("tipo"), FORMAS, _ALIAS_FORMA)
        if not tipo:
            raise ErroWidget(t("A forma {n} tem um tipo desconhecido; use retangulo, circulo, linha, seta, texto, poligono ou cota.", n=i))
        c = f"formas[{i}]"
        s = {"tipo": tipo}
        if tipo == "retangulo":
            s["x"], s["y"] = _numero(f.get("x"), c + ".x"), _numero(f.get("y"), c + ".y")
            s["largura"] = _numero(f.get("largura"), c + ".largura", minimo=0.000001)
            s["altura"] = _numero(f.get("altura"), c + ".altura", minimo=0.000001)
            dentro(s["x"], largura, "x", i, tipo)
            dentro(s["y"], altura, "y", i, tipo)
            dentro(s["x"] + s["largura"], largura, "x + largura", i, tipo)
            dentro(s["y"] + s["altura"], altura, "y + altura", i, tipo)
            rot = _numero(f.get("rotacao"), c + ".rotacao", minimo=-360, maximo=360, obrigatorio=False)
            if rot:
                s["rotacao"] = rot
        elif tipo == "circulo":
            s["x"], s["y"] = _numero(f.get("x"), c + ".x"), _numero(f.get("y"), c + ".y")
            s["raio"] = _numero(f.get("raio"), c + ".raio", minimo=0.000001)
            dentro(s["x"], largura, "x", i, tipo)
            dentro(s["y"], altura, "y", i, tipo)
            dentro(s["raio"], max(largura, altura), "raio", i, tipo)
        elif tipo in ("linha", "seta", "cota"):
            for k in ("x1", "y1", "x2", "y2"):
                s[k] = _numero(f.get(k), f"{c}.{k}")
                dentro(s[k], largura if k[0] == "x" else altura, k, i, tipo)
            if s["x1"] == s["x2"] and s["y1"] == s["y2"]:
                raise ErroWidget(t("A forma {n} ({forma}) começa e termina no mesmo ponto.", n=i, forma=tipo))
            if tipo == "cota":
                desl = _numero(f.get("deslocamento"), c + ".deslocamento", obrigatorio=False)
                if desl:
                    dentro(abs(desl), max(largura, altura), "deslocamento", i, tipo)
                    s["deslocamento"] = desl
        elif tipo == "texto":
            s["x"], s["y"] = _numero(f.get("x"), c + ".x"), _numero(f.get("y"), c + ".y")
            dentro(s["x"], largura, "x", i, tipo)
            dentro(s["y"], altura, "y", i, tipo)
            s["texto"] = _texto(f.get("texto") or f.get("rotulo"), 80)
            if not s["texto"]:
                raise ErroWidget(t("A forma {n} (texto) está sem texto.", n=i))
            tam = _escolha(f.get("tamanho") or "medio", ("pequeno", "medio", "grande"), _ALIAS_TAMANHO, "medio")
            if tam != "medio":
                s["tamanho"] = tam
        elif tipo == "poligono":
            pts = f.get("pontos")
            if not isinstance(pts, list) or not 3 <= len(pts) <= 60:
                raise ErroWidget(t("A forma {n} (poligono) precisa de 3 a 60 pontos em pontos: [[x, y], ...].", n=i))
            s["pontos"] = [_ponto_xy(p, f"{c}.pontos[{j}]") for j, p in enumerate(pts, 1)]
            for x, y in s["pontos"]:
                dentro(x, largura, "x", i, tipo)
                dentro(y, altura, "y", i, tipo)
        if tipo != "texto":
            rot = _texto(f.get("rotulo"), 60)
            if rot:
                s["rotulo"] = rot
        cor = _cor(f.get("cor"), c, avisos)
        if cor:
            s["cor"] = cor
        if tipo in ("retangulo", "circulo", "poligono") and _booleano(f.get("preenchido"), c + ".preenchido", avisos):
            s["preenchido"] = True
        saida.append(s)
    resultado = {"largura": largura, "altura": altura, "unidade": unidade, "formas": saida}
    leg = d.get("legenda")
    if isinstance(leg, str) and leg.strip():
        resultado["legenda"] = _texto(leg, 200)
    elif isinstance(leg, list):
        itens = []
        for j, x in enumerate(leg[:12], 1):
            if isinstance(x, dict) and _texto(x.get("rotulo"), 60):
                itens.append({"cor": _cor(x.get("cor"), f"legenda[{j}]", avisos) or "acao",
                              "rotulo": _texto(x.get("rotulo"), 60)})
        if itens:
            resultado["legenda"] = itens
    return resultado


def _grafico(d: dict, avisos: list[str]) -> dict:
    tipo = _escolha(d.get("tipo_grafico") or "barras", TIPOS_GRAFICO, _ALIAS_GRAFICO)
    if not tipo:
        raise ErroWidget(t("tipo_grafico precisa ser barras, linhas, pizza ou area."))
    rotulos = d.get("rotulos")
    if not isinstance(rotulos, list) or not rotulos:
        raise ErroWidget(t("Mande em rotulos a lista dos nomes do eixo (ou das fatias da pizza)."))
    if len(rotulos) > 60:
        raise ErroWidget(t("O gráfico aceita até 60 rótulos; agrupe os dados (por mês, por exemplo)."))
    rotulos = [_texto(r, 40) or "?" for r in rotulos]
    series = d.get("series")
    if isinstance(series, dict):
        series = [series]
    if not isinstance(series, list) or not series:
        raise ErroWidget(t("Mande em series uma lista como [{nome, valores: [...]}], com um valor por rótulo."))
    if len(series) > 8:
        avisos.append(t("{campo} tinha {quantos}; ficaram os primeiros {maximo}.", campo="series", quantos=len(series),
                        maximo=8))
        series = series[:8]
    saida = []
    for i, s in enumerate(series, 1):
        if isinstance(s, list):
            s = {"valores": s}
        if not isinstance(s, dict) or not isinstance(s.get("valores"), list):
            raise ErroWidget(t("A série {n} precisa de valores: uma lista de números.", n=i))
        nome = _texto(s.get("nome"), 60) or t("Série {n}", n=i)
        if len(s["valores"]) != len(rotulos):
            raise ErroWidget(t("A série \"{nome}\" tem {quantos} valores, mas há {total} rótulos: mande um valor por rótulo.",
                               nome=nome, quantos=len(s["valores"]), total=len(rotulos)))
        valores = []
        for j, v in enumerate(s["valores"], 1):
            if v is None and tipo in ("linhas", "area"):
                valores.append(None)
            else:
                valores.append(_numero(v, f"series[{i}].valores[{j}]", minimo=-1e15, maximo=1e15))
        item = {"nome": nome, "valores": valores}
        cor = _cor(s.get("cor"), f"series[{i}]", avisos)
        if cor:
            item["cor"] = cor
        saida.append(item)
    if tipo == "pizza":
        if len(saida) > 1:
            avisos.append(t("A pizza usa uma série só; as outras ficaram de fora."))
            saida = saida[:1]
        if any(v < 0 for v in saida[0]["valores"]):
            raise ErroWidget(t("A pizza não aceita valores negativos."))
        if sum(saida[0]["valores"]) <= 0:
            raise ErroWidget(t("A pizza precisa de pelo menos um valor maior que zero."))
        if len(rotulos) > 12:
            pares = sorted(zip(rotulos, saida[0]["valores"]), key=lambda p: -p[1])
            resto = sum(v for _, v in pares[11:])
            # chave própria: "Outros" sozinho já é a trilha padrão das lições ("Other") no catálogo do servidor
            outros = t("Outros (fatias menores)")
            rotulos = [r for r, _ in pares[:11]] + [outros]
            saida[0]["valores"] = [v for _, v in pares[:11]] + [round(resto, 6)]
            avisos.append(t("A pizza tinha mais de 12 fatias; as menores viraram uma só, \"{rotulo}\".", rotulo=outros))
    resultado = {"tipo_grafico": tipo, "rotulos": rotulos, "series": saida}
    unidade = _texto(d.get("unidade"), 20)
    if unidade:
        resultado["unidade"] = unidade
    return resultado


def _valor_celula(v):
    if v is None or isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v if math.isfinite(v) else None
    return _texto(v, 120)


def _comparacao(d: dict, avisos: list[str]) -> dict:
    colunas = d.get("colunas")
    if not isinstance(colunas, list) or not 2 <= len(colunas) <= 6:
        raise ErroWidget(t("Mande em colunas de 2 a 6 nomes (o que está sendo comparado)."))
    colunas = [_texto(c, 60) or "?" for c in colunas]
    linhas = _lista(d.get("linhas"), "linhas", 1, 30, avisos)
    saida = []
    chaves = [_chave(c) for c in colunas]
    for i, ln in enumerate(linhas, 1):
        if not isinstance(ln, dict) or not isinstance(ln.get("valores"), list):
            raise ErroWidget(t("A linha {n} precisa de criterio e valores (uma lista).", n=i))
        criterio = _texto(ln.get("criterio"), 80)
        if not criterio:
            raise ErroWidget(t("A linha {n} está sem criterio.", n=i))
        if len(ln["valores"]) != len(colunas):
            raise ErroWidget(t("A linha \"{criterio}\" tem {quantos} valores para {total} colunas: mande um por coluna.",
                               criterio=criterio, quantos=len(ln["valores"]), total=len(colunas)))
        item = {"criterio": criterio, "valores": [_valor_celula(v) for v in ln["valores"]]}
        melhor = ln.get("melhor")
        if isinstance(melhor, str) and _chave(melhor) in chaves:
            melhor = chaves.index(_chave(melhor))
        if melhor is not None and not isinstance(melhor, bool) and isinstance(melhor, (int, float)) \
                and float(melhor).is_integer() and 0 <= int(melhor) < len(colunas):
            item["melhor"] = int(melhor)
        elif melhor not in (None, ""):
            avisos.append(t("melhor da linha \"{criterio}\" ficou de fora: use o número da coluna, começando do 0.",
                            criterio=criterio))
        saida.append(item)
    return {"colunas": colunas, "linhas": saida}


def _linha_do_tempo(d: dict, avisos: list[str]) -> dict:
    eventos = _lista(d.get("eventos"), "eventos", 1, 40, avisos)
    saida = []
    for i, ev in enumerate(eventos, 1):
        if not isinstance(ev, dict):
            raise ErroWidget(t("O evento {n} precisa ser um objeto com data e titulo.", n=i))
        data, titulo = _texto(ev.get("data"), 40), _texto(ev.get("titulo"), 120)
        if not data or not titulo:
            raise ErroWidget(t("O evento {n} precisa de data e titulo.", n=i))
        item = {"data": data, "titulo": titulo}
        desc = _texto(ev.get("descricao"), 400)
        if desc:
            item["descricao"] = desc
        saida.append(item)
    return {"eventos": saida}


def _checklist(d: dict, avisos: list[str]) -> dict:
    itens = _lista(d.get("itens"), "itens", 1, 60, avisos)
    saida = []
    for i, it in enumerate(itens, 1):
        if isinstance(it, str):
            it = {"texto": it}
        texto = _texto(it.get("texto") if isinstance(it, dict) else None, 200)
        if not texto:
            raise ErroWidget(t("O item {n} do checklist está sem texto.", n=i))
        saida.append({"texto": texto, "feito": _booleano(it.get("feito"), f"itens[{i}].feito", avisos)})
    return {"itens": saida}


def normalizar(entrada, geocodificar=None) -> tuple[dict, list[str]]:
    """O widget pronto para mostrar e a lista do que foi ajustado no caminho. ErroWidget diz o que corrigir."""
    if not isinstance(entrada, dict):
        raise ErroWidget(t("Mande tipo, titulo e dados."))
    tipo = _escolha(entrada.get("tipo"), TIPOS, _ALIAS_TIPO)
    if not tipo:
        raise ErroWidget(t("tipo precisa ser um destes: {tipos}.", tipos=", ".join(TIPOS)))
    dados = entrada.get("dados")
    if isinstance(dados, str):
        try:
            dados = json.loads(dados)
        except ValueError:
            dados = None
    if not isinstance(dados, dict):
        raise ErroWidget(t("dados precisa ser um objeto no formato do tipo {tipo}.", tipo=tipo))
    avisos: list[str] = []
    if tipo == "produtos":
        dados = _produtos(dados, avisos)
    elif tipo == "mapa":
        dados = _mapa(dados, avisos, geocodificar or mapas.geocodificar)
    elif tipo == "recomendacoes":
        dados = _recomendacoes(dados, avisos)
    elif tipo == "desenho":
        dados = _desenho(dados, avisos)
    elif tipo == "grafico":
        dados = _grafico(dados, avisos)
    elif tipo == "comparacao":
        dados = _comparacao(dados, avisos)
    elif tipo == "linha_do_tempo":
        dados = _linha_do_tempo(dados, avisos)
    else:
        dados = _checklist(dados, avisos)
    widget = {"tipo": tipo, "titulo": _texto(entrada.get("titulo"), 120), "dados": dados, "versao": 1,
              "criado_em": datetime.now().astimezone().isoformat(timespec="seconds")}
    if len(json.dumps(widget, ensure_ascii=False)) > MAX_JSON:
        raise ErroWidget(t("O widget ficou grande demais; mande menos itens ou textos mais curtos."))
    return widget, avisos


# ======================= imagens de fora =======================

TIPOS_IMAGEM = ("image/png", "image/jpeg", "image/webp", "image/gif")
MAX_IMAGEM = 5 * 1024 * 1024
VALIDADE_IMAGEM = 7 * 86400
MAX_REDIRECIONAMENTOS = 3
_sem_imagens = threading.BoundedSemaphore(4)


class ErroImagem(Erro):
    pass


def _ip_publico(ip: str) -> bool:
    try:
        a = ipaddress.ip_address(ip.split("%", 1)[0])
    except ValueError:
        return False
    if isinstance(a, ipaddress.IPv6Address):
        embutido = a.ipv4_mapped or a.sixtofour or (a.teredo[1] if a.teredo else None)
        if embutido is not None and not _ip_publico(str(embutido)):
            return False
    return a.is_global and not (a.is_private or a.is_loopback or a.is_link_local or a.is_multicast
                                or a.is_reserved or a.is_unspecified)


def _resolver(host: str) -> list[str]:
    infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    return list(dict.fromkeys(str(i[4][0]) for i in infos))


def _partes_url(url: str) -> tuple[str, str, str | None]:
    """(host, caminho com a query, IP quando o endereço já é um IP) conferidos sem rede: esquema, usuário, porta e o IP
    escrito direto. ErroImagem quando o endereço nunca poderia ser buscado."""
    try:
        p = urllib.parse.urlsplit(str(url or "").strip())
        porta = p.port
    except ValueError:
        raise ErroImagem(400, t("Endereço de imagem inválido."))
    if p.scheme.lower() != "https":
        raise ErroImagem(400, t("Só dá para mostrar imagem de endereço https."))
    host = (p.hostname or "").strip(".")
    if not host or p.username or p.password or len(str(url)) > 2048:
        raise ErroImagem(400, t("Endereço de imagem inválido."))
    if porta not in (None, 443):
        raise ErroImagem(400, t("Só a porta padrão do https (443) é aceita para imagens."))
    try:
        ip = str(ipaddress.ip_address(host))
    except ValueError:
        ip = None
    if ip is not None and not _ip_publico(ip):
        raise ErroImagem(403, t("Endereço recusado: a imagem aponta para a rede interna ou para este computador."))
    alvo = (p.path or "/") + (f"?{p.query}" if p.query else "")
    return host, alvo, ip


def _conferir_url(url: str) -> tuple[str, str, str]:
    """(host, caminho com a query, IP conferido) de um endereço que pode ser buscado agora; ErroImagem quando não pode.
    Resolve o nome: só para baixar, nunca para servir o que já está em disco."""
    host, alvo, ip = _partes_url(url)
    if ip:
        ips = [ip]
    else:
        try:
            ips = _resolver(host)
        except (OSError, UnicodeError):
            raise ErroImagem(502, t("Não achei o site da imagem."))
    if not ips:
        raise ErroImagem(502, t("Não achei o site da imagem."))
    if any(not _ip_publico(ip) for ip in ips):
        raise ErroImagem(403, t("Endereço recusado: a imagem aponta para a rede interna ou para este computador."))
    return host, alvo, ips[0]


class _ConexaoNoIp(http.client.HTTPSConnection):
    """HTTPS para o IP já conferido, com o nome do site no certificado e no Host (assim um DNS que muda de resposta
    entre a conferência e a conexão não leva a busca para a rede interna)."""

    def __init__(self, host: str, ip: str, timeout: float):
        super().__init__(host, 443, timeout=timeout, context=ssl.create_default_context())
        self._ip = ip

    def connect(self):
        sock = socket.create_connection((self._ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def _pedir_https(host: str, ip: str, alvo: str, limite: int) -> tuple[int, dict, bytes]:
    conn = _ConexaoNoIp(host, ip, timeout=15)
    try:
        conn.request("GET", alvo, headers={
            "User-Agent": mapas.user_agent(), "Accept": "image/png,image/jpeg,image/webp,image/gif;q=0.9",
            "Accept-Encoding": "identity"})
        r = conn.getresponse()
        cab = {k.lower(): v for k, v in r.getheaders()}
        if 300 <= r.status < 400:
            return r.status, cab, b""
        try:
            if int(cab.get("content-length") or 0) > limite:
                raise ErroImagem(413, t("A imagem passa de 5 MB."))
        except ValueError:
            pass
        corpo = r.read(limite + 1)
        return r.status, cab, corpo
    finally:
        conn.close()


def _tipo_real(corpo: bytes) -> str | None:
    if corpo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if corpo[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if corpo[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if corpo[:4] == b"RIFF" and corpo[8:12] == b"WEBP":
        return "image/webp"
    return None


def _arquivos_imagem(url: str):
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()
    base = config.DADOS / "cache" / "imagens"
    return base / f"{h}.img", base / f"{h}.json"


def _guardada(arq_img, arq_meta) -> tuple[bytes, str, float] | None:
    """(bytes, tipo, quando baixou) da cópia em disco, vencida ou não; None quando não há cópia que sirva."""
    try:
        meta = json.loads(arq_meta.read_text(encoding="utf-8"))
        if meta.get("tipo") in TIPOS_IMAGEM:
            return arq_img.read_bytes(), meta["tipo"], float(meta.get("em") or 0)
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    return None


def _baixar_de_fora(url: str) -> tuple[bytes, str]:
    atual = url
    with _sem_imagens:
        for _ in range(MAX_REDIRECIONAMENTOS + 1):
            host, alvo, ip = _conferir_url(atual)
            try:
                status, cab, corpo = _pedir_https(host, ip, alvo, MAX_IMAGEM)
            except ErroImagem:
                raise
            except (OSError, http.client.HTTPException, ssl.SSLError):
                raise ErroImagem(502, t("Não deu para baixar a imagem."))
            if status in (301, 302, 303, 307, 308) and cab.get("location"):
                atual = urllib.parse.urljoin(atual, cab["location"])
                continue
            break
        else:
            raise ErroImagem(502, t("A imagem redirecionou vezes demais."))
    if status != 200:
        raise ErroImagem(502, t("O site da imagem respondeu com o erro {codigo}.", codigo=status))
    if len(corpo) > MAX_IMAGEM:
        raise ErroImagem(413, t("A imagem passa de 5 MB."))
    declarado = str(cab.get("content-type") or "").split(";")[0].strip().lower()
    real = _tipo_real(corpo)
    if "svg" in declarado or "xml" in declarado or real is None or declarado not in TIPOS_IMAGEM:
        raise ErroImagem(415, t("Esse arquivo não é uma imagem aceita (só PNG, JPEG, WebP e GIF)."))
    return corpo, real


def baixar_imagem(url: str) -> tuple[bytes, str]:
    """(bytes, Content-Type) de uma imagem de fora, pelas regras do docstring do módulo. O que já está em disco vale
    antes de qualquer acesso à rede (nem o DNS é consultado), então a foto aparece também sem internet; vencida, ela é
    baixada de novo, e a cópia velha só volta se a internet ou o site falharem."""
    url = str(url or "").strip()
    _partes_url(url)  # recusa já, sem rede e antes de olhar o cache, o que nunca poderia ser buscado
    _talvez_podar()
    arq_img, arq_meta = _arquivos_imagem(url)
    guardada = _guardada(arq_img, arq_meta)
    if guardada and time.time() - guardada[2] < VALIDADE_IMAGEM:
        mapas.marcar_uso(arq_meta)
        return guardada[0], guardada[1]
    try:
        corpo, real = _baixar_de_fora(url)
    except ErroImagem as e:
        if guardada and e.status == 502:  # sem internet ou site fora do ar: a foto velha é melhor que nenhuma
            mapas.marcar_uso(arq_meta)
            return guardada[0], guardada[1]
        raise
    try:
        mapas.gravar(arq_img, corpo)
        mapas.gravar(arq_meta, json.dumps({"tipo": real, "em": time.time(), "url": url[:2048]}).encode("utf-8"))
    except OSError:
        pass
    return corpo, real


# ---- o cache de imagens não cresce para sempre ----
SEM_USO_IMAGEM = 30 * 86400            # imagem que ninguém abriu em 30 dias sai do disco
MAX_CACHE_IMAGENS = 200 * 1024 * 1024  # e passando disso, saem as usadas há mais tempo
INTERVALO_PODA = 6 * 3600
_poda = {"em": 0.0}
_trava_poda = threading.Lock()


def podar_imagens(agora: float | None = None) -> int:
    """Apaga do cache as imagens sem uso há 30 dias e, se ainda passar de MAX_CACHE_IMAGENS, as usadas há mais tempo
    (o uso é o horário do .json, que mapas.marcar_uso atualiza). Devolve quantas apagou."""
    agora = agora or time.time()
    pasta = config.DADOS / "cache" / "imagens"
    if not pasta.is_dir():
        return 0
    entradas = []
    for arq_meta in pasta.glob("*.json"):
        arq_img = arq_meta.with_suffix(".img")
        try:
            uso = arq_meta.stat().st_mtime
            tamanho = arq_meta.stat().st_size + (arq_img.stat().st_size if arq_img.is_file() else 0)
        except OSError:
            continue
        entradas.append({"uso": uso, "tamanho": tamanho, "protegida": False, "arquivos": (arq_img, arq_meta)})
    apagadas = mapas.podar_entradas(entradas, agora=agora, sem_uso=SEM_USO_IMAGEM, limite=MAX_CACHE_IMAGENS,
                                    apagar=lambda e: mapas.apagar_arquivos(*e["arquivos"]))
    mapas.apagar_sobras(pasta, ".img", agora)
    return apagadas


def _talvez_podar() -> None:
    """Poda o cache numa linha de fundo: na primeira imagem pedida depois que o app abre e, depois, a cada 6 horas."""
    agora = time.time()
    with _trava_poda:
        if agora - _poda["em"] < INTERVALO_PODA:
            return
        _poda["em"] = agora

    def podar():
        try:
            podar_imagens()
        except Exception:  # faxina é melhor esforço: nunca derruba quem pediu a imagem
            pass
    threading.Thread(target=podar, daemon=True, name="poda-imagens").start()


# ======================= exportar a conversa em Markdown =======================
# O Claude é orientado a não repetir no texto o que o widget mostra; sem isto, a conversa exportada perderia os dados
# (os preços, os pontos do mapa, a tabela). Mesma informação do "Copiar como texto" da tela (textoDoWidget, widgets.js).

_ESCAPAR_MD = re.compile(r"([\\`*_\[\]<>|#])")


def _md(v) -> str:
    """Texto solto dentro do Markdown: numa linha só e sem os caracteres que viram formatação (nem o | da tabela)."""
    return _ESCAPAR_MD.sub(r"\\\1", " ".join(str("" if v is None else v).split()))


def _en() -> bool:
    return idioma() == "en"


def _trocar_separadores(s: str) -> str:
    return s if _en() else s.translate(str.maketrans({",": ".", ".": ","}))


def _num(n, casas: int = 2) -> str:
    if n is None or isinstance(n, bool):
        return t("sem dado")
    try:
        f = float(n)
    except (TypeError, ValueError):
        return str(n)
    s = f"{f:,.{casas}f}"
    if casas:
        s = s.rstrip("0").rstrip(".")
    return _trocar_separadores("0" if s == "-0" else s)


def _preco_md(valor, moeda) -> str:
    moeda = str(moeda or "BRL")
    casas = 0 if moeda in _MOEDAS_SEM_CASAS else 3 if moeda in _MOEDAS_3_CASAS else 2
    numero = _trocar_separadores(f"{float(valor):,.{casas}f}")
    simbolo = {"BRL": "R$", "USD": "$" if _en() else "US$", "EUR": "€", "GBP": "£", "JPY": "¥"}.get(moeda)
    return f"{simbolo} {numero}" if simbolo else f"{moeda} {numero}"


def _data_md(v) -> str:
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(v or ""))
    if not m:
        return str(v or "")
    ano, mes, dia = m.groups()
    return f"{int(mes)}/{int(dia)}/{ano}" if _en() else f"{dia}/{mes}/{ano}"


def _valor_md(v, unidade) -> str:
    if v is None:
        return t("sem dado")
    n = _num(v)
    if not unidade:
        return n
    if unidade in ("R$", "US$", "$", "€", "£", "¥"):
        return f"{unidade} {n}"
    return f"{n}%" if unidade == "%" else f"{n} {unidade}"


def _nota_md(nota: dict) -> str:
    texto = _num(nota.get("valor"), 1)
    if nota.get("escala"):
        texto += f"/{_num(nota['escala'], 1)}"
    return texto + (f" ({nota['fonte']})" if nota.get("fonte") else "")


def _link_md(texto, url) -> str:
    alvo = str(url).replace("(", "%28").replace(")", "%29").replace(" ", "%20")
    return f"[{_md(texto)}]({alvo})"


def _par_md(x, y) -> str:
    return t("({x}; {y})", x=_num(x, 2), y=_num(y, 2))


def _tabela_md(cabecalho: list[str], linhas: list[list[str]]) -> list[str]:
    saida = ["| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho)]
    saida += ["| " + " | ".join(c if c else " " for c in ln) + " |" for ln in linhas]
    return saida


def _nome_tipo(tipo) -> str:
    return {"produtos": t("Produtos"), "mapa": t("Mapa"), "recomendacoes": t("Recomendações"), "desenho": t("Desenho"),
            "grafico": t("Gráfico"), "comparacao": t("Comparação"), "linha_do_tempo": t("Linha do tempo"),
            "checklist": t("Checklist")}.get(tipo, str(tipo))


def _nome_recomendacao(tipo) -> str:
    return {"serie": t("Série"), "filme": t("Filme"), "jogo": t("Jogo"), "anime": t("Anime"), "livro": t("Livro"),
            "musica": t("Música"), "podcast": t("Podcast")}.get(tipo, t("Indicação"))


def _rotulo_onde(tipo) -> str:
    if tipo == "jogo":
        return t("Onde jogar")
    if tipo == "livro":
        return t("Onde ler")
    if tipo in ("musica", "podcast"):
        return t("Onde ouvir")
    return t("Onde encontrar") if tipo == "outro" else t("Onde ver")


def _nome_forma(tipo) -> str:
    return {"retangulo": t("Retângulo"), "circulo": t("Círculo"), "linha": t("Linha"), "seta": t("Seta"),
            "texto": t("Texto"), "poligono": t("Polígono"), "cota": t("Cota")}.get(tipo, str(tipo))


def _nome_cor(cor) -> str:
    return {"acao": t("Verde-petróleo"), "azul": t("Azul"), "verde": t("Verde"), "vermelho": t("Vermelho"),
            "laranja": t("Laranja"), "amarelo": t("Amarelo"), "roxo": t("Roxo"), "rosa": t("Rosa"),
            "marrom": t("Marrom"), "cinza": t("Cinza"), "preto": t("Preto")}.get(cor, str(cor))


def motivo_fora(motivo) -> str:
    if motivo == "limite":
        return t("passou do limite de {maximo} endereços por mapa", maximo=MAX_ENDERECOS)
    if motivo == "sem_conexao":
        return t("sem conexão com o serviço de endereços")
    return t("endereço não encontrado")


def _md_produtos(d: dict) -> list[str]:
    itens = [it for it in d.get("itens") or [] if isinstance(it, dict)]
    contagem: dict[str, int] = {}
    for it in itens:
        contagem[it.get("moeda")] = contagem.get(it.get("moeda"), 0) + 1
    principal = max(contagem, key=contagem.get) if contagem else "BRL"
    comparaveis = [it["preco"] for it in itens if it.get("moeda") == principal]
    menor = min(comparaveis) if comparaveis else None
    itens.sort(key=lambda it: (0, it["preco"]) if it.get("moeda") == principal else (1, 0))
    com_loja = any(it.get("loja") for it in itens)
    com_nota = any(it.get("nota") for it in itens)
    com_obs = any(it.get("observacao") for it in itens)
    cab = [t("Produto"), t("Preço")] + ([t("Loja")] if com_loja else []) + ([t("Nota")] if com_nota else []) \
        + ([t("Observação")] if com_obs else [])
    linhas = []
    for it in itens:
        preco = _md(_preco_md(it["preco"], it.get("moeda")))
        if len(comparaveis) > 1 and it.get("moeda") == principal and it["preco"] == menor:
            preco = f"**{preco}** ({_md(t('mais barato'))})"
        ln = [_link_md(it["nome"], it["link"]) if it.get("link") else _md(it["nome"]), preco]
        if com_loja:
            ln.append(_md(it.get("loja")))
        if com_nota:
            ln.append(_md(_nota_md(it["nota"])) if it.get("nota") else "")
        if com_obs:
            ln.append(_md(it.get("observacao")))
        linhas.append(ln)
    return _tabela_md(cab, linhas) + ["", "_" + _md(t("Preços vistos em {data}; confira na loja.",
                                                       data=_data_md(d.get("visto_em")))) + "_"]


def _md_mapa(d: dict) -> list[str]:
    linhas = []
    for i, p in enumerate(d.get("pontos") or [], 1):
        linhas.append(f"{i}. **{_md(p['nome'])}**" + (f": {_md(p['descricao'])}" if p.get("descricao") else ""))
        if p.get("endereco"):
            linhas.append("   - " + _md(t("Endereço: {endereco}", endereco=p["endereco"])))
        if p.get("achado") and p.get("achado") != p.get("endereco"):
            linhas.append("   - " + _md(t("No mapa: {lugar}", lugar=p["achado"])))
        osm = f"https://www.openstreetmap.org/?mlat={p['lat']}&mlon={p['lon']}#map=17/{p['lat']}/{p['lon']}"
        linhas.append(f"   - {_link_md(t('Abrir no OpenStreetMap'), osm)} {_md(_par_md(p['lat'], p['lon']))}")
    if d.get("fora"):
        linhas += ["", f"**{_md(t('Ficaram de fora do mapa:'))}**"]
        linhas += [f"- {_md(f.get('nome'))} ({_md(motivo_fora(f.get('motivo')))})" for f in d["fora"]]
    if d.get("rota"):
        linhas += ["", _md(t("A linha liga os pontos na ordem da lista."))]
    return linhas


def _md_recomendacoes(d: dict) -> list[str]:
    linhas = []
    for i, it in enumerate(d.get("itens") or [], 1):
        meta = ", ".join(str(x) for x in (_nome_recomendacao(it.get("tipo")), it.get("ano"), it.get("duracao")) if x)
        linhas.append(f"{i}. **{_md(it['titulo'])}** ({_md(meta)})")
        if it.get("generos"):
            linhas.append(f"   - {_md(t('Gêneros'))}: {_md(', '.join(it['generos']))}")
        if it.get("onde"):
            linhas.append(f"   - {_md(_rotulo_onde(it.get('tipo')))}: {_md(it['onde'])}")
        if it.get("nota"):
            linhas.append(f"   - {_md(t('Nota'))}: {_md(_nota_md(it['nota']))}")
        linhas.append(f"   - {_md(t('Por que'))}: {_md(it['por_que'])}")
    return linhas


def _md_desenho(d: dict) -> list[str]:
    un = d.get("unidade") or ""
    linhas = [_md(t("Desenho de {largura} por {altura} {unidade}", largura=_num(d["largura"]),
                    altura=_num(d["altura"]), unidade=un)), ""]
    for f in d.get("formas") or []:
        tipo = f.get("tipo")
        nome = _nome_forma(tipo) + (f" \"{f['rotulo']}\"" if f.get("rotulo") else "")
        if tipo == "retangulo":
            onde = t("em {ponto}, {largura} × {altura} {unidade}", ponto=_par_md(f["x"], f["y"]),
                     largura=_num(f["largura"]), altura=_num(f["altura"]), unidade=un)
        elif tipo == "circulo":
            onde = t("centro em {ponto}, raio {raio} {unidade}", ponto=_par_md(f["x"], f["y"]), raio=_num(f["raio"]),
                     unidade=un)
        elif tipo in ("linha", "seta"):
            onde = t("de {inicio} a {fim}", inicio=_par_md(f["x1"], f["y1"]), fim=_par_md(f["x2"], f["y2"]))
        elif tipo == "cota":
            onde = f"{_num(math.hypot(f['x2'] - f['x1'], f['y2'] - f['y1']))} {un}"
        elif tipo == "texto":
            onde = f"\"{f['texto']}\" " + t("em {ponto}", ponto=_par_md(f["x"], f["y"]))
        elif tipo == "poligono":
            onde = t("{n} pontos", n=len(f.get("pontos") or []))
        else:
            onde = ""
        linhas.append(f"- {_md(nome)}: {_md(onde)}")
    leg = d.get("legenda")
    if isinstance(leg, list) and leg:
        itens = "; ".join(f"{_nome_cor(x.get('cor'))} = {x.get('rotulo')}" for x in leg if isinstance(x, dict))
        linhas += ["", f"{_md(t('Legenda'))}: {_md(itens)}"]
    elif isinstance(leg, str) and leg:
        linhas += ["", _md(leg)]
    return linhas


def _md_grafico(d: dict) -> list[str]:
    rotulos, series, un = d.get("rotulos") or [], d.get("series") or [], d.get("unidade")
    if d.get("tipo_grafico") == "pizza":
        valores = (series[0].get("valores") if series else None) or []
        total = sum(v for v in valores if v)
        linhas = [[_md(r), _md(_valor_md(v, un)), _md(f"{_num((v / total) * 100 if total and v else 0, 1)}%")]
                  for r, v in zip(rotulos, valores)]
        linhas.append([f"**{_md(t('Total'))}**", f"**{_md(_valor_md(total, un))}**", "**100%**"])
        return _tabela_md([t("Fatia"), t("Valor"), "%"], linhas)
    cab = [t("Rótulo")] + [_md(s.get("nome")) for s in series]
    linhas = [[_md(r)] + [_md(_valor_md((s.get("valores") or [None] * len(rotulos))[i], un)) for s in series]
              for i, r in enumerate(rotulos)]
    return _tabela_md(cab, linhas)


def _md_comparacao(d: dict) -> list[str]:
    colunas = d.get("colunas") or []

    def celula(v) -> str:
        if v is True:
            return t("sim")
        if v is False:
            return t("não")
        if v is None or v == "":
            return t("sem dado")
        return _num(v) if isinstance(v, (int, float)) else str(v)

    linhas, vitorias = [], [0] * len(colunas)
    for ln in d.get("linhas") or []:
        melhor = ln.get("melhor")
        valores = []
        for j, v in enumerate(ln.get("valores") or []):
            c = _md(celula(v))
            if melhor == j:
                c = f"**{c}** {_md(t('(melhor)'))}"
                vitorias[j] += 1
            valores.append(c)
        linhas.append([_md(ln.get("criterio"))] + valores)
    com_melhor = sum(vitorias)
    if com_melhor:
        linhas.append([f"**{_md(t('Melhor em'))}**"] + [_md(t("{n} de {total}", n=n, total=com_melhor)) for n in vitorias])
    return _tabela_md([t("Critério")] + [_md(c) for c in colunas], linhas)


def _markdown(w: dict) -> list[str]:
    tipo, d = w["tipo"], w["dados"]
    linhas = [f"**{_md(_nome_tipo(tipo))}: {_md(w.get('titulo') or _nome_tipo(tipo))}**", ""]
    if tipo == "produtos":
        linhas += _md_produtos(d)
    elif tipo == "mapa":
        linhas += _md_mapa(d)
    elif tipo == "recomendacoes":
        linhas += _md_recomendacoes(d)
    elif tipo == "desenho":
        linhas += _md_desenho(d)
    elif tipo == "grafico":
        linhas += _md_grafico(d)
    elif tipo == "comparacao":
        linhas += _md_comparacao(d)
    elif tipo == "linha_do_tempo":
        linhas += [f"- **{_md(ev.get('data'))}**: {_md(ev.get('titulo'))}"
                   + (f". {_md(ev['descricao'])}" if ev.get("descricao") else "") for ev in d.get("eventos") or []]
    elif tipo == "checklist":
        linhas += [f"- [{'x' if it.get('feito') else ' '}] {_md(it.get('texto'))}" for it in d.get("itens") or []]
    return linhas


def texto_para_exportar(tool_use_id: str) -> str | None:
    """O widget salvo desta chamada de mostrar_widget em Markdown legível (tabela para produtos, gráfico e comparação;
    lista com coordenadas para o mapa...), no idioma do app, para a exportação da conversa. None quando não há widget
    salvo com esse id."""
    try:
        w = ler(tool_use_id)
    except Erro:
        return None
    if not w or w.get("tipo") not in TIPOS or not isinstance(w.get("dados"), dict):
        return None
    try:
        return "\n".join(_markdown(w)).strip()
    except (KeyError, TypeError, ValueError, AttributeError, IndexError, ZeroDivisionError):
        # arquivo estragado (editado à mão, de uma versão antiga): fica pelo menos o título
        return f"**{_md(_nome_tipo(w.get('tipo')))}: {_md(w.get('titulo') or '')}**"


# ======================= rotas =======================
# a da imagem vem antes da do widget: "/api/widgets/imagem" também casaria com "/api/widgets/<tid>"

@rota("GET", "/api/widgets/imagem")
def r_imagem(h):
    dados, tipo = baixar_imagem(h.query().get("url", ""))
    h._bytes(dados, tipo, cab={"Cache-Control": "private, max-age=604800", "X-Content-Type-Options": "nosniff",
                               "Content-Security-Policy": "default-src 'none'; sandbox"})


@rota("GET", "/api/widgets/<tid>")
def r_widget(h, tid):
    w = ler(tid)
    if w is None:
        raise Erro(404, t("Este widget não existe mais."))
    h._json(w)


@rota("PATCH", "/api/widgets/<tid>")
def r_marcar(h, tid):
    h._json(marcar(tid, h.corpo().get("marcados")))


# ======================= demonstração (api_falsa.py) =======================

def _sem_acento(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii").lower()


_GATILHOS = (  # a ordem importa: o mais específico primeiro
    ("linha_do_tempo", r"linha do tempo|cronologia", r"timeline"),
    ("checklist", r"checklist|lista de (tarefas|verificacao|coisas)", r"checklist|to-?do list|packing list"),
    ("mapa", r"\bmapas?\b|onde fica", r"\bmaps?\b|where is"),
    ("desenho", r"\bplanta\b|desenh|comodo|layout", r"floor ?plan|drawing|\bdraw\b|layout"),
    ("grafico", r"grafico", r"\bchart\b|\bgraph\b"),
    ("produtos", r"preco|produto|comprar", r"\bprices?\b|product|\bbuy\b|shopping"),
    ("recomendacoes", r"recomend|indica|\bseries?\b|filmes?\b", r"recommend|\bmovies?\b|\bshows?\b|what to watch"),
    ("comparacao", r"compar", r"compar"),
)


def demo(texto: str, nomes) -> dict | None:
    """Para a API de mentira: o input pronto de um mostrar_widget quando a mensagem pede um (mapa, preços,
    recomendações, planta, gráfico, comparação, linha do tempo ou checklist), em português ou inglês. Os pontos do
    mapa já vêm com coordenada, para a demonstração funcionar sem internet."""
    if "mostrar_widget" not in (nomes or ()):
        return None
    s = _sem_acento(str(texto or ""))
    en = len(re.findall(r"\b(the|and|show|of|for|please|with|what|my|some|can|you|this|these|to|is|in|recommend|"
                        r"movies?|maps?|charts?|draw|prices?|plans?|make|build|between|two|project|timeline|moving|"
                        r"comparison|checklist)\b", s))
    pt = len(re.findall(r"\b(de|do|da|dos|das|que|para|um|uma|com|meu|minha|mostre|mostra|quero|faca|voce|os|as|"
                        r"no|na|em|recomende|desenhe|filmes?|mapas?|grafico|precos?|planta|monte|entre|dois|linha|"
                        r"tempo|mudanca|comparacao)\b", s))
    ingles = en > pt or (en == pt and idioma() == "en")  # empate: vale o idioma do app
    for tipo, pt, en in _GATILHOS:
        if re.search(en if ingles else pt, s) or re.search(pt if ingles else en, s):
            return _exemplo(tipo, ingles, s)
    return None


def _exemplo(tipo: str, en: bool, s: str) -> dict:
    hoje = date.today().isoformat()
    if tipo == "mapa":
        if re.search(r"\brio\b", s):
            pontos = [("Cristo Redentor", "Corcovado", -22.951916, -43.210487),
                      ("Pão de Açúcar", "Bondinho na Urca" if not en else "Cable car in Urca", -22.948658, -43.157444),
                      ("Escadaria Selarón", "Lapa", -22.915370, -43.179360),
                      ("Praia de Copacabana", "Posto 5", -22.971177, -43.182543)]
            titulo = "Passeio pelo Rio de Janeiro" if not en else "A day in Rio de Janeiro"
        else:
            pontos = [("MASP", "Avenida Paulista", -23.561414, -46.655881),
                      ("Parque Ibirapuera", "Portão 3" if not en else "Gate 3", -23.587416, -46.657634),
                      ("Pinacoteca", "Luz", -23.534237, -46.633855),
                      ("Mercado Municipal", "Centro" if not en else "Downtown", -23.541696, -46.629848)]
            titulo = "Passeio por São Paulo" if not en else "A day in São Paulo"
        return {"tipo": "mapa", "titulo": titulo, "dados": {
            "pontos": [{"nome": n, "descricao": d, "lat": la, "lon": lo} for n, d, la, lo in pontos], "rota": True}}
    if tipo == "produtos":
        if en:
            itens = [("Wireless noise-cancelling headphones (sample)", 189.0, "Sample Store A", 4.6, "Free shipping"),
                     ("Over-ear Bluetooth headphones (sample)", 149.9, "Sample Store B", 4.3, "Ships in 5 days"),
                     ("Sports earbuds (sample)", 79.0, "Sample Store C", 4.1, "Water resistant")]
            moeda, titulo = "USD", "Headphones: prices compared"
        else:
            itens = [("Fone sem fio com cancelamento de ruído (exemplo)", 899.9, "Loja de exemplo A", 4.6, "Frete grátis"),
                     ("Headphone Bluetooth (exemplo)", 649.0, "Loja de exemplo B", 4.3, "Entrega em 5 dias"),
                     ("Fone esportivo intra-auricular (exemplo)", 289.9, "Loja de exemplo C", 4.1, "Resistente a suor")]
            moeda, titulo = "BRL", "Fones de ouvido: preços lado a lado"
        return {"tipo": "produtos", "titulo": titulo, "dados": {
            "itens": [{"nome": n, "preco": p, "moeda": moeda, "loja": lj, "nota": nt, "observacao": o,
                       "link": "https://example.com/"} for n, p, lj, nt, o in itens], "visto_em": hoje}}
    if tipo == "recomendacoes":
        itens = [
            {"titulo": "Dark", "tipo": "serie", "ano": 2017, "generos": ["ficção científica", "suspense"] if not en else ["sci-fi", "thriller"],
             "onde": "Netflix", "duracao": "3 temporadas" if not en else "3 seasons",
             "por_que": "Mistério de viagem no tempo que se fecha direitinho no final." if not en else "A time-travel mystery that ties up neatly at the end."},
            {"titulo": "Interestelar" if not en else "Interstellar", "tipo": "filme", "ano": 2014,
             "generos": ["ficção científica", "drama"] if not en else ["sci-fi", "drama"], "duracao": "2 h 49 min",
             "por_que": "Ciência de verdade e uma história de pai e filha." if not en else "Real science and a father and daughter story."},
            {"titulo": "Hollow Knight", "tipo": "jogo", "ano": 2017, "generos": ["metroidvania"],
             "onde": "PC, Switch, PlayStation, Xbox", "duracao": "30 a 40 h" if not en else "30 to 40 h",
             "por_que": "Mapa enorme para explorar e chefes difíceis na medida." if not en else "A huge map to explore and fair, tough bosses."},
            {"titulo": "Fullmetal Alchemist: Brotherhood", "tipo": "anime", "ano": 2009, "generos": ["aventura", "fantasia"] if not en else ["adventure", "fantasy"],
             "duracao": "64 episódios" if not en else "64 episodes",
             "por_que": "Começa leve e vira uma história fechada sobre escolhas e consequências." if not en else "Starts light and becomes a complete story about choices and consequences."}]
        return {"tipo": "recomendacoes", "titulo": "Para ver e jogar no fim de semana" if not en else "For the weekend",
                "dados": {"itens": itens}}
    if tipo == "desenho":
        r = (lambda pt_, en_: en_ if en else pt_)
        return {"tipo": "desenho", "titulo": r("Sala de estar, 5 × 4 m", "Living room, 5 × 4 m"), "dados": {
            "largura": 5, "altura": 4, "unidade": "m", "formas": [
                {"tipo": "retangulo", "x": 0.7, "y": 1.25, "largura": 2.6, "altura": 1.7, "cor": "amarelo", "preenchido": True},
                {"tipo": "retangulo", "x": 0.4, "y": 0.25, "largura": 2.2, "altura": 0.9, "cor": "cinza", "preenchido": True, "rotulo": r("Sofá", "Sofa")},
                {"tipo": "retangulo", "x": 1.1, "y": 1.75, "largura": 1.0, "altura": 0.55, "cor": "marrom", "preenchido": True, "rotulo": r("Mesa", "Table")},
                {"tipo": "circulo", "x": 3.9, "y": 1.1, "raio": 0.45, "cor": "verde", "preenchido": True, "rotulo": r("Poltrona", "Armchair")},
                {"tipo": "retangulo", "x": 0.9, "y": 3.55, "largura": 1.8, "altura": 0.4, "cor": "preto", "preenchido": True, "rotulo": "TV"},
                {"tipo": "linha", "x1": 1.5, "y1": 0, "x2": 3.5, "y2": 0, "cor": "azul", "rotulo": r("Janela", "Window")},
                {"tipo": "linha", "x1": 5, "y1": 2.8, "x2": 5, "y2": 3.7, "cor": "laranja"},
                {"tipo": "seta", "x1": 4.85, "y1": 3.25, "x2": 4.1, "y2": 3.25, "cor": "laranja", "rotulo": r("Entrada", "Entrance")},
                {"tipo": "cota", "x1": 0, "y1": 4, "x2": 5, "y2": 4, "deslocamento": 0.3},
                {"tipo": "cota", "x1": 0, "y1": 0, "x2": 0, "y2": 4, "deslocamento": 0.3}],
            "legenda": [{"cor": "amarelo", "rotulo": r("Tapete", "Rug")}, {"cor": "azul", "rotulo": r("Janela", "Window")},
                        {"cor": "laranja", "rotulo": r("Porta", "Door")}]}}
    if tipo == "grafico":
        forma = "pizza" if re.search(r"pizza|\bpie\b", s) else "linhas" if re.search(r"\blinhas?\b|\blines?\b", s) else "barras"
        if forma == "pizza":
            return {"tipo": "grafico", "titulo": "Para onde foi o gasto do mês" if not en else "Where this month's spending went",
                    "dados": {"tipo_grafico": "pizza", "unidade": "US$",
                              "rotulos": ["Chat", "Code", "Fluxos" if not en else "Workflows", "Rotinas" if not en else "Routines"],
                              "series": [{"nome": "Gasto" if not en else "Spending", "valores": [6.4, 9.1, 2.3, 0.8]}]}}
        meses = ["jan", "fev", "mar", "abr", "mai", "jun"] if not en else ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        return {"tipo": "grafico", "titulo": "Gasto com a API por mês" if not en else "API spending per month",
                "dados": {"tipo_grafico": forma, "unidade": "US$", "rotulos": meses,
                          "series": [{"nome": "Chat", "valores": [3.2, 4.1, 3.8, 5.6, 4.9, 6.4]},
                                     {"nome": "Code", "valores": [5.0, 6.3, 8.7, 7.9, 10.2, 9.1]}]}}
    if tipo == "comparacao":
        if en:
            linhas = [("Cost", ["Cheapest", "Middle", "Most expensive"], 0),
                      ("Speed", ["Fastest", "Fast", "Slower"], 0),
                      ("Hard tasks", ["Simple ones", "Most of them", "The hardest"], 2),
                      ("Good for", ["Quick questions", "Everyday work", "Big projects"], None)]
            titulo = "Which model to use"
        else:
            linhas = [("Custo", ["Mais barato", "Médio", "Mais caro"], 0),
                      ("Velocidade", ["Mais rápido", "Rápido", "Mais lento"], 0),
                      ("Tarefas difíceis", ["As simples", "A maioria", "As mais difíceis"], 2),
                      ("Bom para", ["Dúvidas rápidas", "O dia a dia", "Projetos grandes"], None)]
            titulo = "Qual modelo usar"
        return {"tipo": "comparacao", "titulo": titulo, "dados": {
            "colunas": ["Haiku 5.5", "Sonnet 5.5", "Opus 5.5"],
            "linhas": [{"criterio": c, "valores": v, **({"melhor": m} if m is not None else {})} for c, v, m in linhas]}}
    if tipo == "linha_do_tempo":
        eventos = [("1961", "Kennedy anuncia a meta de ir à Lua" if not en else "Kennedy sets the goal of reaching the Moon"),
                   ("1968", "Apollo 8 dá a volta na Lua" if not en else "Apollo 8 orbits the Moon"),
                   ("1969", "Apollo 11: primeiros passos na Lua" if not en else "Apollo 11: first steps on the Moon"),
                   ("1970", "Apollo 13 volta depois de uma explosão" if not en else "Apollo 13 returns after an explosion"),
                   ("1972", "Apollo 17, a última missão tripulada" if not en else "Apollo 17, the last crewed mission")]
        return {"tipo": "linha_do_tempo", "titulo": "Programa Apollo" if not en else "The Apollo program",
                "dados": {"eventos": [{"data": d, "titulo": ti} for d, ti in eventos]}}
    itens = (["Passaporte e documentos", "Carregador e adaptador de tomada", "Remédios de uso diário",
              "Reserva do hotel impressa", "Seguro viagem"] if not en else
             ["Passport and documents", "Charger and plug adapter", "Daily medicines", "Printed hotel booking",
              "Travel insurance"])
    return {"tipo": "checklist", "titulo": "Antes de viajar" if not en else "Before the trip",
            "dados": {"itens": [{"texto": x, "feito": i < 2} for i, x in enumerate(itens)]}}
