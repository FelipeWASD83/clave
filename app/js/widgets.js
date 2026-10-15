// Widgets: os cartões visuais que o Claude desenha na conversa (produtos, mapa, recomendações, desenho, gráfico,
// comparação, linha do tempo e checklist). renderizarWidget devolve o cartão pronto; textoDoWidget, a versão em
// texto (o "Copiar como texto"); widgetPorId busca um widget salvo e mostra "carregando" enquanto isso.
import { api } from './api.js';
import { ic } from './icones.js';
import { el, esc, aviso, janela, copiarTexto, menu } from './ui.js';
import { t, localidade } from './i18n.js';
import { cfg } from './estado.js';

const SVGNS = 'http://www.w3.org/2000/svg';
const ORDEM_CORES = ['acao', 'laranja', 'roxo', 'verde', 'vermelho', 'azul', 'amarelo', 'rosa', 'marrom', 'cinza'];

// ícones próprios, no mesmo traço dos de icones.js
const P = {
  mapa: '<path d="M9 4 3.5 6v14L9 18l6 2 5.5-2V4L15 6z"/><path d="M9 4v14M15 6v14"/>',
  planta: '<rect x="3.5" y="3.5" width="17" height="17" rx="1"/><path d="M3.5 12h7v8.5M14 3.5v6h6.5M10.5 15.5h3"/>',
  colunas: '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M9.5 4.5v15M15 4.5v15"/>',
  tempo: '<path d="M7 3.5v17"/><circle cx="7" cy="7" r="2"/><circle cx="7" cy="17" r="2"/><path d="M11 7h9M11 17h6"/>',
  tela_cheia: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
  zoom_mais: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M8 11h6M11 8v6"/>',
  zoom_menos: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5M8 11h6"/>',
  ajustar: '<path d="M4 9V5a1 1 0 0 1 1-1h4M15 4h4a1 1 0 0 1 1 1v4M20 15v4a1 1 0 0 1-1 1h-4M9 20H5a1 1 0 0 1-1-1v-4"/><rect x="8.5" y="8.5" width="7" height="7" rx="1"/>',
  tv: '<rect x="3" y="6.5" width="18" height="12" rx="2"/><path d="M8.5 3l3.5 3.5L15.5 3"/>',
  filme: '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M7.5 4.5v15M16.5 4.5v15M3.5 9.5h4M3.5 14.5h4M16.5 9.5h4M16.5 14.5h4"/>',
  jogo: '<path d="M7.5 8h9a4.5 4.5 0 0 1 4.3 5.8l-.9 3a2.4 2.4 0 0 1-4 1L14 16h-4l-1.9 1.8a2.4 2.4 0 0 1-4-1l-.9-3A4.5 4.5 0 0 1 7.5 8z"/><path d="M8 11v3M6.5 12.5h3M15.5 12h.01M17.5 13.5h.01"/>',
  musica: '<path d="M9 18V5.5l11-2V16"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
  microfone: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/>',
  pino: '<path d="M12 21s-6.5-6.2-6.5-11a6.5 6.5 0 0 1 13 0c0 4.8-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
};
function icone(nome) {
  return P[nome] ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[nome]}</svg>` : ic(nome);
}

const ICONE_TIPO = { produtos: 'etiqueta', mapa: 'mapa', recomendacoes: 'estrela', desenho: 'planta', grafico: 'grafico', comparacao: 'colunas', linha_do_tempo: 'tempo', checklist: 'feito' };
// A linha "Mostrou um widget" da conversa desenha o ícone com o ic() de icones.js, que não tem os ícones próprios
// daqui (mapa, planta, colunas, tempo): para esses vai o parecido de lá; os outros são os mesmos do cartão.
const ICONE_FERRAMENTA = { ...ICONE_TIPO, mapa: 'globo', desenho: 'lapis', comparacao: 'painel', linha_do_tempo: 'relogio' };
export function iconeDaFerramenta(tipo) {
  return ICONE_FERRAMENTA[tipo] || 'grafico';
}
const ICONE_RECOMENDACAO = { serie: 'tv', filme: 'filme', jogo: 'jogo', anime: 'faisca', livro: 'livro', musica: 'musica', podcast: 'microfone', outro: 'estrela' };

function nomeTipo(tipo) {
  return {
    produtos: t('Produtos'), mapa: t('Mapa'), recomendacoes: t('Recomendações'), desenho: t('Desenho'), grafico: t('Gráfico'),
    comparacao: t('Comparação'), linha_do_tempo: t('Linha do tempo'), checklist: t('Checklist'),
  }[tipo] || tipo;
}
function nomeRecomendacao(tipo) {
  return {
    serie: t('Série'), filme: t('Filme'), jogo: t('Jogo'), anime: t('Anime'), livro: t('Livro'), musica: t('Música'),
    podcast: t('Podcast'), outro: t('Indicação'),
  }[tipo] || t('Indicação');
}
function rotuloOnde(tipo) {
  if (tipo === 'jogo') return t('Onde jogar');
  if (tipo === 'livro') return t('Onde ler');
  if (tipo === 'musica' || tipo === 'podcast') return t('Onde ouvir');
  if (tipo === 'outro') return t('Onde encontrar');
  return t('Onde ver');
}
function nomeCor(cor) {
  return {
    acao: t('Verde-petróleo'), azul: t('Azul'), verde: t('Verde'), vermelho: t('Vermelho'), laranja: t('Laranja'), amarelo: t('Amarelo'),
    roxo: t('Roxo'), rosa: t('Rosa'), marrom: t('Marrom'), cinza: t('Cinza'), preto: t('Preto'),
  }[cor] || cor;
}
function nomeForma(tipo) {
  return {
    retangulo: t('Retângulo'), circulo: t('Círculo'), linha: t('Linha'), seta: t('Seta'), texto: t('Texto'), poligono: t('Polígono'), cota: t('Cota'),
  }[tipo] || tipo;
}

const corVar = (cor) => `var(--w-${ORDEM_CORES.includes(cor) || cor === 'preto' ? cor : 'acao'})`;
const reduzMovimento = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- formatação ----------
function fmtNumero(n, casas = 2) {
  return Number(n).toLocaleString(localidade(), { maximumFractionDigits: casas });
}
function fmtPreco(valor, moeda) {
  try { return new Intl.NumberFormat(localidade(), { style: 'currency', currency: moeda || 'BRL' }).format(valor); }
  catch { return `${moeda || ''} ${fmtNumero(valor)}`.trim(); }
}
function fmtData(s) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(String(s || ''))) return new Date(`${s}T12:00:00`).toLocaleDateString(localidade());
  return String(s || '');
}
function fmtValor(v, unidade, compacto = false) {
  if (v === null || v === undefined) return t('sem dado');
  const n = compacto && Math.abs(v) >= 10000
    ? new Intl.NumberFormat(localidade(), { notation: 'compact', maximumFractionDigits: 1 }).format(v)
    : fmtNumero(v);
  if (!unidade) return n;
  if (/^(R\$|US\$|\$|€|£|¥)$/.test(unidade)) return `${unidade} ${n}`;
  if (unidade === '%') return `${n}%`;
  return `${n} ${unidade}`;
}
// a nota com a escala que veio ("8/10" fica 8/10, nunca 8 estrelas); sem escala, até 5 é estrela
function valorNota(nota) {
  return nota.escala ? `${fmtNumero(nota.valor, 1)}/${fmtNumero(nota.escala, 1)}` : fmtNumero(nota.valor, 1);
}
function fmtNota(nota) {
  if (!nota) return '';
  const estrela = nota.escala ? nota.escala <= 5 : nota.valor <= 5;
  return estrela ? `★ ${valorNota(nota)}` : valorNota(nota);
}
function fmtMedida(v, unidade) { return `${fmtNumero(v, 2)} ${unidade}`; }
function fmtPar(x, y) { return t('({x}; {y})', { x: fmtNumero(x, 2), y: fmtNumero(y, 2) }); }

function abrirFora(url) {
  if (!/^https?:\/\//.test(String(url || ''))) return;
  if (window.clave?.abrirExterno) window.clave.abrirExterno(url);
  else window.open(url, '_blank', 'noopener');
}
const urlOsm = (p) => `https://www.openstreetmap.org/?mlat=${p.lat}&mlon=${p.lon}#map=17/${p.lat}/${p.lon}`;

function hash(texto) {
  let h = 2166136261;
  for (const ch of String(texto || '')) { h ^= ch.codePointAt(0); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

let sequencia = 0;
const novoId = (prefixo) => `${prefixo}-${++sequencia}`;

function s(tag, attrs = {}, ...filhos) {
  const e = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'texto') e.textContent = v;
    else if (k === 'dados') Object.assign(e.dataset, v);
    else if (k.startsWith('on') && typeof v === 'function') e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const f of filhos.flat()) if (f) e.append(f);
  return e;
}

function botaoIcone(nomeIcone, rotulo, acao, extra = {}) {
  return el('button', { class: 'icone-botao', type: 'button', title: rotulo, 'aria-label': rotulo, html: icone(nomeIcone), onclick: (e) => acao(e.currentTarget), ...extra });
}

// ---------- o cartão ----------
const DESENHAR = {
  produtos: desenharProdutos, mapa: desenharMapa, recomendacoes: desenharRecomendacoes, desenho: desenharDesenho,
  grafico: desenharGrafico, comparacao: desenharComparacao, linha_do_tempo: desenharLinhaDoTempo, checklist: desenharChecklist,
};

function cartaoErro(mensagem) {
  return el('div', { class: 'widget widget-falhou', role: 'alert' },
    el('span', { class: 'widget-icone', html: ic('alerta') }), el('span', { texto: mensagem }));
}

export function renderizarWidget(widget, { id = '', cheia = false } = {}) {
  if (widget && widget.widget && !widget.tipo) widget = widget.widget;
  if (!widget || !DESENHAR[widget.tipo] || !widget.dados || typeof widget.dados !== 'object') return cartaoErro(t('Este widget não pôde ser mostrado.'));
  const titulo = widget.titulo || nomeTipo(widget.tipo);
  const corpo = el('div', { class: 'widget-corpo' });
  const acoes = el('div', { class: 'widget-acoes' });
  const cartao = el('div', { class: `widget widget-de-${widget.tipo}${cheia ? ' widget-cheio' : ''}`, role: 'group', 'aria-label': `${nomeTipo(widget.tipo)}: ${titulo}`, dados: { widgetId: id || '' } },
    el('header', { class: 'widget-topo' },
      el('span', { class: 'widget-icone', html: icone(ICONE_TIPO[widget.tipo]) }),
      el('div', { class: 'widget-titulos' }, el('span', { class: 'widget-tipo', texto: nomeTipo(widget.tipo) }), el('h3', { class: 'widget-titulo', texto: titulo })),
      acoes),
    corpo);
  const ctx = { id, cheia, widget, cartao, corpo, exportar: null };
  try {
    DESENHAR[widget.tipo](corpo, widget.dados, ctx);
  } catch (e) {
    console.error(e);
    corpo.replaceChildren(el('p', { class: 'widget-erro', texto: t('Este widget não pôde ser mostrado.') }));
  }
  if (ctx.exportar) {
    acoes.append(botaoIcone('baixar', t('Baixar imagem'), (b) => menu(b, [
      { texto: t('Imagem PNG'), sub: t('Para mandar ou colar em documentos'), icone: 'imagem', acao: () => baixarImagem(ctx, 'png') },
      { texto: t('Desenho SVG'), sub: t('Dá para ampliar sem perder qualidade'), icone: 'arquivo', acao: () => baixarImagem(ctx, 'svg') },
    ], { alinhar: 'direita' }), { 'aria-haspopup': 'menu' }));
  }
  acoes.append(botaoIcone('copiar', t('Copiar como texto'), (b) => copiarTexto(textoDoWidget(widget), b)));
  if (!cheia) acoes.append(botaoIcone('tela_cheia', t('Tela cheia'), () => abrirTelaCheia(widget, id)));
  return cartao;
}

// Os widgets já buscados ficam um minuto na memória: a conversa redesenha tudo a cada resposta, e sem isso cada
// redesenho pedia de novo cada widget ao servidor. Guarda a promessa (pedidos ao mesmo tempo viram um só) e o objeto
// é o mesmo para todas as cópias, então o que o checklist marca já vale para o próximo redesenho.
const VALIDADE_CACHE = 60_000;
const MAX_CACHE = 300;
const cacheWidgets = new Map(); // id -> { ate, promessa }
function buscarWidget(id) {
  const agora = Date.now();
  const achado = cacheWidgets.get(id);
  if (achado && achado.ate > agora) return achado.promessa;
  const promessa = api(`/widgets/${encodeURIComponent(id)}`);
  cacheWidgets.delete(id);
  cacheWidgets.set(id, { ate: agora + VALIDADE_CACHE, promessa });
  promessa.catch(() => { if (cacheWidgets.get(id)?.promessa === promessa) cacheWidgets.delete(id); });
  if (cacheWidgets.size > MAX_CACHE) {
    for (const [k, v] of cacheWidgets) if (v.ate <= agora) cacheWidgets.delete(k);
    for (const k of cacheWidgets.keys()) { if (cacheWidgets.size <= MAX_CACHE) break; cacheWidgets.delete(k); }
  }
  return promessa;
}
// Um widget que acabou de chegar (o evento "widget" da resposta ou o que o servidor devolveu ao salvar o checklist)
// entra no cache, para o redesenho seguinte não pedir de novo nem mostrar uma versão velha.
export function lembrarWidget(id, widget) {
  if (!id || !widget) return;
  cacheWidgets.delete(id);
  cacheWidgets.set(id, { ate: Date.now() + VALIDADE_CACHE, promessa: Promise.resolve(widget) });
}

// Um widget salvo (GET /api/widgets/<id>): mostra "carregando" e troca pelo cartão (ou por um aviso de erro).
export function widgetPorId(id) {
  const lugar = el('div', { class: 'widget widget-carregando', role: 'status' },
    el('span', { class: 'widget-girando', 'aria-hidden': 'true' }), el('span', { texto: t('Carregando o widget…') }));
  buscarWidget(id)
    .then((w) => lugar.replaceWith(renderizarWidget(w, { id })))
    .catch((e) => lugar.replaceWith(cartaoErro(e.status === 404 ? t('Este widget não existe mais.') : t('Não deu para carregar o widget: {erro}', { erro: e.message }))));
  return lugar;
}

function abrirTelaCheia(widget, id) {
  janela({ titulo: widget.titulo || nomeTipo(widget.tipo), corpo: renderizarWidget(widget, { id, cheia: true }), larga: true, classe: 'janela-widget' });
}

// ---------- baixar como imagem (desenho e gráfico) ----------
const PROPS_SVG = ['fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity', 'stroke-dasharray', 'stroke-linecap',
  'stroke-linejoin', 'opacity', 'font-family', 'font-size', 'font-weight', 'text-anchor', 'dominant-baseline', 'paint-order',
  'vector-effect', 'display'];

function svgParaArquivo(svg, viewBox, largura, altura, fundo) {
  const copia = svg.cloneNode(true);
  const originais = [svg, ...svg.querySelectorAll('*')];
  const novos = [copia, ...copia.querySelectorAll('*')];
  originais.forEach((o, i) => {
    const n = novos[i];
    const cs = getComputedStyle(o);
    for (const p of PROPS_SVG) {
      const v = cs.getPropertyValue(p);
      if (v && v !== 'normal' && !(p === 'display' && v !== 'none')) n.setAttribute(p, v);
    }
    for (const a of ['class', 'style', 'tabindex', 'role', 'aria-label', 'focusable']) n.removeAttribute(a);
  });
  copia.querySelectorAll('[data-exportar="nao"], [display="none"]').forEach((x) => x.remove());
  copia.setAttribute('xmlns', SVGNS);
  copia.setAttribute('viewBox', viewBox.join(' '));
  copia.setAttribute('width', String(Math.round(largura)));
  copia.setAttribute('height', String(Math.round(altura)));
  copia.insertBefore(s('rect', { x: viewBox[0], y: viewBox[1], width: viewBox[2], height: viewBox[3], fill: fundo }), copia.firstChild);
  return new XMLSerializer().serializeToString(copia);
}

function nomeArquivo(titulo, ext) {
  const base = String(titulo || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '-').toLowerCase().slice(0, 60);
  return `${base || 'widget'}.${ext}`;
}

function baixarBlob(blob, nome) {
  const a = el('a', { href: URL.createObjectURL(blob), download: nome });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}

// A imagem baixada leva o título em cima e a legenda embaixo (sem elas, uma pizza vira só porcentagens soltas).
// É montada num SVG escondido dentro do cartão, para as cores do tema valerem na hora de copiar os estilos.
function montarExportacao(ctx, { svg, viewBox, largura, altura }) {
  const itens = ctx.legendaExportar ? ctx.legendaExportar() : [];
  const W = Math.max(Math.round(largura), 420);
  const topo = 46;
  let x = 16, linha = 0;
  const lugares = itens.map((it) => {
    const w = String(it.texto).length * 7.2 + (it.cor ? 30 : 16);
    if (x + w > W - 16 && x > 16) { x = 16; linha++; }
    const lugar = [x, linha];
    x += w;
    return lugar;
  });
  const alturaLegenda = itens.length ? (linha + 1) * 22 + 10 : 0;
  const total = Math.round(topo + altura + alturaLegenda + 10);
  const raiz = s('svg', { viewBox: `0 0 ${W} ${total}`, width: W, height: total });
  raiz.append(s('text', { class: 'w-exp-titulo', x: 16, y: 29, texto: ctx.widget.titulo || nomeTipo(ctx.widget.tipo) }));
  const interno = svg.cloneNode(true);
  interno.removeAttribute('class');
  for (const [k, v] of Object.entries({ x: (W - largura) / 2, y: topo, width: largura, height: altura, viewBox: viewBox.join(' ') })) interno.setAttribute(k, v);
  raiz.append(interno);
  itens.forEach((it, i) => {
    const [lx, ln] = lugares[i];
    const ly = topo + altura + 18 + ln * 22;
    if (it.cor) raiz.append(s('rect', { x: lx, y: ly - 6, width: 11, height: 11, rx: 3, style: `fill: ${corVar(it.cor)}` }));
    raiz.append(s('text', { class: 'w-exp-legenda', x: lx + (it.cor ? 17 : 0), y: ly, 'dominant-baseline': 'central', texto: it.texto }));
  });
  const fora = el('div', { class: 'widget-exportando', 'aria-hidden': 'true' }, raiz);
  ctx.cartao.append(fora);
  return { svg: raiz, viewBox: [0, 0, W, total], largura: W, altura: total, limpar: () => fora.remove() };
}

async function baixarImagem(ctx, formato) {
  try {
    const montado = montarExportacao(ctx, ctx.exportar());
    const { viewBox, largura, altura } = montado;
    const fundo = getComputedStyle(ctx.cartao).getPropertyValue('--papel').trim() || '#ffffff';
    let texto;
    try { texto = svgParaArquivo(montado.svg, viewBox, largura, altura, fundo); } finally { montado.limpar(); }
    if (formato === 'svg') { baixarBlob(new Blob([texto], { type: 'image/svg+xml' }), nomeArquivo(ctx.widget.titulo, 'svg')); return; }
    const url = URL.createObjectURL(new Blob([texto], { type: 'image/svg+xml' }));
    try {
      const img = new Image();
      await new Promise((ok, falha) => { img.onload = ok; img.onerror = falha; img.src = url; });
      const escala = 2;
      const tela = document.createElement('canvas');
      tela.width = Math.round(largura * escala); tela.height = Math.round(altura * escala);
      const c2 = tela.getContext('2d');
      c2.scale(escala, escala);
      c2.drawImage(img, 0, 0, largura, altura);
      const blob = await new Promise((ok) => tela.toBlob(ok, 'image/png'));
      if (!blob) throw new Error('png');
      baixarBlob(blob, nomeArquivo(ctx.widget.titulo, 'png'));
    } finally { URL.revokeObjectURL(url); }
  } catch (e) {
    console.error(e);
    aviso(t('Não deu para gerar a imagem.'), 'erro');
  }
}

// ---------- imagens de fora (produtos e recomendações) ----------
// Nunca carregam sozinhas: buscar a foto avisa o site de onde ela vem. Só com o clique em "Mostrar imagens de
// loja.com e outra.com" (o botão diz de quais sites), ou sempre, se quem usa escolheu isso nas Configurações
// (widgets_imagens = "sempre").
function sitesDe(urls) {
  const sites = [];
  for (const u of urls) {
    try {
      const host = new URL(u).hostname.replace(/^www\./, '');
      if (host && !sites.includes(host)) sites.push(host);
    } catch { /* endereço que não abre: não entra na lista */ }
  }
  return sites;
}
function listaDeSites(sites) {
  const nomes = sites.length > 3 ? [...sites.slice(0, 2), t('mais {n} sites', { n: sites.length - 2 })] : sites;
  try { return new Intl.ListFormat(localidade(), { type: 'conjunction' }).format(nomes); } catch { return nomes.join(', '); }
}

function controleImagens(urls) {
  const vagas = new Set();
  const sites = sitesDe(urls);
  const temImagens = urls.length > 0;
  let ligadas = cfg().widgets_imagens === 'sempre';
  const carregar = (vaga) => {
    if (vaga.dataset.carregada) return;
    vaga.dataset.carregada = '1';
    vaga.classList.add('carregando');
    const img = el('img', { alt: vaga.dataset.alt || '', loading: 'lazy', decoding: 'async', src: `/api/widgets/imagem?url=${encodeURIComponent(vaga.dataset.url)}` });
    img.addEventListener('load', () => { vaga.classList.remove('carregando'); vaga.classList.add('com-imagem'); });
    img.addEventListener('error', () => {
      img.remove();
      vaga.classList.remove('carregando');
      vaga.classList.add('sem-imagem');
      vaga.title = t('A imagem não pôde ser carregada.');
    });
    vaga.append(img);
  };
  const rotulo = sites.length ? t('Mostrar imagens de {sites}', { sites: listaDeSites(sites) }) : t('Mostrar imagens');
  const botao = temImagens && !ligadas ? el('button', {
    class: 'botao pequeno widget-botao-imagens', type: 'button',
    title: `${t('As fotos vêm de sites de fora. Elas só carregam quando você pede, porque buscar a foto avisa o site de onde ela vem.')}${sites.length ? `\n${sites.join(', ')}` : ''}`,
    html: `${ic('imagem')}<span>${esc(rotulo)}</span>`,
    onclick: () => { ligadas = true; botao.remove(); vagas.forEach((v) => { if (v.isConnected) carregar(v); }); },
  }) : null;
  return {
    botao,
    vaga(url, alt, conteudo) {
      const v = el('div', { class: 'widget-imagem', dados: { url, alt } }, conteudo || el('span', { class: 'widget-imagem-vazia', html: ic('imagem') }));
      vagas.add(v);
      if (ligadas) carregar(v);
      return v;
    },
  };
}

// ---------- produtos ----------
function desenharProdutos(corpo, d, ctx) {
  const itens = (d.itens || []).map((it, i) => ({ ...it, i }));
  const contagem = {};
  itens.forEach((it) => { contagem[it.moeda] = (contagem[it.moeda] || 0) + 1; });
  const moeda = Object.entries(contagem).sort((a, b) => b[1] - a[1])[0]?.[0] || 'BRL';
  const comparaveis = itens.filter((it) => it.moeda === moeda);
  const menor = Math.min(...comparaveis.map((it) => it.preco));
  const imagens = controleImagens(itens.map((it) => it.imagem).filter(Boolean));
  const lista = el('ul', { class: 'widget-produtos', role: 'list', style: `--itens: ${itens.length}` });
  let ordem = 'preco';

  // Todos os cartões têm as mesmas faixas (foto, nome, preço, detalhes, link) e dividem as linhas da grade (subgrid):
  // o preço fica na mesma altura em todos, mesmo com o selo "Mais barato" ou um nome de três linhas ao lado.
  const temImagem = itens.some((it) => it.imagem);
  const temDetalhes = itens.some((it) => it.loja || it.nota || it.observacao);
  const temLink = itens.some((it) => it.link);
  const faixas = 2 + temImagem + temDetalhes + temLink;
  const cartaoProduto = (it) => {
    const barato = comparaveis.length > 1 && it.moeda === moeda && it.preco === menor;
    const loja = [it.loja, it.nota ? `${fmtNota(it.nota)}${it.nota.fonte ? ` (${it.nota.fonte})` : ''}` : ''].filter(Boolean).join(' · ');
    const semFoto = () => el('div', { class: 'widget-imagem sem-imagem', 'aria-hidden': 'true' }, el('span', { class: 'widget-imagem-vazia', html: ic('imagem') }));
    return el('li', { class: `widget-produto${barato ? ' mais-barato' : ''}`, style: `--faixas: ${faixas}` },
      temImagem ? (it.imagem ? imagens.vaga(it.imagem, it.nome) : semFoto()) : null,
      el('div', { class: 'widget-produto-nome' },
        barato ? el('span', { class: 'etiqueta acao', texto: t('Mais barato') }) : null,
        el('h4', { texto: it.nome })),
      el('p', { class: 'widget-preco', texto: fmtPreco(it.preco, it.moeda) }),
      temDetalhes ? el('div', { class: 'widget-produto-detalhes' },
        loja ? el('p', { class: 'widget-loja', texto: loja }) : null,
        it.observacao ? el('p', { class: 'widget-obs', texto: it.observacao }) : null) : null,
      temLink ? (it.link ? el('button', { class: 'botao pequeno widget-produto-link', type: 'button', title: it.link, html: `${ic('externo')}<span>${esc(t('Ver na loja'))}</span>`, onclick: () => abrirFora(it.link) }) : el('span')) : null);
  };
  const desenhar = () => {
    const ordenados = ordem === 'preco'
      ? [...itens].sort((a, b) => (a.moeda === b.moeda ? a.preco - b.preco : a.moeda === moeda ? -1 : b.moeda === moeda ? 1 : a.i - b.i))
      : itens;
    lista.replaceChildren(...ordenados.map(cartaoProduto));
  };
  const botaoOrdem = (valor, rotulo) => el('button', {
    type: 'button', 'aria-pressed': String(ordem === valor), texto: rotulo,
    onclick: (e) => { ordem = valor; e.currentTarget.parentElement.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b === e.currentTarget))); desenhar(); },
  });
  const barra = el('div', { class: 'widget-barra' },
    itens.length > 1 ? el('div', { class: 'segmentado', role: 'group', 'aria-label': t('Ordenar') }, botaoOrdem('preco', t('Menor preço')), botaoOrdem('original', t('Ordem original'))) : null,
    el('span', { class: 'espaco' }), imagens.botao);
  desenhar();
  corpo.append(barra.childElementCount > 1 ? barra : '', lista,
    el('p', { class: 'widget-nota', html: `${ic('info')}<span>${esc(t('Preços vistos em {data}; confira na loja.', { data: fmtData(d.visto_em) }))}</span>` }));
}

// ---------- mapa ----------
let leaflet = null;
function carregarLeaflet() {
  if (!leaflet) {
    const css = new Promise((ok) => {
      if (document.getElementById('clave-leaflet-css')) { ok(); return; }
      const link = el('link', { id: 'clave-leaflet-css', rel: 'stylesheet', href: new URL('../vendor/leaflet/leaflet.css', import.meta.url).href });
      link.addEventListener('load', ok); link.addEventListener('error', ok);
      setTimeout(ok, 3000);
      document.head.append(link);
    });
    leaflet = Promise.all([import('../vendor/leaflet/leaflet-src.esm.js'), css]).then(([L]) => L)
      .catch((e) => { leaflet = null; throw e; });
  }
  return leaflet;
}

function motivoFora(motivo) {
  if (motivo === 'limite') return t('passou do limite de endereços por mapa');
  if (motivo === 'sem_conexao') return t('sem conexão com o serviço de endereços');
  return t('endereço não encontrado');
}

function desenharMapa(corpo, d, ctx) {
  const pontos = d.pontos || [];
  const area = el('div', { class: 'widget-mapa-area' });
  const estadoMapa = el('div', { class: 'widget-mapa-estado', role: 'status' }, el('span', { class: 'widget-girando', 'aria-hidden': 'true' }), el('span', { texto: t('Carregando o mapa…') }));
  const dica = el('div', { class: 'widget-mapa-dica', 'aria-hidden': 'true', texto: t('Clique no mapa para dar zoom com a roda do mouse') });
  area.append(estadoMapa, dica);
  const itensLista = [];
  const lista = el('ol', { class: 'widget-mapa-lista', 'aria-label': t('Pontos do mapa') });
  let mapa = null;
  const marcadores = [];
  let iniciado = false;

  const marcarAtivo = (i) => itensLista.forEach((li, j) => li.classList.toggle('ativo', j === i));
  const focarPonto = (i) => {
    marcarAtivo(i);
    if (!mapa) return;
    const m = marcadores[i];
    const zoom = Math.max(mapa.getZoom(), 15);
    // o balão abre depois do voo: aberto no meio dele, ficava cortado na borda do mapa
    const abrir = () => { mapa.off('moveend', abrir); m.openPopup(); };
    mapa.on('moveend', abrir);
    if (reduzMovimento()) mapa.setView(m.getLatLng(), zoom, { animate: false });
    else mapa.flyTo(m.getLatLng(), zoom, { duration: 0.6 });
    setTimeout(() => { if (!m.isPopupOpen()) abrir(); }, 900);
  };
  pontos.forEach((p, i) => {
    const li = el('li', {},
      el('button', { class: 'widget-mapa-ponto', type: 'button', title: t('Mostrar no mapa'), onclick: () => focarPonto(i) },
        el('span', { class: 'widget-num', texto: String(i + 1) }),
        el('span', { class: 'widget-mapa-textos' }, el('b', { texto: p.nome }), p.descricao ? el('small', { texto: p.descricao }) : null)),
      botaoIcone('externo', t('Abrir {nome} no OpenStreetMap', { nome: p.nome }), () => abrirFora(urlOsm(p))));
    itensLista.push(li);
    lista.append(li);
  });
  corpo.append(el('div', { class: 'widget-mapa' }, area, lista));
  if (d.rota) corpo.append(el('p', { class: 'widget-nota', html: `${icone('pino')}<span>${esc(t('A linha liga os pontos na ordem da lista.'))}</span>` }));
  // os pontos que não entraram aparecem para quem usa também, não só no resultado que o Claude lê
  if (d.fora?.length) {
    corpo.append(el('div', { class: 'widget-mapa-fora', role: 'note' },
      el('p', { class: 'widget-nota', html: `${ic('alerta')}<span>${esc(t('Ficaram de fora do mapa:'))}</span>` }),
      el('ul', {}, ...d.fora.map((f) => el('li', {}, el('b', { texto: f.nome }), ` (${motivoFora(f.motivo)})`)))));
  }

  // links da atribuição (OpenStreetMap, Leaflet) abrem fora do app
  area.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="http"]');
    if (a && area.contains(a)) { e.preventDefault(); abrirFora(a.href); }
  });
  let tempoDica = 0;
  area.addEventListener('wheel', () => {
    if (!mapa || ctx.cheia || mapa.scrollWheelZoom.enabled()) return;
    dica.classList.add('visivel');
    clearTimeout(tempoDica);
    tempoDica = setTimeout(() => dica.classList.remove('visivel'), 1600);
  }, { passive: true });
  area.addEventListener('mouseleave', () => { if (mapa && !ctx.cheia) mapa.scrollWheelZoom.disable(); });

  const enquadrar = () => {
    const latlngs = pontos.map((p) => [p.lat, p.lon]);
    if (latlngs.length === 1) mapa.setView(latlngs[0], 15, { animate: false });
    else mapa.fitBounds(latlngs, { padding: [32, 32], maxZoom: 16, animate: false });
  };

  async function iniciar() {
    let L;
    try { L = await carregarLeaflet(); }
    catch (e) {
      console.error(e);
      estadoMapa.replaceChildren(el('span', { html: ic('alerta') }), el('span', { texto: t('Não deu para abrir o mapa. A lista de pontos continua aqui ao lado.') }));
      estadoMapa.classList.add('erro');
      return;
    }
    estadoMapa.remove();
    const reduz = reduzMovimento();
    mapa = L.map(area, {
      zoomControl: true, attributionControl: false, scrollWheelZoom: !!ctx.cheia, keyboard: true, maxZoom: 19,
      zoomAnimation: !reduz, fadeAnimation: !reduz, markerZoomAnimation: !reduz, inertia: !reduz,
    });
    L.control.attribution({ prefix: '<a href="https://leafletjs.com">Leaflet</a>' }).addTo(mapa);
    L.tileLayer('/api/mapa/tile/{z}/{x}/{y}', {
      maxZoom: 19, keepBuffer: 1,
      attribution: '<a href="https://www.openstreetmap.org/copyright">© OpenStreetMap</a>',
    }).addTo(mapa);
    pontos.forEach((p, i) => {
      const marcador = L.marker([p.lat, p.lon], {
        title: p.nome, alt: p.nome, keyboard: true, riseOnHover: true,
        icon: L.divIcon({ className: 'widget-marcador', html: `<span>${i + 1}</span>`, iconSize: [30, 34], iconAnchor: [15, 31], popupAnchor: [0, -28] }),
      }).addTo(mapa);
      marcador.bindPopup(el('div', { class: 'widget-popup' },
        el('b', { texto: `${i + 1}. ${p.nome}` }),
        p.descricao ? el('p', { texto: p.descricao }) : null,
        p.endereco ? el('small', { texto: p.endereco }) : null,
        p.achado && p.achado !== p.endereco ? el('small', { texto: t('No mapa: {lugar}', { lugar: p.achado }) }) : null,
        el('button', { class: 'botao pequeno', type: 'button', html: `${ic('externo')}<span>${esc(t('Abrir no mapa'))}</span>`, title: t('Abre no OpenStreetMap, no navegador'), onclick: () => abrirFora(urlOsm(p)) })),
      { maxWidth: 260, autoPanPadding: [24, 24] });
      marcador.on('click', () => marcarAtivo(i));
      marcadores.push(marcador);
    });
    if (d.rota && pontos.length > 1) {
      // um contorno na cor do papel por baixo do tracejado: a linha aparece sobre qualquer rua, nos dois temas
      const caminho = pontos.map((p) => [p.lat, p.lon]);
      L.polyline(caminho, { className: 'widget-rota-fundo', weight: 7, opacity: 1, interactive: false }).addTo(mapa);
      L.polyline(caminho, { className: 'widget-rota', weight: 3, opacity: 1, interactive: false }).addTo(mapa);
    }
    mapa.on('click', () => mapa.scrollWheelZoom.enable());
    enquadrar();
    const ajustar = L.Control.extend({
      options: { position: 'topleft' },
      onAdd() {
        const caixa = L.DomUtil.create('div', 'leaflet-bar');
        const b = L.DomUtil.create('a', 'widget-mapa-ajustar', caixa);
        b.href = '#'; b.setAttribute('role', 'button'); b.title = t('Ver todos os pontos'); b.setAttribute('aria-label', t('Ver todos os pontos'));
        b.innerHTML = icone('ajustar');
        L.DomEvent.on(b, 'click', (e) => { L.DomEvent.preventDefault(e); L.DomEvent.stopPropagation(e); enquadrar(); });
        return caixa;
      },
    });
    new ajustar().addTo(mapa);
  }

  // o mapa nasce quando o cartão aparece com largura (na conversa ou na tela cheia) e se ajusta quando ela muda
  const observador = new ResizeObserver(() => requestAnimationFrame(() => {
    if (!area.isConnected || !area.clientWidth) return;
    if (!iniciado) { iniciado = true; iniciar(); }
    else if (mapa) mapa.invalidateSize({ animate: false });
  }));
  observador.observe(area);
}

// ---------- recomendações ----------
// A capa desenhada de cada item. A cor de fundo e o desenho seguem a posição do item no cartão (a partir de um ponto
// tirado do título do cartão): itens do mesmo cartão nunca saem com a mesma capa, e a capa não muda ao redesenhar.
// O fundo usa só as cores vivas (marrom e cinza, lado a lado, saíam quase iguais). No tema escuro, o fundo se mistura
// com o papel (--w-capa-forca): as cores claras do escuro são para traço e texto, não para uma área grande.
const CORES_CAPA = ['acao', 'laranja', 'roxo', 'verde', 'vermelho', 'azul', 'amarelo', 'rosa'];
const tomDeCapa = (cor) => `color-mix(in srgb, ${corVar(cor)} var(--w-capa-forca), var(--papel))`;
const tomDeTraco = (cor) => `color-mix(in srgb, ${corVar(cor)} var(--w-capa-traco), var(--papel))`;
function capa(it, i = 0, base = 0) {
  const h = hash(it.titulo);
  const c1 = CORES_CAPA[(base + i) % CORES_CAPA.length];
  let c2 = ORDEM_CORES[(h >>> 5) % ORDEM_CORES.length];
  if (c2 === c1) c2 = ORDEM_CORES[(ORDEM_CORES.indexOf(c1) + 3) % ORDEM_CORES.length];
  const desenho = ((base >>> 4) + i) % 4;
  const formas = [];
  const traco = { style: `stroke: ${tomDeTraco(c2)}`, 'stroke-width': 5, fill: 'none', opacity: 0.55 };
  if (desenho === 0) for (let k = -80; k < 120; k += 14) formas.push(s('line', { x1: k, y1: 0, x2: k + 80, y2: 80, ...traco }));
  else if (desenho === 1) for (let x = 6; x < 60; x += 12) for (let y = 6; y < 80; y += 12) formas.push(s('circle', { cx: x, cy: y, r: 2.6, style: `fill: ${tomDeTraco(c2)}`, opacity: 0.6 }));
  else if (desenho === 2) for (let r = 10; r < 90; r += 12) formas.push(s('circle', { cx: 60, cy: 80, r, ...traco, 'stroke-width': 4 }));
  else for (let y = 0; y < 100; y += 14) formas.push(s('path', { d: `M-5 ${y} l10 -8 l10 8 l10 -8 l10 8 l10 -8 l10 8 l10 -8`, ...traco, 'stroke-width': 4 }));
  const palavras = String(it.titulo).split(/\s+/).filter((p) => /[\p{L}\p{N}]/u.test(p));
  const fortes = palavras.filter((p) => p.length > 2);
  const iniciais = ((fortes.length ? fortes : palavras).slice(0, 2).map((p) => [...p.replace(/^[^\p{L}\p{N}]+/u, '')][0] || '').join('') || '?').toUpperCase();
  return el('div', { class: 'widget-capa', 'aria-hidden': 'true' },
    s('svg', { viewBox: '0 0 60 80', preserveAspectRatio: 'xMidYMid slice', class: 'widget-capa-fundo', focusable: 'false' },
      s('rect', { width: 60, height: 80, style: `fill: ${tomDeCapa(c1)}` }), ...formas),
    el('span', { class: 'widget-capa-iniciais', texto: iniciais }),
    el('span', { class: 'widget-capa-icone', html: icone(ICONE_RECOMENDACAO[it.tipo] || 'estrela') }));
}

function desenharRecomendacoes(corpo, d, ctx) {
  const itens = d.itens || [];
  const imagens = controleImagens(itens.map((it) => it.imagem).filter(Boolean));
  const base = hash(ctx?.widget?.titulo || itens.map((it) => it.titulo).join('|'));
  const lista = el('ul', { class: 'widget-recomendacoes', role: 'list' }, ...itens.map((it, i) => {
    const meta = [nomeRecomendacao(it.tipo), it.ano, it.duracao].filter(Boolean).join(' · ');
    const nota = it.nota ? `${fmtNota(it.nota)}${it.nota.fonte ? ` · ${it.nota.fonte}` : ''}` : '';
    return el('li', { class: 'widget-rec' },
      it.imagem ? imagens.vaga(it.imagem, it.titulo, capa(it, i, base)) : capa(it, i, base),
      el('div', { class: 'widget-rec-info' },
        el('h4', { texto: it.titulo }),
        el('p', { class: 'widget-rec-meta', texto: meta }),
        it.generos?.length ? el('ul', { class: 'widget-chips', 'aria-label': t('Gêneros') }, ...it.generos.map((g) => el('li', { texto: g }))) : null,
        it.onde || nota ? el('p', { class: 'widget-rec-onde' },
          it.onde ? el('span', {}, el('b', { texto: `${rotuloOnde(it.tipo)}: ` }), it.onde) : null,
          nota ? el('span', { class: 'widget-rec-nota', texto: nota }) : null) : null,
        el('p', { class: 'widget-rec-porque' }, el('b', { texto: `${t('Por que')}: ` }), it.por_que)));
  }));
  if (imagens.botao) corpo.append(el('div', { class: 'widget-barra' }, el('span', { class: 'espaco' }), imagens.botao));
  corpo.append(lista);
}

// ---------- desenho (planta, diagrama) ----------
function passoBonito(bruto) {
  const e = Math.floor(Math.log10(bruto));
  const f = bruto / 10 ** e;
  return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * 10 ** e;
}

function desenharDesenho(corpo, d, ctx) {
  const BASE = 800;
  const esc_ = BASE / Math.max(d.largura, d.altura);
  const W = d.largura * esc_, H = d.altura * esc_;
  const fonte = Math.max(W, H) / 52;
  const px = (v) => v * esc_;
  // o enquadramento cobre o desenho e tudo o que sai dele (cotas e rótulos de fora)
  const lim = [0, 0, W, H];
  const incluir = (x, y) => { lim[0] = Math.min(lim[0], x); lim[1] = Math.min(lim[1], y); lim[2] = Math.max(lim[2], x); lim[3] = Math.max(lim[3], y); };
  const incluirTexto = (x, y, texto, tam, girado = false) => {
    const meia = Math.max(String(texto).length * tam * 0.3, tam * 0.6);
    const [mx, my] = girado ? [meia, meia] : [meia, tam * 0.6];
    incluir(x - mx, y - my); incluir(x + mx, y + my);
  };
  // para que lado fica "fora": a normal da linha que se afasta do centro do desenho
  const paraFora = (x1, y1, x2, y2) => {
    const ang = Math.atan2(y2 - y1, x2 - x1);
    let nx = -Math.sin(ang), ny = Math.cos(ang);
    if (nx * ((x1 + x2) / 2 - W / 2) + ny * ((y1 + y2) / 2 - H / 2) < 0) { nx = -nx; ny = -ny; }
    return [ang, nx, ny];
  };

  const svg = s('svg', { class: 'widget-svg widget-desenho-svg', preserveAspectRatio: 'xMidYMid meet', role: 'img', 'aria-label': t('Desenho de {largura} por {altura} {unidade}', { largura: fmtNumero(d.largura), altura: fmtNumero(d.altura), unidade: d.unidade }) });
  const grade = s('g', { class: 'w-grades' });
  const passo = passoBonito(Math.max(d.largura, d.altura) / 16);
  for (let k = 1; k * passo < d.largura - 1e-9; k++) grade.append(s('line', { class: `w-grade${k % 5 === 0 ? ' forte' : ''}`, x1: px(k * passo), y1: 0, x2: px(k * passo), y2: H }));
  for (let k = 1; k * passo < d.altura - 1e-9; k++) grade.append(s('line', { class: `w-grade${k % 5 === 0 ? ' forte' : ''}`, x1: 0, y1: px(k * passo), x2: W, y2: px(k * passo) }));
  // o contorno vem antes das formas: janela e porta desenhadas na parede ficam por cima dela
  svg.append(s('rect', { class: 'w-plano', x: 0, y: 0, width: W, height: H }), grade, s('rect', { class: 'w-contorno', x: 0, y: 0, width: W, height: H }));

  const rotulo = (x, y, texto, extra = {}) => {
    incluirTexto(x, y, texto, extra['font-size'] || fonte, !!extra.transform);
    return s('text', { class: 'w-rotulo', x, y, 'text-anchor': 'middle', 'dominant-baseline': 'central', 'font-size': fonte, texto, dados: { tam: extra['font-size'] || fonte }, ...extra });
  };
  const camadaRotulos = s('g');
  for (const f of d.formas || []) {
    const cor = corVar(f.cor || (f.tipo === 'cota' ? 'cinza' : 'preto'));
    const estilo = `--c: ${cor}`;
    const classe = `w-forma${f.preenchido ? ' cheia' : ''}`;
    if (f.tipo === 'retangulo') {
      const cx = px(f.x + f.largura / 2), cy = px(f.y + f.altura / 2);
      const giro = (f.rotacao || 0) * Math.PI / 180;
      for (const [dx, dy] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
        const ox = dx * px(f.largura) / 2, oy = dy * px(f.altura) / 2;
        incluir(cx + ox * Math.cos(giro) - oy * Math.sin(giro), cy + ox * Math.sin(giro) + oy * Math.cos(giro));
      }
      svg.append(s('rect', { class: classe, style: estilo, x: px(f.x), y: px(f.y), width: px(f.largura), height: px(f.altura), transform: f.rotacao ? `rotate(${f.rotacao} ${cx} ${cy})` : null }));
      if (f.rotulo) camadaRotulos.append(rotulo(cx, cy, f.rotulo));
    } else if (f.tipo === 'circulo') {
      incluir(px(f.x - f.raio), px(f.y - f.raio)); incluir(px(f.x + f.raio), px(f.y + f.raio));
      svg.append(s('circle', { class: classe, style: estilo, cx: px(f.x), cy: px(f.y), r: px(f.raio) }));
      if (f.rotulo) camadaRotulos.append(rotulo(px(f.x), px(f.y), f.rotulo));
    } else if (f.tipo === 'poligono') {
      f.pontos.forEach(([x, y]) => incluir(px(x), px(y)));
      svg.append(s('polygon', { class: classe, style: estilo, points: f.pontos.map(([x, y]) => `${px(x)},${px(y)}`).join(' ') }));
      if (f.rotulo) {
        const cx = f.pontos.reduce((a, p) => a + p[0], 0) / f.pontos.length, cy = f.pontos.reduce((a, p) => a + p[1], 0) / f.pontos.length;
        camadaRotulos.append(rotulo(px(cx), px(cy), f.rotulo));
      }
    } else if (f.tipo === 'linha' || f.tipo === 'seta') {
      const [x1, y1, x2, y2] = [px(f.x1), px(f.y1), px(f.x2), px(f.y2)];
      incluir(x1, y1); incluir(x2, y2);
      svg.append(s('line', { class: 'w-forma w-traco', style: estilo, x1, y1, x2, y2 }));
      const [ang, nx, ny] = paraFora(x1, y1, x2, y2);
      if (f.tipo === 'seta') {
        const tam = fonte * 0.9;
        const pontaA = [x2 - tam * Math.cos(ang - 0.42), y2 - tam * Math.sin(ang - 0.42)];
        const pontaB = [x2 - tam * Math.cos(ang + 0.42), y2 - tam * Math.sin(ang + 0.42)];
        svg.append(s('polygon', { class: 'w-ponta', style: estilo, points: `${x2},${y2} ${pontaA.join(',')} ${pontaB.join(',')}` }));
      }
      if (f.rotulo) {
        // afasta o rótulo da linha o bastante para a caixa do texto não encostar nela, em qualquer inclinação
        const dist = Math.abs(nx) * String(f.rotulo).length * fonte * 0.29 + Math.abs(ny) * fonte * 0.55 + fonte * 0.35;
        camadaRotulos.append(rotulo((x1 + x2) / 2 + nx * dist, (y1 + y2) / 2 + ny * dist, f.rotulo));
      }
    } else if (f.tipo === 'cota') {
      const [x1, y1, x2, y2] = [px(f.x1), px(f.y1), px(f.x2), px(f.y2)];
      const [ang, nx, ny] = paraFora(x1, y1, x2, y2);
      const o = px(f.deslocamento || 0);
      const a = [x1 + nx * o, y1 + ny * o], b = [x2 + nx * o, y2 + ny * o];
      const g = s('g', { class: 'w-cota', style: estilo });
      if (o) {
        const sobra = Math.sign(o) * fonte * 0.35;
        g.append(s('line', { x1, y1, x2: a[0] + nx * sobra, y2: a[1] + ny * sobra }), s('line', { x1: x2, y1: y2, x2: b[0] + nx * sobra, y2: b[1] + ny * sobra }));
      }
      g.append(s('line', { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }));
      incluir(...a); incluir(...b); incluir(x1, y1); incluir(x2, y2);
      const tique = fonte * 0.45;
      for (const [px_, py_] of [a, b]) {
        g.append(s('line', { x1: px_ - tique * Math.cos(ang + Math.PI / 4), y1: py_ - tique * Math.sin(ang + Math.PI / 4), x2: px_ + tique * Math.cos(ang + Math.PI / 4), y2: py_ + tique * Math.sin(ang + Math.PI / 4) }));
      }
      svg.append(g);
      const comprimento = Math.hypot(f.x2 - f.x1, f.y2 - f.y1);
      let graus = ang * 180 / Math.PI;
      if (graus > 90) graus -= 180;
      if (graus <= -90) graus += 180;
      const lado = Math.sign(o || 1);
      const mx = (a[0] + b[0]) / 2 + nx * lado * fonte * 0.75, my = (a[1] + b[1]) / 2 + ny * lado * fonte * 0.75;
      camadaRotulos.append(rotulo(mx, my, f.rotulo || fmtMedida(comprimento, d.unidade), { class: 'w-rotulo w-rotulo-cota', transform: `rotate(${graus} ${mx} ${my})` }));
    } else if (f.tipo === 'texto') {
      const mult = f.tamanho === 'pequeno' ? 0.8 : f.tamanho === 'grande' ? 1.45 : 1;
      camadaRotulos.append(rotulo(px(f.x), px(f.y), f.texto, { 'font-size': fonte * mult, style: f.cor ? `--c: ${cor}` : null, class: `w-rotulo${f.cor ? ' colorido' : ''}` }));
    }
  }
  svg.append(camadaRotulos);
  const folga = fonte * 1.2;
  const base = [lim[0] - folga, lim[1] - folga, lim[2] - lim[0] + 2 * folga, lim[3] - lim[1] + 2 * folga];
  let vb = [...base];
  svg.setAttribute('viewBox', base.join(' '));

  // em tela estreita o desenho encolhe e as letras iriam junto: elas não ficam menores que uns 11 px na tela
  const ajustarLetras = () => {
    const caixaSvg = svg.getBoundingClientRect();
    if (!caixaSvg.width) return;
    const escalaTela = Math.min(caixaSvg.width / vb[2], (caixaSvg.height || Infinity) / vb[3]);
    const fator = Math.max(1, 11 / (fonte * escalaTela));
    camadaRotulos.querySelectorAll('text').forEach((tx) => tx.setAttribute('font-size', Number(tx.dataset.tam) * fator));
  };
  new ResizeObserver(() => requestAnimationFrame(ajustarLetras)).observe(svg);

  // zoom e arrasto
  const aplicar = () => { svg.setAttribute('viewBox', vb.join(' ')); ajustarLetras(); };
  const zoom = (fator, cx = vb[0] + vb[2] / 2, cy = vb[1] + vb[3] / 2) => {
    const nova = Math.min(Math.max(vb[2] / fator, base[2] / 12), base[2] * 1.6);
    const r = nova / vb[2];
    vb = [cx - (cx - vb[0]) * r, cy - (cy - vb[1]) * r, nova, vb[3] * r];
    aplicar();
  };
  const ajustar = () => { vb = [...base]; aplicar(); };
  const noDesenho = (e) => {
    const m = svg.getScreenCTM();
    if (!m) return [vb[0] + vb[2] / 2, vb[1] + vb[3] / 2];
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(m.inverse());
    return [p.x, p.y];
  };
  const palco = el('div', { class: 'widget-desenho-palco', tabindex: '0', role: 'group', 'aria-label': t('Desenho. Use + e - para aproximar, as setas para mover e 0 para ver tudo.') }, svg);
  const dica = el('div', { class: 'widget-mapa-dica', 'aria-hidden': 'true', texto: t('Clique no desenho para dar zoom com a roda do mouse') });
  palco.append(dica,
    el('div', { class: 'widget-desenho-botoes' },
      botaoIcone('zoom_mais', t('Aproximar'), () => zoom(1.4)),
      botaoIcone('zoom_menos', t('Afastar'), () => zoom(1 / 1.4)),
      botaoIcone('ajustar', t('Ver o desenho inteiro'), ajustar)));
  let ativo = !!ctx.cheia, arrasto = null, tempoDica = 0;
  palco.addEventListener('wheel', (e) => {
    if (!ativo && !e.ctrlKey) {
      dica.classList.add('visivel');
      clearTimeout(tempoDica);
      tempoDica = setTimeout(() => dica.classList.remove('visivel'), 1600);
      return;
    }
    e.preventDefault();
    const [cx, cy] = noDesenho(e);
    zoom(e.deltaY < 0 ? 1.18 : 1 / 1.18, cx, cy);
  }, { passive: false });
  palco.addEventListener('pointerdown', (e) => {
    if (e.button !== 0 || e.target.closest('button')) return;
    ativo = true;
    arrasto = { x: e.clientX, y: e.clientY, vb: [...vb], escala: svg.getScreenCTM()?.a || 1 };
    palco.setPointerCapture(e.pointerId);
    palco.classList.add('arrastando');
  });
  palco.addEventListener('pointermove', (e) => {
    if (!arrasto) return;
    vb = [arrasto.vb[0] - (e.clientX - arrasto.x) / arrasto.escala, arrasto.vb[1] - (e.clientY - arrasto.y) / arrasto.escala, vb[2], vb[3]];
    aplicar();
  });
  const soltar = () => { arrasto = null; palco.classList.remove('arrastando'); };
  palco.addEventListener('pointerup', soltar);
  palco.addEventListener('pointercancel', soltar);
  palco.addEventListener('pointerleave', () => { if (!arrasto && !ctx.cheia) ativo = false; });
  palco.addEventListener('keydown', (e) => {
    const mover = vb[2] * 0.1;
    const acoes = {
      '+': () => zoom(1.4), '=': () => zoom(1.4), '-': () => zoom(1 / 1.4), _: () => zoom(1 / 1.4), 0: ajustar,
      ArrowLeft: () => { vb[0] -= mover; aplicar(); }, ArrowRight: () => { vb[0] += mover; aplicar(); },
      ArrowUp: () => { vb[1] -= mover; aplicar(); }, ArrowDown: () => { vb[1] += mover; aplicar(); },
    };
    if (acoes[e.key]) { e.preventDefault(); acoes[e.key](); }
  });

  const rodape = el('div', { class: 'widget-legenda' },
    el('span', { class: 'widget-legenda-item' }, el('span', { class: 'widget-amostra grade', 'aria-hidden': 'true' }), t('Cada quadrado da grade: {medida}', { medida: fmtMedida(passo, d.unidade) })));
  if (Array.isArray(d.legenda)) {
    d.legenda.forEach((l) => rodape.append(el('span', { class: 'widget-legenda-item' }, el('span', { class: 'widget-amostra', style: `--c: ${corVar(l.cor)}`, 'aria-hidden': 'true' }), l.rotulo)));
  }
  corpo.append(palco, rodape);
  if (typeof d.legenda === 'string') corpo.append(el('p', { class: 'widget-nota', texto: d.legenda }));
  ctx.exportar = () => {
    const largura = Math.min(900, base[2]);
    return { svg, viewBox: base, largura, altura: largura * base[3] / base[2] };
  };
  ctx.legendaExportar = () => [
    { cor: null, texto: t('Cada quadrado da grade: {medida}', { medida: fmtMedida(passo, d.unidade) }) },
    ...(Array.isArray(d.legenda) ? d.legenda.map((l) => ({ cor: l.cor, texto: l.rotulo })) : d.legenda ? [{ cor: null, texto: d.legenda }] : []),
  ];
}

// ---------- gráfico ----------
function escala(min, max, alvo = 5) {
  if (min === max) { max = min + 1; }
  const passo = passoBonito((max - min) / alvo);
  const inicio = Math.floor(min / passo + 1e-9) * passo, fim = Math.ceil(max / passo - 1e-9) * passo;
  const lista = [];
  for (let k = 0; inicio + k * passo <= fim + passo / 2; k++) lista.push(Number((inicio + k * passo).toPrecision(12)));
  return { inicio, fim, lista };
}
const larguraTexto = (texto, tam = 12) => String(texto).length * tam * 0.56;
const encurtar = (texto, max) => (String(texto).length > max ? `${String(texto).slice(0, max - 1)}…` : String(texto));

function desenharGrafico(corpo, d, ctx) {
  const series = (d.series || []).map((serie, i) => ({ ...serie, cor: serie.cor || ORDEM_CORES[i % ORDEM_CORES.length] }));
  const rotulos = d.rotulos || [];
  const pizza = d.tipo_grafico === 'pizza';
  const caixa = el('div', { class: `widget-grafico${pizza ? ' widget-grafico-pizza' : ''}`, tabindex: '0', role: 'group', 'aria-label': t('Gráfico. Use as setas para ver os valores.') });
  const dica = el('div', { class: 'widget-dica', role: 'status', 'aria-live': 'polite', hidden: true });
  const desenhoBox = el('div', { class: 'widget-grafico-desenho' });
  caixa.append(desenhoBox, dica);
  const fatias = pizza ? rotulos.map((r, i) => ({ rotulo: r, valor: series[0].valores[i], cor: ORDEM_CORES[i % ORDEM_CORES.length] })) : [];
  const total = pizza ? fatias.reduce((a, f) => a + f.valor, 0) : 0;
  const pct = (v) => `${fmtNumero(total ? (v / total) * 100 : 0, 1)}%`;

  // legenda e tabela para leitores de tela
  const legenda = el('ul', { class: 'widget-legenda', 'aria-hidden': 'true' });
  if (pizza) fatias.forEach((f) => legenda.append(el('li', { class: 'widget-legenda-item' }, el('span', { class: 'widget-amostra', style: `--c: ${corVar(f.cor)}` }), el('span', { texto: f.rotulo }), el('b', { texto: `${fmtValor(f.valor, d.unidade)} (${pct(f.valor)})` }))));
  else if (series.length > 1) series.forEach((serie) => legenda.append(el('li', { class: 'widget-legenda-item' }, el('span', { class: 'widget-amostra', style: `--c: ${corVar(serie.cor)}` }), el('span', { texto: serie.nome }))));
  const tabela = el('table', { class: 'sr' },
    el('thead', {}, el('tr', {}, el('th', { texto: t('Rótulo') }), ...series.map((serie) => el('th', { texto: serie.nome })))),
    el('tbody', {}, ...rotulos.map((r, i) => el('tr', {}, el('th', { texto: r }), ...series.map((serie) => el('td', { texto: fmtValor(serie.valores[i], d.unidade) }))))));
  corpo.append(caixa, legenda.childElementCount ? legenda : '', tabela);

  let svgAtual = null, dims = [0, 0], foco = -1, marcas = [];
  const esconder = () => { dica.hidden = true; marcas.forEach((m) => m.classList.remove('ativo')); svgAtual?.querySelector('.w-guia')?.setAttribute('visibility', 'hidden'); };
  const posicionar = (x, y) => {
    const w = dica.offsetWidth, h = dica.offsetHeight;
    dica.style.left = `${Math.min(Math.max(4, x - w / 2), caixa.clientWidth - w - 4)}px`;
    dica.style.top = `${Math.max(4, y - h - 10)}px`;
  };
  let mostrar = () => {};

  function desenhar(largura) {
    const altura = pizza ? Math.min(largura, ctx.cheia ? 420 : 300) : Math.round(Math.min(Math.max(largura * 0.5, 220), ctx.cheia ? 520 : 320));
    const svg = s('svg', { class: 'widget-svg', width: largura, height: altura, viewBox: `0 0 ${largura} ${altura}`, 'aria-hidden': 'true', focusable: 'false' });
    marcas = [];
    if (pizza) {
      const tam = Math.min(largura, altura);
      const cx = largura / 2, cy = altura / 2, r = tam / 2 - 6, ri = r * 0.56;
      let ang = -Math.PI / 2;
      fatias.forEach((f, i) => {
        const a = total ? (f.valor / total) * Math.PI * 2 : 0;
        if (!a) { marcas.push(null); return; }
        let caminho;
        if (a >= Math.PI * 2 - 1e-6) {
          caminho = `M${cx} ${cy - r}A${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r}Z M${cx} ${cy - ri}A${ri} ${ri} 0 1 0 ${cx + 0.01} ${cy - ri}Z`;
        } else {
          const p = (raio, an) => `${cx + raio * Math.cos(an)} ${cy + raio * Math.sin(an)}`;
          const grande = a > Math.PI ? 1 : 0;
          caminho = `M${p(r, ang)}A${r} ${r} 0 ${grande} 1 ${p(r, ang + a)}L${p(ri, ang + a)}A${ri} ${ri} 0 ${grande} 0 ${p(ri, ang)}Z`;
        }
        const fatia = s('path', { class: 'w-fatia', style: `--c: ${corVar(f.cor)}`, d: caminho, 'fill-rule': 'evenodd', onpointerenter: () => mostrar(i), dados: { i } });
        svg.append(fatia);
        marcas.push(fatia);
        if (a > 0.32) {
          const meio = ang + a / 2, rr = (r + ri) / 2;
          svg.append(s('text', { class: 'w-pct', x: cx + rr * Math.cos(meio), y: cy + rr * Math.sin(meio), 'text-anchor': 'middle', 'dominant-baseline': 'central', texto: pct(f.valor) }));
        }
        f.meio = ang + a / 2; f.r = r; f.cx = cx; f.cy = cy;
        ang += a;
      });
      svg.append(s('text', { class: 'w-total', x: cx, y: cy - 8, 'text-anchor': 'middle', 'dominant-baseline': 'central', texto: fmtValor(total, d.unidade, true) }),
        s('text', { class: 'w-total-rotulo', x: cx, y: cy + 12, 'text-anchor': 'middle', 'dominant-baseline': 'central', texto: t('total') }));
      mostrar = (i) => {
        const f = fatias[i];
        if (!marcas[i]) return;
        foco = i;
        marcas.forEach((m, j) => m?.classList.toggle('ativo', j === i));
        dica.replaceChildren(el('b', { texto: f.rotulo }), el('span', { class: 'widget-dica-linha' }, el('span', { class: 'widget-amostra', style: `--c: ${corVar(f.cor)}` }), `${fmtValor(f.valor, d.unidade)} (${pct(f.valor)})`));
        dica.hidden = false;
        posicionar(f.cx + f.r * 0.8 * Math.cos(f.meio), f.cy + f.r * 0.8 * Math.sin(f.meio));
      };
    } else {
      const valores = series.flatMap((serie) => serie.valores).filter((v) => v !== null && v !== undefined);
      const { inicio, fim, lista } = escala(Math.min(0, ...valores), Math.max(0, ...valores));
      const fmtEixo = (v) => fmtValor(v, d.unidade, true);
      const esq = Math.max(...lista.map((v) => larguraTexto(fmtEixo(v), 11.5))) + 14;
      const dir = 12, topo = 14;
      const n = rotulos.length;
      const plotW = Math.max(40, largura - esq - dir);
      const banda = plotW / n;
      const maxRot = Math.max(...rotulos.map((r) => String(r).length));
      let girar = false, pulo = 1, corte = 24;
      if (larguraTexto(encurtar('x'.repeat(maxRot), corte), 11.5) > banda - 6) {
        if (n <= 16) { girar = true; corte = 16; }
        else { corte = 10; while (larguraTexto('x'.repeat(Math.min(maxRot, corte)), 11.5) > banda * pulo - 6 && pulo < n) pulo++; }
      }
      const baixo = girar ? Math.min(Math.max(...rotulos.map((r) => larguraTexto(encurtar(r, corte), 11.5))) * 0.66 + 18, 96) : 26;
      const plotH = altura - topo - baixo;
      const y = (v) => topo + plotH * (1 - (v - inicio) / (fim - inicio));
      const xc = (i) => esq + banda * (i + 0.5);
      const grade = s('g');
      lista.forEach((v) => {
        grade.append(s('line', { class: v === 0 ? 'w-eixo' : 'w-grade', x1: esq, x2: largura - dir, y1: y(v), y2: y(v) }),
          s('text', { class: 'w-eixo-texto', x: esq - 7, y: y(v), 'text-anchor': 'end', 'dominant-baseline': 'central', texto: fmtEixo(v) }));
      });
      rotulos.forEach((r, i) => {
        if (i % pulo) return;
        const texto = encurtar(r, corte);
        if (girar) grade.append(s('text', { class: 'w-eixo-texto', x: xc(i), y: topo + plotH + 10, 'text-anchor': 'end', 'dominant-baseline': 'central', transform: `rotate(-35 ${xc(i)} ${topo + plotH + 10})`, texto }));
        else grade.append(s('text', { class: 'w-eixo-texto', x: xc(i), y: topo + plotH + 15, 'text-anchor': 'middle', 'dominant-baseline': 'central', texto }));
      });
      svg.append(grade);
      const guia = s('line', { class: 'w-guia', x1: 0, x2: 0, y1: topo, y2: topo + plotH, visibility: 'hidden', dados: { exportar: 'nao' } });
      svg.append(guia);
      const y0 = y(Math.min(Math.max(0, inicio), fim));
      const mostrarValores = d.tipo_grafico === 'barras' && n * series.length <= 14;
      if (d.tipo_grafico === 'barras') {
        const grupo = banda * 0.74, bw = grupo / series.length;
        series.forEach((serie, j) => serie.valores.forEach((v, i) => {
          const x = esq + banda * i + (banda - grupo) / 2 + j * bw;
          const barra = s('rect', { class: 'w-barra', style: `--c: ${corVar(serie.cor)}`, x: x + 1, width: Math.max(1, bw - 2), y: Math.min(y(v), y0), height: Math.max(Math.abs(y(v) - y0), v ? 1 : 0), rx: Math.min(3, bw / 4), dados: { i } });
          svg.append(barra);
          marcas.push(barra);
          if (mostrarValores && bw >= 22) svg.append(s('text', { class: 'w-valor', x: x + bw / 2, y: v >= 0 ? y(v) - 7 : y(v) + 9, 'text-anchor': 'middle', 'dominant-baseline': 'central', texto: fmtValor(v, d.unidade, true) }));
        }));
      } else {
        series.forEach((serie) => {
          const partes = [];
          let atual = [];
          serie.valores.forEach((v, i) => {
            if (v === null || v === undefined) { if (atual.length) partes.push(atual); atual = []; }
            else atual.push([xc(i), y(v), i]);
          });
          if (atual.length) partes.push(atual);
          partes.forEach((pts) => {
            const caminho = pts.map(([x, yy], k) => `${k ? 'L' : 'M'}${x} ${yy}`).join('');
            if (d.tipo_grafico === 'area' && pts.length > 1) svg.append(s('path', { class: 'w-area', style: `--c: ${corVar(serie.cor)}`, d: `${caminho}L${pts[pts.length - 1][0]} ${y0}L${pts[0][0]} ${y0}Z` }));
            svg.append(s('path', { class: 'w-linha', style: `--c: ${corVar(serie.cor)}`, d: caminho }));
            if (n <= 40 || pts.length === 1) pts.forEach(([x, yy, i]) => { const ponto = s('circle', { class: 'w-ponto', style: `--c: ${corVar(serie.cor)}`, cx: x, cy: yy, r: 3.5, dados: { i } }); svg.append(ponto); marcas.push(ponto); });
          });
        });
      }
      const alvos = s('g', { dados: { exportar: 'nao' } });
      rotulos.forEach((_, i) => alvos.append(s('rect', { class: 'w-alvo', x: esq + banda * i, y: topo, width: banda, height: plotH, onpointerenter: () => mostrar(i) })));
      svg.append(alvos);
      mostrar = (i) => {
        foco = i;
        marcas.forEach((m) => m.classList.toggle('ativo', Number(m.dataset.i) === i));
        guia.setAttribute('x1', xc(i)); guia.setAttribute('x2', xc(i)); guia.setAttribute('visibility', 'visible');
        dica.replaceChildren(el('b', { texto: rotulos[i] }), ...series.map((serie) => el('span', { class: 'widget-dica-linha' },
          el('span', { class: 'widget-amostra', style: `--c: ${corVar(serie.cor)}` }), series.length > 1 ? `${serie.nome}: ` : '', fmtValor(serie.valores[i], d.unidade))));
        dica.hidden = false;
        const topoValor = Math.min(...series.map((serie) => (serie.valores[i] === null || serie.valores[i] === undefined ? y0 : y(Math.max(serie.valores[i], 0)))));
        posicionar(xc(i), topoValor);
      };
    }
    desenhoBox.replaceChildren(svg);
    svgAtual = svg;
    dims = [largura, altura];
    if (foco >= 0 && !dica.hidden) mostrar(foco);
  }

  caixa.addEventListener('pointerleave', esconder);
  caixa.addEventListener('blur', esconder);
  caixa.addEventListener('keydown', (e) => {
    const n = rotulos.length;
    const validos = (i) => !pizza || marcas[i];
    let i = foco;
    const passo = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (passo) {
      e.preventDefault();
      for (let k = 0; k < n; k++) { i = ((i < 0 && passo < 0 ? 0 : i) + passo + n) % n; if (validos(i)) break; }
      mostrar(i);
    } else if (e.key === 'Home' || e.key === 'End') { e.preventDefault(); mostrar(e.key === 'Home' ? 0 : n - 1); }
    else if (e.key === 'Escape') esconder();
  });
  // redesenha na largura de verdade (o texto fica do mesmo tamanho em qualquer tela), fora do aviso do observador
  let larguraAtual = 0;
  const observador = new ResizeObserver(() => requestAnimationFrame(() => {
    const w = Math.floor(desenhoBox.clientWidth);
    if (w > 0 && w !== larguraAtual) { larguraAtual = w; desenhar(w); }
  }));
  observador.observe(desenhoBox);
  ctx.exportar = () => {
    if (!svgAtual) desenhar(640);
    return { svg: svgAtual, viewBox: [0, 0, dims[0], dims[1]], largura: dims[0], altura: dims[1] };
  };
  ctx.legendaExportar = () => (pizza
    ? fatias.map((f) => ({ cor: f.cor, texto: `${f.rotulo}: ${fmtValor(f.valor, d.unidade)} (${pct(f.valor)})` }))
    : series.length > 1 ? series.map((serie) => ({ cor: serie.cor, texto: serie.nome })) : []);
}

// ---------- comparação ----------
function celula(v, melhor) {
  let conteudo;
  if (v === true) conteudo = [el('span', { class: 'widget-sim', html: ic('certo') }), el('span', { class: 'sr', texto: t('sim') })];
  else if (v === false) conteudo = [el('span', { class: 'widget-nao', html: ic('x') }), el('span', { class: 'sr', texto: t('não') })];
  else if (v === null || v === undefined || v === '') conteudo = [el('span', { class: 'widget-vazio', texto: '–' }), el('span', { class: 'sr', texto: t('sem dado') })];
  else conteudo = [typeof v === 'number' ? fmtNumero(v) : String(v)];
  if (!melhor) return el('td', {}, ...conteudo);
  // a estrela anda grudada na última palavra: nunca desce sozinha para a linha de baixo
  const estrela = el('span', { class: 'widget-melhor', title: t('Melhor nesta linha') }, el('span', { html: ic('estrela') }), el('span', { class: 'sr', texto: t('(melhor)') }));
  if (typeof conteudo[0] === 'string') {
    const texto = conteudo[0].trimEnd();
    const corte = texto.lastIndexOf(' ') + 1;
    return el('td', { class: 'melhor' }, texto.slice(0, corte), el('span', { class: 'widget-junto' }, texto.slice(corte), estrela));
  }
  return el('td', { class: 'melhor' }, el('span', { class: 'widget-junto' }, ...conteudo, estrela));
}

function desenharComparacao(corpo, d) {
  const colunas = d.colunas || [];
  const linhas = d.linhas || [];
  const vitorias = colunas.map((_, j) => linhas.filter((l) => l.melhor === j).length);
  const comMelhor = linhas.filter((l) => l.melhor !== undefined && l.melhor !== null).length;
  const tabela = el('table', { class: 'widget-tabela' },
    el('thead', {}, el('tr', {}, el('th', { scope: 'col', class: 'canto', texto: t('Critério') }), ...colunas.map((c) => el('th', { scope: 'col', texto: c })))),
    el('tbody', {}, ...linhas.map((l) => el('tr', {}, el('th', { scope: 'row', texto: l.criterio }), ...l.valores.map((v, j) => celula(v, l.melhor === j))))),
    comMelhor ? el('tfoot', {}, el('tr', {}, el('th', { scope: 'row', texto: t('Melhor em') }),
      ...vitorias.map((n) => el('td', { class: n && n === Math.max(...vitorias) ? 'lider' : '', texto: t('{n} de {total}', { n, total: comMelhor }) })))) : null);
  const rolagem = el('div', { class: 'widget-rolagem', tabindex: '0', role: 'region', 'aria-label': t('Tabela de comparação') }, tabela);
  const caixa = el('div', { class: 'widget-rolagem-caixa' }, rolagem);
  // tabela mais larga que o cartão: uma sombra na borda direita avisa que dá para rolar para o lado
  const marcarSobra = () => caixa.classList.toggle('sobra-direita', rolagem.scrollLeft + rolagem.clientWidth < rolagem.scrollWidth - 1);
  rolagem.addEventListener('scroll', marcarSobra, { passive: true });
  new ResizeObserver(() => requestAnimationFrame(marcarSobra)).observe(rolagem);
  corpo.append(caixa);
}

// ---------- linha do tempo ----------
function desenharLinhaDoTempo(corpo, d) {
  corpo.append(el('ol', { class: 'widget-tempo' }, ...(d.eventos || []).map((ev) => el('li', {},
    el('span', { class: 'widget-tempo-marca', 'aria-hidden': 'true' }),
    el('div', { class: 'widget-tempo-texto' },
      el('span', { class: 'widget-tempo-data', texto: ev.data }),
      el('b', { texto: ev.titulo }),
      ev.descricao ? el('p', { texto: ev.descricao }) : null)))));
}

// ---------- checklist ----------
const copiasChecklist = new Map(); // id do widget -> funções que redesenham cada cópia aberta (conversa e tela cheia)
function avisarCopias(id) {
  for (const fn of [...(copiasChecklist.get(id) || [])]) fn();
}

function desenharChecklist(corpo, d, ctx) {
  const itens = d.itens || [];
  const texto = el('span', { class: 'widget-progresso-texto' });
  const cheio = el('span', { class: 'widget-progresso-cheio' });
  const progresso = el('div', { class: 'widget-progresso' }, texto, el('span', { class: 'widget-progresso-barra', 'aria-hidden': 'true' }, cheio));
  const caixas = [];
  const lista = el('ul', { class: 'widget-checklist', role: 'list' }, ...itens.map((it, i) => {
    const id = novoId('widget-item');
    const caixa = el('input', { type: 'checkbox', id });
    caixa.checked = !!it.feito;
    caixa.addEventListener('change', () => alternar(i, caixa.checked));
    caixas.push(caixa);
    return el('li', {}, el('label', { for: id }, caixa, el('span', { class: 'widget-caixa', 'aria-hidden': 'true', html: ic('certo') }), el('span', { class: 'widget-item-texto', texto: it.texto })));
  }));
  const atualizar = () => {
    itens.forEach((it, i) => { caixas[i].checked = !!it.feito; caixas[i].closest('li').classList.toggle('feito', !!it.feito); });
    const feitos = itens.filter((it) => it.feito).length;
    texto.textContent = t('{feitos} de {total} feitos', { feitos, total: itens.length });
    cheio.style.width = `${itens.length ? (feitos / itens.length) * 100 : 0}%`;
  };
  let salvo = itens.map((it) => !!it.feito);
  let fila = Promise.resolve();
  const enviar = async () => {
    const marcados = itens.map((it, i) => (it.feito ? i : -1)).filter((i) => i >= 0);
    try {
      await api(`/widgets/${encodeURIComponent(ctx.id)}`, { metodo: 'PATCH', corpo: { marcados } });
      salvo = itens.map((it) => !!it.feito);
      lembrarWidget(ctx.id, ctx.widget);  // o objeto daqui já tem o que foi marcado (inclusive o que ainda está na fila)
    } catch (e) {
      itens.forEach((it, i) => { it.feito = salvo[i]; });
      avisarCopias(ctx.id);
      atualizar();
      aviso(t('Não deu para salvar o checklist: {erro}', { erro: e.message }), 'erro');
    }
  };
  function alternar(i, marcado) {
    itens[i].feito = marcado;
    atualizar();
    if (!ctx.id) return;
    avisarCopias(ctx.id);
    fila = fila.then(enviar);
  }
  if (ctx.id) {
    if (!copiasChecklist.has(ctx.id)) copiasChecklist.set(ctx.id, new Set());
    const copias = copiasChecklist.get(ctx.id);
    const redesenhar = () => {
      if (!lista.isConnected) { copias.delete(redesenhar); if (!copias.size) copiasChecklist.delete(ctx.id); return; }
      atualizar();
    };
    copias.add(redesenhar);
  }
  atualizar();
  corpo.append(progresso, lista);
}

// ---------- a versão em texto ----------
export function textoDoWidget(widget) {
  if (widget && widget.widget && !widget.tipo) widget = widget.widget;
  if (!widget || !widget.dados) return '';
  const d = widget.dados;
  const linhas = [widget.titulo || nomeTipo(widget.tipo), ''];
  if (widget.tipo === 'produtos') {
    const itens = [...(d.itens || [])].sort((a, b) => (a.moeda === b.moeda ? a.preco - b.preco : 0));
    itens.forEach((it, i) => {
      const extra = [it.loja, it.nota ? t('nota {nota}', { nota: valorNota(it.nota) }) + (it.nota.fonte ? ` (${it.nota.fonte})` : '') : ''].filter(Boolean).join(', ');
      linhas.push(`${i + 1}. ${it.nome}: ${fmtPreco(it.preco, it.moeda)}${extra ? ` (${extra})` : ''}`);
      if (it.observacao) linhas.push(`   ${it.observacao}`);
      if (it.link) linhas.push(`   ${it.link}`);
    });
    linhas.push('', t('Preços vistos em {data}; confira na loja.', { data: fmtData(d.visto_em) }));
  } else if (widget.tipo === 'mapa') {
    (d.pontos || []).forEach((p, i) => {
      linhas.push(`${i + 1}. ${p.nome}${p.descricao ? `: ${p.descricao}` : ''}`);
      if (p.endereco) linhas.push(`   ${p.endereco}`);
      if (p.achado && p.achado !== p.endereco) linhas.push(`   ${t('No mapa: {lugar}', { lugar: p.achado })}`);
      linhas.push(`   ${urlOsm(p)}`);
    });
    if (d.fora?.length) {
      linhas.push('', t('Ficaram de fora do mapa:'));
      d.fora.forEach((f) => linhas.push(`• ${f.nome} (${motivoFora(f.motivo)})`));
    }
    if (d.rota) linhas.push('', t('A linha liga os pontos na ordem da lista.'));
  } else if (widget.tipo === 'recomendacoes') {
    (d.itens || []).forEach((it, i) => {
      const meta = [nomeRecomendacao(it.tipo), it.ano, it.duracao].filter(Boolean).join(', ');
      linhas.push(`${i + 1}. ${it.titulo} (${meta})`);
      if (it.generos?.length) linhas.push(`   ${t('Gêneros')}: ${it.generos.join(', ')}`);
      if (it.onde) linhas.push(`   ${rotuloOnde(it.tipo)}: ${it.onde}`);
      if (it.nota) linhas.push(`   ${t('Nota')}: ${valorNota(it.nota)}${it.nota.fonte ? ` (${it.nota.fonte})` : ''}`);
      linhas.push(`   ${t('Por que')}: ${it.por_que}`);
    });
  } else if (widget.tipo === 'desenho') {
    linhas.push(t('Desenho de {largura} por {altura} {unidade}', { largura: fmtNumero(d.largura), altura: fmtNumero(d.altura), unidade: d.unidade }));
    for (const f of d.formas || []) {
      const nome = `${nomeForma(f.tipo)}${f.rotulo ? ` "${f.rotulo}"` : ''}`;
      let onde = '';
      if (f.tipo === 'retangulo') onde = t('em {ponto}, {largura} × {altura} {unidade}', { ponto: fmtPar(f.x, f.y), largura: fmtNumero(f.largura), altura: fmtNumero(f.altura), unidade: d.unidade });
      else if (f.tipo === 'circulo') onde = t('centro em {ponto}, raio {raio} {unidade}', { ponto: fmtPar(f.x, f.y), raio: fmtNumero(f.raio), unidade: d.unidade });
      else if (f.tipo === 'linha' || f.tipo === 'seta') onde = t('de {inicio} a {fim}', { inicio: fmtPar(f.x1, f.y1), fim: fmtPar(f.x2, f.y2) });
      else if (f.tipo === 'cota') onde = fmtMedida(Math.hypot(f.x2 - f.x1, f.y2 - f.y1), d.unidade);
      else if (f.tipo === 'texto') onde = `"${f.texto}" ${t('em {ponto}', { ponto: fmtPar(f.x, f.y) })}`;
      else if (f.tipo === 'poligono') onde = t('{n} pontos', { n: f.pontos.length });
      linhas.push(`• ${nome}: ${onde}`);
    }
    if (Array.isArray(d.legenda)) linhas.push('', `${t('Legenda')}: ${d.legenda.map((l) => `${nomeCor(l.cor)} = ${l.rotulo}`).join('; ')}`);
    else if (d.legenda) linhas.push('', d.legenda);
  } else if (widget.tipo === 'grafico') {
    if (d.tipo_grafico === 'pizza') {
      const valores = d.series?.[0]?.valores || [];
      const total = valores.reduce((a, v) => a + v, 0);
      (d.rotulos || []).forEach((r, i) => linhas.push(`${r}: ${fmtValor(valores[i], d.unidade)} (${fmtNumero(total ? (valores[i] / total) * 100 : 0, 1)}%)`));
      linhas.push(`${t('Total')}: ${fmtValor(total, d.unidade)}`);
    } else {
      linhas.push([t('Rótulo'), ...(d.series || []).map((serie) => serie.nome)].join(' | '));
      (d.rotulos || []).forEach((r, i) => linhas.push([r, ...(d.series || []).map((serie) => fmtValor(serie.valores[i], d.unidade))].join(' | ')));
    }
  } else if (widget.tipo === 'comparacao') {
    const colunas = d.colunas || [];
    for (const l of d.linhas || []) {
      const valores = l.valores.map((v, j) => {
        const texto = v === true ? t('sim') : v === false ? t('não') : v === null || v === undefined || v === '' ? t('sem dado') : typeof v === 'number' ? fmtNumero(v) : String(v);
        return `${colunas[j]}: ${texto}${l.melhor === j ? ` ${t('(melhor)')}` : ''}`;
      });
      linhas.push(`• ${l.criterio}: ${valores.join('; ')}`);
    }
  } else if (widget.tipo === 'linha_do_tempo') {
    (d.eventos || []).forEach((ev) => linhas.push(`• ${ev.data}: ${ev.titulo}${ev.descricao ? `. ${ev.descricao}` : ''}`));
  } else if (widget.tipo === 'checklist') {
    (d.itens || []).forEach((it) => linhas.push(`${it.feito ? '[x]' : '[ ]'} ${it.texto}`));
  }
  return linhas.join('\n').trim();
}
