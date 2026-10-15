---
name: proposta-comercial
description: Use when the person needs a sales proposal or quote (orçamento) for a client: client data, items with quantity and unit price, discount, payment terms (Pix, boleto, cartão), validity and delivery. Delivers a Word file and a PDF, with every number checked.
---

# Sales proposal

Write everything the person reads in their language. The proposal itself goes in the client's language (in Brazil, Portuguese).

## 1. Gather the data (ask only what is missing)
If there is a previous proposal or a template in the folder (`.docx` or PDF), read it first and follow its layout, wording and numbering. Then make sure you have:
- **Seller:** company name, CNPJ, address, phone, e-mail, who signs.
- **Client:** razão social (or the person's name), CNPJ or CPF, contact person, e-mail or phone, city and UF.
- **Items:** description, unit (un, cx, kg, m², hora), quantity, unit price; product code if the company uses one.
- **Discount:** per item or on the total, in % or in R$.
- **Freight:** CIF (seller pays) or FOB (client pays), and the value.
- **Payment:** Pix (the key the person gives you), boleto (à vista or in installments such as 30/60/90 dias), cartão (how many installments, with or without interest), down payment.
- **Validity** of the proposal (e.g. 15 days) and **delivery time** (e.g. 10 dias úteis after the order is confirmed).
- **Taxes:** whether prices include taxes. Never calculate ICMS, IPI, ISS or any tax yourself; write only what the person tells you (e.g. "Impostos inclusos").

Ask at most 5 things at a time. **Never invent** a price, discount, deadline or condition. If the person wants to go ahead without some data, put a visible placeholder (`[PRAZO DE ENTREGA]`) and list every placeholder at the end.

## 2. Do the math, then check it
- Line total = quantity × unit price, rounded to centavos on each line.
- Subtotal = sum of the line totals.
- Discount in %: discount = subtotal × rate, rounded to centavos. Total = subtotal − discount + freight (when the client pays it in the proposal).
- Discount per line and discount on the total can differ by a few centavos: choose one rule, write it in the proposal and use it everywhere.
- Installments: total ÷ number of installments, rounded; the last one absorbs the difference so the sum is exactly the total (R$ 1.000,00 in 3x = 333,33 + 333,33 + 333,34).
- Validity date: today + N calendar days, written as a real date ("válida até 30/10/2026").
- Don't do the arithmetic in your head. In Code mode, run a short Python calculation with `rodar_comando` (Clave needs Python, so it is on the computer; the command is `py` or `python`). Then recalculate a second way (e.g. sum quantity × price × (1 − rate) line by line) and compare.
- Money as `R$ 1.234,56` (dot for thousands, comma for decimals), percentages as `10%`, dates as `dd/mm/aaaa`.
- CNPJ and CPF: check the check digits (module 11). Since July 2026 a new CNPJ can have letters in its first 12 positions (the last 2 are always digits; each character counts as its ASCII code minus 48). A number that fails the check is reported to the person, never "fixed" by you.

## 3. Structure of the document
1. Header: seller (name, CNPJ, contacts), "Proposta comercial nº 2026-041" and the date.
2. Client block.
3. One or two lines saying what is being offered.
4. Items table: Item | Descrição | Un. | Qtd. | Valor unit. | Total. Numbers right-aligned.
5. Totals: Subtotal, Desconto, Frete, **Total** in bold.
6. Conditions: payment, validity, delivery, freight, what is not included.
7. Acceptance: seller's name and role, and a line for the client to sign ("De acordo").

No images from the internet. A logo only if the person gives you the file.

## 4. Create the files
**With Clave's Word tools** (`word_criar`, `word_ler`, `word_alterar`, `word_no_app`), if they are in your tool list:
- `word_ler` to read a template or a previous proposal.
- `word_criar` to create the proposal (e.g. `Proposta 2026-041 - Cliente.docx`). Never save over an existing proposal: new number, new file.
- `word_alterar` for corrections the person asks for afterwards.
- `word_no_app` to export the PDF with the Word installed on the computer.
Read each tool's description for its fields instead of guessing.

**Without them** (not in your tool list, or Word is not installed):
- Create `proposta-2026-041.html` as a single file with the CSS inside: `@page { size: A4; margin: 18mm; }`, `font-family: "Segoe UI", Arial, sans-serif`, table header highlighted, `tr { break-inside: avoid; }`.
- Convert it with Microsoft Edge, which comes with Windows (the same technique as the skill `escritorio:relatorio-em-pdf`):

```powershell
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe" }
$html = (Resolve-Path ".\proposta-2026-041.html").Path
& $edge --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="$PWD\proposta-2026-041.pdf" "file:///$($html -replace '\\','/')"
```

- If the person needs an editable Word file, tell them that Word opens the HTML (File > Open) and saves it as `.docx`.
- In chat, with no folder: deliver the HTML in an ```html block, so the person sees the preview and can save it.

## 5. Before saying it's done
- [ ] Every line total, the subtotal, the discount, the freight and the total recalculated a second way.
- [ ] Installments add up exactly to the total.
- [ ] The same total appears in the table, in the conditions and in any message that goes with it.
- [ ] Client name and CNPJ/CPF exactly as the person gave them, with valid check digits.
- [ ] Validity date is a real date after today.
- [ ] No placeholder left, or all of them listed for the person.
- [ ] The PDF exists and is larger than zero bytes; read it with `ler_arquivo` (it shows the pages) and look at the layout.

Then deliver: where the files are, the total and the conditions in two lines, and the assumptions you made. Offer to open the PDF with `excel_abrir` (it opens any file in its program), to write the e-mail that goes with it (nothing is sent without the person's OK) and to plan the follow-up with the skill `vendas:follow-up-de-cliente`.
