> Esta é a cópia em português do [`CLAUDE.md`](CLAUDE.md). A referência é o `CLAUDE.md` em inglês; se os dois divergirem, vale o inglês.

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
| `servidor/precos.py` | Planos de assinatura, perfis de mensagem, custo de uma mensagem, a estimativa "API ou assinatura?" e a projeção do teto |
| `servidor/estatisticas.py` | O painel "Seu uso": dias seguidos, mapa de calor, favorito, últimos 7 dias |
| `servidor/rotinas.py`, `rodar_rotina.py` | Rotinas: horário, `Relogio` (dentro do app, a cada 30 s), Agendador de Tarefas (`schtasks`, pasta `Clave`) e o executor sem janela |
| `servidor/ferramentas/excel.py`, `planilhas.py` | Excel com openpyxl e pelo Excel instalado (PowerShell + COM) |
| `servidor/ferramentas/memoria.py` | Ferramenta `memory_20250818` em `dados/memoria`, com índice `MEMORY.md` |
| `servidor/ferramentas/github.py`, `github_api.py` | GitHub REST (token do `gh` ou pessoal) |
| `servidor/atualizador.py`, `iniciar.py` | Atualização pela release mais nova do GitHub e supervisor |
| `servidor/api_falsa.py` | API do Claude de mentira (demonstração e testes) |
| `servidor/i18n.py`, `servidor/i18n/en/*.json` | Tradução do servidor: `t("texto em português", nome=valor)`, `traduzir_ferramentas()` para as descrições das ferramentas, `guardado_pt()` para o português guardado ao lado dos pacotes em inglês |
| `servidor/compactar.py` | `/compact`: compactação sob demanda (beta `compact-2026-09-04`); o bloco vira uma mensagem `compactacao` e o pedido começa nela |
| `servidor/importar.py` | Importar do Claude ou do ChatGPT: o pedido para colar lá, a leitura da resposta (seções e uma entrada por linha) e a aplicação |
| `servidor/ferramentas/email.py`, `word.py` | E-mail (IMAP e SMTP com senha de app, ou o Outlook clássico por COM) e Word (.docx com a biblioteca padrão, PDF pelo Word instalado) |
| `servidor/lancamentos.py`, `lancamentos.json` | Fichas de lançamento dos modelos: o cartão de apresentação (abre uma vez para modelo novo), o banner de modelo novo, os cartões "Modelos", a nota de inteligência e a fonte dela (`_inteligencia`) e os modelos que a conta tem e o Clave ainda não conhece (API de modelos, uma vez por dia) |
| `app/js/i18n.js`, `app/i18n/en/*.json` | Tradução da interface (`t()`); o servidor junta os catálogos em `/i18n/en.json` |
| `app/js/tour.js` | Tours com setinhas (destaque, balão, Voltar/Próximo/Pular), um por tela, mostrado uma vez (`cfg.tours_vistos`) |
| `app/js/lancamentos.js`, `app/img/modelos/` | Cartão de apresentação, banner de modelo novo e cartões "Modelos"; ilustrações (`<familia>.svg`) e renders (`render-<familia>.jpg`, feitas pelo `ferramentas/gerar_renders.py`) próprias do Clave por família de modelo |
| `app/js/*.js` | Interface sem build: `conversa.js` (tela e resposta ao vivo), `compositor.js` (caixa de texto e comandos de barra), `fluxo-ui.js` (cartões de aprovação, fluxo, plano, sugestão de outra conversa e avisos), `painel-uso.js` (painéis do início: uso e ambientes), `precos.js`, `fluxos.js`, `permissoes.js`, `plugins.js`, `rotinas.js`, `blocos.js`, `config.js`, `aprender.js`, `minichat.js`... |
| `agentes/`, `fluxos/`, `plugins/` | Agentes, fluxos e plugins que vêm com o app (o atualizador troca essas pastas) |
| `electron/` | Janela, menu de contexto, escolher pasta nativo, abrir links fora |
| `tutoriais/*.md`, `tutoriais/en/*.md` | Lições (cabeçalho: titulo, trilha, ordem, duracao, resumo), mesmo nome de arquivo nos dois idiomas; `glossario.md` alimenta o prompt. Os títulos do glossário em inglês guardam a âncora em português: `## API key {#chave-da-api}` |
| `modelo-de-pasta/`, `modelo-de-pasta-en/` | O modelo de pasta de trabalho. Em inglês o app copia o português (prints, scripts) e põe por cima os textos traduzidos de `modelo-de-pasta-en/`; `READ-ME-FIRST.md` substitui o `LEIA-PRIMEIRO.md` |
| `skills/ver-video/` | Skill que vem com o app (`SKILL.md` em inglês, **idêntico** ao de `modelo-de-pasta-en/.claude/skills/ver-video/`; os scripts são iguais aos do modelo em português; teste confere) |

## 3. Decisões que não se desfazem sem motivo

- **Idioma.** `cfg["idioma"]` é "pt-BR" ou "en". Instalação nova segue o Windows (`config.detectar_idioma()`:
  interface do Windows em português vira pt-BR; outra, ou ilegível, vira inglês); config gravada antes do idioma
  existir fica em português. `CLAVE_IDIOMA` força (os testes usam pt-BR). Trocar em Configurações > Aparência
  recarrega a janela.
- **A chave da tradução é o texto em português.** Interface: `t('...')` do `i18n.js`; servidor: `t("...")` do
  `i18n.py`; variáveis `{nome}`. Nunca chamar `t()` no topo do módulo (catálogo e idioma são lidos na hora):
  constante com texto de tela vira função. Toda chave literal precisa estar nos catálogos e as descrições das
  ferramentas também (o `testes/test_i18n.py` confere as duas coisas). O `t()` do servidor recebe `lingua` como
  2º argumento: nunca usar `{texto}` nem `{lingua}` como variável.
- **Plugins, agentes e fluxos do app são em inglês**, com o nome e a descrição em português guardados ao lado
  (`plugins/<p>/i18n/pt-BR.json`, `agentes/i18n/pt-BR.json`, `"i18n": {"pt-BR": ...}` dentro de
  `fluxos/*.json`); `i18n.guardado_pt()` e `fluxos._no_idioma()` aplicam isso para quem usa em português. Os
  ids (nomes de skill, agente e comando) não mudam. As etapas de fluxo são avisadas do idioma em que escrever.
- **Os campos das ferramentas têm nome em português** (`titulo`, `pedido`, `etapas`...) e puxam o modelo para o
  português: no Haiku 5.5, "escreva no idioma da pessoa" não bastou. O prompt de sistema em inglês diz com todas
  as letras ("write every value you put in tools ... in English"); manter assim ao criar ferramenta que a pessoa lê.
- **Ficha de lançamento de modelo é fato com fonte.** O `servidor/lancamentos.json` só tem dado conferível
  (preço oficial, número com a origem dita). Modelo novo: entrada em `modelos.MODELOS` (preço e o que aceita),
  ficha em `lancamentos.json` com `lancado_em` (o cartão de apresentação abre uma vez e o banner aparece por 14
  dias) e a `inteligencia` no mesmo índice dos outros, a família (ou ilustração e render novas para uma família
  nova), e uma release. Não preencher ficha antes do anúncio oficial. As renders são do Clave, geradas por
  código: nunca imagem da Anthropic.

- **A busca na web vem ligada** (3.1.0): `cfg["busca_web"]` nasce True e o modelo decide quando pesquisar.
  `migrar_web_por_padrao()` (ao subir o servidor) liga uma vez para quem já usava e tira o `busca_web` que as
  conversas antigas de chat e Code gravaram (era o padrão de antes, não uma escolha). Sem a opção no pedido, chat
  e Code seguem a configuração; etapa de fluxo, rotina e ajudante sempre mandam a deles. Regra que nega
  `WebSearch` continua valendo.
- **Enviar e-mail sempre pergunta.** O `email_enviar` mostra o e-mail inteiro e espera OK em qualquer modo; só
  uma regra de permitir específica `Email(enviar)` dispensa, e rotina para sem ela. Ler é livre. A Microsoft
  (Outlook.com, Microsoft 365) não aceita mais senha por IMAP: o caminho é o Outlook clássico (COM) ou o Zapier. O
  Outlook novo não tem COM.
- **Word sem python-docx.** Ele precisa do lxml (parte nativa que o Smart App Control pode barrar), então o
  `word.py` lê e escreve o XML do .docx com a biblioteca padrão. A troca de texto funciona quando o trecho está
  num pedaço (run) só.
- **`/compact` é a compactação sob demanda.** Com a conversa começando no bloco, a compactação automática por
  limite não vai junto (a API recusa os dois), e o `_para_api` corta tudo antes da última mensagem `compactacao`.
  Os arquivos do projeto vão na primeira mensagem da pessoa depois do corte.
- **`mostrar_arquivo` copia o arquivo** para `dados/anexos` (até 100 MB, qualquer tipo) e o resultado leva
  `(id ...)`, que a tela usa para desenhar a prévia (como nas planilhas geradas). Vídeo e áudio saem com Range.
- **O prompt de sistema economiza** (`sistema._economia`): resposta curta quando cabe, não reler, programa sem IA
  no lugar de rotina para trabalho repetitivo, modelo mais barato e recomendar ferramentas gratuitas uma vez.
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
- **Sugestão de outra conversa nunca abre sozinha.** A ferramenta `sugerir_conversa` só mostra um cartão; `POST /api/sugestoes/<id>/abrir` (o clique) cria a conversa com o pedido gravado no `tool_use` (não com o que a tela mandar) e a tabela `sugestoes` impede abrir duas vezes.
- **Estimativa pela assinatura é piso declarado.** A Anthropic não publica o limite das assinaturas em tokens; a conta usa o único número oficial (pelo menos 45 mensagens curtas por janela de 5 h no Pro, 5x e 20x no Max) e diz isso na tela. Os preços dos planos ficam editáveis porque o do Max 20x só aparece em guias de terceiros.
- **Lições ensinam o que o app faz de verdade.** Não prometer recurso que não
  existe (ex.: as ferramentas de Word criam .docx a partir de Markdown simples e trocam texto; não fazem
  controle de alterações nem mexem em imagens).
- **Demonstração não cobra**: com `CLAVE_API_FALSA`, o custo registrado é zero.

## 4. Rodar, testar, publicar

- Demonstração: `.venv\Scripts\python.exe servidor\servidor.py --demo --sem-senha --porta 8041`
  (dados em `%TEMP%\clave-demo`).
- Testes: `.venv\Scripts\python.exe -m unittest discover -s testes -t testes`
  (o `test_servidor` sobe o servidor de verdade com a API falsa; a API falsa
  também propõe fluxo e plano quando a mensagem pede).
- Janela de verdade: `.venv\Scripts\python.exe testes\testar_janela.py` (abre e
  fecha uma janela; confere pela porta de depuração).
- Prints de todas as telas: `testes\prints_demo.py <pasta> --porta 8041 [--idioma en]`
  com a demonstração no ar (Edge headless). Tira também os tours (eles abrem sozinhos
  na primeira vez), no idioma escolhido.
- Prints da tela ao vivo (fluxo rodando, aprovação, plano): `testes\prints_janela.py
  <pasta>` (abre o Electron com a demonstração, `CLAVE_TESTE_DEMO=1`).
- Teste real barato: `CLAVE_FORCAR_MODELO=claude-haiku-5-5` força todos os
  pedidos (inclusive os ajudantes) para o Haiku 5.5.
- Ícone: `ferramentas\gerar_icone.py` (gera `.png` e `.ico` a partir do SVG). Renders dos modelos:
  `python ferramentas\gerar_renders.py` (numpy e Pillow, fora do venv do app).
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
- Para conferir a sintaxe do JavaScript da interface, use
  `node --input-type=module --check < app/js/arquivo.js`. O `node --check arquivo.js`
  sozinho deixou passar um parêntese a mais que quebrou a tela inteira.
- Fórmulas do openpyxl são em inglês (`SUM`, vírgula); o Excel em português
  mostra `SOMA`.
