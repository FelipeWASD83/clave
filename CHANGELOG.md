# What's new in Clave

**English** · [Português](CHANGELOG.pt-BR.md)

## 3.0.0 (2026-10-15)

Clave now speaks English, shows you around the first time, and presents every new Claude model.

**New**

- **English**, alongside Brazilian Portuguese: the whole interface, the lessons and the glossary, the folder
  template, the built-in plugins, agents and workflows, and what Clave tells Claude. A new install follows the
  Windows language (English when it isn't Portuguese); if you already used Clave, it stays in Portuguese. Switch
  in Settings > Appearance > Language.
- **Guided tours**: the first time you open Clave, arrows point to each part of the screen and explain it (16
  short steps you can skip). Code, Pricing & plans and Workflows have their own tour the first time you visit
  them. "Take the tours again" is in Learn.
- **New model card**: when Anthropic releases a model, a card opens once with its picture, what it is, what
  changed from the previous version, its price next to the other models and an intelligence score for all of
  them on the same scale (the Artificial Analysis index, with the source). A banner on the start screen stays for
  14 days, and the same card opens from the "Models" row in Pricing & plans.
- **Models** row in Pricing & plans, with a card and an illustration for each model.
- Clave warns you when your Anthropic account already has a model that Clave doesn't know yet (it checks once a
  day, for free) and offers to look for an update.

**Changed**

- The repository is in English, with Portuguese copies of the README, this changelog and the project notes.
- Workflow proposals, plans and suggestion cards are written in the language you use.

**Fixed**

- On the new conversation screen, when the banner and the panels made the page taller than the window, the text
  box ended up above the top of the window, where scrolling couldn't reach it.
- When suggesting another conversation, Claude sometimes repeated its whole answer after the card.

## 2.1.0 (2026-10-14)

**New**

- **Pricing & plans** page: the price of each model (and what a short, medium or long message costs), Claude's
  plans and the "API or subscription?" calculation. You tell it how you use regular Claude (how many 5-hour
  windows per week and how much of the limit you use, or how many messages per day) and it estimates the API
  cost for each model, compared with the price of the plan. When you already have replies in Clave, the
  calculation based on your real cost appears too.
- **Your usage** panel on the new conversation screen (chat and Code): total tokens, streak of days of use (and
  the record), heat map of the last 20 weeks, favorite model, each model over the last 7 days and the month's
  projection: at the pace of the last 14 days, how much the cycle will total and on which day the cap runs out.
  You can hide it in Settings > Appearance.
- **Environment** panel in Code, as in the official app: recent folders with the current one marked, "Choose
  environment" and "Turn on auto mode" (Auto mode). Code now starts in the last folder you used.
- **Suggesting another conversation**: when a separate job comes up, Claude can suggest opening another
  conversation. It becomes a card with the title and the request; "Open in another conversation" creates the
  conversation and Claude starts working on it right away, while you carry on in the current one. Nothing opens
  without your click.

**Changed**

- Code no longer has the separate "Which folder" screen: the choice now lives in the environments panel.

## 2.0.1 (2026-10-14)

**Fixed**

- If Windows won't let a folder be swapped during the update (for example, Clave's folder open in a terminal or
  held by the antivirus), going back to the previous version no longer leaves the app unable to open.

## 2.0.0 (2026-10-14)

Workflows with several models, permission rules, plugins, slash commands,
routines and a real Plan mode.

**New**

- Workflows: a big task becomes steps, each on the right model and agent
  (for example, Opus 5.5 plans, Sonnet 5.5 does the work and tests it, Haiku 5.5
  checks it). Before running, a card always appears with the steps, the cost
  estimate and a cap, and you can change the model and reasoning of each step or
  remove steps. Steps can run in parallel, and you can open each one and see what
  it is doing. Five ready-made workflows (Plan, do and test; Deep research;
  Parallel review; Large spreadsheet; Write and review), with a history of
  everything that ran.
- Agents: six ready-made (planner, executor, tester, reviewer, researcher and
  writer) and an editor to create your own, in the same format as Claude Code
  (`.claude/agents`).
- Permission rules, in the Claude Code format: Never, Always ask and Do without
  asking, for commands, files, sites, connectors, GitHub and workflows. They
  apply to all of Clave or to one folder (`.claude/settings.local.json`).
  The approval card gained "More options" to allow something for the rest of the
  task or to save the suggested rule. Permissions page with a test ("would this
  command pass?") and a history of every decision.
- Plugins in the Claude Code format, with skills, agents, commands and
  workflows. Seven ready-made (Office, Windows automation, Research, Writing,
  Sites and apps, Programming and Make your own) with 25 new skills. Installing
  from a folder or from GitHub (a single plugin or a marketplace), always
  showing the content first.
- Slash commands: `/novo`, `/modelo`, `/esforco`, `/plano`, `/custo`,
  `/fluxo`, `/memoria`, `/permissoes`, `/plugins`, `/ajuda`, the plugins'
  commands and your own (`.claude/commands`), and skills called by name.
- Plan mode with a plan card: you approve and choose how it executes (asking,
  accepting edits or auto) or ask it to keep planning.
- Routines: requests that Claude carries out on its own every day, on some days
  of the week or every few hours, with a cap per run. They run with Clave open or,
  if you want, through the Windows Task Scheduler with it closed. In a routine
  Claude asks nothing: whatever would need an OK makes the routine stop and tell
  you which rule was missing.
- Skills in chat too (the ones that aren't manual).
- Five new lessons (why use Clave, workflows and agents, permissions,
  routines, plugins and commands) and eight new glossary terms.
- In the README, the "Why you should use Clave" section.

**Changed**

- Windows notifications now come out through Clave's window, flash in the
  taskbar and also warn you when Claude is waiting for an OK, proposes a
  workflow, finishes a plan, or when a workflow or routine finishes.
- The Update button also updates the plugins, agents and workflows that ship
  with the app.

**Fixed**

- Long menus (like the commands one) no longer go off the screen: they open
  downward when they don't fit upward, and they scroll.

## 1.0.0 (2026-10-14)

First version.

**New**

- Chat with Claude through the Anthropic API, with your key: conversations,
  search, pin, rename, export to Markdown, edit a message and generate another
  reply with versions (< > arrows).
- Attachments: images, PDFs, Excel spreadsheets and text and code files; drag,
  paste or choose, and also from GitHub.
- Models Opus 5.5, Sonnet 5.5, Haiku 5.5 and Fable 5.1 (and the older ones, if
  you want), reasoning from Low to Max, visible reasoning, fast mode and a model
  switch when the safety filter refuses by mistake.
- Code mode: Claude works in a folder on the computer with permissions (Ask,
  Accept edits, Plan, Auto), approval cards with the before and after, a step
  list, undo, protected files, a cap per task, the folder's CLAUDE.md rules and
  skills (called with /name).
- Excel: read, create and edit spreadsheets with formulas, formatting, tables,
  charts, filters, conditional formatting and dropdown lists; recalculate,
  export PDF and convert .xls through the computer's Excel. In chat, the
  finished spreadsheet comes with download and open buttons.
- Projects with instructions and knowledge files.
- Personalization: about you, how to respond, ready-made and custom styles.
- Memory across conversations in files by topic, with an index, and a memory
  editor (Sonnet 5.5) that changes the memories however you ask.
- Monthly spending cap with alerts, the cost of each reply, a usage page by day,
  model and conversation, and a context gauge.
- GitHub (through the gh login or a token), web search and MCP connectors.
- Learn: 19 lessons and a glossary of more than 60 terms for people who have
  never used AI, focused on automation and personalization, and a helper
  (Haiku 5.5) that answers questions about each lesson. Claude points to the
  right lesson when you trip on a term, even if it is misspelled.
- Working folder template with rules, skills (watching videos, reviewing code,
  visuals for sites and others) and a library of visual references.
- Own window (Electron), installer with shortcuts and an Update button that
  downloads the new version from GitHub and goes back if it doesn't open.
- Light, dark or system theme, font size and typeface, conversation width and
  Windows notifications when Claude finishes.
