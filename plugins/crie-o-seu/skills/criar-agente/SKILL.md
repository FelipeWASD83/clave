---
name: criar-agente
description: Use when the person wants to create an agent (a "specialist" with its own instructions, model and tools) to use in Clave workflows or in Claude Code.
---

# Create an agent

An agent is a `.md` file with fixed instructions, a model and a list of what it may use. In workflows, each step can be done by an agent (e.g. a `revisor-juridico`, a legal reviewer, on Opus that only reads).

## Questions
- What does it do, and when should it be used? (becomes the description)
- Which model? `opus` (smartest, most expensive), `sonnet` (balanced), `haiku` (cheap and fast) or `inherit` (the conversation's).
- What can it do? Only read (`Read, Glob, Grep`), change files (`Edit, Write`), run commands (`Bash`), search the web (`WebSearch, WebFetch`). Give only what is needed.

## File
`.claude/agents/<name>.md` in the folder (applies there) or `~/.claude/agents/<name>.md` (personal):

```markdown
---
name: revisor-juridico
description: Reviews contracts and points out risky clauses
tools: Read, Glob, Grep
model: opus
effort: high
---

You review contracts. For each risky clause, say ...
```

The body is written as an instruction to the agent ("You are ..."), including what to deliver at the end.

You can also create one from the screen: left sidebar > **Workflows** > **Agents** tab > New agent.
