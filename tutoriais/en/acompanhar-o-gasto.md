---
titulo: Tracking and capping your spending (and 10 habits that save money)
trilha: 5. Saving credit
ordem: 46
duracao: 8 min
resumo: Where to see what you've spent, how to read the numbers, the limits that hold the month in check and the list of this track's 10 habits.
---

Saving gets easy once you can see your spending. Clave adds up the cost of every answer at the official prices and shows it in several places, from the detail of one answer to the whole month. And it has limits so the month doesn't get out of hand, even on a distracted day.

## Where to look

| Where | What it shows |
|---|---|
| Below each answer | the model and what it cost (if it doesn't show up, turn on **Settings > Appearance > Show the cost of each reply**) |
| Below the text box | the gauge with the size of the conversation and what it has cost so far |
| **/cost** | how much this chat and the month have spent |
| The inkwell, in the corner of the left sidebar | how much of the monthly cap is used and the day it resets (click it to open **Usage & spend**) |
| **Your usage**, on the new chat screen | total tokens, day streak, heatmap, favorite model, the month's spending, each model over the last 7 days and the month's forecast |
| **Usage & spend**, in the left sidebar | the whole cycle: per day, per model and per chat |
| **Pricing & plans**, in the left sidebar | the price of each model, your forecast and the **API or subscription?** calculator |

The forecast looks at the pace of the last 14 days and tells you where the month should end up and, if you have a cap, on what day it runs out. You can hide the **Your usage** panel with its X (and bring it back in **Settings > Appearance > Usage panel on the start screen**).

## How to read Usage & spend

**By model** has these columns: **Requests**, **Input**, **Cache read**, **Output**, **Searches** and **Cost**. What each one usually tells you:

| If you see | It's probably | Lesson |
|---|---|---|
| Opus or Fable with most of the cost, on simple tasks | an expensive model doing Haiku's job | [The right model](#/aprender/modelo-certo-mais-barato) |
| High **Output** | long answers and a lot of reasoning | [Reasoning](#/aprender/raciocinio-sem-desperdicio) |
| **Input** high compared with **Cache read** | breaks in long conversations, switching models midway, big attachments | [Lean conversations](#/aprender/conversas-enxutas) |
| Many **Searches** | Web on where it wasn't needed ($0.01 each) | habit 7, at the end of this lesson |
| **Requests** far above the messages you sent | Code steps, workflow steps and routines | [Code mode](#/aprender/code-sem-desperdicio) |

**By chat** shows the 30 that spent the most in the cycle (click to open). If a routine is always at the top, see [Automating without paying the AI every time](#/aprender/automatizar-sem-ia).

**Spend outside Clave this month**: Clave only sees what it spends itself. If the same Anthropic account is used by other programs, add what they spent here (the Anthropic Console shows it) so the cap stays accurate.

## The limits

| Limit | Where | Default | What happens |
|---|---|---|---|
| **Monthly cap** | Settings > Spending limit | the amount chosen the first time you opened Clave | warnings at 50%, 80% and 95%; at the cap, it stops answering until the month resets, or just warns you |
| **Day the month resets** | Settings > Spending limit | day 1 | use the day your credit renews (from 1 to 28) |
| **Per-task cap in Code mode** | Settings > Spending limit | $2 | pauses the task; you send "continue" to keep going |
| **Actions in a row in Code mode** | Settings > Spending limit | 60 | after this many actions (read, edit, run a command) in one message, it pauses; you send "continue" or click Continue |
| **Cap per run** | in each routine's form | | the run stops when it reaches it |
| **Workflow cap** | on the workflow card, before it runs | | the workflow stops if the total goes past it |
| **Limit in the Anthropic Console** | a workspace with a spending limit, and a key from that workspace | | a limit that not even Clave can get past |

In **When the cap is reached**, prefer **Stop replying until the month resets**: with **Just warn and keep going**, the warning shows up, but the spending goes on. While it's stopped at the cap, Clave doesn't run the routines either. The notice tells you the day the month resets; to keep going before that, raise the cap in **Settings > Spending limit**.

**Do you subscribe to Claude Max?** The plan gives monthly API credit ($100 on Max 5x, $200 on Max 20x). Setting the cap to that amount shows you, through the forecast, whether the plan's credit will last the month. The lesson [Your API key and what it costs](#/aprender/chave-da-api) explains how to turn that credit on.

## Five minutes a week

1. Open **Usage & spend** and read the month's forecast.
2. Look at the top 3 in **By chat**: were they worth what they cost?
3. In **By model**, check whether the most expensive model was doing simple tasks.
4. In **Routines**, ask of each one: is it still needed? Could it become a program without AI?
5. Adjust the cap, if the month changed.

```experimentar
These are my Clave expenses this month, copied from the Usage & spend page:

[paste the By model and By chat tables here]

In 6 short bullet points at most, tell me where I'm probably spending more than I need to and what to change. Use these references: Haiku 5.5 costs about 40 times less than Opus 5.5 per message; each web search costs $0.01; a long conversation picked up again after more than 5 minutes pays for the whole conversation again.
```

## The 10 habits that save money

This is the whole track in one list. Come back to it now and then.

1. **Start on Haiku and move up only when you need to.** It costs about 40 times less than Opus; the advisor tells you when the task needs more. [Learn more](#/aprender/modelo-certo-mais-barato)
2. **Reasoning on Low or Medium for everyday work.** Thinking is charged like written text; High and above only for what's hard. [Learn more](#/aprender/raciocinio-sem-desperdicio)
3. **Ask for short answers.** "In 5 lines", "no introduction": about three quarters of the price of a short message is what Claude writes. [Learn more](#/aprender/para-onde-vai-o-credito)
4. **New subject, new chat.** And to continue a long conversation after a break, take a /summary to a new chat instead of going back into it. [Learn more](#/aprender/conversas-enxutas)
5. **Decide the model, the reasoning and Web at the start of the chat.** Changing them in the middle of a long conversation makes the next message pay for everything again.
6. **Edit your message instead of correcting it with another one.** The wrong answer gets out of the way and isn't reread in the following messages.
7. **Send only what matters, and use /web off when nothing current is needed.** One PDF page is worth 1,500 to 3,000 tokens; one search costs the same as about 20 short messages on Haiku.
8. **In Code: name the file, ask for the plan, test on a few and answer the cards right away.** Fewer steps and no pointless rereading. [Learn more](#/aprender/code-sem-desperdicio)
9. **A repeated task becomes a program, not a routine.** The program costs once; the routine costs on every run, forever. [Learn more](#/aprender/automatizar-sem-ia)
10. **Keep the monthly cap on and look at Usage & spend every week.** Spending you can see is spending you can control.
