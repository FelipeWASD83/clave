"""Atualização do Clave pelo repositório no GitHub.

1. `checar` pergunta ao GitHub qual é a versão mais nova (a release mais recente).
2. `baixar_e_preparar` baixa o pacote, confere e deixa pronto em dados/atualizacao.
3. O servidor fecha com o código 3; o `iniciar.py` chama `aplicar_pendente`, que
   guarda a versão atual (para voltar se der errado), troca os arquivos e sobe
   o servidor de novo. Os dados (dados/) e o ambiente Python (.venv/) nunca são tocados.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import config

GERENCIADOS = ["servidor", "app", "electron", "skills", "plugins", "agentes", "fluxos", "tutoriais",
               "modelo-de-pasta", "ferramentas", "versao.json",
               "package.json", "requirements.txt", "Clave.bat", "instalar.bat", "README.md", "CHANGELOG.md", "LICENSE"]
PASTA = config.DADOS / "atualizacao"
_CACHE = PASTA / "checagem.json"
_PRONTA = PASTA / "pronta.json"


class ErroAtualizacao(Exception):
    pass


def _versao_tupla(v: str) -> tuple:
    partes = []
    for p in (v or "0").lstrip("vV").split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        partes.append(int(num or 0))
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes[:3])


def mais_nova(a: str, b: str) -> bool:
    return _versao_tupla(a) > _versao_tupla(b)


def copia_de_desenvolvimento() -> bool:
    return (config.RAIZ / ".git").exists()


def _get_json(url: str, tempo=20):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                               "User-Agent": f"Clave/{config.VERSAO}",
                                               "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req, timeout=tempo) as r:
        return json.loads(r.read())


def checar(forcar: bool = False) -> dict:
    repo = config.info_versao().get("repositorio", "")
    atual = config.VERSAO
    base = {"atual": atual, "repositorio": repo, "dev": copia_de_desenvolvimento()}
    if not repo:
        return {**base, "erro": "Sem repositório configurado em versao.json."}
    if not forcar:
        try:
            cache = json.loads(_CACHE.read_text(encoding="utf-8"))
            if time.time() - cache.get("checado_em", 0) < 6 * 3600 and cache.get("atual") == atual:
                return cache
        except (OSError, ValueError):
            pass
    try:
        rel = _get_json(f"https://api.github.com/repos/{repo}/releases/latest")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {**base, "erro": "O repositório ainda não tem nenhuma versão publicada (ou é privado)."}
        return {**base, "erro": f"O GitHub respondeu {e.code}."}
    except (urllib.error.URLError, OSError, ValueError) as e:
        return {**base, "erro": f"Sem conexão com o GitHub ({e})."}
    versao = (rel.get("tag_name") or "").lstrip("vV")
    pacote = None
    for a in rel.get("assets") or []:
        if a.get("name", "").endswith(".zip"):
            pacote = {"url": a["browser_download_url"], "tamanho": a.get("size", 0), "digest": a.get("digest")}
            break
    if pacote is None:
        pacote = {"url": rel.get("zipball_url"), "tamanho": 0, "digest": None}
    info = {**base, "ultima": versao, "nova": mais_nova(versao, atual), "notas": rel.get("body") or "",
            "publicada_em": rel.get("published_at"), "pagina": rel.get("html_url"), "pacote": pacote,
            "checado_em": time.time()}
    PASTA.mkdir(parents=True, exist_ok=True)
    _CACHE.write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return info


def _baixar(url: str, destino: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": f"Clave/{config.VERSAO}",
                                               "Accept": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=120) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def _raiz_do_pacote(pasta: Path) -> Path:
    if (pasta / "versao.json").is_file():
        return pasta
    for d in pasta.iterdir():
        if d.is_dir() and (d / "versao.json").is_file():
            return d
    raise ErroAtualizacao("O pacote baixado não parece ser do Clave (falta versao.json).")


def baixar_e_preparar() -> dict:
    if copia_de_desenvolvimento():
        raise ErroAtualizacao("Esta é uma cópia de desenvolvimento (tem .git). Atualize com git pull.")
    info = checar(forcar=True)
    if info.get("erro"):
        raise ErroAtualizacao(info["erro"])
    if not info.get("nova"):
        raise ErroAtualizacao("Você já está na versão mais nova.")
    PASTA.mkdir(parents=True, exist_ok=True)
    zip_path = PASTA / "pacote.zip"
    novo = PASTA / "novo"
    shutil.rmtree(novo, ignore_errors=True)
    _baixar(info["pacote"]["url"], zip_path)
    digest = info["pacote"].get("digest") or ""
    if digest.startswith("sha256:"):
        h = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        if h != digest.split(":", 1)[1]:
            zip_path.unlink(missing_ok=True)
            raise ErroAtualizacao("O pacote baixado não confere com a assinatura do GitHub. Tente de novo.")
    with zipfile.ZipFile(zip_path) as z:
        for nome in z.namelist():
            alvo = (novo / nome).resolve()
            if not alvo.is_relative_to(novo.resolve()):
                raise ErroAtualizacao("Pacote com caminho inválido.")
        z.extractall(novo)
    raiz = _raiz_do_pacote(novo)
    v_pacote = json.loads((raiz / "versao.json").read_text(encoding="utf-8")).get("versao", "")
    if not (raiz / "servidor" / "servidor.py").is_file() or not (raiz / "app" / "index.html").is_file():
        raise ErroAtualizacao("Pacote incompleto.")
    if v_pacote and _versao_tupla(v_pacote) != _versao_tupla(info["ultima"]):
        raise ErroAtualizacao(f"O pacote diz versão {v_pacote}, mas a release é {info['ultima']}.")
    _PRONTA.write_text(json.dumps({"versao": info["ultima"], "pasta": str(raiz), "notas": info.get("notas", "")},
                                  ensure_ascii=False), encoding="utf-8")
    zip_path.unlink(missing_ok=True)
    return {"versao": info["ultima"]}


def pendente() -> dict | None:
    try:
        return json.loads(_PRONTA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _copiar(origem: Path, destino: Path) -> None:
    if origem.is_dir():
        shutil.copytree(origem, destino, dirs_exist_ok=False)
    else:
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, destino)


def aplicar_pendente(raiz_app: Path | None = None) -> dict | None:
    """Troca os arquivos pela versão baixada. Devolve info da troca, ou None se não havia nada."""
    p = pendente()
    if not p:
        return None
    raiz_app = raiz_app or config.RAIZ
    novo = Path(p["pasta"])
    anterior = PASTA / "anterior"
    shutil.rmtree(anterior, ignore_errors=True)
    anterior.mkdir(parents=True)
    req_antes = (raiz_app / "requirements.txt").read_bytes() if (raiz_app / "requirements.txt").exists() else b""
    try:
        for nome in GERENCIADOS:
            atual = raiz_app / nome
            if atual.exists():
                shutil.move(str(atual), str(anterior / nome))
        for nome in GERENCIADOS:
            if (novo / nome).exists():
                _copiar(novo / nome, raiz_app / nome)
    except Exception as e:
        reverter(raiz_app)
        _PRONTA.unlink(missing_ok=True)
        raise ErroAtualizacao(f"Não deu para trocar os arquivos ({e}); a versão anterior foi restaurada.")
    _PRONTA.unlink(missing_ok=True)
    shutil.rmtree(PASTA / "novo", ignore_errors=True)
    req_depois = (raiz_app / "requirements.txt").read_bytes() if (raiz_app / "requirements.txt").exists() else b""
    return {"versao": p["versao"], "dependencias_mudaram": req_antes != req_depois}


def reverter(raiz_app: Path | None = None) -> bool:
    raiz_app = raiz_app or config.RAIZ
    anterior = PASTA / "anterior"
    if not anterior.is_dir() or not any(anterior.iterdir()):
        return False
    for nome in GERENCIADOS:
        if (anterior / nome).exists():
            alvo = raiz_app / nome
            if alvo.is_dir():
                shutil.rmtree(alvo, ignore_errors=True)
            elif alvo.exists():
                alvo.unlink()
            shutil.move(str(anterior / nome), str(alvo))
    return True
