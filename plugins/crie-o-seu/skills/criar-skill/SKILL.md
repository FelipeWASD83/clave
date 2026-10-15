---
name: criar-skill
description: Use quando a pessoa quiser ensinar ao Claude um jeito fixo de fazer uma tarefa que ela repete (um procedimento, um checklist, um padrão de texto). Entrevista a pessoa e escreve a skill no formato do Claude Code.
---

# Criar uma skill

Uma skill é um arquivo `SKILL.md` com instruções que o Claude carrega quando a tarefa combina com a descrição. Funciona no Clave e no Claude Code.

## 1. Entrevista (curta)
Pergunte, no máximo 4 coisas por vez:
- Que tarefa é essa, e quando ela aparece? (vira a descrição)
- Como você faz hoje, passo a passo? Tem um exemplo de resultado bom?
- O que não pode acontecer de jeito nenhum?
- Vale para todo lugar (skill pessoal) ou só para uma pasta (skill da pasta)?

## 2. Escrever
- Pasta: `.claude/skills/<nome>/SKILL.md` na pasta de trabalho (skill da pasta) ou `~/.claude/skills/<nome>/SKILL.md` (pessoal, vale em toda pasta). No chat, sem pasta, mostre o arquivo pronto e diga onde salvar.
- Nome: minúsculo, com hífen (`relatorio-mensal`).
- Cabeçalho:

```markdown
---
name: relatorio-mensal
description: Use quando ... (diga QUANDO usar, com as palavras que a pessoa usaria ao pedir)
---
```

  Opcionais: `disable-model-invocation: true` (só roda quando a pessoa chama por /nome), `argument-hint: [mês]`.
- Corpo: passos numerados, regras curtas, um exemplo de resultado. Menos de 500 linhas. Arquivos de apoio (modelos, exemplos) na mesma pasta, citados com link.

## 3. Testar
Mostre como chamar: `/nome-da-skill` na caixa de mensagem (ou só pedir a tarefa, e o Claude carrega sozinho). Ofereça ajustar depois do primeiro uso.
