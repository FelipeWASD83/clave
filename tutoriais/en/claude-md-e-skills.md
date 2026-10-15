---
titulo: CLAUDE.md and skills: teach rules and procedures
trilha: 4. Going further
ordem: 31
duracao: 7 min
resumo: Write your folder's rules and turn repeated tasks into procedures Claude follows on its own.
---

## CLAUDE.md: the folder's rules

[CLAUDE.md](#/aprender/glossario/claude-md) is a text file that Claude reads on its own when it works in a folder (in Code mode). It applies to the folder and all of its subfolders. If a subfolder has its own CLAUDE.md, both apply, and the more specific one wins when they disagree.

Good things to write in a CLAUDE.md:

- **Who you are** and what you know ("I don't know how to code, explain what you did and how to use it").
- **How you want the work done** ("always show me the plan before changing files").
- **How the folder is organized** ("each client has a subfolder with their name").
- **What to never do** ("never delete anything from the Originals folder").
- **Lessons learned** ("the accounting report uses semicolons, not commas").

Write in simple sentences, as if you were explaining to a new assistant. You can even ask Claude itself:

```experimentar-code
Create a CLAUDE.md for this folder. Ask me questions about how I work, what is in here and what you should never do, and at the end write the file.
```

## Skills: saved procedures

A [skill](#/aprender/glossario/skill) is a step-by-step procedure saved in a file, at `.claude/skills/skill-name/SKILL.md`. It starts with a header giving the name and **when to use it**:

```
---
name: monthly-report
description: Builds the monthly sales report. Use when I ask for the month's report.
---

1. Read the month's sales spreadsheets in the sales/ folder.
2. Add up by salesperson and by product.
3. ...
```

Claude sees the list of skills (name and description) and loads the whole skill when the task matches. You can also call one directly by typing `/monthly-report` in the Code mode text box (when you type `/`, the list appears).

Skills that come ready-made in the [folder template](#/aprender/modelo-de-pasta): watching videos, reviewing code, visual direction for websites, a delivery checklist and others. The [plugins](#/aprender/plugins-e-comandos) bring 25 more (Excel, email, research with sources, Windows scripts...), and skills that aren't manual-only also work in chat.

A cousin of the skill is the **command**: a ready-made request in `.claude/commands/name.md`, called with `/name`. Claude chooses a skill on its own; a command only runs when you call it.

## Turn what you repeat into a skill

Did a task with Claude and it came out well? Ask:

```experimentar-code
Turn what we just did into a skill in this folder, so I can ask for it again next month with just its name.
```

## Where each thing applies

| File | Applies to |
|---|---|
| Settings > Personalization | All conversations, in chat and in Code |
| A folder's CLAUDE.md | Code mode only, in that folder and the ones inside it |
| Skills in `.claude/skills` | Code mode only, in that folder and the ones inside it |
| Permission rules in `.claude/settings.local.json` | Code mode only, in that folder |
| Agents in `.claude/agents` and commands in `.claude/commands` | In that folder (the ones in your personal `~/.claude` folder apply everywhere) |
| Plugins turned on | All conversations |
| Memory | All conversations (if turned on) |
