---
titulo: Plugins and slash commands
trilha: 4. Going further
ordem: 37
duracao: 5 min
resumo: Ready-made packages of skills, agents and workflows, and the shortcuts that start with /.
---

## Slash commands

Type `/` in the message box and the list of shortcuts appears:

- **Clave's own:** `/novo`, `/modelo haiku`, `/esforco alto`, `/plano` (Plan mode in Code), `/custo`, `/fluxo`, `/memoria`, `/permissoes`, `/plugins`, `/ajuda`. (These names stay in Portuguese because that is what the app accepts.)
- **Commands:** ready-made requests with room for you to fill in, like `/escrita:email to the supplier asking for more time`.
- **Skills:** call a [skill](#/aprender/glossario/skill) directly, like `/escritorio:excel-avancado`.

You create your own commands in a file `.claude/commands/name.md` (inside the folder or in your personal folder). The text becomes the message, and `$ARGUMENTS` is replaced by whatever you write after the command. Or ask Claude: `/crie-o-seu:nova-skill`.

## Plugins

A **plugin** bundles skills, agents, commands and workflows for one kind of work. Clave comes with seven:

| Plugin | What it is for |
|---|---|
| Office | Excel, PDF reports, cleaning up and comparing spreadsheets |
| Windows automation | scripts you can run again, Task Scheduler, organizing and renaming files |
| Research | researching with sources and comparing options |
| Writing | email, proofreading, summaries, meeting minutes |
| Sites & apps | single-file pages, checks before publishing, how to publish |
| Programming | finding the cause of an error, tests, reviewing and explaining code |
| Build your own | Claude helps you create skills, agents, commands and plugins |

In **Plugins** (left sidebar) you turn each one on and off. When it is off, nothing from it shows up for Claude.

## Install others

The format is the same as Claude Code plugins, so you can install the ones other people publish:

- **Install from GitHub:** write `owner/repository`. Clave downloads it, shows what the plugin brings and only installs after your OK.
- **Install from a folder:** for a plugin you made or downloaded.

Install only from people you trust: a plugin brings instructions for Claude. The commands it suggests still go through your [permissions](#/aprender/permissoes).
