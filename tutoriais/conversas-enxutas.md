---
titulo: Conversas enxutas: nova conversa, /compact e projetos
trilha: 5. Economizar crédito
ordem: 43
duracao: 7 min
resumo: Quando a conversa longa fica cara de verdade, como levar o assunto para uma conversa nova e como deixar os projetos leves.
---

A lição [Tokens, contexto e gasto](#/aprender/contexto-e-gasto) diz que conversa longa fica mais cara. É verdade, com um detalhe que muda a estratégia: graças ao [cache](#/aprender/glossario/cache), enquanto você está respondendo, reler a conversa custa pouco. A conta sobe de verdade em dois momentos, e é neles que vale agir.

## Quanto custa a próxima mensagem

Estimativa com os preços do Clave, para uma pergunta de uns 200 tokens e uma resposta de uns 500, sem contar o raciocínio (que soma o mesmo valor nas duas situações). O tamanho da conversa é o número que a régua mostra embaixo da caixa de texto.

| Tamanho da conversa | Haiku, respondendo logo | Haiku, depois de uma pausa | Opus, respondendo logo | Opus, depois de uma pausa |
|---|---|---|---|---|
| 10 mil tokens | US$ 0,0004 | US$ 0,0016 | US$ 0,016 | US$ 0,064 |
| 50 mil tokens | US$ 0,0008 | US$ 0,0066 | US$ 0,024 | US$ 0,26 |
| 90 mil tokens | US$ 0,0012 | US$ 0,012 | US$ 0,032 | US$ 0,46 |
| 120 mil tokens | US$ 0,0077 | US$ 0,077 | US$ 0,038 | US$ 0,61 |

O Sonnet fica no meio do caminho entre os dois.

## Os dois saltos

**1. A pausa.** O cache guarda a conversa por 5 minutos depois da última mensagem. Passou disso, a próxima mensagem paga a conversa inteira de novo, e ainda 25% a mais para guardar outra vez. No Opus, com 50 mil tokens, é a diferença entre US$ 0,024 e US$ 0,26.

**2. Os 100 mil tokens do Haiku.** Acima de 100 mil tokens, o Haiku cobra 5 vezes mais por tudo. Repare na tabela: de 90 mil para 120 mil, a próxima mensagem fica 6 vezes mais cara. E com 120 mil, depois de uma pausa, o Haiku chega a custar mais que o Opus respondendo logo.

Fora desses dois momentos, dividir não faz tanta diferença: sem pausas, 60 trocas numa conversa só custam no Opus uns US$ 1,00, e as mesmas 60 trocas em 6 conversas de 10 custam uns US$ 0,94 (estimativa). Ainda assim, **assunto novo, conversa nova**: conversa comprida e cheia de assuntos também confunde mais o Claude, e resposta errada é a coisa mais cara que existe.

## Nova conversa, /compact ou resumo automático?

| | O que faz | Quando usar |
|---|---|---|
| **Conversa nova** | começa do zero, só com as instruções | assunto novo, ou você voltou depois de muito tempo |
| **/resumo** + conversa nova | o Claude escreve o que foi decidido, feito e o que falta; você leva para uma conversa nova | conversa longa que você quer continuar mais tarde, no Sonnet ou no Opus |
| **/compact** | troca a conversa por um resumo, dentro da mesma conversa | conversa longa no Haiku, ou quando você quer continuar no mesmo lugar |
| **Resumo automático** | a Anthropic resume o começo quando a conversa passa do tamanho definido | rede de segurança, sem você fazer nada |

## Levar o assunto para uma conversa nova

1. Logo depois de uma resposta (com o cache ainda valendo), digite **/resumo** e mande. Ele vira um pedido normal: "Resuma esta conversa em tópicos curtos: o que foi decidido, o que foi feito (com os arquivos) e o que ainda falta."
2. Copie o resumo.
3. Abra uma conversa nova e cole, junto com o que você quer fazer agora.

Como o /resumo é uma mensagem comum, ele lê a conversa pelo preço do cache: no Opus, com 50 mil tokens, fica perto de US$ 0,03 (estimativa). Depois disso, a conversa nova começa leve, e uma pausa nela custa pouco.

```experimentar
Estou continuando um trabalho de outra conversa. Resumo do que já foi feito:

[cole aqui o resumo]

Agora quero: [o próximo passo]. Responda de forma curta e não repita o que já está no resumo.
```

## /compact: prático, mas lê tudo pelo preço cheio

Digite **/compact** e o Clave pede à Anthropic um resumo que guarda o que você pediu e como gosta das coisas, as decisões, os arquivos mexidos, números e nomes importantes, o que deu errado e o que ficou pendente. Aparece uma linha marcando onde a conversa foi compactada (clique nela para ler o resumo), e as próximas mensagens partem dali.

- O /compact lê a conversa inteira **sem o desconto do cache**. Com 50 mil tokens, isso dá uns US$ 0,006 no Haiku, US$ 0,12 no Sonnet e US$ 0,24 no Opus (estimativas).
- **No Haiku, é barato: use antes dos 100 mil tokens**, para não entrar na faixa que custa 5 vezes mais.
- **No Sonnet e no Opus**, ele compensa quando você ainda vai trabalhar bastante na mesma conversa, com pausas no meio: cada pausa depois dele custa pouco. Se a ideia é só recomeçar o assunto, o /resumo com uma conversa nova sai mais barato.
- Ele usa o modelo da conversa, só funciona depois de pelo menos duas mensagens suas e espera a resposta em andamento terminar.
- O resumo perde detalhes. Se você vai precisar de um trecho exato depois (um texto, uma tabela), copie antes.

## O resumo automático

Em **Configurações > Recursos**, **Resumir conversas muito longas** vem ligado: quando a conversa passa do valor em **Resumir a partir de (tokens)** (padrão 150 mil, entre 50 mil e 900 mil), a Anthropic resume o começo sozinha. Cada resumo é uma chamada a mais, quando acontece.

Usa o Haiku em conversas muito longas? Baixar esse valor para 90.000 faz o resumo acontecer antes da faixa de 5 vezes do Haiku. O preço: a regra vale para todos os modelos, e o resumo perde detalhes mais cedo.

## Edite em vez de corrigir

Quando uma resposta sai errada, a tentação é mandar "não, não era isso". Só que a resposta errada fica na conversa e é relida em todas as mensagens seguintes. Em vez disso, **clique no lápis da sua mensagem**, deixe o pedido mais claro e mande de novo: a resposta errada sai do caminho (ela continua guardada nas setas **< 1/2 >**, mas não vai mais junto). O mesmo vale para **Gerar outra resposta**.

## Decida no começo

Trocar o modelo, o raciocínio ou ligar e desligar a Web no meio de uma conversa longa faz a próxima mensagem pagar a conversa inteira de novo. Escolha no começo. Se a conversa mudou de natureza (de bate-papo para uma análise pesada, por exemplo), é a hora de uma conversa nova.

## Anexos e projetos enxutos

- Uma página de PDF vira algo como 1.500 a 3.000 tokens. Para perguntar sobre uma parte, mande só aquela parte (copie o trecho ou salve as páginas que importam).
- Os arquivos de um [projeto](#/aprender/projetos) entram no começo de **cada conversa nova** do projeto, e são relidos a cada mensagem. Um arquivo de 40 mil tokens (um PDF de umas 20 páginas) custa, para começar cada conversa, uns US$ 0,005 no Haiku, US$ 0,10 no Sonnet e US$ 0,20 no Opus.
- Em vez de um manual inteiro no projeto, peça ao Claude uma ficha de uma ou duas páginas com o que importa e ponha a ficha no projeto. O manual completo fica para quando precisar de verdade.

```experimentar
Vou colar abaixo um documento longo. Transforme ele numa ficha de no máximo uma página, só com o que alguém precisa consultar no dia a dia (regras, números, prazos, nomes), em tópicos curtos. Não invente nada que não esteja no texto.

[cole aqui o documento]
```
