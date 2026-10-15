---
titulo: O modo Code sem desperdício
trilha: 5. Economizar crédito
ordem: 44
duracao: 7 min
resumo: Por que uma tarefa no Code custa mais que uma pergunta, e os hábitos que cortam passos, releituras e esperas.
---

No [modo Code](#/aprender/modo-code) o Claude trabalha em passos: olha a pasta, lê um arquivo, roda um comando, edita outro. É o modo mais útil e também o que mais gasta por tarefa. A boa notícia é que quase todo o desperdício vem de poucos hábitos, fáceis de trocar.

## Como uma tarefa no Code gasta

- **Cada passo é um pedido novo à API**, que relê a tarefa inteira até ali (pelo preço do cache, se não houve pausa). Uma tarefa de 20 passos são 20 pedidos. Na página **Uso e gasto**, a coluna **Pedidos** conta cada um deles.
- **A conversa já começa grande**: as instruções do modo Code, as regras da pasta (CLAUDE.md) e a descrição das ferramentas passam de 10 mil tokens antes do seu pedido (estimativa).
- **O que cada passo traz entra na conversa**: o conteúdo de um arquivo lido ou a saída de um comando é relido em todos os passos seguintes.
- **O raciocínio no Code começa no Alto.**

Uma estimativa para uma tarefa em que cada passo traz uns 1.500 tokens novos e escreve uns 1.000 (com o raciocínio):

| Modelo | Tarefa de 20 passos | Tarefa de 40 passos |
|---|---|---|
| **Haiku 5.5** | US$ 0,02 | US$ 0,05 |
| **Sonnet 5.5** | US$ 0,36 | US$ 0,75 |
| **Opus 5.5** | US$ 0,73 | US$ 1,51 |

Ou seja: o que mais economiza no Code é **ter menos passos** e **usar o modelo certo**.

## Faça isto em vez daquilo

| Em vez de | Faça |
|---|---|
| "Procure onde está a planilha de vendas" | "Leia vendas.xlsx, na pasta Relatórios" |
| Pedir a tarefa inteira de uma vez | Pedir o plano antes (modo **Plano**, ou o cartão **Posso fazer assim?**) e corrigir o plano, que custa uma mensagem |
| "Renomeie as 300 fotos" | "Renomeie 3 para eu conferir; depois faça o resto" |
| "Abra o relatório e me mostre" | Abrir você mesmo no painel do Code, que não gasta nada |
| Pedir ao Claude para rodar um comando só para ver o resultado | Rodar você mesmo no **Console** |
| Um comando que despeja milhares de linhas | "Mostre só os erros" ou "só as últimas 20 linhas" |
| Deixar o cartão de permissão esperando enquanto faz outra coisa | Responder logo, ou liberar com **Permitir nesta tarefa** |
| Opus no Alto para mover e renomear arquivos | Haiku no Médio ou no Baixo |
| Pedir a mesma tarefa toda semana | Pedir um programa uma vez, que roda sem IA ([veja como](#/aprender/automatizar-sem-ia)) |

## Olhe você mesmo: o painel do Code

Ao lado da conversa, o painel do Code (**Ctrl + J** abre e fecha) tem:

- **Arquivos**: a pasta inteira. Abra qualquer arquivo no **Visualizador** para ler, em vez de pedir ao Claude.
- **Console**: o PowerShell de verdade, já na pasta. O botão **Mandar para o Claude** leva o resultado para a conversa; só a partir daí ele vira tokens.
- **Tarefas**: o que está rodando em segundo plano, com o botão **Parar**.

Tudo o que você faz no painel, sem pedir ao Claude, custa zero token. Um servidor que o Claude deixou rodando em segundo plano também não gasta nada sozinho: só gasta quando o Claude lê o que ele escreveu.

O **Navegador** do painel é diferente: cada página que o Claude abre e lê, e cada print que ele tira, entra na conversa como tokens. Dê o endereço certo em vez de pedir para ele procurar, e peça só o print quando o visual importar.

## Responda os cartões logo

O cache guarda a tarefa por 5 minutos. Se um cartão de permissão fica esperando 10 minutos enquanto você faz outra coisa, o passo seguinte paga a tarefa inteira de novo. Numa tarefa de 40 mil tokens no Sonnet, esse passo custa uns US$ 0,11 em vez de uns US$ 0,02 (estimativa).

- Ações repetidas e seguras na mesma tarefa: no cartão, **Mais opções > Permitir nesta tarefa** (vale até aquela resposta terminar).
- Ações sempre seguras naquela pasta: uma [regra de permissão](#/aprender/permissoes).
- Precisou sair no meio? Tudo bem: cada espera longa custa uma releitura, uma vez. O que pesa é uma tarefa que para em vários cartões e fica esperando em todos.

## O modelo e o raciocínio no Code

- O Code também começa no **Haiku 5.5**, e o conselheiro de modelo também funciona aqui.
- Tarefa mecânica (organizar, renomear, juntar arquivos, uma planilha simples): Haiku, raciocínio no Médio ou no Baixo.
- Código de tamanho médio, documento grande, ou quando o Haiku se perdeu: Sonnet.
- Código grande, com muitos arquivos, ou algo difícil de desfazer: Opus.
- Escolha no começo da tarefa: trocar no meio faz o passo seguinte reler tudo sem o desconto do cache.

## Regras da pasta curtas

O CLAUDE.md da pasta entra no começo de toda conversa do Code e vai junto em todos os passos. Escreva **regras**, não manuais: "use datas no formato 2026-10-15", "nunca mexa na pasta Originais". Um material grande de consulta fica num arquivo à parte, com uma linha no CLAUDE.md dizendo quando ler ("para dúvidas de preço, leia docs/precos.md"): assim ele só é lido quando precisa. As skills funcionam do mesmo jeito: só a descrição vai sempre; o procedimento inteiro só entra quando é usado. Veja [CLAUDE.md e skills](#/aprender/claude-md-e-skills).

## Um trabalho por conversa

- Um ajuste na mesma tarefa, logo em seguida: continue na mesma conversa (o cache está valendo e ele já conhece os arquivos).
- Uma tarefa nova, sem relação: **Novo trabalho no Code**. A conversa nova começa leve, sem carregar arquivos e saídas da tarefa anterior.

## O teto por tarefa

Em **Configurações > Limite de gasto**, o **Teto por tarefa no modo Code** (padrão US$ 2) pausa uma tarefa que gastou isso. Aparece um aviso, e você manda "continue" para seguir. Antes de mandar, dê uma olhada nos últimos passos: se ele está repetindo a mesma coisa sem sair do lugar, é melhor parar e explicar de outro jeito do que pagar mais voltas.

## Tarefa grande: um fluxo

Para uma tarefa grande, com partes bem diferentes, peça "faça isso como um fluxo". O cartão mostra as etapas, o modelo de cada uma, a estimativa de custo e o teto, antes de rodar. Ponha o Haiku nas etapas simples. Veja [Fluxos](#/aprender/fluxos-e-agentes).

```experimentar-code
Quero organizar os arquivos desta pasta por ano. Antes de começar, me diga em no máximo 5 linhas quais arquivos e pastas você vai precisar olhar e o que pretende mudar. Não leia nada fora disso sem me perguntar e não me mostre o conteúdo dos arquivos na resposta.
```

```experimentar-code
Liste os 10 maiores arquivos desta pasta e das subpastas, com o tamanho em MB, numa tabela. Não liste o resto nem explique o comando.
```
