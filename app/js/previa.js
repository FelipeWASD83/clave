// Painel lateral que mostra páginas HTML e desenhos SVG que o Claude escreveu.
import { api } from './api.js';
import { ic } from './icones.js';
import { el, aviso, copiarTexto } from './ui.js';
import { colorirCodigo } from './markdown.js';
import { t } from './i18n.js';

export async function abrirPrevia({ codigo, lingua }) {
  const painel = document.getElementById('painel-previa');
  const tipo = lingua === 'svg' || (lingua === 'xml' && /<svg[\s>]/i.test(codigo)) ? 'svg' : 'html';
  let url;
  try {
    url = (await api('/previa', { metodo: 'POST', corpo: { html: codigo, tipo } })).url;
  } catch (e) { aviso(e.message, 'erro'); return; }
  const quadro = el('iframe', { src: url, title: t('Prévia'), sandbox: 'allow-scripts allow-forms allow-popups allow-modals allow-downloads' });
  const cod = el('pre', { class: 'bloco-codigo', hidden: true, style: 'border-radius:0;border:0' }, el('code', { class: `language-${tipo === 'svg' ? 'xml' : 'html'}`, texto: codigo }));
  const alternar = el('div', { class: 'segmentado', role: 'group', 'aria-label': t('Ver') },
    el('button', { type: 'button', 'aria-pressed': 'true', texto: t('Prévia'), onclick: (e) => mostrar(true, e.currentTarget) }),
    el('button', { type: 'button', 'aria-pressed': 'false', texto: t('Código'), onclick: (e) => mostrar(false, e.currentTarget) }));
  function mostrar(previa, botao) {
    quadro.hidden = !previa; cod.hidden = previa;
    alternar.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b === botao)));
    if (!previa) colorirCodigo(cod);
  }
  painel.replaceChildren(
    el('header', { class: 'topo' },
      el('h1', { texto: tipo === 'svg' ? t('Desenho (SVG)') : t('Página (HTML)') }), alternar,
      el('button', { class: 'icone-botao', type: 'button', title: t('Copiar o código'), 'aria-label': t('Copiar o código'), html: ic('copiar'), onclick: (e) => copiarTexto(codigo, e.currentTarget) }),
      el('button', { class: 'icone-botao', type: 'button', title: t('Baixar como arquivo'), 'aria-label': t('Baixar'), html: ic('baixar'), onclick: () => baixar(codigo, tipo) }),
      el('button', { class: 'icone-botao', type: 'button', title: t('Abrir no navegador'), 'aria-label': t('Abrir no navegador'), html: ic('externo'),
        onclick: () => { const u = location.origin + url; if (window.clave?.abrirExterno) window.clave.abrirExterno(u); else window.open(u, '_blank', 'noopener'); } }),
      el('button', { class: 'icone-botao', type: 'button', title: t('Fechar'), 'aria-label': t('Fechar a prévia'), html: ic('x'), onclick: fecharPrevia })),
    quadro, cod);
  painel.hidden = false;
}

function baixar(codigo, tipo) {
  const blob = new Blob([codigo], { type: tipo === 'svg' ? 'image/svg+xml' : 'text/html' });
  const a = el('a', { href: URL.createObjectURL(blob), download: tipo === 'svg' ? t('desenho.svg') : t('pagina.html') });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

export function fecharPrevia() {
  const painel = document.getElementById('painel-previa');
  painel.hidden = true;
  painel.replaceChildren();
}
