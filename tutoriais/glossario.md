---
titulo: Glossário: as palavras difíceis
trilha: 1. Primeiros passos
ordem: 7
duracao: consulta
resumo: API, token, JSON, Git, GitHub, Python, Electron e mais de 60 termos explicados em linguagem simples.
---

Palavras que aparecem no Clave, nas lições e nas respostas do Claude, explicadas do jeito mais simples possível. Não precisa ler tudo: use como dicionário. Se ficar com dúvida, pergunte ao ajudante no fim da página.

## IA (inteligência artificial)

Programa de computador que faz coisas que antes só pessoas faziam, como entender um texto, escrever, resumir ou reconhecer o que tem numa foto. O Claude é uma IA. Ela não "pensa" como gente: aprendeu padrões lendo uma quantidade enorme de texto e usa esses padrões para responder.

## Modelo

É a "versão" de uma IA. A Anthropic tem vários modelos do Claude: o **Opus** (o mais inteligente do dia a dia), o **Sonnet** (quase tão bom e mais barato), o **Haiku** (rápido e muito barato) e o **Fable** (para raciocínios muito longos). Escolher o modelo é como escolher entre um especialista caro e um assistente rápido.

## Claude

A IA da empresa Anthropic. O Clave é um jeito de conversar com o Claude pelo seu computador.

## Anthropic

A empresa que cria o Claude. Você paga a Anthropic pelo que usa da API. O Clave não é da Anthropic: é um app independente que usa a API dela.

## Prompt

O pedido que você escreve para a IA. "Resuma este texto em 3 tópicos" é um prompt. Quanto mais claro o prompt (com contexto e o formato que você quer), melhor a resposta.

## Token

O "pedacinho" de texto que a IA lê e escreve. Uma palavra curta costuma ser 1 token; uma palavra longa vira 2 ou 3. É por token que a API cobra: tanto o que você manda quanto o que o Claude responde. Mil tokens dão umas 600 a 700 palavras em português.

## Janela de contexto (contexto)

Tudo o que o Claude consegue "ter na cabeça" de uma vez: a conversa inteira, os arquivos anexados e as instruções. Os modelos atuais aguentam até 1 milhão de tokens. A régua embaixo da caixa de texto mostra quanto já foi usado. Conversa muito longa fica mais cara, porque cada resposta relê tudo.

## Raciocínio (pensamento)

Antes de responder, o Claude pode "pensar" por um tempo: planejar, conferir contas, comparar caminhos. Isso melhora respostas difíceis, mas gasta mais tokens. No Clave dá para ver um resumo desse raciocínio.

## Esforço

O quanto o Claude pensa antes de responder: Baixo, Médio, Alto, Muito alto ou Máximo. Esforço alto é melhor para problemas difíceis e código; esforço baixo é mais rápido e barato para coisas simples.

## Alucinação

Quando a IA inventa uma informação com toda a confiança, como um livro que não existe ou um número errado. Acontece menos nos modelos novos, mas acontece. Para coisas importantes, peça a fonte e confira.

## API

Sigla de "interface de programação de aplicações". É uma porta que um programa abre para outros programas conversarem com ele. A API da Anthropic é a porta pela qual o Clave manda suas mensagens ao Claude e recebe as respostas. Pense num balcão de pedidos: o Clave entrega o pedido no balcão (a API) e recebe a resposta pronta.

## Chave da API

Uma senha comprida (começa com `sk-ant-`) que diz à Anthropic de qual conta sai o pagamento. Quem tem a sua chave gasta o seu dinheiro, então nunca mostre para ninguém e nunca cole em sites. No Clave ela fica guardada só no seu computador, criptografada.

## Crédito (cobrança por uso)

A API não tem mensalidade: você coloca crédito (dinheiro) na sua conta da Anthropic e cada resposta desconta um pouco, pelo número de tokens. Quem assina o plano Max do Claude ganha um crédito mensal na API.

## Cache

Uma memória rápida que reaproveita o começo de uma conversa entre uma mensagem e outra. A parte reaproveitada custa bem menos (até 20 vezes menos). O Clave liga isso sozinho.

## Agente

Uma IA que não só responde, mas **age**: usa ferramentas, lê arquivos, roda comandos e vai fazendo uma tarefa em vários passos até terminar. No Clave, o modo Code transforma o Claude num agente que trabalha numa pasta do seu computador.

## Ferramenta (tool)

Uma ação que a IA pode pedir para o app fazer por ela, como "ler este arquivo", "pesquisar na web" ou "criar esta planilha". O Claude pede, o Clave executa (às vezes depois do seu OK) e devolve o resultado.

## Modo Code

O modo do Clave em que o Claude trabalha numa pasta do seu computador: lê e cria arquivos, mexe em planilhas e roda comandos para automatizar tarefas. Ele pede seu OK antes de mudar algo (dá para ajustar isso).

## Skill

Um procedimento salvo num arquivo de texto (`SKILL.md`) que ensina o Claude a fazer uma tarefa do seu jeito, passo a passo. Exemplo: uma skill de "revisar código" ou de "ver vídeos". O Claude usa a skill sozinho quando a tarefa combina, ou quando você chama com `/nome-da-skill`.

## CLAUDE.md

Um arquivo de texto com as regras de uma pasta: quem você é, como gosta das respostas, como os projetos são organizados. O Claude lê sozinho quando trabalha nessa pasta (no modo Code e no Claude Code). É o jeito mais forte de deixar o Claude do seu jeito.

## MCP (conector)

Sigla de Model Context Protocol, um padrão para ligar a IA a outros serviços (documentação, sistemas, bancos de dados). Um "conector MCP" dá ao Claude ferramentas novas vindas desse serviço.

## Markdown

Um jeito simples de formatar texto com símbolos: `**negrito**`, `# Título`, `- item de lista`. O Claude escreve em Markdown e o Clave transforma em texto formatado. Arquivos `.md` são textos em Markdown.

## Arquivo e pasta

Arquivo é um documento (foto, planilha, texto). Pasta é uma "gaveta" que guarda arquivos e outras pastas. No Windows você vê os dois no Explorador de Arquivos.

## Caminho (de arquivo)

O "endereço" de um arquivo no computador, como `C:\Users\Ana\Documents\orcamento.xlsx`. Cada parte separada por `\` é uma pasta dentro da outra.

## Extensão de arquivo

As letras depois do ponto no nome do arquivo, que dizem o tipo dele: `.xlsx` (planilha do Excel), `.pdf`, `.jpg` (foto), `.txt` (texto), `.py` (programa em Python).

## Terminal

Uma janela onde você dá ordens ao computador digitando, em vez de clicar. Parece coisa de hacker, mas é só outro jeito de mandar o computador fazer as coisas.

## PowerShell

O terminal do Windows. No modo Code, quando o Claude "roda um comando", ele usa o PowerShell.

## Comando

Uma ordem digitada no terminal. Por exemplo, `mkdir Fotos` cria uma pasta chamada Fotos.

## Script

Um arquivo com uma sequência de comandos ou instruções que o computador executa de uma vez. Um script pode, por exemplo, renomear 500 fotos em segundos. O Claude é ótimo escrevendo scripts.

## Programa (app)

Um conjunto de instruções que o computador executa para fazer algo útil: o Excel, o navegador, o próprio Clave.

## Código

O texto que diz ao computador o que fazer, escrito numa linguagem de programação.

## Linguagem de programação

Um idioma que o computador entende, com regras rígidas. Cada uma é boa para uma coisa: **Python** para automação e dados, **JavaScript** para sites, **C#** e **C++** para programas e jogos, **SQL** para bancos de dados. Você não precisa saber nenhuma para usar o Claude: ele escreve o código por você.

## Python

Uma linguagem de programação fácil de ler, muito usada para automatizar tarefas, mexer em planilhas e analisar dados. O próprio Clave é feito em Python por dentro.

## JavaScript

A linguagem que faz os sites serem interativos (botões, animações, jogos no navegador). Não tem nada a ver com Java, apesar do nome.

## HTML

A linguagem que diz o que tem numa página da internet: títulos, textos, imagens, botões. Arquivos `.html` abrem no navegador. O Claude pode criar páginas HTML e o Clave mostra a prévia.

## CSS

A linguagem que diz como a página fica: cores, tamanhos, posições. HTML é o conteúdo; CSS é a aparência.

## JSON

Um formato de texto para guardar dados organizados, que tanto pessoas quanto programas conseguem ler. Por exemplo: `{"nome": "Ana", "idade": 30}`. Muitos programas e APIs trocam informação em JSON. (O nome se lê "djêison", e é por isso que muita gente escreve "Jason", mas não tem nada a ver com pessoa.)

## CSV

Uma planilha em forma de texto simples: cada linha é uma linha da tabela e as colunas são separadas por vírgula ou ponto e vírgula. O Excel abre arquivos `.csv`.

## Planilha (.xlsx)

O arquivo do Excel, com abas, células, fórmulas e gráficos. O Claude consegue ler, criar e alterar planilhas no Clave.

## Fórmula

Uma conta dentro de uma célula do Excel que começa com `=`, como `=SOMA(B2:B10)`. Quando os números mudam, o resultado muda sozinho.

## Macro

Uma automação gravada dentro de uma planilha (arquivos `.xlsm`). Macros podem ser perigosas se vierem de desconhecidos, porque executam ações no computador.

## PDF

Um formato de documento que fica igual em qualquer computador, bom para enviar e imprimir. O Claude lê PDFs e o Clave consegue exportar planilhas em PDF.

## Git

Um programa que guarda o histórico de um projeto: cada vez que você salva uma versão (um "commit"), dá para voltar nela depois. É como o "histórico de versões" do Google Docs, mas para pastas inteiras.

## Repositório

Uma pasta de projeto controlada pelo Git, com todo o histórico de versões. Pode ficar só no seu computador ou também no GitHub.

## Commit

Uma "foto" do projeto num momento, com uma mensagem dizendo o que mudou. "Commitar" é salvar essa versão no histórico do Git.

## Branch (ramo)

Uma linha paralela de trabalho no Git, para testar mudanças sem mexer na versão principal. Depois, se ficou bom, junta de volta.

## GitHub

Um site onde as pessoas guardam repositórios Git na internet: serve de backup, para compartilhar projetos e para trabalhar em equipe. Git é o programa; GitHub é o site que hospeda. O próprio Clave é atualizado a partir do GitHub.

## Pull request (PR)

Um pedido, no GitHub, para juntar as mudanças de um ramo na versão principal, com espaço para revisar e comentar antes.

## Issue

Uma "anotação de problema ou ideia" num repositório do GitHub: um bug, uma sugestão, uma tarefa.

## Clonar

Baixar uma cópia de um repositório do GitHub para o seu computador, com todo o histórico.

## Electron

Uma tecnologia para fazer programas de computador usando as mesmas linguagens dos sites (HTML, CSS e JavaScript). O app do Claude, o Discord, o VS Code e o próprio Clave usam Electron: por isso eles parecem sites, mas abrem numa janela própria.

## Node.js

Um programa que roda JavaScript fora do navegador. É a base do Electron e de muitas ferramentas de programação.

## npm

A "loja" de pacotes do Node.js: um jeito de baixar bibliotecas prontas com um comando (`npm install`).

## pip

A "loja" de pacotes do Python (`pip install nome-do-pacote`). O instalador do Clave usa o pip para baixar o que ele precisa.

## Biblioteca (pacote)

Código pronto que outra pessoa escreveu e que um programa usa para não reinventar a roda. O Clave usa uma biblioteca para ler planilhas, por exemplo.

## Servidor

Um programa que fica esperando pedidos e respondendo. Os servidores da Anthropic respondem ao Clave; e o Clave tem um pequeno servidor dentro do seu próprio computador, que só ele usa.

## Localhost

O "endereço" do seu próprio computador (`127.0.0.1`). Quando algo roda em localhost, só o seu computador acessa.

## Porta

Um número que separa os serviços dentro de um mesmo computador, como os apartamentos de um prédio. O Clave usa a porta 8040 do seu computador.

## Navegador

O programa que abre sites: Chrome, Edge, Brave, Firefox.

## Site e página

Página é um documento da internet (um arquivo HTML). Site é um conjunto de páginas.

## Deploy (publicar)

Colocar um site ou programa "no ar", num servidor da internet, para outras pessoas acessarem.

## Bug

Um erro num programa, que faz ele se comportar errado.

## Backup

Uma cópia de segurança dos seus arquivos, guardada em outro lugar (HD externo, nuvem, GitHub), para não perder nada se o computador quebrar.

## Criptografia

Embaralhar uma informação de um jeito que só quem tem a "chave" certa consegue ler. A chave da API fica criptografada no seu computador.

## Token de acesso

Uma senha especial, comprida, que dá a um programa permissão para usar uma conta sua (por exemplo, o GitHub). Igual à chave da API: nunca compartilhe.

## Código aberto (open source)

Programa cujo código qualquer pessoa pode ler, e muitas vezes usar e modificar, seguindo uma licença.

## Versão

O número que diz qual "edição" de um programa você tem, como 1.4.2. Número maior quer dizer mais novo. O botão Atualizar do Clave baixa a versão mais nova.

## Diff

A comparação entre o antes e o depois de um arquivo: linhas tiradas aparecem em vermelho (com `-`) e linhas novas em verde (com `+`). O modo Code mostra o diff de cada mudança.

## Variável de ambiente

Uma configuração que o computador guarda "por fora" dos programas e que eles podem ler. Às vezes guarda chaves de API; o Clave não usa isso de propósito, para a chave ficar mais protegida.

## Prompt injection

Um truque em que um texto (de um site, e-mail ou arquivo) traz instruções escondidas para a IA, tentando fazê-la obedecer outra pessoa. Por isso o Clave pede o seu OK antes de ações importantes: confira sempre o que está aprovando.
