---
titulo: How Code mode works
trilha: 3. Automation with Code mode
ordem: 20
duracao: 7 min
resumo: Claude working in a folder on your computer, with you approving every change.
---

In chat, Claude only talks. In **Code mode**, it becomes an [agent](#/aprender/glossario/agente): it works in a **folder on your computer**, reads and creates files, edits spreadsheets and runs [commands](#/aprender/glossario/comando). This is where automation lives.

## Getting started

1. In the left sidebar, click **New Code task**.
2. **Choose the environment**, the folder where it will work, in the panel under the text box. Clave starts in the last folder you used; under **Choose environment** you can pick another one or create one with the [folder template](#/aprender/modelo-de-pasta), which is the recommended way. In the same panel, **Turn on auto mode** switches on Auto mode (explained below).
3. Ask for the task, the same way you would ask a person.

It shows each step as it goes: "Looked at the folder", "Read spreadsheet.xlsx", "Ran: rename photos". Click any step to see the details.

## The side panel

The buttons at the top of the chat open a panel on the right side, with tabs: **Files** (the working folder; clicking a file opens the **Viewer**), **Console** (PowerShell inside Clave), **Browser** (you and Claude on the same page) and **Tasks** (what's running in the background). **Ctrl+J** opens and closes the panel, and you can drag its edge to change the width. All of it in [The Code panel](#/aprender/painel-do-code).

## Permissions: you're in charge

The shield button in the text box sets how much freedom it has:

| Mode | What happens |
|---|---|
| **Ask** (default) | Reads on its own; asks for your OK to change files and run commands. |
| **Accept edits** | Changes files on its own; asks for your OK to run commands. |
| **Plan** | Only reads and shows a plan on a card. You approve it (and choose how it runs) or ask for a different one. Great for getting started. |
| **Auto** | Does everything on its own, except deleting or publishing things, which always ask for your OK. In the Code browser, it uses any site, clicks and types without asking. |

When it asks for permission, a card shows you **exactly** what it is about to do: the command, or the before and after of the file (red lines go away, green lines come in). You can **Allow** it or **Deny** it and say what you would prefer instead. Under **More options** you can allow that for the rest of the task or save a rule ("Always in this folder" or "Always, everywhere in Clave") so it doesn't ask again. See the [permissions](#/aprender/permissoes) lesson.

**Read before you approve.** If you don't understand a command, deny it and ask "what does this command do?".

## The plan before a big task

Before touching a lot (three files or more, moving or renaming files, reorganizing a folder), Claude shows a **Can I do it like this?** card with the plan, and only starts after your answer:

- **Go ahead**: it carries on, and the permissions work as usual.
- **Change the plan**: write what you want different in the field and it redoes the plan.
- **Don't do it**: it stops and asks what you prefer.

This works in any mode. If you would rather it went straight ahead, turn it off in **Settings > Code mode > Ask for OK before big tasks**.

## Undo

Made a mistake? Below the reply you will see **Undo changes**: the files it created or edited in that reply go back to how they were. What a **command** did (moving, renaming, deleting, running a script) doesn't come back with the button: that's why the command card shows what will run first, and the ones that delete things or touch anything outside the folder always ask for your OK. For a big change made by a command, ask first for a list of what will be touched, or for a copy. More ways to go back in [Undo, backup and Git: your safety net](#/aprender/rede-de-seguranca).

## Protected files

In Settings > Code mode there is the **Protected files and folders** list, such as passwords and keys (`.env`, `*.key`). The file tools **never** read or change these files, and a command that mentions one always asks for your OK. Put anything sensitive there.

## Per-task cap

A big task can make a lot of calls. The **per-task cap** (default $2) pauses the task when it has spent that much; you decide whether to keep going by sending "continue". To spend less in Code, see [Code mode without waste](#/aprender/code-sem-desperdicio).

## Big task? Use a workflow

For a big task, ask "do this as a workflow": Claude splits it into steps, each on the right model (for example, Opus plans and Sonnet does the work), and shows the estimated cost before starting. See the [workflows](#/aprender/fluxos-e-agentes) lesson.

## Requests that work well

- "Before you change anything, show me the plan." (or use Plan mode)
- "Do it on 3 files first so I can check; then do the rest."
- "Create a script I can run again next month."

```experimentar-code
Look at this folder and explain to me, in simple words, what is in it and what you could automate here.
```
