---
titulo: For studying
trilha: 9. Recipes by area
ordem: 80
duracao: reference
resumo: Summaries, flashcards, practice questions, simple explanations and a study plan, each with the cheapest model that can handle it.
---

Ready-made requests for studying with Claude. Click **Send to a new chat**: the request goes into the text box, and you replace what's in square brackets before sending.

Each recipe says what Claude will do, the [model](#/aprender/glossario/modelo) that's enough (the cheapest one that works) and when another Clave tool does a better job. Clave starts on **Haiku 5.5**, the cheapest, and it handles almost everything here. When a task needs more, the model advisor tells you (see [The right model for the lowest price](#/aprender/modelo-certo-mais-barato)).

| Recipe | Where | Model |
|---|---|---|
| Summary of a text | chat | Haiku (Sonnet for long, hard material) |
| Flashcards in a spreadsheet | chat | Haiku |
| Practice questions | chat | Haiku |
| Explain it like I'm a child | chat | Haiku, no thinking |
| Study plan on a timeline | chat, with a widget | Haiku |
| Correct your essay | chat | Haiku (Sonnet for deeper feedback) |
| Research for an assignment | chat or workflow | Haiku |
| One review a day | routine | Haiku |

## 1. Summary of a text or chapter

Attach the PDF (or photos of the pages) and send:

```experimentar
Summarize the text I attached so I can study for the test. I want: the 5 main ideas, one sentence each; the new terms, with a short explanation; and 3 questions a teacher would ask about it. Use only what is in the text and tell me if any part was confusing.
```

- **What it does:** reads the whole attachment and gives you the summary in the format you asked for. The "use only what is in the text" part matters: that way it tells you when the text doesn't say something, instead of filling it in from memory.
- **Model:** Haiku is enough for a chapter. Long, hard material (a scientific paper, a whole book) does better on Sonnet, and the advisor usually suggests the switch.
- **Good to know:** the attachment is read again with every message in the chat. Send only the chapter you're going to study and start a new chat for the next one (see [Lean chats](#/aprender/conversas-enxutas)). And once the chat goes over 100,000 [tokens](#/aprender/glossario/token) (a whole book easily does), Haiku charges 5 times its normal price for that reply.

## 2. Flashcards in a spreadsheet

```experimentar
Create a flashcard spreadsheet about the digestive system, high school level. Columns: Front (the question), Back (the answer, in two lines at most) and Topic. Make 30 cards, from easiest to hardest.
```

- **What it does:** creates the Excel [spreadsheet](#/aprender/glossario/planilha) and shows a card with **Download** and **Open**. Attached your own material? Say "use only the attached text" and the cards come from what your teacher covered.
- **Model:** Haiku is enough.
- **Best tool:** want to take the cards to a flashcard app that imports CSV (like Anki)? Open the spreadsheet in Excel and save it as CSV. Want to practice right on the screen? Ask for "an HTML flashcard page that flips the card when I click": it opens in the **Preview**, next to the chat (see [Build web pages and small apps](#/aprender/paginas-e-apps)).

## 3. Practice questions

```experimentar
I want to practice for a biology test about the cell, high school level. Ask one question at a time, multiple choice, with 4 options. Wait for my answer, tell me if I got it right, explain why in two lines and only then move on to the next one. After 10 questions, tell me which topic I need to study more.
```

- **What it does:** becomes a private tutor who corrects you on the spot and, at the end, points out your weak spots.
- **Model:** Haiku is enough. Exercises with math (math, physics, chemistry) go wrong less often with [reasoning](#/aprender/glossario/raciocinio) on **Medium** or higher: thinking first helps with the arithmetic.
- **Best tool:** prefer a practice test to do on paper? Ask for "20 questions in a spreadsheet, with the answer key on another sheet".

## 4. Explain it like I'm a child

```experimentar
Explain what inflation is as if I were 10 years old. Use an everyday example, 6 sentences at most, and end with a question to check that I understood.
```

- **What it does:** swaps the jargon for a simple comparison. Got it? Ask "now explain it again, as if to an adult who has a test coming up", and the level goes up step by step.
- **Model:** Haiku, with no thinking: in the second button of the text box, uncheck **Think before responding**. The answer comes faster and cheaper, and a short explanation doesn't need it.
- **Best tool:** if you always want explanations like this, write it once in **Settings > Personalization** (see [Teach Claude about you](#/aprender/sobre-voce-e-estilos)).

## 5. Study plan on a timeline

```experimentar
I have a history exam in 4 weeks and can study 1 hour a day, Monday to Friday. The topics are: the Industrial Revolution, the French Revolution, American Independence and the Napoleonic Era. Build a plan with a review at the end of each week and a light day before the exam, and show the plan on a timeline.
```

- **What it does:** spreads the topics over the days and draws a timeline in the chat. That card is a **widget**: a drawing Claude puts together when it helps more than text. Widgets are on by default (the switch is in **Settings > Features > Widgets**).
- **Model:** Haiku is enough.
- **Best tool:** want to tick off what you've studied? Also ask for "the same plan in a spreadsheet, one row per day, with a Done column".

## 6. Correct your essay (without writing it for you)

```experimentar
Correct my essay below, but don't rewrite it for me. Point out the grammar mistakes, the confusing sentences and where the argument is weak, quoting the passage for each problem. At the end, give me 3 tips for next time.

Essay: [paste it here]
```

- **What it does:** lists each problem with its passage, and you do the rewriting. That's how you learn (and it's what most schools accept: follow your school's rules on AI).
- **Model:** Haiku is enough for grammar and clarity. For deeper feedback on argument and structure, Sonnet does better.
- **Best tool:** just want the corrected text, without the lesson? The `/writing:review` command followed by the text fixes grammar and clarity without changing the meaning (see [Plugins and slash commands](#/aprender/plugins-e-comandos)).

## 7. Research for an assignment, with sources

```experimentar
I'm doing a school assignment on solar energy. Search the web and bring me: a 10-line summary of the subject, 5 important facts with the source for each one, and 3 reliable websites for me to read. Give the date of the information and point out where the sources disagree.
```

- **What it does:** searches the web (search is on by default), reads the pages and cites the sources. Each search costs $0.01, on top of the tokens of the pages it reads.
- **Model:** Haiku is enough.
- **Best tool:** a big subject? Type `/workflow` and pick **Deep research**: three Haiku models research different angles at the same time and a Sonnet puts it all together with the sources. It shows the cost estimate and only runs after your OK (see [Workflows](#/aprender/fluxos-e-agentes)).
- **Watch out:** Claude can be wrong and can even make up a source (this is called a [hallucination](#/aprender/glossario/alucinacao)). Open the links before you cite them, and write the assignment yourself.

## 8. One review a day, on its own

A [routine](#/aprender/rotinas) sends a request at the time you choose, without you opening anything.

1. In the left sidebar, **Routines** > **New routine**.
2. In **What to do**, write the complete request, with the topics inside it:

   ```
   I'm a high school student. Ask me 5 short review questions, one on each topic below, and put the answers at the end, after a line that says "Answers". Topics: the cell, photosynthesis, the French Revolution, linear equations, figures of speech.
   ```

3. In **When**, choose **Every day** and the time. In **Model**, choose **Haiku 5.5**. In **Cap per run**, set a low value, like $0.05.
4. Click **Run now** to test it.

- **What it does:** each run becomes a chat in the left sidebar, and a notification tells you when it's ready.
- **Model:** Haiku is enough. A run like this usually costs less than one US cent (this is an estimate).
- **Good to know:** the routine doesn't read your other chats. Everything it needs to know (here, the topics) goes in the request itself: update the list when the subject changes.

## Tips for studying with Claude

- **One project per subject:** instructions ("I'm in 11th grade, explain with everyday examples") and the subject's material as files. See [Projects](#/aprender/projetos).
- **New subject, new chat:** it's cheaper and Claude gets less confused.
- **Ask "how did you get that?"** when an answer looks odd.
- **It helps you learn, it doesn't replace your teacher:** take whatever doubts are left to class.
