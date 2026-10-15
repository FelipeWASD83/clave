---
titulo: Glossary: the hard words
trilha: 1. First steps
ordem: 7
duracao: reference
resumo: API, token, JSON, Git, GitHub, Python, Electron and more than 70 terms explained in plain language.
---

Words that show up in Clave, in the lessons and in Claude's answers, explained as simply as possible. You don't have to read it all: use it like a dictionary. If you're still confused, ask the helper at the bottom of the page.

## AI (artificial intelligence) {#ia}

A computer program that does things only people used to do, like understanding a text, writing, summarizing or recognizing what's in a photo. Claude is an AI. It doesn't "think" like a person: it learned patterns by reading an enormous amount of text and uses those patterns to answer.

## Model {#modelo}

It's the "version" of an AI. Anthropic has several Claude models: **Opus** (the smartest for everyday use), **Sonnet** (almost as good and cheaper), **Haiku** (fast and very cheap) and **Fable** (for very long reasoning). Choosing the model is like choosing between an expensive specialist and a quick assistant.

## Claude {#claude}

The AI from the company Anthropic. Clave is a way to talk to Claude from your computer.

## Anthropic {#anthropic}

The company that makes Claude. You pay Anthropic for what you use of the API. Clave isn't from Anthropic: it's an independent app that uses its API.

## Prompt {#prompt}

The request you write to the AI. "Summarize this text in 3 bullet points" is a prompt. The clearer the prompt (with context and the format you want), the better the answer.

## Token {#token}

The "little piece" of text the AI reads and writes. A short word is usually 1 token; a long word becomes 2 or 3. The API charges per token: both what you send and what Claude answers. A thousand tokens is about 700 words of English.

## Context window (context) {#janela-de-contexto}

Everything Claude can "keep in mind" at once: the whole conversation, the attached files and the instructions. Current models handle up to 1 million tokens. The gauge below the text box shows how much has been used. A very long conversation gets more expensive, because every answer rereads everything.

## Reasoning (thinking) {#raciocinio}

Before answering, Claude can "think" for a while: plan, check math, compare paths. This improves hard answers, but uses more tokens. In Clave you can see a summary of this reasoning.

## Effort {#esforco}

How much Claude thinks before answering: Low, Medium, High, Extra high or Max. High effort is better for hard problems and code; low effort is faster and cheaper for simple things.

## Hallucination {#alucinacao}

When the AI makes up information with total confidence, like a book that doesn't exist or a wrong number. It happens less with the newer models, but it happens. For anything important, ask for the source and double-check.

## API {#api}

Short for "application programming interface". It's a door that one program opens so other programs can talk to it. Anthropic's API is the door Clave uses to send your messages to Claude and get the answers back. Think of an order counter: Clave drops the order off at the counter (the API) and gets the finished answer back.

## API key {#chave-da-api}

A long password (it starts with `sk-ant-`) that tells Anthropic which account the payment comes out of. Whoever has your key spends your money, so never show it to anyone and never paste it into websites. In Clave it's stored only on your computer, encrypted.

## Credit (pay-as-you-go billing) {#credito}

The API has no monthly fee: you put credit (money) on your Anthropic account and each answer takes a little off, based on the number of tokens. People who subscribe to the Claude Max plan get a monthly API credit.

## Cache {#cache}

A fast memory that reuses the beginning of a conversation from one message to the next. The reused part costs much less (up to 20 times less). Clave turns this on by itself.

## Agent {#agente}

An AI that doesn't just answer, it **acts**: it uses tools, reads files, runs commands and works through a task in several steps until it's done. In Clave, Code mode turns Claude into an agent that works in a folder on your computer.

## Tool {#ferramenta}

An action the AI can ask the app to do for it, like "read this file", "search the web" or "create this spreadsheet". Claude asks, Clave carries it out (sometimes after your OK) and returns the result.

## Code mode {#modo-code}

The Clave mode in which Claude works in a folder on your computer: it reads and creates files, edits spreadsheets and runs commands to automate tasks. It asks for your OK before changing anything (you can adjust that).

## Skill {#skill}

A procedure saved in a text file (`SKILL.md`) that teaches Claude to do a task your way, step by step. Example: a "review code" skill or a "watch videos" skill. Claude uses a skill on its own when the task fits, or when you call it with `/skill-name`.

## CLAUDE.md {#claude-md}

A text file with the rules for a folder: who you are, how you like your answers, how your projects are organized. Claude reads it on its own when it works in that folder (in Code mode and in Claude Code). It's the strongest way to make Claude work your way.

## MCP (connector) {#mcp}

Short for Model Context Protocol, a standard for connecting AI to other services (documentation, systems, databases). An "MCP connector" gives Claude new tools from that service.

## Subagent {#subagente}

An agent that Claude calls to do part of the task, with its own instructions, model and tools. In Clave, agents live in **Workflows & agents** and carry out the steps of workflows (e.g. "planejador", the planner, on Opus and "executor" on Sonnet).

## Workflow {#fluxo}

A task split into steps, each done by a different model or agent: for example, Opus plans, Sonnet does and tests, Haiku checks. Since it spends more than a regular answer, Clave always shows the steps and the cost estimate and only runs after your OK.

## Plugin {#plugin}

A package that bundles skills, agents, commands and workflows for a kind of work (office, writing, programming...). Clave comes with a few and installs others from GitHub, in the same format as Claude Code plugins. You can turn each one on and off.

## Marketplace {#marketplace}

A list of plugins published in a GitHub repository (a `marketplace.json` file). When you install from a marketplace, you choose which plugins on the list you want.

## Slash command {#comando-de-barra}

A shortcut that starts with `/` in the message box, like `/novo` (starts a new chat), `/modelo haiku` (switches the model) or `/escrita:email` (a command from the writing plugin). Some belong to Clave itself, others are ready-made requests saved in a file (`.claude/commands`) or skills.

## Permission rule {#regra-de-permissao}

A line that says what Claude can do without asking, what it always asks about and what it never does, like `Bash(npm test *)` or `Edit(docs/**)`. It applies to one folder or to all of Clave, and it takes priority over the permission mode.

## Routine {#rotina}

A saved request that Claude carries out on its own at a set time (every day, on certain days of the week, or every few hours). In a routine it doesn't ask anything: it only does what your permission rules already allow.

## Task Scheduler {#agendador-de-tarefas}

A program built into Windows that runs things at a set time, even with no app open. Clave uses it when you ask for a routine to run with Clave closed.

## Markdown {#markdown}

A simple way to format text with symbols: `**bold**`, `# Title`, `- list item`. Claude writes in Markdown and Clave turns it into formatted text. `.md` files are Markdown text.

## File and folder {#arquivo-e-pasta}

A file is a document (photo, spreadsheet, text). A folder is a "drawer" that holds files and other folders. In Windows you see both in File Explorer.

## Path (file path) {#caminho}

A file's "address" on the computer, like `C:\Users\Ana\Documents\budget.xlsx`. Each part separated by `\` is one folder inside another.

## File extension {#extensao-de-arquivo}

The letters after the dot in a file's name, which say its type: `.xlsx` (Excel spreadsheet), `.pdf`, `.jpg` (photo), `.txt` (text), `.py` (Python program).

## Terminal {#terminal}

A window where you give orders to the computer by typing instead of clicking. It looks like hacker stuff, but it's just another way to tell the computer what to do.

## PowerShell {#powershell}

The Windows terminal. In Code mode, when Claude "runs a command", it uses PowerShell.

## Command {#comando}

An order typed in the terminal. For example, `mkdir Photos` creates a folder called Photos.

## Script {#script}

A file with a sequence of commands or instructions that the computer runs all at once. A script can, for example, rename 500 photos in seconds. Claude is great at writing scripts.

## Program (app) {#programa}

A set of instructions the computer runs to do something useful: Excel, the browser, Clave itself.

## Code {#codigo}

The text that tells the computer what to do, written in a programming language.

## Programming language {#linguagem-de-programacao}

A language the computer understands, with strict rules. Each one is good for something: **Python** for automation and data, **JavaScript** for websites, **C#** and **C++** for programs and games, **SQL** for databases. You don't need to know any of them to use Claude: it writes the code for you.

## Python {#python}

An easy-to-read programming language, widely used to automate tasks, work with spreadsheets and analyze data. Clave itself is built in Python under the hood.

## JavaScript {#javascript}

The language that makes websites interactive (buttons, animations, games in the browser). It has nothing to do with Java, despite the name.

## HTML {#html}

The language that says what is on a web page: headings, text, images, buttons. `.html` files open in the browser. Claude can create HTML pages and Clave shows a preview.

## CSS {#css}

The language that says how the page looks: colors, sizes, positions. HTML is the content; CSS is the appearance.

## JSON {#json}

A text format for storing organized data that both people and programs can read. For example: `{"name": "Ana", "age": 30}`. Many programs and APIs exchange information in JSON. (The name sounds like "Jason" when you say it out loud, which is why some people type it that way, but it has nothing to do with a person.)

## CSV {#csv}

A spreadsheet as plain text: each line is a row of the table and the columns are separated by commas or semicolons. Excel opens `.csv` files.

## Spreadsheet (.xlsx) {#planilha}

The Excel file, with tabs, cells, formulas and charts. Claude can read, create and edit spreadsheets in Clave.

## Formula {#formula}

A calculation inside an Excel cell that starts with `=`, like `=SUM(B2:B10)`. When the numbers change, the result changes on its own.

## Macro {#macro}

An automation recorded inside a spreadsheet (`.xlsm` files). Macros can be dangerous if they come from strangers, because they run actions on your computer.

## PDF {#pdf}

A document format that looks the same on any computer, good for sending and printing. Claude reads PDFs and Clave can export spreadsheets as PDF.

## Git {#git}

A program that keeps a project's history: every time you save a version (a "commit"), you can go back to it later. It's like Google Docs' "version history", but for whole folders.

## Repository {#repositorio}

A project folder controlled by Git, with its whole version history. It can stay only on your computer or also on GitHub.

## Commit {#commit}

A "snapshot" of the project at a moment in time, with a message saying what changed. "Committing" is saving that version into Git's history.

## Branch {#branch}

A parallel line of work in Git, for trying out changes without touching the main version. Afterwards, if it turned out well, you merge it back.

## GitHub {#github}

A website where people store Git repositories online: it works as a backup, for sharing projects and for working as a team. Git is the program; GitHub is the site that hosts it. Clave itself is updated from GitHub.

## Pull request (PR) {#pull-request}

A request, on GitHub, to merge the changes from a branch into the main version, with room to review and comment before that.

## Issue {#issue}

A "note about a problem or an idea" in a GitHub repository: a bug, a suggestion, a task.

## Clone {#clonar}

Downloading a copy of a GitHub repository to your computer, with its whole history.

## Electron {#electron}

A technology for making computer programs using the same languages as websites (HTML, CSS and JavaScript). The Claude app, Discord, VS Code and Clave itself use Electron: that's why they look like websites, but open in their own window.

## Node.js {#node-js}

A program that runs JavaScript outside the browser. It's the foundation of Electron and of many programming tools.

## npm {#npm}

Node.js's "store" of packages: a way to download ready-made libraries with one command (`npm install`).

## pip {#pip}

Python's "store" of packages (`pip install package-name`). Clave's installer uses pip to download what it needs.

## Library (package) {#biblioteca}

Ready-made code that someone else wrote and that a program uses so it doesn't have to reinvent the wheel. Clave uses a library to read spreadsheets, for example.

## Server {#servidor}

A program that sits waiting for requests and answers them. Anthropic's servers answer Clave; and Clave has a small server inside your own computer, which only it uses.

## Localhost {#localhost}

Your own computer's "address" (`127.0.0.1`). When something runs on localhost, only your computer can access it.

## Port {#porta}

A number that separates services within a single computer, like the apartments in a building. Clave uses port 8040 on your computer.

## Browser {#navegador}

The program that opens websites: Chrome, Edge, Brave, Firefox.

## Website and page {#site-e-pagina}

A page is a document on the internet (an HTML file). A website is a set of pages.

## Deploy (publish) {#deploy}

Putting a website or program "live" on an internet server so other people can access it.

## Bug {#bug}

An error in a program that makes it misbehave.

## Backup {#backup}

A safety copy of your files, kept somewhere else (external drive, cloud, GitHub), so you don't lose anything if the computer breaks.

## Encryption {#criptografia}

Scrambling information so that only someone with the right "key" can read it. The API key is stored encrypted on your computer.

## Access token {#token-de-acesso}

A special, long password that gives a program permission to use an account of yours (GitHub, for example). Like the API key: never share it.

## Open source {#codigo-aberto}

A program whose code anyone can read, and often use and modify, following a license.

## Version {#versao}

The number that says which "edition" of a program you have, like 1.4.2. A bigger number means newer. Clave's Update button downloads the newest version.

## Diff {#diff}

The comparison between the before and the after of a file: removed lines appear in red (with `-`) and new lines in green (with `+`). Code mode shows the diff of each change.

## Environment variable {#variavel-de-ambiente}

A setting the computer keeps "outside" the programs and which they can read. Sometimes it holds API keys; Clave deliberately doesn't use this, so the key stays better protected.

## Prompt injection {#prompt-injection}

A trick in which a text (from a website, email or file) carries hidden instructions for the AI, trying to make it obey someone else. That's why Clave asks for your OK before important actions: always check what you're approving.
