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

**Rule of thumb:** start on Haiku for simple things and on Opus for what matters. If Haiku gets it wrong, generate another answer and pick Opus (circular arrow menu).

## Reasoning

Before answering, Claude can think. The levels are **Low**, **Medium**, **High**, **Extra high** and **Max**:

- **Low**: fast and cheap. Chatting, direct questions, short texts.
- **Medium**: the balance. A good default for almost everything.
- **High** or above: hard problems, math, planning, complicated code. Takes longer and costs more.

On Haiku and Sonnet you can **turn thinking off** (it gets faster). On Opus and Fable it always thinks a little; the level controls how much.

**Show reasoning** displays a summary of what it thought, in a little box that opens and closes. It doesn't change the price.

**Fast mode** (Opus only) answers up to 2.5 times faster, at double the price.

## What if it refuses?

The models have safety filters. Sometimes a normal request gets refused by mistake: in that case Clave asks Anthropic to try again with another model (you can turn this off in Settings > Features). If it still refuses, rephrase your request.

```experimentar
I have $2,000 saved up and I want to start investing, but I don't understand any of it. Explain the safest options for beginners, without recommending any specific product.
```
