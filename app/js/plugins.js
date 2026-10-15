// Plugins: pacotes de skills, agentes, comandos e fluxos, no formato dos plugins do Claude Code.
import { api } from './api.js';
import { cfg, salvarConfig, nomeComando } from './estado.js';
import { ic } from './icones.js';
import { el, janela, aviso, confirmar, chaveLiga } from './ui.js';
import { escolherPasta } from './pastas.js';
import { t } from './i18n.js';

function conteudo(p) {
  const partes = [];
  if (p.skills?.length) partes.push(t('{n} skill(s)', { n: p.skills.length }));
  if (p.agentes?.length) partes.push(t('{n} agente(s)', { n: p.agentes.length }));
  if (p.comandos?.length) partes.push(t('{n} comando(s)', { n: p.comandos.length }));
  if (p.fluxos?.length) partes.push(t('{n} fluxo(s)', { n: p.fluxos.length }));
  return partes.join(' · ') || t('vazio');
}

function detalhes(p) {
  const lista = (titulo, itens, prefixo = '') => itens?.length ? el('div', {},
    el('div', { class: 'rotulo-detalhe', texto: titulo }),
    el('ul', { class: 'lista-simples' }, ...itens.map((x) => el('li', {}, el('code', { texto: prefixo + nomeComando(x.nome) }), x.descricao ? ` ${x.descricao}` : '')))) : null;
  const nome = nomeComando(p.nome);  // em inglês: /sales:proposal (os dois nomes funcionam)
  return el('div', { class: 'plugin-detalhes' },
    lista(t('Skills (o Claude usa sozinho ou você chama com /)'), p.skills, `/${nome}:`),
    lista(t('Comandos'), p.comandos, `/${nome}:`),
    lista(t('Agentes (para as etapas dos fluxos)'), p.agentes, `${p.nome}:`),
    lista(t('Fluxos prontos'), p.fluxos),
    ...(p.avisos || []).map((a) => el('p', { class: 'nota-plugin' }, el('span', { html: ic('alerta') }), el('span', { texto: a }))),
    ...(p.mcp_remotos || []).map((m) => el('div', { class: 'nota-plugin info' },
      el('span', { html: ic('conector') }), el('span', { texto: t('Sugere o conector "{nome}" ({url}).', { nome: m.nome, url: m.url }) }),
      el('button', { class: 'botao pequeno', type: 'button', texto: t('Adicionar conector'), onclick: async () => {
        const lista2 = cfg().conectores_mcp || [];
        if (lista2.some((c) => c.nome === m.nome)) return aviso(t('Esse conector já está na lista.'));
        await salvarConfig({ conectores_mcp: [...lista2, { nome: m.nome, url: m.url, ligado: false }] });
        aviso(t('Conector adicionado, desligado. Ligue em Configurações > Conectores quando quiser usar.'));
      } }))));
}

export async function telaPlugins(principal) {
  const { plugins } = await api('/plugins');
  const desenhar = () => telaPlugins(principal);
  const cartao = (p) => {
    const det = el('details', {}, el('summary', { texto: t('Ver o que traz') }), detalhes(p));
    return el('div', { class: `cartao plugin ${p.ligado ? '' : 'desligado'}` },
      el('div', { class: 'cartao-cab' }, el('span', { class: 'ic', html: ic('peca') }),
        el('h3', { texto: p.titulo || p.nome }),
        el('span', { class: 'etiqueta', texto: p.origem === 'embutido' ? t('vem com o Clave') : t('instalado') })),
      el('p', { texto: p.descricao || p.erro || '' }),
      el('div', { class: 'meta', texto: [conteudo(p), p.versao ? t('versão {versao}', { versao: p.versao }) : '', p.autor ? t('por {autor}', { autor: p.autor }) : ''].filter(Boolean).join(' · ') }),
      det,
      el('div', { class: 'cartao-acoes' },
        p.erro ? el('span', { class: 'etiqueta perigo', texto: t('com erro') }) : chaveLiga({ rotulo: p.ligado ? t('Ligado') : t('Desligado'), marcado: p.ligado,
          aoMudar: async (v) => { await api(`/plugins/${encodeURIComponent(p.nome)}/ligar`, { metodo: 'POST', corpo: { ligado: v } }); desenhar(); } }),
        p.origem === 'instalado' ? el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Remover {nome}', { nome: p.titulo }), title: t('Remover'), html: ic('lixo'), onclick: async () => {
          if (!await confirmar(t('Remover o plugin "{nome}"? As skills, os agentes e os comandos dele somem do Clave.', { nome: p.titulo }), { titulo: t('Remover plugin'), sim: t('Remover'), perigo: true })) return;
          await api(`/plugins/${encodeURIComponent(p.nome)}`, { metodo: 'DELETE' }); desenhar();
        } }) : null));
  };
  const embutidos = plugins.filter((p) => p.origem === 'embutido');
  const instalados = plugins.filter((p) => p.origem !== 'embutido');
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' },
      el('div', {}, el('h1', { texto: t('Plugins') }),
        el('p', { texto: t('Um plugin junta skills, agentes, comandos e fluxos prontos para um tipo de trabalho. O formato é o mesmo dos plugins do Claude Code: dá para instalar plugins feitos para ele, e os seus funcionam lá.') })),
      el('button', { class: 'botao', type: 'button', html: `${ic('pasta')}${t('Instalar de uma pasta')}`, onclick: () => instalarDePasta(desenhar) }),
      el('button', { class: 'botao primario', type: 'button', html: `${ic('ramo')}${t('Instalar do GitHub')}`, onclick: () => instalarDoGitHub(desenhar) })),
    instalados.length ? el('div', { class: 'secao-titulo', texto: t('Instalados por você') }) : null,
    instalados.length ? el('div', { class: 'grade-cartoes' }, ...instalados.map(cartao)) : null,
    el('div', { class: 'secao-titulo', texto: t('Vêm com o Clave') }),
    el('div', { class: 'grade-cartoes' }, ...embutidos.map(cartao)),
    el('p', { class: 'ajuda', html: t('Quer fazer o seu? Na conversa, digite <code>/crie-o-seu:criar-plugin</code> e o Claude te guia.') }))));
  return {};
}

function janelaInstalar(titulo, lista, aoInstalar, avisos = []) {
  const marcados = new Set(lista.map((p) => p.nome));
  janela({
    titulo, larga: true,
    corpo: el('div', { class: 'form-grade' },
      el('div', { class: 'nota-conversa' }, el('span', { html: ic('alerta') }),
        el('span', { texto: t('Plugins trazem instruções e às vezes scripts para o Claude. Instale só de quem você confia. Os scripts continuam passando pelas suas regras de permissão (o Clave pergunta antes de rodar comandos).') })),
      ...avisos.map((a) => el('p', { class: 'ajuda', texto: a })),
      ...lista.map((p) => {
        const c = el('input', { type: 'checkbox', checked: true });
        c.addEventListener('change', () => (c.checked ? marcados.add(p.nome) : marcados.delete(p.nome)));
        return el('div', { class: 'cartao plugin' },
          el('label', { class: 'cartao-cab' }, c, el('h3', { texto: p.titulo || p.nome }), el('span', { class: 'meta', texto: conteudo(p) })),
          el('p', { texto: p.descricao || '' }), detalhes(p));
      })),
    botoes: [{ texto: t('Cancelar') }, { texto: t('Instalar'), classe: 'primario', acao: async () => {
      if (!marcados.size) { aviso(t('Escolha pelo menos um.'), 'erro'); return false; }
      await aoInstalar([...marcados]);
    } }],
  });
}

async function instalarDePasta(depois) {
  const pasta = await escolherPasta({ titulo: t('Pasta do plugin') });
  if (!pasta) return;
  try {
    const { plugin } = await api('/plugins/analisar-pasta', { metodo: 'POST', corpo: { pasta } });
    janelaInstalar(t('Instalar plugin'), [plugin], async () => {
      await api('/plugins/instalar-pasta', { metodo: 'POST', corpo: { pasta } });
      aviso(t('Plugin "{nome}" instalado.', { nome: plugin.titulo })); depois?.();
    });
  } catch (e) { aviso(e.message, 'erro'); }
}

function instalarDoGitHub(depois) {
  const repo = el('input', { class: 'entrada mono', placeholder: t('dono/repositorio  ou  https://github.com/dono/repositorio') });
  janela({
    titulo: t('Instalar do GitHub'),
    corpo: el('div', { class: 'form-grade' },
      el('label', {}, el('span', { texto: t('Repositório público com um plugin ou um marketplace do Claude Code') }), repo),
      el('small', { class: 'ajuda', texto: t('O Clave baixa o repositório, mostra o que ele traz e só instala depois do seu OK. Para uma versão específica, acrescente #versão (ex.: dono/repo#v1.2.0).') })),
    botoes: [{ texto: t('Cancelar') }, { texto: t('Procurar'), classe: 'primario', acao: async () => {
      if (!repo.value.trim()) { aviso(t('Escreva o repositório.'), 'erro'); return false; }
      const r = await api('/plugins/github', { metodo: 'POST', corpo: { repositorio: repo.value.trim() } });
      if (!r.plugins.length) { aviso(t('Esse repositório não tem plugin que o Clave consiga instalar.'), 'erro'); return false; }
      janelaInstalar(t('Plugins em {repo}', { repo: r.repositorio }), r.plugins, async (nomes) => {
        const { instalados } = await api('/plugins/github/instalar', { metodo: 'POST', corpo: { id: r.id, nomes } });
        aviso(t('{n} plugin(s) instalado(s).', { n: instalados.length })); depois?.();
      }, r.avisos);
    } }],
  });
}
