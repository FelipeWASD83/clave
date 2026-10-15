# CLAUDE.md: rules for this work folder

Instructions for Claude (in Clave's Code mode or in Claude Code) for any work
inside this folder and its subfolders. A specific project's own `CLAUDE.md`,
when there is one, **takes priority over this file** for that project. And
whatever I say in the conversation counts more than any file.

---

## 0. About me

<!-- SOBRE-MIM -->

---

## 1. How to answer

- **English**, straight to the point. No preamble and no praising my request.
- Answer length proportional to the subject: simple question, short answer.
- If I am wrong, say so right at the start, not hidden at the end.
- If there is a clearly better way than the one I asked for, point it out
  **before** doing it. If I understand and keep my decision, respect it.
- **Never invent** files, functions, test results or sources. Never claim
  something works without having checked. When you don't know, say you don't know.
- Keep apart what is a checked fact, what is a deduction and what is a guess.
- Explain in plain language **what was done and how to use it**. Technical
  detail only when I ask for it or when I need it to decide something.
- Need me to change something by hand? Say it in the format "in file X, look
  for Y and replace it with Z".

## 2. Environment

- System: see section 0. If it isn't written there, ask or check before
  assuming.
- On Windows the terminal is **PowerShell**: example commands in PowerShell.
- **Use `python`, never `python3`** on Windows (`python3` opens the Microsoft
  Store instead of running).
- Before assuming a program exists (Git, Node, Python, Excel), check.

## 3. Rules for this folder

1. **One project = one subfolder.** Do not create a new folder at the root
   unless I ask; a new project that I asked for is already that request.
2. **Nothing loose at the root.** The root holds only the rule and guide files
   (`CLAUDE.md`, `READ-ME-FIRST.md`, `PORTAS.md`, `.gitignore`) and the
   `.claude/` and `_organizacao/` folders. (`PORTAS.md` is the list of ports;
   `_organizacao` is for maintenance scripts. Their names stay in Portuguese
   so that everything keeps working.)
3. **Folder names in `lowercase-with-hyphens`**, no spaces, no accents, no
   parentheses and no `_1`/`_2` left over from repeated downloads.
4. **Never version or hand over:** `node_modules/`, `__pycache__/`, `dist/`,
   `.env`, passwords, keys, tokens. The `.gitignore` at the root already
   covers the basics.
5. **`_originais/`** (in any project) holds irreplaceable raw material
   (photos, videos, original documents): never delete, convert or "optimize"
   it on your own.
6. **`.claude/`** holds Claude's configuration for this folder:
   - `skills/`: ready-made procedures (section 3.1);
   - `referencias-visuais/`: the library of visual references for websites and apps;
   - `launch.json`: how to run each web project (together with `PORTAS.md`);
   - `settings.json`: permission rules for Claude Code.

### 3.1 Skills in this folder

| Skill | What it is for |
|---|---|
| `ver-video` | Watch and listen to videos (a file or a link): frames + transcript |
| `direcao-visual` | Decide the look of a website or app before writing CSS |
| `revisar-visual` | Open it in the browser, take screenshots and fix what is broken or ugly (manual: `/revisar-visual`) |
| `checklist-web` | What must be ready before saying a website works |
| `entregar-site` | Checklist before publishing a website (manual: `/entregar-site`) |
| `revisar-codigo` | Look for half-done work, stubs and functions that pretend to work |
| `pesquisa-tecnica` | Research before choosing a library, API or approach |
| `gml` | GameMaker: consult the official manual instead of writing from memory |
| `inicializar-pasta` | First tidy-up of the folder and the project map (manual: `/inicializar-pasta`) |

The skill names stay in Portuguese so that the slash commands keep working.

A skill mentioned inside another one does not load by itself: when a rule or
skill says to follow another one, load both.

## 4. Before touching any project

1. Read the `CLAUDE.md`, the `README.md` and the other `.md` files **in the
   project's own folder**. They take priority over this file.
2. **Do not guess what the project does from its name.** Open the files.
3. Preserve what already works. Do not rewrite half the project to fix a small
   problem; if a big change is worth it, explain why first.
4. Found an important problem outside what I asked for? Tell me, do not fix it
   quietly.
5. Finished? Check that the project's line in the map (section 8) is still correct.

## 5. Plan before changing

For any task that is not trivial (more than one file, a new system, a new
website, a reorganization, a fix that requires understanding the project):
present a **short plan** and wait for my OK before changing files. The plan says:

1. what I understood needs to be done, in one sentence;
2. which files will be created, changed or deleted;
3. the chosen approach (and the discarded alternative, if there was one);
4. what could break among the things that already work;
5. how the result will be checked.

A trivial task (changing a text, a color, a value I pointed out) does not need
a plan. If I say "do it however you think is best", choose, tell me in a few
lines what was decided and carry on. If halfway through the plan turns out to
be wrong, stop and tell me.

**New website or app:** before any CSS, read
`.claude/referencias-visuais/CLAUDE.md` and follow the `direcao-visual` skill.

## 6. Check before saying you are done

- Run whatever can be run: tests, the script, the website in the browser.
- Web project: the `checklist-web` skill before saying "done".
- Big change: the `revisar-codigo` skill.
- **Do not say it works without having seen it work.** Could not test it? Say
  so in so many words.

## 7. Git, versions and publishing

- **Every project has git.** A new project starts with `git init`. Before a big
  change, check `git status`: if there is already unsaved work of mine, warn me
  before touching anything (mixing the two removes the chance to undo).
- **Save a version (commit) when you finish** a checked task, not in the
  middle. The message says in English **what changed and why**.
- The commit includes only what was changed in the task (`git add` on its files).
- **Sending to GitHub (`git push`) and publishing a website are my decision:**
  show the command and wait. Never `git push --force`.
- **Version X.Y.Z** on any project that someone uses: Z for a fix, Y for
  something new, X for a big change. Note in the project's `CHANGELOG.md`, in
  plain language, what changed for the people who use it.

## 8. Project map

> Empty because the folder is new. The `/inicializar-pasta` skill fills it in
> (or ask: "update the project map").

| Folder | What it is | Technology | How to run |
|---|---|---|---|
| _(empty)_ | | | |

## 9. Open items

No open items recorded yet.
