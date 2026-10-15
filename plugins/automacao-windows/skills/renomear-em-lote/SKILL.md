---
name: renomear-em-lote
description: Use para renomear muitos arquivos de uma vez seguindo um padrão (data no nome, numeração, tirar texto repetido, padronizar maiúsculas), com prévia e jeito de desfazer.
---

# Renomear em lote

1. Entenda o padrão que a pessoa quer e mostre **antes e depois** de 5 a 10 arquivos reais, numa tabela.
2. Regras:
   - nunca mude a extensão (`.jpg` continua `.jpg`);
   - nunca deixe dois arquivos com o mesmo nome: se colidir, numere (`foto-001.jpg`, `foto-002.jpg`);
   - evite caracteres que o Windows não aceita: `\ / : * ? " < > |`;
   - data no nome no formato `AAAA-MM-DD` (fica na ordem certa quando o Windows ordena por nome);
   - para usar a data da foto, prefira a data de criação do arquivo e diga que foi essa.
3. Depois do OK, renomeie e grave `renomeacao-AAAA-MM-DD.csv` (nome antigo, nome novo) e um `desfazer-renomeacao.ps1`.
4. Conte quantos foram renomeados e quantos ficaram de fora, e por quê.
