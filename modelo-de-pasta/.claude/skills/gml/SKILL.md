---
name: gml
description: Escrever, ler ou corrigir GML (GameMaker Language) consultando o manual oficial em vez de escrever de memória. Usar sempre que a tarefa envolver GameMaker - código .gml, projeto .yyp, eventos de objeto, shaders, dúvida sobre função ou API - e antes de afirmar que qualquer função existe ou se comporta de determinada forma.
argument-hint: "[o que fazer em GML]"
allowed-tools: Bash Read Write Edit Grep Glob WebSearch
---

# GML sem inventar função

Tarefa: `$ARGUMENTS`

## Por que esta skill existe

GML é a linguagem onde eu mais alucino, e por um motivo específico: existem
**três gerações de API** com nomes parecidos, e a internet está cheia de código
das duas primeiras.

- Game Maker 8 / GMS 1.x — `instance_create()`, `argument0`, `d3d_*`
- GMS 2.0–2.2 — camadas chegaram, scripts ainda eram arquivo-único
- GMS 2.3+ até hoje — funções nomeadas, structs, constructors, métodos, `static`

Chute em GML não dá erro de sintaxe óbvio nem "undefined is not a function" no
navegador: dá erro de compilação no meio do trabalho do usuário, ou pior, uma
função que existe mas faz outra coisa. E, se o GameMaker não estiver instalado
nesta máquina (conferir: `C:\ProgramData\GameMakerStudio2` e a IDE em `Program Files`),
**não existe compilador aqui para me corrigir**. A verificação tem que ser feita
por mim, antes de entregar.

Regra dura: **nenhuma chamada de função GML sai daqui sem estar confirmada no
manual oficial.** Não "eu lembro que existe". Confirmada.

## As ferramentas desta skill

O manual oficial (`manual.gamemaker.io`) **devolve 403 para o WebFetch**, mas
responde normalmente a `curl`/`urllib`. Por isso a skill traz dois scripts.
Rodar de dentro de `.claude/skills/gml/`:

```bash
python docgml.py buscar instance_create
```

Busca no índice local do manual (3113 páginas) e devolve caminho + URL. É
instantâneo e offline.

```bash
python docgml.py ver array_foreach
```

Baixa a página da função e imprime em texto limpo — sintaxe, argumentos, retorno
e exemplo. `--completo` para não cortar em 120 linhas.

```bash
python checar-gml.py caminho/do/projeto
```

Varre os `.gml` e lista toda chamada `nome(...)` que **não** está no manual, não
foi definida no próprio projeto e não é palavra-chave. É o linter de invenção.
Rodar **sempre** antes de entregar código GML. Ele não valida assinatura nem
comportamento — só pega nome que não existe, que é o erro mais comum.

```bash
python docgml.py atualizar --canal monthly
```

Regera o índice a partir do `sitemap.xml` do manual. Vale rodar se o projeto for
de uma versão diferente ou se o índice estiver velho.

**Canais do manual:** `monthly` (padrão, versão corrente), `lts` (LTS 2026.0) e
`beta`. Se o projeto declarar a versão do GameMaker, usar o canal correspondente
— há funções que só existem em um deles.

## Procedimento

1. **Descobrir a versão.** Ler o `.yyp` do projeto (campo de versão da IDE) ou
   perguntar. Sem isso, assumir `monthly` e **dizer que assumiu**.
2. **Ler o projeto antes de escrever.** Onde o código vive, quais scripts já
   existem, que convenção de nome ele usa. Ver
   `referencias/projeto-gamemaker.md`.
3. **Ler `referencias/armadilhas.md`** antes de escrever a primeira linha. São
   os erros que eu cometo por reflexo, todos conferidos no manual.
4. **Escrever o código**, consultando `docgml.py ver` para cada função que eu
   não usei nesta mesma sessão. Sim, para cada uma.
5. **Rodar `checar-gml.py`** no que foi escrito. Zero suspeitas ou explicação
   para cada uma.
6. **Entregar dizendo o que não foi testado.** Sem GameMaker instalado, o
   máximo honesto é "compilei mentalmente e o nome de todas as funções está
   confirmado no manual" — nunca "testei" ou "funciona".

## O que é seguro escrever de cabeça

Estrutura da linguagem: `if/else`, `for`, `while`, `repeat`, `do/until`,
`switch`, `with`, `try/catch/finally`, `function`, `constructor`, `new`,
`delete`, `static`, `var`, `global.`, `enum`, `#macro`, `#region`. Isso é
estável e eu erro pouco.

O que **nunca** é seguro de cabeça: **nome e assinatura de função de runtime**,
nome de constante (`c_*`, `ev_*`, `vk_*`, `fa_*`, `bm_*`), nome de variável
built-in de instância, e ordem de argumentos. Tudo isso vai ao manual.

## Erros de postura, não de sintaxe

- **Não reescrever o projeto do usuário para "ficar mais moderno".** Se o
  projeto usa `ds_list`, não trocar tudo por array porque eu acho melhor. Vale
  a regra da seção 4 das regras da pasta (`CLAUDE.md`).
- **Não inventar organização de projeto GameMaker.** A IDE gera a estrutura;
  criar `.yy` na mão quebra o projeto. Ver `referencias/projeto-gamemaker.md`.
- **Não afirmar performance sem medir.** "YYC é mais rápido", "`with` é lento",
  "struct é mais rápido que ds_map" — isso vira chute em cima de folclore de
  fórum. Se importar, medir; se não der pra medir, dizer que é hipótese.
- Fonte confiável, nesta ordem: manual oficial → release notes
  (`releases.gamemaker.io`) → tutoriais do `gamemaker.io` → fórum e comunidade
  (útil, mas frequentemente desatualizado: muito post de GMS 1.x sem aviso).
