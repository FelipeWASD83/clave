---
name: pedido-para-planilha
description: Use when client orders arrive by e-mail, pasted WhatsApp text or PDF and need to become rows in an Excel order sheet (date, client, CNPJ/CPF, items, quantities, prices, total, delivery, status). Never overwrites the original sheet without a copy and flags doubtful fields instead of guessing.
---

# Orders into a spreadsheet

Write everything the person reads in their language.

## 1. Know the sheet first
- If an order sheet already exists, read all of it: `excel_ler` in Code mode, `planilha_ler` in chat. Learn the columns, the formats, whether it is one row per order or one row per item, which status values are used, where the totals and formulas are.
- If there is none, propose this layout, one row per item (it makes reports easy later):
  `Pedido | Data | Cliente | CNPJ/CPF | Contato | Produto | Código | Qtd. | Un. | Preço unit. | Total do item | Entrega | Local de entrega | Pagamento | Status | Origem | A conferir`
  - `Total do item` as a formula (`=H2*J2`), money as `"R$" #,##0.00`, dates as `dd/mm/yyyy`.
  - `Status` as a dropdown: Novo, Confirmado, Separando, Faturado, Entregue, Cancelado.
  - `Origem`: e-mail, WhatsApp, PDF, telefone.
- Don't change the layout of an existing sheet without asking.

## 2. Read the orders
- **E-mail:** if `email_ler` is in your tool list, use it; otherwise the person pastes the text or saves the e-mail as PDF.
- **WhatsApp:** text pasted in the chat, or the file from WhatsApp's "Exportar conversa" (a `.txt`, which `ler_arquivo` reads). Each line starts with the date, time and sender.
- **PDF:** `ler_arquivo` shows you the pages. A scanned PDF can be misread: be extra careful with numbers.
- Attachments in chat (PDF, spreadsheet) are read the same way.

## 3. Extract each field
- **Numbers the Brazilian way:** `1.250,50` is one thousand two hundred fifty and fifty centavos; `1,5` is one and a half; `1.000` is one thousand. If it could be read two ways, flag it.
- **Units:** keep the unit the client wrote (cx, un, kg, fardo). Convert only with a conversion table the person gave you.
- **Prices:** the price the client wrote, or the company's price list if the person gave you one (read it). No price anywhere: leave it blank and flag it. Never invent a price.
- **Dates:** `dd/mm/aaaa`. "Amanhã" or "sexta" are resolved from the date of the message, and the note says so ("sexta = 16/10/2026, calculado").
- **CNPJ/CPF:** keep it as written and check the check digits (module 11). Since July 2026 a new CNPJ can have letters in its first 12 positions (the last 2 are always digits; each character counts as its ASCII code minus 48). Invalid: flag it, never correct it on your own.
- **Client:** look for the client already in the sheet. Same CNPJ = same client: use the name already registered and mention it if the order spelled it differently.
- **Products:** match to the product list or codes if there is one. A doubtful match is flagged, not chosen.
- **Possible duplicate:** same client, same items, close dates. It may be the same order sent twice: flag it and don't add it twice.

**Doubtful field = flag, don't guess.** Put your best reading (or leave it blank), write what is doubtful in `A conferir` and give the row a yellow fill.

## 4. Show before writing
Show a preview table with the rows you are going to add and, below it, the list of doubtful fields. Wait for the person's OK. With many orders, show the count, the total value and the doubtful ones, not every row.

## 5. Write, never on the original without a copy
- **Chat:** `planilha_criar` with `base_anexo_id` creates a new version and the original is not touched.
- **Code mode:** `excel_alterar` saves on the file it receives, so make the copy first with `rodar_comando`, e.g.
  `New-Item -ItemType Directory -Force backup | Out-Null; Copy-Item "Pedidos.xlsx" "backup\Pedidos 2026-10-15 14h30.xlsx"`
  and only then add the rows. Ask whether they prefer the new rows in the original (with the backup) or in a separate file.
- The file must be closed in Excel (on every computer, if the sheet is shared). If it is open, stop and ask.
- If the sheet has images, shapes, buttons or macros (`.xlsm`), saving through Clave may lose them: write to a copy and warn the person.
- Add rows after the last filled row; never rewrite or reorder the existing rows.

## 6. Before saying it's done
- [ ] Read the sheet again: the new rows are there, in the right columns, and the old rows did not change.
- [ ] Recalculate (`excel_no_app` with `recalcular`, if Excel is installed) and check the totals: the sum of `Total do item` per order matches what the client wrote, when the client wrote a total.
- [ ] Number of rows added = number of items read.
- [ ] Every doubtful field is in `A conferir` and in your answer.
- [ ] Say where the backup is.

If orders arrive all the time in the same format (a form, a system e-mail, a supplier's PDF), offer the skill `vendas:automacao-sem-ia`: a small program can do this every few minutes without AI and without cost per order.
