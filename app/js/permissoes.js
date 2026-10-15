// Permissões: as regras que decidem o que o Claude faz sozinho, o que pergunta e o que nunca faz.
import { api } from './api.js';
import { cfg } from './estado.js';
import { ic } from './icones.js';
import { el, aviso, confirmar } from './ui.js';
import { escolherPasta } from './pastas.js';

const ACOES = [['deny', 'Nunca', 'perigo'], ['ask', 'Sempre perguntar', ''], ['allow', 'Fazer sem perguntar', 'acao']];
const DECISAO = { auto: 'fez sozinho', permitir: 'você permitiu', recusar: 'você recusou', negar: 'bloqueado', perguntar: 'perguntaria' };
const ORIGEM = { regra: 'por uma regra', modo: 'pelo modo de permissão', voce: 'por você', protegido: 'arquivo protegido', perigoso: 'comando perigoso', tarefa: '"nesta tarefa"', rotina: 'rotina sem regra', clave: 'pelo Clave' };
const EXEMPLOS = [
  ['allow', 'Bash(git status *)', 'ver o estado do git sem perguntar'],
  ['allow', 'Bash(npm test *)', 'rodar os testes sem perguntar'],
  ['allow', 'Edit(docs/**)', 'mudar qualquer arquivo dentro de docs'],
  ['allow', 'Read(//c/Users/*/Documents/Planilhas/**)', 'ler uma pasta fora da pasta de trabalho'],
  ['ask', 'Edit(*.xlsx)', 'sempre perguntar antes de mexer em planilha, mesmo no modo Livre'],
  ['deny', 'Bash(git push *)', 'nunca mandar nada para o GitHub'],
  ['deny', 'WebFetch(domain:exemplo.com)', 'nunca abrir páginas de um site'],
  ['deny', 'Fluxo', 'o Claude nunca propõe fluxos'],
];

let pastaAtual = '';

function listaRegras(regras, aoApagar) {
  return el('div', { class: 'regras-colunas' }, ...ACOES.map(([acao, titulo, cls]) => {
    const minhas = regras.filter((r) => r.acao === acao);
    return el('div', { class: `regras-coluna ${cls}` }, el('div', { class: 'rotulo', texto: titulo }),
      minhas.length ? el('ul', {}, ...minhas.map((r) => el('li', {},
        el('code', { texto: r.texto }),
        r.origem ? el('small', { class: 'meta', title: r.origem, texto: r.origem.split(/[\\/]/).pop() }) : null,
        el('button', { class: 'icone-botao', type: 'button', 'aria-label': `Apagar a regra ${r.texto}`, html: ic('x'), onclick: () => aoApagar(r) }))))
        : el('p', { class: 'ajuda', texto: 'nenhuma' }));
  }));
}

function formNova(aoAdicionar) {
  const acao = el('select', { class: 'entrada', 'aria-label': 'O que fazer' }, ...ACOES.map(([v, t]) => el('option', { value: v, texto: t })));
  const regra = el('input', { class: 'entrada mono', placeholder: 'Bash(git status *)', 'aria-label': 'Regra', spellcheck: 'false' });
  const enviar = async () => {
    if (!regra.value.trim()) return;
    try { await aoAdicionar(acao.value, regra.value.trim()); regra.value = ''; } catch (e) { aviso(e.message, 'erro'); }
  };
  regra.addEventListener('keydown', (e) => { if (e.key === 'Enter') enviar(); });
  return el('div', { class: 'linha-regra' }, acao, regra, el('button', { class: 'botao', type: 'button', html: `${ic('mais')}Adicionar`, onclick: enviar }));
}

export async function telaPermissoes(principal) {
  const corpo = el('div', {});
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: 'Permissões' }),
        el('p', { texto: 'Regras que decidem o que o Claude faz sozinho, o que ele pergunta antes e o que ele nunca faz. Valem por cima do modo escolhido na caixa de mensagem (Perguntar, Aceitar edições, Plano, Livre).' }))),
    corpo)));
  await desenhar(corpo);
  return {};
}

async function desenhar(corpo) {
  const q = pastaAtual ? `?pasta=${encodeURIComponent(pastaAtual)}` : '';
  let dados;
  try { dados = await api(`/permissoes${q}`); } catch (e) { pastaAtual = ''; aviso(e.message, 'erro'); dados = await api('/permissoes'); }
  const regrasApp = ACOES.flatMap(([acao]) => (dados.app[acao] || []).map((texto) => ({ acao, texto })));
  const recarregar = () => desenhar(corpo);

  const secApp = el('section', { class: 'config-secao' },
    el('h2', { texto: 'Regras do Clave (todas as pastas)' }),
    listaRegras(regrasApp, async (r) => {
      await api('/permissoes', { metodo: 'DELETE', corpo: { escopo: 'app', acao: r.acao, regra: r.texto } }); recarregar();
    }),
    formNova(async (acao, regra) => { await api('/permissoes', { metodo: 'POST', corpo: { escopo: 'app', acao, regra } }); aviso('Regra salva.'); recarregar(); }));

  const recentes = cfg().pastas_recentes || [];
  const seletor = el('select', { class: 'entrada', 'aria-label': 'Pasta' }, el('option', { value: '', texto: 'Escolha uma pasta…' }),
    ...recentes.map((p) => el('option', { value: p, texto: p, selected: p === pastaAtual })));
  seletor.addEventListener('change', () => { pastaAtual = seletor.value; recarregar(); });
  const pastaBloco = dados.pasta ? el('div', {},
    listaRegras(dados.pasta.regras, async (r) => {
      await api('/permissoes', { metodo: 'DELETE', corpo: { escopo: 'pasta', pasta: pastaAtual, acao: r.acao, regra: r.texto } }); recarregar();
    }),
    ...dados.pasta.avisos.map((a) => el('p', { class: 'nota-conversa', texto: a })),
    formNova(async (acao, regra) => { await api('/permissoes', { metodo: 'POST', corpo: { escopo: 'pasta', pasta: pastaAtual, acao, regra } }); aviso('Regra salva na pasta.'); recarregar(); }),
    el('small', { class: 'ajuda', html: 'Ficam em <code>.claude/settings.json</code> (compartilhado) e <code>.claude/settings.local.json</code> (só seu) dentro da pasta: os mesmos arquivos do Claude Code. As que você cria aqui vão para o <code>settings.local.json</code>.' }))
    : el('p', { class: 'ajuda', texto: 'Escolha uma pasta para ver e mudar as regras dela.' });
  const secPasta = el('section', { class: 'config-secao' },
    el('h2', { texto: 'Regras de uma pasta' }),
    el('div', { class: 'linha-regra' }, seletor, el('button', { class: 'botao', type: 'button', html: `${ic('pasta')}Outra pasta`, onclick: async () => {
      const p = await escolherPasta({ titulo: 'Pasta' }); if (p) { pastaAtual = p; recarregar(); }
    } })),
    pastaBloco);

  // testador
  const ferr = el('select', { class: 'entrada', 'aria-label': 'Tipo de ação' },
    ...[['Bash', 'Rodar o comando'], ['Edit', 'Mudar o arquivo'], ['Read', 'Ler o arquivo'], ['WebFetch', 'Abrir a página']].map(([v, t]) => el('option', { value: v, texto: t })));
  const valor = el('input', { class: 'entrada mono', placeholder: 'git push origin main', spellcheck: 'false' });
  const modo = el('select', { class: 'entrada', 'aria-label': 'Modo' },
    ...[['perguntar', 'no modo Perguntar'], ['aceitar_edicoes', 'no modo Aceitar edições'], ['plano', 'no modo Plano'], ['livre', 'no modo Livre']].map(([v, t]) => el('option', { value: v, texto: t })));
  const resposta = el('div', { class: 'resultado-teste', hidden: true });
  const testar = async () => {
    if (!valor.value.trim()) return;
    try {
      const r = await api('/permissoes/testar', { metodo: 'POST', corpo: { ferramenta: ferr.value, valor: valor.value, modo: modo.value, pasta: pastaAtual || undefined } });
      const frase = { auto: 'O Claude faria sozinho', perguntar: 'O Claude pediria o seu OK', negar: 'O Claude não poderia fazer' }[r.decisao] || r.decisao;
      resposta.hidden = false;
      resposta.className = `resultado-teste ${r.decisao}`;
      resposta.replaceChildren(el('b', { texto: frase }),
        el('span', { texto: r.motivo ? ` (${r.motivo})` : (r.regra ? ` (regra ${r.regra})` : ` (${ORIGEM[r.origem] || r.origem})`) }),
        r.decisao === 'perguntar' && r.sugestao ? el('small', { class: 'ajuda', texto: `Para liberar: regra de "fazer sem perguntar" ${r.sugestao}` }) : null);
    } catch (e) { aviso(e.message, 'erro'); }
  };
  valor.addEventListener('keydown', (e) => { if (e.key === 'Enter') testar(); });
  const secTeste = el('section', { class: 'config-secao' },
    el('h2', { texto: 'Testar' }), el('p', { texto: 'Esta ação passaria? Responde sem rodar nada, usando as regras acima (e as da pasta escolhida).' }),
    el('div', { class: 'linha-regra' }, ferr, valor, modo, el('button', { class: 'botao primario', type: 'button', texto: 'Testar', onclick: testar })),
    resposta);

  const secExemplos = el('section', { class: 'config-secao' },
    el('h2', { texto: 'Como escrever uma regra' }),
    el('p', { html: 'O formato é o do Claude Code: <code>Ferramenta(padrão)</code>. <code>Bash</code> é comando (o <code>*</code> vale qualquer coisa), <code>Read</code> é ler, <code>Edit</code> é criar ou mudar arquivo (padrões como no .gitignore: <code>docs/**</code>, <code>*.xlsx</code>; <code>//c/...</code> é caminho completo), <code>WebFetch(domain:site.com)</code> é página da web, <code>mcp__conector</code> é um conector. A ordem é: <b>nunca</b> vence <b>sempre perguntar</b>, que vence <b>fazer sem perguntar</b>.' }),
    el('table', { class: 'tabela' }, el('tbody', {}, ...EXEMPLOS.map(([acao, regra, desc]) => el('tr', {},
      el('td', { texto: ACOES.find((a) => a[0] === acao)[1] }), el('td', {}, el('code', { texto: regra })), el('td', { texto: desc }))))),
    el('p', { class: 'ajuda', html: 'Algumas proteções não mudam com regra: arquivos protegidos (<a href="#/config/code">Configurações &gt; Modo Code</a>) nunca são lidos nem mudados; comando que apaga ou publica pergunta mesmo com <code>Bash</code> liberado, a não ser que a regra seja escrita para ele; e fluxo sempre pede OK.' }));

  // histórico
  const filtro = el('select', { class: 'entrada', 'aria-label': 'Filtrar' }, el('option', { value: '', texto: 'Tudo' }),
    ...Object.entries(DECISAO).map(([v, t]) => el('option', { value: v, texto: t })));
  const tabela = el('div', {});
  const carregarHist = async () => {
    const { registros } = await api(`/permissoes/historico?decisao=${filtro.value}`);
    tabela.replaceChildren(registros.length ? el('table', { class: 'tabela' },
      el('thead', {}, el('tr', {}, ...['Quando', 'Ação', 'Em quê', 'Resultado', 'Por quê'].map((t) => el('th', { texto: t })))),
      el('tbody', {}, ...registros.map((r) => el('tr', {},
        el('td', { texto: new Date(r.criado_em * 1000).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' }) }),
        el('td', { texto: r.ferramenta }),
        el('td', {}, el('code', { class: 'corta', title: r.alvo, texto: r.alvo })),
        el('td', { class: `decisao ${r.decisao}`, texto: DECISAO[r.decisao] || r.decisao }),
        el('td', { texto: r.regra ? `regra ${r.regra}` : (ORIGEM[r.origem] || r.origem) })))))
      : el('p', { class: 'ajuda', texto: 'Nada registrado ainda.' }));
  };
  filtro.addEventListener('change', carregarHist);
  const secHist = el('section', { class: 'config-secao' },
    el('h2', { texto: 'Histórico' }), el('p', { texto: 'Cada ação do modo Code, de fluxo e de rotina, com o que foi decidido e por quê (guarda as últimas 5 mil).' }),
    el('div', { class: 'linha-regra' }, filtro, el('button', { class: 'botao pequeno fantasma', type: 'button', texto: 'Limpar o histórico', onclick: async () => {
      if (await confirmar('Apagar o histórico de permissões?', { titulo: 'Limpar histórico', sim: 'Apagar', perigo: true })) { await api('/permissoes/historico', { metodo: 'DELETE' }); carregarHist(); }
    } })),
    tabela);
  corpo.replaceChildren(secApp, secPasta, secTeste, secExemplos, secHist);
  carregarHist();
}
