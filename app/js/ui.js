// Pequenas ferramentas de interface: criar elementos, avisos, janelas, menus e formatação.
import { ic } from './icones.js';
import { t, localidade, emIngles } from './i18n.js';

export function el(tag, attrs = {}, ...filhos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else if (k === 'texto') e.textContent = v;
    else if (k.startsWith('on') && typeof v === 'function') e.addEventListener(k.slice(2), v);
    else if (k === 'dados') Object.assign(e.dataset, v);
    else if (v === true) e.setAttribute(k, '');
    else e.setAttribute(k, v);
  }
  for (const f of filhos.flat()) {
    if (f === null || f === undefined || f === false) continue;
    e.append(f instanceof Node ? f : document.createTextNode(String(f)));
  }
  return e;
}

export function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

export function aviso(texto, tipo = '') {
  const caixa = document.getElementById('avisos');
  const a = el('div', { class: `aviso-flutuante ${tipo}`, texto });
  caixa.append(a);
  setTimeout(() => a.remove(), tipo === 'erro' ? 7000 : 3800);
}

// ---------- janelas ----------
export function janela({ titulo, corpo, botoes = [], larga = false, classe = '', aoFechar } = {}) {
  const camada = document.getElementById('camada');
  const anterior = document.activeElement;
  let fechada = false;
  const fechar = () => {
    if (fechada) return;
    fechada = true;
    j.remove();
    document.removeEventListener('keydown', tecla);
    camada.removeEventListener('mousedown', cliqueFora);
    aoFechar?.();
    anterior?.focus?.();
  };
  const tecla = (e) => { if (e.key === 'Escape' && camada.lastElementChild === j) fechar(); };
  const cliqueFora = (e) => { if (e.target === camada && camada.lastElementChild === j) fechar(); };
  const rodape = botoes.length ? el('div', { class: 'janela-rodape' }, ...botoes.map((b) => {
    const bt = el('button', { class: `botao ${b.classe || ''}`, type: 'button', texto: b.texto });
    bt.addEventListener('click', async () => {
      if (b.acao) {
        bt.disabled = true;
        try { const r = await b.acao(fechar); if (r !== false) fechar(); }
        catch (e) { aviso(e.message || String(e), 'erro'); }
        finally { bt.disabled = false; }
      } else fechar();
    });
    return bt;
  })) : null;
  const j = el('div', { class: `janela ${larga ? 'larga' : ''} ${classe}`, role: 'dialog', 'aria-modal': 'true', 'aria-label': titulo || t('Janela') },
    titulo ? el('div', { class: 'janela-topo' }, el('h2', { texto: titulo }),
      el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Fechar'), html: ic('x'), onclick: () => fechar() })) : null,
    el('div', { class: 'janela-corpo' }, corpo),
    rodape);
  camada.addEventListener('mousedown', cliqueFora);
  camada.append(j);
  document.addEventListener('keydown', tecla);
  setTimeout(() => j.querySelector('input, textarea, select, button.primario')?.focus(), 30);
  return { fechar, elemento: j };
}

export function confirmar(texto, { titulo = t('Confirmar'), sim = t('Confirmar'), perigo = false } = {}) {
  return new Promise((ok) => {
    let respondeu = false;
    janela({
      titulo, corpo: el('p', { texto, style: 'margin:0' }),
      botoes: [
        { texto: t('Cancelar'), acao: () => { respondeu = true; ok(false); } },
        { texto: sim, classe: perigo ? 'primario perigo' : 'primario', acao: () => { respondeu = true; ok(true); } },
      ],
      aoFechar: () => { if (!respondeu) ok(false); },
    });
  });
}

export function perguntarTexto(titulo, { valor = '', rotulo = '', placeholder = '' } = {}) {
  return new Promise((ok) => {
    const input = el('input', { class: 'entrada', value: valor, placeholder });
    let respondeu = false;
    const { fechar } = janela({
      titulo,
      corpo: el('label', { class: 'campo' }, rotulo ? el('span', { texto: rotulo }) : null, input),
      botoes: [
        { texto: t('Cancelar'), acao: () => { respondeu = true; ok(null); } },
        { texto: t('Salvar'), classe: 'primario', acao: () => { respondeu = true; ok(input.value.trim()); } },
      ],
      aoFechar: () => { if (!respondeu) ok(null); },
    });
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { respondeu = true; ok(input.value.trim()); fechar(); } });
  });
}

// ---------- menus flutuantes ----------
let menuAberto = null;
export function fecharMenu() { menuAberto?.remove(); menuAberto = null; }
export function menu(ancora, itens, { alinhar = 'esquerda', acima = false } = {}) {
  fecharMenu();
  const m = el('div', { class: 'menu', role: 'menu' });
  for (const it of itens) {
    if (it === '-') { m.append(el('div', { class: 'separador' })); continue; }
    if (it.titulo) { m.append(el('div', { class: 'titulo-menu', texto: it.titulo })); continue; }
    const b = el('button', { type: 'button', role: it.marcado !== undefined ? 'menuitemradio' : 'menuitem', 'aria-checked': it.marcado !== undefined ? String(!!it.marcado) : null, disabled: it.desligado },
      it.icone ? el('span', { html: ic(it.icone) }) : null,
      el('span', { class: 'item-textos' }, el('span', { texto: it.texto }), it.sub ? el('small', { texto: it.sub }) : null));
    b.addEventListener('click', () => { if (!it.manterAberto) fecharMenu(); it.acao?.(); });
    m.append(b);
  }
  document.body.append(m);
  const r = ancora.getBoundingClientRect();
  const w = m.offsetWidth, h = m.offsetHeight;
  let x = alinhar === 'direita' ? r.right - w : r.left;
  let y = acima ? r.top - h - 6 : r.bottom + 6;
  if (acima && y < 8 && r.bottom + 6 + h <= innerHeight - 8) y = r.bottom + 6;  // não cabe em cima: abre embaixo
  if (y + h > innerHeight - 8) y = Math.max(8, r.top - h - 6);
  if (y < 8) y = 8;
  x = Math.min(Math.max(8, x), innerWidth - w - 8);
  m.style.left = `${x}px`; m.style.top = `${y}px`;
  menuAberto = m;
  setTimeout(() => {
    const fora = (e) => { if (!m.contains(e.target)) { fecharMenu(); document.removeEventListener('mousedown', fora); } };
    document.addEventListener('mousedown', fora);
  });
  m.querySelector('button')?.focus();
  return m;
}
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') fecharMenu(); });

// ---------- formatação ----------
export function usd(v, casas) {
  const n = Number(v || 0);
  const c = casas ?? (n !== 0 && n < 0.01 ? 4 : 2);
  const valor = n.toLocaleString(localidade(), { minimumFractionDigits: c, maximumFractionDigits: c });
  return emIngles() ? (n < 0 ? `-$${valor.slice(1)}` : `$${valor}`) : 'US$ ' + valor;
}
export function tokens(n) {
  n = Number(n || 0);
  if (n >= 1e6) return (n / 1e6).toLocaleString(localidade(), { maximumFractionDigits: 2 }) + (emIngles() ? 'M' : ' mi');
  if (n >= 1e3) return (n / 1e3).toLocaleString(localidade(), { maximumFractionDigits: 1 }) + (emIngles() ? 'K' : ' mil');
  return String(n);
}
export function dataBr(iso) {
  if (!iso) return '';
  const d = new Date(iso.length === 10 ? iso + 'T12:00:00' : iso);
  return d.toLocaleDateString(localidade());
}
// data e hora curtas (para tabelas de histórico)
export function dataHora(ts) {
  return new Date(ts * 1000).toLocaleString(localidade(), { dateStyle: 'short', timeStyle: 'short' });
}
// número inteiro com separador de milhar do idioma
export function numero(n) { return Number(n || 0).toLocaleString(localidade()); }
export function grupoData(ts) {
  const d = new Date(ts * 1000), hoje = new Date();
  const dia = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const dif = Math.round((dia(hoje) - dia(d)) / 86400000);
  if (dif <= 0) return t('Hoje');
  if (dif === 1) return t('Ontem');
  if (dif < 7) return t('Últimos 7 dias');
  if (dif < 30) return t('Últimos 30 dias');
  return d.toLocaleDateString(localidade(), { month: 'long', year: 'numeric' });
}

// Frase traduzida com elementos no meio: frase(textoTraduzido, { link: el('a', ...) }) troca cada {link} pelo
// elemento e devolve os pedaços (texto, elemento, texto) para passar ao el(). A frase inteira fica numa chave só.
export function frase(texto, elementos = {}) {
  return String(texto).split(/(\{\w+\})/).filter(Boolean).map((p) => {
    const m = /^\{(\w+)\}$/.exec(p);
    return m && m[1] in elementos ? elementos[m[1]] : p;
  });
}

export async function copiarTexto(texto, botao) {
  try {
    await navigator.clipboard.writeText(texto);
    if (botao) {
      const antes = botao.innerHTML;
      botao.innerHTML = ic('certo');
      setTimeout(() => { botao.innerHTML = antes; }, 1400);
    } else aviso(t('Copiado.'));
  } catch { aviso(t('Não deu para copiar.'), 'erro'); }
}

export function chaveLiga({ rotulo, ajuda, marcado, aoMudar, nome }) {
  const input = el('input', { type: 'checkbox', name: nome });
  input.checked = !!marcado;
  input.addEventListener('change', () => aoMudar?.(input.checked));
  return el('label', { class: 'chave-liga' }, input, el('span', { class: 'trilho' }),
    el('span', { class: 'textos' }, el('b', { texto: rotulo }), ajuda ? el('small', { texto: ajuda }) : null));
}

export function escolherArquivos({ multiplo = true, aceitar = '' } = {}) {
  return new Promise((ok) => {
    const i = el('input', { type: 'file', multiple: multiplo, accept: aceitar || null, style: 'display:none' });
    i.addEventListener('change', () => { ok([...i.files]); i.remove(); });
    document.body.append(i);
    i.click();
  });
}
