"""Planilhas no chat: ler a planilha que a pessoa anexou e devolver planilhas prontas para baixar.

Os arquivos gerados ficam guardados como anexos (origem "gerado"), então a
mesma ferramenta de leitura serve para conferir o resultado, e a interface
mostra um botão de baixar e de abrir no Excel.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

import anexos
import banco
from ferramentas import excel
from i18n import t

_ID = {"type": "string", "description": "O id do arquivo (aparece em <planilha anexada id=...> ou no resultado de planilha_criar)."}


def _f(nome, descricao, props, obrig):
    return {"name": nome, "description": descricao, "eager_input_streaming": True,
            "input_schema": {"type": "object", "properties": props, "required": obrig}}


def definicoes() -> list[dict]:
    defs = [
        _f("planilha_ler",
           "Lê uma planilha anexada na conversa (ou criada por você com planilha_criar): abas, valores e fórmulas. "
           "Use para ver abas que não vieram no anexo, mais linhas ou um intervalo específico.",
           {"anexo_id": _ID, "aba": {"type": "string"}, "intervalo": {"type": "string", "description": "Ex.: A1:F50"},
            "max_linhas": {"type": "integer"}}, ["anexo_id"]),
        _f("planilha_criar",
           "Cria uma planilha do Excel (.xlsx) que a pessoa baixa pela conversa: tabelas, fórmulas, formatação, "
           "gráficos, filtros, listas de opção. Para devolver uma versão alterada de uma planilha anexada, passe "
           "base_anexo_id (o original não é mexido; imagens e formas do original podem não vir na cópia). Use sempre que a pessoa pedir uma planilha, um controle, uma "
           "tabela para o Excel ou mudanças numa planilha que ela mandou.",
           {"nome_arquivo": {"type": "string", "description": "Nome do arquivo, terminando em .xlsx"},
            "operacoes": excel.ESQUEMA_OPERACOES,
            "base_anexo_id": {"type": "string", "description": "Começar de uma cópia desta planilha anexada (opcional)."},
            "recalcular": {"type": "boolean", "description": "Calcular as fórmulas no Excel do computador (se houver) "
                                                             "para você conferir os resultados com planilha_ler."}},
           ["nome_arquivo", "operacoes"]),
    ]
    if excel.excel_instalado():
        defs.append(_f("planilha_pdf",
                       "Exporta uma planilha (anexada ou criada por você) para PDF usando o Excel do computador. "
                       "A pessoa baixa o PDF pela conversa.",
                       {"anexo_id": _ID}, ["anexo_id"]))
    return defs


NOMES = {"planilha_ler", "planilha_criar", "planilha_pdf"}


def _caminho_anexo(aid: str) -> tuple[Path, dict]:
    reg = banco.anexo(str(aid or "").strip())
    if not reg:
        raise excel.ErroExcel(t("Não achei o arquivo com id {id}.", id=aid))
    if reg["tipo"] != excel.MIME_XLSX:
        raise excel.ErroExcel(t("O arquivo {nome} não é uma planilha .xlsx.", nome=reg["nome"]))
    return anexos.caminho(reg["id"]), reg


def _nome_xlsx(nome: str) -> str:
    nome = re.sub(r'[<>:"/\\|?*]+', "-", (nome or "planilha").strip()) or "planilha"
    return nome if nome.lower().endswith((".xlsx", ".xlsm")) else nome + ".xlsx"


def executar(nome: str, e: dict) -> str:
    if nome == "planilha_ler":
        caminho, reg = _caminho_anexo(e.get("anexo_id"))
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / Path(reg["nome"]).name
            if copia.suffix.lower() not in excel.EXTENSOES:
                copia = copia.with_suffix(".xlsx")
            copia.write_bytes(caminho.read_bytes())
            return excel.ler(copia, e.get("aba"), e.get("intervalo"), int(e.get("max_linhas") or 100))
    if nome == "planilha_criar":
        nome_arq = _nome_xlsx(e.get("nome_arquivo"))
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / nome_arq
            base = None
            if e.get("base_anexo_id"):
                base_caminho, reg = _caminho_anexo(e["base_anexo_id"])
                base = Path(tmp) / ("base" + (Path(reg["nome"]).suffix or ".xlsx"))
                base.write_bytes(base_caminho.read_bytes())
            resumo = excel.aplicar(destino, e.get("operacoes") or [], criar=True, base=base)
            nota = ""
            if e.get("recalcular"):
                try:
                    excel.no_excel(destino, "recalcular")
                    nota = "\n" + t("Fórmulas calculadas pelo Excel; use planilha_ler para conferir os valores.")
                except excel.ErroExcel as erro:
                    nota = "\n" + t("(Não deu para recalcular: {erro})", erro=erro)
            reg = anexos.salvar(nome_arq, destino.read_bytes(), origem="gerado")
        resumo = resumo.replace(str(destino), nome_arq)
        return f"{resumo}{nota}\n" + t("Arquivo pronto para a pessoa baixar: {nome} (id {id}). Diga a ela que o botão de baixar aparece aqui na conversa.", nome=nome_arq, id=reg["id"])
    if nome == "planilha_pdf":
        caminho, reg = _caminho_anexo(e.get("anexo_id"))
        with tempfile.TemporaryDirectory() as tmp:
            entrada = Path(tmp) / Path(reg["nome"]).name
            entrada.write_bytes(caminho.read_bytes())
            saida = entrada.with_suffix(".pdf")
            excel.no_excel(entrada, "pdf", saida)
            novo = anexos.salvar(saida.name, saida.read_bytes(), origem="gerado")
        return t("PDF pronto para a pessoa baixar: {nome} (id {id}).", nome=novo["nome"], id=novo["id"])
    raise excel.ErroExcel(t("Ferramenta desconhecida: {nome}", nome=nome))
