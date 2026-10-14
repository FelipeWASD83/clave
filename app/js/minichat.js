// Mini-conversa dos ajudantes: dúvidas das lições (Haiku 5.5) e editor de memória (Sonnet 5.5).
import { api, acompanhar } from './api.js';
import { atualizarOrcamento } from './estado.js';
import { ic } from './icones.js';
import { el, aviso, usd } from './ui.js';
import { renderizar } from './markdown.js';
import { renderizarTurno, blocoFerramenta, nota } from './blocos.js';

export function criarMiniChat({ tipo, licao = null, titulo, descricao, placeholder, sugestoes = [], aoTerminar, rotuloBotao = 'Perguntar' }) {
  let cid = null, conexao = null, rodando = false;
  const lista = el('div', { class: 'mini-mensagens' });
  const area = el('textarea', { class: 'area', rows: 2, placeholder, style: 'min-height:64px' });
  const enviarBt = el('button', { class: 'botao primario pequeno', type: 'button', html: `${ic('enviar')}${rotuloBotao}` });
  const meta = el('span', { class: 'meta' });
  const recomecar = el('button', { class: 'botao pequeno fantasma', type: 'button', texto: 'Começar de novo' });
  const sugs = el('div', { class: 'sugestoes', style: 'justify-content:flex-start;margin:0' }, ...sugestoes.map((s) =>
    el('button', { class: 'sugestao', type: 'button', texto: s, onclick: () => { area.value = s; area.focus(); } })));
  const caixa = el('section', { class: 'mini-chat' },
    el('div', { class: 'mini-cab' }, el('span', { html: ic('faisca') }), el('div', {}, el('b', { texto: titulo }), el('small', { texto: descricao }))),
    lista, sugs,
    el('div', { class: 'mini-entrada' }, area, el('div', { class: 'mini-barra' }, recomecar, meta, el('span', { style: 'flex:1' }), enviarBt)));

  async function carregar(nova = false) {
    try {
      const v = await api(`/ajudantes/${tipo}`, { metodo: 'POST', corpo: { licao, nova } });
      cid = v.conversa.id;
      desenhar(v);
      if (v.execucao) seguir(v.execucao);
    } catch (e) { lista.replaceChildren(nota(e.message, 'erro')); }
  }

  function desenhar(v) {
    const turnos = [];
    for (const m of v.mensagens || []) {
      if (m.papel === 'user' && m.tipo === 'normal') turnos.push({ u: m, r: [] });
      else if (turnos.length) turnos[turnos.length - 1].r.push(m);
    }
    lista.replaceChildren(...turnos.flatMap((t) => {
      const texto = (t.u.conteudo || []).filter?.((b) => b.type === 'text').map((b) => b.text).join('\n') || '';
      const resp = el('div', { class: 'blocos', style: 'display:grid;gap:10px' });
      renderizarTurno(resp, t.r);
      const erro = t.u.meta?.erro && !t.r.length ? nota(t.u.meta.erro, 'erro') : null;
      return [el('div', { class: 'msg-usuario' }, el('div', { class: 'balao', texto: texto })), t.r.length ? el('div', { class: 'msg-claude' }, resp) : null, erro].filter(Boolean);
    }));
    sugs.hidden = turnos.length > 0;
    recomecar.hidden = turnos.length === 0;
    meta.textContent = v.gasto ? `gasto aqui: ${usd(v.gasto)}` : '';
    lista.scrollTop = lista.scrollHeight;
  }

  function seguir(execucaoId) {
    rodando = true;
    enviarBt.disabled = true;
    const vivo = el('div', { class: 'msg-claude' });
    const indicador = el('div', { class: 'nota-progresso', texto: 'Pensando…' });
    vivo.append(indicador);
    lista.append(vivo);
    let texto = '', alvo = null, agendado = false;
    conexao?.parar();
    conexao = acompanhar(execucaoId, async (ev) => {
      if (ev.tipo === 'bloco_inicio' && ev.bloco.type === 'text') { indicador.remove(); alvo = el('div', { class: 'resposta' }); vivo.append(alvo); texto = ''; }
      else if (ev.tipo === 'texto' && alvo) {
        texto += ev.texto;
        if (!agendado) { agendado = true; requestAnimationFrame(() => { agendado = false; renderizar(alvo, texto, { final: false }); lista.scrollTop = lista.scrollHeight; }); }
      } else if (ev.tipo === 'bloco_fim' && ev.bloco.type === 'tool_use') {
        indicador.remove();
        vivo.append(blocoFerramenta(ev.bloco));
      } else if (ev.tipo === 'uso') atualizarOrcamento(ev.orcamento);
      else if (ev.tipo === 'erro' || ev.tipo === 'aviso') { indicador.remove(); vivo.append(nota(ev.mensagem, ev.tipo === 'erro' ? 'erro' : '')); }
      else if (ev.tipo === 'fim') {
        rodando = false;
        enviarBt.disabled = false;
        try { desenhar(await api(`/conversas/${cid}`)); } catch { /* fica o que já apareceu */ }
        aoTerminar?.();
      }
    });
  }

  async function enviar() {
    const t = area.value.trim();
    if (!t || rodando || !cid) return;
    try {
      const r = await api(`/conversas/${cid}/enviar`, { metodo: 'POST', corpo: { texto: t } });
      area.value = '';
      desenhar(await api(`/conversas/${cid}`));
      seguir(r.execucao);
    } catch (e) { aviso(e.message, 'erro'); }
  }

  enviarBt.addEventListener('click', enviar);
  area.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); enviar(); } });
  recomecar.addEventListener('click', () => carregar(true));
  carregar();
  return { elemento: caixa, parar: () => conexao?.parar() };
}
