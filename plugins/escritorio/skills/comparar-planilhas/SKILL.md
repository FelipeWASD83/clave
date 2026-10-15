---
name: comparar-planilhas
description: Use para descobrir o que mudou entre duas planilhas (versão antiga e nova, dois meses, dois sistemas): linhas que entraram, saíram ou mudaram, usando uma coluna como chave.
---

# Comparar planilhas

1. Leia as duas e descubra a **coluna-chave**, que identifica cada linha (código, CPF, número do pedido). Se não houver uma óbvia, pergunte. Sem chave, a comparação vira chute.
2. Confira se as colunas têm os mesmos nomes; se não, diga como você casou uma com a outra.
3. Compare e separe em três grupos:
   - **Entraram:** a chave só existe na nova.
   - **Saíram:** a chave só existe na antiga.
   - **Mudaram:** a chave existe nas duas, mas algum valor é diferente (diga qual coluna, o valor antigo e o novo).
4. Ignore diferenças que não são de verdade: espaço sobrando, maiúscula e minúscula, `10` e `10,00`. Diga que ignorou.
5. Entregue:
   - um resumo com a contagem de cada grupo;
   - uma planilha nova (ex.: `comparacao.xlsx`) com uma aba por grupo e as células que mudaram destacadas.
6. Nunca mexa nas duas planilhas originais.
