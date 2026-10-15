---
name: excel-avancado
description: Use when creating, changing or analyzing Excel spreadsheets (.xlsx) with formulas, formatting, tables, charts, filters or dropdown lists. Makes sure the original is not lost and the numbers check out.
---

# Advanced Excel

## Before touching anything
1. Read the whole spreadsheet with `excel_ler` (all sheets) and describe to the person what you found: sheets, columns, where the totals are, important formulas.
2. **Never save over the original unless the person asks.** Use the `saida` field of `excel_alterar` to create a copy (e.g. `vendas - revisada.xlsx`).
3. A spreadsheet with a macro (`.xlsm`) or with charts and images that must stay intact: warn that saving through Clave may lose those parts, and prefer the copy.

## Formulas
- Write formulas **in English and with commas** (`=SUM(B2:B10)`, `=IF(C2>0,"ok","missing")`, `=VLOOKUP(A2,Table!A:C,3,FALSE)`). Excel in another language (in Portuguese it shows `SOMA`, `SE` and `PROCV`) translates them by itself.
- Clave writes the formula but doesn't calculate it. To see the result, ask for `excel_no_app` with `recalcular` (needs Excel installed) and read the file again.
- Prefer a reference to a parameter cell (e.g. the rate in `F1`) over a number written inside the formula.

## Make it presentable
- Bold header, freeze the first row, filter on the header.
- Money values with a currency format (e.g. `"R$" #,##0.00` for reais); dates as dates, not as text.
- Turn the range into a **table** when the person will keep filling it in.
- Conditional formatting to draw attention (e.g. red when negative), without too many colors.
- A chart only when it helps understanding; a clear title and named axes.

## At the end
- Check the totals: add them up again in a different way and compare. Say which numbers you checked.
- List what changed (sheet by sheet) and where the copy is.
- If the person wants to see it, offer `excel_abrir` to open it in Excel, or `excel_no_app` with `pdf` to generate a PDF.
