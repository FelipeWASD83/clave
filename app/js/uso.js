// Uso e gasto: quanto do teto do mês já foi, por dia, por modelo e por conversa.
import { api } from './api.js';
import { atualizarOrcamento, modeloInfo } from './estado.js';
import { el, usd, tokens, dataBr, aviso } from './ui.js';

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
  const grafico = el('div', { class: 'grafico-dias', role: 'img', 'aria-label': 'Gasto por dia' }, ...dias.map((dia) => {
    const v = porDia.get(dia)?.usd || 0;
    return el('div', { class: `barra ${v ? '' : 'zero'}`, style: `height:${(v / maior) * 100}%`, title: `${dataBr(dia)}: ${usd(v)} (${porDia.get(dia)?.pedidos || 0} pedidos)` });
  }));

  const ajuste = el('input', { class: 'entrada mono', type: 'number', min: '0', step: '0.01', value: o.ajuste || '', placeholder: '0,00', style: 'max-width:140px' });
  const salvarAjuste = el('button', { class: 'botao pequeno', type: 'button', texto: 'Salvar', onclick: async () => {
    try { const r = await api('/uso/ajuste', { metodo: 'POST', corpo: { valor: ajuste.value || 0 } }); atualizarOrcamento(r.orcamento); telaUso(principal); }
    catch (e) { aviso(e.message, 'erro'); }
  } });

  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' }, el('div', {}, el('h1', { texto: 'Uso e gasto' }),
      el('p', { texto: `Ciclo de ${dataBr(o.inicio)} a ${dataBr(o.fim)}. Os valores são calculados pelo Clave a partir dos tokens de cada resposta, com os preços oficiais.` }))),
    el('div', { class: 'uso-topo' },
      el('div', { class: 'uso-painel' },
        el('div', { class: 'meta', texto: 'Gasto neste mês' }),
        el('div', { class: 'uso-valor' }, usd(o.gasto, 2), ' ', el('small', { texto: o.teto ? `de ${usd(o.teto, 2)}` : 'sem teto definido' })),
        el('div', { class: `medidor ${pct >= 100 ? 'cheio' : pct >= 80 ? 'alerta' : ''}` }, el('i', { style: `width:${pct}%` })),
        el('div', { class: 'meta', texto: o.teto ? `${pct.toFixed(1)}% · restam ${usd(Math.max(0, o.restante), 2)} · ${o.ao_atingir === 'bloquear' ? 'bloqueia ao chegar no teto' : 'só avisa ao chegar no teto'}` : 'Defina um teto em Configurações > Limite de gasto' }),
        el('div', { style: 'margin-top:18px;display:grid;gap:6px' },
          el('span', { class: 'rotulo', texto: 'Gastos fora do Clave neste mês (US$)' }),
          el('div', { style: 'display:flex;gap:8px;align-items:center' }, ajuste, salvarAjuste),
          el('small', { class: 'ajuda', texto: 'O Clave só enxerga o que ele mesmo gasta. Se a mesma conta da Anthropic é usada por outros apps, some aqui o que eles gastaram (o Console da Anthropic mostra) para o teto ficar certo.' }))),
      el('div', { class: 'uso-painel' },
        el('div', { class: 'meta', texto: 'Como gastar menos' }),
        el('ul', { class: 'passo-a-passo', style: 'margin-top:10px' },
          el('li', { texto: 'Use o Haiku 5.5 para perguntas simples: custa 40 vezes menos que o Opus.' }),
          el('li', { texto: 'Raciocínio no Baixo ou Médio resolve a maioria das coisas.' }),
          el('li', { texto: 'Conversa muito longa encarece cada resposta: comece uma nova quando o assunto mudar.' }),
          el('li', { texto: 'Deixe o cache ligado (Configurações > Recursos): ele barateia o que se repete.' })))),
    el('div', { class: 'secao-titulo', texto: 'Por dia' }),
    grafico,
    el('div', { class: 'eixo-dias' }, el('span', { class: 'meta', texto: dataBr(o.inicio) }), el('span', { class: 'meta', texto: dataBr(o.fim) })),
    el('div', { class: 'secao-titulo', texto: 'Por modelo' }),
    d.por_modelo.length ? tabela(['Modelo', 'Pedidos', 'Entrada', 'Cache lido', 'Saída', 'Buscas', 'Custo'],
      d.por_modelo.map((m) => [modeloInfo(m.modelo).nome || m.modelo, m.pedidos, tokens(m.entrada + m.cache_escrita), tokens(m.cache_leitura), tokens(m.saida), m.buscas || '', usd(m.usd)]))
      : el('p', { class: 'ajuda', texto: 'Nada gasto neste ciclo ainda.' }),
    el('div', { class: 'secao-titulo', texto: 'Por conversa (as 30 que mais gastaram)' }),
    d.por_conversa.length ? tabela(['Conversa', 'Modo', 'Pedidos', 'Custo'],
      d.por_conversa.map((c) => [c.conversa_id ? el('a', { href: `#/c/${c.conversa_id}`, texto: c.titulo || 'Sem título' }) : 'Títulos automáticos', c.modo === 'code' ? 'Code' : c.modo ? 'Chat' : '', c.pedidos, usd(c.usd)]))
      : el('p', { class: 'ajuda', texto: 'Nenhuma conversa gastou nada neste ciclo ainda.' }))));
  return {};
}

function tabela(cab, linhas) {
  return el('div', { style: 'overflow-x:auto' }, el('table', { class: 'tabela' },
    el('thead', {}, el('tr', {}, ...cab.map((c, i) => el('th', { class: i > 0 && c !== 'Modo' ? 'num' : '', texto: c })))),
    el('tbody', {}, ...linhas.map((l) => el('tr', {}, ...l.map((v, i) => el('td', { class: i > 0 && cab[i] !== 'Modo' ? 'num' : '' }, v instanceof Node ? v : String(v))))))));
}
