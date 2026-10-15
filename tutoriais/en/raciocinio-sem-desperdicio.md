---
titulo: Reasoning: when it's worth paying for it to think
trilha: 5. Saving credit
ordem: 42
duracao: 5 min
resumo: Thinking is charged like written text. What it costs, when to raise the level, when to turn it off and when fast mode is worth it.
---

Before answering, Claude can think: plan, check the math, compare options. That thinking is charged **at the output price**, just like the answer, even when you don't read it. Turning on **Show reasoning** only shows a summary of it: the price is the same whether it's shown or not.

## What thinking costs

Thinking is measured in [tokens](#/aprender/glossario/token), like the answer. Here is what just the thinking part costs, at a few sizes:

| Reasoning tokens | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 | Fable 5.1 |
|---|---|---|---|---|
| 1,000 | $0.0005 | $0.01 | $0.02 | $0.05 |
| 5,000 | $0.0025 | $0.05 | $0.10 | $0.25 |
| 20,000 | $0.01 | $0.20 | $0.40 | $1.00 |

For comparison: the answer to a short message is about 400 tokens. Long reasoning can cost far more than the answer itself.

Reasoning is adaptive: Claude decides how much to think, and the level you choose pushes that up or down. That's why the same level can be cheap on an easy question and expensive on a hard problem.

## The levels and the defaults

The second button in the text box picks the level: **Low**, **Medium**, **High**, **Extra high** and **Max**. Clave starts on **Medium** in chat and on **High** in Code mode (you can change this in **Settings > Models**). In the menu, each model's default is marked with "(model default)".

- On **Haiku** and **Sonnet** you can turn it off: uncheck **Think before responding**. It answers faster and costs less (with thinking off, the level goes up to High).
- On **Opus** and **Fable** it always thinks a little. To spend less, lower the level.

## When it's worth paying

A guide to get started (adjust it to your case):

| Task | Reasoning |
|---|---|
| Chatting, a direct question, a translation, a short e-mail, a summary | Low, or off on Haiku and Sonnet |
| Everyday work in general | Medium |
| Math, planning, comparing several options, code with a tricky bug | High |
| A hard problem where a mistake is costly | Extra high or Max, preferably in a chat just for that |

## Do this instead of that

- **Instead of moving up a model, raise the reasoning first.** Haiku got a calculation wrong? Switch the reasoning to **High**, click the pencil on your message and send it again. Thinking on Haiku is so cheap (5,000 tokens cost $0.0025) that it comes out cheaper than a single short message on Sonnet ($0.0094). If it still gets it wrong, then move up the model, as [The right model for the lowest price](#/aprender/modelo-certo-mais-barato) shows.
- **Instead of Max "just in case", use Medium and check.** Max has no reasoning limit: on a simple task, it just spends more.
- **In Code mode, mechanical work doesn't need High.** Renaming, moving or merging files: Medium or Low. Save High for code and tricky bugs. See [Code mode without waste](#/aprender/code-sem-desperdicio).
- **A hard problem in the middle of a light chat?** Open a new chat with a high level just for it, instead of making the whole conversation think hard.

## Choose at the start

Changing the level, or turning thinking on or off, in the middle of a long conversation makes the next message pay for the whole conversation again (the cache stops counting). In a short chat this barely matters; in a long one, choose at the start or open a new chat for the hard part.

Shortcut: **/effort low** (or medium, high, xhigh, max) changes the level without opening the menu.

## Fast mode

On **Opus**, the reasoning menu has **Fast mode**: it answers up to 2.5 times faster, **at twice the price**. It's worth it when you're sitting there waiting for the answer to get on with urgent work. The rest of the time, leave it off. Like changing the level, turning fast mode on in the middle of a long conversation also makes the next message pay for everything again.

```experimentar
A product cost $80. It got a 10% discount and then another 15% discount on the new price. What is the final price, and what single discount would be equivalent? Show the math in a few lines.
```

Send it first with the reasoning on **Low**. Then switch to **High**, click the pencil on your message and send it again. Compare the cost below the two answers and see whether the answer changed.
