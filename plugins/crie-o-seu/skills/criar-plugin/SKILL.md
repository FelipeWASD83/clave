---
name: criar-plugin
description: Use when the person wants to bundle skills, agents and commands into a package (plugin) to reuse on another computer or share with other people, in the Claude Code format.
---

# Create a plugin

A plugin is a folder that bundles skills, agents and commands. The format is the same as Claude Code plugins.

## Structure

```
meu-plugin/
├── .claude-plugin/plugin.json
├── skills/<name>/SKILL.md
├── agents/<name>.md
├── commands/<name>.md
└── README.md
```

`plugin.json` (only `name` is required):

```json
{
  "name": "meu-plugin",
  "version": "1.0.0",
  "description": "What the plugin brings, in one sentence",
  "author": {"name": "Your name"}
}
```

In Clave you can also add `fluxos/*.json` (workflow templates); Claude Code ignores that folder.

## Test it in Clave
Left sidebar > **Plugins** > **Install from a folder** > choose the plugin's folder. The skills show up as `/meu-plugin:name`.

## Share
- Push the folder to a **public** GitHub repository. People who use Clave install it in Plugins > **Install from GitHub** with `your-username/repository`; in Claude Code, with `/plugin marketplace add`.
- For several plugins in one repository, create `.claude-plugin/marketplace.json` at the root:

```json
{"name": "minha-loja", "owner": {"name": "Your name"},
 "plugins": [{"name": "meu-plugin", "source": "./meu-plugin"}]}
```

- Never put a password, key or personal data in a plugin: it becomes public.
