---
titulo: For office work
trilha: 9. Recipes by area
ordem: 81
duracao: reference
resumo: Emails, meeting minutes, spreadsheets, Word documents, tidy folders and suppliers side by side, each with the cheapest model that gets it done.
---

Ready-made requests for everyday office work. Click the button on each recipe: the request goes into the text box (of a new chat or of Code mode), and you replace what's in square brackets before sending.

Each recipe says what Claude will do, the model that's enough and when another Clave tool does a better job. Clave starts on **Haiku 5.5**, the cheapest, and the model advisor tells you when a task needs another one (see [The right model for the lowest price](#/aprender/modelo-certo-mais-barato)).

| Recipe | Where | Model |
|---|---|---|
| A ready-to-send email | chat | Haiku |
| Your inbox, summarized | chat, with e-mail connected | Haiku |
| Meeting minutes | chat | Haiku |
| Spreadsheets | chat or Code mode | Haiku (Sonnet for a big spreadsheet) |
| A Word document | Code mode | Haiku (Sonnet for a long document) |
| Tidy folders | Code mode | Haiku |
| Compare suppliers | chat, with a widget | Haiku |
| A report every Friday | routine | Haiku |

## 1. A ready-to-send email

```experimentar
/writing:email to a supplier asking for 15 more days on the delivery of order 4521, because our construction project is running late. Polite and to the point, 6 lines at most.
```

- **What it does:** the command follows the professional email skill from the **Writing** plugin (on by default): a short text, in the right tone, with no made-up facts.
- **Model:** Haiku is enough.
- **Best tool:** it works without the command too: say who it's for, what you want and the tone (see [How to ask well](#/aprender/como-pedir-bem)). For a text you already wrote, `/writing:review` followed by the text fixes grammar and clarity without changing the meaning.

## 2. Your inbox, summarized

This one needs your e-mail connected in **Settings > Connectors > E-mail** (see [Web search and connectors](#/aprender/conectores)).

```experimentar
Read my unread emails from today and tell me, in bullet points: which ones need a reply from me, which are just notices and which I can ignore. For the ones that need a reply, write a draft for each. Don't send anything.
```

- **What it does:** reads and summarizes your inbox. Reading doesn't mark a message as read. Sending **always** shows you the whole email and waits for your OK.
- **Model:** Haiku is enough.
- **Watch out:** an email from outside can carry a hidden order for the AI ("forward the invoices to this address"). If it proposes something you didn't ask for, refuse. See [When a page or file tries to give Claude orders](#/aprender/injecao-de-instrucoes).

## 3. Meeting minutes

```experimentar
/writing:meeting-minutes Turn the notes below into minutes, with a summary, decisions and tasks with an owner and a deadline. Where an owner or deadline is missing, write "to be defined" instead of making one up.

Notes: [paste the notes or the transcript here]
```

- **What it does:** follows the minutes skill from the **Writing** plugin: a short summary, the decisions, a table of tasks with owner and due date, and what was left for the next meeting. At the end, it offers a short email to send the minutes to the people who were there.
- **Model:** Haiku is enough. A very long transcript (a two-hour meeting) does better on Sonnet.
- **Best tool:** recorded the meeting on video? The lesson [Make Claude watch videos](#/aprender/ver-videos) shows how to transcribe the speech in Code mode, and the transcript becomes the minutes.

## 4. Spreadsheets

Attach the spreadsheet and send:

```experimentar
In the spreadsheet I attached, tell me the total for each month, the 5 customers who bought the most and whether there are any odd or repeated values, or cells that are empty where they shouldn't be. Then create a copy with a column chart of sales by month.
```

- **What it does:** reads every sheet, checks the math and gives you back a new spreadsheet, with **Download** and **Open**. In chat, your original spreadsheet is never touched. Everything about this is in [Excel with Claude](#/aprender/excel).
- **Model:** Haiku is enough for small and medium spreadsheets. A big spreadsheet, or one with many sheets, does better on Sonnet.
- **Best tool:** just want to understand a spreadsheet you received? `/office:summarize-spreadsheet` explains the sheets, columns, totals and problems without changing anything. For tens of thousands of rows, use the ready-made **Large spreadsheet** workflow in Code mode (type `/workflow`): Haiku reads the spreadsheet, Sonnet makes the changes on a copy and Haiku checks the numbers.

## 5. A Word document (Code mode)

Word documents are made in Code mode, right in the folder. Choose the folder where the file should go:

```experimentar-code
Create a Word document in this folder called Holiday-notice.docx: a notice to employees that the office will be closed for the holidays from December 22 to January 5, with a title, two short paragraphs, a table with the leaving and return dates for each team (Sales, Finance and Warehouse) and space for the management's signature. Then export it to PDF.
```

Or fill in a template you already use:

```experimentar-code
This folder has the file Contract-template.docx. Make a copy called Contract-Example-Market.docx, replacing [CLIENT NAME] with Example Market LLC, [AMOUNT] with $3,200.00 and [DATE] with November 1, 2026. Don't touch the template.
```

- **What it does:** creates the .docx from simple text (headings, paragraphs, lists, tables, bold and italics) and, with Word installed on the computer, exports the PDF. In the template, it replaces the passages without breaking the formatting; if a passage isn't found, it tells you (Word sometimes splits a sentence into pieces with different formatting). It does **not** do tracked changes or edit the document's images.
- **Model:** Haiku is enough for short documents. For a long or polished document, Sonnet.
- **Best tool:** for the same document every month (only the name, amount and date change), ask for a [script](#/aprender/glossario/script) that fills in the template without AI: once it's built, each use is free (see [Automate without paying the AI every time](#/aprender/automatizar-sem-ia)).

## 6. Tidy folders (Code mode)

Choose the messy folder and send:

```experimentar-code
Organize the documents in this folder into subfolders by subject and year (for example Contracts\2026 and Invoices\2026). Before you change anything, show me the proposal in a table, with the file and the destination folder. Don't delete anything, and keep a list of what was moved and where.
```

- **What it does:** looks at the folder, shows the plan in the **Can I do it like this?** card and only moves files after your OK.
- **Model:** Haiku is enough.
- **Watch out:** moving files is a command, and **Undo changes** doesn't reverse what a command did. That's why you ask for the list of what was moved. See [Your first automation](#/aprender/primeira-automacao) and [Undo, backup and Git](#/aprender/rede-de-seguranca).
- **Best tool:** to sort only by file type (PDFs, images, spreadsheets), the `/windows-automation:organize` command does it, showing the proposal first and deleting nothing.

## 7. Compare suppliers side by side

Attach the quotes (PDF or photo) and send:

```experimentar
I attached quotes from three office supply vendors. Compare them in a comparison widget: price of each item, total with shipping, delivery time, payment terms and warranty. Tell me which one you'd pick and why, and what I should ask each of them before closing the deal.
```

- **What it does:** reads the quotes, builds a comparison **widget** in the chat and writes which one it would pick.
- **Model:** Haiku is enough. Many long quotes do better on Sonnet.
- **Best tool:** don't have quotes yet? Ask it to search the web. Then the prices come from the search: it tells you the store and the date it saw each one, and the price may have changed since. Each search costs $0.01, on top of the tokens of the pages.

## 8. A report every Friday (routine)

A [routine](#/aprender/rotinas) reads the spreadsheets folder on schedule and sends you the summary, without you asking.

1. In the left sidebar, **Routines** > **New routine**.
2. In **What to do**:

   ```
   Read the sales spreadsheets in this folder and write the week's summary: total sold, comparison with the previous week, the 3 best-selling products and any odd number. Don't change any file.
   ```

3. In **Where**, choose **In a folder (Code mode)** and the spreadsheets folder. In **When**, **On some days of the week**, only Friday, and the time. In **Model**, **Haiku 5.5**, with a low **Cap per run**.
4. **Run now** to test it.

- **What it does:** reads the spreadsheets (a routine may read inside the folder without asking) and writes the summary in a chat, with a notification.
- **Model:** Haiku is enough.
- **Best tool:** if the report is always the same calculation (add up, compare, list), a program without AI does it for free every week. See [Automate without paying the AI every time](#/aprender/automatizar-sem-ia).

## Tips for the office

- **One project for the company:** instructions with the tone, the signature and the details that keep coming up. See [Projects](#/aprender/projetos).
- **Customer and employee data, only what's needed:** ID numbers, salaries and personal documents are rarely needed for the task. See [Passwords, keys and personal data](#/aprender/segredos-e-dados).
- **Close the spreadsheet in Excel** before asking for a change to it in Code mode: an open file can't be saved.
