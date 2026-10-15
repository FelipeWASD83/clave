---
titulo: Where your credit goes
trilha: 5. Saving credit
ordem: 40
duracao: 7 min
resumo: What Anthropic charges for each answer, what weighs most on the bill and the spending that happens without you seeing it.
---

The lesson [Tokens, context and spending](#/aprender/contexto-e-gasto) covered the basics: the API charges by [token](#/aprender/glossario/token), and a long conversation gets more expensive. This track goes deeper, with numbers taken from the prices Clave itself uses in its calculations. Start here: to save, you first need to know where the money goes.

## What goes into the bill

Each answer from Claude is charged in four parts:

| Part | What it is | Price |
|---|---|---|
| **Input** | Everything Clave sends: your message, the conversation so far, the attachments, Clave's instructions and the description of the tools | the model's input price |
| **Cache write** | The new part of the conversation, stored so the next message costs less | 1.25 times the input price |
| **Cache read** | The part of the conversation that was already stored | 10 to 40 times less than input, depending on the model |
| **Output** | What Claude writes: the answer, the [reasoning](#/aprender/glossario/raciocinio) (even the part you don't read) and its requests to use tools | 5 times the input price, on every model |

And on top of that: **each web search costs $0.01**, plus the tokens of what it brought back.

## A short message, inside

In the **Price of each model** table (in **Pricing & plans**, in the left sidebar), Clave works out what a typical message costs. For a short message, it assumes 400 new tokens, 3,000 coming from the cache (the instructions and the start of the conversation), 500 stored in the cache, 400 of answer and 300 of reasoning. Here is that calculation on Opus 5.5:

| Piece | Tokens | Cost |
|---|---|---|
| Your message and what's new | 400 | $0.0016 |
| Instructions and history, read from the cache | 3,000 | $0.0006 |
| The new part, stored in the cache | 500 | $0.0025 |
| Answer and reasoning | 700 | $0.0140 |
| **Total** | | **$0.0187** |

About **three quarters of the price is what Claude writes**. On Haiku 5.5 the proportion is similar, only the total is about 40 times smaller: $0.0005.

That gives you the first rule: **a shorter answer and less reasoning save money on any model**. Asking for "answer in 5 lines" or "no introduction" isn't just a matter of taste.

## What Claude rereads with every message

Claude doesn't remember anything on its own: with every message, Clave sends everything again. That includes:

- the whole conversation, with its answers;
- the attachments (a PDF attached at the start goes along with every message after it);
- the [project](#/aprender/projetos) instructions and files, if the conversation belongs to one;
- Clave's instructions and the description of the [tools](#/aprender/glossario/ferramenta): a few thousand tokens before your first word (in Code mode, more than 10 thousand; this is an estimate).

The [cache](#/aprender/glossario/cache) is what keeps this cheap: what was already sent before costs 10 to 40 times less. But it has an expiry.

## The 5-minute window

The cache keeps the conversation for **5 minutes** after its last use, and each message renews that window. If you stop for longer (you went to lunch, you joined a meeting), the next message pays for the whole conversation again, at 1.25 times the input price, to store it all over again.

An example on Opus 5.5, in a 50,000-token conversation (the gauge below the text box shows this number): the next message costs about $0.024 if you reply right away and about $0.26 after a break. Ten times more for the same message. The lesson [Lean conversations](#/aprender/conversas-enxutas) has the full table and what to do about it.

The same happens when you **switch the model, change the reasoning or turn Web on or off** in the middle of a long conversation: what was stored stops counting, and the next message pays for everything again.

## The spending you don't see

Some things spend without showing up as an answer on the screen:

- **Model advisor**: Haiku reads the chat at the 1st message and then every 5. Each check is short and has no reasoning; at Haiku's price, it comes to around $0.0003 (an estimate).
- **Automatic titles**: Haiku names the chat, once per chat (a fraction of a cent).
- **Web search**: $0.01 per search, plus the page excerpts it brings, which go into the conversation and are reread in the following messages. A single search costs the same as about 20 short messages on Haiku.
- **Summarizing the chat**: the automatic summary and /compact are one more call, which reads the whole conversation.
- **Code mode**: each step (reading a file, running a command) is a new request to the API, which rereads the whole task. A 20-step task is 20 requests.
- **Workflows**: each step is a hidden conversation. The workflow card shows the estimate before it runs.
- **Routines**: each run is a new conversation, every day, for as long as the routine is on.
- **Helpers**: the lesson helper uses Haiku, and the memory editor uses Sonnet.

None of this is expensive once. What adds up is whatever repeats many times: routines, searches and Code steps.

## Where every cent shows up

- **Below each answer**: the model and what it cost (if it doesn't show up, turn on **Settings > Appearance > Show the cost of each reply**).
- **Below the text box**: the gauge with the size of the conversation and what it has cost so far.
- **/cost**: type it in the text box to see how much this chat and the month have spent.
- **Usage & spend**, in the left sidebar: spending per day, per model and per chat.

The lesson [Tracking and capping your spending](#/aprender/acompanhar-o-gasto) explains how to read each of them.

## Expensive and cheap, side by side

| Usually expensive | Usually cheap |
|---|---|
| A simple question on Opus or Fable | The same question on Haiku, about 40 times less than on Opus |
| A long answer you won't read all the way through | "Answer in 5 lines" |
| Going back to a long conversation after a break | A new chat with a summary of what matters |
| A whole PDF attached to ask about one page | Just the page that matters |
| A routine that calls Claude every hour | A program without AI, built once ([see how](#/aprender/automatizar-sem-ia)) |
| Web on in a chat that doesn't need anything current | **/web off** |

Each row of that table becomes a lesson in this track: [the right model](#/aprender/modelo-certo-mais-barato), [reasoning](#/aprender/raciocinio-sem-desperdicio), [lean conversations](#/aprender/conversas-enxutas), [Code mode](#/aprender/code-sem-desperdicio), [automating without AI](#/aprender/automatizar-sem-ia) and [tracking your spending](#/aprender/acompanhar-o-gasto).

```experimentar
Do the math in a short table, without a long explanation. On Haiku 5.5, input costs $0.10 per million tokens and output $0.50. On Opus 5.5, input costs $4 and output $20. How much would 30 questions a day cost per month on each, with each question using about 3,000 input tokens and 700 output tokens?
```
