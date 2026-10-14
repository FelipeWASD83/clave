---
titulo: O modelo de pasta (recomendado)
trilha: 4. Ir além
ordem: 30
duracao: 7 min
resumo: Uma pasta pronta com regras, skills e referências visuais que faz o Claude trabalhar muito melhor.
---

**Recomendação forte:** se você vai usar o modo Code para mais do que uma tarefa solta, comece por uma pasta criada com o **modelo**. É a diferença entre um assistente que você tem que explicar tudo toda vez e um que já chega sabendo como você trabalha.

O modelo foi montado a partir da pasta de trabalho de alguém que usa o Claude todo dia para dezenas de projetos, com o que funcionou de verdade e sem nada pessoal.

## O que vem dentro

- **CLAUDE.md**: as regras da pasta, que o Claude lê sozinho. Já vem com boas práticas testadas: planejar antes de mudar, não inventar resultado, conferir antes de dizer que terminou, um projeto por pasta, guardar versões com Git, explicar em linguagem simples. No topo, uma seção **Sobre mim** que o Clave preenche com as suas respostas.
- **Skills** (procedimentos prontos):
  - *ver-video*: o Claude "assiste" a vídeos (arquivo ou link do YouTube, TikTok, Instagram...) tirando quadros e transcrevendo a fala. [Veja a lição](#/aprender/ver-videos).
  - *direcao-visual* e *revisar-visual*: decidir o visual de um site antes de fazer e conferir o resultado com prints.
  - *checklist-web* e *entregar-site*: tudo o que precisa estar certo antes de dizer que um site está pronto ou de publicar.
  - *revisar-codigo*: procura o que ficou pela metade ou só finge funcionar.
  - *pesquisa-tecnica*: pesquisar antes de escolher uma ferramenta ou biblioteca.
  - *gml*: para quem faz jogos no GameMaker.
  - *inicializar-pasta*: arruma a pasta e o mapa de projetos na primeira vez.
- **Referências visuais**: uma biblioteca de sites bem feitos, com prints e o que aproveitar de cada um, para os sites que o Claude fizer não ficarem com cara de "site genérico de IA".
- **Guias**: LEIA-PRIMEIRO, PORTAS (para projetos web) e instalar-ferramentas (Git, GitHub, Python, Node).

## Como criar

1. **Novo trabalho no Code** > **Criar pasta com o modelo**.
2. Escolha onde criar (os Documentos, por exemplo) e o nome da pasta.
3. Responda as perguntas sobre você: elas entram no CLAUDE.md.
4. Pronto: o Clave já abre o modo Code na pasta nova.

Cada projeto seu vira uma **subpasta** dela (`orcamento-da-casa`, `site-da-loja`...). As regras e as skills da pasta-mãe valem para todas.

## Depois de criar

Abra o `CLAUDE.md` (num editor de texto, ou peça ao Claude para mostrar) e ajuste o que quiser. Ele é seu: quanto mais ele refletir o seu jeito, melhores as respostas.

```experimentar-code
Leia o CLAUDE.md desta pasta e me explique, em tópicos curtos, as regras que você vai seguir aqui. Depois me pergunte o que eu quero mudar.
```

## Funciona também no Claude Code

O modelo usa os mesmos arquivos que o Claude Code (o programa oficial da Anthropic para programar). Se um dia você usar o Claude Code, abra nele a mesma pasta: as regras e as skills funcionam igual.
