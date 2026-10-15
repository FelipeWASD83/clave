"""Gera a narração dos vídeos com vozes neurais (edge-tts, a voz de leitura do Edge), em português e em inglês.

As falas ficam em roteiros/<vídeo>.json, uma por cena e por idioma. Cada fala vira
public/narracao/<vídeo>/<lingua>/<cena>.mp3, e o tempo de cada palavra vai para
public/narracao/<vídeo>/<lingua>/tempos.json: as cenas usam esse tempo para animar cada coisa na hora em que ela é dita.

Marcas: {nome} logo antes de uma palavra da fala (ex.: "{volte}Volte em cinco horas") vira tempos.json > marcas > nome,
o segundo em que a palavra começa. As cenas pedem quando(cena, "volte"), e o mesmo código serve aos dois idiomas.

Precisa de internet e do edge-tts num ambiente próprio (a primeira vez):
    python -m venv .venv
    .venv\\Scripts\\pip install edge-tts==7.3.1
Depois é só `npm run narrar` (este script se reabre no .venv sozinho).

    python ferramentas/narrar.py                       # todos os vídeos, os dois idiomas
    python ferramentas/narrar.py chave-da-api --lingua en
    python ferramentas/narrar.py --forcar              # refaz mesmo o que não mudou

Uma fala que não mudou (mesmo texto, voz e velocidade) não é pedida de novo. O português usa grafia de pronúncia para os
nomes em inglês ("Clód", "Ráicu", "A P I", "Guít Râb"); a tela mostra o nome certo.
"""
import asyncio
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VENV = RAIZ / ".venv" / "Scripts" / "python.exe"

try:
    import edge_tts
except ImportError:
    if VENV.exists() and Path(sys.executable).resolve() != VENV.resolve():
        sys.exit(subprocess.call([str(VENV), __file__, *sys.argv[1:]]))
    sys.exit("Falta o edge-tts. Rode: python -m venv .venv  e  .venv\\Scripts\\pip install edge-tts==7.3.1")

VOZES = {
    "pt-BR": ("pt-BR-ThalitaMultilingualNeural", "+6%"),
    "en": ("en-US-AvaMultilingualNeural", "+3%"),
}
MARCA = re.compile(r"\{([a-z0-9_]+)\}")


def normal(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    return re.sub(r"[^a-z0-9]", "", s)


def separar(texto: str) -> tuple[str, list[dict]]:
    """Tira as marcas do texto e devolve (texto limpo, palavras com as marcas que vêm antes de cada uma)."""
    palavras, pendentes, limpo = [], [], []
    for i, pedaco in enumerate(MARCA.split(texto)):
        if i % 2:
            pendentes.append(pedaco)
            continue
        limpo.append(pedaco)
        for w in pedaco.split():
            if not normal(w):
                continue
            palavras.append({"texto": w, "n": normal(w), "marcas": pendentes})
            pendentes = []
    if pendentes:
        raise ValueError(f"marca no fim da fala, sem palavra depois: {pendentes}")
    return re.sub(r"\s+", " ", "".join(limpo)).strip(), palavras


def alinhar(palavras: list[dict], limites: list[dict]) -> dict[int, int]:
    """Casa as palavras do texto com as palavras que a voz devolveu (a voz às vezes junta ou separa: "A P I" e "API")."""
    W = [p["n"] for p in palavras]
    B = [normal(b["texto"]) for b in limites]
    mapa: dict[int, int] = {}
    i = j = 0
    while i < len(W) and j < len(B):
        w, b = W[i], B[j]
        if not b:
            j += 1
            continue
        if w == b:
            mapa[i] = j
            i, j = i + 1, j + 1
            continue
        if w.startswith(b):  # a voz separou a palavra
            acc, k = b, j + 1
            while k < len(B) and len(acc) < len(w):
                acc += B[k]
                k += 1
            if acc == w:
                mapa[i] = j
                i, j = i + 1, k
                continue
        if b.startswith(w):  # a voz juntou palavras
            acc, k = w, i + 1
            while k < len(W) and len(acc) < len(b):
                acc += W[k]
                k += 1
            if acc == b:
                for x in range(i, k):
                    mapa[x] = j
                i, j = k, j + 1
                continue
        achou = False
        for soma in range(1, 6):  # ressincroniza um pouco à frente
            for di in range(soma + 1):
                dj = soma - di
                if i + di < len(W) and j + dj < len(B) and W[i + di] == B[j + dj]:
                    for x in range(i, i + di):
                        mapa[x] = j + dj
                    i, j = i + di, j + dj
                    achou = True
                    break
            if achou:
                break
        if not achou:
            i += 1
    return mapa


def duracao(arq: Path) -> float:
    saida = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                           capture_output=True, text=True, check=True).stdout
    return float(saida.strip())


async def narrar(video: str, lingua: str, cena: str, texto_marcado: str, pasta: Path, antigo: dict | None, forcar: bool) -> dict:
    voz, velocidade = VOZES[lingua]
    texto, palavras = separar(texto_marcado)
    assinatura = hashlib.sha1(f"{voz}|{velocidade}|{texto_marcado}".encode("utf-8")).hexdigest()[:16]
    arq = pasta / f"{cena}.mp3"
    if antigo and antigo.get("assinatura") == assinatura and arq.exists() and not forcar:
        return antigo
    for tentativa in range(4):  # o serviço às vezes devolve vazio: tenta de novo
        com = edge_tts.Communicate(texto, voz, rate=velocidade, boundary="WordBoundary")
        audio, limites = bytearray(), []
        try:
            async for pedaco in com.stream():
                if pedaco["type"] == "audio":
                    audio += pedaco["data"]
                elif pedaco["type"] == "WordBoundary":
                    # offset e duração vêm em unidades de 100 ns
                    limites.append({"t": round(pedaco["offset"] / 1e7, 3), "d": round(pedaco["duration"] / 1e7, 3),
                                    "texto": pedaco["text"]})
            break
        except edge_tts.exceptions.NoAudioReceived:
            if tentativa == 3:
                raise RuntimeError(f"{video}/{lingua}/{cena}: a voz não devolveu áudio para: {texto}")
            await asyncio.sleep(2 + tentativa * 3)
    arq.write_bytes(bytes(audio))
    mapa = alinhar(palavras, limites)
    marcas, faltam = {}, []
    for i, p in enumerate(palavras):
        for m in p["marcas"]:
            if i in mapa:
                marcas[m] = limites[mapa[i]]["t"]
            else:
                faltam.append(f"{m} ({p['texto']})")
    if faltam:
        ditas = " ".join(b["texto"] for b in limites)
        raise RuntimeError(f"{video}/{lingua}/{cena}: não achei na fala as marcas {faltam}. A voz disse: {ditas}")
    return {"id": cena, "arquivo": f"narracao/{video}/{lingua}/{cena}.mp3", "duracao": round(duracao(arq), 3),
            "texto": texto, "assinatura": assinatura, "palavras": limites, "marcas": marcas}


async def main():
    args = sys.argv[1:]
    forcar = "--forcar" in args
    linguas = [args[args.index("--lingua") + 1]] if "--lingua" in args else list(VOZES)
    nomes = [a for a in args if not a.startswith("--") and a not in linguas]
    roteiros = sorted((RAIZ / "roteiros").glob("*.json"))
    if nomes:
        roteiros = [r for r in roteiros if r.stem in nomes]
        if len(roteiros) != len(nomes):
            sys.exit(f"roteiro não encontrado: {nomes}")
    for rot in roteiros:
        dados = json.loads(rot.read_text(encoding="utf-8"))
        video = dados["id"]
        for lingua in linguas:
            voz, _ = VOZES[lingua]
            pasta = RAIZ / "public" / "narracao" / video / lingua
            pasta.mkdir(parents=True, exist_ok=True)
            destino = pasta / "tempos.json"
            antigos = {}
            if destino.exists():
                antigos = {c["id"]: c for c in json.loads(destino.read_text(encoding="utf-8")).get("cenas", [])}
            cenas = []
            for c in dados["cenas"]:
                cenas.append(await narrar(video, lingua, c["id"], c[lingua], pasta, antigos.get(c["id"]), forcar))
            destino.write_text(json.dumps({"video": video, "lingua": lingua, "voz": voz, "cenas": cenas},
                                          ensure_ascii=False, indent=1), encoding="utf-8")
            total = sum(c["duracao"] for c in cenas)
            print(f"ok {video:20} {lingua:5} {len(cenas)} cenas, {total:5.1f} s de fala  ({voz})", flush=True)


if __name__ == "__main__":
    os.chdir(RAIZ)
    asyncio.run(main())
