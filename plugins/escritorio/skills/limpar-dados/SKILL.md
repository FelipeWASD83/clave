---
name: limpar-dados
description: Use to fix a messy spreadsheet or CSV: extra spaces, repeated rows, dates and numbers in mixed formats, broken accents. Saves the result in a new file and says what changed.
---

# Clean data

## Before
1. Open the file and describe the problem with real examples (e.g. "the Date column has 12/03/2026 and 2026-03-12").
2. CSV files from Brazil usually use `;` as the separator and a decimal comma. Broken accents (`SÃ£o Paulo`) mean a UTF-8 file was read as Latin-1 (or the other way around): find the right encoding before touching anything.
3. Agree with the person on what to do with doubtful cases (e.g. a row with no name: delete or flag?).

## Cleaning (in this order)
1. Trim spaces at the start and end; standardize capitalization where it makes sense (names, state abbreviations).
2. Dates in a single format, such as dd/mm/yyyy (or as a real date, in Excel).
3. Numbers: remove `R$` and other currency symbols and thousands separators, and turn the decimal comma into the numeric format.
4. Repeated rows: only remove the **identical** ones; list the similar ones for the person to decide.
5. Empty cells: don't invent a value; flag them or leave them empty.

## After
- Save to a new file (e.g. `clientes - limpo.xlsx`) and keep the original intact.
- Show a summary: how many rows before and after, what was fixed in each column, what was left to decide.
- If the person will repeat this every month, offer to turn the cleaning into a script they can run again.
