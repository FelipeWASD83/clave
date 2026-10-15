---
titulo: Automation recipes for everyday life
trilha: 3. Automation with Code mode
ordem: 23
duracao: reference
resumo: Ready-made requests for photos, PDFs, documents, reports and tasks that run by themselves.
---

Ready-made requests to copy. In all of them, choose the right folder in Code mode and keep the permission mode on **Ask** until you feel confident.

Some recipes need extra programs (for example, a Python library to work with PDFs or photos). When that happens, Claude explains what it is and asks for your OK before installing.

## Photos and images

```experimentar-code
Rename the photos in this folder with the date they were taken, in the format 2026-10-14_001.jpg. First, show me what the first 5 names would look like.
```

```experimentar-code
Make a copy of all the photos in this folder at a smaller size (at most 1600 pixels wide), in a subfolder called "for-whatsapp".
```

## PDFs and documents

```experimentar-code
Combine all the PDFs in this folder into a single PDF, in alphabetical order, called combined-documents.pdf.
```

```experimentar-code
Read the invoice PDFs in this folder and build a spreadsheet with the date, supplier and amount of each one.
```

## Reports

```experimentar-code
Read the spreadsheets in this folder and write a report.md with the main numbers of the month, compared with the previous month, in simple language.
```

## Files and folders

```experimentar-code
Find duplicate files in this folder (same content, different names) and show me the list. Don't delete anything.
```

```experimentar-code
Create a folder structure to organize my household documents: bills, health, car, kids' school and taxes, each with subfolders by year.
```

## Tasks that run by themselves

Windows has the **Task Scheduler**, which runs a script at set times. Claude sets it up for you:

```experimentar-code
Create a script that copies my Documents folder to my external hard drive (drive letter E:) every Friday at 8 PM, using the Task Scheduler. First explain to me what will be created and how to turn it off.
```

A scheduled script is good for a task that is always the same. When the task needs to **think** (read new files and summarize them, check a spreadsheet and point out problems), use a [routine](#/aprender/rotinas): Claude itself runs at the set time.

## Tips for automations that last

- Always ask for a **script** (a .ps1 or .py file) instead of a one-time action: you can run it again.
- Ask it to **write a README** explaining what the script does and how to use it.
- Test on a **copy** of the folder before running it on the real files.
