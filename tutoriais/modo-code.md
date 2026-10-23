---
titulo: Como o modo Code funciona
trilha: 3. Automação com o modo Code
ordem: 20
duracao: 7 min
resumo: O Claude trabalhando numa pasta do seu computador, com você aprovando cada mudança.
---

No chat, o Claude só conversa. No **modo Code**, ele vira um [agente](#/aprender/glossario/agente): trabalha numa **pasta do seu computador**, lê e cria arquivos, mexe em planilhas e roda [comandos](#/aprender/glossario/comando). É aqui que mora a automação.

## Começando

1. Na barra da esquerda, clique em **Novo trabalho no Code**.
2. **Escolha o ambiente**, a pasta onde ele vai trabalhar, no painel embaixo da caixa de texto. O Clave já começa na última pasta que você usou; em **Escolher ambiente** dá para pegar outra ou criar uma com o [modelo de pasta](#/aprender/modelo-de-pasta), que é o recomendado. No mesmo painel, **Ativar modo automático** liga o modo Livre (explicado abaixo).
3. Peça a tarefa, do mesmo jeito que pediria a uma pessoa.

Ele vai mostrando cada passo: "Olhou a pasta", "Leu planilha.xlsx", "Rodou: renomear fotos". Clique em qualquer passo para ver os detalhes.

## O painel ao lado

Os botões no topo da conversa abrem um painel do lado direito, com abas: **Arquivos** (a pasta de trabalho; clicar num arquivo abre o **Visualizador**), **Console** (o PowerShell dentro do Clave), **Navegador** (você e o Claude na mesma página) e **Tarefas** (o que está rodando em segundo plano). **Ctrl+J** abre e fecha o painel, e dá para arrastar a borda dele para mudar a largura. Tudo em [O painel do Code](#/aprender/painel-do-code).

## Permissões: você manda

O botão do escudo na caixa de texto escolhe quanta liberdade ele tem:

| Modo | O que acontece |
|---|---|
| **Perguntar** (padrão) | Lê sozinho; pede o seu OK para mudar arquivos e rodar comandos. |
| **Aceitar edições** | Muda arquivos sozinho; pede OK para comandos. |
| **Plano** | Só lê e apresenta um plano num cartão. Você aprova (e escolhe como ele executa) ou pede outro. Ótimo para começar. |
| **Livre** | Faz tudo sozinho, inclusive publicar, mandar e-mail e mexer fora da pasta. Só comando que apaga arquivos ou dados pede OK. No navegador do Code, usa qualquer site, clica e digita sem perguntar. |

Quando ele pede permissão, aparece um cartão mostrando **exatamente** o que vai fazer: o comando, ou o antes e depois do arquivo (as linhas vermelhas saem, as verdes entram). Você pode **Permitir** ou **Recusar** dizendo o que prefere. Em **Mais opções** dá para liberar aquilo pelo resto da tarefa ou salvar uma regra ("sempre nesta pasta" ou "sempre em todo o Clave"), para ele não perguntar de novo. Veja a lição de [permissões](#/aprender/permissoes).

**Leia antes de aprovar.** Se não entender o comando, recuse e pergunte "o que esse comando faz?".

## O plano antes da tarefa grande

Antes de mexer em muita coisa (três arquivos ou mais, mover ou renomear arquivos, reorganizar uma pasta), o Claude mostra um cartão **Posso fazer assim?** com o plano, e só começa depois da sua resposta:

- **Pode ir**: ele executa, e as permissões continuam valendo como sempre.
- **Mudar o plano**: escreva o que quer diferente no campo e ele refaz o plano.
- **Não fazer**: ele para e pergunta o que você prefere.

Isso vale em qualquer modo. Se preferir que ele vá direto, desligue em **Configurações > Modo Code > Pedir OK antes de tarefas grandes**.

## Desfazer

Errou? Embaixo da resposta aparece **Desfazer mudanças**: os arquivos que ele criou ou editou naquela resposta voltam a ser como eram. O que um **comando** fez (mover, renomear, apagar, rodar um script) não volta com o botão: por isso o card do comando mostra o que vai rodar antes, e os que apagam sempre pedem OK (os que mexem fora da pasta também, menos no modo Livre). Para uma mudança grande feita por comando, peça antes uma lista do que vai ser mexido, ou uma cópia. Mais jeitos de voltar atrás em [Desfazer, backup e Git: a sua rede de segurança](#/aprender/rede-de-seguranca).

## Arquivos protegidos

Em Configurações > Modo Code fica a lista **Arquivos e pastas protegidos**, como senhas e chaves (`.env`, `*.key`): as ferramentas de arquivo **nunca** leem nem mudam esses arquivos, e um comando que cite um deles sempre pede o seu OK. Ponha ali qualquer coisa sensível.

## Teto por tarefa

Uma tarefa grande pode fazer muitas chamadas. O **teto por tarefa** (padrão US$ 2) pausa a tarefa quando ela gasta isso; você decide se continua mandando "continue". Para gastar menos no Code, veja [O modo Code sem desperdício](#/aprender/code-sem-desperdicio).

## Tarefa grande? Fluxo

Para tarefa grande, peça "faça isso como um fluxo": o Claude divide em etapas, cada uma no modelo certo (por exemplo, Opus planeja e Sonnet faz), e mostra o custo estimado antes de começar. Veja a lição de [fluxos](#/aprender/fluxos-e-agentes).

## Pedidos que funcionam bem

- "Antes de mudar qualquer coisa, me mostre o plano." (ou use o modo Plano)
- "Faça primeiro em 3 arquivos para eu conferir; depois faça o resto."
- "Crie um script que eu possa rodar de novo no mês que vem."

```experimentar-code
Olhe esta pasta e me explique, em linguagem simples, o que tem nela e o que você conseguiria automatizar aqui.
```
