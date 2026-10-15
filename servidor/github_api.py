"""Cliente pequeno da API REST do GitHub.

O token vem do `gh` (quem já fez `gh auth login`) ou de um token pessoal colado
nas configurações (guardado com os outros segredos).
"""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

import config
import segredos
from i18n import t

API = "https://api.github.com"


class ErroGitHub(Exception):
    def __init__(self, mensagem: str, status: int = 0):
        super().__init__(mensagem)
        self.status = status


def token_do_gh() -> str | None:
    exe = shutil.which("gh")
    if not exe:
        return None
    try:
        r = subprocess.run([exe, "auth", "token"], capture_output=True, text=True, timeout=15,
                           creationflags=0x08000000 if sys.platform == "win32" else 0)
    except (OSError, subprocess.TimeoutExpired):
        return None
    t = (r.stdout or "").strip()
    return t if r.returncode == 0 and t else None


def gh_instalado() -> bool:
    return shutil.which("gh") is not None


def token() -> str | None:
    origem = config.carregar().get("github_origem")
    if origem == "gh":
        return token_do_gh()
    if origem == "token":
        return segredos.ler("github_token")
    return None


def pedir(metodo: str, caminho: str, params: dict | None = None, corpo: dict | None = None,
          aceitar: str = "application/vnd.github+json", tok: str | None = "auto", bruto=False, tempo=30):
    url = caminho if caminho.startswith("http") else API + caminho
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    cab = {"Accept": aceitar, "X-GitHub-Api-Version": "2022-11-28", "User-Agent": f"Clave/{config.VERSAO}"}
    tk = token() if tok == "auto" else tok
    if tk:
        cab["Authorization"] = f"Bearer {tk}"
    dados = None
    if corpo is not None:
        dados = json.dumps(corpo).encode("utf-8")
        cab["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=dados, headers=cab, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=tempo) as r:
            conteudo = r.read()
            if bruto:
                return conteudo
            return json.loads(conteudo) if conteudo else {}
    except urllib.error.HTTPError as e:
        msg = ""
        try:
            msg = json.loads(e.read()).get("message", "")
        except (ValueError, OSError):
            pass
        if e.code == 401:
            raise ErroGitHub(t("O GitHub recusou o login (token inválido ou vencido)."), 401)
        if e.code == 403 and "rate limit" in msg.lower():
            raise ErroGitHub(t("Limite de pedidos do GitHub atingido. Tente de novo daqui a pouco (com login no GitHub o limite é bem maior)."), 403)
        if e.code == 404:
            raise ErroGitHub(t("Não encontrado no GitHub (ou o repositório é privado e falta permissão)."), 404)
        raise ErroGitHub(t("GitHub respondeu {codigo}: {erro}", codigo=e.code, erro=msg or e.reason), e.code)
    except urllib.error.URLError as e:
        raise ErroGitHub(t("Sem conexão com o GitHub: {erro}", erro=e.reason))


def usuario() -> dict:
    return pedir("GET", "/user")


def repos(pagina=1) -> list[dict]:
    dados = pedir("GET", "/user/repos", {"per_page": 100, "page": pagina, "sort": "pushed",
                                         "affiliation": "owner,collaborator,organization_member"})
    return [{"nome": r["full_name"], "privado": r["private"], "descricao": r.get("description") or "",
             "ramo": r.get("default_branch"), "atualizado": r.get("pushed_at")} for r in dados]


def arvore(repo: str, ref: str | None = None) -> dict:
    if not ref:
        ref = pedir("GET", f"/repos/{repo}").get("default_branch", "main")
    dados = pedir("GET", f"/repos/{repo}/git/trees/{urllib.parse.quote(ref, safe='')}", {"recursive": 1})
    itens = [{"caminho": i["path"], "tipo": "pasta" if i["type"] == "tree" else "arquivo", "tamanho": i.get("size", 0)}
             for i in dados.get("tree", []) if i["type"] in ("tree", "blob")]
    return {"ref": ref, "itens": itens, "cortada": bool(dados.get("truncated"))}


def conteudo(repo: str, caminho: str, ref: str | None = None) -> dict:
    dados = pedir("GET", f"/repos/{repo}/contents/{urllib.parse.quote(caminho)}", {"ref": ref})
    if isinstance(dados, list):
        return {"tipo": "pasta", "itens": [{"nome": i["name"], "caminho": i["path"], "tipo": i["type"]} for i in dados]}
    if dados.get("encoding") == "base64":
        bruto = base64.b64decode(dados.get("content", ""))
    elif dados.get("download_url"):
        bruto = pedir("GET", dados["download_url"], bruto=True)
    else:
        bruto = b""
    return {"tipo": "arquivo", "caminho": dados.get("path", caminho), "bytes": bruto, "tamanho": dados.get("size", 0)}


def buscar_codigo(q: str) -> list[dict]:
    dados = pedir("GET", "/search/code", {"q": q, "per_page": 30})
    return [{"repo": i["repository"]["full_name"], "caminho": i["path"]} for i in dados.get("items", [])]


def issues(repo: str, estado="open", prs=False) -> list[dict]:
    if prs:
        dados = pedir("GET", f"/repos/{repo}/pulls", {"state": estado, "per_page": 30})
    else:
        dados = [i for i in pedir("GET", f"/repos/{repo}/issues", {"state": estado, "per_page": 50})
                 if "pull_request" not in i]
    return [{"numero": i["number"], "titulo": i["title"], "estado": i["state"], "autor": i["user"]["login"],
             "criado": i["created_at"]} for i in dados]


def issue(repo: str, numero: int) -> dict:
    i = pedir("GET", f"/repos/{repo}/issues/{numero}")
    coms = pedir("GET", f"/repos/{repo}/issues/{numero}/comments", {"per_page": 50})
    return {"numero": i["number"], "titulo": i["title"], "estado": i["state"], "autor": i["user"]["login"],
            "texto": i.get("body") or "", "comentarios": [{"autor": c["user"]["login"], "texto": c.get("body") or ""}
                                                          for c in coms], "e_pr": "pull_request" in i}


def pr_diff(repo: str, numero: int) -> str:
    return pedir("GET", f"/repos/{repo}/pulls/{numero}", aceitar="application/vnd.github.diff", bruto=True).decode(
        "utf-8", errors="replace")


def commits(repo: str, ref: str | None = None) -> list[dict]:
    dados = pedir("GET", f"/repos/{repo}/commits", {"sha": ref, "per_page": 20})
    return [{"sha": c["sha"][:7], "mensagem": c["commit"]["message"].splitlines()[0],
             "autor": c["commit"]["author"]["name"], "data": c["commit"]["author"]["date"]} for c in dados]


def criar_issue(repo: str, titulo: str, texto: str) -> dict:
    i = pedir("POST", f"/repos/{repo}/issues", corpo={"title": titulo, "body": texto})
    return {"numero": i["number"], "url": i["html_url"]}


def comentar(repo: str, numero: int, texto: str) -> dict:
    c = pedir("POST", f"/repos/{repo}/issues/{numero}/comments", corpo={"body": texto})
    return {"url": c["html_url"]}


def criar_pr(repo: str, titulo: str, texto: str, origem: str, destino: str) -> dict:
    p = pedir("POST", f"/repos/{repo}/pulls", corpo={"title": titulo, "body": texto, "head": origem, "base": destino})
    return {"numero": p["number"], "url": p["html_url"]}
