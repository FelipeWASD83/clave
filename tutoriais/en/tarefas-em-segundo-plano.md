---
titulo: Background tasks and local servers
trilha: 6. The Code workspace
ordem: 53
duracao: 7 min
resumo: What keeps running while you do something else, how to follow and stop it, and what localhost and a port are.
---

"In the background" means anything that keeps running while you do something else: a long reply that's still coming in, a [workflow](#/aprender/fluxos-e-agentes) with several steps, a [routine](#/aprender/rotinas), the download of a lesson video, or a command Claude left running, like a website's server.

## The Tasks tab

It shows all of that in one place. To open it:

- **Ctrl + Shift + Y**, or the Tasks button at the top of any conversation (in chat too);
- or the **1 running** counter (or 2, 3...) in the left sidebar, below **New Code task**. It only shows up when something is running.

The tab has two lists: **Running now** and **Recently finished** (which stay there for 30 minutes). Each card shows:

- the type (**Reply**, **Workflow**, **Routine**, **Command** or **Download**), how long it has been running and which conversation it came from; for replies, workflows and routines, also how much it has spent;
- the status: **Running**, **Waiting for your OK**, **Completed**, **Failed** or **Stopped**;
- for a workflow, how many steps are done; for a download, the percentage;
- for a command, the actual command and, if it's a server, its address with an **Open in browser** button;
- the **Stop**, **View log** (what the task has written so far) and **Go to the conversation** buttons, the last one when the task belongs to another conversation.

When a task that took more than 30 seconds finishes while you're in another conversation or another program, Clave lets you know. With its window in the background, you also get a Windows notification (you can turn it off in **Settings > Appearance > Windows notifications**).

## Commands that keep running

Usually, when Claude runs a [command](#/aprender/glossario/comando), it waits for the command to finish (the limit is 2 minutes, and it can raise it to 10) and reads the result. But some commands never finish on their own: a website's server, for example, stays on until someone turns it off. For those, Claude leaves the command **in the background**:

- the permission card says **Leave running in the background** and shows the command;
- the step in the conversation shows the command with "(in the background)", and the reply carries on without waiting;
- the command shows up in the Tasks tab as **Running**, until someone stops it;
- Claude can check what the command wrote ("Checked a background command") and stop it ("Stopped a background command") without asking for your OK;
- there can be at most 5 per conversation;
- **Clave stops all of them when it closes.** Nothing keeps running hidden on your computer afterwards. A program with a window that the command opened (an editor, the browser a server opens by itself) stays open, in plain sight, for you to close when you want.

Starting a command like this follows the permission mode, like any other command: it asks for your OK in **Ask** and **Accept edits**, runs on its own in **Auto** and doesn't run in **Plan**.

It also works for a slow job, like converting a lot of files: ask it to "run it in the background" and keep chatting. The tab lets you know when it's done.

## Stopping

- In the Tasks tab, **Stop** ends the command and whatever it opened without a window. A program with a window that it opened (VS Code, Notepad, the browser a server opens) stays open. The card moves to **Recently finished**, as **Stopped**.
- Or ask Claude: "stop the server".
- Or close Clave: it stops all of them, with the same care for windows. Only if Clave closes suddenly (it crashed or was forced to close) can the programs with a window close with it.

**Stop** also works on a reply, a workflow or a routine that's still running. A workflow stops together with the reply that started it.

## Local servers, in plain words

- A [server](#/aprender/glossario/servidor) is a program that waits for requests and answers them. A website server hands the pages to the browser.
- [Localhost](#/aprender/glossario/localhost) is your own computer. `http://localhost:8000` is a website that only exists there, and only you can see it.
- A [port](#/aprender/glossario/porta) is the number after the colon. Each server uses one, and two can't use the same one at the same time: that's the "port in use" error.

Why does a website that's already in your folder need a server? Clave's browser only opens `http` and `https` addresses, and some parts of a website only work when it arrives that way. For a simple website, a command like `python -m http.server 8000` is enough; bigger projects, built with [Node.js](#/aprender/glossario/node-js), usually use `npm run dev`. Claude picks the right one for each folder.

A running server doesn't spend credit: it just hands pages to your browser. It only costs something when Claude reads what it wrote or opens the page.

## Local: what's running on your computer

In the [browser](#/aprender/navegador), the **Local** button (and the browser's start screen) lists the servers running on your computer right now: the ones Claude's commands started, with the command's name, and the ones from other programs, like one you started yourself in the [Console](#/aprender/console). One click opens one. Something that answers but isn't a web page shows up with the note "answers, but is not a web page (maybe an API)".

A server you started in the Console doesn't show up in the Tasks tab, because Claude didn't start it. It stops with **Ctrl + C** in that console, or when you close its tab.

On a command's card, **Open in browser** opens the address in the Browser tab when you're in a Code task, and in your computer's browser when you're in a chat.

## Try it

```experimentar-code
Run a PowerShell command in the background that counts from 1 to 60, one number per second, and writes "done" at the end. Don't create or change any files.
```

If the **Leave running in the background** card shows up, click **Allow**. Then open the **Tasks** tab with **Ctrl + Shift + Y**. Click **View log** to watch the numbers come in. Let it finish to see the card move to **Recently finished**, or click **Stop** before that.

The lesson [A website from scratch to the browser](#/aprender/site-do-zero-ao-navegador) does the same with a real server.
