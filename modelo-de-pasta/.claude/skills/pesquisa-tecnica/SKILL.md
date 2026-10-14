---
name: pesquisa-tecnica
description: Pesquisar a fundo antes de decidir uma questão técnica - qual biblioteca usar, se uma abordagem se sustenta, se algo ainda funciona na versão atual, se roda no sistema e no hardware do usuário. Usar antes de escolher dependência, API, formato, engine ou arquitetura; quando a resposta depender de versão, changelog ou de algo que mudou; e quando um erro cheira a breaking change. Não usar para dúvida factual simples nem para algo que ler o próprio projeto responde.
argument-hint: "[assunto ou decisão]"
allowed-tools: WebSearch WebFetch Read Grep Glob Bash
---

# Pesquisa técnica antes de decidir

O objetivo não é produzir um documento. É **chegar numa recomendação que se
sustenta** — e conseguir defendê-la quando o usuário perguntar "por que não a
outra?" três mensagens depois.

Vale a regra geral dele: **fato confirmado, inferência e especulação são coisas
diferentes** e não podem ser misturadas. E o pior resultado possível aqui é
preencher lacuna com plausibilidade.

Assunto: `$ARGUMENTS`

## 0. Olhar o projeto antes de olhar a internet

Pesquisar antes de conhecer o terreno produz recomendação incompatível. Então,
primeiro:

- Ler a documentação do projeto (`CLAUDE.md`, `README.md`) e as
  decisões que já foram tomadas.
- Ver o que já está instalado e em qual versão: `package.json`, `package-lock.json`,
  `requirements.txt`, `import`/`require` espalhados pelo código.
- Checar se o projeto **já resolve isso** de alguma forma. Trocar coisa que
  funciona por preferência pessoal é proibido — se a substituição vale a pena,
  o motivo tem que aparecer no relatório.
- Anotar as restrições que já existem: runtime, build e **alvo de deploy** — a
  seção 6 do `CLAUDE.md` da raiz diz como cada projeto é publicado, e isso
  elimina candidato antes da primeira busca (Cloudflare Worker não roda API de
  Node; app Electron não tem as restrições de um site; hospedagem estática não
  executa backend).

Se a decisão não pertence a nenhum projeto da pasta, perguntar a qual projeto
ela pertence antes de continuar.

## 1. Escrever as perguntas de decisão

Antes da primeira busca, listar o que precisa ser respondido para decidir.
Tipicamente:

- Quais são os 2–4 candidatos reais? (Não dez. Dez opções é fuga de escolha.)
- O que exatamente cada um resolve, e o que **não** resolve?
- Está vivo? Última release, último commit, issues abertas se acumulando?
- Roda no sistema do usuário (seção 0 do `CLAUDE.md`)? No Windows: sem WSL, sem "só funciona no Linux"?
- Peso: tamanho do bundle, dependências transitivas, tempo de build.
- Licença permite o uso dele — inclusive em projeto **comercial**, se algum dos
  projetos desta pasta for?
- Se envolve IA local ou GPU: cabe na placa de vídeo e na memória do computador do usuário (seção 0 do `CLAUDE.md`; se não estiver lá, perguntar)?
- Qual o custo de sair depois, se der errado?

Esse mapa é a lista de buscas. Sem ele, saem cinco buscas parecidas.

## 2. Buscar em camadas

1. **Terreno** — o que é, vocabulário, quais são as alternativas de fato usadas hoje.
2. **Fonte primária** — abrir a **documentação oficial** e o **repositório**.
   Tutorial de blog é a origem da maior parte do erro de detalhe: costuma estar
   uma ou duas versões major atrás e ensinar API que já não existe.
3. **Changelog e releases** — ler o que mudou. É aqui que aparece o breaking
   change que explica por que o exemplo da internet não roda.
4. **Atrito** — procurar ativamente quem reclama: issues abertas, "problems with",
   "alternatives to", thread de gente que migrou pra fora. Se toda fonte elogia,
   só foi lido material de marketing.
5. **Estado atual** — incluir o ano na query quando atualidade importar. Confirmar
   a versão estável de agora, não a que estava no ar quando o modelo foi treinado.

Parar quando as buscas novas pararem de trazer informação nova — não quando bater
um número. Se a última busca ainda revelou algo desconhecido, não acabou.

## 3. Verificar de verdade — a parte que só quem tem terminal faz

Aqui existe terminal. Então, sempre que der, **não acreditar: testar.**

- Conferir a versão real publicada (`npm view <pacote> version`,
  `pip index versions <pacote>`) em vez de repetir a versão do tutorial.
- Montar o menor exemplo possível numa pasta descartável **fora da pasta do
  projeto**, instalar o candidato e rodar. Se não roda em 10 linhas, isso é dado.
- Windows: usar `python`, nunca `python3`. Comando de exemplo em PowerShell.
- Se o candidato depende de compilar algo nativo, testar isso — é onde a maioria
  quebra no Windows.
- **Não instalar nada dentro de um projeto do usuário durante a pesquisa.**
  A pesquisa é descartável; a instalação só acontece depois que ele aprovar.

O que foi testado vira **confirmado**. O que só foi lido continua sendo o que a
fonte disse — e isso precisa ficar visível no relatório.

## 4. Recomendar, não empurrar catálogo

Uma recomendação, com motivo. Comparar só o que muda a decisão dele — não montar
tabela de doze linhas com features que ele nunca vai usar.

Pesar, quando for relevante: resolve o problema real, dificuldade de usar,
compatibilidade com o que já existe no projeto, peso, manutenção futura,
confiabilidade, custo de sair. **Não escolher pelo que é tecnicamente mais
sofisticado.** Para ferramenta pequena, "não usar biblioteca nenhuma" é uma
resposta válida e frequentemente a certa.

Se as opções empatam de verdade, dizer que empatam e qual critério desempata —
não fingir que existe um vencedor claro.

## 5. Entregar

**Sempre gerar o arquivo**, em `docs/pesquisa-<assunto-em-kebab-case>.md` dentro
da pasta do projeto (criar `docs/` se não existir). No chat vai só o resumo curto:
recomendação, motivo em duas linhas, e o que ele precisa decidir. Não repetir o
arquivo inteiro no chat.

Estrutura do arquivo:

```markdown
# Pesquisa: <assunto>
Data: AAAA-MM-DD · Projeto: <pasta>

## Pergunta
<a decisão que precisava ser tomada, em uma frase>

## Recomendação
<o que usar e por quê, em até 5 linhas>

## Candidatos avaliados
<um bloco por candidato: o que é, versão atual, licença, prós, contras,
por que foi ou não escolhido>

## O que eu testei
<comando rodado e resultado real. Se não testei nada, escrever "não testei" e por quê>

## Riscos e o que pode dar errado
<inclusive o custo de trocar depois>

## Confirmado / inferência / incerto
Confirmado: <o que está na fonte primária ou foi testado aqui>
Inferência: <o que eu deduzi juntando coisas confirmadas>
Incerto: <fonte única, informação antiga, ou o que eu não achei>

## Fontes
<links, com o que cada um sustenta>
```

Regras do arquivo:

- Escrito em português, explicando **o que a coisa faz e o que muda para ele** —
  nada de aula sobre o funcionamento interno de biblioteca web.
- "Não encontrei dado confiável sobre X" é informação útil e vai no arquivo.
- Nada de `node_modules/`, `dist/` ou pasta de teste sobrando depois. Limpar a
  pasta descartável usada nos testes.

## 6. Depois

O resultado alimenta a **seção 5 das regras da pasta** (plano antes do código): a
recomendação vira a abordagem do plano, e os riscos viram o item "o que pode
quebrar". Não sair implementando junto com a pesquisa — pesquisa, plano,
aprovação, código.

Se ele perguntar depois algo que a pesquisa não cobriu, dizer isso e pesquisar de
novo. Não improvisar em cima do que já tem.
