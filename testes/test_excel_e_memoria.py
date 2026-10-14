import shutil
import tempfile
import unittest
from pathlib import Path

import base  # noqa: F401
import anexos
from ferramentas import excel, memoria, planilhas


class TestExcel(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-xl-"))

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_criar_ler_e_alterar(self):
        arq = self.pasta / "t.xlsx"
        excel.aplicar(arq, [
            {"acao": "escrever", "aba": "Dados", "inicio": "A1", "linhas": [["Nome", "Valor", "Quando"], ["a", 1, "2026-10-14"], ["b", 2.5, "x"]]},
            {"acao": "celulas", "aba": "Dados", "valores": {"B4": "=SUM(B2:B3)"}},
            {"acao": "formatar", "aba": "Dados", "intervalo": "A1:C1", "negrito": True, "cor_fundo": "verde_claro", "formato_numero": "0.00"},
            {"acao": "tabela", "aba": "Dados", "intervalo": "A1:C3", "nome": "T"},
            {"acao": "grafico", "aba": "Dados", "tipo": "pizza", "dados": "B1:B3", "categorias": "A2:A3"},
            {"acao": "validacao_lista", "aba": "Dados", "intervalo": "A2:A9", "opcoes": ["a", "b"]},
            {"acao": "formatacao_condicional", "aba": "Dados", "intervalo": "B2:B3", "regra": "maior_que", "valor": 2},
            {"acao": "criar_aba", "aba": "Outra"},
        ])
        texto = excel.ler(arq)
        self.assertIn("Abas: Dados", texto)
        self.assertIn("B==SUM(B2:B3) → ?", texto)
        self.assertIn("C=2026-10-14", texto, "data em texto ISO vira data")
        self.assertIn("tabelas: T (A1:C3)", texto)
        excel.aplicar(arq, [{"acao": "renomear_aba", "aba": "Outra", "novo_nome": "Resumo"},
                            {"acao": "inserir_linhas", "aba": "Dados", "linha": 2, "quantidade": 1}])
        self.assertIn("Resumo", excel.ler(arq, aba="Resumo"))
        self.assertIn("2 | (vazia)", excel.ler(arq, aba="Dados", intervalo="A1:C3"))

    def test_erros_claros(self):
        arq = self.pasta / "e.xlsx"
        with self.assertRaises(excel.ErroExcel) as c:
            excel.aplicar(arq, [{"acao": "voar"}])
        self.assertIn("Ação desconhecida", str(c.exception))
        with self.assertRaises(excel.ErroExcel):
            excel.aplicar(arq, [{"acao": "formatar", "aba": "Planilha", "intervalo": "A1", "cor_fundo": "furta-cor"}])
        with self.assertRaises(excel.ErroExcel):
            excel.aplicar(self.pasta / "x.txt", [{"acao": "criar_aba", "aba": "a"}])
        with self.assertRaises(excel.ErroExcel):
            excel.ler(self.pasta / "nao-existe.xlsx")

    def test_planilha_no_chat_gera_anexo_e_le(self):
        r = planilhas.executar("planilha_criar", {"nome_arquivo": "gastos", "operacoes": [
            {"acao": "escrever", "aba": "Gastos", "linhas": [["Item", "Valor"], ["pão", 7]]}]})
        self.assertIn("gastos.xlsx (id ", r)
        aid = r.split("(id ")[1].split(")")[0]
        self.assertIn("A=pão", planilhas.executar("planilha_ler", {"anexo_id": aid}))
        copia = planilhas.executar("planilha_criar", {"nome_arquivo": "gastos-v2.xlsx", "base_anexo_id": aid, "operacoes": [
            {"acao": "celulas", "aba": "Gastos", "valores": {"A3": "leite", "B3": 5}}]})
        aid2 = copia.split("(id ")[1].split(")")[0]
        texto = planilhas.executar("planilha_ler", {"anexo_id": aid2})
        self.assertIn("A=pão", texto)
        self.assertIn("A=leite", texto)
        self.assertNotIn("leite", planilhas.executar("planilha_ler", {"anexo_id": aid}), "o original não pode mudar")

    def test_anexo_xlsx_vira_texto_com_id(self):
        arq = self.pasta / "a.xlsx"
        excel.aplicar(arq, [{"acao": "escrever", "aba": "P", "linhas": [["x", 1]]}])
        reg = anexos.salvar("minha planilha.xlsx", arq.read_bytes())
        self.assertEqual(reg["tipo"], excel.MIME_XLSX)
        bloco = anexos.expandir(anexos.referencia(reg))
        self.assertEqual(bloco["type"], "text")
        self.assertIn(f'id="{reg["id"]}"', bloco["text"])
        self.assertIn("A=x", bloco["text"])


class TestMemoria(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(memoria.raiz(), ignore_errors=True)

    def test_comandos(self):
        m = memoria.executar
        m({"command": "create", "path": "/memories/sobre-mim.md",
           "file_text": "---\nnome: Sobre mim\ndescricao: quem é\ntipo: sobre-voce\n---\nSou professora.\n"})
        m({"command": "create", "path": "/memories/MEMORY.md", "file_text": "- [Sobre mim](sobre-mim.md): quem é\n"})
        self.assertIn("Sou professora", m({"command": "view", "path": "/memories/sobre-mim.md"}))
        m({"command": "str_replace", "path": "/memories/sobre-mim.md", "old_str": "professora", "new_str": "designer"})
        m({"command": "insert", "path": "/memories/sobre-mim.md", "insert_line": 5, "insert_text": "Mora em Recife."})
        texto = m({"command": "view", "path": "/memories/sobre-mim.md"})
        self.assertIn("designer", texto)
        self.assertIn("Recife", texto)
        m({"command": "rename", "old_path": "/memories/sobre-mim.md", "new_path": "/memories/quem-sou.md"})
        self.assertIn("quem-sou.md", m({"command": "view", "path": "/memories"}))
        lista = memoria.listar()
        self.assertEqual(lista[0]["caminho"], "/memories/MEMORY.md", "o índice vem primeiro")
        item = next(a for a in lista if a["caminho"].endswith("quem-sou.md"))
        self.assertEqual((item["nome"], item["tipo"]), ("Sobre mim", "sobre-voce"))
        self.assertIn("Sobre mim", memoria.instrucoes_completas())
        m({"command": "delete", "path": "/memories/quem-sou.md"})
        self.assertNotIn("quem-sou", m({"command": "view", "path": "/memories"}))

    def test_nao_sai_da_pasta(self):
        for caminho in ("/memories/../fora.md", "/etc/passwd", "C:/Windows/x.md", "/memories/a/../../b.md"):
            with self.assertRaises(memoria.ErroMemoria, msg=caminho):
                memoria.executar({"command": "create", "path": caminho, "file_text": "x"})
        with self.assertRaises(memoria.ErroMemoria):
            memoria.executar({"command": "delete", "path": "/memories"})


if __name__ == "__main__":
    unittest.main()
