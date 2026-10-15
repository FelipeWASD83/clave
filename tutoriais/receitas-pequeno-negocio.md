---
titulo: Para o pequeno negócio
trilha: 9. Receitas por área
ordem: 82
duracao: consulta
resumo: Tabela de preços, orçamentos e propostas, follow-up, pedidos sem IA, posts e um mapa das entregas, com o modelo mais barato que dá conta.
---

Pedidos prontos para quem toca um negócio pequeno: loja, confeitaria, oficina, prestador de serviço. Clique no botão de cada receita: o pedido vai para a caixa de texto (de uma conversa nova ou do modo Code), e você troca o que está entre colchetes e os exemplos pelos dados do seu negócio antes de enviar.

Várias receitas usam o plugin **Vendas**, que vem com o Clave e já começa ligado (dá para ligar e desligar em **Plugins**, na barra da esquerda). Os comandos dele começam com `/vendas:`; veja [Plugins e comandos de barra](#/aprender/plugins-e-comandos).

O Clave começa no **Haiku 5.5**, o mais barato, e ele dá conta de quase tudo aqui. O conselheiro de modelo avisa quando a tarefa pede outro (veja [O modelo certo pelo menor preço](#/aprender/modelo-certo-mais-barato)).

| Receita | Onde | Modelo |
|---|---|---|
| Tabela de preços com margem | chat | Haiku |
| Orçamento e proposta em Word e PDF | modo Code | Haiku (Sonnet para proposta grande) |
| Follow-up de quem não respondeu | chat | Haiku |
| Responder um cliente | chat | Haiku |
| Pedidos na planilha (e um app sem IA) | modo Code | Haiku |
| Posts para as redes | chat, com widget | Haiku |
| Mapa das entregas | chat, com widget | Haiku |
| Relatório de vendas | chat ou modo Code | Haiku (Sonnet para planilha grande) |

## 1. Tabela de preços com margem

```experimentar
Crie uma planilha de preços para a minha confeitaria com as colunas Produto, Custo dos ingredientes, Embalagem, Custo total, Margem desejada (%) e Preço de venda, com fórmulas para eu só trocar os custos e a margem. Preencha com 5 produtos de exemplo e destaque em vermelho os produtos com margem abaixo de 30%.
```

- **O que ele faz:** cria a [planilha](#/aprender/glossario/planilha) com as [fórmulas](#/aprender/glossario/formula) prontas e mostra **Baixar** e **Abrir**. Quem calcula as fórmulas é o Excel, quando você abre o arquivo. Com o Excel instalado, ele também exporta a tabela em PDF para mandar aos clientes.
- **Modelo:** o Haiku basta.
- **Bom saber:** os valores de exemplo são inventados de propósito. Troque pelos seus custos reais; o Claude nunca deve chutar o preço de um produto seu. Mais em [Excel com o Claude](#/aprender/excel).

## 2. Orçamento e proposta em Word e PDF (modo Code)

Escolha a pasta onde você guarda as propostas e mande:

```experimentar-code
/vendas:proposta para o cliente Mercado Exemplo Ltda: 20 caixas de café 500 g a R$ 18,90 a unidade e 10 fardos de açúcar 5 kg a R$ 22,50, desconto de 5% para pagamento no Pix, frete por conta do cliente, validade de 15 dias e entrega em 5 dias úteis.
```

- **O que ele faz:** pergunta só o que falta (os dados da sua empresa, por exemplo), confere todas as contas de dois jeitos e entrega o arquivo do Word e o PDF na pasta. Se já existe uma proposta antiga ou um modelo na pasta, ele segue o mesmo jeito. Ele nunca inventa preço, prazo ou condição: o que faltar vira um campo marcado, e ele lista esses campos no fim.
- **Modelo:** o Haiku basta para uma proposta simples. Com muitos itens e condições, o Sonnet.
- **Melhor ferramenta:** é o modo Code porque o arquivo nasce na sua pasta. Depois, `/vendas:follow-up` (a próxima receita) cuida das mensagens para quem recebeu a proposta.

## 3. Follow-up de quem não respondeu

```experimentar
/vendas:follow-up O Mercado Exemplo recebeu a proposta 2026-041, de R$ 4.380,00, há 3 dias. Ela vale até o dia 30 e ninguém respondeu. O contato é a compradora, pelo WhatsApp.
```

- **O que ele faz:** escreve as mensagens no ritmo de 2, 5 e 10 dias: curtas, educadas, com um pedido claro, sem inventar urgência nem dar desconto que você não autorizou. Se faltar informação (o que foi mandado, quando, quanto), ele pergunta antes.
- **Modelo:** o Haiku basta.
- **Bom saber:** ele escreve, quem manda é você. Com o e-mail ligado em Configurações > Conectores, ele pode enviar por lá, mas cada envio mostra o e-mail inteiro e espera o seu OK.

## 4. Responder um cliente

```experimentar
/vendas:responder-cliente Uma cliente pediu 10% de desconto num pedido de R$ 1.200,00. Eu posso dar no máximo 5% se ela pagar no Pix. Responda no tom da loja: simpático e direto.
```

- **O que ele faz:** usa só os fatos que você der (nunca promete reembolso, desconto ou prazo por conta própria) e entrega duas versões: uma curta, para WhatsApp, e uma completa, para e-mail. Embaixo, uma nota com o que conferir antes de mandar.
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** um [projeto](#/aprender/projetos) com o tom da loja e a política de trocas evita repetir isso em todo pedido.

## 5. Pedidos na planilha (e um app sem IA)

Para passar os pedidos de hoje de uma vez, no modo Code, na pasta da planilha:

```experimentar-code
/vendas:pedidos Os pedidos de hoje estão no arquivo pedidos-whatsapp.txt (copiei as conversas do WhatsApp). Passe para a planilha pedidos.xlsx desta pasta, uma linha por item.
```

- **O que ele faz:** lê o texto e mostra as linhas e os campos em dúvida antes de gravar. Ele não mexe na planilha original sem fazer uma cópia.
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** isso se repete todo dia, sempre no mesmo formato? Em vez de pagar o Claude a cada vez, peça **uma vez** um programa que faz o serviço **sem IA**. O comando `/vendas:automatizar` começa por aí, e a lição [Um app de pedidos sem IA](#/aprender/app-de-pedidos-sem-ia) mostra o caminho inteiro, do e-mail ao site. Veja também [Automatizar sem pagar a IA toda vez](#/aprender/automatizar-sem-ia).

## 6. Posts para as redes

```experimentar
Escreva 8 posts para o Instagram da minha confeitaria no próximo mês: 2 por semana, alternando produto, bastidores, dica e depoimento. Para cada um, o texto (no máximo 5 linhas e até 2 emojis), 5 hashtags e uma sugestão de foto. Mostre o calendário dos posts numa linha do tempo.
```

- **O que ele faz:** escreve os textos, sugere a foto de cada post e desenha o calendário num **widget** de linha do tempo. Ele **não cria fotos**: a sugestão é para você fotografar ou montar no seu editor de imagem.
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** um [projeto](#/aprender/projetos) com o público, o tom da marca e a tabela de preços. Assim os posts saem no seu jeito e ninguém inventa preço.

## 7. Mapa das entregas

```experimentar
Amanhã tenho estas entregas, saindo da loja na [endereço da loja]:
[cole os endereços, um por linha, com bairro e cidade]

Mostre os pontos num mapa e sugira uma ordem de visita que evite ir e voltar.
```

- **O que ele faz:** marca os pontos num **widget** de mapa e sugere a ordem das entregas. Os mapas vêm do OpenStreetMap, pela internet. Mais em [Mapas e roteiros](#/aprender/mapas-e-roteiros).
- **Modelo:** o Haiku basta.
- **Cuidado:** ele não vê trânsito, obra nem rua fechada. Confira a rota num app de navegação antes de sair. E mande só o endereço: o nome e o telefone do cliente não fazem falta aqui (veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados)).

## 8. Relatório de vendas

Anexe a planilha de vendas e mande:

```experimentar
/vendas:relatorio da planilha de vendas que eu anexei, comparando este mês com o mês passado.
```

- **O que ele faz:** totais por período, produto e cliente, ticket médio, os maiores clientes e a comparação com o período anterior, começando por um resumo em linguagem simples. Ele confere os totais antes de entregar e não mexe na planilha original.
- **Modelo:** o Haiku basta. Planilha grande, o Sonnet.
- **Melhor ferramenta:** quer o relatório toda semana sem pedir? Uma [rotina](#/aprender/rotinas) no modo Code, na pasta das vendas, faz isso no horário. Se a conta é sempre a mesma, um programa sem IA faz de graça.

## Dicas para o negócio

- **Preço, prazo e condição são seus:** o Claude usa o que você passa e marca o que falta. Desconfie de qualquer número que você não deu.
- **Os comandos também têm nome em inglês** (`/sales:proposal`, por exemplo). Tanto faz qual você usa.
- **Antes de mandar algo para um cliente, leia.** O Claude ajuda muito, mas quem assina é você.
