"""Renderiza os vídeos (Remotion, pelo Edge), normaliza o áudio e gera a capa de cada um.

    python ferramentas/videos.py                                  # todos, nos dois idiomas
    python ferramentas/videos.py chave-da-api                     # um vídeo, nos dois idiomas
    python ferramentas/videos.py por-que-o-clave --lingua pt-BR   # um vídeo, um idioma
    python ferramentas/videos.py --so-capas                       # só as capas

Saída:
    saida/<vídeo>.<lingua>.mp4  1920×1080, 30 fps, H.264 (yuv420p, faixa de TV), AAC a -16 LUFS (loudnorm em duas passadas), +faststart,
                                no máximo ~15 MB (o CRF sobe de 2 em 2 até caber)
    capas/<vídeo>.<lingua>.jpg  1280 px de largura, o quadro que o src/videos/<vídeo>.ts escolhe
    saida/por-que-o-clave.mp4   cópia do português (o nome do anexo da release v2.0.0, o link do README antes da 4.3)

Antes: npm run narrar (a voz), npm run sons (os efeitos) e, para os tutoriais, npm run telas (os prints do app).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "saida"
CAPAS = RAIZ / "capas"
REMOTION = RAIZ / "node_modules" / ".bin" / "remotion.cmd"

VIDEOS = {  # id do roteiro -> prefixo da composição (src/videos/*.ts)
    "por-que-o-clave": "PorQueOClave",
    "chave-da-api": "ChaveDaApi",
    "primeiros-passos": "PrimeirosPassos",
    "primeira-automacao": "PrimeiraAutomacao",
}
SUFIXO = {"pt-BR": "PtBR", "en": "En"}
LIMITE_MB = 15.0
CRF_INICIAL = 23


def rodar(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", **kw)
    if r.returncode != 0:
        sys.exit(f"falhou: {' '.join(map(str, cmd))}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r


def remotion(*args: str):
    # o remotion.cmd é um .cmd: no Windows ele precisa passar pelo cmd.exe
    return rodar(["cmd", "/c", str(REMOTION), *args])


def medir_volume(arq: Path) -> dict:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(arq), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    bloco = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr)
    if not bloco:
        sys.exit(f"não consegui medir o volume de {arq}:\n{r.stderr[-1500:]}")
    return json.loads(bloco[-1])


def finalizar(bruto: Path, destino: Path) -> tuple[int, float]:
    m = medir_volume(bruto)
    filtro = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    crf = CRF_INICIAL
    while True:
        rodar(["ffmpeg", "-y", "-v", "error", "-i", str(bruto), "-c:v", "libx264", "-preset", "slow", "-tune", "animation",
               "-crf", str(crf), "-vf", "scale=out_range=tv,format=yuv420p", "-color_range", "tv", "-r", "30", "-af", filtro, "-ar", "48000", "-c:a", "aac", "-b:a", "128k",
               "-movflags", "+faststart", str(destino)])
        mb = destino.stat().st_size / 1e6
        if mb <= LIMITE_MB or crf >= 35:
            return crf, mb
        crf += 2


def capa(video: str, lingua: str):
    CAPAS.mkdir(exist_ok=True)
    png = SAIDA / f"capa-{video}.{lingua}.png"
    remotion("still", "src/index.ts", f"{VIDEOS[video]}{SUFIXO[lingua]}Capa", str(png.relative_to(RAIZ)))
    jpg = CAPAS / f"{video}.{lingua}.jpg"
    rodar(["ffmpeg", "-y", "-v", "error", "-i", str(png), "-vf", "scale=1280:-2:flags=lanczos", "-q:v", "3", str(jpg)])
    png.unlink(missing_ok=True)
    print(f"   capa: capas/{jpg.name} ({jpg.stat().st_size // 1024} KB)", flush=True)


def video(video: str, lingua: str):
    comp = f"{VIDEOS[video]}{SUFIXO[lingua]}"
    bruto = SAIDA / f"bruto-{video}.{lingua}.mp4"
    destino = SAIDA / f"{video}.{lingua}.mp4"
    t0 = time.time()
    remotion("render", "src/index.ts", comp, str(bruto.relative_to(RAIZ)), "--codec", "h264", "--crf", "16", "--audio-bitrate", "320k")
    crf, mb = finalizar(bruto, destino)
    bruto.unlink(missing_ok=True)
    dur = float(rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(destino)]).stdout)
    print(f"ok {destino.name:36} {dur:5.1f} s  {mb:5.1f} MB  CRF {crf}  ({time.time() - t0:.0f} s)", flush=True)
    if video == "por-que-o-clave" and lingua == "pt-BR":
        shutil.copyfile(destino, SAIDA / "por-que-o-clave.mp4")


def main():
    args = sys.argv[1:]
    linguas = [args[args.index("--lingua") + 1]] if "--lingua" in args else list(SUFIXO)
    nomes = [a for a in args if not a.startswith("--") and a not in linguas] or list(VIDEOS)
    for n in nomes:
        if n not in VIDEOS:
            sys.exit(f"vídeo desconhecido: {n} (tem: {', '.join(VIDEOS)})")
    SAIDA.mkdir(exist_ok=True)
    for n in nomes:
        for L in linguas:
            if "--so-capas" not in args:
                video(n, L)
            capa(n, L)


if __name__ == "__main__":
    main()
