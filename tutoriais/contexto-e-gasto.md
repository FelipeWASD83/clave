---
titulo: Tokens, contexto e gasto
trilha: 1. Primeiros passos
ordem: 6
duracao: 5 min
resumo: Por que conversa longa fica cara, o que a régua mostra e como o teto do mês funciona.
---

## Tokens

A API cobra por [token](#/aprender/glossario/token), o pedacinho de texto que a IA lê e escreve. Mil tokens são umas 600 a 700 palavras em português. Fotos e PDFs também viram tokens (uma página de PDF dá algo como 1.500 a 3.000).

## Contexto: a memória da conversa

A cada mensagem, o Claude relê **a conversa inteira** (ele não guarda nada entre uma resposta e outra; quem manda o histórico é o Clave). Por isso:

- uma conversa de 50 mensagens custa mais por resposta que uma de 5;
- anexar um PDF grande no começo faz ele ser relido em toda resposta.

A **régua** embaixo da caixa de texto mostra quanto da [janela de contexto](#/aprender/glossario/janela-de-contexto) (até 1 milhão de tokens) já foi usado.

Duas coisas ajudam sozinhas:

- **Cache**: o começo repetido da conversa sai até 20 vezes mais barato. Já vem ligado.
- **Resumo automático**: quando a conversa passa de um tamanho (150 mil tokens, por padrão), a Anthropic resume o começo para caber e ficar mais barata. Aparece uma linha "A conversa foi resumida aqui".

Mesmo assim, a melhor economia é simples: **mudou de assunto, conversa nova**.

## O teto do mês

Em **Configurações > Limite de gasto** você define:

- o **teto por mês** em dólares;
- o **dia em que o mês vira** (use o dia em que seu crédito renova);
- o que fazer ao chegar no teto: **parar** ou **só avisar**;
- o **teto por tarefa** do modo Code, que pausa uma tarefa longa quando ela gasta demais.

O Clave avisa quando você passa de 50%, 80% e 95% do teto. Em **Uso e gasto** você vê o gasto por dia, por modelo e por conversa.

Na tela de conversa nova, o painel **Seu uso** mostra os tokens que você já gastou, há quantos dias seguidos usa, um mapa de calor dos dias, o modelo favorito, cada modelo nos últimos 7 dias e uma **projeção**: no ritmo dos últimos 14 dias, quanto o mês vai fechar e em que dia o teto acaba. Assina o Max? Pôr o teto em US$ 100 (ou 200) mostra quando o crédito do plano acaba.

Em **Preços e planos** fica o preço de cada modelo e a conta **API ou assinatura?**: você diz como usa o Claude normal (quantas vezes bate o limite de 5 horas, ou quantas mensagens manda por dia) e ele estima quanto isso custaria na API, modelo por modelo.

## Quanto custa, na prática

Valores aproximados, só para ter ideia:

- pergunta curta no Haiku: menos de US$ 0,001;
- resposta média no Sonnet: em torno de US$ 0,01;
- análise de um PDF de 20 páginas no Opus: em torno de US$ 0,10 a US$ 0,30;
- tarefa grande no modo Code (muitos passos): de US$ 0,20 a alguns dólares.

```experimentar
Explique de um jeito simples por que uma conversa muito longa com uma IA fica mais cara a cada resposta.
```
