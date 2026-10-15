import filecmp
import re
import shutil
import tempfile
import unittest
from pathlib import Path

import base
import contexto_pasta
import modelo_pasta
import tutoriais
from conferir_links import quebrados

MODELO = base.RAIZ / "modelo-de-pasta"
# Os termos pessoais ficam numa lista local, fora do git: escrever a lista aqui seria publicar o que ela protege.
LISTA_LOCAL = Path(__file__).with_name("privacidade-local.txt")
# o modelo e as lições não falam de outros agentes (o app aceita AGENTS.md como reserva, e isso pode aparecer na interface)
AGENTES = re.compile(r"codex|agents\.md|\.agents/", re.I)


def termos_pessoais():
    if not LISTA_LOCAL.is_file():
        return None
    linhas = [l.strip() for l in LISTA_LOCAL.read_text(encoding="utf-8").splitlines()]
    termos = [l for l in linhas if l and not l.startswith("#")]
    return re.compile("|".join(f"(?:{t})" for t in termos), re.I) if termos else None


def procurar(regra_por_pasta):
    achados = []
    for raiz in (MODELO, base.RAIZ / "modelo-de-pasta-en", base.RAIZ / "tutoriais", base.RAIZ / "skills",
                 base.RAIZ / "app" / "js", base.RAIZ / "app" / "i18n", base.RAIZ / "plugins", base.RAIZ / "agentes"):
        regras = regra_por_pasta(raiz)
        if not regras:
            continue
        for arq in raiz.rglob("*"):
            if arq.is_file() and arq.suffix in (".md", ".py", ".ps1", ".json", ".js", ".txt") and "prints" not in arq.parts:
                for n, linha in enumerate(arq.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if any(r.search(linha) for r in regras):
                        achados.append(f"{arq.relative_to(base.RAIZ)}:{n}: {linha.strip()[:90]}")
    return achados


class TestModeloDePasta(unittest.TestCase):
    def test_nada_pessoal_no_modelo_nem_nas_licoes(self):
        pessoal = termos_pessoais()
        if pessoal is None:
            self.skipTest("sem a lista local testes/privacidade-local.txt (fica fora do git)")
        achados = procurar(lambda raiz: [pessoal])
        self.assertEqual(achados, [], "\n".join(achados))

    def test_modelo_e_licoes_nao_falam_de_outros_agentes(self):
        achados = procurar(lambda raiz: [AGENTES] if raiz.name not in ("js", "i18n") else [])
        self.assertEqual(achados, [], "\n".join(achados))

    def test_sem_agents_md(self):
        self.assertEqual(list(MODELO.rglob("AGENTS.md")), [])
        self.assertFalse((MODELO / ".agents").exists())

    def test_ver_video_igual_no_app_e_no_modelo(self):
        a, b = base.RAIZ / "skills" / "ver-video", MODELO / ".claude" / "skills" / "ver-video"
        # a skill do app é a em inglês (igual à do modelo em inglês); os scripts são os mesmos nos dois modelos
        en = base.RAIZ / "modelo-de-pasta-en" / ".claude" / "skills" / "ver-video"
        self.assertTrue(filecmp.cmp(a / "SKILL.md", en / "SKILL.md", shallow=False))
        for nome in ("ver_video.py", "instalar.ps1"):
            self.assertTrue(filecmp.cmp(a / nome, b / nome, shallow=False), nome)

    def test_criar_pasta_preenche_sobre_mim(self):
        destino = Path(tempfile.mkdtemp(prefix="clave-modelo-"))
        try:
            r = modelo_pasta.criar(str(destino), "meu-trabalho", {"nome": "Ana", "experiencia": "nenhuma", "ocupacao": "confeiteira"}, iniciar_git=False)
            claude_md = (Path(r["caminho"]) / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("**Nome:** Ana", claude_md)
            self.assertIn("Não sei programar", claude_md)
            self.assertNotIn("SOBRE-MIM", claude_md)
            skills = {s["nome"] for s in contexto_pasta.skills(r["caminho"])}
            self.assertTrue({"ver-video", "direcao-visual", "revisar-codigo", "inicializar-pasta"} <= skills)
            projeto = Path(r["caminho"]) / "um-projeto"
            projeto.mkdir()
            self.assertTrue(any(a["caminho"].endswith("CLAUDE.md") for a in contexto_pasta.instrucoes(projeto)),
                            "o CLAUDE.md da pasta-mãe vale nas subpastas")
            with self.assertRaises(ValueError):
                modelo_pasta.criar(str(destino), "meu-trabalho", {})
            with self.assertRaises(ValueError):
                modelo_pasta.criar(str(destino), "nome/ruim", {})
        finally:
            shutil.rmtree(destino, ignore_errors=True)

    def test_skill_da_pasta_vence_a_do_app(self):
        pasta = Path(tempfile.mkdtemp(prefix="clave-skill-"))
        try:
            s = pasta / ".claude" / "skills" / "ver-video"
            s.mkdir(parents=True)
            (s / "SKILL.md").write_text("---\nname: ver-video\ndescription: versão da pasta\n---\ncorpo", encoding="utf-8")
            achada = next(x for x in contexto_pasta.skills(pasta) if x["nome"] == "ver-video")
            self.assertEqual(achada["descricao"], "versão da pasta")
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


class TestLicoes(unittest.TestCase):
    def test_links_entre_licoes(self):
        self.assertEqual(quebrados(), [])

    def test_metadados_e_glossario(self):
        lista = tutoriais.listar()
        self.assertGreaterEqual(len(lista), 15)
        for t in lista:
            self.assertTrue(t["titulo"] and t["trilha"] and t["resumo"], t["slug"])
        ancoras = [a for _, a in tutoriais.termos_glossario()]
        self.assertEqual(len(ancoras), len(set(ancoras)), "âncora repetida no glossário")
        for termo in ("api", "json", "git", "github", "electron", "python", "token", "linguagem-de-programacao"):
            self.assertIn(termo, ancoras)

    def test_guia_do_claude_cita_json_escrito_errado(self):
        guia = tutoriais.guia_para_o_claude()
        self.assertIn("JASON", guia)
        self.assertIn("[JSON](#/aprender/glossario/json)", guia)


if __name__ == "__main__":
    unittest.main()
