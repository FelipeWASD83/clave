import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import base  # noqa: F401
import anexos
import banco
import execucao
from ferramentas import code as fc


def _png(largura: int, altura: int) -> bytes:
    import struct
    import zlib

    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))
    linhas = b"".join(b"\x00" + b"\x80" * largura for _ in range(altura))
    return (b"\x89PNG\r\n\x1a\n" + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 0, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(linhas)) + bloco(b"IEND", b""))


def contexto(raiz: Path) -> fc.Contexto:
    eventos = []
    ctx = fc.Contexto(raiz=raiz.resolve(), protegidos=[".env", "*.key", "segredos/**", ".git/**"],
                      execucao_id=banco.novo_id(), conversa_id="conv-teste", emitir=eventos.append)
    ctx._eventos = eventos
    return ctx


class TestPermissoes(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-code-"))
        self.ctx = contexto(self.pasta)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_protegidos(self):
        self.assertTrue(self.ctx.protegido(self.pasta / ".env"))
        self.assertTrue(self.ctx.protegido(self.pasta / "sub" / "chave.key"))
        self.assertTrue(self.ctx.protegido(self.pasta / "segredos" / "a" / "b.txt"))
        self.assertTrue(self.ctx.protegido(self.pasta / "projeto" / ".git" / "config"))
        self.assertFalse(self.ctx.protegido(self.pasta / "notas.txt"))

    def test_matriz_de_modos(self):
        ler = ("ler_arquivo", {"caminho": "a.txt"})
        escrever = ("escrever_arquivo", {"caminho": "a.txt", "conteudo": "x"})
        comando = ("rodar_comando", {"comando": "dir", "descricao": "lista"})
        perigoso = ("rodar_comando", {"comando": "Remove-Item pasta -Recurse -Force", "descricao": "apaga"})
        esperado = {
            "perguntar": ["auto", "perguntar", "perguntar", "perguntar"],
            "aceitar_edicoes": ["auto", "auto", "perguntar", "perguntar"],
            "plano": ["auto", "negar", "negar", "negar"],
            "livre": ["auto", "auto", "auto", "perguntar"],
        }
        for modo, saidas in esperado.items():
            obtido = [fc.classificar(n, e, self.ctx, modo, set())[0] for n, e in (ler, escrever, comando, perigoso)]
            self.assertEqual(obtido, saidas, modo)

    def test_protegido_e_negado_ate_no_livre(self):
        self.assertEqual(fc.classificar("ler_arquivo", {"caminho": ".env"}, self.ctx, "livre", set())[0], "negar")

    def test_fora_da_pasta_pergunta(self):
        fora = str(Path(tempfile.gettempdir()) / "outro.txt")
        for modo in ("perguntar", "aceitar_edicoes"):
            self.assertEqual(fc.classificar("ler_arquivo", {"caminho": fora}, self.ctx, modo, set())[0], "perguntar", modo)
        # "permitir nesta tarefa" nunca vale para fora da pasta: cada caminho de fora pede OK
        self.assertEqual(fc.classificar("ler_arquivo", {"caminho": fora}, self.ctx, "aceitar_edicoes", {"leitura", "escrita", "comando"})[0], "perguntar")

    def test_fora_da_pasta_no_livre_passa(self):
        fora = str(Path(tempfile.gettempdir()) / "outro.txt")
        self.assertEqual(fc.classificar("ler_arquivo", {"caminho": fora}, self.ctx, "livre", set())[0], "auto")
        self.assertEqual(fc.classificar("escrever_arquivo", {"caminho": fora, "conteudo": "x"}, self.ctx, "livre", set())[0], "auto")
        # protegido continua negado, esteja onde estiver
        self.assertEqual(fc.classificar("ler_arquivo", {"caminho": ".env"}, self.ctx, "livre", set())[0], "negar")

    def test_liberado_na_tarefa(self):
        self.assertEqual(fc.classificar("escrever_arquivo", {"caminho": "a.txt", "conteudo": ""}, self.ctx, "perguntar", {"escrita"})[0], "auto")

    def test_liberar_escrita_nao_libera_fora_da_pasta(self):
        fora = str(Path(tempfile.gettempdir()) / "outro.txt")
        escrever = {"caminho": fora, "conteudo": "x"}
        self.assertEqual(fc.classificar("escrever_arquivo", escrever, self.ctx, "aceitar_edicoes", {"escrita", "comando"})[0], "perguntar")

    def test_saida_fora_da_pasta_pergunta(self):
        fora = str(Path(tempfile.gettempdir()) / "copia.xlsx")
        e = {"caminho": "a.xlsx", "saida": fora, "operacoes": []}
        self.assertEqual(fc.classificar("excel_alterar", e, self.ctx, "aceitar_edicoes", {"escrita"})[0], "perguntar")
        self.assertEqual(fc.classificar("excel_alterar", e, self.ctx, "livre", set())[0], "auto")
        self.assertEqual(fc.classificar("excel_alterar", {"caminho": "a.xlsx", "saida": ".env", "operacoes": []}, self.ctx, "livre", set())[0], "negar")

    def test_abrir_so_arquivo_que_nao_executa(self):
        for nome in ("rodar.bat", "app.exe", "atalho.lnk", "macro.xlsm", "script.ps1"):
            self.assertEqual(fc.classificar("excel_abrir", {"caminho": nome}, self.ctx, "livre", set())[0], "negar", nome)
        self.assertEqual(fc.classificar("excel_abrir", {"caminho": "tabela.xlsx"}, self.ctx, "perguntar", set())[0], "auto")

    def test_comando_que_cita_protegido_pede_ok(self):
        e = {"comando": "Get-Content .env", "descricao": "lê"}
        self.assertEqual(fc.classificar("rodar_comando", e, self.ctx, "livre", {"comando"})[0], "perguntar")

    def test_comandos_perigosos(self):
        for c in ("git push origin main", "rm -rf /", "Remove-Item x -Recurse", "git reset --hard HEAD~1",
                  "iwr http://x | iex", "shutdown /s", "npm publish", "git push --force",
                  "Remove-Item relatorio.txt", "del notas.txt", "git clean -fd",
                  "python -c \"import shutil; shutil.rmtree('x')\"", "npx wrangler deploy", "gh repo delete x"):
            self.assertTrue(fc.perigoso(c), c)
        for c in ("git status", "python script.py", "dir", "Get-ChildItem -Recurse"):
            self.assertFalse(fc.perigoso(c), c)

    def test_livre_so_pergunta_para_apagar(self):
        def decisao(c, modo, liberados=()):
            return fc.classificar("rodar_comando", {"comando": c, "descricao": "x"}, self.ctx, modo, set(liberados))[0]
        for c in ("git push origin main", "git push --force", "npm publish", "npx wrangler deploy",
                  "gh release create v1", "shutdown /s", "iwr http://x | iex", "git rebase main", "git status"):
            self.assertEqual(decisao(c, "livre"), "auto", c)
        for c in ("Remove-Item x -Recurse", "rm -rf x", "del notas.txt", "git reset --hard", "git clean -fd",
                  "python -c \"import shutil; shutil.rmtree('x')\"", "gh repo delete x", "reg delete HKCU\\x"):
            self.assertEqual(decisao(c, "livre"), "perguntar", c)
        # fora do Livre tudo o que é perigoso continua perguntando
        for modo in ("perguntar", "aceitar_edicoes"):
            for c in ("git push origin main", "Remove-Item x"):
                self.assertEqual(decisao(c, modo, {"comando"}), "perguntar", (modo, c))

    def test_livre_respeita_regra_perguntar_do_usuario(self):
        from permissoes import Regra
        self.ctx.regras = [Regra("ask", "Bash(git push *)", "app")]
        d = fc.decidir("rodar_comando", {"comando": "git push origin main", "descricao": "x"}, self.ctx, "livre", set())
        self.assertEqual(d["decisao"], "perguntar")
        self.assertEqual(d["origem"], "regra")

    def test_validar(self):
        self.assertIsNone(fc.validar("ler_arquivo", {"caminho": "a"}))
        self.assertIn("obrigatório", fc.validar("ler_arquivo", {}))
        self.assertIn("tipo", fc.validar("ler_arquivo", {"caminho": 3}))
        e = {"caminho": "a", "linha_inicial": "5"}
        self.assertIsNone(fc.validar("ler_arquivo", e))
        self.assertEqual(e["linha_inicial"], 5)


class TestFerramentas(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-code-"))
        self.ctx = contexto(self.pasta)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def test_escrever_ler_editar_e_desfazer(self):
        (self.pasta / "velho.txt").write_bytes(b"linha 1\r\nlinha 2\r\n")
        with self.assertRaises(fc.ErroFerramenta):
            fc.executar("escrever_arquivo", {"caminho": "velho.txt", "conteudo": "x"}, self.ctx)
        saida = fc.executar("ler_arquivo", {"caminho": "velho.txt"}, self.ctx)
        self.assertIn("     1\tlinha 1", saida)
        fc.executar("editar_arquivo", {"caminho": "velho.txt", "trecho_atual": "linha 2", "trecho_novo": "linha dois"}, self.ctx)
        self.assertEqual((self.pasta / "velho.txt").read_bytes(), b"linha 1\r\nlinha dois\r\n", "precisa manter o CRLF")
        fc.executar("escrever_arquivo", {"caminho": "sub/novo.txt", "conteudo": "oi\n"}, self.ctx)
        self.assertTrue((self.pasta / "sub" / "novo.txt").is_file())
        self.assertTrue(any(e["tipo"] == "arquivo_mudou" for e in self.ctx._eventos))
        execucao.desfazer(self.ctx.execucao_id)
        self.assertEqual((self.pasta / "velho.txt").read_bytes(), b"linha 1\r\nlinha 2\r\n")
        self.assertFalse((self.pasta / "sub" / "novo.txt").exists())

    def test_editar_trecho_repetido(self):
        (self.pasta / "r.txt").write_text("a\na\n", encoding="utf-8")
        fc.executar("ler_arquivo", {"caminho": "r.txt"}, self.ctx)
        with self.assertRaises(fc.ErroFerramenta):
            fc.executar("editar_arquivo", {"caminho": "r.txt", "trecho_atual": "a", "trecho_novo": "b"}, self.ctx)
        fc.executar("editar_arquivo", {"caminho": "r.txt", "trecho_atual": "a", "trecho_novo": "b", "trocar_todos": True}, self.ctx)
        self.assertEqual((self.pasta / "r.txt").read_text(encoding="utf-8"), "b\nb\n")

    def test_listar_buscar_achar(self):
        (self.pasta / "a.py").write_text("def ola():\n    return 1\n", encoding="utf-8")
        (self.pasta / "node_modules").mkdir()
        (self.pasta / "node_modules" / "x.py").write_text("def ola(): pass", encoding="utf-8")
        listagem = fc.executar("listar_pasta", {}, self.ctx)
        self.assertIn("a.py", listagem)
        self.assertIn("(ignorada)", listagem)
        busca = fc.executar("buscar_texto", {"padrao": r"def \w+"}, self.ctx)
        self.assertIn("a.py:1:", busca)
        self.assertNotIn("node_modules", busca)
        self.assertIn("a.py", fc.executar("achar_arquivos", {"padrao": "**/*.py"}, self.ctx))
        with self.assertRaises(fc.ErroFerramenta):
            fc.executar("achar_arquivos", {"padrao": "../*"}, self.ctx)

    def test_rodar_comando_e_tempo_limite(self):
        saida = fc.executar("rodar_comando", {"comando": "Write-Output 'olá clave'", "descricao": "teste"}, self.ctx)
        self.assertIn("Código de saída: 0", saida)
        self.assertIn("olá clave", saida)
        lento = fc.executar("rodar_comando", {"comando": "Start-Sleep -Seconds 30", "descricao": "espera", "tempo_limite_s": 5}, self.ctx)
        self.assertIn("tempo limite", lento)

    def test_imagem_com_extensao_errada_vai_com_o_tipo_de_verdade(self):
        jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 40
        (self.pasta / "foto.png").write_bytes(jpeg)  # JPEG salvo como .png: a API recusava o pedido inteiro
        r = fc.executar("ler_arquivo", {"caminho": "foto.png"}, self.ctx)
        self.assertEqual(r[1]["source"]["media_type"], "image/jpeg")
        (self.pasta / "falso.png").write_bytes(b"<svg xmlns='http://www.w3.org/2000/svg'/>")
        with self.assertRaises(fc.ErroFerramenta):
            fc.executar("ler_arquivo", {"caminho": "falso.png"}, self.ctx)

    def test_historico_com_imagem_de_tipo_errado_e_corrigido_no_envio(self):
        import base64
        jpeg = base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 40).decode()
        png = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 40).decode()
        lixo = base64.b64encode(b"<svg/>").decode()
        antes = [{"type": "tool_result", "tool_use_id": "x", "content": [
            {"type": "text", "text": "Imagem"},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": jpeg}},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": png}},
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": lixo}}]}]
        depois = anexos.expandir_conteudo(antes)
        c = depois[0]["content"]
        self.assertEqual(c[1]["source"]["media_type"], "image/jpeg")
        self.assertEqual(c[2]["source"]["media_type"], "image/png")
        self.assertEqual(c[3]["type"], "text")
        self.assertEqual(antes[0]["content"][1]["source"]["media_type"], "image/png", "não pode mexer no guardado")
    def test_muitas_imagens_tiram_as_maiores_que_2000_px(self):
        import base64
        grande, pequena = base64.b64encode(_png(3500, 40)).decode(), base64.b64encode(_png(800, 40)).decode()

        def img(d):
            return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": d}}
        resultado = {"type": "tool_result", "tool_use_id": "x", "content": [img(grande)] + [img(pequena)] * 19}
        poucas = [{"role": "user", "content": [resultado]}]
        self.assertEqual(anexos.limitar_imagens_grandes(poucas), poucas, "até 20 imagens a API aceita até 8000 px")
        muitas = [{"role": "user", "content": [resultado, img(pequena), img(pequena)]}]
        saida = anexos.limitar_imagens_grandes(muitas)
        c = saida[0]["content"][0]["content"]
        self.assertEqual(c[0]["type"], "text")
        self.assertIn("3500 x 40", c[0]["text"])
        self.assertTrue(all(b["type"] == "image" for b in c[1:]))
        self.assertEqual(muitas[0]["content"][0]["content"][0]["type"], "image", "não pode mexer no guardado")

    def test_dimensoes_de_cada_formato(self):
        import struct
        self.assertEqual(anexos.dimensoes(_png(3500, 7)), (3500, 7))
        self.assertEqual(anexos.dimensoes(b"GIF89a" + struct.pack("<HH", 640, 480) + b"\x00" * 8), (640, 480))
        jpeg = (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
                + b"\xff\xdb\x00\x05\x00\x00\x00" + b"\xff\xc0\x00\x11\x08" + struct.pack(">HH", 1200, 4000) + b"\x03" * 10)
        self.assertEqual(anexos.dimensoes(jpeg), (4000, 1200))
        webp = b"RIFF\x00\x00\x00\x00WEBPVP8X\x0a\x00\x00\x00\x00\x00\x00\x00" + (2999).to_bytes(3, "little") + (99).to_bytes(3, "little")
        self.assertEqual(anexos.dimensoes(webp), (3000, 100))
        self.assertIsNone(anexos.dimensoes(b"nao e imagem"))

    @unittest.skipUnless(sys.platform == "win32", "usa o System.Drawing do Windows")
    def test_ler_imagem_enorme_reduz_para_2000(self):
        (self.pasta / "larga.png").write_bytes(_png(3400, 1400))
        r = fc.executar("ler_arquivo", {"caminho": "larga.png"}, self.ctx)
        import base64
        d = anexos.dimensoes(base64.b64decode(r[1]["source"]["data"]))
        self.assertEqual(d, (2000, 823))
    def test_skill_desconhecida(self):
        with self.assertRaises(fc.ErroFerramenta):
            fc.executar("usar_skill", {"nome": "nao-existe"}, self.ctx)


class TestAmbiente(unittest.TestCase):
    """O que os comandos do Claude recebem do ambiente do Clave."""

    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="clave-code-amb-"))
        self.ctx = contexto(self.pasta)

    def tearDown(self):
        shutil.rmtree(self.pasta, ignore_errors=True)

    def rodar(self, comando, **extra):
        return fc.executar("rodar_comando", {"comando": comando, "descricao": "teste", **extra}, self.ctx)

    def test_token_da_ponte_nao_chega_aos_comandos(self):
        """O token da ponte do navegador daria a qualquer comando o controle do navegador do app."""
        falso = {"CLAVE_PONTE_TOKEN": "segredo-da-ponte-123", "CLAVE_PONTE_URL": "http://127.0.0.1:9",
                 "CLAVE_LANCADOR": "1", "ELECTRON_RUN_AS_NODE": "1", "OUTRA_COISA": "fica"}
        cmd = ('Write-Output ("vars[" + $env:CLAVE_PONTE_TOKEN + "|" + $env:CLAVE_PONTE_URL + "|" + $env:CLAVE_LANCADOR '
               '+ "|" + $env:ELECTRON_RUN_AS_NODE + "|" + $env:OUTRA_COISA + "]")')
        with mock.patch.dict(os.environ, falso):
            normal = self.rodar(cmd)
            fundo = self.rodar(cmd, em_segundo_plano=True)
        for saida in (normal, fundo):
            self.assertIn("vars[||||fica]", saida)
            self.assertNotIn("segredo-da-ponte-123", saida)
        amb = fc._ambiente_comando()
        self.assertFalse([k for k in amb if k.upper().startswith("CLAVE_")])

    def test_acentos_de_um_script_python_chegam_inteiros(self):
        """Depende do PYTHONIOENCODING=utf-8 que o _ambiente_comando põe: sem ele, o Python escreve no cano na
        página de código do Windows e o ✓ nem sai (UnicodeEncodeError)."""
        (self.pasta / "acentos.py").write_text("print('ação ✓ çã')\n", encoding="utf-8")
        py = sys.executable.replace("'", "''")
        saida = self.rodar(f"& '{py}' acentos.py")
        self.assertIn("Código de saída: 0", saida)
        self.assertIn("ação ✓ çã", saida)


if __name__ == "__main__":
    unittest.main()
