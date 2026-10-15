// Cartões da conversa que pedem decisão ou mostram trabalho em etapas: aprovação (com "sempre" e regra
// editável), proposta de fluxo, fluxo ao vivo, fluxo salvo no histórico e o plano para aprovar.
import { api } from './api.js';
import { estado, cfg, modeloInfo } from './estado.js';
import { ic } from './icones.js';
import { el, aviso, usd, menu } from './ui.js';
import { renderizar } from './markdown.js';
import { blocoFerramenta, descreverFerramenta, htmlDiff, nota } from './blocos.js';

const NOMES_PODE = { ler: 'ler', editar: 'mudar arquivos', comandos: 'comandos', web: 'web' };
const STATUS_ETAPA = {
  esperando: ['circulo', 'Esperando'], rodando: ['progresso', 'Rodando'], concluida: ['feito', 'Pronta'],
  erro: ['alerta', 'Deu erro'], parada: ['parar', 'Parada'], pulada: ['circulo', 'Pulada'],
};
const STATUS_FLUXO = {
  proposto: 'esperando o seu OK', rodando: 'rodando', concluido: 'concluído', erro: 'parou com erro',
  parado: 'parado por você', teto: 'parou no teto de gasto', recusado: 'recusado',
};

function faixa(e) {
  if (!e) return '';
  return e.min === e.max ? usd(e.max, 3) : `${usd(e.min, 3)} a ${usd(e.max, 3)}`;
}

// ---------- notificação do Windows ----------
let pediuPermissao = false;
export function notificar(titulo, corpo) {
  // notificação é extra: nada aqui pode atrapalhar a conversa
  try {
    if (cfg().notificacoes === false) return;
    if (document.hasFocus() && !document.hidden) return;
    if (window.clave?.notificar) { window.clave.notificar(titulo, String(corpo || '').slice(0, 180))?.catch?.(() => {}); return; }
    if (!('Notification' in window)) return;
    if (Notification.permission === 'granted') new Notification(titulo, { body: String(corpo || '').slice(0, 180) });
    else if (Notification.permission === 'default' && !pediuPermissao) {
      pediuPermissao = true;
      Notification.requestPermission()?.catch?.(() => {});
    }
  } catch { /* sem notificação, segue a vida */ }
}

// ---------- aprovação de uma ação ----------
export function cartaoAprovacao(ev, { execucaoId, temPasta = true, etapa = '' } = {}) {
  const [, verbo, alvo] = descreverFerramenta(ev.nome, ev.entrada || {});
  const comentario = el('input', { class: 'entrada', placeholder: 'Se recusar, diga o que prefere (opcional)' });
  const regra = el('input', { class: 'entrada mono', 'aria-label': 'Regra de permissão', spellcheck: 'false' });
  regra.value = ev.sugestao || '';
  const explicacao = el('small', { class: 'ajuda' });
  let escopo = null;
  const caixaRegra = el('div', { class: 'aprovacao-regra', hidden: true },
    el('label', {}, el('span', { texto: 'Regra que vai ser salva (dá para editar):' }), regra),
    explicacao,
    el('div', { class: 'aprovacao-botoes-mini' },
      el('button', { class: 'botao pequeno primario', type: 'button', texto: 'Salvar a regra e permitir', onclick: () => decidir(escopo, { regra: regra.value.trim() }) }),
      el('button', { class: 'botao pequeno fantasma', type: 'button', texto: 'Cancelar', onclick: () => { caixaRegra.hidden = true; } })));

  async function decidir(decisao, dados) {
    try {
      await api(`/execucoes/${execucaoId}/aprovar`, { metodo: 'POST', corpo: { id: ev.id, decisao, texto: comentario.value, dados } });
      card.remove();
    } catch (e) { aviso(e.message, 'erro'); }
  }

  function pedirRegra(qual) {
    escopo = qual;
    explicacao.textContent = qual === 'permitir_pasta'
      ? 'Fica no arquivo .claude/settings.local.json desta pasta (o mesmo do Claude Code): vale para as próximas conversas nesta pasta.'
      : 'Fica nas regras do Clave e vale em todas as pastas. Dá para ver e apagar em Permissões.';
    caixaRegra.hidden = false;
    regra.focus();
  }

  const podeTarefa = ev.pode_tarefa ?? ['mudar arquivo', 'rodar comando'].includes(ev.motivo);
  const podeSempre = ev.pode_sempre && ev.sugestao;
  const opcoes = [];
  if (podeTarefa) opcoes.push({ texto: ev.nome === 'rodar_comando' ? 'Permitir comandos nesta tarefa' : 'Permitir nesta tarefa', sub: 'Até esta resposta terminar, sem perguntar de novo.', acao: () => decidir('permitir_tarefa', { regra: ev.sugestao || '' }) });
  if (podeSempre && temPasta) opcoes.push({ texto: 'Sempre nesta pasta…', sub: 'Salva uma regra para esta pasta.', acao: () => pedirRegra('permitir_pasta') });
  if (podeSempre) opcoes.push({ texto: 'Sempre, em todo o Clave…', sub: 'Salva uma regra que vale em todas as pastas.', acao: () => pedirRegra('permitir_app') });

  let previa = null;
  if (ev.previa) previa = el('pre', { class: 'diff', html: htmlDiff(ev.previa) });
  else if (ev.nome === 'rodar_comando') previa = el('pre', { texto: ev.entrada?.comando || '' });
  else if (ev.entrada) previa = el('pre', { texto: JSON.stringify(ev.entrada, null, 2) });

  const maisBotao = opcoes.length ? el('button', { class: 'botao pequeno', type: 'button', html: `Mais opções${ic('baixo', 'class="seta"')}`,
    onclick: (e) => menu(e.currentTarget, opcoes, { acima: true }) }) : null;
  const card = el('div', { class: 'aprovacao', dados: { id: ev.id }, role: 'group', 'aria-label': 'Pedido de permissão' },
    el('div', { class: 'aprovacao-topo' }, el('span', { html: ic('escudo') }),
      el('div', {},
        etapa ? el('span', { class: 'etiqueta-etapa', texto: `Etapa: ${etapa}` }) : null,
        el('b', { texto: `Permitir: ${verbo}${alvo ? ' ' + String(alvo).slice(0, 120) : ''}?` }),
        el('small', { texto: `Motivo da pergunta: ${ev.motivo || 'ação que muda algo'}.` }))),
    previa,
    caixaRegra,
    el('div', { class: 'aprovacao-botoes' },
      el('button', { class: 'botao pequeno primario', type: 'button', texto: 'Permitir', onclick: () => decidir('permitir') }),
      maisBotao, comentario,
      el('button', { class: 'botao pequeno perigo', type: 'button', texto: 'Recusar', onclick: () => decidir('recusar') })));
  notificar('O Clave precisa do seu OK', `${verbo} ${alvo || ''}`);
  return card;
}

// ---------- proposta de fluxo ----------
function seletorModelo(atual, aoMudar) {
  const s = el('select', { class: 'entrada mini', 'aria-label': 'Modelo da etapa' });
  const lista = [...(estado.info?.modelos || [])];
  if (!lista.some((m) => m.id === atual)) lista.unshift({ id: atual, nome: modeloInfo(atual).nome || atual });
  for (const m of lista) s.append(el('option', { value: m.id, texto: m.nome, selected: m.id === atual }));
  s.addEventListener('change', () => aoMudar(s.value));
  return s;
}

function seletorEsforco(atual, aoMudar) {
  const s = el('select', { class: 'entrada mini', 'aria-label': 'Raciocínio da etapa' });
  for (const e of estado.info?.esforcos || []) s.append(el('option', { value: e.id, texto: e.nome, selected: e.id === atual }));
  s.addEventListener('change', () => aoMudar(s.value));
  return s;
}

export function cartaoPropostaFluxo(ev, { execucaoId }) {
  const p = ev.proposta;
  const escolhas = new Map(p.etapas.map((e) => [e.i, { modelo: e.modelo, esforco: e.esforco, tirar: false }]));
  const totalEl = el('b', { texto: faixa(p.estimativa) });
  const teto = el('input', { class: 'entrada mini', type: 'number', min: '0.1', step: '0.5', 'aria-label': 'Teto de gasto do fluxo em dólares' });
  teto.value = String(p.teto_usd);
  const comentario = el('input', { class: 'entrada', placeholder: 'Se recusar, diga o que prefere (opcional)' });
  const estimativas = new Map();
  let agendado = null;

  async function reestimar() {
    clearTimeout(agendado);
    agendado = setTimeout(async () => {
      const vivas = p.etapas.filter((e) => !escolhas.get(e.i).tirar);
      if (!vivas.length) { totalEl.textContent = '—'; return; }
      try {
        const r = await api('/fluxos/estimar', { metodo: 'POST', corpo: { modo: p.pasta ? 'code' : 'chat', etapas: vivas.map((e) => ({
          nome: e.nome, tarefa: e.tarefa, agente: e.agente, modelo: escolhas.get(e.i).modelo, esforco: escolhas.get(e.i).esforco, pode: e.pode,
        })) } });
        totalEl.textContent = faixa(r.estimativa);
        r.etapas.forEach((x, k) => estimativas.get(vivas[k].i)?.replaceChildren(faixa(x.estimativa)));
      } catch { /* a estimativa antiga continua na tela */ }
    }, 250);
  }

  const linhas = [];
  let grupoAnterior = null;
  for (const e of p.etapas) {
    const est = el('span', { class: 'meta', texto: faixa(e.estimativa) });
    estimativas.set(e.i, est);
    const linha = el('div', { class: `fluxo-etapa ${e.grupo === grupoAnterior ? 'paralela' : ''}` },
      el('span', { class: 'num', texto: String(e.i + 1) }),
      el('div', { class: 'textos' },
        el('b', { texto: e.nome }),
        el('small', { texto: e.tarefa }),
        el('div', { class: 'etiquetas' },
          e.agente ? el('span', { class: 'etiqueta', html: `${ic('agente')}${e.agente}` }) : null,
          el('span', { class: 'etiqueta', texto: e.pode.length ? 'pode: ' + e.pode.map((x) => NOMES_PODE[x] || x).join(', ') : 'só pensa e escreve' }),
          e.grupo === grupoAnterior ? el('span', { class: 'etiqueta acao', texto: 'ao mesmo tempo que a anterior' }) : null,
          e.aviso ? el('span', { class: 'etiqueta perigo', texto: e.aviso }) : null)),
      el('div', { class: 'controles' },
        seletorModelo(e.modelo, (v) => { escolhas.get(e.i).modelo = v; reestimar(); }),
        seletorEsforco(e.esforco, (v) => { escolhas.get(e.i).esforco = v; reestimar(); }),
        est,
        p.etapas.length > 1 ? el('button', { class: 'icone-botao', type: 'button', title: 'Tirar esta etapa', 'aria-label': `Tirar a etapa ${e.nome}`, html: ic('x'),
          onclick: (ev2) => {
            const c = escolhas.get(e.i); c.tirar = !c.tirar;
            linha.classList.toggle('tirada', c.tirar);
            ev2.currentTarget.innerHTML = ic(c.tirar ? 'refazer' : 'x');
            reestimar();
          } }) : null));
    grupoAnterior = e.grupo;
    linhas.push(linha);
  }

  async function decidir(decisao) {
    const dados = decisao === 'permitir' ? {
      etapas: [...escolhas.entries()].map(([i, c]) => ({ i, modelo: c.modelo, esforco: c.esforco, tirar: c.tirar })),
      teto_usd: parseFloat(teto.value) || p.teto_usd,
    } : null;
    try {
      await api(`/execucoes/${execucaoId}/aprovar`, { metodo: 'POST', corpo: { id: ev.id, decisao, texto: comentario.value, dados } });
      card.remove();
    } catch (e) { aviso(e.message, 'erro'); }
  }

  const card = el('div', { class: 'fluxo proposta', dados: { id: ev.id }, role: 'group', 'aria-label': 'Proposta de fluxo' },
    el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('fluxo') }),
      el('div', {}, el('small', { class: 'sobre', texto: 'O Claude propõe um fluxo' }), el('b', { texto: p.titulo }))),
    p.objetivo ? el('p', { class: 'fluxo-objetivo', texto: p.objetivo }) : null,
    el('div', { class: 'fluxo-etapas' }, ...linhas),
    el('div', { class: 'fluxo-rodape' },
      el('span', {}, 'Estimativa: ', totalEl, el('small', { class: 'ajuda', texto: ' (aproximada: depende de quanto cada etapa precisa ler e fazer)' })),
      el('label', { class: 'teto-fluxo' }, el('span', { texto: 'Parar se passar de US$' }), teto)),
    el('div', { class: 'aprovacao-botoes' },
      el('button', { class: 'botao pequeno primario', type: 'button', html: `${ic('fluxo')}Rodar o fluxo`, onclick: () => decidir('permitir') }),
      comentario,
      el('button', { class: 'botao pequeno perigo', type: 'button', texto: 'Recusar', onclick: () => decidir('recusar') })));
  notificar('O Clave propôs um fluxo', `${p.titulo}: ${faixa(p.estimativa)}`);
  return card;
}

// ---------- fluxo rodando ----------
class EtapaAoVivo {
  constructor(area) {
    this.area = area;
    this.chamada = 0;
    this.blocos = new Map();
    this.ferramentas = new Map();
    this.agendado = new Set();
  }

  chave(i) { return `${this.chamada}:${i}`; }

  evento(ev) {
    switch (ev.tipo) {
      case 'chamando': this.chamada += 1; break;
      case 'bloco_inicio': {
        const k = this.chave(ev.indice);
        if (ev.bloco.type === 'text') {
          const div = el('div', { class: 'resposta' });
          this.area.append(div);
          this.blocos.set(k, { tipo: 'text', el: div, texto: '' });
        } else if (ev.bloco.type === 'tool_use' && ev.bloco.name !== 'atualizar_tarefas') {
          const det = blocoFerramenta({ id: ev.bloco.id, name: ev.bloco.name, input: {} });
          det.classList.add('rodando');
          this.area.append(det);
          this.blocos.set(k, { tipo: 'tool_use', el: det });
          this.ferramentas.set(ev.bloco.id, det);
        }
        break;
      }
      case 'texto': {
        const k = this.chave(ev.indice);
        const b = this.blocos.get(k);
        if (!b) break;
        b.texto += ev.texto;
        if (!this.agendado.has(k)) {
          this.agendado.add(k);
          requestAnimationFrame(() => { this.agendado.delete(k); renderizar(b.el, b.texto, { final: false }); });
        }
        break;
      }
      case 'bloco_fim': {
        const b = this.blocos.get(this.chave(ev.indice));
        if (b?.tipo === 'text') renderizar(b.el, ev.bloco.text || b.texto, { final: true });
        if (b?.tipo === 'tool_use') b.el.definirEntrada(ev.bloco.input || {});
        break;
      }
      case 'ferramenta_fim': {
        const det = this.ferramentas.get(ev.id);
        det?.definirResultado?.(ev.resumo, ev.erro);
        break;
      }
      case 'aviso': this.area.append(nota(ev.mensagem)); break;
      case 'erro': this.area.append(nota(ev.mensagem, 'erro')); break;
      default: break;
    }
  }
}

export class FluxoVivo {
  constructor(proposta, { aoParar } = {}) {
    this.p = proposta;
    this.etapas = new Map();
    this.custoEl = el('span', { class: 'meta', texto: usd(0, 4) });
    this.statusEl = el('span', { class: 'meta', texto: STATUS_FLUXO.rodando });
    this.custos = new Map();
    const linhas = [];
    let grupoAnterior = null;
    for (const e of proposta.etapas) {
      const area = el('div', { class: 'etapa-area' });
      const icone = el('span', { class: 'status', html: ic('circulo') });
      const custo = el('span', { class: 'meta', texto: '' });
      const det = el('details', { class: `fluxo-etapa viva ${e.grupo === grupoAnterior ? 'paralela' : ''}`, dados: { status: 'esperando' } },
        el('summary', {}, icone,
          el('span', { class: 'textos' }, el('b', { texto: `${e.i + 1}. ${e.nome}` }),
            el('small', { texto: [e.modelo_nome || modeloInfo(e.modelo).nome, e.agente].filter(Boolean).join(' · ') })),
          custo),
        area);
      grupoAnterior = e.grupo;
      this.etapas.set(e.i, { e, det, icone, custo, area, vivo: new EtapaAoVivo(area) });
      linhas.push(det);
    }
    this.el = el('div', { class: 'fluxo', dados: { fluxo: proposta.id } },
      el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('fluxo') }),
        el('div', {}, el('small', { class: 'sobre', texto: 'Fluxo' }), el('b', { texto: proposta.titulo })),
        el('span', { class: 'espaco' }), this.statusEl, this.custoEl,
        aoParar ? el('button', { class: 'botao pequeno fantasma', type: 'button', html: `${ic('parar')}Parar`, onclick: aoParar }) : null),
      el('div', { class: 'fluxo-etapas' }, ...linhas),
      el('small', { class: 'ajuda', texto: `Teto do fluxo: ${usd(proposta.teto_usd, 2)}. Clique numa etapa para ver o que ela está fazendo.` }));
  }

  marcar(i, status, custo) {
    const x = this.etapas.get(i);
    if (!x) return;
    const [icone, nome] = STATUS_ETAPA[status] || STATUS_ETAPA.esperando;
    x.det.dataset.status = status;
    x.icone.innerHTML = ic(icone);
    x.icone.title = nome;
    if (custo != null) { this.custos.set(i, custo); x.custo.textContent = usd(custo, 4); }
    const total = [...this.custos.values()].reduce((s, v) => s + v, 0);
    this.custoEl.textContent = usd(total, 4);
  }

  evento(ev) {
    if (ev.tipo === 'etapa_inicio') {
      this.marcar(ev.etapa, 'rodando');
      const x = this.etapas.get(ev.etapa);
      if (x) x.execucao = ev.execucao;
    } else if (ev.tipo === 'etapa_evento') {
      const x = this.etapas.get(ev.etapa);
      if (!x) return;
      const interno = ev.ev;
      if (interno.tipo === 'aprovacao') {
        x.det.open = true;
        x.area.append(cartaoAprovacao(interno, { execucaoId: ev.execucao, temPasta: !!this.p.pasta, etapa: x.e.nome }));
      } else if (interno.tipo === 'aprovacao_decidida') {
        x.area.querySelector(`.aprovacao[data-id="${CSS.escape(interno.id)}"]`)?.remove();
      } else if (interno.tipo === 'uso') {
        this.marcar(ev.etapa, 'rodando', interno.custo_execucao);
      } else {
        x.vivo.evento(interno);
      }
    } else if (ev.tipo === 'etapa_fim') {
      this.marcar(ev.etapa, ev.status, ev.custo_usd);
    } else if (ev.tipo === 'fluxo_fim') {
      this.statusEl.textContent = STATUS_FLUXO[ev.status] || ev.status;
      this.custoEl.textContent = usd(ev.custo_usd, 4);
      this.el.dataset.status = ev.status;
      notificar('Fluxo terminou', `${this.p.titulo}: ${STATUS_FLUXO[ev.status] || ev.status}`);
    }
  }

  // aprovação pendente de uma etapa, ao reabrir a conversa no meio do fluxo
  aprovacaoPendente(ev) {
    for (const x of this.etapas.values()) {
      if (x.execucao === ev.execucao || !x.execucao) {
        x.det.open = true;
        x.area.append(cartaoAprovacao(ev, { execucaoId: ev.execucao, temPasta: !!this.p.pasta, etapa: x.e.nome }));
        return true;
      }
    }
    return false;
  }
}

// ---------- fluxo no histórico ----------
export function cartaoFluxoSalvo(fid) {
  const caixa = el('div', { class: 'fluxo salvo', dados: { fluxo: fid } }, el('small', { class: 'ajuda', texto: 'Carregando o fluxo…' }));
  api(`/fluxos/${encodeURIComponent(fid)}`).then(({ fluxo: f }) => {
    const linhas = f.etapas.map((e) => {
      const [icone, nome] = STATUS_ETAPA[e.status] || STATUS_ETAPA.esperando;
      const corpo = el('div', { class: 'etapa-area' });
      if (e.resultado) renderizar(corpo, e.resultado, { final: true });
      else corpo.append(el('p', { class: 'ajuda', texto: e.erro || 'Sem relatório.' }));
      return el('details', { class: 'fluxo-etapa viva', dados: { status: e.status } },
        el('summary', {}, el('span', { class: 'status', title: nome, html: ic(icone) }),
          el('span', { class: 'textos' }, el('b', { texto: `${e.i + 1}. ${e.nome}` }),
            el('small', { texto: [e.modelo_nome || modeloInfo(e.modelo).nome, e.agente].filter(Boolean).join(' · ') })),
          el('span', { class: 'meta', texto: e.custo_usd ? usd(e.custo_usd, 4) : '' })),
        corpo);
    });
    caixa.dataset.status = f.status;
    caixa.replaceChildren(
      el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('fluxo') }),
        el('div', {}, el('small', { class: 'sobre', texto: 'Fluxo' }), el('b', { texto: f.titulo })),
        el('span', { class: 'espaco' }), el('span', { class: 'meta', texto: STATUS_FLUXO[f.status] || f.status }),
        el('span', { class: 'meta', texto: usd(f.custo_usd || 0, 4) })),
      f.status === 'recusado' ? null : el('div', { class: 'fluxo-etapas' }, ...linhas));
  }).catch(() => caixa.remove());
  return caixa;
}

// ---------- plano para aprovar ----------
export function cartaoPlano(ev, { execucaoId }) {
  const corpo = el('div', { class: 'resposta plano-corpo' });
  renderizar(corpo, ev.plano || ev.entrada?.plano || '', { final: true });
  const comentario = el('input', { class: 'entrada', placeholder: 'O que mudar no plano? (opcional)' });
  async function decidir(decisao) {
    try {
      await api(`/execucoes/${execucaoId}/aprovar`, { metodo: 'POST', corpo: { id: ev.id, decisao, texto: comentario.value } });
      card.remove();
    } catch (e) { aviso(e.message, 'erro'); }
  }
  const card = el('div', { class: 'fluxo plano', dados: { id: ev.id }, role: 'group', 'aria-label': 'Plano para aprovar' },
    el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('lista') }),
      el('div', {}, el('small', { class: 'sobre', texto: 'Modo Plano' }), el('b', { texto: 'O plano está pronto. Executar?' }))),
    corpo,
    el('div', { class: 'aprovacao-botoes' },
      el('button', { class: 'botao pequeno primario', type: 'button', texto: 'Executar, pedindo OK a cada mudança', onclick: () => decidir('executar_perguntar') }),
      el('button', { class: 'botao pequeno', type: 'button', texto: 'Executar e aceitar as edições', onclick: () => decidir('executar_aceitar') }),
      el('button', { class: 'botao pequeno fantasma', type: 'button', texto: 'Modo Livre', title: 'Faz tudo sozinho, menos apagar ou publicar', onclick: () => decidir('executar_livre') })),
    el('div', { class: 'aprovacao-botoes' }, comentario,
      el('button', { class: 'botao pequeno', type: 'button', texto: 'Continuar planejando', onclick: () => decidir('recusar') })));
  notificar('O plano está pronto', 'O Claude terminou o plano e espera a sua decisão.');
  return card;
}

export function cartaoPlanoSalvo(entrada, resultado) {
  const corpo = el('div', { class: 'resposta plano-corpo' });
  renderizar(corpo, entrada?.plano || '', { final: true });
  const aprovado = /^Plano aprovado/.test(resultado || '');
  return el('details', { class: 'fluxo plano salvo', open: false },
    el('summary', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('lista') }),
      el('div', {}, el('small', { class: 'sobre', texto: 'Modo Plano' }), el('b', { texto: aprovado ? 'Plano aprovado' : 'Plano apresentado' }))),
    corpo);
}
