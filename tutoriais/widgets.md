---
titulo: Widgets: quando o Claude desenha a resposta
trilha: 7. Respostas visuais
ordem: 60
duracao: 7 min
resumo: Os oito cartões que o Claude monta na conversa, como pedir um, o que cada botão faz e por que as fotos esperam o seu clique.
---

Nem toda resposta fica boa em texto. Quatro preços lado a lado, cinco lugares de uma viagem ou a planta de um quarto ficam muito mais claros num desenho. Para isso o Claude tem os **widgets**: cartões que ele monta dentro da conversa quando eles ajudam mais que texto. Na lista de passos aparece **Mostrou um widget**, e o cartão vem logo embaixo.

## Os oito tipos

| Widget | O que mostra | Um pedido de exemplo |
|---|---|---|
| **Produtos** | foto, preço, loja e nota de cada opção, com a mais barata marcada | "Compare 4 fones sem fio de até R$ 300 num widget de produtos" |
| **Mapa** | lugares numerados num mapa, com uma linha que liga os pontos na ordem, se você quiser | "Mostre num mapa os 5 museus que eu não posso perder em Paris" |
| **Recomendações** | séries, filmes, jogos, animes, livros, músicas ou podcasts, com o porquê de cada um | "Me indique 5 podcasts de história para ouvir no ônibus" |
| **Desenho** | plantas vistas de cima e diagramas simples, com medidas | "Desenhe a planta da minha sala de 4 por 5 m com o sofá e a TV" |
| **Gráfico** | barras, linhas, pizza ou área | "Faça um gráfico de pizza com os gastos que eu colei abaixo" |
| **Comparação** | uma tabela lado a lado, com uma estrela no melhor de cada linha | "Compare ônibus, bicicleta e carro para ir ao trabalho, lado a lado" |
| **Linha do tempo** | datas e acontecimentos em ordem | "Mostre numa linha do tempo as etapas da Revolução Francesa" |
| **Checklist** | uma lista para marcar, que fica salva | "Faça um checklist do que levar numa viagem de praia de 3 dias" |

As lições seguintes desta trilha mostram os tipos mais úteis em detalhe: [Comparar produtos e preços](#/aprender/compras-e-precos), [Mapas e roteiros](#/aprender/mapas-e-roteiros) e [Plantas, desenhos e gráficos](#/aprender/plantas-e-desenhos).

## Como pedir um

Quase sempre você nem precisa pedir: o Claude decide sozinho quando um cartão ajuda. Para garantir, diga o tipo no pedido ("num mapa", "num gráfico de barras", "como checklist", "num widget de produtos", "lado a lado") e o que você quer ver nele: os critérios da comparação, as medidas da planta, a ordem dos lugares.

Depois do widget, o Claude escreve pouco. Ele é orientado a não repetir no texto o que o cartão já mostra e a comentar só o que ajuda a decidir.

Quer mudar alguma coisa? Peça na mesma conversa: "tira o terceiro item", "troca para gráfico de linhas", "põe a mesa perto da janela". Ele monta um cartão novo, e o anterior continua lá em cima para comparar.

Os widgets aparecem no chat e no modo Code. Numa [rotina](#/aprender/rotinas) ou numa etapa de um [fluxo](#/aprender/fluxos-e-agentes) eles não existem, porque ninguém está olhando.

Quanto custa: o cartão é feito dos dados que o Claude escreve, então custa como uma resposta desse tamanho. Uma planta com dezenas de móveis custa mais que um checklist de 5 itens. Preço de produto e endereço pedem busca na web, que custa US$ 0,01 por busca (veja [Para onde vai o seu crédito](#/aprender/para-onde-vai-o-credito)).

## Os botões do cartão

No canto de cima de cada widget:

- **Copiar como texto**: copia uma versão em texto, para colar numa mensagem, num e-mail ou num documento. Os produtos vão com preço, loja e link; os lugares do mapa, com um link do OpenStreetMap para cada um; o gráfico vira uma tabela; o checklist vem com [x] no que já foi marcado.
- **Tela cheia**: abre o cartão grande, numa janela por cima da conversa. No mapa e no desenho, ali a roda do mouse já dá zoom direto.
- **Baixar imagem** (só no desenho e no gráfico): **Imagem PNG**, para mandar ou colar em documentos, ou **Desenho SVG**, que dá para ampliar sem perder qualidade. A imagem leva o título em cima e a legenda embaixo.

E cada tipo tem os seus controles: os produtos se reorganizam por **Menor preço** ou **Ordem original**; o mapa e o desenho aproximam, afastam e voltam a mostrar tudo; no gráfico, passe o mouse (ou use as setas do teclado) para ver cada valor; no checklist, o topo mostra quantos itens já foram feitos.

O widget fica guardado com a conversa: ao abrir de novo, ele está lá, e o checklist continua com o que você marcou, mesmo depois de fechar o Clave.

## As fotos esperam o seu clique

Produtos e recomendações podem ter foto (do produto, da capa). Essas fotos moram em outros sites e, **por padrão, não carregam sozinhas**: aparece o botão **Mostrar imagens**, e elas só vêm quando você clica.

O motivo: buscar uma foto avisa o site de onde ela vem. Uma página maliciosa, lida durante uma busca, poderia fazer o Claude usar como "foto" um endereço com pedaços da conversa escondidos dentro dele. Quando a foto carrega, o endereço chega ao site, e os dados vão junto. Sem o clique, nada sai sozinho. Se a resposta parecer estranha (um produto que você não pediu, uma loja que você nunca citou), não clique. Mais sobre isso em [Quando uma página ou arquivo tenta dar ordens ao Claude](#/aprender/injecao-de-instrucoes).

Sem foto, o cartão funciona igual: nas recomendações, o Clave desenha uma capa própria, com as iniciais do título.

A opção fica em **Configurações > Recursos > Widgets > Fotos de sites de fora**: **Só carregar quando eu clicar (recomendado)** ou **Carregar sempre**. O recomendado é deixar como está.

O mapa é diferente: ele carrega sozinho, porque os pedaços do mapa vêm sempre do mesmo lugar, o OpenStreetMap, e passam pelo Clave. Mais em [Mapas e roteiros](#/aprender/mapas-e-roteiros).

## De onde vêm os dados

O cartão só desenha o que o Claude mandou. Preços, lojas, notas e endereços ele é orientado a tirar da busca na web, com a data em que viu, e nunca inventar link de produto: sem o link certo, o produto fica sem o botão da loja. O widget de produtos nem aparece sem a data dos preços.

Mesmo assim, ele pode errar. O widget deixa a resposta mais fácil de ler, não mais certa: confira o que importa antes de decidir.

## Desligar

- **Numa resposta**: peça "responda só em texto, sem widget".
- **Sempre**: em **Configurações > Recursos > Widgets**, desligue **Deixar o Claude mostrar widgets**. Vale para as conversas novas e as respostas seguintes; os cartões que já apareceram continuam onde estão.

## Experimente

Três pedidos que não precisam de busca na web, então saem baratos:

```experimentar
Monte um checklist com 12 coisas para levar numa viagem de praia de 3 dias, para uma família com duas crianças pequenas.
```

```experimentar
Compare lado a lado, num widget de comparação, ônibus, bicicleta e carro para ir a um trabalho a 8 km de casa: custo por mês, tempo, saúde, dia de chuva e onde deixar. Marque o melhor de cada linha e diga, em 2 linhas, qual você escolheria.
```

```experimentar
Mostre num gráfico de barras como eu passo um dia: dormir 7 h, trabalho 8 h, transporte 2 h, celular 3 h, refeições 1,5 h, exercício 0,5 h e o resto livre. Depois diga, em 3 linhas, onde dá para ganhar tempo.
```
