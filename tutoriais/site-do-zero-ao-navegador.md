---
titulo: Um site do zero até o navegador
trilha: 6. A mesa do Code
ordem: 54
duracao: 10 min
resumo: Um exemplo completo: o Claude cria um site, liga um servidor local, abre no navegador do Clave, você pede uma mudança e desliga o servidor no fim.
---

Esta lição junta a mesa inteira do Code num trabalho de verdade: o Claude cria um site de uma página, deixa um [servidor local](#/aprender/tarefas-em-segundo-plano) rodando, abre o site no [navegador](#/aprender/navegador) do Clave, você olha, pede uma mudança, confere, e no fim desliga o servidor pela aba Tarefas.

## Antes de começar

- **Use a janela do Clave**, aberta pelo atalho **Clave** na área de trabalho. O navegador do painel só existe nela.
- **Modo de permissão**: **Perguntar** (o padrão) ou **Aceitar edições**. No **Plano** ele só lê: não cria os arquivos nem liga o servidor.
- **Modelo**: um site de uma página sai bem no modelo padrão. Para um site maior, o conselheiro de modelo avisa se vale subir.

## 1. Uma pasta para o site

Clique em **Novo trabalho no Code** > **Escolher ambiente** (ou **Escolher a pasta de trabalho**) > **Criar pasta com o modelo…** e dê um nome como `meu-site`. O [modelo de pasta](#/aprender/modelo-de-pasta) traz regras de qualidade e referências visuais que ajudam o site a sair bonito.

Prefere uma pasta vazia? Crie no Explorador do Windows e escolha em **Outra pasta…**.

## 2. Peça o site e a prévia

```experimentar-code
Crie nesta pasta um site de uma página para a Confeitaria Exemplo, uma confeitaria de bairro: topo com o nome e uma frase, uma seção com 4 doces (nome, descrição curta e preço), o horário de funcionamento e um botão "Fazer encomenda" que leva até uma seção de contato. Use só HTML, CSS e JavaScript, sem nada para instalar. Depois ligue um servidor local em segundo plano e abra o site no navegador do Clave para eu ver.
```

O que acontece, passo a passo:

1. **Ele escreve os arquivos** (`index.html`, um arquivo de estilo e, se precisar, um de JavaScript). No modo Perguntar, cada arquivo pede o seu OK. Para não aprovar um por um, use **Mais opções > Permitir nesta tarefa**.
2. **Ele pede para ligar o servidor.** O cartão diz **Deixar rodando em segundo plano** e mostra o comando, algo como `python -m http.server 8000` (o Python já está no seu computador, porque o Clave usa). Leia e clique em **Permitir**.
3. **O site aparece.** O endereço surge na saída do comando (`http://localhost:8000`), a aba Navegador abre sozinha com a faixa **O Claude está usando o navegador**, e ele confere a página, às vezes com um print. Como o endereço é do seu computador (`localhost`), abrir e ler não pedem OK: o cartão de site só aparece para sites fora do seu computador.
4. **Ele conta o que fez.** Na barra da esquerda aparece **1 rodando**: é o servidor, que continua ligado depois da resposta.

## 3. Olhe você mesmo

O site é de verdade, e é seu:

- Role a página e clique no botão **Fazer encomenda**.
- Arraste a borda do painel para deixar o navegador mais estreito: dá uma ideia de como o site fica numa tela pequena.
- Abra a aba **Arquivos** para ver o que ele criou. Dois cliques num arquivo abrem no Visualizador.
- Quer ver no seu navegador de sempre? Clique em **Abrir no navegador do computador**. Funciona enquanto o servidor estiver ligado, e só no seu computador.

## 4. Peça uma mudança

Na mesma conversa, escreva algo como:

> Troque as cores para tons de rosa e marrom, aumente o nome no topo e deixe os preços em negrito. Depois confira no navegador.

- O cartão de cada arquivo mostra o antes e o depois: o vermelho sai, o verde entra.
- Não precisa ligar o servidor de novo: ele entrega sempre a versão mais nova dos arquivos.
- Ele pode abrir a página de novo para conferir. Se a mudança não aparecer para você, clique em **Recarregar** na barra do navegador (ou aperte **F5** com a página ou a barra do navegador em foco).
- Não gostou? **Desfazer mudanças**, embaixo da resposta, volta os arquivos como eram. Recarregue a página para ver.

Quer que ele mesmo teste o botão? Peça: "clique em Fazer encomenda e confira se a página desce até o contato". No modo Perguntar, cada clique pede OK. Para ele clicar sem perguntar só no seu site local, use no cartão **Mais opções > Sempre nesta pasta…** com a regra `Navegador(clicar:localhost)` (vale em qualquer porta; `Navegador(clicar:localhost:8000)` vale só na 8000).

## 5. Desligue o servidor

1. Aperte **Ctrl + Shift + Y**, ou clique em **1 rodando** na barra da esquerda: abre a aba **Tarefas**.
2. No cartão do comando você vê o comando, há quanto tempo ele roda e o endereço com **Abrir no navegador**.
3. Clique em **Parar**. O cartão vai para **Terminadas há pouco**, como **Parada**.

Se você recarregar o navegador agora, ele mostra **Não deu para abrir esta página**. É o esperado: o site só existe enquanto o servidor está ligado. Os arquivos continuam na pasta.

Esqueceu de desligar? Fechar o Clave desliga também. Para ver o site outro dia, abra o mesmo trabalho e peça: "ligue o servidor do site de novo e abra no navegador".

## Quando algo dá errado

### O servidor não subiu

O passo na conversa diz que o comando terminou logo, ou o navegador mostra "Nada respondeu nesse endereço".

- Na aba Tarefas, em **Terminadas há pouco**, o comando aparece como **Deu erro**. **Ver registro** mostra o que ele escreveu.
- Normalmente o Claude lê o erro e tenta outro caminho sozinho. Se não tentar, peça: "o servidor não subiu, veja o que aconteceu".
- Se o erro diz que `python` não é reconhecido, peça para ele tentar com `py` no lugar de `python`.
- Se você recusou o cartão, ou está no modo **Plano**, o comando não roda: troque para **Perguntar** e peça de novo.
- Se a conversa já tem 5 comandos rodando em segundo plano, pare um na aba Tarefas.

### A porta está ocupada

No registro aparece algo com "10048", "address already in use" ou "EADDRINUSE": já tem outro servidor naquela [porta](#/aprender/glossario/porta).

- Clique em **Locais**, no navegador, para ver o que está rodando e em que porta.
- Se for um servidor do Clave que você não usa mais, pare na aba Tarefas. Se for um que você ligou no Console, aperte **Ctrl + C** naquele console.
- Ou simplesmente peça: "use outra porta, a 8001".

### A aba diz "O navegador só funciona na janela do Clave"

O Clave está aberto num navegador comum, e não na janela dele. Isso acontece quando ele foi aberto por outro caminho, ou quando a janela dele não pôde ser baixada: ela é um programa à parte, de uns 110 MB, que vem da internet na instalação e em algumas atualizações.

- Feche o Clave e abra de novo pelo atalho **Clave** na área de trabalho (ou pelo `Clave.bat`, na pasta do Clave), com a internet ligada.
- Enquanto isso, a própria aba lista os servidores do computador e abre o site no seu navegador de sempre. Só o Claude fica sem poder conferir o site.

### Outros tropeços

- **A mudança não apareceu**: clique em **Recarregar** na barra do navegador.
- **"Nada respondeu nesse endereço"** depois de um tempo: o servidor parou. Veja na aba Tarefas e peça para ligar de novo.
- **O Claude não abre o navegador**: confira **Configurações > Modo Code > Deixar o Claude usar o navegador do Code**.

## E para pôr na internet?

O servidor local só existe no seu computador. Publicar o site (fazer o [deploy](#/aprender/glossario/deploy)) é outro passo, com uma conta num serviço de hospedagem. A lição [Criar páginas e pequenos apps](#/aprender/paginas-e-apps) conta o caminho.
