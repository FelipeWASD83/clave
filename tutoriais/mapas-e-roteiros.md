---
titulo: Mapas e roteiros
trilha: 7. Respostas visuais
ordem: 62
duracao: 6 min
resumo: Lugares num mapa, a linha que liga os pontos, um roteiro de viagem dia a dia e o que fazer quando um endereço não aparece.
---

O widget de **mapa** marca lugares num mapa de verdade, numerados, com a lista ao lado. Serve para planejar um passeio, uma viagem, as visitas do dia ou só para ver onde as coisas ficam umas em relação às outras.

## O que o mapa mostra

- **Até 30 lugares**, numerados na ordem da lista. Clique num item da lista e o mapa vai até ele e abre um balão com a descrição.
- **A rota**: quando você pede, uma linha liga os pontos na ordem da lista. Atenção: é uma **linha reta** de um ponto ao outro, não o caminho pelas ruas. Ela mostra a ordem da visita, não o trajeto.
- **Ver todos os pontos**: o botão embaixo do + e do -, no canto do mapa, enquadra todos de novo.
- **Abrir no mapa**, dentro do balão, e o botão ao lado de cada item da lista abrem aquele lugar no site do OpenStreetMap, no seu navegador.
- **Zoom**: na conversa, clique no mapa antes de usar a roda do mouse (assim a roda continua rolando a conversa quando você só está passando). Em **Tela cheia**, a roda dá zoom direto.
- **Copiar como texto**: copia a lista de lugares com um link do OpenStreetMap para cada um, bom para mandar para quem vai junto.

## Como pedir

Diga os lugares (ou o que você procura) e se quer a rota ligando os pontos:

```experimentar
Mostre num mapa, com a rota na ordem da visita, um passeio de um dia a pé por Roma: Coliseu, Fórum Romano, Panteão, Fontana di Trevi e Piazza Navona. Para cada lugar, uma frase sobre o que ver e quanto tempo ficar.
```

## Um roteiro de viagem

Para uma viagem de vários dias, um mapa por dia funciona melhor que um mapa com tudo: cada dia fica com poucos pontos, e a linha mostra a ordem daquele dia. Na mesma resposta, o Claude pode juntar outros widgets: uma **linha do tempo** com manhã, tarde e noite e um **checklist** do que resolver antes de ir.

```experimentar
Monte um roteiro de 3 dias em Buenos Aires para um casal que gosta de comer bem e de andar a pé, com orçamento médio. Para cada dia, um mapa com a rota na ordem da visita e uma linha do tempo com manhã, tarde e noite. No fim, um checklist do que resolver antes de viajar. Confira na web os horários de funcionamento e diga a data em que viu.
```

O Haiku basta para um roteiro curto. Viagem longa, com várias cidades e trechos de transporte, vai melhor no Sonnet.

Três cuidados:

- **O tempo entre os lugares é estimativa.** O mapa não calcula trajeto e não vê trânsito, obra nem rua fechada. Para o caminho de verdade, use o app de mapas de sempre; o **Abrir no mapa** ajuda a achar o ponto.
- **Horário, ingresso e regra de entrada mudam.** Confira no site oficial antes de ir. Documento de viagem (passaporte, visto), só em fonte oficial.
- **Confira se cada ponto caiu no lugar certo.** Dê zoom ou clique em **Abrir no mapa**. Um ponto fora do lugar? Peça para ele usar o endereço completo daquele lugar.

## Como um endereço vira um ponto

O Claude manda cada lugar de um destes dois jeitos:

- **Com as coordenadas** (latitude e longitude): o ponto vai direto para o mapa.
- **Com o endereço**: o Clave procura o endereço no **Nominatim**, o serviço de busca de endereços do OpenStreetMap, e põe o ponto onde ele achou.

O Nominatim é gratuito e tem regras de uso, que o Clave segue: uma busca por segundo e até 15 endereços por mapa. Então um mapa com 10 endereços novos leva uns 10 segundos para aparecer. O que já foi achado fica guardado no seu computador por uns seis meses, e da segunda vez é na hora.

O endereço que vai para o mapa é enviado a esse serviço. Mande só o endereço: o nome e o telefone de quem mora lá não fazem falta (veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados)).

## Quando um endereço não é achado

Se o Nominatim não acha um endereço, aquele ponto fica de fora e o mapa aparece com os outros. O Claude recebe a lista do que ficou de fora e deve contar na resposta. Se nenhum ponto for achado, o mapa nem aparece, e o Claude recebe o aviso para mandar endereços mais completos ou as coordenadas.

O que fazer:

1. **Complete o endereço**: rua, número, bairro, cidade e país. "Rua das Flores, 120" existe em muitas cidades; "Rua das Flores, 120, Centro, Recife, Brasil" é um lugar só.
2. **Use o nome do lugar com a cidade**: "Museu do Louvre, Paris" costuma funcionar melhor que um endereço pela metade.
3. **Mande as coordenadas**: na maioria dos apps de mapas, clicar com o botão direito no lugar (ou segurar o dedo, no celular) mostra a latitude e a longitude. Copie e cole no pedido: "o ponto 3 fica em [latitude], [longitude]".
4. **Mude o texto antes de tentar de novo**: um "não achei" fica guardado por um dia, então pedir de novo com o mesmo endereço, letra por letra, dá o mesmo resultado.
5. **Mais de 15 endereços?** Os que passarem disso ficam de fora. Divida em dois mapas ou mande coordenadas.

Sem internet, a busca de endereços falha e o mapa fica sem o desenho das ruas, mas a lista de lugares continua no cartão. As áreas que você já viu ficam guardadas por pelo menos 7 dias.

## O mapa é do OpenStreetMap

Os mapas do Clave vêm do **OpenStreetMap**, um mapa do mundo feito por voluntários e livre para usar, desde que se diga de onde ele veio. Por isso todo mapa leva, no canto de baixo, o crédito **© OpenStreetMap** (com um link para a página de direitos) e o nome do **Leaflet**, a peça que desenha o mapa na tela. Se você tirar um print do mapa para mandar ou publicar, deixe o crédito à vista ou escreva "© colaboradores do OpenStreetMap": é a condição de uso.

O Clave segue as regras do serviço: baixa só os pedaços do mapa que aparecem na tela, guarda cada um por pelo menos 7 dias e se identifica em cada pedido. Os créditos ficam também em **Configurações > Atualizações e sobre**.

## Mais ideias

```experimentar
Quero conhecer 4 parques de uma cidade grande num sábado, saindo do centro de manhã e voltando à noite. Escolha uma cidade que você conheça bem, mostre os parques num mapa com a rota na ordem que evita ir e voltar, e diga quanto tempo ficar em cada um.
```

Para entregas e visitas de trabalho, veja a receita do mapa das entregas em [Para o pequeno negócio](#/aprender/receitas-pequeno-negocio).
