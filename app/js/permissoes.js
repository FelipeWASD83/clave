// Permissões: as regras que decidem o que o Claude faz sozinho, o que pergunta e o que nunca faz.
import { api } from './api.js';
import { cfg } from './estado.js';
import { ic } from './icones.js';
import { el, aviso, confirmar, dataHora } from './ui.js';
import { escolherPasta } from './pastas.js';
import { t } from './i18n.js';

const ACOES = () => [['deny', t('Nunca'), 'perigo'], ['ask', t('Sempre perguntar'), ''], ['allow', t('Fazer sem perguntar'), 'acao']];
const DECISAO = () => ({ auto: t('fez sozinho'), permitir: t('você permitiu'), recusar: t('você recusou'), negar: t('bloqueado'), perguntar: t('perguntaria') });
const ORIGEM = () => ({ regra: t('por uma regra'), modo: t('pelo modo de permissão'), voce: t('por você'), protegido: t('arquivo protegido'), perigoso: t('comando perigoso'), tarefa: t('"nesta tarefa"'), rotina: t('rotina sem regra'), clave: t('pelo Clave') });
const EXEMPLOS = () => [
  ['allow', 'Bash(git status *)', t('ver o estado do git sem perguntar')],
  ['allow', 'Bash(npm test *)', t('rodar os testes sem perguntar')],
  ['allow', 'Edit(docs/**)', t('mudar qualquer arquivo dentro de docs')],
  ['allow', 'Read(//c/Users/*/Documents/Planilhas/**)', t('ler uma pasta fora da pasta de trabalho')],
  ['ask', 'Edit(*.xlsx)', t('sempre perguntar antes de mexer em planilha, mesmo no modo Livre')],
  ['deny', 'Bash(git push *)', t('nunca mandar nada para o GitHub')],
  ['deny', 'WebFetch(domain:exemplo.com)', t('nunca abrir páginas de um site')],
  ['deny', 'Fluxo', t('o Claude nunca propõe fluxos')],
];

let pastaAtual = '';

function listaRegras(regras, aoApagar) {
  return el('div', { class: 'regras-colunas' }, ...ACOES().map(([acao, titulo, cls]) => {
    const minhas = regras.filter((r) => r.acao === acao);
    return el('div', { class: `regras-coluna ${cls}` }, el('div', { class: 'rotulo', texto: titulo }),
      minhas.length ? el('ul', {}, ...minhas.map((r) => el('li', {},
        el('code', { texto: r.texto }),
        r.origem ? el('small', { class: 'meta', title: r.origem, texto: r.origem.split(/[\\/]/).pop() }) : null,
        el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar a regra {regra}', { regra: r.texto }), html: ic('x'), onclick: () => aoApagar(r) }))))
        : el('p', { class: 'ajuda', texto: t('nenhuma') }));
  }));
}

function formNova(aoAdicionar) {
  const acao = el('select', { class: 'entrada', 'aria-label': t('O que fazer') }, ...ACOES().map(([v, rot]) => el('option', { value: v, texto: rot })));
  const regra = el('input', { class: 'entrada mono', placeholder: 'Bash(git status *)', 'aria-label': t('Regra'), spellcheck: 'false' });
  const enviar = async () => {
    if (!regra.value.trim()) return;
    try { await aoAdicionar(acao.value, regra.value.trim()); regra.value = ''; } catch (e) { aviso(e.message, 'erro'); }
  };
  regra.addEventListener('keydown', (e) => { if (e.key === 'Enter') enviar(); });
  return el('div', { class: 'linha-regra' }, acao, regra, el('button', { class: 'botao', type: 'button', html: `${ic('mais')}${t('Adicionar')}`, onclick: enviar }));
}

export async function telaPermissoes(principal) {
  const corpo = el('div', {});
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: t('Permissões') }),
        el('p', { texto: t('Regras que decidem o que o Claude faz sozinho, o que ele pergunta antes e o que ele nunca faz. Valem por cima do modo escolhido na caixa de mensagem (Perguntar, Aceitar edições, Plano, Livre).') }))),
    corpo)));
  await desenhar(corpo);
  return {};
}

async function desenhar(corpo) {
  const q = pastaAtual ? `?pasta=${encodeURIComponent(pastaAtual)}` : '';
  let dados;
  try { dados = await api(`/permissoes${q}`); } catch (e) { pastaAtual = ''; aviso(e.message, 'erro'); dados = await api('/permissoes'); }
  const acoes = ACOES();
  const origens = ORIGEM();
  const decisoes = DECISAO();
  const regrasApp = acoes.flatMap(([acao]) => (dados.app[acao] || []).map((texto) => ({ acao, texto })));
  const recarregar = () => desenhar(corpo);

  const secApp = el('section', { class: 'config-secao' },
    el('h2', { texto: t('Regras do Clave (todas as pastas)') }),
    listaRegras(regrasApp, async (r) => {
      await api('/permissoes', { metodo: 'DELETE', corpo: { escopo: 'app', acao: r.acao, regra: r.texto } }); recarregar();
    }),
    formNova(async (acao, regra) => { await api('/permissoes', { metodo: 'POST', corpo: { escopo: 'app', acao, regra } }); aviso(t('Regra salva.')); recarregar(); }));

  const recentes = cfg().pastas_recentes || [];
  const seletor = el('select', { class: 'entrada', 'aria-label': t('Pasta') }, el('option', { value: '', texto: t('Escolha uma pasta…') }),
    ...recentes.map((p) => el('option', { value: p, texto: p, selected: p === pastaAtual })));
  seletor.addEventListener('change', () => { pastaAtual = seletor.value; recarregar(); });
  const pastaBloco = dados.pasta ? el('div', {},
    listaRegras(dados.pasta.regras, async (r) => {
      await api('/permissoes', { metodo: 'DELETE', corpo: { escopo: 'pasta', pasta: pastaAtual, acao: r.acao, regra: r.texto } }); recarregar();
    }),
    ...dados.pasta.avisos.map((a) => el('p', { class: 'nota-conversa', texto: a })),
    formNova(async (acao, regra) => { await api('/permissoes', { metodo: 'POST', corpo: { escopo: 'pasta', pasta: pastaAtual, acao, regra } }); aviso(t('Regra salva na pasta.')); recarregar(); }),
    el('small', { class: 'ajuda', html: t('Ficam em <code>.claude/settings.json</code> (compartilhado) e <code>.claude/settings.local.json</code> (só seu) dentro da pasta: os mesmos arquivos do Claude Code. As que você cria aqui vão para o <code>settings.local.json</code>.') }))
    : el('p', { class: 'ajuda', texto: t('Escolha uma pasta para ver e mudar as regras dela.') });
  const secPasta = el('section', { class: 'config-secao' },
    el('h2', { texto: t('Regras de uma pasta') }),
    el('div', { class: 'linha-regra' }, seletor, el('button', { class: 'botao', type: 'button', html: `${ic('pasta')}${t('Outra pasta')}`, onclick: async () => {
      const p = await escolherPasta({ titulo: t('Pasta') }); if (p) { pastaAtual = p; recarregar(); }
    } })),
    pastaBloco);

  // testador
  const ferr = el('select', { class: 'entrada', 'aria-label': t('Tipo de ação') },
    ...[['Bash', t('Rodar o comando')], ['Edit', t('Mudar o arquivo')], ['Read', t('Ler o arquivo')], ['WebFetch', t('Abrir a página')]].map(([v, rot]) => el('option', { value: v, texto: rot })));
  const valor = el('input', { class: 'entrada mono', placeholder: 'git push origin main', spellcheck: 'false' });
  const modo = el('select', { class: 'entrada', 'aria-label': t('Modo') },
    ...[['perguntar', t('no modo Perguntar')], ['aceitar_edicoes', t('no modo Aceitar edições')], ['plano', t('no modo Plano')], ['livre', t('no modo Livre')]].map(([v, rot]) => el('option', { value: v, texto: rot })));
  const resposta = el('div', { class: 'resultado-teste', hidden: true });
  const testar = async () => {
    if (!valor.value.trim()) return;
    try {
      const r = await api('/permissoes/testar', { metodo: 'POST', corpo: { ferramenta: ferr.value, valor: valor.value, modo: modo.value, pasta: pastaAtual || undefined } });
      const frase = { auto: t('O Claude faria sozinho'), perguntar: t('O Claude pediria o seu OK'), negar: t('O Claude não poderia fazer') }[r.decisao] || r.decisao;
      resposta.hidden = false;
      resposta.className = `resultado-teste ${r.decisao}`;
      resposta.replaceChildren(el('b', { texto: frase }),
        el('span', { texto: r.motivo ? ` (${r.motivo})` : (r.regra ? ` (${t('regra {regra}', { regra: r.regra })})` : ` (${origens[r.origem] || r.origem})`) }),
        r.decisao === 'perguntar' && r.sugestao ? el('small', { class: 'ajuda', texto: t('Para liberar: regra de "fazer sem perguntar" {regra}', { regra: r.sugestao }) }) : null);
    } catch (e) { aviso(e.message, 'erro'); }
  };
  valor.addEventListener('keydown', (e) => { if (e.key === 'Enter') testar(); });
  const secTeste = el('section', { class: 'config-secao' },
    el('h2', { texto: t('Testar') }), el('p', { texto: t('Esta ação passaria? Responde sem rodar nada, usando as regras acima (e as da pasta escolhida).') }),
    el('div', { class: 'linha-regra' }, ferr, valor, modo, el('button', { class: 'botao primario', type: 'button', texto: t('Testar'), onclick: testar })),
    resposta);

  const secExemplos = el('section', { class: 'config-secao' },
    el('h2', { texto: t('Como escrever uma regra') }),
    el('p', { html: t('O formato é o do Claude Code: <code>Ferramenta(padrão)</code>. <code>Bash</code> é comando (o <code>*</code> vale qualquer coisa), <code>Read</code> é ler, <code>Edit</code> é criar ou mudar arquivo (padrões como no .gitignore: <code>docs/**</code>, <code>*.xlsx</code>; <code>//c/...</code> é caminho completo), <code>WebFetch(domain:site.com)</code> é página da web, <code>mcp__conector</code> é um conector. A ordem é: <b>nunca</b> vence <b>sempre perguntar</b>, que vence <b>fazer sem perguntar</b>.') }),
    el('table', { class: 'tabela' }, el('tbody', {}, ...EXEMPLOS().map(([acao, regra, desc]) => el('tr', {},
      el('td', { texto: acoes.find((a) => a[0] === acao)[1] }), el('td', {}, el('code', { texto: regra })), el('td', { texto: desc }))))),
    el('p', { class: 'ajuda', html: t('Algumas proteções não mudam com regra: arquivos protegidos (<a href="#/config/code">Configurações &gt; Modo Code</a>) nunca são lidos nem mudados; comando que apaga ou publica pergunta mesmo com <code>Bash</code> liberado, a não ser que a regra seja escrita para ele; e fluxo sempre pede OK.') }));

  // histórico
  const filtro = el('select', { class: 'entrada', 'aria-label': t('Filtrar') }, el('option', { value: '', texto: t('Tudo') }),
    ...Object.entries(decisoes).map(([v, rot]) => el('option', { value: v, texto: rot })));
  const tabela = el('div', {});
  const carregarHist = async () => {
    const { registros } = await api(`/permissoes/historico?decisao=${filtro.value}`);
    tabela.replaceChildren(registros.length ? el('table', { class: 'tabela' },
      el('thead', {}, el('tr', {}, ...[t('Quando'), t('Ação'), t('Em quê'), t('Resultado'), t('Por quê')].map((x) => el('th', { texto: x })))),
      el('tbody', {}, ...registros.map((r) => el('tr', {},
        el('td', { texto: dataHora(r.criado_em) }),
        el('td', { texto: r.ferramenta }),
        el('td', {}, el('code', { class: 'corta', title: r.alvo, texto: r.alvo })),
        el('td', { class: `decisao ${r.decisao}`, texto: decisoes[r.decisao] || r.decisao }),
        el('td', { texto: r.regra ? t('regra {regra}', { regra: r.regra }) : (origens[r.origem] || r.origem) })))))
      : el('p', { class: 'ajuda', texto: t('Nada registrado ainda.') }));
  };
  filtro.addEventListener('change', carregarHist);
  const secHist = el('section', { class: 'config-secao' },
    el('h2', { texto: t('Histórico') }), el('p', { texto: t('Cada ação do modo Code, de fluxo e de rotina, com o que foi decidido e por quê (guarda as últimas 5 mil).') }),
    el('div', { class: 'linha-regra' }, filtro, el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Limpar o histórico'), onclick: async () => {
      if (await confirmar(t('Apagar o histórico de permissões?'), { titulo: t('Limpar histórico'), sim: t('Apagar'), perigo: true })) { await api('/permissoes/historico', { metodo: 'DELETE' }); carregarHist(); }
    } })),
    tabela);
  corpo.replaceChildren(secApp, secPasta, secTeste, secExemplos, secHist);
  carregarHist();
}
