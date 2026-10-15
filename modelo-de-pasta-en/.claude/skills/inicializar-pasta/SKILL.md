---
name: inicializar-pasta
description: Does the first tidy-up of a folder created from the template - looks at the projects that already exist, fills in the map in CLAUDE.md, builds the launch.json and PORTAS.md and makes sure every project has Git. Use when the user calls /inicializar-pasta, or when they ask to update the project map.
argument-hint: "[nothing, or the name the folder should have]"
disable-model-invocation: true
---

# Initialize the folder

This folder was born from a template: the rules, the skills and the visual
library are ready, but the root `CLAUDE.md` doesn't know **which projects exist
in here**. Without that, it describes an imaginary folder.

The job of this skill is to close that gap once, carefully, and get out.

## 0. Check that it hasn't been done already

If the map in section 8 of `CLAUDE.md` **already lists a project**, the folder
has already been initialized. Do not run it again on top of that: ask whether
the user only wants to **update** the map (a project that came in, a project
that left), which is a smaller job, done with steps 2 and 4.

## 1. Look at the folder before writing anything

List the root and sort it into three groups:

- **Projects**: the real working subfolders.
- **Template infrastructure**: `.claude/`, `_organizacao/`, `.gitignore`,
  `CLAUDE.md`, `PORTAS.md`, `READ-ME-FIRST.md`. These are not projects and
  don't go into the map.
- **Out of place**: a loose file at the root, a `.zip`, a folder with a space
  or a parenthesis in its name, a `_1`/`_2` suffix from a repeated download.
  **Do not move anything now**: note it down and report it at the end. Changing
  the folder without telling is worse than leaving it messy.

## 2. Open each project: don't deduce from the name

For each project folder, **read before describing**:

1. `CLAUDE.md`, `README.md` and any documentation `.md` in the folder. If they
   exist, they take priority over any deduction.
2. What the technology says: `package.json` (look at `scripts`),
   `requirements.txt`, `pyproject.toml`, `*.csproj`, `*.yyp`, `index.html`,
   spreadsheets and documents.
3. The entry point: `main`, `src/main.*`, `server.py`, `app.py`, `*.bat`,
   `index.html`.

Only then write the map line:

```
| folder | what it is, in one sentence that states the purpose | technology | how to run |
```

- **One sentence that tells it apart.** "Spreadsheets" tells nothing apart.
  "Household expense tracking, one spreadsheet per year" does.
- **How to run is the literal command**, with the port when there is one. A
  folder that doesn't run (documents, spreadsheets) says so.
- Two similar folders? **Find out and write the difference.**
- Couldn't tell what the folder is after opening the files? **Ask.** An
  invented line in the map misleads every following conversation.

## 3. Ask what can't be found out alone

Ask all at once, in a block:

1. **Is any project a client's or live?** It changes everything: confirm before
   touching, never publish on your own, the `entregar-site` skill is mandatory.
2. **Is any project private**, so that it isn't opened or commented on without
   being asked?
3. **Should any project stay out of Git** on purpose?

The answers become notes in the map (section 8) and, if it applies, `deny`/`ask`
permission rules in `.claude/settings.json`.

## 4. Build the `launch.json` and `PORTAS.md`

Every project that runs as a website or server gets an entry in
`.claude/launch.json`, with the port taken from the ranges in `PORTAS.md` (and
noted in the table there). Two traps:

- **Never `python3`** on Windows: use `python`.
- **Never repeat a port**: what a website stores in the browser is separated by
  port; two projects on the same port mix their data.

Format for a static website:

```json
{
  "name": "project-name",
  "runtimeExecutable": "python",
  "runtimeArgs": ["-m", "http.server", "4310", "--bind", "127.0.0.1", "--directory", "project-name"],
  "port": 4310
}
```

Format for a project with its own script (`cwd` is the folder where the command runs):

```json
{
  "name": "project-name",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "dev"],
  "cwd": "project-name",
  "port": 5173
}
```

Afterwards, **check that the file is valid JSON** and start at least one
project to confirm that the configuration really works.

## 5. Git

```powershell
powershell -ExecutionPolicy Bypass -File ".\_organizacao\git-setup.ps1"
```

It creates Git in the ones that don't have it and lists the ones with no copy
on GitHub. It **publishes nothing**: show the list and let the user decide what
goes up.

## 6. Close `CLAUDE.md`

- Fill in section 8 (the map) and, if there are any, the notes per project.
- Date section 9 (open items) with today's date. With no open items, write
  "no open items" with the date.
- Check section 0 (About me): if it is empty, ask the user for the essentials
  and fill it in.

## 7. Report

```
Folder: <name>
Projects mapped: <n>: <short list>
launch.json and PORTAS.md: <n> entries. Tested: <which one I started and what I saw>
Git: <n> already had it, <n> I created. No copy on GitHub: <list or "none">
Out of place (I did not touch): <loose file, name outside the pattern, zip>
Needs you: <what couldn't be found out and was not invented>
```

Do not mark as done what was not checked.
