"""5.0: o Haiku para quem já usava (com aviso), os vídeos das lições baixando sozinhos e o gancho das ferramentas que
moram em módulos próprios (provedores.py)."""
import base  # noqa: F401  (precisa vir antes dos módulos do servidor)

import http.client
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import config
import provedores
import videos


class _ConfigTemporaria(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-testes-base50-"))
        self.antes = config.DADOS
        config.DADOS = self.pasta
        config.recarregar()

    def tearDown(self):
        config.DADOS = self.antes
        config.recarregar()
        shutil.rmtree(self.pasta, ignore_errors=True)


class TestHaikuParaTodos(_ConfigTemporaria):
    def _migrar(self):
        import servidor
        servidor.migrar_haiku_padrao()
        config.recarregar()
        return config.carregar()

    def test_quem_usava_opus_vai_para_o_haiku_com_aviso(self):
        (self.pasta / "config.json").write_text(json.dumps({"configurado": True, "modelo_chat": "claude-opus-5-5",
                                                            "modelo_code": "claude-sonnet-5-5"}), encoding="utf-8")
        config.recarregar()
        cfg = self._migrar()
        self.assertEqual(cfg["modelo_chat"], "claude-haiku-5-5")
        self.assertEqual(cfg["modelo_code"], "claude-haiku-5-5")
        self.assertEqual(cfg["aviso_haiku"], {"modelo_chat": "claude-opus-5-5", "modelo_code": "claude-sonnet-5-5"})
        self.assertTrue(cfg["padrao_haiku_migrado"])

    def test_roda_uma_vez_so(self):
        (self.pasta / "config.json").write_text(json.dumps({"modelo_chat": "claude-opus-5-5"}), encoding="utf-8")
        config.recarregar()
        self._migrar()
        config.salvar({"modelo_chat": "claude-opus-5-5", "aviso_haiku": None})  # a pessoa escolheu voltar
        cfg = self._migrar()
        self.assertEqual(cfg["modelo_chat"], "claude-opus-5-5")
        self.assertIsNone(cfg["aviso_haiku"])

    def test_instalacao_nova_nao_ganha_aviso(self):
        cfg = self._migrar()
        self.assertTrue(cfg["padrao_haiku_migrado"])
        self.assertIsNone(cfg["aviso_haiku"])
        self.assertEqual(cfg["modelo_chat"], "claude-haiku-5-5")

    def test_sair_da_conta_nao_faz_a_migracao_voltar(self):
        self._migrar()
        config.resetar()
        self.assertTrue(config.carregar()["padrao_haiku_migrado"])

    def test_chaves_novas_tem_padrao(self):
        cfg = config.carregar()
        self.assertTrue(cfg["widgets_ligados"])
        self.assertEqual(cfg["widgets_imagens"], "clicar")
        self.assertTrue(cfg["navegador_ligado"])
        self.assertTrue(cfg["baixar_videos"])


class _Resposta:
    def __init__(self, dados, atraso=0.0):
        self.dados, self.pos, self.atraso = dados, 0, atraso
        self.headers = {"Content-Length": str(len(dados))}

    def read(self, n=-1):
        if self.atraso:
            time.sleep(self.atraso)
        if self.pos >= len(self.dados):
            return b""
        fim = len(self.dados) if n < 0 else min(len(self.dados), self.pos + 1024 * 64)
        pedaco = self.dados[self.pos:fim]
        self.pos = fim
        return pedaco

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _mp4(tamanho=300_000):
    return b"\x00\x00\x00\x18ftypisom" + b"\x00" * tamanho


class _LicoesComVideo(_ConfigTemporaria):
    def setUp(self):
        super().setUp()
        videos._andamento.clear()  # o estado de um teste (erro, parado) não vaza para o outro
        self.raiz_antes = config.RAIZ
        config.RAIZ = self.pasta  # sem video/saida aqui: nada conta como já baixado
        self.env = mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        os.environ.pop("CLAVE_API_FALSA", None)
        self.licoes = mock.patch("tutoriais.listar", return_value=[
            {"slug": "a", "titulo": "Lição A", "video": "video-a"},
            {"slug": "b", "titulo": "Lição B", "video": "video-b"},
            {"slug": "c", "titulo": "Lição C", "video": ""},
            {"slug": "d", "titulo": "Lição D", "video": "video-a"}])
        self.licoes.start()

    def tearDown(self):
        self.licoes.stop()
        self.env.stop()
        config.RAIZ = self.raiz_antes
        videos._andamento.clear()
        super().tearDown()


class TestVideosSozinhos(_LicoesComVideo):
    def test_faltando_lista_cada_video_uma_vez(self):
        self.assertEqual(videos.faltando("pt-BR"), [("video-a", "Lição A"), ("video-b", "Lição B")])

    def test_baixa_todos_e_mostra_na_aba_tarefas(self):
        registradas = []

        class Tarefa:
            def __init__(self, titulo):
                self.titulo, self.passos, self.fim = titulo, [], None
                registradas.append(self)

            def atualizar(self, progresso=None, detalhe=None):
                self.passos.append(progresso)

            def terminar(self, status="concluida", detalhe=None):
                self.fim = status

        falso = SimpleNamespace(registrar=lambda tipo, titulo, **kw: Tarefa(titulo))
        with mock.patch.dict("sys.modules", {"tarefas": falso}), \
                mock.patch.object(videos.urllib.request, "urlopen", side_effect=lambda *a, **k: _Resposta(_mp4())):
            self.assertTrue(videos.baixar_todos("pt-BR", em_segundo_plano=False))
        self.assertTrue((self.pasta / "videos" / "video-a.pt-BR.mp4").is_file())
        self.assertTrue((self.pasta / "videos" / "video-b.pt-BR.mp4").is_file())
        self.assertEqual([r.fim for r in registradas], ["concluida", "concluida"])
        self.assertTrue(all(p is not None and 0 < p <= 1 for r in registradas for p in r.passos))
        self.assertEqual(videos.estado("video-a", "pt-BR"), {"pronto": True})
        self.assertEqual(videos.faltando("pt-BR"), [])

    def test_nao_baixa_com_a_opcao_desligada_nem_na_demonstracao(self):
        config.salvar({"baixar_videos": False})
        with mock.patch.object(videos.urllib.request, "urlopen", side_effect=AssertionError("baixou")):
            self.assertFalse(videos.baixar_todos("pt-BR", em_segundo_plano=False))
        config.salvar({"baixar_videos": True})
        with mock.patch.dict(os.environ, {"CLAVE_API_FALSA": "http://127.0.0.1:1"}), \
                mock.patch.object(videos.urllib.request, "urlopen", side_effect=AssertionError("baixou")):
            self.assertFalse(videos.baixar_todos("pt-BR", em_segundo_plano=False))

    def test_erro_fica_no_estado_da_licao(self):
        with mock.patch.object(videos.urllib.request, "urlopen", return_value=_Resposta(b"<html>nao</html>")):
            with self.assertRaises(ValueError):
                videos.baixar("video-a", "en")
        e = videos.estado("video-a", "en")
        self.assertFalse(e["pronto"])
        self.assertIn("erro", e)

    def test_duas_chamadas_juntas_baixam_uma_vez(self):
        chamadas = []

        def abrir(*a, **k):
            chamadas.append(1)
            return _Resposta(_mp4(200_000), atraso=0.01)

        estados = []
        with mock.patch.object(videos.urllib.request, "urlopen", side_effect=abrir):
            t1 = threading.Thread(target=videos.baixar, args=("video-b", "pt-BR"))
            t1.start()
            for _ in range(200):  # enquanto baixa, a lição vê "baixando" com o progresso
                e = videos.estado("video-b", "pt-BR")
                if e.get("baixando"):
                    estados.append(e)
                    break
                time.sleep(0.01)
            videos.baixar("video-b", "pt-BR")
            t1.join(10)
        self.assertEqual(len(chamadas), 1)
        self.assertTrue(estados and estados[0]["baixando"])


class _Cortada(_Resposta):
    """O GitHub anuncia um tamanho e a conexão fecha antes (sem erro nenhum, só para de vir dado)."""

    def __init__(self, dados, anunciado):
        super().__init__(dados)
        self.headers = {"Content-Length": str(anunciado)}


class _Quebra(_Resposta):
    """Manda o primeiro pedaço e depois quebra com o erro dado."""

    def __init__(self, dados, erro):
        super().__init__(dados)
        self.erro = erro

    def read(self, n=-1):
        if self.pos:
            raise self.erro
        return super().read(n)


class _Presa(_Resposta):
    """Manda o primeiro pedaço e espera liberar para mandar o resto."""

    def __init__(self, dados, liberar: threading.Event):
        super().__init__(dados)
        self.liberar = liberar

    def read(self, n=-1):
        if self.pos:
            self.liberar.wait(10)
        return super().read(n)


class _TarefaFalsa:
    def __init__(self, titulo, parar):
        self.titulo, self.parar, self.passos, self.fim, self.detalhe = titulo, parar, [], None, None

    def atualizar(self, progresso=None, detalhe=None):
        self.passos.append(progresso)

    def terminar(self, status="concluida", detalhe=None):
        self.fim, self.detalhe = status, detalhe


class TestVideosRevisao(_LicoesComVideo):
    """O que a revisão achou: download cortado, erro inesperado, troca de idioma no meio e parar pela aba Tarefas."""

    def _tarefas_falsas(self):
        registradas = []

        def registrar(tipo, titulo, **kw):
            tf = _TarefaFalsa(titulo, kw.get("parar"))
            registradas.append(tf)
            return tf
        return registradas, mock.patch.dict("sys.modules", {"tarefas": SimpleNamespace(registrar=registrar)})

    def _sem_sobra(self):
        sobra = [a.name for a in (self.pasta / "videos").glob("*")] if (self.pasta / "videos").exists() else []
        self.assertEqual(sobra, [], "nem vídeo pela metade nem arquivo temporário")

    def test_download_cortado_no_meio_nao_vira_video_pronto(self):
        registradas, falso = self._tarefas_falsas()
        with falso, mock.patch.object(videos.urllib.request, "urlopen", return_value=_Cortada(_mp4(100_000), 300_000)):
            with self.assertRaisesRegex(ValueError, "parou no meio"):
                videos.baixar("video-a", "pt-BR")
        self._sem_sobra()
        e = videos.estado("video-a", "pt-BR")
        self.assertFalse(e["pronto"])
        self.assertIn("parou no meio", e["erro"], "a lição mostra o erro e oferece Tentar de novo")
        self.assertEqual(registradas[0].fim, "erro")
        with mock.patch.object(videos.urllib.request, "urlopen", return_value=_Resposta(_mp4())):
            videos.baixar("video-a", "pt-BR")
        self.assertEqual(videos.estado("video-a", "pt-BR"), {"pronto": True})

    def test_erro_inesperado_termina_a_tarefa_e_tira_do_baixando(self):
        for erro in (http.client.IncompleteRead(b"x" * 10, 500), http.client.BadStatusLine("lixo"),
                     RuntimeError("estranho")):
            registradas, falso = self._tarefas_falsas()
            with falso, mock.patch.object(videos.urllib.request, "urlopen", return_value=_Quebra(_mp4(), erro)):
                with self.assertRaises(ValueError, msg=type(erro).__name__) as ctx:
                    videos.baixar("video-b", "en")
            self.assertNotIsInstance(ctx.exception, http.client.HTTPException)
            e = videos.estado("video-b", "en")
            self.assertFalse(e.get("baixando"), f"{type(erro).__name__}: a lição não fica presa em Baixando")
            self.assertTrue(e.get("erro"))
            self.assertEqual(registradas[0].fim, "erro", "a tarefa não fica rodando para sempre")
            self._sem_sobra()
        # baixar_todos segue para o próximo vídeo depois de um erro inesperado
        registradas, falso = self._tarefas_falsas()

        def abrir(req, *a, **k):
            if "video-a" in req.full_url:
                return _Quebra(_mp4(), http.client.IncompleteRead(b"", 1))
            return _Resposta(_mp4())
        with falso, mock.patch.object(videos.urllib.request, "urlopen", side_effect=abrir):
            self.assertTrue(videos.baixar_todos("pt-BR", em_segundo_plano=False))
        self.assertEqual([r.fim for r in registradas], ["erro", "concluida"])
        self.assertEqual(videos.estado("video-b", "pt-BR"), {"pronto": True})

    def test_trocar_de_idioma_no_meio_baixa_o_idioma_novo(self):
        liberar = threading.Event()

        def abrir(req, *a, **k):
            if ".pt-BR.mp4" in req.full_url:
                return _Presa(_mp4(), liberar)
            return _Resposta(_mp4())
        _, falso = self._tarefas_falsas()
        with falso, mock.patch.object(videos.urllib.request, "urlopen", side_effect=abrir):
            self.assertTrue(videos.baixar_todos("pt-BR"))  # fica preso no primeiro vídeo em português
            for _ in range(200):
                if videos.estado("video-a", "pt-BR").get("baixando"):
                    break
                time.sleep(0.01)
            self.assertFalse(videos.baixar_todos("pt-BR"), "o mesmo idioma não roda duas vezes")
            self.assertTrue(videos.baixar_todos("en", em_segundo_plano=False), "o idioma novo começa ao lado")
            self.assertEqual(videos.estado("video-a", "en"), {"pronto": True})
            self.assertEqual(videos.estado("video-b", "en"), {"pronto": True})
            liberar.set()
            for th in [t for t in threading.enumerate() if t.name == "videos-pt-BR"]:
                th.join(10)
        self.assertEqual(videos.faltando("pt-BR"), [])

    def test_parar_pela_aba_tarefas(self):
        import tarefas
        liberar = threading.Event()
        erros = []

        def da_licao():
            try:
                videos.baixar("video-a", "pt-BR")
            except ValueError as e:
                erros.append(e)
        with mock.patch.object(videos.urllib.request, "urlopen", return_value=_Presa(_mp4(), liberar)):
            th = threading.Thread(target=da_licao)
            th.start()
            tf = None
            for _ in range(300):
                tf = next((x for x in tarefas.registradas() if x.tipo == "download" and x.rodando
                           and "Lição A" in x.titulo and x.progresso), None)
                if tf:
                    break
                time.sleep(0.01)
            self.assertIsNotNone(tf, "o download aparece na aba Tarefas")
            self.assertTrue(tf.item()["pode_parar"], "com o botão Parar")
            self.assertTrue(tf.parar())
            liberar.set()
            th.join(10)
        self.assertEqual(tf.status, "parada")
        self.assertIsInstance(erros[0], videos.DownloadParado)
        self._sem_sobra()
        self.assertEqual(videos.estado("video-a", "pt-BR"), {"pronto": False, "baixando": False, "parado": True})
        with mock.patch.object(videos.urllib.request, "urlopen", side_effect=AssertionError("recomeçou sozinho")):
            with self.assertRaises(videos.DownloadParado):
                videos.baixar("video-a", "pt-BR", automatico=True)
        with mock.patch.object(videos.urllib.request, "urlopen", return_value=_Resposta(_mp4())):
            videos.baixar("video-a", "pt-BR")  # o botão da lição baixa de novo
        self.assertEqual(videos.estado("video-a", "pt-BR"), {"pronto": True})


# ---- a lição na tela (a função playerVideo do aprender.js, rodando no Node) ----

_PLAYER_STUBS = r"""
const pedidos = [];
const api = (caminho, op) => new Promise((ok, falha) => pedidos.push({ caminho, metodo: (op && op.metodo) || 'GET', ok, falha }));
const estado = { info: { demo: false } };
let config = {};
const cfg = () => config;
const ic = () => '';
const idioma = () => 'pt-BR';
const t = (s, v) => (v ? s.replace(/\{(\w+)\}/g, (m, k) => (k in v ? String(v[k]) : m)) : s);
const timers = [];
const setTimeout = (fn) => { timers.push(fn); return timers.length; };
const clearTimeout = (id) => { if (id) timers[id - 1] = null; };
const rodarTimers = () => { const fila = timers.splice(0); fila.forEach((fn) => fn && fn()); };
const tick = () => new Promise((r) => globalThis.setTimeout(r, 5));
const el = (tag, attrs = {}, ...filhos) => ({
  tag, attrs, filhos: filhos.flat().filter(Boolean), isConnected: true, removido: false,
  replaceChildren(...x) { this.filhos = x; }, remove() { this.removido = true; },
  querySelector(sel) { return this.filhos.find((f) => f && f.tag === sel) || null; },
  addEventListener(ev, fn) { this.clique = fn; }, play() { return Promise.resolve(); },
});
const texto = (no) => (no ? [no.attrs?.texto || '', ...(no.filhos || []).map(texto)].join(' ') : '');
"""


def _player_fonte() -> str:
    fonte = (base.RAIZ / "app" / "js" / "aprender.js").read_text(encoding="utf-8")
    return fonte[fonte.index("function playerVideo(vid) {"):fonte.index("export function ancora")]


class TestPlayerDaLicaoNoNode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("sem o Node")

    def rodar(self, corpo: str):
        script = (_PLAYER_STUBS + _player_fonte() + "\nconst r = await (async () => {" + corpo + "})();\n"
                  + "process.stdout.write(JSON.stringify(r));\n")
        p = subprocess.run([self.node, "--input-type=module"], input=script, capture_output=True, text=True,
                           encoding="utf-8", timeout=60)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout)

    def test_resposta_velha_nao_troca_o_video_pela_barra(self):
        r = self.rodar(r"""
          const caixa = playerVideo('video-a');
          pedidos[0].ok({ pronto: false, baixando: false }); await tick();   // ainda não começou: a lição começa
          const post = pedidos[1];
          rodarTimers();                                                      // pergunta o andamento de novo
          const atrasada = pedidos[2];
          post.ok({ pronto: true }); await tick();                             // terminou: o vídeo aparece
          const comVideo = caixa.filhos[0]?.tag;
          atrasada.ok({ pronto: false, baixando: true, progresso: 0.5 }); await tick();  // a resposta velha chega depois
          rodarTimers(); await tick();
          return { post: post.metodo, comVideo, depois: caixa.filhos[0]?.tag, pedidos: pedidos.length };
        """)
        self.assertEqual(r["post"], "POST")
        self.assertEqual(r["comVideo"], "video")
        self.assertEqual(r["depois"], "video", "a barra de progresso não volta por cima do vídeo")
        self.assertEqual(r["pedidos"], 3, "com o vídeo na tela, ninguém pergunta mais o andamento")

    def test_na_demonstracao_nao_baixa_sozinho(self):
        r = self.rodar(r"""
          estado.info.demo = true;
          const caixa = playerVideo('video-a');
          pedidos[0].ok({ pronto: false, baixando: false }); await tick();
          const capa = caixa.filhos[0];
          const botao = capa.filhos[0];
          const antes = pedidos.length;
          botao.clique(); await tick();                                       // o botão continua funcionando
          return { antes, depois: pedidos.length, metodo: pedidos[1]?.metodo, botao: botao.tag };
        """)
        self.assertEqual(r["antes"], 1, "só perguntou o estado; não começou o download")
        self.assertEqual(r["botao"], "button")
        self.assertEqual((r["depois"], r["metodo"]), (2, "POST"))

    def test_parado_na_aba_tarefas_nao_recomeca(self):
        r = self.rodar(r"""
          const caixa = playerVideo('video-a');
          pedidos[0].ok({ pronto: false, baixando: false, parado: true }); await tick();
          return { pedidos: pedidos.length, texto: texto(caixa) };
        """)
        self.assertEqual(r["pedidos"], 1)
        self.assertIn("O download foi parado na aba Tarefas", r["texto"])

    def test_erro_do_download_nao_some_com_resposta_atrasada(self):
        r = self.rodar(r"""
          const caixa = playerVideo('video-a');
          pedidos[0].ok({ pronto: false, baixando: false }); await tick();
          const post = pedidos[1];
          rodarTimers();
          const atrasada = pedidos[2];
          post.falha(new Error('sem internet')); await tick();
          atrasada.ok({ pronto: false, baixando: true, progresso: 0.2 }); await tick();
          return texto(caixa);
        """)
        self.assertIn("Não deu para baixar o vídeo agora: sem internet", r)


class _Provedor:
    """Um módulo de mentira no formato de provedores.py."""
    NOMES = {"ferramenta_de_teste"}

    def __init__(self):
        self.executou = []

    def oferecer(self, ex, *, modo, op, cfg, etapa, pasta):
        return [{"name": "ferramenta_de_teste", "description": "Ferramenta de teste.",
                 "input_schema": {"type": "object", "properties": {}}}] if modo == "chat" else []

    def executar(self, ex, tid, nome, entrada, cfg, modo):
        self.executou.append((tid, nome, entrada))
        return ex.resultado(tid, "feito")


class TestProvedores(unittest.TestCase):
    def test_dono_e_resultado(self):
        prov = _Provedor()
        with mock.patch.object(provedores, "_carregados", [prov]):
            self.assertIs(provedores.dono("ferramenta_de_teste"), prov)
            self.assertIsNone(provedores.dono("outra"))
            import execucao
            ex = execucao.Execucao.__new__(execucao.Execucao)
            r = execucao.Execucao._uma(ex, "t1", "ferramenta_de_teste", {"a": 1}, {}, "chat")
        self.assertEqual(r, {"type": "tool_result", "tool_use_id": "t1", "content": "feito"})
        self.assertEqual(prov.executou, [("t1", "ferramenta_de_teste", {"a": 1})])

    def test_modulo_que_nao_existe_e_ignorado(self):
        with mock.patch.object(provedores, "MODULOS", ("modulo_que_nao_existe_xyz",)), \
                mock.patch.object(provedores, "_carregados", None):
            self.assertEqual(provedores.todos(), [])

    def test_execucao_tem_inicio(self):
        import execucao
        antes = time.time()
        ex = execucao.Execucao("conversa-x", {})
        self.assertGreaterEqual(ex.inicio, antes - 1)


if __name__ == "__main__":
    unittest.main()
