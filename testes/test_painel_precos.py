"""Painel de uso (dias seguidos, mapa, favorito), preços, estimativa pela assinatura e projeção do teto."""
import time
import unittest
from datetime import date, timedelta

import base  # noqa: F401
import banco
import config
import estatisticas
import modelos
import precos


def limpar_uso():
    con = banco.conexao()
    con.execute("DELETE FROM uso")
    con.commit()


def uso(dias_atras: float, modelo="claude-sonnet-5-5", usd=1.0, origem="chat", tokens=1000):
    con = banco.conexao()
    con.execute("INSERT INTO uso (criado_em, modelo, origem, entrada, saida, custo_usd) VALUES (?,?,?,?,?,?)",
                (time.time() - dias_atras * 86400, modelo, origem, tokens, 100, usd))
    con.commit()


class TestSequencias(unittest.TestCase):
    def test_hoje_ontem_e_recorde(self):
        hoje = date(2026, 10, 14)
        dias = [(hoje - timedelta(days=n)).isoformat() for n in (0, 1, 2, 10, 11, 12, 13)]
        self.assertEqual(estatisticas.sequencias(dias, hoje), (3, 4))

    def test_hoje_sem_uso_nao_quebra_a_sequencia_de_ontem(self):
        hoje = date(2026, 10, 14)
        dias = [(hoje - timedelta(days=n)).isoformat() for n in (1, 2)]
        self.assertEqual(estatisticas.sequencias(dias, hoje), (2, 2))

    def test_buraco_zera(self):
        hoje = date(2026, 10, 14)
        self.assertEqual(estatisticas.sequencias([(hoje - timedelta(days=3)).isoformat()], hoje), (0, 1))
        self.assertEqual(estatisticas.sequencias([], hoje), (0, 0))


class TestPrecos(unittest.TestCase):
    def test_custo_de_uma_mensagem(self):
        i = modelos.info("claude-haiku-5-5")
        p = precos.PERFIS["curta"]
        esperado = (p["entrada"] * i["entrada"] + p["cache_lido"] * i["cache_leitura"]
                    + p["cache_escrito"] * i["entrada"] * 1.25 + (p["saida"] + p["raciocinio"]) * i["saida"]) / 1e6
        self.assertAlmostEqual(precos.custo_mensagem("claude-haiku-5-5", "curta"), esperado, places=6)
        self.assertLess(precos.custo_mensagem("claude-haiku-5-5", "curta", raciocinio=False),
                        precos.custo_mensagem("claude-haiku-5-5", "curta"))
        # o Opus 5.5 sempre raciocina: desligar não barateia
        self.assertEqual(precos.custo_mensagem("claude-opus-5-5", "curta", raciocinio=False),
                         precos.custo_mensagem("claude-opus-5-5", "curta"))

    def test_tabela_tem_os_atuais_primeiro(self):
        t = precos.tabela_modelos()
        self.assertTrue(t[0]["atual"])
        self.assertEqual([m["id"] for m in t if m["atual"]][:2], ["claude-opus-5-5", "claude-sonnet-5-5"])
        self.assertEqual(t[0]["cache_escrita"], round(t[0]["entrada"] * 1.25, 4))

    def test_estimativa_pela_assinatura(self):
        r = precos.estimar({"plano": "pro", "janelas": 10, "porcentagem": 60, "perfil": "curta"})
        self.assertEqual(r["mensagens_mes"], round(10 * 0.6 * 45 * 52 / 12))
        sonnet = next(m for m in r["modelos"] if m["id"] == "claude-sonnet-5-5")
        self.assertAlmostEqual(sonnet["custo_mes"], r["mensagens_mes"] * precos.custo_mensagem("claude-sonnet-5-5", "curta"), delta=0.05)
        self.assertEqual(sonnet["mais_barato"], sonnet["custo_mes"] < 20)
        # Max 5x: cinco vezes as mensagens; o preço digitado vale mais que o da tabela
        r5 = precos.estimar({"plano": "max5", "janelas": 10, "porcentagem": 60, "perfil": "curta", "preco": 90})
        self.assertEqual(r5["mensagens_mes"], round(10 * 0.6 * 45 * 5 * 52 / 12))
        self.assertEqual(r5["plano"]["preco"], 90)
        # por mensagens por dia
        rd = precos.estimar({"plano": "pro", "mensagens_dia": 10, "perfil": "media"})
        self.assertEqual(rd["mensagens_mes"], round(10 * 365 / 12))
        self.assertEqual(rd["base"], "mensagens por dia")
        with self.assertRaises(ValueError):
            precos.estimar({"plano": "pro", "janelas": "muitas"})


class TestProjecaoEPainel(unittest.TestCase):
    def setUp(self):
        limpar_uso()
        self.cfg_antes = config.carregar().get("teto_mensal_usd")

    def tearDown(self):
        limpar_uso()
        config.salvar({"teto_mensal_usd": self.cfg_antes})

    def test_ritmo_e_teto(self):
        for d in range(5):  # US$ 1 por dia nos últimos 5 dias (hoje incluído)
            uso(d + 0.01)
        config.salvar({"teto_mensal_usd": 1000})
        r = precos.projecao()
        self.assertAlmostEqual(r["ritmo_dia"], 5 / r["dias_base"], delta=0.02)
        self.assertGreaterEqual(r["previsto_ciclo"], r["gasto"])
        self.assertIn(r["acaba"]["situacao"], ("neste_ciclo", "depois"))
        config.salvar({"teto_mensal_usd": 0.5})
        self.assertEqual(precos.projecao()["acaba"]["situacao"], "ja")

    def test_painel(self):
        for d in range(4):
            uso(d + 0.01, modelo="claude-haiku-5-5", tokens=500)
        uso(0.02, modelo="claude-opus-5-5", tokens=5000)
        uso(0.03, modelo="claude-haiku-5-5", origem="titulo")  # título automático não conta para o favorito
        p = estatisticas.painel()
        self.assertEqual(p["dias_seguidos"], 4)
        self.assertEqual(p["favorito"]["modelo"], "claude-haiku-5-5")
        self.assertEqual(p["favorito"]["pedidos"], 4)
        self.assertEqual(len(p["dias7"]), 7)
        self.assertTrue(all(len(m["tokens"]) == 7 for m in p["ultimos7"]))
        self.assertEqual(p["ultimos7"][0]["modelo"], "claude-opus-5-5", "o que mais gastou token vem primeiro")
        self.assertEqual(len(p["mapa"]) % 7, (date.today().weekday() + 1) % 7)
        self.assertEqual(p["mapa"][-1]["dia"], date.today().isoformat())
        self.assertGreater(p["mapa"][-1]["tokens"], 0)


if __name__ == "__main__":
    unittest.main()
