---
titulo: Web search and connectors
trilha: 4. Going further
ordem: 36
duracao: 4 min
resumo: Let Claude search the internet and connect outside services through the MCP standard.
---

## Web search

Without search, Claude only knows what it learned up to its cutoff date (mid-2026) and doesn't know what happened yesterday. That's why web search comes on: it **searches and reads pages** on its own when the answer needs something current. For a chat without search, click the **Web** button in the text box (it turns off just there); to turn it off for good, go to Settings > Features. The sources show up in the answer (small numbers next to the sentences and the list of sites).

Each search costs $0.01, on top of the tokens for the pages it reads. To leave it on all the time: Settings > Features.

```experimentar
What were the main tech news stories this week? Cite the sources.
```

## Connectors (MCP)

[MCP](#/aprender/glossario/mcp) is a standard for connecting AI to other services. A connector gives Claude new tools: looking up a program's documentation, searching a system, reading a database.

In **Settings > Connectors**, add the name and the address (https://...) of an MCP server. Anthropic itself makes the connection, so:

- only **public servers on the internet** work (not the ones running on your own computer);
- use only services you trust: what Claude sends to them is out of your control.

A free, public example is DeepWiki (`https://mcp.deepwiki.com/mcp`), which explains GitHub projects.

```experimentar
Use the DeepWiki connector to explain to me, in simple language, what the anthropics/anthropic-sdk-python project does.
```
