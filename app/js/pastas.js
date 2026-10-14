// Escolher a pasta do modo Code (janela nativa no app; navegador de pastas no modo navegador)
// e criar uma pasta nova a partir do modelo que vem com o Clave.
import { api } from './api.js';
import { cfg } from './estado.js';
import { ic } from './icones.js';
import { el, janela, aviso } from './ui.js';

export async function escolherPasta({ titulo = 'Escolher pasta' } = {}) {
  if (window.clave?.escolherPasta) return window.clave.escolherPasta(titulo);
  return navegarPastas(titulo);
}

function navegarPastas(titulo) {
  return new Promise((ok) => {
    let atual = '';
    let escolhido = null;
    const caminhoEl = el('span', { texto: '' });
    const listaEl = el('ul');
    const atalhosEl = el('div', { class: 'atalhos-pastas' });
    async function ir(caminho) {
      try {
        const r = await api(`/pastas?caminho=${encodeURIComponent(caminho || '')}`);
        atual = r.caminho;
        caminhoEl.textContent = r.caminho || 'Discos';
        const itens = [];
        if (r.pai) itens.push(el('li', {}, el('button', { type: 'button', onclick: () => ir(r.pai) }, el('span', { html: ic('esq') }), 'Voltar')));
        for (const p of r.pastas) itens.push(el('li', {}, el('button', { type: 'button', ondblclick: () => ir(p.caminho), onclick: () => ir(p.caminho) }, el('span', { html: ic('pasta') }), p.nome)));
        if (!r.pastas.length) itens.push(el('li', { class: 'ajuda', style: 'padding:8px', texto: 'Nenhuma subpasta aqui.' }));
        listaEl.replaceChildren(...itens);
        if (r.atalhos && !atalhosEl.children.length) {
          atalhosEl.replaceChildren(...r.atalhos.map((a) => el('button', { class: 'botao pequeno', type: 'button', texto: a.nome, onclick: () => ir(a.caminho) })));
        }
      } catch (e) { aviso(e.message, 'erro'); }
    }
    janela({
      titulo, larga: true,
      corpo: el('div', { style: 'display:grid;gap:10px' },
        atalhosEl,
        el('div', { class: 'navegador-pastas' }, el('div', { class: 'caminho-atual' }, el('span', { html: ic('pasta') }), caminhoEl), listaEl),
        el('small', { class: 'ajuda', texto: 'Entre na pasta que você quer usar e clique em "Usar esta pasta".' })),
      botoes: [
        { texto: 'Cancelar' },
        { texto: 'Usar esta pasta', classe: 'primario', acao: () => { if (!atual) { aviso('Entre numa pasta primeiro.', 'erro'); return false; } escolhido = atual; } },
      ],
      aoFechar: () => ok(escolhido),
    });
    ir((cfg().pastas_recentes || [])[0] || '');
  });
}

// Pasta nova com o modelo: CLAUDE.md (regras), skills, referências visuais e guias.
export function criarPastaComModelo() {
  return new Promise((ok) => {
    let destino = '';
    let criada = null;
    const destinoEl = el('code', { texto: 'nenhuma ainda' });
    const nome = el('input', { class: 'entrada', value: 'meus-projetos-com-claude' });
    const campo = (rotulo, input, ajuda) => el('label', { class: 'campo' }, el('span', { texto: rotulo }), input, ajuda ? el('small', { texto: ajuda }) : null);
    const r = {
      nome: el('input', { class: 'entrada', value: cfg().nome || '', placeholder: 'Como o Claude deve te chamar' }),
      ocupacao: el('input', { class: 'entrada', placeholder: 'Ex.: estudante de direito, tenho uma loja, faço vídeos' }),
      experiencia: el('select', { class: 'selecao' },
        el('option', { value: 'nenhuma', texto: 'Não sei programar' }),
        el('option', { value: 'pouca', texto: 'Sei um pouco' }),
        el('option', { value: 'programo', texto: 'Sei programar' })),
      linguagens: el('input', { class: 'entrada', placeholder: 'Ex.: Excel, Python, Photoshop (opcional)' }),
      sistema: el('input', { class: 'entrada', value: navigator.userAgent.includes('Windows') ? 'Windows' : '', placeholder: 'Ex.: Windows 11, notebook com 8 GB de RAM' }),
      preferencias: el('textarea', { class: 'area', placeholder: 'Ex.: respostas curtas, sem termos difíceis; sempre me diga como testar' }),
    };
    janela({
      titulo: 'Criar pasta com o modelo', larga: true,
      corpo: el('div', { style: 'display:grid;gap:14px' },
        el('p', { class: 'ajuda', style: 'margin:0;font-size:14px', texto: 'O modelo é uma pasta já preparada para trabalhar com o Claude: um arquivo de regras (CLAUDE.md) que ele lê sozinho, procedimentos prontos (skills, como revisar código e ver vídeos), uma biblioteca de referências visuais para sites bonitos e guias. Suas respostas abaixo entram no CLAUDE.md, e você pode mudar depois.' }),
        el('div', { class: 'campo' }, el('span', { texto: 'Onde criar' }),
          el('div', { style: 'display:flex;gap:8px;align-items:center;flex-wrap:wrap' },
            el('button', { class: 'botao pequeno', type: 'button', html: `${ic('pasta')}Escolher lugar`, onclick: async () => { const p = await escolherPasta({ titulo: 'Onde criar a pasta nova' }); if (p) { destino = p; destinoEl.textContent = p; } } }),
            destinoEl)),
        campo('Nome da pasta nova', nome, 'Sem espaços é melhor (use hífen).'),
        el('div', { class: 'linha-campos' }, campo('Seu nome', r.nome), campo('O que você faz', r.ocupacao)),
        el('div', { class: 'linha-campos' }, campo('Programação', r.experiencia), campo('Programas e linguagens que usa', r.linguagens)),
        campo('Seu computador', r.sistema),
        campo('Como prefere as respostas', r.preferencias)),
      botoes: [
        { texto: 'Cancelar' },
        { texto: 'Criar pasta', classe: 'primario', acao: async () => {
          if (!destino) { aviso('Escolha onde criar.', 'erro'); return false; }
          const respostas = Object.fromEntries(Object.entries(r).map(([k, v]) => [k, v.value.trim()]));
          const res = await api('/modelo-de-pasta', { metodo: 'POST', corpo: { destino, nome: nome.value.trim(), respostas, git: true } });
          criada = res.caminho;
          aviso('Pasta criada. O Claude já vai ler as regras dela.');
        } },
      ],
      aoFechar: () => ok(criada),
    });
  });
}
