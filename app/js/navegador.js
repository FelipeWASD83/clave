// A aba Navegador do painel (modo Code): um navegador de verdade que a pessoa e o Claude usam juntos.
//
// A página em si não é HTML desta tela: é uma vista nativa do Electron (WebContentsView) desenhada POR CIMA da
// janela, no retângulo da área .navegador-vista. Por isso esta aba manda a posição dessa área para o Electron
// sempre que ela muda (abrir, fechar, arrastar a alça, redimensionar, zoom) e esconde a vista quando algo do app
// precisa aparecer por cima (janela, menu, tour, cartão de modelo novo, aviso): nesses momentos fica no lugar uma
// foto congelada da página, para nada piscar.
//
// Fora da janela do Clave (o modo Edge, sem Electron) não existe navegador: a aba explica isso.
import { api } from './api.js';
import { ic } from './icones.js';
import { el, aviso, menu } from './ui.js';
import { registrarAba, abrirPainel, ouvirPainel } from './painel.js';
import { t } from './i18n.js';

const nav = () => window.clave?.navegador || null;
let aba = null;                 // a aba montada (só existe uma)
let claudeAtivo = false;        // o Claude está mexendo no navegador agora
let timerClaude = null;

registrarAba({
  id: 'navegador', titulo: () => t('Navegador'), icone: 'globo', modos: ['code'],
  atalho: 'Ctrl+Shift+L', tecla: (e) => e.shiftKey && (e.key === 'L' || e.key === 'l'),
  montar(caixa) {
    aba = nav() ? montar(caixa) : montarSemJanela(caixa);
    return aba.ganchos;
  },
});

// A conversa chama isto quando uma ferramenta navegador_* começa (true) e quando termina (false). A faixa some um
// pouco depois do false, para não piscar entre uma ação e a próxima; sem o false, some sozinha.
export function marcarClaudeUsando(sim) {
  clearTimeout(timerClaude);
  if (sim) {
    claudeAtivo = true;
    aba?.claude(true);
    timerClaude = setTimeout(() => marcarClaudeUsando(false), 10_000);
  } else {
    timerClaude = setTimeout(() => { claudeAtivo = false; aba?.claude(false); }, 2500);
  }
}

// o que a pessoa digita na barra de endereço vira um endereço ou uma busca
export function paraUrl(texto) {
  const s = String(texto || '').trim();
  if (!s) return null;
  if (/^https?:\/\//i.test(s)) return s;
  if (/^:?\d{2,5}$/.test(s)) return `http://localhost:${s.replace(':', '')}/`;
  if (/^(localhost|127(\.\d+){3}|0\.0\.0\.0|\[[0-9a-f:]+\])(:\d+)?([/?#].*)?$/i.test(s)) return 'http://' + s;
  if (!/\s/.test(s) && /^[^/?#]+\.[^/?#]+/.test(s) && !/^[a-z][a-z0-9+.-]*:(?!\d)/i.test(s)) {
    return (/^\d+(\.\d+){3}/.test(s) ? 'http://' : 'https://') + s;
  }
  return 'https://duckduckgo.com/?q=' + encodeURIComponent(s);
}

// pedidos que chegam do Electron: o Claude vai agir (mostrar a aba), atalhos de dentro da página, downloads
function ouvirPedidos() {
  if (!window.clave?.aoPedir) return;
  window.clave.aoPedir((p) => {
    if (!p || typeof p !== 'object' || p.tipo !== 'navegador') return;
    if (p.acao === 'mostrar') {
      abrirPainel('navegador', null, { foco: false });
      if (p.claude) marcarClaudeUsando(true);
    } else if (p.acao === 'focar-endereco') {
      abrirPainel('navegador', null, { foco: false });
      aba?.focarEndereco?.();
    } else if (p.acao === 'tecla') {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: p.key, ctrlKey: true, shiftKey: !!p.shift, bubbles: true, cancelable: true }));
    } else if (p.acao === 'download') {
      if (p.estado === 'completed') aviso(t('Download concluído: {nome}', { nome: p.nome || '' }));
      else if (p.estado === 'interrupted') aviso(t('O download de {nome} não terminou.', { nome: p.nome || '' }), 'erro');
    }
  });
}
ouvirPedidos();

function erroAmigavel(erro) {
  const c = String(erro?.codigo || '');
  if (c === 'travou') return t('A página travou e foi fechada. Tente recarregar.');
  if (c.startsWith('ERR_CERT')) return t('O certificado de segurança do site não é válido. Pode ser um site falso ou com a configuração errada.');
  const textos = {
    ERR_NAME_NOT_RESOLVED: () => t('Esse endereço não foi encontrado. Confira se está escrito certo.'),
    ERR_CONNECTION_REFUSED: () => t('Nada respondeu nesse endereço. Se for um servidor do seu projeto, confira se ele está rodando.'),
    ERR_CONNECTION_TIMED_OUT: () => t('O site demorou demais para responder.'),
    ERR_TIMED_OUT: () => t('O site demorou demais para responder.'),
    ERR_INTERNET_DISCONNECTED: () => t('O computador está sem internet.'),
    ERR_CONNECTION_RESET: () => t('A conexão caiu no meio. Tente de novo.'),
    ERR_ADDRESS_UNREACHABLE: () => t('Esse endereço não pode ser alcançado daqui.'),
    ERR_EMPTY_RESPONSE: () => t('O servidor respondeu sem nada.'),
  };
  return (textos[c] || (() => t('O navegador não conseguiu abrir a página.')))();
}

// ---------- a lista de servidores locais (usada no menu Locais e na tela inicial) ----------
async function buscarLocais() {
  return (await api('/navegador/localhosts')).servidores || [];
}

function descreverLocal(s) {
  const partes = [s.url.replace(/^https?:\/\//, '').replace(/\/$/, '')];
  if (s.tarefa) partes.push(t('do comando "{titulo}"', { titulo: s.tarefa }));
  else if (s.processo) partes.push(s.processo);
  if (!s.pagina && s.origem !== 'tarefa') partes.push(t('responde, mas não é uma página (talvez uma API)'));
  return partes.join(' · ');
}

function listaLocais(servidores, aoEscolher) {
  if (!servidores.length) {
    return el('p', { class: 'navegador-locais-vazio', texto: t('Nenhum servidor rodando neste computador agora. Quando um projeto subir um (npm run dev, python -m http.server...), ele aparece aqui.') });
  }
  return el('ul', { class: 'navegador-locais', role: 'list' }, ...servidores.map((s) => {
    const descricao = descreverLocal(s);
    return el('li', {},
      el('button', { type: 'button', class: `navegador-local ${s.pagina || s.origem === 'tarefa' ? '' : 'mudo'}`, title: `${s.url}\n${descricao}`, onclick: () => aoEscolher(s.url) },
        el('span', { class: 'navegador-local-porta', texto: String(s.porta) }),
        el('span', { class: 'navegador-local-textos' },
          el('b', { texto: s.titulo || `localhost:${s.porta}` }),
          el('small', { texto: descricao }))));
  }));
}

// ---------- fora da janela do Clave ----------
function montarSemJanela(caixa) {
  const locais = el('div', { class: 'navegador-sem-janela-locais' });
  const pedido = el('p', { class: 'navegador-pedido', hidden: true });
  const abrirFora = (url) => window.open(url, '_blank', 'noopener');
  caixa.append(el('div', { class: 'painel-vazio navegador-sem-janela' },
    el('span', { html: ic('globo') }),
    el('h3', { texto: t('O navegador só funciona na janela do Clave') }),
    el('p', { texto: t('Esta tela está aberta num navegador comum, fora da janela do Clave. Abra o Clave pelo atalho na área de trabalho (ou pelo Clave.bat) para usar o navegador embutido, que você e o Claude usam juntos.') }),
    pedido, locais));
  let carregou = false;
  async function carregar() {
    carregou = true;
    locais.replaceChildren(el('p', { class: 'navegador-locais-vazio', texto: t('Procurando servidores neste computador…') }));
    try {
      const lista = await buscarLocais();
      locais.replaceChildren(el('h4', { texto: t('Servidores neste computador') }), listaLocais(lista, abrirFora));
    } catch (e) { locais.replaceChildren(el('p', { class: 'navegador-locais-vazio', title: e.message, texto: t('Não deu para procurar os servidores deste computador agora.') })); }
  }
  return {
    claude() {},
    ganchos: {
      mostrar() { if (!carregou) carregar(); },
      abrir(args) {
        if (!args?.url) return;
        pedido.hidden = false;
        pedido.replaceChildren(t('Endereço pedido: '), el('a', { href: args.url, target: '_blank', rel: 'noopener', texto: args.url }));
      },
    },
  };
}

// ---------- na janela do Clave ----------
function montar(caixa) {
  const n = nav();
  let est = { url: '', titulo: '', carregando: false, podeVoltar: false, podeAvancar: false, erro: null };
  let cobertura = false;          // algo do app está por cima da área da página
  let posta = null;               // o retângulo que o Electron recebeu por último (null = vista escondida)
  let seq = 0;
  let menuSeq = 0;
  let editando = false;

  const botao = (icone, rotulo, onclick, extra = {}) => el('button', { class: 'icone-botao', type: 'button', title: rotulo, 'aria-label': rotulo, html: ic(icone), onclick, ...extra });
  const bVoltar = botao('esq', t('Voltar (Alt+seta para a esquerda)'), () => n.voltar());
  const bAvancar = botao('dir', t('Avançar (Alt+seta para a direita)'), () => n.avancar());
  const bRecarregar = botao('refazer', t('Recarregar (F5)'), () => (est.carregando ? n.parar() : recarregar()));
  const entrada = el('input', {
    class: 'navegador-endereco-campo', type: 'text', spellcheck: 'false', autocomplete: 'off', 'data-foco': '',
    'aria-label': t('Endereço ou busca'), placeholder: t('Digite um endereço ou o que buscar'),
  });
  const form = el('form', { class: 'navegador-endereco', role: 'search' }, el('span', { class: 'navegador-endereco-icone', html: ic('globo') }), entrada);
  const bLocais = el('button', { class: 'botao pequeno fantasma navegador-botao-locais', type: 'button', title: t('Servidores rodando neste computador'),
    'aria-haspopup': 'menu', html: `${ic('computador')}<span>${t('Locais')}</span>`, onclick: (e) => menuLocais(e.currentTarget) });
  const bFora = botao('externo', t('Abrir no navegador do computador'), () => { if (est.url) window.clave.abrirExterno(est.url); });
  const carga = el('div', { class: 'navegador-carga', role: 'progressbar', 'aria-label': t('Carregando a página'), hidden: true });
  const faixa = el('div', { class: 'navegador-claude', role: 'status', hidden: true },
    el('span', { class: 'navegador-claude-ponto', 'aria-hidden': 'true' }),
    el('b', { texto: t('O Claude está usando o navegador') }),
    el('small', { texto: t('Dá para olhar junto; evite clicar enquanto ele trabalha.') }));
  const vista = el('div', { class: 'navegador-vista' });
  const foto = el('img', { class: 'navegador-foto', alt: '', hidden: true });
  const tela = el('div', { class: 'navegador-tela' });
  const area = el('div', { class: 'navegador-area' }, vista, foto, tela);

  caixa.append(el('div', { class: 'painel-barra navegador-barra' }, bVoltar, bAvancar, bRecarregar, form, bLocais, bFora), carga, faixa, area);

  // ---------- atalhos com o foco na barra da aba (endereço, botões) ----------
  // Com o foco dentro da página quem atende é o Electron (teclaNaPagina, no main.js); aqui é o mesmo para quando o
  // foco está na barra: Alt+setas voltam e avançam, F5 (ou Ctrl+R) recarrega, Ctrl+L vai para o endereço.
  caixa.addEventListener('keydown', (e) => {
    if (e.defaultPrevented || e.isComposing) return;
    const ctrl = e.ctrlKey || e.metaKey;
    const k = e.key;
    if (e.altKey && !ctrl && !e.shiftKey && (k === 'ArrowLeft' || k === 'ArrowRight')) {
      e.preventDefault();
      if (k === 'ArrowLeft' ? est.podeVoltar : est.podeAvancar) (k === 'ArrowLeft' ? n.voltar() : n.avancar())?.catch?.(() => {});
    } else if ((k === 'F5' && !ctrl && !e.altKey) || (ctrl && !e.shiftKey && !e.altKey && (k === 'r' || k === 'R'))) {
      e.preventDefault();
      if (est.url || est.erro) recarregar();
    } else if (ctrl && !e.shiftKey && !e.altKey && (k === 'l' || k === 'L')) {
      e.preventDefault();
      entrada.focus();
    }
  });

  // ---------- endereço ----------
  entrada.addEventListener('focus', () => { editando = true; setTimeout(() => entrada.select(), 0); });
  entrada.addEventListener('blur', () => { editando = false; desenharEndereco(); });
  entrada.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') { e.preventDefault(); entrada.value = est.url; entrada.blur(); }
  });
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const url = paraUrl(entrada.value);
    if (!url) return;
    entrada.blur();
    ir(url);
  });

  async function ir(url) {
    est = { ...est, erro: null, url };
    desenhar();
    try {
      const r = await n.ir(url);
      if (r?.erro) aviso(t('Esse endereço não pode ser aberto aqui: só páginas http e https.'), 'erro');
    } catch (e) { aviso(e.message, 'erro'); }
  }

  function recarregar() {
    if (est.erro?.url) { ir(est.erro.url); return; }
    n.recarregar();
  }

  function desenharEndereco() {
    if (!editando) entrada.value = est.url || '';
    form.title = est.titulo || '';
  }

  // ---------- estado da página ----------
  const temPagina = () => !!est.url;

  function desenhar() {
    desenharEndereco();
    bVoltar.disabled = !est.podeVoltar;
    bAvancar.disabled = !est.podeAvancar;
    bFora.disabled = !est.url;
    const parar = est.carregando && !est.erro;
    bRecarregar.innerHTML = ic(parar ? 'x' : 'refazer');
    const rot = parar ? t('Parar de carregar') : t('Recarregar (F5)');
    bRecarregar.title = rot; bRecarregar.setAttribute('aria-label', rot);
    bRecarregar.disabled = !est.url && !est.erro;
    carga.hidden = !est.carregando;
    desenharTela();
    sincronizar();
  }

  let telaFeita = '';
  function desenharTela() {
    const qual = est.erro ? `erro:${est.erro.codigo}:${est.erro.url}` : temPagina() ? 'pagina' : 'inicio';
    if (qual === telaFeita) return;
    telaFeita = qual;
    tela.hidden = qual === 'pagina';
    if (qual === 'pagina') { tela.replaceChildren(); return; }
    if (est.erro) {
      tela.replaceChildren(el('div', { class: 'painel-vazio navegador-erro' },
        el('span', { html: ic('alerta') }),
        el('h3', { texto: t('Não deu para abrir esta página') }),
        el('p', { texto: erroAmigavel(est.erro) }),
        el('p', { class: 'meta navegador-erro-url' }, est.erro.url || '', est.erro.codigo ? el('small', { texto: est.erro.codigo }) : null),
        el('div', { class: 'navegador-erro-botoes' },
          el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Tentar de novo'), onclick: () => ir(est.erro.url || est.url) }),
          est.erro.url ? el('button', { class: 'botao pequeno', type: 'button', texto: t('Abrir no navegador do computador'), onclick: () => window.clave.abrirExterno(est.erro.url) }) : null)));
      return;
    }
    const locais = el('div', { class: 'navegador-inicio-locais' });
    tela.replaceChildren(el('div', { class: 'painel-vazio navegador-inicio' },
      el('span', { html: ic('globo') }),
      el('h3', { texto: t('Navegador') }),
      el('p', { texto: t('Digite um endereço ou uma busca na barra acima. O Claude também usa este navegador quando precisa ver uma página, e você acompanha tudo por aqui.') }),
      locais));
    carregarLocais(locais);
  }

  let ultimaBusca = 0;
  async function carregarLocais(onde) {
    ultimaBusca = Date.now();
    onde.replaceChildren(el('h4', { texto: t('Servidores neste computador') }),
      el('p', { class: 'navegador-locais-vazio', texto: t('Procurando servidores neste computador…') }));
    try {
      const lista = await buscarLocais();
      onde.replaceChildren(
        el('div', { class: 'navegador-inicio-titulo' }, el('h4', { texto: t('Servidores neste computador') }),
          el('button', { class: 'icone-botao', type: 'button', title: t('Procurar de novo'), 'aria-label': t('Procurar de novo'), html: ic('refazer'), onclick: () => carregarLocais(onde) })),
        listaLocais(lista, ir));
    } catch (e) {
      onde.replaceChildren(el('h4', { texto: t('Servidores neste computador') }),
        el('p', { class: 'navegador-locais-vazio', title: e.message, texto: t('Não deu para procurar os servidores deste computador agora.') }));
    }
  }

  async function menuLocais(ancora) {
    const minha = ++menuSeq;
    menu(ancora, [{ titulo: t('Servidores neste computador') }, { texto: t('Procurando…'), desligado: true }], { alinhar: 'direita' });
    let lista;
    try { lista = await buscarLocais(); } catch (e) {
      if (minha === menuSeq && document.querySelector('body > .menu')) menu(ancora, [{ titulo: t('Servidores neste computador') }, { texto: t('Não deu para procurar os servidores deste computador agora.'), sub: e.message, desligado: true }], { alinhar: 'direita' });
      return;
    }
    if (minha !== menuSeq || !document.querySelector('body > .menu')) return;  // a pessoa já fechou
    const itens = [{ titulo: t('Servidores neste computador') }];
    if (!lista.length) itens.push({ texto: t('Nenhum servidor rodando agora'), sub: t('Quando um projeto subir um, ele aparece aqui.'), desligado: true });
    for (const s of lista) itens.push({ icone: 'computador', texto: s.titulo || `localhost:${s.porta}`, sub: descreverLocal(s), acao: () => ir(s.url) });
    itens.push('-', { icone: 'refazer', texto: t('Procurar de novo'), acao: () => menuLocais(ancora) });
    menu(ancora, itens, { alinhar: 'direita' });
  }

  // ---------- a vista nativa: posição e o que fica por cima ----------
  function cobertoAgora() {
    if (document.querySelector('#camada > *, body > .menu, .tour-camada, .apresentacao-fundo')) return true;
    // arrastando a alça do painel: a vista nativa engoliria o arraste quando o mouse passa por cima dela
    if (document.body.classList.contains('arrastando-painel')) return true;
    const avisos = document.querySelectorAll('#avisos > *');
    if (!avisos.length) return false;
    const r = area.getBoundingClientRect();
    return [...avisos].some((a) => { const b = a.getBoundingClientRect(); return b.left < r.right && b.right > r.left && b.top < r.bottom && b.bottom > r.top; });
  }

  // a aba está mesmo à vista? (o painel pode reabrir na mesma aba sem chamar mostrar(), ou sumir junto com a tela da
  // conversa: por isso olha o DOM, não só os ganchos)
  const painelEl = document.getElementById('painel-lateral');
  function aVista() {
    return caixa.isConnected && !caixa.hidden && !!painelEl && !painelEl.hidden
      && !painelEl.classList.contains('saindo') && caixa.getClientRects().length > 0;
  }

  function sincronizar() {
    const deve = aVista() && !cobertura && temPagina() && !est.erro;
    const r = deve ? vista.getBoundingClientRect() : null;
    const m = caixa.classList.contains('com-claude') ? 2 : 0;  // com o Claude agindo, sobra a moldura verde em volta
    const ret = r && r.width >= 2 + 2 * m && r.height >= 2 + 2 * m
      ? { x: r.left + m, y: r.top + m, width: r.width - 2 * m, height: r.height - 2 * m } : null;
    if (!ret) {
      reservarAvisos(null);
      if (posta !== null) { posta = null; n.posicionar(null).catch(() => {}); }
      return;
    }
    reservarAvisos(ret);
    if (posta && Math.abs(posta.x - ret.x) < 0.5 && Math.abs(posta.y - ret.y) < 0.5 && Math.abs(posta.width - ret.width) < 0.5 && Math.abs(posta.height - ret.height) < 0.5) return;
    posta = ret;
    n.posicionar(ret).catch(() => {});
    // a foto congelada fica embaixo da vista: some depois que a página já voltou a aparecer por cima
    if (!foto.hidden) requestAnimationFrame(() => requestAnimationFrame(() => { if (posta) { foto.hidden = true; foto.removeAttribute('src'); } }));
  }

  // os avisos do app (canto de baixo à direita) passam para a esquerda da página quando cabem ali, para não ficarem
  // escondidos atrás dela
  function reservarAvisos(ret) {
    const cabe = !!ret && ret.x > 360;
    document.body.classList.toggle('navegador-a-vista', cabe);
    if (cabe) document.body.style.setProperty('--navegador-reserva', `${Math.max(0, innerWidth - ret.x)}px`);
  }

  // durante animações (o painel entra deslizando) a área anda sem mudar de tamanho: acompanha por alguns quadros
  let seguindoAte = 0;
  function seguir(ms = 450) {
    const ja = seguindoAte > performance.now();
    seguindoAte = Math.max(seguindoAte, performance.now() + ms);
    if (ja) return;
    const passo = () => { sincronizar(); if (performance.now() < seguindoAte) requestAnimationFrame(passo); };
    requestAnimationFrame(passo);
  }

  async function checarCobertura() {
    const agora = cobertoAgora();
    if (agora === cobertura) return;
    cobertura = agora;
    const minha = ++seq;
    if (cobertura) {
      if (posta !== null) {
        posta = null;
        reservarAvisos(null);
        let imagem = null;
        try { imagem = await n.congelar(); } catch { /* sem foto: fica só o fundo */ }
        if (minha !== seq || !cobertura) return;
        if (imagem) { foto.src = imagem; foto.hidden = false; }
      }
    } else {
      sincronizar();
      if (posta === null) { foto.hidden = true; foto.removeAttribute('src'); }  // a página não volta (aba fechada, erro)
    }
  }

  const observador = new MutationObserver(() => checarCobertura());
  observador.observe(document.body, { childList: true, attributes: true, attributeFilter: ['class'] });
  for (const id of ['camada', 'avisos']) { const alvo = document.getElementById(id); if (alvo) observador.observe(alvo, { childList: true }); }
  // o painel abriu, fechou, começou a sair ou trocou de aba: acompanha
  const olhoPainel = new MutationObserver(() => {
    if (!aVista()) { sincronizar(); return; }
    seguir();
    // voltou a aparecer na tela inicial depois de um tempo: a lista de servidores pode ter mudado
    if (telaFeita === 'inicio' && Date.now() - ultimaBusca > 15000) { telaFeita = ''; desenharTela(); }
  });
  if (painelEl) olhoPainel.observe(painelEl, { attributes: true, attributeFilter: ['hidden', 'class'] });
  olhoPainel.observe(caixa, { attributes: true, attributeFilter: ['hidden'] });
  ouvirPainel(() => seguir());
  new ResizeObserver(() => sincronizar()).observe(vista);
  addEventListener('resize', () => seguir(200));
  document.addEventListener('visibilitychange', () => { if (!document.hidden) seguir(200); });  // a janela voltou a aparecer
  addEventListener('scroll', () => sincronizar(), true);
  matchMedia(`(resolution: ${devicePixelRatio}dppx)`).addEventListener?.('change', () => seguir(200));

  // ---------- o Electron conta o que mudou na página ----------
  n.aoMudar((novo) => { est = { ...est, ...novo }; desenhar(); });
  n.estado().then((e) => { if (e) { est = { ...est, ...e }; desenhar(); } }).catch(() => {});

  function claude(sim) {
    faixa.hidden = !sim;
    caixa.classList.toggle('com-claude', !!sim);
    sincronizar();
  }
  claude(claudeAtivo);
  desenhar();

  return {
    claude,
    focarEndereco() { entrada.focus(); },
    ganchos: {
      abrir(args) { if (args?.url) { const url = paraUrl(args.url); if (url) ir(url); } },
      mostrar() {
        if (!temPagina() && !est.erro) { telaFeita = ''; desenharTela(); }  // a lista de servidores locais se atualiza
        checarCobertura();
        seguir();
      },
      esconder() { sincronizar(); },
      redimensionar() { seguir(120); },
      contexto() { /* o navegador é um só para todas as conversas */ },
    },
  };
}
