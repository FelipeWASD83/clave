# CLAUDE.md: regras desta pasta de trabalho

Instruções para o Claude (no modo Code do Clave ou no Claude Code) em qualquer
trabalho dentro desta pasta e das subpastas dela. O `CLAUDE.md` de um projeto
específico, quando existir, **manda mais que este arquivo** para aquele
projeto. E o que eu disser na conversa vale mais que qualquer arquivo.

---

## 0. Sobre mim

<!-- SOBRE-MIM -->

---

## 1. Como responder

- **Português do Brasil**, direto ao ponto. Sem preâmbulo e sem elogiar o pedido.
- Tamanho da resposta proporcional ao assunto: pergunta simples, resposta curta.
- Se eu estiver errado, dizer logo no começo, não escondido no fim.
- Se houver um caminho claramente melhor do que o que eu pedi, apontar **antes**
  de executar. Se eu entender e mantiver a decisão, respeitar.
- **Não inventar** arquivos, funções, resultados de teste ou fontes. Não afirmar
  que algo funciona sem ter conferido. Quando não souber, dizer que não sabe.
- Separar o que é fato conferido, o que é dedução e o que é chute.
- Explicar em linguagem simples **o que foi feito e como usar**. Detalhe técnico
  só quando eu pedir ou quando for necessário para eu decidir algo.
- Precisa que eu mude algo na mão? Dizer no formato "no arquivo X, procure Y e
  troque por Z".

## 2. Ambiente

- Sistema: veja a seção 0. Se não estiver escrito, perguntar ou conferir antes
  de supor.
- No Windows, o terminal é o **PowerShell**: comandos de exemplo em PowerShell.
- **Usar `python`, nunca `python3`** no Windows (o `python3` abre a loja da
  Microsoft em vez de rodar).
- Antes de supor que um programa existe (Git, Node, Python, Excel), conferir.

## 3. Regras desta pasta

1. **Um projeto = uma subpasta.** Não criar pasta nova na raiz sem eu pedir;
   projeto novo que eu pedi já é o pedido.
2. **Nada solto na raiz.** Na raiz ficam só os arquivos de regra e de guia
   (`CLAUDE.md`, `LEIA-PRIMEIRO.md`, `PORTAS.md`, `.gitignore`) e as pastas
   `.claude/` e `_organizacao/`.
3. **Nomes de pasta em `minusculas-com-hifen`**, sem espaço, sem acento, sem
   parênteses e sem `_1`/`_2` de download repetido.
4. **Nunca versionar nem entregar:** `node_modules/`, `__pycache__/`, `dist/`,
   `.env`, senhas, chaves, tokens. O `.gitignore` da raiz já cobre o básico.
5. **`_originais/`** (em qualquer projeto) guarda material bruto insubstituível
   (fotos, vídeos, documentos originais): nunca apagar, converter ou
   "otimizar" por conta própria.
6. **`.claude/`** guarda a configuração do Claude nesta pasta:
   - `skills/`: procedimentos prontos (seção 3.1);
   - `referencias-visuais/`: a biblioteca de referências para sites e apps;
   - `launch.json`: como rodar cada projeto web (com o `PORTAS.md`);
   - `settings.json`: permissões do Claude Code.

### 3.1 Skills desta pasta

| Skill | Para quê |
|---|---|
| `ver-video` | Ver e ouvir vídeos (arquivo ou link): quadros + transcrição |
| `direcao-visual` | Decidir o visual de um site ou app antes de escrever CSS |
| `revisar-visual` | Abrir no navegador, tirar prints e corrigir o que está quebrado ou feio (manual: `/revisar-visual`) |
| `checklist-web` | O que precisa estar pronto antes de dizer que um site funciona |
| `entregar-site` | Checklist antes de publicar um site (manual: `/entregar-site`) |
| `revisar-codigo` | Procurar implementação pela metade, stub e função que finge funcionar |
| `pesquisa-tecnica` | Pesquisar antes de escolher biblioteca, API ou abordagem |
| `gml` | GameMaker: consultar o manual oficial em vez de escrever de memória |
| `inicializar-pasta` | Primeira arrumação da pasta e do mapa de projetos (manual: `/inicializar-pasta`) |

Skill citada dentro de outra não carrega sozinha: quando uma regra ou skill
mandar seguir outra, carregar as duas.

## 4. Antes de mexer em qualquer projeto

1. Ler o `CLAUDE.md`, o `README.md` e os outros `.md` **da própria pasta do
   projeto**. Eles mandam mais que este arquivo.
2. **Não deduzir o que o projeto faz pelo nome.** Abrir os arquivos.
3. Preservar o que já funciona. Não reescrever metade do projeto para corrigir
   um problema pequeno; se uma mudança grande vale a pena, explicar por quê antes.
4. Achou um problema importante fora do que eu pedi? Avisar, não corrigir calado.
5. Terminou? Conferir se a linha do projeto no mapa (seção 8) continua certa.

## 5. Plano antes de mudar

Em tarefa que não é trivial (mais de um arquivo, sistema novo, site novo,
reorganização, correção que exige entender o projeto): apresentar um **plano
curto** e esperar meu OK antes de mudar arquivos. O plano diz:

1. o que eu entendi que é para fazer, em uma frase;
2. quais arquivos vão ser criados, alterados ou apagados;
3. a abordagem escolhida (e a alternativa descartada, se havia);
4. o que pode quebrar do que já funciona;
5. como o resultado vai ser conferido.

Tarefa trivial (trocar um texto, uma cor, um valor que eu apontei) não precisa
de plano. Se eu disser "faz do jeito que achar melhor", escolher, contar em
poucas linhas o que foi decidido e seguir. Se no meio do caminho o plano se
mostrar errado, parar e avisar.

**Site ou app novo:** antes de qualquer CSS, ler
`.claude/referencias-visuais/CLAUDE.md` e seguir a skill `direcao-visual`.

## 6. Conferir antes de dizer que terminou

- Rodar o que der para rodar: testes, o script, o site no navegador.
- Projeto web: skill `checklist-web` antes de dizer "pronto".
- Mudança grande: skill `revisar-codigo`.
- **Não dizer que funciona sem ter visto funcionar.** Não deu para testar? Dizer
  isso com todas as letras.

## 7. Git, versões e publicação

- **Todo projeto tem git.** Projeto novo nasce com `git init`. Antes de uma
  mudança grande, conferir `git status`: se já houver mudança minha não salva,
  avisar antes de mexer (misturar as duas tira a chance de desfazer).
- **Salvar versão (commit) ao terminar** uma tarefa conferida, não no meio. A
  mensagem diz em português **o que mudou e por quê**.
- O commit leva só o que foi mudado na tarefa (`git add` nos arquivos dela).
- **Enviar para o GitHub (`git push`) e publicar site são decisão minha:**
  mostrar o comando e esperar. Nunca `git push --force`.
- **Versão X.Y.Z** em projeto que alguém usa: Z para correção, Y para novidade,
  X para mudança grande. Anotar no `CHANGELOG.md` do projeto, em linguagem
  simples, o que mudou para quem usa.

## 8. Mapa dos projetos

> Vazio porque a pasta é nova. A skill `/inicializar-pasta` preenche (ou peça:
> "atualize o mapa dos projetos").

| Pasta | O que é | Tecnologia | Como rodar |
|---|---|---|---|
| _(vazio)_ | | | |

## 9. Pendências

Nenhuma pendência registrada ainda.
