"""4.3.0: o Haiku como padrão, o conselheiro de modelo, os comandos em inglês e em português, sair da conta e desinstalar."""
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

import base
import banco
import comandos
import config
import conselheiro
import contexto_pasta
import execucao
import fluxos
import rotinas
import segredos
from test_servidor import Servidor


class TestModeloPadrao(unittest.TestCase):
    def test_haiku_e_o_padrao_das_instalacoes_novas(self):
        self.assertEqual(config.PADRAO["modelo_chat"], "claude-haiku-5-5")
        self.assertEqual(config.PADRAO["modelo_code"], "claude-haiku-5-5")
        self.assertTrue(config.PADRAO["conselheiro_modelo"])
        self.assertFalse(config.PADRAO["trocar_modelo_sozinho"])


class _ClienteFalso:
    def __init__(self, escolha, motivo="Tem código com vários arquivos."):
        self.pedidos = []
        bloco = SimpleNamespace(type="tool_use", name="recomendar_modelo", input={"modelo": escolha, "motivo": motivo})
        uso = SimpleNamespace(model_dump=lambda mode="json", exclude_none=True: {"input_tokens": 600, "output_tokens": 30})
        resposta = SimpleNamespace(content=[bloco], usage=uso)
        self.messages = SimpleNamespace(create=lambda **kw: (self.pedidos.append(kw), resposta)[1])
        self.opcoes = None

    def with_options(self, **kw):
        self.opcoes = kw
        return self


class TestConselheiro(unittest.TestCase):
    def test_quando_avalia(self):
        self.assertEqual([n for n in range(1, 17) if conselheiro.deve_avaliar(n)], [1, 6, 11, 16])
        self.assertFalse(conselheiro.deve_avaliar(0))

    def test_conta_so_as_mensagens_de_quem_usa(self):
        caminho = [{"papel": "user", "tipo": "normal"}, {"papel": "assistant", "tipo": "normal"},
                   {"papel": "user", "tipo": "resultado_ferramenta"}, {"papel": "user", "tipo": "normal"}]
        self.assertEqual(conselheiro.contar_pedidos(caminho), 2)

    def _conversa(self, texto):
        conv = banco.criar_conversa("chat")
        banco.adicionar_mensagem(conv["id"], None, "user", [{"type": "text", "text": texto}])
        return conv["id"]

    def _avaliar(self, cliente, cid, atual="claude-haiku-5-5"):
        original = execucao.cliente
        execucao.cliente = lambda: cliente
        try:
            return conselheiro.avaliar(cid, atual, "chat")
        finally:
            execucao.cliente = original

    def test_avalia_no_haiku_e_registra_o_custo(self):
        cid = self._conversa("Revise o código destes 12 arquivos e ache os erros.")
        falso = _ClienteFalso("claude-sonnet-5-5")
        r = self._avaliar(falso, cid)
        self.assertEqual((r["modelo"], r["motivo"]), ("claude-sonnet-5-5", "Tem código com vários arquivos."))
        pedido = falso.pedidos[0]
        self.assertEqual(pedido["model"], "claude-haiku-5-5")
        self.assertEqual(pedido["tool_choice"], {"type": "tool", "name": "recomendar_modelo"})
        self.assertIn("Revise o código destes 12 arquivos", pedido["messages"][0]["content"])
        self.assertIn("claude-haiku-5-5", pedido["system"])
        uso = banco.conexao().execute("SELECT origem, modelo FROM uso WHERE conversa_id=?", (cid,)).fetchall()
        self.assertEqual([(u["origem"], u["modelo"]) for u in uso], [("conselheiro", "claude-haiku-5-5")])

    def test_modelo_antigo_pode_ficar(self):
        import modelos
        antigo = next((m for m, i in modelos.MODELOS.items() if not i.get("atual")), None)
        if not antigo:
            self.skipTest("nenhum modelo antigo na lista")
        self.assertIn(antigo, conselheiro.candidatos(antigo))
        self.assertNotIn(antigo, conselheiro.candidatos())
        cid = self._conversa("Oi")
        falso = _ClienteFalso(antigo)
        self.assertEqual(self._avaliar(falso, cid, atual=antigo)["modelo"], antigo)
        self.assertIn(antigo, falso.pedidos[0]["system"])
        self.assertEqual(falso.opcoes, {"timeout": 20, "max_retries": 1}, "o conselho desiste rápido")

    def test_modelo_que_nao_existe_vira_nada(self):
        cid = self._conversa("Oi")
        self.assertIsNone(self._avaliar(_ClienteFalso("gpt-qualquer"), cid))


class TestConselheiroNoServidor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Servidor(sem_senha=True)

    @classmethod
    def tearDownClass(cls):
        cls.s.fechar()

    def _conversa(self):
        return self.s.pedir("POST", "/api/conversas", {"modo": "chat"})[1]["conversa"]["id"]

    def _mandar(self, cid, texto, modelo="claude-haiku-5-5"):
        _, r = self.s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": texto, "opcoes": {"modelo": modelo}})
        return self.s.eventos(r["execucao"])

    def _modelo_da_resposta(self, cid):
        _, v = self.s.pedir("GET", f"/api/conversas/{cid}")
        return [m for m in v["mensagens"] if m["papel"] == "assistant"][-1].get("modelo")

    def test_sugere_na_primeira_e_depois_a_cada_cinco(self):
        cid = self._conversa()
        evs = self._mandar(cid, "explique este código complexo")
        sug = [e for e in evs if e["tipo"] == "modelo_sugerido"]
        self.assertEqual(len(sug), 1)
        self.assertEqual((sug[0]["atual"], sug[0]["modelo"]), ("claude-haiku-5-5", "claude-sonnet-5-5"))
        self.assertEqual(self._modelo_da_resposta(cid), "claude-haiku-5-5", "só sugerir não troca")
        # o conselho fica na mensagem (a tela redesenha a conversa no fim da resposta e o aviso não pode sumir)
        _, v = self.s.pedir("GET", f"/api/conversas/{cid}")
        pedido = [m for m in v["mensagens"] if m["papel"] == "user" and m["tipo"] == "normal"][0]
        self.assertEqual(pedido["meta"]["conselho"]["modelo"], "claude-sonnet-5-5")
        self.assertEqual(sug[0]["mensagem"], pedido["id"])
        self.s.pedir("PATCH", f"/api/conversas/{cid}", {"ajustes_mesclar": {"conselho_visto": pedido["id"]}})
        _, v = self.s.pedir("GET", f"/api/conversas/{cid}")
        self.assertEqual(v["conversa"]["ajustes"]["conselho_visto"], pedido["id"])
        for i in range(2, 6):
            evs = self._mandar(cid, "mais um código complexo")
            self.assertFalse([e for e in evs if e["tipo"].startswith("modelo_")], f"mensagem {i} não avalia")
        evs = self._mandar(cid, "e agora outro código complexo")
        self.assertTrue([e for e in evs if e["tipo"] == "modelo_sugerido"], "a 6ª avalia de novo")

    def test_pedido_simples_nao_sugere_nada(self):
        evs = self._mandar(self._conversa(), "oi, tudo bem?")
        self.assertFalse([e for e in evs if e["tipo"].startswith("modelo_")])
        pasta = tempfile.mkdtemp(prefix="clave-conselheiro-code-")
        try:  # no Code também (a 1ª linha do pedido ao conselheiro diz "Code", e isso não pode contar como difícil)
            _, r = self.s.pedir("POST", "/api/conversas", {"modo": "code", "pasta": pasta})
            evs = self._mandar(r["conversa"]["id"], "oi")
            self.assertFalse([e for e in evs if e["tipo"].startswith("modelo_")])
        finally:
            shutil.rmtree(pasta, ignore_errors=True)

    def test_troca_sozinho_quando_deixa_e_respeita_o_voltar(self):
        self.s.pedir("POST", "/api/config", {"trocar_modelo_sozinho": True})
        try:
            cid = self._conversa()
            evs = self._mandar(cid, "explique este código complexo")
            troca = [e for e in evs if e["tipo"] == "modelo_trocado"]
            self.assertEqual((troca[0]["de"], troca[0]["para"]), ("claude-haiku-5-5", "claude-sonnet-5-5"))
            self.assertEqual(self._modelo_da_resposta(cid), "claude-sonnet-5-5")
            _, v = self.s.pedir("GET", f"/api/conversas/{cid}")
            self.assertEqual(v["conversa"]["ajustes"]["modelo"], "claude-sonnet-5-5")
            self._mandar(cid, "mais um", modelo="claude-sonnet-5-5")
            self.assertEqual(self._modelo_da_resposta(cid), "claude-sonnet-5-5", "a 2ª resposta continua no modelo novo")
            _, v = self.s.pedir("GET", f"/api/conversas/{cid}")
            self.assertEqual(v["conversa"]["ajustes"]["modelo"], "claude-sonnet-5-5")
            # "Voltar para o Haiku": a conversa fica com o modelo fixo e o conselheiro não mexe mais nela
            cid2 = self._conversa()
            self.s.pedir("PATCH", f"/api/conversas/{cid2}", {"ajustes_mesclar": {"modelo_fixo": True, "permissao": "livre"}})
            _, v = self.s.pedir("GET", f"/api/conversas/{cid2}")
            self.assertNotIn("permissao", v["conversa"]["ajustes"], "só modelo e modelo_fixo entram por aqui")
            evs = self._mandar(cid2, "explique este código complexo")
            self.assertFalse([e for e in evs if e["tipo"].startswith("modelo_")])
        finally:
            self.s.pedir("POST", "/api/config", {"trocar_modelo_sozinho": False})

    def test_desligado_nao_avalia(self):
        self.s.pedir("POST", "/api/config", {"conselheiro_modelo": False})
        try:
            evs = self._mandar(self._conversa(), "explique este código complexo")
            self.assertFalse([e for e in evs if e["tipo"].startswith("modelo_")])
        finally:
            self.s.pedir("POST", "/api/config", {"conselheiro_modelo": True})

    def test_gerar_outra_resposta_nao_avalia(self):
        cid = self._conversa()
        self._mandar(cid, "explique este código complexo")
        _, v = self.s.pedir("GET", f"/api/conversas/{cid}")
        ultima = [m for m in v["mensagens"] if m["papel"] == "assistant"][-1]
        _, r = self.s.pedir("POST", f"/api/conversas/{cid}/regenerar", {"mensagem_id": ultima["id"]})
        evs = self.s.eventos(r["execucao"])
        self.assertFalse([e for e in evs if e["tipo"].startswith("modelo_")])


class TestComandosNosDoisIdiomas(unittest.TestCase):
    def test_ida_e_volta_e_sem_colisao(self):
        for pt, en in comandos.NOMES_EN.items():
            if pt != "compactar":
                self.assertEqual(comandos.canonico(en), pt, en)
        traduzidos = {en for pt, en in comandos.NOMES_EN.items() if en != pt}
        self.assertFalse(traduzidos & set(comandos.NOMES_EN), "um nome em inglês não pode ser o nome em português de outra coisa")
        self.assertEqual(comandos.nome_en("vendas:proposta"), "sales:proposal")
        self.assertEqual(comandos.canonico("sales:proposal"), "vendas:proposta")
        self.assertEqual(comandos.canonico("algo-meu"), "algo-meu")

    def test_tudo_que_vem_com_o_clave_tem_nome_em_ingles(self):
        faltam = []
        for p in (base.RAIZ / "plugins").iterdir():
            if not p.is_dir():
                continue
            nomes = [p.name] + [c.stem for c in (p / "commands").glob("*.md")] + [s.name for s in (p / "skills").glob("*") if s.is_dir()]
            faltam += [n for n in nomes if n not in comandos.NOMES_EN]
        faltam += [f.stem for f in (base.RAIZ / "fluxos").glob("*.json") if f.stem not in comandos.NOMES_EN]
        faltam += [s.name for s in (base.RAIZ / "skills").glob("*") if s.is_dir() and s.name not in comandos.NOMES_EN]
        faltam += [n for n, _ in comandos.EMBUTIDOS_APP if n not in comandos.NOMES_EN]
        iguais = {"compact", "web", "plugins", "email", "follow-up"}  # o mesmo nome nos dois idiomas
        self.assertEqual([n for n in faltam if n not in iguais], [], "dê um nome em inglês em comandos.NOMES_EN")

    def test_listar_traz_os_dois_nomes(self):
        lista = {c["nome"]: c for c in comandos.listar(None)}
        self.assertEqual(lista["resumo"]["nome_en"], "summary")
        self.assertEqual(lista["vendas:proposta"]["nome_en"], "sales:proposal")
        self.assertEqual(lista["vendas:proposta-comercial"]["nome_en"], "sales:sales-proposal")

    def test_expandir_aceita_os_dois(self):
        pt = comandos.expandir("/vendas:proposta para a Padaria Sol, 3 bolos")
        en = comandos.expandir("/sales:proposal para a Padaria Sol, 3 bolos")
        self.assertEqual(pt["nome"], "vendas:proposta")
        self.assertEqual(en["texto"], pt["texto"])
        skill = comandos.expandir("/sales:sales-proposal Padaria Sol")
        self.assertEqual((skill["tipo"], skill["nome"]), ("skill", "vendas:proposta-comercial"))
        self.assertIsNone(comandos.expandir("/summary"), "comando do app quem trata é a tela")
        self.assertIsNone(comandos.expandir("/nao-existe"))

    def test_comando_da_pessoa_vence_a_traducao(self):
        pasta = Path(tempfile.mkdtemp(prefix="clave-cmd-plan-"))
        try:
            (pasta / ".claude" / "commands").mkdir(parents=True)
            (pasta / ".claude" / "commands" / "plan.md").write_text("Revise o plano: $ARGUMENTS", encoding="utf-8")
            exp = comandos.expandir("/plan o módulo de vendas", pasta)
            self.assertEqual((exp["tipo"], exp["nome"]), ("comando", "plan"))
            lista = {c["nome"]: c for c in comandos.listar(pasta)}
            self.assertEqual(lista["plano"]["nome_en"], "plano", "o /plan do menu é o da pessoa")
            self.assertEqual(lista["plan"]["nome_en"], "plan")
        finally:
            shutil.rmtree(pasta, ignore_errors=True)

    def test_skill_e_fluxo_pelo_nome_em_ingles(self):
        lista = contexto_pasta.skills(None)
        self.assertEqual(contexto_pasta.conteudo_skill(lista, "sales:sales-proposal")["nome"], "vendas:proposta-comercial")
        self.assertEqual(fluxos.modelo("deep-research")["id"], "pesquisa-profunda")


class TestSairDaConta(unittest.TestCase):
    def test_apaga_senhas_volta_o_padrao_e_desliga_rotinas(self):
        segredos.guardar("anthropic", "sk-ant-teste")
        segredos.guardar("email:senha", "x")
        config.salvar({"configurado": True, "nome": "Ana", "tours_vistos": ["geral"], "modelo_chat": "claude-opus-5-5"})
        r = rotinas.salvar(None, "Resumo", {"prompt": "Resuma.", "quando": {"tipo": "diaria", "hora": "08:00"}})
        rotinas.desligar_todas()
        self.assertFalse(banco.rotina(r["id"])["ligada"])
        self.assertEqual(segredos.apagar_tudo(), 2)
        novo = config.resetar()
        self.assertFalse(segredos.existe("anthropic"))
        self.assertFalse(novo["configurado"])
        self.assertEqual((novo["nome"], novo["tours_vistos"], novo["modelo_chat"]), ("", [], "claude-haiku-5-5"))
        self.assertEqual(config.carregar()["nome"], "")
        rotinas.apagar(r["id"])

    def test_nao_mexe_no_que_nao_e_preferencia(self):
        config.salvar({"plugins": {"de-terceiro": {"ligado": False, "fonte": "github:alguem/plugin"}},
                       "ajudantes": {"tutor:excel": "c-123"}, "web_por_padrao_migrada": True})
        novo = config.resetar()
        self.assertEqual(novo["plugins"]["de-terceiro"]["ligado"], False, "plugin desligado continua desligado")
        self.assertEqual(novo["ajudantes"], {"tutor:excel": "c-123"})
        self.assertTrue(novo["web_por_padrao_migrada"], "a migração da 3.1.0 não roda de novo")
        config.salvar({"plugins": {}, "ajudantes": {}})


class TestDesinstalar(unittest.TestCase):
    def test_demonstracao_e_copia_de_desenvolvimento_nao_desinstalam(self):
        # os testes sobem o servidor de verdade a partir da pasta do Clave: ele nunca pode se desinstalar aqui
        s = Servidor(sem_senha=True)
        try:
            status, r = s.pedir("POST", "/api/desinstalar")
            self.assertEqual(status, 400)
            self.assertIn("demonstração", r.get("erro", ""))
        finally:
            s.fechar()
        import desinstalador
        if (base.RAIZ / ".git").exists():
            self.assertIn(".git", desinstalador.motivo_para_nao(base.RAIZ))
        raiz = Path(tempfile.mkdtemp(prefix="clave-desinstalar-"))
        try:
            self.assertIsNone(desinstalador.motivo_para_nao(self._instalacao(raiz)))
            self.assertIsNotNone(desinstalador.motivo_para_nao(raiz), "sem versao.json não é o Clave")
        finally:
            shutil.rmtree(raiz, ignore_errors=True)

    @unittest.skipUnless(sys.platform == "win32", "só no Windows")
    def test_sobrevive_ao_taskkill_da_arvore(self):
        """Do jeito do app: o servidor lança e responde, e o Electron, ao fechar, derruba a árvore dele com
        taskkill /T. O desinstalador tem de estar fora dessa árvore e terminar o serviço sozinho."""
        raiz = Path(tempfile.mkdtemp(prefix="clave-desinstalar-"))
        try:
            pasta = self._instalacao(raiz)
            appdata = raiz / "AppData-Clave"
            appdata.mkdir()
            filho = (f"import os, sys, time; os.environ['CLAVE_DADOS'] = {str(raiz / 'dados-teste')!r}; "
                     f"sys.path.insert(0, {str(base.RAIZ / 'servidor')!r}); from pathlib import Path; import desinstalador; "
                     f"desinstalador.lancar(Path({str(pasta)!r}), os.getpid(), sem_janela=True, "
                     f"atalhos=[{str(raiz / 'nada.lnk')!r}], dados_electron={str(appdata)!r}); "
                     f"print('lancei', flush=True); time.sleep(120)")
            proc = subprocess.Popen([sys.executable, "-c", filho], stdout=subprocess.PIPE, text=True)
            self.assertEqual(proc.stdout.readline().strip(), "lancei")
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            proc.wait(timeout=10)
            proc.stdout.close()
            for _ in range(60):
                if not pasta.exists():
                    break
                time.sleep(0.5)
            self.assertFalse(pasta.exists(), "o desinstalador morreu junto com a árvore do servidor")
            self.assertFalse(appdata.exists())
        finally:
            shutil.rmtree(raiz, ignore_errors=True)

    def _instalacao(self, raiz: Path) -> Path:
        pasta = raiz / "Clave instalado"
        (pasta / "servidor").mkdir(parents=True)
        (pasta / "dados").mkdir()
        (pasta / "versao.json").write_text('{"versao": "4.3.0"}', encoding="utf-8")
        (pasta / "servidor" / "servidor.py").write_text("# servidor", encoding="utf-8")
        (pasta / "dados" / "clave.db").write_bytes(b"x")
        return pasta

    def _atalho(self, caminho: Path, alvo: Path) -> None:
        cmd = (f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{caminho}'); $s.TargetPath = '{alvo}'; "
               f"$s.WorkingDirectory = '{alvo.parent}'; $s.Save()")
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], check=True, capture_output=True)

    def _rodar(self, pasta: Path, atalhos: list[Path], appdata: Path) -> int:
        # pelo -Command, para o PowerShell receber -Atalhos como lista; sem atalhos, um caminho que não existe
        lista = ", ".join(f"'{a}'" for a in atalhos) or f"'{appdata}.lnk'"
        cmd = (f"& '{base.RAIZ / 'ferramentas' / 'desinstalar.ps1'}' -Pasta '{pasta}' -SemJanela "
               f"-DadosElectron '{appdata}' -Atalhos @({lista}); exit $LASTEXITCODE")
        return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                              capture_output=True, text=True).returncode

    @unittest.skipUnless(sys.platform == "win32", "só no Windows")
    def test_apaga_a_pasta_os_atalhos_dela_e_o_appdata(self):
        raiz = Path(tempfile.mkdtemp(prefix="clave-desinstalar-"))
        try:
            pasta = self._instalacao(raiz)
            outra = raiz / "outro programa"
            outra.mkdir()
            meu, alheio = raiz / "Clave.lnk", raiz / "Outro.lnk"
            self._atalho(meu, pasta / ".venv" / "Scripts" / "pythonw.exe")
            self._atalho(alheio, outra / "programa.exe")
            appdata = raiz / "AppData-Clave"
            (appdata / "Cache").mkdir(parents=True)
            self.assertEqual(self._rodar(pasta, [meu, alheio], appdata), 0)
            self.assertFalse(pasta.exists())
            self.assertFalse(meu.exists())
            self.assertTrue(alheio.exists(), "atalho de outra coisa fica")
            self.assertFalse(appdata.exists())
        finally:
            shutil.rmtree(raiz, ignore_errors=True)

    @unittest.skipUnless(sys.platform == "win32", "só no Windows")
    def test_travas_de_seguranca(self):
        raiz = Path(tempfile.mkdtemp(prefix="clave-desinstalar-"))
        try:
            com_git = self._instalacao(raiz)
            (com_git / ".git").mkdir()
            self.assertEqual(self._rodar(com_git, [], raiz / "nada"), 1)
            self.assertTrue((com_git / "dados" / "clave.db").exists(), "cópia com .git não se apaga")
            qualquer = raiz / "uma pasta qualquer"
            (qualquer / "sub").mkdir(parents=True)
            self.assertEqual(self._rodar(qualquer, [], raiz / "nada"), 1)
            self.assertTrue(qualquer.exists(), "pasta que não é o Clave não se apaga")
        finally:
            shutil.rmtree(raiz, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
