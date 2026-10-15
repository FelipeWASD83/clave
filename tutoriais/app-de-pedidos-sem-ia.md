---
titulo: Um app de pedidos sem IA (e quase sem custo)
trilha: 3. Automação com o modo Code
ordem: 28
duracao: 12 min
resumo: Pedidos que chegam por e-mail viram linhas no Excel e vão para o site, com um programa feito uma vez só, em vez de pagar o Claude toda hora.
---

Imagine um escritório de vendas. Os pedidos chegam por e-mail, alguém copia cada um para uma planilha do Excel e depois digita tudo de novo no site da empresa. A ideia natural é criar uma [rotina](#/aprender/rotinas) que chama o Claude de hora em hora para fazer isso.

Funciona, mas é o jeito caro. Esta lição mostra o jeito melhor: pedir ao modo Code, **uma vez só**, um pequeno programa que faz o serviço **sem IA**. Quem roda o programa no horário é o próprio Windows, e cada rodada custa zero token.

## 1. Por que não uma rotina

No Clave, a rotina mais frequente roda de hora em hora (**A cada N horas**, de 1 a 24). Isso dá 24 chamadas ao Claude por dia, cerca de 730 por mês. Cada chamada paga para o Claude ler os e-mails, mesmo quando não chegou pedido nenhum. E o gasto continua no mês seguinte, e no outro, para sempre. Além disso, um pedido pode esperar até uma hora para entrar: conferir a cada 15 minutos só dá com um programa fora do Clave, que é justamente o que esta lição monta.

Um [script](#/aprender/glossario/script) faz o mesmo serviço seguindo regras fixas: acha o e-mail, separa os campos, grava na planilha. Ele custa só a conversa que o construiu. Depois disso, pode rodar o dia inteiro de graça.

Tem mais duas vantagens:

- O programa faz **sempre igual**. Uma IA pode variar um pouco de uma vez para outra, e pedido é coisa que precisa sair igual sempre.
- Uma rotina não pede OK a ninguém. Para ela gravar na planilha e mandar ao site, você teria que liberar tudo com [regras de permissão](#/aprender/permissoes).

**Quando a IA vale a pena:** quando os pedidos chegam em texto livre, cada cliente escrevendo de um jeito ("me manda aquele café de sempre, umas dez caixas"). Aí regras fixas se perdem. Mesmo assim, use a IA só nesse pedaço: o programa faz todo o resto e chama o Claude apenas para entender os e-mails fora do padrão, com o Haiku, o modelo mais barato (veja [Modelos e raciocínio](#/aprender/modelos-e-raciocinio)). Pelo preço atual do Haiku 5.5, isso fica em menos de um centavo de dólar por pedido (é uma estimativa).

## 2. O que você precisa

- O Clave, com o [modo Code](#/aprender/modo-code).
- O [Python](#/aprender/glossario/python). Ele já está no seu computador: o instalador do Clave cuidou disso.
- Acesso à conta de e-mail onde os pedidos chegam (passo 3).
- A [planilha](#/aprender/glossario/planilha) de pedidos. Se ainda não existe, o programa cria uma chamada `pedidos.xlsx`.
- Saber como o site da empresa recebe pedidos: por uma [API](#/aprender/glossario/api), por um formulário numa página ou só digitando na tela. Se não souber, pergunte a quem cuida do site. O passo 6 explica os três casos.

Crie uma pasta só para isso, por exemplo `Documentos\robo-de-pedidos`. É nela que o modo Code vai trabalhar.

## 3. Ligue o e-mail

O programa lê os e-mails por **IMAP**, o jeito padrão de um programa entrar numa caixa de e-mail. Para isso ele precisa de uma senha.

**Gmail:**

1. Ligue a **Verificação em duas etapas** na sua Conta do Google (myaccount.google.com > Segurança).
2. Abra myaccount.google.com/apppasswords e crie uma **senha de app** com um nome como "robô de pedidos".
3. O Google mostra uma senha de 16 letras. Deixe essa tela aberta até o passo 5. Essa senha só serve para isso, não muda a sua senha normal e pode ser apagada a qualquer hora.

Se o e-mail é da empresa no Google Workspace, o administrador pode ter bloqueado a senha de app. Nesse caso, fale com ele.

**Outros provedores** (Locaweb, Hostinger, KingHost, Zoho, Yahoo e a maioria das hospedagens): procure "IMAP" na página de ajuda do seu provedor. Ela mostra o endereço do servidor (algo como `imap.seuprovedor.com.br`) e a porta (quase sempre 993). Alguns, como o Yahoo, também pedem uma senha de app, parecida com a do Gmail.

**Microsoft (Outlook.com, Hotmail e Microsoft 365):** a Microsoft não aceita mais entrar por IMAP com senha, nem com senha de app. Você tem dois caminhos:

- Usar o **Outlook clássico** instalado no computador (o que vem com o Office, não o "novo Outlook"), já entrando na conta. O programa lê os e-mails através dele, sem precisar de senha nenhuma.
- Usar um conector de e-mail em **Configurações > Conectores** (veja a lição [Busca na web e conectores](#/aprender/conectores)). Atenção: pelo conector quem lê os e-mails é o Claude, então cada leitura volta a gastar tokens. É a saída para quando não houver outra.

**Onde a senha fica.** A senha nunca é escrita dentro do programa e nunca é colada na conversa com o Claude. O programa guarda a senha no **Gerenciador de Credenciais do Windows**, o cofre de senhas que já vem no Windows, e pega de lá na hora de entrar. Você digita a senha uma vez só, numa janela do próprio programa (o pedido do passo 5 já cuida disso). Para ver ou apagar depois: menu Iniciar > **Gerenciador de Credenciais** > **Credenciais do Windows**.

## 4. Combine um modelo de pedido

Um programa sem IA precisa que o pedido chegue sempre do mesmo jeito. Combine isso com os clientes. Pode ser:

- um formato fixo de e-mail, como o do exemplo abaixo;
- um formulário simples de pedido, por exemplo uma planilha modelo que o cliente preenche e manda anexada;
- o anexo que eles já mandam hoje, se ele vem sempre igual.

Exemplo de e-mail de pedido:

```
Assunto: Pedido - Mercado Exemplo

Cliente: Mercado Exemplo
Código do cliente: 1042

Itens (quantidade; produto; preço da unidade):
10; Café 500 g; R$ 18,90
5; Açúcar 1 kg; R$ 4,50
20; Arroz 5 kg; R$ 27,00

Entrega: 20/10/2026
Observação: entregar pela manhã
```

Salve um exemplo como esse num arquivo `exemplo-de-pedido.txt` dentro da pasta `robo-de-pedidos`. O Claude vai usar esse arquivo para entender o formato.

## 5. Peça ao modo Code

1. **Novo trabalho no Code** > escolha a pasta `robo-de-pedidos`.
2. Deixe a permissão em **Perguntar** (ou em **Plano**, para ver o plano antes).
3. Mande o pedido abaixo. Troque o que está entre colchetes pelos dados do seu caso.

```experimentar-code
Quero um programa em Python, nesta pasta, que passe para uma planilha os pedidos que chegam por e-mail. Ele não deve usar IA nenhuma. Ele deve:

1. Entrar na caixa de e-mail por IMAP (servidor [imap.gmail.com], porta 993) e ler só os e-mails não lidos com "Pedido" no assunto.
2. Tirar de cada e-mail: cliente, código do cliente, itens (quantidade, produto, preço da unidade), data de entrega e observação. O formato está no arquivo exemplo-de-pedido.txt.
3. Gravar uma linha por item em pedidos.xlsx, sempre no fim, sem apagar nem sobrescrever nada. Se a planilha não existir, criar com cabeçalho.
4. Marcar o e-mail como lido só depois de gravar, e lembrar quais e-mails já foram registrados, para nunca registrar o mesmo pedido duas vezes.
5. Se o e-mail não seguir o formato, não adivinhar: mover para uma pasta "Pedidos com problema" e anotar no log.
6. Se a planilha estiver aberta no Excel, não perder o pedido: deixar o e-mail como não lido e tentar de novo na próxima vez.
7. Mandar cada pedido para o site da empresa (vou explicar como numa próxima mensagem).
8. Escrever tudo o que fez num arquivo pedidos.log, com data e hora, sem nunca escrever senha no log.
9. Ter um modo de teste, que só mostra o que faria, sem gravar, sem marcar e-mail e sem mandar nada ao site.

A senha do e-mail não pode ficar escrita no código: guarde no Gerenciador de Credenciais do Windows (biblioteca keyring). Crie um configurar.bat que eu rodo com dois cliques: ele pergunta o e-mail e a senha numa janela e guarda. Não me peça a senha aqui na conversa.

No fim, escreva um LEIA-ME.md em linguagem simples explicando como usar, como testar e o que fazer se der erro.
```

Usa o Outlook clássico (conta da Microsoft)? Troque o item 1 por "Ler os e-mails pelo Outlook clássico instalado neste computador, na Caixa de Entrada". Nesse caso não existe senha de e-mail para guardar.

O que esperar: ele vai pedir o seu OK para instalar algumas [bibliotecas](#/aprender/glossario/biblioteca) do Python e para criar os arquivos. Leia cada cartão antes de permitir. No fim, dê dois cliques em `configurar.bat` e digite a senha de app do passo 3 na janela que abrir.

**Atalho:** o plugin Vendas tem o comando `/vendas:automatizar` para esse tipo de pedido. Com o plugin ligado (em **Plugins**, na barra da esquerda), digite o comando no modo Code e conte o que você quer automatizar. Veja [Plugins e comandos de barra](#/aprender/plugins-e-comandos).

## 6. Mandar para o site da empresa

Peça esta parte numa segunda mensagem, depois que o e-mail e a planilha estiverem funcionando. Existem três casos, do melhor para o pior.

**O site tem uma API.** É o melhor caso: uma API é uma porta de entrada feita para programas. Peça a quem fez o site (o desenvolvedor ou a empresa que cuida dele) três coisas: o endereço da API, uma chave de acesso (um [token de acesso](#/aprender/glossario/token-de-acesso)) e um exemplo de pedido no formato que ela aceita. Se o site tiver um ambiente de teste, peça também. A chave vai para o Gerenciador de Credenciais, igual à senha do e-mail.

```experimentar-code
O site da empresa recebe pedidos por uma API. O que o desenvolvedor mandou está no arquivo api-do-site.txt. Faça o programa mandar cada pedido para essa API depois de gravar na planilha. A chave da API fica no Gerenciador de Credenciais (acrescente essa pergunta no configurar.bat). Se o site recusar o pedido ou estiver fora do ar, anote no log e tente de novo na próxima rodada, sem mandar o mesmo pedido duas vezes.
```

**O site tem um formulário de pedido.** O programa preenche e envia o formulário, como se uma pessoa tivesse feito. Funciona bem enquanto o formulário não mudar. Se o formulário pede para provar que você não é um robô (o famoso "não sou um robô"), não dá: isso existe justamente para barrar programas. Nesse caso, peça uma API ao responsável pelo site.

**O site só aceita digitar na tela** (entrar com usuário e senha, clicar, preencher). O programa consegue abrir um [navegador](#/aprender/glossario/navegador) sozinho e clicar e digitar no seu lugar, com uma biblioteca chamada Playwright. É o último recurso: é mais lento, quebra quando o site muda de visual e precisa da senha do site (que também vai para o Gerenciador de Credenciais). Antes, confira se os termos de uso do site permitem.

```experimentar-code
O site da empresa só aceita pedidos digitados na tela, na página [endereço da página de pedidos]. Faça o programa abrir o Microsoft Edge com o Playwright, entrar com o usuário e a senha guardados no Gerenciador de Credenciais e lançar cada pedido. Antes de escrever, me pergunte o que precisar saber sobre a tela de pedido. No modo de teste, preencha tudo mas não clique em enviar.
```

## 7. Teste antes de confiar

1. Mande para você mesmo um e-mail de pedido falso, no formato combinado, com "Pedido" no assunto.
2. Rode o programa no **modo de teste** (o `LEIA-ME.md` diz como, ou peça no Code: "rode o programa no modo de teste"). Confira no `pedidos.log` se ele achou o e-mail e entendeu cada item.
3. Rode de verdade. Abra `pedidos.xlsx` e confira as linhas. Veja se o e-mail ficou como lido.
4. Rode de novo e confirme que o mesmo pedido **não** entrou duas vezes.
5. Teste os problemas: um e-mail fora do formato e a planilha aberta no Excel na hora de rodar.
6. Por último, teste o envio ao site, de preferência no ambiente de teste do site ou com um pedido combinado com quem cuida dele.

**Quando algo quebrar:** abra o `pedidos.log` (ele abre no Bloco de Notas). As últimas linhas dizem o que aconteceu. Copie o erro, abra o modo Code na mesma pasta e cole: "O programa de pedidos deu este erro: [cole aqui]. Descubra a causa e corrija." Se a correção piorar as coisas, use **Desfazer mudanças**.

## 8. Deixe rodando sozinho

Quem roda o programa no horário é o [Agendador de Tarefas](#/aprender/glossario/agendador-de-tarefas) do Windows. O Code cria a tarefa para você (com o comando `schtasks` ou pelo PowerShell) e mostra o comando antes:

```experimentar-code
Crie uma tarefa no Agendador de Tarefas do Windows que rode o programa de pedidos a cada 15 minutos, numa pasta do Agendador chamada "Minhas automações". Use o pythonw, para não abrir janela a cada rodada. Me mostre o comando antes de rodar e me explique como pausar e como apagar a tarefa.
```

Para pausar, mudar ou apagar depois, abra o **Agendador de Tarefas** pelo menu Iniciar, entre na pasta "Minhas automações" e clique com o botão direito na tarefa:

- **Desabilitar** pausa (e **Habilitar** volta a ligar);
- **Propriedades** > aba **Disparadores** muda o intervalo;
- **Excluir** apaga a tarefa (o programa continua na pasta).

Ou peça ao Code, por exemplo "pause a tarefa de pedidos". Apagar sempre pede o seu OK.

Cuidados:

- O computador precisa estar **ligado** e com o seu usuário entrado no Windows (pode estar com a tela bloqueada). Se ele fica desligado à noite, nada se perde: os pedidos da noite continuam como não lidos e entram na primeira rodada da manhã.
- Se der, use um computador que fica sempre ligado no escritório e desligue a suspensão nas configurações de energia do Windows.
- Rode o programa em **um computador só**. Dois computadores rodando o mesmo programa podem registrar o mesmo pedido duas vezes.
- Quem consulta a planilha deve fechar o Excel depois. Com ela aberta o dia todo, os pedidos ficam esperando.

## 9. Quanto custa

| | Rotina de hora em hora | Programa sem IA, a cada 15 min |
|---|---|---|
| Para montar | nada (só escrever o pedido) | uma conversa no modo Code, uma vez |
| Cada rodada | tokens, mesmo sem pedido novo | zero |
| Rodadas por mês | cerca de 730 | cerca de 2.900 |
| Um pedido espera até | 1 hora | 15 minutos |
| Exemplo, a US$ 0,02 por rodada | cerca de US$ 15 por mês, todo mês | US$ 0 |
| Resultado | pode variar um pouco | sempre igual |
| Se o formato do e-mail mudar | se adapta sozinha | precisa de um ajuste (outra conversa curta) |

Os US$ 0,02 por rodada são só um exemplo (é o preço de uma resposta média no Sonnet 5.5 com raciocínio, na tabela de **Preços e planos**): o custo de verdade depende do modelo e de quantos e-mails ela lê. Para entender de onde vem o gasto, veja [Tokens, contexto e gasto](#/aprender/contexto-e-gasto).

## 10. Antes de deixar no automático

- As senhas (do e-mail e do site) estão no Gerenciador de Credenciais, não no código nem na conversa.
- O formato do pedido foi combinado com os clientes.
- O modo de teste funcionou com um pedido falso.
- O mesmo pedido não entra duas vezes.
- Pedido fora do formato vai para "Pedidos com problema", e alguém olha essa pasta todo dia.
- O envio ao site foi testado.
- A tarefa está no Agendador, na pasta "Minhas automações", e você sabe pausar.
- O computador que roda o programa fica ligado.
- A planilha `pedidos.xlsx` entra na cópia de segurança do escritório.
- O `LEIA-ME.md` explica tudo para quem chegar depois.
