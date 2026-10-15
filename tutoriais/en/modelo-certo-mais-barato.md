---
titulo: The right model for the lowest price
trilha: 5. Saving credit
ordem: 41
duracao: 7 min
resumo: What each model charges per message, the ladder from Haiku to Opus, the advisor and the hidden price of switching in the middle of a chat.
---

Choosing the [model](#/aprender/glossario/modelo) is the decision that moves the bill the most: between the cheapest and the most expensive, the same message costs almost 100 times more. The lesson [Models and reasoning](#/aprender/modelos-e-raciocinio) introduces all four. Here the focus is spending as little as possible without losing quality where it matters.

## What one message costs on each

Values from the **Price of each model** table, in **Pricing & plans** (with reasoning):

| Model | Short message | Medium message | Long message | Short messages for $1 |
|---|---|---|---|---|
| **Haiku 5.5** | $0.0005 | $0.0012 | $0.0027 | about 2,000 |
| **Sonnet 5.5** | $0.0094 | $0.023 | $0.048 | about 100 |
| **Opus 5.5** | $0.019 | $0.045 | $0.095 | about 50 |
| **Fable 5.1** | $0.046 | $0.11 | $0.22 | about 20 |

"Short" is a quick question with few exchanges; "medium" has several exchanges and one-page texts; "long" has attached documents, code or a long conversation. These are typical sizes Clave assumes. Once you have 10 or more answers from a model, the **API or subscription?** calculator, on the same page, also shows the cost based on your real usage.

One detail about Haiku: when the conversation goes past **100,000 tokens**, it charges 5 times more for everything (the table warns you: "5x above 100K tokens"). It's still cheaper than Sonnet, but the jump is real. The lesson [Lean conversations](#/aprender/conversas-enxutas) shows how to stay clear of it.

## What each one is for

Clave's model advisor chooses with these criteria, and they work for you too:

| Model | Use it for |
|---|---|
| **Haiku 5.5** | everyday questions and chats, short texts, summaries, translations, e-mails, explaining something, routine tasks and small files |
| **Sonnet 5.5** | long or polished texts, big documents and spreadsheets, medium-sized code, multi-step analysis, or when Haiku already got it wrong or got lost |
| **Opus 5.5** | hard and important tasks: big code or many files, high-stakes decisions, long reasoning, reviewing something with a critical eye |
| **Fable 5.1** | only very long reasoning or long creative writing, when it is worth paying a lot more |

## The ladder: start at the bottom

Since version 5.0, new chats start on **Haiku 5.5**, including for people who used another model before (they saw a notice, once, with the **Keep Haiku** and **Go back to the previous one** buttons). The idea is to climb only when you need to:

1. **Haiku** first.
2. It got it wrong or the answer is shallow? Hover over the answer, click the circular arrow (**Generate another response**) and pick **Sonnet**. You only pay for that one answer on Sonnet.
3. Still not good? Do the same with **Opus**.
4. **Fable** is for the rare case where even Opus couldn't do it, or for long creative writing.

Compare: five simple questions on Opus cost about $0.09. The same five on Haiku, redoing one of them on Opus because it came out weak, cost about $0.03. Even if it misses now and then, starting at the bottom is much cheaper than keeping Opus on "just in case".

## The advisor does this for you

So you don't have to guess, Haiku reads the chat at the 1st message and then every 5 (at the 6th, the 11th...) and tells you whether another model does the task for the lowest price. A note shows up like "For this task, Sonnet 5.5 should do better", with the reason and the **Use Sonnet 5.5** and **Keep Haiku 5.5** buttons.

- Each check costs around $0.0003 (an estimate based on Haiku's price). In a 50-message chat it checks 10 times: less than half a cent in total.
- It also tells you to **go down**: from Opus to Haiku for a short translation, for example.
- In **Settings > Models** you can let it **switch on its own** (it switches, tells you and shows a button to go back; in a chat where you go back, it stops switching) or turn the advisor off.
- It doesn't run in routines, workflow steps, the lesson helpers, **Generate another response** (there, you're the one choosing) or a command or skill that already sets the model.

## Switching in the middle of a chat has a price

The cache belongs to each model. When you switch models in a long conversation, the new model reads the whole conversation without the discount and also pays to store it in the cache. In a 50,000-token conversation, the first message on the new model spends about $0.13 just to read the conversation on Sonnet, and about $0.25 on Opus (an estimate).

So:

- **switch early**: that's why the advisor already looks at the 1st message;
- **for a hard part in the middle of a long conversation**, open a new chat on the strong model with only what it needs (the piece of text and the request), instead of switching the model of the whole conversation.

## Cheap draft, expensive review

One way to get Opus quality while paying little: do the back and forth on Haiku (ideas, draft, adjustments) and, at the end, open a new chat, pick Opus and send only the finished text:

```experimentar
Review the text below with a critical eye: point out mistakes, confusing parts and anything that isn't needed, in short bullet points. Don't rewrite it all, just show me what to change.

[paste the final text here]
```

Twenty exchanges on Haiku (about $0.01) and one review on Opus (about $0.05) cost a fraction of twenty exchanges on Opus (about $0.30). These are estimates, but the difference really is that big.

## Older models

In **Settings > Models > Show older models**, previous models that Anthropic still sells show up. It's almost never worth it: Haiku 4.5 costs 10 times as much as Haiku 5.5, and Opus 5 costs more than Opus 5.5.

## Where the model is fixed

In a few places the advisor doesn't step in, and you're the one who chooses, just once:

- **Routines**: the model is set in the routine's form. A simple routine (checking, summarizing, alerting) does fine on Haiku.
- **Workflows**: on the workflow card you can change the model of each step before it runs. Put Haiku on the simple steps, like searching or putting results together.
- **Settings > Models**: the model each new chat starts with, in chat and in Code.

Shortcut: **/model haiku** (or sonnet, opus, fable) switches the chat's model without opening the menu.

```experimentar
Translate into Spanish, in a natural and polite way: "Hi, how are you? I'd like to confirm our meeting on Thursday at 3 PM. If you need to change the time, just let me know."
```

After you get the answer on Haiku, use **Generate another response** with Opus and compare the cost below the two. For a short translation, the difference in quality is usually small; the difference in price isn't.
