---
titulo: Para a casa e a vida pessoal
trilha: 9. Receitas por área
ordem: 83
duracao: consulta
resumo: Comparar antes de comprar, roteiro de viagem, planta de um cômodo, orçamento da casa, cardápio com lista de compras e o que assistir.
---

Pedidos prontos para a vida fora do trabalho. Clique em **Mandar para uma conversa nova**: o pedido vai para a caixa de texto, e você troca os detalhes (orçamento, cidade, medidas) pelos seus antes de enviar.

Muitas receitas daqui usam [widgets](#/aprender/widgets): cartões que o Claude desenha na conversa quando ajudam mais que texto (produtos e preços, mapas, recomendações, desenhos e plantas, gráficos, comparações, linhas do tempo e listas). Eles vêm ligados; o interruptor fica em **Configurações > Recursos > Widgets**.

O Clave começa no **Haiku 5.5**, o mais barato, e ele dá conta de quase tudo aqui. O conselheiro de modelo avisa quando a tarefa pede outro (veja [O modelo certo pelo menor preço](#/aprender/modelo-certo-mais-barato)).

| Receita | Onde | Modelo |
|---|---|---|
| Comparar antes de comprar | chat, com widget de produtos | Haiku |
| Roteiro de viagem | chat, com widget de mapa | Haiku (Sonnet para viagem longa) |
| Planta de um cômodo | chat, com desenho | Haiku |
| Orçamento da casa | chat, planilha e gráfico | Haiku |
| Cardápio e lista de compras | chat, com lista | Haiku |
| O que assistir | chat, com widget de recomendações | Haiku |
| Entender um documento | chat | Haiku (Sonnet para contrato longo) |

## 1. Comparar antes de comprar

```experimentar
Quero comprar uma air fryer de até R$ 500 para uma família de 4 pessoas. Pesquise na web e me mostre 4 opções num widget de produtos, com o preço, a loja e a data em que você viu cada preço. Diga qual você escolheria e por quê.
```

- **O que ele faz:** pesquisa na web e monta um **widget de produtos** com foto, preço e loja, e escreve qual escolheria. O preço é o que a busca achou, no dia em que ele pesquisou: confira na loja antes de pagar. Quem decide e quem paga é você. Mais em [Comparar produtos e preços](#/aprender/compras-e-precos).
- **Modelo:** o Haiku basta. Cada busca custa US$ 0,01, além dos tokens das páginas lidas; uma comparação dessas costuma ficar em poucos centavos de dólar (é uma estimativa).
- **Bom saber:** as fotos vêm de outros sites e, por segurança, só carregam quando você clica nelas. Isso muda em **Configurações > Recursos > Widgets > Fotos de sites de fora**, mas o recomendado é deixar como está. Por que, e o que mais uma página pode tentar: [Quando uma página ou arquivo tenta dar ordens ao Claude](#/aprender/injecao-de-instrucoes).

## 2. Roteiro de viagem

```experimentar
Monte um roteiro de 3 dias em Lisboa para um casal que gosta de comer bem e de andar a pé, com orçamento médio. Para cada dia: manhã, tarde e noite, com o tempo a pé entre os lugares. Mostre os lugares num mapa e confira na web os horários de funcionamento, dizendo a data em que viu.
```

- **O que ele faz:** monta o roteiro dia a dia e marca os lugares num **widget de mapa** (os mapas vêm do OpenStreetMap, pela internet). Mais em [Mapas e roteiros](#/aprender/mapas-e-roteiros).
- **Modelo:** o Haiku basta para um roteiro curto. Viagem longa, com várias cidades e trechos de transporte, vai melhor no Sonnet.
- **Cuidado:** horário, preço de ingresso e regra de entrada mudam. Confira no site oficial antes de ir, e documentos de viagem (passaporte, visto) só em fonte oficial.

## 3. A planta de um cômodo

```experimentar
Meu quarto tem 3 m por 3,5 m. A porta fica no canto de uma das paredes de 3 m e a janela no meio da parede em frente. Quero que caibam uma cama de casal (1,38 por 1,88 m), um guarda-roupa de 1,60 m de largura por 0,55 m de fundo e uma escrivaninha de 1 m. Desenhe a planta vista de cima com duas arrumações diferentes e diga qual deixa mais espaço livre para andar.
```

- **O que ele faz:** desenha as plantas num **widget de desenho**, vistas de cima e com as medidas, e compara as duas. Dá para anexar uma foto do cômodo junto. Mais em [Plantas, desenhos e gráficos](#/aprender/plantas-e-desenhos).
- **Modelo:** o Haiku basta para um cômodo. Muitas restrições (vários móveis, tomadas, um pilar no meio) vão melhor no Sonnet.
- **Cuidado:** é um esboço para pensar a arrumação, não um projeto. Meça de novo antes de comprar um móvel, e obra, parede e parte elétrica são com um profissional.

## 4. Orçamento da casa

```experimentar
Crie uma planilha de orçamento mensal da casa com as abas Entradas, Gastos fixos (aluguel, luz, água, internet), Gastos variáveis (mercado, transporte, lazer) e Resumo. No Resumo, o total de cada aba, quanto sobra no mês e um gráfico de pizza dos gastos por categoria. Preencha com valores de exemplo para eu trocar pelos meus.
```

- **O que ele faz:** cria a [planilha](#/aprender/glossario/planilha) com as fórmulas e o gráfico, e mostra **Baixar** e **Abrir**. Mais em [Excel com o Claude](#/aprender/excel).
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** só quer entender para onde o dinheiro foi? Anexe o extrato que o banco deixa baixar em planilha ou CSV e peça "um gráfico dos meus gastos por categoria": ele desenha o **gráfico** na conversa. Antes de anexar, apague o que não faz falta para a análise, como o número da conta e o CPF (veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados)). Ele ajuda a organizar, mas não é consultor financeiro.

## 5. Cardápio e lista de compras

```experimentar
Sugira 5 jantares rápidos para a semana (até 30 minutos cada) para 2 pessoas, sem carne de porco. Depois junte os ingredientes numa lista de compras só, separada por seção do mercado, como uma lista de marcar.
```

- **O que ele faz:** escreve as receitas e junta os ingredientes num **widget de lista** (uma checklist), já separado por seção do mercado.
- **Modelo:** o Haiku basta. Sem pensar (no segundo botão da caixa de texto, desmarque **Pensar antes de responder**) sai ainda mais barato.
- **Cuidado:** alergia ou dieta por motivo de saúde, diga logo no pedido e confira os rótulos: ele pode errar.
- **Melhor ferramenta:** quer uma lista que fica guardada e que você marca no mercado? Peça um pequeno app de lista de compras (veja [Criar páginas e pequenos apps](#/aprender/paginas-e-apps)).

## 6. O que assistir

```experimentar
Gosto de séries de suspense curtas, com poucas temporadas, e não gosto de terror. Recomende 5 séries e 3 filmes num widget de recomendações, com uma frase sobre cada um e onde dá para assistir no Brasil. Confira na web onde cada um está e diga a data em que viu.
```

- **O que ele faz:** monta um **widget de recomendações** com as capas e o porquê de cada escolha. Cite no pedido títulos que você já viu e de que gostou: as sugestões melhoram muito.
- **Modelo:** o Haiku basta.
- **Bom saber:** o catálogo dos serviços de streaming muda todo mês; por isso o pedido manda conferir na web e dizer a data. As capas vêm de outros sites e só carregam com um clique, como as fotos dos produtos.

## 7. Entender um documento

Anexe o PDF ou uma foto e mande:

```experimentar
Anexei o contrato de aluguel que vão me pedir para assinar. Explique em linguagem simples o que cada cláusula diz, destaque multas, reajuste e o que acontece se eu sair antes do prazo, e me dê uma lista de perguntas para fazer antes de assinar.
```

- **O que ele faz:** lê o documento e traduz o "juridiquês" para palavras do dia a dia. Funciona também com conta de luz, carta do banco ou bula.
- **Modelo:** o Haiku basta para uma conta ou uma carta curta. Contrato longo vai melhor no Sonnet.
- **Cuidado:** ele não substitui advogado, contador ou médico numa decisão séria; ele ajuda a entender e a preparar as perguntas. Se der, cubra CPF, RG e número de conta antes de anexar (veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados)).

## Dicas para a casa

- **Preço e horário vêm da busca, com data:** peça sempre a loja e o dia em que ele viu, e confira antes de pagar ou sair de casa.
- **Assunto novo, conversa nova:** a viagem numa conversa, o orçamento em outra. Fica mais barato e ele se confunde menos (veja [Conversas enxutas](#/aprender/conversas-enxutas)).
- **Prefere a resposta só em texto?** Desligue os widgets em **Configurações > Recursos > Widgets**.
