---
titulo: Primeira automação: arrumar a pasta Downloads
trilha: 3. Automação com o modo Code
ordem: 21
duracao: 6 min
resumo: Um exemplo completo, do pedido à revisão, sem risco de perder nada.
---

Vamos fazer uma automação de verdade: separar a bagunça da pasta Downloads em subpastas por tipo (Documentos, Imagens, Planilhas, Instaladores, Outros).

## 1. Escolha a pasta

**Novo trabalho no Code** > **Escolher pasta** > Downloads. Deixe a permissão em **Perguntar**.

## 2. Peça o plano primeiro

```experimentar-code
Quero organizar esta pasta em subpastas por tipo de arquivo: Documentos (pdf, doc, docx, txt), Imagens (jpg, png, gif, webp), Planilhas (xlsx, xls, csv), Instaladores (exe, msi) e Outros. Antes de mexer, me mostre quantos arquivos iriam para cada subpasta. Não apague nada.
```

Ele vai olhar a pasta e devolver a contagem. Confira se faz sentido.

## 3. Mande fazer

Responda algo como "pode fazer". Ele vai pedir permissão para criar as subpastas e mover os arquivos: leia o cartão e clique em **Permitir**. Para não aprovar um por um, use **Permitir pelo resto da tarefa**.

## 4. Confira

Abra a pasta no Explorador (clique no nome da pasta, no topo da conversa) e veja se ficou como você queria. Não gostou? Peça ajustes ("os .zip vão para Outros") ou use **Desfazer mudanças**.

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
- Desfazer existe para arquivos que ele criou ou mudou.
- Uma automação boa vira um script que você reusa.
