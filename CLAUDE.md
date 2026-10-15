# CLAUDE.md: Clave

A Windows app that uses Claude through the Anthropic API, with the user's own key.
Chat, Code mode (an agent working in a folder, with a side panel: files, viewer,
console, browser and background tasks), widgets, workflows with several models,
agents, permission rules, plugins, slash commands, routines, Excel, memory,
spending cap, GitHub, lessons for beginners and updating through GitHub. **Public
repository, used by other people**: nothing personal goes into the code, the
lessons or the folder template. The test that checks this reads the forbidden
terms from `testes/privacidade-local.txt`, which stays **outside git** (writing
the list in the test would publish what it protects); without the file, that
test is skipped. MIT license (`LICENSE`).

Current version: see `versao.json` (it also applies to `package.json` and the top
of `CHANGELOG.md`: the three move together).

**Languages.** The app is bilingual (Brazilian Portuguese and English): the
interface uses `t()` with Portuguese keys and English catalogs in `app/i18n/en/`
and `servidor/i18n/en/`. The code identifiers and comments are in Portuguese on
purpose (`precos.py`, `estatisticas.painel()`, `conversas.sistema`...) and are not
renamed. The documentation is in English, with Brazilian Portuguese copies named
`*.pt-BR.md` (`README.pt-BR.md`, `CHANGELOG.pt-BR.md`, `CLAUDE.pt-BR.md`,
`video/CLAUDE.pt-BR.md`). The English file is the reference: when you change it,
update the Portuguese copy in the same task.

## 1. How it runs

```
shortcut / Clave.bat ─► ferramentas/abrir.pyw (preparar.py: downloads the requested Electron version) ─► runtime/electron/electron.exe <folder>
                                                              │
electron/main.js ─► servidor/iniciar.py --sem-janela --pai <pid>   (supervisor: applies updates, restarts)
                        └─► servidor/servidor.py --porta 8040 --pai <pid>  (local HTTP + API + engine)
window ◄── http://127.0.0.1:8040/?t=<secret>  (becomes an HttpOnly cookie and disappears from the URL)
```

- **Without Electron** (download failed): `iniciar.py` alone opens the interface
  in an Edge app window (`--app=`) with its own profile in `dados/janela-edge`.
- **Local security**: 127.0.0.1 only; `Host` is checked; every `/api` route
  requires the session cookie (`dados/sessao.key`); a request that changes
  something with a different `Origin` is refused. This is what stops a web page
  from telling Code mode to run a command. **Do not loosen it.** `--sem-senha`
  exists only for tests and preview. The Code browser's bridge (`electron/main.js`)
  follows the same idea: 127.0.0.1 only, random port and token handed to the
  server in `CLAVE_PONTE_URL` and `CLAVE_PONTE_TOKEN`, and a request with an
  `Origin` header or a foreign `Host` is refused. Commands and consoles never
  inherit the `CLAVE_*` variables (the token included).
- **End of life**: closing the window (and the window's restart) first posts
  `/api/sair` with the session cookie and waits up to 3 s for the supervisor to
  exit (`pararServidorComCalma`). On that path the server's `atexit` closes the
  consoles and the background commands with care: programs with a window
  survive, orphaned and out of the reach of `/T`. Only after that, or when the
  request fails, Electron kills the supervisor's tree (`taskkill /T /F`). If the
  window dies abruptly, the server notices through `--pai` within 3 s and leaves
  with `os._exit` (no `atexit`: the Job Objects close and take everything,
  windows included); with no window for 10 min, it also shuts down
  (`--fechar-sem-janela`).
- **Data**: everything in `dados/` (outside git): `clave.db` (SQLite),
  `config.json`, `segredos.json` (key and tokens, protected with Windows DPAPI),
  `memoria/`, `anexos/`, `logs/`, `atualizacao/`, `plugins/` (installed),
  `fluxos/` (the user's templates), `servidor.json` (port of the running server,
  for `rodar_rotina.py`), `widgets/` (one JSON per widget tool call), `cache/`
  (map tiles, widget images, `geocode.json`), `tarefas/` (background task logs),
  `videos/` (lesson videos) and `ponte.json` (the bridge address and token, only
  with `CLAVE_TESTE_DEMO=1`, deleted on exit). The browser's cookies and storage
  live in Electron's profile (partition `persist:clave-navegador`), not in
  `dados/`. `CLAVE_DADOS` changes the folder (the tests use this).

## 2. Code map

| File | What it does |
|---|---|
| `servidor/servidor.py` | HTTP routes, static files, preview (`/previa/<id>` with a sandbox CSP), security, the start-up migrations; it imports `console`, `explorador`, `navegador`, `tarefas` and `widgets` so their routes exist from the start |
| `servidor/rotas.py` | The route registry (`@rota`, `Erro`, `ROTAS`) shared by `servidor.py` and the module of each part; a module registers its routes when it is imported |
| `servidor/execucao.py` | The engine of each reply: stream, tools, approvals, cost, undo, titles |
| `servidor/provedores.py` | Tools that live in their own module (`MODULOS`: `widgets`, `navegador`). Each module has `NOMES`, `oferecer()` (the definitions valid in this reply, or `[]`), `executar()` and optionally `definicoes_para_teste()`; `execucao.py` asks every module |
| `servidor/pedido.py` | Builds the request per model and turns off any optional feature the API refuses (`dados/compat.json`) |
| `servidor/modelos.py` | Catalog: prices (official page, 2026-10-14) and what each model accepts |
| `servidor/custo.py`, `orcamento.py` | Cost from `usage` and the monthly cap (cycle, alerts, blocking) |
| `servidor/sistema.py` | System prompts (chat, Code, lessons helper, memory editor) |
| `servidor/contexto_pasta.py` | The folder's CLAUDE.md/AGENTS.md from the folder upward, and skills (folder, personal, app) |
| `servidor/ferramentas/code.py` | Code mode tools, permission decision (`decidir`, with the rules), dangerous commands, background commands (`em_segundo_plano`, `ver_comando`, `parar_comando`), the Job Object of every command (`_Job`) and the command environment without `CLAVE_*` (`_ambiente_comando`) |
| `servidor/permissoes.py` | Rules in the Claude Code format: read and save (app in `cfg["permissoes"]`, folder in `.claude/settings*.json`), match command, path, domain and `Navegador(...)` (action, site and port, actions also in English), suggest a rule, filter server tools, and read hosts and URLs the way the browser does (`host_canonico`, `url_canonica`, `site_de`) |
| `servidor/fluxos.py` | Workflows: proposal (`normalizar`, estimate, cap), `Rodada` (steps as hidden conversations, in parallel groups, with a cost `Cofre`) and ready-made templates |
| `servidor/agentes.py`, `comandos.py`, `plugins.py` | Agents (`.claude/agents`), slash commands (`.claude/commands`, `$ARGUMENTS`) and plugins (`.claude-plugin/plugin.json`, install from a folder and from GitHub) |
| `servidor/precos.py` | Subscription plans, message profiles, cost of one message, the "API or subscription?" estimate and the cap projection |
| `servidor/estatisticas.py` | The "Your usage" panel: streak of days, heat map, favorite, last 7 days |
| `servidor/rotinas.py`, `rodar_rotina.py` | Routines: schedule, `Relogio` (inside the app, every 30 s), Task Scheduler (`schtasks`, `Clave` folder) and the windowless runner |
| `servidor/ferramentas/excel.py`, `planilhas.py` | Excel with openpyxl and through the installed Excel (PowerShell + COM) |
| `servidor/ferramentas/memoria.py` | The `memory_20250818` tool in `dados/memoria`, with a `MEMORY.md` index |
| `servidor/ferramentas/github.py`, `github_api.py` | GitHub REST (the `gh` token or a personal one) |
| `servidor/atualizador.py`, `iniciar.py` | Updating from the newest GitHub release, and the supervisor |
| `servidor/api_falsa.py` | A fake Claude API (demo and tests) |
| `servidor/i18n.py`, `servidor/i18n/en/*.json` | Server translation: `t("Portuguese text", name=value)`, `traduzir_ferramentas()` for tool descriptions, `guardado_pt()` for the Portuguese texts kept next to English packages |
| `servidor/compactar.py` | `/compact`: on-demand compaction (beta `compact-2026-09-04`); the block becomes a `compactacao` message and the request starts from it |
| `servidor/importar.py` | Import from Claude or ChatGPT: the request to paste there, reading the reply (sections and one entry per line) and applying it |
| `servidor/tom.py` | The way of talking (base tone and the Less, Default, More controls): the sentence for each choice in the system prompt and the example on Haiku |
| `servidor/conselheiro.py` | The model advisor: Haiku reads the chat at the 1st message and every 5 and recommends the cheapest model that does the task (`recomendar_modelo`, forced tool call) |
| `servidor/desinstalador.py` | Checks whether this folder may uninstall itself and launches `desinstalar.ps1` outside the server's process tree |
| `ferramentas/desinstalar.ps1` | Uninstall, run from `%TEMP%` after the app closes: shortcuts that point to this folder, `%APPDATA%\Clave` and the Clave folder, behind safety checks |
| `servidor/videos.py` | The lesson videos: the local file in the development copy (`video/saida/`), otherwise downloaded from the `videos` release into `dados/videos` (in the background by `baixar_todos()`, or on play), each download registered in Tasks and stoppable, served with Range |
| `servidor/console.py` | The Console tab: ConPTY through ctypes (a simple pipe mode when it fails), each shell in a Job Object, output kept in numbered chunks (the last ~2 MB) and read by SSE from `desde`, up to 6 consoles, routes `/api/consoles`, and `encerrar_job_com_cuidado()` (programs with a window survive), which `code.py` uses too |
| `servidor/explorador.py` | Files and Viewer routes (`/api/arquivos/*`): list, search, content with the encoding found, raw with Range and a sandbox CSP, spreadsheet, docx, Claude's changes from the checkpoints, create, rename, Recycle Bin (`SHFileOperationW`), open and reveal. Nothing leaves the root (`..`, a drive, an NTFS stream, a junction pointing out) and protected files need `forcar=1` |
| `servidor/navegador.py` | The Code browser: the `navegador_*` tools, the decision by rule, mode and site per task (`decidir`), the bridge client (`chamar`), the page text between random markers, the local server scan (netstat, tasklist and a quick GET) and `/api/navegador/estado`, `localhosts` and `limpar` |
| `servidor/tarefas.py` | The Tasks registry: `registrar()` for background commands and downloads (log, local URLs, stop), plus the replies, workflows and routines read from `execucao`; `parar_da_conversa()`, `conversa_dona()` and `/api/tarefas` |
| `servidor/widgets.py` | `mostrar_widget`: `normalizar()` for the 8 kinds, one JSON per tool call in `dados/widgets`, the image proxy `/api/widgets/imagem` (SSRF guard), `GET` and `PATCH /api/widgets/<tid>`, `texto_para_exportar()` (Markdown export), cache pruning and `demo()` for the fake API |
| `servidor/mapas.py` | Addresses to coordinates (Nominatim, 1 lookup per second app-wide, disk cache) and the OpenStreetMap tile proxy `/api/mapa/tile/<z>/<x>/<y>` (disk cache, at least 7 days, ETag/Last-Modified revalidation, pruning) |
| `servidor/ferramentas/email.py`, `word.py` | E-mail (IMAP and SMTP with an app password, or the classic Outlook by COM) and Word (.docx with the standard library, PDF through the installed Word) |
| `servidor/lancamentos.py`, `lancamentos.json` | Model launch cards: the presentation card (opens once for a new model), the "new model" banner, the "Models" cards, the intelligence score and its source (`_inteligencia`) and models the account has that Clave doesn't know yet (Models API, once a day) |
| `app/js/i18n.js`, `app/i18n/en/*.json` | Interface translation (`t()`); the server merges the catalogs into `/i18n/en.json` |
| `app/js/tour.js` | Guided tours with arrows (spotlight, bubble, Back/Next/Skip), a list per screen (Code shows `code`, then `mesa` for the panel), each shown once (`cfg.tours_vistos`) |
| `app/js/painel.js`, `abas.js` | The side panel: `registrarAba()`, `abrirPainel(id, args)`, `fecharPainel()`, `alternarAba()`, `ouvirPainel()`, the conversation's context (`definirContexto`), the width and the shortcuts (`atalhoDoPainel`). `abas.js` imports the tab modules |
| `app/js/arquivos.js`, `console.js`, `navegador.js`, `tarefas.js`, `previa.js` | The tabs: Files and Viewer (`abrirArquivo()`), Console (xterm.js), Browser (drives the Electron view through `window.clave.navegador`), Tasks (plus `contadorTarefas()` in the left bar and `observarTarefas()`) and Preview |
| `app/js/widgets.js` | Draws the 8 widget kinds (`renderizarWidget`, `widgetPorId`, `lembrarWidget`), Copy as text, PNG/SVG download and the map with Leaflet |
| `app/js/aviso-modelo.js` | The one-time notice "Haiku 5.5 is now the default" (`cfg.aviso_haiku`): Keep Haiku or Go back to the previous one |
| `app/vendor/xterm/`, `app/vendor/leaflet/` | xterm.js 6.0.0 with the fit addon 0.11.0 (ES modules, loaded the first time the Console opens) and Leaflet 1.9.4 (ES module build), each with its LICENSE |
| `app/js/lancamentos.js`, `app/img/modelos/` | Presentation card, new model banner and "Models" cards; Clave's own illustrations (`<family>.svg`) and renders (`render-<family>.jpg`, made by `ferramentas/gerar_renders.py`) per model family |
| `app/js/*.js` | Interface with no build step: `conversa.js` (screen and live reply), `markdown.js` (the replies; code blocks get Preview and, in Code, Run in console), `compositor.js` (text box and slash commands), `fluxo-ui.js` (approval cards, workflow, plan, suggesting another conversation, and notices), `painel-uso.js` (the start screen panels: usage and environments), `precos.js`, `fluxos.js`, `permissoes.js`, `plugins.js`, `rotinas.js`, `blocos.js`, `config.js`, `aprender.js`, `minichat.js`... |
| `agentes/`, `fluxos/`, `plugins/` | Agents, workflows and plugins that ship with the app (the updater replaces these folders) |
| `electron/` | Window, context menu, native folder picker, opening links outside, the graceful close (`pararServidorComCalma`) and the Code browser: a `WebContentsView` in the partition `persist:clave-navegador`, the HTTP bridge for the server, the scripts it injects in an isolated world, and `preload.js` (`window.clave.navegador`) for the tab |
| `tutoriais/*.md`, `tutoriais/en/*.md` | Lessons (header: titulo, trilha, ordem, duracao, resumo), same file names in both languages; `glossario.md` feeds the prompt. English glossary headings keep the Portuguese anchor: `## API key {#chave-da-api}` |
| `modelo-de-pasta/`, `modelo-de-pasta-en/` | The working folder template. In English the app copies the Portuguese one (prints, scripts) and lays the translated texts from `modelo-de-pasta-en/` over it; `READ-ME-FIRST.md` replaces `LEIA-PRIMEIRO.md` |
| `skills/ver-video/` | Skill that ships with the app (English `SKILL.md`, **identical** to `modelo-de-pasta-en/.claude/skills/ver-video/SKILL.md`; the scripts are identical to the Portuguese template's copy; a test checks) |

## 3. Decisions that are not undone without a reason

- **Language.** `cfg["idioma"]` is "pt-BR" or "en". A new install follows Windows (`config.detectar_idioma()`:
  UI language Portuguese → pt-BR, anything else or unreadable → English); a config written before the language
  existed stays in Portuguese. `CLAVE_IDIOMA` forces it (the tests use pt-BR). Changing it in Settings >
  Appearance reloads the window.
- **Translation keys are the Portuguese text.** UI: `t('...')` from `i18n.js`; server: `t("...")` from
  `i18n.py`; placeholders `{name}`. Never call `t()` at module top level (the catalog/language are read at call
  time): make display constants functions. Every literal key must exist in the catalogs and tool descriptions
  must be catalog keys (`testes/test_i18n.py` checks both). The server `t()` takes `lingua` as its 2nd argument,
  so never name a placeholder `{texto}` or `{lingua}`.
- **Built-in plugins, agents and workflows are English**, with the Portuguese names/descriptions kept beside
  them (`plugins/<p>/i18n/pt-BR.json`, `agentes/i18n/pt-BR.json`, `"i18n": {"pt-BR": ...}` inside
  `fluxos/*.json`); `i18n.guardado_pt()` and `fluxos._no_idioma()` apply them for Portuguese users. Ids (skill,
  agent and command names) stay as they are. Workflow steps are told which language to write in.
- **Tool field names are Portuguese** (`titulo`, `pedido`, `etapas`...) and they pull the model toward Portuguese:
  on Haiku 5.5, "write in the person's language" was not enough. The English system prompt says it outright
  ("write every value you put in tools ... in English"); keep it that way when adding a tool the person reads.
- **Model launch cards are facts with a source.** `servidor/lancamentos.json` only holds verifiable data
  (official prices, numbers with their origin). A new model: add it to `modelos.MODELOS` (price and what it
  accepts), add its card to `lancamentos.json` with `lancado_em` (the presentation card opens once and the banner
  shows for 14 days) and its `inteligencia` on the same index as the others, pick the family (or add an
  illustration and a render for a new one), and publish a release. Don't fill a card before the official
  announcement. The renders are Clave's own, generated by code: never Anthropic's images.

- **Web search is on by default** (3.1.0): `cfg["busca_web"]` starts True and the model decides when to search.
  `migrar_web_por_padrao()` (server start) switches it on once for existing users and removes the `busca_web` that
  old chat/Code conversations saved (it was the old default, not a choice). Without the option in a request, chat
  and Code follow the setting; workflow steps, routines and helpers always send their own. A `WebSearch` deny rule
  still wins.
- **Sending e-mail always asks.** `email_enviar` shows the whole e-mail and waits for an OK in any mode; only a
  specific allow rule `Email(enviar)` skips it, and a routine stops without it. Reading is free. Microsoft
  (Outlook.com, Microsoft 365) doesn't take passwords over IMAP anymore: the path is the classic Outlook (COM) or
  Zapier. The new Outlook has no COM.
- **Word without python-docx.** It needs lxml (native code that Smart App Control may block), so `word.py` reads
  and writes the .docx XML with the standard library. Text replacement works when the piece is inside one run.
- **`/compact` is on-demand compaction.** Once a conversation starts with the block, threshold compaction is not
  sent with it (the API rejects the pair), and `_para_api` cuts everything before the last `compactacao` message.
  Project files go into the first user message after the cut.
- **`mostrar_arquivo` copies the file** into `dados/anexos` (up to 100 MB, any type) and the result carries
  `(id ...)`, which the screen uses to draw the preview (as the generated spreadsheets do). Video and audio are
  served with Range.
- **The system prompt saves money** (`sistema._economia`): short answers when they fit, no rereading, a program
  without AI instead of a routine for repetitive work, cheaper models, and recommending free tools once.
- **The way of talking only adds, never changes.** Each choice other than Default becomes one sentence inside
  `<jeito_de_falar>`; everything on Default sends exactly the old prompt (a test checks it). What the person wrote in
  "How you want the answers" wins over the controls. There is no Professional or Efficient tone because the Formal
  and Concise styles already cover them.
- **`perguntar` and the plan outside Plan mode go through the approval path** (`_pedir_aprovacao`, decisions
  `responder`/`pular` and `pode_ir`/`mudar`/`nao_fazer`), so they wait, survive a reload (`aprovacoes_pendentes`)
  and never exist in routines or workflow steps. `apresentar_plano` is offered in every Code mode while
  `pedir_ok_plano` is on, with one description for all modes (the tool list does not change when the mode does).
  Haiku only presented the plan once the system prompt gave concrete criteria (3 files or more, moving, renaming
  or deleting, reorganizing a folder): keep them concrete.
- **The videos never ship inside the app.** Each MP4 is several MB and the Update button would download all of
  them on every version. They live in the `videos` release, created as a pre-release so `releases/latest` (the
  Update button) never picks it; re-rendered video: `gh release upload videos <file> --clobber`. Lessons point to
  them with `video: <id>` in the front matter (`<id>.<pt-BR|en>.mp4`), and the README links there too, with the
  covers from `video/capas/`. **Since 5.0 they download on their own**: `videos.baixar_todos()` runs in the background
  at server start and again when the language changes or `baixar_videos` is switched on, only for the app's language
  (about 28 MB for the 4 videos), one run per language, never in the demo. Each download is registered in Tasks and can be stopped there
  (the partial file is deleted; the automatic run doesn't restart a stopped video until the app restarts, the
  lesson's button does). A download that ends short of the `Content-Length` GitHub announced is an error, never a
  ready video. With `baixar_videos` off, the lesson downloads on play as before.
- **Haiku is the default model for everyone since 5.0** (4.3 made it the default only for new installs). The old
  config can't tell a model the person chose from the old default, so `migrar_haiku_padrao()` (server start, once,
  marked by `padrao_haiku_migrado`, which `resetar()` keeps) switches `modelo_chat` and `modelo_code` to Haiku when
  either was something else and, when the config was already set up (`configurado`), keeps the old pair in
  `aviso_haiku`. `aviso-modelo.js` shows the notice once (Keep Haiku, or Go back to the previous one, which restores
  the pair) and clears it; if the person already picked another model, it is dropped without showing. Chats and
  routines with their own model don't change; a new routine defaults to Haiku. The **model advisor** runs before the
  reply on the 1st user message and every 5 (`(n - 1) % 5 == 0`),
  only in chat and Code, never in routines, workflow steps, lesson helpers, a command or skill with a fixed model,
  "generate another answer" or a chat with `modelo_fixo`. It only suggests unless `trocar_modelo_sozinho` is on.
  The advice is saved in the user message `meta.conselho` (the screen redraws the chat when the reply ends, and the
  note with its buttons must survive); what the person decides goes to the chat `ajustes` (`conselho_visto`,
  `modelo`, `modelo_fixo`) through `PATCH ... ajustes_mesclar`. `r_enviar` saves the `ajustes` before starting the
  run, so the advisor's write is not lost. With `CLAVE_FORCAR_MODELO` (real-API tests) it reports the switch but the
  forced model keeps answering. Tested on real Haiku: keeps Haiku for simple questions, goes up for big tasks, goes
  down from Opus for a short translation, answers the reason in English when the app is in English.
- **Commands in two languages**: the Portuguese name (the file name) is the real one; `comandos.NOMES_EN` gives the
  English name of everything that ships with Clave (app commands, plugins, their commands and skills, ready-made
  workflows), each `:`-part translated. Resolution tries the exact typed name first, then `canonico()`, so a user's
  own skill named like an English alias still wins. A test fails when a shipped plugin, command, skill or workflow
  has no English name.
- **The side panel is a frame; the tabs register themselves.** `painel.js` knows no tab: each module calls
  `registrarAba({ id, titulo, icone, modos, atalho, tecla, botao, soDepoisDeAberta, montar })` when `abas.js`
  imports it, and the order comes from `ORDEM` in `painel.js`. `montar()` runs the first time the tab opens and
  returns hooks (`abrir`, `mostrar`, `esconder`, `contexto`, `redimensionar`). **Mounted tabs stay alive** when the
  panel closes or the screen changes: the console keeps its shells and output, the browser view its page. Tabs talk
  through contracts, not imports of each other: `clave:inserir-texto` (the message box), `clave:arquivos-mudaram`
  (the conversation fires it when a reply writes files, with an empty list after `rodar_comando`),
  `abrirArquivo(caminho, { linha })`, `abrirPainel('navegador', { url })` and `abrirPainel('console', { comando })`
  (types the command and never presses Enter; a multi-line block goes in with Shift+Enter between lines). On the
  server, each part registers its routes in its own module through `rotas.rota`, and `servidor.py` imports the
  modules at start (otherwise the routes only exist after the first reply, when `provedores.todos()` imports them).
- **The Code browser's rules** (`navegador.py` decides, `electron/main.js` holds the locks that need the page):
  - It only exists in the Electron window (the bridge variables; the Edge mode shows a notice), in its own
    partition, so its cookies and logins never mix with the app's session. Routines and workflow steps never get it.
  - Order: a `Navegador` deny or a domain-specific `WebFetch(domain:x)` deny (a generic WebFetch deny does not block
    it, or localhost dev servers would be blocked too), then Plan mode (no clicking or typing), then ask rules, then
    the **site per task**: outside Livre, the first action on a site that isn't local shows "Let Claude use the
    site X in this task?" (allow once, for this task, always in this folder, or always as `Navegador(site)`);
    localhost, 127.x and [::1] are free. Then **clicking and typing ask every time** outside Livre unless an allow
    rule names the action (`Navegador(clicar:x)`): a site-only allow frees the site, not the click. Why: the site
    gate closes "open the logged-in webmail, read it, carry it to another site", and a click can't be undone.
  - After every action, the site where the page ended (redirect, click, back) goes through the same rules: blocked
    turns the page blank (`em_branco`), a new site shows the site card before Claude sees anything.
  - An approved click or typing is pinned to the page (origin and path) and to the element (role and name); the
    bridge refuses with `pagina_mudou` or `elemento_mudou`, and without `esperado` it does nothing. The element
    numbers of a read live in the isolated world (`__claveRefs`), never in a DOM attribute a page's
    MutationObserver could move to another element.
  - The page text reaches Claude between markers with a random code per read (the page can't forge the end) and
    the title is labeled as page data. Passwords, access codes and card fields (by type, name, autocomplete and
    label) are refused by the bridge: the person types them.
  - Rule sites and page URLs go through the same reading as the browser's (`permissoes.host_canonico` and
    `url_canonica`: case, trailing dot, `%xx`, wide letters, IDNA, IPv4 in any form, user and password dropped) and
    the browser opens the rebuilt URL, so no parser difference escapes a rule.
  - No client certificate is ever sent (`select-client-certificate` with an empty callback; otherwise Electron hands
    the first Windows certificate to any site that asks). Sign out and Settings > Code mode > Delete the browser
    data clear the partition (bridge action `limpar`).
- **Widgets are saved per tool call** in `dados/widgets/<tool_use id>.json` (the checklist ticks go there too):
  reopening the chat reads them through `GET /api/widgets/<tid>`, and the Markdown export writes
  `widgets.texto_para_exportar()` in place of the call. `normalizar()` checks each kind and returns clear errors to
  Claude (links only https, colors only from the palette, a price read as a price), and `executar` checks again
  where the tool was offered (never routines, workflow steps or lesson helpers, nor with `widgets_ligados` off).
  - **Outside images only through `/api/widgets/imagem`**, an SSRF guard: https on the default port, no user in the
    URL, every resolved IP public (checked again on each redirect, at most 3, and the connection goes to the checked
    IP), up to 5 MB, only PNG, JPEG, WebP and GIF (never SVG), kept 7 days.
  - **Photos load only on click** by default (`widgets_imagens: "clicar"`): a page Claude read could plant an image
    URL that carries conversation data to a server, and the button names the sites before anything loads.
  - **Maps load without a click** because the tiles come through Clave's own proxy from one fixed host, following
    the OpenStreetMap tile policy: a User-Agent with the app and the repository, at least 7 days on disk, revalidation
    with ETag/Last-Modified, only the tiles on screen. Nominatim: at most 1 lookup per second app-wide, cached (found
    180 days, not found 1 day). The caches are pruned (30 days unused, caps of 300 MB for tiles and 200 MB for
    images, never a tile younger than 7 days).
- **Background commands and the Job Object.** Every command `rodar_comando` starts (in the foreground or with
  `em_segundo_plano`) and every console shell (created suspended, then resumed) runs in a Windows Job Object with
  KILL_ON_JOB_CLOSE: if the server dies abruptly, Windows closes the last handle and the whole tree dies, so no
  orphan server outlives Clave. A normal stop is done with care (`console.encerrar_job_com_cuidado`): what has no
  visible window dies, programs with a window (with their helpers and their living ancestors) stay, then
  KILL_ON_JOB_CLOSE is removed. It is used when a console closes, a background command stops and the server's
  `atexit` runs; a foreground command stopped by Stop or the time limit still kills its whole job. A foreground
  command whose terminal exited loses only the windowless processes still holding its output (with a note).
  Background commands: at most 5 per conversation (`MAX_SEGUNDO_PLANO`), back in a few seconds with the id, the first
  output and the local URL, registered in `tarefas`; a workflow step's command belongs to the parent conversation
  (`tarefas.conversa_dona`); a process left after the terminal exits (a hidden `Start-Process`) keeps the task
  running. Deleting a conversation calls `tarefas.parar_da_conversa()` first. `BREAKAWAY_OK` lets out only a process
  that asks for it. **The graceful close in Electron is required**: `taskkill /T` alone walks supervisor > server >
  PowerShell > the window and kills the windows before the server can do anything.
- **The console is ConPTY through ctypes**, with no native package (pywinpty and the like are a new native binary
  that Smart App Control may block): `CreatePseudoConsole` plus `CreateProcessW` with
  `PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE`, PowerShell 7 when `pwsh.exe` is on the PATH, otherwise Windows PowerShell.
  If ConPTY fails, a simple pipe mode takes over (always Windows PowerShell, no colors, arrows, interactive programs
  or Ctrl+C, OEM code page). The environment drops `CLAVE_*` and the `PYTHONUTF8` that Electron sets for the server
  (the person's own value, if set in Windows, is used). The commands of `rodar_comando` keep `PYTHONUTF8=1` and
  `PYTHONIOENCODING=utf-8` on purpose: their output is decoded as UTF-8.
- **Sign out keeps data and removes credentials**: `segredos.apagar_tudo()`, `config.resetar()` (the language
  follows Windows again, so the welcome flow and tours show up), the account's model cache, routines turned off
  and out of the Task Scheduler, and the Code browser's data (`navegador.limpar_dados()` in a thread: cookies,
  logins, storage and cache are credentials too; without the bridge there is nothing to clear). Conversations,
  projects, memory and attachments stay. `resetar()` keeps what is not a preference: `plugins` (resetting would turn
  a third-party plugin the person disabled back on), `ajudantes` (the lesson helper chats would be orphaned),
  `web_por_padrao_migrada` (the 3.1.0 migration would run again and wipe each chat's Web choice) and
  `padrao_haiku_migrado` (the 5.0 migration would run again).
- **Uninstall never runs on a development copy, in the demo or outside the launcher** (`servidor/desinstalador.py`
  refuses `.git`, `DEMO` and a missing `CLAVE_LANCADOR`; the tests start the real server from the Clave folder, so
  this is what keeps the test suite from uninstalling an install), only deletes a folder with `versao.json` and
  `servidor\servidor.py`, never a drive root or a user folder, and only removes shortcuts that point inside it. Two
  traps the review found and a test now covers: **no `DETACHED_PROCESS`** (Windows PowerShell 5.1 started that way
  exits 0 without running the script), and the script must be **outside the server's process tree** (Electron kills
  the tree with `taskkill /T` when it closes): it is started by a short-lived PowerShell running `Start-Process`,
  before the server answers, with its parameters in a `.json` next to it. It kills processes that live in the folder
  and the Edge window of the no-Electron mode (profile in `dados\janela-edge`), never an editor that just has the
  folder open.
- **Every release also carries `clave.zip`** (same package, fixed name, folder `clave/`), so
  `releases/latest/download/clave.zip` is always the newest version. The short link `tinyurl.com/instalar-clave`
  points there; it is what the repository owner sends in the one-line PowerShell install. The Update button takes
  the first `.zip` and finds the app folder by `versao.json`, so either package works for it.
- **The screenshot script reloads before photographing a card that waits for a click** (`testes/prints_demo.py`,
  `recarregar`): on this PC the antivirus holds the streamed reply in the test Edge until it ends, so a waiting
  card never arrives live there. The app and the in-app browser get it right away.
- **Official `anthropic` SDK at a pinned version** (`requirements.txt`). Windows
  Smart App Control can block a new version of a package with a native part
  (`pydantic_core`, `jiter`). Only update after testing the import on Windows.
- **No executable of our own.** Packaging Electron (electron-builder) produces a
  new `.exe`, unsigned and with no reputation, which Smart App Control blocks. So
  the official Electron is downloaded (`ferramentas/preparar.py`, checked against
  the release's `SHASUMS256.txt`) and runs the app folder.
- **System prompt frozen per conversation** (`conversas.sistema`). Changing the
  personalization applies to new conversations. This keeps the cache and the
  preserved thinking valid. For the same reason the history only grows: editing a
  message creates a new branch (a sibling), it does not rewrite.
- **`block_binding: drop_block`** on the current models with adaptive reasoning:
  if something changes the start of the conversation (a tool turned on midway, a
  model switch), the API discards the old reasoning instead of returning a 400
  error.
- **Optional features turn themselves off** when the API refuses them (fallbacks,
  updates, compaction, cache, eager streaming, new web, fast mode): see
  `pedido.desligar_por_erro`. Only Haiku 5.5 was really tested during
  development; the other models depend on this safety net.
- **Helpers** (`tutor` mode on Haiku 5.5, `memoria` mode on Sonnet 5.5) are
  conversations hidden from the list (`banco.listar_conversas` filters only chat
  and code) with a forced model (`execucao.AJUDANTES`).
- **Dangerous commands always ask for an OK**, even in Auto mode
  (`code.PERIGOSOS`: any delete, push, reset, publish, deploy, registry), unless
  a specific allow rule exists for that command. Protected files: the file tools
  always deny; a command that mentions one asks for an OK. In Plan mode, writes
  and commands are denied. "Allow for this task" only allows writes and commands
  inside the folder: a path outside asks every time.
- **The shortcut opens through `ferramentas/abrir.pyw`**, not straight into
  `electron.exe`: an update may change the Electron version (`versao.json`), and
  it is `abrir.pyw` that downloads the new one before opening. The window's
  "restart" also goes through it.
- **Excel with openpyxl**: it writes formulas but does not calculate them;
  recalculating is done by the installed Excel (`excel.no_excel`). When saving an
  existing file, images and shapes may be lost: the tool's description tells the
  model to save a copy.
- **A workflow always asks for an OK** (the `fluxo_proposta` card), in any mode
  and with any rule; a rule can only forbid (`deny` on `Fluxo`). Each step is a
  hidden conversation (`etapa` mode) run by a child `Execucao`: events go up to
  the parent as `etapa_evento`, the OK requests appear in the parent
  conversation, the cost goes to the parent conversation with origin `fluxo` and
  the `execucao_id` is the parent's (Undo covers the steps). The workflow's cap is
  a `Cofre` shared by all the steps.
- **Order of the rules**: deny, then ask, then allow, then the mode. A compound
  command (`&&`, `|`, `;`...) is split: allow must cover every part; deny and ask
  match any of them. A dangerous command only passes without asking with a
  specific allow (not a generic one such as `Bash(*)`). A server tool (web, MCP)
  has no way to ask: ask becomes deny there.
- **A routine never asks.** Whatever would ask for an OK makes the routine stop
  (`rotina_parou`) with the suggested rule. A routine does not run workflows.
- **Plugins**: hooks, local MCP and a plugin's LSP are ignored with a warning
  (running a program on its own is what we don't want from a downloaded package);
  a remote MCP becomes a connector suggestion. A plugin command loses the `Bash`
  from `allowed-tools`. Zip extraction checks for zip-slip and skips symbolic
  links.
- **SSE with padding**: the first thing in `/eventos` is a 4 KB comment and the
  headers `X-Accel-Buffering: no` and `Cache-Control: no-transform`. On this
  machine, headless Edge holds the SSE until it closes (probably the antivirus);
  Electron and curl receive it right away. To test the live screen, use
  `testes\prints_janela.py` (Electron), not headless Edge.
- **Suggesting another conversation never opens on its own.** The
  `sugerir_conversa` tool only shows a card; `POST /api/sugestoes/<id>/abrir` (the
  click) creates the conversation with the request recorded in the `tool_use`
  (not with what the screen sends), and the `sugestoes` table prevents opening it
  twice.
- **The subscription estimate is a declared floor.** Anthropic does not publish
  the subscriptions' limit in tokens; the calculation uses the only official
  number (at least 45 short messages per 5 h window on Pro, 5x and 20x on Max)
  and says so on the screen. The plan prices are editable because the Max 20x one
  only appears in third-party guides.
- **Lessons teach what the app really does.** Do not promise a feature that does
  not exist (e.g. the Word tools create .docx from simple Markdown and replace text; they don't do tracked
  changes or edit images).
- **The demo does not charge**: with `CLAVE_API_FALSA`, the recorded cost is zero.

## 4. Run, test, publish

- Demo: `.venv\Scripts\python.exe servidor\servidor.py --demo --sem-senha --porta 8041`
  (data in `%TEMP%\clave-demo`).
- Tests: `.venv\Scripts\python.exe -m unittest discover -s testes -t testes`
  (`test_servidor` starts the real server with the fake API; the fake API also
  proposes a workflow and a plan when the message asks for it).
- The 5.0 parts each have `testes/test_5_0_<part>.py`: `base` (the Haiku migration, the lesson videos downloading
  on their own, the `provedores.py` hook), `integracao` (routes registered, tools offered, the Haiku notice only for
  a config already set up), `arquivos` (Files and Viewer; the classes that drive a headless Edge or run the pure
  functions in Node are skipped without Edge or Node, and the Recycle Bin test sends small `clave-teste-*` items to
  the real Recycle Bin), `console` (real ConPTY shells in a temporary folder, windows that survive closing),
  `navegador` (rules, URL reading, decisions per mode, the tools against a fake bridge), `tarefas` (the registry,
  background commands with real processes, the Job Object, the routes) and `widgets` (normalization, the image proxy
  with fake DNS, tiles, export). One part: `-p "test_5_0_<part>.py"`.
- Real window: `.venv\Scripts\python.exe testes\testar_janela.py` (opens and
  closes a window; checks through the debugging port).
- Real browser: `.venv\Scripts\python.exe testes\testar_navegador.py [folder-for-screenshots] [--en]` opens Clave
  in Electron (demo, temporary data and profile, debugging port), serves a local test page and drives the bridge
  the way the server does: reading, typing, password and card refusal, clicks pinned to the page and the element,
  the view inside the panel, blank page, deleting the data, the bridge refusing a wrong token, `Origin` and `Host`.
  A window shows on screen for about 30 s.
- Screenshots of all screens: `testes\prints_demo.py <folder> --porta 8041 [--idioma en]`
  with the demo running (headless Edge). It also takes the tours (they open on their
  own the first time) in the chosen language.
- Screenshots of the live screen (workflow running, approval, plan):
  `testes\prints_janela.py <folder>` (opens Electron with the demo,
  `CLAVE_TESTE_DEMO=1`).
- Cheap real test: `CLAVE_FORCAR_MODELO=claude-haiku-5-5` forces every request
  (including the helpers) to Haiku 5.5.
- Icon: `ferramentas\gerar_icone.py` (generates `.png` and `.ico` from the SVG). Model renders:
  `python ferramentas\gerar_renders.py` (numpy and Pillow, outside the app's venv).
- **Publishing a version**: bump the version in `versao.json`, `package.json` and
  `CHANGELOG.md`, commit, push and run `ferramentas\publicar-versao.ps1`, which
  creates the `vX.Y.Z` release with the `.zip` package. The Update button of the
  other users downloads that release. **Publishing is the repository owner's
  decision.**

## 5. Pitfalls

- A `.ps1` with accented characters must be **UTF-8 with BOM** (PowerShell 5.1
  reads it without a BOM as ANSI).
- The `.venv` Python on Windows is a launcher that starts another process: to
  kill the server, kill the tree (`taskkill /T`).
- Editing a file that contains backslashes through a heredoc in Git Bash loses
  the backslashes: use the edit tool or a `.py` script written directly.
- To check the syntax of the interface's JavaScript, use
  `node --input-type=module --check < app/js/file.js`. Plain
  `node --check file.js` once let through an extra parenthesis that broke the
  whole screen.
- openpyxl formulas are in English (`SUM`, comma); Excel in Portuguese shows
  `SOMA`.
- The Code browser's view is another CDP `page` target, sometimes listed before the app page. Scripts that drive
  Electron through the debugging port pick the target at the server's port (from `dados/servidor.json`), as
  `testar_janela.py`, `prints_janela.py` and `testar_navegador.py` do.
- A page opens at most 6 connections per address. Only the visible console keeps its SSE open; the others catch up
  through `desde` when they show. A new tab that streams must do the same, or the conversation's `/eventos` and the
  app's requests stall.
- Hide the browser view by moving it off-screen at the same size, never with `setVisible(false)` (the page stayed
  blank after resizes and the first capture failed). With the Clave window covered or minimized, Chromium stops
  painting: `navegador_print` falls back to `Page.captureScreenshot` through the debugger, and
  `testar_navegador.py` keeps its window on top.
