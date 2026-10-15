---
titulo: An order app without AI (and almost free)
trilha: 3. Automation with Code mode
ordem: 28
duracao: 12 min
resumo: Orders that arrive by email become rows in Excel and go to the website, with a program built only once, instead of paying Claude every 15 minutes.
---

Picture a sales office. Orders arrive by email, someone copies each one into an Excel spreadsheet and then types it all again on the company website. The natural idea is to create a [routine](#/aprender/rotinas) that calls Claude every 15 minutes to do this.

It works, but it's the expensive way. This lesson shows the better way: ask Code mode, **only once**, for a small program that does the job **without AI**. Windows itself runs the program on schedule, and each run costs zero tokens.

## 1. Why not a routine

A routine every 15 minutes means 96 calls to Claude a day, about 2,900 a month. Each call pays for Claude to read the emails, even when no order came in. And the spending goes on next month, and the month after, forever.

A [script](#/aprender/glossario/script) does the same job by following fixed rules: it finds the email, splits out the fields, writes them to the spreadsheet. It costs only the conversation that built it. After that, it can run all day for free.

There are two more advantages:

- The program does it **the same way every time**. An AI can vary a little from one time to the next, and orders need to come out the same every time.
- A routine doesn't ask anyone for an OK. For it to write to the spreadsheet and send to the website, you would have to allow everything with [permission rules](#/aprender/permissoes).

**When AI is worth it:** when orders arrive as free text, with each client writing in their own way ("send me the usual coffee, about ten boxes"). Fixed rules get lost there. Even then, use AI only for that piece: the program does everything else and calls Claude only to understand the emails that don't follow the pattern, with Haiku, the cheapest model (see [Models and reasoning](#/aprender/modelos-e-raciocinio)). At the current Haiku 5.5 price, that comes to less than one US cent per order (this is an estimate).

## 2. What you need

- Clave, with [Code mode](#/aprender/modo-code).
- [Python](#/aprender/glossario/python). It's already on your computer: the Clave installer took care of that.
- Access to the email account where the orders arrive (step 3).
- The orders [spreadsheet](#/aprender/glossario/planilha). If it doesn't exist yet, the program creates one called `orders.xlsx`.
- Knowing how the company website receives orders: through an [API](#/aprender/glossario/api), through a form on a page, or only by typing on the screen. If you don't know, ask whoever looks after the website. Step 6 explains the three cases.

Create a folder just for this, for example `Documents\order-robot`. That's where Code mode will work.

## 3. Connect the email

The program reads the emails through **IMAP**, the standard way for a program to get into an email inbox. For that it needs a password.

**Gmail:**

1. Turn on **2-Step Verification** in your Google Account (myaccount.google.com > Security).
2. Open myaccount.google.com/apppasswords and create an **app password** with a name like "order robot".
3. Google shows a 16-letter password. Keep that screen open until step 5. This password only works for this, doesn't change your normal password and can be deleted at any time.

If the email belongs to a company on Google Workspace, the administrator may have blocked app passwords. In that case, talk to them.

**Other providers** (Locaweb, Hostinger, KingHost, Zoho, Yahoo and most hosting companies): search for "IMAP" on your provider's help page. It shows the server address (something like `imap.yourprovider.com`) and the port (almost always 993). Some, like Yahoo, also ask for an app password, similar to Gmail's.

**Microsoft (Outlook.com, Hotmail and Microsoft 365):** Microsoft no longer accepts signing in through IMAP with a password, not even with an app password. You have two paths:

- Use the **classic Outlook** installed on the computer (the one that comes with Office, not the "new Outlook"), already signed in to the account. The program reads the emails through it, with no password at all.
- Use an email connector in **Settings > Connectors** (see the lesson [Web search and connectors](#/aprender/conectores)). Watch out: through the connector it's Claude that reads the emails, so every read costs tokens again. It's the way out for when there's no other.

**Where the password lives.** The password is never written inside the program and never pasted into the conversation with Claude. The program stores the password in the **Windows Credential Manager**, the password vault that already comes with Windows, and takes it from there when it signs in. You type the password only once, in a window of the program itself (the request in step 5 already takes care of this). To see or delete it later: Start menu > **Credential Manager** > **Windows Credentials**.

## 4. Agree on an order template

A program without AI needs the order to always arrive in the same way. Agree on this with your clients. It can be:

- a fixed email format, like the example below;
- a simple order form, for example a template spreadsheet that the client fills in and sends as an attachment;
- the attachment they already send today, if it always comes the same way.

Example of an order email:

```
Subject: Order - Example Market

Client: Example Market
Client code: 1042

Items (quantity; product; unit price):
10; Coffee 500 g; $18.90
5; Sugar 1 kg; $4.50
20; Rice 5 kg; $27.00

Delivery: 10/20/2026
Note: deliver in the morning
```

Save an example like this one in a file called `order-example.txt` inside the `order-robot` folder. Claude will use that file to understand the format.

## 5. Ask Code mode

1. **New Code task** > choose the `order-robot` folder.
2. Leave the permission mode on **Ask** (or on **Plan**, to see the plan first).
3. Send the request below. Replace what's in square brackets with the details of your case.

```experimentar-code
I want a Python program, in this folder, that moves the orders that arrive by email into a spreadsheet. It must not use any AI. It must:

1. Sign in to the email inbox through IMAP (server [imap.gmail.com], port 993) and read only the unread emails with "Order" in the subject.
2. Take from each email: client, client code, items (quantity, product, unit price), delivery date and note. The format is in the file order-example.txt.
3. Write one row per item in orders.xlsx, always at the end, without deleting or overwriting anything. If the spreadsheet doesn't exist, create it with a header.
4. Mark the email as read only after writing it, and remember which emails were already recorded, so the same order is never recorded twice.
5. If the email doesn't follow the format, don't guess: move it to a folder called "Orders with problems" and write it in the log.
6. If the spreadsheet is open in Excel, don't lose the order: leave the email unread and try again next time.
7. Send each order to the company website (I'll explain how in a later message).
8. Write everything it did to a file called orders.log, with date and time, and never write a password in the log.
9. Have a test mode, which only shows what it would do, without writing, without marking emails and without sending anything to the website.

The email password can't be written in the code: store it in the Windows Credential Manager (keyring library). Create a setup.bat that I run with a double-click: it asks for the email and the password in a window and stores them. Don't ask me for the password here in the conversation.

At the end, write a README.md in simple language explaining how to use it, how to test it and what to do if there's an error.
```

Using classic Outlook (a Microsoft account)? Replace item 1 with "Read the emails through the classic Outlook installed on this computer, in the Inbox". In that case there's no email password to store.

What to expect: it will ask for your OK to install a few Python [libraries](#/aprender/glossario/biblioteca) and to create the files. Read each card before allowing it. At the end, double-click `setup.bat` and type the app password from step 3 in the window that opens.

**Shortcut:** the Sales plugin has the `/vendas:automatizar` command for this kind of request. With the plugin turned on (in **Plugins**, in the left sidebar), type the command in Code mode and say what you want to automate. See [Plugins and slash commands](#/aprender/plugins-e-comandos).

## 6. Sending to the company website

Ask for this part in a second message, once the email and the spreadsheet are working. There are three cases, from best to worst.

**The website has an API.** This is the best case: an API is an entrance made for programs. Ask whoever built the website (the developer or the company that looks after it) for three things: the API address, an access key (an [access token](#/aprender/glossario/token-de-acesso)) and an example order in the format it accepts. If the website has a test environment, ask for that too. The key goes into the Credential Manager, just like the email password.

```experimentar-code
The company website receives orders through an API. What the developer sent is in the file site-api.txt. Make the program send each order to this API after writing it to the spreadsheet. The API key goes in the Credential Manager (add that question to setup.bat). If the website rejects the order or is down, write it in the log and try again on the next run, without sending the same order twice.
```

**The website has an order form.** The program fills in and sends the form, as if a person had done it. It works well as long as the form doesn't change. If the form asks you to prove you're not a robot (the well-known "I'm not a robot"), it can't be done: that exists precisely to stop programs. In that case, ask whoever runs the website for an API.

**The website only accepts typing on the screen** (signing in with a username and password, clicking, filling in). The program can open a [browser](#/aprender/glossario/navegador) on its own and click and type for you, with a library called Playwright. It's the last resort: it's slower, it breaks when the website changes its look, and it needs the website password (which also goes into the Credential Manager). First, check whether the website's terms of use allow it.

```experimentar-code
The company website only accepts orders typed on the screen, on the page [address of the order page]. Make the program open Microsoft Edge with Playwright, sign in with the username and password stored in the Credential Manager and enter each order. Before writing it, ask me whatever you need to know about the order screen. In test mode, fill everything in but don't click send.
```

## 7. Test before you trust it

1. Send yourself a fake order email, in the agreed format, with "Order" in the subject.
2. Run the program in **test mode** (the `README.md` says how, or ask in Code: "run the program in test mode"). Check in `orders.log` whether it found the email and understood each item.
3. Run it for real. Open `orders.xlsx` and check the rows. See whether the email was marked as read.
4. Run it again and confirm the same order did **not** go in twice.
5. Test the problems: an email that doesn't follow the format, and the spreadsheet open in Excel when it runs.
6. Last, test sending to the website, preferably in the website's test environment or with an order agreed with whoever looks after it.

**When something breaks:** open `orders.log` (it opens in Notepad). The last lines say what happened. Copy the error, open Code mode in the same folder and paste: "The order program gave this error: [paste it here]. Find the cause and fix it." If the fix makes things worse, use **Undo changes**.

## 8. Let it run on its own

The [Task Scheduler](#/aprender/glossario/agendador-de-tarefas) in Windows is what runs the program on schedule. Code creates the task for you (with the `schtasks` command or through PowerShell) and shows you the command first:

```experimentar-code
Create a task in the Windows Task Scheduler that runs the order program every 15 minutes, in a Task Scheduler folder called "My automations". Use pythonw, so no window opens on each run. Show me the command before running it and explain how to pause and how to delete the task.
```

To pause, change or delete it later, open **Task Scheduler** from the Start menu, go into the "My automations" folder and right-click the task:

- **Disable** pauses it (and **Enable** turns it back on);
- **Properties** > **Triggers** tab changes the interval;
- **Delete** removes the task (the program stays in the folder).

Or ask Code, for example "pause the orders task". Deleting always asks for your OK.

Things to watch:

- The computer needs to be **on**, with your user signed in to Windows (the screen can be locked). If it's off at night, nothing is lost: the night's orders stay unread and go in on the first run in the morning.
- If you can, use a computer that stays on in the office and turn off sleep in the Windows power settings.
- Run the program on **one computer only**. Two computers running the same program can record the same order twice.
- Whoever looks at the spreadsheet should close Excel afterwards. If it's open all day, the orders are left waiting.

## 9. What it costs

| | Routine every 15 min | Program without AI |
|---|---|---|
| To set up | nothing (just writing the request) | one conversation in Code mode, once |
| Each run | tokens, even with no new order | zero |
| Runs per month | about 2,900 | about 2,900 |
| Example, at $0.02 per run | about $58 a month, every month | $0 |
| Result | can vary a little | always the same |
| If the email format changes | adapts on its own | needs an adjustment (another short conversation) |

The $0.02 per run is only an example: the real cost depends on the model and on how many emails it reads. To understand where the spending comes from, see [Tokens, context and spending](#/aprender/contexto-e-gasto).

## 10. Before leaving it on automatic

- The passwords (for the email and the website) are in the Credential Manager, not in the code or in the conversation.
- The order format was agreed with the clients.
- Test mode worked with a fake order.
- The same order doesn't go in twice.
- An order that doesn't follow the format goes to "Orders with problems", and someone checks that folder every day.
- Sending to the website was tested.
- The task is in the Task Scheduler, in the "My automations" folder, and you know how to pause it.
- The computer that runs the program stays on.
- The `orders.xlsx` spreadsheet is part of the office backup.
- The `README.md` explains everything for whoever comes along later.
