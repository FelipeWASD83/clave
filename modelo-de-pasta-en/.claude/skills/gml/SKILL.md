---
name: gml
description: Write, read or fix GML (GameMaker Language) by consulting the official manual instead of writing from memory. Always use it when the task involves GameMaker (.gml code, .yyp project, object events, shaders, a question about a function or the API), and before claiming that any function exists or behaves in a certain way.
argument-hint: "[what to do in GML]"
allowed-tools: Bash Read Write Edit Grep Glob WebSearch
---

# GML without inventing functions

Task: `$ARGUMENTS`

## Why this skill exists

GML is the language where I hallucinate the most, for one specific reason:
there are **three generations of API** with similar names, and the internet is
full of code from the first two.

- Game Maker 8 / GMS 1.x: `instance_create()`, `argument0`, `d3d_*`
- GMS 2.0–2.2: layers arrived, scripts were still one file each
- GMS 2.3+ up to today: named functions, structs, constructors, methods, `static`

A guess in GML doesn't give an obvious syntax error or an "undefined is not a
function" in the browser: it gives a compile error in the middle of the user's
work, or worse, a function that exists but does something else. And if
GameMaker is not installed on this machine (check: `C:\ProgramData\GameMakerStudio2`
and the IDE under `Program Files`), **there is no compiler here to correct
me**. The verification has to be done by me, before delivering.

Hard rule: **no GML function call leaves here without being confirmed in the
official manual.** Not "I remember it exists". Confirmed.

## The tools of this skill

The official manual (`manual.gamemaker.io`) **returns 403 to WebFetch**, but
answers normally to `curl`/`urllib`. That is why the skill brings two scripts.
Run them from inside `.claude/skills/gml/`:

```bash
python docgml.py buscar instance_create
```

Searches the local index of the manual (3113 pages) and returns the path + URL.
It is instant and offline. (`buscar` means "search".)

```bash
python docgml.py ver array_foreach
```

Downloads the function's page and prints it as clean text: syntax, arguments,
return value and example. `--completo` ("full") so it isn't cut at 120 lines.
(`ver` means "view".)

```bash
python checar-gml.py path/to/the/project
```

Scans the `.gml` files and lists every call `name(...)` that is **not** in the
manual, was not defined in the project itself and is not a keyword. It is the
invention linter. Run it **always** before delivering GML code. It doesn't
validate signatures or behavior, it only catches names that don't exist, which
is the most common mistake.

```bash
python docgml.py atualizar --canal monthly
```

Regenerates the index from the manual's `sitemap.xml`. Worth running if the
project is of a different version or if the index is old. (`atualizar` means
"update" and `--canal` means "channel".)

**Manual channels:** `monthly` (default, the current version), `lts` (LTS
2026.0) and `beta`. If the project declares the GameMaker version, use the
matching channel: some functions exist in only one of them.

## Procedure

1. **Find out the version.** Read the project's `.yyp` (the IDE version field)
   or ask. Without it, assume `monthly` and **say that you assumed it**.
2. **Read the project before writing.** Where the code lives, which scripts
   already exist, what naming convention it uses. See
   `referencias/projeto-gamemaker.md`.
3. **Read `referencias/armadilhas.md`** before writing the first line. These
   are the mistakes I make by reflex, all checked against the manual.
4. **Write the code**, consulting `docgml.py ver` for every function I have not
   used in this same session. Yes, for every one.
5. **Run `checar-gml.py`** on what was written. Zero suspects, or an
   explanation for each one.
6. **Deliver saying what was not tested.** Without GameMaker installed, the
   most honest thing is "I compiled it in my head and the name of every
   function is confirmed in the manual", never "I tested it" or "it works".

## What is safe to write from memory

The structure of the language: `if/else`, `for`, `while`, `repeat`, `do/until`,
`switch`, `with`, `try/catch/finally`, `function`, `constructor`, `new`,
`delete`, `static`, `var`, `global.`, `enum`, `#macro`, `#region`. This is
stable and I rarely get it wrong.

What is **never** safe from memory: the **name and signature of a runtime
function**, the name of a constant (`c_*`, `ev_*`, `vk_*`, `fa_*`, `bm_*`), the
name of a built-in instance variable, and the order of arguments. All of that
goes to the manual.

## Mistakes of attitude, not of syntax

- **Do not rewrite the user's project to make it "more modern".** If the
  project uses `ds_list`, don't swap everything for arrays because I think it
  is better. The rule from section 4 of the folder rules (`CLAUDE.md`) applies.
- **Do not invent a GameMaker project organization.** The IDE generates the
  structure; creating `.yy` files by hand breaks the project. See
  `referencias/projeto-gamemaker.md`.
- **Do not claim performance without measuring.** "YYC is faster", "`with` is
  slow", "a struct is faster than a ds_map": this becomes a guess built on forum
  folklore. If it matters, measure; if it can't be measured, say it is a hypothesis.
- Reliable sources, in this order: the official manual → release notes
  (`releases.gamemaker.io`) → tutorials on `gamemaker.io` → forum and community
  (useful, but often out of date: many GMS 1.x posts with no warning).
