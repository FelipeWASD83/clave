---
titulo: Why use Clave (and the API)
trilha: 1. First steps
ordem: 0
duracao: 4 min
resumo: Pay for what you use, with no 5-hour limit and your data on your own computer. And when the official app is better.
---

Clave talks to Claude through the [API](#/aprender/glossario/api), using your [key](#/aprender/glossario/chave-da-api). It sounds like a technical detail, but it changes a lot for the person using it.

## You pay for what you use

The Claude Pro subscription costs $20 a month, whether you use it a lot or a little. With the API, each answer costs what it actually used:

| Use | Approximate cost |
|---|---|
| A thousand short messages on Haiku 5.5 | about $0.40 |
| A thousand short messages on Sonnet 5.5 | about $7 |
| One question to the lesson helper | a fraction of a cent |

(These are estimates without long reasoning; with reasoning, the answer costs more.) Clave shows the cost **of each answer** and the month's total in the left sidebar. If you use AI a few times a day, you spend cents.

## No "come back in 5 hours"

The official app's plans have a limit per 5-hour window and a weekly limit. The API has none of that: the limit is requests per minute, which is plenty for one person. You are the one in control of spending, with Clave's **monthly cap**: when you reach it, Clave stops. No surprises on your bill.

## Your data stays with you

- By default, Anthropic **does not use what goes through the API to train models**, and deletes it from its servers within 30 days.
- Your conversations, your [memory](#/aprender/memoria) and your spending history stay **only on your computer**.
- The key is stored encrypted by Windows.
- Clave's code is open: anyone can check what it does.

## The right model for each job

You pick the [model](#/aprender/modelos-e-raciocinio) in each conversation: Haiku for the simple stuff, Sonnet for everyday use, Opus for the hard stuff. With [workflows](#/aprender/fluxos-e-agentes), all three work together on a big task, and you see the estimated cost before approving.

## Real automation

In [Code mode](#/aprender/modo-code), Claude works in a folder of yours: it organizes files, builds spreadsheets, writes scripts and runs commands, always showing the before and after and an undo button. [Routines](#/aprender/rotinas) make it work on a schedule, even with Clave closed. And what you learn here (CLAUDE.md, skills, agents, commands, plugins, permission rules) uses the same format as Claude Code.

## Already on Max?

The Max plan gives monthly API credit ($100 on Max 5x, $200 on Max 20x), and Clave uses that credit. See how to turn it on in the [API key](#/aprender/chave-da-api) lesson.

## When the official app is better

Straight talk: if you want Claude **on your phone** or synced across several devices, the official app does that and Clave doesn't. And if you use Opus all day, every day, you might spend more through the API than on the subscription. The **Pricing & plans** page does that math for you: tell it how you use regular Claude and it estimates what that would cost on the API. And the **Usage & spend** page shows what you really spent, by day and by model.

```experimentar
How much would I spend per month if I asked about 20 short questions a day on Haiku 5.5? And on Sonnet 5.5? Work it out step by step.
```
