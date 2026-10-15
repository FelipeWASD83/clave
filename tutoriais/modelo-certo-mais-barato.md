---
titulo: O modelo certo pelo menor preço
trilha: 5. Economizar crédito
ordem: 41
duracao: 7 min
resumo: Quanto cada modelo cobra por mensagem, a escada do Haiku ao Opus, o conselheiro e o preço escondido de trocar no meio da conversa.
---

Escolher o [modelo](#/aprender/glossario/modelo) é a decisão que mais mexe na conta: entre o mais barato e o mais caro, a mesma mensagem custa quase 100 vezes mais. A lição [Modelos e raciocínio](#/aprender/modelos-e-raciocinio) apresenta os quatro. Aqui o foco é gastar o mínimo sem perder qualidade onde ela importa.

## Quanto custa uma mensagem em cada um

Valores da tabela **Preço de cada modelo**, em **Preços e planos** (com raciocínio):

| Modelo | Mensagem curta | Mensagem média | Mensagem longa | Mensagens curtas com US$ 1 |
|---|---|---|---|---|
| **Haiku 5.5** | US$ 0,0005 | US$ 0,0012 | US$ 0,0027 | cerca de 2.000 |
| **Sonnet 5.5** | US$ 0,0094 | US$ 0,023 | US$ 0,048 | cerca de 100 |
| **Opus 5.5** | US$ 0,019 | US$ 0,045 | US$ 0,095 | cerca de 50 |
| **Fable 5.1** | US$ 0,046 | US$ 0,11 | US$ 0,22 | cerca de 20 |

"Curta" é pergunta rápida, com poucas trocas; "média" tem várias trocas e textos de uma página; "longa" tem documentos anexados, código ou conversa comprida. São tamanhos típicos que o Clave supõe. Quando você já tiver 10 respostas ou mais de um modelo, a conta **API ou assinatura?**, na mesma página, mostra também o custo pelo seu uso real.

Um detalhe do Haiku: quando a conversa passa de **100 mil tokens**, ele cobra 5 vezes mais por tudo (a tabela avisa: "5x acima de 100 mil tokens"). Mesmo assim continua mais barato que o Sonnet, mas o salto existe. A lição [Conversas enxutas](#/aprender/conversas-enxutas) mostra como fugir dele.

## Para que serve cada um

O conselheiro de modelo do Clave escolhe com estes critérios, e eles servem para você também:

| Modelo | Use para |
|---|---|
| **Haiku 5.5** | perguntas e conversas do dia a dia, textos curtos, resumos, traduções, e-mails, explicar algo, tarefas de rotina e arquivos pequenos |
| **Sonnet 5.5** | textos longos ou caprichados, documentos e planilhas grandes, código de tamanho médio, análises com vários passos, ou quando o Haiku já errou ou se perdeu |
| **Opus 5.5** | tarefas difíceis e importantes: código grande ou com muitos arquivos, decisões com muito em jogo, raciocínio longo, revisar algo com olho crítico |
| **Fable 5.1** | só raciocínio muito longo ou escrita criativa longa, quando vale pagar bem mais |

## A escada: comece embaixo

Desde a versão 5.0, as conversas novas começam no **Haiku 5.5**, também para quem já usava outro modelo (quem usava viu um aviso, uma vez, com os botões **Manter o Haiku** e **Voltar para o de antes**). A ideia é subir só quando precisa:

1. **Haiku** primeiro.
2. Errou ou ficou raso? Passe o mouse na resposta, clique na setinha circular (**Gerar outra resposta**) e escolha o **Sonnet**. Você paga só aquela resposta no Sonnet.
3. Ainda não ficou bom? Faça o mesmo com o **Opus**.
4. O **Fable** fica para o caso raro em que nem o Opus deu conta, ou para escrita criativa longa.

Compare: cinco perguntas simples no Opus custam uns US$ 0,09. As mesmas cinco no Haiku, refazendo uma delas no Opus porque ficou fraca, custam uns US$ 0,03. Mesmo errando de vez em quando, começar embaixo sai muito mais barato do que deixar o Opus "por garantia".

## O conselheiro faz isso por você

Para você não ter que adivinhar, o Haiku lê a conversa na 1ª mensagem e depois a cada 5 (na 6ª, na 11ª...) e diz se outro modelo faz a tarefa pelo menor preço. Aparece um aviso como "Para esta tarefa, o Sonnet 5.5 deve ir melhor", com o motivo e os botões **Usar o Sonnet 5.5** e **Manter o Haiku 5.5**.

- Cada avaliação custa em torno de US$ 0,0003 (estimativa pelo preço do Haiku). Numa conversa de 50 mensagens ele avalia 10 vezes: menos de meio centavo de dólar no total.
- Ele também manda **descer**: de Opus para Haiku numa tradução curta, por exemplo.
- Em **Configurações > Modelos** dá para deixar ele **trocar sozinho** (ele troca, avisa e mostra um botão para voltar; numa conversa em que você voltar, ele não troca mais) ou desligar o conselheiro.
- Ele não roda em rotinas, em etapas de fluxo, nos ajudantes das lições, em **Gerar outra resposta** (ali quem escolhe é você) nem em comando ou skill que já fixa o modelo.

## Trocar no meio da conversa tem preço

O cache é de cada modelo. Quando você troca de modelo numa conversa longa, o modelo novo lê a conversa inteira sem o desconto e ainda paga para guardá-la no cache. Numa conversa de 50 mil tokens, a primeira mensagem no modelo novo gasta uns US$ 0,13 só para ler a conversa no Sonnet, e uns US$ 0,25 no Opus (estimativa).

Por isso:

- **troque cedo**: é por isso que o conselheiro já olha a 1ª mensagem;
- **para uma parte difícil no meio de uma conversa longa**, abra uma conversa nova no modelo forte só com o que ele precisa (o trecho do texto e o pedido), em vez de trocar o modelo da conversa inteira.

## Rascunho barato, revisão cara

Um jeito de ter a qualidade do Opus pagando pouco: faça o vai e vem no Haiku (ideias, rascunho, ajustes) e, no fim, abra uma conversa nova, escolha o Opus e mande só o texto pronto:

```experimentar
Revise o texto abaixo com olho crítico: aponte erros, partes confusas e o que está sobrando, em tópicos curtos. Não reescreva tudo, só me mostre o que mudar.

[cole aqui o texto final]
```

Vinte trocas no Haiku (uns US$ 0,01) e uma revisão no Opus (uns US$ 0,05) custam uma fração de vinte trocas no Opus (uns US$ 0,30). São estimativas, mas a diferença é desse tamanho.

## Modelos antigos

Em **Configurações > Modelos > Mostrar modelos antigos** aparecem modelos anteriores que a Anthropic ainda vende. Quase nunca compensa: o Haiku 4.5 custa 10 vezes o Haiku 5.5, e o Opus 5 custa mais que o Opus 5.5.

## Onde o modelo fica fixo

Em alguns lugares o conselheiro não entra, e quem escolhe é você, uma vez só:

- **Rotinas**: o modelo vem no formulário da rotina. Rotina simples (conferir, resumir, avisar) vai bem no Haiku.
- **Fluxos**: no cartão do fluxo dá para trocar o modelo de cada etapa antes de rodar. Ponha o Haiku nas etapas simples, como pesquisar ou juntar resultados.
- **Configurações > Modelos**: o modelo com que cada conversa nova começa, no chat e no Code.

Atalho: **/modelo haiku** (ou sonnet, opus, fable) troca o modelo da conversa sem abrir o menu.

```experimentar
Traduza para o inglês, de um jeito natural e educado: "Oi, tudo bem? Queria confirmar a nossa reunião de quinta às 15h. Se precisar mudar o horário, é só me avisar."
```

Depois de receber a resposta no Haiku, use **Gerar outra resposta** com o Opus e compare o custo embaixo das duas. Para uma tradução curta, a diferença de qualidade costuma ser pequena; a de preço, não.
