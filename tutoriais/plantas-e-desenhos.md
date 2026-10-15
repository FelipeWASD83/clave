---
titulo: Plantas, desenhos e gráficos
trilha: 7. Respostas visuais
ordem: 63
duracao: 7 min
resumo: A planta de um cômodo com medidas, diagramas simples, gráficos a partir de uma planilha, linhas do tempo e checklists.
---

Quatro widgets servem para organizar o que você já tem na mão: medidas, números, datas e tarefas. O **desenho** vira planta e diagrama, o **gráfico** mostra os números, a **linha do tempo** põe as datas em ordem e o **checklist** guarda o que falta fazer. O que vale para todos (copiar, tela cheia, baixar) está em [Widgets](#/aprender/widgets).

## A planta de um cômodo

O widget de **desenho** faz plantas vistas de cima, com medidas. O Claude monta o desenho com formas simples:

| Forma | Serve para |
|---|---|
| retângulo | móveis, tapete, bancada (pode ser girado) |
| círculo | mesa redonda, vaso, poltrona |
| linha e seta | janela, porta, o caminho de passagem |
| polígono | um cômodo em L, um canto cortado |
| texto | nomes e observações dentro do desenho |
| cota | a linha de medida: o número aparece sozinho |

Atrás vai uma grade, e o rodapé diz quanto vale cada quadrado (por exemplo, **Cada quadrado da grade: 0,5 m**). As medidas podem ser em metros ou centímetros.

Quanto mais medidas você der, melhor sai:

- o tamanho do cômodo (largura e comprimento);
- onde fica a porta, quanto ela mede e para que lado abre;
- onde ficam janelas, tomadas, ar-condicionado ou um pilar;
- a largura e a profundidade de cada móvel;
- o que não pode mudar ("a cama fica na parede da janela").

Medida que você não deu, ele supõe. Peça para ele dizer o que supôs.

```experimentar
Minha sala tem 4 m por 5 m. A porta de entrada tem 80 cm e fica no canto de uma das paredes de 4 m; a janela ocupa o meio da parede em frente. Quero um sofá de 2,10 por 0,90 m, uma TV num rack de 1,60 m, uma mesa redonda de 1 m de diâmetro com 4 cadeiras e um tapete. Desenhe a planta vista de cima, com as cotas das paredes, deixando pelo menos 70 cm de passagem entre os móveis. Depois diga se cabe mesmo.
```

Para explorar o desenho: **Aproximar**, **Afastar** e **Ver o desenho inteiro**; arraste para mover; clique no desenho para dar zoom com a roda do mouse. No teclado, + e - aproximam e afastam, as setas movem e 0 mostra tudo.

Para mudar, peça na conversa: "vira o sofá para a janela", "testa com uma mesa quadrada". Quer comparar? Peça duas ou três arrumações: cada uma vira um desenho.

Para levar: **Baixar imagem** dá uma **Imagem PNG** (para mandar a alguém ou colar num documento) ou um **Desenho SVG** (amplia sem perder qualidade), com o título e a legenda. **Copiar como texto** lista cada forma com a posição e o tamanho.

### Uma planta simples de casa

O mesmo widget desenha vários cômodos juntos, para ter uma ideia de como eles se encaixam:

```experimentar
Desenhe a planta simples de um apartamento de 2 quartos com 55 m²: sala e cozinha integradas, 2 quartos, 1 banheiro e uma área de serviço. Use medidas comuns, marque as portas e escreva a área de cada cômodo dentro dele. É só para eu ter uma ideia de como os cômodos se encaixam.
```

### O que o desenho não é

É um esboço para pensar a arrumação, não um projeto. O Claude calcula as posições, mas pode errar uma conta ou deixar dois móveis encostados. O Clave só confere se as formas não saem muito do desenho; se a porta bate no armário, quem percebe é você. Confira as cotas, meça de novo antes de comprar um móvel, e obra, parede, gás e parte elétrica são com um profissional.

O Haiku basta para um cômodo. Muitas restrições (vários móveis, tomadas, um pilar no meio) vão melhor no Sonnet.

## Diagramas simples

O desenho também faz diagramas: caixas e setas para um passo a passo, um organograma pequeno, o caminho de um pedido. Nesses, medida não importa.

```experimentar
Desenhe um diagrama simples, com caixas e setas, do caminho de um pedido numa loja online: pedido feito, pagamento aprovado, separação, envio, entrega e, se precisar, troca. Use uma cor para o caminho normal e outra para a troca.
```

## Gráficos

O widget de **gráfico** tem quatro formas:

| Forma | Serve para |
|---|---|
| **Barras** | comparar quantidades: gasto por categoria, vendas por vendedor |
| **Linhas** | ver como algo muda com o tempo: a conta de luz mês a mês |
| **Pizza** | ver as partes de um todo: para onde foi o salário |
| **Área** | como linhas, com a parte de baixo pintada: bom para volume ao longo do tempo |

Passe o mouse (ou use as setas do teclado) para ver cada valor. Cabem até 8 séries (por exemplo, "este ano" e "ano passado") e até 60 rótulos; com mais que isso, peça para agrupar por mês ou por categoria. Na pizza, mais de 12 fatias viram 11 fatias e um "Outros".

### A partir de uma planilha

No chat, anexe a planilha pelo clipe da caixa de texto (.xlsx ou .csv) e peça:

```experimentar
Anexei a planilha dos gastos da casa. Some os gastos por categoria e mostre num gráfico de pizza. Depois, num gráfico de linhas, mostre o total de cada mês. Em 3 linhas, diga o que mais pesou.
```

Numa planilha grande, ele lê as primeiras linhas e busca o resto quando precisa. Antes de anexar um extrato, apague o que a análise não usa, como o número da conta (veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados)). No modo Code vale o mesmo para uma planilha da pasta: "leia vendas.xlsx e mostre as vendas por mês num gráfico de barras".

### Gráfico na conversa ou na planilha?

São duas coisas diferentes:

- O **widget** é para olhar e decidir agora: aparece na hora e dá para baixar como imagem. Ele não muda se você mudar a planilha depois.
- Um gráfico **dentro do arquivo do Excel** fica junto dos dados e acompanha quando você muda os números. Peça "crie uma planilha com um gráfico" (veja [Excel com o Claude](#/aprender/excel)).

## Linhas do tempo

O widget de **linha do tempo** põe acontecimentos em ordem, cada um com data, título e, se quiser, uma descrição curta. A data é texto livre: vale "1969", "março", "Semana 2" ou "Dia 3, 14h". Cabem até 40 acontecimentos.

Bom para o cronograma de uma obra ou de um evento, um plano de estudo, a história de um assunto ou as etapas de um processo.

```experimentar
Monte numa linha do tempo o cronograma de uma festa de aniversário daqui a 6 semanas: o que fazer em cada semana (convites, local, bolo, decoração, lembrancinhas) e, no dia da festa, hora a hora.
```

## Checklists

O widget de **checklist** é uma lista para marcar, com até 60 itens. O que você marca fica salvo: feche o Clave, abra a conversa de novo e as marcas continuam lá, com o topo mostrando quantos já foram feitos (**3 de 10 feitos**). **Copiar como texto** leva a lista com [x] nos itens feitos, pronta para colar numa mensagem.

```experimentar
Faça um checklist, na ordem certa, de tudo o que eu preciso fazer para tirar o passaporte pela primeira vez no Brasil. Confira na web o que o site oficial pede e diga a data em que viu.
```

O checklist mora na conversa, no computador. Quer uma lista que vai com você ao mercado, no celular? Copie como texto e mande para você mesmo, ou peça um pequeno app (veja [Criar páginas e pequenos apps](#/aprender/paginas-e-apps)).

## Dicas

- **Dê os números.** O Claude não adivinha medida nem valor; o que ele supõe, ele deve dizer.
- **Diga para que serve**: "para mostrar ao marceneiro", "para colar no relatório", "para eu decidir hoje". Ele escolhe o widget e o nível de detalhe por isso.
- **Um assunto por conversa**: a planta numa, o orçamento em outra. Fica mais barato e ele se confunde menos (veja [Conversas enxutas](#/aprender/conversas-enxutas)).
