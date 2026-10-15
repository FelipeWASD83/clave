import shutil
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path

import base  # noqa: F401
import banco
import fluxos
import permissoes
import rotinas


class TestProposta(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp(prefix="clave-fluxo-")

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def entrada(self, **extra):
        return {"titulo": "T", "objetivo": "O", "etapas": [
            {"nome": "Planejar", "agente": "planejador", "tarefa": "planeje"},
            {"nome": "Fazer", "agente": "executor", "modelo": "sonnet", "tarefa": "faça", "pode": ["ler", "editar"]},
            {"nome": "Revisar A", "agente": "revisor", "tarefa": "revise"},
            {"nome": "Revisar B", "modelo": "haiku", "tarefa": "revise", "paralelo": True},
        ], **extra}

    def test_agente_da_os_padroes_e_paralelo_agrupa(self):
        p = fluxos.normalizar(self.entrada(), fid="f1", pasta=self.pasta, modelo_padrao="claude-opus-5-5")
        e = p["etapas"]
        self.assertEqual(e[0]["modelo"], "claude-opus-5-5")         # do agente planejador
        self.assertEqual(e[0]["esforco"], "high")
        self.assertEqual(e[0]["pode"], ["ler"])
        self.assertEqual(e[1]["modelo"], "claude-sonnet-5-5")       # a etapa escolheu
        self.assertEqual([x["grupo"] for x in e], [0, 1, 2, 2])
        self.assertLess(p["estimativa"]["min"], p["estimativa"]["max"])
        self.assertGreaterEqual(p["teto_usd"], 0.5)

    def test_no_chat_etapa_so_pesquisa(self):
        p = fluxos.normalizar(self.entrada(), fid="f2", pasta=None, modelo_padrao="claude-opus-5-5")
        self.assertTrue(all(set(x["pode"]) <= {"web"} for x in p["etapas"]))

    def test_erros_e_agente_bloqueado(self):
        with self.assertRaises(fluxos.ErroFluxo):
            fluxos.normalizar({"titulo": "x", "objetivo": "y", "etapas": []}, fid="f", pasta=None, modelo_padrao="x")
        with self.assertRaises(fluxos.ErroFluxo):
            fluxos.normalizar({"titulo": "x", "objetivo": "y", "etapas": [{"nome": "a", "tarefa": "b"}] * 9},
                              fid="f", pasta=None, modelo_padrao="claude-haiku-5-5")
        regras = [permissoes.Regra("deny", "Agent(revisor)", "app")]
        with self.assertRaises(fluxos.ErroFluxo):
            fluxos.normalizar(self.entrada(), fid="f", pasta=self.pasta, modelo_padrao="claude-opus-5-5", regras=regras)
        p = fluxos.normalizar({"titulo": "x", "objetivo": "y", "etapas": [{"nome": "a", "agente": "fantasma",
                                                                             "tarefa": "b"}]},
                              fid="f", pasta=None, modelo_padrao="claude-haiku-5-5")
        self.assertIn("não existe", p["etapas"][0]["aviso"])

    def test_estimativa_segue_o_modelo(self):
        caro = fluxos.estimar_etapa("claude-opus-5-5", "high", ["ler", "editar"])
        barato = fluxos.estimar_etapa("claude-haiku-5-5", "high", ["ler", "editar"])
        self.assertGreater(caro[1], barato[1] * 10)

    def test_ajustes_da_pessoa(self):
        p = fluxos.normalizar(self.entrada(), fid="f3", pasta=self.pasta, modelo_padrao="claude-opus-5-5")
        antes = p["estimativa"]["max"]
        p = fluxos.aplicar_ajustes(p, {"etapas": [{"i": 0, "modelo": "haiku"}, {"i": 3, "tirar": True}], "teto_usd": 2})
        self.assertEqual(p["etapas"][0]["modelo"], "claude-haiku-5-5")
        self.assertEqual(len(p["etapas"]), 3)
        self.assertLess(p["estimativa"]["max"], antes)
        self.assertEqual(p["teto_usd"], 2)
        with self.assertRaises(fluxos.ErroFluxo):
            fluxos.aplicar_ajustes(p, {"etapas": [{"i": e["i"], "tirar": True} for e in p["etapas"]]})

    def test_cofre(self):
        c = fluxos.Cofre(1.0)
        c.somar(0.6)
        self.assertFalse(c.estourou())
        c.somar(0.5)
        self.assertTrue(c.estourou())
        self.assertFalse(fluxos.Cofre(0).estourou())

    def test_modelos_de_fluxo(self):
        ids = [m["id"] for m in fluxos.listar_modelos()]
        for i in ("planejar-fazer-testar", "pesquisa-profunda", "revisao-em-paralelo", "planilha-grande",
                  "escrever-e-revisar"):
            self.assertIn(i, ids)
        m = fluxos.salvar_modelo({"nome": "Meu fluxo", "etapas": [{"nome": "A", "tarefa": "x", "modelo": "haiku"}]})
        self.assertEqual(m["id"], "meu-fluxo")
        self.assertTrue(fluxos.modelo("meu-fluxo")["editavel"])
        self.assertIn("Meu fluxo", fluxos.texto_para_comando(m, "fazer X"))
        fluxos.apagar_modelo("meu-fluxo")
        self.assertIsNone(fluxos.modelo("meu-fluxo"))
        with self.assertRaises(fluxos.ErroFluxo):
            fluxos.apagar_modelo("pesquisa-profunda")  # do app: não apaga

    def test_definicao_lista_os_agentes(self):
        d = fluxos.definicao(None)
        self.assertIn("planejador", d["description"])
        self.assertIn("chat", d["description"])


class TestRotinas(unittest.TestCase):
    def test_proxima(self):
        base_t = datetime(2026, 10, 14, 9, 30).timestamp()  # quarta-feira
        diaria = rotinas.proxima({"tipo": "diaria", "hora": "08:00"}, base_t)
        self.assertEqual(datetime.fromtimestamp(diaria), datetime(2026, 10, 15, 8, 0))
        hoje = rotinas.proxima({"tipo": "diaria", "hora": "10:00"}, base_t)
        self.assertEqual(datetime.fromtimestamp(hoje), datetime(2026, 10, 14, 10, 0))
        semanal = rotinas.proxima({"tipo": "semanal", "hora": "08:00", "dias": [0, 4]}, base_t)  # seg e sex
        self.assertEqual(datetime.fromtimestamp(semanal), datetime(2026, 10, 16, 8, 0))
        horas = rotinas.proxima({"tipo": "horas", "a_cada": 3}, base_t)
        self.assertEqual(datetime.fromtimestamp(horas), datetime(2026, 10, 14, 12, 30))
        with self.assertRaises(rotinas.ErroRotina):
            rotinas.proxima({"tipo": "semanal", "hora": "08:00", "dias": []}, base_t)
        with self.assertRaises(rotinas.ErroRotina):
            rotinas.proxima({"tipo": "diaria", "hora": "25:00"}, base_t)
        self.assertEqual(rotinas.descrever({"tipo": "semanal", "hora": "07:15", "dias": [0, 2]}), "seg, qua, às 07:15")

    def test_validar(self):
        with self.assertRaises(rotinas.ErroRotina):
            rotinas.validar("", {"prompt": "x"})
        with self.assertRaises(rotinas.ErroRotina):
            rotinas.validar("a", {"prompt": ""})
        with self.assertRaises(rotinas.ErroRotina):
            rotinas.validar("a", {"prompt": "x", "modo": "code", "pasta": "C:/nao/existe/mesmo"})
        with self.assertRaises(rotinas.ErroRotina):
            rotinas.validar("a", {"prompt": "x", "teto_usd": 0})
        ok = rotinas.validar("a", {"prompt": "x", "quando": {"tipo": "horas", "a_cada": 2}})
        self.assertEqual(ok["modo"], "chat")

    def test_relogio_roda_so_as_vencidas_e_pula_as_muito_atrasadas(self):
        rodadas = []
        original = rotinas.rodar
        rotinas.rodar = lambda rid, motivo="agendada": rodadas.append(rid)
        try:
            for r in banco.listar_rotinas():
                banco.apagar_rotina(r["id"])
            agora = time.time()
            venceu = banco.salvar_rotina(None, "venceu", rotinas.validar("v", {"prompt": "x"}), True, agora - 60)
            futura = banco.salvar_rotina(None, "futura", rotinas.validar("f", {"prompt": "x"}), True, agora + 3600)
            velha = banco.salvar_rotina(None, "velha", rotinas.validar("o", {"prompt": "x"}), True, agora - 86400)
            windows = banco.salvar_rotina(None, "win", {**rotinas.validar("w", {"prompt": "x"}), "agendador": True},
                                          True, agora - 60)
            desligada = banco.salvar_rotina(None, "off", rotinas.validar("d", {"prompt": "x"}), False, agora - 60)
            rotinas.Relogio().uma_volta(agora)
            self.assertEqual(rodadas, [venceu["id"]])
            self.assertIn("pulada", banco.rotina(velha["id"])["ultimo_status"])
            self.assertGreater(banco.rotina(venceu["id"])["proxima"], agora)
            for r in (venceu, futura, velha, windows, desligada):
                banco.apagar_rotina(r["id"])
        finally:
            rotinas.rodar = original


if __name__ == "__main__":
    unittest.main()
