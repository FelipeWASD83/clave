# What's new in Clave

**English** · [Português](CHANGELOG.pt-BR.md)

## 4.3.0 (2026-10-15)

**New**

- **Haiku is the default model** on new installs: the cheapest one. If you already use Clave, your model stays.
- **Model advisor**: at the first message of each chat and then every 5, Haiku reads the chat and says which model
  does the task for the lowest price ("For this task, Sonnet 5.5 should do better", with Use and Keep). If you
  allow it (Settings > Models), Clave switches on its own and shows a button to go back; in a chat where you go
  back, it stops switching. Each check costs a fraction of a cent, and it can be turned off.
- **Commands in English and Portuguese**: every command, skill and workflow that comes with Clave works with both
  names (/summary or /resumo, /sales:proposal or /vendas:proposta, /workflow deep-research), and the menu, the help
  and the Plugins and Workflows pages show the one in your language. A command or skill of your own with the same
  name as a translation stays yours.
- **Sign out** (Settings > Updates & about): deletes the API key and the saved passwords, sets the settings back to
  default, turns routines off and shows the welcome screens and the tours again. Conversations, projects, memory and
  installed plugins stay.
- **Uninstall** (same place): closes Clave and removes its folder, the shortcuts and the routines' tasks in the
  Task Scheduler, with a link to download the backup first.
- **Videos in the lessons**, in Portuguese and in English: why use Clave, how to get the API key, first steps and
  the first automation in Code mode. They are not inside the app: the lesson downloads the video from GitHub the
  first time you press play (a few MB) and keeps it on the computer.

**Fixed**

- The welcome window showed the word "null" under the API key field when no key was saved.
- The approval card's title now says what Claude is asking to do ("Write", "Run this command", "Send an e-mail to")
  instead of describing it as already done.
- The lessons "Your first automation" and "How Code mode works" promised too much from **Undo changes**: it brings back the
  files Claude wrote or edited, not what a command did (like moving files). They now say so, and the first lesson
  uses the folder button's real name (**Choose the working folder**).

## 4.2.0 (2026-10-15)

**New**

- **Claude asks with a card**: when it is stuck on a decision that is yours, Claude shows a card with up to 4
  questions and options to click (one or several, plus a field for another answer), and goes on from your
  answer. "Skip" lets it go on with the option it would recommend. It works in chat and in Code; routines don't
  ask, since nobody is there to answer.
- **"Can I do it like this?"**: in Code, in any mode, before a big task (several files, moving or renaming files,
  something hard to undo) Claude shows the plan and waits for "Go ahead", "Change the plan" or "Don't do it".
  Plan mode stays as it was. It can be turned off in Settings > Code mode.

**Fixed**

- When you reopened a chat that was waiting for your decision on a plan, the plan showed up twice.

## 4.1.0 (2026-10-15)

**New**

- **Way of talking** (Settings > Personalization), like ChatGPT's tone controls: base style and tone (Friendly,
  Candid, Playful, Nerdy or Skeptical), warmth, enthusiasm, emoji, headers and lists, bold and tables, simple or
  technical language, whether Claude asks first or assumes when something is missing, and whether it ends with a
  "want me to...?". Everything on Default changes nothing. It applies to new chats, in chat and in Code.
- **See an example**: Haiku answers a question with the tone you picked, so you can feel the difference before using
  it (it costs a fraction of a cent).

**Fixed**

- The icon at the end of Pricing & plans showed up giant; it's back to text size.

## 4.0.0 (2026-10-15)

Clave for the office: e-mail, Word, Zapier, bringing everything from Claude or ChatGPT, and a Claude that saves your
money.

**New**

- **E-mail connector** (Settings > Connectors): Gmail, Yahoo, Zoho and hosting providers with an app password, or
  the classic Outlook installed on the computer (for Outlook.com and Microsoft 365). Claude reads and searches your
  e-mail and writes replies; sending always shows you the whole e-mail and waits for your OK. In Code mode it also
  saves attachments to the folder.
- **Word**: in Code mode Claude creates documents (proposals, contracts, letters) with headings and tables, fills
  in templates and exports to PDF with the installed Word.
- **Zapier shortcut**: a guided way to connect Gmail, Google Sheets and Calendar, Outlook, WhatsApp Business and
  hundreds of apps.
- **Import from Claude or ChatGPT** (Settings > Import from Claude): copy a request, paste it into the other
  assistant and paste the answer back. Your rules, who you are, projects, preferences and automations come in, with
  a preview to uncheck what you don't want. Routines come in off and on Haiku, for you to check.
- **Files in the chat**: when Claude takes a screenshot, makes a chart or finds a file you need to see, it shows it
  right in the chat (images, video and audio play there; other files get a card to open or download).
- **/compact** summarizes the chat on the spot so the next messages cost less, and the summary appears in the chat.
- More commands: **/web on|off**, **/resumo**, **/exportar**, **/economia** (tips to spend less) and **/importar**.
- **Sales plugin**: commercial proposal, client follow-up, orders into a spreadsheet, sales report, answering
  clients, and "automation without AI".
- New lesson: **An order app without AI**, step by step: e-mail, Excel spreadsheet and sending orders to the
  company website, scheduled by Windows, at zero cost per run.

**Changed**

- **Claude saves your credit on its own**: answers at the size the question needs, doesn't reread what it already
  read, and before turning something repetitive into a routine it explains that a program without AI, built once in
  Code, costs nothing per run. It also suggests Haiku for simple things, /compact for long chats, and free tools like
  Git, GitHub, Obsidian and Power Automate when they fit.
- The Routines page asks "does it need AI every time?" and opens Code ready to build the program without AI.
- Plugin commands and skills, written in English, now tell Claude which language to answer in.
- `excel_alterar` can save to a copy (the `saida` field), as the Excel skill already asked for.

**Fixed**

- The step list in Code no longer looks like it's still working after the reply ends: the step stops spinning and
  the list says which steps were left open.

## 3.1.0 (2026-10-15)

**Changed**

- **Web search comes on**: Claude searches the internet on its own when the answer needs something current
  (news, prices, versions), and shows the sources. You don't need to turn anything on. The **Web** button in the
  text box now turns it off just for that chat, and Settings > Features turns it off everywhere. Each search costs
  $0.01 on top of the tokens. If you already used Clave, it's switched on for you once, including in your old
  chats.

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
