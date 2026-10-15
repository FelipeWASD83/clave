---
titulo: O painel do Code: arquivos, visualizador, console, navegador e tarefas
trilha: 6. A mesa do Code
ordem: 50
duracao: 6 min
resumo: A mesa de trabalho ao lado da conversa: ver a pasta, abrir arquivos, rodar comandos, usar o navegador e acompanhar o que está rodando.
---

No [modo Code](#/aprender/modo-code), o Claude trabalha numa pasta do seu computador. O **painel do Code** é a sua mesa de trabalho ao lado da conversa: dá para ver os arquivos que ele criou, abrir cada um, rodar um comando você mesmo, olhar um site e acompanhar o que ficou rodando, sem sair do Clave. Tudo o que você faz no painel, sem pedir ao Claude, não gasta crédito.

## Abrir, fechar e ajustar

- No topo da conversa, à direita, ficam os botões do painel, um ícone para cada aba. Passe o mouse em cima para ver o nome e o atalho.
- **Ctrl + J** abre e fecha o painel, na última aba que você usou.
- **Arraste a borda** do painel para deixar mais largo ou mais estreito. **Dois cliques na borda** voltam à largura padrão.
- Fechar o painel não perde nada: o console guarda o que rodou, e o que estava rodando continua rodando.
- Se você deixar o painel aberto, o próximo trabalho no Code já abre com ele.

## As abas

| Aba | Para que serve | Atalho |
|---|---|---|
| **Arquivos** | a pasta do trabalho inteira, em árvore | Ctrl + Shift + E |
| **Visualizador** | mostra o arquivo que você escolher: código, texto, imagem, PDF, planilha, Word, áudio e vídeo | dois cliques num arquivo |
| **Console** | o [PowerShell](#/aprender/glossario/powershell) de verdade, já aberto na pasta | Ctrl + `` ` `` (a tecla à esquerda do 1) |
| **Navegador** | um [navegador](#/aprender/glossario/navegador) que você e o Claude usam juntos | Ctrl + Shift + L |
| **Tarefas** | o que está rodando em segundo plano, com o botão **Parar** | Ctrl + Shift + Y |

Numa conversa do chat, o painel tem só a aba Tarefas (e a **Prévia**, quando você abre uma página que o Claude escreveu).

## Arquivos: a pasta à vista

- Clique numa pasta para abrir. **Dois cliques** num arquivo abrem no Visualizador.
- O campo de cima filtra pelo nome. **Enter** procura em todas as subpastas.
- **Botão direito** num item: abrir com o programa padrão, mostrar no Explorador, copiar o [caminho](#/aprender/glossario/caminho), **Mencionar na conversa**, renomear (F2), criar arquivo ou pasta e **Mandar para a Lixeira** (Delete). O que vai para a Lixeira do Windows dá para recuperar por lá.
- **Arraste um arquivo** para a caixa de texto: o caminho dele entra no pedido, e você completa ("melhore o `index.html`").
- O que o Claude mudou nesta conversa aparece com a marca **mudado pelo Claude**. O ícone de uma trava marca os arquivos protegidos (Configurações > Modo Code), que o Claude não lê.
- Pastas de sistema, como `.git` e `node_modules`, ficam escondidas. O botão do olho mostra.
- A lista se atualiza sozinha quando algo muda na pasta.
- Abrir um programa ou script (`.exe`, `.bat`, `.ps1`...) com o programa padrão pede confirmação antes, porque abrir é rodar.

## Visualizador: ler sem gastar

- Abre até 8 arquivos, em guias pequenas no topo.
- Código com cores e número de linha; Markdown formatado ou como código; planilhas (as primeiras 200 linhas e 50 colunas; para ver tudo, abra no Excel); Word (só o texto); imagens, PDF, áudio e vídeo.
- **Ctrl + F** procura dentro do arquivo. Escreva `:` e um número (`:120`) para ir até a linha.
- **Mudanças do Claude**: num arquivo que ele mexeu nesta conversa, mostra o antes e o depois (o vermelho saiu, o verde entrou).
- Numa página [HTML](#/aprender/glossario/html), **Ver como página** abre na Prévia. Os arquivos de fora da página (o CSS, as imagens) podem não aparecer ali; para ver o site inteiro, use o [navegador com um servidor local](#/aprender/site-do-zero-ao-navegador).
- Na conversa, clicar no nome do arquivo num passo ("Leu", "Escreveu", "Editou") abre ele aqui.
- Arquivo protegido: você pode clicar em **Mostrar mesmo assim**. Você vê; o Claude continua sem ler.

Ler um arquivo no Visualizador não gasta nada. Pedir ao Claude "abra e me mostre" gasta, porque ele lê o arquivo inteiro e ainda escreve uma resposta.

## Console, Navegador e Tarefas

Cada uma dessas abas tem uma lição própria:

- **Console**: o PowerShell já na pasta, para você rodar um comando sem pedir ao Claude. O botão **Mandar para o Claude** leva o resultado para a caixa de texto. Veja [O console](#/aprender/console).
- **Navegador**: um navegador de verdade, que o Claude também usa para conferir um site. Fora do modo Livre, cada site novo pede o seu OK na primeira vez em cada tarefa (o seu computador, `localhost`, não pede), e clicar e digitar num site pedem o seu OK a cada vez. Veja [O navegador](#/aprender/navegador).
- **Tarefas**: respostas que ainda estão chegando, fluxos, rotinas, servidores que o Claude deixou rodando e downloads, com o botão **Parar**. Quando tem algo rodando, aparece também um contador na barra da esquerda, embaixo de **Novo trabalho no Code**. Veja [Tarefas em segundo plano](#/aprender/tarefas-em-segundo-plano).

E a lição [Um site do zero até o navegador](#/aprender/site-do-zero-ao-navegador) usa todas juntas, do começo ao fim.

## As setinhas do tour

Nas primeiras vezes que você abre o Code, o Clave mostra setinhas em cima dos botões do painel. Quer ver de novo? Em **Aprender**, clique em **Refazer os tours**.

## Experimente

```experimentar-code
Crie nesta pasta um arquivo dicas.txt com cinco dicas curtas para organizar arquivos no computador. Depois me diga onde ele está.
```

Quando ele terminar, aperte **Ctrl + J**, abra a aba **Arquivos** e dê dois cliques no `dicas.txt`. Depois clique em **Mudanças do Claude** para ver o que ele criou nesta conversa.
