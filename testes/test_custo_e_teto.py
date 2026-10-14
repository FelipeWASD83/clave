import unittest
from datetime import date

import base  # noqa: F401
import banco
import config
import custo
import orcamento


class TestCusto(unittest.TestCase):
    def test_opus_simples(self):
        c = custo.custo_uso("claude-opus-5-5", {"input_tokens": 1_000_000, "output_tokens": 1_000_000})
        self.assertAlmostEqual(c["usd"], 4 + 20)

    def test_cache_escrita_5m_e_1h(self):
        uso = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 300_000,
               "cache_creation": {"ephemeral_5m_input_tokens": 100_000, "ephemeral_1h_input_tokens": 200_000}}
        c = custo.custo_uso("claude-sonnet-5-5", uso)
        self.assertAlmostEqual(c["usd"], 0.1 * 2 * 1.25 + 0.2 * 2 * 2.0)

    def test_leitura_de_cache(self):
        c = custo.custo_uso("claude-opus-5-5", {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 1_000_000})
        self.assertAlmostEqual(c["usd"], 0.20)

    def test_haiku_acima_de_100_mil_custa_5x(self):
        curto = custo.custo_uso("claude-haiku-5-5", {"input_tokens": 100_000, "output_tokens": 0})
        longo = custo.custo_uso("claude-haiku-5-5", {"input_tokens": 100_001, "output_tokens": 0})
        self.assertAlmostEqual(curto["usd"], 0.01)
        self.assertAlmostEqual(longo["usd"], 100_001 * 0.5 / 1e6)

    def test_iteracoes_somam_e_buscas(self):
        uso = {"input_tokens": 999, "output_tokens": 999, "server_tool_use": {"web_search_requests": 3},
               "iterations": [{"type": "compaction", "input_tokens": 1_000_000, "output_tokens": 0},
                              {"type": "message", "input_tokens": 0, "output_tokens": 1_000_000}]}
        c = custo.custo_uso("claude-opus-5-5", uso)
        self.assertAlmostEqual(c["usd"], 4 + 20 + 0.03)
        self.assertEqual(c["buscas"], 3)

    def test_modo_rapido_dobra(self):
        c = custo.custo_uso("claude-opus-5-5", {"input_tokens": 1_000_000, "output_tokens": 0, "speed": "fast"})
        self.assertAlmostEqual(c["usd"], 8)

    def test_modelo_desconhecido_e_estimado_e_caro(self):
        c = custo.custo_uso("claude-futuro-9", {"input_tokens": 1_000_000, "output_tokens": 0})
        self.assertTrue(c["estimado"])
        self.assertAlmostEqual(c["usd"], 10)

    def test_contexto_usado(self):
        self.assertEqual(custo.contexto_usado({"input_tokens": 10, "cache_read_input_tokens": 20,
                                               "cache_creation_input_tokens": 5}), 35)


class TestTeto(unittest.TestCase):
    def test_ciclo_virada_no_dia(self):
        ini, fim = orcamento.ciclo(date(2026, 10, 14), 7)
        self.assertEqual((ini.date(), fim.date()), (date(2026, 10, 7), date(2026, 11, 7)))
        ini, fim = orcamento.ciclo(date(2026, 10, 3), 7)
        self.assertEqual((ini.date(), fim.date()), (date(2026, 9, 7), date(2026, 10, 7)))

    def test_ciclo_dia_31_em_fevereiro(self):
        ini, fim = orcamento.ciclo(date(2027, 2, 15), 31)
        self.assertEqual((ini.date(), fim.date()), (date(2027, 1, 31), date(2027, 2, 28)))

    def test_ciclo_virada_de_ano(self):
        ini, fim = orcamento.ciclo(date(2026, 12, 20), 10)
        self.assertEqual((ini.date(), fim.date()), (date(2026, 12, 10), date(2027, 1, 10)))

    def test_bloqueio_e_alertas(self):
        config.salvar({"teto_mensal_usd": 1.0, "ao_atingir": "bloquear", "dia_virada": 1, "alertas_vistos": {}, "ajustes": {}})
        self.assertTrue(orcamento.pode_gastar()[0])
        banco.registrar_uso(None, None, "claude-haiku-5-5", "teste", {"usd": 0.85})
        self.assertEqual(orcamento.novo_alerta(), 80)
        self.assertIsNone(orcamento.novo_alerta(), "o mesmo alerta não pode aparecer duas vezes")
        banco.registrar_uso(None, None, "claude-haiku-5-5", "teste", {"usd": 0.2})
        ok, motivo = orcamento.pode_gastar()
        self.assertFalse(ok)
        self.assertIn("teto", motivo)
        config.salvar({"ao_atingir": "avisar"})
        self.assertTrue(orcamento.pode_gastar()[0])
        s = orcamento.situacao()
        config.salvar({"ajustes": {s["chave"]: 5.0}})
        self.assertAlmostEqual(orcamento.situacao()["gasto"], s["gasto_app"] + 5.0)
        config.salvar({"teto_mensal_usd": None, "ajustes": {}, "ao_atingir": "bloquear"})
        self.assertTrue(orcamento.pode_gastar()[0])


class TestBackup(unittest.TestCase):
    def test_importar_ignora_coluna_estranha_e_nao_duplica_uso(self):
        dados = {
            "formato": "clave-backup-1",
            "conversas": [{"x) VALUES (1); DROP TABLE conversas; --": 1}],
            # data de 2001: não entra no ciclo de nenhum outro teste
            "uso": [{"id": 999, "criado_em": 1_000_000_000.0, "modelo": "claude-haiku-5-5", "custo_usd": 0.5,
                     "coluna_que_nao_existe": "x"}],
        }
        r1 = banco.importar_tudo(dados)
        self.assertEqual(r1["conversas"], 0)
        self.assertEqual(r1["uso"], 1)
        self.assertEqual(banco.importar_tudo(dados)["uso"], 0, "importar o mesmo backup duas vezes não pode dobrar o gasto")
        banco.listar_conversas()  # a tabela continua lá
        with self.assertRaises(ValueError):
            banco.importar_tudo({"formato": "outro"})


if __name__ == "__main__":
    unittest.main()
