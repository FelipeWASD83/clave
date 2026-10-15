---
name: revisar-codigo
description: Reviews the code that was just written or changed, with a clean context, looking for half-done implementations, stubs, hidden TODOs and functions that pretend to work. Use after any big change, before declaring a task finished, and whenever the user asks whether it is really done.
argument-hint: "[project or file]"
context: fork
allowed-tools: Read Grep Glob Bash
---

# Code review with fresh eyes

The person who wrote the code is the worst person to review it: they know what
they meant and read the intention instead of what is written. That is why this
review runs in a separate context, arriving **without** the conversation that
produced the code.

And there is a common aggravating factor: the user often **can't read HTML,
CSS and JavaScript**. They have no way of opening the file and seeing that an
empty handler was left behind. If it gets past here, it goes straight to them.

Target: `$ARGUMENTS`

## What to review

If the project has git, review the diff (`git diff`, `git diff --staged`).
Without git, review the files that were touched in the task. Don't review the
whole project: the target is what changed.

## Look for, in this order

**1. Implementation that pretends to be ready**, the most important finding:

- A function that returns a fixed value, `null` or `[]` where it should calculate.
- An empty event handler, or one that only has `console.log`.
- `try { ... } catch (e) {}` swallowing an error in silence.
- `TODO`, `FIXME`, `XXX`, "for now", "temporary", "mock", "placeholder".
- A button or field created in the HTML with nothing in the JS that responds to it.
- An error path that exists in the code but never shows anything on the screen.
- A `setTimeout` faking loading that loads nothing.

Grep helps to start, but it isn't enough: actually read the changed functions.

**2. Breaking what already worked**

- A function or variable renamed in one place and not in the others that call it.
- An `import`/`require` pointing to a file or export that no longer exists.
- A function signature changed without updating whoever calls it.
- A file path, route or port changed in only one place.
- A saved data format changed without a migration, which breaks what was
  already in the user's `localStorage`/IndexedDB.

**3. Consistency between files**, when the change touched several:
does the same CSS class exist in both places? do the HTML and the JS use the
same id? is the key name the same on both sides?

**4. Things that shouldn't be there**
Debugging `console.log`, an API key in the front end, a credential in plain
text, a new large file that doesn't belong in the project, a new dependency
nobody asked for, `node_modules/` or `__pycache__/` about to go into the commit.

**5. Out of scope**
Whatever was changed beyond what the task asked for. Rewriting something that
worked, mass formatting that pollutes the diff, a file touched for no reason.

## Verify for real when possible

Run whatever the project has: `npm run typecheck`, `npm test`,
`python tools/validate.py`, `tests.html`. A real result is worth more than
reading. If nothing was run, say so.

## Report

In English, ordered by severity, **without CSS/JS jargon**: the user needs to
understand the problem, not the syntax:

```
BROKEN: <what won't work, and what the user will see happen>
  file:line: <what is wrong>

HALF-DONE: <what looks ready and isn't>
  file:line: <what is missing>

OUT OF SCOPE: <what changed beyond the request>

OK: <what I checked and is right>
```

Rules of the report:

- A finding without a file and line doesn't count. If I didn't find where, I
  don't claim that it exists.
- **Don't invent problems to look useful.** A review that found nothing and
  says "I found nothing" is a valid result and more useful than noise.
- Don't repeat what the code does. The report is about what is wrong.
- If something depends on the user's choice (two possible behaviors, both
  valid), list it as a question, not as a defect.
