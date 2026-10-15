---
name: relatorio-em-pdf
description: Use quando a pessoa pedir um relatório, documento ou resumo para imprimir ou mandar em PDF. Monta uma página bonita em HTML e converte em PDF pelo Microsoft Edge, que vem no Windows.
---

# Relatório em PDF

## 1. Conteúdo primeiro
- Junte os dados (planilha, arquivos, o que a pessoa disse) e confira os números antes de formatar.
- Estrutura: título, data, resumo de 3 a 5 linhas no topo, depois as seções, e no fim as fontes ou observações.

## 2. Página HTML
Crie `relatorio.html` (ou o nome que fizer sentido) na pasta, num arquivo só, com o CSS dentro da página:
- Fonte do sistema (`font-family: "Segoe UI", Arial, sans-serif`), corpo em 11pt, títulos maiores.
- Página A4 para impressão: `@page { size: A4; margin: 18mm; }`.
- Tabelas com cabeçalho destacado e linhas alternadas; números alinhados à direita.
- Evite quebra no meio de tabela pequena: `tr, figure { break-inside: avoid; }`.
- Sem imagem da internet: se precisar de imagem, use arquivo da pasta.

No chat (sem pasta), entregue o HTML num bloco ```html: a pessoa vê a prévia e pode salvar.

## 3. Converter em PDF (modo Code)
O Edge faz isso sem abrir janela. Rode (ajuste os caminhos):

```powershell
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe" }
$html = (Resolve-Path ".\relatorio.html").Path
& $edge --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="$PWD\relatorio.pdf" "file:///$($html -replace '\\','/')"
```

Depois confira que `relatorio.pdf` existe e tem tamanho maior que zero. Se for uma planilha que já está pronta no Excel, `excel_no_app` com `pdf` é mais simples.

## 4. Entregar
Diga onde estão o HTML (para editar) e o PDF, e ofereça abrir o PDF com `excel_abrir`.
