// Escolher arquivos de um repositório do GitHub para anexar na conversa.
import { api } from './api.js';
import { ic } from './icones.js';
import { el, janela, aviso } from './ui.js';
import { t } from './i18n.js';

export function escolherDoGitHub({ projetoId = null } = {}) {
  return new Promise((ok) => {
    let resultado = null;
    let repo = null, ref = null, arvore = [], pasta = '';
    const marcados = new Set();
    const lista = el('ul');
    const caminho = el('span', { texto: t('Seus repositórios') });
    const contador = el('small', { class: 'ajuda', texto: '' });

    async function mostrarRepos() {
      repo = null; pasta = ''; marcados.clear(); atualizarContador();
      caminho.textContent = t('Seus repositórios');
      lista.replaceChildren(el('li', { class: 'ajuda', style: 'padding:8px', texto: t('Carregando…') }));
      try {
        const r = await api('/github/repos');
        lista.replaceChildren(...r.repos.map((x) => el('li', {}, el('button', { type: 'button', onclick: () => abrirRepo(x.nome) },
          el('span', { html: ic('ramo') }), el('span', { texto: x.nome }), x.privado ? el('span', { class: 'etiqueta', texto: t('privado') }) : null))));
        if (!r.repos.length) lista.replaceChildren(el('li', { class: 'ajuda', style: 'padding:8px', texto: t('Nenhum repositório encontrado.') }));
      } catch (e) { lista.replaceChildren(el('li', { class: 'ajuda', style: 'padding:8px', texto: e.message })); }
    }

    async function abrirRepo(nome) {
      repo = nome;
      lista.replaceChildren(el('li', { class: 'ajuda', style: 'padding:8px', texto: t('Carregando…') }));
      try {
        const r = await api(`/github/arvore?repo=${encodeURIComponent(nome)}`);
        arvore = r.itens; ref = r.ref;
        if (r.cortada) aviso(t('Repositório grande: nem todos os arquivos aparecem.'));
        mostrarPasta('');
      } catch (e) { aviso(e.message, 'erro'); mostrarRepos(); }
    }

    function mostrarPasta(p) {
      pasta = p;
      caminho.textContent = `${repo}/${p}`;
      const prefixo = p ? p + '/' : '';
      const filhos = arvore.filter((i) => i.caminho.startsWith(prefixo) && !i.caminho.slice(prefixo.length).includes('/'));
      filhos.sort((a, b) => (a.tipo === b.tipo ? a.caminho.localeCompare(b.caminho) : a.tipo === 'pasta' ? -1 : 1));
      const itens = [el('li', {}, el('button', { type: 'button', onclick: () => (p ? mostrarPasta(p.split('/').slice(0, -1).join('/')) : mostrarRepos()) }, el('span', { html: ic('esq') }), t('Voltar')))];
      for (const i of filhos) {
        const nome = i.caminho.slice(prefixo.length);
        if (i.tipo === 'pasta') itens.push(el('li', {}, el('button', { type: 'button', onclick: () => mostrarPasta(i.caminho) }, el('span', { html: ic('pasta') }), nome)));
        else {
          const cx = el('input', { type: 'checkbox', checked: marcados.has(i.caminho) });
          cx.addEventListener('change', () => { cx.checked ? marcados.add(i.caminho) : marcados.delete(i.caminho); atualizarContador(); });
          itens.push(el('li', {}, el('label', { style: 'display:flex;gap:8px;align-items:center;padding:6px 8px;cursor:pointer' }, cx, el('span', { html: ic('arquivo') }), nome,
            el('span', { class: 'meta', style: 'margin-left:auto', texto: `${Math.ceil((i.tamanho || 0) / 1024)} KB` }))));
        }
      }
      lista.replaceChildren(...itens);
    }

    function atualizarContador() { contador.textContent = marcados.size ? t('{n} arquivo(s) marcado(s)', { n: marcados.size }) : t('Marque os arquivos que o Claude deve ler.'); }

    janela({
      titulo: t('Anexar do GitHub'), larga: true,
      corpo: el('div', { style: 'display:grid;gap:10px' },
        el('div', { class: 'navegador-pastas' }, el('div', { class: 'caminho-atual' }, el('span', { html: ic('ramo') }), caminho), lista),
        contador),
      botoes: [
        { texto: t('Cancelar') },
        { texto: t('Anexar'), classe: 'primario', acao: async () => {
          if (!marcados.size) { aviso(t('Marque pelo menos um arquivo.'), 'erro'); return false; }
          const r = await api('/github/anexar', { metodo: 'POST', corpo: { repo, ref, caminhos: [...marcados], projeto_id: projetoId } });
          if (r.erros?.length) aviso(t('Alguns arquivos não vieram: {erros}', { erros: r.erros.slice(0, 3).join('; ') }), 'erro');
          resultado = r.anexos;
        } },
      ],
      aoFechar: () => ok(resultado),
    });
    atualizarContador();
    mostrarRepos();
  });
}
