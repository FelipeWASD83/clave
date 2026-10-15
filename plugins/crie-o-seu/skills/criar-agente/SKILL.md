---
name: criar-agente
description: Use quando a pessoa quiser criar um agente (um "especialista" com instruções, modelo e ferramentas próprios) para usar nos fluxos do Clave ou no Claude Code.
---

# Criar um agente

Um agente é um arquivo `.md` com instruções fixas, um modelo e o que ele pode usar. Nos fluxos, cada etapa pode ser feita por um agente (ex.: um "revisor-juridico" no Opus que só lê).

## Perguntas
- O que ele faz, e quando usar? (vira a descrição)
- Qual modelo? `opus` (mais inteligente, mais caro), `sonnet` (equilíbrio), `haiku` (barato e rápido) ou `inherit` (o da conversa).
- O que ele pode fazer? Só ler (`Read, Glob, Grep`), mudar arquivos (`Edit, Write`), rodar comandos (`Bash`), pesquisar na web (`WebSearch, WebFetch`). Dê só o necessário.

## Arquivo
`.claude/agents/<nome>.md` na pasta (vale ali) ou `~/.claude/agents/<nome>.md` (pessoal):

```markdown
---
name: revisor-juridico
description: Revisa contratos e aponta cláusulas arriscadas
tools: Read, Glob, Grep
model: opus
effort: high
---

Você revisa contratos em português. Para cada cláusula arriscada, diga ...
```

O corpo é escrito como instrução para o agente ("Você é ..."), com o que entregar no fim.

Também dá para criar pela tela: barra da esquerda > **Fluxos** > aba **Agentes** > Novo agente.
