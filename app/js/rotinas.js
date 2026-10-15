// Rotinas: um pedido salvo que roda sozinho (todo dia, em alguns dias ou a cada N horas).
import { api } from './api.js';
import { estado, modeloInfo, avisar } from './estado.js';
import { ic } from './icones.js';
import { el, janela, aviso, confirmar, usd, chaveLiga } from './ui.js';
import { escolherPasta } from './pastas.js';

const DIAS = ['seg', 'ter', 'qua', 'qui', 'sex', 'sáb', 'dom'];

function quando(ts) {
  if (!ts) return '—';
  return new Date(ts * 1000).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
}

export async function telaRotinas(principal) {
  const { rotinas, windows } = await api('/rotinas');
  const desenhar = () => telaRotinas(principal);
  const cartao = (r) => el('div', { class: `cartao rotina ${r.ligada ? '' : 'desligado'}` },
    el('div', { class: 'cartao-cab' }, el('span', { class: 'ic', html: ic('calendario') }), el('h3', { texto: r.nome }),
      r.rodando ? el('span', { class: 'etiqueta acao', texto: 'rodando agora' }) : null),
    el('p', { class: 'rotina-pedido', texto: r.prompt }),
    el('div', { class: 'etiquetas' },
      el('span', { class: 'etiqueta', html: `${ic('relogio')}${r.quando_texto}` }),
      el('span', { class: 'etiqueta', texto: r.modo === 'code' ? `Code · ${(r.pasta || '').split(/[\\/]/).pop()}` : 'Chat' }),
      el('span', { class: 'etiqueta', texto: modeloInfo(r.modelo).nome || r.modelo }),
      el('span', { class: 'etiqueta', texto: `até ${usd(r.teto_usd, 2)} por rodada` }),
      r.agendador ? el('span', { class: 'etiqueta', texto: 'pelo Agendador do Windows' }) : null),
    el('div', { class: 'meta', texto: `Última: ${quando(r.ultima)}${r.ultimo_status ? ` (${r.ultimo_status})` : ''} · Próxima: ${r.ligada ? quando(r.proxima) : 'desligada'}` }),
    el('div', { class: 'cartao-acoes' },
      chaveLiga({ rotulo: r.ligada ? 'Ligada' : 'Desligada', marcado: r.ligada, aoMudar: async (v) => {
        try { await api('/rotinas', { metodo: 'POST', corpo: { ...r, ligada: v } }); desenhar(); } catch (e) { aviso(e.message, 'erro'); }
      } }),
      el('button', { class: 'botao pequeno', type: 'button', html: `${ic('enviar')}Rodar agora`, disabled: r.rodando, onclick: async () => {
        try { const x = await api(`/rotinas/${r.id}/rodar`, { metodo: 'POST' }); avisar('conversas-mudaram'); location.hash = `#/c/${x.conversa}`; }
        catch (e) { aviso(e.message, 'erro'); }
      } }),
      r.ultima_conversa ? el('a', { class: 'botao pequeno fantasma', href: `#/c/${r.ultima_conversa}`, texto: 'Ver a última' }) : null,
      el('button', { class: 'botao pequeno fantasma', type: 'button', texto: 'Editar', onclick: () => editarRotina(r, windows, desenhar) }),
      el('button', { class: 'icone-botao', type: 'button', 'aria-label': 'Apagar rotina', html: ic('lixo'), onclick: async () => {
        if (!await confirmar(`Apagar a rotina "${r.nome}"?${r.agendador ? ' A tarefa no Agendador do Windows também sai.' : ''}`, { titulo: 'Apagar rotina', sim: 'Apagar', perigo: true })) return;
        await api(`/rotinas/${r.id}`, { metodo: 'DELETE' }); desenhar();
      } })));
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: 'Rotinas' }),
        el('p', { texto: 'Um pedido que o Claude faz sozinho no horário que você escolher: resumir os arquivos novos da pasta toda manhã, montar o relatório da semana na sexta, conferir uma planilha a cada 3 horas.' })),
      el('button', { class: 'botao primario', type: 'button', html: `${ic('mais')}Nova rotina`, onclick: () => editarRotina(null, windows, desenhar) })),
    el('div', { class: 'nota-conversa info' }, el('span', { html: ic('escudo') }),
      el('span', {}, 'Numa rotina ninguém está olhando, então ela só faz o que as suas ', el('a', { href: '#/permissoes', texto: 'regras de permissão' }),
        ' já liberam (ler na pasta, e o que tiver regra de permitir). Se precisar de um OK, ela para e conta o que precisaria. Cada rodada tem teto de gasto.')),
    rotinas.length ? el('div', { class: 'grade-cartoes' }, ...rotinas.map(cartao))
      : el('div', { class: 'vazio' }, el('p', { texto: 'Nenhuma rotina ainda.' }), el('a', { href: '#/aprender/rotinas', texto: 'Como as rotinas funcionam' })))));
  return {};
}

function editarRotina(r, windows, depois) {
  r = r || { modo: 'chat', quando: { tipo: 'diaria', hora: '08:00' }, modelo: 'claude-sonnet-5-5', esforco: 'medium', teto_usd: 0.5 };
  let pasta = r.pasta || '';
  const nome = el('input', { class: 'entrada', placeholder: 'Ex.: Resumo da manhã' }); nome.value = r.nome || '';
  const prompt = el('textarea', { class: 'area', rows: 4, placeholder: 'O que o Claude deve fazer, do começo ao fim, sem precisar perguntar nada.' }); prompt.value = r.prompt || '';
  const modo = el('select', { class: 'entrada' }, el('option', { value: 'chat', texto: 'No chat (sem pasta)', selected: r.modo !== 'code' }),
    el('option', { value: 'code', texto: 'Numa pasta (modo Code)', selected: r.modo === 'code' }));
  const pastaTexto = el('span', { class: 'meta', texto: pasta || 'nenhuma pasta escolhida' });
  const pastaLinha = el('div', { class: 'linha-pasta', hidden: r.modo !== 'code' }, pastaTexto,
    el('button', { class: 'botao pequeno', type: 'button', html: `${ic('pasta')}Escolher`, onclick: async () => {
      const p = await escolherPasta({ titulo: 'Pasta da rotina' }); if (p) { pasta = p; pastaTexto.textContent = p; }
    } }));
  modo.addEventListener('change', () => { pastaLinha.hidden = modo.value !== 'code'; });
  const q = r.quando || {};
  const tipo = el('select', { class: 'entrada' },
    ...[['diaria', 'Todo dia'], ['semanal', 'Em alguns dias da semana'], ['horas', 'A cada N horas']].map(([v, t]) => el('option', { value: v, texto: t, selected: (q.tipo || 'diaria') === v })));
  const hora = el('input', { class: 'entrada', type: 'time' }); hora.value = q.hora || '08:00';
  const aCada = el('input', { class: 'entrada', type: 'number', min: '1', max: '23' }); aCada.value = String(q.a_cada || 3);
  const dias = new Set((q.dias || [0, 1, 2, 3, 4]).map(Number));
  const diasEl = el('div', { class: 'checks dias' }, ...DIAS.map((d, i) => {
    const c = el('input', { type: 'checkbox', checked: dias.has(i) });
    c.addEventListener('change', () => (c.checked ? dias.add(i) : dias.delete(i)));
    return el('label', {}, c, ' ', d);
  }));
  const campoHora = el('label', {}, el('span', { texto: 'Hora' }), hora);
  const campoACada = el('label', {}, el('span', { texto: 'A cada quantas horas' }), aCada);
  const ajustar = () => { campoHora.hidden = tipo.value === 'horas'; campoACada.hidden = tipo.value !== 'horas'; diasEl.hidden = tipo.value !== 'semanal'; };
  tipo.addEventListener('change', ajustar); ajustar();
  const modelo = el('select', { class: 'entrada' }, ...(estado.info?.modelos || []).map((m) => el('option', { value: m.id, texto: m.nome, selected: m.id === r.modelo })));
  const esforco = el('select', { class: 'entrada' }, ...(estado.info?.esforcos || []).map((e) => el('option', { value: e.id, texto: e.nome, selected: e.id === r.esforco })));
  const teto = el('input', { class: 'entrada', type: 'number', min: '0.01', step: '0.1' }); teto.value = String(r.teto_usd ?? 0.5);
  const web = el('input', { type: 'checkbox', checked: !!r.busca_web });
  const agendador = el('input', { type: 'checkbox', checked: !!r.agendador, disabled: !windows });
  janela({
    titulo: r.id ? 'Editar rotina' : 'Nova rotina', larga: true,
    corpo: el('div', { class: 'form-grade' },
      el('label', {}, el('span', { texto: 'Nome' }), nome),
      el('label', {}, el('span', { texto: 'O que fazer' }), prompt),
      el('div', { class: 'linha-campos' }, el('label', {}, el('span', { texto: 'Onde' }), modo), pastaLinha),
      el('div', { class: 'linha-campos' }, el('label', {}, el('span', { texto: 'Quando' }), tipo), campoHora, campoACada), diasEl,
      el('div', { class: 'linha-campos' }, el('label', {}, el('span', { texto: 'Modelo' }), modelo), el('label', {}, el('span', { texto: 'Raciocínio' }), esforco),
        el('label', {}, el('span', { texto: 'Teto por rodada (US$)' }), teto)),
      el('label', { class: 'check' }, web, ' Pode pesquisar na web'),
      el('label', { class: 'check' }, agendador, ' Rodar mesmo com o Clave fechado (cria uma tarefa no Agendador de Tarefas do Windows)'),
      el('small', { class: 'ajuda', texto: 'Com o Clave fechado, a rotina roda sem janela e avisa por notificação do Windows quando terminar. O computador precisa estar ligado.' })),
    botoes: [{ texto: 'Cancelar' }, { texto: 'Salvar', classe: 'primario', acao: async () => {
      if (agendador.checked && !r.agendador && !await confirmar('O Clave vai criar uma tarefa no Agendador de Tarefas do Windows (pasta "Clave") para rodar esta rotina. Para tirar, é só desmarcar esta opção ou apagar a rotina.', { titulo: 'Agendador do Windows', sim: 'Criar a tarefa' })) return false;
      try {
        await api('/rotinas', { metodo: 'POST', corpo: {
          id: r.id, nome: nome.value, prompt: prompt.value, modo: modo.value, pasta: modo.value === 'code' ? pasta : null,
          quando: { tipo: tipo.value, hora: hora.value, a_cada: Number(aCada.value), dias: [...dias] },
          modelo: modelo.value, esforco: esforco.value, teto_usd: Number(teto.value), busca_web: web.checked,
          agendador: agendador.checked, ligada: r.ligada ?? true,
        } });
        aviso('Rotina salva.'); depois?.();
      } catch (e) { aviso(e.message, 'erro'); return false; }
    } }],
  });
}
