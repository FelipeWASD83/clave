---
titulo: Models and reasoning: which to choose
trilha: 1. First steps
ordem: 5
duracao: 5 min
resumo: Opus, Sonnet, Haiku and Fable, what each one costs and when it's worth thinking harder.
---

In the text box, the first button picks the [model](#/aprender/glossario/modelo) and the second one picks the [reasoning](#/aprender/glossario/raciocinio). Both change the quality, the speed and the price.

## The models

| Model | What it's for | Price per million tokens (input / output) |
|---|---|---|
| **Opus 5.5** | The smartest for everyday use. Good at everything, including code and analysis. | $4 / $20 |
| **Sonnet 5.5** | Almost as good as Opus, faster, half the price. | $2 / $10 |
| **Haiku 5.5** | Very fast and very cheap. Great for simple questions, summaries and for learning. | $0.10 / $0.50 |
| **Fable 5.1** | Very long reasoning and creative writing. The most expensive. | $10 / $50 |

"Input" is what you send (message, attachments, the earlier conversation); "output" is what it writes. A million tokens is a lot of text: something like 700,000 words.

Watch out with Haiku 5.5: when a request goes over 100,000 input tokens (a very long chat or a big attachment), that whole request costs 5 times more.

**Rule of thumb:** start on Haiku for simple things and on Opus for what matters. If Haiku gets it wrong, generate another answer and pick Opus (circular arrow menu).

## The model advisor

Clave starts on **Haiku 5.5**, the cheapest one. Since version 5.0 it's the default for everyone, including people who already used Clave: after updating, a notice shows up once with the model you used before and the **Keep Haiku** and **Go back to the previous one** buttons. So you don't have to guess, Haiku itself reads the chat at the first message and then every 5 and says which model does that task for the lowest price: a note shows up like "For this task, Sonnet 5.5 should do better", with the reason and the **Use** and **Keep** buttons. Each check costs a fraction of a cent.

If you prefer, let Clave **switch on its own** (Settings > Models > Let Clave switch the model on its own): it switches, tells you and shows a button to go back. In a chat where you go back, it stops switching. You can turn the advisor off there too.

To choose by the lowest price without losing quality, see [The right model for the lowest price](#/aprender/modelo-certo-mais-barato).

## Reasoning

Before answering, Claude can think. The levels are **Low**, **Medium**, **High**, **Extra high** and **Max**:

- **Low**: fast and cheap. Chatting, direct questions, short texts.
- **Medium**: the balance. A good default for almost everything.
- **High** or above: hard problems, math, planning, complicated code. Takes longer and costs more.

On Haiku and Sonnet you can **turn thinking off** (it gets faster). On Opus and Fable it always thinks a little; the level controls how much.

**Show reasoning** displays a summary of what it thought, in a little box that opens and closes. It doesn't change the price.

**Fast mode** (Opus only) answers up to 2.5 times faster, at double the price.

When it's worth paying for it to think more: [Reasoning: when it's worth paying for it to think](#/aprender/raciocinio-sem-desperdicio).

## What if it refuses?

The models have safety filters. Sometimes a normal request gets refused by mistake: in that case Clave asks Anthropic to try again with another model (you can turn this off in Settings > Features). If it still refuses, rephrase your request.

```experimentar
I have $2,000 saved up and I want to start investing, but I don't understand any of it. Explain the safest options for beginners, without recommending any specific product.
```
