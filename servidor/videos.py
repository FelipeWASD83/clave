"""Os vídeos das lições (por exemplo, como pegar a chave da API), em português e em inglês.

Eles não vêm dentro do app: cada MP4 tem vários MB, e o botão Atualizar baixaria todos a cada versão. Ficam na
release "videos" do repositório (marcada como pré-lançamento, para o Atualizar nunca confundir com versão). Desde a
5.0, o app baixa sozinho, em segundo plano, os vídeos do idioma escolhido para dados/videos (baixar_todos), e a lição
já abre com o vídeo pronto; com isso desligado em Configurações, a lição baixa na primeira vez que alguém dá play.
Na cópia de desenvolvimento, o arquivo que o subprojeto video/ gerou (video/saida/) vale antes de tudo: dá para
testar antes de publicar.

Cada download de verdade aparece na aba Tarefas (tarefas.registrar) e pode ser parado por lá: o arquivo pela metade é
apagado, a tarefa termina "parada" e a lição oferece baixar de novo. Um download que termina sem todos os bytes que o
GitHub anunciou (conexão caída no meio) é erro, nunca um vídeo pronto.
"""
from __future__ import annotations

import http.client
import os
import re
import threading
import urllib.error
import urllib.request
from pathlib import Path

import config
from i18n import t

TAG = "videos"
LIMITE = 80 * 1024 * 1024
_ID = re.compile(r"[a-z0-9-]{1,60}")
_trava = threading.Lock()
_travas_arquivo: dict[str, threading.Lock] = {}
# nome do arquivo -> {"baixados", "total"} enquanto baixa, {"erro": texto} depois de falhar ou {"parado": True} depois
# que alguém parou pela aba Tarefas
_andamento: dict[str, dict] = {}
_rodando: set[str] = set()   # idiomas com baixar_todos em andamento (um por idioma)


class DownloadParado(ValueError):
    """Quem usa parou o download pela aba Tarefas."""


def _lingua(lingua: str | None) -> str:
    return "en" if lingua == "en" else "pt-BR"


def nome_arquivo(vid: str, lingua: str | None) -> str:
    if not _ID.fullmatch(vid or ""):
        raise ValueError(t("Vídeo inválido."))
    return f"{vid}.{_lingua(lingua)}.mp4"


def pasta_cache() -> Path:
    return config.DADOS / "videos"


def local(vid: str, lingua: str | None) -> Path | None:
    nome = nome_arquivo(vid, lingua)
    for arq in (config.RAIZ / "video" / "saida" / nome, pasta_cache() / nome):
        if arq.is_file() and arq.stat().st_size > 0:
            return arq
    return None


def url(vid: str, lingua: str | None) -> str:
    repo = config.info_versao().get("repositorio", "")
    return f"https://github.com/{repo}/releases/download/{TAG}/{nome_arquivo(vid, lingua)}"


def estado(vid: str, lingua: str | None) -> dict:
    """Para a lição: pronto, baixando (com o progresso de 0 a 1 quando o tamanho é conhecido), parado (alguém parou
    na aba Tarefas: a lição não recomeça sozinha) ou o erro da última vez."""
    nome = nome_arquivo(vid, lingua)
    if local(vid, lingua):
        return {"pronto": True}
    with _trava:
        a = dict(_andamento.get(nome) or {})
    if a.get("parado"):
        return {"pronto": False, "baixando": False, "parado": True}
    if a.get("erro"):
        return {"pronto": False, "baixando": False, "erro": a["erro"]}
    if a:
        total = a.get("total") or 0
        return {"pronto": False, "baixando": True,
                "progresso": round(min(a.get("baixados", 0) / total, 1.0), 3) if total else None}
    return {"pronto": False, "baixando": False}


def _trava_de(nome: str) -> threading.Lock:
    with _trava:
        return _travas_arquivo.setdefault(nome, threading.Lock())


def _titulo(vid: str, lingua: str | None) -> str:
    """O título da lição que usa este vídeo (para a aba Tarefas)."""
    try:
        import tutoriais
        for li in tutoriais.listar(_lingua(lingua)):
            if li.get("video") == vid:
                return li.get("titulo") or vid
    except Exception:  # sem a lista de lições, o id do vídeo já serve de título
        pass
    return vid


def _registrar(titulo: str, parar: threading.Event):
    """A tarefa na aba Tarefas, com o botão Parar ligado a este download. None sem o módulo de tarefas."""
    try:
        import tarefas
    except ModuleNotFoundError:
        return None
    try:
        return tarefas.registrar("download", t("Vídeo da lição \"{titulo}\"", titulo=titulo),
                                 detalhe=t("Baixando do GitHub"), parar=parar.set)
    except Exception:  # a aba Tarefas é um extra: o download segue sem ela
        return None


def _na_tarefa(tarefa, metodo: str, *args, **kw) -> None:
    if tarefa is None:
        return
    try:
        getattr(tarefa, metodo)(*args, **kw)
    except Exception:
        pass


def _motivo(e: BaseException) -> str:
    return str(e) or e.__class__.__name__


def _amigavel(e: Exception) -> ValueError:
    """Qualquer falha vira ValueError com um texto que a lição pode mostrar (a rota responde 502 com ele)."""
    if isinstance(e, ValueError):
        return e
    if isinstance(e, urllib.error.HTTPError):
        return ValueError(t("Este vídeo ainda não está no GitHub ({codigo}).", codigo=e.code))
    if isinstance(e, (urllib.error.URLError, TimeoutError, ConnectionError)):
        return ValueError(t("Sem conexão para baixar o vídeo ({erro}).", erro=_motivo(getattr(e, "reason", None) or e)))
    if isinstance(e, http.client.HTTPException):  # IncompleteRead, BadStatusLine...: a conexão caiu no meio
        return ValueError(t("A conexão caiu no meio do download do vídeo ({erro}); tente de novo.", erro=_motivo(e)))
    if isinstance(e, OSError):
        return ValueError(t("Sem conexão para baixar o vídeo ({erro}).", erro=_motivo(e)))
    return ValueError(t("Não deu para baixar o vídeo ({erro}).", erro=_motivo(e)))


def _baixar_arquivo(vid: str, lingua: str | None, nome: str, progresso, tarefa, parar: threading.Event) -> Path:
    destino = pasta_cache() / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".baixando")
    req = urllib.request.Request(url(vid, lingua), headers={"User-Agent": f"Clave/{config.VERSAO}",
                                                            "Accept": "application/octet-stream"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            try:
                total_esperado = int((getattr(r, "headers", None) or {}).get("Content-Length") or 0)
            except ValueError:
                total_esperado = 0
            if total_esperado > LIMITE:
                raise ValueError(t("O vídeo é maior do que o esperado; o download parou."))
            total = 0
            while True:
                if parar.is_set():
                    raise DownloadParado(t("O download foi parado."))
                pedaco = r.read(1024 * 256)
                if not pedaco:
                    break
                total += len(pedaco)
                if total > LIMITE:
                    raise ValueError(t("O vídeo é maior do que o esperado; o download parou."))
                f.write(pedaco)
                with _trava:
                    _andamento[nome] = {"baixados": total, "total": total_esperado}
                _na_tarefa(tarefa, "atualizar", progresso=(total / total_esperado) if total_esperado else None,
                           detalhe=f"{total / 1048576:.1f} MB"
                           + (f" / {total_esperado / 1048576:.1f} MB" if total_esperado else ""))
                if progresso:
                    try:
                        progresso(total, total_esperado)
                    except Exception:
                        pass
            if parar.is_set():
                raise DownloadParado(t("O download foi parado."))
            # a conexão pode fechar antes do fim sem erro nenhum: o tamanho anunciado é a prova de que veio tudo
            if total_esperado and total != total_esperado:
                raise ValueError(t("O download do vídeo parou no meio ({baixados} de {total} MB); tente de novo.",
                                   baixados=f"{total / 1048576:.1f}", total=f"{total_esperado / 1048576:.1f}"))
        with open(tmp, "rb") as f:
            if b"ftyp" not in f.read(64):
                raise ValueError(t("O arquivo baixado não é um vídeo."))
        os.replace(tmp, destino)
        return destino
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass


def baixar(vid: str, lingua: str | None, progresso=None, *, titulo: str | None = None,
           automatico: bool = False) -> Path:
    """Baixa da release (uma vez) e devolve o arquivo; ValueError com o motivo quando não dá (DownloadParado quando
    alguém parou na aba Tarefas). Duas chamadas ao mesmo tempo para o mesmo vídeo (a lição e o download em segundo
    plano) não brigam: a segunda espera a primeira. progresso(baixados, total) é chamado a cada pedaço, quando
    informado. automatico=True (o download em segundo plano) não recomeça um vídeo que alguém parou."""
    pronto = local(vid, lingua)
    if pronto:
        return pronto
    nome = nome_arquivo(vid, lingua)
    with _trava_de(nome):
        pronto = local(vid, lingua)
        if pronto:
            return pronto
        if automatico:
            with _trava:
                if (_andamento.get(nome) or {}).get("parado"):
                    raise DownloadParado(t("O download foi parado."))
        parar = threading.Event()
        tarefa = _registrar(titulo or _titulo(vid, lingua), parar)
        with _trava:
            _andamento[nome] = {"baixados": 0, "total": 0}
        try:
            destino = _baixar_arquivo(vid, lingua, nome, progresso, tarefa, parar)
        except DownloadParado:
            with _trava:
                _andamento[nome] = {"parado": True}
            _na_tarefa(tarefa, "terminar", "parada", t("Parado; dá para baixar de novo na lição"))
            raise
        except BaseException as e:  # tudo (até o inesperado) termina a tarefa e tira a lição do "Baixando"
            erro = _amigavel(e) if isinstance(e, Exception) else ValueError(_motivo(e))
            with _trava:
                _andamento[nome] = {"erro": str(erro)}
            _na_tarefa(tarefa, "terminar", "erro", str(erro))
            if erro is e or not isinstance(e, Exception):
                raise
            raise erro from e
        with _trava:
            _andamento.pop(nome, None)
        _na_tarefa(tarefa, "terminar", "concluida", t("Pronto para assistir na lição"))
        return destino


def faltando(lingua: str | None) -> list[tuple[str, str]]:
    """(id, título da lição) dos vídeos das lições deste idioma que ainda não estão no computador."""
    import tutoriais
    vistos, saida = set(), []
    for li in tutoriais.listar(_lingua(lingua)):
        vid = li.get("video") or ""
        if vid and vid not in vistos and _ID.fullmatch(vid):
            vistos.add(vid)
            if not local(vid, lingua):
                saida.append((vid, li.get("titulo") or vid))
    return saida


def baixar_todos(lingua: str | None = None, em_segundo_plano: bool = True) -> bool:
    """Baixa os vídeos que faltam do idioma do app, um de cada vez, cada um aparecendo na aba Tarefas. Não faz nada
    com a opção desligada, na demonstração ou quando esse idioma já está baixando (trocar de idioma no meio começa o
    do idioma novo ao lado). Devolve se começou."""
    cfg = config.carregar()
    if not cfg.get("baixar_videos", True) or os.environ.get("CLAVE_API_FALSA"):
        return False
    lingua = _lingua(lingua or cfg.get("idioma"))
    try:
        if not faltando(lingua):
            return False
    except Exception:
        return False
    with _trava:
        if lingua in _rodando:
            return False
        _rodando.add(lingua)

    def rodar():
        try:
            try:
                lista = faltando(lingua)
            except Exception:
                lista = []
            for vid, titulo in lista:
                try:
                    baixar(vid, lingua, titulo=titulo, automatico=True)
                except Exception:  # baixar já pôs o motivo na tarefa e no estado da lição; segue para o próximo
                    continue
        finally:
            with _trava:
                _rodando.discard(lingua)

    if em_segundo_plano:
        threading.Thread(target=rodar, daemon=True, name=f"videos-{lingua}").start()
    else:
        rodar()
    return True
