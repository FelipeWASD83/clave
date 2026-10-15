"""Fichas dos modelos: cartão de apresentação (render, nota de inteligência com fonte) e o banner de 14 dias."""
import unittest
from datetime import date
from pathlib import Path

import base  # noqa: F401
import lancamentos
import modelos

APP = Path(__file__).resolve().parent.parent / "app"


class TestFichas(unittest.TestCase):
    def test_toda_ficha_e_de_modelo_conhecido_e_tem_render(self):
        for mid, f in lancamentos.fichas().items():
            self.assertIn(mid, modelos.MODELOS, mid)
            self.assertTrue((APP / "img" / "modelos" / f"{f['familia']}.svg").is_file(), mid)
            self.assertTrue((APP / "img" / "modelos" / f"render-{f['familia']}.jpg").is_file(), mid)
            ficha = lancamentos.ficha(mid)
            self.assertEqual(ficha["render"], f"img/modelos/render-{f['familia']}.jpg")

    def test_nota_de_inteligencia_tem_fonte(self):
        notas = [f.get("inteligencia") for f in lancamentos.fichas().values()]
        self.assertTrue(all(n is None or 0 < n <= 100 for n in notas))
        if any(n is not None for n in notas):
            fonte = lancamentos.fonte_inteligencia()
            self.assertTrue(fonte["url"].startswith("https://"))
            self.assertTrue(fonte["nota"])

    def test_banner_so_nos_14_dias_e_some_quando_dispensado(self):
        lancado = date.fromisoformat(lancamentos.fichas()["claude-haiku-5-5"]["lancado_em"])
        dentro, fora = date.fromordinal(lancado.toordinal() + 13), date.fromordinal(lancado.toordinal() + 14)
        self.assertIn("claude-haiku-5-5", [f["id"] for f in lancamentos.novidades({}, dentro)])
        self.assertNotIn("claude-haiku-5-5", [f["id"] for f in lancamentos.novidades({}, fora)])
        self.assertEqual([], [f for f in lancamentos.novidades({"modelos_vistos": ["claude-haiku-5-5"]}, dentro)
                              if f["id"] == "claude-haiku-5-5"])


if __name__ == "__main__":
    unittest.main()
