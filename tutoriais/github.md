---
titulo: Git e GitHub para quem nunca usou
trilha: 4. Ir além
ordem: 33
duracao: 7 min
resumo: Guardar versões do seu trabalho, ter backup na internet e ligar o GitHub ao Clave.
---

## Git: o histórico de versões

O [Git](#/aprender/glossario/git) guarda "fotos" da sua pasta ao longo do tempo (os [commits](#/aprender/glossario/commit)). Mudou algo e estragou? Volta para a foto anterior. É o melhor seguro para trabalhar com o modo Code, porque você sempre consegue desfazer.

Você não precisa aprender os comandos: peça ao Claude.

```experimentar-code
Esta pasta já usa Git? Se não usa, explique o que é, ative e salve uma primeira versão de tudo. Me mostre os comandos antes de rodar.
```

Depois, no fim de cada trabalho:

```experimentar-code
Salve uma versão no Git com uma mensagem explicando o que mudou hoje.
```

## GitHub: o Git na internet

O [GitHub](#/aprender/glossario/github) é um site que guarda repositórios Git na nuvem. Serve para:

- **backup**: o computador quebrou, seu trabalho está lá;
- **compartilhar** projetos com outras pessoas;
- **trabalhar em equipe**, com [issues](#/aprender/glossario/issue) e [pull requests](#/aprender/glossario/pull-request).

Repositórios podem ser **privados** (só você vê) ou **públicos**. **Nunca** envie senhas, chaves ou dados pessoais para o GitHub, nem em repositório privado.

Para isso existe o [`.gitignore`](#/aprender/glossario/gitignore): um arquivo de texto na pasta com a lista do que o Git nunca deve guardar (por exemplo, `.env` e `*.key`). O que está nele não entra nas versões e não vai para o GitHub. O que nunca deve sair do seu computador está em [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados).

```experimentar-code
Confira se esta pasta tem um .gitignore que deixa de fora senhas, chaves e arquivos com dados pessoais. Se faltar algo, me mostre o que você colocaria antes de mudar.
```

## Ligar o GitHub ao Clave

Em **Configurações > GitHub**:

- Se você tem o programa **gh** (GitHub CLI) instalado e logado, clique em **Usar o login do gh**.
- Ou crie um **token pessoal** no GitHub (Settings > Developer settings > Personal access tokens) e cole no Clave.

Com o GitHub ligado:

- **Anexar arquivos** de um repositório numa conversa (clipe > Arquivos do GitHub).
- Ligar o botão **GitHub** na caixa de texto para o Claude consultar seus repositórios, ler código, issues e pull requests.
- (Opcional) Deixar ele **criar issues, comentar e abrir pull requests**: cada ação pede o seu OK antes.

```experimentar
Liste os meus repositórios do GitHub e me diga quais estão parados há mais tempo.
```

## Enviar o seu projeto para o GitHub

No modo Code, peça:

```experimentar-code
Quero guardar esta pasta no GitHub como repositório privado. Me explique o passo a passo e faça o que der por aqui, sempre me mostrando os comandos antes.
```

O Clave pede o seu OK antes de um `git push` (o comando que envia para a internet), menos no modo **Livre**, em que ele envia sozinho.
