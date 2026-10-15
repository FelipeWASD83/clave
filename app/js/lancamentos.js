// Modelos: o banner de modelo novo no início, os cartões "Modelos" (como os do site da Anthropic, com
// ilustrações próprias) e o cartão de apresentação de cada modelo. As fichas vêm de /api/modelos/lancamentos.
import { api } from './api.js';
import { salvarConfig, cfg } from './estado.js';
import { ic } from './icones.js';
import { t } from './i18n.js';
import { el, usd, dataBr, aviso } from './ui.js';
import { tourVindo } from './tour.js';

const ilustracao = (familia) => el('div', { class: `modelo-arte familia-${familia || 'outro'}` },
  familia ? el('img', { src: `img/modelos/${familia}.svg`, alt: '' }) : el('span', { html: ic('faisca') }));

function linhaPreco(f) {
  const agora = t('Entrada {entrada} · saída {saida} por milhão de tokens', { entrada: usd(f.entrada, 2), saida: usd(f.saida, 2) });
  if (!f.anterior) return agora;
  return `${agora} ${t('(o {nome} custava {entrada} e {saida})', { nome: f.anterior.nome, entrada: usd(f.anterior.entrada, 2), saida: usd(f.anterior.saida, 2) })}`;
}

async function usarComoPadrao(f) {
  await salvarConfig({ modelo_chat: f.id, modelo_code: f.id });
  aviso(t('{nome} agora é o modelo padrão do chat e do Code.', { nome: f.nome }));
}

async function dispensar(id) {
  const vistos = new Set(cfg().modelos_vistos || []);
  vistos.add(id);
  await salvarConfig({ modelos_vistos: [...vistos] });
}

// O cartão de apresentação: a render da família no topo com o nome por cima e, embaixo, o que o modelo é, o que
// mudou, o preço ao lado dos outros modelos e a nota de inteligência de todos na mesma régua.
let pedidoFichas = null;
const dadosModelos = () => (pedidoFichas ||= api('/modelos/lancamentos').catch((e) => { pedidoFichas = null; throw e; }));

export async function janelaModelo(f) {
  let dados = { fichas: [f], inteligencia: {} };
  try { dados = await dadosModelos(); } catch { /* sem a lista, o cartão mostra só este modelo */ }
  apresentarModelo(f, dados.fichas?.length ? dados.fichas : [f], dados.inteligencia || {});
}

function apresentarModelo(f, todas, fonteNota) {
  if (document.querySelector('.apresentacao-fundo')) return;
  const anterior = document.activeElement;
  const fechar = () => {
    fundo.classList.add('saindo');
    removeEventListener('keydown', teclas, true);
    setTimeout(() => fundo.remove(), 180);
    anterior?.focus?.({ preventScroll: true });
  };
  const teclas = (e) => { if (e.key === 'Escape') { e.preventDefault(); fechar(); } };
  const coluna = (m) => ({ class: m.id === f.id ? 'atual' : '' });
  const nomeCurto = (m) => m.nome.replace(/^Claude\s+/, '');
  const preco = (v) => usd(v, Number.isInteger(v) ? 0 : 2);   // US$ 20 e US$ 0,10: cabe no celular
  const comNota = todas.filter((m) => typeof m.inteligencia === 'number');
  const cols = `grid-template-columns: auto repeat(${todas.length}, minmax(0, 1fr))`;

  const botaoFechar = el('button', { class: 'apresentacao-fechar', type: 'button', title: t('Fechar'), 'aria-label': t('Fechar'), html: ic('x'), onclick: fechar });
  const cartao = el('article', { class: `apresentacao familia-${f.familia || 'outro'}` },
    el('header', { class: 'apresentacao-capa', style: f.render ? `background-image: url("${f.render}")` : '' },
      botaoFechar,
      el('h2', { class: 'apresentacao-nome', texto: nomeCurto(f) })),
    el('div', { class: 'apresentacao-corpo' },
      el('div', { class: 'apresentacao-rotulo' },
        f.novo ? el('span', { class: 'apresentacao-novo', texto: t('Novo') }) : null,
        f.lancado_em ? el('span', { texto: t('Lançado em {data}', { data: dataBr(f.lancado_em) }) }) : null),
      el('h3', { texto: `Claude ${nomeCurto(f)}` }),
      el('p', { class: 'apresentacao-resumo', texto: f.resumo }),
      f.novidades.length ? el('ul', { class: 'apresentacao-lista' }, ...f.novidades.map((n) => el('li', { texto: n }))) : null,

      el('h4', {}, t('Preços'), el('small', { texto: t('por milhão de tokens') })),
      el('div', { class: 'apresentacao-grade', style: cols, role: 'table', 'aria-label': t('Preços') },
        el('span', { role: 'columnheader' }), ...todas.map((m) => el('span', { ...coluna(m), role: 'columnheader', texto: nomeCurto(m) })),
        el('span', { class: 'rotulo-linha', role: 'rowheader', texto: t('Entrada') }), ...todas.map((m) => el('b', { ...coluna(m), role: 'cell', texto: preco(m.entrada) })),
        el('span', { class: 'rotulo-linha', role: 'rowheader', texto: t('Saída') }), ...todas.map((m) => el('b', { ...coluna(m), role: 'cell', texto: preco(m.saida) }))),
      f.anterior ? el('p', { class: 'meta', texto: t('O {nome} custava {entrada} e {saida}.', { nome: f.anterior.nome, entrada: preco(f.anterior.entrada), saida: preco(f.anterior.saida) }) }) : null,

      comNota.length ? el('h4', { texto: t('Inteligência') }) : null,
      comNota.length ? el('div', { class: 'apresentacao-barras', style: `grid-template-columns: repeat(${comNota.length}, minmax(0, 1fr))` },
        ...comNota.map((m) => el('div', { class: `barra ${m.id === f.id ? 'atual' : ''}`, title: `${m.nome}: ${m.inteligencia}/100` },
          el('span', { class: 'barra-nome', texto: nomeCurto(m) }),
          el('div', { class: 'barra-trilho' }, el('div', { class: 'barra-valor', style: `height: ${Math.max(4, Math.min(100, m.inteligencia))}%` })),
          el('b', { texto: `${m.inteligencia}/100` })))) : null,
      comNota.length && fonteNota.nota ? el('p', { class: 'meta' }, fonteNota.nota + ' ',
        fonteNota.url ? el('a', { href: fonteNota.url, target: '_blank', rel: 'noopener', texto: t('Ver o ranking') }) : null) : null,

      el('div', { class: 'apresentacao-acoes' },
        el('button', { class: 'botao primario', type: 'button', texto: t('Usar como padrão'), onclick: async () => { await usarComoPadrao(f); fechar(); } }),
        f.pagina || f.fonte ? el('a', { class: 'botao fantasma', href: f.pagina || f.fonte, target: '_blank', rel: 'noopener', texto: t('Página do lançamento') }) : null)));
  const fundo = el('div', { class: 'apresentacao-fundo', role: 'dialog', 'aria-modal': 'true', 'aria-label': `Claude ${nomeCurto(f)}` }, cartao);
  fundo.addEventListener('click', (e) => { if (e.target === fundo) fechar(); });
  addEventListener('keydown', teclas, true);
  document.body.append(fundo);
  botaoFechar.focus({ preventScroll: true });
}

// Modelo lançado há pouco: o cartão abre sozinho uma vez (depois do tour, se ele estiver aberto). Some-se a isso o
// banner do início, que fica até a pessoa fechar.
export async function apresentarNovidade() {
  if (!cfg().configurado) return;
  let dados;
  try { dados = await dadosModelos(); } catch { return; }
  const ja = new Set(cfg().modelos_apresentados || []);
  const f = (dados.novos || []).find((m) => !ja.has(m.id));
  if (!f) return;
  // com um tour aberto ou para abrir, o cartão fica para depois: o main.js chama de novo quando o tour fecha
  if (tourVindo() || document.querySelector('.tour-camada')) return;
  ja.add(f.id);
  salvarConfig({ modelos_apresentados: [...ja] }).catch(() => {});
  apresentarModelo(f, dados.fichas?.length ? dados.fichas : [f], dados.inteligencia || {});
}

// o banner do início: o modelo lançado há menos de 14 dias, ou um que a conta tem e o Clave ainda não conhece
export function bannerModeloNovo() {
  const caixa = el('div', { class: 'banner-modelo-vaga' });
  api('/modelos/lancamentos').then((d) => {
    const f = d.novos?.[0];
    if (f) return caixa.replaceWith(bannerFicha(f));
    const x = d.desconhecidos?.[0];
    if (x) return caixa.replaceWith(bannerDesconhecido(x));
    caixa.remove();
  }).catch(() => caixa.remove());
  return caixa;
}

function bannerFicha(f) {
  const banner = el('section', { class: 'banner-modelo', 'aria-label': t('Modelo novo') },
    ilustracao(f.familia),
    el('div', { class: 'banner-corpo' },
      el('div', { class: 'banner-rotulo' }, el('span', { class: 'selo-novo', texto: t('Novo') }),
        el('span', { texto: t('Lançado em {data}', { data: dataBr(f.lancado_em) }) })),
      el('h3', { texto: f.nome }),
      el('div', { class: 'modelo-etiquetas' }, ...f.etiquetas.map((e) => el('span', { class: 'etiqueta', texto: e }))),
      el('p', { class: 'banner-resumo', texto: f.resumo }),
      f.novidades.length ? el('ul', { class: 'banner-novidades' }, ...f.novidades.slice(0, 3).map((n) => el('li', { texto: n }))) : null,
      el('p', { class: 'meta', texto: linhaPreco(f) }),
      el('div', { class: 'banner-acoes' },
        el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Usar como padrão'), onclick: () => usarComoPadrao(f) }),
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Ver tudo'), onclick: () => janelaModelo(f) }))),
    el('button', { class: 'icone-botao banner-fechar', type: 'button', title: t('Fechar'), 'aria-label': t('Fechar'), html: ic('x'),
      onclick: async () => { banner.remove(); await dispensar(f.id); } }));
  return banner;
}

function bannerDesconhecido(m) {
  const banner = el('section', { class: 'banner-modelo compacto', 'aria-label': t('Modelo novo na sua conta') },
    ilustracao(''),
    el('div', { class: 'banner-corpo' },
      el('div', { class: 'banner-rotulo' }, el('span', { class: 'selo-novo', texto: t('Novo') }),
        el('span', { texto: m.criado_em ? t('Na sua conta desde {data}', { data: dataBr(m.criado_em) }) : t('Na sua conta') })),
      el('h3', { texto: m.nome }),
      el('p', { class: 'banner-resumo', texto: t('Este modelo já está disponível na sua conta da Anthropic, mas o Clave ainda não tem o preço e os detalhes dele. Eles chegam numa atualização do Clave.') }),
      el('div', { class: 'banner-acoes' },
        el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Procurar atualização'), onclick: async () => {
          const { checarAtualizacao } = await import('./atualizar.js');
          checarAtualizacao({ silencioso: false });
        } }))),
    el('button', { class: 'icone-botao banner-fechar', type: 'button', title: t('Fechar'), 'aria-label': t('Fechar'), html: ic('x'),
      onclick: async () => { banner.remove(); await dispensar(m.id); } }));
  return banner;
}

// a fileira "Modelos" de Preços e planos
export function cartoesModelos(fichas) {
  return el('div', { class: 'cartoes-modelos' }, ...fichas.map((f) => el('button', { class: 'cartao-modelo', type: 'button', onclick: () => janelaModelo(f) },
    ilustracao(f.familia),
    el('div', { class: 'cartao-modelo-corpo' },
      el('div', { class: 'cartao-modelo-nome' }, el('b', { texto: f.nome }), f.novo ? el('span', { class: 'selo-novo', texto: t('Novo') }) : null),
      el('div', { class: 'modelo-etiquetas' }, ...f.etiquetas.map((e) => el('span', { class: 'etiqueta', texto: e })))))));
}
