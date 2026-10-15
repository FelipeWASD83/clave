// Início do app: carrega o estado, monta a barra lateral e troca de tela conforme o endereço (#/...).
import { api } from './api.js';
import { estado, carregarEstado, carregarConversas, ouvir } from './estado.js';
import { montarLateral, marcarAtual, alternarLateral } from './lateral.js';
import { abrirConversa, novaConversa } from './conversa.js';
import { telaProjetos, telaProjeto } from './projetos.js';
import { telaAprender, telaLicao } from './aprender.js';
import { telaUso } from './uso.js';
import { telaConfig } from './config.js';
import { boasVindas } from './boas-vindas.js';
import { checarAtualizacao } from './atualizar.js';
import { telaFluxos } from './fluxos.js';
import { telaPlugins } from './plugins.js';
import { telaRotinas } from './rotinas.js';
import { telaPrecos } from './precos.js';
import { telaPermissoes } from './permissoes.js';
import { notificar } from './fluxo-ui.js';
import { aviso, el } from './ui.js';

const principal = document.getElementById('principal');
let telaAtual = null;

function rota() {
  const h = location.hash.replace(/^#\/?/, '');
  const [a, b, c] = h.split('/');
  return { a: a || 'novo', b, c };
}

async function trocarTela() {
  const { a, b, c } = rota();
  telaAtual?.sair?.();
  telaAtual = null;
  document.getElementById('app').classList.remove('lateral-aberta');
  try {
    if (a === 'c' && b) telaAtual = await abrirConversa(principal, b);
    else if (a === 'novo') telaAtual = await novaConversa(principal, { modo: 'chat', projeto: b === 'projeto' ? c : null });
    else if (a === 'code') telaAtual = await novaConversa(principal, { modo: 'code' });
    else if (a === 'projetos' && b) telaAtual = await telaProjeto(principal, b);
    else if (a === 'projetos') telaAtual = await telaProjetos(principal);
    else if (a === 'aprender' && b) telaAtual = await telaLicao(principal, b, c);
    else if (a === 'aprender') telaAtual = await telaAprender(principal);
    else if (a === 'uso') telaAtual = await telaUso(principal);
    else if (a === 'fluxos') telaAtual = await telaFluxos(principal, b);
    else if (a === 'plugins') telaAtual = await telaPlugins(principal);
    else if (a === 'rotinas') telaAtual = await telaRotinas(principal);
    else if (a === 'precos') telaAtual = await telaPrecos(principal);
    else if (a === 'permissoes') telaAtual = await telaPermissoes(principal);
    else if (a === 'config') telaAtual = await telaConfig(principal, b);
    else location.hash = '#/novo';
  } catch (e) {
    console.error(e);
    principal.replaceChildren(el('div', { class: 'vazio' }, el('p', { texto: e.message || String(e) }),
      el('a', { href: '#/novo', texto: 'Voltar ao início' })));
  }
  marcarAtual();
}

function atalhos(e) {
  const ctrl = e.ctrlKey || e.metaKey;
  if (ctrl && e.shiftKey && (e.key === 'O' || e.key === 'o')) { e.preventDefault(); location.hash = '#/novo'; }
  else if (ctrl && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); document.querySelector('.busca-lateral input')?.focus(); }
  else if (ctrl && e.key === 'b') { e.preventDefault(); alternarLateral(); }
  else if (ctrl && e.key === ',') { e.preventDefault(); location.hash = '#/config'; }
}

function sessaoInvalida() {
  principal.replaceChildren(el('div', { class: 'vazio' },
    el('h2', { texto: 'Abra o Clave pelo atalho' }),
    el('p', { texto: 'Esta janela não tem a sessão do Clave (ela é criada quando você abre pelo atalho Clave na área de trabalho ou pelo Clave.bat). Feche e abra de novo por lá.' })));
}

async function iniciar() {
  document.addEventListener('clave:sessao', sessaoInvalida, { once: true });
  try {
    await carregarEstado();
  } catch (e) {
    if (e.status === 401) return sessaoInvalida();
    principal.replaceChildren(el('div', { class: 'vazio', texto: e.message }));
    return;
  }
  montarLateral(document.getElementById('lateral'));
  await carregarConversas().catch(() => {});
  window.addEventListener('hashchange', trocarTela);
  document.addEventListener('keydown', atalhos);
  await trocarTela();
  if (!estado.info.cfg.configurado) boasVindas();
  else if (estado.info.cfg.checar_atualizacoes && !estado.info.dev) checarAtualizacao({ silencioso: true });
  ouvir('conversas-mudaram', () => carregarConversas().catch(() => {}));
  // sinal de vida: sem a janela aberta por muito tempo, o servidor fecha sozinho (no modo navegador)
  setInterval(() => api('/saude').catch(() => {}), 60_000);
  acompanharAvisos();
  window.clave?.aoPedir?.((pedido) => {
    if (pedido === 'nova-conversa') location.hash = '#/novo';
    if (pedido === 'configuracoes') location.hash = '#/config';
  });
}

// rotinas que terminaram (ou pararam) enquanto a pessoa fazia outra coisa
async function acompanharAvisos() {
  let visto = null;
  const buscar = async () => {
    try {
      const r = await api(`/avisos?desde=${visto ?? 0}`);
      if (visto !== null) {
        for (const a of r.avisos) {
          if (a.tipo !== 'rotina') continue;
          const texto = `Rotina "${a.nome}": ${a.status}.`;
          aviso(texto, /parou|erro|bloquead/.test(a.status) ? 'erro' : '');
          notificar('Clave', texto);
        }
        if (r.avisos.length) import('./estado.js').then((m) => m.avisar('conversas-mudaram'));
      }
      visto = r.total;
    } catch { /* tenta de novo na próxima */ }
  };
  await buscar();
  setInterval(buscar, 20_000);
}

window.addEventListener('unhandledrejection', (e) => {
  const m = e.reason?.message;
  if (m) aviso(m, 'erro');
});

iniciar();
