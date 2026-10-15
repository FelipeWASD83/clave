# Novidades do Clave

[English](CHANGELOG.md) · **Português**

## 4.1.0 (15/10/2026)

**Novo**

- **Jeito de falar** (Configurações > Personalização), como o controle de tom do ChatGPT: estilo e tom básicos
  (Amigável, Sincero, Divertido, Nerd ou Cético), cordialidade, entusiasmo, emoji, títulos e listas, negrito e
  tabelas, linguagem simples ou técnica, se o Claude pergunta antes ou supõe quando falta informação e se ele termina
  com um "quer que eu...?". Tudo em Padrão não muda nada. Vale para as conversas novas, no chat e no Code.
- **Ver um exemplo**: o Haiku responde uma pergunta com o tom escolhido, para você sentir a diferença antes de usar
  (custa uma fração de centavo).

**Corrigido**

- O ícone no fim de Preços e planos aparecia gigante; voltou ao tamanho da letra.

## 4.0.0 (15/10/2026)

O Clave para o escritório: e-mail, Word, Zapier, trazer tudo do Claude ou do ChatGPT, e um Claude que economiza o
seu dinheiro.

**Novo**

- **Conector de e-mail** (Configurações > Conectores): Gmail, Yahoo, Zoho e provedores de hospedagem com senha de
  app, ou o Outlook clássico instalado no computador (para Outlook.com e Microsoft 365). O Claude lê e procura os
  seus e-mails e escreve respostas; enviar sempre mostra o e-mail inteiro e espera o seu OK. No modo Code ele também
  salva anexos na pasta.
- **Word**: no modo Code o Claude cria documentos (propostas, contratos, cartas) com títulos e tabelas, preenche
  modelos e exporta para PDF pelo Word instalado.
- **Atalho do Zapier**: um jeito guiado de ligar Gmail, Planilhas e Agenda do Google, Outlook, WhatsApp Business e
  centenas de apps.
- **Importar do Claude ou do ChatGPT** (Configurações > Importar do Claude): você copia um pedido, cola no outro
  assistente e cola a resposta de volta. Vêm as suas regras, quem você é, projetos, preferências e automações, com
  uma prévia para desmarcar o que não quiser. As rotinas chegam desligadas e no Haiku, para você conferir.
- **Arquivos na conversa**: quando o Claude tira um print, faz um gráfico ou acha um arquivo que você precisa ver,
  ele mostra ali mesmo (imagem, vídeo e áudio tocam na conversa; o resto vira um cartão para abrir ou baixar).
- **/compact** resume a conversa na hora para as próximas mensagens gastarem menos, e o resumo aparece na conversa.
- Mais comandos: **/web on|off**, **/resumo**, **/exportar**, **/economia** (dicas para gastar menos) e **/importar**.
- **Plugin de vendas**: proposta comercial, follow-up de cliente, pedidos para planilha, relatório de vendas,
  responder cliente e "automação sem IA".
- Lição nova: **Um app de pedidos sem IA**, passo a passo: e-mail, planilha do Excel e envio dos pedidos para o
  site da empresa, agendado pelo Windows, com custo zero por rodada.

**Mudou**

- **O Claude economiza o seu crédito sozinho**: responde no tamanho que a pergunta pede, não relê o que já leu e,
  antes de transformar algo repetitivo em rotina, explica que um programa sem IA, feito uma vez no Code, custa zero
  por rodada. Também sugere o Haiku para o simples, o /compact para conversa longa e ferramentas gratuitas como Git,
  GitHub, Obsidian e Power Automate quando servirem.
- A página de Rotinas pergunta "precisa de IA toda vez?" e abre o Code pronto para montar o programa sem IA.
- Comandos e skills de plugin, escritos em inglês, agora dizem ao Claude em que idioma responder.
- O `excel_alterar` pode salvar numa cópia (o campo `saida`), como a skill de Excel já pedia.

**Corrigido**

- A lista de passos do Code não fica mais parecendo que ainda está trabalhando depois que a resposta acaba: o passo
  para de girar e a lista diz quais passos ficaram abertos.

## 3.1.0 (15/10/2026)

**Mudou**

- **A busca na web vem ligada**: o Claude pesquisa na internet sozinho quando a resposta precisa de algo atual
  (notícia, preço, versão) e mostra as fontes. Não precisa ligar nada. O botão **Web** da caixa de texto agora
  desliga só naquela conversa, e Configurações > Recursos desliga em todas. Cada busca custa US$ 0,01 além dos
  tokens. Para quem já usava o Clave, ela é ligada uma vez, inclusive nas conversas antigas.

## 3.0.0 (15/10/2026)

O Clave agora fala inglês, mostra onde fica cada coisa na primeira vez e apresenta cada modelo novo do Claude.

**Novo**

- **Inglês**, ao lado do português do Brasil: a interface inteira, as lições e o glossário, o modelo de pasta, os
  plugins, agentes e fluxos que vêm com o app e o que o Clave diz ao Claude. Instalação nova segue o idioma do
  Windows (inglês quando não é português); quem já usava continua em português. Para trocar: Configurações >
  Aparência > Idioma.
- **Tours com setinhas**: na primeira vez que você abre o Clave, setas apontam cada parte da tela e explicam
  para que serve (16 passos curtos, dá para pular). O Code, Preços e planos e Fluxos têm o tour deles na
  primeira visita. "Refazer os tours" fica em Aprender.
- **Cartão de modelo novo**: quando a Anthropic lança um modelo, um cartão abre uma vez com a imagem dele, o que
  ele é, o que mudou da versão anterior, o preço ao lado dos outros modelos e a nota de inteligência de todos na
  mesma régua (o índice da Artificial Analysis, com a fonte). Um banner fica no início por 14 dias, e o mesmo
  cartão abre pela fileira "Modelos" de Preços e planos.
- Fileira **Modelos** em Preços e planos, com um cartão e uma ilustração para cada modelo.
- O Clave avisa quando a sua conta da Anthropic já tem um modelo que ele ainda não conhece (confere uma vez por
  dia, de graça) e oferece procurar atualização.

**Mudou**

- O repositório está em inglês, com cópias em português do README, deste changelog e das notas do projeto.
- Propostas de fluxo, planos e cartões de sugestão saem no idioma que você usa.

**Corrigido**

- Na tela de nova conversa, quando o banner e os painéis deixavam a página mais alta que a janela, a caixa de
  texto ficava acima do topo, onde a rolagem não chegava.
- Ao sugerir outra conversa, o Claude às vezes repetia a resposta inteira depois do cartão.

## 2.1.0 (14/10/2026)

**Novo**

- Página **Preços e planos**: o preço de cada modelo (e quanto sai uma mensagem curta, média ou longa), os
  planos do Claude e a conta "API ou assinatura?". Você diz como usa o Claude normal (quantas janelas de 5
  horas por semana e quanto do limite gasta, ou quantas mensagens por dia) e ela estima o custo na API de cada
  modelo, comparado com o preço do plano. Quando você já tem respostas no Clave, aparece também a conta pelo
  seu custo real.
- Painel **Seu uso** na tela de conversa nova (chat e Code): tokens no total, dias seguidos de uso (e o
  recorde), mapa de calor das últimas 20 semanas, modelo favorito, cada modelo nos últimos 7 dias e a
  projeção do mês: no ritmo dos últimos 14 dias, quanto o ciclo fecha e em que dia o teto acaba. Dá para
  esconder em Configurações > Aparência.
- Painel **Ambiente** no Code, como no app oficial: as pastas recentes com a atual marcada, "Escolher
  ambiente" e "Ativar modo automático" (o modo Livre). O Code já começa na última pasta usada.
- **Sugestão de outra conversa**: quando aparece um trabalho separado, o Claude pode sugerir abrir outra
  conversa. Vira um cartão com o título e o pedido; "Abrir em outra conversa" cria a conversa e o Claude já
  começa a trabalhar nela, enquanto você continua na atual. Nada abre sem o seu clique.

**Mudou**

- O Code não tem mais a tela separada "Em qual pasta": a escolha fica no painel de ambientes.

## 2.0.1 (14/10/2026)

**Corrigido**

- Se o Windows não deixar trocar uma pasta durante a atualização (por exemplo, a pasta do Clave aberta
  num terminal ou presa pelo antivírus), a volta para a versão anterior não deixa mais o app sem abrir.

## 2.0.0 (14/10/2026)

Fluxos com vários modelos, permissões por regras, plugins, comandos de barra,
rotinas e um modo Plano de verdade.

**Novo**

- Fluxos: uma tarefa grande vira etapas, cada uma no modelo e no agente certo
  (por exemplo, o Opus 5.5 planeja, o Sonnet 5.5 faz e testa, o Haiku 5.5
  confere). Antes de rodar, sempre aparece um cartão com as etapas, a
  estimativa de custo e um teto, e dá para trocar modelo e raciocínio de cada
  etapa ou tirar etapas. Etapas podem rodar em paralelo, e dá para abrir cada
  uma e ver o que ela está fazendo. Cinco fluxos prontos (Planejar, fazer e
  testar; Pesquisa profunda; Revisão em paralelo; Planilha grande; Escrever e
  revisar), com histórico de tudo o que rodou.
- Agentes: seis prontos (planejador, executor, testador, revisor, pesquisador
  e redator) e um editor para criar os seus, no mesmo formato do Claude Code
  (`.claude/agents`).
- Permissões por regras, no formato do Claude Code: Nunca, Sempre perguntar e
  Fazer sem perguntar, para comandos, arquivos, sites, conectores, GitHub e
  fluxos. Valem no Clave inteiro ou numa pasta (`.claude/settings.local.json`).
  O cartão de aprovação ganhou "Mais opções" para liberar pelo resto da tarefa
  ou salvar a regra sugerida. Página de permissões com teste ("esse comando
  passaria?") e histórico de cada decisão.
- Plugins no formato do Claude Code, com skills, agentes, comandos e fluxos.
  Sete prontos (Escritório, Automação no Windows, Pesquisa, Escrita, Sites e
  apps, Programação e Crie o seu) com 25 skills novas. Instalação de uma pasta
  ou do GitHub (plugin único ou marketplace), sempre mostrando o conteúdo
  antes.
- Comandos de barra: `/novo`, `/modelo`, `/esforco`, `/plano`, `/custo`,
  `/fluxo`, `/memoria`, `/permissoes`, `/plugins`, `/ajuda`, os comandos dos
  plugins e os seus (`.claude/commands`), e as skills chamadas pelo nome.
- Modo Plano com cartão de plano: você aprova e escolhe como ele executa
  (perguntando, aceitando edições ou livre) ou pede para continuar planejando.
- Rotinas: pedidos que o Claude faz sozinho todo dia, em alguns dias da semana
  ou a cada poucas horas, com teto por rodada. Rodam com o Clave aberto ou,
  se você quiser, pelo Agendador de Tarefas do Windows com ele fechado. Numa
  rotina o Claude não pergunta nada: o que precisaria de OK faz a rotina parar
  e contar a regra que faltou.
- Skills também no chat (as que não são manuais).
- Cinco lições novas (por que usar o Clave, fluxos e agentes, permissões,
  rotinas, plugins e comandos) e oito termos novos no glossário.
- No README, a seção "Por que você deveria usar o Clave".

**Mudou**

- Os avisos do Windows saem pela janela do Clave, piscam na barra de tarefas
  e avisam também quando o Claude espera um OK, propõe um fluxo, termina um
  plano ou quando um fluxo ou rotina termina.
- O botão Atualizar também atualiza os plugins, agentes e fluxos que vêm com
  o app.

**Corrigido**

- Menus compridos (como o de comandos) não saem mais da tela: abrem para baixo
  quando não cabem para cima e rolam.

## 1.0.0 (14/10/2026)

Primeira versão.

**Novo**

- Chat com o Claude pela API da Anthropic, com a sua chave: conversas, busca,
  fixar, renomear, exportar em Markdown, editar mensagem e gerar outra resposta
  com versões (setas < >).
- Anexos: imagens, PDFs, planilhas do Excel e arquivos de texto e código;
  arrastar, colar ou escolher, e também do GitHub.
- Modelos Opus 5.5, Sonnet 5.5, Haiku 5.5 e Fable 5.1 (e os antigos, se quiser),
  raciocínio de Baixo a Máximo, raciocínio visível, modo rápido e troca de
  modelo quando o filtro de segurança recusa por engano.
- Modo Code: o Claude trabalha numa pasta do computador com permissões
  (Perguntar, Aceitar edições, Plano, Livre), cartões de aprovação com o antes e
  depois, lista de passos, desfazer, arquivos protegidos, teto por tarefa,
  regras CLAUDE.md da pasta e skills (chamadas com /nome).
- Excel: ler, criar e alterar planilhas com fórmulas, formatação, tabelas,
  gráficos, filtros, formatação condicional e listas de opção; recalcular,
  exportar PDF e converter .xls pelo Excel do computador. No chat, a planilha
  pronta vem com botões de baixar e abrir.
- Projetos com instruções e arquivos de conhecimento.
- Personalização: sobre você, como responder, estilos prontos e próprios.
- Memória entre conversas em arquivos por assunto, com índice, e um editor de
  memória (Sonnet 5.5) que muda as memórias do jeito que você pedir.
- Teto de gasto mensal com alertas, custo de cada resposta, página de uso por
  dia, modelo e conversa, e régua de contexto.
- GitHub (pelo login do gh ou token), busca na web e conectores MCP.
- Aprender: 19 lições e um glossário de mais de 60 termos para quem nunca usou
  IA, com foco em automação e personalização, e um ajudante (Haiku 5.5) que
  tira dúvidas de cada lição. O Claude indica a lição certa quando você
  tropeça num termo, mesmo escrito errado.
- Modelo de pasta de trabalho com regras, skills (ver vídeos, revisar código,
  visual de sites e outras) e biblioteca de referências visuais.
- Janela própria (Electron), instalador com atalhos e botão Atualizar que baixa
  a versão nova do GitHub e volta atrás se ela não abrir.
- Tema claro, escuro ou do sistema, tamanho e tipo de letra, largura da
  conversa e avisos do Windows quando o Claude termina.
