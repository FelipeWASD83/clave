// Markdown das respostas: marked + DOMPurify + cores de código + fórmulas (KaTeX, carregado só quando aparece).
import { Marked } from '../vendor/marked/marked.esm.js';
import DOMPurify from '../vendor/dompurify/purify.es.mjs';
import hljs from '../vendor/highlight/highlight.min.js';
import { ic } from './icones.js';
import { esc } from './ui.js';

const PREVIAVEIS = new Set(['html', 'svg', 'xml']);

const marked = new Marked({
  gfm: true,
  breaks: false,
  renderer: {
    code({ text, lang }) {
      const lingua = String(lang || '').trim().split(/\s+/)[0].toLowerCase();
      const previa = PREVIAVEIS.has(lingua) && (lingua !== 'xml' || /<svg[\s>]/i.test(text));
      return `<div class="bloco-codigo" data-lingua="${esc(lingua)}">`
        + `<div class="bloco-codigo-topo"><span class="lingua">${esc(lingua || 'texto')}</span>`
        + (previa ? `<button type="button" data-acao="previa">${ic('olho')}Prévia</button>` : '')
        + `<button type="button" data-acao="copiar-codigo">${ic('copiar')}Copiar</button></div>`
        + `<pre><code class="${lingua ? 'language-' + esc(lingua) : ''}">${esc(text)}</code></pre></div>`;
    },
    link({ href, title, tokens }) {
      const texto = this.parser.parseInline(tokens);
      if (String(href).startsWith('#/')) {
        // link para dentro do app (lições do Aprender, por exemplo)
        return `<a href="${esc(href)}" class="link-interno"${title ? ` title="${esc(title)}"` : ''}>${texto}</a>`;
      }
      return `<a href="${esc(href)}" target="_blank" rel="noopener noreferrer"${title ? ` title="${esc(title)}"` : ''}>${texto}</a>`;
    },
  },
});

DOMPurify.addHook('afterSanitizeAttributes', (no) => {
  if (no.tagName !== 'A') return;
  const href = no.getAttribute('href') || '';
  if (href.startsWith('#/')) { no.removeAttribute('target'); no.classList.add('link-interno'); return; }
  no.setAttribute('target', '_blank'); no.setAttribute('rel', 'noopener noreferrer');
});

const PURIFY = { ADD_ATTR: ['target', 'data-acao', 'data-lingua', 'data-i'], FORBID_TAGS: ['style', 'form', 'input', 'textarea', 'select', 'button'], FORBID_ATTR: ['style'] };
const PURIFY_COM_BOTOES = { ...PURIFY, FORBID_TAGS: ['style', 'form', 'input', 'textarea', 'select'] };

// Separa código (que não pode virar fórmula) do resto e extrai as fórmulas.
function protegerFormulas(md) {
  const codigos = [];
  let t = md.replace(/(^|\n)(```|~~~)[^\n]*\n[\s\S]*?(\n\2[ \t]*(?=\n|$)|$)/g, (m) => { codigos.push(m); return `\u0000C${codigos.length - 1}\u0000`; });
  t = t.replace(/`[^`\n]+`/g, (m) => { codigos.push(m); return `\u0000C${codigos.length - 1}\u0000`; });
  const formulas = [];
  const guardar = (tex, bloco) => { formulas.push({ tex, bloco }); return `<span class="mat" data-i="${formulas.length - 1}"></span>`; };
  t = t.replace(/\$\$([\s\S]+?)\$\$/g, (_, tex) => guardar(tex, true));
  t = t.replace(/\\\[([\s\S]+?)\\\]/g, (_, tex) => guardar(tex, true));
  t = t.replace(/\\\(([\s\S]+?)\\\)/g, (_, tex) => guardar(tex, false));
  t = t.replace(/(^|[^\\$\w])\$(?!\s)([^$\n]+?)(?<!\s)\$(?![\d\w])/g, (m, antes, tex) => antes + guardar(tex, false));
  t = t.replace(/\u0000C(\d+)\u0000/g, (_, i) => codigos[+i]);
  return { texto: t, formulas };
}

let katex = null;
let carregandoKatex = null;
function carregarKatex() {
  if (katex) return Promise.resolve(katex);
  if (!carregandoKatex) {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = 'vendor/katex/katex.min.css';
    document.head.append(link);
    carregandoKatex = import('../vendor/katex/katex.mjs').then((m) => { katex = m.default; return katex; });
  }
  return carregandoKatex;
}

function aplicarFormulas(raiz, formulas) {
  if (!formulas.length) return;
  const pintar = (k) => {
    raiz.querySelectorAll('span.mat').forEach((s) => {
      const f = formulas[+s.dataset.i];
      if (!f) return;
      try {
        k.render(f.tex, s, { displayMode: f.bloco, throwOnError: false, output: 'html', strict: 'ignore' });
      } catch { s.textContent = f.tex; }
    });
  };
  if (katex) pintar(katex);
  else {
    raiz.querySelectorAll('span.mat').forEach((s) => { const f = formulas[+s.dataset.i]; if (f) s.textContent = f.tex; });
    carregarKatex().then(pintar).catch(() => {});
  }
}

export function colorirCodigo(raiz) {
  raiz.querySelectorAll('pre code').forEach((c) => {
    if (c.dataset.colorido) return;
    const m = /language-([\w+#-]+)/.exec(c.className);
    try {
      if (m && hljs.getLanguage(m[1])) c.innerHTML = hljs.highlight(c.textContent, { language: m[1], ignoreIllegals: true }).value;
      else if (c.textContent.length < 20000 && !m) { /* texto puro: sem cor */ }
    } catch { /* deixa sem cor */ }
    c.dataset.colorido = '1';
  });
}

// Renderiza markdown dentro do elemento. `final` = a resposta terminou (aí colore o código).
export function renderizar(alvo, md, { final = true } = {}) {
  const { texto, formulas } = protegerFormulas(md || '');
  const html = marked.parse(texto);
  alvo.innerHTML = DOMPurify.sanitize(html, PURIFY_COM_BOTOES);
  aplicarFormulas(alvo, formulas);
  if (final) colorirCodigo(alvo);
}

export function markdownSeguro(md) {
  const div = document.createElement('div');
  renderizar(div, md);
  return div;
}

export const purificar = (html) => DOMPurify.sanitize(html, PURIFY);
