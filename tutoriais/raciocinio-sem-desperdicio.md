---
titulo: Raciocínio: quando vale pagar para ele pensar
trilha: 5. Economizar crédito
ordem: 42
duracao: 5 min
resumo: O pensamento é cobrado como texto escrito. Quanto custa, quando subir o nível, quando desligar e quando o modo rápido compensa.
---

Antes de responder, o Claude pode pensar: planejar, conferir contas, comparar caminhos. Esse pensamento é cobrado **pelo preço de saída**, igual à resposta, mesmo quando você não lê. Ligar **Mostrar o raciocínio** só mostra um resumo dele: o preço é o mesmo, mostrando ou não.

## Quanto custa pensar

O pensamento é medido em [tokens](#/aprender/glossario/token), como a resposta. Quanto custa só a parte do pensamento, em alguns tamanhos:

| Tokens de raciocínio | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 | Fable 5.1 |
|---|---|---|---|---|
| 1.000 | US$ 0,0005 | US$ 0,01 | US$ 0,02 | US$ 0,05 |
| 5.000 | US$ 0,0025 | US$ 0,05 | US$ 0,10 | US$ 0,25 |
| 20.000 | US$ 0,01 | US$ 0,20 | US$ 0,40 | US$ 1,00 |

Para comparar: a resposta de uma mensagem curta tem uns 400 tokens. Um raciocínio longo pode custar muito mais que a própria resposta.

O raciocínio é adaptativo: o Claude decide quanto pensar, e o nível que você escolhe empurra isso para cima ou para baixo. Por isso o mesmo nível pode sair barato numa pergunta fácil e caro num problema difícil.

## Os níveis e os padrões

O segundo botão da caixa de texto escolhe o nível: **Baixo**, **Médio**, **Alto**, **Muito alto** e **Máximo**. O Clave começa no **Médio** no chat e no **Alto** no modo Code (dá para mudar em **Configurações > Modelos**). No menu, o padrão de cada modelo aparece marcado com "(padrão do modelo)".

- No **Haiku** e no **Sonnet** dá para desligar: desmarque **Pensar antes de responder**. Ele responde mais rápido e gasta menos (com o pensamento desligado, o nível vai até o Alto).
- No **Opus** e no **Fable** ele sempre pensa um pouco. Para gastar menos, baixe o nível.

## Quando vale pagar

Um guia para começar (ajuste ao seu caso):

| Tarefa | Raciocínio |
|---|---|
| Conversa, pergunta direta, tradução, e-mail curto, resumo | Baixo, ou desligado no Haiku e no Sonnet |
| O dia a dia em geral | Médio |
| Contas, planejamento, comparar várias opções, código com erro difícil | Alto |
| Problema difícil em que errar custa caro | Muito alto ou Máximo, de preferência numa conversa só para isso |

## Faça isto em vez daquilo

- **Em vez de subir o modelo, suba o raciocínio primeiro.** O Haiku errou uma conta? Mude o raciocínio para **Alto**, clique no lápis da sua mensagem e mande de novo. Pensar no Haiku é tão barato (5.000 tokens custam US$ 0,0025) que sai mais em conta que uma única mensagem curta no Sonnet (US$ 0,0094). Se ainda errar, aí suba o modelo, como mostra [O modelo certo pelo menor preço](#/aprender/modelo-certo-mais-barato).
- **Em vez de Máximo "para garantir", use Médio e confira.** O Máximo não tem limite de raciocínio: numa tarefa simples, ele só gasta mais.
- **No modo Code, tarefa mecânica não precisa do Alto.** Renomear, mover ou juntar arquivos: Médio ou Baixo. Deixe o Alto para código e para erro difícil. Veja [O modo Code sem desperdício](#/aprender/code-sem-desperdicio).
- **Problema difícil no meio de uma conversa leve?** Abra uma conversa nova com o nível alto só para ele, em vez de deixar a conversa inteira pensando muito.

## Escolha no começo

Trocar o nível, ligar ou desligar o pensamento no meio de uma conversa longa faz a próxima mensagem pagar a conversa inteira de novo (o cache deixa de valer). Numa conversa curta isso quase não pesa; numa longa, escolha no começo ou abra uma conversa nova para a parte difícil.

Atalho: **/esforco baixo** (ou medio, alto, muito-alto, maximo) troca o nível sem abrir o menu.

## O modo rápido

No **Opus**, o menu do raciocínio tem o **Modo rápido**: responde até 2,5 vezes mais rápido, **pelo dobro do preço**. Vale quando você está parado esperando a resposta para seguir um trabalho com pressa. No resto do tempo, deixe desligado. Como trocar o nível, ligar o modo rápido no meio de uma conversa longa também faz a próxima mensagem pagar tudo de novo.

```experimentar
Um produto custava R$ 80. Teve um desconto de 10% e, depois, mais um desconto de 15% sobre o novo preço. Qual é o preço final e qual seria o desconto único equivalente? Mostre a conta em poucas linhas.
```

Mande primeiro com o raciocínio no **Baixo**. Depois mude para o **Alto**, clique no lápis da sua mensagem e mande de novo. Compare o custo embaixo das duas respostas e veja se a resposta mudou.
