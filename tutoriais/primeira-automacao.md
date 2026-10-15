---
titulo: Primeira automação: arrumar a pasta Downloads
trilha: 3. Automação com o modo Code
ordem: 21
duracao: 6 min
resumo: Um exemplo completo, do pedido à revisão, sem risco de perder nada.
video: primeira-automacao
---

Vamos fazer uma automação de verdade: separar a bagunça da pasta Downloads em subpastas por tipo (Documentos, Imagens, Planilhas, Instaladores, Outros).

## 1. Escolha a pasta

**Novo trabalho no Code** > **Escolher a pasta de trabalho** > **Outra pasta…** > Downloads (se você já usou outras pastas, o botão se chama **Escolher ambiente**). Deixe a permissão em **Perguntar**.

## 2. Peça o plano primeiro

```experimentar-code
Quero organizar esta pasta em subpastas por tipo de arquivo: Documentos (pdf, doc, docx, txt), Imagens (jpg, png, gif, webp), Planilhas (xlsx, xls, csv), Instaladores (exe, msi) e Outros. Antes de mexer, me mostre quantos arquivos iriam para cada subpasta. Não apague nada.
```

Ele vai olhar a pasta e devolver a contagem. Confira se faz sentido.

## 3. Mande fazer

Responda algo como "pode fazer". Ele vai pedir permissão para criar as subpastas e mover os arquivos: leia o cartão e clique em **Permitir**. Para não aprovar um por um, use **Mais opções > Permitir comandos nesta tarefa** (quem cria as pastas e move os arquivos é um comando; no cartão de mudar um arquivo, a mesma opção se chama **Permitir nesta tarefa**). Vale até a resposta terminar.

## 4. Confira

Abra a pasta no Explorador (clique no nome da pasta, no topo da conversa) e veja se ficou como você queria. Não gostou? Peça ajustes na mesma conversa ("os .zip vão para Outros"). O botão **Desfazer mudanças** não serve aqui: ele volta os arquivos que o Claude escreveu ou editou, e quem moveu os arquivos foi um comando. Quer poder voltar atrás? Peça antes: "guarde uma lista do que foi movido e para onde".

## 5. Transforme em algo que se repete

O melhor da automação é poder rodar de novo:

```experimentar-code
Crie um script chamado organizar-downloads.ps1 que faça essa mesma organização sempre que eu rodar, e me explique como rodar com dois cliques.
```

Dá até para pedir que rode sozinho todo dia, pelo Agendador de Tarefas do Windows:

```experimentar-code
Configure o Agendador de Tarefas do Windows para rodar o organizar-downloads.ps1 todo dia às 18h. Me mostre o comando antes e me explique como desligar depois.
```

## O que você aprendeu

- Pedir o plano antes evita surpresas.
- Os cartões de permissão mostram exatamente o que vai acontecer.
- Desfazer mudanças volta os arquivos que ele escreveu ou editou, não o que um comando fez (como mover arquivos).
- Uma automação boa vira um script que você reusa.
