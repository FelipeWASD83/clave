---
titulo: Tarefas em segundo plano e servidores locais
trilha: 6. A mesa do Code
ordem: 53
duracao: 7 min
resumo: O que fica rodando enquanto você faz outra coisa, como acompanhar e parar, e o que são localhost e porta.
---

"Em segundo plano" é tudo o que continua rodando enquanto você faz outra coisa: uma resposta comprida que ainda está chegando, um [fluxo](#/aprender/fluxos-e-agentes) com várias etapas, uma [rotina](#/aprender/rotinas), o download do vídeo de uma lição ou um comando que o Claude deixou rodando, como o servidor de um site.

## A aba Tarefas

Ela mostra tudo isso num lugar só. Para abrir:

- **Ctrl + Shift + Y**, ou o botão de Tarefas no topo de qualquer conversa (no chat também);
- ou o contador **1 rodando** (ou 2, 3...) na barra da esquerda, embaixo de **Novo trabalho no Code**. Ele só aparece quando tem algo rodando.

A aba tem duas listas: **Rodando agora** e **Terminadas há pouco** (que ficam ali por 30 minutos). Cada cartão mostra:

- o tipo (**Resposta**, **Fluxo**, **Rotina**, **Comando** ou **Download**), há quanto tempo roda e de que conversa veio; nas respostas, fluxos e rotinas, também quanto já gastou;
- o estado: **Rodando**, **Esperando o seu OK**, **Concluída**, **Deu erro** ou **Parada**;
- num fluxo, quantas etapas já terminaram; num download, a porcentagem;
- num comando, o comando de verdade e, se ele for um servidor, o endereço com o botão **Abrir no navegador**;
- os botões **Parar**, **Ver registro** (o que a tarefa escreveu até agora) e **Ir para a conversa**, quando ela é de outra conversa.

Quando uma tarefa de mais de 30 segundos termina e você está em outra conversa ou em outro programa, o Clave avisa. Com a janela dele em segundo plano, vem também uma notificação do Windows (dá para desligar em **Configurações > Aparência > Notificação do Windows**).

## Comandos que ficam rodando

Normalmente, quando o Claude roda um [comando](#/aprender/glossario/comando), ele espera o comando acabar (o limite é de 2 minutos, e ele pode aumentar até 10) e lê o resultado. Só que alguns comandos não acabam sozinhos: um servidor de site, por exemplo, fica ligado até alguém desligar. Para esses, o Claude deixa o comando **em segundo plano**:

- o cartão de permissão diz **Deixar rodando em segundo plano** e mostra o comando;
- o passo na conversa mostra o comando com "(em segundo plano)", e a resposta segue sem esperar;
- o comando aparece na aba Tarefas como **Rodando**, até alguém parar;
- o Claude pode olhar o que o comando escreveu ("Olhou um comando em segundo plano") e parar ele ("Parou um comando em segundo plano") sem pedir o seu OK;
- são no máximo 5 por conversa;
- **o Clave para todos quando fecha.** Nada fica rodando escondido no seu computador depois. Um programa com janela que o comando abriu (um editor, o navegador que um servidor abre sozinho) continua aberto, à vista, para você fechar quando quiser.

Começar um comando assim segue o modo de permissão, como qualquer comando: pede OK em **Perguntar** e **Aceitar edições**, roda sozinho no **Livre** e não roda no **Plano**.

Também serve para um trabalho demorado, como converter muitos arquivos: peça "rode em segundo plano" e continue conversando. A aba avisa quando acabar.

## Parar

- Na aba Tarefas, **Parar** encerra o comando e o que ele abriu sem janela. Um programa com janela que ele abriu (o VS Code, o Bloco de Notas, o navegador que um servidor abre) continua aberto. O cartão passa para **Terminadas há pouco**, como **Parada**.
- Ou peça ao Claude: "pare o servidor".
- Ou feche o Clave: ele para todos, com o mesmo cuidado com as janelas. Só se o Clave fechar de repente (travou ou foi encerrado à força) os programas com janela podem fechar junto.

**Parar** também funciona numa resposta, num fluxo ou numa rotina que ainda estão rodando. Um fluxo para junto com a resposta que o começou.

## Servidores locais, em palavras simples

- [Servidor](#/aprender/glossario/servidor) é um programa que fica esperando pedidos e respondendo. Um servidor de site entrega as páginas para o navegador.
- [Localhost](#/aprender/glossario/localhost) é o seu próprio computador. `http://localhost:8000` é um site que só existe aí, e só você vê.
- [Porta](#/aprender/glossario/porta) é o número depois dos dois-pontos. Cada servidor usa uma, e dois não podem usar a mesma ao mesmo tempo: é o erro de "porta ocupada".

Por que um site que está na sua pasta precisa de um servidor? O navegador do Clave só abre endereços `http` e `https`, e algumas coisas de um site só funcionam quando ele chega assim. Para um site simples, um comando como `python -m http.server 8000` basta; projetos maiores, feitos com [Node.js](#/aprender/glossario/node-js), costumam usar `npm run dev`. O Claude escolhe o certo para cada pasta.

Um servidor ligado não gasta crédito: ele só entrega páginas para o seu navegador. Só gasta quando o Claude lê o que ele escreveu ou abre a página.

## Locais: o que está rodando no computador

No [navegador](#/aprender/navegador), o botão **Locais** (e a tela inicial do navegador) lista os servidores rodando no seu computador agora: os que os comandos do Claude abriram, com o nome do comando, e os de outros programas, como um que você mesmo ligou no [Console](#/aprender/console). Um clique abre. O que responde mas não é uma página aparece com o aviso "responde, mas não é uma página (talvez uma API)".

Um servidor que você ligou no Console não aparece na aba Tarefas, porque não foi o Claude que ligou. Ele para com **Ctrl + C** naquele console, ou quando você fecha a guia dele.

No cartão de um comando, **Abrir no navegador** abre o endereço na aba Navegador quando você está num trabalho do Code, e no navegador do computador quando está numa conversa do chat.

## Experimente

```experimentar-code
Rode em segundo plano um comando de PowerShell que conte de 1 a 60, um número por segundo, e no fim escreva "pronto". Não crie nem mude nenhum arquivo.
```

Se aparecer o cartão **Deixar rodando em segundo plano**, clique em **Permitir**. Depois abra a aba **Tarefas** com **Ctrl + Shift + Y**. Clique em **Ver registro** para ver os números chegando. Deixe terminar para ver o cartão ir para **Terminadas há pouco**, ou clique em **Parar** antes.

A lição [Um site do zero até o navegador](#/aprender/site-do-zero-ao-navegador) faz o mesmo com um servidor de verdade.
