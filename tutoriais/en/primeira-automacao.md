---
titulo: Your first automation: tidy up the Downloads folder
trilha: 3. Automation with Code mode
ordem: 21
duracao: 6 min
resumo: A complete example, from the request to the review, with no risk of losing anything.
video: primeira-automacao
---

Let's build a real automation: sorting the mess in the Downloads folder into subfolders by type (Documents, Images, Spreadsheets, Installers, Other).

## 1. Choose the folder

**New Code task** > **Choose the working folder** > **Another folder…** > pick your Downloads folder (if you have used other folders before, the button is called **Choose environment**). Leave the permission mode on **Ask**.

## 2. Ask for the plan first

```experimentar-code
I want to organize this folder into subfolders by file type: Documents (pdf, doc, docx, txt), Images (jpg, png, gif, webp), Spreadsheets (xlsx, xls, csv), Installers (exe, msi) and Other. Before you change anything, show me how many files would go into each subfolder. Don't delete anything.
```

It will look at the folder and give you the count. Check that it makes sense.

## 3. Tell it to go ahead

Reply with something like "go ahead". It will ask for permission to create the subfolders and move the files: read the card and click **Allow**. To avoid approving one by one, use **More options > Allow for this task**.

## 4. Check the result

Open the folder in File Explorer (click the folder name at the top of the conversation) and see if it came out the way you wanted. Don't like it? Ask for adjustments in the same chat ("the .zip files go to Other"). The **Undo changes** button doesn't help here: it brings back the files Claude wrote or edited, and the files were moved by a command. Want a way back? Ask before: "keep a list of what was moved and where".

## 5. Turn it into something you can repeat

The best thing about automation is being able to run it again:

```experimentar-code
Create a script called organize-downloads.ps1 that does this same organizing every time I run it, and explain how to run it with a double-click.
```

You can even ask for it to run by itself every day, using the Windows Task Scheduler:

```experimentar-code
Set up the Windows Task Scheduler to run organize-downloads.ps1 every day at 6 PM. Show me the command first and explain how to turn it off later.
```

## What you learned

- Asking for the plan first avoids surprises.
- The permission cards show exactly what is going to happen.
- Undo changes brings back the files it wrote or edited, not what a command did (like moving files).
- A good automation becomes a script you can reuse.
