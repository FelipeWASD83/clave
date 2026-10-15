---
titulo: Web search and connectors
trilha: 4. Going further
ordem: 36
duracao: 4 min
resumo: Let Claude search the internet and connect outside services through the MCP standard.
---

## Web search

Without search, Claude only knows what it learned up to its cutoff date (mid-2026) and doesn't know what happened yesterday. That's why web search comes on: it **searches and reads pages** on its own when the answer needs something current. For a chat without search, click the **Web** button in the text box (it turns off just there); to turn it off for good, go to Settings > Features. The sources show up in the answer (small numbers next to the sentences and the list of sites).

Each search costs $0.01, on top of the tokens for the pages it reads.

```experimentar
What were the main tech news stories this week? Cite the sources.
```

## E-mail

In **Settings > Connectors > E-mail**, connect your mailbox. Then Claude reads, searches and summarizes your e-mails and writes replies. **Sending always shows you the whole e-mail and waits for your OK.**

- **Gmail**: turn on 2-Step Verification in your Google Account and create an **app password** at myaccount.google.com/apppasswords (16 letters). Paste that password, not your normal one.
- **Yahoo, Zoho and the company website's e-mail** (hosting): also with an app password or the mailbox password, and the IMAP and SMTP servers your provider lists.
- **Outlook.com and Microsoft 365** no longer accept passwords from other apps. Use **Outlook on this computer** (the classic Outlook installed, already signed in) or Zapier.

```experimentar
Summarize today's unread e-mails and tell me which ones need a reply.
```

## Zapier

Zapier connects Claude to hundreds of apps (Google Sheets and Calendar, WhatsApp Business, CRMs) without programming. **Settings > Connectors > Zapier** has the step by step: you create the server at mcp.zapier.com, choose the actions you want to allow and paste the address into Clave. It's an outside service with a limited free plan.

For something that always repeats the same way, compare it first with a program without AI: see [An order app without AI](#/aprender/app-de-pedidos-sem-ia).

## Connectors (MCP)

[MCP](#/aprender/glossario/mcp) is a standard for connecting AI to other services. A connector gives Claude new tools: looking up a program's documentation, searching a system, reading a database.

In **Settings > Connectors**, add the name and the address (https://...) of an MCP server. Anthropic itself makes the connection, so:

- only **public servers on the internet** work (not the ones running on your own computer);
- use only services you trust: what Claude sends to them is out of your control.

A free, public example is DeepWiki (`https://mcp.deepwiki.com/mcp`), which explains GitHub projects.

```experimentar
Use the DeepWiki connector to explain to me, in simple language, what the anthropics/anthropic-sdk-python project does.
```
