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

Clave suggests the rule (for example, `Bash(git status *)`) and you can adjust it before saving. On the site card of the [Code browser](#/aprender/navegador), **Allow** itself already lasts until the reply finishes, and **More options** only has the two **Always** choices.

## How a rule is written

The format is the same as Claude Code's, so rules work in both:

- `Bash(npm test *)`: a [command](#/aprender/glossario/comando) (the `*` means "anything").
- `Edit(docs/**)`: creating or changing files inside the `docs` folder.
- `Read(*.pdf)`: reading PDF files.
- `WebFetch(domain:example.com)`: opening pages from a website. In a **Never** rule, it also stops the [Code browser](#/aprender/navegador) from using that site (no opening, reading or clicking).
- `Navegador(example.com)`: the Code browser on that site (the name stays in Portuguese); `Navegador(*.example.com)` covers the site and its subdomains (the asterisk only works at the start). In **Allow without asking**, it removes the site card, but clicking and typing still ask for OK. `Navegador` alone or `Navegador(*)` do the same on every site.
- `Navegador(clicar:example.com)`: only one browser action on that site. The actions are `abrir` (open), `ler` (read), `print` (screenshot), `rolar` (scroll), `voltar` (back), `clicar` (click) and `digitar` (type), and the English names work too: `open`, `read`, `print`, `scroll`, `back`, `click` and `type`; `Navegador(digitar)` or `Navegador(click:*)` apply on any site. Only a rule that names the action skips the OK for clicking and typing. Example: `Navegador(clicar:localhost)` in **Allow without asking** lets it click on the site you're testing on your computer without asking for OK. A word that isn't an action (`Navegador(delete:example.com)`) or a colon with nothing before it (`Navegador(:example.com)`) doesn't count as a rule.
- **The port matters.** `Navegador(clicar:localhost:5173)` only applies on port 5173; without a port, it applies on any port. `Navegador(*:8080)` applies to any site on port 8080.
- The site in a rule is read the same way the browser reads the address. `EXAMPLE.com`, `example.com.` (with a dot at the end) and other disguised ways of writing the same address count as `example.com`, and an IP written another way (`127.1`) counts as the same IP (`127.0.0.1`). So nobody gets around a **Never** rule by changing how it's written.
- `Fluxo`: workflows (the name stays in Portuguese; only "Never" has an effect, because a workflow always asks for your OK).

The rules for a folder live in that folder's `.claude/settings.local.json` file, the same one Claude Code uses.

## Protections that always apply

- **Protected files and folders** (Settings > Code mode), such as `.env` and keys: the file tools never read or change them.
- A command that **deletes or publishes** something asks even when commands are allowed, unless the rule is written for that exact command.
- A **workflow** always asks for your OK.
- In the Code browser, Claude never fills in **password**, **access code** or **card** fields, not even with a rule: you type those. In **Plan** mode, it doesn't click or type.

## Test and check

In **Permissions** (Settings > Code mode, or by typing `/permissions`), you can:

- see and delete rules;
- **test** ("would this command go through?") without running anything;
- see the **history** of every action: what was done on its own, what you allowed, what was blocked and why.
