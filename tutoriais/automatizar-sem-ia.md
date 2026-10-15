---
titulo: Automatizar sem pagar a IA toda vez
trilha: 5. Economizar crédito
ordem: 45
duracao: 7 min
resumo: Uma rotina paga a cada rodada, para sempre; um programa feito uma vez roda de graça. Como decidir, as contas e os pedidos prontos.
---

Uma [rotina](#/aprender/rotinas) é ótima para o que precisa de julgamento: ler, entender e decidir. Para o que é sempre igual, existe um caminho bem mais barato: pedir ao modo Code, **uma vez**, um pequeno programa sem IA (um [script](#/aprender/glossario/script)) e deixar o [Agendador de Tarefas](#/aprender/glossario/agendador-de-tarefas) do Windows rodar no horário. A lição [Um app de pedidos sem IA](#/aprender/app-de-pedidos-sem-ia) mostra um exemplo completo. Aqui você aprende a decidir e vê outras trocas que economizam.

## A conta: rotina contra programa

Cada rodada de uma rotina é uma conversa nova: as instruções, o pedido, o que ela lê e a resposta. O preço depende do modelo e do que ela lê. Veja dois exemplos de preço por rodada (estimativas: algo perto de uma rodada simples no Haiku e de uma no Sonnet):

| Frequência | Rodadas por mês | A US$ 0,003 por rodada | A US$ 0,03 por rodada |
|---|---|---|---|
| De hora em hora | cerca de 720 | US$ 2,16 | US$ 21,60 |
| A cada 3 horas | cerca de 240 | US$ 0,72 | US$ 7,20 |
| Todo dia | cerca de 30 | US$ 0,09 | US$ 0,90 |
| Toda semana | cerca de 4 | US$ 0,01 | US$ 0,13 |
| **Programa sem IA**, em qualquer frequência | | **US$ 0** | **US$ 0** |

O programa custa só a conversa no Code que o construiu (para um programa simples, de alguns centavos no Haiku a menos de US$ 1 no Sonnet, numa estimativa) e depois roda de graça, todo dia, quantas vezes quiser. As rotinas do Clave rodam no máximo de hora em hora; um programa no Agendador pode rodar a cada 15 minutos, sem custo nenhum.

Quer saber o custo real de uma rotina sua? Em **Rotinas**, clique em **Rodar agora** e depois em **Ver a última**: o custo aparece embaixo da resposta. Multiplique pelas rodadas do mês.

## Precisa de IA ou não?

| Precisa de IA (rotina) | Não precisa (programa) |
|---|---|
| Ler texto livre e decidir o que importa ("quais e-mails precisam de resposta hoje?") | Mover, renomear, copiar ou juntar arquivos |
| Resumir documentos que mudam a cada vez | Passar dados de um formato fixo para uma planilha |
| Escrever algo novo: uma resposta, um post, um comentário sobre os números | Conferir regras fixas: "linha sem preço", "valor acima de 1.000" |
| Classificar coisas que não têm regra clara | Gerar o mesmo relatório com os números atualizados |
| | Fazer cópia de segurança de uma pasta |

Uma pergunta resolve quase sempre: **se eu escrevesse as regras num papel, qualquer pessoa faria igual, toda vez?** Se sim, é programa.

## O meio-termo

Às vezes só um pedaço precisa de julgamento: os pedidos chegam quase sempre no mesmo formato, mas de vez em quando um cliente escreve do jeito dele. Aí o programa faz todo o resto e chama o Claude só para esse pedaço, no Haiku. A lição [Um app de pedidos sem IA](#/aprender/app-de-pedidos-sem-ia) mostra como, e quanto custa: menos de um centavo de dólar por pedido (estimativa).

## Trocas que economizam

| Em vez desta rotina | Peça este programa |
|---|---|
| Toda manhã: "organize os arquivos novos de Downloads" | Um script que separa por tipo, agendado no Windows (veja a [Primeira automação](#/aprender/primeira-automacao)) |
| A cada 3 horas: "confira se a planilha de pedidos tem linha sem preço" | Um script que confere e mostra um aviso do Windows quando acha |
| Toda sexta: "copie a pasta Contratos para o backup" | Um script de cópia, agendado |
| Todo dia: "renomeie as fotos novas com a data" | Um script de renomear |
| Todo mês: "some os gastos por categoria nesta planilha" | Fórmulas no Excel, pedidas uma vez (veja [Excel com o Claude](#/aprender/excel)) |
| Toda manhã: "leia os e-mails e diga quais precisam de resposta" | Esta precisa de julgamento: fica como rotina, no Haiku |

## Como pedir o programa

- Na página **Rotinas**, o botão **Montar no Code sem IA** abre o modo Code com um pedido pronto: o Claude pergunta o que entra, o que sai e de quanto em quanto tempo, diz se dá para fazer sem IA e monta o programa com modo de teste, registro do que fez e agendamento no Windows.
- O plugin **Vendas** tem o comando **/vendas:automatizar** e a skill **vendas:automacao-sem-ia**, feitos para isso.
- O plugin **Automação no Windows** tem skills para agendar tarefas, renomear em lote, organizar pastas e criar scripts de PowerShell que mostram antes o que vão fazer. Veja [Plugins e comandos de barra](#/aprender/plugins-e-comandos).

Seja qual for o caminho, peça sempre: **modo de teste** (mostra o que faria, sem fazer), **registro** do que fez (um arquivo .log), senhas no **Gerenciador de Credenciais** do Windows (nunca no código nem na conversa) e o comando do Agendador **mostrado antes de rodar**, com o jeito de pausar.

```experimentar-code
Quero um script, sem IA, que confira a planilha pedidos.xlsx desta pasta e me avise com uma notificação do Windows se alguma linha estiver sem preço ou sem data. Ele precisa de um modo de teste e de um arquivo de registro. Me explique como rodar com dois cliques e, no fim, me mostre o comando para agendar a cada 3 horas no Agendador de Tarefas, sem rodar ainda.
```

## Fórmula em vez de conta

Pedir ao Claude para fazer a mesma conta todo mês é pagar sempre pelo mesmo resultado. Peça **a fórmula**, uma vez, e a planilha calcula sozinha para sempre:

```experimentar
Tenho uma planilha do Excel com a data na coluna A, a categoria na coluna B e o valor na coluna C. Me dê as fórmulas do Excel em português para: o total de cada categoria, o total do mês atual e a média por dia. Diga onde colar cada uma, sem texto longo.
```

## Quando a rotina é a escolha certa

Se a tarefa precisa mesmo de julgamento, a rotina é o caminho. Deixe ela barata:

- **Haiku** no formulário, a não ser que a tarefa seja difícil de verdade;
- **Teto por rodada** baixo, para uma rodada que der errado não gastar muito;
- **Pode pesquisar na web** desmarcado, se a resposta não depende de nada atual;
- um pedido que diga o tamanho da resposta ("em no máximo 5 tópicos");
- a frequência mais baixa que resolve: todo dia em vez de de hora em hora, se der.
