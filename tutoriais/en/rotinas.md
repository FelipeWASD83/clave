---
titulo: Routines: Claude working on a schedule
trilha: 3. Automation with Code mode
ordem: 27
duracao: 5 min
resumo: A saved request that runs by itself every day, on certain days of the week or every few hours.
---

A **routine** is a request that Claude carries out on its own at the time you choose. Examples:

- "Every morning, read the new files in the Reports folder and tell me what needs my attention."
- "Every Friday at 5 PM, put together the week's summary from the sales spreadsheet."
- "Every 3 hours, check whether the orders spreadsheet has a row with no price."

## Create one

1. Left sidebar > **Routines** > **New routine**.
2. Write the **complete** request, as if it were for someone who can't ask you anything.
3. Choose where it works (in chat or in a folder), when it runs, the model and the **per-run cap** (the most it can spend each time).
4. Click **Run now** to test before leaving it on automatic.

Each run becomes a conversation in the left sidebar ("Routine: name · date"), and a notification tells you when it finishes.

## A routine only does what you have already allowed

In a routine nobody is watching, so it **doesn't ask anything**:

- reading files inside the folder: allowed;
- changing files or running commands: only if a [permission rule](#/aprender/permissoes) allows it;
- if it needs an OK, it **stops** and tells you what it would need (with the suggested rule). You create the rule and run it again.

A routine also doesn't run workflows (nobody would be there to approve the workflow card).

## With Clave closed

By default, a routine runs while Clave is open. If you tick **Run even with Clave closed**, Clave creates a task in the **Windows Task Scheduler** ("Clave" folder), which runs the routine without opening a window and notifies you. The computer needs to be on. Deleting the routine (or unticking the option) removes the task from the Task Scheduler.

If the PC was off at the scheduled time, the routine doesn't "pile up": it runs at the next scheduled time.
