---
titulo: Glossário: as palavras difíceis
trilha: 1. Primeiros passos
ordem: 7
duracao: consulta
resumo: API, token, JSON, Git, GitHub, Python, Electron e mais de 90 termos explicados em linguagem simples.
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

## Tokens de entrada e de saída {#entrada-e-saida}

Os dois lados da conta de cada resposta. **Entrada** é tudo o que vai para o Claude: a sua mensagem, os anexos, as instruções e a conversa inteira até ali (ele relê tudo a cada resposta). **Saída** é o que ele escreve, contando o raciocínio. Nos modelos atuais, um token de saída custa 5 vezes o de entrada: por isso pedir uma resposta mais curta economiza.

## Janela de contexto (contexto)

Tudo o que o Claude consegue "ter na cabeça" de uma vez: a conversa inteira, os arquivos anexados e as instruções. Os modelos atuais aguentam até 1 milhão de tokens. A régua embaixo da caixa de texto mostra quanto já foi usado. Conversa muito longa fica mais cara, porque cada resposta relê tudo.

## Raciocínio (pensamento)

Antes de responder, o Claude pode "pensar" por um tempo: planejar, conferir contas, comparar caminhos. Isso melhora respostas difíceis, mas gasta mais tokens. No Clave dá para ver um resumo desse raciocínio.

## Esforço

O quanto o Claude pensa antes de responder: Baixo, Médio, Alto, Muito alto ou Máximo. Esforço alto é melhor para problemas difíceis e código; esforço baixo é mais rápido e barato para coisas simples.

## Conselheiro de modelo

O aviso que sugere o modelo certo para a tarefa. O Haiku lê a conversa na primeira mensagem e depois a cada 5 e diz qual modelo faz aquilo pelo menor preço, com um botão para usar o sugerido e outro para manter o atual. Cada avaliação custa uma fração de centavo. Liga e desliga em **Configurações > Modelos**, onde também dá para deixar o Clave trocar sozinho.

## Alucinação

Quando a IA inventa uma informação com toda a confiança, como um livro que não existe ou um número errado. Acontece menos nos modelos novos, mas acontece. Para coisas importantes, peça a fonte e confira.

## API

Sigla de "interface de programação de aplicações". É uma porta que um programa abre para outros programas conversarem com ele. A API da Anthropic é a porta pela qual o Clave manda suas mensagens ao Claude e recebe as respostas. Pense num balcão de pedidos: o Clave entrega o pedido no balcão (a API) e recebe a resposta pronta.

## Chave da API

Uma senha comprida (começa com `sk-ant-`) que diz à Anthropic de qual conta sai o pagamento. Quem tem a sua chave gasta o seu dinheiro, então nunca mostre para ninguém e nunca cole em sites. No Clave ela fica guardada só no seu computador, criptografada.

## Crédito (cobrança por uso)

A API não tem mensalidade: você coloca crédito (dinheiro) na sua conta da Anthropic e cada resposta desconta um pouco, pelo número de tokens. Quem assina o plano Max do Claude ganha um crédito mensal na API.

## Teto de gasto

O limite em dólares que você põe em **Configurações > Limite de gasto**. Quando a soma do mês chega no teto, o Clave para de responder até o mês virar (ou só avisa, se você preferir). Existe também o teto por tarefa do modo Code, que pausa uma tarefa longa quando ela gasta demais. Mais em [Acompanhar e travar o gasto](#/aprender/acompanhar-o-gasto).

## Cache

Uma memória rápida que reaproveita o começo de uma conversa entre uma mensagem e outra. A parte reaproveitada custa de 10 a 40 vezes menos, conforme o modelo. Ela dura 5 minutos depois do último uso: se você demorar mais que isso para mandar a próxima mensagem, o começo volta a ser cobrado pelo preço cheio. O Clave liga isso sozinho.

## Compactação (/compact) {#compactacao}

Trocar o começo de uma conversa longa por um resumo, para cada resposta nova reler menos e custar menos. Acontece sozinha quando a conversa fica muito grande (**Configurações > Recursos > Resumir conversas muito longas**) ou na hora, quando você digita `/compact`. Fazer o resumo também custa um pouco, mas as mensagens seguintes ficam mais baratas. Mais em [Conversas enxutas](#/aprender/conversas-enxutas).

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

## Subagente

Um agente que o Claude chama para fazer uma parte da tarefa, com instruções, modelo e ferramentas próprios. No Clave, os agentes ficam em **Fluxos e agentes** e fazem as etapas dos fluxos (ex.: o "planejador" no Opus, o "executor" no Sonnet).

## Fluxo (workflow)

Uma tarefa dividida em etapas, cada uma feita por um modelo ou agente diferente: por exemplo, o Opus planeja, o Sonnet faz e testa, o Haiku confere. Como gasta mais que uma resposta comum, o Clave sempre mostra as etapas e a estimativa de custo e só roda depois do seu OK.

## Plugin

Um pacote que junta skills, agentes, comandos e fluxos para um tipo de trabalho (escritório, escrita, programação...). O Clave vem com alguns e instala outros do GitHub, no mesmo formato dos plugins do Claude Code. Dá para ligar e desligar cada um.

## Marketplace

Uma lista de plugins publicada num repositório do GitHub (arquivo `marketplace.json`). Instalando de um marketplace, você escolhe quais plugins da lista quer.

## Comando de barra

Um atalho que começa com `/` na caixa de mensagem, como `/novo`, `/modelo haiku` ou `/escrita:email`. Alguns são do próprio Clave, outros são pedidos prontos salvos em arquivo (`.claude/commands`) ou skills.

## Regra de permissão

Uma linha que diz o que o Claude pode fazer sozinho, o que sempre pergunta e o que nunca faz, como `Bash(npm test *)` ou `Edit(docs/**)`. Vale numa pasta ou no Clave inteiro, e tem prioridade sobre o modo de permissão.

## Arquivo protegido

Um arquivo ou pasta da lista **Arquivos e pastas protegidos** (Configurações > Modo Code), como `.env` e `*.key`. As ferramentas de arquivo do Claude nunca leem nem mudam o que está ali, e um comando que cite um deles sempre pede o seu OK. Ponha ali o que tiver senha ou dado sensível.

## Rotina

Um pedido salvo que o Claude faz sozinho num horário (todo dia, em alguns dias da semana ou a cada poucas horas). Numa rotina ele não pergunta nada: só faz o que suas regras de permissão já liberam.

## Agendador de Tarefas

Um programa do próprio Windows que roda coisas num horário, mesmo sem nenhum app aberto. O Clave usa ele quando você pede que uma rotina rode com o Clave fechado.

## Markdown

Um jeito simples de formatar texto com símbolos: `**negrito**`, `# Título`, `- item de lista`. O Claude escreve em Markdown e o Clave transforma em texto formatado. Arquivos `.md` são textos em Markdown.

## Widget

Um cartão que o Claude desenha na conversa quando ele ajuda mais que texto: produtos e preços, mapa, recomendações, desenho ou planta, gráfico, comparação, linha do tempo e lista de tarefas. Vêm ligados; o interruptor fica em **Configurações > Recursos > Widgets**. Fotos de outros sites só carregam quando você clica. Veja [Widgets](#/aprender/widgets).

## OpenStreetMap

Um mapa do mundo gratuito, feito por voluntários, como uma Wikipédia de mapas. Os mapas dos widgets do Clave vêm dele, pela internet, e os endereços viram pontos no mapa pela busca de endereços dele (o Nominatim).

## Arquivo e pasta

Arquivo é um documento (foto, planilha, texto). Pasta é uma "gaveta" que guarda arquivos e outras pastas. No Windows você vê os dois no Explorador de Arquivos.

## Lixeira

O lugar do Windows para onde vai o arquivo apagado pelo Explorador de Arquivos ou pela aba **Arquivos** do modo Code. De lá dá para trazer de volta (botão direito > **Restaurar**). Arquivo apagado por um comando não passa pela Lixeira: some de vez. Veja [Desfazer, backup e Git](#/aprender/rede-de-seguranca).

## Caminho (de arquivo)

O "endereço" de um arquivo no computador, como `C:\Users\Ana\Documents\orcamento.xlsx`. Cada parte separada por `\` é uma pasta dentro da outra.

## Extensão de arquivo

As letras depois do ponto no nome do arquivo, que dizem o tipo dele: `.xlsx` (planilha do Excel), `.pdf`, `.jpg` (foto), `.txt` (texto), `.py` (programa em Python).

## Terminal

Uma janela onde você dá ordens ao computador digitando, em vez de clicar. Parece coisa de hacker, mas é só outro jeito de mandar o computador fazer as coisas.

## Console (terminal) {#console}

A aba **Console** do painel do modo Code: um terminal do Windows (o PowerShell) de verdade dentro do Clave, já aberto na pasta de trabalho, onde você mesmo digita comandos. Abre com **Ctrl+`** (no teclado brasileiro, a tecla à esquerda do 1). O botão **Mandar para o Claude** leva o texto selecionado, ou as últimas linhas, para a caixa de mensagem. Veja [O console](#/aprender/console).

## PowerShell

O terminal do Windows. No modo Code, quando o Claude "roda um comando", ele usa o PowerShell.

## Comando

Uma ordem digitada no terminal. Por exemplo, `mkdir Fotos` cria uma pasta chamada Fotos.

## Segundo plano

Quando um programa continua rodando sem prender a conversa. No modo Code, o Claude deixa em segundo plano o que precisa ficar ligado, como um [servidor local](#/aprender/glossario/servidor-local): a resposta termina e o comando segue rodando. Você acompanha e para na aba **Tarefas** (Ctrl+Shift+Y), e um contador na barra da esquerda mostra quantos estão rodando. São no máximo 5 por conversa, e todos param quando o Clave fecha.

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

## Flashcard

Um cartão de estudo com uma pergunta de um lado e a resposta do outro, para treinar a memória. O Claude cria flashcards numa planilha (que dá para levar para apps como o Anki) ou numa pequena página que vira o cartão quando você clica.

## Git

Um programa que guarda o histórico de um projeto: cada vez que você salva uma versão (um "commit"), dá para voltar nela depois. É como o "histórico de versões" do Google Docs, mas para pastas inteiras.

## Repositório

Uma pasta de projeto controlada pelo Git, com todo o histórico de versões. Pode ficar só no seu computador ou também no GitHub.

## Commit

Uma "foto" do projeto num momento, com uma mensagem dizendo o que mudou. "Commitar" é salvar essa versão no histórico do Git.

## .gitignore

Um arquivo de texto na pasta com a lista do que o Git deve ignorar, como `.env`, `*.key` e pastas de arquivos temporários. O que está nele não entra nas versões e não vai para o GitHub: é o jeito de deixar senhas e chaves de fora. Veja [Git e GitHub](#/aprender/github).

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

## Servidor local

Um servidor que roda no seu próprio computador, só para você testar. Quando o Claude cria um site no modo Code, ele costuma ligar um com um comando como `npm run dev` ou `python -m http.server`, que mostra um endereço como `http://localhost:8000`. Você abre esse endereço no **Navegador** do painel (o botão **Locais** lista os servidores ligados neste computador). O que o Claude ligou fica na aba **Tarefas** e para quando o Clave fecha. Veja [Tarefas em segundo plano e servidores locais](#/aprender/tarefas-em-segundo-plano).

## Localhost e porta {#localhost}

**Localhost** é o "endereço" do seu próprio computador (`127.0.0.1`): o que roda em localhost só o seu computador acessa. A **porta** é o número depois dos dois-pontos, que separa um programa do outro: em `http://localhost:5173`, o site que você está testando está na porta 5173.

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

## Senha de app

Uma senha extra que você cria na sua conta (do Gmail, por exemplo) só para um programa entrar nela, como o conector de e-mail do Clave ou um script. Ela não muda a sua senha normal e dá para apagar a qualquer hora, sem afetar o resto. No Google, ela só aparece com a verificação em duas etapas ligada.

## Gerenciador de Credenciais

O cofre de senhas que já vem no Windows (menu Iniciar > **Gerenciador de Credenciais** > **Credenciais do Windows**). Um programa que o Claude cria para você pode guardar a senha ali, em vez de escrever no código ou pedir na conversa. Veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados).

## Código aberto (open source)

Programa cujo código qualquer pessoa pode ler, e muitas vezes usar e modificar, seguindo uma licença.

## Versão

O número que diz qual "edição" de um programa você tem, como 1.4.2. Número maior quer dizer mais novo. O botão Atualizar do Clave baixa a versão mais nova.

## Diff

A comparação entre o antes e o depois de um arquivo: linhas tiradas aparecem em vermelho (com `-`) e linhas novas em verde (com `+`). O modo Code mostra o diff de cada mudança.

## Variável de ambiente

Uma configuração que o computador guarda "por fora" dos programas e que eles podem ler. Às vezes guarda chaves de API; o Clave não usa isso de propósito, para a chave ficar mais protegida.

## Prompt injection

Um truque em que um texto (de um site, e-mail ou arquivo) traz instruções escondidas para a IA, tentando fazê-la obedecer outra pessoa. Por isso o Clave pede o seu OK antes de ações importantes: confira sempre o que está aprovando. Veja [Quando uma página ou arquivo tenta dar ordens ao Claude](#/aprender/injecao-de-instrucoes).

## Vazamento de dados (exfiltração) {#vazamento-de-dados}

Quando uma informação sua sai para quem não devia ter: uma senha colada num site, uma chave enviada para o GitHub, dados de clientes num e-mail errado. "Exfiltração" é quando alguém faz isso de propósito, por exemplo com uma ordem escondida numa página que tenta fazer a IA mandar dados da conversa para fora (até dentro do endereço de uma foto). Por isso as fotos dos widgets esperam o seu clique.

## Dado pessoal

Qualquer informação que identifica uma pessoa: nome, CPF, RG, telefone, endereço, e-mail, dados de saúde, número de conta. Antes de mandar uma planilha ou um documento, tire ou troque o que o Claude não precisa (por exemplo, "Cliente 1" no lugar do nome). Veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados).
