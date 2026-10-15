// Cartões da conversa que pedem decisão ou mostram trabalho em etapas: aprovação (com "sempre" e regra
// editável), proposta de fluxo, fluxo ao vivo, fluxo salvo no histórico e o plano para aprovar.
import { api } from './api.js';
import { estado, cfg, modeloInfo } from './estado.js';
import { ic } from './icones.js';
import { el, aviso, usd, menu } from './ui.js';
import { renderizar } from './markdown.js';
import { blocoFerramenta, descreverFerramenta, htmlDiff, nota } from './blocos.js';
import { t } from './i18n.js';

const NOMES_PODE = () => ({ ler: t('ler'), editar: t('mudar arquivos'), comandos: t('comandos'), web: t('web') });
const STATUS_ETAPA = () => ({
  esperando: ['circulo', t('Esperando')], rodando: ['progresso', t('Rodando')], concluida: ['feito', t('Pronta')],
  erro: ['alerta', t('Deu erro')], parada: ['parar', t('Parada')], pulada: ['circulo', t('Pulada')],
});
const STATUS_FLUXO = () => ({
  proposto: t('esperando o seu OK'), rodando: t('rodando'), concluido: t('concluído'), erro: t('parou com erro'),
  parado: t('parado por você'), teto: t('parou no teto de gasto'), recusado: t('recusado'),
});

function faixa(e) {
  if (!e) return '';
  return e.min === e.max ? usd(e.max, 3) : t('{min} a {max}', { min: usd(e.min, 3), max: usd(e.max, 3) });
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
// o cartão pede permissão para algo que ainda vai acontecer: o verbo vai no infinitivo (o histórico usa o passado)
const PEDIDO = () => ({
  escrever_arquivo: (e) => [t('Escrever'), e.caminho],
  editar_arquivo: (e) => [t('Editar'), e.caminho],
  rodar_comando: (e) => [e.em_segundo_plano ? t('Deixar rodando em segundo plano') : t('Rodar este comando'), ''],
  navegador_clicar: (e) => [t('Clicar na página'), e.descricao || (e.ref != null ? `[${e.ref}]` : '')],
  navegador_digitar: (e) => [t('Digitar na página'), `"${String(e.texto || '').slice(0, 80)}"`],
  navegador_abrir: (e) => [t('Abrir no navegador do Clave'), e.url],
  navegador_ler: () => [t('Ler a página do navegador'), ''],
  navegador_print: () => [t('Tirar um print da página'), ''],
  navegador_rolar: () => [t('Rolar a página'), ''],
  navegador_voltar: () => [t('Voltar uma página no navegador'), ''],
  word_criar: (e) => [t('Criar o documento'), e.caminho],
  word_alterar: (e) => [t('Mexer no documento'), e.caminho],
  word_no_app: (e) => [t('Exportar o documento para PDF'), e.caminho],
  email_enviar: (e) => [t('Enviar um e-mail para'), e.para],
  email_salvar_anexo: (e) => [t('Salvar o anexo'), e.anexo],
  excel_alterar: (e) => [t('Mexer na planilha'), e.caminho],
  excel_no_app: (e) => [{ recalcular: t('Recalcular no Excel'), pdf: t('Exportar para PDF'), converter_xlsx: t('Converter para .xlsx') }[e.acao] || t('Usar o Excel'), e.caminho],
  excel_abrir: (e) => [t('Abrir no Excel'), e.caminho],
  planilha_criar: (e) => [t('Criar a planilha'), e.nome_arquivo],
});

export function cartaoAprovacao(ev, { execucaoId, temPasta = true, etapa = '' } = {}) {
  const pedido = PEDIDO()[ev.nome];
  const [verbo, alvo] = pedido ? pedido(ev.entrada || {}) : descreverFerramenta(ev.nome, ev.entrada || {}).slice(1);
  const comentario = el('input', { class: 'entrada', placeholder: t('Se recusar, diga o que prefere (opcional)') });
  const regra = el('input', { class: 'entrada mono', 'aria-label': t('Regra de permissão'), spellcheck: 'false' });
  regra.value = ev.sugestao || '';
  const explicacao = el('small', { class: 'ajuda' });
  let escopo = null;
  const caixaRegra = el('div', { class: 'aprovacao-regra', hidden: true },
    el('label', {}, el('span', { texto: t('Regra que vai ser salva (dá para editar):') }), regra),
    explicacao,
    el('div', { class: 'aprovacao-botoes-mini' },
      el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Salvar a regra e permitir'), onclick: () => decidir(escopo, { regra: regra.value.trim() }) }),
      el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Cancelar'), onclick: () => { caixaRegra.hidden = true; } })));

  async function decidir(decisao, dados) {
    try {
      await api(`/execucoes/${execucaoId}/aprovar`, { metodo: 'POST', corpo: { id: ev.id, decisao, texto: comentario.value, dados } });
      card.remove();
    } catch (e) { aviso(e.message, 'erro'); }
  }

  function pedirRegra(qual) {
    escopo = qual;
    explicacao.textContent = qual === 'permitir_pasta'
      ? t('Fica no arquivo .claude/settings.local.json desta pasta (o mesmo do Claude Code): vale para as próximas conversas nesta pasta.')
      : t('Fica nas regras do Clave e vale em todas as pastas. Dá para ver e apagar em Permissões.');
    caixaRegra.hidden = false;
    regra.focus();
  }

  const podeTarefa = ev.pode_tarefa ?? ['mudar arquivo', 'rodar comando'].includes(ev.motivo);
  const podeSempre = ev.pode_sempre && ev.sugestao;
  // o cartão do site do navegador pergunta "usar o site X nesta tarefa?": o Permitir dele já vale para a tarefa
  const doSite = Boolean(ev.site);
  const permitir = () => (doSite ? decidir('permitir_tarefa', { regra: ev.sugestao || '' }) : decidir('permitir'));
  const opcoes = [];
  if (podeTarefa && !doSite) opcoes.push({ texto: ev.nome === 'rodar_comando' ? t('Permitir comandos nesta tarefa') : t('Permitir nesta tarefa'), sub: t('Até esta resposta terminar, sem perguntar de novo.'), acao: () => decidir('permitir_tarefa', { regra: ev.sugestao || '' }) });
  if (podeSempre && temPasta) opcoes.push({ texto: t('Sempre nesta pasta…'), sub: t('Salva uma regra para esta pasta.'), acao: () => pedirRegra('permitir_pasta') });
  if (podeSempre) opcoes.push({ texto: t('Sempre, em todo o Clave…'), sub: t('Salva uma regra que vale em todas as pastas.'), acao: () => pedirRegra('permitir_app') });

  let previa = null;
  if (ev.previa) previa = el('pre', { class: 'diff', html: htmlDiff(ev.previa) });
  else if (ev.nome === 'rodar_comando') previa = el('pre', { texto: ev.entrada?.comando || '' });
  else if (ev.entrada) previa = el('pre', { texto: JSON.stringify(ev.entrada, null, 2) });

  const maisBotao = opcoes.length ? el('button', { class: 'botao pequeno', type: 'button', html: `${t('Mais opções')}${ic('baixo', 'class="seta"')}`,
    onclick: (e) => menu(e.currentTarget, opcoes, { acima: true }) }) : null;
  const card = el('div', { class: 'aprovacao', dados: { id: ev.id }, role: 'group', 'aria-label': t('Pedido de permissão') },
    el('div', { class: 'aprovacao-topo' }, el('span', { html: ic('escudo') }),
      el('div', {},
        etapa ? el('span', { class: 'etiqueta-etapa', texto: t('Etapa: {etapa}', { etapa }) }) : null,
        el('b', { texto: ev.pergunta || t('Permitir: {acao}?', { acao: `${verbo}${alvo ? ' ' + String(alvo).slice(0, 120) : ''}` }) }),
        el('small', { texto: t('Motivo da pergunta: {motivo}.', { motivo: ev.motivo || t('ação que muda algo') }) }))),
    previa,
    caixaRegra,
    el('div', { class: 'aprovacao-botoes' },
      el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Permitir'), onclick: permitir }),
      maisBotao, comentario,
      el('button', { class: 'botao pequeno perigo', type: 'button', texto: t('Recusar'), onclick: () => decidir('recusar') })));
  notificar(t('O Clave precisa do seu OK'), `${verbo} ${alvo || ''}`);
  return card;
}

// ---------- proposta de fluxo ----------
function seletorModelo(atual, aoMudar) {
  const s = el('select', { class: 'entrada mini', 'aria-label': t('Modelo da etapa') });
  const lista = [...(estado.info?.modelos || [])];
  if (!lista.some((m) => m.id === atual)) lista.unshift({ id: atual, nome: modeloInfo(atual).nome || atual });
  for (const m of lista) s.append(el('option', { value: m.id, texto: m.nome, selected: m.id === atual }));
  s.addEventListener('change', () => aoMudar(s.value));
  return s;
}

function seletorEsforco(atual, aoMudar) {
  const s = el('select', { class: 'entrada mini', 'aria-label': t('Raciocínio da etapa') });
  for (const e of estado.info?.esforcos || []) s.append(el('option', { value: e.id, texto: e.nome, selected: e.id === atual }));
  s.addEventListener('change', () => aoMudar(s.value));
  return s;
}

export function cartaoPropostaFluxo(ev, { execucaoId }) {
  const p = ev.proposta;
  const escolhas = new Map(p.etapas.map((e) => [e.i, { modelo: e.modelo, esforco: e.esforco, tirar: false }]));
  const totalEl = el('b', { texto: faixa(p.estimativa) });
  const teto = el('input', { class: 'entrada mini', type: 'number', min: '0.1', step: '0.5', 'aria-label': t('Teto de gasto do fluxo em dólares') });
  teto.value = String(p.teto_usd);
  const comentario = el('input', { class: 'entrada', placeholder: t('Se recusar, diga o que prefere (opcional)') });
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
          el('span', { class: 'etiqueta', texto: e.pode.length ? t('pode: {lista}', { lista: e.pode.map((x) => NOMES_PODE()[x] || x).join(', ') }) : t('só pensa e escreve') }),
          e.grupo === grupoAnterior ? el('span', { class: 'etiqueta acao', texto: t('ao mesmo tempo que a anterior') }) : null,
          e.aviso ? el('span', { class: 'etiqueta perigo', texto: e.aviso }) : null)),
      el('div', { class: 'controles' },
        seletorModelo(e.modelo, (v) => { escolhas.get(e.i).modelo = v; reestimar(); }),
        seletorEsforco(e.esforco, (v) => { escolhas.get(e.i).esforco = v; reestimar(); }),
        est,
        p.etapas.length > 1 ? el('button', { class: 'icone-botao', type: 'button', title: t('Tirar esta etapa'), 'aria-label': t('Tirar a etapa {nome}', { nome: e.nome }), html: ic('x'),
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

  const card = el('div', { class: 'fluxo proposta', dados: { id: ev.id }, role: 'group', 'aria-label': t('Proposta de fluxo') },
    el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('fluxo') }),
      el('div', {}, el('small', { class: 'sobre', texto: t('O Claude propõe um fluxo') }), el('b', { texto: p.titulo }))),
    p.objetivo ? el('p', { class: 'fluxo-objetivo', texto: p.objetivo }) : null,
    el('div', { class: 'fluxo-etapas' }, ...linhas),
    el('div', { class: 'fluxo-rodape' },
      el('span', {}, t('Estimativa:'), ' ', totalEl, el('small', { class: 'ajuda', texto: ' ' + t('(aproximada: depende de quanto cada etapa precisa ler e fazer)') })),
      el('label', { class: 'teto-fluxo' }, el('span', { texto: t('Parar se passar de US$') }), teto)),
    el('div', { class: 'aprovacao-botoes' },
      el('button', { class: 'botao pequeno primario', type: 'button', html: `${ic('fluxo')}${t('Rodar o fluxo')}`, onclick: () => decidir('permitir') }),
      comentario,
      el('button', { class: 'botao pequeno perigo', type: 'button', texto: t('Recusar'), onclick: () => decidir('recusar') })));
  notificar(t('O Clave propôs um fluxo'), `${p.titulo}: ${faixa(p.estimativa)}`);
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
    this.statusEl = el('span', { class: 'meta', texto: STATUS_FLUXO().rodando });
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
        el('div', {}, el('small', { class: 'sobre', texto: t('Fluxo') }), el('b', { texto: proposta.titulo })),
        el('span', { class: 'espaco' }), this.statusEl, this.custoEl,
        aoParar ? el('button', { class: 'botao pequeno fantasma', type: 'button', html: `${ic('parar')}${t('Parar')}`, onclick: aoParar }) : null),
      el('div', { class: 'fluxo-etapas' }, ...linhas),
      el('small', { class: 'ajuda', texto: t('Teto do fluxo: {valor}. Clique numa etapa para ver o que ela está fazendo.', { valor: usd(proposta.teto_usd, 2) }) }));
  }

  marcar(i, status, custo) {
    const x = this.etapas.get(i);
    if (!x) return;
    const st = STATUS_ETAPA();
    const [icone, nome] = st[status] || st.esperando;
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
      this.statusEl.textContent = STATUS_FLUXO()[ev.status] || ev.status;
      this.custoEl.textContent = usd(ev.custo_usd, 4);
      this.el.dataset.status = ev.status;
      notificar(t('Fluxo terminou'), `${this.p.titulo}: ${STATUS_FLUXO()[ev.status] || ev.status}`);
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
  const caixa = el('div', { class: 'fluxo salvo', dados: { fluxo: fid } }, el('small', { class: 'ajuda', texto: t('Carregando o fluxo…') }));
  api(`/fluxos/${encodeURIComponent(fid)}`).then(({ fluxo: f }) => {
    const st = STATUS_ETAPA();
    const linhas = f.etapas.map((e) => {
      const [icone, nome] = st[e.status] || st.esperando;
      const corpo = el('div', { class: 'etapa-area' });
      if (e.resultado) renderizar(corpo, e.resultado, { final: true });
      else corpo.append(el('p', { class: 'ajuda', texto: e.erro || t('Sem relatório.') }));
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
        el('div', {}, el('small', { class: 'sobre', texto: t('Fluxo') }), el('b', { texto: f.titulo })),
        el('span', { class: 'espaco' }), el('span', { class: 'meta', texto: STATUS_FLUXO()[f.status] || f.status }),
        el('span', { class: 'meta', texto: usd(f.custo_usd || 0, 4) })),
      f.status === 'recusado' ? null : el('div', { class: 'fluxo-etapas' }, ...linhas));
  }).catch(() => caixa.remove());
  return caixa;
}

// ---------- plano para aprovar ----------
export function cartaoPlano(ev, { execucaoId }) {
  const corpo = el('div', { class: 'resposta plano-corpo' });
  renderizar(corpo, ev.plano || ev.entrada?.plano || '', { final: true });
  const comentario = el('input', { class: 'entrada', placeholder: t('O que mudar no plano? (opcional)') });
  let card;
  async function decidir(decisao) {
    try {
      await api(`/execucoes/${execucaoId}/aprovar`, { metodo: 'POST', corpo: { id: ev.id, decisao, texto: comentario.value } });
      card.remove();
    } catch (e) { aviso(e.message, 'erro'); }
  }
  if (ev.modo && ev.modo !== 'plano') {
    // o "posso fazer?" antes de uma tarefa grande: o modo de permissão continua o mesmo
    card = el('div', { class: 'fluxo plano', dados: { id: ev.id }, role: 'group', 'aria-label': t('Plano para aprovar') },
      el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('lista') }),
        el('div', {}, el('small', { class: 'sobre', texto: t('Plano') }), el('b', { texto: t('Posso fazer assim?') }))),
      corpo,
      el('div', { class: 'aprovacao-botoes' },
        el('button', { class: 'botao pequeno primario', type: 'button', html: `${ic('certo')}${t('Pode ir')}`, onclick: () => decidir('pode_ir') }),
        el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Não fazer'), onclick: () => decidir('nao_fazer') })),
      el('div', { class: 'aprovacao-botoes' }, comentario,
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Mudar o plano'), onclick: () => decidir('mudar') })));
    notificar(t('O Claude pede o seu OK'), t('Ele mostrou o plano e espera você dizer se pode ir.'));
    return card;
  }
  card = el('div', { class: 'fluxo plano', dados: { id: ev.id }, role: 'group', 'aria-label': t('Plano para aprovar') },
    el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('lista') }),
      el('div', {}, el('small', { class: 'sobre', texto: t('Modo Plano') }), el('b', { texto: t('O plano está pronto. Executar?') }))),
    corpo,
    el('div', { class: 'aprovacao-botoes' },
      el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Executar, pedindo OK a cada mudança'), onclick: () => decidir('executar_perguntar') }),
      el('button', { class: 'botao pequeno', type: 'button', texto: t('Executar e aceitar as edições'), onclick: () => decidir('executar_aceitar') }),
      el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Modo Livre'), title: t('Faz tudo sozinho, menos apagar ou publicar'), onclick: () => decidir('executar_livre') })),
    el('div', { class: 'aprovacao-botoes' }, comentario,
      el('button', { class: 'botao pequeno', type: 'button', texto: t('Continuar planejando'), onclick: () => decidir('recusar') })));
  notificar(t('O plano está pronto'), t('O Claude terminou o plano e espera a sua decisão.'));
  return card;
}

export function cartaoPlanoSalvo(entrada, resultado) {
  const corpo = el('div', { class: 'resposta plano-corpo' });
  renderizar(corpo, entrada?.plano || '', { final: true });
  const aprovado = /^(Plano aprovado|Plan approved)/.test(resultado || '');
  return el('details', { class: 'fluxo plano salvo', open: false },
    el('summary', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('lista') }),
      el('div', {}, el('small', { class: 'sobre', texto: t('Plano') }), el('b', { texto: aprovado ? t('Plano aprovado') : t('Plano apresentado') }))),
    corpo);
}

// ---------- perguntas do Claude ----------
// Um cartão com 1 a 4 perguntas: opções para clicar (uma ou várias) e um campo "Outra". A resposta volta para o
// Claude e a tarefa continua dali; "Pular" deixa ele seguir com a opção que recomendaria.
export function cartaoPergunta(ev, { execucaoId }) {
  const perguntas = ev.perguntas || [];
  const estados = perguntas.map(() => ({ escolhas: new Set(), outra: '' }));
  const blocos = perguntas.map((p, i) => {
    const nomeGrupo = `perg-${ev.id}-${i}`;
    const opcoes = p.opcoes.map((o) => {
      const entrada = el('input', { type: p.varias ? 'checkbox' : 'radio', name: nomeGrupo, value: o.rotulo });
      entrada.addEventListener('change', () => {
        if (!p.varias) estados[i].escolhas.clear();
        if (entrada.checked) estados[i].escolhas.add(o.rotulo); else estados[i].escolhas.delete(o.rotulo);
        if (!p.varias && entrada.checked) { estados[i].outra = ''; outra.value = ''; }
        atualizar();
      });
      return el('label', { class: 'pergunta-opcao' }, entrada,
        el('span', { class: 'textos' }, el('b', { texto: o.rotulo }), o.descricao ? el('small', { texto: o.descricao }) : null));
    });
    const outra = el('input', { class: 'entrada', placeholder: t('Outra resposta (opcional)') });
    outra.addEventListener('input', () => {
      estados[i].outra = outra.value;
      if (!p.varias && outra.value.trim()) {
        estados[i].escolhas.clear();
        blocos[i]?.querySelectorAll('input[type=radio]').forEach((r) => { r.checked = false; });
      }
      atualizar();
    });
    return el('fieldset', { class: 'pergunta' },
      el('legend', {}, p.titulo ? el('span', { class: 'etiqueta', texto: p.titulo }) : null, el('b', { texto: p.pergunta })),
      p.varias ? el('small', { class: 'ajuda', texto: t('Pode marcar mais de uma.') }) : null,
      el('div', { class: 'pergunta-opcoes' }, ...opcoes), outra);
  });
  const responder = el('button', { class: 'botao pequeno primario', type: 'button', html: `${ic('enviar')}${t('Responder')}`, disabled: true });
  function atualizar() {
    responder.disabled = !estados.every((s) => s.escolhas.size || s.outra.trim());
  }
  async function decidir(decisao) {
    const respostas = estados.map((s) => ({ escolhas: [...s.escolhas], outra: s.outra.trim() }));
    try {
      await api(`/execucoes/${execucaoId}/aprovar`, { metodo: 'POST', corpo: { id: ev.id, decisao, dados: { respostas } } });
      card.replaceWith(cartaoPerguntaSalva({ perguntas }, decisao === 'responder' ? textoDasRespostas(perguntas, respostas) : ''));
    } catch (e) { aviso(e.message, 'erro'); }
  }
  responder.addEventListener('click', () => decidir('responder'));
  const card = el('div', { class: 'fluxo pergunta-card', dados: { id: ev.id }, role: 'group', 'aria-label': t('Pergunta do Claude') },
    el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('chat') }),
      el('div', {}, el('small', { class: 'sobre', texto: t('Pergunta') }),
        el('b', { texto: perguntas.length > 1 ? t('O Claude tem {n} perguntas', { n: perguntas.length }) : t('O Claude tem uma pergunta') }))),
    el('div', { class: 'perguntas' }, ...blocos),
    el('div', { class: 'aprovacao-botoes' }, responder,
      el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Pular'), title: t('O Claude segue com a opção que ele recomendaria'), onclick: () => decidir('pular') })));
  notificar(t('O Claude tem uma pergunta'), perguntas[0]?.pergunta || '');
  return card;
}

// o mesmo texto que o servidor devolve para o Claude (execucao.texto_respostas)
function textoDasRespostas(perguntas, respostas) {
  const partes = [t('Respostas de quem usa:')];
  perguntas.forEach((p, i) => {
    const r = respostas[i] || {};
    const itens = [...(r.escolhas || []), ...(r.outra ? [t('Outra: {resposta}', { resposta: r.outra })] : [])];
    partes.push(`**${p.pergunta}**\n${itens.length ? itens.join(', ') : t('(sem resposta)')}`);
  });
  return partes.join('\n\n');
}

export function cartaoPerguntaSalva(entrada, resultado) {
  const respondida = /^(Respostas de quem usa|Answers from the person)/.test(resultado || '');
  const corpo = el('div', { class: 'resposta plano-corpo' });
  renderizar(corpo, respondida ? resultado.replace(/^[^\n]*\n\n/, '')
    : (entrada?.perguntas || []).map((p) => `**${p.pergunta}**`).join('\n\n'), { final: true });
  return el('details', { class: 'fluxo pergunta-card salvo', open: respondida },
    el('summary', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('chat') }),
      el('div', {}, el('small', { class: 'sobre', texto: t('Pergunta') }),
        el('b', { texto: respondida ? t('Você respondeu') : t('Ficou sem resposta') }))),
    corpo);
}

// ---------- sugestão de outra conversa ----------
// O Claude propôs um trabalho separado; nada roda sem o clique. "Abrir em outra conversa" cria a conversa (mesmo
// modo e pasta) e já manda o pedido, em segundo plano: quem usa continua aqui.
export function cartaoSugestao(s, { conversaId } = {}) {
  const origem = conversaId || estado.conversaAtual;
  const acoes = el('div', { class: 'aprovacao-botoes' });
  const pedido = el('div', { class: 'resposta sugestao-pedido' });
  renderizar(pedido, s.pedido || '', { final: true });
  const card = el('div', { class: 'fluxo sugestao-conversa', dados: { id: s.id }, role: 'group', 'aria-label': t('Sugestão de outra conversa') },
    el('div', { class: 'fluxo-cab' }, el('span', { class: 'ic', html: ic('mais_tarefa') }),
      el('div', {}, el('small', { class: 'sobre', texto: t('Sugestão de outra conversa') }), el('b', { texto: s.titulo || t('Nova tarefa') }))),
    s.por_que ? el('p', { class: 'sugestao-motivo', texto: s.por_que }) : null,
    el('details', { class: 'sugestao-detalhes' }, el('summary', { texto: t('Ver o pedido') }), pedido),
    acoes);
  const linkAberta = (c) => el('a', { class: 'botao pequeno', href: `#/c/${c.id}`, html: `${ic('chat')}${t('Ir para "{titulo}"', { titulo: (c.titulo || t('a conversa')).replace(/[<>&"]/g, '') })}` });
  const desenhar = (estadoAtual, conversa) => {
    if (estadoAtual === 'aberta' && conversa) {
      acoes.replaceChildren(el('span', { class: 'meta', texto: t('Aberta em outra conversa, rodando por lá.') }), linkAberta(conversa));
    } else if (estadoAtual === 'dispensada') {
      acoes.replaceChildren(el('span', { class: 'meta', texto: t('Dispensada.') }),
        el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Abrir mesmo assim'), onclick: abrir }));
    } else {
      acoes.replaceChildren(
        el('button', { class: 'botao pequeno primario', type: 'button', html: `${ic('mais_tarefa')}${t('Abrir em outra conversa')}`, onclick: abrir }),
        el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Dispensar'), onclick: dispensar }));
    }
  };
  async function abrir() {
    try {
      acoes.querySelectorAll('button').forEach((b) => { b.disabled = true; });
      const r = await api(`/sugestoes/${encodeURIComponent(s.id)}/abrir`, { metodo: 'POST', corpo: { conversa_id: origem } });
      desenhar('aberta', r.conversa);
      const { avisar } = await import('./estado.js');
      avisar('conversas-mudaram');
      aviso(r.ja_aberta ? t('Essa conversa já tinha sido aberta.') : t('Conversa aberta. O Claude já está trabalhando nela.'));
    } catch (e) { aviso(e.message, 'erro'); desenhar('nova'); }
  }
  async function dispensar() {
    try { await api(`/sugestoes/${encodeURIComponent(s.id)}/dispensar`, { metodo: 'POST', corpo: { conversa_id: origem } }); desenhar('dispensada'); }
    catch (e) { aviso(e.message, 'erro'); }
  }
  desenhar('nova');
  api(`/sugestoes/${encodeURIComponent(s.id)}`).then((r) => { if (r.estado !== 'nova') desenhar(r.estado, r.conversa); }).catch(() => {});
  return card;
}
