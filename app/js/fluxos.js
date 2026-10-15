// Fluxos e agentes: os fluxos prontos (e os seus), os agentes que fazem as etapas e o histórico do que já rodou.
import { api } from './api.js';
import { cfg, salvarConfig, modeloInfo, estado } from './estado.js';
import { ic } from './icones.js';
import { el, janela, aviso, confirmar, usd, chaveLiga, dataHora } from './ui.js';
import { t } from './i18n.js';

const ABAS = () => [['prontos', t('Fluxos')], ['agentes', t('Agentes')], ['historico', t('Histórico')]];
const NOMES_PODE = () => ({ ler: t('ler arquivos'), editar: t('mudar arquivos'), comandos: t('rodar comandos'), web: t('pesquisar na web') });
const MODELOS_AGENTE = () => [['opus', 'Opus 5.5'], ['sonnet', 'Sonnet 5.5'], ['haiku', 'Haiku 5.5'], ['fable', 'Fable 5.1'], ['inherit', t('O da conversa')]];
const ORIGEM = () => ({ clave: t('do Clave'), meus: t('seu'), pessoal: t('pessoal'), pasta: t('da pasta') });
const STATUS = () => ({ concluido: t('concluído'), erro: t('com erro'), parado: t('parado'), teto: t('parou no teto'), recusado: t('recusado'), proposto: t('esperando OK'), rodando: t('rodando') });

function nomeModelo(m) {
  const alias = { opus: 'Opus 5.5', sonnet: 'Sonnet 5.5', haiku: 'Haiku 5.5', fable: 'Fable 5.1', inherit: t('o da conversa') };
  return alias[m] || modeloInfo(m).nome || m || t('o da conversa');
}

function rotuloOrigem(o) {
  if (o?.startsWith('plugin:')) return `plugin ${o.slice(7)}`;
  return ORIGEM()[o] || o || '';
}

function usarFluxo(m, modo) {
  sessionStorage.setItem('clave:rascunho', `/fluxo ${m.id} `);
  location.hash = modo === 'code' ? '#/code' : '#/novo';
}

export async function telaFluxos(principal, aba = 'prontos') {
  const abas = ABAS();
  if (!abas.some(([id]) => id === aba)) aba = 'prontos';
  const conteudo = el('div', {});
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: t('Fluxos e agentes') }),
        el('p', { texto: t('Um fluxo divide uma tarefa grande em etapas, cada uma num modelo: por exemplo, o Opus planeja, o Sonnet faz e testa. Ele gasta mais que uma resposta, então o Clave sempre mostra as etapas e a estimativa de custo e espera o seu OK.') }))),
    el('nav', { class: 'abas', 'aria-label': t('Seções') }, ...abas.map(([id, nome]) => el('a', { href: `#/fluxos/${id}`, 'aria-current': id === aba ? 'page' : null, texto: nome }))),
    conteudo)));
  await ({ prontos, agentes, historico }[aba])(conteudo);
  return {};
}

async function prontos(alvo) {
  const { modelos } = await api('/fluxos');
  const desenhar = () => prontos(alvo);
  const grade = el('div', { class: 'grade-cartoes' }, ...modelos.map((m) => {
    const est = el('span', { class: 'meta', texto: t('calculando…') });
    api('/fluxos/estimar', { metodo: 'POST', corpo: { modo: 'code', etapas: m.etapas.map((e) => ({ ...e, tarefa: e.tarefa || e.nome })) } })
      .then((r) => { est.textContent = t('cerca de {min} a {max}', { min: usd(r.estimativa.min, 2), max: usd(r.estimativa.max, 2) }); })
      .catch(() => { est.textContent = ''; });
    return el('div', { class: 'cartao fluxo-modelo' },
      el('div', { class: 'cartao-cab' }, el('h3', { texto: m.nome || m.id }), el('span', { class: 'etiqueta', texto: rotuloOrigem(m.origem) })),
      el('p', { texto: m.descricao || '' }),
      el('ol', { class: 'etapas-resumo' }, ...m.etapas.map((e) => el('li', {},
        el('span', { texto: e.nome }), el('span', { class: 'meta', texto: `${nomeModelo(e.modelo)}${e.paralelo ? ' · ' + t('junto com a anterior') : ''}` })))),
      est,
      el('div', { class: 'cartao-acoes' },
        el('button', { class: 'botao pequeno primario', type: 'button', html: `${ic('chat')}${t('Usar no chat')}`, onclick: () => usarFluxo(m, 'chat') }),
        el('button', { class: 'botao pequeno', type: 'button', html: `${ic('terminal')}${t('Usar no Code')}`, onclick: () => usarFluxo(m, 'code') }),
        el('button', { class: 'botao pequeno fantasma', type: 'button', texto: m.editavel ? t('Editar') : t('Copiar e editar'),
          onclick: () => editarFluxo(m.editavel ? m : { ...m, id: '', nome: t('{nome} (minha versão)', { nome: m.nome }) }, desenhar) }),
        m.editavel ? el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar fluxo'), html: ic('lixo'), onclick: async () => {
          if (!await confirmar(t('Apagar o fluxo "{nome}"?', { nome: m.nome }), { titulo: t('Apagar fluxo'), sim: t('Apagar'), perigo: true })) return;
          await api(`/fluxos/modelos/${m.id}`, { metodo: 'DELETE' }); desenhar();
        } }) : null));
  }));
  alvo.replaceChildren(
    el('div', { class: 'faixa-opcoes' },
      chaveLiga({ rotulo: t('O Claude pode propor fluxos'), ajuda: t('Desligado, ele faz tudo sozinho num modelo só. Ligado, ele pode propor um fluxo quando a tarefa for grande, e nada roda sem o seu OK.'),
        marcado: cfg().fluxos_ligados !== false, aoMudar: async (v) => { await salvarConfig({ fluxos_ligados: v }); aviso(v ? t('Fluxos ligados.') : t('Fluxos desligados.')); } }),
      el('button', { class: 'botao primario', type: 'button', html: `${ic('mais')}${t('Novo fluxo')}`, onclick: () => editarFluxo({ nome: '', etapas: [{ nome: t('Planejar'), agente: 'planejador', modelo: 'opus', tarefa: '' }] }, desenhar) })),
    el('p', { class: 'ajuda', html: t('Para usar: escolha um fluxo e descreva a tarefa, ou digite <code>/fluxo</code> na caixa de mensagem. Você também pode só pedir ("faça isso com um fluxo") e o Claude monta as etapas.') }),
    grade);
}

function editarFluxo(m, depois) {
  const nome = el('input', { class: 'entrada', placeholder: t('Ex.: Relatório do mês') }); nome.value = m.nome || '';
  const descricao = el('input', { class: 'entrada', placeholder: t('Para que serve, em uma frase') }); descricao.value = m.descricao || '';
  const pede = el('input', { class: 'entrada', placeholder: t('O que a pessoa precisa dizer ao usar (ex.: o mês e a planilha)') }); pede.value = m.pede || '';
  const lista = el('div', { class: 'editor-etapas' });
  const etapas = (m.etapas || []).map((e) => ({ ...e }));
  const desenharEtapas = () => {
    lista.replaceChildren(...etapas.map((e, i) => {
      const n = el('input', { class: 'entrada', placeholder: t('Nome da etapa') }); n.value = e.nome || '';
      n.addEventListener('input', () => { e.nome = n.value; });
      const ag = el('input', { class: 'entrada', placeholder: t('Agente (opcional)'), list: 'lista-agentes' }); ag.value = e.agente || '';
      ag.addEventListener('input', () => { e.agente = ag.value.trim(); });
      const mod = el('select', { class: 'entrada' }, ...MODELOS_AGENTE().map(([v, rot]) => el('option', { value: v, texto: rot, selected: (e.modelo || 'inherit') === v })));
      mod.addEventListener('change', () => { e.modelo = mod.value; });
      const esf = el('select', { class: 'entrada' }, ...(estado.info?.esforcos || []).map((x) => el('option', { value: x.id, texto: x.nome, selected: (e.esforco || 'medium') === x.id })));
      esf.addEventListener('change', () => { e.esforco = esf.value; });
      const tarefa = el('textarea', { class: 'area', rows: 2, placeholder: t('O que esta etapa faz e o que deve entregar') }); tarefa.value = e.tarefa || '';
      tarefa.addEventListener('input', () => { e.tarefa = tarefa.value; });
      const pode = el('div', { class: 'checks' }, ...Object.entries(NOMES_PODE()).map(([k, rot]) => {
        const c = el('input', { type: 'checkbox', checked: (e.pode || ['ler']).includes(k) });
        c.addEventListener('change', () => { const s = new Set(e.pode || ['ler']); c.checked ? s.add(k) : s.delete(k); e.pode = [...s]; });
        return el('label', {}, c, ' ', rot);
      }));
      const par = el('input', { type: 'checkbox', checked: !!e.paralelo, disabled: i === 0 });
      par.addEventListener('change', () => { e.paralelo = par.checked; });
      return el('div', { class: 'etapa-editor' },
        el('div', { class: 'etapa-editor-cab' }, el('b', { texto: t('Etapa {n}', { n: i + 1 }) }),
          el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Tirar etapa'), html: ic('lixo'), disabled: etapas.length < 2, onclick: () => { etapas.splice(i, 1); desenharEtapas(); } })),
        el('div', { class: 'linha-campos' }, n, ag), el('div', { class: 'linha-campos' }, mod, esf), tarefa, pode,
        el('label', { class: 'ajuda' }, par, ' ' + t('Rodar ao mesmo tempo que a etapa anterior')));
    }));
  };
  desenharEtapas();
  const datalist = el('datalist', { id: 'lista-agentes' });
  api('/agentes').then(({ agentes }) => datalist.replaceChildren(...agentes.map((a) => el('option', { value: a.nome })))).catch(() => {});
  janela({
    titulo: m.id ? t('Editar fluxo') : t('Novo fluxo'), larga: true,
    corpo: el('div', { class: 'form-grade' }, datalist,
      el('label', {}, el('span', { texto: t('Nome') }), nome), el('label', {}, el('span', { texto: t('Descrição') }), descricao),
      el('label', {}, el('span', { texto: t('O que pedir a quem usa') }), pede),
      el('div', { class: 'secao-titulo', texto: t('Etapas') }), lista,
      el('button', { class: 'botao pequeno', type: 'button', html: `${ic('mais')}${t('Adicionar etapa')}`, onclick: () => { if (etapas.length >= 8) return aviso(t('No máximo 8 etapas.'), 'erro'); etapas.push({ nome: '', modelo: 'sonnet', pode: ['ler'] }); desenharEtapas(); } })),
    botoes: [{ texto: t('Cancelar') }, { texto: t('Salvar'), classe: 'primario', acao: async () => {
      try {
        await api('/fluxos/modelos', { metodo: 'POST', corpo: { id: m.id || undefined, nome: nome.value, descricao: descricao.value, pede: pede.value, etapas } });
        aviso(t('Fluxo salvo.')); depois?.();
      } catch (e) { aviso(e.message, 'erro'); return false; }
    } }],
  });
}

async function agentes(alvo) {
  const { agentes: lista } = await api('/agentes');
  const desenhar = () => agentes(alvo);
  const nomesPode = NOMES_PODE();
  alvo.replaceChildren(
    el('div', { class: 'faixa-opcoes' },
      el('p', { class: 'ajuda', html: t('Um agente é um especialista com instruções, modelo e ferramentas próprios. Cada etapa de fluxo pode ser feita por um. Eles usam o mesmo formato do Claude Code: arquivos em <code>.claude/agents</code> (da pasta) ou <code>~/.claude/agents</code> (pessoais).') }),
      el('button', { class: 'botao primario', type: 'button', html: `${ic('mais')}${t('Novo agente')}`, onclick: () => editarAgente({ modelo: 'sonnet', pode: ['ler'] }, desenhar) })),
    el('div', { class: 'grade-cartoes' }, ...lista.map((a) => el('div', { class: 'cartao agente' },
      el('div', { class: 'cartao-cab' }, el('span', { class: 'ic', html: ic('agente') }), el('h3', { texto: a.nome }), el('span', { class: 'etiqueta', texto: rotuloOrigem(a.origem) })),
      el('p', { texto: a.descricao || '' }),
      el('div', { class: 'etiquetas' },
        el('span', { class: 'etiqueta', texto: nomeModelo(a.modelo) }),
        a.esforco ? el('span', { class: 'etiqueta', texto: t('raciocínio {nome}', { nome: (estado.info?.esforcos || []).find((x) => x.id === a.esforco)?.nome || a.esforco }) }) : null,
        el('span', { class: 'etiqueta', texto: a.pode.length ? a.pode.map((p) => nomesPode[p]).join(', ') : t('só pensa e escreve') })),
      a.editavel ? el('div', { class: 'cartao-acoes' },
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Editar'), onclick: () => editarAgente(a, desenhar) }),
        el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar agente'), html: ic('lixo'), onclick: async () => {
          if (!await confirmar(t('Apagar o agente "{nome}"?', { nome: a.nome }), { titulo: t('Apagar agente'), sim: t('Apagar'), perigo: true })) return;
          try { await api('/agentes', { metodo: 'DELETE', corpo: { caminho: a.caminho } }); desenhar(); } catch (e) { aviso(e.message, 'erro'); }
        } })) : el('div', { class: 'cartao-acoes' },
        el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Copiar e editar'), onclick: () => editarAgente({ ...a, nome: `${a.nome_base}-meu`, caminho: null }, desenhar) }))))));
}

function editarAgente(a, depois) {
  const nome = el('input', { class: 'entrada mono', placeholder: t('ex.: revisor-de-contratos') }); nome.value = a.nome_base || a.nome || '';
  if (a.editavel) nome.disabled = true;
  const desc = el('input', { class: 'entrada', placeholder: t('O que ele faz e quando usar') }); desc.value = a.descricao || '';
  const mod = el('select', { class: 'entrada' }, ...MODELOS_AGENTE().map(([v, rot]) => el('option', { value: v, texto: rot,
    selected: (({ 'claude-opus-5-5': 'opus', 'claude-sonnet-5-5': 'sonnet', 'claude-haiku-5-5': 'haiku', 'claude-fable-5-1': 'fable' })[a.modelo] || a.modelo || 'inherit') === v })));
  const esf = el('select', { class: 'entrada' }, el('option', { value: '', texto: t('Padrão do modelo') }),
    ...(estado.info?.esforcos || []).map((x) => el('option', { value: x.id, texto: x.nome, selected: a.esforco === x.id })));
  const pode = new Set(a.pode || ['ler']);
  const checks = el('div', { class: 'checks' }, ...Object.entries(NOMES_PODE()).map(([k, rot]) => {
    const c = el('input', { type: 'checkbox', checked: pode.has(k) });
    c.addEventListener('change', () => (c.checked ? pode.add(k) : pode.delete(k)));
    return el('label', {}, c, ' ', rot);
  }));
  const inst = el('textarea', { class: 'area', rows: 9, placeholder: t('Você é ... Seu trabalho é ... No fim, entregue ...') }); inst.value = a.instrucoes || '';
  janela({
    titulo: a.editavel ? t('Editar {nome}', { nome: a.nome }) : t('Novo agente'), larga: true,
    corpo: el('div', { class: 'form-grade' },
      el('label', {}, el('span', { texto: t('Nome (minúsculas e hífen)') }), nome),
      el('label', {}, el('span', { texto: t('Descrição') }), desc),
      el('div', { class: 'linha-campos' }, el('label', {}, el('span', { texto: t('Modelo') }), mod), el('label', {}, el('span', { texto: t('Raciocínio') }), esf)),
      el('div', {}, el('span', { class: 'rotulo', texto: t('O que ele pode fazer') }), checks),
      el('label', {}, el('span', { texto: t('Instruções') }), inst),
      el('small', { class: 'ajuda', html: t('Fica em <code>~/.claude/agents</code> e vale em todas as pastas (e no Claude Code).') })),
    botoes: [{ texto: t('Cancelar') }, { texto: t('Salvar'), classe: 'primario', acao: async () => {
      try {
        await api('/agentes', { metodo: 'POST', corpo: { nome: nome.value.trim(), descricao: desc.value, modelo: mod.value, esforco: esf.value, pode: [...pode], instrucoes: inst.value, onde: 'pessoal' } });
        aviso(t('Agente salvo.')); depois?.();
      } catch (e) { aviso(e.message, 'erro'); return false; }
    } }],
  });
}

async function historico(alvo) {
  const { historico: lista } = await api('/fluxos');
  if (!lista.length) {
    alvo.replaceChildren(el('div', { class: 'vazio' }, el('p', { texto: t('Nenhum fluxo rodou ainda.') })));
    return;
  }
  const total = lista.reduce((s, f) => s + (f.custo_usd || 0), 0);
  const status = STATUS();
  alvo.replaceChildren(
    el('p', { class: 'ajuda', texto: t('{n} fluxo(s), {total} no total. O gasto de cada fluxo também conta no teto do mês e aparece em Uso e gasto como "fluxo".', { n: lista.length, total: usd(total, 2) }) }),
    el('table', { class: 'tabela' },
      el('thead', {}, el('tr', {}, ...[t('Quando'), t('Fluxo'), t('Situação'), t('Gasto'), ''].map((x) => el('th', { texto: x })))),
      el('tbody', {}, ...lista.map((f) => el('tr', {},
        el('td', { texto: dataHora(f.criado_em) }),
        el('td', { texto: f.titulo }),
        el('td', { texto: status[f.status] || f.status }),
        el('td', { class: 'num', texto: usd(f.custo_usd || 0, 4) }),
        el('td', {}, f.conversa_id ? el('a', { href: `#/c/${f.conversa_id}`, texto: t('Ver conversa') }) : null))))));
}
