---
name: criar-comando
description: Use quando a pessoa quiser um atalho de barra (/nome) para um pedido que ela repete, com espaço para completar (ex.: /orcamento cliente valor).
---

# Criar um comando de barra

Um comando é um arquivo `.md` cujo texto vira a mensagem quando a pessoa digita `/nome`. Funciona no Clave e no Claude Code.

## Arquivo
`.claude/commands/<nome>.md` na pasta de trabalho (ou `~/.claude/commands/` para todas as pastas). Subpasta vira prefixo: `.claude/commands/vendas/orcamento.md` é `/vendas:orcamento`.

```markdown
---
description: Monta um orçamento a partir do nome do cliente e do valor
argument-hint: [cliente] [valor]
---

Monte um orçamento para $0 no valor de R$ $1, usando o modelo modelo-orcamento.docx da pasta.
```

## O que dá para usar no texto
- `$ARGUMENTS`: tudo o que veio depois do comando.
- `$0`, `$1`, ...: cada palavra (texto com espaço vai entre aspas: `/orcamento "Padaria Sol" 1500`).
- Cabeçalho opcional: `model: haiku` (roda num modelo mais barato), `allowed-tools: Read, Bash(git status *)` (libera essas ações sem perguntar, só durante o comando; use com cuidado).

Teste digitando `/` na caixa de mensagem: o comando novo aparece na lista.
