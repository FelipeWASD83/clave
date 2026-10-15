"""Fichas de lançamento dos modelos: o banner de modelo novo no início, os cartões "Modelos" de Preços e planos
e o aviso de modelo que apareceu na conta antes do Clave conhecer.

As fichas moram em servidor/lancamentos.json (dados, nos dois idiomas). Modelo novo da Anthropic: entrada em
modelos.MODELOS (preço e o que aceita) + ficha aqui com lancado_em; o banner aparece sozinho por 14 dias.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import date
from pathlib import Path

import config
import modelos
import segredos
from i18n import idioma

ARQUIVO = Path(__file__).resolve().with_name("lancamentos.json")
DIAS_DE_NOVIDADE = 14
_CACHE_CONTA = config.DADOS / "modelos_conta.json"
_trava = threading.Lock()


def fichas() -> dict:
    try:
        dados = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in dados.items() if not k.startswith("_")}


def _no_idioma(valor, lingua: str):
    if isinstance(valor, dict):
        return valor.get(lingua) or valor.get("pt-BR") or next(iter(valor.values()), "")
    return valor


def _preco(mid: str) -> dict:
    i = modelos.info(mid)
    return {"id": mid, "nome": i.get("nome") or mid, "entrada": i["entrada"], "saida": i["saida"],
            "cache_leitura": i["cache_leitura"]}


def ficha(mid: str, hoje: date | None = None) -> dict | None:
    f = fichas().get(mid)
    if not f or mid not in modelos.MODELOS:
        return None
    hoje = hoje or date.today()
    lingua = idioma()
    lancado = f.get("lancado_em")
    idade = (hoje - date.fromisoformat(lancado)).days if lancado else None
    anterior = f.get("anterior")
    return {
        **_preco(mid),
        "familia": f.get("familia") or "",
        "lancado_em": lancado,
        "novo": idade is not None and 0 <= idade < DIAS_DE_NOVIDADE,
        "etiquetas": _no_idioma(f.get("etiquetas") or {}, lingua) or [],
        "resumo": _no_idioma(f.get("resumo") or {}, lingua) or "",
        "novidades": _no_idioma(f.get("novidades") or {}, lingua) or [],
        "fonte": f.get("fonte") or "",
        "pagina": f.get("pagina") or "",
        "inteligencia": f.get("inteligencia"),
        "render": _render(f.get("familia") or ""),
        "anterior": _preco(anterior) if anterior and anterior in modelos.MODELOS else None,
    }


def _render(familia: str) -> str:
    """A imagem do topo do cartão de apresentação (gerada por ferramentas/gerar_renders.py)."""
    arq = ARQUIVO.parent.parent / "app" / "img" / "modelos" / f"render-{familia}.jpg"
    return f"img/modelos/{arq.name}" if familia and arq.is_file() else ""


def fonte_inteligencia() -> dict:
    """De onde vem a nota de inteligência dos cartões (a mesma régua para todos os modelos)."""
    try:
        bruto = json.loads(ARQUIVO.read_text(encoding="utf-8")).get("_inteligencia") or {}
    except (OSError, ValueError):
        bruto = {}
    return {"nota": _no_idioma(bruto.get("nota") or {}, idioma()) or "", "url": bruto.get("fonte") or ""}


def lista(hoje: date | None = None) -> list[dict]:
    """Os modelos atuais que têm ficha, na ordem do catálogo (Opus, Sonnet, Haiku, Fable)."""
    saida = []
    for m in modelos.lista_publica():
        f = ficha(m["id"], hoje)
        if f:
            saida.append(f)
    return saida


def novidades(cfg: dict, hoje: date | None = None) -> list[dict]:
    """Os modelos lançados há menos de 14 dias que a pessoa ainda não dispensou."""
    vistos = set(cfg.get("modelos_vistos") or [])
    return [f for f in lista(hoje) if f["novo"] and f["id"] not in vistos]


def desconhecidos(cfg: dict, forcar: bool = False) -> list[dict]:
    """Modelos que a conta já tem na API e o Clave ainda não conhece (o preço e a ficha vêm numa atualização).
    Consulta a API uma vez por dia, no máximo; a lista de modelos não gasta nada."""
    if os.environ.get("CLAVE_API_FALSA") or not segredos.existe("anthropic"):
        return []
    with _trava:
        cache = {}
        try:
            cache = json.loads(_CACHE_CONTA.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        if forcar or time.time() - cache.get("checado_em", 0) > 86400:
            try:
                import anthropic
                cliente = anthropic.Anthropic(api_key=segredos.ler("anthropic"), max_retries=1, timeout=15)
                ids = [{"id": m.id, "nome": m.display_name or m.id,
                        "criado_em": m.created_at.date().isoformat() if m.created_at else ""}
                       for m in cliente.models.list(limit=100)]
                cache = {"checado_em": time.time(), "modelos": ids}
                _CACHE_CONTA.parent.mkdir(parents=True, exist_ok=True)
                _CACHE_CONTA.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            except Exception:
                cache.setdefault("modelos", [])
    vistos = set(cfg.get("modelos_vistos") or [])
    return [m for m in cache.get("modelos", []) if m["id"] not in modelos.MODELOS and m["id"] not in vistos]
