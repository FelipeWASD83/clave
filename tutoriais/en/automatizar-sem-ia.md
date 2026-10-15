---
titulo: Automating without paying the AI every time
trilha: 5. Saving credit
ordem: 45
duracao: 7 min
resumo: A routine pays on every run, forever; a program built once runs for free. How to decide, the math and ready-made requests.
---

A [routine](#/aprender/rotinas) is great for what needs judgment: reading, understanding and deciding. For what's always the same, there's a much cheaper path: ask Code mode, **once**, for a small program without AI (a [script](#/aprender/glossario/script)) and let the Windows [Task Scheduler](#/aprender/glossario/agendador-de-tarefas) run it on schedule. The lesson [An order app without AI](#/aprender/app-de-pedidos-sem-ia) shows a complete example. Here you learn how to decide, and you'll see more swaps that save money.

## The math: routine versus program

Each run of a routine is a new conversation: the instructions, the request, what it reads and the answer. The price depends on the model and on what it reads. Here are two example prices per run (estimates: something close to a simple run on Haiku and one on Sonnet):

| How often | Runs per month | At $0.003 per run | At $0.03 per run |
|---|---|---|---|
| Every hour | about 720 | $2.16 | $21.60 |
| Every 3 hours | about 240 | $0.72 | $7.20 |
| Every day | about 30 | $0.09 | $0.90 |
| Every week | about 4 | $0.01 | $0.13 |
| **Program without AI**, at any frequency | | **$0** | **$0** |

The program only costs the Code conversation that built it (for a simple program, from a few cents on Haiku to less than $1 on Sonnet, as an estimate) and then runs for free, every day, as many times as you like. Clave's routines run at most once an hour; a program in the Task Scheduler can run every 15 minutes at no cost at all.

Want to know the real cost of one of your routines? In **Routines**, click **Run now** and then **View the last run**: the cost shows up below the answer. Multiply it by the runs in a month.

## Does it need AI or not?

| Needs AI (routine) | Doesn't (program) |
|---|---|
| Reading free text and deciding what matters ("which e-mails need an answer today?") | Moving, renaming, copying or merging files |
| Summarizing documents that change every time | Moving data from a fixed format into a spreadsheet |
| Writing something new: a reply, a post, a comment on the numbers | Checking fixed rules: "row without a price", "amount over 1,000" |
| Sorting things that have no clear rule | Producing the same report with updated numbers |
| | Backing up a folder |

One question settles it almost every time: **if I wrote the rules down on paper, would anyone do it the same way, every time?** If yes, it's a program.

## The middle ground

Sometimes only one piece needs judgment: orders almost always arrive in the same format, but now and then a client writes in their own way. Then the program does everything else and calls Claude only for that piece, on Haiku. The lesson [An order app without AI](#/aprender/app-de-pedidos-sem-ia) shows how, and what it costs: less than one US cent per order (an estimate).

## Swaps that save money

| Instead of this routine | Ask for this program |
|---|---|
| Every morning: "organize the new files in Downloads" | A script that sorts them by type, scheduled in Windows (see [Your first automation](#/aprender/primeira-automacao)) |
| Every 3 hours: "check whether the orders spreadsheet has a row without a price" | A script that checks and shows a Windows notification when it finds one |
| Every Friday: "copy the Contracts folder to the backup" | A copy script, scheduled |
| Every day: "rename the new photos with the date" | A renaming script |
| Every month: "add up the expenses by category in this spreadsheet" | Excel formulas, asked for once (see [Excel with Claude](#/aprender/excel)) |
| Every morning: "read the e-mails and tell me which ones need an answer" | This one needs judgment: keep it as a routine, on Haiku |

## How to ask for the program

- On the **Routines** page, the **Build it in Code without AI** button opens Code mode with a ready-made request: Claude asks what comes in, what goes out and how often, tells you whether it can be done without AI and builds the program with a test mode, a log of what it did and scheduling in Windows.
- The **Sales** plugin has the **/sales:automate** command and the **sales:automation-without-ai** skill, made for this.
- The **Windows automation** plugin has skills for scheduling tasks, batch renaming, organizing folders and creating PowerShell scripts that show what they'll do before doing it. See [Plugins and slash commands](#/aprender/plugins-e-comandos).

Whichever path you take, always ask for: a **test mode** (shows what it would do, without doing it), a **log** of what it did (a .log file), passwords in the Windows **Credential Manager** (never in the code or in the chat) and the Task Scheduler command **shown before it runs**, with how to pause it.

```experimentar-code
I want a script, without AI, that checks the orders.xlsx spreadsheet in this folder and alerts me with a Windows notification if any row has no price or no date. It needs a test mode and a log file. Explain how to run it with a double-click and, at the end, show me the command to schedule it every 3 hours in the Task Scheduler, without running it yet.
```

## A formula instead of the math

Asking Claude to do the same math every month means always paying for the same result. Ask for **the formula**, once, and the spreadsheet calculates it on its own forever:

```experimentar
I have an Excel spreadsheet with the date in column A, the category in column B and the amount in column C. Give me the Excel formulas for: the total of each category, the total for the current month and the average per day. Tell me where to paste each one, without a long explanation.
```

## When a routine is the right choice

If the task really needs judgment, a routine is the way to go. Keep it cheap:

- **Haiku** in the form, unless the task is genuinely hard;
- a low **Cap per run**, so a run that goes wrong doesn't spend much;
- **Can search the web** unchecked, if the answer doesn't depend on anything current;
- a request that says how long the answer should be ("in 5 bullet points at most");
- the lowest frequency that does the job: every day instead of every hour, if that works.
