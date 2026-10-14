// Botão de atualizar: pergunta ao GitHub se tem versão nova e instala quando a pessoa manda.
import { api } from './api.js';
import { estado, avisar } from './estado.js';
import { el, janela, aviso } from './ui.js';
import { markdownSeguro } from './markdown.js';

let ultima = null;

export async function checarAtualizacao({ forcar = false, silencioso = false } = {}) {
  try {
    ultima = await api(`/atualizacao${forcar ? '?forcar=1' : ''}`);
    if (estado.info) estado.info.atualizacao = { nova: ultima.nova, ultima: ultima.ultima };
    avisar('atualizacao', ultima);
    if (!silencioso) {
      if (ultima.erro) aviso(ultima.erro, 'erro');
      else if (!ultima.nova) aviso(`Você já está na versão mais nova (${ultima.atual}).`);
    }
    return ultima;
  } catch (e) {
    if (!silencioso) aviso(e.message, 'erro');
    return null;
  }
}

export async function abrirAtualizacao() {
  const info = ultima?.nova ? ultima : await checarAtualizacao({ forcar: true });
  if (!info?.nova) return;
  const notas = markdownSeguro(info.notas || 'Sem notas desta versão.');
  notas.classList.add('resposta');
  notas.style.cssText = 'max-height:300px;overflow:auto;font-size:15px';
  janela({
    titulo: `Versão ${info.ultima} disponível`, larga: true,
    corpo: el('div', { style: 'display:grid;gap:12px' },
      el('p', { class: 'ajuda', style: 'margin:0', texto: `Você está na ${info.atual}. A atualização baixa a versão nova do GitHub, guarda a atual (para voltar se algo der errado) e reinicia o Clave. Suas conversas e configurações não são tocadas.` }),
      el('div', { class: 'rotulo', texto: 'O que mudou' }), notas),
    botoes: [
      { texto: 'Agora não' },
      { texto: 'Atualizar e reiniciar', classe: 'primario', acao: async () => {
        await api('/atualizacao/aplicar', { metodo: 'POST' });
        esperarVoltar(info.ultima);
      } },
    ],
  });
}

function esperarVoltar(versao) {
  document.getElementById('principal').replaceChildren(el('div', { class: 'vazio' },
    el('h2', { texto: 'Atualizando…' }), el('p', { texto: `Instalando a versão ${versao}. O Clave volta sozinho em alguns segundos.` })));
  const inicio = Date.now();
  const tentar = async () => {
    try {
      const r = await fetch('/api/saude', { credentials: 'same-origin' }).then((x) => x.json());
      if (r.versao === versao) {
        if (window.clave?.reiniciar) window.clave.reiniciar();
        else location.reload();
        return;
      }
    } catch { /* ainda reiniciando */ }
    if (Date.now() - inicio > 180_000) {
      document.getElementById('principal').replaceChildren(el('div', { class: 'vazio' },
        el('h2', { texto: 'A atualização está demorando' }), el('p', { texto: 'Feche o Clave e abra de novo. Se a versão nova não subir, o Clave volta sozinho para a anterior.' })));
      return;
    }
    setTimeout(tentar, 1500);
  };
  setTimeout(tentar, 2500);
}
