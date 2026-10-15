---
titulo: Modelos e raciocínio: qual escolher
trilha: 1. Primeiros passos
ordem: 5
duracao: 5 min
resumo: Opus, Sonnet, Haiku e Fable, quanto cada um custa e quando vale pensar mais.
---

Na caixa de texto, o primeiro botão escolhe o [modelo](#/aprender/glossario/modelo) e o segundo, o [raciocínio](#/aprender/glossario/raciocinio). Os dois mudam a qualidade, a velocidade e o preço.

## Os modelos

| Modelo | Para quê | Preço por milhão de tokens (entrada / saída) |
|---|---|---|
| **Opus 5.5** | O mais inteligente do dia a dia. Bom para tudo, inclusive código e análises. | US$ 4 / US$ 20 |
| **Sonnet 5.5** | Quase tão bom quanto o Opus, mais rápido, metade do preço. | US$ 2 / US$ 10 |
| **Haiku 5.5** | Muito rápido e muito barato. Ótimo para perguntas simples, resumos e para aprender. | US$ 0,10 / US$ 0,50 |
| **Fable 5.1** | Raciocínio muito longo e escrita criativa. O mais caro. | US$ 10 / US$ 50 |

"Entrada" é o que você manda (mensagem, anexos, conversa anterior); "saída" é o que ele escreve. Um milhão de tokens é muito texto: algo como 700 mil palavras.

Atenção ao Haiku 5.5: quando um pedido passa de 100 mil tokens de entrada (conversa muito longa ou anexo grande), esse pedido inteiro custa 5 vezes mais.

**Regra prática:** comece no Haiku para coisas simples e no Opus para o que importa. Se o Haiku errar, gere outra resposta escolhendo o Opus (menu da setinha circular).

## O conselheiro de modelo

O Clave começa no **Haiku 5.5**, o mais barato. Desde a versão 5.0 ele é o padrão para todo mundo, inclusive para quem já usava o Clave: depois de atualizar, aparece uma vez um aviso com o modelo que você usava antes e os botões **Manter o Haiku** e **Voltar para o de antes**. Para você não ficar adivinhando, o próprio Haiku lê a conversa na primeira mensagem e depois a cada 5 e diz qual modelo faz aquela tarefa pelo menor preço: aparece um aviso como "Para esta tarefa, o Sonnet 5.5 deve ir melhor", com o motivo e os botões **Usar** e **Manter**. Cada avaliação custa uma fração de centavo.

Se preferir, deixe o Clave **trocar sozinho** (Configurações > Modelos > Deixar o Clave trocar o modelo sozinho): ele troca, avisa e mostra um botão para voltar. Numa conversa em que você voltar, ele não troca mais. Dá para desligar o conselheiro ali também.

Para escolher pelo menor preço sem perder qualidade, veja [O modelo certo pelo menor preço](#/aprender/modelo-certo-mais-barato).

## O raciocínio

Antes de responder, o Claude pode pensar. Os níveis são **Baixo**, **Médio**, **Alto**, **Muito alto** e **Máximo**:

- **Baixo**: rápido e barato. Conversa, perguntas diretas, textos curtos.
- **Médio**: o equilíbrio. Bom padrão para quase tudo.
- **Alto** ou mais: problemas difíceis, contas, planejamento, código complicado. Demora mais e gasta mais.

No Haiku e no Sonnet dá para **desligar o pensamento** (fica mais rápido). No Opus e no Fable ele sempre pensa um pouco; o nível controla quanto.

**Mostrar o raciocínio** exibe um resumo do que ele pensou, numa caixinha que abre e fecha. Não muda o preço.

O **modo rápido** (só no Opus) responde até 2,5 vezes mais rápido, pelo dobro do preço.

Quando vale pagar para ele pensar mais: [Raciocínio: quando vale pagar para ele pensar](#/aprender/raciocinio-sem-desperdicio).

## E se ele recusar?

Os modelos têm filtros de segurança. Às vezes um pedido normal é recusado por engano: nesse caso o Clave pede à Anthropic para tentar com outro modelo (dá para desligar em Configurações > Recursos). Se mesmo assim recusar, reformule o pedido.

```experimentar
Tenho R$ 2.000 guardados e quero começar a investir, mas não entendo nada. Me explique as opções mais seguras para iniciantes no Brasil, sem recomendar produto específico.
```
