---
titulo: Comparar produtos e preços
trilha: 7. Respostas visuais
ordem: 61
duracao: 6 min
resumo: Busca na web, o widget de produtos e o de comparação, e os cuidados com preço e link antes de comprar.
---

Antes de comprar alguma coisa, o Claude pode fazer a parte chata: procurar opções, juntar preço, loja e nota e pôr tudo lado a lado. Ele **não compra nada**: quem decide e quem paga é você, na loja.

## Como funciona

1. Você diz o que quer, quanto pode gastar e o que importa para você (tamanho, marca, garantia, prazo de entrega).
2. Ele pesquisa na web. Para isso, o botão **Web** da caixa de texto precisa estar ligado (ele já vem ligado). Cada busca aparece como um passo **Pesquisou na web**: clique nele para ver as páginas que a busca achou.
3. Ele monta um **widget de produtos** e, se você pedir, um **widget de comparação** com os detalhes lado a lado.
4. Ele escreve, em poucas linhas, qual escolheria e por quê.

O Haiku, o modelo mais barato, dá conta (veja [O modelo certo pelo menor preço](#/aprender/modelo-certo-mais-barato)). Cada busca custa US$ 0,01, além dos tokens das páginas lidas; uma comparação dessas costuma ficar em poucos centavos de dólar (é uma estimativa).

## O widget de produtos

Cada opção vem num cartão com nome, preço, loja, nota (quando ele achou uma) e uma observação curta, como "frete grátis". A opção mais barata ganha a etiqueta **Mais barato** (só entre preços na mesma moeda). Em cima, **Menor preço** e **Ordem original** reorganizam a lista.

Embaixo vem a data: **Preços vistos em [dia]; confira na loja.** O widget nem aparece sem essa data. É o dia em que a busca achou o preço, não o preço de agora.

O botão **Ver na loja** abre a página no seu navegador de sempre. Ele só aparece quando o Claude tem o link de verdade: ele é orientado a nunca inventar link de produto, e sem o link certo o produto fica sem o botão.

As fotos só aparecem quando você clica em **Mostrar imagens** (o porquê está em [Widgets](#/aprender/widgets)).

```experimentar
Quero comprar um fone de ouvido sem fio para usar no ônibus, de até R$ 300. Pesquise na web e me mostre 4 opções num widget de produtos, com preço, loja, nota e a data em que você viu cada preço. Depois diga qual você escolheria e por quê, em 3 linhas.
```

## O widget de comparação

Preço é só um critério. Para ver o resto, peça uma comparação: uma tabela com até 6 colunas (as opções) e uma linha para cada critério. O Claude marca com uma estrela o melhor de cada linha, e o rodapé **Melhor em** conta quantas linhas cada opção venceu.

```experimentar
Compare lado a lado, num widget de comparação, 3 aspiradores robôs de até R$ 1.500: preço, potência de sucção, se passa pano, tempo de bateria, barulho, garantia e nota dos compradores. Pesquise na web, marque o melhor de cada linha e diga a data em que viu os dados.
```

Diga quais critérios importam para você. "Vou usar num apartamento pequeno, com um gato que solta pelo" muda a resposta muito mais que "qual o melhor aspirador".

## Preço muda: confira na loja

O preço do widget é uma fotografia do dia da busca, e às vezes nem isso:

- a página que a busca leu pode estar desatualizada;
- promoção acaba, estoque acaba, e o preço muda com o CEP, o frete, o cupom e a forma de pagamento;
- a nota pode ser de outra versão do produto, ou de outra loja;
- o Claude pode ler errado um número da página.

Antes de pagar, abra a página da loja e confira **preço, frete, prazo e o modelo exato** (cor, tamanho, voltagem). Se o preço da loja for bem diferente do widget, acredite na loja.

## Link: só o que a página mostrou

Um link de produto só merece confiança se veio de uma página que a busca mostrou de verdade. Antes de clicar:

1. Pare o mouse em cima de **Ver na loja**: aparece o endereço. Confira se é o site da loja que o cartão diz (`nomedaloja.com.br`, e não `nomedaloja-ofertas.xyz`).
2. Clique no passo **Pesquisou na web** e veja se esse site está entre as páginas que a busca achou. Os numerozinhos no meio do texto também levam às fontes.
3. Na dúvida, não clique: entre no site da loja pelo endereço que você já conhece, ou pela busca do próprio site.

Um link que não aparece em lugar nenhum da busca pode ter sido inventado, pode estar errado ou pode ter vindo de uma página que tenta empurrar um site falso. Promoção boa demais com link estranho é um golpe velho conhecido. Mais em [Quando uma página ou arquivo tenta dar ordens ao Claude](#/aprender/injecao-de-instrucoes).

## Conferir a página com o Claude, no modo Code

No modo Code, o [navegador](#/aprender/navegador) do Clave (só na janela do Clave) deixa o Claude abrir a página do produto e ler o que está escrito nela. A página aparece na aba **Navegador** do painel ao lado, e você vê o mesmo que ele. Antes de usar o site da loja pela primeira vez na tarefa, ele mostra um cartão com o endereço da loja e espera o seu OK (menos no modo Livre); com o site liberado, abrir, ler, tirar print e rolar ele faz sozinho. Clicar e digitar pedem o seu OK a cada vez nos modos Perguntar e Aceitar edições; e senha, código de acesso e cartão quem digita é você. Ele pode olhar a página, mas a compra é sua.

```experimentar-code
Abra no navegador a página deste produto: [cole o link da loja]. Leia o preço, as formas de pagamento e o prazo de entrega que aparecem na página e me diga em 5 linhas. Não clique em nada.
```

Quando aparecer o cartão do site, clique em **Permitir**: o site fica liberado até a resposta terminar, e ele abre e lê a página sem perguntar de novo.

## Dicas

- **Dê o contexto**: para quem é, onde vai usar, o que você já tem. Comparação boa depende de critério bom.
- **Peça a data e a loja de cada preço**, sempre. Sem data, você não sabe se o preço é de hoje ou de meses atrás.
- **Uma compra por conversa**: o fone numa conversa, o aspirador em outra. Fica mais barato e ele se confunde menos (veja [Conversas enxutas](#/aprender/conversas-enxutas)).
- **Desconfie do elogio sem motivo**: se a resposta exalta uma loja ou um produto sem mostrar por quê, pergunte "de onde veio essa informação?".
