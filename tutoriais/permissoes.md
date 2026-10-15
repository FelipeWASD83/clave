---
titulo: Permissões: o que o Claude faz sozinho
trilha: 3. Automação com o modo Code
ordem: 26
duracao: 6 min
resumo: Regras para liberar o que é seguro, bloquear o que nunca deve acontecer e ver o histórico de tudo.
---

O modo de permissão (Perguntar, Aceitar edições, Plano, Livre) vale para tudo de uma vez. As **regras** são mais finas: liberam ou bloqueiam uma ação específica.

## Três tipos de regra

| Regra | O que faz | Exemplo |
|---|---|---|
| **Nunca** | bloqueia, em qualquer modo | nunca mandar nada para o GitHub |
| **Sempre perguntar** | pede OK mesmo no modo Livre | sempre perguntar antes de mexer em planilha |
| **Fazer sem perguntar** | libera mesmo no modo Perguntar | pode rodar os testes sem perguntar |

Se duas regras se contradizem, **Nunca** vence **Sempre perguntar**, que vence **Fazer sem perguntar**.

## O jeito mais fácil de criar uma regra

Quando o Claude pedir permissão, clique em **Mais opções**:

- **Permitir nesta tarefa:** vale até essa resposta terminar.
- **Sempre nesta pasta…:** salva uma regra para aquela pasta.
- **Sempre, em todo o Clave…:** salva uma regra que vale em todas as pastas.

O Clave sugere a regra (por exemplo, `Bash(git status *)`) e você pode ajustar antes de salvar.

## Como uma regra é escrita

O formato é o mesmo do Claude Code, então as regras servem nos dois:

- `Bash(npm test *)`: um [comando](#/aprender/glossario/comando) (o `*` vale "qualquer coisa").
- `Edit(docs/**)`: criar ou mudar arquivos dentro da pasta `docs`.
- `Read(*.pdf)`: ler arquivos PDF.
- `WebFetch(domain:exemplo.com)`: abrir páginas de um site.
- `Fluxo`: os fluxos (só "Nunca" tem efeito; fluxo sempre pede OK).

As regras de uma pasta ficam no arquivo `.claude/settings.local.json` dela, o mesmo que o Claude Code usa.

## Proteções que continuam valendo

- **Arquivos protegidos** (Configurações > Modo Code), como `.env` e chaves: as ferramentas de arquivo nunca leem nem mudam.
- Comando que **apaga ou publica** algo pergunta mesmo com os comandos liberados, a não ser que a regra seja escrita para aquele comando.
- **Fluxo** sempre pede OK.

## Testar e conferir

Em **Permissões** (Configurações > Modo Code, ou digitando `/permissoes`), dá para:

- ver e apagar as regras;
- **testar** ("esse comando passaria?") sem rodar nada;
- ver o **histórico** de cada ação: o que foi feito sozinho, o que você permitiu, o que foi bloqueado e por quê.
