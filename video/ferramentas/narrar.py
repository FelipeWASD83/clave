"""Gera a narração do vídeo com uma voz neural em português (edge-tts, a voz de leitura do Edge).

Uma fala por cena, em public/narracao/<cena>.mp3, e o tempo de cada palavra em src/narracao.gerado.json:
as cenas usam esse tempo para animar cada coisa na hora em que ela é dita.

Precisa de internet e do edge-tts num ambiente próprio (a primeira vez):
    python -m venv .venv
    .venv\\Scripts\\pip install edge-tts==7.3.1
Depois é só `npm run narrar` (este script se reabre no .venv sozinho).

O texto falado tem grafia de pronúncia para os nomes em inglês ("Clód", "Ráicu", "A P I", "Guít Râb"); a tela mostra o
nome certo. Mudou uma fala? Rode de novo e renderize: as cenas se ajustam à duração nova.
"""
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VENV = RAIZ / ".venv" / "Scripts" / "python.exe"

try:
    import edge_tts
except ImportError:
    if VENV.exists() and Path(sys.executable).resolve() != VENV.resolve():
        sys.exit(subprocess.call([str(VENV), __file__, *sys.argv[1:]]))
    sys.exit("Falta o edge-tts. Rode: python -m venv .venv  e  .venv\\Scripts\\pip install edge-tts==7.3.1")

VOZ = "pt-BR-ThalitaMultilingualNeural"
VELOCIDADE = "+6%"

# (cena, fala). A ordem é a ordem do vídeo.
FALAS = [
    ("gancho", "Vinte dólares por mês de assinatura. E, mesmo assim: limite atingido. Volte em cinco horas."),
    ("apresenta", "Conheça o Clave. Um app para Windows que usa o Clód pela A P I, com a sua própria chave."),
    ("custo", "Na A P I, você paga só o que usa. Mil mensagens curtas no Ráicu saem por uns quarenta centavos de "
              "dólar. E o Clave mostra o custo de cada resposta, com um teto mensal que você mesmo define."),
    ("limite", "Sem janela de cinco horas. Sem limite semanal."),
    ("dados", "Na A P I, por padrão, as suas mensagens não são usadas para treinar modelos. E as suas conversas "
              "ficam no seu computador."),
    ("fluxo", "Escolha o modelo certo para cada tarefa. Ou junte todos num fluxo: o Opus planeja, o Sonnet faz, "
              "o Ráicu confere. E você vê o preço antes de aprovar."),
    ("code", "No modo Code, o Clód trabalha nas suas pastas: planilhas, arquivos, scripts. Você aprova cada "
             "mudança, e pode desfazer. Com as rotinas, ele trabalha sozinho, no horário que você escolher."),
    ("aprender", "Nunca usou inteligência artificial? Tem lições em português, do zero."),
    ("fecho", "O Clave é código aberto e gratuito. Você só paga o que usar. É só baixar no Guít Râb."),
]


def duracao(arq: Path) -> float:
    saida = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                           capture_output=True, text=True, check=True).stdout
    return float(saida.strip())


async def narrar(cena: str, texto: str, pasta: Path) -> dict:
    com = edge_tts.Communicate(texto, VOZ, rate=VELOCIDADE, boundary="WordBoundary")
    audio, palavras = bytearray(), []
    async for pedaco in com.stream():
        if pedaco["type"] == "audio":
            audio += pedaco["data"]
        elif pedaco["type"] == "WordBoundary":
            # offset e duração vêm em unidades de 100 ns
            palavras.append({"t": round(pedaco["offset"] / 1e7, 3), "d": round(pedaco["duration"] / 1e7, 3),
                             "texto": pedaco["text"]})
    arq = pasta / f"{cena}.mp3"
    arq.write_bytes(bytes(audio))
    return {"id": cena, "arquivo": f"narracao/{cena}.mp3", "duracao": round(duracao(arq), 3), "texto": texto,
            "palavras": palavras}


async def main():
    pasta = RAIZ / "public" / "narracao"
    pasta.mkdir(parents=True, exist_ok=True)
    cenas = []
    for cena, texto in FALAS:
        c = await narrar(cena, texto, pasta)
        print(f"ok {cena:10} {c['duracao']:5.2f} s  {len(c['palavras'])} palavras")
        cenas.append(c)
    destino = RAIZ / "src" / "narracao.gerado.json"
    destino.write_text(json.dumps({"voz": VOZ, "cenas": cenas}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total:", round(sum(c["duracao"] for c in cenas), 1), "s de fala")


if __name__ == "__main__":
    os.chdir(RAIZ)
    asyncio.run(main())
