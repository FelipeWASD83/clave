---
titulo: Tokens, context and spending
trilha: 1. First steps
ordem: 6
duracao: 5 min
resumo: Why a long conversation gets expensive, what the gauge shows and how the monthly cap works.
---

## Tokens

The API charges by [token](#/aprender/glossario/token), the little piece of text the AI reads and writes. A thousand tokens is about 700 words of English. Photos and PDFs turn into tokens too (one PDF page comes to something like 1,500 to 3,000).

## Context: the conversation's memory

With every message, Claude rereads **the whole conversation** (it doesn't keep anything between one answer and the next; Clave is the one that sends the history). That's why:

- a 50-message conversation costs more per answer than a 5-message one;
- attaching a big PDF at the start means it gets reread with every answer.

The **gauge** below the text box shows how much of the [context window](#/aprender/glossario/janela-de-contexto) (up to 1 million tokens) has been used.

Two things help on their own:

- **Cache**: the repeated beginning of the conversation costs 10 to 40 times less, depending on the model. It lasts 5 minutes after it was last used: replying within that time keeps the discount. It's on by default.
- **Automatic summary**: when the conversation passes a certain size (150 thousand tokens, by default), Anthropic summarizes the beginning so it fits and gets cheaper. A line saying "The conversation was summarized here" appears.

Even so, the best saving is a simple one: **new subject, new chat**.

## The monthly cap

In **Settings > Spending limit** you set:

- the **monthly cap** in dollars;
- the **day the month rolls over** (use the day your credit renews);
- what to do when the cap is reached: **stop** or **only warn**;
- the **per-task cap** for Code mode, which pauses a long task when it spends too much.

Clave warns you when you pass 50%, 80% and 95% of the cap. In **Usage & spend** you can see spending by day, by model and by conversation.

On the new chat screen, the **Your usage** panel shows the tokens you've already used, your day streak (how many days in a row you've used Clave), a heatmap of your days, your favorite model, each model over the last 7 days and a **forecast**: at the pace of the last 14 days, where the month will end up and on what day the cap runs out. Do you have Max? Setting the cap to $100 (or $200) shows you when your plan's credit runs out.

**Pricing & plans** has the price of each model and the **API or subscription?** calculator: you tell it how you use regular Claude (how often you hit the 5-hour limit, or how many messages you send per day) and it estimates what that would cost on the API, model by model.

## What it costs, in practice

Approximate values, just to give you an idea:

- a short question on Haiku: less than $0.001;
- an average answer on Sonnet, with reasoning: around $0.02;
- analyzing a 20-page PDF on Opus: around $0.10 to $0.30;
- a big task in Code mode (many steps): from $0.20 to a few dollars.

```experimentar
Explain in a simple way why a very long conversation with an AI gets more expensive with every answer.
```

Want to spend less? The saving track starts at [Where your credit goes](#/aprender/para-onde-vai-o-credito).
