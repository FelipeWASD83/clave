// Os painéis do início: o seu uso (tokens, dias seguidos, mapa de calor, modelo favorito, últimos 7 dias e a
// projeção do mês) e, no Code, os ambientes (a pasta em que o Claude trabalha e o modo automático).
import { api } from './api.js';
import { cfg, salvarConfig, estado } from './estado.js';
import { ic } from './icones.js';
import { el, usd, tokens, aviso, menu, numero } from './ui.js';
import { t, localidade } from './i18n.js';
import { textoProjecao } from './precos.js';
import { escolherPasta, criarPastaComModelo } from './pastas.js';

// mês e dia da semana curtos no idioma da interface ("out", "seg" / "Oct", "Mon"), sem o ponto do pt-BR
const mesCurto = (d) => d.toLocaleDateString(localidade(), { month: 'short' }).replace('.', '');
const diaCurto = (d) => d.toLocaleDateString(localidade(), { weekday: 'short' }).replace('.', '');

// cor de cada família de modelo nos gráficos (a mesma em todo lugar)
export function corModelo(id = '') {
  if (id.includes('opus')) return 'var(--cor-opus)';
  if (id.includes('sonnet')) return 'var(--cor-sonnet)';
  if (id.includes('haiku')) return 'var(--cor-haiku)';
  if (id.includes('fable') || id.includes('mythos')) return 'var(--cor-fable)';
  return 'var(--texto-3)';
}

function nomeDia(iso) {
  const d = new Date(iso + 'T12:00:00');
  return t('{semana}, {dia} de {mes}', { semana: diaCurto(d), dia: d.getDate(), mes: mesCurto(d) });
}

export function painelUso() {
  if (cfg().painel_uso_inicio === false) return null;
  const caixa = el('section', { class: 'painel-uso carregando', 'aria-label': t('Seu uso') },
    el('div', { class: 'painel-cab' }, el('h2', { texto: t('Seu uso') })));
  api('/uso/painel').then(({ painel: p, orcamento: o }) => desenhar(caixa, p, o)).catch(() => caixa.remove());
  return caixa;
}

function desenhar(caixa, p, o) {
  caixa.classList.remove('carregando');
  const esconder = el('button', { class: 'icone-botao', type: 'button', title: t('Esconder este painel'), 'aria-label': t('Esconder este painel'), html: ic('x'),
    onclick: async () => { caixa.remove(); await salvarConfig({ painel_uso_inicio: false }); aviso(t('Painel escondido. Dá para mostrar de novo em Configurações > Aparência.')); } });
  const pct = o.teto ? Math.min(100, o.porcentagem) : 0;

  const blocos = [
    bloco('faisca', t('Tokens no total'), tokens(p.tokens_total), t('{respostas} respostas · {gasto}', { respostas: numero(p.pedidos_total), gasto: usd(p.gasto_total, 2) })),
    bloco('chama', t('Dias seguidos'), p.dias_seguidos === 1 ? t('{n} dia', { n: p.dias_seguidos }) : t('{n} dias', { n: p.dias_seguidos }),
      p.recorde ? t('recorde: {recorde} · {dias} dias de uso', { recorde: p.recorde, dias: p.dias_usados }) : t('comece hoje')),
    bloco('estrela', t('Modelo favorito'), p.favorito ? p.favorito.nome : t('nenhum ainda'), p.favorito ? t('{pct}% das respostas em 30 dias', { pct: p.favorito.porcentagem }) : t('nos últimos 30 dias')),
    el('div', { class: 'painel-bloco' },
      el('div', { class: 'painel-rotulo', html: `${ic('grafico')}<span>${t('Este mês')}</span>` }),
      el('div', { class: 'painel-numero', texto: usd(o.gasto, 2) }),
      o.teto ? el('div', { class: `medidor fino ${pct >= 100 ? 'cheio' : pct >= 80 ? 'alerta' : ''}` }, el('i', { style: `width:${pct}%` })) : null,
      el('div', { class: 'painel-sub', texto: o.teto ? t('de {teto} ({pct}%)', { teto: usd(o.teto, 2), pct: pct.toFixed(0) }) : t('sem teto definido') })),
  ];

  caixa.replaceChildren(
    el('div', { class: 'painel-cab' }, el('h2', { texto: t('Seu uso') }),
      el('a', { href: '#/uso', texto: t('Uso e gasto') }), el('a', { href: '#/precos', texto: t('Preços e planos') }), esconder),
    el('div', { class: 'painel-blocos' }, ...blocos),
    el('div', { class: 'painel-graficos' }, mapaDeCalor(p.mapa), seteDias(p)),
    el('p', { class: 'painel-projecao', html: `${ic('relogio')}` }, el('span', { texto: textoProjecao(p.projecao) })));
}

function bloco(icone, rotulo, numero, sub) {
  return el('div', { class: 'painel-bloco' },
    el('div', { class: 'painel-rotulo', html: `${ic(icone)}<span>${rotulo}</span>` }),
    el('div', { class: 'painel-numero', texto: numero }),
    el('div', { class: 'painel-sub', texto: sub }));
}

// um quadrado por dia, colunas de semanas (segunda em cima); a cor fica mais forte quanto mais tokens no dia
function mapaDeCalor(mapa) {
  const usados = mapa.map((d) => d.tokens).filter((t) => t > 0).sort((a, b) => a - b);
  const corte = (q) => usados.length ? usados[Math.min(usados.length - 1, Math.floor(q * usados.length))] : 0;
  const cortes = [corte(0.25), corte(0.5), corte(0.75)];
  const nivel = (t) => !t ? 0 : t <= cortes[0] ? 1 : t <= cortes[1] ? 2 : t <= cortes[2] ? 3 : 4;
  const semanas = [];
  for (let i = 0; i < mapa.length; i += 7) semanas.push(mapa.slice(i, i + 7));
  const meses = semanas.map((s, i) => {
    const data = new Date(s[0].dia + 'T12:00:00');
    const m = data.getMonth();
    const antes = i ? new Date(semanas[i - 1][0].dia + 'T12:00:00').getMonth() : -1;
    return el('span', { texto: m !== antes ? mesCurto(data) : '' });
  });
  return el('div', { class: 'mapa-calor' },
    el('div', { class: 'grafico-titulo', texto: t('Dias de uso nas últimas {n} semanas', { n: semanas.length }) }),
    el('div', { class: 'mapa-meses', style: `grid-template-columns:repeat(${semanas.length}, 1fr)` }, ...meses),
    el('div', { class: 'mapa-grade', role: 'img', 'aria-label': t('Uso por dia nas últimas {n} semanas', { n: semanas.length }), style: `grid-template-columns:repeat(${semanas.length}, 1fr)` },
      ...semanas.map((s) => el('div', { class: 'mapa-semana' }, ...s.map((d) => el('i', {
        class: `n${nivel(d.tokens)}`,
        title: `${nomeDia(d.dia)}: ${d.tokens ? usoDoDia(d) : t('sem uso')}`,
      }))))),
    el('div', { class: 'mapa-legenda' }, el('span', { texto: t('menos') }), ...[0, 1, 2, 3, 4].map((n) => el('i', { class: `n${n}` })), el('span', { texto: t('mais') })));
}

function usoDoDia(d) {
  const v = { tokens: tokens(d.tokens), n: d.pedidos, valor: usd(d.usd) };
  return d.pedidos === 1 ? t('{tokens} tokens, {n} pedido, {valor}', v) : t('{tokens} tokens, {n} pedidos, {valor}', v);
}

// barras empilhadas dos últimos 7 dias, uma cor por modelo
function seteDias(p) {
  const totalDia = p.dias7.map((_, i) => p.ultimos7.reduce((s, m) => s + m.tokens[i], 0));
  const maior = Math.max(1, ...totalDia);
  return el('div', { class: 'sete-dias' },
    el('div', { class: 'grafico-titulo', texto: t('Cada modelo nos últimos 7 dias') }),
    el('div', { class: 'sete-barras', role: 'img', 'aria-label': t('Tokens por modelo em cada um dos últimos 7 dias') },
      ...p.dias7.map((dia, i) => el('div', { class: 'sete-coluna', title: `${nomeDia(dia)}: ${tokens(totalDia[i])} tokens` },
        el('div', { class: 'sete-pilha', style: `height:${(totalDia[i] / maior) * 100}%` },
          ...p.ultimos7.filter((m) => m.tokens[i]).map((m) => el('i', { style: `flex:${m.tokens[i]};background:${corModelo(m.modelo)}`, title: `${m.nome}: ${tokens(m.tokens[i])} tokens` }))),
        el('span', { texto: diaCurto(new Date(dia + 'T12:00:00')) })))),
    p.ultimos7.length ? el('ul', { class: 'sete-legenda' }, ...p.ultimos7.map((m) => el('li', {},
      el('i', { style: `background:${corModelo(m.modelo)}` }), el('span', { texto: m.nome }),
      el('small', { texto: `${tokens(m.tokens.reduce((a, b) => a + b, 0))} · ${usd(m.usd)}` }))))
      : el('p', { class: 'painel-sub', texto: t('Nada nos últimos 7 dias.') }));
}

// ---------- ambientes do Code ----------

function nomePasta(c) { return c.split(/[\\/]/).filter(Boolean).pop() || c; }

// atual: a pasta escolhida; aoEscolher(caminho); auto: se o modo automático (Livre) está ligado; aoAuto(ligado)
export function painelAmbientes({ atual, aoEscolher, auto, aoAuto }) {
  const recentes = (cfg().pastas_recentes || []).slice(0, 6);
  if (atual && !recentes.includes(atual)) recentes.unshift(atual);
  const botaoEscolher = el('button', { class: 'ambiente-escolher', type: 'button', 'aria-haspopup': 'menu' },
    el('span', { texto: recentes.length ? t('Escolher ambiente') : t('Escolher a pasta de trabalho') }), el('span', { html: ic('baixo') }));
  botaoEscolher.addEventListener('click', () => menu(botaoEscolher, [
    { texto: t('Outra pasta…'), sub: t('Uma pasta do computador'), icone: 'pasta', acao: async () => aoEscolher(await escolherPasta()) },
    estado.info.modelo_de_pasta ? { texto: t('Criar pasta com o modelo…'), sub: t('Regras, skills e referências prontas'), icone: 'mais', acao: async () => aoEscolher(await criarPastaComModelo()) } : null,
  ].filter(Boolean)));
  const autoBotao = el('button', { class: `ambiente-auto ${auto ? 'ligado' : ''}`, type: 'button', 'aria-pressed': String(!!auto),
    title: t('Modo automático: o Claude muda arquivos e roda comandos sem perguntar (é o modo Livre). Apagar e publicar continuam pedindo OK.') },
    el('span', { html: ic('raio') }), el('span', { texto: auto ? t('Modo automático ligado') : t('Ativar modo automático') }),
    auto ? el('span', { class: 'ambiente-check', html: ic('certo') }) : null);
  autoBotao.addEventListener('click', () => aoAuto(!auto));
  return el('section', { class: 'painel-ambientes', 'aria-label': t('Ambiente') },
    el('div', { class: 'ambientes-lista' },
      el('div', { class: 'painel-rotulo', html: `${ic('pasta')}<span>${t('Ambiente')}</span>` }),
      ...recentes.map((c) => el('button', { class: `ambiente ${c === atual ? 'atual' : ''}`, type: 'button', title: c, 'aria-current': c === atual ? 'true' : null,
        onclick: () => c !== atual && aoEscolher(c) },
        el('span', { class: 'ambiente-icone', html: ic('computador') }),
        el('span', { class: 'ambiente-nome' }, el('b', { texto: nomePasta(c) }), el('small', { texto: c })),
        c === atual ? el('span', { class: 'ambiente-check', html: ic('certo') }) : null)),
      recentes.length ? el('div', { class: 'separador' }) : null,
      botaoEscolher),
    autoBotao,
    !atual ? el('p', { class: 'painel-sub', texto: t('Escolha a pasta em que o Claude vai trabalhar. Ele só mexe dentro dela.') }) : null);
}

