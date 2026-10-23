---
titulo: Fluxos: vários modelos numa tarefa só
trilha: 3. Automação com o modo Code
ordem: 25
duracao: 6 min
resumo: Como dividir uma tarefa grande em etapas, cada uma no modelo certo, sabendo o custo antes.
---

Numa conversa normal, um [modelo](#/aprender/glossario/modelo) faz tudo. Num **fluxo**, a tarefa vira etapas, e cada etapa vai para quem faz melhor (ou mais barato):

| Etapa | Quem faz | Por quê |
|---|---|---|
| Planejar | Opus 5.5 | é o mais caprichoso para pensar no plano |
| Fazer | Sonnet 5.5 | faz o trabalho pesado pela metade do preço |
| Testar | Sonnet 5.5 | roda os testes e confere o resultado |
| Revisar | Opus 5.5 | olha tudo de novo com olho crítico |

Cada etapa recebe o objetivo e o relatório das etapas anteriores, e no fim o Claude junta tudo e te conta o que foi feito.

## Ele pede o seu OK

Fluxo gasta mais que uma resposta comum (são várias conversas por trás). Por isso o Clave não roda um fluxo sozinho: primeiro aparece um cartão com:

- as etapas, o modelo e o nível de raciocínio de cada uma (você pode trocar ali mesmo, por exemplo pôr o Haiku numa etapa simples);
- o que cada etapa pode fazer (ler, mudar arquivos, rodar comandos, pesquisar na web);
- a **estimativa de custo** (uma faixa, porque depende de quanto cada etapa precisa ler);
- o **teto do fluxo**: se a soma passar desse valor, o fluxo para.

Só depois de **Rodar o fluxo** alguma coisa acontece. Durante o fluxo, clique numa etapa para ver o que ela está fazendo; se uma etapa quiser mudar um arquivo, o pedido de permissão aparece ali.

No modo **Livre** o cartão não aparece: o fluxo roda direto, com o teto de gasto sugerido, e as etapas também não pedem permissão (só comando que apaga). Se quiser conferir antes, use outro modo.

## Como começar um fluxo

- Peça: "faça isso como um fluxo" e o Claude monta as etapas.
- Ou digite `/fluxo` na caixa de mensagem e escolha um fluxo pronto (Planejar, fazer e testar; Pesquisa profunda; Revisão em paralelo; Planilha grande; Escrever e revisar).
- Ou vá em **Fluxos e agentes** na barra da esquerda, escolha um e clique em *Usar no chat* ou *Usar no Code*.

Algumas etapas rodam **ao mesmo tempo** (por exemplo, três pesquisas em paralelo), o que deixa o fluxo mais rápido sem gastar mais.

## Agentes

Cada etapa pode ser feita por um **agente**: um "especialista" com instruções, modelo e ferramentas próprios. O Clave já vem com seis (planejador, executor, testador, revisor, pesquisador e redator) e os plugins trazem outros. Você cria os seus em **Fluxos e agentes > Agentes**: dê um nome, diga o que ele faz, escolha o modelo e o que ele pode usar. Os agentes usam o mesmo formato do Claude Code (arquivos em `.claude/agents`).

## Quando vale a pena

Vale para tarefa grande, em que errar custa caro ou que tem partes bem diferentes (pesquisar, escrever, conferir). Para pergunta simples ou tarefa pequena, uma conversa normal é mais rápida e mais barata.

```experimentar
Pesquise as 3 formas mais baratas de fazer backup automático das minhas fotos no Windows e monte uma comparação. Faça isso como um fluxo, com as pesquisas em paralelo no Haiku.
```
