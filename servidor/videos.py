"""Os vídeos das lições (por exemplo, como pegar a chave da API), em português e em inglês.

Eles não vêm dentro do app: cada MP4 tem vários MB, e o botão Atualizar baixaria todos a cada versão. Ficam na
release "videos" do repositório (marcada como pré-lançamento, para o Atualizar nunca confundir com versão) e são
baixados na primeira vez que alguém dá play, para dados/videos. Na cópia de desenvolvimento, o arquivo que o
subprojeto video/ gerou (video/saida/) vale antes de tudo: dá para testar antes de publicar.
"""
from __future__ import annotations

import os
import re
import urllib.error
import urllib.request
from pathlib import Path

import config
from i18n import t

TAG = "videos"
LIMITE = 80 * 1024 * 1024
_ID = re.compile(r"[a-z0-9-]{1,60}")


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


def baixar(vid: str, lingua: str | None) -> Path:
    """Baixa da release (uma vez) e devolve o arquivo; ValueError com o motivo quando não dá."""
    pronto = local(vid, lingua)
    if pronto:
        return pronto
    destino = pasta_cache() / nome_arquivo(vid, lingua)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".baixando")
    req = urllib.request.Request(url(vid, lingua), headers={"User-Agent": f"Clave/{config.VERSAO}",
                                                            "Accept": "application/octet-stream"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
            total = 0
            while True:
                pedaco = r.read(1024 * 256)
                if not pedaco:
                    break
                total += len(pedaco)
                if total > LIMITE:
                    raise ValueError(t("O vídeo é maior do que o esperado; o download parou."))
                f.write(pedaco)
        with open(tmp, "rb") as f:
            if b"ftyp" not in f.read(64):
                raise ValueError(t("O arquivo baixado não é um vídeo."))
        os.replace(tmp, destino)
        return destino
    except urllib.error.HTTPError as e:
        raise ValueError(t("Este vídeo ainda não está no GitHub ({codigo}).", codigo=e.code))
    except (urllib.error.URLError, OSError) as e:
        raise ValueError(t("Sem conexão para baixar o vídeo ({erro}).", erro=e))
    finally:
        tmp.unlink(missing_ok=True)
