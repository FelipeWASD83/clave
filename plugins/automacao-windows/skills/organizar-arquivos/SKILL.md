---
name: organizar-arquivos
description: Use para arrumar uma pasta bagunçada (Downloads, Documentos, fotos): separa por tipo ou data, mostra a prévia antes de mover, nunca apaga e deixa um jeito de desfazer.
---

# Organizar arquivos

## 1. Olhar antes
- Liste a pasta (com subpastas, se fizer sentido) e conte: quantos arquivos de cada tipo, os maiores, os mais antigos.
- Ignore arquivos de sistema e escondidos (`desktop.ini`, `Thumbs.db`, os que começam com `~$`).

## 2. Propor a organização
Sugira um critério e mostre como ficaria, antes de mover qualquer coisa. Exemplo para Downloads:

| Pasta | O que vai para lá |
|---|---|
| Documentos | .pdf .docx .xlsx .txt .csv |
| Imagens | .jpg .png .webp .heic |
| Instaladores | .exe .msi |
| Compactados | .zip .rar .7z |
| Vídeos e áudios | .mp4 .mov .mp3 .wav |
| Outros | o resto |

Pergunte se a pessoa quer separar também por ano (ex.: `Imagens\2026`).

## 3. Mover com registro
- Mova, não apague. Duplicado com o mesmo nome no destino: acrescente ` (2)` ao nome, nunca sobrescreva.
- Grave `organizacao-AAAA-MM-DD.csv` com origem e destino de cada arquivo.
- Junto, crie `desfazer-organizacao.ps1`, que lê o CSV e devolve tudo ao lugar.
- Para muitas pastas ou para repetir todo mês, faça um script com a skill `automacao-windows:script-powershell-seguro`.

## 4. Fechar
Conte quantos arquivos foram para cada pasta, onde estão o registro e o desfazer, e o que ficou de fora (e por quê).
