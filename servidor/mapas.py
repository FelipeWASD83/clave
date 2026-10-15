"""Mapas dos widgets: endereço vira coordenada (Nominatim) e os quadradinhos do mapa (tiles) vêm do OpenStreetMap.

Os dois serviços são gratuitos e têm regras de uso, seguidas aqui:
- o User-Agent diz quem pede (Clave, a versão e o repositório);
- no máximo uma busca de endereço por segundo, no app inteiro (uma trava global);
- o que já foi buscado fica em disco: endereços em <dados>/cache/geocode.json, tiles em <dados>/cache/tiles, cada
  tile pelo prazo que o servidor manda (Cache-Control/Expires) e nunca menos de 7 dias; vencido, ele é conferido de
  novo com ETag/Last-Modified antes de baixar outra vez;
- nada é baixado antes de alguém olhar: o mapa pede só os tiles que aparecem na tela.

O cache de tiles não cresce para sempre: sai o tile que ninguém abriu em 30 dias e, passando de MAX_CACHE_TILES, os
usados há mais tempo, mas nunca um baixado há menos de 7 dias (o mínimo da política). A faxina roda numa linha de
fundo no primeiro tile pedido depois que o app abre e, depois, a cada 6 horas. As funções de faxina daqui
(marcar_uso, podar_entradas, apagar_arquivos, apagar_sobras) servem também ao cache de imagens dos widgets.
"""
from __future__ import annotations

import email.utils
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import config
from i18n import idioma, t
from rotas import Erro, rota

NOMINATIM = "https://nominatim.openstreetmap.org/search"
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
ZOOM_MAX = 19
VALIDADE_MINIMA = 7 * 86400          # política de uso dos tiles do OpenStreetMap: guardar pelo menos 7 dias
MAX_TILE = 2 * 1024 * 1024
GEO_ACHADO_DIAS = 180                 # um endereço achado vale por meio ano no cache
GEO_NADA_SEGUNDOS = 86400             # "não achei" vale um dia (pode ter sido um erro de digitação corrigido depois)
GEO_MAX_ITENS = 5000


class SemConexao(Exception):
    """A busca de endereço não aconteceu (sem internet, serviço fora do ar ou recusou)."""


def user_agent() -> str:
    info = config.info_versao()
    repo = info.get("repositorio") or "FelipeWASD83/clave"
    return f"Clave/{info.get('versao', '0.0.0')} (+https://github.com/{repo})"


def _cache() -> Path:
    return config.DADOS / "cache"


def gravar(arq: Path, dados: bytes) -> None:
    """Grava inteiro ou nada (arquivo temporário e troca), para quem lê ao mesmo tempo nunca pegar metade."""
    arq.parent.mkdir(parents=True, exist_ok=True)
    tmp = arq.with_name(f"{arq.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        tmp.write_bytes(dados)
        os.replace(tmp, arq)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise


_gravar = gravar


# ======================= faxina dos caches =======================

USO_MARCADO_A_CADA = 86400            # o uso de um arquivo do cache é anotado no máximo uma vez por dia
SEM_USO_MAXIMO = 30 * 86400           # 30 dias sem ninguém abrir: sai do cache
MAX_CACHE_TILES = 300 * 1024 * 1024
INTERVALO_PODA = 6 * 3600


def marcar_uso(arq: Path) -> None:
    """Anota que o item do cache foi usado agora (o horário do arquivo de dados dele), para a faxina saber o que
    ninguém abre há tempo. O Windows não atualiza o horário de acesso, por isso é o de modificação."""
    try:
        if time.time() - arq.stat().st_mtime > USO_MARCADO_A_CADA:
            os.utime(arq)
    except OSError:
        pass


def podar_entradas(entradas: list[dict], *, agora: float, sem_uso: float, limite: int, apagar) -> int:
    """Cada entrada é {"uso": horário do último uso, "tamanho": bytes, "protegida": bool, ...}. Apaga (apagar(entrada)
    devolve se conseguiu) as sem uso há mais de sem_uso segundos e, se o total ainda passar de limite bytes, as usadas
    há mais tempo, até caber. Uma protegida nunca é apagada. Devolve quantas apagou."""
    apagadas, restantes = 0, []
    for e in entradas:
        if not e.get("protegida") and agora - e["uso"] > sem_uso and apagar(e):
            apagadas += 1
        else:
            restantes.append(e)
    total = sum(e["tamanho"] for e in restantes)
    if total > limite:
        for e in sorted((e for e in restantes if not e.get("protegida")), key=lambda e: e["uso"]):
            if total <= limite:
                break
            if apagar(e):
                total -= e["tamanho"]
                apagadas += 1
    return apagadas


def apagar_arquivos(*arquivos: Path) -> bool:
    ok = True
    for arq in arquivos:
        try:
            arq.unlink(missing_ok=True)
        except OSError:
            ok = False
    return ok


def apagar_sobras(pasta: Path, extensao: str, agora: float, recursivo: bool = False) -> None:
    """Restos que nenhuma entrada controla: temporário de gravação que ficou para trás (mais de 1 hora) e arquivo de
    dados (extensao, como ".png") sem o .json ao lado (mais de 1 dia). Com recursivo, também as pastas vazias que não
    mudam há 1 hora (as recentes podem estar recebendo um arquivo agora)."""
    busca = pasta.rglob if recursivo else pasta.glob
    for arq in busca("*.tmp"):
        try:
            if agora - arq.stat().st_mtime > 3600:
                arq.unlink()
        except OSError:
            pass
    for arq in busca(f"*{extensao}"):
        try:
            if not arq.with_suffix(".json").exists() and agora - arq.stat().st_mtime > 86400:
                arq.unlink()
        except OSError:
            pass
    if recursivo:
        for sub in sorted((d for d in pasta.rglob("*") if d.is_dir()), key=lambda d: len(d.parts), reverse=True):
            try:
                if agora - sub.stat().st_mtime > 3600 and not any(sub.iterdir()):
                    sub.rmdir()
            except OSError:
                pass


# ======================= endereço → coordenada =======================

_trava_busca = threading.Lock()       # uma busca por vez no app inteiro
_trava_arquivo = threading.Lock()
_ultima = {"em": None}                # relógio (monotônico) do fim da última busca


def _agora() -> float:
    return time.monotonic()


def _esperar(segundos: float) -> None:
    time.sleep(segundos)


def _chave(endereco: str) -> str:
    return " ".join(str(endereco).lower().split())


def _ler_cache_geo() -> dict:
    try:
        dados = json.loads((_cache() / "geocode.json").read_text(encoding="utf-8"))
        return dados if isinstance(dados, dict) else {}
    except (OSError, ValueError):
        return {}


def _do_cache(chave: str):
    """O que o cache sabe: dict com lat/lon, {} quando "não achei" ainda vale, None quando não sabe."""
    with _trava_arquivo:
        item = _ler_cache_geo().get(chave)
    if not isinstance(item, dict):
        return None
    idade = time.time() - float(item.get("em") or 0)
    if item.get("nada"):
        return {} if idade < GEO_NADA_SEGUNDOS else None
    if idade < GEO_ACHADO_DIAS * 86400 and "lat" in item and "lon" in item:
        return {"lat": item["lat"], "lon": item["lon"], "nome": item.get("nome", "")}
    return None


def _guardar_geo(chave: str, valor: dict | None) -> None:
    with _trava_arquivo:
        dados = _ler_cache_geo()
        dados[chave] = {**valor, "em": time.time()} if valor else {"nada": True, "em": time.time()}
        if len(dados) > GEO_MAX_ITENS:  # os mais antigos saem
            for k in sorted(dados, key=lambda k: float((dados[k] or {}).get("em") or 0))[:len(dados) - GEO_MAX_ITENS]:
                dados.pop(k, None)
        try:
            _gravar(_cache() / "geocode.json", json.dumps(dados, ensure_ascii=False).encode("utf-8"))
        except OSError:
            pass


def _buscar(endereco: str) -> dict | None:
    q = urllib.parse.urlencode({"q": endereco, "format": "jsonv2", "limit": 1,
                                "accept-language": "en" if idioma() == "en" else "pt-BR"})
    req = urllib.request.Request(f"{NOMINATIM}?{q}", headers={"User-Agent": user_agent(), "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            lista = json.loads(r.read(2 * 1024 * 1024).decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SemConexao(t("o serviço de endereços respondeu com o erro {codigo}", codigo=e.code)) from e
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        raise SemConexao(t("sem conexão com o serviço de endereços")) from e
    except ValueError as e:
        raise SemConexao(t("o serviço de endereços mandou uma resposta que não deu para ler")) from e
    if not isinstance(lista, list) or not lista or not isinstance(lista[0], dict):
        return None
    try:
        return {"lat": round(float(lista[0]["lat"]), 6), "lon": round(float(lista[0]["lon"]), 6),
                "nome": str(lista[0].get("display_name") or "")[:300]}
    except (KeyError, TypeError, ValueError):
        return None


def geocodificar(endereco: str) -> dict | None:
    """{lat, lon, nome} do endereço, ou None quando o serviço não achou. SemConexao quando a busca não aconteceu.
    Respeita o limite de uma busca por segundo no app inteiro e guarda o resultado em <dados>/cache/geocode.json."""
    chave = _chave(endereco)
    if not chave:
        return None
    achado = _do_cache(chave)
    if achado is not None:
        return achado or None
    with _trava_busca:
        achado = _do_cache(chave)  # outra thread pode ter buscado enquanto esta esperava a vez
        if achado is not None:
            return achado or None
        if _ultima["em"] is not None:
            falta = 1.0 - (_agora() - _ultima["em"])
            if falta > 0:
                _esperar(falta)
        try:
            achado = _buscar(" ".join(str(endereco).split()))
        finally:
            _ultima["em"] = _agora()
    _guardar_geo(chave, achado)
    return achado


# ======================= tiles do mapa =======================

_sem_tiles = threading.BoundedSemaphore(2)   # no máximo 2 downloads de tile ao mesmo tempo
_travas_tile: dict[str, threading.Lock] = {}
_trava_travas = threading.Lock()


def _trava_do_tile(chave: str) -> threading.Lock:
    with _trava_travas:
        if len(_travas_tile) > 500:
            for k in [k for k, v in _travas_tile.items() if not v.locked()]:
                _travas_tile.pop(k, None)
        return _travas_tile.setdefault(chave, threading.Lock())


def _inteiro(valor: str, nome: str) -> int:
    s = str(valor)
    if nome == "y" and s.endswith(".png"):
        s = s[:-4]
    if not re.fullmatch(r"\d{1,7}", s):
        raise Erro(400, t("Tile inválido: {nome} precisa ser um número inteiro.", nome=nome))
    return int(s)


def validar_tile(z, x, y) -> tuple[int, int, int]:
    z, x, y = _inteiro(z, "z"), _inteiro(x, "x"), _inteiro(y, "y")
    if not 0 <= z <= ZOOM_MAX:
        raise Erro(400, t("Tile inválido: o zoom vai de 0 a {maximo}.", maximo=ZOOM_MAX))
    n = 2 ** z
    if not (0 <= x < n and 0 <= y < n):
        raise Erro(400, t("Tile inválido: neste zoom, x e y vão de 0 a {maximo}.", maximo=n - 1))
    return z, x, y


def _validade(cab) -> float:
    """Por quanto tempo (em segundos) o tile pode ser usado sem conferir: o que o servidor mandou, nunca menos de 7
    dias."""
    segundos = 0.0
    cc = str(cab.get("Cache-Control") or "")
    m = re.search(r"(?:^|[,\s])max-age\s*=\s*(\d+)", cc)
    if m:
        segundos = float(m.group(1))
    elif cab.get("Expires"):
        try:
            quando = email.utils.parsedate_to_datetime(str(cab.get("Expires")))
            segundos = quando.timestamp() - time.time()
        except (TypeError, ValueError, IndexError):
            segundos = 0.0
    return max(segundos, float(VALIDADE_MINIMA))


def _arquivos_tile(z: int, x: int, y: int) -> tuple[Path, Path]:
    base = _cache() / "tiles" / str(z) / str(x)
    return base / f"{y}.png", base / f"{y}.json"


def _ler_meta(arq: Path) -> dict | None:
    try:
        m = json.loads(arq.read_text(encoding="utf-8"))
        return m if isinstance(m, dict) else None
    except (OSError, ValueError):
        return None


def _salvar_meta(arq: Path, meta: dict) -> None:
    try:
        _gravar(arq, json.dumps(meta).encode("utf-8"))
    except OSError:
        pass


def _meta_nova(cab, antes: dict | None, tipo: str) -> dict:
    antes = antes or {}
    return {"expira": time.time() + _validade(cab), "baixado_em": time.time(), "tipo": tipo,
            "etag": cab.get("ETag") or antes.get("etag") or "",
            "modificado": cab.get("Last-Modified") or antes.get("modificado") or ""}


def _restante(meta: dict) -> int:
    return int(max(300, min(VALIDADE_MINIMA, float(meta.get("expira") or 0) - time.time())))


def _ler_guardado(arq_img: Path, meta: dict | None) -> bytes | None:
    if not meta:
        return None
    try:
        return arq_img.read_bytes()
    except OSError:  # não existe, ou a faxina levou entre a leitura do .json e a da imagem
        return None


def obter_tile(z, x, y) -> tuple[bytes, str, int]:
    """(bytes da imagem, Content-Type, segundos que a tela pode guardar). Erro(502) quando não tem nem no disco nem
    na internet."""
    z, x, y = validar_tile(z, x, y)
    _talvez_podar()
    arq_img, arq_meta = _arquivos_tile(z, x, y)
    with _trava_do_tile(f"{z}/{x}/{y}"):
        meta = _ler_meta(arq_meta)
        guardado = _ler_guardado(arq_img, meta)
        if guardado is not None and float(meta.get("expira") or 0) > time.time():
            marcar_uso(arq_meta)
            return guardado, meta.get("tipo") or "image/png", _restante(meta)
        cab = {"User-Agent": user_agent(), "Accept": "image/png,image/*;q=0.8"}
        if guardado is not None:  # vencido: pergunta se mudou antes de baixar de novo
            if meta.get("etag"):
                cab["If-None-Match"] = meta["etag"]
            if meta.get("modificado"):
                cab["If-Modified-Since"] = meta["modificado"]
        req = urllib.request.Request(TILE_URL.format(z=z, x=x, y=y), headers=cab)
        try:
            with _sem_tiles:
                with urllib.request.urlopen(req, timeout=20) as r:
                    status = getattr(r, "status", 200)
                    cab_resp = r.headers
                    corpo = r.read(MAX_TILE + 1) if status != 304 else b""
        except urllib.error.HTTPError as e:
            status, cab_resp, corpo = e.code, e.headers, b""
        except (urllib.error.URLError, OSError, TimeoutError):
            status, cab_resp, corpo = 0, {}, b""

        if status == 304 and guardado is not None:
            meta = _meta_nova(cab_resp or {}, meta, meta.get("tipo") or "image/png")
            _salvar_meta(arq_meta, meta)
            return guardado, meta["tipo"], _restante(meta)
        tipo = str((cab_resp or {}).get("Content-Type") or "").split(";")[0].strip().lower()
        if status == 200 and corpo and len(corpo) <= MAX_TILE and tipo.startswith("image/") and "svg" not in tipo:
            meta = _meta_nova(cab_resp, meta, tipo)
            try:
                _gravar(arq_img, corpo)
                _salvar_meta(arq_meta, meta)
            except OSError:
                pass
            return corpo, tipo, _restante(meta)
        if guardado is not None:  # a internet falhou: o tile velho é melhor que nenhum
            marcar_uso(arq_meta)
            return guardado, meta.get("tipo") or "image/png", 300
        if status:
            raise Erro(502, t("O OpenStreetMap não mandou este pedaço do mapa (erro {codigo}).", codigo=status))
        raise Erro(502, t("Não deu para baixar o mapa agora. Confira a internet."))


def podar_tiles(agora: float | None = None) -> int:
    """Apaga os tiles sem uso há 30 dias e, se o cache ainda passar de MAX_CACHE_TILES, os usados há mais tempo; um
    tile baixado (ou conferido) há menos de 7 dias nunca sai, pela política do OpenStreetMap. Um tile que está sendo
    servido agora (com a trava pega) fica para a próxima faxina. Devolve quantos apagou."""
    agora = agora or time.time()
    base = _cache() / "tiles"
    if not base.is_dir():
        return 0
    entradas = []
    for arq_meta in base.glob("*/*/*.json"):
        arq_img = arq_meta.with_suffix(".png")
        try:
            uso = arq_meta.stat().st_mtime
            tamanho = arq_meta.stat().st_size + (arq_img.stat().st_size if arq_img.is_file() else 0)
        except OSError:
            continue
        meta = _ler_meta(arq_meta) or {}
        try:
            baixado = float(meta.get("baixado_em") or 0)
        except (TypeError, ValueError):
            baixado = 0.0
        entradas.append({"uso": uso, "tamanho": tamanho, "protegida": agora - baixado < VALIDADE_MINIMA,
                         "chave": f"{arq_meta.parent.parent.name}/{arq_meta.parent.name}/{arq_meta.stem}",
                         "arquivos": (arq_img, arq_meta)})

    def apagar(e) -> bool:
        trava = _trava_do_tile(e["chave"])
        if not trava.acquire(blocking=False):
            return False
        try:
            return apagar_arquivos(*e["arquivos"])
        finally:
            trava.release()

    apagados = podar_entradas(entradas, agora=agora, sem_uso=SEM_USO_MAXIMO, limite=MAX_CACHE_TILES, apagar=apagar)
    apagar_sobras(base, ".png", agora, recursivo=True)
    return apagados


_poda = {"em": 0.0}
_trava_poda = threading.Lock()


def _talvez_podar() -> None:
    agora = time.time()
    with _trava_poda:
        if agora - _poda["em"] < INTERVALO_PODA:
            return
        _poda["em"] = agora

    def podar():
        try:
            podar_tiles()
        except Exception:  # faxina é melhor esforço: nunca atrapalha o mapa
            pass
    threading.Thread(target=podar, daemon=True, name="poda-tiles").start()


@rota("GET", "/api/mapa/tile/<z>/<x>/<y>")
def r_tile(h, z, x, y):
    dados, tipo, segundos = obter_tile(z, x, y)
    h._bytes(dados, tipo, cab={"Cache-Control": f"private, max-age={segundos}", "X-Content-Type-Options": "nosniff"})
