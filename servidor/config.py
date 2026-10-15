"""Caminhos, versão e configurações do Clave (guardadas em dados/config.json)."""
from __future__ import annotations

import copy
import json
import os
import threading
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = Path(os.environ.get("CLAVE_DADOS") or (RAIZ / "dados")).resolve()
APP = RAIZ / "app"
TUTORIAIS = RAIZ / "tutoriais"
MODELO_DE_PASTA = RAIZ / "modelo-de-pasta"
PORTA_PADRAO = int(os.environ.get("CLAVE_PORTA") or 8040)


def info_versao() -> dict:
    try:
        return json.loads((RAIZ / "versao.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"versao": "0.0.0", "repositorio": ""}


VERSAO = info_versao().get("versao", "0.0.0")

ESTILOS_PRONTOS = {
    "normal": {"nome": "Normal", "instrucoes": ""},
    "conciso": {
        "nome": "Conciso",
        "instrucoes": "Responda de forma curta e direta. Vá ao ponto, sem introdução nem resumo no fim. "
        "Use listas só quando ajudarem de verdade.",
    },
    "explicativo": {
        "nome": "Explicativo",
        "instrucoes": "Explique como para alguém que está aprendendo: defina termos técnicos na primeira vez, "
        "dê um exemplo concreto e diga o porquê de cada passo.",
    },
    "formal": {
        "nome": "Formal",
        "instrucoes": "Escreva em tom profissional e formal, com frases completas e organização clara, "
        "adequado para e-mail de trabalho ou documento.",
    },
}

PADRAO = {
    "configurado": False,
    # personalização
    "nome": "",
    "sobre_voce": "",
    "como_responder": "",
    "estilo": "normal",
    "estilos_proprios": [],
    "memoria_ligada": False,
    "titulos_automaticos": True,
    # modelos
    "modelo_chat": "claude-opus-5-5",
    "esforco_chat": "medium",
    "modelo_code": "claude-opus-5-5",
    "esforco_code": "high",
    "mostrar_raciocinio": True,
    "modelos_antigos": False,
    # recursos
    "busca_web": False,
    "cache_automatico": True,
    "compactacao": True,
    "compactar_em": 150000,
    "troca_se_recusar": True,
    # teto de gasto
    "teto_mensal_usd": 20.0,
    "dia_virada": 1,
    "ao_atingir": "bloquear",
    "teto_tarefa_code_usd": 2.0,
    "ajustes": {},
    "alertas_vistos": {},
    # modo Code
    "permissao_code": "perguntar",
    "pastas_recentes": [],
    "protegidos": [
        ".env", ".env.*", "*.pem", "*.key", "*.pfx", "id_rsa*", "id_ed25519*",
        ".ssh/**", ".aws/**", ".git/**",
    ],
    "carregar_claude_md": True,
    # GitHub
    "github_origem": "",
    "github_ferramentas": False,
    "github_escrita": False,
    # conectores MCP remotos: [{nome, url, ligado}] (o token, se houver, fica nos segredos)
    "conectores_mcp": [],
    # interface
    "tema": "sistema",
    "tamanho_letra": 16,
    "largura_chat": "media",
    "letra_resposta": "serifa",
    "enviar_com": "enter",
    "mostrar_custo": True,
    # atualizações
    "checar_atualizacoes": True,
    "ultima_checagem": "",
    "tutoriais_feitos": [],
    # conversas escondidas dos ajudantes (lições e editor de memória)
    "ajudantes": {},
    # regras de permissão do app inteiro, no formato do Claude Code: {"allow": [], "ask": [], "deny": []}
    "permissoes": {"allow": [], "ask": [], "deny": []},
    # fluxos (várias etapas em modelos diferentes): sempre pedem OK antes de rodar
    "fluxos_ligados": True,
    # plugins: {nome: {ligado, fonte, versao}}
    "plugins": {},
    # notificação do Windows quando uma resposta termina ou pede OK com a janela em segundo plano
    "notificacoes": True,
}

_trava = threading.Lock()
_cache: dict | None = None


def _arquivo() -> Path:
    return DADOS / "config.json"


def carregar() -> dict:
    global _cache
    with _trava:
        if _cache is None:
            dados = {}
            try:
                dados = json.loads(_arquivo().read_text(encoding="utf-8"))
            except (OSError, ValueError):
                dados = {}
            cfg = copy.deepcopy(PADRAO)
            cfg.update({k: v for k, v in dados.items() if k in PADRAO})
            _cache = cfg
        return copy.deepcopy(_cache)


def salvar(alteracoes: dict) -> dict:
    global _cache
    atual = carregar()
    for chave, valor in alteracoes.items():
        if chave in PADRAO:
            atual[chave] = valor
    with _trava:
        DADOS.mkdir(parents=True, exist_ok=True)
        tmp = _arquivo().with_suffix(".tmp")
        tmp.write_text(json.dumps(atual, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, _arquivo())
        _cache = copy.deepcopy(atual)
    return atual


def recarregar() -> None:
    global _cache
    with _trava:
        _cache = None


def estilos(cfg: dict) -> dict:
    todos = copy.deepcopy(ESTILOS_PRONTOS)
    for est in cfg.get("estilos_proprios") or []:
        if est.get("id") and est.get("nome"):
            todos[est["id"]] = {"nome": est["nome"], "instrucoes": est.get("instrucoes", ""), "proprio": True}
    return todos
