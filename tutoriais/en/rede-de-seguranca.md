---
titulo: Undo, backup and Git: your safety net
trilha: 8. Using it safely
ordem: 72
duracao: 7 min
resumo: What you can take back in Clave, what you can't, and how to keep everything safe before a big task.
---

Mistakes happen, yours or Claude's. What matters is being able to go back. Clave has several safety nets, and each one catches a different kind of mistake:

| Net | When it helps | The limit |
|---|---|---|
| **Can I do it like this?** | before it starts: you see the plan and decide | only shows up for big tasks |
| **Undo changes** | files Claude created or edited in one answer | doesn't undo what a command did |
| **Windows Recycle Bin** | a file deleted from the Files tab or in File Explorer | a file deleted by a command is gone for good |
| **Git** | any change in the folder, by going back to a saved version | only keeps what you saved in a version |
| **GitHub** | a computer that broke, was stolen or was wiped | only has what you sent |
| **Clave backup** | chats, projects and spending history | attachments, memory and the key are left out |

## Before: the plan

Before touching a lot (creating or changing three files or more, moving, renaming or deleting files, reorganizing a folder), Claude shows a **Can I do it like this?** card with the plan and waits for your answer:

- **Go ahead**: it carries on, and the permissions work as usual;
- **Change the plan**: write in the field what you want different and it redoes the plan;
- **Don't do it**: it stops and asks what you prefer.

This is the best moment to catch a mistake, because nothing has changed yet. It works in any mode, as long as **Ask for OK before big tasks** is on in Settings > Code mode (leave it on). If it went straight ahead and you wanted to see first, ask: "show me the plan before changing anything". **Plan** mode goes further: it only reads and proposes.

## Undo changes

Below each answer that created or edited files you'll see **Undo changes**. It puts that answer's files back the way they were before it: what was edited goes back to the old text, and a file the answer created disappears.

What it **doesn't** bring back is what a [command](#/aprender/glossario/comando) did: moving, renaming, deleting, running a script, installing a program, sending something to the internet. The button can't reach any of that. That's why the card for each command shows what will run first, and a command that deletes always asks for your OK, even in **Auto** mode. Publishing and sending something to the internet ask too, except in Auto.

Details worth knowing:

- Each answer has its own button. To go back several, undo from the last one to the first.
- It puts the file back as it was before the answer. If you changed the file yourself afterwards, your change goes away too.
- If the task is still running, stop it before undoing.
- Want to see what changed before deciding? Open the file in the **Viewer** (click it in the **Files** tab of the [Code panel](#/aprender/painel-do-code)) and click **Claude's changes**: it shows what Claude changed in that file in this chat.
- The button stays in the chat even after you close Clave. Deleting the chat also deletes the chance to undo.
- In chat, nothing is lost: editing your message or generating another answer creates a new version, and the **< 1/2 >** arrows switch between them.

Want to be able to take back what a command is going to do? Ask first:

```experimentar-code
Before moving or renaming anything in this folder, save the list of what will change (from where and to where) in a file called changes.csv and create a script that undoes everything using that list. Only then make the changes.
```

## The Recycle Bin

- A file deleted in Windows File Explorer, or from the **Files** tab of the [Code mode panel](#/aprender/painel-do-code), goes to the **Recycle Bin**. To bring it back: open the Recycle Bin (the icon on the desktop), right-click the file and choose **Restore**.
- A file deleted by a **command** (such as `Remove-Item` or `del`) **doesn't go through the Recycle Bin**: it's gone for good. That's why this kind of command always asks for your OK. Read the card calmly.
- Need Claude to delete something? Ask: "instead of deleting, send it to the Recycle Bin" or "move it to a folder called to-delete, and I'll check and delete it later".
- USB flash drives and network folders have no Recycle Bin: File Explorer deletes for good there, and the **Files** tab doesn't let you delete there at all.

## Git: the folder's history

Undo covers one answer. [Git](#/aprender/glossario/git) covers weeks: it keeps "snapshots" of the folder over time (the [commits](#/aprender/glossario/commit)), and you can go back to any of them.

- Folders created with the [folder template](#/aprender/modelo-de-pasta) already start with Git, if Git is installed on the computer.
- The `.git` folder, where the history lives, already comes on the protected files list: Claude's file tools don't touch it.
- A command that throws changes away (`git reset --hard`, `git clean`) always asks for your OK, even in Auto mode. One that sends to the internet (`git push`) asks in the other modes, but in Auto it goes on its own.

Before a big task:

```experimentar-code
Before any change, save a version of this folder in Git with the message "before the cleanup". If the folder doesn't use Git yet, explain what it is and turn it on first. Show me the commands before running them.
```

When something went wrong:

```experimentar-code
Show me the latest saved versions of this folder in Git and what changed in each one, in simple words. Don't change anything. Then tell me how to bring back the file I choose to one of those versions.
```

The lesson [Git and GitHub for people who have never used them](#/aprender/github) explains it step by step.

## GitHub: the copy outside your computer

Git keeps the history on the computer itself: if the computer breaks, the history goes with it. [GitHub](#/aprender/glossario/github) keeps a copy on the internet, in a **private** repository only you can see. Clave asks for your OK before sending (`git push`), except in Auto mode.

Passwords, keys and personal data do **not** go to GitHub, not even in a private repository. Ask Claude for a `.gitignore` file (the list of what Git leaves out) with your password and key files. See [Passwords, keys and personal data](#/aprender/segredos-e-dados).

## Clave's backup

In Settings > **Data & backup**:

- **Download chat backup**: a file with your chats, projects and spending history.
- **Import backup**: brings everything back, on a new computer, for example.

Attachments, memory and the key don't go in the backup. To keep everything, copy Clave's `dados` folder to an external drive or to the cloud from time to time, with Clave closed. The key and the passwords stored there only open for the same Windows user: on a new computer, paste the key again in Settings > Account & key.

Three more things:

- To keep **one** chat, use its menu (the three dots) > **Export as Markdown**, or type `/export` in it.
- **Deleting a chat can't be undone**, and uninstalling Clave deletes all of them. Download the backup first (see [Updating Clave and backing up](#/aprender/atualizar-e-backup)).
- The backup file has everything you wrote in your chats: keep it somewhere safe.

## Before a big task

1. Save a version in Git (or ask for a copy of the folder, with the date in its name).
2. Keep the mode on **Ask** or **Plan** and read the **Can I do it like this?** card.
3. Ask it to do just a few files first, so you can check.
4. For moving or renaming, ask for the list of what will change.
5. At the end, check the result and save another version.

That's it: if something goes wrong, you know which net to use. The rules that decide what Claude does on its own are in [Permissions](#/aprender/permissoes), and the rest of Clave's security is in [Security and privacy](#/aprender/seguranca-e-privacidade).
