---
titulo: Memory across conversations
trilha: 2. Make Claude yours
ordem: 12
duracao: 4 min
resumo: How Claude takes notes on what it learns about you, where the notes live, and how to change or delete them.
---

By default Claude doesn't remember one conversation in the next. With **memory turned on**, it starts taking notes on what's worth remembering and checks those notes in later conversations.

## How it works

It works like Claude Code: **one text file per subject** (who you are, how you like your answers, each of your projects) and an **index** (`MEMORY.md`) that lists all of them, one line each.

- At the start of every conversation, Claude receives the index.
- When a subject comes up, it opens the file for that subject.
- When it finds out something useful (or when you say "remember this"), it writes it down or updates it.

Everything stays **on your computer**, in Markdown, and you can see it all in **Settings > Memory**.

## Turn it on

Settings > Memory > **Turn on memory**. It applies to new conversations, in chat and in Code mode.

## See, change and delete

The same screen lists all the memories, with the name, the subject and the text. You can:

- **Edit by hand**: opens the text so you can change it and save.
- **Delete**: gone for good.
- **Ask the memory editor**: write what you want changed in plain words and it makes the change in the right files, keeping everything organized. It runs on Sonnet 5.5 and tells you what changed.

Examples of requests for the editor:

- "I changed jobs: I'm now a designer at an agency. Update what you know about me."
- "Forget everything about my ex."
- "Any duplicate memories? Merge and tidy them up."
- "What do you know about me?"

## In the conversation

You can also ask directly in a conversation:

```experimentar
Remember that I prefer answers in bullet points and that I work in cosmetics sales.
```

```experimentar
Forget what you noted about my trip to Japan.
```

## Be careful

Claude is instructed to never write down passwords, keys, or ID and card numbers. Even so, take a look at the memories from time to time: they are yours and you're in charge of them.
