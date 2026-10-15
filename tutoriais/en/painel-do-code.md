---
titulo: The Code panel: files, viewer, console, browser and tasks
trilha: 6. The Code workspace
ordem: 50
duracao: 6 min
resumo: Your workbench next to the chat: see the folder, open files, run commands, use the browser and keep an eye on what's running.
---

In [Code mode](#/aprender/modo-code), Claude works in a folder on your computer. The **Code panel** is your workbench next to the chat: you can see the files it created, open each one, run a command yourself, look at a website and keep an eye on whatever is still running, without leaving Clave. Everything you do in the panel, without asking Claude, costs no credit.

## Open, close and resize

- At the top of the conversation, on the right, are the panel buttons, one icon per tab. Hover over one to see its name and shortcut.
- **Ctrl + J** opens and closes the panel, on the last tab you used.
- **Drag the panel's edge** to make it wider or narrower. **Double-click the edge** to go back to the default width.
- Closing the panel doesn't lose anything: the console keeps what it ran, and whatever was running keeps running.
- If you leave the panel open, your next Code task opens with it already there.

## The tabs

| Tab | What it's for | Shortcut |
|---|---|---|
| **Files** | the whole work folder, as a tree | Ctrl + Shift + E |
| **Viewer** | shows the file you pick: code, text, image, PDF, spreadsheet, Word, audio and video | double-click a file |
| **Console** | the real [PowerShell](#/aprender/glossario/powershell), already open in the folder | Ctrl + `` ` `` (the key to the left of 1) |
| **Browser** | a [browser](#/aprender/glossario/navegador) that you and Claude use together | Ctrl + Shift + L |
| **Tasks** | what's running in the background, with a **Stop** button | Ctrl + Shift + Y |

In a regular chat, the panel only has the Tasks tab (and the **Preview**, when you open a page Claude wrote).

## Files: the folder in plain sight

- Click a folder to expand it. **Double-click** a file to open it in the Viewer.
- The box at the top filters by name. **Enter** searches every subfolder.
- **Right-click** an item: open it with the default program, show it in File Explorer, copy its [path](#/aprender/glossario/caminho), **Mention in the conversation**, rename it (F2), create a file or folder, and **Send to the Recycle Bin** (Delete). Whatever goes to the Windows Recycle Bin can be restored from there.
- **Drag a file** into the text box: its path goes into your request, and you finish the sentence ("improve `index.html`").
- Whatever Claude changed in this conversation is marked **changed by Claude**. A padlock shows the protected files (Settings > Code mode), which Claude doesn't read.
- System folders, such as `.git` and `node_modules`, are hidden. The eye button shows them.
- The list updates on its own when something changes in the folder.
- Opening a program or script (`.exe`, `.bat`, `.ps1`...) with the default program asks you first, because opening it runs it.

## Viewer: read without spending

- Opens up to 8 files, in small tabs at the top.
- Code with colors and line numbers; Markdown formatted or as code; spreadsheets (the first 200 rows and 50 columns; to see everything, open it in Excel); Word (text only); images, PDF, audio and video.
- **Ctrl + F** searches inside the file. Type `:` and a number (`:120`) to jump to that line.
- **Claude's changes**: on a file it touched in this conversation, shows the before and after (red went away, green came in).
- On an [HTML](#/aprender/glossario/html) page, **View as a page** opens it in the Preview. Files outside the page (the CSS, the images) may not show there; to see the whole website, use the [browser with a local server](#/aprender/site-do-zero-ao-navegador).
- In the conversation, clicking a file name in a step ("Read", "Wrote", "Edited") opens it here.
- A protected file: you can click **Show anyway**. You see it; Claude still doesn't read it.

Reading a file in the Viewer costs nothing. Asking Claude to "open it and show me" costs money, because it reads the whole file and then writes an answer.

## Console, Browser and Tasks

Each of these tabs has a lesson of its own:

- **Console**: PowerShell, already in the folder, so you can run a command without asking Claude. The **Send to Claude** button takes the output to the text box. See [The console](#/aprender/console).
- **Browser**: a real browser that Claude also uses to check a website. Outside Auto mode, each new site asks for your OK the first time in each task (your own computer, `localhost`, doesn't ask), and clicking and typing on a site ask for your OK every time. See [The browser](#/aprender/navegador).
- **Tasks**: replies still coming in, workflows, routines, servers Claude left running and downloads, with a **Stop** button. When something is running, a counter also shows up in the left sidebar, below **New Code task**. See [Background tasks](#/aprender/tarefas-em-segundo-plano).

And the lesson [A website from scratch to the browser](#/aprender/site-do-zero-ao-navegador) uses all of them together, from start to finish.

## The tour arrows

The first few times you open Code mode, Clave shows arrows over the panel buttons. Want to see them again? In **Learn**, click **Take the tours again**.

## Try it

```experimentar-code
Create a file called tips.txt in this folder with five short tips for organizing files on a computer. Then tell me where it is.
```

When it's done, press **Ctrl + J**, open the **Files** tab and double-click `tips.txt`. Then click **Claude's changes** to see what it created in this conversation.
