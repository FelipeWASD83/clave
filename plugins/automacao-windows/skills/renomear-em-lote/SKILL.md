---
name: renomear-em-lote
description: Use to rename many files at once following a pattern (date in the name, numbering, removing repeated text, standardizing capitalization), with a preview and a way to undo.
---

# Rename in batch

1. Understand the pattern the person wants and show **before and after** for 5 to 10 real files, in a table.
2. Rules:
   - never change the extension (`.jpg` stays `.jpg`);
   - never leave two files with the same name: if they collide, number them (`foto-001.jpg`, `foto-002.jpg`);
   - avoid characters Windows doesn't accept: `\ / : * ? " < > |`;
   - date in the name in `YYYY-MM-DD` format (it sorts in the right order when Windows sorts by name);
   - to use the date of the photo, prefer the file's creation date and say that is the one you used.
3. After the OK, rename and save `renomeacao-AAAA-MM-DD.csv` (old name, new name) and a `desfazer-renomeacao.ps1`.
4. Say how many were renamed and how many were left out, and why.
