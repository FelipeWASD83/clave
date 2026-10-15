// Estado compartilhado da interface e um avisador simples de mudanças.
import { api } from './api.js';

export const estado = {
  info: null,          // resposta de /api/estado (configurações, teto, modelos...)
  conversas: [],
  busca: '',
  conversaAtual: null, // id
  rodando: new Map(),  // conversa_id -> execucao_id
};

const ouvintes = new Map();
export function ouvir(evento, fn) {
  if (!ouvintes.has(evento)) ouvintes.set(evento, new Set());
  ouvintes.get(evento).add(fn);
  return () => ouvintes.get(evento)?.delete(fn);
}
export function avisar(evento, dados) {
  for (const fn of ouvintes.get(evento) || []) {
    try { fn(dados); } catch (e) { console.error(e); }
  }
}

export const cfg = () => estado.info?.cfg || {};

export async function carregarEstado() {
  estado.info = await api('/estado');
  aplicarAparencia();
  avisar('estado', estado.info);
  return estado.info;
}

export async function salvarConfig(alteracoes) {
  const r = await api('/config', { metodo: 'POST', corpo: alteracoes });
  estado.info.cfg = r.cfg;
  estado.info.estilos = r.estilos;
  estado.info.orcamento = r.orcamento;
  aplicarAparencia();
  avisar('estado', estado.info);
  return r.cfg;
}

export function atualizarOrcamento(orc) {
  if (!estado.info || !orc) return;
  estado.info.orcamento = orc;
  avisar('orcamento', orc);
}

export async function carregarConversas() {
  const q = estado.busca ? `?busca=${encodeURIComponent(estado.busca)}` : '';
  const r = await api('/conversas' + q);
  estado.conversas = r.conversas;
  avisar('conversas', estado.conversas);
}

export function aplicarAparencia() {
  const c = cfg();
  const raiz = document.documentElement;
  if (c.tema === 'claro' || c.tema === 'escuro') raiz.dataset.tema = c.tema;
  else delete raiz.dataset.tema;
  document.body.dataset.largura = c.largura_chat || 'media';
  document.body.dataset.letra = c.letra_resposta || 'serifa';
  raiz.style.setProperty('--t-leitura', `${c.tamanho_letra || 17}px`);
}

export function modeloInfo(id) {
  return (estado.info?.modelos || []).find((m) => m.id === id) || { id, nome: id, esforco: true };
}

// O nome em inglês de um comando, plugin, skill ou fluxo que vem com o Clave (comandos.NOMES_EN no servidor), com a
// interface em inglês; cada parte separada por ":" é traduzida. Os dois nomes funcionam ao digitar.
export function nomeComando(nome) {
  if (cfg()?.idioma !== 'en') return nome;
  const mapa = estado.info?.nomes_en || {};
  return String(nome).split(':').map((p) => mapa[p] || p).join(':');
}
