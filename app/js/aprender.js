// Aprender: as lições para quem nunca usou o Claude (nem nenhuma IA), em trilhas, e o glossário.
import { api } from './api.js';
import { refazerTours } from './tour.js';
import { estado, cfg } from './estado.js';
import { ic } from './icones.js';
import { el } from './ui.js';
import { renderizar } from './markdown.js';
import { criarMiniChat } from './minichat.js';
import { t, idioma } from './i18n.js';

let cache = null;

// O vídeo da lição: não vem dentro do app; o Clave baixa do GitHub uma vez (sozinho, em segundo plano, ou no play)
// e guarda no computador.
function playerVideo(vid) {
  const lingua = encodeURIComponent(idioma());
  const caixa = el('div', { class: 'video-licao' });
  // na demonstração o servidor não baixa nada sozinho; a lição também não: fica o botão
  const demo = !!estado.info?.demo;
  let espera = null;
  let mostrado = false;  // com o vídeo na tela, nenhuma resposta atrasada troca ele pela barra de progresso
  let rodada = 0;        // cada pergunta ao /estado ganha um número: só a resposta da última vale
  const mostrar = (tocar = false) => {
    clearTimeout(espera);
    rodada += 1;
    if (!mostrado) {
      mostrado = true;
      caixa.replaceChildren(el('video', { src: `/api/videos/${vid}?lingua=${lingua}`, controls: true, preload: 'metadata', playsinline: true }));
    }
    if (tocar) caixa.querySelector('video')?.play().catch(() => {});
  };
  // o app baixa os vídeos sozinho em segundo plano (Configurações > Atualizações): enquanto baixa, a lição mostra quanto
  // falta e troca para o vídeo quando termina
  const acompanhar = (r) => {
    const barra = el('div', { class: 'video-progresso', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': '100' },
      el('i', { style: `width:${Math.round((r.progresso ?? 0) * 100)}%` }));
    if (r.progresso != null) barra.setAttribute('aria-valuenow', String(Math.round(r.progresso * 100)));
    caixa.replaceChildren(el('div', { class: 'video-capa' },
      el('p', { class: 'ajuda', texto: r.progresso != null ? t('Baixando o vídeo… {pct}%', { pct: Math.round(r.progresso * 100) }) : t('Baixando o vídeo…') }),
      barra));
    clearTimeout(espera);
    espera = setTimeout(verificar, 1000);
  };
  const baixar = async (botao) => {
    if (botao) { botao.disabled = true; botao.innerHTML = `${ic('progresso')}${t('Baixando o vídeo…')}`; }
    clearTimeout(espera);
    espera = setTimeout(verificar, 800);
    try {
      await api(`/videos/${vid}/baixar?lingua=${lingua}`, { metodo: 'POST' });
      mostrar(!!botao);
    } catch (e) {
      if (mostrado) return;
      clearTimeout(espera);
      rodada += 1;  // uma resposta do /estado ainda a caminho não apaga o aviso de erro
      falhou(e.message);
    }
  };
  const falhou = (mensagem) => {
    caixa.replaceChildren(el('p', { class: 'ajuda', texto: t('Não deu para baixar o vídeo agora: {erro}', { erro: mensagem }) }),
      el('button', { class: 'botao pequeno', type: 'button', texto: t('Tentar de novo'), onclick: (ev) => baixar(ev.currentTarget) }));
  };
  const capa = (r) => {
    const botao = el('button', { class: 'botao primario', type: 'button', html: `${ic('olho')}${t('Assistir ao vídeo')}` });
    botao.addEventListener('click', () => baixar(botao));
    let texto = t('Na primeira vez o Clave baixa o vídeo do GitHub (alguns MB) e guarda neste computador.');
    if (r.parado) texto = t('O download foi parado na aba Tarefas. Clique para baixar de novo.');
    else if (r.erro) texto = t('Não deu para baixar o vídeo agora: {erro}', { erro: r.erro });
    caixa.replaceChildren(el('div', { class: 'video-capa' }, botao, el('small', { class: 'ajuda', texto })));
  };
  const verificar = () => {
    if (mostrado || (!caixa.isConnected && espera)) return;  // já mostrando o vídeo, ou saiu da lição
    const minha = ++rodada;
    api(`/videos/${vid}/estado?lingua=${lingua}`).then((r) => {
      if (mostrado || minha !== rodada) return;  // resposta velha: o vídeo (ou outra resposta) já chegou
      if (r.pronto) return mostrar();
      if (r.baixando) return acompanhar(r);
      // ainda não começou: começa já, menos na demonstração, depois de um erro ou de alguém parar na aba Tarefas
      if (!demo && cfg().baixar_videos !== false && !r.erro && !r.parado) return baixar(null);
      capa(r);
    }).catch(() => { if (!mostrado && minha === rodada) caixa.remove(); });
  };
  verificar();
  return caixa;
}

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
  for (const tut of tutoriais) {
    if (!trilhas.has(tut.trilha)) trilhas.set(tut.trilha, []);
    trilhas.get(tut.trilha).push(tut);
  }
  const total = tutoriais.length, ok = tutoriais.filter((tut) => feitos.includes(tut.slug)).length;
  let n = 0;
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: t('Aprender') }),
        el('p', { texto: t('Lições curtas para quem nunca usou o Claude. Comece pela primeira trilha; o foco é fazer o Claude trabalhar para você e do seu jeito. Cada lição tem botões para experimentar na hora.') })),
      el('span', { class: 'meta', texto: t('{ok} de {total} feitas', { ok, total }) }),
      el('button', { class: 'botao pequeno', type: 'button', texto: t('Refazer os tours'), title: t('Mostra de novo as setinhas que explicam cada parte do app'), onclick: () => refazerTours() })),
    ...[...trilhas.entries()].map(([nome, itens]) => el('section', { class: 'trilha' },
      el('div', { class: 'trilha-cab' }, el('h2', { texto: nome }), el('span', { class: 'meta', texto: t('{n} lições', { n: itens.length }) })),
      el('div', { class: 'grade-cartoes' }, ...itens.map((tut) => {
        n += 1;
        const feito = feitos.includes(tut.slug);
        return el('a', { class: `cartao ${feito ? 'feito' : ''}`, href: `#/aprender/${tut.slug}` },
          el('span', { class: 'licao-num', texto: String(n).padStart(2, '0') }),
          el('h3', { texto: tut.titulo }), el('p', { texto: tut.resumo }),
          el('span', { class: 'meta', texto: [tut.duracao, tut.video ? t('com vídeo') : '', feito ? t('feita') : ''].filter(Boolean).join(' · ') }));
      })))))));
  return {};
}

export async function telaLicao(principal, slug, alvo) {
  const [lic, idx] = await Promise.all([api(`/tutoriais/${slug}`), cache ? Promise.resolve(cache) : lista()]);
  const ordem = idx.tutoriais;
  const i = ordem.findIndex((x) => x.slug === slug);
  const ant = ordem[i - 1], prox = ordem[i + 1];
  const corpo = el('div', { class: 'resposta' });
  renderizar(corpo, lic.texto);
  transformarExperimentos(corpo);
  // "## API key {#chave-da-api}": a âncora fixa (a do título em português) vale nos dois idiomas
  corpo.querySelectorAll('h2, h3').forEach((h) => {
    const fixa = h.textContent.match(/\s*\{#([\w-]+)\}\s*$/);
    if (fixa) {
      h.id = fixa[1];
      const ultimo = [...h.childNodes].reverse().find((n) => n.nodeType === 3 && n.textContent.includes('{#'));
      if (ultimo) ultimo.textContent = ultimo.textContent.replace(/\s*\{#[\w-]+\}\s*$/, '');
    } else h.id = ancora(h.textContent);
  });
  const feito = idx.feitos.includes(slug);
  const botaoFeito = el('button', { class: `botao ${feito ? '' : 'primario'}`, type: 'button', html: `${ic('certo')}${feito ? t('Lição feita') : t('Marcar como feita')}`,
    onclick: async () => { const r = await api(`/tutoriais/${slug}/feito`, { metodo: 'POST' }); cache.feitos = r.feitos; botaoFeito.className = 'botao'; botaoFeito.innerHTML = `${ic('certo')}${t('Lição feita')}`; } });
  const ajudante = criarMiniChat({
    tipo: 'tutor', licao: slug,
    titulo: t('Ficou com dúvida? Pergunte ao ajudante'),
    descricao: t('Ele conhece esta lição e o glossário e explica com calma, do jeito mais simples. Roda no Haiku 5.5: cada pergunta custa uma fração de centavo.'),
    placeholder: t('Escreva a sua dúvida, do seu jeito. Ex.: não entendi o que é um token'),
    sugestoes: slug === 'glossario' ? [t('O que é JSON, com um exemplo?'), t('Qual a diferença entre Git e GitHub?')] : [t('Pode explicar de um jeito mais simples?'), t('Me dá um exemplo do dia a dia')],
  });
  const rolagem = el('div', { class: 'pagina' }, el('article', { class: 'leitor' },
    el('a', { class: 'botao pequeno fantasma voltar', href: '#/aprender', html: `${ic('esq')}${t('Todas as lições')}` }),
    el('div', { class: 'meta', texto: [lic.trilha, lic.duracao].filter(Boolean).join(' · ') }),
    el('h1', { texto: lic.titulo }),
    lic.video ? playerVideo(lic.video) : null,
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
      el('span', { class: 'rotulo-exp', texto: code ? t('Experimente no modo Code') : t('Experimente') }),
      el('blockquote', { texto }),
      el('button', { class: 'botao primario pequeno', type: 'button', html: `${ic(code ? 'terminal' : 'chat')}${code ? t('Abrir no Code com este pedido') : t('Mandar para uma conversa nova')}`,
        onclick: () => {
          sessionStorage.setItem('clave:rascunho', texto);
          location.hash = code ? '#/code' : '#/novo';
        } }));
    b.replaceWith(cartao);
  });
}

export function pegarRascunho() {
  const r = sessionStorage.getItem('clave:rascunho');
  if (r) sessionStorage.removeItem('clave:rascunho');
  return r;
}

export function temLicoes() { return !!estado.info; }
