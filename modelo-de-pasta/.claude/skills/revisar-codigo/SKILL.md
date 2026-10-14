---
name: revisar-codigo
description: Revisa o código que acabou de ser escrito ou alterado, com contexto limpo, procurando implementação pela metade, stub, TODO escondido e função que finge funcionar. Usar depois de qualquer alteração grande, antes de declarar uma tarefa concluída, e sempre que o usuário perguntar se ficou realmente pronto.
argument-hint: "[projeto ou arquivo]"
context: fork
allowed-tools: Read Grep Glob Bash
---

# Revisão de código com olhar limpo

Quem escreveu o código é a pior pessoa pra revisar: sabe o que quis dizer e lê a
intenção em vez do que está escrito. Por isso esta revisão roda em contexto
separado — chegando **sem** a conversa que produziu o código.

E tem um agravante comum: o usuário muitas vezes **não lê HTML, CSS e JavaScript**.
Ele não tem como abrir o arquivo e ver que ficou um handler vazio. Se isso passar
daqui, passa direto pra ele.

Alvo: `$ARGUMENTS`

## O que revisar

Se houver git no projeto, revisar o diff (`git diff`, `git diff --staged`). Sem
git, revisar os arquivos que foram tocados na tarefa. Não revisar o projeto
inteiro — o alvo é o que mudou.

## Procurar, nesta ordem

**1. Implementação que finge estar pronta** — é o achado mais importante:

- Função que retorna valor fixo, `null` ou `[]` onde deveria calcular.
- Handler de evento vazio, ou que só tem `console.log`.
- `try { ... } catch (e) {}` engolindo erro em silêncio.
- `TODO`, `FIXME`, `XXX`, "por enquanto", "temporário", "mock", "placeholder".
- Botão ou campo criado no HTML sem nada que responda a ele no JS.
- Caminho de erro que existe no código mas nunca mostra nada na tela.
- `setTimeout` fingindo carregamento que não carrega nada.

Grep ajuda a começar, mas não basta — ler as funções alteradas de fato.

**2. Quebra do que já funcionava**

- Função ou variável renomeada em um lugar e não nos outros que a chamam.
- `import`/`require` apontando pra arquivo ou export que não existe mais.
- Assinatura de função mudada sem atualizar quem chama.
- Caminho de arquivo, rota ou porta alterado em um lugar só.
- Formato de dado salvo mudou sem migração — quebra o que já estava no
  `localStorage`/IndexedDB do usuário.

**3. Coerência entre arquivos** — quando a mudança tocou vários:
mesma classe CSS existe nos dois lugares? o HTML e o JS usam o mesmo id?
o nome da chave é o mesmo nos dois lados?

**4. Coisa que não devia estar aí**
`console.log` de depuração, chave de API no front, credencial em texto,
arquivo grande novo que não pertence ao projeto, dependência nova que ninguém
pediu, `node_modules/` ou `__pycache__/` prestes a entrar no commit.

**5. Fora do escopo**
O que foi alterado além do que a tarefa pedia. Reescrita de algo que funcionava,
formatação em massa que polui o diff, arquivo mexido sem motivo.

## Verificar de verdade quando der

Rodar o que o projeto tiver: `npm run typecheck`, `npm test`,
`python tools/validate.py`, `tests.html`. Resultado real vale mais que leitura.
Se não rodou nada, dizer isso.

## Relatar

Em português, ordenado por gravidade, **sem jargão de CSS/JS** — o usuário precisa
entender o problema, não a sintaxe:

```
QUEBRADO — <o que não vai funcionar, e o que ele vai ver acontecer>
  arquivo:linha — <o que está errado>

PELA METADE — <o que parece pronto e não está>
  arquivo:linha — <o que falta>

FORA DO ESCOPO — <o que mudou além do pedido>

OK — <o que eu conferi e está certo>
```

Regras do relatório:

- Achado sem arquivo e linha não vale. Se não achei onde, não afirmo que existe.
- **Não inventar problema pra parecer útil.** Revisão que não achou nada e diz
  "não achei nada" é um resultado válido e mais útil que ruído.
- Não repetir o que o código faz. O relatório é sobre o que está errado.
- Se algo depende de escolha dele (dois comportamentos possíveis, ambos válidos),
  listar como pergunta, não como defeito.
