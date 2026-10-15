# CLAUDE.md: Clave

A Windows app that uses Claude through the Anthropic API, with the user's own key.
Chat, Code mode (an agent working in a folder), workflows with several models,
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
  exists only for tests and preview.
- **End of life**: closing the window kills the supervisor's tree (`taskkill /T`).
  If the window dies abruptly, the server notices through `--pai` within 3 s and
  shuts down; with no window for 10 min, it also shuts down
  (`--fechar-sem-janela`).
- **Data**: everything in `dados/` (outside git): `clave.db` (SQLite),
  `config.json`, `segredos.json` (key and tokens, protected with Windows DPAPI),
  `memoria/`, `anexos/`, `logs/`, `atualizacao/`, `plugins/` (installed),
  `fluxos/` (the user's templates), `servidor.json` (port of the running server,
  for `rodar_rotina.py`). `CLAVE_DADOS` changes the folder (the tests use this).

## 2. Code map

| File | What it does |
|---|---|
| `servidor/servidor.py` | HTTP routes, static files, preview (`/previa/<id>` with a sandbox CSP), security |
| `servidor/execucao.py` | The engine of each reply: stream, tools, approvals, cost, undo, titles |
| `servidor/pedido.py` | Builds the request per model and turns off any optional feature the API refuses (`dados/compat.json`) |
| `servidor/modelos.py` | Catalog: prices (official page, 2026-10-14) and what each model accepts |
| `servidor/custo.py`, `orcamento.py` | Cost from `usage` and the monthly cap (cycle, alerts, blocking) |
| `servidor/sistema.py` | System prompts (chat, Code, lessons helper, memory editor) |
| `servidor/contexto_pasta.py` | The folder's CLAUDE.md/AGENTS.md from the folder upward, and skills (folder, personal, app) |
| `servidor/ferramentas/code.py` | Code mode tools, permission decision (`decidir`, with the rules) and dangerous commands |
| `servidor/permissoes.py` | Rules in the Claude Code format: read and save (app in `cfg["permissoes"]`, folder in `.claude/settings*.json`), match command, path and domain, suggest a rule, filter server tools |
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
| `servidor/ferramentas/email.py`, `word.py` | E-mail (IMAP and SMTP with an app password, or the classic Outlook by COM) and Word (.docx with the standard library, PDF through the installed Word) |
| `servidor/lancamentos.py`, `lancamentos.json` | Model launch cards: the presentation card (opens once for a new model), the "new model" banner, the "Models" cards, the intelligence score and its source (`_inteligencia`) and models the account has that Clave doesn't know yet (Models API, once a day) |
| `app/js/i18n.js`, `app/i18n/en/*.json` | Interface translation (`t()`); the server merges the catalogs into `/i18n/en.json` |
| `app/js/tour.js` | Guided tours with arrows (spotlight, bubble, Back/Next/Skip), one per screen, shown once (`cfg.tours_vistos`) |
| `app/js/lancamentos.js`, `app/img/modelos/` | Presentation card, new model banner and "Models" cards; Clave's own illustrations (`<family>.svg`) and renders (`render-<family>.jpg`, made by `ferramentas/gerar_renders.py`) per model family |
| `app/js/*.js` | Interface with no build step: `conversa.js` (screen and live reply), `compositor.js` (text box and slash commands), `fluxo-ui.js` (approval cards, workflow, plan, suggesting another conversation, and notices), `painel-uso.js` (the start screen panels: usage and environments), `precos.js`, `fluxos.js`, `permissoes.js`, `plugins.js`, `rotinas.js`, `blocos.js`, `config.js`, `aprender.js`, `minichat.js`... |
| `agentes/`, `fluxos/`, `plugins/` | Agents, workflows and plugins that ship with the app (the updater replaces these folders) |
| `electron/` | Window, context menu, native folder picker, opening links outside |
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
- Real window: `.venv\Scripts\python.exe testes\testar_janela.py` (opens and
  closes a window; checks through the debugging port).
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
