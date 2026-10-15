// Botão de atualizar: pergunta ao GitHub se tem versão nova e instala quando a pessoa manda.
import { api } from './api.js';
import { estado, avisar } from './estado.js';
import { el, janela, aviso } from './ui.js';
import { markdownSeguro } from './markdown.js';
import { t } from './i18n.js';

let ultima = null;

export async function checarAtualizacao({ forcar = false, silencioso = false } = {}) {
  try {
    ultima = await api(`/atualizacao${forcar ? '?forcar=1' : ''}`);
    if (estado.info) estado.info.atualizacao = { nova: ultima.nova, ultima: ultima.ultima };
    avisar('atualizacao', ultima);
    if (!silencioso) {
      if (ultima.erro) aviso(ultima.erro, 'erro');
      else if (!ultima.nova) aviso(t('Você já está na versão mais nova ({versao}).', { versao: ultima.atual }));
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
  const notas = markdownSeguro(info.notas || t('Sem notas desta versão.'));
  notas.classList.add('resposta');
  notas.style.cssText = 'max-height:300px;overflow:auto;font-size:15px';
  janela({
    titulo: t('Versão {versao} disponível', { versao: info.ultima }), larga: true,
    corpo: el('div', { style: 'display:grid;gap:12px' },
      el('p', { class: 'ajuda', style: 'margin:0', texto: t('Você está na {atual}. A atualização baixa a versão nova do GitHub, guarda a atual (para voltar se algo der errado) e reinicia o Clave. Suas conversas e configurações não são tocadas.', { atual: info.atual }) }),
      el('div', { class: 'rotulo', texto: t('O que mudou') }), notas),
    botoes: [
      { texto: t('Agora não') },
      { texto: t('Atualizar e reiniciar'), classe: 'primario', acao: async () => {
        await api('/atualizacao/aplicar', { metodo: 'POST' });
        esperarVoltar(info.ultima);
      } },
    ],
  });
}

function esperarVoltar(versao) {
  document.getElementById('principal').replaceChildren(el('div', { class: 'vazio' },
    el('h2', { texto: t('Atualizando…') }), el('p', { texto: t('Instalando a versão {versao}. O Clave volta sozinho em alguns segundos.', { versao }) })));
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
        el('h2', { texto: t('A atualização está demorando') }), el('p', { texto: t('Feche o Clave e abra de novo. Se a versão nova não subir, o Clave volta sozinho para a anterior.') })));
      return;
    }
    setTimeout(tentar, 1500);
  };
  setTimeout(tentar, 2500);
}
