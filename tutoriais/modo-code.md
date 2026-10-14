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
2. **Escolha a pasta** onde ele vai trabalhar (ou crie uma com o [modelo de pasta](#/aprender/modelo-de-pasta), que é o recomendado).
3. Peça a tarefa, do mesmo jeito que pediria a uma pessoa.

Ele vai mostrando cada passo: "Olhou a pasta", "Leu planilha.xlsx", "Rodou: renomear fotos". Clique em qualquer passo para ver os detalhes.

## Permissões: você manda

O botão do escudo na caixa de texto escolhe quanta liberdade ele tem:

| Modo | O que acontece |
|---|---|
| **Perguntar** (padrão) | Lê sozinho; pede o seu OK para mudar arquivos e rodar comandos. |
| **Aceitar edições** | Muda arquivos sozinho; pede OK para comandos. |
| **Plano** | Só lê e propõe um plano. Não muda nada. Ótimo para começar. |
| **Livre** | Faz tudo sozinho, menos apagar ou publicar coisas, que sempre pedem OK. |

Quando ele pede permissão, aparece um cartão mostrando **exatamente** o que vai fazer: o comando, ou o antes e depois do arquivo (as linhas vermelhas saem, as verdes entram). Você pode **Permitir**, **Permitir pelo resto da tarefa** ou **Recusar** dizendo o que prefere.

**Leia antes de aprovar.** Se não entender o comando, recuse e pergunte "o que esse comando faz?".

## Desfazer

Errou? Embaixo da resposta aparece **Desfazer mudanças**: os arquivos que ele criou ou mudou naquela resposta voltam a ser como eram. (Comandos que apagam ou mexem fora da pasta não têm como ser desfeitos: por isso eles sempre pedem OK.)

## Arquivos protegidos

Em Configurações > Modo Code fica a lista de arquivos protegidos, como senhas e chaves (`.env`, `*.key`): as ferramentas de arquivo **nunca** leem nem mudam esses arquivos, e um comando que cite um deles sempre pede o seu OK. Ponha ali qualquer coisa sensível.

## Teto por tarefa

Uma tarefa grande pode fazer muitas chamadas. O **teto por tarefa** (padrão US$ 2) pausa a tarefa quando ela gasta isso; você decide se continua mandando "continue".

## Pedidos que funcionam bem

- "Antes de mudar qualquer coisa, me mostre o plano." (ou use o modo Plano)
- "Faça primeiro em 3 arquivos para eu conferir; depois faça o resto."
- "Crie um script que eu possa rodar de novo no mês que vem."

```experimentar-code
Olhe esta pasta e me explique, em linguagem simples, o que tem nela e o que você conseguiria automatizar aqui.
```
