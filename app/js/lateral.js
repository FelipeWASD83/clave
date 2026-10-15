// Barra lateral: nova conversa, navegação, busca, lista de conversas e o tinteiro do teto de gasto.
import { api } from './api.js';
import { estado, ouvir, avisar, carregarConversas } from './estado.js';
import { ic } from './icones.js';
import { el, menu, confirmar, perguntarTexto, aviso, grupoData, usd, dataBr } from './ui.js';
import { abrirAtualizacao } from './atualizar.js';

let raiz, lista, tinteiro, seloAtualizar;

export function alternarLateral() {
  const app = document.getElementById('app');
  if (matchMedia('(max-width: 900px)').matches) app.classList.toggle('lateral-aberta');
  else app.classList.toggle('lateral-fechada');
}

export function montarLateral(alvo) {
  raiz = alvo;
  const busca = el('input', { type: 'search', placeholder: 'Buscar conversas', 'aria-label': 'Buscar conversas' });
  let espera;
  busca.addEventListener('input', () => {
    clearTimeout(espera);
    espera = setTimeout(() => { estado.busca = busca.value.trim(); carregarConversas(); }, 220);
  });

  lista = el('nav', { class: 'lista-conversas', 'aria-label': 'Conversas' });
  tinteiro = el('a', { class: 'tinteiro', href: '#/uso', title: 'Quanto do teto de gasto deste mês já foi usado' });
  seloAtualizar = el('button', { class: 'selo-atualizar', type: 'button', hidden: true, onclick: () => abrirAtualizacao() }, 'Atualizar');

  raiz.replaceChildren(
    el('div', { class: 'lateral-topo' },
      el('a', { class: 'marca', href: '#/novo' }, el('img', { src: 'img/icone.svg', alt: '' }), el('b', { texto: 'Clave' })),
      el('button', { class: 'icone-botao', type: 'button', title: 'Recolher a barra (Ctrl+B)', 'aria-label': 'Recolher a barra', html: ic('painel'), onclick: alternarLateral })),
    el('div', { class: 'lateral-acoes' },
      el('button', { class: 'nova-conversa', type: 'button', onclick: () => { location.hash = '#/novo'; } },
        el('span', { html: ic('mais') }), 'Nova conversa', el('span', { class: 'atalho', texto: 'Ctrl Shift O' })),
      el('button', { class: 'nova-conversa', type: 'button', onclick: () => { location.hash = '#/code'; } },
        el('span', { html: ic('terminal') }), 'Novo trabalho no Code')),
    el('div', { class: 'navegacao' },
      el('a', { href: '#/projetos', dados: { secao: 'projetos' } }, el('span', { html: ic('camadas') }), 'Projetos'),
      el('a', { href: '#/fluxos', dados: { secao: 'fluxos' } }, el('span', { html: ic('fluxo') }), 'Fluxos e agentes'),
      el('a', { href: '#/rotinas', dados: { secao: 'rotinas' } }, el('span', { html: ic('calendario') }), 'Rotinas'),
      el('a', { href: '#/plugins', dados: { secao: 'plugins' } }, el('span', { html: ic('peca') }), 'Plugins'),
      el('a', { href: '#/aprender', dados: { secao: 'aprender' } }, el('span', { html: ic('livro') }), 'Aprender'),
      el('a', { href: '#/uso', dados: { secao: 'uso' } }, el('span', { html: ic('grafico') }), 'Uso e gasto'),
      el('a', { href: '#/precos', dados: { secao: 'precos' } }, el('span', { html: ic('etiqueta') }), 'Preços e planos')),
    el('div', { class: 'busca-lateral' }, busca),
    lista,
    tinteiro,
    el('div', { class: 'lateral-base' },
      el('a', { class: 'botao-config', href: '#/config', dados: { secao: 'config' } }, el('span', { html: ic('ajustes') }), 'Configurações'),
      seloAtualizar),
  );
  ouvir('conversas', desenharLista);
  ouvir('estado', () => { desenharTinteiro(); desenharSelo(); });
  ouvir('orcamento', desenharTinteiro);
  ouvir('atualizacao', desenharSelo);
  ouvir('rodando', desenharLista);
  desenharLista();
  desenharTinteiro();
  desenharSelo();
}

function desenharSelo() {
  const at = estado.info?.atualizacao;
  seloAtualizar.hidden = !(at && at.nova);
  if (at?.nova) seloAtualizar.title = `Versão ${at.ultima} disponível`;
}

function desenharTinteiro() {
  const o = estado.info?.orcamento;
  if (!o) return;
  const pct = o.teto ? Math.min(100, o.porcentagem) : 0;
  tinteiro.classList.toggle('alerta', pct >= 80 && pct < 100);
  tinteiro.classList.toggle('cheio', pct >= 100);
  const vidro = el('div', { class: 'tinteiro-vidro' }, el('div', { class: 'tinteiro-tinta', style: `width:${pct}%` }));
  tinteiro.replaceChildren(
    el('div', { class: 'tinteiro-linha' },
      el('span', { class: 'tinteiro-valor', texto: usd(o.gasto, 2) }),
      el('span', { class: 'tinteiro-teto', texto: o.teto ? `de ${usd(o.teto, 0)}` : 'sem teto' })),
    vidro,
    el('div', { class: 'tinteiro-rodape', texto: o.teto ? `${pct.toFixed(0)}% do mês · zera em ${dataBr(proximoDia(o.fim))}` : 'Defina um teto em Configurações' }));
}

function proximoDia(iso) {
  const d = new Date(iso + 'T12:00:00');
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

function desenharLista() {
  if (!lista) return;
  const conversas = estado.conversas || [];
  if (!conversas.length) {
    lista.replaceChildren(el('div', { class: 'grupo-titulo', texto: estado.busca ? 'Nada encontrado' : 'Nenhuma conversa ainda' }));
    return;
  }
  const grupos = new Map();
  for (const c of conversas) {
    const g = c.fixada ? 'Fixadas' : grupoData(c.atualizada_em);
    if (!grupos.has(g)) grupos.set(g, []);
    grupos.get(g).push(c);
  }
  const filhos = [];
  for (const [nome, itens] of grupos) {
    filhos.push(el('div', { class: 'grupo-titulo', texto: nome }));
    for (const c of itens) filhos.push(itemConversa(c));
  }
  lista.replaceChildren(...filhos);
  marcarAtual();
}

function itemConversa(c) {
  const mais = el('button', { class: 'icone-botao mais', type: 'button', 'aria-label': 'Opções da conversa', html: ic('pontos') });
  const a = el('a', { class: 'item-conversa', href: `#/c/${c.id}`, dados: { id: c.id }, title: c.titulo || 'Conversa sem título' },
    el('span', { class: 'marcador-modo', html: ic(c.modo === 'code' ? 'terminal' : 'chat') }),
    el('span', { class: 'nome', texto: c.titulo || 'Nova conversa' }),
    estado.rodando.has(c.id) ? el('span', { class: 'rodando', title: 'Respondendo' }) : null,
    mais);
  mais.addEventListener('click', (e) => {
    e.preventDefault(); e.stopPropagation();
    menuConversa(mais, c);
  });
  return a;
}

export function menuConversa(ancora, c, { aoApagar } = {}) {
  menu(ancora, [
    { texto: c.fixada ? 'Desafixar' : 'Fixar no topo', icone: 'alfinete', acao: async () => { await api(`/conversas/${c.id}`, { metodo: 'PATCH', corpo: { fixada: !c.fixada } }); avisar('conversas-mudaram'); } },
    { texto: 'Renomear', icone: 'lapis', acao: async () => {
      const t = await perguntarTexto('Renomear conversa', { valor: c.titulo || '' });
      if (t) { await api(`/conversas/${c.id}`, { metodo: 'PATCH', corpo: { titulo: t } }); avisar('conversas-mudaram'); avisar('titulo', { id: c.id, titulo: t }); }
    } },
    { texto: 'Exportar em Markdown', icone: 'baixar', acao: () => { location.href = `/api/conversas/${c.id}/exportar`; } },
    '-',
    { texto: 'Apagar', icone: 'lixo', acao: async () => {
      if (!await confirmar(`Apagar "${c.titulo || 'esta conversa'}"? Não dá para desfazer.`, { titulo: 'Apagar conversa', sim: 'Apagar', perigo: true })) return;
      try {
        await api(`/conversas/${c.id}`, { metodo: 'DELETE' });
        avisar('conversas-mudaram');
        if (estado.conversaAtual === c.id) location.hash = '#/novo';
        aoApagar?.();
      } catch (e) { aviso(e.message, 'erro'); }
    } },
  ], { alinhar: 'direita' });
}

export function marcarAtual() {
  if (!raiz) return;
  const h = location.hash;
  raiz.querySelectorAll('.item-conversa').forEach((a) => {
    if (a.dataset.id === estado.conversaAtual && h.startsWith('#/c/')) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
  raiz.querySelectorAll('[data-secao]').forEach((a) => {
    if (h.startsWith(`#/${a.dataset.secao}`)) a.setAttribute('aria-current', 'page');
    else a.removeAttribute('aria-current');
  });
}
