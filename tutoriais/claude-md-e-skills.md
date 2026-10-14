---
titulo: CLAUDE.md e skills: ensine regras e procedimentos
trilha: 4. Ir além
ordem: 31
duracao: 7 min
resumo: Escreva as regras da sua pasta e transforme tarefas repetidas em procedimentos que o Claude segue sozinho.
---

## CLAUDE.md: as regras da pasta

O [CLAUDE.md](#/aprender/glossario/claude-md) é um arquivo de texto que o Claude lê sozinho quando trabalha numa pasta (no modo Code). Ele vale para a pasta e para todas as subpastas. Se uma subpasta tiver o próprio CLAUDE.md, os dois valem, e o mais específico ganha quando eles discordam.

Coisas boas para escrever num CLAUDE.md:

- **Quem você é** e o que sabe ("não sei programar, me explique o que fez e como usar").
- **Como você quer o trabalho** ("sempre me mostre o plano antes de mudar arquivos").
- **Como a pasta é organizada** ("cada cliente tem uma subpasta com o nome dele").
- **O que nunca fazer** ("nunca apague nada da pasta Originais").
- **Lições aprendidas** ("o relatório da contabilidade usa ponto e vírgula, não vírgula").

Escreva em frases simples, como se explicasse a um assistente novo. Dá para pedir ao próprio Claude:

```experimentar-code
Crie um CLAUDE.md para esta pasta. Me faça perguntas sobre como eu trabalho, o que tem aqui e o que você nunca deve fazer, e no fim escreva o arquivo.
```

## Skills: procedimentos salvos

Uma [skill](#/aprender/glossario/skill) é um procedimento passo a passo salvo num arquivo, em `.claude/skills/nome-da-skill/SKILL.md`. Ela começa com um cabeçalho dizendo o nome e **quando usar**:

```
---
name: relatorio-mensal
description: Monta o relatório mensal de vendas. Usar quando eu pedir o relatório do mês.
---

1. Leia as planilhas de vendas do mês na pasta vendas/.
2. Some por vendedor e por produto.
3. ...
```

O Claude vê a lista de skills (nome e descrição) e carrega a skill inteira quando a tarefa combina. Você também pode chamar direto, escrevendo `/relatorio-mensal` na caixa de texto do modo Code (ao digitar `/` aparece a lista).

Skills que vêm prontas no [modelo de pasta](#/aprender/modelo-de-pasta): ver vídeos, revisar código, direção visual de sites, checklist de entrega e outras.

## Transforme o que você repete em skill

Fez uma tarefa com o Claude e ficou bom? Peça:

```experimentar-code
Transforme o que a gente acabou de fazer numa skill nesta pasta, para eu poder pedir de novo no mês que vem só com o nome dela.
```

## Onde cada coisa vale

| Arquivo | Vale para |
|---|---|
| Configurações > Personalização | Todas as conversas, no chat e no Code |
| CLAUDE.md de uma pasta | Só o modo Code, naquela pasta e nas de dentro |
| Skills em `.claude/skills` | Só o modo Code, naquela pasta e nas de dentro |
| Memória | Todas as conversas (se ligada) |
