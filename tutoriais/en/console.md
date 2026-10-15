---
titulo: The console: PowerShell inside Clave
trilha: 6. The Code workspace
ordem: 51
duracao: 6 min
resumo: Run a command yourself, already in the work folder, and send the output to Claude only when you need to.
---

The [terminal](#/aprender/glossario/terminal) is the window where you tell the computer what to do by typing, instead of clicking. On Windows, it's called [PowerShell](#/aprender/glossario/powershell). The **Console** tab of the [Code panel](#/aprender/painel-do-code) is a real PowerShell, inside Clave and already open in the work folder.

## What it's for

- **Seeing the result of a command without spending anything.** What runs in the Console doesn't go through the AI.
- **Running a command Claude suggested yourself** and watching it happen.
- **Showing Claude an error** with one click, instead of copying and pasting.
- **Leaving a program running** while you chat.

## Open it

- Click the terminal button at the top of the conversation or press **Ctrl + `` ` ``** (the key to the left of 1).
- The first time, a console opens right away in the work folder. The **+** button opens another one, up to 6 at a time, each in a small tab. Hover over a tab to see which folder it opened in.
- Consoles belong to all of Clave: when you switch tasks, the ones already open stay in the folder where they started. To get one in the current task's folder, click **+**.
- A small dot on a tab means it wrote something new while you were looking at another one.

## Use it

- Type the [command](#/aprender/glossario/comando) and press **Enter**. Two to start with: `dir` lists what's in the folder, and `python --version` shows the Python version.
- The up and down arrows bring back the commands you already typed.
- **Copy**: select with the mouse and press **Ctrl + C**, or right-click.
- **Paste**: **Ctrl + V**, or right-click with nothing selected.
- **Stop a command** that's running: **Ctrl + C** with nothing selected.
- At the top, **Clear the screen** wipes what's in view, and **Restart the console** starts over in the same folder.
- Closing a tab (the X) or restarting while a program without a window runs in it (a server, for example) asks you first, because the program stops midway.

## Send to Claude

The **Send to Claude** button puts what you selected in the console into the text box or, with nothing selected, the last 60 lines. Nothing is sent on its own: you add your question ("what does this error mean?") and send it. Only from that point does that text turn into [tokens](#/aprender/glossario/token).

## The Console and Claude's commands

They're separate things:

- The commands Claude runs **don't show up in the Console**. Each one becomes a step in the conversation ("Ran a command"); click it to see what the command answered.
- The commands it leaves running, like a server, show up in the [Tasks](#/aprender/tarefas-em-segundo-plano) tab.
- Claude **doesn't see your Console**. It only learns what you send with **Send to Claude**.

## Careful: there are no OK cards here

In the Console, you're the one typing, and what you type runs right away. Permission cards, [rules](#/aprender/permissoes) and protected files apply to Claude, not to you. So:

- Don't paste a command you found on the internet without knowing what it does. If in doubt, ask Claude first: "what does this command do?".
- A command that deletes (`Remove-Item`, `del`, `rd`) really deletes, without going to the Recycle Bin.
- Whatever runs without a window in the Console (a server, a long command) stops when you close that tab, or when you close Clave. A program with a window that you opened from there (Notepad, VS Code) stays open, like when you close a Windows Terminal tab. Only if Clave closes suddenly (it crashed or was forced to close) can those programs close with it.

## Simple mode

If Windows doesn't open the full console, you'll see the **Simple mode** notice. Commands work, but without colors, without the arrow keys and without programs that ask questions, and Ctrl + C doesn't stop a command: in that case, use **Restart the console**.

## Try it

```experimentar-code
Give me a PowerShell command that lists the 10 largest files in this folder and its subfolders, with the size in MB. Don't run it: I'll run it in the Console.
```

When the answer arrives, copy the command, open the Console, paste it with **Ctrl + V** and press **Enter**. Then click **Send to Claude** and ask what those files are.
