---
titulo: O console: o PowerShell dentro do Clave
trilha: 6. A mesa do Code
ordem: 51
duracao: 6 min
resumo: Rodar um comando você mesmo, já na pasta do trabalho, e mandar o resultado para o Claude só quando precisar.
---

O [terminal](#/aprender/glossario/terminal) é a janela onde você manda o computador fazer as coisas digitando, em vez de clicar. No Windows, ele se chama [PowerShell](#/aprender/glossario/powershell). A aba **Console** do [painel do Code](#/aprender/painel-do-code) é um PowerShell de verdade, dentro do Clave e já aberto na pasta do trabalho.

## Para que serve

- **Ver o resultado de um comando sem gastar nada.** O que roda no Console não passa pela IA.
- **Rodar você mesmo um comando que o Claude sugeriu** e ver acontecer na hora.
- **Mostrar um erro para o Claude** com um clique, em vez de copiar e colar.
- **Deixar um programa rodando** enquanto você conversa.

## Abrir

- Clique no botão do terminal no topo da conversa ou aperte **Ctrl + `` ` ``** (a tecla à esquerda do 1; no teclado brasileiro, a das aspas).
- Na primeira vez, um console já abre na pasta do trabalho. O botão **+** abre outro, até 6 ao mesmo tempo, cada um numa guia pequena. Passe o mouse numa guia para ver em que pasta ela abriu.
- Os consoles valem para o Clave inteiro: quando você troca de trabalho, os que já estavam abertos continuam na pasta onde nasceram. Para ter um na pasta do trabalho atual, clique em **+**.
- Um pontinho numa guia avisa que ela escreveu algo novo enquanto você olhava outra.

## Usar

- Digite o [comando](#/aprender/glossario/comando) e aperte **Enter**. Dois para começar: `dir` lista o que tem na pasta, e `python --version` mostra a versão do Python.
- As setas para cima e para baixo trazem os comandos que você já digitou.
- **Copiar**: selecione com o mouse e aperte **Ctrl + C**, ou clique com o botão direito.
- **Colar**: **Ctrl + V**, ou o botão direito sem nada selecionado.
- **Parar um comando** que está rodando: **Ctrl + C** sem nada selecionado.
- Em cima, **Limpar a tela** apaga o que está à vista, e **Reiniciar o console** começa de novo na mesma pasta.
- Fechar uma guia (o X) ou reiniciar enquanto um programa sem janela roda nela (um servidor, por exemplo) pede confirmação, porque o programa para no meio.

## Mandar para o Claude

O botão **Mandar para o Claude** leva para a caixa de texto o que você selecionou no console ou, sem seleção, as últimas 60 linhas. Nada é enviado sozinho: você escreve a pergunta junto ("o que esse erro quer dizer?") e manda. Só a partir daí aquele texto vira [tokens](#/aprender/glossario/token).

## O Console e os comandos do Claude

São coisas separadas:

- Os comandos que o Claude roda **não aparecem no Console**. Cada um vira um passo na conversa ("Rodou um comando"); clique nele para ver o que o comando respondeu.
- Os comandos que ele deixa rodando, como um servidor, aparecem na aba [Tarefas](#/aprender/tarefas-em-segundo-plano).
- O Claude **não vê o seu Console**. Ele só fica sabendo do que você mandar com **Mandar para o Claude**.

## Cuidado: aqui não tem cartão de OK

No Console, quem digita é você, e o que você digita roda na hora. Os cartões de permissão, as [regras](#/aprender/permissoes) e os arquivos protegidos valem para o Claude, não para você. Por isso:

- Não cole um comando que você achou na internet sem saber o que ele faz. Na dúvida, pergunte ao Claude antes: "o que esse comando faz?".
- Comando que apaga (`Remove-Item`, `del`, `rd`) apaga de verdade, sem passar pela Lixeira.
- O que roda sem janela no Console (um servidor, um comando demorado) para quando você fecha aquela guia, ou quando fecha o Clave. Um programa com janela que você abriu por ali (o Bloco de Notas, o VS Code) continua aberto, como quando se fecha uma aba do Terminal do Windows. Só se o Clave fechar de repente (travou ou foi encerrado à força) esses programas podem fechar junto.

## Modo simples

Se o Windows não abrir o console completo, aparece o aviso de **Modo simples**. Os comandos funcionam, mas sem cores, sem as setas e sem programas que fazem perguntas, e o Ctrl + C não para um comando: nesse caso, use **Reiniciar o console**.

## Experimente

```experimentar-code
Me passe um comando de PowerShell que liste os 10 maiores arquivos desta pasta e das subpastas, com o tamanho em MB. Não rode: eu vou rodar no Console.
```

Quando a resposta chegar, copie o comando, abra o Console, cole com **Ctrl + V** e aperte **Enter**. Depois clique em **Mandar para o Claude** e pergunte o que são esses arquivos.
