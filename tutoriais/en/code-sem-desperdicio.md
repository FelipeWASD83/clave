---
titulo: Code mode without waste
trilha: 5. Saving credit
ordem: 44
duracao: 7 min
resumo: Why a task in Code costs more than a question, and the habits that cut steps, rereading and waiting.
---

In [Code mode](#/aprender/modo-code) Claude works in steps: it looks at the folder, reads a file, runs a command, edits another one. It's the most useful mode and also the one that spends the most per task. The good news is that almost all the waste comes from a few habits that are easy to change.

## How a task in Code spends

- **Each step is a new request to the API**, which rereads the whole task so far (at the cache price, if there was no break). A 20-step task is 20 requests. On the **Usage & spend** page, the **Requests** column counts each one of them.
- **The conversation already starts big**: the Code mode instructions, the folder's rules (CLAUDE.md) and the description of the tools add up to more than 10,000 tokens before your request (an estimate).
- **What each step brings goes into the conversation**: the contents of a file it read, or the output of a command, are reread in every step after that.
- **Reasoning in Code starts on High.**

An estimate for a task where each step brings in about 1,500 new tokens and writes about 1,000 (with the reasoning):

| Model | 20-step task | 40-step task |
|---|---|---|
| **Haiku 5.5** | $0.02 | $0.05 |
| **Sonnet 5.5** | $0.36 | $0.75 |
| **Opus 5.5** | $0.73 | $1.51 |

In other words: what saves the most in Code is **having fewer steps** and **using the right model**.

## Do this instead of that

| Instead of | Do |
|---|---|
| "Find where the sales spreadsheet is" | "Read sales.xlsx, in the Reports folder" |
| Asking for the whole task at once | Asking for the plan first (**Plan** mode, or the **Can I do it like this?** card) and fixing the plan, which costs one message |
| "Rename the 300 photos" | "Rename 3 so I can check; then do the rest" |
| "Open the report and show it to me" | Opening it yourself in the Code panel, which costs nothing |
| Asking Claude to run a command just to see the result | Running it yourself in the **Console** |
| A command that dumps thousands of lines | "Show only the errors" or "only the last 20 lines" |
| Leaving the permission card waiting while you do something else | Answering right away, or allowing it with **Allow for this task** |
| Opus on High to move and rename files | Haiku on Medium or Low |
| Asking for the same task every week | Asking once for a program that runs without AI ([see how](#/aprender/automatizar-sem-ia)) |

## Look for yourself: the Code panel

Next to the chat, the Code panel (**Ctrl + J** opens and closes it) has:

- **Files**: the whole folder. Open any file in the **Viewer** to read it, instead of asking Claude.
- **Console**: the real PowerShell, already in the folder. The **Send to Claude** button takes the output to the chat; only from that point does it turn into tokens.
- **Tasks**: what's running in the background, with the **Stop** button.

Everything you do in the panel, without asking Claude, costs zero tokens. A server Claude left running in the background doesn't spend anything on its own either: it only costs when Claude reads what it wrote.

The panel's **Browser** is different: every page Claude opens and reads, and every screenshot it takes, goes into the conversation as tokens. Give it the right address instead of asking it to search, and ask for a screenshot only when the look matters.

## Answer the cards right away

The cache keeps the task for 5 minutes. If a permission card sits waiting for 10 minutes while you do something else, the next step pays for the whole task again. In a 40,000-token task on Sonnet, that step costs about $0.11 instead of about $0.02 (an estimate).

- Repeated, safe actions in the same task: on the card, **More options > Allow for this task** (it lasts until that answer ends).
- Actions that are always safe in that folder: a [permission rule](#/aprender/permissoes).
- Had to step away in the middle? That's fine: each long wait costs one reread, once. What adds up is a task that stops at several cards and waits at every one of them.

## The model and the reasoning in Code

- Code also starts on **Haiku 5.5**, and the model advisor works here too.
- Mechanical work (organizing, renaming, merging files, a simple spreadsheet): Haiku, with reasoning on Medium or Low.
- Medium-sized code, a big document, or when Haiku got lost: Sonnet.
- Big code, with many files, or something hard to undo: Opus.
- Choose at the start of the task: switching in the middle makes the next step reread everything without the cache discount.

## Short folder rules

The folder's CLAUDE.md goes in at the start of every Code conversation and travels along with every step. Write **rules**, not manuals: "use dates in the 2026-10-15 format", "never touch the Originals folder". A big reference document belongs in a separate file, with one line in CLAUDE.md saying when to read it ("for pricing questions, read docs/prices.md"): that way it's only read when needed. Skills work the same way: only the description always goes along; the whole procedure only comes in when it's used. See [CLAUDE.md and skills](#/aprender/claude-md-e-skills).

## One job per conversation

- A tweak to the same task, right after: keep going in the same chat (the cache is valid and it already knows the files).
- A new, unrelated task: **New Code task**. The new chat starts out light, without carrying the files and outputs of the previous task.

## The per-task cap

In **Settings > Spending limit**, the **Per-task cap in Code mode** (default $2) pauses a task that has spent that much. A notice shows up, and you send "continue" to keep going. Before you send it, take a look at the last steps: if it's repeating the same thing without getting anywhere, it's better to stop and explain it differently than to pay for more rounds.

## A big task: a workflow

For a big task with very different parts, ask "do this as a workflow". The card shows the steps, the model of each one, the cost estimate and the cap, before it runs. Put Haiku on the simple steps. See [Workflows](#/aprender/fluxos-e-agentes).

```experimentar-code
I want to organize the files in this folder by year. Before you start, tell me in 5 lines at most which files and folders you'll need to look at and what you plan to change. Don't read anything outside that without asking me, and don't show me the contents of the files in your answer.
```

```experimentar-code
List the 10 largest files in this folder and its subfolders, with their size in MB, in a table. Don't list the rest and don't explain the command.
```
