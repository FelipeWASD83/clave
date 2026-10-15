---
titulo: Permissions: what Claude does on its own
trilha: 3. Automation with Code mode
ordem: 26
duracao: 6 min
resumo: Rules to allow what is safe, block what must never happen and see the history of everything.
---

The permission mode (Ask, Accept edits, Plan, Auto) applies to everything at once. **Rules** are finer: they allow or block one specific action.

## Three kinds of rule

| Rule | What it does | Example |
|---|---|---|
| **Never** | blocks, in any mode | never send anything to GitHub |
| **Always ask** | asks for OK even in Auto mode | always ask before touching a spreadsheet |
| **Allow without asking** | allows even in Ask mode | running the tests without asking is fine |

If two rules contradict each other, **Never** beats **Always ask**, which beats **Allow without asking**.

## The easiest way to create a rule

When Claude asks for permission, click **More options**:

- **Allow for this task:** lasts until that reply finishes.
- **Always in this folder…:** saves a rule for that folder.
- **Always, everywhere in Clave…:** saves a rule that applies in every folder.

Clave suggests the rule (for example, `Bash(git status *)`) and you can adjust it before saving.

## How a rule is written

The format is the same as Claude Code's, so rules work in both:

- `Bash(npm test *)`: a [command](#/aprender/glossario/comando) (the `*` means "anything").
- `Edit(docs/**)`: creating or changing files inside the `docs` folder.
- `Read(*.pdf)`: reading PDF files.
- `WebFetch(domain:example.com)`: opening pages from a website.
- `Fluxo`: workflows (the name stays in Portuguese; only "Never" has an effect, because a workflow always asks for your OK).

The rules for a folder live in that folder's `.claude/settings.local.json` file, the same one Claude Code uses.

## Protections that always apply

- **Protected files** (Settings > Code mode), such as `.env` and keys: the file tools never read or change them.
- A command that **deletes or publishes** something asks even when commands are allowed, unless the rule is written for that exact command.
- A **workflow** always asks for your OK.

## Test and check

In **Permissions** (Settings > Code mode, or by typing `/permissoes`), you can:

- see and delete rules;
- **test** ("would this command go through?") without running anything;
- see the **history** of every action: what was done on its own, what you allowed, what was blocked and why.
