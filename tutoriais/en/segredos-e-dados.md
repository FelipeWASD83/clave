---
titulo: Passwords, keys and personal data: what never to paste
trilha: 8. Using it safely
ordem: 71
duracao: 7 min
resumo: The API key, passwords, cards and documents: what goes to Anthropic, what stays on your computer and how to work without exposing anything.
---

Everything you write or attach in a chat goes to Anthropic (that's how Claude answers) and is saved in the conversation, on your computer. For almost everything, that's great. For passwords, keys and card numbers, it isn't.

## What never to paste in a chat

- Your [API key](#/aprender/glossario/chave-da-api) and any other key or [access token](#/aprender/glossario/token-de-acesso).
- Passwords for any account, including your e-mail app password.
- Card numbers, security codes, banking passwords, codes you got by text message.
- Full documents belonging to other people (ID cards, Social Security numbers, medical results, contracts), unless you really need to.

Why:

- it goes to Anthropic along with the message;
- it's saved in the conversation, in a regular file on your computer, without the [encryption](#/aprender/glossario/criptografia) that protects the key;
- it ends up in the chat backup and in the exported conversation;
- with [memory](#/aprender/memoria) turned on, it can become a note;
- and Claude doesn't need it: there's a better way to sign in to a service (see below).

**Pasted one by mistake?** Change the password (or delete the key in the Console, as explained below). Deleting the chat removes the text from Clave, but it has already been sent, and any backups you downloaded before still have it.

## The API key

In Settings > Account & key, Clave keeps the key encrypted by Windows, tied to your user: copied to another computer, it won't open.

- Never show the key: no screenshots, messages, e-mails, websites, scripts or GitHub. Whoever has the key spends your credit.
- A key that ended up in a public GitHub repository has leaked, even if you delete it later: [Git](#/aprender/glossario/git) history keeps the old versions.
- **Did it leak?** Go to the Anthropic Console (platform.claude.com), open **API Keys** and delete the key. Create another one and paste it in Settings > Account & key > **Paste a new key** > **Check and save**.
- Use the **monthly cap** (Settings > Spending limit) and, for an extra safeguard, a workspace with a spending limit in the Console. The lesson [Your API key](#/aprender/chave-da-api) explains how, and [Tracking and capping your spending](#/aprender/acompanhar-o-gasto) shows how to notice strange spending.

## Passwords a program needs

Sometimes an automation needs to sign in to your e-mail or a website. The password doesn't go in the chat or inside the code: it goes into the **Windows Credential Manager**, the password vault that already comes with Windows. You type the password once, in a window of the program itself, and the program takes it from there.

```experimentar-code
I'm going to need a website password in a script in this folder. Don't ask me for the password here in the chat. Store the password in the Windows Credential Manager (keyring library), create a setup.bat that asks for the password in a window, and make the script read it from there. Never write the password to a log or on the screen.
```

The lesson [An order app without AI](#/aprender/app-de-pedidos-sem-ia) shows this approach in a complete example, and [Automating without paying the AI every time](#/aprender/automatizar-sem-ia) explains when a program like that is worth it.

## Passwords Clave keeps

- **E-mail** (Settings > Connectors > E-mail): use an **app password**, a password just for Clave that you can delete whenever you want, never your normal password. It's stored encrypted on this computer, only for the e-mail.
- **GitHub** and **connectors**: the token is also stored encrypted and is only used to sign in to its own service.
- **Zapier**: allow only the actions you need.
- **Code browser**: the sites you sign in to through it stay signed in. **Delete the browser data** (Settings > Code mode) deletes those logins and cookies.
- **Sign out** (Settings > Updates & about) deletes the key, all of these passwords and the Code browser's data from this computer.

## Cards and shopping

Claude never needs your card number. In the Code mode browser, it can open and read a store's pages, but **passwords, access codes and cards are typed by you**: Clave doesn't let Claude fill in those fields. When it's time to pay or sign in to an account, it asks and you take over.

## Protected files in Code mode

In Settings > Code mode there's the **Protected files and folders** list. It already comes with the most common password and key files programmers use (`.env`, `*.key`, `*.pem`, `*.pfx`, the `.ssh` and `.aws` folders) and with the `.git` folder, where Git history lives.

- File tools **never** read or change anything on the list.
- A command that mentions one of these files **always** asks for your OK.
- Add anything sensitive there, one per line: `passwords.txt`, `documents/**`.

The list protects you well against mistakes, but a command can't know everything it will touch. The safest way is to keep passwords and documents **outside the working folder**: in Code mode, the file tools ask for your OK every time they read or change anything outside it (except in **Auto** mode, which doesn't ask), unless one of your [permission rules](#/aprender/permissoes) allows it.

## Personal data and documents

Before sending a customer spreadsheet, a contract or a medical result, think about what Claude really needs:

- replace names with "Customer 1", "Customer 2";
- remove the ID number, phone and address columns if the question is about sales;
- send only the page of the contract that matters;
- in a screenshot, crop out what isn't relevant.

```experimentar
I want to send you a customer spreadsheet so you can analyze this year's sales. Which columns should I remove or replace first, so I don't expose personal data, without ruining the analysis?
```

Code mode has a trick: a [script](#/aprender/glossario/script) that runs on your computer handles the data **without sending anything to Anthropic**. Only what Claude reads or what the command shows on the screen goes out. So ask for a program that does the job without showing the data:

```experimentar-code
Create a script that makes a copy of customers.xlsx called customers-no-data.xlsx, replacing the names with Customer 1, Customer 2... and deleting the ID number, phone and address columns. Read only the first row of the spreadsheet (the column names) and don't show any other data on the screen.
```

## What goes where

| What | Does it leave the computer? | Where it's kept |
|---|---|---|
| Your messages and attachments | they go to Anthropic with every answer | in the conversation, on your computer |
| What Claude reads in Code mode, what a command shows on the screen, what it sees in the Code browser | goes to Anthropic | in the conversation |
| Memories | only what it reads during a chat | in text files, on your computer |
| API key, e-mail app password, GitHub and connector tokens | each one only to sign in to its own service | encrypted, on your computer |
| Spending history and settings | they don't leave | on your computer |
| Your files on GitHub | only what you ask it to send | on GitHub |

Widgets use the internet too: maps come from OpenStreetMap, and photos from other sites only load when you click (the reason is in [When a page or file tries to give Claude orders](#/aprender/injecao-de-instrucoes)).

According to Anthropic, by default what goes through the API isn't used to train models (see [Why use Clave](#/aprender/por-que-o-clave)). Even so, the rule stands: send only what's needed. More details in [Security and privacy](#/aprender/seguranca-e-privacidade).
