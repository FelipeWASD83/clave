---
name: criar-comando
description: Use when the person wants a slash shortcut (/name) for a request they repeat, with room to fill in details (e.g. /orcamento client amount).
---

# Create a slash command

A command is a `.md` file whose text becomes the message when the person types `/name`. It works in Clave and in Claude Code.

## File
`.claude/commands/<name>.md` in the working folder (or `~/.claude/commands/` for all folders). A subfolder becomes a prefix: `.claude/commands/vendas/orcamento.md` is `/vendas:orcamento`.

```markdown
---
description: Builds a quote from the client's name and the amount
argument-hint: [client] [amount]
---

Build a quote for $0 in the amount of $1, using the modelo-orcamento.docx template in the folder.
```

## What you can use in the text
- `$ARGUMENTS`: everything that came after the command.
- `$0`, `$1`, ...: each word (text with spaces goes in quotes: `/orcamento "Sun Bakery" 1500`).
- Optional header: `model: haiku` (runs on a cheaper model), `allowed-tools: Read, Bash(git status *)` (allows those actions without asking, only while the command runs; use with care).

Test it by typing `/` in the message box: the new command shows up in the list.
