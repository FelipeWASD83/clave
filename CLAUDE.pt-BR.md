> Esta é a cópia em português do [`CLAUDE.md`](CLAUDE.md). A referência é o `CLAUDE.md` em inglês; se os dois divergirem, vale o inglês.

# CLAUDE.md: Clave

App para Windows que usa o Claude pela API da Anthropic, com a chave de quem
usa. Chat, modo Code (agente numa pasta, com um painel lateral: arquivos,
visualizador, console, navegador e tarefas em segundo plano), widgets, fluxos com
vários modelos, agentes, permissões por regras, plugins, comandos de barra, rotinas, Excel, memória,
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
  e preview. A ponte do navegador do Code (`electron/main.js`) segue a mesma
  ideia: só 127.0.0.1, porta e token aleatórios passados ao servidor em
  `CLAVE_PONTE_URL` e `CLAVE_PONTE_TOKEN`, e pedido com cabeçalho `Origin` ou
  `Host` de fora é recusado. Comandos e consoles nunca herdam as variáveis
  `CLAVE_*` (o token inclusive).
- **Fim de vida**: fechar a janela (e o reiniciar da janela) primeiro manda
  `/api/sair` com o cookie de sessão e espera até 3 s o supervisor sair
  (`pararServidorComCalma`). Nesse caminho o `atexit` do servidor fecha os
  consoles e os comandos em segundo plano com cuidado: programas com janela
  sobrevivem, órfãos e fora do alcance do `/T`. Só depois disso, ou se o pedido
  falhar, o Electron mata a árvore do supervisor (`taskkill /T /F`). Se a janela
  morrer à força, o servidor percebe pelo `--pai` em até 3 s e sai com
  `os._exit` (sem `atexit`: os Job Objects fecham e levam tudo, janelas
  inclusive); sem janela por 10 min, fecha também (`--fechar-sem-janela`).
- **Dados**: tudo em `dados/` (fora do git): `clave.db` (SQLite), `config.json`,
  `segredos.json` (chave e tokens com DPAPI do Windows), `memoria/`, `anexos/`,
  `logs/`, `atualizacao/`, `plugins/` (instalados), `fluxos/` (modelos do
  usuário), `servidor.json` (porta do servidor aberto, para o
  `rodar_rotina.py`), `widgets/` (um JSON por chamada de widget), `cache/`
  (tiles do mapa, imagens dos widgets, `geocode.json`), `tarefas/` (registros das
  tarefas em segundo plano), `videos/` (vídeos das lições) e `ponte.json` (o
  endereço e o token da ponte, só com `CLAVE_TESTE_DEMO=1`, apagado ao sair). Os
  cookies e o armazenamento do navegador ficam no perfil do Electron (partição
  `persist:clave-navegador`), não em `dados/`. `CLAVE_DADOS` troca a pasta (os
  testes usam isso).

## 2. Mapa do código

| Arquivo | O que faz |
|---|---|
| `servidor/servidor.py` | Rotas HTTP, estáticos, prévia (`/previa/<id>` com CSP sandbox), segurança, as migrações ao subir; importa `console`, `explorador`, `navegador`, `tarefas` e `widgets` para as rotas deles existirem desde o começo |
| `servidor/rotas.py` | O registro das rotas (`@rota`, `Erro`, `ROTAS`) que o `servidor.py` e o módulo de cada parte dividem; um módulo registra as rotas dele quando é importado |
| `servidor/execucao.py` | Motor de cada resposta: stream, ferramentas, aprovações, custo, desfazer, títulos |
| `servidor/provedores.py` | Ferramentas que moram em módulo próprio (`MODULOS`: `widgets`, `navegador`). Cada módulo tem `NOMES`, `oferecer()` (as definições que valem nesta resposta, ou `[]`), `executar()` e, opcional, `definicoes_para_teste()`; o `execucao.py` pergunta a cada módulo |
| `servidor/pedido.py` | Monta o pedido por modelo e desliga recurso opcional que a API recusar (`dados/compat.json`) |
| `servidor/modelos.py` | Catálogo: preços (página oficial, 14/10/2026) e o que cada modelo aceita |
| `servidor/custo.py`, `orcamento.py` | Custo pelo `usage` e o teto do mês (ciclo, alertas, bloqueio) |
| `servidor/sistema.py` | Prompts de sistema (chat, Code, ajudante das lições, editor de memória) |
| `servidor/contexto_pasta.py` | CLAUDE.md/AGENTS.md da pasta para cima e skills (pasta, pessoais, do app) |
| `servidor/ferramentas/code.py` | Ferramentas do modo Code, decisão de permissão (`decidir`, com as regras), comandos perigosos, comandos em segundo plano (`em_segundo_plano`, `ver_comando`, `parar_comando`), o Job Object de todo comando (`_Job`) e o ambiente dos comandos sem `CLAVE_*` (`_ambiente_comando`) |
| `servidor/permissoes.py` | Regras no formato do Claude Code: ler e salvar (app em `cfg["permissoes"]`, pasta em `.claude/settings*.json`), casar comando, caminho, domínio e `Navegador(...)` (ação, site e porta, ações também em inglês), sugerir regra, filtrar ferramentas de servidor, e ler host e URL como o navegador lê (`host_canonico`, `url_canonica`, `site_de`) |
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
| `servidor/tom.py` | O jeito de falar (tom básico e os controles de Menos, Padrão e Mais): a frase de cada escolha no prompt de sistema e o exemplo no Haiku |
| `servidor/conselheiro.py` | O conselheiro de modelo: o Haiku lê a conversa na 1ª mensagem e a cada 5 e recomenda o modelo mais barato que faz a tarefa (`recomendar_modelo`, ferramenta forçada) |
| `servidor/desinstalador.py` | Confere se esta pasta pode se desinstalar sozinha e lança o `desinstalar.ps1` fora da árvore de processos do servidor |
| `ferramentas/desinstalar.ps1` | Desinstalar, rodando do `%TEMP%` depois que o app fecha: atalhos que apontam para esta pasta, `%APPDATA%\Clave` e a pasta do Clave, atrás de travas de segurança |
| `servidor/videos.py` | Os vídeos das lições: o arquivo local na cópia de desenvolvimento (`video/saida/`), senão baixado da release `videos` para `dados/videos` (em segundo plano pelo `baixar_todos()`, ou no play), cada download registrado em Tarefas e com como parar, entregue com Range |
| `servidor/console.py` | A aba Console: ConPTY por ctypes (um modo simples por pipes quando falha), cada shell num Job Object, a saída guardada em pedaços numerados (os últimos ~2 MB) e lida por SSE a partir de `desde`, até 6 consoles, rotas `/api/consoles`, e `encerrar_job_com_cuidado()` (programas com janela sobrevivem), que o `code.py` também usa |
| `servidor/explorador.py` | Rotas das abas Arquivos e Visualizador (`/api/arquivos/*`): lista, busca, conteúdo com a codificação achada, bruto com Range e CSP sandbox, planilha, docx, mudanças do Claude pelos checkpoints, criar, renomear, Lixeira (`SHFileOperationW`), abrir e revelar. Nada sai da raiz (`..`, unidade, fluxo do NTFS, junção apontando para fora) e arquivo protegido precisa de `forcar=1` |
| `servidor/navegador.py` | O navegador do Code: as ferramentas `navegador_*`, a decisão por regra, modo e site por tarefa (`decidir`), o cliente da ponte (`chamar`), o texto da página entre marcas aleatórias, a busca de servidores locais (netstat, tasklist e um GET rápido) e `/api/navegador/estado`, `localhosts` e `limpar` |
| `servidor/tarefas.py` | O registro da aba Tarefas: `registrar()` para comandos em segundo plano e downloads (registro, endereços locais, parar), mais as respostas, fluxos e rotinas lidos do `execucao`; `parar_da_conversa()`, `conversa_dona()` e `/api/tarefas` |
| `servidor/widgets.py` | `mostrar_widget`: `normalizar()` dos 8 tipos, um JSON por chamada em `dados/widgets`, o proxy de imagem `/api/widgets/imagem` (trava contra SSRF), `GET` e `PATCH /api/widgets/<tid>`, `texto_para_exportar()` (exportação em Markdown), faxina dos caches e `demo()` para a API falsa |
| `servidor/mapas.py` | Endereço para coordenada (Nominatim, 1 busca por segundo no app inteiro, cache em disco) e o proxy de tiles do OpenStreetMap `/api/mapa/tile/<z>/<x>/<y>` (cache em disco, no mínimo 7 dias, revalidação com ETag/Last-Modified, faxina) |
| `servidor/ferramentas/email.py`, `word.py` | E-mail (IMAP e SMTP com senha de app, ou o Outlook clássico por COM) e Word (.docx com a biblioteca padrão, PDF pelo Word instalado) |
| `servidor/lancamentos.py`, `lancamentos.json` | Fichas de lançamento dos modelos: o cartão de apresentação (abre uma vez para modelo novo), o banner de modelo novo, os cartões "Modelos", a nota de inteligência e a fonte dela (`_inteligencia`) e os modelos que a conta tem e o Clave ainda não conhece (API de modelos, uma vez por dia) |
| `app/js/i18n.js`, `app/i18n/en/*.json` | Tradução da interface (`t()`); o servidor junta os catálogos em `/i18n/en.json` |
| `app/js/tour.js` | Tours com setinhas (destaque, balão, Voltar/Próximo/Pular), uma lista por tela (o Code mostra `code` e depois `mesa`, o do painel), cada um mostrado uma vez (`cfg.tours_vistos`) |
| `app/js/painel.js`, `abas.js` | O painel lateral: `registrarAba()`, `abrirPainel(id, args)`, `fecharPainel()`, `alternarAba()`, `ouvirPainel()`, o contexto da conversa (`definirContexto`), a largura e os atalhos (`atalhoDoPainel`). O `abas.js` importa os módulos das abas |
| `app/js/arquivos.js`, `console.js`, `navegador.js`, `tarefas.js`, `previa.js` | As abas: Arquivos e Visualizador (`abrirArquivo()`), Console (xterm.js), Navegador (comanda a vista do Electron pelo `window.clave.navegador`), Tarefas (mais o `contadorTarefas()` da barra da esquerda e o `observarTarefas()`) e Prévia |
| `app/js/widgets.js` | Desenha os 8 tipos de widget (`renderizarWidget`, `widgetPorId`, `lembrarWidget`), Copiar como texto, baixar em PNG/SVG e o mapa com o Leaflet |
| `app/js/aviso-modelo.js` | O aviso único "O padrão agora é o Haiku 5.5" (`cfg.aviso_haiku`): Manter o Haiku ou Voltar para o de antes |
| `app/vendor/xterm/`, `app/vendor/leaflet/` | xterm.js 6.0.0 com o addon fit 0.11.0 (módulos ES, carregados na primeira vez que o Console abre) e Leaflet 1.9.4 (build em módulo ES), cada um com a LICENSE dele |
| `app/js/lancamentos.js`, `app/img/modelos/` | Cartão de apresentação, banner de modelo novo e cartões "Modelos"; ilustrações (`<familia>.svg`) e renders (`render-<familia>.jpg`, feitas pelo `ferramentas/gerar_renders.py`) próprias do Clave por família de modelo |
| `app/js/*.js` | Interface sem build: `conversa.js` (tela e resposta ao vivo), `markdown.js` (as respostas; blocos de código ganham Prévia e, no Code, Rodar no console), `compositor.js` (caixa de texto e comandos de barra), `fluxo-ui.js` (cartões de aprovação, fluxo, plano, sugestão de outra conversa e avisos), `painel-uso.js` (painéis do início: uso e ambientes), `precos.js`, `fluxos.js`, `permissoes.js`, `plugins.js`, `rotinas.js`, `blocos.js`, `config.js`, `aprender.js`, `minichat.js`... |
| `agentes/`, `fluxos/`, `plugins/` | Agentes, fluxos e plugins que vêm com o app (o atualizador troca essas pastas) |
| `electron/` | Janela, menu de contexto, escolher pasta nativo, abrir links fora, o fechamento com calma (`pararServidorComCalma`) e o navegador do Code: uma `WebContentsView` na partição `persist:clave-navegador`, a ponte HTTP para o servidor, os scripts que ele injeta num mundo isolado, e o `preload.js` (`window.clave.navegador`) para a aba |
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
- **Enviar e-mail pergunta.** O `email_enviar` mostra o e-mail inteiro e espera OK em qualquer modo, menos no Livre,
  onde sai direto a não ser que quem usa tenha escrito uma regra `ask` para `Email(enviar)`; uma regra de permitir
  específica `Email(enviar)` também dispensa, e rotina para sem ela. Ler é livre. A Microsoft
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
- **O jeito de falar só acrescenta, nunca troca.** Cada escolha diferente de Padrão vira uma frase dentro de
  `<jeito_de_falar>`; tudo em Padrão manda exatamente o prompt de antes (um teste confere). O que a pessoa escreveu em
  "Como você quer as respostas" vale mais que os controles. Não há tom Profissional nem Eficiente porque os estilos
  Formal e Conciso já cobrem isso.
- **`perguntar` e o plano fora do modo Plano passam pelo caminho das aprovações** (`_pedir_aprovacao`, decisões
  `responder`/`pular` e `pode_ir`/`mudar`/`nao_fazer`): esperam, sobrevivem a recarregar a tela
  (`aprovacoes_pendentes`) e nunca existem em rotina nem em etapa de fluxo. O `apresentar_plano` vai em todos os
  modos do Code enquanto `pedir_ok_plano` estiver ligado, com uma descrição só para todos os modos (a lista de
  ferramentas não muda quando o modo muda). O Haiku só apresentou o plano depois que o prompt de sistema deu
  critério concreto (3 arquivos ou mais, mover, renomear ou apagar, reorganizar pasta): manter concreto.
- **Os vídeos nunca vão dentro do app.** Cada MP4 tem vários MB, e o botão Atualizar baixaria todos a cada versão.
  Eles ficam na release `videos`, criada como pré-lançamento para o `releases/latest` (o botão Atualizar) nunca
  pegá-la; vídeo renderizado de novo: `gh release upload videos <arquivo> --clobber`. As lições apontam com
  `video: <id>` no cabeçalho (`<id>.<pt-BR|en>.mp4`), e o README aponta para lá também, com as capas de
  `video/capas/`. **Desde a 5.0 eles baixam sozinhos**: o `videos.baixar_todos()` roda em segundo plano ao subir o
  servidor e de novo quando o idioma muda ou o `baixar_videos` é ligado, só no idioma do app (uns 28 MB para os 4
  vídeos), uma rodada por idioma, nunca na demonstração. Cada download fica registrado em Tarefas e dá para parar por lá (o arquivo pela
  metade é apagado; a rodada automática não recomeça um vídeo parado até o app reiniciar, o botão da lição sim). Um
  download que termina antes do `Content-Length` que o GitHub anunciou é erro, nunca vídeo pronto. Com o
  `baixar_videos` desligado, a lição baixa no play, como antes.
- **O Haiku é o modelo padrão para todo mundo desde a 5.0** (a 4.3 fez dele o padrão só em instalação nova). A
  configuração antiga não diz se o modelo foi escolhido ou só ficou o padrão de antes, então o
  `migrar_haiku_padrao()` (ao subir o servidor, uma vez, marcado por `padrao_haiku_migrado`, que o `resetar()`
  mantém) troca `modelo_chat` e `modelo_code` para o Haiku quando um deles era outro e, se a configuração já estava
  pronta (`configurado`), guarda o par antigo em `aviso_haiku`. O `aviso-modelo.js` mostra o aviso uma vez (Manter o
  Haiku, ou Voltar para o de antes, que devolve o par) e limpa; se a pessoa já escolheu outro modelo, ele some sem
  aparecer. Conversas e rotinas com modelo próprio não mudam; rotina nova nasce no Haiku. O **conselheiro de
  modelo** roda antes da resposta na 1ª mensagem de quem usa e a cada 5
  (`(n - 1) % 5 == 0`), só no chat e no Code, nunca em rotina, etapa de fluxo, ajudante de lição, comando ou skill
  com modelo fixo, "gerar outra resposta" ou conversa com `modelo_fixo`. Só sugere, a não ser com
  `trocar_modelo_sozinho` ligado. O conselho fica gravado no `meta.conselho` da mensagem de quem usa (a tela
  redesenha a conversa quando a resposta termina, e o aviso com os botões precisa continuar lá); o que a pessoa
  decide vai para os `ajustes` da conversa (`conselho_visto`, `modelo`, `modelo_fixo`) pelo
  `PATCH ... ajustes_mesclar`. O `r_enviar` grava os `ajustes` antes de começar a resposta, para a escrita do
  conselheiro não se perder. Com `CLAVE_FORCAR_MODELO` (testes com a API de verdade) ele avisa a troca, mas o modelo
  forçado continua respondendo. Testado no Haiku de verdade: mantém o Haiku em pergunta simples, sobe em tarefa
  grande, desce do Opus numa tradução curta e escreve o motivo em inglês com o app em inglês.
- **Comandos nos dois idiomas**: o nome em português (o do arquivo) é o de verdade; `comandos.NOMES_EN` dá o nome em
  inglês de tudo que vem com o Clave (comandos do app, plugins, os comandos e as skills deles, fluxos prontos), cada
  parte separada por `:` traduzida. A resolução tenta primeiro o nome exato digitado e depois o `canonico()`, então
  uma skill da pessoa com o mesmo nome de uma tradução continua vencendo. Um teste falha quando plugin, comando,
  skill ou fluxo que vem com o Clave fica sem nome em inglês.
- **O painel lateral é uma moldura; as abas se registram sozinhas.** O `painel.js` não conhece aba nenhuma: cada
  módulo chama `registrarAba({ id, titulo, icone, modos, atalho, tecla, botao, soDepoisDeAberta, montar })` quando o
  `abas.js` importa, e a ordem vem do `ORDEM` do `painel.js`. O `montar()` roda na primeira vez que a aba abre e
  devolve os ganchos (`abrir`, `mostrar`, `esconder`, `contexto`, `redimensionar`). **A aba montada continua viva**
  quando o painel fecha ou a tela muda: o console guarda os shells e a saída, a vista do navegador a página. As abas
  conversam por contratos, não importando umas às outras: `clave:inserir-texto` (a caixa de mensagem),
  `clave:arquivos-mudaram` (a conversa dispara quando uma resposta escreve arquivos, com lista vazia depois de um
  `rodar_comando`), `abrirArquivo(caminho, { linha })`, `abrirPainel('navegador', { url })` e
  `abrirPainel('console', { comando })` (escreve o comando e nunca aperta Enter; um bloco de várias linhas entra com
  Shift+Enter entre elas). No servidor, cada parte registra as rotas no próprio módulo pelo `rotas.rota`, e o
  `servidor.py` importa os módulos ao subir (senão as rotas só existiriam depois da primeira resposta, quando o
  `provedores.todos()` importa).
- **As regras do navegador do Code** (o `navegador.py` decide, o `electron/main.js` guarda as travas que precisam
  da página):
  - Ele só existe na janela do Electron (as variáveis da ponte; o modo Edge mostra um aviso), numa partição
    própria, então os cookies e logins dele nunca se misturam com a sessão do app. Rotina e etapa de fluxo nunca
    recebem o navegador.
  - Ordem: `deny` de `Navegador` ou `deny` de `WebFetch(domain:x)` com domínio (um `deny` genérico de WebFetch não
    barra, senão barraria também os servidores de desenvolvimento em localhost), depois o modo Plano (sem clicar nem
    digitar), depois as regras `ask`, depois o **site por tarefa**: fora do Livre, a primeira ação num site que não é
    local mostra "Deixar o Claude usar o site X nesta tarefa?" (permitir só desta vez, nesta tarefa, sempre nesta
    pasta, ou sempre como `Navegador(site)`); localhost, 127.x e [::1] são livres. Depois, **clicar e digitar pedem
    OK toda vez** fora do Livre, a não ser que uma regra de permitir diga a ação (`Navegador(clicar:x)`): a regra só
    do site libera o site, não o clique. Por quê: a trava do site fecha o caminho "abrir o webmail logado, ler e
    levar para outro site", e um clique não tem desfazer.
  - Depois de cada ação, o site em que a página ficou (redirecionamento, clique, voltar) passa pelas mesmas regras:
    negado vira página em branco (`em_branco`), site novo mostra o cartão do site antes de o Claude ver qualquer
    coisa.
  - O clique ou a digitação aprovados ficam presos à página (origem e caminho) e ao elemento (papel e nome); a
    ponte recusa com `pagina_mudou` ou `elemento_mudou`, e sem `esperado` não faz nada. Os números dos elementos de
    uma leitura moram no mundo isolado (`__claveRefs`), nunca num atributo do DOM que um MutationObserver da página
    poderia passar para outro elemento.
  - O texto da página chega ao Claude entre marcas com um código aleatório a cada leitura (a página não forja o
    fim), e o título vai rotulado como dado da página. Campos de senha, código de acesso e cartão (pelo tipo, nome,
    autocomplete e rótulo) são recusados pela ponte: quem digita é a pessoa.
  - O site das regras e a URL da página passam pela mesma leitura do navegador (`permissoes.host_canonico` e
    `url_canonica`: maiúsculas, ponto no fim, `%xx`, letras largas, IDNA, IPv4 em qualquer forma, usuário e senha
    tirados) e o navegador abre a URL remontada, então nenhuma diferença de leitor escapa de uma regra.
  - Certificado de cliente nunca é enviado (`select-client-certificate` com callback vazio; senão o Electron entrega
    o primeiro certificado do Windows a qualquer site que pedir). Sair da conta e Configurações > Modo Code > Apagar
    os dados do navegador limpam a partição (ação `limpar` da ponte).
- **Widgets ficam gravados por chamada** em `dados/widgets/<id do tool_use>.json` (o que foi marcado no checklist
  também): reabrir a conversa lê por `GET /api/widgets/<tid>`, e a exportação em Markdown escreve o
  `widgets.texto_para_exportar()` no lugar da chamada. O `normalizar()` confere cada tipo e devolve erro claro ao
  Claude (link só https, cor só da paleta, preço lido como preço), e o `executar` confere de novo onde a ferramenta
  foi oferecida (nunca rotina, etapa de fluxo ou ajudante de lição, nem com `widgets_ligados` desligado).
  - **Imagem de fora só pelo `/api/widgets/imagem`**, uma trava contra SSRF: https na porta padrão, sem usuário na
    URL, todo IP resolvido público (conferido de novo a cada redirecionamento, no máximo 3, e a conexão vai para o
    IP conferido), até 5 MB, só PNG, JPEG, WebP e GIF (nunca SVG), guardada 7 dias.
  - **Foto só carrega com clique** por padrão (`widgets_imagens: "clicar"`): uma página que o Claude leu poderia
    plantar uma URL de imagem que leva dados da conversa para um servidor, e o botão diz os sites antes de carregar.
  - **Mapa carrega sem clique** porque os tiles vêm pelo proxy do próprio Clave, de um host fixo, seguindo a política
    de tiles do OpenStreetMap: User-Agent com o app e o repositório, no mínimo 7 dias em disco, revalidação com
    ETag/Last-Modified, só os tiles que aparecem na tela. Nominatim: no máximo 1 busca por segundo no app inteiro,
    com cache (achado 180 dias, não achado 1 dia). Os caches têm faxina (30 dias sem uso, teto de 300 MB para tiles
    e 200 MB para imagens, nunca um tile com menos de 7 dias).
- **Comandos em segundo plano e o Job Object.** Todo comando que o `rodar_comando` abre (em primeiro plano ou com
  `em_segundo_plano`) e todo shell de console (criado suspenso e depois solto) roda num Job Object do Windows com
  KILL_ON_JOB_CLOSE: se o servidor morrer à força, o Windows fecha o último handle e a árvore inteira morre, então
  nenhum servidor órfão sobra depois do Clave. A parada normal é com cuidado (`console.encerrar_job_com_cuidado`):
  morre o que não tem janela visível, programas com janela (com os ajudantes e os ancestrais vivos deles) ficam, e
  depois o KILL_ON_JOB_CLOSE sai. Vale ao fechar um console, ao parar um comando em segundo plano e no `atexit` do
  servidor; um comando em primeiro plano parado pelo Parar ou pelo tempo limite ainda mata o job inteiro. Um comando
  em primeiro plano cujo terminal saiu perde só os processos sem janela que ainda seguravam a saída (com aviso).
  Comandos em segundo plano: no máximo 5 por conversa (`MAX_SEGUNDO_PLANO`), voltam em poucos segundos com o id, a
  primeira saída e o endereço local, registrados em `tarefas`; o comando de uma etapa de fluxo é da conversa mãe
  (`tarefas.conversa_dona`); um processo que sobra depois de o terminal sair (um `Start-Process` escondido) mantém a
  tarefa rodando. Apagar uma conversa chama `tarefas.parar_da_conversa()` antes. O `BREAKAWAY_OK` só deixa sair
  processo que pede. **O fechamento com calma no Electron é obrigatório**: o `taskkill /T` sozinho percorre
  supervisor > servidor > PowerShell > a janela e mata as janelas antes de o servidor poder fazer qualquer coisa.
- **O console é ConPTY por ctypes**, sem pacote nativo (pywinpty e parecidos são binário nativo novo, que o Smart App
  Control pode barrar): `CreatePseudoConsole` mais `CreateProcessW` com `PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE`,
  PowerShell 7 quando o `pwsh.exe` está no PATH, senão o Windows PowerShell. Se o ConPTY falhar, entra um modo
  simples por pipes (sempre o Windows PowerShell, sem cores, setas, programas interativos nem Ctrl+C, na página de
  código OEM). O ambiente tira os `CLAVE_*` e o `PYTHONUTF8` que o Electron liga para o servidor (vale o da pessoa,
  se ela tiver um no Windows). Os comandos do `rodar_comando` mantêm `PYTHONUTF8=1` e `PYTHONIOENCODING=utf-8` de
  propósito: a saída deles é lida como UTF-8.
- **Sair da conta mantém os dados e tira as credenciais**: `segredos.apagar_tudo()`, `config.resetar()` (o idioma
  volta a seguir o Windows, então a apresentação e os tours aparecem), o cache de modelos da conta, as rotinas
  desligadas e fora do Agendador e os dados do navegador do Code (`navegador.limpar_dados()` numa thread: cookies,
  logins, armazenamento e cache também são credenciais; sem a ponte não há o que limpar). Conversas, projetos,
  memória e anexos ficam. O `resetar()` mantém o que não é preferência: `plugins` (zerar religaria um plugin de
  terceiro que a pessoa desligou), `ajudantes` (as conversas dos ajudantes das lições ficariam órfãs),
  `web_por_padrao_migrada` (a migração da 3.1.0 rodaria de novo e apagaria a escolha de Web de cada conversa) e
  `padrao_haiku_migrado` (a migração da 5.0 rodaria de novo).
- **Desinstalar nunca roda numa cópia de desenvolvimento, na demonstração nem fora do lançador**
  (`servidor/desinstalador.py` recusa `.git`, `DEMO` e a falta do `CLAVE_LANCADOR`; os testes sobem o servidor de
  verdade a partir da pasta do Clave, e é isso que impede a suíte de desinstalar uma instalação), só apaga uma pasta
  com `versao.json` e `servidor\servidor.py`, nunca a raiz de um disco nem uma pasta do usuário, e só tira atalhos que
  apontam para dentro dela. Duas armadilhas que a revisão achou e um teste cobre agora: **nada de
  `DETACHED_PROCESS`** (o PowerShell 5.1 lançado assim sai com código 0 sem rodar o script), e o script tem de ficar
  **fora da árvore de processos do servidor** (o Electron derruba a árvore com `taskkill /T` ao fechar): ele é
  lançado por um PowerShell curto com `Start-Process`, antes de o servidor responder, com os parâmetros num `.json`
  ao lado. Ele fecha os processos que moram na pasta e a janela do Edge do modo sem Electron (perfil em
  `dados\janela-edge`), nunca um editor que só está com a pasta aberta.
- **Toda release leva também o `clave.zip`** (o mesmo pacote, nome fixo, pasta `clave/`), então
  `releases/latest/download/clave.zip` é sempre a versão mais nova. O link curto `tinyurl.com/instalar-clave`
  aponta para lá; é ele que o dono do repositório manda no comando de instalação de uma linha do PowerShell. O
  botão Atualizar pega o primeiro `.zip` e acha a pasta do app pelo `versao.json`, então qualquer um dos dois serve.
- **O script de prints recarrega antes de fotografar um cartão que espera clique** (`testes/prints_demo.py`,
  `recarregar`): neste PC o antivírus segura a resposta em fluxo no Edge de teste até ela terminar, então o cartão
  que espera nunca chega ao vivo ali. O app e o navegador do Claude recebem na hora.
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
- **Comandos perigosos pedem OK** (`code.PERIGOSOS` = `APAGADORES` +
  `OUTROS_PERIGOSOS`: apagar, push, reset, publicar, deploy, registro), a não
  ser que uma regra allow específica para aquele comando exista. **O modo Livre
  só pergunta pelos `APAGADORES`** (apagar arquivo ou dado, `reset --hard`,
  `clean`, `gh repo delete`...); publicar, mexer fora da pasta, mandar e-mail
  (`_email`), escrever no GitHub e rodar fluxo passam sozinhos
  (`Execucao._livre`), e a ferramenta `apresentar_plano` nem é oferecida. No
  Livre continuam valendo: regra `deny` e `ask` escrita por quem usa, arquivo
  protegido (as ferramentas de arquivo negam sempre; comando que cita um deles
  pede OK) e o cartão de perguntas do modelo. O modelo fica sabendo do Livre
  pela nota escondida de `servidor._nota_de_modo` (o prompt de sistema é
  congelado). No modo Plano, escrita e comando são negados. Fora do Livre,
  "permitir nesta tarefa" só libera escrita e comando dentro da pasta: caminho
  de fora pede OK toda vez.
- **O atalho abre pelo `ferramentas/abrir.pyw`**, não direto no `electron.exe`:
  uma atualização pode trocar a versão do Electron (`versao.json`), e é o
  `abrir.pyw` que baixa a nova antes de abrir. O "reiniciar" da janela também
  passa por ele.
- **Excel com openpyxl**: ele escreve fórmula mas não calcula; recalcular é pelo
  Excel instalado (`excel.no_excel`). Ao salvar arquivo existente, imagens e
  formas podem se perder: a descrição da ferramenta manda salvar cópia.
- **Fluxo pede OK** (cartão `fluxo_proposta`) em qualquer modo e com qualquer
  regra, menos no Livre, onde roda direto com o teto de gasto sugerido; regra só
  consegue proibir (`deny` em `Fluxo`). Cada etapa é
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
- Cada parte da 5.0 tem o seu `testes/test_5_0_<parte>.py`: `base` (a migração do Haiku, os vídeos das lições
  baixando sozinhos, o gancho do `provedores.py`), `integracao` (rotas registradas, ferramentas oferecidas, o aviso
  do Haiku só para configuração já pronta), `arquivos` (Arquivos e Visualizador; as classes que dirigem um Edge
  headless ou rodam as funções puras no Node são puladas sem Edge ou Node, e o teste da Lixeira manda itens pequenos
  `clave-teste-*` para a Lixeira de verdade), `console` (shells ConPTY de verdade numa pasta temporária, janelas que
  sobrevivem ao fechar), `navegador` (regras, leitura de URL, decisão por modo, as ferramentas contra uma ponte de
  mentira), `tarefas` (o registro, comandos em segundo plano com processos de verdade, o Job Object, as rotas) e
  `widgets` (normalização, o proxy de imagem com DNS de mentira, tiles, exportação). Uma parte só:
  `-p "test_5_0_<parte>.py"`.
- Janela de verdade: `.venv\Scripts\python.exe testes\testar_janela.py` (abre e
  fecha uma janela; confere pela porta de depuração).
- Navegador de verdade: `.venv\Scripts\python.exe testes\testar_navegador.py [pasta-para-os-prints] [--en]` abre o
  Clave no Electron (demonstração, dados e perfil temporários, porta de depuração), serve uma página de teste local e
  fala com a ponte como o servidor fala: leitura, digitação, recusa de senha e cartão, clique preso à página e ao
  elemento, a vista dentro do painel, página em branco, apagar os dados, a ponte recusando token errado, `Origin` e
  `Host`. Uma janela aparece na tela por uns 30 s.
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
- A vista do navegador do Code é mais um alvo `page` do CDP, às vezes listado antes da página do app. Script que
  dirige o Electron pela porta de depuração escolhe o alvo na porta do servidor (do `dados/servidor.json`), como
  fazem o `testar_janela.py`, o `prints_janela.py` e o `testar_navegador.py`.
- Uma página abre no máximo 6 conexões por endereço. Só o console à vista mantém o SSE aberto; os outros alcançam
  pelo `desde` quando aparecem. Aba nova que recebe fluxo tem de fazer o mesmo, senão o `/eventos` da conversa e os
  pedidos do app travam.
- Esconder a vista do navegador movendo para fora da tela do mesmo tamanho, nunca com `setVisible(false)` (a página
  ficava em branco depois de redimensionar e a primeira captura falhava). Com a janela do Clave coberta ou
  minimizada, o Chromium para de pintar: o `navegador_print` cai no `Page.captureScreenshot` pelo debugger, e o
  `testar_navegador.py` deixa a janela dele por cima.
