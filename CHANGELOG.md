# Novidades do Clave

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
