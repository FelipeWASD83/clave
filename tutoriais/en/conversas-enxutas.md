---
titulo: Lean conversations: new chat, /compact and projects
trilha: 5. Saving credit
ordem: 43
duracao: 7 min
resumo: When a long conversation really gets expensive, how to carry the subject over to a new chat and how to keep projects light.
---

The lesson [Tokens, context and spending](#/aprender/contexto-e-gasto) says a long conversation gets more expensive. That's true, with one detail that changes the strategy: thanks to the [cache](#/aprender/glossario/cache), while you keep replying, rereading the conversation costs little. The bill really jumps at two moments, and that's where it pays to act.

## What the next message costs

An estimate with Clave's prices, for a question of about 200 tokens and an answer of about 500, not counting the reasoning (which adds the same amount in both situations). The size of the conversation is the number the gauge shows below the text box.

| Size of the conversation | Haiku, replying right away | Haiku, after a break | Opus, replying right away | Opus, after a break |
|---|---|---|---|---|
| 10,000 tokens | $0.0004 | $0.0016 | $0.016 | $0.064 |
| 50,000 tokens | $0.0008 | $0.0066 | $0.024 | $0.26 |
| 90,000 tokens | $0.0012 | $0.012 | $0.032 | $0.46 |
| 120,000 tokens | $0.0077 | $0.077 | $0.038 | $0.61 |

Sonnet sits somewhere between the two.

## The two jumps

**1. The break.** The cache keeps the conversation for 5 minutes after the last message. After that, the next message pays for the whole conversation again, plus 25% to store it again. On Opus, with 50,000 tokens, that's the difference between $0.024 and $0.26.

**2. Haiku's 100,000 tokens.** Above 100,000 tokens, Haiku charges 5 times more for everything. Look at the table: from 90,000 to 120,000, the next message becomes 6 times more expensive. And at 120,000, after a break, Haiku ends up costing more than Opus replying right away.

Outside those two moments, splitting doesn't make that much difference: without breaks, 60 exchanges in a single conversation cost about $1.00 on Opus, and the same 60 exchanges in 6 conversations of 10 cost about $0.94 (an estimate). Still, **new subject, new chat**: a long conversation full of subjects also confuses Claude more, and a wrong answer is the most expensive thing there is.

## New chat, /compact or automatic summary?

| | What it does | When to use it |
|---|---|---|
| **New chat** | starts from scratch, with just the instructions | a new subject, or you're coming back after a long time |
| **/summary** + new chat | Claude writes down what was decided, what was done and what's left; you take that to a new chat | a long conversation you want to continue later, on Sonnet or Opus |
| **/compact** | replaces the conversation with a summary, inside the same chat | a long conversation on Haiku, or when you want to keep going in the same place |
| **Automatic summary** | Anthropic summarizes the beginning when the conversation goes past the size you set | a safety net, without you doing anything |

## Carrying the subject over to a new chat

1. Right after an answer (while the cache is still valid), type **/summary** and send it. It becomes a normal request: Claude summarizes the chat in short bullet points with what was decided, what was done (with the files) and what's still left.
2. Copy the summary.
3. Open a new chat and paste it, together with what you want to do now.

Because /summary is an ordinary message, it reads the conversation at the cache price: on Opus, with 50,000 tokens, it comes to around $0.03 (an estimate). After that, the new chat starts out light, and a break in it costs little.

```experimentar
I'm continuing work from another chat. Summary of what has been done:

[paste the summary here]

Now I want: [the next step]. Keep your answer short and don't repeat what's already in the summary.
```

## /compact: handy, but it reads everything at full price

Type **/compact** and Clave asks Anthropic for a summary that keeps what you asked for and how you like things, the decisions, the files that were changed, important numbers and names, what went wrong and what's still pending. A line marks where the chat was compacted (click it to read the summary), and the next messages start from there.

- /compact reads the whole conversation **without the cache discount**. With 50,000 tokens, that's about $0.006 on Haiku, $0.12 on Sonnet and $0.24 on Opus (estimates).
- **On Haiku it's cheap: use it before 100,000 tokens**, so you don't enter the range that costs 5 times more.
- **On Sonnet and Opus**, it pays off when you'll keep working a lot in the same chat, with breaks in between: every break after it costs little. If the idea is just to restart the subject, /summary with a new chat is cheaper.
- It uses the chat's model, only works after at least two messages from you and waits for an answer in progress to finish.
- The summary loses details. If you'll need an exact passage later (a text, a table), copy it first.

## The automatic summary

In **Settings > Features**, **Summarize very long chats** comes turned on: when the conversation goes past the value in **Summarize starting at (tokens)** (default 150,000, between 50,000 and 900,000), Anthropic summarizes the beginning on its own. Each summary is one more call, when it happens.

Do you use Haiku for very long conversations? Lowering that value to 90,000 makes the summary happen before Haiku's 5x range. The trade-off: the setting applies to every model, and the summary loses details earlier.

## Edit instead of correcting

When an answer comes out wrong, the temptation is to send "no, that's not what I meant". But the wrong answer stays in the conversation and is reread with every message after it. Instead, **click the pencil on your message**, make the request clearer and send it again: the wrong answer gets out of the way (it's still kept behind the **< 1/2 >** arrows, but it doesn't go along anymore). The same goes for **Generate another response**.

## Decide at the start

Switching the model, changing the reasoning or turning Web on or off in the middle of a long conversation makes the next message pay for the whole conversation again. Choose at the start. If the conversation changed in nature (from casual chat to heavy analysis, for example), it's time for a new chat.

## Lean attachments and projects

- One PDF page turns into something like 1,500 to 3,000 tokens. To ask about one part, send only that part (copy the passage or save just the pages that matter).
- A [project](#/aprender/projetos)'s files go in at the start of **every new chat** in the project, and are reread with each message. A 40,000-token file (a PDF of about 20 pages) costs, to start each chat, about $0.005 on Haiku, $0.10 on Sonnet and $0.20 on Opus.
- Instead of a whole manual in the project, ask Claude for a one- or two-page fact sheet with what matters and put the fact sheet in the project. The full manual stays for when you really need it.

```experimentar
I'll paste a long document below. Turn it into a fact sheet of one page at most, with only what someone needs to look up day to day (rules, numbers, deadlines, names), in short bullet points. Don't make up anything that isn't in the text.

[paste the document here]
```
