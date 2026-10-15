import json
import shutil
import tempfile
import unittest
from pathlib import Path

import base  # noqa: F401
import banco
import permissoes as P
from ferramentas import code as fc


def regras(*pares, escopo="app"):
    return [P.Regra(a, t, escopo) for a, t in pares]


class TestFormato(unittest.TestCase):
    def test_analisar_e_validar(self):
        self.assertEqual(P.analisar("Bash(git status *)"), ("Bash", "git status *"))
        self.assertEqual(P.analisar("Write(docs/**)"), ("Edit", "docs/**"))
        self.assertEqual(P.analisar("Grep"), ("Read", None))
        self.assertEqual(P.analisar("mcp__drive__buscar"), ("mcp__drive__buscar", None))
        self.assertIsNone(P.validar("Edit(*.xlsx)"))
        self.assertIsNone(P.validar("WebFetch(domain:github.com)"))
        self.assertIn("domain:", P.validar("WebFetch(github.com)"))
        self.assertIn("não é uma ferramenta", P.validar("Apagar(tudo)"))
        self.assertIn("formato", P.validar("Bash(sem fechar"))

    def test_comando_curinga_e_prefixo(self):
        self.assertTrue(P.casa_comando("npm run *", "npm run build"))
        self.assertTrue(P.casa_comando("npm run *", "npm run"))
        self.assertFalse(P.casa_comando("npm run *", "npm install"))
        self.assertTrue(P.casa_comando("ls:*", "ls -la"))
        self.assertFalse(P.casa_comando("ls *", "lsof"))
        self.assertTrue(P.casa_comando("ls*", "lsof"))
        self.assertTrue(P.casa_comando("git status", "git   status"))
        self.assertFalse(P.casa_comando("git status", "git status --short"))

    def test_subcomandos(self):
        self.assertEqual(P.subcomandos('echo "a && b" && git push; dir | more'), ['echo "a && b"', "git push", "dir", "more"])

    def test_permitir_precisa_valer_para_cada_parte(self):
        r = regras(("allow", "Bash(git status *)"))
        self.assertEqual(P.avaliar(r, [("Bash", "git status")], None)[0], "allow")
        self.assertIsNone(P.avaliar(r, [("Bash", "git status && Remove-Item x")], None)[0])
        r2 = regras(("deny", "Bash(git push *)"))
        self.assertEqual(P.avaliar(r2, [("Bash", "git add . && git push origin main")], None)[0], "deny")

    def test_negar_vence_permitir(self):
        r = regras(("allow", "Bash"), ("deny", "Bash(npm publish *)"))
        self.assertEqual(P.avaliar(r, [("Bash", "npm publish")], None)[0], "deny")
        r = regras(("allow", "Edit(docs/**)"), ("ask", "Edit(docs/contrato.md)"))
        base = Path(tempfile.gettempdir()).resolve()
        self.assertEqual(P.avaliar(r, [("Edit", base / "docs" / "contrato.md")], base)[0], "ask")

    def test_caminhos_estilo_gitignore(self):
        base = Path(tempfile.mkdtemp(prefix="clave-perm-")).resolve()
        try:
            self.assertTrue(P.casa_caminho(".env", base / "a" / "b" / ".env", base))       # sem barra: qualquer nível
            self.assertTrue(P.casa_caminho("docs/**", base / "docs" / "x" / "y.md", base))
            self.assertFalse(P.casa_caminho("docs/**", base / "src" / "docs.md", base))
            self.assertTrue(P.casa_caminho("/src/*.py", base / "src" / "a.py", base))
            self.assertFalse(P.casa_caminho("/src/*.py", base / "src" / "sub" / "a.py", base))
            self.assertTrue(P.casa_caminho("docs", base / "docs" / "a.md", base))           # pasta cobre o conteúdo
            fora = Path(tempfile.gettempdir()).resolve() / "fora.txt"
            self.assertFalse(P.casa_caminho("*.txt", fora, base))                            # relativo não sai da pasta
            abs_rx = "/" + P._posix_abs(fora.parent) + "/*.txt"
            self.assertTrue(P.casa_caminho(abs_rx, fora, base))                              # //c/... absoluto
            self.assertTrue(P.casa_caminho("~/**", Path.home() / "x.txt", base))
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def test_dominio_e_mcp(self):
        self.assertTrue(P.casa_dominio("domain:github.com", "https://github.com/a/b"))
        self.assertFalse(P.casa_dominio("domain:github.com", "https://api.github.com/x"))
        self.assertTrue(P.casa_dominio("domain:*.github.com", "api.github.com"))
        r = regras(("deny", "WebFetch(domain:*.exemplo.com)"), ("deny", "mcp__drive__apagar"), ("deny", "mcp__jira"))
        self.assertEqual(P.dominios_bloqueados(r), ["exemplo.com"])
        self.assertEqual(P.mcp_filtrado(r, "drive"), (True, ["apagar"]))
        self.assertEqual(P.mcp_filtrado(r, "jira"), (False, []))
        self.assertFalse(P.web_negada(r))
        self.assertTrue(P.web_negada(regras(("deny", "WebFetch"))))


class TestArquivos(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-perm-")).resolve()

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_le_settings_do_claude_code_e_grava_no_local(self):
        (self.pasta / ".claude").mkdir()
        (self.pasta / ".claude" / "settings.json").write_text(json.dumps({
            "model": "opus", "permissions": {"allow": ["Bash(npm run *)"], "deny": ["Read(.env)", "Inventada(x)"]}}),
            encoding="utf-8")
        lidas, avisos = P.ler_pasta(self.pasta)
        self.assertEqual({(r.acao, r.texto) for r in lidas}, {("allow", "Bash(npm run *)"), ("deny", "Read(.env)")})
        self.assertTrue(any("Inventada" in a for a in avisos))
        arq = P.salvar_na_pasta(self.pasta, "allow", "Edit(docs/**)")
        self.assertEqual(arq.name, "settings.local.json")
        P.salvar_na_pasta(self.pasta, "allow", "Edit(docs/**)")  # repetida não duplica
        dados = json.loads(arq.read_text(encoding="utf-8"))
        self.assertEqual(dados["permissions"]["allow"], ["Edit(docs/**)"])
        self.assertTrue(P.remover_da_pasta(self.pasta, "allow", "Edit(docs/**)"))
        with self.assertRaises(ValueError):
            P.salvar_na_pasta(self.pasta, "allow", "Bash(sem fechar")

    def test_regras_do_app(self):
        P.salvar_no_app("deny", "Bash(git push *)")
        self.assertIn(("deny", "Bash(git push *)"), {(r.acao, r.texto) for r in P.do_app()})
        self.assertTrue(P.remover_do_app("deny", "Bash(git push *)"))
        self.assertFalse(P.remover_do_app("deny", "Bash(git push *)"))

    def test_sugestoes(self):
        ctx = fc.Contexto(raiz=self.pasta, protegidos=[], execucao_id="x", conversa_id="x")
        self.assertEqual(P.sugerir("rodar_comando", {"comando": "git status --short"}, ctx), "Bash(git status *)")
        self.assertEqual(P.sugerir("rodar_comando", {"comando": "dir"}, ctx), "Bash(dir)")
        self.assertEqual(P.sugerir("rodar_comando", {"comando": "python script.py --x"}, ctx), "Bash(python script.py *)")
        self.assertEqual(P.sugerir("escrever_arquivo", {"caminho": "docs/a.md"}, ctx), "Edit(docs/**)")
        self.assertEqual(P.sugerir("escrever_arquivo", {"caminho": "a.md"}, ctx), "Edit(a.md)")
        fora = str(Path(tempfile.gettempdir()) / "x" / "y.txt")
        self.assertTrue(P.sugerir("ler_arquivo", {"caminho": fora}, ctx).startswith("Read(//"))


class TestDecisaoNoCode(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-perm-")).resolve()
        self.ctx = fc.Contexto(raiz=self.pasta, protegidos=[".env"], execucao_id="x", conversa_id="x")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def d(self, nome, entrada, modo="perguntar"):
        return fc.decidir(nome, entrada, self.ctx, modo, set())

    def test_regra_de_permitir_libera_comando(self):
        self.ctx.regras = regras(("allow", "Bash(npm test *)"))
        r = self.d("rodar_comando", {"comando": "npm test -- --watch=false"})
        self.assertEqual((r["decisao"], r["origem"], r["regra"]), ("auto", "regra", "Bash(npm test *)"))

    def test_regra_generica_nao_libera_perigoso(self):
        self.ctx.regras = regras(("allow", "Bash"))
        self.assertEqual(self.d("rodar_comando", {"comando": "dir"})["decisao"], "auto")
        self.assertEqual(self.d("rodar_comando", {"comando": "Remove-Item a.txt"})["decisao"], "perguntar")
        self.ctx.regras = regras(("allow", "Bash(Remove-Item tmp/*)"))  # regra escrita para ele: vale
        self.assertEqual(self.d("rodar_comando", {"comando": "Remove-Item tmp/a.txt"})["decisao"], "auto")

    def test_negar_e_perguntar_por_regra(self):
        self.ctx.regras = regras(("deny", "Edit(*.xlsx)"), ("ask", "Read(segredos/**)"))
        r = self.d("escrever_arquivo", {"caminho": "a.xlsx", "conteudo": ""}, "livre")
        self.assertEqual((r["decisao"], r["origem"]), ("negar", "regra"))
        self.assertEqual(self.d("ler_arquivo", {"caminho": "segredos/x.txt"})["decisao"], "perguntar")

    def test_protegido_vence_regra_de_permitir(self):
        self.ctx.regras = regras(("allow", "Read"))
        self.assertEqual(self.d("ler_arquivo", {"caminho": ".env"})["decisao"], "negar")

    def test_plano_nao_deixa_regra_liberar_edicao(self):
        self.ctx.regras = regras(("allow", "Edit"), ("allow", "Bash"))
        self.assertEqual(self.d("escrever_arquivo", {"caminho": "a.txt", "conteudo": ""}, "plano")["decisao"], "negar")
        self.assertEqual(self.d("rodar_comando", {"comando": "dir"}, "plano")["decisao"], "negar")

    def test_regra_absoluta_libera_fora_da_pasta(self):
        fora = Path(tempfile.mkdtemp(prefix="clave-fora-")).resolve()
        try:
            alvo = str(fora / "dados.csv")
            self.assertEqual(self.d("ler_arquivo", {"caminho": alvo})["decisao"], "perguntar")
            self.ctx.regras = regras(("allow", f"Read(/{P._posix_abs(fora)}/**)"))
            self.assertEqual(self.d("ler_arquivo", {"caminho": alvo})["decisao"], "auto")
        finally:
            shutil.rmtree(fora, ignore_errors=True)


class TestHistorico(unittest.TestCase):
    def test_registra_e_lista(self):
        banco.limpar_log_permissoes()
        banco.registrar_permissao("c", "e", "rodar_comando", "git status", "auto", "regra", "Bash(git status *)")
        banco.registrar_permissao("c", "e", "escrever_arquivo", "a.txt", "recusar", "voce")
        tudo = banco.log_permissoes()
        self.assertEqual([r["decisao"] for r in tudo], ["recusar", "auto"])
        self.assertEqual(len(banco.log_permissoes(decisao="auto")), 1)


if __name__ == "__main__":
    unittest.main()
