// Configurações: conta, personalização, modelos, recursos, teto de gasto, modo Code, GitHub, conectores, aparência e dados.
import { api } from './api.js';
import { estado, cfg, salvarConfig, carregarEstado } from './estado.js';
import { ic } from './icones.js';
import { el, aviso, chaveLiga, confirmar, janela, escolherArquivos, usd } from './ui.js';
import { checarAtualizacao, abrirAtualizacao } from './atualizar.js';
import { criarMiniChat } from './minichat.js';
import { t, localidade } from './i18n.js';

const ABAS = () => [
  ['conta', t('Conta e chave')], ['personalizacao', t('Personalização')], ['memoria', t('Memória')], ['modelos', t('Modelos')],
  ['recursos', t('Recursos')], ['limite', t('Limite de gasto')], ['code', t('Modo Code')], ['github', t('GitHub')],
  ['conectores', t('Conectores')], ['aparencia', t('Aparência')], ['dados', t('Dados e backup')], ['sobre', t('Atualizações e sobre')],
];

export async function telaConfig(principal, aba = 'conta') {
  const abas = ABAS();
  if (!abas.some(([id]) => id === aba)) aba = 'conta';
  const conteudo = el('div', {});
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' }, el('h1', { texto: t('Configurações') })),
    el('div', { class: 'config' },
      el('nav', { class: 'config-abas', 'aria-label': t('Seções') }, ...abas.map(([id, nome]) => el('a', { href: `#/config/${id}`, 'aria-current': id === aba ? 'page' : null, texto: nome }))),
      conteudo))));
  await SECOES[aba](conteudo);
  return {};
}

const salvar = async (alt, msg) => {
  try { await salvarConfig(alt); if (msg) aviso(msg); } catch (e) { aviso(e.message, 'erro'); }
};

function campo(rotulo, entrada, ajuda) {
  return el('label', { class: 'campo' }, el('span', { texto: rotulo }), entrada, ajuda ? el('small', { texto: ajuda }) : null);
}
function texto(chave, { area = false, placeholder = '', tipo = 'text' } = {}) {
  const e = el(area ? 'textarea' : 'input', { class: area ? 'area' : 'entrada', placeholder, type: area ? null : tipo });
  e.value = cfg()[chave] ?? '';
  e.addEventListener('change', () => salvar({ [chave]: tipo === 'number' ? (e.value === '' ? '' : Number(e.value)) : e.value }, t('Salvo.')));
  return e;
}
function selecao(chave, opcoes) {
  const s = el('select', { class: 'selecao' }, ...opcoes.map(([v, rot]) => el('option', { value: v, texto: rot })));
  s.value = cfg()[chave] ?? opcoes[0][0];
  s.addEventListener('change', () => salvar({ [chave]: s.value }));
  return s;
}
function liga(chave, rotulo, ajuda) {
  return chaveLiga({ rotulo, ajuda, marcado: !!cfg()[chave], aoMudar: (v) => salvar({ [chave]: v }) });
}
function secao(titulo, descricao, ...filhos) {
  return el('section', { class: 'config-secao' }, el('h2', { texto: titulo }), descricao ? el('p', { texto: descricao }) : null, ...filhos);
}
const preco = (v) => Number(v).toLocaleString(localidade(), { maximumFractionDigits: 4 });
const modelosOpcoes = () => (estado.info?.modelos || []).map((m) => [m.id, t('{nome} (US$ {entrada} / {saida} por milhão)', { nome: m.nome, entrada: preco(m.entrada), saida: preco(m.saida) })]);
const esforcoOpcoes = () => (estado.info?.esforcos || []).map((e) => [e.id, e.nome]);

const SECOES = {
  async conta(alvo) {
    const info = estado.info;
    const chave = el('input', { class: 'entrada mono', type: 'password', placeholder: 'sk-ant-...', autocomplete: 'off' });
    const status = info.demo
      ? el('div', { class: 'nota-conversa info' }, el('span', { html: ic('info') }), t('Modo demonstração: as respostas são de mentira e nada é cobrado.'))
      : info.tem_chave
        ? el('div', { class: 'item-lista' }, el('span', { html: ic('chave') }), el('span', { class: 'textos' }, el('b', { texto: t('Chave salva') }), el('small', { class: 'mono', texto: info.chave })),
          el('button', { class: 'botao pequeno perigo', type: 'button', texto: t('Apagar'), onclick: async () => {
            if (!await confirmar(t('Apagar a chave deste computador? O Claude para de responder até você colar outra.'), { sim: t('Apagar'), perigo: true })) return;
            await api('/chave', { metodo: 'DELETE' }); await carregarEstado(); SECOES.conta(alvo);
          } }))
        : el('div', { class: 'nota-conversa' }, el('span', { html: ic('alerta') }), t('Nenhuma chave salva ainda.'));
    alvo.replaceChildren(secao(t('Conta e chave da API'),
      t('O Clave conversa com o Claude pela API da Anthropic, usando a sua chave. A chave fica guardada só neste computador, criptografada pelo Windows.'),
      status,
      campo(t('Colar uma chave nova'), chave, t('Ela começa com sk-ant-. O Clave confere com a Anthropic antes de salvar.')),
      el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap' },
        el('button', { class: 'botao primario', type: 'button', texto: t('Conferir e salvar'), onclick: async (e) => {
          const b = e.currentTarget;
          b.disabled = true;
          try { await api('/chave', { metodo: 'POST', corpo: { chave: chave.value.trim() } }); chave.value = ''; await carregarEstado(); aviso(t('Chave salva.')); SECOES.conta(alvo); }
          catch (er) { aviso(er.message, 'erro'); } finally { b.disabled = false; }
        } }),
        el('a', { class: 'botao', href: '#/aprender/chave-da-api', texto: t('Como conseguir uma chave') }))));
  },

  async personalizacao(alvo) {
    const estilos = estado.info.estilos;
    const listaEstilos = el('div', { class: 'lista-itens' });
    const desenharEstilos = () => {
      listaEstilos.replaceChildren(...(cfg().estilos_proprios || []).map((s) => el('div', { class: 'item-lista' },
        el('span', { class: 'textos' }, el('b', { texto: s.nome }), el('small', { texto: s.instrucoes })),
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Editar'), onclick: () => editarEstilo(s) }),
        el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar estilo'), html: ic('lixo'), onclick: async () => {
          await salvar({ estilos_proprios: cfg().estilos_proprios.filter((x) => x.id !== s.id), estilo: cfg().estilo === s.id ? 'normal' : cfg().estilo });
          SECOES.personalizacao(alvo);
        } }))));
    };
    const editarEstilo = (s = null) => {
      const nome = el('input', { class: 'entrada', value: s?.nome || '', placeholder: t('Ex.: Professor paciente') });
      const inst = el('textarea', { class: 'area', placeholder: t('Ex.: Explique com analogias do dia a dia, faça uma pergunta no fim para ver se entendi.') });
      inst.value = s?.instrucoes || '';
      janela({ titulo: s ? t('Editar estilo') : t('Novo estilo'), corpo: el('div', { style: 'display:grid;gap:12px' }, campo(t('Nome'), nome), campo(t('Como o Claude deve escrever'), inst)),
        botoes: [{ texto: t('Cancelar') }, { texto: t('Salvar'), classe: 'primario', acao: async () => {
          if (!nome.value.trim()) { aviso(t('Dê um nome.'), 'erro'); return false; }
          const lista = (cfg().estilos_proprios || []).filter((x) => x.id !== s?.id);
          lista.push({ id: s?.id || 'proprio-' + Date.now().toString(36), nome: nome.value.trim(), instrucoes: inst.value.trim() });
          await salvar({ estilos_proprios: lista });
          SECOES.personalizacao(alvo);
        } }] });
    };
    desenharEstilos();
    alvo.replaceChildren(
      secao(t('Sobre você'), t('O Claude lê isto no começo de cada conversa nova. Quanto mais ele souber, melhor ele acerta o tom e o nível das respostas.'),
        campo(t('Como o Claude deve te chamar'), texto('nome', { placeholder: t('Seu nome ou apelido') })),
        campo(t('Sobre você'), texto('sobre_voce', { area: true, placeholder: t('Ex.: Tenho 34 anos, sou confeiteira, tenho uma loja no Instagram. Não sei programar. Uso Windows e celular Android.') }),
          t('O que você faz, o que sabe, o que não sabe, que programas usa.')),
        campo(t('Como você quer as respostas'), texto('como_responder', { area: true, placeholder: t('Ex.: Respostas curtas e diretas, em português do Brasil, sem palavras difíceis. Quando der passo a passo, numere.') }))),
      secao(t('Estilo das respostas'), t('O jeito de escrever. Vale para as conversas novas.'),
        campo(t('Estilo padrão'), selecao('estilo', Object.entries(estilos).map(([id, s]) => [id, s.nome]))),
        el('div', { class: 'rotulo', texto: t('Seus estilos') }), listaEstilos,
        el('button', { class: 'botao', type: 'button', html: `${ic('mais')}${t('Criar estilo')}`, onclick: () => editarEstilo() })),
      secao(t('Outros'), null, liga('titulos_automaticos', t('Dar título às conversas sozinho'), t('Usa o Haiku 5.5 uma vez por conversa (custa uma fração de centavo).'))));
  },

  async memoria(alvo) {
    const listaEl = el('div', { class: 'lista-itens' });
    const NOMES_TIPO = { 'sobre-voce': t('Sobre você'), preferencia: t('Preferência'), projeto: t('Projeto'), referencia: t('Referência') };
    const desenharLista = async () => {
      const { arquivos } = await api('/memoria');
      rotulo.textContent = t('Memórias guardadas ({n})', { n: arquivos.filter((a) => !a.indice).length });
      listaEl.replaceChildren(...(arquivos.length ? arquivos.map((a) => {
        const area = el('textarea', { class: 'area mono', style: 'font-size:13px;min-height:140px', hidden: true });
        area.value = a.texto;
        const salvarBt = el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Salvar'), hidden: true, onclick: async () => {
          await api('/memoria', { metodo: 'POST', corpo: { caminho: a.caminho, texto: area.value } }); aviso(t('Salvo.')); desenharLista();
        } });
        const corpo = el('div', { class: 'corpo-mem', texto: a.indice ? a.texto : a.corpo });
        return el('div', { class: `memoria-cartao ${a.indice ? 'indice' : ''}` },
          el('div', { class: 'linha-topo' },
            el('b', { texto: a.indice ? t('Índice (MEMORY.md)') : a.nome }),
            a.tipo ? el('span', { class: 'etiqueta', texto: NOMES_TIPO[a.tipo] || a.tipo }) : null,
            el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Editar à mão'), onclick: () => { area.hidden = !area.hidden; salvarBt.hidden = area.hidden; corpo.hidden = !area.hidden; } }),
            el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar {caminho}', { caminho: a.caminho }), title: t('Apagar'), html: ic('lixo'), onclick: async () => {
              const pergunta = a.indice
                ? t('Apagar {caminho}?', { caminho: a.caminho })
                : t('Apagar {caminho}? (Lembre de tirar a linha dele do índice, ou peça ao editor abaixo.)', { caminho: a.caminho });
              if (await confirmar(pergunta, { sim: t('Apagar'), perigo: true })) {
                await api(`/memoria?caminho=${encodeURIComponent(a.caminho)}`, { metodo: 'DELETE' }); desenharLista();
              }
            } })),
          a.descricao ? el('p', { texto: a.descricao }) : null,
          el('code', { class: 'meta', texto: a.caminho }),
          corpo, area, salvarBt);
      }) : [el('p', { class: 'ajuda', texto: t('Nada guardado ainda. Com a memória ligada, o Claude vai anotando o que vale lembrar.') })]));
    };
    const rotulo = el('div', { class: 'rotulo', texto: t('Memórias guardadas') });
    const editor = criarMiniChat({
      tipo: 'memoria',
      titulo: t('Pedir uma mudança ao editor de memória (Sonnet 5.5)'),
      descricao: t('Diga o que quer mudar, em palavras normais. Ele lê as memórias, faz a mudança e conta o que mudou.'),
      placeholder: t('Ex.: Mudei de emprego, agora trabalho como designer. Atualize o que você sabe sobre mim.'),
      sugestoes: [t('O que você sabe sobre mim?'), t('Esqueça tudo sobre o meu antigo emprego'), t('Junte as memórias repetidas')],
      rotuloBotao: t('Pedir mudança'),
      aoTerminar: desenharLista,
    });
    alvo.replaceChildren(secao(t('Memória'),
      t('Com a memória ligada, o Claude guarda o que vale lembrar entre conversas, do mesmo jeito que o Claude Code: um arquivo de texto para cada assunto (quem você é, suas preferências, seus projetos) e um índice que ele lê no começo de cada conversa. Tudo fica neste computador e você pode ler, mudar e apagar aqui.'),
      liga('memoria_ligada', t('Ligar a memória'), t('Vale para as conversas novas, no chat e no Code. Ele nunca deve anotar senhas ou documentos.')),
      editor.elemento,
      rotulo, listaEl));
    desenharLista();
  },

  async modelos(alvo) {
    alvo.replaceChildren(
      secao(t('Modelos'), t('O modelo e o raciocínio de cada conversa nova. Dá para trocar a qualquer momento na caixa de texto.'),
        el('div', { class: 'linha-campos' }, campo(t('Modelo no chat'), selecao('modelo_chat', modelosOpcoes())), campo(t('Raciocínio no chat'), selecao('esforco_chat', esforcoOpcoes()))),
        el('div', { class: 'linha-campos' }, campo(t('Modelo no Code'), selecao('modelo_code', modelosOpcoes())), campo(t('Raciocínio no Code'), selecao('esforco_code', esforcoOpcoes()))),
        liga('mostrar_raciocinio', t('Mostrar o raciocínio'), t('Mostra um resumo do que o Claude pensou antes de responder. Não muda o preço.')),
        liga('modelos_antigos', t('Mostrar modelos antigos'), t('Modelos anteriores que a Anthropic ainda vende. Costumam ser mais caros e menos inteligentes que os atuais.')),
        el('a', { href: '#/aprender/modelos-e-raciocinio', texto: t('Qual modelo escolher?') })));
  },

  async recursos(alvo) {
    alvo.replaceChildren(
      secao(t('Recursos'), null,
        liga('busca_web', t('Deixar o Claude pesquisar na web'), t('Ele decide sozinho quando a resposta precisa de algo atual e mostra as fontes. Cada busca custa US$ 0,01 além dos tokens. Numa conversa, o botão Web desliga só ali.')),
        liga('cache_automatico', t('Cache automático'), t('Reaproveita o começo da conversa entre uma mensagem e outra e cobra bem menos por ele. Deixe ligado.')),
        liga('compactacao', t('Resumir conversas muito longas'), t('Quando a conversa passa do tamanho abaixo, a Anthropic resume o começo dela para caber e ficar mais barata.')),
        campo(t('Resumir a partir de (tokens)'), texto('compactar_em', { tipo: 'number' }), t('Entre 50 mil e 900 mil. Padrão: 150 mil.')),
        liga('troca_se_recusar', t('Trocar de modelo se ele recusar'), t('Se o filtro de segurança recusar um pedido normal por engano, a Anthropic tenta de novo com outro modelo indicado por ela. Não vale para o Haiku.')),
        el('div', { class: 'campo' }, el('span', { texto: t('Recursos desligados por erro') }),
          el('small', { texto: t('Quando a API recusa um destes recursos para um modelo, o Clave desliga só aquele recurso e segue. Se a Anthropic passar a aceitar, religue aqui.') }),
          el('button', { class: 'botao pequeno', type: 'button', texto: t('Religar tudo'), style: 'justify-self:start', onclick: async () => { await api('/compat', { metodo: 'DELETE' }); aviso(t('Recursos religados.')); } }))));
  },

  async limite(alvo) {
    const o = estado.info.orcamento;
    alvo.replaceChildren(
      secao(t('Limite de gasto'), t('O Clave soma o custo de cada resposta e para (ou avisa) quando o mês chega no teto. Quem tem o plano Max ganha crédito mensal na API (US$ 100 no Max 5x, US$ 200 no Max 20x): um bom teto é esse valor.'),
        el('div', { class: 'item-lista' }, el('span', { html: ic('grafico') }), el('span', { class: 'textos' }, el('b', { texto: t('{valor} gastos neste ciclo', { valor: usd(o.gasto, 2) }) }), el('small', { texto: o.teto ? t('{p}% do teto', { p: o.porcentagem.toFixed(1) }) : t('sem teto') })),
          el('a', { class: 'botao pequeno', href: '#/uso', texto: t('Ver detalhes') })),
        el('div', { class: 'linha-campos' },
          campo(t('Teto por mês (US$)'), texto('teto_mensal_usd', { tipo: 'number', placeholder: t('sem teto') }), t('Deixe vazio para não ter teto.')),
          campo(t('Dia em que o mês vira'), texto('dia_virada', { tipo: 'number' }), t('De 1 a 28. Use o dia em que seu crédito renova.'))),
        campo(t('Quando chegar no teto'), selecao('ao_atingir', [['bloquear', t('Parar de responder até o mês virar')], ['avisar', t('Só avisar e continuar')]])),
        campo(t('Teto por tarefa no modo Code (US$)'), texto('teto_tarefa_code_usd', { tipo: 'number' }), t('Uma tarefa longa no Code pausa ao gastar isso, e você decide se continua. 0 = sem teto.')),
        el('p', { class: 'ajuda', texto: t('Para ter uma trava que nem o Clave consegue passar, crie no Console da Anthropic um workspace com limite de gasto e use uma chave dele.') })));
  },

  async code(alvo) {
    const prot = el('textarea', { class: 'area mono', style: 'font-size:13px;min-height:160px' });
    prot.value = (cfg().protegidos || []).join('\n');
    prot.addEventListener('change', () => salvar({ protegidos: prot.value.split('\n').map((x) => x.trim()).filter(Boolean) }, t('Salvo.')));
    alvo.replaceChildren(
      secao(t('Modo Code'), t('No modo Code o Claude trabalha numa pasta do seu computador: lê, cria e edita arquivos e roda comandos.'),
        campo(t('Permissão padrão'), selecao('permissao_code', [
          ['perguntar', t('Perguntar: pede OK para editar e rodar comandos')],
          ['aceitar_edicoes', t('Aceitar edições: só pede OK para comandos')],
          ['plano', t('Plano: só lê e propõe')],
          ['livre', t('Livre: faz tudo (menos apagar ou publicar)')]])),
        liga('carregar_claude_md', t('Ler as regras da pasta (CLAUDE.md e AGENTS.md)'), t('Como no Claude Code: as regras escritas na pasta e nas pastas acima dela valem para o Claude.')),
        campo(t('Arquivos e pastas protegidos'), prot, t('Um por linha (ex.: .env, *.key, segredos/**). As ferramentas de arquivo nunca leem nem mudam o que combina com estes padrões, e um comando que cite um deles sempre pede o seu OK.'))),
      secao(t('Regras de permissão'), t('Para liberar ou bloquear ações específicas (um comando, uma pasta, um site), sem mudar o modo inteiro. Mesmo formato do Claude Code.'),
        el('a', { class: 'botao', href: '#/permissoes', html: `${ic('escudo')}${t('Abrir as regras de permissão')}` })));
  },

  async github(alvo) {
    alvo.replaceChildren(el('p', { class: 'ajuda', texto: t('Carregando…') }));
    const g = await api('/github/estado');
    const token = el('input', { class: 'entrada mono', type: 'password', placeholder: t('ghp_... ou github_pat_...') });
    const conectar = async (origem) => {
      try { const r = await api('/github/conectar', { metodo: 'POST', corpo: { origem, token: token.value } }); await carregarEstado(); aviso(origem ? t('Conectado como {login}.', { login: r.usuario?.login }) : t('Desconectado.')); SECOES.github(alvo); }
      catch (e) { aviso(e.message, 'erro'); }
    };
    const conectado = g.origem && g.usuario;
    alvo.replaceChildren(secao(t('GitHub'), t('Conecte para anexar arquivos dos seus repositórios e deixar o Claude ler código, issues e pull requests. Criar issue, comentar e abrir PR sempre pedem o seu OK.'),
      conectado ? el('div', { class: 'item-lista' }, el('span', { html: ic('ramo') }), el('span', { class: 'textos' }, el('b', { texto: g.usuario.login }), el('small', { texto: g.origem === 'gh' ? t('Pelo login do gh') : t('Por token pessoal') })),
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Desconectar'), onclick: () => conectar('') }))
        : g.erro ? el('div', { class: 'nota-conversa erro' }, el('span', { html: ic('alerta') }), g.erro) : null,
      !conectado ? el('div', { style: 'display:grid;gap:12px' },
        g.gh_instalado ? el('button', { class: 'botao primario', type: 'button', texto: t('Usar o login do gh (GitHub CLI)'), onclick: () => conectar('gh') }) : null,
        campo(t('Ou cole um token pessoal'), token, t('Crie em github.com > Settings > Developer settings > Personal access tokens. Para ler, basta a permissão de leitura dos repositórios.')),
        el('button', { class: 'botao', type: 'button', texto: t('Conectar com o token'), onclick: () => conectar('token') }),
        el('a', { href: '#/aprender/github', texto: t('O que é o GitHub e para que serve?') })) : null,
      conectado ? liga('github_ferramentas', t('Ferramentas do GitHub ligadas por padrão'), t('Deixa o Claude consultar seus repositórios durante a conversa (botão GitHub na caixa de texto).')) : null,
      conectado ? liga('github_escrita', t('Permitir criar issue, comentar e abrir PR'), t('Mesmo ligado, cada ação pede o seu OK antes.')) : null));
  },

  async conectores(alvo) {
    const lista = cfg().conectores_mcp || [];
    const nome = el('input', { class: 'entrada', placeholder: t('ex.: deepwiki') });
    const url = el('input', { class: 'entrada mono', placeholder: t('https://mcp.exemplo.com/mcp') });
    const token = el('input', { class: 'entrada mono', type: 'password', placeholder: t('só se o serviço pedir'), autocomplete: 'off' });
    alvo.replaceChildren(secao(t('Conectores (MCP)'),
      t('Conectores ligam o Claude a outros serviços (documentação, ferramentas, bancos de dados) que falam o padrão MCP. A Anthropic se conecta direto ao endereço, então só funciona com servidores MCP públicos na internet (não com os do seu computador). Use só serviços em que você confia.'),
      lista.length ? el('div', { class: 'lista-itens' }, ...lista.map((m, i) => el('div', { class: 'item-lista' },
        el('span', { html: ic('conector') }), el('span', { class: 'textos' }, el('b', { texto: m.nome }), el('small', { class: 'mono', texto: m.url })),
        chaveLiga({ rotulo: m.ligado ? t('Ligado') : t('Desligado'), marcado: m.ligado, aoMudar: async (v) => { lista[i] = { ...m, ligado: v }; await salvar({ conectores_mcp: lista }); SECOES.conectores(alvo); } }),
        el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar conector'), html: ic('lixo'), onclick: async () => { await api('/conectores/token', { metodo: 'POST', corpo: { nome: m.nome, token: '' } }); lista.splice(i, 1); await salvar({ conectores_mcp: lista }); SECOES.conectores(alvo); } }))))
        : el('p', { class: 'ajuda', texto: t('Nenhum conector.') }),
      el('div', { class: 'linha-campos' }, campo(t('Nome'), nome), campo(t('Endereço (URL)'), url)),
      campo(t('Token de acesso (opcional)'), token, t('Fica guardado criptografado neste computador e vai só para esse conector.')),
      el('button', { class: 'botao', type: 'button', html: `${ic('mais')}${t('Adicionar conector')}`, onclick: async () => {
        const n = nome.value.trim().replace(/[^\w-]/g, '-');
        if (!n || !/^https:\/\//.test(url.value.trim())) { aviso(t('Preencha um nome e um endereço https://'), 'erro'); return; }
        if (token.value.trim()) await api('/conectores/token', { metodo: 'POST', corpo: { nome: n, token: token.value.trim() } });
        await salvar({ conectores_mcp: [...lista.filter((m) => m.nome !== n), { nome: n, url: url.value.trim(), ligado: true }] }, t('Conector adicionado.'));
        SECOES.conectores(alvo);
      } })));
  },

  async aparencia(alvo) {
    const tema = el('div', { class: 'segmentado', role: 'group', 'aria-label': t('Tema') }, ...[['sistema', t('Do sistema')], ['claro', t('Claro')], ['escuro', t('Escuro')]].map(([v, rot]) =>
      el('button', { type: 'button', 'aria-pressed': String(cfg().tema === v), texto: rot, onclick: async () => { await salvar({ tema: v }); SECOES.aparencia(alvo); } })));
    const tamanho = el('input', { type: 'range', min: '14', max: '22', step: '1', value: cfg().tamanho_letra || 17 });
    const rotTam = el('span', { class: 'meta', texto: `${tamanho.value}px` });
    tamanho.addEventListener('input', () => { rotTam.textContent = `${tamanho.value}px`; document.documentElement.style.setProperty('--t-leitura', `${tamanho.value}px`); });
    tamanho.addEventListener('change', () => salvar({ tamanho_letra: Number(tamanho.value) }));
    // o idioma troca a interface, as lições, os prompts e o modelo de pasta; a tela recarrega para valer em tudo
    const idiomas = el('div', { class: 'segmentado', role: 'group', 'aria-label': t('Idioma') },
      ...[['pt-BR', 'Português (Brasil)'], ['en', 'English']].map(([v, rot]) =>
        el('button', { type: 'button', 'aria-pressed': String(cfg().idioma === v), texto: rot, onclick: async () => {
          if (cfg().idioma === v) return;
          await salvar({ idioma: v });
          location.reload();
        } })));
    alvo.replaceChildren(secao(t('Aparência'), null,
      el('div', { class: 'campo' }, el('span', { texto: t('Idioma') }), idiomas,
        el('small', { texto: t('Vale para a interface, as lições, o modelo de pasta e o que o Clave diz ao Claude. O Claude responde no idioma em que você escrever.') })),
      el('div', { class: 'campo' }, el('span', { texto: t('Tema') }), tema),
      el('div', { class: 'campo' }, el('span', { texto: t('Tamanho da letra das respostas') }), el('div', { style: 'display:flex;gap:12px;align-items:center' }, tamanho, rotTam)),
      el('div', { class: 'linha-campos' },
        campo(t('Letra das respostas'), selecao('letra_resposta', [['serifa', t('Serifada (de livro)')], ['sans', t('Sem serifa')]])),
        campo(t('Largura da conversa'), selecao('largura_chat', [['estreita', t('Estreita')], ['media', t('Média')], ['larga', t('Larga')]]))),
      campo(t('Enviar mensagem com'), selecao('enviar_com', [['enter', t('Enter (Shift+Enter pula linha)')], ['ctrl_enter', t('Ctrl+Enter (Enter pula linha)')]])),
      liga('mostrar_custo', t('Mostrar o custo de cada resposta'), t('Aparece pequeno, embaixo de cada resposta.')),
      liga('painel_uso_inicio', t('Painel de uso no início'), t('Mostra tokens, dias seguidos, mapa de calor, modelo favorito e a projeção do mês na tela de conversa nova.')),
      liga('notificacoes', t('Notificação do Windows'), t('Avisa quando o Claude termina, pede o seu OK, propõe um fluxo ou quando uma rotina acaba, se a janela do Clave estiver em segundo plano.')),
      !window.clave && 'Notification' in window && Notification.permission !== 'granted' ? el('button', { class: 'botao', type: 'button', texto: t('Deixar o navegador mostrar as notificações'),
        onclick: async () => { await Notification.requestPermission(); SECOES.aparencia(alvo); } }) : null));
  },

  async dados(alvo) {
    alvo.replaceChildren(secao(t('Dados e backup'),
      t('Suas conversas, projetos e gastos ficam num arquivo dentro da pasta dados/ do Clave, neste computador. Nada vai para outro lugar além da própria Anthropic (as mensagens que você manda).'),
      el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap' },
        el('a', { class: 'botao', href: '/api/backup', html: `${ic('baixar')}${t('Baixar backup das conversas')}` }),
        el('button', { class: 'botao', type: 'button', html: `${ic('subir')}${t('Importar backup')}`, onclick: async () => {
          const [f] = await escolherArquivos({ multiplo: false, aceitar: '.json' });
          if (!f) return;
          try {
            const r = await fetch('/api/backup', { method: 'POST', body: f, credentials: 'same-origin' }).then((x) => x.json());
            if (r.erro) throw new Error(r.erro);
            aviso(t('Importado: {conversas} conversa(s), {mensagens} mensagem(ns).', { conversas: r.importado.conversas, mensagens: r.importado.mensagens }));
          } catch (e) { aviso(e.message, 'erro'); }
        } })),
      el('p', { class: 'ajuda', texto: t('O backup leva as conversas, os projetos e o histórico de gasto. Os arquivos anexados e a chave não vão junto.') })));
  },

  async sobre(alvo) {
    const info = estado.info;
    const caixaAtual = el('div', { class: 'ajuda', texto: '' });
    alvo.replaceChildren(
      secao(t('Atualizações'), null,
        el('div', { class: 'item-lista' }, el('span', { html: ic('subir') }), el('span', { class: 'textos' }, el('b', { texto: t('Versão {versao}', { versao: info.versao }) }),
          el('small', { texto: info.dev ? t('Cópia de desenvolvimento (atualize com git pull)') : (cfg().ultima_checagem ? t('Última verificação: {quando}', { quando: cfg().ultima_checagem }) : t('Ainda não verificou')) })),
          el('button', { class: 'botao pequeno', type: 'button', texto: t('Procurar atualização'), onclick: async () => { const r = await checarAtualizacao({ forcar: true }); if (r?.nova) abrirAtualizacao(); } })),
        caixaAtual,
        liga('checar_atualizacoes', t('Procurar atualização sozinho'), t('Uma vez por dia, ao abrir. Nunca instala sem você clicar.'))),
      secao(t('Sobre o Clave'), null,
        el('p', { style: 'margin:0', texto: t('O Clave é um app independente para usar o Claude pela API da Anthropic, com a sua chave. Ele não é um produto da Anthropic nem tem ligação com ela. "Claude" é marca da Anthropic.') }),
        el('p', { class: 'ajuda', texto: t('Feito com: marked, DOMPurify, highlight.js, KaTeX, fontes Source Serif 4 e IBM Plex, o SDK oficial da Anthropic para Python e o Electron. As licenças estão na pasta app/vendor.') }),
        el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap' },
          el('a', { class: 'botao', href: '#/aprender', texto: t('Abrir as lições') }),
          el('button', { class: 'botao perigo', type: 'button', html: `${ic('sair')}${t('Fechar o Clave')}`, onclick: async () => {
            if (!await confirmar(t('Fechar o Clave? Respostas em andamento são interrompidas.'), { sim: t('Fechar') })) return;
            if (window.clave?.sair) window.clave.sair(); else { await api('/sair', { metodo: 'POST' }).catch(() => {}); document.body.innerHTML = `<p style="padding:40px;font-family:sans-serif">${t('O Clave foi fechado. Pode fechar esta janela.')}</p>`; }
          } }))));
  },
};
