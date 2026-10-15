---
name: relatorio-de-vendas
description: Use when the person wants to understand their sales from a spreadsheet: totals per period, salesperson, product and client, ticket médio (average ticket), top clients and comparison with the previous period, with a short plain-language summary and, if asked, a PDF report.
---

# Sales report

Write everything the person reads in their language.

## 1. Understand the spreadsheet
- Read all the sheets (`excel_ler` in Code mode, `planilha_ler` in chat) and find the columns: date, order number, client, CNPJ/CPF, salesperson, product, quantity, unit price, total, status.
- Is it **one row per order or one row per item**? It changes how you count orders. Say which it is.
- Which value column is the revenue: gross or after discount, with or without freight? Use the one that exists and say which.
- Ask the period the person wants (this month, the quarter, the year). With no answer, use the last complete month.

## 2. Don't count in your head
- A few dozen rows: read them all (raise `max_linhas`) and calculate.
- Hundreds or thousands of rows, in Code mode, choose one:
  - a short Python script in the folder that reads the file (`csv` from the standard library, or `openpyxl` installed in a `.venv` inside the folder), run with `rodar_comando`;
  - or a summary sheet with formulas (`SUMIFS`, `COUNTIFS`, in English with commas) in a **copy** of the file, recalculated with `excel_no_app` (`recalcular`) and read again.
- In chat, with a big spreadsheet, say that Code mode does it better and why.

## 3. Clean before counting
- Cancelled orders and returns: leave them out of the revenue, but list them on their own (how many and how much).
- Numbers stored as text, dates stored as text, `R$` inside the cell: convert them for the calculation, not in the original.
- Identical repeated rows: list them and ask before excluding.
- Same client written in different ways: group by CNPJ/CPF when the column exists; otherwise show the similar names and ask.
- No salesperson or no product: group as "(sem vendedor)" / "(sem produto)", don't drop the value.

Say what you left out and how much money that was.

## 4. What to calculate (and write the definitions in the report)
- **Faturamento:** sum of the valid orders in the period.
- **Número de pedidos:** distinct order numbers (if one row per item) or rows (if one row per order).
- **Ticket médio:** faturamento ÷ número de pedidos. Not ÷ rows, not ÷ clients.
- **By period:** by month (or by week for short periods). Compare with the previous period of the same length and, if the data has it, the same period last year.
- **Partial period:** if the current month is not over, compare the same days (1 to 15 against 1 to 15) and say so.
- **Variation:** (current − previous) ÷ previous. Previous = 0 is "new", not an infinite percentage.
- **By salesperson:** revenue, orders, ticket médio, clients served. Show the numbers without judging people.
- **By product:** quantity, revenue, share of the total; products that sold last period and nothing in this one.
- **By client:** top 10 by revenue and their share of the total ("os 5 maiores clientes são 62% do faturamento"); clients that bought in the previous period and not in this one (worth a call).

## 5. Check before delivering
- [ ] Sum by salesperson = sum by product = sum by client = total revenue, to the centavo. If not, find why (usually a blank field) before going on.
- [ ] The number of orders matches between the summaries.
- [ ] Ticket médio recalculated from the totals shown.
- [ ] Each variation % recalculated from the two values shown next to it.

## 6. Deliver
- **Summary at the top, 5 to 8 lines in plain language:** total for the period and how it compares, what drove the change (product, client, salesperson), the biggest client, one point that deserves attention. Money as `R$ 1.234,56`, percentages with one decimal (`12,5%`).
- **Causes:** say what the data shows. A cause the data can't show ("caiu por causa da economia") is a hypothesis and is written as one.
- **New spreadsheet**, never changing the original (e.g. `Relatorio de vendas - 2026-10.xlsx`): sheets Resumo, Por mes, Por vendedor, Por produto, Por cliente, Excluidos. Bold header, first row frozen, money in `"R$" #,##0.00`, a column chart by month only if it helps.
- **PDF, if asked:** `excel_no_app` with `pdf` on the report spreadsheet (needs Excel installed), or a designed A4 page in HTML converted by Microsoft Edge, as in the skill `escritorio:relatorio-em-pdf`. Check that the PDF exists and look at it with `ler_arquivo`.
- Offer to open the result with `excel_abrir`.

If the person wants this report every week or every month, the calculations need no AI: offer the skill `vendas:automacao-sem-ia` for the numbers, and Claude only for the written comments, if they want them.
