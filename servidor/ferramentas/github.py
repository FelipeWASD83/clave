"""Ferramentas do GitHub para o Claude. As de escrita sempre pedem o OK de quem usa."""
from __future__ import annotations

import json

import github_api as gh
from i18n import t


def _f(nome, descricao, props, obrig, risco):
    return {"def": {"name": nome, "description": descricao, "eager_input_streaming": True,
                    "input_schema": {"type": "object", "properties": props, "required": obrig}},
            "risco": risco}


_REPO = {"type": "string", "description": "Repositório no formato dono/nome."}

FERRAMENTAS = {
    "github_meus_repositorios": _f(
        "github_meus_repositorios", "Lista os repositórios do GitHub da pessoa (os mais recentes primeiro).",
        {}, [], "leitura"),
    "github_ver_pasta": _f(
        "github_ver_pasta", "Lista o conteúdo de uma pasta de um repositório do GitHub.",
        {"repo": _REPO, "caminho": {"type": "string", "description": "Pasta (vazio = raiz)."},
         "ref": {"type": "string", "description": "Ramo, tag ou commit (opcional)."}}, ["repo"], "leitura"),
    "github_ler_arquivo": _f(
        "github_ler_arquivo", "Lê um arquivo de um repositório do GitHub.",
        {"repo": _REPO, "caminho": {"type": "string"}, "ref": {"type": "string"}}, ["repo", "caminho"], "leitura"),
    "github_buscar_codigo": _f(
        "github_buscar_codigo", "Busca código no GitHub com a sintaxe de busca do GitHub "
        "(ex.: 'funcao repo:dono/nome' ou 'extension:py user:dono').",
        {"consulta": {"type": "string"}}, ["consulta"], "leitura"),
    "github_listar_issues": _f(
        "github_listar_issues", "Lista issues ou pull requests de um repositório.",
        {"repo": _REPO, "estado": {"type": "string", "enum": ["open", "closed", "all"]},
         "pull_requests": {"type": "boolean", "description": "true para listar PRs em vez de issues."}},
        ["repo"], "leitura"),
    "github_ler_issue": _f(
        "github_ler_issue", "Lê uma issue ou PR com os comentários; para PR pode trazer o diff.",
        {"repo": _REPO, "numero": {"type": "integer"}, "com_diff": {"type": "boolean"}},
        ["repo", "numero"], "leitura"),
    "github_commits": _f(
        "github_commits", "Lista os commits recentes de um repositório.",
        {"repo": _REPO, "ref": {"type": "string"}}, ["repo"], "leitura"),
    "github_criar_issue": _f(
        "github_criar_issue", "Cria uma issue. Sempre pede confirmação de quem usa antes.",
        {"repo": _REPO, "titulo": {"type": "string"}, "texto": {"type": "string"}}, ["repo", "titulo", "texto"],
        "github_escrita"),
    "github_comentar": _f(
        "github_comentar", "Comenta numa issue ou PR. Sempre pede confirmação de quem usa antes.",
        {"repo": _REPO, "numero": {"type": "integer"}, "texto": {"type": "string"}}, ["repo", "numero", "texto"],
        "github_escrita"),
    "github_criar_pr": _f(
        "github_criar_pr", "Abre um pull request de um ramo já enviado ao GitHub. Sempre pede confirmação antes.",
        {"repo": _REPO, "titulo": {"type": "string"}, "texto": {"type": "string"},
         "ramo_origem": {"type": "string"}, "ramo_destino": {"type": "string"}},
        ["repo", "titulo", "texto", "ramo_origem", "ramo_destino"], "github_escrita"),
}


def definicoes(escrita: bool) -> list[dict]:
    return [f["def"] for f in FERRAMENTAS.values() if escrita or f["risco"] == "leitura"]


def executar(nome: str, e: dict) -> str:
    try:
        if nome == "github_meus_repositorios":
            return json.dumps(gh.repos(), ensure_ascii=False, indent=1)
        if nome == "github_ver_pasta":
            r = gh.conteudo(e["repo"], e.get("caminho", ""), e.get("ref"))
            if r["tipo"] != "pasta":
                return t("Isso é um arquivo, não uma pasta. Use github_ler_arquivo.")
            return "\n".join((t("[pasta] ") if i["tipo"] == "dir" else "") + i["caminho"] for i in r["itens"])
        if nome == "github_ler_arquivo":
            r = gh.conteudo(e["repo"], e["caminho"], e.get("ref"))
            if r["tipo"] != "arquivo":
                return t("Isso é uma pasta. Use github_ver_pasta.")
            if b"\x00" in r["bytes"][:4096]:
                return t("{caminho} é um arquivo binário ({n} bytes).", caminho=r["caminho"], n=r["tamanho"])
            texto = r["bytes"].decode("utf-8", errors="replace")
            if len(texto) > 60_000:
                texto = texto[:60_000] + "\n" + t("[... arquivo cortado ...]")
            return texto
        if nome == "github_buscar_codigo":
            return json.dumps(gh.buscar_codigo(e["consulta"]), ensure_ascii=False, indent=1)
        if nome == "github_listar_issues":
            return json.dumps(gh.issues(e["repo"], e.get("estado") or "open", bool(e.get("pull_requests"))),
                              ensure_ascii=False, indent=1)
        if nome == "github_ler_issue":
            r = gh.issue(e["repo"], int(e["numero"]))
            texto = json.dumps(r, ensure_ascii=False, indent=1)
            if r.get("e_pr") and e.get("com_diff"):
                diff = gh.pr_diff(e["repo"], int(e["numero"]))
                texto += "\n\nDiff:\n" + (diff[:50_000] + ("\n" + t("[... diff cortado ...]") if len(diff) > 50_000 else ""))
            return texto
        if nome == "github_commits":
            return json.dumps(gh.commits(e["repo"], e.get("ref")), ensure_ascii=False, indent=1)
        if nome == "github_criar_issue":
            return json.dumps(gh.criar_issue(e["repo"], e["titulo"], e["texto"]), ensure_ascii=False)
        if nome == "github_comentar":
            return json.dumps(gh.comentar(e["repo"], int(e["numero"]), e["texto"]), ensure_ascii=False)
        if nome == "github_criar_pr":
            return json.dumps(gh.criar_pr(e["repo"], e["titulo"], e["texto"], e["ramo_origem"], e["ramo_destino"]),
                              ensure_ascii=False)
    except gh.ErroGitHub as erro:
        raise RuntimeError(str(erro))
    raise RuntimeError(t("Ferramenta desconhecida: {nome}", nome=nome))
