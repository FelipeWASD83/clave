---
name: relatorio-em-pdf
description: Use when the person asks for a report, document or summary to print or send as a PDF. Builds a nice page in HTML and converts it to PDF through Microsoft Edge, which comes with Windows.
---

# PDF report

## 1. Content first
- Gather the data (spreadsheet, files, what the person said) and check the numbers before formatting.
- Structure: title, date, a 3 to 5 line summary at the top, then the sections, and at the end the sources or notes.

## 2. HTML page
Create `relatorio.html` (or whatever name makes sense) in the folder, as a single file, with the CSS inside the page:
- System font (`font-family: "Segoe UI", Arial, sans-serif`), body at 11pt, larger headings.
- A4 page for printing: `@page { size: A4; margin: 18mm; }`.
- Tables with a highlighted header and alternating rows; numbers right-aligned.
- Avoid page breaks in the middle of a small table: `tr, figure { break-inside: avoid; }`.
- No image from the internet: if you need an image, use a file from the folder.

In chat (no folder), deliver the HTML in an ```html block: the person sees the preview and can save it.

## 3. Convert to PDF (Code mode)
Edge does this without opening a window. Run (adjust the paths):

```powershell
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe" }
$html = (Resolve-Path ".\relatorio.html").Path
& $edge --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="$PWD\relatorio.pdf" "file:///$($html -replace '\\','/')"
```

Then check that `relatorio.pdf` exists and is larger than zero bytes. If it is a spreadsheet that is already finished in Excel, `excel_no_app` with `pdf` is simpler.

## 4. Deliver
Say where the HTML (to edit) and the PDF are, and offer to open the PDF with `excel_abrir`.
