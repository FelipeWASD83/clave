// Rotinas: um pedido salvo que roda sozinho (todo dia, em alguns dias ou a cada N horas).
import { api } from './api.js';
import { estado, modeloInfo, avisar } from './estado.js';
import { ic } from './icones.js';
import { el, janela, aviso, confirmar, usd, chaveLiga, dataHora } from './ui.js';
import { escolherPasta } from './pastas.js';
import { t } from './i18n.js';

const DIAS = () => [t('seg'), t('ter'), t('qua'), t('qui'), t('sex'), t('sáb'), t('dom')];

function quando(ts) {
  if (!ts) return '—';
  return dataHora(ts);
}

export async function telaRotinas(principal) {
  const { rotinas, windows } = await api('/rotinas');
  const desenhar = () => telaRotinas(principal);
  const cartao = (r) => el('div', { class: `cartao rotina ${r.ligada ? '' : 'desligado'}` },
    el('div', { class: 'cartao-cab' }, el('span', { class: 'ic', html: ic('calendario') }), el('h3', { texto: r.nome }),
      r.rodando ? el('span', { class: 'etiqueta acao', texto: t('rodando agora') }) : null),
    el('p', { class: 'rotina-pedido', texto: r.prompt }),
    el('div', { class: 'etiquetas' },
      el('span', { class: 'etiqueta', html: `${ic('relogio')}${r.quando_texto}` }),
      el('span', { class: 'etiqueta', texto: r.modo === 'code' ? `Code · ${(r.pasta || '').split(/[\\/]/).pop()}` : 'Chat' }),
      el('span', { class: 'etiqueta', texto: modeloInfo(r.modelo).nome || r.modelo }),
      el('span', { class: 'etiqueta', texto: t('até {valor} por rodada', { valor: usd(r.teto_usd, 2) }) }),
      r.agendador ? el('span', { class: 'etiqueta', texto: t('pelo Agendador do Windows') }) : null),
    el('div', { class: 'meta', texto: t('Última: {ultima} · Próxima: {proxima}', {
      ultima: `${quando(r.ultima)}${r.ultimo_status ? ` (${r.ultimo_status})` : ''}`,
      proxima: r.ligada ? quando(r.proxima) : t('desligada'),
    }) }),
    el('div', { class: 'cartao-acoes' },
      chaveLiga({ rotulo: r.ligada ? t('Ligada') : t('Desligada'), marcado: r.ligada, aoMudar: async (v) => {
        try { await api('/rotinas', { metodo: 'POST', corpo: { ...r, ligada: v } }); desenhar(); } catch (e) { aviso(e.message, 'erro'); }
      } }),
      el('button', { class: 'botao pequeno', type: 'button', html: `${ic('enviar')}${t('Rodar agora')}`, disabled: r.rodando, onclick: async () => {
        try { const x = await api(`/rotinas/${r.id}/rodar`, { metodo: 'POST' }); avisar('conversas-mudaram'); location.hash = `#/c/${x.conversa}`; }
        catch (e) { aviso(e.message, 'erro'); }
      } }),
      r.ultima_conversa ? el('a', { class: 'botao pequeno fantasma', href: `#/c/${r.ultima_conversa}`, texto: t('Ver a última') }) : null,
      el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Editar'), onclick: () => editarRotina(r, windows, desenhar) }),
      el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar rotina'), html: ic('lixo'), onclick: async () => {
        const pergunta = r.agendador
          ? t('Apagar a rotina "{nome}"? A tarefa no Agendador do Windows também sai.', { nome: r.nome })
          : t('Apagar a rotina "{nome}"?', { nome: r.nome });
        if (!await confirmar(pergunta, { titulo: t('Apagar rotina'), sim: t('Apagar'), perigo: true })) return;
        await api(`/rotinas/${r.id}`, { metodo: 'DELETE' }); desenhar();
      } })));
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: t('Rotinas') }),
        el('p', { texto: t('Um pedido que o Claude faz sozinho no horário que você escolher: resumir os arquivos novos da pasta toda manhã, montar o relatório da semana na sexta, conferir uma planilha a cada 3 horas.') })),
      el('button', { class: 'botao primario', type: 'button', html: `${ic('mais')}${t('Nova rotina')}`, onclick: () => editarRotina(null, windows, desenhar) })),
    el('div', { class: 'nota-conversa economia' }, el('span', { html: ic('raio') }),
      el('span', { texto: t("Precisa de IA toda vez? Uma rotina chama o Claude a cada rodada e gasta sempre. Se a tarefa é sempre igual (ler e-mails de pedido e passar para a planilha, renomear arquivos, mandar o mesmo relatório), peça uma vez ao modo Code um programa sem IA: ele roda sozinho pelo Windows e custa zero por rodada.") }),
      el('button', { class: 'botao pequeno', type: 'button', html: `${ic('terminal')}${t('Montar no Code sem IA')}`, onclick: () => {
        sessionStorage.setItem('clave:rascunho', t("Quero automatizar uma tarefa que se repete, sem usar IA a cada vez. Antes de fazer, me pergunte o que preciso explicar (o que entra, o que sai, de quanto em quanto tempo) e me diga se dá para fazer sem IA. Depois monte um programa que roda sozinho, com modo de teste e registro do que fez, e agende no Windows."));
        location.hash = '#/code';
      } }),
      el('a', { href: '#/aprender/app-de-pedidos-sem-ia', texto: t('Ver a lição') })),
    el('div', { class: 'nota-conversa info' }, el('span', { html: ic('escudo') }),
      el('span', { html: t('Numa rotina ninguém está olhando, então ela só faz o que as suas <a href="#/permissoes">regras de permissão</a> já liberam (ler na pasta, e o que tiver regra de permitir). Se precisar de um OK, ela para e conta o que precisaria. Cada rodada tem teto de gasto.') })),
    rotinas.length ? el('div', { class: 'grade-cartoes' }, ...rotinas.map(cartao))
      : el('div', { class: 'vazio' }, el('p', { texto: t('Nenhuma rotina ainda.') }), el('a', { href: '#/aprender/rotinas', texto: t('Como as rotinas funcionam') })))));
  return {};
}

function editarRotina(r, windows, depois) {
  r = r || { modo: 'chat', quando: { tipo: 'diaria', hora: '08:00' }, modelo: 'claude-sonnet-5-5', esforco: 'medium', teto_usd: 0.5 };
  let pasta = r.pasta || '';
  const nome = el('input', { class: 'entrada', placeholder: t('Ex.: Resumo da manhã') }); nome.value = r.nome || '';
  const prompt = el('textarea', { class: 'area', rows: 4, placeholder: t('O que o Claude deve fazer, do começo ao fim, sem precisar perguntar nada.') }); prompt.value = r.prompt || '';
  const modo = el('select', { class: 'entrada' }, el('option', { value: 'chat', texto: t('No chat (sem pasta)'), selected: r.modo !== 'code' }),
    el('option', { value: 'code', texto: t('Numa pasta (modo Code)'), selected: r.modo === 'code' }));
  const pastaTexto = el('span', { class: 'meta', texto: pasta || t('nenhuma pasta escolhida') });
  const pastaLinha = el('div', { class: 'linha-pasta', hidden: r.modo !== 'code' }, pastaTexto,
    el('button', { class: 'botao pequeno', type: 'button', html: `${ic('pasta')}${t('Escolher')}`, onclick: async () => {
      const p = await escolherPasta({ titulo: t('Pasta da rotina') }); if (p) { pasta = p; pastaTexto.textContent = p; }
    } }));
  modo.addEventListener('change', () => { pastaLinha.hidden = modo.value !== 'code'; });
  const q = r.quando || {};
  const tipo = el('select', { class: 'entrada' },
    ...[['diaria', t('Todo dia')], ['semanal', t('Em alguns dias da semana')], ['horas', t('A cada N horas')]].map(([v, rot]) => el('option', { value: v, texto: rot, selected: (q.tipo || 'diaria') === v })));
  const hora = el('input', { class: 'entrada', type: 'time' }); hora.value = q.hora || '08:00';
  const aCada = el('input', { class: 'entrada', type: 'number', min: '1', max: '23' }); aCada.value = String(q.a_cada || 3);
  const dias = new Set((q.dias || [0, 1, 2, 3, 4]).map(Number));
  const diasEl = el('div', { class: 'checks dias' }, ...DIAS().map((d, i) => {
    const c = el('input', { type: 'checkbox', checked: dias.has(i) });
    c.addEventListener('change', () => (c.checked ? dias.add(i) : dias.delete(i)));
    return el('label', {}, c, ' ', d);
  }));
  const campoHora = el('label', {}, el('span', { texto: t('Hora') }), hora);
  const campoACada = el('label', {}, el('span', { texto: t('A cada quantas horas') }), aCada);
  const ajustar = () => { campoHora.hidden = tipo.value === 'horas'; campoACada.hidden = tipo.value !== 'horas'; diasEl.hidden = tipo.value !== 'semanal'; };
  tipo.addEventListener('change', ajustar); ajustar();
  const modelo = el('select', { class: 'entrada' }, ...(estado.info?.modelos || []).map((m) => el('option', { value: m.id, texto: m.nome, selected: m.id === r.modelo })));
  const esforco = el('select', { class: 'entrada' }, ...(estado.info?.esforcos || []).map((e) => el('option', { value: e.id, texto: e.nome, selected: e.id === r.esforco })));
  const teto = el('input', { class: 'entrada', type: 'number', min: '0.01', step: '0.1' }); teto.value = String(r.teto_usd ?? 0.5);
  const web = el('input', { type: 'checkbox', checked: !!r.busca_web });
  const agendador = el('input', { type: 'checkbox', checked: !!r.agendador, disabled: !windows });
  janela({
    titulo: r.id ? t('Editar rotina') : t('Nova rotina'), larga: true,
    corpo: el('div', { class: 'form-grade' },
      el('label', {}, el('span', { texto: t('Nome') }), nome),
      el('label', {}, el('span', { texto: t('O que fazer') }), prompt),
      el('div', { class: 'linha-campos' }, el('label', {}, el('span', { texto: t('Onde') }), modo), pastaLinha),
      el('div', { class: 'linha-campos' }, el('label', {}, el('span', { texto: t('Quando') }), tipo), campoHora, campoACada), diasEl,
      el('div', { class: 'linha-campos' }, el('label', {}, el('span', { texto: t('Modelo') }), modelo), el('label', {}, el('span', { texto: t('Raciocínio') }), esforco),
        el('label', {}, el('span', { texto: t('Teto por rodada (US$)') }), teto)),
      el('label', { class: 'check' }, web, ' ' + t('Pode pesquisar na web')),
      el('label', { class: 'check' }, agendador, ' ' + t('Rodar mesmo com o Clave fechado (cria uma tarefa no Agendador de Tarefas do Windows)')),
      el('small', { class: 'ajuda', texto: t('Com o Clave fechado, a rotina roda sem janela e avisa por notificação do Windows quando terminar. O computador precisa estar ligado.') })),
    botoes: [{ texto: t('Cancelar') }, { texto: t('Salvar'), classe: 'primario', acao: async () => {
      if (agendador.checked && !r.agendador && !await confirmar(t('O Clave vai criar uma tarefa no Agendador de Tarefas do Windows (pasta "Clave") para rodar esta rotina. Para tirar, é só desmarcar esta opção ou apagar a rotina.'), { titulo: t('Agendador do Windows'), sim: t('Criar a tarefa') })) return false;
      try {
        await api('/rotinas', { metodo: 'POST', corpo: {
          id: r.id, nome: nome.value, prompt: prompt.value, modo: modo.value, pasta: modo.value === 'code' ? pasta : null,
          quando: { tipo: tipo.value, hora: hora.value, a_cada: Number(aCada.value), dias: [...dias] },
          modelo: modelo.value, esforco: esforco.value, teto_usd: Number(teto.value), busca_web: web.checked,
          agendador: agendador.checked, ligada: r.ligada ?? true,
        } });
        aviso(t('Rotina salva.')); depois?.();
      } catch (e) { aviso(e.message, 'erro'); return false; }
    } }],
  });
}
