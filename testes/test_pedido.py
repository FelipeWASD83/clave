import unittest

import base  # noqa: F401
import config
import pedido
from ferramentas import code as fc


def montar(modelo, **kw):
    padrao = dict(modelo=modelo, esforco="high", pensar=True, mostrar_raciocinio=True, modo="chat", sistema="s",
                  mensagens=[{"role": "user", "content": "oi"}], ferramentas_cliente=[], cfg=dict(config.PADRAO))
    padrao.update(kw)
    return pedido.montar(**padrao)


class TestPedido(unittest.TestCase):
    def test_opus(self):
        kw, usados = montar("claude-opus-5-5", pensar=False)
        self.assertEqual(kw["thinking"]["type"], "adaptive", "no Opus 5.5 o raciocínio não desliga")
        self.assertEqual(kw["thinking"]["display"], "summarized")
        self.assertEqual(kw["thinking"]["block_binding"], {"prefix_mismatch_behavior": "drop_block"})
        self.assertEqual(kw["output_config"], {"effort": "high"})
        self.assertEqual(kw["fallbacks"], "default")
        self.assertIn("server-side-fallback-2026-07-01", kw["betas"])
        self.assertIn("thinking-binding-controls-2026-08-01", kw["betas"])
        self.assertIn("compact-2026-01-12", kw["betas"])
        self.assertEqual(kw["cache_control"], {"type": "ephemeral"})
        self.assertNotIn("temperature", kw)

    def test_sonnet_sem_pensar_usa_between_tools_sem_outros_campos(self):
        kw, _ = montar("claude-sonnet-5-5", pensar=False, esforco="max")
        self.assertEqual(kw["thinking"], {"type": "between_tools"})
        self.assertEqual(kw["output_config"]["effort"], "high", "between_tools só aceita até high")

    def test_haiku(self):
        kw, _ = montar("claude-haiku-5-5", pensar=False, esforco="low")
        self.assertEqual(kw["thinking"], {"type": "disabled"})
        self.assertNotIn("fallbacks", kw, "o Haiku não tem troca de modelo no servidor")
        kw, _ = montar("claude-haiku-5-5", busca_web=True)
        tipos = [t["type"] for t in kw["tools"]]
        self.assertIn("web_search_20250305", tipos, "o Haiku usa a versão básica da busca")

    def test_code_mostra_progresso_quando_raciocinio_escondido(self):
        kw, usados = montar("claude-opus-5-5", modo="code", mostrar_raciocinio=False,
                            ferramentas_cliente=fc.definicoes(True))
        self.assertEqual(kw["thinking"]["display"], "updates")
        self.assertIn("thinking-display-updates-2026-08-18", kw["betas"])
        self.assertEqual(kw["max_tokens"], 64_000)
        self.assertTrue(all(t.get("eager_input_streaming") for t in kw["tools"]))

    def test_modelo_desconhecido_nao_manda_extras(self):
        kw, _ = montar("claude-desconhecido-1")
        self.assertNotIn("thinking", kw)
        self.assertNotIn("output_config", kw)
        self.assertNotIn("fallbacks", kw)
        self.assertEqual(kw["max_tokens"], 16_000)

    def test_desligar_por_erro(self):
        desl = pedido.desligar_por_erro("claude-teste-x", "fallbacks: Extra inputs are not permitted", {"fallbacks", "cache"})
        self.assertEqual(desl, {"fallbacks"})
        self.assertIn("fallbacks", pedido.desligados("claude-teste-x"))
        kw, _ = montar("claude-teste-x")
        self.assertNotIn("fallbacks", kw)

    def test_erro_sem_pista_nao_desliga_nada(self):
        usados = {"fallbacks", "cache", "compactacao", "eager", "web_novo"}
        for msg in ("Your credit balance is too low to access the Anthropic API.",
                    "prompt is too long: 1200000 tokens > 1000000 maximum",
                    "MCP server 'dw' connection failed"):
            self.assertEqual(pedido.desligar_por_erro("claude-teste-y", msg, usados), set(), msg)
        self.assertEqual(pedido.desligados("claude-teste-y"), set())

    def test_mcp_e_memoria(self):
        kw, _ = montar("claude-opus-5-5", memoria_ligada=True, mcp=[{"nome": "dw", "url": "https://x/mcp"}])
        self.assertIn({"type": "memory_20250818", "name": "memory"}, kw["tools"])
        self.assertIn({"type": "mcp_toolset", "mcp_server_name": "dw"}, kw["tools"])
        self.assertEqual(kw["mcp_servers"][0]["name"], "dw")
        self.assertIn("mcp-client-2025-11-20", kw["betas"])

    def test_sem_pensamento(self):
        msgs = [{"role": "user", "content": "a"},
                {"role": "assistant", "content": [{"type": "thinking", "thinking": "", "signature": "s"}, {"type": "text", "text": "b"}]},
                {"role": "assistant", "content": [{"type": "thinking", "thinking": "", "signature": "s"}]}]
        limpo = pedido.sem_pensamento(msgs)
        self.assertEqual(len(limpo), 2)
        self.assertEqual(limpo[1]["content"], [{"type": "text", "text": "b"}])


if __name__ == "__main__":
    unittest.main()
