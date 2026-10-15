import io
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import base  # noqa: F401
import agentes
import comandos
import config
import contexto_pasta
import plugins


def criar_plugin(raiz: Path, nome="meu-plugin", extra=True) -> Path:
    p = raiz / nome
    (p / ".claude-plugin").mkdir(parents=True)
    (p / ".claude-plugin" / "plugin.json").write_text(json.dumps(
        {"name": nome, "version": "1.2.0", "description": "Plugin de teste", "author": {"name": "Ana"}}), encoding="utf-8")
    (p / "skills" / "resumir").mkdir(parents=True)
    (p / "skills" / "resumir" / "SKILL.md").write_text(
        "---\nname: resumir\ndescription: Resume textos longos\n---\nResuma em 5 linhas: $ARGUMENTS\n", encoding="utf-8")
    (p / "agents").mkdir()
    (p / "agents" / "critico.md").write_text(
        "---\nname: critico\ndescription: Critica\ntools: Read, Grep\nmodel: haiku\n---\nSeja crítico.\n", encoding="utf-8")
    (p / "commands").mkdir()
    (p / "commands" / "limpar.md").write_text(
        "---\ndescription: Limpa a pasta\nallowed-tools: Bash(Remove-Item *), Read\n---\nLimpe $0 e depois $1.\n",
        encoding="utf-8")
    if extra:
        (p / "hooks").mkdir()
        (p / "hooks" / "hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
        (p / ".mcp.json").write_text(json.dumps({"mcpServers": {
            "local": {"command": "node", "args": ["x.js"]},
            "remoto": {"type": "http", "url": "https://mcp.exemplo.com/mcp"}}}), encoding="utf-8")
        (p / "fluxos").mkdir()
        (p / "fluxos" / "duplo.json").write_text(json.dumps(
            {"nome": "Duplo", "etapas": [{"nome": "A", "tarefa": "a"}, {"nome": "B", "tarefa": "b"}]}), encoding="utf-8")
    return p


class TestPlugins(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="clave-plug-"))
        shutil.rmtree(plugins.instalados_dir(), ignore_errors=True)
        config.salvar({"plugins": {}})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(plugins.instalados_dir(), ignore_errors=True)
        config.salvar({"plugins": {}})

    def test_analisar_avisa_o_que_fica_de_fora(self):
        info = plugins.analisar(criar_plugin(self.tmp))
        self.assertEqual(info["nome"], "meu-plugin")
        self.assertEqual(info["versao"], "1.2.0")
        self.assertEqual([s["nome"] for s in info["skills"]], ["resumir"])
        self.assertEqual([a["nome"] for a in info["agentes"]], ["critico"])
        self.assertEqual([c["nome"] for c in info["comandos"]], ["limpar"])
        self.assertEqual(info["mcp_remotos"], [{"nome": "remoto", "url": "https://mcp.exemplo.com/mcp"}])
        self.assertTrue(any("hooks" in a for a in info["avisos"]))
        self.assertTrue(any("local" in a for a in info["avisos"]))

    def test_sem_manifesto_nao_e_plugin(self):
        (self.tmp / "x").mkdir()
        with self.assertRaises(plugins.ErroPlugin):
            plugins.analisar(self.tmp / "x")

    def test_instalar_ligar_e_partes_com_prefixo(self):
        plugins.instalar_de_pasta(criar_plugin(self.tmp))
        nomes = [s["nome"] for s in contexto_pasta.skills(None)]
        self.assertIn("meu-plugin:resumir", nomes)
        self.assertIn("meu-plugin:critico", [a["nome"] for a in agentes.listar(None)])
        self.assertIn("meu-plugin:limpar", [c["nome"] for c in comandos.listar(None)])
        plugins.ligar("meu-plugin", False)
        self.assertNotIn("meu-plugin:resumir", [s["nome"] for s in contexto_pasta.skills(None)])
        plugins.ligar("meu-plugin", True)
        plugins.remover("meu-plugin")
        self.assertNotIn("meu-plugin", [p["nome"] for p in plugins.listar()])

    def test_skill_da_pasta_vence_a_do_plugin(self):
        plugins.instalar_de_pasta(criar_plugin(self.tmp))
        pasta = self.tmp / "trabalho"
        (pasta / ".claude" / "skills" / "resumir").mkdir(parents=True)
        (pasta / ".claude" / "skills" / "resumir" / "SKILL.md").write_text(
            "---\nname: resumir\ndescription: A minha\n---\nx\n", encoding="utf-8")
        nomes = [s["nome"] for s in contexto_pasta.skills(pasta)]
        self.assertIn("resumir", nomes)
        self.assertNotIn("meu-plugin:resumir", nomes)

    def _zip(self, arquivos: dict) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            for nome, conteudo in arquivos.items():
                z.writestr(nome, conteudo)
        return buf.getvalue()

    def test_github_plugin_unico_e_marketplace(self):
        man = json.dumps({"name": "unico"})
        dados = self._zip({"repo-main/.claude-plugin/plugin.json": man,
                           "repo-main/skills/oi/SKILL.md": "---\nname: oi\ndescription: diz oi\n---\noi"})
        prep = plugins.preparar_github("ana/repo", _baixar=lambda *a: dados)
        self.assertEqual([p["nome"] for p in prep["plugins"]], ["unico"])
        feitos = plugins.instalar_preparado(prep["id"], ["unico"])
        self.assertEqual(feitos[0]["nome"], "unico")

        mkt = json.dumps({"name": "loja", "owner": {"name": "Ana"}, "plugins": [
            {"name": "um", "source": "./plugins/um"},
            {"name": "dois", "source": "./plugins/dois", "description": "sem manifesto próprio"},
            {"name": "fora", "source": {"source": "github", "repo": "outro/repo"}}]})
        dados = self._zip({"loja-main/.claude-plugin/marketplace.json": mkt,
                           "loja-main/plugins/um/.claude-plugin/plugin.json": json.dumps({"name": "um"}),
                           "loja-main/plugins/dois/skills/x/SKILL.md": "---\nname: x\n---\nx"})
        prep = plugins.preparar_github("https://github.com/ana/loja/tree/v2", _baixar=lambda *a: dados)
        self.assertEqual(sorted(p["nome"] for p in prep["plugins"]), ["dois", "um"])
        self.assertEqual(prep["ref"], "v2")
        self.assertTrue(any("outro/repo" in a for a in prep["avisos"]))

    def test_zip_que_tenta_sair_da_pasta(self):
        dados = self._zip({"../../fora.txt": "x"})
        with self.assertRaises(plugins.ErroPlugin):
            plugins.preparar_github("ana/repo", _baixar=lambda *a: dados)

    def test_referencias_do_github(self):
        self.assertEqual(plugins._ref_github("ana/repo#v1"), ("ana", "repo", "v1"))
        self.assertEqual(plugins._ref_github("https://github.com/ana/repo.git"), ("ana", "repo", "HEAD"))
        with self.assertRaises(plugins.ErroPlugin):
            plugins._ref_github("https://gitlab.com/ana/repo")
        with self.assertRaises(plugins.ErroPlugin):
            plugins._ref_github("ana")


class TestComandos(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-cmd-"))
        (self.pasta / ".claude" / "commands" / "docs").mkdir(parents=True)
        (self.pasta / ".claude" / "commands" / "revisar.md").write_text(
            "---\ndescription: Revisa um arquivo\nargument-hint: [arquivo]\nmodel: haiku\n"
            "allowed-tools: Read, Bash(git diff *)\n---\nRevise $ARGUMENTS. Primeiro: $0.\n", encoding="utf-8")
        (self.pasta / ".claude" / "commands" / "docs" / "novo.md").write_text("Crie um documento.", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_listar_e_expandir(self):
        nomes = [c["nome"] for c in comandos.listar(self.pasta)]
        self.assertIn("revisar", nomes)
        self.assertIn("docs:novo", nomes)
        self.assertIn("fluxo", nomes)  # do app
        e = comandos.expandir('/revisar "meu arquivo.txt" outro', self.pasta)
        self.assertEqual(e["texto"], 'Revise "meu arquivo.txt" outro. Primeiro: meu arquivo.txt.')
        self.assertEqual(e["modelo"], "haiku")
        self.assertEqual(e["ferramentas_permitidas"], ["Read", "Bash(git diff *)"])
        e = comandos.expandir("/docs:novo sobre gatos", self.pasta)
        self.assertTrue(e["texto"].endswith("ARGUMENTS: sobre gatos"))
        self.assertIsNone(comandos.expandir("/modelo opus", self.pasta))   # do app: a tela resolve
        self.assertIsNone(comandos.expandir("/nao-existe", self.pasta))
        self.assertIsNone(comandos.expandir("texto normal", self.pasta))

    def test_comando_de_plugin_nao_libera_terminal(self):
        shutil.rmtree(plugins.instalados_dir(), ignore_errors=True)
        tmp = Path(tempfile.mkdtemp(prefix="clave-plug-"))
        try:
            plugins.instalar_de_pasta(criar_plugin(tmp, extra=False))
            e = comandos.expandir("/meu-plugin:limpar a b", None)
            self.assertEqual(e["texto"], "Limpe a e depois b.")
            self.assertEqual(e["ferramentas_permitidas"], ["Read"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(plugins.instalados_dir(), ignore_errors=True)
            config.salvar({"plugins": {}})


class TestAgentes(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-ag-"))

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_embutidos_e_capacidades(self):
        nomes = {a["nome"]: a for a in agentes.listar(None)}
        for n in ("planejador", "executor", "testador", "revisor", "pesquisador", "redator"):
            self.assertIn(n, nomes)
        self.assertEqual(nomes["planejador"]["pode"], ["ler"])
        self.assertEqual(nomes["executor"]["pode"], ["ler", "editar", "comandos", "web"])  # sem tools = tudo
        self.assertEqual(nomes["pesquisador"]["pode"], ["web"])
        self.assertEqual(agentes.resolver_modelo("opus", "x"), "claude-opus-5-5")
        self.assertEqual(agentes.resolver_modelo("inherit", "claude-haiku-5-5"), "claude-haiku-5-5")
        self.assertEqual(agentes.capacidades("Read, Bash(git *)", "Bash"), ["ler"])

    def test_da_pasta_vence_e_salvar_apagar(self):
        a = agentes.salvar({"nome": "revisor", "descricao": "O meu revisor", "modelo": "claude-haiku-5-5",
                            "pode": ["ler", "web"], "instrucoes": "Revise."}, "pasta", self.pasta)
        self.assertEqual(a["pode"], ["ler", "web"])
        texto = Path(a["caminho"]).read_text(encoding="utf-8")
        self.assertIn("model: haiku", texto)
        self.assertIn("tools: Read, Glob, Grep, WebFetch, WebSearch", texto)
        self.assertEqual(agentes.pegar("revisor", self.pasta)["descricao"], "O meu revisor")
        with self.assertRaises(ValueError):
            agentes.salvar({"nome": "Nome Ruim"}, "pasta", self.pasta)
        with self.assertRaises(ValueError):
            agentes.apagar(str(Path(agentes.EMBUTIDOS) / "revisor.md"), self.pasta)
        agentes.apagar(a["caminho"], self.pasta)
        self.assertEqual(agentes.pegar("revisor", self.pasta)["origem"], "clave")


if __name__ == "__main__":
    unittest.main()
