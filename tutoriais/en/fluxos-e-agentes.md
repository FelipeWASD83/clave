---
titulo: Workflows: several models on one task
trilha: 3. Automation with Code mode
ordem: 25
duracao: 6 min
resumo: How to split a big task into steps, each on the right model, knowing the cost beforehand.
---

In a normal conversation, one [model](#/aprender/glossario/modelo) does everything. In a **workflow**, the task becomes steps, and each step goes to whoever does it best (or cheapest):

| Step | Who does it | Why |
|---|---|---|
| Plan | Opus 5.5 | the most careful one for thinking through the plan |
| Do | Sonnet 5.5 | does the heavy work for half the price |
| Test | Sonnet 5.5 | runs the tests and checks the result |
| Review | Opus 5.5 | looks at everything again with a critical eye |

Each step receives the goal and the reports from the previous steps, and at the end Claude puts everything together and tells you what was done.

## It always asks for your OK

A workflow costs more than a normal reply (there are several conversations behind it). That is why Clave **never** runs a workflow on its own. First a card appears with:

- the steps, the model and the reasoning level of each one (you can change them right there, for example putting Haiku on a simple step);
- what each step is allowed to do (read, change files, run commands, search the web);
- the **cost estimate** (a range, because it depends on how much each step needs to read);
- the **workflow cap**: if the total goes over this amount, the workflow stops.

Nothing happens until you click **Run workflow**. While it runs, click a step to see what it is doing; if a step wants to change a file, the permission request shows up right there.

## How to start a workflow

- Ask: "do this as a workflow" and Claude builds the steps.
- Or type `/workflow` in the message box and pick a ready-made workflow (Plan, do and test; Deep research; Parallel review; Large spreadsheet; Write and review).
- Or go to **Workflows & agents** in the left sidebar, pick one and click *Use in chat* or *Use in Code*.

Some steps run **at the same time** (for example, three searches in parallel), which makes the workflow faster without costing more.

## Agents

Each step can be done by an **agent**: a "specialist" with its own instructions, model and tools. Clave comes with six, named in Portuguese: planejador (planner), executor, testador (tester), revisor (reviewer), pesquisador (researcher) and redator (writer) and plugins bring more. You create your own in **Workflows & agents > Agents**: give it a name, say what it does, and choose the model and what it is allowed to use. Agents use the same format as Claude Code (files in `.claude/agents`).

## When it is worth it

It is worth it for a big task, where a mistake is expensive or which has very different parts (researching, writing, checking). For a simple question or a small task, a normal conversation is faster and cheaper.

```experimentar
Research the 3 cheapest ways to automatically back up my photos on Windows and build a comparison. Do it as a workflow, with the searches running in parallel on Haiku.
```
