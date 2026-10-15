---
titulo: Para onde vai o seu crédito
trilha: 5. Economizar crédito
ordem: 40
duracao: 7 min
resumo: O que a Anthropic cobra em cada resposta, o que pesa mais na conta e os gastos que acontecem sem você ver.
---

A lição [Tokens, contexto e gasto](#/aprender/contexto-e-gasto) explicou o básico: a API cobra por [token](#/aprender/glossario/token) e conversa longa fica mais cara. Esta trilha vai mais fundo, com números tirados dos preços que o próprio Clave usa nas contas. Comece por aqui: para economizar, primeiro você precisa saber para onde o dinheiro vai.

## O que entra na conta

Cada resposta do Claude é cobrada em quatro partes:

| Parte | O que é | Preço |
|---|---|---|
| **Entrada** | Tudo o que o Clave manda: a sua mensagem, a conversa até ali, os anexos, as instruções do Clave e a descrição das ferramentas | o preço de entrada do modelo |
| **Escrita no cache** | A parte nova da conversa, guardada para a próxima mensagem sair mais barata | 1,25 vez o preço de entrada |
| **Leitura do cache** | A parte da conversa que já estava guardada | de 10 a 40 vezes menos que a entrada, conforme o modelo |
| **Saída** | O que o Claude escreve: a resposta, o [raciocínio](#/aprender/glossario/raciocinio) (mesmo o que você não lê) e os pedidos para usar ferramentas | 5 vezes o preço de entrada, em todos os modelos |

E por fora: **cada busca na web custa US$ 0,01**, mais os tokens do que ela trouxe.

## Uma mensagem curta, por dentro

Na tabela **Preço de cada modelo** (em **Preços e planos**, na barra da esquerda), o Clave calcula quanto custa uma mensagem típica. Para a mensagem curta, ele supõe 400 tokens novos, 3.000 que vêm do cache (as instruções e o começo da conversa), 500 guardados no cache, 400 de resposta e 300 de raciocínio. Veja essa conta no Opus 5.5:

| Pedaço | Tokens | Custo |
|---|---|---|
| A sua mensagem e o que é novo | 400 | US$ 0,0016 |
| Instruções e histórico, lidos do cache | 3.000 | US$ 0,0006 |
| A parte nova, guardada no cache | 500 | US$ 0,0025 |
| Resposta e raciocínio | 700 | US$ 0,0140 |
| **Total** | | **US$ 0,0187** |

Uns **três quartos do preço são o que o Claude escreve**. No Haiku 5.5 a proporção é parecida, só que o total é uns 40 vezes menor: US$ 0,0005.

Daí sai a primeira regra: **resposta mais curta e menos raciocínio economizam em qualquer modelo**. Pedir "responda em 5 linhas" ou "sem introdução" não é só questão de gosto.

## O que o Claude relê a cada mensagem

O Claude não lembra de nada sozinho: a cada mensagem, o Clave manda tudo de novo. Isso inclui:

- a conversa inteira, com as respostas dele;
- os anexos (um PDF anexado no começo vai junto em todas as mensagens seguintes);
- as instruções e os arquivos do [projeto](#/aprender/projetos), se a conversa for de um;
- as instruções do Clave e a descrição das [ferramentas](#/aprender/glossario/ferramenta): alguns milhares de tokens antes da sua primeira palavra (no modo Code, mais de 10 mil; é uma estimativa).

O [cache](#/aprender/glossario/cache) é o que deixa isso barato: o que já foi mandado antes custa de 10 a 40 vezes menos. Mas ele tem prazo.

## O prazo de 5 minutos

O cache guarda a conversa por **5 minutos** depois do último uso, e cada mensagem renova o prazo. Se você para por mais tempo (foi almoçar, entrou numa reunião), a próxima mensagem paga a conversa inteira de novo, e ainda 1,25 vez o preço de entrada, para guardar tudo outra vez.

Exemplo no Opus 5.5, numa conversa de 50 mil tokens (a régua embaixo da caixa de texto mostra esse número): a próxima mensagem custa uns US$ 0,024 se você responde logo e uns US$ 0,26 depois de uma pausa. Dez vezes mais pela mesma mensagem. A lição [Conversas enxutas](#/aprender/conversas-enxutas) mostra a tabela completa e o que fazer.

O mesmo acontece quando você **troca o modelo, troca o raciocínio ou liga e desliga a Web** no meio de uma conversa longa: o que estava guardado deixa de valer, e a próxima mensagem paga tudo de novo.

## Os gastos que você não vê

Algumas coisas gastam sem aparecer como resposta na tela:

- **Conselheiro de modelo**: o Haiku lê a conversa na 1ª mensagem e depois a cada 5. Cada avaliação é curta e sem raciocínio; pelo preço do Haiku, fica em torno de US$ 0,0003 (estimativa).
- **Títulos automáticos**: o Haiku dá nome à conversa, uma vez por conversa (uma fração de centavo).
- **Busca na web**: US$ 0,01 por busca, mais os trechos de páginas que ela traz, que entram na conversa e são relidos nas mensagens seguintes. Uma busca sozinha custa o mesmo que umas 20 mensagens curtas no Haiku.
- **Resumir a conversa**: o resumo automático e o /compact são uma chamada a mais, que lê a conversa inteira.
- **Modo Code**: cada passo (ler um arquivo, rodar um comando) é um pedido novo à API, que relê a tarefa toda. Uma tarefa de 20 passos são 20 pedidos.
- **Fluxos**: cada etapa é uma conversa escondida. O cartão do fluxo mostra a estimativa antes de rodar.
- **Rotinas**: cada rodada é uma conversa nova, todo dia, enquanto a rotina estiver ligada.
- **Ajudantes**: o ajudante das lições usa o Haiku, e o editor de memória usa o Sonnet.

Nada disso é caro uma vez só. O que pesa é o que se repete muitas vezes: rotinas, buscas e passos do Code.

## Onde cada centavo aparece

- **Embaixo de cada resposta**: o modelo e quanto ela custou (se não aparecer, ligue em **Configurações > Aparência > Mostrar o custo de cada resposta**).
- **Embaixo da caixa de texto**: a régua com o tamanho da conversa e quanto ela já custou.
- **/custo**: digite na caixa de texto para ver quanto esta conversa e o mês já gastaram.
- **Uso e gasto**, na barra da esquerda: o gasto por dia, por modelo e por conversa.

A lição [Acompanhar e travar o gasto](#/aprender/acompanhar-o-gasto) explica como ler cada um.

## Caro e barato, lado a lado

| Costuma sair caro | Costuma sair barato |
|---|---|
| Pergunta simples no Opus ou no Fable | A mesma pergunta no Haiku, uns 40 vezes menos que no Opus |
| Resposta longa que você não vai ler inteira | "Responda em 5 linhas" |
| Voltar a uma conversa longa depois de uma pausa | Conversa nova com um resumo do que importa |
| PDF inteiro anexado para perguntar sobre uma página | Só a página que importa |
| Rotina que chama o Claude toda hora | Um programa sem IA, feito uma vez ([veja como](#/aprender/automatizar-sem-ia)) |
| Web ligada numa conversa que não precisa de nada atual | **/web off** |

Cada linha dessa tabela vira uma lição nesta trilha: [o modelo certo](#/aprender/modelo-certo-mais-barato), [o raciocínio](#/aprender/raciocinio-sem-desperdicio), [conversas enxutas](#/aprender/conversas-enxutas), [o modo Code](#/aprender/code-sem-desperdicio), [automatizar sem IA](#/aprender/automatizar-sem-ia) e [acompanhar o gasto](#/aprender/acompanhar-o-gasto).

```experimentar
Faça as contas numa tabela curta, sem explicação longa. No Haiku 5.5, a entrada custa US$ 0,10 por milhão de tokens e a saída US$ 0,50. No Opus 5.5, a entrada custa US$ 4 e a saída US$ 20. Quanto custariam por mês, em cada um, 30 perguntas por dia, cada uma com uns 3.000 tokens de entrada e 700 de saída?
```
