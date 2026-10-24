# Novidades do Clave

[English](CHANGELOG.md) · **Português**

## 5.2.2 (23/10/2026)

**Corrigido**

- **A conversa não trava mais quando tem muitas imagens grandes.** A API só aceita imagem de até 2000 px de lado
  quando o pedido tem mais de 20 imagens (prints e quadros que o Claude leu antes contam), e senão recusa o pedido
  inteiro, em toda mensagem seguinte. Agora a leitura de arquivo do Claude reduz antes qualquer imagem acima de
  2000 px, e quando a conversa passa de 20 imagens, as antigas acima desse tamanho viram um aviso curto de texto em vez
  de quebrar tudo. Conversas que já estavam travadas voltam a funcionar.

## 5.2.1 (23/10/2026)

**Corrigido**

- **A conversa não trava mais por causa de uma imagem salva com a extensão errada.** Quando o Claude lia um JPEG
  chamado `.png` (ou o contrário), o Clave dizia o tipo errado para a API, que recusava o pedido inteiro, e como a
  imagem ficava no histórico o erro voltava a cada mensagem. Agora o tipo é lido da própria imagem, tanto na leitura do
  arquivo quanto no envio do histórico, então conversas que já estavam travadas voltam a funcionar. Arquivo que só
  parece imagem (um SVG chamado `.png`, por exemplo) é recusado com uma mensagem clara em vez de quebrar a conversa.

## 5.2.0 (23/10/2026)

**Mudou**

- **O modo Livre não pergunta mais nada além de apagar.** Antes ele ainda perguntava sobre publicar (`git push`,
  deploy, release), mandar e-mail, mexer em arquivo fora da pasta, escrever no GitHub e o cartão do fluxo. Agora tudo
  isso acontece sozinho no modo Livre, e o fluxo roda com o teto de gasto sugerido. O que ainda pergunta: comando que
  apaga arquivos ou dados, comando que cita arquivo protegido e as regras `Sempre perguntar` que você mesmo
  escreveu. As regras `Nunca` e a lista de arquivos protegidos continuam valendo. Os outros modos não mudaram, e
  rotina continua nunca rodando no modo Livre. O tour, os textos das configurações e as lições dizem o mesmo agora.

## 5.1.0 (23/10/2026)

**Novo**

- **Você escolhe quantas ações seguidas o Claude faz no modo Code.** Cada ação (ler um arquivo, editar, rodar um
  comando) é uma ida e volta com a API, e depois de 60 seguidas num mesmo envio ele pausava e pedia "continue". Agora
  o número fica em Configurações > Limite de gasto, de 10 a 1000 (o padrão continua 60). O aviso de pausa diz quantas
  foram e onde aumentar.

## 5.0.1 (23/10/2026)

**Corrigido**

- **Tarefa longa no modo Code não para mais "do nada".** Quando uma resposta parava antes do fim (o teto por tarefa,
  muitas voltas seguidas, resposta longa demais, a conversa cheia ou um erro no meio do trabalho), o aviso aparecia
  por um instante e sumia assim que a resposta acabava, e o Windows ainda avisava que o Claude tinha terminado. Agora
  o motivo fica escrito no fim da resposta, com um botão **Continuar**, e o aviso do Windows diz por que parou.

## 5.0.0 (15/10/2026)

O modo Code vira uma bancada: os seus arquivos, um console de verdade, um navegador que você divide com o Claude e o
que roda em segundo plano, tudo ao lado da conversa. E no chat e no Code o Claude pode desenhar a resposta num cartão.

**Novo**

- **Painel lateral no modo Code**, ao lado da conversa e da largura que você arrastar, com as abas **Arquivos**,
  **Visualizador**, **Console**, **Navegador** e **Tarefas**. Ctrl+J abre e fecha; Ctrl+Shift+E vai para Arquivos,
  Ctrl+` para o Console, Ctrl+Shift+L para o Navegador e Ctrl+Shift+Y para Tarefas. A aba continua trabalhando com o
  painel fechado (o console guarda o que rodou), e o modo Code reabre o painel do jeito que você deixou. Um tour
  mostra o painel na primeira vez.
- **Arquivos**: a pasta de trabalho em árvore, com filtro e busca em todas as pastas. O botão direito abre no
  Visualizador, mostra no Explorador, copia o caminho, menciona na conversa, renomeia (F2), cria arquivo ou pasta e
  manda para a Lixeira (Delete). Arrastar um arquivo para a caixa de mensagem menciona ele. Os arquivos que o Claude
  mudou nesta conversa ganham uma marca, e a árvore se atualiza sozinha. Abrir programa ou script com o programa
  padrão pergunta antes.
- **Visualizador**: código com cores e números de linha (Ctrl+F, ir para uma linha), Markdown com as imagens dele,
  imagens, PDF, planilhas do Excel e CSV (fórmula aparece como fórmula), Word (o texto), JSON organizado, áudio e
  vídeo, e **Ver como página** para HTML. **Mudanças do Claude** mostra o que o Claude mudou no arquivo nesta conversa.
  Arquivos protegidos (como o `.env`) só abrem depois de **Mostrar mesmo assim**. Nas respostas do Claude, o caminho
  de cada passo com arquivo (ler, escrever, editar, Word, Excel) abre o arquivo aqui com um clique.
- **Console**: um PowerShell de verdade dentro do Clave, já na pasta de trabalho, com cores, histórico e programas
  interativos, até 6 de uma vez. **Mandar para o Claude** põe o texto selecionado (ou as últimas linhas) na caixa de
  mensagem. No modo Code, os blocos de código de PowerShell e cmd nas respostas ganham **Rodar no console**: o comando
  é escrito no console, e você confere e aperta Enter.
- **Navegador**: um navegador dentro da janela do Clave que você e o Claude usam juntos. O Claude abre páginas, lê,
  tira print, rola e volta, para conferir o que construiu ou usar uma página, e uma faixa mostra quando ele está
  usando o navegador. **Locais** lista os servidores rodando neste computador (npm run dev, python -m
  http.server...) para abrir com um clique.
- **As travas do navegador**: os cookies e logins dele ficam separados do resto do Clave. Fora do modo Livre, o
  Claude pergunta uma vez por tarefa antes de usar cada site novo (localhost, o seu próprio computador, não pergunta),
  e cada clique e cada digitação pedem o seu OK, a não ser que uma regra diga aquela ação
  (`Navegador(clicar:localhost)`); o modo Plano só lê. O Claude nunca digita senha, código de acesso nem número de
  cartão: quem digita é você. O que a página diz é tratado como dado, nunca como ordem. Um bloqueio
  `WebFetch(domain:...)` também bloqueia o navegador naquele site, e uma página que pula para um site bloqueado fica
  em branco. O Clave nunca entrega a um site um certificado do Windows (como um e-CPF). **Sair da conta** apaga os
  dados do navegador, e Configurações > Modo Code tem **Apagar os dados do navegador**. As regras novas são
  `Navegador(site)` e `Navegador(ação:site)`, com porta se você quiser (`Navegador(localhost:5173)`), e as ações podem
  ser escritas em português ou em inglês.
- **Comandos em segundo plano**: o Claude pode deixar um servidor local ou um observador de arquivos rodando (npm run
  dev, python -m http.server) e seguir trabalhando: ele lê a saída quando precisa e para quando termina, no máximo 5
  por conversa. Eles aparecem em Tarefas com o endereço local, que abre no navegador com um clique, e param quando
  você aperta Parar, quando apaga a conversa e quando o Clave fecha. Um programa com janela que eles abriram (o
  navegador de um servidor de desenvolvimento, um editor) continua aberto, e o mesmo vale para programas abertos pelo
  console.
- **Tarefas** (Ctrl+Shift+Y), no chat e no Code: tudo o que roda em segundo plano (respostas ainda chegando, fluxos
  com as etapas, rotinas, comandos em segundo plano e downloads dos vídeos das lições), com o tempo, o registro,
  **Parar** e **Ir para a conversa**. As terminadas ficam 30 minutos. A barra da esquerda mostra "N rodando", e uma
  tarefa longa que termina mostra um aviso (e uma notificação do Windows quando o Clave está em segundo plano).
- **Widgets**, no chat e no Code: quando um cartão ajuda mais que texto, o Claude desenha ele na conversa. Oito
  tipos: produtos e preços (em ordem de preço, com o mais barato marcado e a data em que foram vistos), mapa com
  pontos e rota, recomendações (séries, filmes, jogos, livros, música...), desenhos e plantas com medidas, gráficos
  (barras, linhas, pizza, área), comparações, linhas do tempo e listas para marcar. Cada um tem tela cheia e **Copiar
  como texto**, e desenhos e gráficos baixam em PNG ou SVG. Eles voltam quando você reabre a conversa e vão junto na
  exportação em Markdown. Configurações > Recursos desliga.
- **Fotos só com clique**: fotos de produto e capas vêm de outros sites, então só carregam quando você clica em
  **Mostrar imagens** (o botão diz de quais sites), porque uma página poderia usar o endereço de uma foto para levar
  dados da conversa para fora. Configurações > Recursos muda isso. As imagens passam pelo Clave: só endereço https
  público, até 5 MB, nunca SVG. **Mapas** carregam na hora: vêm do OpenStreetMap pelo próprio Clave, seguindo as
  regras de uso dele (cada pedaço de mapa fica guardado pelo menos 7 dias, e endereço é procurado no máximo uma vez
  por segundo), e o Clave diz onde cada endereço caiu e quais ficaram de fora.
- **23 lições novas**, em cinco trilhas novas: **Economizar crédito** (para onde vai o seu crédito, o modelo certo
  pelo menor preço, raciocínio, conversas enxutas, o modo Code sem desperdício, automatizar sem pagar a IA toda vez,
  acompanhar e travar o gasto), **A mesa do Code** (o painel, o console, o navegador, tarefas em segundo plano e
  servidores locais, um site do zero até o navegador), **Respostas visuais** (widgets, comparar produtos e preços,
  mapas e roteiros, plantas, desenhos e gráficos), **Usar com segurança** (quando uma página ou arquivo tenta dar
  ordens ao Claude, o que nunca colar, desfazer, backup e Git) e **Receitas por área** (estudar, escritório, pequeno
  negócio, casa). O glossário ganhou as palavras novas (widget, console, segundo plano, servidor local, Lixeira...).

**Mudou**

- **O Haiku 5.5 é o padrão para todo mundo**, inclusive para quem já usava: as conversas novas começam no modelo
  mais barato. Uma vez, depois de atualizar, o Clave mostra o modelo que você usava antes, com **Manter o Haiku** e
  **Voltar para o de antes**. As conversas que já existem continuam no modelo delas, e o conselheiro de modelo
  continua sugerindo um mais forte quando a tarefa pede. Rotinas novas também começam no Haiku.
- **Os vídeos das lições baixam sozinhos**, em segundo plano e só no idioma do app (uns 28 MB), então a lição já
  abre com o vídeo pronto e toca do seu computador. Eles continuam fora do download do Clave. O download aparece em
  Tarefas e dá para parar por lá; Configurações > Atualizações e sobre desliga (aí a lição baixa o vídeo quando você
  dá play).
- **A prévia de HTML e SVG** agora é a aba **Prévia** do painel lateral.
- **Apagar uma conversa** para o que roda por ela (a resposta ainda chegando, os fluxos e os comandos em segundo
  plano dela) em vez de pedir que você pare a resposta antes.
- **Fechar o Clave** primeiro pede ao servidor que termine sozinho (por até 3 segundos), então programas com janela
  que o console ou um comando em segundo plano abriram continuam abertos.
- **Interface mais suave**: janelas, menus e avisos saem com uma animação curta em vez de sumir, os botões cedem ao
  clique, a barra da esquerda desliza ao abrir e fechar, rolagens longas deslizam e a barra do topo da conversa se
  ajeita numa janela estreita em vez de transbordar. Com as animações do Windows desligadas, tudo fica parado.
- **Em monitor bem largo** (ultrawide), o painel lateral começa mais largo (até 1200 px), os cartões dos widgets
  ganham espaço fora da coluna do texto, e Aprender, Projetos, Fluxos, Plugins e Rotinas mostram mais cartões por
  linha. Em 1440 px nada muda.
- **No cartão do site do navegador**, o **Permitir** já libera o site até o fim da tarefa, como a pergunta diz:
  ler a página logo depois de abrir não pergunta de novo.

**Corrigido**

- Um comando que deixava um processo escondido para trás, ainda segurando a saída (um servidor local aberto de dentro
  do comando), deixava ele rodando depois da resposta, sem nada que o parasse. Agora o Clave fecha esse processo,
  avisa no resultado e indica ao Claude a opção de segundo plano. Uma janela que o comando abriu (o Bloco de Notas, um
  editor) continua aberta.
- Um vídeo de lição cujo download caía no meio podia ficar guardado como se estivesse inteiro; agora é erro com
  **Tentar de novo**, e qualquer outra falha de rede mostra uma mensagem legível.
- Configurações > Dados e backup agora diz o que o backup leva de verdade: as rotinas vão junto; a memória, os anexos
  e a chave não.
- A skill "automação sem IA" do plugin de vendas contava uma rotina conferindo a cada 15 minutos, mas rotina roda no
  máximo uma vez por hora; a comparação agora usa isso.
- Reabrir uma conversa que ainda estava respondendo ou esperando o seu OK mostrava o texto da resposta duas vezes.
- Na primeira abertura, o tour e o cartão do modelo novo abriam um por cima do outro. Agora o tour vem primeiro e o
  cartão aparece quando ele fecha, e um tour nunca abre por cima de uma janela.
- Numa janela estreita, as páginas Aprender, a lição e Configurações não tinham botão para abrir a barra da esquerda,
  e uma faixa escura aparecia na borda esquerda da janela. O botão de enviar caía sozinho numa segunda linha.
- Configurações: as descrições de **Sair da conta** e **Desinstalar** eram cortadas com "...", os botões que levam a
  outra página apareciam sublinhados, **Abrir as regras de permissão** se esticava pela coluna inteira, a caixa de
  arquivos protegidos cortava a última linha ao meio e os campos de número ocupavam a largura toda.
- No tema escuro, o logo da barra da esquerda aparecia dentro de um quadrado mais claro, e o cartão de modelo novo
  tinha um bloco claro demais.

## 4.3.0 (15/10/2026)

**Novo**

- **O Haiku é o modelo padrão** nas instalações novas: o mais barato. Se você já usa o Clave, o seu modelo continua.
- **Conselheiro de modelo**: na primeira mensagem de cada conversa e depois a cada 5, o Haiku lê a conversa e diz
  qual modelo faz a tarefa pelo menor preço ("Para esta tarefa, o Sonnet 5.5 deve ir melhor", com Usar e Manter).
  Se você deixar (Configurações > Modelos), o Clave troca sozinho e mostra um botão para voltar; numa conversa em que
  você voltar, ele não troca mais. Cada avaliação custa uma fração de centavo, e dá para desligar.
- **Comandos em português e inglês**: todo comando, skill e fluxo que vem com o Clave funciona com os dois nomes
  (/resumo ou /summary, /vendas:proposta ou /sales:proposal, /fluxo pesquisa-profunda), e o menu, a ajuda e as
  páginas Plugins e Fluxos mostram o do seu idioma. Um comando ou skill seu com o mesmo nome de uma tradução
  continua sendo seu.
- **Sair da conta** (Configurações > Atualizações e sobre): apaga a chave da API e as senhas salvas, volta as
  configurações ao padrão, desliga as rotinas e mostra a apresentação e os tours de novo. Conversas, projetos,
  memória e plugins instalados ficam.
- **Desinstalar** (no mesmo lugar): fecha o Clave e tira a pasta dele, os atalhos e as tarefas das rotinas no
  Agendador, com um link para baixar o backup antes.
- **Vídeos nas lições**, em português e em inglês: por que usar o Clave, como pegar a chave da API, primeiros passos
  e a primeira automação no modo Code. Eles não vêm dentro do app: a lição baixa o vídeo do GitHub na primeira vez
  que você dá play (alguns MB) e guarda no computador.

**Corrigido**

- A janela de boas-vindas mostrava a palavra "null" embaixo do campo da chave da API quando não havia chave salva.
- O título do cartão de aprovação agora diz o que o Claude pede para fazer ("Escrever", "Rodar este comando",
  "Enviar um e-mail para") em vez de descrever como se já tivesse feito.
- As lições "Primeira automação" e "Como o modo Code funciona" prometiam demais do **Desfazer mudanças**: ele volta os arquivos
  que o Claude escreveu ou editou, não o que um comando fez (como mover arquivos). Agora elas dizem isso, e a
  primeira usa o nome de verdade do botão da pasta (**Escolher a pasta de trabalho**).

## 4.2.0 (15/10/2026)

**Novo**

- **O Claude pergunta com um cartão**: quando ele trava numa decisão que é sua, aparece um cartão com até 4
  perguntas e opções para clicar (uma ou várias, e um campo para outra resposta), e ele segue a partir da sua
  resposta. "Pular" deixa ele seguir com a opção que recomendaria. Funciona no chat e no Code; as rotinas não
  perguntam, porque não tem ninguém para responder.
- **"Posso fazer assim?"**: no Code, em qualquer modo, antes de uma tarefa grande (vários arquivos, mover ou
  renomear arquivos, algo difícil de desfazer) o Claude mostra o plano e espera "Pode ir", "Mudar o plano" ou
  "Não fazer". O modo Plano continua como era. Dá para desligar em Configurações > Modo Code.

**Corrigido**

- Ao reabrir uma conversa que esperava a sua decisão sobre um plano, o plano aparecia duas vezes.

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
