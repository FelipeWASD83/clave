# CLAUDE.md: Clave

App para Windows que usa o Claude pela API da Anthropic, com a chave de quem
usa. Chat, modo Code (agente numa pasta), fluxos com vários modelos, agentes,
permissões por regras, plugins, comandos de barra, rotinas, Excel, memória,
teto de gasto, GitHub, lições para iniciantes e atualização pelo GitHub. **Repositório
público, usado por outras pessoas**: nada pessoal entra no código, nas lições
nem no modelo de pasta. O teste que confere lê os termos proibidos de
`testes/privacidade-local.txt`, que fica **fora do git** (escrever a lista no
teste seria publicar o que ela protege); sem o arquivo, esse teste é pulado.
Licença MIT (`LICENSE`).

Versão atual: veja `versao.json` (vale também para `package.json` e o topo do
`CHANGELOG.md`: os três andam juntos).

## 1. Como roda

```
atalho / Clave.bat ─► ferramentas/abrir.pyw (preparar.py: baixa o Electron da versão pedida) ─► runtime/electron/electron.exe <pasta>
                                                              │
electron/main.js ─► servidor/iniciar.py --sem-janela --pai <pid>   (supervisor: aplica atualização, reinicia)
                        └─► servidor/servidor.py --porta 8040 --pai <pid>  (HTTP local + API + motor)
janela ◄── http://127.0.0.1:8040/?t=<segredo>  (vira cookie HttpOnly e some da URL)
```

- **Sem Electron** (download falhou): `iniciar.py` sozinho abre a interface numa
  janela de app do Edge (`--app=`) com perfil próprio em `dados/janela-edge`.
- **Segurança local**: só 127.0.0.1; `Host` conferido; toda rota `/api` exige o
  cookie de sessão (`dados/sessao.key`); pedido que muda algo com `Origin`
  diferente é recusado. Isso é o que impede uma página da internet de mandar o
  modo Code rodar comando. **Não afrouxar.** `--sem-senha` existe só para teste
  e preview.
- **Fim de vida**: fechar a janela mata a árvore do supervisor (`taskkill /T`).
  Se a janela morrer à força, o servidor percebe pelo `--pai` em até 3 s e
  fecha; sem janela por 10 min, fecha também (`--fechar-sem-janela`).
- **Dados**: tudo em `dados/` (fora do git): `clave.db` (SQLite), `config.json`,
  `segredos.json` (chave e tokens com DPAPI do Windows), `memoria/`, `anexos/`,
  `logs/`, `atualizacao/`, `plugins/` (instalados), `fluxos/` (modelos do
  usuário), `servidor.json` (porta do servidor aberto, para o
  `rodar_rotina.py`). `CLAVE_DADOS` troca a pasta (os testes usam isso).

## 2. Mapa do código

| Arquivo | O que faz |
|---|---|
| `servidor/servidor.py` | Rotas HTTP, estáticos, prévia (`/previa/<id>` com CSP sandbox), segurança |
| `servidor/execucao.py` | Motor de cada resposta: stream, ferramentas, aprovações, custo, desfazer, títulos |
| `servidor/pedido.py` | Monta o pedido por modelo e desliga recurso opcional que a API recusar (`dados/compat.json`) |
| `servidor/modelos.py` | Catálogo: preços (página oficial, 14/10/2026) e o que cada modelo aceita |
| `servidor/custo.py`, `orcamento.py` | Custo pelo `usage` e o teto do mês (ciclo, alertas, bloqueio) |
| `servidor/sistema.py` | Prompts de sistema (chat, Code, ajudante das lições, editor de memória) |
| `servidor/contexto_pasta.py` | CLAUDE.md/AGENTS.md da pasta para cima e skills (pasta, pessoais, do app) |
| `servidor/ferramentas/code.py` | Ferramentas do modo Code, decisão de permissão (`decidir`, com as regras) e comandos perigosos |
| `servidor/permissoes.py` | Regras no formato do Claude Code: ler e salvar (app em `cfg["permissoes"]`, pasta em `.claude/settings*.json`), casar comando, caminho e domínio, sugerir regra, filtrar ferramentas de servidor |
| `servidor/fluxos.py` | Fluxos: proposta (`normalizar`, estimativa, teto), `Rodada` (etapas como conversas escondidas, em grupos paralelos, com `Cofre` de custo) e modelos prontos |
| `servidor/agentes.py`, `comandos.py`, `plugins.py` | Agentes (`.claude/agents`), comandos de barra (`.claude/commands`, `$ARGUMENTS`) e plugins (`.claude-plugin/plugin.json`, instalação de pasta e do GitHub) |
| `servidor/rotinas.py`, `rodar_rotina.py` | Rotinas: horário, `Relogio` (dentro do app, a cada 30 s), Agendador de Tarefas (`schtasks`, pasta `Clave`) e o executor sem janela |
| `servidor/ferramentas/excel.py`, `planilhas.py` | Excel com openpyxl e pelo Excel instalado (PowerShell + COM) |
| `servidor/ferramentas/memoria.py` | Ferramenta `memory_20250818` em `dados/memoria`, com índice `MEMORY.md` |
| `servidor/ferramentas/github.py`, `github_api.py` | GitHub REST (token do `gh` ou pessoal) |
| `servidor/atualizador.py`, `iniciar.py` | Atualização pela release mais nova do GitHub e supervisor |
| `servidor/api_falsa.py` | API do Claude de mentira (demonstração e testes) |
| `app/js/*.js` | Interface sem build: `conversa.js` (tela e resposta ao vivo), `compositor.js` (caixa de texto e comandos de barra), `fluxo-ui.js` (cartões de aprovação, fluxo, plano e avisos), `fluxos.js`, `permissoes.js`, `plugins.js`, `rotinas.js`, `blocos.js`, `config.js`, `aprender.js`, `minichat.js`... |
| `agentes/`, `fluxos/`, `plugins/` | Agentes, fluxos e plugins que vêm com o app (o atualizador troca essas pastas) |
| `electron/` | Janela, menu de contexto, escolher pasta nativo, abrir links fora |
| `tutoriais/*.md` | Lições (cabeçalho: titulo, trilha, ordem, duracao, resumo); `glossario.md` alimenta o prompt |
| `modelo-de-pasta/` | O modelo de pasta de trabalho que o app copia |
| `skills/ver-video/` | Skill que vem com o app; **cópia idêntica** em `modelo-de-pasta/.claude/skills/ver-video` (teste confere) |

## 3. Decisões que não se desfazem sem motivo

- **SDK oficial `anthropic` em versão fixa** (`requirements.txt`). O Smart App
  Control do Windows pode barrar versão nova de pacote com parte nativa
  (`pydantic_core`, `jiter`). Atualizar só testando o import no Windows.
- **Sem executável próprio.** Empacotar o Electron (electron-builder) gera um
  `.exe` novo, sem assinatura e sem reputação, que o Smart App Control bloqueia.
  Por isso o Electron oficial é baixado (`ferramentas/preparar.py`, conferido
  pelo `SHASUMS256.txt` da release) e roda a pasta do app.
- **Prompt de sistema congelado por conversa** (`conversas.sistema`). Mudar a
  personalização vale para conversas novas. Mantém o cache e o raciocínio
  preservado (preserved thinking) válidos. Pela mesma razão o histórico só
  cresce: editar mensagem cria um ramo novo (irmão), não reescreve.
- **`block_binding: drop_block`** nos modelos atuais com raciocínio adaptativo:
  se algo mudar o começo da conversa (tool ligada no meio, troca de modelo), a
  API descarta o raciocínio antigo em vez de dar erro 400.
- **Recursos opcionais desligam sozinhos** quando a API recusa (fallbacks,
  updates, compactação, cache, eager streaming, web nova, modo rápido): ver
  `pedido.desligar_por_erro`. Só o Haiku 5.5 foi testado de verdade no
  desenvolvimento; os outros modelos dependem dessa rede.
- **Ajudantes** (modo `tutor` no Haiku 5.5, modo `memoria` no Sonnet 5.5) são
  conversas escondidas da lista (`banco.listar_conversas` filtra só chat e code)
  com modelo forçado (`execucao.AJUDANTES`).
- **Comandos perigosos sempre pedem OK**, mesmo no modo Livre
  (`code.PERIGOSOS`: qualquer apagar, push, reset, publicar, deploy, registro),
  a não ser que uma regra allow específica para aquele comando exista.
  Protegidos: as ferramentas de arquivo negam sempre; comando que cita um deles
  pede OK. No modo Plano, escrita e comando são negados. "Permitir nesta
  tarefa" só libera escrita e comando dentro da pasta: caminho de fora pede OK
  toda vez.
- **O atalho abre pelo `ferramentas/abrir.pyw`**, não direto no `electron.exe`:
  uma atualização pode trocar a versão do Electron (`versao.json`), e é o
  `abrir.pyw` que baixa a nova antes de abrir. O "reiniciar" da janela também
  passa por ele.
- **Excel com openpyxl**: ele escreve fórmula mas não calcula; recalcular é pelo
  Excel instalado (`excel.no_excel`). Ao salvar arquivo existente, imagens e
  formas podem se perder: a descrição da ferramenta manda salvar cópia.
- **Fluxo sempre pede OK** (cartão `fluxo_proposta`), em qualquer modo e com
  qualquer regra; regra só consegue proibir (`deny` em `Fluxo`). Cada etapa é
  uma conversa escondida (modo `etapa`) rodada por uma `Execucao` filha: os
  eventos sobem para a mãe como `etapa_evento`, os pedidos de OK aparecem na
  conversa mãe, o custo vai para a conversa mãe com origem `fluxo` e o
  `execucao_id` é o da mãe (o Desfazer cobre as etapas). O teto do fluxo é um
  `Cofre` dividido por todas as etapas.
- **Ordem das regras**: deny, depois ask, depois allow, depois o modo. Comando
  composto (`&&`, `|`, `;`...) é dividido: allow precisa cobrir todas as
  partes; deny e ask casam com qualquer uma. Comando perigoso só passa sem
  pergunta com allow específico (não genérico, como `Bash(*)`). Ferramenta de
  servidor (web, MCP) não tem como perguntar: ask vira deny lá.
- **Rotina nunca pergunta.** O que pediria OK faz a rotina parar
  (`rotina_parou`) com a regra sugerida. Rotina não roda fluxo.
- **Plugins**: hooks, MCP local e LSP de plugin são ignorados com aviso (rodar
  programa sozinho é o que não queremos de pacote baixado); MCP remoto vira
  sugestão de conector. Comando de plugin perde o `Bash` do `allowed-tools`.
  Extração do zip confere zip-slip e pula link simbólico.
- **SSE com enchimento**: a primeira coisa do `/eventos` é um comentário de
  4 KB e os cabeçalhos `X-Accel-Buffering: no` e `Cache-Control: no-transform`.
  Nesta máquina, o Edge headless segura o SSE até fechar (provavelmente o
  antivírus); o Electron e o curl recebem na hora. Para testar a tela ao vivo,
  usar `testes\prints_janela.py` (Electron), não o Edge headless.
- **Lições ensinam o que o app faz de verdade.** Não prometer recurso que não
  existe (ex.: o app não gera Word).
- **Demonstração não cobra**: com `CLAVE_API_FALSA`, o custo registrado é zero.

## 4. Rodar, testar, publicar

- Demonstração: `.venv\Scripts\python.exe servidor\servidor.py --demo --sem-senha --porta 8041`
  (dados em `%TEMP%\clave-demo`).
- Testes: `.venv\Scripts\python.exe -m unittest discover -s testes -t testes`
  (o `test_servidor` sobe o servidor de verdade com a API falsa; a API falsa
  também propõe fluxo e plano quando a mensagem pede).
- Janela de verdade: `.venv\Scripts\python.exe testes\testar_janela.py` (abre e
  fecha uma janela; confere pela porta de depuração).
- Prints de todas as telas: `testes\prints_demo.py <pasta> --porta 8041` com a
  demonstração no ar (Edge headless).
- Prints da tela ao vivo (fluxo rodando, aprovação, plano): `testes\prints_janela.py
  <pasta>` (abre o Electron com a demonstração, `CLAVE_TESTE_DEMO=1`).
- Teste real barato: `CLAVE_FORCAR_MODELO=claude-haiku-5-5` força todos os
  pedidos (inclusive os ajudantes) para o Haiku 5.5.
- Ícone: `ferramentas\gerar_icone.py` (gera `.png` e `.ico` a partir do SVG).
- **Publicar versão**: subir a versão em `versao.json`, `package.json` e no
  `CHANGELOG.md`, commitar, dar push e rodar `ferramentas\publicar-versao.ps1`,
  que cria a release `vX.Y.Z` com o pacote `.zip`. O botão Atualizar dos outros
  usuários baixa essa release. **Publicar é decisão do dono do repositório.**

## 5. Armadilhas

- `.ps1` com acento precisa estar em **UTF-8 com BOM** (o PowerShell 5.1 lê sem
  BOM como ANSI).
- O Python do `.venv` no Windows é um lançador que abre outro processo: para
  matar o servidor, mate a árvore (`taskkill /T`).
- Edição de arquivo com barra invertida feita por heredoc no Git Bash perde as
  barras: use a ferramenta de edição ou um script `.py` escrito direto.
- Fórmulas do openpyxl são em inglês (`SUM`, vírgula); o Excel em português
  mostra `SOMA`.
