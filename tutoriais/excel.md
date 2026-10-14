---
titulo: Excel com o Claude
trilha: 3. Automação com o modo Code
ordem: 22
duracao: 8 min
resumo: Ler, criar e alterar planilhas: fórmulas, tabelas, gráficos, PDF, no chat e no modo Code.
---

O Claude mexe em [planilhas](#/aprender/glossario/planilha) do Excel de verdade: lê, cria, altera, põe [fórmulas](#/aprender/glossario/formula), formatação, tabelas, gráficos, filtros e listas de opção. Funciona de dois jeitos.

## No chat: mande a planilha, receba outra pronta

**Anexe** a planilha (.xlsx, ou .xls, que o Clave converte) e pergunte:

```experimentar
Crie uma planilha de controle de gastos mensal com as colunas Data, Descrição, Categoria (com lista de opções: Mercado, Contas, Transporte, Lazer, Outros) e Valor em reais. Coloque um total no fim, um resumo por categoria em outra aba e um gráfico de pizza com os gastos por categoria.
```

Quando ele cria ou altera uma planilha no chat, aparece um cartão com **Baixar** e **Abrir** (abre no Excel). A sua planilha original nunca é mexida: ele entrega uma cópia nova.

Exemplos de pedidos com uma planilha anexada:

- "Quais foram os 5 clientes que mais compraram?"
- "Tem algum valor estranho ou repetido aqui?"
- "Junte as colunas Nome e Sobrenome e me devolva a planilha."
- "Faça um gráfico de vendas por mês e exporte em PDF."

## No modo Code: planilhas da sua pasta

No modo Code ele trabalha direto nos arquivos da pasta, e isso abre automações maiores:

```experimentar-code
Nesta pasta tem várias planilhas de vendas, uma por mês. Junte todas numa planilha só chamada vendas-do-ano.xlsx, com uma aba por mês e uma aba Resumo com o total de cada mês e um gráfico de colunas.
```

Outros exemplos:

- "Leia relatorio.xlsx e escreva um resumo do que mudou em relação ao mês passado."
- "Para cada linha de clientes.xlsx, crie um arquivo de texto com uma carta de cobrança personalizada."
- "Destaque em vermelho as linhas com vencimento já passado."
- "Recalcule as fórmulas e exporte a aba Resumo em PDF."

Ele pede permissão antes de salvar mudanças (no modo Perguntar) e o **Desfazer mudanças** devolve a planilha como era.

## Fórmulas e o Excel do computador

O Clave escreve fórmulas, mas quem **calcula** é o Excel. Se o Microsoft Excel estiver instalado, o Claude consegue pedir para ele recalcular a planilha (e conferir os resultados), exportar em PDF e converter arquivos .xls e .csv em .xlsx. Sem o Excel, as fórmulas são calculadas quando você abre o arquivo.

## Cuidados

- **Feche a planilha no Excel** antes de pedir uma alteração nela: arquivo aberto não pode ser salvo.
- Planilhas com **imagens, formas ou macros** podem perder esses itens ao serem alteradas. Nesse caso, peça para ele salvar uma cópia com outro nome.
- Planilha enorme (dezenas de milhares de linhas): peça para ele trabalhar por partes ou com um script em Python, que é mais rápido.
