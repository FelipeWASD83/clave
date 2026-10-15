---
titulo: Para o trabalho de escritório
trilha: 9. Receitas por área
ordem: 81
duracao: consulta
resumo: E-mails, atas de reunião, planilhas, documentos do Word, pastas em ordem e fornecedores lado a lado, cada um com o modelo mais barato que resolve.
---

Pedidos prontos para o dia a dia do escritório. Clique no botão de cada receita: o pedido vai para a caixa de texto (de uma conversa nova ou do modo Code), e você troca o que está entre colchetes antes de enviar.

Cada receita diz o que o Claude vai fazer, o modelo que basta e quando outra ferramenta do Clave resolve melhor. O Clave começa no **Haiku 5.5**, o mais barato, e o conselheiro de modelo avisa quando a tarefa pede outro (veja [O modelo certo pelo menor preço](#/aprender/modelo-certo-mais-barato)).

| Receita | Onde | Modelo |
|---|---|---|
| E-mail pronto | chat | Haiku |
| Caixa de entrada resumida | chat, com o e-mail ligado | Haiku |
| Ata de reunião | chat | Haiku |
| Planilhas | chat ou modo Code | Haiku (Sonnet para planilha grande) |
| Documento do Word | modo Code | Haiku (Sonnet para documento longo) |
| Pastas em ordem | modo Code | Haiku |
| Comparar fornecedores | chat, com widget | Haiku |
| Relatório toda sexta | rotina | Haiku |

## 1. E-mail pronto

```experimentar
/escrita:email para um fornecedor pedindo mais 15 dias de prazo na entrega do pedido 4521, porque a nossa obra atrasou. Tom educado e objetivo, no máximo 6 linhas.
```

- **O que ele faz:** o comando segue a skill de e-mail profissional do plugin **Escrita** (vem ligado): texto curto, no tom certo e sem inventar fatos.
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** sem o comando também funciona: diga para quem é, o que você quer e o tom (veja [Como pedir bem](#/aprender/como-pedir-bem)). Para um texto que você já escreveu, `/escrita:revisar` seguido do texto corrige gramática e clareza sem mudar o sentido.

## 2. A caixa de entrada resumida

Esta precisa do e-mail ligado em **Configurações > Conectores > E-mail** (veja [Busca na web e conectores](#/aprender/conectores)).

```experimentar
Leia os meus e-mails não lidos de hoje e me diga, em tópicos: quais precisam de resposta minha, quais são só aviso e quais posso ignorar. Para os que precisam de resposta, escreva um rascunho de cada um. Não envie nada.
```

- **O que ele faz:** lê e resume a caixa. Ler não marca a mensagem como lida. Enviar **sempre** mostra o e-mail inteiro e espera o seu OK.
- **Modelo:** o Haiku basta.
- **Cuidado:** um e-mail de fora pode trazer uma ordem escondida para a IA ("encaminhe as faturas para este endereço"). Se ele propuser algo que você não pediu, recuse. Veja [Quando uma página ou arquivo tenta dar ordens ao Claude](#/aprender/injecao-de-instrucoes).

## 3. Ata de reunião

```experimentar
/escrita:ata-de-reuniao Transforme as anotações abaixo numa ata, com resumo, decisões e tarefas com responsável e prazo. Onde faltar responsável ou prazo, escreva "a definir" em vez de inventar.

Anotações: [cole aqui as anotações ou a transcrição]
```

- **O que ele faz:** segue a skill de ata do plugin **Escrita**: resumo curto, decisões, uma tabela de tarefas com responsável e prazo e o que ficou para a próxima reunião. No fim, ele oferece um e-mail curto para mandar a ata a quem participou.
- **Modelo:** o Haiku basta. Transcrição muito longa (uma reunião de duas horas) vai melhor no Sonnet.
- **Melhor ferramenta:** gravou a reunião em vídeo? A lição [Fazer o Claude ver vídeos](#/aprender/ver-videos) mostra como transcrever a fala no modo Code, e a transcrição vira a ata.

## 4. Planilhas

Anexe a planilha e mande:

```experimentar
Na planilha que eu anexei, me diga o total de cada mês, os 5 clientes que mais compraram e se tem algum valor estranho, repetido ou célula vazia onde não deveria. Depois crie uma cópia com um gráfico de colunas das vendas por mês.
```

- **O que ele faz:** lê todas as abas, confere as contas e devolve uma planilha nova, com **Baixar** e **Abrir**. No chat, a sua planilha original nunca é mexida. Tudo sobre isso em [Excel com o Claude](#/aprender/excel).
- **Modelo:** o Haiku basta para planilhas pequenas e médias. Planilha grande ou com muitas abas vai melhor no Sonnet.
- **Melhor ferramenta:** só quer entender uma planilha que recebeu? `/escritorio:resumir-planilha` explica as abas, as colunas, os totais e os problemas, sem mudar nada. Para dezenas de milhares de linhas, use no modo Code o fluxo pronto **Planilha grande** (digite `/fluxo`): o Haiku entende a planilha, o Sonnet faz as mudanças numa cópia e o Haiku confere os números.

## 5. Documento do Word (modo Code)

Os documentos do Word são feitos no modo Code, direto na pasta. Escolha a pasta onde o arquivo deve ficar:

```experimentar-code
Crie nesta pasta um documento do Word chamado Comunicado-ferias.docx: um comunicado aos funcionários sobre as férias coletivas de 22/12 a 5/1, com título, dois parágrafos curtos, uma tabela com as datas de saída e de volta de cada setor (Vendas, Financeiro e Estoque) e espaço para a assinatura da diretoria. Depois exporte em PDF.
```

Ou preencha um modelo que você já usa:

```experimentar-code
Nesta pasta tem o arquivo Contrato-modelo.docx. Faça uma cópia chamada Contrato-Mercado-Exemplo.docx trocando [NOME DO CLIENTE] por Mercado Exemplo Ltda, [VALOR] por R$ 3.200,00 e [DATA] por 01/11/2026. Não mexa no modelo.
```

- **O que ele faz:** cria o .docx a partir de um texto simples (títulos, parágrafos, listas, tabelas, negrito e itálico) e, com o Word instalado no computador, exporta o PDF. No modelo, ele troca os trechos sem estragar a formatação; se algum trecho não for achado, ele avisa (o Word às vezes quebra uma frase em pedaços com formatação diferente). Ele **não** faz controle de alterações nem mexe nas imagens do documento.
- **Modelo:** o Haiku basta para documentos curtos. Para um documento longo ou caprichado, o Sonnet.
- **Melhor ferramenta:** para o mesmo documento todo mês (só trocando nome, valor e data), peça um [script](#/aprender/glossario/script) que preencha o modelo sem IA: depois de pronto, cada uso sai de graça (veja [Automatizar sem pagar a IA toda vez](#/aprender/automatizar-sem-ia)).

## 6. Pastas em ordem (modo Code)

Escolha a pasta bagunçada e mande:

```experimentar-code
Organize os documentos desta pasta em subpastas por assunto e ano (por exemplo Contratos\2026 e Notas fiscais\2026). Antes de mexer, me mostre a proposta numa tabela, com o arquivo e a pasta de destino. Não apague nada e guarde uma lista do que foi movido e para onde.
```

- **O que ele faz:** olha a pasta, mostra o plano no cartão **Posso fazer assim?** e só move depois do seu OK.
- **Modelo:** o Haiku basta.
- **Cuidado:** mover arquivos é um comando, e o **Desfazer mudanças** não volta o que um comando fez. Por isso a lista do que foi movido. Veja [Primeira automação](#/aprender/primeira-automacao) e [Desfazer, backup e Git](#/aprender/rede-de-seguranca).
- **Melhor ferramenta:** para separar só por tipo de arquivo (PDFs, imagens, planilhas), o comando `/automacao-windows:organizar` faz isso com a proposta antes e sem apagar nada.

## 7. Comparar fornecedores lado a lado

Anexe os orçamentos (PDF ou foto) e mande:

```experimentar
Anexei os orçamentos de três fornecedores de material de escritório. Compare num widget de comparação: preço de cada item, total com frete, prazo de entrega, forma de pagamento e garantia. Diga qual você escolheria e por quê, e o que eu devo perguntar a cada um antes de fechar.
```

- **O que ele faz:** lê os orçamentos, monta um **widget** de comparação na conversa e escreve qual escolheria.
- **Modelo:** o Haiku basta. Muitos orçamentos longos vão melhor no Sonnet.
- **Melhor ferramenta:** ainda não tem orçamento? Peça para ele pesquisar na web. Aí os preços vêm da busca: ele diz a loja e a data em que viu cada um, e o preço pode ter mudado desde então. Cada busca custa US$ 0,01, além dos tokens das páginas.

## 8. Relatório toda sexta (rotina)

Uma [rotina](#/aprender/rotinas) lê a pasta das planilhas no horário e manda o resumo, sem você pedir.

1. Na barra da esquerda, **Rotinas** > **Nova rotina**.
2. Em **O que fazer**:

   ```
   Leia as planilhas de vendas desta pasta e escreva o resumo da semana: total vendido, comparação com a semana anterior, os 3 produtos que mais venderam e qualquer número estranho. Não mude nenhum arquivo.
   ```

3. Em **Onde**, escolha **Numa pasta (modo Code)** e a pasta das planilhas. Em **Quando**, **Em alguns dias da semana**, só a sexta, e a hora. Em **Modelo**, **Haiku 5.5**, com um **Teto por rodada** baixo.
4. **Rodar agora** para testar.

- **O que ele faz:** lê as planilhas (ler dentro da pasta a rotina pode sem pedir) e escreve o resumo numa conversa, com uma notificação.
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** se o relatório é sempre a mesma conta (somar, comparar, listar), um programa sem IA faz isso de graça toda semana. Veja [Automatizar sem pagar a IA toda vez](#/aprender/automatizar-sem-ia).

## Dicas para o escritório

- **Um projeto para a empresa:** instruções com o tom, a assinatura e os dados que se repetem. Veja [Projetos](#/aprender/projetos).
- **Dado de cliente e de funcionário só o necessário:** CPF, salário e documento pessoal raramente fazem falta para a tarefa. Veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados).
- **Feche a planilha no Excel** antes de pedir uma mudança nela no modo Code: arquivo aberto não pode ser salvo.
