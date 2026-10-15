---
name: revisar-visual
description: Opens the project in the browser, takes screenshots on desktop and mobile, reads the console and the network, and fixes whatever is broken or ugly. Use when the user asks for /revisar-visual or asks to check how a website/app is turning out.
argument-hint: "[project] [optional-path]"
disable-model-invocation: true
---

# Visual review of a web project

The user often **can't read HTML/CSS/JS in a useful way**. They have no way of
opening the code and seeing that a button disappeared or that the layout blew
up on the phone. This review exists so that **I** see the result, not them.

Project: `$0`. Extra path (if any): `$1`

## 1. Start the project

1. Read `.claude/launch.json` at the root of the folder and look for a
   configuration with the project's name. If it exists, use the port from
   there. If it doesn't, **creating the entry is part of the job**: without it
   the project has no preview and no automatic verification. (The file belongs
   to the Claude Code preview, but it works as a port index for any agent.)
2. To find out how the project runs, read its documentation
   (`dev.bat`, `npm run dev`, `iniciar.bat`, `python -m http.server`).
3. **Windows: use `python`, never `python3`.**
4. If the project is single-file HTML with no server, serve it with
   `python -m http.server` anyway: `file://` breaks fetch, modules and fonts,
   and then I would be reviewing a bug that doesn't exist in production.

If you can't find out how to run it, **ask** instead of guessing a port.

## 2. Really look

With the agent's browser tool: the Chrome DevTools MCP (`chrome-devtools`), the
Claude Code preview panel or, with neither of them, the visual library's
`capturar-print.py` (Edge with no window):

1. Navigate to the URL.
2. Screenshot at **1440×900** (desktop).
3. Resize to **390×844** (phone) and take another screenshot.
4. Read the **console** messages: errors and warnings.
5. Read the **network requests**: look for 404s and 500s (font, image, JSON, API).
6. If the project has a main interaction (a start button, a form, a menu),
   perform that interaction and take a screenshot **of the state afterwards**,
   not only of the initial screen.

If there is no browser tool available, **say so** and stop here. Don't pretend
to have reviewed it.

## 3. Judge

For each screenshot, list what is wrong, being specific and honest. Look mainly at:

- Text that is cut off, overlapping, overflowing its container or leaving the screen.
- Unwanted horizontal scroll on mobile.
- Contrast too low to read.
- Inconsistent spacing (one block with 40px, its neighbor with 13px for no reason).
- Interactive elements with a touch area smaller than ~44px on mobile.
- Broken alignment, a stretched image, wrong proportion.
- An empty/loading/error state that shows up as a blank screen.
- Console errors and 404 resources.

Then run the `checklist-web` skill and report the items that fail.

## 3.5 Compare with the visual reference

Judging "it's ugly" in a vacuum leads nowhere. Open
`.claude/referencias-visuais/CLAUDE.md`, identify which entry guided this
project (if none did, choose now the one from the right section: **Product**
for an app/tool/dashboard/institutional site, **Spectacle/Award winners** for
a landing page and a campaign) and open the matching print in
`.claude/referencias-visuais/prints/`.

With the reference's print on one side and the project's screenshot on the
other, answer the five questions from step 4 of that file:

1. Is the hierarchy as clear as the reference's?
2. Is the breathing room comparable, or is mine cramped?
3. Is the scale contrast between title and body similar?
4. Is the color playing the same role, or did I only copy the hex?
5. Is there an element that only makes sense in this project?

Whatever fails here goes on the list of fixes together with the technical
defects. And the "do not copy" list from section 6 of the library applies: entry
gate, hijacked scroll, automatic sound, a cursor with no function, animation
before the first reading, low contrast for style. If the project has any of
these, it is a defect, even if I was the one who put it there.

To capture the result's print without depending on the agent's browser, you can
use the library's capture tool pointing at the project's localhost:

```bash
python .claude/referencias-visuais/capturar-print.py lista.json output-folder
```

## 4. Fix

- **Fix it**, don't describe in theory what the user could fix.
- After fixing, **take the screenshots again** and compare. Only claim it was
  fixed if the new screenshot shows that it was.
- A matter of taste (which color, which of two layouts) follows the delegated
  choice rule from the folder rules: if the user didn't reserve that choice for
  themselves, decide, fix and tell it in the report. Ask, showing the options,
  only if the user asked to choose or if the project is a client's.

## 5. Report

Format of the final report, in English, without CSS jargon:

```
What I saw: <description of what the page shows today>
Compared with: <which reference from the library, and where the project falls behind it>
Fixed: <list of what I fixed, in plain language>
Still broken: <what couldn't be fixed and why>
Decided for you: <a matter of taste I decided, and why>
Your decision: <only what the user reserved for themselves, or what is a client's>
```

If the user needs to change something by hand, always use the format
`in file X, look for line Y and change it to Z`.
