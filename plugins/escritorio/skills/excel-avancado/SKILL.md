---
name: excel-avancado
description: Use ao criar, mudar ou analisar planilhas do Excel (.xlsx) com fórmulas, formatação, tabelas, gráficos, filtros ou listas de opção. Garante que a original não se perde e que os números conferem.
---

# Excel avançado

## Antes de mexer
1. Leia a planilha inteira com `excel_ler` (todas as abas) e descreva para a pessoa o que encontrou: abas, colunas, onde estão os totais, fórmulas importantes.
2. **Nunca salve por cima da original sem a pessoa pedir.** Use o campo `saida` de `excel_alterar` para criar uma cópia (ex.: `vendas - revisada.xlsx`).
3. Planilha com macro (`.xlsm`) ou com gráfico e imagem que precisam ficar intactos: avise que salvar pelo Clave pode perder essas partes e prefira a cópia.

## Fórmulas
- Escreva as fórmulas **em inglês e com vírgula** (`=SUM(B2:B10)`, `=IF(C2>0,"ok","falta")`, `=VLOOKUP(A2,Tabela!A:C,3,FALSE)`). O Excel em português mostra `SOMA`, `SE` e `PROCV` sozinho.
- O Clave grava a fórmula mas não calcula. Para ver o resultado, peça `excel_no_app` com `recalcular` (precisa do Excel instalado) e leia de novo.
- Prefira referência a uma célula de parâmetro (ex.: taxa em `F1`) a número escrito dentro da fórmula.

## Deixar apresentável
- Cabeçalho em negrito, congelar a primeira linha, filtro no cabeçalho.
- Valores em dinheiro com formato `"R$" #,##0.00`; datas como data, não como texto.
- Transforme o intervalo em **tabela** quando a pessoa for continuar preenchendo.
- Formatação condicional para chamar atenção (ex.: vermelho quando negativo), sem exagero de cores.
- Gráfico só quando ajudar a entender; título claro e eixos com nome.

## No fim
- Confira os totais: some de novo de outro jeito e compare. Diga quais números você conferiu.
- Liste o que mudou (aba por aba) e onde está a cópia.
- Se a pessoa quiser ver, ofereça `excel_abrir` para abrir no Excel, ou `excel_no_app` com `pdf` para gerar um PDF.
