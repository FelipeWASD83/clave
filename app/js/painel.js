// O painel do lado direito da conversa: abas que ficam abertas ao lado do chat (no Code: Arquivos, Visualizador,
// Console, Navegador e Tarefas; em qualquer conversa: a Prévia de HTML e as Tarefas).
//
// Cada aba se registra com registrarAba({ id, titulo, icone, modos, atalho, montar }):
//   - titulo: função que devolve o nome já traduzido (t() roda depois que o idioma carregou);
//   - modos: em que conversas ela aparece ('code', 'chat');
//   - botao: false para não ter botão no topo da conversa (a Prévia e o Visualizador abrem por uma ação);
//   - soDepoisDeAberta: true para a guia só aparecer no painel depois da primeira vez que abriu (a Prévia);
//   - tecla(e): devolve true quando o atalho de teclado é o dela; atalho: o texto do atalho para a dica;
//   - montar(caixa, contexto): monta a aba dentro de `caixa` na primeira vez que ela abre e devolve um objeto com
//     os ganchos que quiser: abrir(args) (cada vez que alguém pede a aba, com o que pediu), mostrar() e esconder()
//     (ela ficou visível ou saiu de vista), contexto(ctx) (trocou a conversa ou a pasta) e redimensionar().
// A aba montada continua viva quando o painel fecha ou a pessoa troca de tela (o console não perde o que rodou).
import { el } from './ui.js';
import { ic } from './icones.js';
import { t } from './i18n.js';

const abas = new Map();          // id -> definição
const montadas = new Map();      // id -> { caixa, inst }
let contexto = null;             // { modo, pasta, conversaId } da tela atual, ou null fora de uma conversa
let ativa = null;
let aberto = false;
const ouvintes = new Set();
const CHAVE_LARGURA = 'clave:painel-largura';
const CHAVE_ABA = 'clave:painel-aba';

function painel() { return document.getElementById('painel-lateral'); }

export function registrarAba(def) {
  abas.set(def.id, { modos: ['code'], ...def });
}

// as abas que valem para a conversa atual, na ordem em que foram registradas
// a ordem das guias não depende de qual módulo carregou primeiro (a Prévia carrega junto com a conversa)
const ORDEM = { arquivos: 1, visualizador: 2, console: 3, navegador: 4, tarefas: 5, previa: 9 };
export function abasDisponiveis() {
  if (!contexto) return [];
  return [...abas.values()].filter((a) => a.modos.includes(contexto.modo) && (!a.disponivel || a.disponivel(contexto)))
    .sort((a, b) => (ORDEM[a.id] ?? 8) - (ORDEM[b.id] ?? 8));
}

export function contextoAtual() { return contexto; }
export function abaAtiva() { return aberto ? ativa : null; }
export function painelAberto() { return aberto; }

// quem quer saber quando o painel abre, fecha ou troca de aba (os botões do topo, o navegador)
export function ouvirPainel(fn) { ouvintes.add(fn); return () => ouvintes.delete(fn); }
function avisarOuvintes() { for (const fn of ouvintes) { try { fn({ aberto, ativa }); } catch (e) { console.error(e); } } }

// a tela da conversa chama ao montar; as outras telas chamam com null (o painel some, as abas ficam vivas)
export function definirContexto(ctx) {
  const antes = contexto;
  contexto = ctx;
  const p = painel();
  if (!p) return;
  if (!ctx) { esconderPainel(); return; }
  for (const [id, m] of montadas) {
    const def = abas.get(id);
    if (!def.modos.includes(ctx.modo)) continue;
    if (!antes || antes.pasta !== ctx.pasta || antes.conversaId !== ctx.conversaId || antes.modo !== ctx.modo) m.inst.contexto?.(ctx);
  }
  if (aberto && ativa && !abasDisponiveis().some((a) => a.id === ativa)) fecharPainel();
  else if (aberto) {
    if (p.hidden) { p.hidden = false; montadas.get(ativa)?.inst.mostrar?.(); }  // voltou para uma conversa
    desenharCabecalho();
  }
  else if (ctx.modo === 'code' && lerPreferencia().aberto && ctx.pasta) abrirPainel(lerPreferencia().aba || 'arquivos', null, { foco: false });
  avisarOuvintes();
}

function lerPreferencia() {
  try { return JSON.parse(localStorage.getItem(CHAVE_ABA) || '{}'); } catch { return {}; }
}
function salvarPreferencia() {
  if (contexto?.modo !== 'code') return;  // só o Code reabre o painel sozinho na próxima vez
  try { localStorage.setItem(CHAVE_ABA, JSON.stringify({ aberto, aba: ativa })); } catch { /* sem armazenamento: tudo bem */ }
}

export function abrirPainel(id, args = null, { foco = true } = {}) {
  const def = abas.get(id);
  if (!def || !contexto || !def.modos.includes(contexto.modo)) return null;
  const p = painel();
  const estavaFora = !aberto || p.hidden;  // fechado, ou escondido por outra tela: a aba volta a ficar à vista
  if (!aberto || p.hidden) {
    p.hidden = false;
    p.classList.remove('saindo');
    p.classList.add('entrando');
    setTimeout(() => p.classList.remove('entrando'), 320);
    aberto = true;
  }
  let m = montadas.get(id);
  if (!m) {
    const caixa = el('div', { class: `painel-aba aba-${id}`, role: 'tabpanel', 'aria-label': def.titulo(), hidden: true });
    p.querySelector('.painel-corpo').append(caixa);
    m = { caixa, inst: def.montar(caixa, contexto) || {} };
    montadas.set(id, m);
  }
  if (ativa !== id) {
    const anterior = montadas.get(ativa);
    if (anterior) { anterior.caixa.hidden = true; anterior.inst.esconder?.(); }
    ativa = id;
    m.caixa.hidden = false;
    m.inst.mostrar?.();
  } else if (estavaFora) {
    m.inst.mostrar?.();
  }
  if (args !== null && args !== undefined) m.inst.abrir?.(args);
  desenharCabecalho();
  salvarPreferencia();
  avisarOuvintes();
  if (foco) setTimeout(() => (m.caixa.querySelector('[data-foco]') || m.caixa.querySelector('input, textarea, button'))?.focus?.({ preventScroll: true }), 40);
  return m.inst;
}

export function alternarAba(id) {
  if (aberto && ativa === id) fecharPainel();
  else abrirPainel(id);
}

function esconderPainel() {
  const p = painel();
  if (!p || p.hidden) return;
  montadas.get(ativa)?.inst.esconder?.();
  p.hidden = true;
}

export function fecharPainel() {
  if (!aberto) return;
  aberto = false;
  const p = painel();
  montadas.get(ativa)?.inst.esconder?.();
  p.classList.add('saindo');
  setTimeout(() => { if (!aberto) { p.hidden = true; p.classList.remove('saindo'); } }, 180);
  salvarPreferencia();
  avisarOuvintes();
}

// Uma fileira de guias que rola de lado (as abas do painel e os arquivos abertos no Visualizador): a roda do mouse
// rola na horizontal, a borda esmaece do lado em que há guia escondida (a barra de rolagem fica escondida) e
// mostrar(guia) traz a guia à vista com uma folga, sem encostar na borda. Só mexe na rolagem da própria fileira.
export function fileiraDeGuias(lista, folga = 8) {
  const marcar = () => {
    const max = lista.scrollWidth - lista.clientWidth;
    lista.classList.toggle('esconde-inicio', max > 1 && lista.scrollLeft > 1);
    lista.classList.toggle('esconde-fim', max > 1 && lista.scrollLeft < max - 1);
  };
  lista.classList.add('fileira-guias');
  lista.addEventListener('scroll', marcar, { passive: true });
  lista.addEventListener('wheel', (e) => {
    if (e.ctrlKey || lista.scrollWidth <= lista.clientWidth || Math.abs(e.deltaX) >= Math.abs(e.deltaY)) return;
    e.preventDefault();
    lista.scrollLeft += e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
  }, { passive: false });
  if (typeof ResizeObserver === 'function') new ResizeObserver(marcar).observe(lista);
  return {
    marcar,
    mostrar(guia) {
      if (guia && lista.clientWidth) {
        const inicio = guia.offsetLeft - folga, fim = guia.offsetLeft + guia.offsetWidth + folga;
        if (inicio < lista.scrollLeft) lista.scrollLeft = Math.max(0, inicio);
        else if (fim > lista.scrollLeft + lista.clientWidth) lista.scrollLeft = fim - lista.clientWidth;
      }
      marcar();
    },
  };
}
let fileiraAbas = null;

function desenharCabecalho() {
  const p = painel();
  const lista = p.querySelector('.painel-abas');
  lista.replaceChildren(...abasDisponiveis().filter((a) => !a.soDepoisDeAberta || montadas.has(a.id)).map((a) => {
    const atual = a.id === ativa;
    return el('button', {
      type: 'button', role: 'tab', class: 'painel-guia', 'aria-selected': String(atual), tabindex: atual ? '0' : '-1',
      title: a.atalho ? `${a.titulo()} (${a.atalho})` : a.titulo(), 'aria-label': a.titulo(), dados: { aba: a.id },
      html: `${ic(a.icone)}<span>${a.titulo()}</span>`, onclick: () => abrirPainel(a.id),
    });
  }));
  // a guia aberta sempre à vista (o nome das outras some no painel estreito, mas a fileira ainda pode rolar)
  fileiraAbas?.mostrar(lista.querySelector('[aria-selected="true"]'));
}

// abre a aba usada por último (ou a primeira que existe aqui): o Ctrl+J e o botão geral do painel
function abrirUltimaAba() {
  const disp = abasDisponiveis();
  const alvo = disp.find((a) => a.id === (lerPreferencia().aba || ativa)) || disp.find((a) => a.botao !== false) || disp[0];
  if (alvo) abrirPainel(alvo.id);
}

// botões do topo da conversa para abrir cada aba (ficam marcados quando a aba está aberta). No fim vai um botão
// geral, que só aparece quando a conversa fica tão estreita que os botões das abas somem (o CSS decide)
export function botoesDoPainel() {
  const caixa = el('div', { class: 'botoes-painel', role: 'group', 'aria-label': t('Painel') });
  const desenhar = () => {
    const botoes = abasDisponiveis().filter((a) => a.botao !== false).map((a) => el('button', {
      class: `icone-botao ${aberto && ativa === a.id ? 'ativo' : ''}`, type: 'button', dados: { aba: a.id },
      title: a.atalho ? `${a.titulo()} (${a.atalho})` : a.titulo(), 'aria-label': a.titulo(), 'aria-pressed': String(aberto && ativa === a.id),
      html: ic(a.icone), onclick: () => alternarAba(a.id),
    }));
    if (botoes.length && !aberto) {
      botoes.push(el('button', {
        class: 'icone-botao painel-geral', type: 'button', title: t('Abrir o painel (Ctrl+J)'), 'aria-label': t('Abrir o painel'),
        html: ic('painel_direito'), onclick: abrirUltimaAba,
      }));
    }
    caixa.replaceChildren(...botoes);
  };
  desenhar();
  const sair = ouvirPainel(desenhar);
  // a tela da conversa troca o topo várias vezes: o botão velho para de ouvir quando sai da página
  const obs = new MutationObserver(() => { if (!caixa.isConnected) { sair(); obs.disconnect(); } });
  setTimeout(() => obs.observe(document.body, { childList: true, subtree: true }), 0);
  return caixa;
}

// ---------- a alça que ajusta a largura ----------
function aplicarLargura(px) {
  const p = painel();
  const min = 320, max = Math.max(min, Math.round(innerWidth * 0.72));
  const v = Math.min(max, Math.max(min, Math.round(px)));
  p.style.setProperty('--largura-painel', `${v}px`);
  return v;
}

function montarAlca(p) {
  const alca = el('div', { class: 'painel-alca', role: 'separator', 'aria-orientation': 'vertical', tabindex: '0', title: t('Arraste para mudar a largura') });
  let inicioX = 0, inicioL = 0;
  const mover = (e) => { aplicarLargura(inicioL + (inicioX - e.clientX)); redimensionarAtiva(); };
  const soltar = (e) => {
    alca.releasePointerCapture?.(e.pointerId);
    document.body.classList.remove('arrastando-painel');
    alca.removeEventListener('pointermove', mover);
    alca.removeEventListener('pointerup', soltar);
    try { localStorage.setItem(CHAVE_LARGURA, String(p.getBoundingClientRect().width)); } catch { /* tudo bem */ }
  };
  alca.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    inicioX = e.clientX; inicioL = p.getBoundingClientRect().width;
    alca.setPointerCapture?.(e.pointerId);
    document.body.classList.add('arrastando-painel');
    alca.addEventListener('pointermove', mover);
    alca.addEventListener('pointerup', soltar);
  });
  alca.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();
    const v = aplicarLargura(p.getBoundingClientRect().width + (e.key === 'ArrowLeft' ? 40 : -40));
    redimensionarAtiva();
    try { localStorage.setItem(CHAVE_LARGURA, String(v)); } catch { /* tudo bem */ }
  });
  alca.addEventListener('dblclick', () => { p.style.removeProperty('--largura-painel'); try { localStorage.removeItem(CHAVE_LARGURA); } catch { /* */ } redimensionarAtiva(); });
  return alca;
}

function redimensionarAtiva() { montadas.get(ativa)?.inst.redimensionar?.(); }

export function iniciarPainel() {
  const p = painel();
  p.setAttribute('aria-label', t('Painel'));
  p.replaceChildren(
    montarAlca(p),
    el('header', { class: 'painel-topo' },
      el('div', { class: 'painel-abas', role: 'tablist', 'aria-label': t('Painel') }),
      el('button', { class: 'icone-botao', type: 'button', title: t('Fechar o painel (Ctrl+J)'), 'aria-label': t('Fechar o painel'), html: ic('x'), onclick: fecharPainel })),
    el('div', { class: 'painel-corpo' }));
  fileiraAbas = fileiraDeGuias(p.querySelector('.painel-abas'));
  p.querySelector('.painel-abas').addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    const lista = abasDisponiveis();
    const i = lista.findIndex((a) => a.id === ativa);
    const prox = lista[(i + (e.key === 'ArrowRight' ? 1 : -1) + lista.length) % lista.length];
    if (prox) { abrirPainel(prox.id); p.querySelector(`.painel-guia[data-aba="${prox.id}"]`)?.focus(); }
  });
  try { const l = Number(localStorage.getItem(CHAVE_LARGURA)); if (l) aplicarLargura(l); } catch { /* tudo bem */ }
  new ResizeObserver(() => {
    redimensionarAtiva();
    fileiraAbas?.mostrar(p.querySelector('.painel-abas [aria-selected="true"]'));
  }).observe(p);
  addEventListener('resize', () => { const l = p.style.getPropertyValue('--largura-painel'); if (l) aplicarLargura(parseInt(l, 10)); });
}

// atalhos: devolve true quando o atalho era do painel
export function atalhoDoPainel(e) {
  const ctrl = e.ctrlKey || e.metaKey;
  if (!ctrl || !contexto) return false;
  // com uma janela, o tour ou o cartão de modelo novo por cima, o painel de trás não muda
  if (document.getElementById('camada')?.children.length || document.querySelector('.tour-camada, .apresentacao')) return false;
  if (!e.shiftKey && (e.key === 'j' || e.key === 'J')) {
    if (aberto) fecharPainel();
    else abrirUltimaAba();
    return true;
  }
  for (const a of abasDisponiveis()) {
    if (a.tecla && a.tecla(e)) { alternarAba(a.id); return true; }
  }
  return false;
}
