"""Inglês e português: nenhum texto sem tradução, lições e plugins nos dois idiomas e o idioma certo na primeira vez."""
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

import base
import config

RAIZ = base.RAIZ
# t('...'), t("...") ou t(`...`) sem ${} dentro; também i18n.t("...") no servidor
_CHAVE = re.compile(r"""(?<![\w$.])(?:i18n\.)?t\(\s*(?:'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"|`((?:[^`\\$]|\\.)*)`)""")


def _desescapar(s: str) -> str:
    return re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), s)


def chaves(arquivos) -> dict[str, list[str]]:
    achadas: dict[str, list[str]] = {}
    for arq in arquivos:
        texto = arq.read_text(encoding="utf-8")
        for m in _CHAVE.finditer(texto):
            chave = _desescapar(next(g for g in m.groups() if g is not None))
            achadas.setdefault(chave, []).append(f"{arq.relative_to(RAIZ)}:{texto[:m.start()].count(chr(10)) + 1}")
    return achadas


def catalogo(pasta: Path) -> dict:
    junto = {}
    for arq in sorted(pasta.glob("*.json")):
        junto.update(json.loads(arq.read_text(encoding="utf-8")))
    return junto


def frente(arq: Path) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", arq.read_text(encoding="utf-8"), re.S)
    meta = {}
    for linha in (m.group(1).splitlines() if m else []):
        if ":" in linha:
            k, v = linha.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


class TestCatalogos(unittest.TestCase):
    def faltando(self, arquivos, pasta):
        cat = catalogo(pasta)
        return [f"{k!r} em {lugares[0]}" for k, lugares in chaves(arquivos).items() if k not in cat]

    def test_interface_toda_traduzida(self):
        falta = self.faltando(sorted((RAIZ / "app" / "js").glob("*.js")), RAIZ / "app" / "i18n" / "en")
        self.assertEqual(falta, [], "textos da interface sem inglês:\n" + "\n".join(falta[:40]))

    def test_servidor_todo_traduzido(self):
        arquivos = [a for a in sorted((RAIZ / "servidor").rglob("*.py")) if a.name not in ("api_falsa.py", "i18n.py")]
        falta = self.faltando(arquivos, RAIZ / "servidor" / "i18n" / "en")
        self.assertEqual(falta, [], "textos do servidor sem inglês:\n" + "\n".join(falta[:40]))

    def test_descricoes_das_ferramentas(self):
        import execucao
        import fluxos
        import navegador
        import widgets
        from ferramentas import code as fcode, github as fgithub, planilhas as fplanilhas
        defs = (fcode.definicoes(com_skills=True) + fplanilhas.definicoes() + fgithub.definicoes(escrita=True)
                + [execucao.PLANO, execucao.SUGERIR, execucao.PERGUNTAR, fluxos.DEFINICAO]
                + navegador.definicoes_para_teste() + widgets.definicoes_para_teste())
        cat = catalogo(RAIZ / "servidor" / "i18n" / "en")
        falta = []

        def passar(no):
            if isinstance(no, dict):
                for k, v in no.items():
                    if k == "description" and isinstance(v, str) and v not in cat:
                        falta.append(v[:90])
                    else:
                        passar(v)
            elif isinstance(no, list):
                for x in no:
                    passar(x)
        passar(defs)
        self.assertEqual(falta, [], "descrições de ferramenta sem inglês:\n" + "\n".join(falta[:20]))

    def test_mesmas_variaveis_nas_duas_linguas(self):
        for pasta in (RAIZ / "app" / "i18n" / "en", RAIZ / "servidor" / "i18n" / "en"):
            for pt, en in catalogo(pasta).items():
                self.assertEqual(sorted(re.findall(r"\{(\w+)\}", pt)), sorted(re.findall(r"\{(\w+)\}", en)), f"{pasta.name}: {pt!r}")

    def test_sem_travessao_no_ingles(self):
        for pasta in (RAIZ / "app" / "i18n" / "en", RAIZ / "servidor" / "i18n" / "en"):
            for pt, en in catalogo(pasta).items():
                self.assertNotIn("\u2014", en, f"travessão em {pt!r}")


class TestConteudo(unittest.TestCase):
    def test_toda_licao_tem_versao_em_ingles(self):
        for arq in sorted((RAIZ / "tutoriais").glob("*.md")):
            en = RAIZ / "tutoriais" / "en" / arq.name
            self.assertTrue(en.is_file(), f"falta tutoriais/en/{arq.name}")
            a, b = frente(arq), frente(en)
            self.assertEqual(set(a), set(b), arq.name)
            self.assertEqual(a.get("ordem"), b.get("ordem"), arq.name)

    def test_glossario_em_ingles_guarda_as_ancoras(self):
        import tutoriais
        pt = [a for _, a in tutoriais.termos_glossario("pt-BR")]
        en = [a for _, a in tutoriais.termos_glossario("en")]
        self.assertEqual(pt, en)

    def test_plugins_agentes_e_fluxos_guardam_o_portugues(self):
        for p in sorted((RAIZ / "plugins").iterdir()):
            if p.is_dir():
                self.assertTrue((p / "i18n" / "pt-BR.json").is_file(), f"plugin {p.name} sem i18n/pt-BR.json")
        nomes = {frente(a).get("name") for a in (RAIZ / "agentes").glob("*.md")}
        pt = json.loads((RAIZ / "agentes" / "i18n" / "pt-BR.json").read_text(encoding="utf-8"))
        self.assertEqual(nomes, set(pt))
        for f in (RAIZ / "fluxos").glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            self.assertIn("pt-BR", d.get("i18n", {}), f.name)
            self.assertEqual(len(d["etapas"]), len(d["i18n"]["pt-BR"]["etapas"]), f.name)

    def test_modelo_de_pasta_em_ingles(self):
        en = RAIZ / "modelo-de-pasta-en"
        self.assertTrue((en / "CLAUDE.md").is_file())
        self.assertTrue((en / "READ-ME-FIRST.md").is_file())
        self.assertEqual((RAIZ / "skills" / "ver-video" / "SKILL.md").read_bytes(),
                         (en / ".claude" / "skills" / "ver-video" / "SKILL.md").read_bytes())


class TestIdiomaNaPrimeiraVez(unittest.TestCase):
    def carregar_em(self, pasta: Path, forcado: str):
        antes = (config.DADOS, config._cache, os.environ.get("CLAVE_IDIOMA"))
        try:
            config.DADOS, config._cache = pasta, None
            os.environ["CLAVE_IDIOMA"] = forcado
            return config.carregar()["idioma"]
        finally:
            config.DADOS, config._cache = antes[0], antes[1]
            os.environ["CLAVE_IDIOMA"] = antes[2] or "pt-BR"

    def test_instalacao_nova_segue_o_windows(self):
        self.assertEqual(self.carregar_em(Path(tempfile.mkdtemp()), "en-US"), "en")
        self.assertEqual(self.carregar_em(Path(tempfile.mkdtemp()), "pt-BR"), "pt-BR")

    def test_quem_ja_usava_fica_em_portugues(self):
        pasta = Path(tempfile.mkdtemp())
        (pasta / "config.json").write_text(json.dumps({"configurado": True, "nome": "Ana"}), encoding="utf-8")
        self.assertEqual(self.carregar_em(pasta, "en-US"), "pt-BR")

    def test_escolha_salva_vale(self):
        pasta = Path(tempfile.mkdtemp())
        (pasta / "config.json").write_text(json.dumps({"configurado": True, "idioma": "en"}), encoding="utf-8")
        self.assertEqual(self.carregar_em(pasta, "pt-BR"), "en")


if __name__ == "__main__":
    unittest.main()
