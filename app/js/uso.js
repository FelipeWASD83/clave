// Uso e gasto: quanto do teto do mês já foi, por dia, por modelo e por conversa.
import { api } from './api.js';
import { atualizarOrcamento, modeloInfo } from './estado.js';
import { el, usd, tokens, dataBr, aviso } from './ui.js';
import { t } from './i18n.js';

export async function telaUso(principal) {
  const d = await api('/uso');
  const o = d.orcamento;
  atualizarOrcamento(o);
  const pct = o.teto ? Math.min(100, o.porcentagem) : 0;

  // um ponto por dia do ciclo
  const dias = [];
  const ini = new Date(o.inicio + 'T12:00:00'), fim = new Date(o.fim + 'T12:00:00');
  for (let x = new Date(ini); x <= fim; x.setDate(x.getDate() + 1)) dias.push(x.toISOString().slice(0, 10));
  const porDia = new Map(d.por_dia.map((x) => [x.dia, x]));
  const maior = Math.max(0.0001, ...d.por_dia.map((x) => x.usd));
  const grafico = el('div', { class: 'grafico-dias', role: 'img', 'aria-label': t('Gasto por dia') }, ...dias.map((dia) => {
    const v = porDia.get(dia)?.usd || 0;
    return el('div', { class: `barra ${v ? '' : 'zero'}`, style: `height:${(v / maior) * 100}%`, title: t('{data}: {valor} ({n} pedidos)', { data: dataBr(dia), valor: usd(v), n: porDia.get(dia)?.pedidos || 0 }) });
  }));

  const ajuste = el('input', { class: 'entrada mono', type: 'number', min: '0', step: '0.01', value: o.ajuste || '', placeholder: t('0,00'), style: 'max-width:140px' });
  const salvarAjuste = el('button', { class: 'botao pequeno', type: 'button', texto: t('Salvar'), onclick: async () => {
    try { const r = await api('/uso/ajuste', { metodo: 'POST', corpo: { valor: ajuste.value || 0 } }); atualizarOrcamento(r.orcamento); telaUso(principal); }
    catch (e) { aviso(e.message, 'erro'); }
  } });

  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' }, el('div', {}, el('h1', { texto: t('Uso e gasto') }),
      el('p', { texto: t('Ciclo de {inicio} a {fim}. Os valores são calculados pelo Clave a partir dos tokens de cada resposta, com os preços oficiais.', { inicio: dataBr(o.inicio), fim: dataBr(o.fim) }) }))),
    el('div', { class: 'uso-topo' },
      el('div', { class: 'uso-painel' },
        el('div', { class: 'meta', texto: t('Gasto neste mês') }),
        el('div', { class: 'uso-valor' }, usd(o.gasto, 2), ' ', el('small', { texto: o.teto ? t('de {teto}', { teto: usd(o.teto, 2) }) : t('sem teto definido') })),
        el('div', { class: `medidor ${pct >= 100 ? 'cheio' : pct >= 80 ? 'alerta' : ''}` }, el('i', { style: `width:${pct}%` })),
        el('div', { class: 'meta', texto: o.teto ? t('{pct}% · restam {restante} · {regra}', { pct: pct.toFixed(1), restante: usd(Math.max(0, o.restante), 2), regra: o.ao_atingir === 'bloquear' ? t('bloqueia ao chegar no teto') : t('só avisa ao chegar no teto') }) : t('Defina um teto em Configurações > Limite de gasto') }),
        el('div', { style: 'margin-top:18px;display:grid;gap:6px' },
          el('span', { class: 'rotulo', texto: t('Gastos fora do Clave neste mês (US$)') }),
          el('div', { style: 'display:flex;gap:8px;align-items:center' }, ajuste, salvarAjuste),
          el('small', { class: 'ajuda', texto: t('O Clave só enxerga o que ele mesmo gasta. Se a mesma conta da Anthropic é usada por outros apps, some aqui o que eles gastaram (o Console da Anthropic mostra) para o teto ficar certo.') }))),
      el('div', { class: 'uso-painel' },
        el('div', { class: 'meta', texto: t('Como gastar menos') }),
        el('ul', { class: 'passo-a-passo', style: 'margin-top:10px' },
          el('li', { texto: t('Use o Haiku 5.5 para perguntas simples: custa 40 vezes menos que o Opus.') }),
          el('li', { texto: t('Raciocínio no Baixo ou Médio resolve a maioria das coisas.') }),
          el('li', { texto: t('Conversa muito longa encarece cada resposta: comece uma nova quando o assunto mudar.') }),
          el('li', { texto: t('Deixe o cache ligado (Configurações > Recursos): ele barateia o que se repete.') })))),
    el('div', { class: 'secao-titulo', texto: t('Por dia') }),
    grafico,
    el('div', { class: 'eixo-dias' }, el('span', { class: 'meta', texto: dataBr(o.inicio) }), el('span', { class: 'meta', texto: dataBr(o.fim) })),
    el('div', { class: 'secao-titulo', texto: t('Por modelo') }),
    d.por_modelo.length ? tabela([t('Modelo'), t('Pedidos'), t('Entrada'), t('Cache lido'), t('Saída'), t('Buscas'), t('Custo')],
      d.por_modelo.map((m) => [modeloInfo(m.modelo).nome || m.modelo, m.pedidos, tokens(m.entrada + m.cache_escrita), tokens(m.cache_leitura), tokens(m.saida), m.buscas || '', usd(m.usd)]))
      : el('p', { class: 'ajuda', texto: t('Nada gasto neste ciclo ainda.') }),
    el('div', { class: 'secao-titulo', texto: t('Por conversa (as 30 que mais gastaram)') }),
    d.por_conversa.length ? tabela([t('Conversa'), t('Modo'), t('Pedidos'), t('Custo')],
      d.por_conversa.map((c) => [c.conversa_id ? el('a', { href: `#/c/${c.conversa_id}`, texto: c.titulo || t('Sem título') }) : t('Títulos automáticos'), c.modo === 'code' ? 'Code' : c.modo ? 'Chat' : '', c.pedidos, usd(c.usd)]))
      : el('p', { class: 'ajuda', texto: t('Nenhuma conversa gastou nada neste ciclo ainda.') }))));
  return {};
}

function tabela(cab, linhas) {
  return el('div', { style: 'overflow-x:auto' }, el('table', { class: 'tabela' },
    el('thead', {}, el('tr', {}, ...cab.map((c, i) => el('th', { class: i > 0 && c !== t('Modo') ? 'num' : '', texto: c })))),
    el('tbody', {}, ...linhas.map((l) => el('tr', {}, ...l.map((v, i) => el('td', { class: i > 0 && cab[i] !== t('Modo') ? 'num' : '' }, v instanceof Node ? v : String(v))))))));
}
