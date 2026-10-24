# What's new in Clave

**English** · [Português](CHANGELOG.pt-BR.md)

## 5.2.1 (2026-10-23)

**Fixed**

- **A conversation no longer gets stuck on an image saved with the wrong extension.** When Claude read a JPEG named
  `.png` (or the reverse), Clave told the API the wrong type, the API refused the whole request, and since the image
  stayed in the history the error came back on every message. Now the type is read from the image itself, both when
  Claude reads the file and when the history is sent, so conversations already stuck start working again. A file that
  only looks like an image (an SVG named `.png`, for example) is refused with a clear message instead of breaking the
  conversation.

## 5.2.0 (2026-10-23)

**Changed**

- **Auto mode no longer asks about anything except deleting.** Before, it still asked about publishing (`git push`,
  deploys, releases), sending e-mail, touching files outside the folder, writing to GitHub, and the workflow card.
  Now all of that happens on its own in Auto mode, and the workflow runs with the suggested spending cap. What still
  asks: a command that deletes files or data, a command that mentions a protected file, and the `Always ask` rules
  you wrote yourself. `Never` rules and the protected-files list keep working. Other modes are unchanged, and
  routines still never run in Auto mode. The tour, the settings texts and the lessons say the same now.

## 5.1.0 (2026-10-23)

**New**

- **You choose how many actions in a row Claude takes in Code mode.** Each action (reading a file, editing, running a
  command) is one round trip to the API, and after 60 in a row in the same message it used to pause and ask for
  "continue". Now the number is in Settings > Spending limit, from 10 to 1000 (the default is still 60). The pause
  notice says how many it took and where to raise it.

## 5.0.1 (2026-10-23)

**Fixed**

- **Long Code tasks no longer stop "out of nowhere".** When a reply stopped before the end (the per-task cap, too
  many rounds in a row, a reply that was too long, a full conversation or an error in the middle of the work), the
  notice showed for a moment and vanished as soon as the reply ended, and Windows still said Claude had finished.
  Now the reason stays written at the end of the reply, with a **Continue** button, and the Windows notification says
  why it stopped.

## 5.0.0 (2026-10-15)

Code mode becomes a workbench: your files, a real console, a browser you share with Claude and the work running in
the background, all beside the conversation. And in chat and in Code, Claude can draw the answer as a card.

**New**

- **Side panel in Code mode**, beside the conversation and as wide as you drag it, with the tabs **Files**,
  **Viewer**, **Console**, **Browser** and **Tasks**. Ctrl+J opens and closes it; Ctrl+Shift+E goes to Files, Ctrl+`
  to the Console, Ctrl+Shift+L to the Browser and Ctrl+Shift+Y to Tasks. A tab keeps working while the panel is
  closed (the console keeps what it ran), and Code mode reopens the panel the way you left it. A tour shows it the
  first time.
- **Files**: the working folder as a tree, with a filter and a search across every folder. Right-click to open in
  the Viewer, show in Explorer, copy the path, mention it in the conversation, rename (F2), create a file or a folder,
  or send it to the Recycle Bin (Delete). Drag a file to the message box to mention it. The files Claude changed in
  this conversation get a mark, and the tree updates on its own. Opening a program or a script with its default
  program asks first.
- **Viewer**: code with colors and line numbers (Ctrl+F, go to a line), Markdown with its images, pictures, PDF, Excel
  and CSV spreadsheets (a formula shows as a formula), Word (the text), formatted JSON, audio and video, and **View as
  a page** for HTML. **Claude's changes** shows what Claude changed in the file during this conversation. Protected
  files (like `.env`) only open after **Show anyway**. In Claude's replies, the path of each file step (read, write,
  edit, Word, Excel) opens the file here with one click.
- **Console**: a real PowerShell inside Clave, already in the working folder, with colors, history and interactive
  programs, up to 6 at once. **Send to Claude** puts the selected text (or the last lines) in the message box. In
  Code mode, the PowerShell and cmd code blocks in Claude's replies get **Run in console**: the command is typed in
  the console, and you check it and press Enter.
- **Browser**: a browser inside the Clave window that you and Claude use together. Claude opens pages, reads them,
  takes screenshots, scrolls and goes back, to check what it built or to use a page, and a strip shows when it is
  using the browser. **Local** lists the servers running on this computer (npm run dev, python -m http.server...)
  to open with one click.
- **The browser's safety rules**: its cookies and logins live apart from the rest of Clave. Outside Auto mode,
  Claude asks once per task before using each new site (localhost, your own computer, doesn't ask), and every click
  and every bit of typing asks for your OK unless a rule names that action (`Navegador(click:localhost)`); Plan mode
  only reads. Claude never types passwords, access codes or card numbers: you do. What a page says is treated as
  data, never as orders. A `WebFetch(domain:...)` block also blocks the browser on that site, and a page that jumps
  to a blocked site turns blank. Clave never hands a site a certificate from Windows (like a digital ID). **Sign out**
  deletes the browser's data, and Settings > Code mode has **Delete the browser data**. The new rules are
  `Navegador(site)` and `Navegador(action:site)`, with a port if you want one (`Navegador(localhost:5173)`), and the
  actions can be written in English or Portuguese.
- **Background commands**: Claude can leave a local server or a file watcher running (npm run dev, python -m
  http.server) and keep working: it reads the output when it needs to and stops it when it's done, at most 5 per
  conversation. They show up in Tasks with the local address, which opens in the browser with one click, and they
  stop when you press Stop, when you delete the conversation and when Clave closes. A program with a window that they
  opened (the browser of a dev server, an editor) stays open, and the same goes for programs opened from the console.
- **Tasks** (Ctrl+Shift+Y), in chat and in Code: everything running in the background (replies still arriving,
  workflows with their steps, routines, background commands and lesson video downloads), with the time, the log,
  **Stop** and **Go to the conversation**. Finished ones stay for 30 minutes. The left bar shows "N running", and a
  long task that ends shows a notice (and a Windows notification when Clave is in the background).
- **Widgets**, in chat and in Code: when a card helps more than text, Claude draws it in the conversation. Eight
  kinds: products and prices (sorted by price, with the cheapest marked and the date they were seen), a map with
  points and a route, recommendations (series, movies, games, books, music...), drawings and floor plans with
  measurements, charts (bars, lines, pie, area), comparisons, timelines and checklists you can tick. Each one has
  full screen and **Copy as text**, and drawings and charts download as PNG or SVG. They come back when you reopen
  the conversation and go into the Markdown export. Settings > Features turns them off.
- **Photos only on click**: product photos and covers come from other sites, so they only load when you click **Show
  images** (the button names the sites), because a page could use the address of a photo to carry data out of the
  conversation. Settings > Features changes that. Images go through Clave: only public https addresses, up to 5 MB,
  never SVG. **Maps** load right away: they come from OpenStreetMap through Clave itself, following its usage rules
  (each piece of map is kept for at least 7 days, and addresses are looked up at most once a second), and Clave says
  where each address landed and which ones were left out.
- **23 new lessons**, in five new tracks: **Saving credit** (where your credit goes, the right model for the lowest
  price, reasoning, lean conversations, Code mode without waste, automating without paying the AI every time,
  tracking and capping your spending), **The Code workspace** (the panel, the console, the browser, background tasks
  and local servers, a website from scratch to the browser), **Visual answers** (widgets, comparing products and
  prices, maps and itineraries, floor plans, drawings and charts), **Using it safely** (when a page or a file tries
  to give Claude orders, what never to paste, undo, backup and Git) and **Recipes by area** (studying, office work, a
  small business, home). The glossary got the new words (widget, console, background, local server, Recycle Bin...).

**Changed**

- **Haiku 5.5 is the default for everyone**, existing installs too: new chats start on the cheapest model. Once,
  after the update, Clave shows the model you used before, with **Keep Haiku** and **Go back to the previous one**.
  Existing chats keep their model, and the model advisor still suggests a stronger one when the task needs it. New
  routines also start on Haiku.
- **Lesson videos download on their own**, in the background and only in the app's language (about 28 MB), so a
  lesson opens with the video ready and plays it from your computer. They are still not part of Clave's download. The
  download shows in Tasks and can be stopped there; Settings > Updates & about turns it off (then the lesson
  downloads the video when you press play).
- **The HTML and SVG preview** is now the **Preview** tab of the side panel.
- **Deleting a conversation** stops what runs for it (the reply still arriving, its workflows and its background
  commands) instead of asking you to stop the reply first.
- **Closing Clave** first asks its server to finish on its own (for up to 3 seconds), so programs with a window that
  the console or a background command opened stay open.
- **Smoother interface**: windows, menus and notices leave with a short animation instead of vanishing, buttons give
  under the click, the left bar slides open and closed, long scrolls glide, and the conversation's top bar tightens
  in a narrow window instead of overflowing. With Windows animations turned off, everything stays still.
- **On a very wide monitor** (ultrawide), the side panel starts wider (up to 1200 px), widget cards get room beyond
  the text column, and Learn, Projects, Workflows, Plugins and Routines show more cards per row. At 1440 px nothing
  changes.
- **On the browser's site card**, **Allow** already allows the site until the task ends, as the question says:
  reading the page right after opening it doesn't ask again.

**Fixed**

- A command that left a hidden process behind still holding its output (a local server started from inside the
  command) kept it running after the reply, with nothing to stop it. Clave now closes it, says so in the result and
  points Claude to the background option. A window that the command opened (Notepad, an editor) stays open.
- A lesson video whose download was cut in the middle could be kept as if it were complete; now it is an error with
  **Try again**, and any other network failure shows a readable message.
- Settings > Data & backup now says what the backup really carries: the routines go with it; memory, attachments and
  the key don't.
- The sales plugin's "automation without AI" skill counted a routine checking every 15 minutes, but routines run at
  most once an hour; the comparison now uses that.
- Reopening a conversation that was still replying or waiting for your OK showed the reply's text twice.
- On the first start, the tour and the new model card opened on top of each other. Now the tour comes first and the
  card shows when it closes, and a tour never opens over a window.
- In a narrow window, the Learn page, a lesson and Settings had no button to open the left bar, and a dark strip
  showed on the window's left edge. The send button dropped alone to a second line.
- Settings: the descriptions of **Sign out** and **Uninstall** were cut with "...", buttons that lead to another
  page were underlined, **Open permission rules** stretched across the whole column, the protected files box cut
  its last line in half and number fields took the full width.
- In the dark theme, the logo in the left bar sat inside a lighter square, and the new model card had a block that
  was too bright.

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
