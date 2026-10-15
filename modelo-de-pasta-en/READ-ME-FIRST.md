# Read me first: your work folder with Claude

This folder was created from **Clave's template**. It comes ready for Claude to
work well inside it, in **Clave's Code mode** or in **Claude Code** (Anthropic's
program for programming).

## What is in here

| File or folder | What it is for |
|---|---|
| `CLAUDE.md` | The rules of the folder, which Claude reads on its own. Section 0 (About me) is yours: adjust it whenever you like. |
| `.claude/skills/` | Ready-made procedures (watching videos, reviewing code, the look of websites and others). |
| `.claude/referencias-visuais/` | A library of references (`referencias-visuais` means "visual references") so websites and apps don't end up looking generic. |
| `.claude/launch.json` and `PORTAS.md` | How to run each web project and on which port (`PORTAS.md` means "ports"). Claude fills them in. |
| `_organizacao/` | Maintenance scripts and the tool installation guide (`_organizacao` means "organization"). |

Some names are in Portuguese on purpose (for example the skill `/inicializar-pasta`).
Please don't rename them: the commands and the app expect these exact names.

## How to use it

1. **Each project is a subfolder**: `home-budget`, `shop-website`,
   `work-spreadsheets`. Ask Claude: "create a new project for X".
2. Work through Clave's Code mode, choosing **this folder** (or the project's
   subfolder): the rules and skills in here apply to the subfolders.
3. The first time, run `/inicializar-pasta` (if there are already projects in
   here) so Claude builds the project map.

## Make it yours

- Open `CLAUDE.md` and complete section **0. About me**: the more Claude knows
  about you, the better the answers.
- Change any rule that doesn't suit you. The file is yours.
- Repeated a task and it turned out well? Ask Claude to turn it into a skill.

## Useful tools

The guide `_organizacao/instalar-ferramentas.md` explains how to install Git,
the GitHub CLI, Python and Node.js, if you need them. Claude can also do it for
you (it asks for your OK first).
