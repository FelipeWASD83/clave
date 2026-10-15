"""Uma API do Claude de mentira, para a demonstração e para os testes.

Responde no mesmo formato da API de verdade (inclusive o streaming), sem gastar
nada. As respostas são fixas: um texto de exemplo com raciocínio, e, no modo
Code, um pedido de ferramenta quando a mensagem fala de pasta, arquivo ou criar.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODELOS = [("claude-opus-5-5", "Claude Opus 5.5"), ("claude-sonnet-5-5", "Claude Sonnet 5.5"),
           ("claude-haiku-5-5", "Claude Haiku 5.5"), ("claude-fable-5-1", "Claude Fable 5.1")]

RESPOSTA_PADRAO = """Claro! Esta é uma resposta da **demonstração** do Clave: nada aqui foi para a internet e nada foi cobrado.

Você perguntou: *{pergunta}*

Algumas coisas que a interface sabe mostrar:

1. Listas numeradas e com marcadores
2. Tabelas
3. Código com cores e botão de copiar
4. Fórmulas, como $E = mc^2$

| Modelo | Bom para |
|---|---|
| Opus 5.5 | quase tudo, inclusive código |
| Sonnet 5.5 | dia a dia, mais barato |
| Haiku 5.5 | tarefas simples, muito barato |

```python
def saudacao(nome):
    return f"Olá, {{nome}}!"

print(saudacao("mundo"))
```

Quando você colocar a sua chave da API em Configurações, quem responde passa a ser o Claude de verdade."""


def _texto_usuario(msg) -> str:
    c = msg.get("content")
    if isinstance(c, str):
        return c
    partes = []
    for b in c or []:
        if b.get("type") == "text" and not b.get("text", "").startswith("<modo-do-clave>"):
            partes.append(b.get("text", ""))
    return "\n".join(partes)


def _tem_resultado(msg) -> bool:
    c = msg.get("content")
    return isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c)


def planejar(corpo: dict) -> tuple[list[dict], str]:
    """Decide os blocos da resposta: lista de {"type":..., ...} e o stop_reason."""
    msgs = corpo.get("messages") or []
    ultima = msgs[-1] if msgs else {"content": ""}
    nomes = {t.get("name") for t in corpo.get("tools") or []}
    thinking = corpo.get("thinking") or {}
    pensa = thinking.get("type") == "adaptive" and thinking.get("display") == "summarized"
    blocos: list[dict] = []
    sistema = str(corpo.get("system", ""))
    etapa = "de um fluxo (" in sistema
    if _tem_resultado(ultima):
        res = next(b for b in ultima["content"] if b.get("type") == "tool_result")
        conteudo = res.get("content")
        if isinstance(conteudo, list):
            conteudo = " ".join(b.get("text", "") for b in conteudo if b.get("type") == "text")
        if res.get("is_error"):
            return [{"type": "text", "text": "A ação não foi feita: " + str(conteudo)[:300]}], "end_turn"
        if str(conteudo).startswith(("Plano aprovado", "Plan approved")) and "escrever_arquivo" in nomes:
            return [{"type": "text", "text": "Plano aprovado. Executando o passo 1."},
                    {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "escrever_arquivo",
                     "input": {"caminho": "exemplo-do-plano.txt", "conteudo": "Feito depois do plano aprovado.\n"}}], \
                "tool_use"
        if etapa:
            return [{"type": "text", "text": "Relatório da etapa: fiz a minha parte. " + str(conteudo)[:200]}], "end_turn"
    texto_etapa = _texto_usuario(ultima)
    if etapa and not _tem_resultado(ultima):
        m = texto_etapa.split("<sua_etapa nome=\"", 1)
        nome_etapa = m[1].split("\"", 1)[0] if len(m) > 1 else "etapa"
        if "escrever_arquivo" in nomes and any(p in texto_etapa.lower() for p in ("crie", "create")):
            return [{"type": "text", "text": f"Etapa {nome_etapa}: vou criar o arquivo."},
                    {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "escrever_arquivo",
                     "input": {"caminho": "exemplo-do-fluxo.txt", "conteudo": "Criado por uma etapa de fluxo.\n"}}], \
                "tool_use"
        return [{"type": "text", "text": f"Relatório da etapa \"{nome_etapa}\": analisei o pedido e deixei tudo "
                 "pronto para a próxima etapa. (Demonstração: com a chave de verdade, o modelo faria de fato.)"}], "end_turn"
    if not _tem_resultado(ultima) and "executar_fluxo" in nomes and any(p in texto_etapa.lower() for p in ("fluxo", "workflow")):
        com_pasta = "escrever_arquivo" in nomes
        etapas = [{"nome": "Planejar", "agente": "planejador", "modelo": "opus", "esforco": "high",
                   "tarefa": "Entenda o pedido e escreva um plano curto.", "pode": ["ler"] if com_pasta else []},
                  {"nome": "Fazer", "agente": "executor", "modelo": "sonnet", "esforco": "high",
                   "tarefa": "Siga o plano: crie o arquivo de exemplo." if com_pasta else "Escreva o texto pedido.",
                   "pode": ["ler", "editar"] if com_pasta else []},
                  {"nome": "Revisar", "agente": "revisor", "modelo": "haiku", "esforco": "medium",
                   "tarefa": "Confira o que foi feito.", "pode": ["ler"] if com_pasta else []},
                  {"nome": "Conferir custos", "modelo": "haiku", "esforco": "low", "paralelo": True,
                   "tarefa": "Liste o que pode ter custado mais.", "pode": []}]
        return [{"type": "text", "text": "Proponho um fluxo em quatro etapas, cada uma num modelo."},
                {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "executar_fluxo",
                 "input": {"titulo": "Fluxo de demonstração", "objetivo": "Mostrar como um fluxo funciona.",
                           "etapas": etapas}}], "tool_use"
    if not _tem_resultado(ultima) and "sugerir_conversa" in nomes and any(p in texto_etapa.lower() for p in ("outra conversa", "another chat")):
        return [{"type": "text", "text": "Respondi o que você pediu. Notei uma coisa que vale fazer à parte:"},
                {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "sugerir_conversa",
                 "input": {"titulo": "Organizar as fotos por data",
                           "pedido": "Explique em linguagem simples como organizar fotos em pastas por ano e mês.",
                           "por_que": "É um trabalho separado deste e fica melhor numa conversa própria."}}], "tool_use"
    if _tem_resultado(ultima) and str(conteudo).startswith(("A sugestão apareceu", "The suggestion appeared")):
        return [{"type": "text", "text": "Se quiser, é só abrir pelo cartão."}], "end_turn"
    if _tem_resultado(ultima) and str(conteudo).startswith(("Respostas de quem usa", "Answers from the person")):
        return [{"type": "text", "text": "Combinado, sigo com o que você escolheu. (Demonstração: com a chave de "
                 "verdade, o Claude faria de fato.)"}], "end_turn"
    if not _tem_resultado(ultima) and "perguntar" in nomes and any(p in texto_etapa.lower() for p in ("pergunte", "ask me")):
        return [{"type": "text", "text": "Antes de começar, preciso de duas escolhas suas."},
                {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "perguntar",
                 "input": {"perguntas": [
                     {"pergunta": "Em que formato você quer o relatório?", "titulo": "Formato",
                      "opcoes": [{"rotulo": "Planilha do Excel (recomendado)", "descricao": "Dá para filtrar e somar depois."},
                                 {"rotulo": "Documento do Word", "descricao": "Bom para imprimir e mandar por e-mail."},
                                 {"rotulo": "Só aqui na conversa", "descricao": "Mais rápido, sem arquivo."}]},
                     {"pergunta": "Quais meses entram?", "titulo": "Período", "varias": True,
                      "opcoes": [{"rotulo": "Agosto"}, {"rotulo": "Setembro"}, {"rotulo": "Outubro"}]}]}}], "tool_use"
    # o plano aparece no modo Plano (o aviso escondido vai junto da mensagem) ou quando o pedido fala em plano
    modo_plano = any(isinstance(b, dict) and str(b.get("text", "")).startswith(("<modo-do-clave>Modo Plano ligado",
                                                                                 "<modo-do-clave>Plan mode is on"))
                     for b in (ultima.get("content") if isinstance(ultima.get("content"), list) else []))
    if (not _tem_resultado(ultima) and "apresentar_plano" in nomes
            and (modo_plano or any(p in texto_etapa.lower() for p in ("planej", "plano", "plan")))):
        return [{"type": "text", "text": "Olhei a pasta. Este é o plano:"},
                {"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "apresentar_plano",
                 "input": {"plano": "1. Criar o arquivo exemplo-do-plano.txt\n2. Conferir que ele existe"}}], "tool_use"
    if _tem_resultado(ultima):
        resumo = str(conteudo)[:400]
        return [{"type": "text", "text": "Pronto. Olhei o resultado:\n\n```\n" + resumo + "\n```\n\n"
                 "(Isto é a demonstração; com a chave de verdade, o Claude analisaria de fato.)"}], "end_turn"
    texto = _texto_usuario(ultima).lower()
    if pensa:
        blocos.append({"type": "thinking", "thinking": "Vou entender o pedido e montar uma resposta curta e "
                       "organizada, com um exemplo de cada formato."})
    if "mostrar_arquivo" in nomes and any(p in texto for p in ("mostre", "show")):
        blocos.append({"type": "text", "text": "Aqui está o print."})
        blocos.append({"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "mostrar_arquivo",
                       "input": {"caminho": "print-de-exemplo.png", "legenda": "O print da página de teste."}})
        return blocos, "tool_use"
    if "atualizar_tarefas" in nomes and any(p in texto for p in ("passos", "steps")):
        # de propósito, a lista fica aberta: a tela tem de mostrar que a resposta terminou mesmo assim
        blocos.append({"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "atualizar_tarefas",
                       "input": {"tarefas": [{"texto": "Ler a pasta", "estado": "feito"},
                                             {"texto": "Montar o relatório", "estado": "fazendo"},
                                             {"texto": "Conferir os totais", "estado": "pendente"}]}})
        return blocos, "tool_use"
    if "escrever_arquivo" in nomes and any(p in texto for p in ("crie", "criar", "create")):
        blocos.append({"type": "text", "text": "Vou criar um arquivo de exemplo na pasta."})
        blocos.append({"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "escrever_arquivo",
                       "input": {"caminho": "exemplo-do-clave.txt", "conteudo": "Arquivo criado pela demonstração.\n"}})
        return blocos, "tool_use"
    if "listar_pasta" in nomes and any(p in texto for p in ("pasta", "arquivo", "organiz", "lista", "folder", "file", "organi", "list")):
        blocos.append({"type": "text", "text": "Primeiro vou ver o que tem na pasta."})
        blocos.append({"type": "tool_use", "id": "toolu_" + uuid.uuid4().hex[:20], "name": "listar_pasta",
                       "input": {}})
        return blocos, "tool_use"
    if any(p in str(corpo.get("system", "")) for p in ("título curto", "short title")):
        en = "short title" in str(corpo.get("system", ""))
        return [{"type": "text", "text": "Demo conversation" if en else "Conversa de demonstração"}], "end_turn"
    sistema_txt = str(corpo.get("system", ""))
    if not nomes and any(m in sistema_txt for m in ("<jeito_de_falar>", "<way_of_talking>")):
        # o "Ver um exemplo" da personalização: mostra que as escolhas chegaram ao pedido
        pt = "<jeito_de_falar>" in sistema_txt
        trecho = sistema_txt.split("_falar>" if pt else "_talking>")[1]
        escolhas = "; ".join(l[2:].split(".")[0] for l in trecho.splitlines() if l.startswith("- "))
        texto = ("**Backup** é uma cópia dos seus arquivos guardada em outro lugar. (Demonstração: com a chave de "
                 f"verdade, o Claude responderia seguindo isto: {escolhas}.)") if pt else (
                 "A **backup** is a copy of your files kept somewhere else. (Demo: with a real key, Claude would "
                 f"answer following this: {escolhas}.)")
        return [{"type": "text", "text": texto}], "end_turn"
    blocos.append({"type": "text", "text": RESPOSTA_PADRAO.format(pergunta=_texto_usuario(ultima)[:200] or "...")})
    return blocos, "end_turn"


def _uso(corpo: dict, blocos: list[dict]) -> dict:
    entrada = max(10, len(json.dumps(corpo, ensure_ascii=False)) // 4)
    saida = max(5, sum(len(b.get("text", "") + b.get("thinking", "") + json.dumps(b.get("input", "")))
                       for b in blocos) // 4)
    return {"input_tokens": entrada, "output_tokens": saida, "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0}


class _Manip(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _json(self, d, status=200):
        b = json.dumps(d).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/v1/models"):
            dados = [{"id": i, "type": "model", "display_name": n, "created_at": "2026-01-01T00:00:00Z",
                      "max_input_tokens": 1_000_000, "max_tokens": 128_000} for i, n in MODELOS]
            return self._json({"data": dados, "has_more": False, "first_id": dados[0]["id"],
                               "last_id": dados[-1]["id"]})
        self._json({"type": "error", "error": {"type": "not_found_error", "message": "não existe"}}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        corpo = json.loads(self.rfile.read(n) or b"{}")
        if self.path.startswith("/v1/messages/count_tokens"):
            return self._json({"input_tokens": max(10, len(json.dumps(corpo)) // 4)})
        if not self.path.startswith("/v1/messages"):
            return self._json({"type": "error", "error": {"type": "not_found_error", "message": "não existe"}}, 404)
        modelo = corpo.get("model", "claude-haiku-5-5")
        mid = "msg_" + uuid.uuid4().hex[:20]
        if corpo.get("compaction"):  # o /compact: só o bloco do resumo, sem resposta
            pedidos = [_texto_usuario(m)[:80] for m in corpo.get("messages", []) if m.get("role") == "user"]
            resumo = ("Resumo de demonstração: a conversa teve " + str(len(pedidos)) + " pedidos. O último foi: "
                      + (pedidos[-1] if pedidos else "nenhum") + ".")
            return self._json({"id": mid, "type": "message", "role": "assistant", "model": modelo,
                               "content": [{"type": "compaction", "content": resumo, "signature": "assinatura-falsa"}],
                               "stop_reason": "compaction", "stop_sequence": None,
                               "usage": {"input_tokens": 0, "output_tokens": 0, "iterations": [
                                   {"type": "compaction", "input_tokens": 500, "output_tokens": 60}]}})
        blocos, stop = planejar(corpo)
        uso = _uso(corpo, blocos)
        if not corpo.get("stream"):
            conteudo = []
            for b in blocos:
                b = dict(b)
                if b["type"] == "thinking":
                    b["signature"] = "assinatura-falsa"
                conteudo.append(b)
            return self._json({"id": mid, "type": "message", "role": "assistant", "model": modelo,
                               "content": conteudo, "stop_reason": stop, "stop_sequence": None, "usage": uso})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        def ev(nome, dados):
            self.wfile.write(f"event: {nome}\ndata: {json.dumps(dados, ensure_ascii=False)}\n\n".encode("utf-8"))
            self.wfile.flush()

        ev("message_start", {"type": "message_start", "message": {
            "id": mid, "type": "message", "role": "assistant", "model": modelo, "content": [],
            "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": uso["input_tokens"], "output_tokens": 1}}})
        for i, b in enumerate(blocos):
            if b["type"] == "thinking":
                ev("content_block_start", {"type": "content_block_start", "index": i,
                                           "content_block": {"type": "thinking", "thinking": "", "signature": ""}})
                for parte in _pedacos(b["thinking"]):
                    ev("content_block_delta", {"type": "content_block_delta", "index": i,
                                               "delta": {"type": "thinking_delta", "thinking": parte}})
                    time.sleep(0.01)
                ev("content_block_delta", {"type": "content_block_delta", "index": i,
                                           "delta": {"type": "signature_delta", "signature": "assinatura-falsa"}})
            elif b["type"] == "text":
                ev("content_block_start", {"type": "content_block_start", "index": i,
                                           "content_block": {"type": "text", "text": ""}})
                for parte in _pedacos(b["text"]):
                    ev("content_block_delta", {"type": "content_block_delta", "index": i,
                                               "delta": {"type": "text_delta", "text": parte}})
                    time.sleep(0.012)
            elif b["type"] == "tool_use":
                ev("content_block_start", {"type": "content_block_start", "index": i, "content_block": {
                    "type": "tool_use", "id": b["id"], "name": b["name"], "input": {}}})
                ev("content_block_delta", {"type": "content_block_delta", "index": i, "delta": {
                    "type": "input_json_delta", "partial_json": json.dumps(b["input"], ensure_ascii=False)}})
            ev("content_block_stop", {"type": "content_block_stop", "index": i})
        ev("message_delta", {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None},
                             "usage": {"output_tokens": uso["output_tokens"]}})
        ev("message_stop", {"type": "message_stop"})


def _pedacos(texto: str, tam: int = 18):
    for i in range(0, len(texto), tam):
        yield texto[i:i + tam]


def iniciar(porta: int = 0) -> str:
    srv = ThreadingHTTPServer(("127.0.0.1", porta), _Manip)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}"
