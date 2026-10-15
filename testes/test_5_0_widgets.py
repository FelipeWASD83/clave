"""5.0: os widgets (cartões visuais na conversa), o mapa (endereços e tiles do OpenStreetMap) e as imagens de fora."""
import http.client
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import base
import config
import i18n
import mapas
import widgets
from rotas import Erro
from test_servidor import Servidor


def _cab(**valores) -> http.client.HTTPMessage:
    m = http.client.HTTPMessage()
    for k, v in valores.items():
        m[k.replace("_", "-")] = v
    return m


class _Resposta:
    def __init__(self, corpo=b"", status=200, cab=None):
        self.status, self._corpo, self.headers = status, corpo, cab or _cab()

    def read(self, n=-1):
        return self._corpo if n is None or n < 0 else self._corpo[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _ExFalso:
    def __init__(self):
        self.eventos = []

    def emitir(self, ev):
        self.eventos.append(ev)

    def resultado(self, tid, conteudo, erro=False):
        r = {"type": "tool_result", "tool_use_id": tid, "content": conteudo}
        if erro:
            r["is_error"] = True
        return r


def _norm(tipo, dados, **kw):
    return widgets.normalizar({"tipo": tipo, "titulo": "Teste", "dados": dados}, **kw)


PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


# ======================= normalização =======================

class TestNormalizarProdutos(unittest.TestCase):
    def test_valido_com_numero_em_texto_e_link_http_fora(self):
        w, avisos = _norm("produtos", {"visto_em": "2026-10-15", "itens": [
            {"nome": "Fone A", "preco": "R$ 1.299,90", "loja": "Loja 1", "link": "https://loja.example/a", "nota": 4.6},
            {"nome": "Fone B", "preco": 999, "moeda": "usd", "link": "http://loja.example/b", "imagem": "javascript:alert(1)"}]})
        a, b = w["dados"]["itens"]
        self.assertEqual(a["preco"], 1299.9)
        self.assertEqual(a["moeda"], "BRL", "BRL é o padrão")
        self.assertEqual(a["nota"], {"valor": 4.6, "fonte": ""})
        self.assertEqual(b["moeda"], "USD")
        self.assertNotIn("link", b, "link que não é https sai")
        self.assertNotIn("imagem", b)
        self.assertEqual(len([x for x in avisos if "https" in x]), 2)
        self.assertEqual(w["dados"]["visto_em"], "2026-10-15")
        self.assertEqual(w["titulo"], "Teste")

    def test_invalidos(self):
        with self.assertRaisesRegex(widgets.ErroWidget, "visto_em"):
            _norm("produtos", {"itens": [{"nome": "A", "preco": 1}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "preco"):
            _norm("produtos", {"visto_em": "2026-10-15", "itens": [{"nome": "A", "preco": "barato"}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "preco"):
            _norm("produtos", {"visto_em": "2026-10-15", "itens": [{"nome": "A", "preco": -3}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "sem nome"):
            _norm("produtos", {"visto_em": "2026-10-15", "itens": [{"preco": 3}]})
        with self.assertRaises(widgets.ErroWidget):
            _norm("produtos", {"visto_em": "2026-10-15", "itens": []})

    def test_limites(self):
        w, avisos = _norm("produtos", {"visto_em": "hoje", "moeda": "€", "itens": [
            {"nome": "x" * 500, "preco": i, "moeda": "reais"} for i in range(30)]})
        self.assertEqual(len(w["dados"]["itens"]), 24)
        self.assertLessEqual(len(w["dados"]["itens"][0]["nome"]), 140)
        self.assertEqual(w["dados"]["itens"][0]["moeda"], "EUR", "moeda inválida cai no padrão do widget")
        self.assertTrue(any("primeiros 24" in a for a in avisos))
        self.assertTrue(any("reais" in a for a in avisos))


class TestNormalizarMapa(unittest.TestCase):
    def test_coordenadas_e_endereco(self):
        achados = {"Av. Paulista, 1578, São Paulo": {"lat": -23.5614, "lon": -46.6559, "nome": "MASP"}}
        w, avisos = _norm("mapa", {"rota": True, "pontos": [
            {"nome": "Ibirapuera", "lat": "-23,5874", "lon": -46.6576, "descricao": "Parque"},
            {"nome": "MASP", "endereco": "Av. Paulista, 1578, São Paulo"},
            {"nome": "Lugar nenhum", "endereco": "Rua Que Não Existe 999"}]}, geocodificar=lambda e: achados.get(e))
        pontos = w["dados"]["pontos"]
        self.assertEqual([p["nome"] for p in pontos], ["Ibirapuera", "MASP"])
        self.assertEqual(pontos[0]["lat"], -23.5874)
        self.assertEqual((pontos[1]["lat"], pontos[1]["lon"]), (-23.5614, -46.6559))
        self.assertTrue(w["dados"]["rota"])
        self.assertTrue(any("Lugar nenhum" in a for a in avisos), "o ponto que não foi achado aparece no resultado")

    def test_invalidos(self):
        with self.assertRaisesRegex(widgets.ErroWidget, "lat"):
            _norm("mapa", {"pontos": [{"nome": "X", "lat": 95, "lon": 0}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "lat e lon"):
            _norm("mapa", {"pontos": [{"nome": "X"}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "Nenhum ponto"):
            _norm("mapa", {"pontos": [{"nome": "X", "endereco": "nada"}]}, geocodificar=lambda e: None)

    def test_sem_internet_nao_trava_os_outros_pontos(self):
        chamadas = []

        def falha(e):
            chamadas.append(e)
            raise mapas.SemConexao("sem conexão com o serviço de endereços")
        w, avisos = _norm("mapa", {"pontos": [{"nome": "A", "lat": 1, "lon": 2}, {"nome": "B", "endereco": "b"},
                                              {"nome": "C", "endereco": "c"}]}, geocodificar=falha)
        self.assertEqual(len(chamadas), 1, "depois da primeira falha não tenta de novo")
        self.assertEqual(len(w["dados"]["pontos"]), 1)
        self.assertTrue(any("falhou" in a for a in avisos))

    def test_rota_de_um_ponto_so_vira_falso(self):
        w, _ = _norm("mapa", {"rota": True, "pontos": [{"nome": "A", "lat": 1, "lon": 2}]})
        self.assertFalse(w["dados"]["rota"])


class TestNormalizarRecomendacoes(unittest.TestCase):
    def test_valido_com_aliases(self):
        w, avisos = _norm("recomendacoes", {"itens": [
            {"titulo": "Interestelar", "tipo": "movie", "ano": "2014", "generos": "ficção, drama", "onde": ["Max", "Prime"],
             "duracao": 169, "nota": {"valor": "8,7", "fonte": "IMDb"}, "por_que": "Ciência e emoção."},
            {"titulo": "Algo", "tipo": "coisa estranha", "ano": "logo", "por_que": "Porque sim."}]})
        a, b = w["dados"]["itens"]
        self.assertEqual(a["tipo"], "filme")
        self.assertEqual(a["ano"], 2014)
        self.assertEqual(a["generos"], ["ficção", "drama"])
        self.assertEqual(a["onde"], "Max, Prime")
        self.assertEqual(a["duracao"], "169 min")
        self.assertEqual(a["nota"], {"valor": 8.7, "fonte": "IMDb"})
        self.assertEqual(b["tipo"], "outro")
        self.assertNotIn("ano", b)
        self.assertTrue(any("ano" in x for x in avisos))

    def test_sem_por_que(self):
        with self.assertRaisesRegex(widgets.ErroWidget, "por_que"):
            _norm("recomendacoes", {"itens": [{"titulo": "X", "tipo": "serie"}]})


class TestNormalizarDesenho(unittest.TestCase):
    def test_todas_as_formas(self):
        w, avisos = _norm("desenho", {"largura": 5, "altura": 4, "unidade": "metros", "formas": [
            {"tipo": "retangulo", "x": 0.5, "y": 0.5, "largura": 2, "altura": 1, "rotulo": "Sofá", "cor": "cinza", "preenchido": True, "rotacao": 10},
            {"tipo": "circle", "x": 4, "y": 1, "raio": 0.4, "cor": "green"},
            {"tipo": "linha", "x1": 1, "y1": 0, "x2": 3, "y2": 0, "cor": "#ff00ff"},
            {"tipo": "arrow", "x1": 4.8, "y1": 3, "x2": 4, "y2": 3},
            {"tipo": "texto", "x": 2.5, "y": 2, "texto": "Sala", "tamanho": "large"},
            {"tipo": "poligono", "pontos": [[0, 0], {"x": 1, "y": 0}, [1, 1]], "preenchido": True},
            {"tipo": "cota", "x1": 0, "y1": 4, "x2": 5, "y2": 4, "deslocamento": 0.3}],
            "legenda": [{"cor": "azul", "rotulo": "Janela"}, {"rotulo": ""}]})
        d = w["dados"]
        self.assertEqual(d["unidade"], "m")
        self.assertEqual([f["tipo"] for f in d["formas"]], ["retangulo", "circulo", "linha", "seta", "texto", "poligono", "cota"])
        self.assertEqual(d["formas"][1]["cor"], "verde", "nome de cor em inglês vira o da paleta")
        self.assertNotIn("cor", d["formas"][2], "cor fora da paleta sai")
        self.assertTrue(any("#ff00ff" in a for a in avisos))
        self.assertEqual(d["formas"][4]["tamanho"], "grande")
        self.assertEqual(d["formas"][5]["pontos"], [[0, 0], [1, 0], [1, 1]])
        self.assertEqual(d["legenda"], [{"cor": "azul", "rotulo": "Janela"}])

    def test_invalidos(self):
        with self.assertRaisesRegex(widgets.ErroWidget, "Confira a unidade"):
            _norm("desenho", {"largura": 5, "altura": 4, "formas": [{"tipo": "retangulo", "x": 300, "y": 0, "largura": 1, "altura": 1}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "unidade"):
            _norm("desenho", {"largura": 5, "altura": 4, "unidade": "léguas", "formas": [{"tipo": "texto", "x": 1, "y": 1, "texto": "a"}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "tipo desconhecido"):
            _norm("desenho", {"largura": 5, "altura": 4, "formas": [{"tipo": "estrela", "x": 1, "y": 1}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "mesmo ponto"):
            _norm("desenho", {"largura": 5, "altura": 4, "formas": [{"tipo": "linha", "x1": 1, "y1": 1, "x2": 1, "y2": 1}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "largura"):
            _norm("desenho", {"largura": 0, "altura": 4, "formas": [{"tipo": "texto", "x": 1, "y": 1, "texto": "a"}]})


class TestNormalizarGrafico(unittest.TestCase):
    def test_barras_e_linhas(self):
        w, _ = _norm("grafico", {"tipo_grafico": "bar", "rotulos": ["jan", "fev"], "unidade": "US$",
                                 "series": [{"nome": "Chat", "valores": [1, "2,5"], "cor": "roxo"}]})
        self.assertEqual(w["dados"]["tipo_grafico"], "barras")
        self.assertEqual(w["dados"]["series"][0]["valores"], [1, 2.5])
        w, _ = _norm("grafico", {"tipo_grafico": "linhas", "rotulos": ["a", "b", "c"], "series": {"valores": [1, None, 3]}})
        self.assertEqual(w["dados"]["series"][0]["valores"], [1, None, 3], "linha aceita buraco")
        with self.assertRaises(widgets.ErroWidget):
            _norm("grafico", {"tipo_grafico": "barras", "rotulos": ["a", "b"], "series": [{"valores": [1, None]}]})

    def test_quantidade_de_valores_errada(self):
        with self.assertRaisesRegex(widgets.ErroWidget, "um valor por rótulo"):
            _norm("grafico", {"rotulos": ["a", "b", "c"], "series": [{"nome": "S", "valores": [1, 2]}]})

    def test_pizza(self):
        with self.assertRaisesRegex(widgets.ErroWidget, "negativos"):
            _norm("grafico", {"tipo_grafico": "pie", "rotulos": ["a", "b"], "series": [{"valores": [1, -1]}]})
        w, avisos = _norm("grafico", {"tipo_grafico": "pizza", "rotulos": [f"f{i}" for i in range(15)],
                                      "series": [{"valores": list(range(1, 16))}, {"valores": [0] * 15}]})
        d = w["dados"]
        self.assertEqual(len(d["series"]), 1)
        self.assertEqual(len(d["rotulos"]), 12)
        self.assertEqual(d["rotulos"][-1], "Outros (fatias menores)")
        self.assertEqual(sum(d["series"][0]["valores"]), sum(range(1, 16)), "nada some ao juntar as fatias")
        self.assertEqual(len(avisos), 2)


class TestNormalizarOutros(unittest.TestCase):
    def test_comparacao(self):
        w, avisos = _norm("comparacao", {"colunas": ["A", "B", "C"], "linhas": [
            {"criterio": "Preço", "valores": [10, 20.5, "caro"], "melhor": "a"},
            {"criterio": "Garantia", "valores": [True, False, None], "melhor": 7}]})
        l1, l2 = w["dados"]["linhas"]
        self.assertEqual(l1["melhor"], 0, "melhor pelo nome da coluna vira índice")
        self.assertEqual(l1["valores"], [10, 20.5, "caro"])
        self.assertNotIn("melhor", l2)
        self.assertEqual(l2["valores"], [True, False, None])
        self.assertTrue(any("Garantia" in a for a in avisos))
        with self.assertRaisesRegex(widgets.ErroWidget, "um por coluna"):
            _norm("comparacao", {"colunas": ["A", "B"], "linhas": [{"criterio": "x", "valores": [1]}]})
        with self.assertRaisesRegex(widgets.ErroWidget, "colunas"):
            _norm("comparacao", {"colunas": ["A"], "linhas": [{"criterio": "x", "valores": [1]}]})

    def test_linha_do_tempo(self):
        w, _ = _norm("linha_do_tempo", {"eventos": [{"data": 1969, "titulo": "Apollo 11", "descricao": "Lua"}]})
        self.assertEqual(w["dados"]["eventos"], [{"data": "1969", "titulo": "Apollo 11", "descricao": "Lua"}])
        with self.assertRaisesRegex(widgets.ErroWidget, "data e titulo"):
            _norm("linha_do_tempo", {"eventos": [{"data": "1969"}]})

    def test_checklist(self):
        w, _ = _norm("checklist", {"itens": ["Passaporte", {"texto": "Carregador", "feito": True}]})
        self.assertEqual(w["dados"]["itens"], [{"texto": "Passaporte", "feito": False}, {"texto": "Carregador", "feito": True}])
        with self.assertRaisesRegex(widgets.ErroWidget, "sem texto"):
            _norm("checklist", {"itens": [{"feito": True}]})

    def test_entrada_errada(self):
        with self.assertRaisesRegex(widgets.ErroWidget, "tipo precisa"):
            widgets.normalizar({"tipo": "foguete", "titulo": "x", "dados": {}})
        with self.assertRaisesRegex(widgets.ErroWidget, "dados precisa"):
            widgets.normalizar({"tipo": "checklist", "titulo": "x", "dados": [1]})
        w, _ = widgets.normalizar({"tipo": "timeline", "titulo": "x", "dados": json.dumps({"eventos": [{"data": "1", "titulo": "a"}]})})
        self.assertEqual(w["tipo"], "linha_do_tempo", "alias em inglês e dados em texto JSON também valem")

    def test_grande_demais(self):
        formas = [{"tipo": "poligono", "pontos": [[i % 10 + 0.123457, (i * 3) % 10 + 0.654321] for i in range(60)],
                   "rotulo": "x" * 60}] * 200
        w, _ = _norm("desenho", {"largura": 11, "altura": 11, "formas": formas})
        self.assertEqual(len(w["dados"]["formas"]), 200, "o maior desenho permitido ainda cabe")
        with mock.patch.object(widgets, "MAX_JSON", len(json.dumps(w, ensure_ascii=False)) - 1):
            with self.assertRaisesRegex(widgets.ErroWidget, "grande demais"):
                _norm("desenho", {"largura": 11, "altura": 11, "formas": formas})


# ======================= a ferramenta =======================

class TestFerramenta(unittest.TestCase):
    def test_oferecer(self):
        cfg = {"widgets_ligados": True}
        self.assertEqual([d["name"] for d in widgets.oferecer(None, modo="chat", op={}, cfg=cfg, etapa=False, pasta=None)], ["mostrar_widget"])
        self.assertTrue(widgets.oferecer(None, modo="code", op={}, cfg=cfg, etapa=False, pasta=Path(".")))
        self.assertEqual(widgets.oferecer(None, modo="code", op={}, cfg=cfg, etapa=True, pasta=None), [], "etapa de fluxo")
        self.assertEqual(widgets.oferecer(None, modo="chat", op={"rotina": True}, cfg=cfg, etapa=False, pasta=None), [], "rotina")
        self.assertEqual(widgets.oferecer(None, modo="tutor", op={}, cfg=cfg, etapa=False, pasta=None), [])
        self.assertEqual(widgets.oferecer(None, modo="chat", op={}, cfg={"widgets_ligados": False}, etapa=False, pasta=None), [])
        self.assertTrue(widgets.oferecer(None, modo="chat", op={}, cfg={}, etapa=False, pasta=None), "ligado por padrão")
        self.assertTrue(config.PADRAO.get("widgets_ligados", True))

    def test_descricoes_tem_ingles(self):
        cat = json.loads((base.RAIZ / "servidor" / "i18n" / "en" / "widgets.json").read_text(encoding="utf-8"))
        descricoes = []

        def passar(no):
            if isinstance(no, dict):
                for k, v in no.items():
                    descricoes.append(v) if k == "description" and isinstance(v, str) else passar(v)
            elif isinstance(no, list):
                for x in no:
                    passar(x)
        passar(widgets.definicoes_para_teste())
        self.assertEqual(len(descricoes), 4)
        self.assertEqual([d for d in descricoes if d not in cat], [])

    def test_executar_salva_e_emite(self):
        ex = _ExFalso()
        r = widgets.executar(ex, "toolu_teste01", "mostrar_widget",
                             {"tipo": "checklist", "titulo": "Viagem", "dados": {"itens": ["A", "B"]}}, {}, "chat")
        self.assertFalse(r.get("is_error"))
        self.assertIn("Viagem", r["content"])
        tipos = [e["tipo"] for e in ex.eventos]
        self.assertEqual(tipos, ["ferramenta_rodando", "widget", "ferramenta_fim"])
        self.assertEqual(ex.eventos[1]["id"], "toolu_teste01")
        self.assertEqual(ex.eventos[1]["widget"]["dados"]["itens"][1]["texto"], "B")
        salvo = json.loads((config.DADOS / "widgets" / "toolu_teste01.json").read_text(encoding="utf-8"))
        self.assertEqual(salvo, ex.eventos[1]["widget"])

    def test_executar_invalido_volta_erro_para_o_claude(self):
        ex = _ExFalso()
        r = widgets.executar(ex, "toolu_teste02", "mostrar_widget", {"tipo": "grafico", "titulo": "x", "dados": {}}, {}, "chat")
        self.assertTrue(r["is_error"])
        self.assertIn("Corrija", r["content"])
        self.assertTrue(ex.eventos[-1]["erro"])
        self.assertFalse((config.DADOS / "widgets" / "toolu_teste02.json").exists())

    def test_marcar_checklist(self):
        widgets.salvar("toolu_marcar", _norm("checklist", {"itens": ["a", "b", "c"]})[0])
        w = widgets.marcar("toolu_marcar", [0, 2])
        self.assertEqual([i["feito"] for i in w["dados"]["itens"]], [True, False, True])
        self.assertEqual(widgets.ler("toolu_marcar"), w)
        for ruim in ([5], "0", [True]):
            with self.assertRaises(Erro):
                widgets.marcar("toolu_marcar", ruim)
        with self.assertRaises(Erro):
            widgets.marcar("../fora", [0])

    def test_demo_de_cada_tipo(self):
        pedidos = {"mostre um mapa de São Paulo": "mapa", "compare os preços de fones": "produtos",
                   "me recomende séries": "recomendacoes", "desenhe a planta da sala": "desenho",
                   "faça um gráfico de pizza": "grafico", "compare os modelos": "comparacao",
                   "linha do tempo da Apollo": "linha_do_tempo", "checklist para viajar": "checklist",
                   "show me a map of Rio": "mapa", "a line chart please": "grafico"}
        for texto, tipo in pedidos.items():
            entrada = widgets.demo(texto, {"mostrar_widget", "perguntar"})
            self.assertEqual(entrada["tipo"], tipo, texto)
            w, avisos = widgets.normalizar(entrada, geocodificar=lambda e: self.fail("a demonstração não busca endereço"))
            self.assertEqual(avisos, [], texto)
        self.assertIsNone(widgets.demo("mostre um mapa", {"perguntar"}), "sem a ferramenta, nada")
        self.assertIsNone(widgets.demo("oi, tudo bem?", {"mostrar_widget"}))
        self.assertEqual(widgets.demo("show me a map of Rio", {"mostrar_widget"})["titulo"], "A day in Rio de Janeiro")


# ======================= endereço → coordenada =======================

class TestGeocodificar(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(config.DADOS / "cache", ignore_errors=True)
        mapas._ultima["em"] = None
        self.relogio = [100.0]
        self.esperas = []
        self.pedidos = []

        def esperar(s):
            self.esperas.append(round(s, 3))
            self.relogio[0] += s

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            self.relogio[0] += 0.2
            q = req.full_url
            if "inexistente" in q:
                return _Resposta(b"[]")
            return _Resposta(json.dumps([{"lat": "-23.5", "lon": "-46.6", "display_name": "São Paulo"}]).encode())
        self.patches = [mock.patch.object(mapas, "_agora", lambda: self.relogio[0]),
                        mock.patch.object(mapas, "_esperar", esperar),
                        mock.patch("urllib.request.urlopen", abrir)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_uma_busca_por_segundo_e_cache(self):
        a = mapas.geocodificar("Rua A, 1, São Paulo")
        b = mapas.geocodificar("Rua B, 2, São Paulo")
        self.assertEqual(a, {"lat": -23.5, "lon": -46.6, "nome": "São Paulo"})
        self.assertEqual(len(self.pedidos), 2)
        self.assertEqual(self.esperas, [1.0], "a segunda busca esperou completar 1 s desde a primeira")
        self.assertIn("format=jsonv2", self.pedidos[0].full_url)
        self.assertIn("limit=1", self.pedidos[0].full_url)
        self.assertTrue(self.pedidos[0].full_url.startswith("https://nominatim.openstreetmap.org/search?"))
        ua = self.pedidos[0].get_header("User-agent")
        self.assertEqual(ua, f"Clave/{config.VERSAO} (+https://github.com/FelipeWASD83/clave)")
        self.assertEqual(mapas.geocodificar("  rua a, 1,   SÃO PAULO "), a, "o mesmo endereço vem do cache")
        self.assertEqual(len(self.pedidos), 2)
        self.assertTrue((config.DADOS / "cache" / "geocode.json").is_file())
        self.assertIsNotNone(b)

    def test_nao_achado_fica_guardado_e_sem_conexao_avisa(self):
        self.assertIsNone(mapas.geocodificar("Lugar inexistente"))
        self.assertIsNone(mapas.geocodificar("Lugar inexistente"))
        self.assertEqual(len(self.pedidos), 1, "o 'não achei' também fica no cache")
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("sem rede")):
            with self.assertRaises(mapas.SemConexao):
                mapas.geocodificar("Outro lugar")
        self.assertNotIn("outro lugar", json.loads((config.DADOS / "cache" / "geocode.json").read_text(encoding="utf-8")),
                         "falha de rede não vira 'não achei'")

    def test_espera_longa_nao_e_preciso(self):
        mapas.geocodificar("Rua C")
        self.relogio[0] += 5
        mapas.geocodificar("Rua D")
        self.assertEqual(self.esperas, [])


# ======================= tiles do mapa =======================

class TestTiles(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(config.DADOS / "cache" / "tiles", ignore_errors=True)
        self.pedidos = []
        self.respostas = []

        def abrir(req, timeout=None):
            self.pedidos.append(req)
            r = self.respostas.pop(0)
            if isinstance(r, Exception):
                raise r
            return r
        self.patch = mock.patch("urllib.request.urlopen", abrir)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def test_baixa_guarda_e_serve_do_disco(self):
        self.respostas.append(_Resposta(PNG, cab=_cab(Content_Type="image/png", Cache_Control="max-age=60", ETag='"v1"',
                                                        Last_Modified="Tue, 13 Oct 2026 10:00:00 GMT")))
        dados, tipo, segundos = mapas.obter_tile("3", "2", "5.png")
        self.assertEqual((dados, tipo), (PNG, "image/png"))
        req = self.pedidos[0]
        self.assertEqual(req.full_url, "https://tile.openstreetmap.org/3/2/5.png")
        self.assertEqual(req.get_header("User-agent"), f"Clave/{config.VERSAO} (+https://github.com/FelipeWASD83/clave)")
        self.assertIsNone(req.get_header("Cache-control"), "nunca manda no-cache")
        meta = json.loads((config.DADOS / "cache" / "tiles" / "3" / "2" / "5.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(meta["expira"] - time.time(), 7 * 86400 - 5, "guarda pelo menos 7 dias mesmo com max-age=60")
        self.assertGreater(segundos, 3600)
        dados2, _, _ = mapas.obter_tile(3, 2, 5)
        self.assertEqual(dados2, PNG)
        self.assertEqual(len(self.pedidos), 1, "a segunda vez vem do disco")

    def test_vencido_confere_antes_de_baixar(self):
        self.respostas.append(_Resposta(PNG, cab=_cab(Content_Type="image/png", ETag='"v1"',
                                                        Last_Modified="Tue, 13 Oct 2026 10:00:00 GMT")))
        mapas.obter_tile(4, 1, 1)
        arq_meta = config.DADOS / "cache" / "tiles" / "4" / "1" / "1.json"
        meta = json.loads(arq_meta.read_text(encoding="utf-8"))
        meta["expira"] = time.time() - 10
        arq_meta.write_text(json.dumps(meta), encoding="utf-8")
        self.respostas.append(urllib.error.HTTPError("u", 304, "Not Modified", _cab(Cache_Control="max-age=864000"), None))
        dados, _, _ = mapas.obter_tile(4, 1, 1)
        self.assertEqual(dados, PNG)
        req = self.pedidos[1]
        self.assertEqual(req.get_header("If-none-match"), '"v1"')
        self.assertEqual(req.get_header("If-modified-since"), "Tue, 13 Oct 2026 10:00:00 GMT")
        meta = json.loads(arq_meta.read_text(encoding="utf-8"))
        self.assertGreater(meta["expira"] - time.time(), 9 * 86400, "o prazo novo vem do 304")
        mapas.obter_tile(4, 1, 1)
        self.assertEqual(len(self.pedidos), 2)

    def test_vencido_e_sem_internet_serve_o_velho(self):
        self.respostas.append(_Resposta(PNG, cab=_cab(Content_Type="image/png", Expires="Thu, 01 Jan 2099 00:00:00 GMT")))
        mapas.obter_tile(5, 3, 3)
        meta = json.loads((config.DADOS / "cache" / "tiles" / "5" / "3" / "3.json").read_text(encoding="utf-8"))
        self.assertGreater(meta["expira"] - time.time(), 365 * 86400, "Expires é respeitado")
        meta["expira"] = 0
        (config.DADOS / "cache" / "tiles" / "5" / "3" / "3.json").write_text(json.dumps(meta), encoding="utf-8")
        self.respostas.append(urllib.error.URLError("sem rede"))
        dados, _, segundos = mapas.obter_tile(5, 3, 3)
        self.assertEqual((dados, segundos), (PNG, 300))

    def test_erros(self):
        for z, x, y in (("20", "0", "0"), ("2", "4", "0"), ("2", "0", "-1"), ("a", "0", "0"), ("1", "0", "1.jpg")):
            with self.assertRaises(Erro) as e:
                mapas.obter_tile(z, x, y)
            self.assertEqual(e.exception.status, 400, (z, x, y))
        self.respostas.append(urllib.error.URLError("sem rede"))
        with self.assertRaises(Erro) as e:
            mapas.obter_tile(1, 1, 1)
        self.assertEqual(e.exception.status, 502)
        self.respostas.append(_Resposta(b"<svg/>", cab=_cab(Content_Type="image/svg+xml")))
        with self.assertRaises(Erro):
            mapas.obter_tile(1, 0, 1)
        self.assertFalse((config.DADOS / "cache" / "tiles" / "1" / "0" / "1.png").exists())


# ======================= imagens de fora =======================

class TestImagens(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(config.DADOS / "cache" / "imagens", ignore_errors=True)
        self.dns = {"loja.example": ["93.184.215.14"], "cdn.example": ["151.101.1.10"],
                    "interno.example": ["10.0.0.7"], "misto.example": ["93.184.215.14", "192.168.0.10"],
                    "seis.example": ["::ffff:127.0.0.1"]}
        self.pedidos = []
        self.respostas = {}

        def pedir(host, ip, alvo, limite):
            self.pedidos.append((host, ip, alvo))
            return self.respostas[(host, alvo)]
        self.patches = [mock.patch.object(widgets, "_resolver", lambda h: self.dns[h]),
                        mock.patch.object(widgets, "_pedir_https", pedir)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def _status(self, url):
        with self.assertRaises(widgets.ErroImagem) as e:
            widgets.baixar_imagem(url)
        return e.exception.status

    def test_recusa_o_que_nao_pode(self):
        self.assertEqual(self._status("http://loja.example/a.png"), 400)
        self.assertEqual(self._status("ftp://loja.example/a.png"), 400)
        self.assertEqual(self._status("https://loja.example:8443/a.png"), 400)
        self.assertEqual(self._status("https://user:senha@loja.example/a.png"), 400)
        self.assertEqual(self._status("https://127.0.0.1/a.png"), 403)
        self.assertEqual(self._status("https://[::1]/a.png"), 403)
        self.assertEqual(self._status("https://169.254.169.254/latest"), 403)
        self.assertEqual(self._status("https://interno.example/a.png"), 403)
        self.assertEqual(self._status("https://misto.example/a.png"), 403, "um IP interno entre os resolvidos já basta")
        self.assertEqual(self._status("https://seis.example/a.png"), 403, "IPv6 que embute IPv4 interno")
        self.assertEqual(self.pedidos, [], "nada disso chegou a ser pedido")

    def test_svg_e_tipo_disfarcado(self):
        self.respostas[("loja.example", "/a.svg")] = (200, {"content-type": "image/svg+xml"}, b"<svg xmlns='x'/>")
        self.assertEqual(self._status("https://loja.example/a.svg"), 415)
        self.respostas[("loja.example", "/b.png")] = (200, {"content-type": "image/png"}, b"<svg onload='x'/>")
        self.assertEqual(self._status("https://loja.example/b.png"), 415, "o conteúdo é conferido, não só o cabeçalho")
        self.respostas[("loja.example", "/c")] = (200, {"content-type": "text/html"}, PNG)
        self.assertEqual(self._status("https://loja.example/c"), 415)

    def test_png_valido_fica_em_cache(self):
        self.respostas[("loja.example", "/foto.png?v=2")] = (200, {"content-type": "image/png"}, PNG)
        dados, tipo = widgets.baixar_imagem("https://loja.example/foto.png?v=2")
        self.assertEqual((dados, tipo), (PNG, "image/png"))
        self.assertEqual(self.pedidos, [("loja.example", "93.184.215.14", "/foto.png?v=2")], "a conexão vai para o IP conferido")
        widgets.baixar_imagem("https://loja.example/foto.png?v=2")
        self.assertEqual(len(self.pedidos), 1, "a segunda vez vem do disco")

    def test_redirecionamentos(self):
        self.respostas[("loja.example", "/r1")] = (302, {"location": "https://cdn.example/f.jpg"}, b"")
        self.respostas[("cdn.example", "/f.jpg")] = (200, {"content-type": "image/jpeg"}, b"\xff\xd8\xff\xe0" + b"\x00" * 20)
        self.assertEqual(widgets.baixar_imagem("https://loja.example/r1")[1], "image/jpeg")
        self.respostas[("loja.example", "/r2")] = (301, {"location": "https://interno.example/x.png"}, b"")
        self.assertEqual(self._status("https://loja.example/r2"), 403, "o redirecionamento é conferido de novo")
        self.respostas[("loja.example", "/r3")] = (302, {"location": "http://loja.example/x.png"}, b"")
        self.assertEqual(self._status("https://loja.example/r3"), 400, "redirecionar para http também é recusado")
        self.respostas[("loja.example", "/laco")] = (302, {"location": "/laco"}, b"")
        self.assertEqual(self._status("https://loja.example/laco"), 502)
        self.assertEqual(sum(1 for p in self.pedidos if p[2] == "/laco"), 4, "segue no máximo 3 redirecionamentos")

    def test_grande_demais(self):
        self.respostas[("loja.example", "/g.png")] = (200, {"content-type": "image/png"}, PNG + b"\x00" * (5 * 1024 * 1024))
        self.assertEqual(self._status("https://loja.example/g.png"), 413)

    def test_ip_publico(self):
        for ip in ("10.1.2.3", "172.16.0.1", "192.168.1.214", "127.0.0.1", "169.254.1.1", "224.0.0.1", "0.0.0.0",
                   "100.64.0.1", "::1", "fe80::1", "fc00::1", "::ffff:10.0.0.1", "2002:0a00:0001::1", "240.0.0.1"):
            self.assertFalse(widgets._ip_publico(ip), ip)
        for ip in ("93.184.215.14", "8.8.8.8", "2606:4700::6810:84e5"):
            self.assertTrue(widgets._ip_publico(ip), ip)


# ======================= revisão: preços, sim/não, notas, onde a ferramenta vale =======================

def _produtos(*itens, **extra):
    return _norm("produtos", {"visto_em": "2026-10-15", "itens": list(itens), **extra})


class TestPrecoSemCentavos(unittest.TestCase):
    def test_milhar_sem_centavos_nas_duas_convencoes(self):
        casos = [({"preco": "R$ 1.299"}, 1299, "BRL"), ({"preco": "R$ 12.499"}, 12499, "BRL"),
                 ({"preco": "US$ 1,299"}, 1299, "USD"), ({"preco": "$12,499"}, 12499, "USD"),
                 ({"preco": "1.299 EUR"}, 1299, "EUR"), ({"preco": "£1,299"}, 1299, "GBP"),
                 ({"preco": "R$ 1.299,90"}, 1299.9, "BRL"), ({"preco": "US$ 1,299.99"}, 1299.99, "USD"),
                 ({"preco": "R$ 1.299.000"}, 1299000, "BRL"), ({"preco": "1299.90", "moeda": "USD"}, 1299.9, "USD"),
                 ({"preco": "R$ 0,99"}, 0.99, "BRL"), ({"preco": "0.999", "moeda": "USD"}, 0.999, "USD"),
                 ({"preco": "1.299", "moeda": "KWD"}, 1.299, "KWD"), ({"preco": "R$ 89,9"}, 89.9, "BRL"),
                 ({"preco": "1.299", "moeda": "brl"}, 1299, "BRL"), ({"preco": 1299.5}, 1299.5, "BRL")]
        for item, preco, moeda in casos:
            w, _ = _produtos({"nome": "A", **item})
            self.assertEqual((w["dados"]["itens"][0]["preco"], w["dados"]["itens"][0]["moeda"]), (preco, moeda), item)

    def test_mais_barato_fica_certo(self):
        w, _ = _produtos({"nome": "Caro", "preco": "R$ 1.299"}, {"nome": "Barato", "preco": "R$ 899,90"})
        itens = w["dados"]["itens"]
        self.assertEqual(min(itens, key=lambda it: it["preco"])["nome"], "Barato",
                         "R$ 1.299 não pode virar 1,299 e passar por mais barato")

    def test_moeda_do_campo_vale_mais_que_a_do_texto(self):
        w, _ = _produtos({"nome": "A", "preco": "US$ 10", "moeda": "BRL"})
        self.assertEqual(w["dados"]["itens"][0]["moeda"], "BRL")
        w, _ = _produtos({"nome": "A", "preco": "por 1.299"})
        self.assertEqual(w["dados"]["itens"][0]["moeda"], "BRL", "três letras quaisquer não viram moeda")

    def test_outros_numeros_continuam_como_antes(self):
        w, _ = _norm("mapa", {"pontos": [{"nome": "X", "lat": "-23,587", "lon": "-46.657"}]})
        self.assertEqual((w["dados"]["pontos"][0]["lat"], w["dados"]["pontos"][0]["lon"]), (-23.587, -46.657),
                         "coordenada com 3 casas não vira milhar")
        w, _ = _norm("grafico", {"rotulos": ["a"], "series": [{"valores": ["1.5"]}]})
        self.assertEqual(w["dados"]["series"][0]["valores"], [1.5])


class TestSimOuNao(unittest.TestCase):
    def test_checklist(self):
        valores = ["false", "não", "0", "no", "False", "", None, 0, False, "true", "sim", "1", "yes", 1, True, "x"]
        w, avisos = _norm("checklist", {"itens": [{"texto": f"item {i}", "feito": v} for i, v in enumerate(valores)]})
        self.assertEqual([it["feito"] for it in w["dados"]["itens"]],
                         [False] * 9 + [True] * 7)
        self.assertEqual(avisos, [])
        w, avisos = _norm("checklist", {"itens": [{"texto": "a", "feito": "talvez"}]})
        self.assertFalse(w["dados"]["itens"][0]["feito"])
        self.assertTrue(any("talvez" in a for a in avisos), "o valor estranho é avisado ao Claude")

    def test_rota_e_preenchido(self):
        pontos = [{"nome": "A", "lat": 1, "lon": 2}, {"nome": "B", "lat": 3, "lon": 4}]
        self.assertFalse(_norm("mapa", {"rota": "false", "pontos": pontos})[0]["dados"]["rota"])
        self.assertFalse(_norm("mapa", {"rota": "não", "pontos": pontos})[0]["dados"]["rota"])
        self.assertTrue(_norm("mapa", {"rota": "true", "pontos": pontos})[0]["dados"]["rota"])
        w, _ = _norm("desenho", {"largura": 5, "altura": 4, "formas": [
            {"tipo": "retangulo", "x": 0, "y": 0, "largura": 1, "altura": 1, "preenchido": "false"},
            {"tipo": "circulo", "x": 2, "y": 2, "raio": 1, "preenchido": "0"},
            {"tipo": "retangulo", "x": 1, "y": 1, "largura": 1, "altura": 1, "preenchido": "sim"}]})
        self.assertEqual([f.get("preenchido", False) for f in w["dados"]["formas"]], [False, False, True])


class TestNotaComEscala(unittest.TestCase):
    def test_escalas(self):
        def nota(v):
            w, avisos = _norm("recomendacoes", {"itens": [{"titulo": "X", "por_que": "Y", "nota": v}]})
            return w["dados"]["itens"][0].get("nota"), avisos
        self.assertEqual(nota("8/10")[0], {"valor": 8, "fonte": "", "escala": 10})
        self.assertEqual(nota("8,5 / 10")[0], {"valor": 8.5, "fonte": "", "escala": 10})
        self.assertEqual(nota("4 de 5")[0], {"valor": 4, "fonte": "", "escala": 5})
        self.assertEqual(nota("85%")[0], {"valor": 85, "fonte": "", "escala": 100})
        self.assertEqual(nota({"valor": 7.9, "escala": 10, "fonte": "IMDb"})[0], {"valor": 7.9, "fonte": "IMDb", "escala": 10})
        self.assertEqual(nota({"valor": "92/100", "fonte": "Metacritic"})[0], {"valor": 92, "fonte": "Metacritic", "escala": 100})
        self.assertEqual(nota(4.6)[0], {"valor": 4.6, "fonte": ""}, "sem escala continua sem escala")
        fora, avisos = nota("11/10")
        self.assertIsNone(fora)
        self.assertTrue(any("escala" in a for a in avisos))


class _ExComOp(_ExFalso):
    def __init__(self, op):
        super().__init__()
        self.op = op


class TestSoRodaOndeFoiOferecida(unittest.TestCase):
    ENTRADA = {"tipo": "mapa", "titulo": "M", "dados": {"pontos": [{"nome": "A", "endereco": "Rua A, 1"}]}}

    def _rodar(self, ex, cfg, modo="chat", tid="toolu_recusa"):
        with mock.patch.object(mapas, "geocodificar", side_effect=AssertionError("buscou endereço")):
            r = widgets.executar(ex, tid, "mostrar_widget", dict(self.ENTRADA), cfg, modo)
        self.assertTrue(r.get("is_error"), r)
        self.assertNotIn("widget", [e["tipo"] for e in ex.eventos], "nada aparece na tela")
        self.assertTrue(ex.eventos[-1]["erro"])
        self.assertFalse((config.DADOS / "widgets" / f"{tid}.json").exists(), "nada é salvo")
        return r["content"]

    def test_widgets_desligados(self):
        self.assertIn("Configurações", self._rodar(_ExComOp({}), {"widgets_ligados": False}))

    def test_rotina_etapa_e_ajudante(self):
        self.assertIn("rotina", self._rodar(_ExComOp({"rotina": True}), {}))
        self.assertIn("rotina", self._rodar(_ExComOp({"etapa_de_fluxo": True}), {}))
        self.assertIn("rotina", self._rodar(_ExComOp({}), {}, modo="tutor"))

    def test_onde_foi_oferecida_roda(self):
        with mock.patch.object(mapas, "geocodificar", return_value={"lat": 1, "lon": 2, "nome": "Rua A, 1, Centro"}):
            r = widgets.executar(_ExComOp({}), "toolu_vale", "mostrar_widget", dict(self.ENTRADA), {}, "code")
        self.assertFalse(r.get("is_error"), r)


class TestMapaMostraOndeCaiu(unittest.TestCase):
    def test_resultado_tem_o_lugar_achado(self):
        achados = {"Rua X, 10": {"lat": -19.9, "lon": -43.9, "nome": "Rua X, 10, Bairro Y, Cidade Z, Brasil"}}
        with mock.patch.object(mapas, "geocodificar", side_effect=lambda e: achados.get(e)):
            r = widgets.executar(_ExComOp({}), "toolu_achado", "mostrar_widget", {
                "tipo": "mapa", "titulo": "M", "dados": {"pontos": [
                    {"nome": "Casa", "endereco": "Rua X, 10"}, {"nome": "Nada", "endereco": "Rua Inexistente"},
                    {"nome": "Coordenada", "lat": 1, "lon": 2}]}}, {}, "chat")
        self.assertIn("Rua X, 10 -> Rua X, 10, Bairro Y, Cidade Z, Brasil (-19.9, -43.9)", r["content"])
        self.assertNotIn("Coordenada ->", r["content"], "ponto com lat e lon não tem endereço para conferir")
        w = widgets.ler("toolu_achado")
        self.assertEqual(w["dados"]["pontos"][0]["achado"], "Rua X, 10, Bairro Y, Cidade Z, Brasil")
        self.assertEqual(w["dados"]["fora"], [{"nome": "Nada (Rua Inexistente)", "motivo": "nao_achado"}],
                         "o cartão também sabe quem ficou de fora")

    def test_fora_por_limite_e_por_conexao(self):
        pontos = [{"nome": f"P{i}", "endereco": f"Rua {i}"} for i in range(4)]
        with mock.patch.object(widgets, "MAX_ENDERECOS", 2):
            w, avisos = _norm("mapa", {"pontos": pontos}, geocodificar=lambda e: {"lat": 1, "lon": 1, "nome": e})
        self.assertEqual(w["dados"]["fora"], [{"nome": "P2 (Rua 2)", "motivo": "limite"},
                                              {"nome": "P3 (Rua 3)", "motivo": "limite"}])
        self.assertTrue(any("limite" in a and "P3" in a for a in avisos))

        def falha(e):
            raise mapas.SemConexao("sem conexão")
        w, avisos = _norm("mapa", {"pontos": [{"nome": "A", "lat": 1, "lon": 1}] + pontos[:2]}, geocodificar=falha)
        self.assertEqual([f["motivo"] for f in w["dados"]["fora"]], ["sem_conexao", "sem_conexao"])
        w, avisos = _norm("mapa", {"pontos": [{"nome": "A", "lat": 1, "lon": 1}]})
        self.assertNotIn("fora", w["dados"], "sem ninguém de fora, nem aparece")


class TestOutrosNaoPisaNasLicoes(unittest.TestCase):
    def test_catalogo_do_servidor(self):
        cat = i18n.catalogo("en")
        self.assertEqual(cat.get("Outros"), "Other", "a trilha padrão das lições continua \"Other\"")
        self.assertEqual(i18n.t("Outros (fatias menores)", "en"), "Others (smaller slices)")
        meu = json.loads((base.RAIZ / "servidor" / "i18n" / "en" / "widgets.json").read_text(encoding="utf-8"))
        self.assertNotIn("Outros", meu)
        # nenhuma chave do catálogo dos widgets troca a tradução de outro módulo no catálogo juntado
        pasta = base.RAIZ / "servidor" / "i18n" / "en"
        for outro in sorted(pasta.glob("*.json")):
            if outro.name == "widgets.json":
                continue
            o = json.loads(outro.read_text(encoding="utf-8"))
            for k, v in meu.items():
                if k in o:
                    self.assertEqual(o[k], v, f"{k!r} traduzido diferente em {outro.name}")


# ======================= revisão: imagens sem internet e caches que não crescem para sempre =======================

class TestImagemGuardadaSemInternet(unittest.TestCase):
    URL = "https://loja.example/foto.png"

    def setUp(self):
        shutil.rmtree(config.DADOS / "cache" / "imagens", ignore_errors=True)
        self.online = mock.patch.object(widgets, "_resolver", lambda h: ["93.184.215.14"])
        self.pedir = mock.patch.object(widgets, "_pedir_https", lambda *a: (200, {"content-type": "image/png"}, PNG))
        self.online.start()
        self.pedir.start()
        widgets.baixar_imagem(self.URL)
        self.online.stop()
        self.pedir.stop()

    def _offline(self):
        return [mock.patch.object(widgets, "_resolver", side_effect=OSError("sem DNS")),
                mock.patch.object(widgets, "_pedir_https", side_effect=AssertionError("tentou a rede"))]

    def test_guardada_aparece_sem_dns(self):
        p1, p2 = self._offline()
        with p1 as resolver, p2:
            self.assertEqual(widgets.baixar_imagem(self.URL), (PNG, "image/png"))
        resolver.assert_not_called()

    def test_vencida_e_sem_internet_serve_a_velha(self):
        _, arq_meta = widgets._arquivos_imagem(self.URL)
        meta = json.loads(arq_meta.read_text(encoding="utf-8"))
        meta["em"] = time.time() - 30 * 86400
        arq_meta.write_text(json.dumps(meta), encoding="utf-8")
        with mock.patch.object(widgets, "_resolver", side_effect=OSError("sem DNS")):
            self.assertEqual(widgets.baixar_imagem(self.URL), (PNG, "image/png"))
        novo = b"\x89PNG\r\n\x1a\n" + b"\x01" * 64
        with mock.patch.object(widgets, "_resolver", lambda h: ["93.184.215.14"]), \
                mock.patch.object(widgets, "_pedir_https", lambda *a: (200, {"content-type": "image/png"}, novo)):
            self.assertEqual(widgets.baixar_imagem(self.URL)[0], novo, "com internet, a vencida é baixada de novo")

    def test_endereco_proibido_continua_recusado_sem_rede(self):
        p1, p2 = self._offline()
        with p1, p2:
            with self.assertRaises(widgets.ErroImagem) as e:
                widgets.baixar_imagem("https://10.0.0.1/a.png")
        self.assertEqual(e.exception.status, 403)


def _envelhecer(arq: Path, dias: float):
    quando = time.time() - dias * 86400
    os.utime(arq, (quando, quando))


class TestPodaDosCaches(unittest.TestCase):
    def setUp(self):
        self.antes = config.DADOS
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-testes-poda-"))
        config.DADOS = self.pasta

    def tearDown(self):
        config.DADOS = self.antes
        shutil.rmtree(self.pasta, ignore_errors=True)

    def _imagem(self, nome: str, uso_dias: float, tamanho: int = 100):
        base_ = self.pasta / "cache" / "imagens"
        base_.mkdir(parents=True, exist_ok=True)
        (base_ / f"{nome}.img").write_bytes(b"x" * tamanho)
        meta = base_ / f"{nome}.json"
        meta.write_text(json.dumps({"tipo": "image/png", "em": time.time() - uso_dias * 86400}), encoding="utf-8")
        _envelhecer(meta, uso_dias)
        return base_ / f"{nome}.img"

    def _tile(self, y: int, uso_dias: float, baixado_dias: float, tamanho: int = 100):
        img, meta = mapas._arquivos_tile(5, 1, y)
        img.parent.mkdir(parents=True, exist_ok=True)
        img.write_bytes(b"x" * tamanho)
        meta.write_text(json.dumps({"expira": time.time() + 86400, "baixado_em": time.time() - baixado_dias * 86400,
                                    "tipo": "image/png"}), encoding="utf-8")
        _envelhecer(meta, uso_dias)
        return img

    def test_imagens_sem_uso_e_teto(self):
        velha = self._imagem("velha", 40)
        usada = self._imagem("usada", 2)
        sobra = self.pasta / "cache" / "imagens" / "orfa.img"
        sobra.write_bytes(b"x")
        _envelhecer(sobra, 3)
        self.assertEqual(widgets.podar_imagens(), 1)
        self.assertFalse(velha.exists())
        self.assertFalse(velha.with_suffix(".json").exists())
        self.assertTrue(usada.exists())
        self.assertFalse(sobra.exists(), "imagem sem o .json ao lado também sai")
        a, b = self._imagem("a", 5, 600), self._imagem("b", 1, 600)
        with mock.patch.object(widgets, "MAX_CACHE_IMAGENS", 1000):
            self.assertEqual(widgets.podar_imagens(), 1)
        self.assertFalse(a.exists(), "passando do teto, sai a usada há mais tempo (5 dias)")
        self.assertTrue(usada.exists() and b.exists(), "e só até caber")
        with mock.patch.object(widgets, "MAX_CACHE_IMAGENS", 700):
            widgets.podar_imagens()
        self.assertFalse(usada.exists())
        self.assertTrue(b.exists())

    def test_tiles_respeitam_os_7_dias(self):
        sem_uso = self._tile(1, uso_dias=40, baixado_dias=40)
        recente = self._tile(2, uso_dias=40, baixado_dias=3)  # relógio estranho, mas baixado há 3 dias: fica
        usado = self._tile(3, uso_dias=1, baixado_dias=20)
        self.assertEqual(mapas.podar_tiles(), 1)
        self.assertFalse(sem_uso.exists())
        self.assertTrue(recente.exists() and usado.exists())
        novo = self._tile(4, uso_dias=0, baixado_dias=0, tamanho=5000)
        with mock.patch.object(mapas, "MAX_CACHE_TILES", 10):
            mapas.podar_tiles()
        self.assertFalse(usado.exists(), "passando do teto sai o mais antigo")
        self.assertTrue(recente.exists() and novo.exists(), "nunca um baixado há menos de 7 dias")

    def test_tile_em_uso_nao_sai(self):
        velho = self._tile(6, uso_dias=40, baixado_dias=40)
        trava = mapas._trava_do_tile("5/1/6")
        with trava:
            self.assertEqual(mapas.podar_tiles(), 0)
        self.assertTrue(velho.exists())

    def test_usar_marca_o_uso(self):
        img = self._tile(7, uso_dias=10, baixado_dias=10)
        meta = img.with_suffix(".json")
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("baixou")):
            self.assertEqual(mapas.obter_tile(5, 1, 7)[0], b"x" * 100)
        self.assertLess(time.time() - meta.stat().st_mtime, 60, "o tile servido do disco conta como usado")
        foto = self._imagem("foto", 10)
        _, arq_meta = widgets._arquivos_imagem("https://loja.example/x.png")
        foto.rename(arq_meta.with_suffix(".img"))
        foto.with_suffix(".json").rename(arq_meta)
        json_meta = json.loads(arq_meta.read_text(encoding="utf-8"))
        json_meta["em"] = time.time()
        arq_meta.write_text(json.dumps(json_meta), encoding="utf-8")
        _envelhecer(arq_meta, 10)
        with mock.patch.object(widgets, "_resolver", side_effect=AssertionError("rede")):
            widgets.baixar_imagem("https://loja.example/x.png")
        self.assertLess(time.time() - arq_meta.stat().st_mtime, 60)

    def test_faxina_roda_sozinha_de_tempos_em_tempos(self):
        with mock.patch.object(widgets, "podar_imagens") as podar, mock.patch.dict(widgets._poda, {"em": 0.0}):
            widgets._talvez_podar()
            widgets._talvez_podar()
            for th in [t for t in __import__("threading").enumerate() if t.name == "poda-imagens"]:
                th.join(5)
        self.assertEqual(podar.call_count, 1, "uma vez a cada 6 horas, não a cada imagem")


# ======================= revisão: exportar em Markdown =======================

class TestExportarMarkdown(unittest.TestCase):
    def _salvo(self, tid, tipo, dados, **kw):
        widgets.salvar(tid, _norm(tipo, dados, **kw)[0])
        return widgets.texto_para_exportar(tid)

    def test_produtos_em_tabela(self):
        md = self._salvo("toolu_exp_prod", "produtos", {"visto_em": "2026-10-15", "itens": [
            {"nome": "Fone | caro", "preco": "R$ 1.299", "loja": "Loja A", "link": "https://loja.example/a(1)", "nota": "8/10"},
            {"nome": "Fone barato", "preco": 289.9, "loja": "Loja B"}]})
        linhas = md.splitlines()
        self.assertEqual(linhas[0], "**Produtos: Teste**")
        self.assertIn("| Produto | Preço | Loja | Nota |", md)
        self.assertIn("| Fone barato | **R$ 289,90** (mais barato) | Loja B |", md)
        self.assertIn("[Fone \\| caro](https://loja.example/a%281%29) | R$ 1.299,00 | Loja A | 8/10 |", md)
        self.assertIn("Preços vistos em 15/10/2026", md)
        self.assertLess(md.index("Fone barato"), md.index("Fone \\| caro"), "do mais barato para o mais caro")

    def test_mapa_com_coordenadas_e_quem_ficou_de_fora(self):
        md = self._salvo("toolu_exp_mapa", "mapa", {"rota": True, "pontos": [
            {"nome": "Casa", "endereco": "Rua X, 10", "descricao": "Onde moro"},
            {"nome": "Nada", "endereco": "Rua Y"}, {"nome": "Praça", "lat": -23.5, "lon": -46.6}]},
            geocodificar=lambda e: {"lat": -19.9, "lon": -43.9, "nome": "Rua X, 10, Centro"} if e == "Rua X, 10" else None)
        self.assertIn("1. **Casa**: Onde moro", md)
        self.assertIn("No mapa: Rua X, 10, Centro", md)
        self.assertIn("(https://www.openstreetmap.org/?mlat=-19.9&mlon=-43.9#map=17/-19.9/-43.9) (-19,9; -43,9)", md)
        self.assertIn("2. **Praça**", md)
        self.assertIn("- Nada (Rua Y) (endereço não encontrado)", md)
        self.assertIn("A linha liga os pontos na ordem da lista.", md)

    def test_grafico_comparacao_tempo_checklist(self):
        md = self._salvo("toolu_exp_graf", "grafico", {"rotulos": ["jan", "fev"], "unidade": "US$",
                                                       "series": [{"nome": "Chat", "valores": [1, 2.5]}, {"nome": "Code", "valores": [3, 4]}]})
        self.assertIn("| Rótulo | Chat | Code |", md)
        self.assertIn("| fev | US$ 2,5 | US$ 4 |", md)
        md = self._salvo("toolu_exp_pizza", "grafico", {"tipo_grafico": "pizza", "rotulos": ["a", "b"], "series": [{"valores": [1, 3]}]})
        self.assertIn("| b | 3 | 75% |", md)
        self.assertIn("| **Total** | **4** | **100%** |", md)
        md = self._salvo("toolu_exp_comp", "comparacao", {"colunas": ["A", "B"], "linhas": [
            {"criterio": "Garantia", "valores": [True, None], "melhor": 0}]})
        self.assertIn("| Critério | A | B |", md)
        self.assertIn("| Garantia | **sim** (melhor) | sem dado |", md)
        self.assertIn("| **Melhor em** | 1 de 1 | 0 de 1 |", md)
        md = self._salvo("toolu_exp_tempo", "linha_do_tempo", {"eventos": [{"data": "1969", "titulo": "Lua", "descricao": "Apollo 11"}]})
        self.assertIn("- **1969**: Lua. Apollo 11", md)
        widgets.salvar("toolu_exp_check", _norm("checklist", {"itens": ["Passaporte", {"texto": "Mala", "feito": "sim"}]})[0])
        widgets.marcar("toolu_exp_check", [0])
        md = widgets.texto_para_exportar("toolu_exp_check")
        self.assertIn("- [x] Passaporte", md, "o que foi marcado na tela vai junto")
        self.assertIn("- [ ] Mala", md)

    def test_recomendacoes_e_desenho(self):
        md = self._salvo("toolu_exp_rec", "recomendacoes", {"itens": [
            {"titulo": "Dark", "tipo": "serie", "ano": 2017, "generos": ["suspense"], "onde": "Netflix",
             "nota": {"valor": "8,7/10", "fonte": "IMDb"}, "por_que": "Viagem no tempo."}]})
        self.assertIn("1. **Dark** (Série, 2017)", md)
        self.assertIn("   - Onde ver: Netflix", md)
        self.assertIn("   - Nota: 8,7/10 (IMDb)", md)
        md = self._salvo("toolu_exp_des", "desenho", {"largura": 5, "altura": 4, "formas": [
            {"tipo": "retangulo", "x": 0.5, "y": 0.5, "largura": 2, "altura": 1, "rotulo": "Sofá"},
            {"tipo": "cota", "x1": 0, "y1": 4, "x2": 5, "y2": 4}], "legenda": [{"cor": "azul", "rotulo": "Janela"}]})
        self.assertIn("Desenho de 5 por 4 m", md)
        self.assertIn("- Retângulo \"Sofá\": em (0,5; 0,5), 2 × 1 m", md)
        self.assertIn("- Cota: 5 m", md)
        self.assertIn("Legenda: Azul = Janela", md)

    def test_em_ingles(self):
        widgets.salvar("toolu_exp_en", _norm("produtos", {"visto_em": "2026-10-05", "itens": [
            {"nome": "A", "preco": 1299.9, "moeda": "USD"}, {"nome": "B", "preco": 5, "moeda": "USD"}]})[0])
        with mock.patch.object(i18n, "idioma", lambda: "en"), mock.patch.object(widgets, "idioma", lambda: "en"):
            md = widgets.texto_para_exportar("toolu_exp_en")
        self.assertIn("**Products: Teste**", md)
        self.assertIn("| Product | Price |", md)
        self.assertIn("| A | $ 1,299.90 |", md)
        self.assertIn("**$ 5.00** (cheapest)", md)
        self.assertIn("Prices seen on 10/5/2026", md)

    def test_cada_demo_exporta_e_id_ruim_da_none(self):
        for i, texto in enumerate(["mostre um mapa", "compare os preços", "me recomende séries", "desenhe a planta",
                                   "gráfico de pizza", "compare os modelos", "linha do tempo", "checklist"]):
            w, _ = widgets.normalizar(widgets.demo(texto, {"mostrar_widget"}))
            widgets.salvar(f"toolu_exp_demo{i}", w)
            md = widgets.texto_para_exportar(f"toolu_exp_demo{i}")
            self.assertTrue(md and md.startswith("**") and w["titulo"] in md, texto)
        self.assertIsNone(widgets.texto_para_exportar("toolu_nao_existe"))
        self.assertIsNone(widgets.texto_para_exportar("../fora"))
        self.assertIsNone(widgets.texto_para_exportar(None))


# ======================= a tela (JavaScript, no Node) =======================

_STUBS = {
    "api.js": "export function api(c, op) { return globalThis.__api(c, op); }\n",
    "icones.js": "export const ic = () => '';\n",
    "ui.js": ("export const el = (...a) => globalThis.__el(...a); export const esc = (s) => String(s);\n"
              "export const aviso = () => {}; export const janela = () => {}; export const copiarTexto = () => {};\n"
              "export const menu = () => {};\n"),
    "i18n.js": ("export const t = (s, v) => (v ? s.replace(/\\{(\\w+)\\}/g, (m, k) => (k in v ? String(v[k]) : m)) : s);\n"
                "export const localidade = () => 'pt-BR';\n"),
    "estado.js": "export const cfg = () => globalThis.__cfg || {};\n",
}

_PRELUDIO = r"""
const qualquer = () => new Proxy(function () {}, {
  get: (o, k) => (k === Symbol.toPrimitive ? () => 0 : k === 'then' ? undefined : qualquer()),
  apply: () => qualquer(), set: () => true });
globalThis.__criados = [];
globalThis.__el = (tag, attrs = {}, ...filhos) => {
  const alvo = { tag, attrs: attrs || {}, filhos: filhos.flat(), trocadoPor: null,
    replaceWith(x) { this.trocadoPor = x; }, append(...x) { this.filhos.push(...x); },
    replaceChildren(...x) { this.filhos = x; } };
  const p = new Proxy(alvo, { get: (o, k) => (k in o ? o[k] : k === 'then' ? undefined : qualquer()),
                              set: (o, k, v) => { o[k] = v; return true; } });
  globalThis.__criados.push(p);
  return p;
};
const esperar = () => new Promise((r) => setTimeout(r, 5));
"""


class TestTelaDosWidgetsNoNode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("sem o Node")
        cls.pasta = Path(tempfile.mkdtemp(prefix="clave-testes-widgetsjs-"))
        for nome, texto in _STUBS.items():
            (cls.pasta / nome).write_text(texto, encoding="utf-8")
        shutil.copy(base.RAIZ / "app" / "js" / "widgets.js", cls.pasta / "widgets.js")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.pasta, ignore_errors=True)

    def rodar(self, corpo: str):
        script = (_PRELUDIO + "const W = await import(" + json.dumps((self.pasta / "widgets.js").as_uri()) + ");\n"
                  + "const r = await (async () => {" + corpo + "})();\nprocess.stdout.write(JSON.stringify(r));\n")
        p = subprocess.run([self.node, "--input-type=module"], input=script, capture_output=True, text=True,
                           encoding="utf-8", timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_widget_por_id_guarda_por_um_tempo(self):
        r = self.rodar(r"""
          let n = 0;
          const w = { tipo: 'checklist', titulo: 'X', dados: { itens: [{ texto: 'a', feito: false }] } };
          globalThis.__api = () => { n++; return Promise.resolve(w); };
          const a = W.widgetPorId('toolu_1'); const b = W.widgetPorId('toolu_1');
          await esperar();
          const depoisDeDois = n;
          W.widgetPorId('toolu_1'); await esperar();
          globalThis.__api = () => { n++; return Promise.reject(Object.assign(new Error('falhou'), { status: 500 })); };
          W.widgetPorId('toolu_2'); await esperar(); W.widgetPorId('toolu_2'); await esperar();
          const comErro = n;
          W.lembrarWidget('toolu_3', w); W.widgetPorId('toolu_3'); await esperar();
          return { depoisDeDois, terceiro: comErro - 2, comErro, lembrado: n, trocou: !!a.trocadoPor && !!b.trocadoPor };
        """)
        self.assertEqual(r["depoisDeDois"], 1, "dois redesenhos juntos pedem uma vez")
        self.assertEqual(r["terceiro"], 1, "o terceiro também vem do cache")
        self.assertEqual(r["comErro"], 3, "erro não fica guardado: tenta de novo")
        self.assertEqual(r["lembrado"], 3, "widget lembrado não é pedido")
        self.assertTrue(r["trocou"])

    def test_botao_de_imagens_diz_os_sites(self):
        r = self.rodar(r"""
          globalThis.__cfg = { widgets_imagens: 'clicar' };
          const botoes = (urls) => {
            globalThis.__criados = [];
            W.renderizarWidget({ tipo: 'produtos', titulo: 'P', dados: { visto_em: '2026-10-15', itens: urls.map((u, i) => ({ nome: 'n' + i, preco: i + 1, moeda: 'BRL', imagem: u })) } });
            return globalThis.__criados.filter((e) => String(e.attrs.html || '').includes('Mostrar imagens')).map((e) => e.attrs.html);
          };
          return [botoes(['https://www.loja.com/a.png', 'https://outra.com/b.png', 'https://loja.com/c.png']),
                  botoes(['https://a.com/1', 'https://b.com/2', 'https://c.com/3', 'https://d.com/4'])];
        """)
        self.assertEqual(len(r[0]), 1)
        self.assertIn("Mostrar imagens de loja.com e outra.com", r[0][0])
        self.assertIn("Mostrar imagens de a.com, b.com e mais 2 sites", r[1][0])

    def test_texto_com_escala_e_pontos_de_fora(self):
        r = self.rodar(r"""
          return [W.textoDoWidget({ tipo: 'recomendacoes', titulo: 'R', dados: { itens: [{ titulo: 'Dark', tipo: 'serie', por_que: 'x', nota: { valor: 8, escala: 10, fonte: 'IMDb' } }] } }),
                  W.textoDoWidget({ tipo: 'mapa', titulo: 'M', dados: { pontos: [{ nome: 'Casa', lat: 1, lon: 2, endereco: 'Rua X', achado: 'Rua X, Centro' }], fora: [{ nome: 'Nada', motivo: 'nao_achado' }, { nome: 'Longe', motivo: 'limite' }] } })];
        """)
        self.assertIn("Nota: 8/10 (IMDb)", r[0])
        self.assertIn("No mapa: Rua X, Centro", r[1])
        self.assertIn("• Nada (endereço não encontrado)", r[1])
        self.assertIn("• Longe (passou do limite de endereços por mapa)", r[1])

    # o SVG das capas e o observador de tamanho da tabela, só o bastante para desenhar fora do navegador
    _DOM = r"""
      globalThis.document = { createElementNS: (ns, tag) => ({ tag, attrs: {}, filhos: [], dataset: {},
        setAttribute(k, v) { this.attrs[k] = String(v); }, addEventListener() {}, append(...x) { this.filhos.push(...x); } }) };
      globalThis.ResizeObserver = class { observe() {} };
      const criados = (classe) => globalThis.__criados.filter((e) => String(e.attrs.class || '').split(' ').includes(classe));
    """

    def test_icone_da_linha_existe_em_icones_js(self):
        tipos = ["produtos", "mapa", "recomendacoes", "desenho", "grafico", "comparacao", "linha_do_tempo", "checklist"]
        r = self.rodar("return " + json.dumps(tipos) + ".map((t) => W.iconeDaFerramenta(t));")
        texto = (base.RAIZ / "app" / "js" / "icones.js").read_text(encoding="utf-8")
        nomes = set(re.findall(r"^  ([a-z_]+):", texto, re.M))
        for tipo, nome in zip(tipos, r):
            self.assertIn(nome, nomes, f"{tipo}: o ic() de icones.js não conhece {nome!r} (a linha ficaria sem ícone)")
        self.assertEqual(len(set(r)), len(tipos), "cada tipo de widget tem um ícone diferente na linha da ferramenta")
        self.assertEqual(self.rodar("return W.iconeDaFerramenta(undefined);"), "grafico")
        blocos = (base.RAIZ / "app" / "js" / "blocos.js").read_text(encoding="utf-8")
        entrada = re.search(r"^\s*mostrar_widget: .*$", blocos, re.M).group(0)
        self.assertIn("iconeDaFerramenta(e.tipo)", entrada)
        self.assertNotIn("e.titulo", entrada, "a linha não repete o título que o cartão logo abaixo já mostra")

    def test_capas_do_mesmo_cartao_nao_se_repetem(self):
        r = self.rodar(self._DOM + r"""
          const cartao = (titulo, nomes) => {
            globalThis.__criados = [];
            W.renderizarWidget({ tipo: 'recomendacoes', titulo, dados: { itens: nomes.map((n) => ({ titulo: n, tipo: 'serie', por_que: 'x' })) } });
            return criados('widget-capa').map((c) => {
              const svg = c.filhos[0];
              return { fundo: (svg.filhos[0].attrs.style.match(/--w-(\w+)/) || [])[1], desenho: svg.filhos[1]?.tag + (svg.filhos[1]?.attrs['stroke-width'] || '') };
            });
          };
          return [cartao('Para ver e jogar no fim de semana', ['Dark', 'Interestelar', 'Hollow Knight', 'Fullmetal Alchemist: Brotherhood']),
                  cartao('Outro', ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'])];
        """)
        for capas in r:
            fundos = [c["fundo"] for c in capas]
            self.assertTrue(all(fundos))
            self.assertEqual(len(set(fundos)), len(fundos), f"duas capas com o mesmo fundo: {fundos}")
            self.assertNotIn("cinza", fundos)
            for a, b in zip(capas, capas[1:]):
                self.assertNotEqual(a["desenho"], b["desenho"], "vizinhas com o mesmo desenho")
        self.assertEqual(len(r[0]), 4)

    def test_cartoes_de_produto_com_as_mesmas_faixas(self):
        r = self.rodar(self._DOM + r"""
          globalThis.__criados = [];
          W.renderizarWidget({ tipo: 'produtos', titulo: 'P', dados: { visto_em: '2026-10-15', itens: [
            { nome: 'Um nome comprido de três linhas', preco: 10, moeda: 'BRL', loja: 'A', link: 'https://a.com/', imagem: 'https://a.com/1.png' },
            { nome: 'Curto', preco: 20, moeda: 'BRL' },
            { nome: 'Outro', preco: 30, moeda: 'BRL', observacao: 'frete grátis' }] } });
          const ultimos = new Map();
          for (const li of criados('widget-produto')) ultimos.set(li, li);
          return [...ultimos.keys()].slice(-3).map((li) => ({ faixas: li.attrs.style, filhos: li.filhos.filter(Boolean).map((f) => String(f.attrs?.class || f.tag || '')) }));
        """)
        self.assertEqual(len(r), 3)
        for cartao in r:
            self.assertEqual(cartao["faixas"], "--faixas: 5")
            self.assertEqual(len(cartao["filhos"]), 5, cartao)
            self.assertEqual(cartao["filhos"][2], "widget-preco", "o preço é sempre a terceira faixa")

    def test_estrela_da_comparacao_anda_com_a_ultima_palavra(self):
        r = self.rodar(self._DOM + r"""
          globalThis.__criados = [];
          W.renderizarWidget({ tipo: 'comparacao', titulo: 'C', dados: { colunas: ['A', 'B'], linhas: [
            { criterio: 'Velocidade', valores: ['Mais rápido', 'Rápido'], melhor: 0 },
            { criterio: 'Tem', valores: [true, false], melhor: 0 }] } });
          return criados('melhor').filter((e) => e.tag === 'td').map((td) => td.filhos.filter(Boolean).map((f) =>
            typeof f === 'string' ? f : { classe: f.attrs.class, filhos: f.filhos.filter(Boolean).map((x) => (typeof x === 'string' ? x : x.attrs.class)) }));
        """)
        self.assertEqual(r[0], ["Mais ", {"classe": "widget-junto", "filhos": ["rápido", "widget-melhor"]}])
        self.assertEqual(r[1][0]["classe"], "widget-junto")
        self.assertEqual(r[1][0]["filhos"][-1], "widget-melhor")


# ======================= pelo servidor de verdade =======================

class _ServidorWidgets(Servidor):
    def fechar(self):
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(self.proc.pid)], capture_output=True)
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
        shutil.rmtree(self.dados, ignore_errors=True)


class TestRotas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = _ServidorWidgets(sem_senha=True)
        # antes do servidor.py importar o widgets.py, as rotas aparecem quando a primeira resposta carrega os
        # provedores; depois da integração, já existem desde o começo. Uma conversa curta cobre os dois casos.
        _, r = cls.s.pedir("POST", "/api/conversas", {"modo": "chat"})
        _, r = cls.s.pedir("POST", f"/api/conversas/{r['conversa']['id']}/enviar", {"texto": "Olá!", "opcoes": {}})
        cls.s.eventos(r["execucao"])

    @classmethod
    def tearDownClass(cls):
        cls.s.fechar()

    def _salvar(self, tid, widget):
        pasta = Path(self.s.dados) / "widgets"
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / f"{tid}.json").write_text(json.dumps(widget, ensure_ascii=False), encoding="utf-8")

    def test_get_e_patch(self):
        w, _ = _norm("checklist", {"itens": ["a", "b", "c"]})
        self._salvar("toolu_rota01", w)
        status, lido = self.s.pedir("GET", "/api/widgets/toolu_rota01")
        self.assertEqual((status, lido), (200, w))
        status, novo = self.s.pedir("PATCH", "/api/widgets/toolu_rota01", {"marcados": [1]})
        self.assertEqual(status, 200)
        self.assertEqual([i["feito"] for i in novo["dados"]["itens"]], [False, True, False])
        _, lido = self.s.pedir("GET", "/api/widgets/toolu_rota01")
        self.assertEqual(lido, novo, "o que foi marcado fica salvo")
        self.assertEqual(self.s.pedir("PATCH", "/api/widgets/toolu_rota01", {"marcados": [9]})[0], 400)
        self.assertEqual(self.s.pedir("PATCH", "/api/widgets/toolu_rota01", {})[0], 400)
        self.assertEqual(self.s.pedir("PATCH", "/api/widgets/toolu_rota01", {"marcados": [0]},
                                      cab={"Origin": "http://evil.example"})[0], 403, "outra origem não muda nada")

    def test_erros_das_rotas(self):
        self._salvar("toolu_rota02", _norm("linha_do_tempo", {"eventos": [{"data": "1", "titulo": "a"}]})[0])
        self.assertEqual(self.s.pedir("PATCH", "/api/widgets/toolu_rota02", {"marcados": []})[0], 400, "só checklist")
        self.assertEqual(self.s.pedir("GET", "/api/widgets/toolu_naoexiste")[0], 404)
        self.assertEqual(self.s.pedir("GET", "/api/widgets/a.b")[0], 400)
        status, corpo = self.s.pedir("GET", "/api/widgets/imagem?url=http%3A%2F%2Fexample.com%2Fa.png")
        self.assertEqual(status, 400)
        self.assertIn("https", corpo["erro"])
        self.assertEqual(self.s.pedir("GET", "/api/widgets/imagem?url=https%3A%2F%2F127.0.0.1%2Fa.png")[0], 403)
        self.assertEqual(self.s.pedir("GET", "/api/mapa/tile/25/0/0")[0], 400)
        self.assertEqual(self.s.pedir("GET", "/api/mapa/tile/2/9/0")[0], 400)

    def test_demonstracao_mostra_o_widget(self):
        api_falsa = (base.RAIZ / "servidor" / "api_falsa.py").read_text(encoding="utf-8")
        if "widgets" not in api_falsa:
            self.skipTest("a API de mentira ainda não chama widgets.demo (integração pendente)")
        s = self.s
        _, r = s.pedir("POST", "/api/conversas", {"modo": "chat"})
        cid = r["conversa"]["id"]
        _, r = s.pedir("POST", f"/api/conversas/{cid}/enviar", {"texto": "mostre um mapa de São Paulo", "opcoes": {}})
        evs = s.eventos(r["execucao"])
        ev = next(e for e in evs if e["tipo"] == "widget")
        self.assertEqual(ev["widget"]["tipo"], "mapa")
        self.assertEqual(s.pedir("GET", f"/api/widgets/{ev['id']}"), (200, ev["widget"]))


if __name__ == "__main__":
    unittest.main()
