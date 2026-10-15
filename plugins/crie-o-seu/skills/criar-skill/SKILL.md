---
name: criar-skill
description: Use when the person wants to teach Claude a fixed way of doing a task they repeat (a procedure, a checklist, a text pattern). Interviews the person and writes the skill in the Claude Code format.
---

# Create a skill

A skill is a `SKILL.md` file with instructions that Claude loads when the task matches the description. It works in Clave and in Claude Code.

## 1. Interview (short)
Ask, at most 4 things at a time:
- What task is it, and when does it come up? (becomes the description)
- How do you do it today, step by step? Is there an example of a good result?
- What must never happen?
- Does it apply everywhere (personal skill) or only to one folder (folder skill)?

## 2. Write
- Location: `.claude/skills/<name>/SKILL.md` in the working folder (folder skill) or `~/.claude/skills/<name>/SKILL.md` (personal, applies in every folder). In chat, with no folder, show the finished file and say where to save it.
- Name: lowercase, with hyphens (`relatorio-mensal`).
- Header:

```markdown
---
name: relatorio-mensal
description: Use when ... (say WHEN to use it, with the words the person would use when asking)
---
```

  Optional: `disable-model-invocation: true` (only runs when the person calls it with /name), `argument-hint: [month]`.
- Body: numbered steps, short rules, an example of the result. Under 500 lines. Support files (templates, examples) go in the same folder, cited with a link.

## 3. Test
Show how to call it: `/skill-name` in the message box (or just ask for the task, and Claude loads it on its own). Offer to adjust it after the first use.
