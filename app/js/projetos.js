// Projetos: instruções e arquivos fixos que entram em todas as conversas do projeto.
import { api, enviarArquivo } from './api.js';
import { avisar } from './estado.js';
import { ic } from './icones.js';
import { el, janela, aviso, confirmar, escolherArquivos, dataBr } from './ui.js';
import { cartaoAnexo } from './compositor.js';
import { escolherDoGitHub } from './github.js';
import { estado } from './estado.js';
import { t } from './i18n.js';

export async function telaProjetos(principal) {
  const { projetos } = await api('/projetos');
  const novo = el('button', { class: 'botao primario', type: 'button', html: `${ic('mais')}${t('Novo projeto')}`, onclick: () => editarProjeto() });
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: t('Projetos') }),
        el('p', { texto: t('Um projeto guarda instruções e arquivos que o Claude lê em todas as conversas dele. Bom para um trabalho que se repete: o TCC, a loja, o canal, o livro.') })),
      novo),
    projetos.length
      ? el('div', { class: 'grade-cartoes' }, ...projetos.map((p) => el('a', { class: 'cartao', href: `#/projetos/${p.id}` },
        el('h3', { texto: p.nome }), el('p', { texto: p.descricao || t('Sem descrição') }),
        el('span', { class: 'meta', texto: t('{n} conversa(s) · {data}', { n: p.conversas, data: dataBr(new Date(p.atualizado_em * 1000).toISOString()) }) }))))
      : el('div', { class: 'vazio' }, el('p', { texto: t('Nenhum projeto ainda.') }), el('a', { href: '#/aprender/projetos', texto: t('Para que serve um projeto?') })))));
  return {};
}

export async function telaProjeto(principal, id) {
  const desenhar = async () => {
    const { projeto, conversas } = await api(`/projetos/${id}`);
    const enviar = async (lista) => {
      for (const f of lista || []) {
        try { await enviarArquivo(f, `/projetos/${id}/arquivos`); } catch (e) { aviso(`${f.name}: ${e.message}`, 'erro'); }
      }
      desenhar();
    };
    principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
      el('a', { class: 'botao pequeno fantasma', href: '#/projetos', html: `${ic('esq')}${t('Projetos')}` }),
      el('div', { class: 'pagina-cab' },
        el('div', {}, el('h1', { texto: projeto.nome }), projeto.descricao ? el('p', { texto: projeto.descricao }) : null),
        el('button', { class: 'botao', type: 'button', html: `${ic('lapis')}${t('Editar')}`, onclick: () => editarProjeto(projeto, desenhar) }),
        el('a', { class: 'botao primario', href: `#/novo/projeto/${id}`, html: `${ic('mais')}${t('Nova conversa no projeto')}` })),
      el('div', { class: 'secao-titulo', texto: t('Instruções') }),
      el('div', { class: 'uso-painel', style: 'white-space:pre-wrap', texto: projeto.instrucoes || t('Nenhuma instrução. Clique em Editar para dizer ao Claude como trabalhar neste projeto.') }),
      el('div', { class: 'secao-titulo', texto: t('Arquivos de conhecimento ({n})', { n: projeto.arquivos.length }) }),
      el('p', { class: 'ajuda', texto: t('Estes arquivos entram no começo de cada conversa nova do projeto. Conversas que já existem continuam com os arquivos de quando começaram.') }),
      el('div', { style: 'display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px' }, ...projeto.arquivos.map((a) => cartaoAnexo(a, async () => {
        if (await confirmar(t('Tirar "{nome}" do projeto?', { nome: a.nome }), { titulo: t('Tirar arquivo'), sim: t('Tirar') })) {
          await api(`/projetos/${id}/arquivos/${a.id}`, { metodo: 'DELETE' }); desenhar();
        }
      }))),
      el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap' },
        el('button', { class: 'botao', type: 'button', html: `${ic('subir')}${t('Adicionar arquivos')}`, onclick: async () => enviar(await escolherArquivos()) }),
        estado.info?.github?.origem ? el('button', { class: 'botao', type: 'button', html: `${ic('ramo')}${t('Do GitHub')}`, onclick: async () => { await escolherDoGitHub({ projetoId: id }); desenhar(); } }) : null),
      el('div', { class: 'secao-titulo', texto: t('Conversas') }),
      conversas.length ? el('div', { class: 'lista-itens' }, ...conversas.map((c) => el('a', { class: 'item-lista', href: `#/c/${c.id}`, style: 'text-decoration:none;color:inherit' },
        el('span', { html: ic('chat') }), el('span', { class: 'textos' }, el('b', { texto: c.titulo || t('Nova conversa') }),
          el('small', { texto: dataBr(new Date(c.atualizada_em * 1000).toISOString()) })))))
        : el('p', { class: 'ajuda', texto: t('Nenhuma conversa ainda.') }),
      el('div', { class: 'secao-titulo', texto: t('Zona de perigo') }),
      el('button', { class: 'botao perigo', type: 'button', html: `${ic('lixo')}${t('Apagar projeto')}`, onclick: async () => {
        if (!await confirmar(t('Apagar o projeto e os arquivos dele? As conversas continuam existindo, só saem do projeto.'), { titulo: t('Apagar projeto'), sim: t('Apagar'), perigo: true })) return;
        await api(`/projetos/${id}`, { metodo: 'DELETE' }); avisar('conversas-mudaram'); location.hash = '#/projetos';
      } }))));
  };
  await desenhar();
  return {};
}

function editarProjeto(projeto = null, depois) {
  const nome = el('input', { class: 'entrada', value: projeto?.nome || '', placeholder: t('Ex.: TCC de Psicologia') });
  const descricao = el('input', { class: 'entrada', value: projeto?.descricao || '', placeholder: t('Uma linha sobre o projeto (opcional)') });
  const instrucoes = el('textarea', { class: 'area', style: 'min-height:200px', placeholder: t('Ex.: Meu TCC é sobre ansiedade em universitários. Use normas da ABNT. Seja crítico com os meus argumentos e aponte fontes fracas.') });
  instrucoes.value = projeto?.instrucoes || '';
  janela({
    titulo: projeto ? t('Editar projeto') : t('Novo projeto'), larga: true,
    corpo: el('div', { style: 'display:grid;gap:14px' },
      el('label', { class: 'campo' }, el('span', { texto: t('Nome') }), nome),
      el('label', { class: 'campo' }, el('span', { texto: t('Descrição') }), descricao),
      el('label', { class: 'campo' }, el('span', { texto: t('Instruções para o Claude') }), instrucoes,
        el('small', { texto: t('Escreva como se fosse explicar o trabalho a um assistente novo: o contexto, o que você quer e o que evitar.') }))),
    botoes: [
      { texto: t('Cancelar') },
      { texto: projeto ? t('Salvar') : t('Criar'), classe: 'primario', acao: async () => {
        if (!nome.value.trim()) { aviso(t('Dê um nome.'), 'erro'); return false; }
        const corpo = { nome: nome.value.trim(), descricao: descricao.value.trim(), instrucoes: instrucoes.value };
        if (projeto) { await api(`/projetos/${projeto.id}`, { metodo: 'PATCH', corpo }); depois?.(); }
        else { const r = await api('/projetos', { metodo: 'POST', corpo }); location.hash = `#/projetos/${r.projeto.id}`; }
      } },
    ],
  });
}
