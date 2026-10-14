---
name: inicializar-pasta
description: Faz a primeira arrumação de uma pasta criada a partir do modelo - olha os projetos que já existem, preenche o mapa do CLAUDE.md, monta o launch.json e o PORTAS.md e garante Git em cada projeto. Usar quando o usuário chamar /inicializar-pasta, ou quando pedir para atualizar o mapa dos projetos.
argument-hint: "[nada, ou o nome que a pasta deve ter]"
disable-model-invocation: true
---

# Inicializar a pasta

Esta pasta nasceu de um modelo: as regras, as skills e a biblioteca visual
estão prontas, mas o `CLAUDE.md` da raiz não sabe **quais projetos existem
aqui**. Sem isso, ele descreve uma pasta imaginária.

O trabalho desta skill é fechar essa distância uma vez, com cuidado, e sair.

## 0. Ver se já não foi feito

Se o mapa da seção 8 do `CLAUDE.md` **já tem projeto listado**, a pasta já foi
inicializada. Não rodar de novo por cima: perguntar se o usuário quer só
**atualizar** o mapa (projeto que entrou, projeto que saiu), que é um trabalho
menor, feito com os passos 2 e 4.

## 1. Olhar a pasta antes de escrever qualquer coisa

Listar a raiz e separar em três grupos:

- **Projetos**: as subpastas de trabalho de verdade.
- **Infra do modelo**: `.claude/`, `_organizacao/`, `.gitignore`, `CLAUDE.md`,
  `PORTAS.md`, `LEIA-PRIMEIRO.md`. Não são projeto e não entram no mapa.
- **Fora do lugar**: arquivo solto na raiz, `.zip`, pasta com espaço ou
  parêntese no nome, sufixo `_1`/`_2` de download repetido. **Não mover nada
  agora**: anotar e reportar no fim. Mexer na pasta sem avisar é pior que
  deixar bagunçado.

## 2. Abrir cada projeto: não deduzir pelo nome

Para cada pasta de projeto, **ler antes de descrever**:

1. `CLAUDE.md`, `README.md` e qualquer `.md` de documentação da pasta. Se
   existirem, mandam mais que qualquer dedução.
2. O que diz a tecnologia: `package.json` (olhar `scripts`), `requirements.txt`,
   `pyproject.toml`, `*.csproj`, `*.yyp`, `index.html`, planilhas e documentos.
3. O ponto de entrada: `main`, `src/main.*`, `server.py`, `app.py`, `*.bat`,
   `index.html`.

Só depois escrever a linha do mapa:

```
| pasta | o que é, numa frase que diga o propósito | tecnologia | como rodar |
```

- **Uma frase que distinga.** "Planilhas" não distingue nada. "Controle de
  gastos da casa, uma planilha por ano" distingue.
- **Como rodar é o comando literal**, com a porta quando houver. Pasta que não
  roda (documentos, planilhas) diz isso.
- Duas pastas parecidas? **Descobrir e escrever a diferença.**
- Não achou o que a pasta é depois de abrir os arquivos? **Perguntar.** Uma
  linha inventada no mapa engana todas as conversas seguintes.

## 3. Perguntar o que não dá para descobrir sozinho

Perguntar de uma vez, em bloco:

1. **Algum projeto é de cliente ou está no ar?** Muda tudo: confirmar antes de
   mexer, nunca publicar sozinho, skill `entregar-site` obrigatória.
2. **Algum projeto é privado**, para não abrir nem comentar sem pedido?
3. **Algum projeto deve ficar fora do Git** de propósito?

As respostas viram observações no mapa (seção 8) e, se for o caso, regras
`deny`/`ask` no `.claude/settings.json`.

## 4. Montar o `launch.json` e o `PORTAS.md`

Todo projeto que roda como site ou servidor ganha uma entrada no
`.claude/launch.json`, com a porta tirada das faixas do `PORTAS.md` (e anotada
na tabela de lá). Duas armadilhas:

- **Nunca `python3`** no Windows: use `python`.
- **Nunca repetir porta**: o que um site guarda no navegador é separado por
  porta; dois projetos na mesma porta misturam os dados.

Formato para site estático:

```json
{
  "name": "nome-do-projeto",
  "runtimeExecutable": "python",
  "runtimeArgs": ["-m", "http.server", "4310", "--bind", "127.0.0.1", "--directory", "nome-do-projeto"],
  "port": 4310
}
```

Formato para projeto com script próprio (`cwd` é a pasta onde o comando roda):

```json
{
  "name": "nome-do-projeto",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "dev"],
  "cwd": "nome-do-projeto",
  "port": 5173
}
```

Depois, **conferir que o arquivo é JSON válido** e subir pelo menos um projeto
para confirmar que a configuração funciona de verdade.

## 5. Git

```powershell
powershell -ExecutionPolicy Bypass -File ".\_organizacao\git-setup.ps1"
```

Ele cria o Git em quem não tem e lista quem está sem cópia no GitHub. **Não
publica nada**: mostrar a lista e deixar o usuário decidir o que sobe.

## 6. Fechar o `CLAUDE.md`

- Preencher a seção 8 (mapa) e, se houver, as observações por projeto.
- Datar a seção 9 (pendências) com a data de hoje. Sem pendência, escrever
  "nenhuma pendência aberta" com a data.
- Conferir a seção 0 (Sobre mim): se estiver vazia, perguntar o essencial ao
  usuário e preencher.

## 7. Relatar

```
Pasta: <nome>
Projetos mapeados: <n>: <lista curta>
launch.json e PORTAS.md: <n> entradas. Testei: <qual subi e o que vi>
Git: <n> já tinham, <n> criei. Sem cópia no GitHub: <lista ou "nenhum">
Fora do lugar (não mexi): <arquivo solto, nome fora do padrão, zip>
Precisa de você: <o que não deu para descobrir e não foi inventado>
```

Não marcar como feito o que não foi conferido.
