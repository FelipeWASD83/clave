---
titulo: Excel with Claude
trilha: 3. Automation with Code mode
ordem: 22
duracao: 8 min
resumo: Read, create and change spreadsheets: formulas, tables, charts, PDF, in chat and in Code mode.
---

Claude works with real Excel [spreadsheets](#/aprender/glossario/planilha): it reads, creates and changes them, and adds [formulas](#/aprender/glossario/formula), formatting, tables, charts, filters and dropdown lists. It works in two ways.

## In chat: send a spreadsheet, get another one back

**Attach** the spreadsheet (.xlsx, or .xls, which Clave converts) and ask:

```experimentar
Create a monthly expense tracking spreadsheet with the columns Date, Description, Category (with a dropdown list: Groceries, Bills, Transport, Fun, Other) and Amount in dollars. Put a total at the bottom, a summary by category on another sheet and a pie chart with the spending by category.
```

When it creates or changes a spreadsheet in chat, a card appears with **Download** and **Open** (opens it in Excel). Your original spreadsheet is never touched: it hands you a new copy.

Examples of requests with a spreadsheet attached:

- "Who were the 5 customers that bought the most?"
- "Is there any strange or repeated value in here?"
- "Join the First name and Last name columns and give me the spreadsheet back."
- "Make a chart of sales by month and export it as a PDF."

## In Code mode: spreadsheets in your folder

In Code mode it works directly on the files in the folder, and that opens the door to bigger automations:

```experimentar-code
This folder has several sales spreadsheets, one per month. Combine them all into one spreadsheet called sales-of-the-year.xlsx, with one sheet per month and a Summary sheet with the total for each month and a column chart.
```

More examples:

- "Read report.xlsx and write a summary of what changed compared with last month."
- "For each row in customers.xlsx, create a text file with a personalized payment reminder letter."
- "Highlight in red the rows whose due date has already passed."
- "Recalculate the formulas and export the Summary sheet as a PDF."

It asks for permission before saving changes (in Ask mode), and **Undo changes** gives the spreadsheet back as it was.

## Formulas and the Excel on your computer

Clave writes the formulas, but it is Excel that **calculates** them. If Microsoft Excel is installed, Claude can ask it to recalculate the spreadsheet (and check the results), export to PDF and convert .xls and .csv files into .xlsx. Without Excel, the formulas are calculated when you open the file.

## Things to watch out for

- **Close the spreadsheet in Excel** before asking for a change to it: an open file can't be saved.
- Spreadsheets with **images, shapes or macros** may lose them when changed. In that case, ask it to save a copy under another name.
- Huge spreadsheet (tens of thousands of rows)? Ask it to work in parts or with a Python script, which is faster.
