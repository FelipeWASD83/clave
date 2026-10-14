// Aprender: as lições para quem nunca usou o Claude (nem nenhuma IA), em trilhas, e o glossário.
import { api } from './api.js';
import { estado } from './estado.js';
import { ic } from './icones.js';
import { el } from './ui.js';
import { renderizar } from './markdown.js';
import { criarMiniChat } from './minichat.js';

let cache = null;

export function ancora(texto) {
  return texto.normalize('NFKD').replace(/[̀-ͯ]/g, '').toLowerCase()
    .replace(/\([^)]*\)/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

async function lista() {
  cache = await api('/tutoriais');
  return cache;
}

export async function telaAprender(principal) {
  const { tutoriais, feitos } = await lista();
  const trilhas = new Map();
  for (const t of tutoriais) {
    if (!trilhas.has(t.trilha)) trilhas.set(t.trilha, []);
    trilhas.get(t.trilha).push(t);
  }
  const total = tutoriais.length, ok = tutoriais.filter((t) => feitos.includes(t.slug)).length;
  let n = 0;
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: 'Aprender' }),
        el('p', { texto: 'Lições curtas para quem nunca usou o Claude. Comece pela primeira trilha; o foco é fazer o Claude trabalhar para você e do seu jeito. Cada lição tem botões para experimentar na hora.' })),
      el('span', { class: 'meta', texto: `${ok} de ${total} feitas` })),
    ...[...trilhas.entries()].map(([nome, itens]) => el('section', { class: 'trilha' },
      el('div', { class: 'trilha-cab' }, el('h2', { texto: nome }), el('span', { class: 'meta', texto: `${itens.length} lições` })),
      el('div', { class: 'grade-cartoes' }, ...itens.map((t) => {
        n += 1;
        const feito = feitos.includes(t.slug);
        return el('a', { class: `cartao ${feito ? 'feito' : ''}`, href: `#/aprender/${t.slug}` },
          el('span', { class: 'licao-num', texto: String(n).padStart(2, '0') }),
          el('h3', { texto: t.titulo }), el('p', { texto: t.resumo }),
          el('span', { class: 'meta', texto: [t.duracao, feito ? 'feita' : ''].filter(Boolean).join(' · ') }));
      })))))));
  return {};
}

export async function telaLicao(principal, slug, alvo) {
  const [t, idx] = await Promise.all([api(`/tutoriais/${slug}`), cache ? Promise.resolve(cache) : lista()]);
  const ordem = idx.tutoriais;
  const i = ordem.findIndex((x) => x.slug === slug);
  const ant = ordem[i - 1], prox = ordem[i + 1];
  const corpo = el('div', { class: 'resposta' });
  renderizar(corpo, t.texto);
  transformarExperimentos(corpo);
  corpo.querySelectorAll('h2, h3').forEach((h) => { h.id = ancora(h.textContent); });
  const feito = idx.feitos.includes(slug);
  const botaoFeito = el('button', { class: `botao ${feito ? '' : 'primario'}`, type: 'button', html: `${ic('certo')}${feito ? 'Lição feita' : 'Marcar como feita'}`,
    onclick: async () => { const r = await api(`/tutoriais/${slug}/feito`, { metodo: 'POST' }); cache.feitos = r.feitos; botaoFeito.className = 'botao'; botaoFeito.innerHTML = `${ic('certo')}Lição feita`; } });
  const ajudante = criarMiniChat({
    tipo: 'tutor', licao: slug,
    titulo: 'Ficou com dúvida? Pergunte ao ajudante',
    descricao: 'Ele conhece esta lição e o glossário e explica com calma, do jeito mais simples. Roda no Haiku 5.5: cada pergunta custa uma fração de centavo.',
    placeholder: 'Escreva a sua dúvida, do seu jeito. Ex.: não entendi o que é um token',
    sugestoes: slug === 'glossario' ? ['O que é JSON, com um exemplo?', 'Qual a diferença entre Git e GitHub?'] : ['Pode explicar de um jeito mais simples?', 'Me dá um exemplo do dia a dia'],
  });
  const rolagem = el('div', { class: 'pagina' }, el('article', { class: 'leitor' },
    el('a', { class: 'botao pequeno fantasma voltar', href: '#/aprender', html: `${ic('esq')}Todas as lições` }),
    el('div', { class: 'meta', texto: [t.trilha, t.duracao].filter(Boolean).join(' · ') }),
    el('h1', { texto: t.titulo }),
    corpo,
    ajudante.elemento,
    el('div', { class: 'leitor-rodape' },
      ant ? el('a', { class: 'botao', href: `#/aprender/${ant.slug}`, html: `${ic('esq')}${ant.titulo}` }) : el('span'),
      botaoFeito,
      prox ? el('a', { class: 'botao', href: `#/aprender/${prox.slug}`, html: `${prox.titulo}${ic('dir')}` }) : el('span'))));
  principal.replaceChildren(rolagem);
  telaAtualLicao = ajudante;
  if (alvo) {
    const h = corpo.querySelector(`#${CSS.escape(alvo)}`);
    if (h) {
      h.scrollIntoView({ block: 'start' });
      h.style.background = 'var(--acao-suave)';
      h.style.borderRadius = '6px';
      setTimeout(() => { h.style.transition = 'background 1.2s'; h.style.background = 'transparent'; }, 1500);
    }
  } else rolagem.scrollTop = 0;
  return { sair: () => telaAtualLicao?.parar() };
}

let telaAtualLicao = null;

// Blocos ```experimentar viram um cartão com botão que leva o texto para uma conversa nova.
function transformarExperimentos(raiz) {
  raiz.querySelectorAll('.bloco-codigo').forEach((b) => {
    const lingua = b.dataset.lingua;
    if (lingua !== 'experimentar' && lingua !== 'experimentar-code') return;
    const texto = b.querySelector('pre code').textContent.trim();
    const code = lingua === 'experimentar-code';
    const cartao = el('div', { class: 'experimentar' },
      el('span', { class: 'rotulo-exp', texto: code ? 'Experimente no modo Code' : 'Experimente' }),
      el('blockquote', { texto }),
      el('button', { class: 'botao primario pequeno', type: 'button', html: `${ic(code ? 'terminal' : 'chat')}${code ? 'Abrir no Code com este pedido' : 'Mandar para uma conversa nova'}`,
        onclick: () => {
          sessionStorage.setItem('clave:rascunho', texto);
          location.hash = code ? '#/code' : '#/novo';
        } }));
    b.replaceWith(cartao);
  });
}

export function pegarRascunho() {
  const t = sessionStorage.getItem('clave:rascunho');
  if (t) sessionStorage.removeItem('clave:rascunho');
  return t;
}

export function temLicoes() { return !!estado.info; }
