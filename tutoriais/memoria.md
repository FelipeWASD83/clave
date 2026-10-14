---
titulo: Memória entre conversas
trilha: 2. Deixe o Claude do seu jeito
ordem: 12
duracao: 4 min
resumo: Como o Claude anota o que aprende sobre você, onde ficam as anotações e como mudar ou apagar.
---

Por padrão o Claude não lembra de uma conversa na outra. Com a **memória ligada**, ele passa a anotar o que vale lembrar e consulta essas anotações nas conversas seguintes.

## Como funciona

Funciona igual ao Claude Code: um **arquivo de texto para cada assunto** (quem você é, como você gosta das respostas, cada projeto seu) e um **índice** (`MEMORY.md`) que lista todos eles numa linha cada.

- No começo de cada conversa, o Claude recebe o índice.
- Quando o assunto aparece, ele abre o arquivo daquele assunto.
- Quando descobre algo útil (ou quando você pede "lembra disso"), ele anota ou atualiza.

Tudo fica **no seu computador**, em Markdown, e você vê tudo em **Configurações > Memória**.

## Ligar

Configurações > Memória > **Ligar a memória**. Vale para as conversas novas, no chat e no modo Code.

## Ver, mudar e apagar

Na mesma tela aparecem todas as memórias, com o nome, o assunto e o texto. Você pode:

- **Editar à mão**: abre o texto para você mudar e salvar.
- **Apagar**: some para sempre.
- **Pedir ao editor de memória**: escreva o que quer mudar em palavras normais e ele faz a mudança nos arquivos certos, mantendo tudo organizado. Ele roda no Sonnet 5.5 e conta o que mudou.

Exemplos de pedidos para o editor:

- "Mudei de emprego: agora sou designer numa agência. Atualize o que você sabe sobre mim."
- "Esqueça tudo sobre o meu ex."
- "Tem memória repetida? Junte e organize."
- "O que você sabe sobre mim?"

## Na conversa

Você também pode pedir direto numa conversa:

```experimentar
Lembre que eu prefiro respostas em tópicos e que trabalho com vendas de cosméticos.
```

```experimentar
Esqueça o que você anotou sobre a minha viagem para Portugal.
```

## Cuidados

O Claude é instruído a nunca anotar senhas, chaves ou números de documento e cartão. Mesmo assim, de vez em quando dê uma olhada nas memórias: elas são suas e você manda nelas.
