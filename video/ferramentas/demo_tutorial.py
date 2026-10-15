"""Sobe a demonstração do Clave (servidor.py --demo) com respostas de roteiro, para os prints dos tutoriais.

É a mesma demonstração do app (API de mentira, nada é cobrado, nenhuma chave), só que, nas mensagens dos tutoriais,
a API de mentira responde como o Claude responderia de verdade, no idioma da mensagem: as ideias de presente da
lição "Sua primeira conversa" e a arrumação da pasta Downloads da lição "Primeira automação" (olhar a pasta, mostrar
os passos e a contagem, escrever o script, pedir o OK e rodar). O resto cai na resposta normal da demonstração.

Uso (o telas.py já chama sozinho):
    python ferramentas/demo_tutorial.py --porta 8051 --dados <pasta temporária>
Não toca no código do Clave: só troca, neste processo, a função que monta as respostas da API de mentira.
"""
from __future__ import annotations

import os
import runpy
import sys
import uuid
from pathlib import Path

CLAVE = Path(__file__).resolve().parents[2]
SERVIDOR = CLAVE / "servidor"
sys.path.insert(0, str(SERVIDOR))

import api_falsa  # noqa: E402

_original = api_falsa.planejar

# ---------- as falas do Claude nos tutoriais ----------

PRESENTES = {
    "pt-BR": """Aqui vão 5 ideias, do mais em conta ao mais caprichado:

1. **Kit de sementes de ervas** (manjericão, alecrim, hortelã), com vasinhos: uns R$ 40.
2. **Luvas e ferramentas de jardinagem** com cabo de madeira: uns R$ 80.
3. **Regador de metal bonito**, daqueles que ficam de enfeite: uns R$ 120.
4. **Horta vertical** para a varanda ou o muro: uns R$ 180.
5. **Orquídea em vaso de cerâmica**, com um cartão escrito à mão: uns R$ 150.

Se ela já tem quase tudo, a orquídea com o cartão costuma acertar em cheio.""",
    "en": """Here are 5 ideas, from budget-friendly to a bit fancier:

1. **Herb seed kit** (basil, rosemary, mint) with small pots: about $10.
2. **Gardening gloves and tools** with wooden handles: about $20.
3. **A pretty metal watering can**, the kind that doubles as decor: about $30.
4. **Vertical garden planter** for a balcony or wall: about $45.
5. **An orchid in a ceramic pot**, with a handwritten card: about $35.

If she already has almost everything, the orchid with a card is usually a winner.""",
}

TITULOS = {
    "presentes": {"pt-BR": "Presentes para mãe jardineira", "en": "Gift ideas for a gardening mom"},
    "organizar": {"pt-BR": "Organizar a pasta Downloads", "en": "Tidy up the Downloads folder"},
}

# as subpastas, na ordem da lição, e o que vai para cada uma (a pasta de exemplo do telas.py tem esses arquivos)
SUBPASTAS = {
    "pt-BR": ["Documentos", "Imagens", "Planilhas", "Instaladores", "Outros"],
    "en": ["Documents", "Images", "Spreadsheets", "Installers", "Other"],
}
EXTENSOES = [["pdf", "doc", "docx", "txt"], ["jpg", "jpeg", "png", "gif", "webp"], ["xlsx", "xls", "csv"], ["exe", "msi"], []]

TAREFAS = {
    "pt-BR": ["Olhar a pasta", "Contar os arquivos por tipo", "Mostrar o plano"],
    "en": ["Look at the folder", "Count the files by type", "Show the plan"],
}

SCRIPT = {"pt-BR": "organizar-downloads.ps1", "en": "organize-downloads.ps1"}


def _script(lingua: str) -> str:
    nomes = SUBPASTAS[lingua]
    pt = lingua == "pt-BR"
    tipos, destino, pasta = ("$tipos", "$destino", "$pasta") if pt else ("$types", "$target", "$folder")
    linhas = ["# Organiza a pasta por tipo de arquivo, sem apagar nada." if pt
              else "# Sorts this folder by file type, without deleting anything.",
              f"{tipos} = [ordered]@{{"]
    for nome, exts in zip(nomes[:-1], EXTENSOES[:-1]):
        linhas.append(f"  '{nome}' = " + ",".join(f"'{e}'" for e in exts))
    linhas += ["}",
               "$n = 0",
               f"Get-ChildItem -LiteralPath $PSScriptRoot -File | Where-Object Name -ne '{SCRIPT[lingua]}' | ForEach-Object {{",
               "  $ext = $_.Extension.TrimStart('.').ToLower()",
               f"  {destino} = '{nomes[-1]}'",
               f"  foreach ($t in {tipos}.Keys) {{ if ({tipos}[$t] -contains $ext) {{ {destino} = $t }} }}",
               f"  {pasta} = Join-Path $PSScriptRoot {destino}",
               f"  New-Item -ItemType Directory -Force -Path {pasta} | Out-Null",
               f"  Move-Item -LiteralPath $_.FullName -Destination {pasta}",
               "  $n++",
               "}",
               ("Write-Output \"$n arquivos movidos.\"" if pt else "Write-Output \"$n files moved.\"")]
    return "\n".join(linhas) + "\n"


def _contagem(pasta: Path) -> list[tuple[str, int, list[str]]]:
    """(subpasta, quantos, extensões encontradas) a partir dos arquivos de verdade da pasta."""
    grupos: list[list[str]] = [[] for _ in EXTENSOES]
    for arq in sorted(pasta.iterdir()):
        if not arq.is_file() or arq.suffix.lower() == ".ps1":
            continue
        ext = arq.suffix.lstrip(".").lower()
        i = next((k for k, exts in enumerate(EXTENSOES) if ext in exts), len(EXTENSOES) - 1)
        grupos[i].append(ext)
    return [(i, len(g), sorted(set(g))) for i, g in enumerate(grupos)]


def _plano(lingua: str, pasta: Path) -> str:
    nomes = SUBPASTAS[lingua]
    cont = _contagem(pasta)
    total = sum(c[1] for c in cont)
    if lingua == "pt-BR":
        linhas = [f"Olhei a pasta: são **{total} arquivos** soltos. Ficaria assim:", "",
                  "| Subpasta | Arquivos | Tipos |", "|---|---|---|"]
    else:
        linhas = [f"I looked at the folder: there are **{total} loose files**. Here's how it would end up:", "",
                  "| Subfolder | Files | Types |", "|---|---|---|"]
    for i, n, exts in cont:
        linhas.append(f"| {nomes[i]} | {n} | {', '.join('.' + e for e in exts)} |")
    linhas.append("")
    linhas.append("Não vou apagar nada: só criar as 5 subpastas e mover os arquivos. Posso fazer?" if lingua == "pt-BR"
                  else "I won't delete anything: I'll just create the 5 subfolders and move the files. Shall I go ahead?")
    return "\n".join(linhas)


def _id() -> str:
    return "toolu_" + uuid.uuid4().hex[:20]


def _usuario(msgs: list[dict]) -> str:
    """O último texto que a pessoa escreveu (pula os resultados de ferramenta)."""
    for m in reversed(msgs):
        if m.get("role") != "user":
            continue
        c = m.get("content")
        if isinstance(c, str):
            return c
        textos = [b.get("text", "") for b in c or [] if isinstance(b, dict) and b.get("type") == "text"
                  and not b.get("text", "").startswith("<modo-do-clave>")]
        if textos:
            return "\n".join(textos)
    return ""


def _ultima_ferramenta(msgs: list[dict]) -> str | None:
    if len(msgs) < 2 or msgs[-1].get("role") != "user":
        return None
    c = msgs[-1].get("content")
    if not (isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c)):
        return None
    ant = msgs[-2]
    for b in reversed(ant.get("content") or []):
        if isinstance(b, dict) and b.get("type") == "tool_use":
            return b.get("name")
    return None


def _pasta(corpo: dict) -> Path | None:
    p = os.environ.get("CLAVE_VIDEO_DOWNLOADS")
    return Path(p) if p else None


def planejar(corpo: dict):
    msgs = corpo.get("messages") or []
    sistema = str(corpo.get("system", ""))
    texto = _usuario(msgs)
    baixo = texto.lower()
    lingua = "en" if any(p in baixo for p in ("gardening", "subfolders", "go ahead")) else "pt-BR"

    if "título curto" in sistema or "short title" in sistema:
        if "jardinagem" in baixo or "gardening" in baixo:
            return [{"type": "text", "text": TITULOS["presentes"][lingua]}], "end_turn"
        if "subpastas" in baixo or "subfolders" in baixo:
            return [{"type": "text", "text": TITULOS["organizar"][lingua]}], "end_turn"
        return _original(corpo)

    if "jardinagem" in baixo or "gardening" in baixo:
        return [{"type": "text", "text": PRESENTES[lingua]}], "end_turn"

    nomes = {t.get("name") for t in corpo.get("tools") or []}
    pasta = _pasta(corpo)
    ultima = _ultima_ferramenta(msgs)

    # 1. o pedido: olhar a pasta, mostrar os passos e a contagem, sem mexer em nada
    if ("subpastas" in baixo or "subfolders" in baixo) and "listar_pasta" in nomes and pasta:
        tarefas = TAREFAS[lingua]
        if ultima is None:
            return [{"type": "text", "text": "Primeiro vou olhar a pasta." if lingua == "pt-BR" else "First I'll look at the folder."},
                    {"type": "tool_use", "id": _id(), "name": "atualizar_tarefas",
                     "input": {"tarefas": [{"texto": tarefas[0], "estado": "fazendo"},
                                           {"texto": tarefas[1], "estado": "pendente"},
                                           {"texto": tarefas[2], "estado": "pendente"}]}}], "tool_use"
        if ultima == "atualizar_tarefas" and not any(
                b.get("name") == "listar_pasta" for m in msgs if m.get("role") == "assistant"
                for b in (m.get("content") or []) if isinstance(b, dict)):
            return [{"type": "tool_use", "id": _id(), "name": "listar_pasta", "input": {}}], "tool_use"
        if ultima == "listar_pasta":
            return [{"type": "tool_use", "id": _id(), "name": "atualizar_tarefas",
                     "input": {"tarefas": [{"texto": t, "estado": "feito"} for t in tarefas]}}], "tool_use"
        return [{"type": "text", "text": _plano(lingua, pasta)}], "end_turn"

    # 2. "pode fazer": escreve o script (pede OK), roda o script (pede OK) e conta o que fez
    if ("pode fazer" in baixo or "go ahead" in baixo) and "escrever_arquivo" in nomes and pasta:
        if ultima is None:
            return [{"type": "text", "text": ("Vou escrever um script que faz a arrumação e depois rodar. Assim ele fica "
                                              "na pasta para você usar de novo.") if lingua == "pt-BR" else
                     "I'll write a script that does the sorting and then run it, so it stays in the folder for you to reuse."},
                    {"type": "tool_use", "id": _id(), "name": "escrever_arquivo",
                     "input": {"caminho": SCRIPT[lingua], "conteudo": _script(lingua)}}], "tool_use"
        if ultima == "escrever_arquivo":
            return [{"type": "tool_use", "id": _id(), "name": "rodar_comando",
                     "input": {"comando": f"powershell -NoProfile -ExecutionPolicy Bypass -File .\\{SCRIPT[lingua]}",
                               "descricao": ("Roda o script: cria as 5 subpastas e move os arquivos" if lingua == "pt-BR"
                                             else "Runs the script: creates the 5 subfolders and moves the files")}}], "tool_use"
        if ultima == "rodar_comando":
            nomes_sub = SUBPASTAS[lingua]
            if lingua == "pt-BR":
                fim = (f"Pronto: os arquivos estão em {', '.join(nomes_sub[:-1])} e {nomes_sub[-1]}. Nada foi apagado.\n\n"
                       f"O script **{SCRIPT[lingua]}** ficou na pasta: quando a Downloads encher de novo, é só rodar.")
            else:
                fim = (f"Done: the files are now in {', '.join(nomes_sub[:-1])} and {nomes_sub[-1]}. Nothing was deleted.\n\n"
                       f"The **{SCRIPT[lingua]}** script stays in the folder: when Downloads fills up again, just run it.")
            return [{"type": "text", "text": fim}], "end_turn"

    return _original(corpo)


api_falsa.planejar = planejar

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--dados" in args:
        os.environ["CLAVE_DADOS"] = args[args.index("--dados") + 1]
    porta = args[args.index("--porta") + 1] if "--porta" in args else "8051"
    os.chdir(CLAVE)
    sys.argv = [str(SERVIDOR / "servidor.py"), "--demo", "--sem-senha", "--porta", porta]
    runpy.run_path(str(SERVIDOR / "servidor.py"), run_name="__main__")
