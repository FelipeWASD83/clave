// Como cada pedaço de uma resposta aparece: texto, raciocínio, ferramentas, busca na web, avisos.
import { ic } from './icones.js';
import { el, esc } from './ui.js';
import { renderizar } from './markdown.js';
import { t } from './i18n.js';
import { widgetPorId, iconeDaFerramenta } from './widgets.js';

// cada entrada é uma função, então o t() roda na hora de desenhar (o catálogo já carregou)
const NOMES_FERRAMENTA = {
  listar_pasta: (e) => ['pasta', t('Olhou a pasta'), e.caminho || '.'],
  ler_arquivo: (e) => ['arquivo', t('Leu'), e.caminho],
  buscar_texto: (e) => ['busca', t('Procurou'), `"${e.padrao || ''}"`],
  achar_arquivos: (e) => ['busca', t('Procurou arquivos'), e.padrao],
  escrever_arquivo: (e) => ['lapis', t('Escreveu'), e.caminho],
  editar_arquivo: (e) => ['lapis', t('Editou'), e.caminho],
  rodar_comando: (e) => ['terminal', e.descricao || t('Rodou um comando'), e.em_segundo_plano ? `${e.comando} ${t('(em segundo plano)')}` : e.comando],
  ver_comando: (e) => ['terminal', t('Olhou um comando em segundo plano'), e.id],
  parar_comando: (e) => ['parar', t('Parou um comando em segundo plano'), e.id],
  atualizar_tarefas: () => ['feito', t('Atualizou a lista de passos'), ''],
  usar_skill: (e) => ['faisca', t('Usou a skill'), e.nome],
  mostrar_arquivo: (e) => ['imagem', t('Mostrou'), e.caminho],
  word_ler: (e) => ['arquivo', t('Leu o documento'), e.caminho],
  word_criar: (e) => ['lapis', t('Criou o documento'), e.caminho],
  word_alterar: (e) => ['lapis', t('Mexeu no documento'), e.caminho],
  word_no_app: (e) => ['arquivo', t('Exportou o documento para PDF'), e.caminho],
  email_ler: (e) => ['chat', e.id ? t('Leu um e-mail') : t('Olhou a caixa de entrada'), e.buscar || e.remetente || ''],
  email_enviar: (e) => ['enviar', t('Enviou um e-mail para'), e.para],
  email_salvar_anexo: (e) => ['baixar', t('Salvou o anexo'), e.anexo],
  memory: (e) => ['memoria', { view: t('Consultou a memória'), create: t('Anotou na memória'), str_replace: t('Atualizou a memória'), insert: t('Atualizou a memória'), delete: t('Apagou da memória'), rename: t('Reorganizou a memória') }[e.command] || t('Memória'), e.path || e.old_path || ''],
  excel_ler: (e) => ['grafico', t('Leu a planilha'), e.caminho + (e.aba ? ` (${e.aba})` : '')],
  excel_alterar: (e) => ['grafico', t('Mexeu na planilha'), e.caminho],
  excel_no_app: (e) => ['grafico', { recalcular: t('Recalculou no Excel'), pdf: t('Exportou para PDF'), converter_xlsx: t('Converteu para .xlsx') }[e.acao] || t('Usou o Excel'), e.caminho],
  excel_abrir: (e) => ['externo', t('Abriu no Excel'), e.caminho],
  planilha_ler: (e) => ['grafico', t('Leu a planilha'), e.aba || ''],
  planilha_criar: (e) => ['grafico', t('Criou a planilha'), e.nome_arquivo],
  planilha_pdf: () => ['arquivo', t('Exportou a planilha para PDF'), ''],
  github_meus_repositorios: () => ['ramo', t('Listou seus repositórios do GitHub'), ''],
  github_ver_pasta: (e) => ['ramo', t('Olhou no GitHub'), `${e.repo}/${e.caminho || ''}`],
  github_ler_arquivo: (e) => ['ramo', t('Leu no GitHub'), `${e.repo}/${e.caminho}`],
  github_buscar_codigo: (e) => ['ramo', t('Buscou código no GitHub'), e.consulta],
  github_listar_issues: (e) => ['ramo', e.pull_requests ? t('Listou os PRs') : t('Listou as issues'), e.repo],
  github_ler_issue: (e) => ['ramo', t('Leu a issue/PR'), `${e.repo}#${e.numero}`],
  github_commits: (e) => ['ramo', t('Viu os commits'), e.repo],
  github_criar_issue: (e) => ['ramo', t('Criar issue'), `${e.repo}: ${e.titulo}`],
  github_comentar: (e) => ['ramo', t('Comentar'), `${e.repo}#${e.numero}`],
  github_criar_pr: (e) => ['ramo', t('Abrir pull request'), `${e.repo}: ${e.titulo}`],
  executar_fluxo: (e) => ['fluxo', t('Propôs um fluxo'), e.titulo || ''],
  apresentar_plano: () => ['lista', t('Apresentou o plano'), ''],
  perguntar: () => ['chat', t('Fez uma pergunta'), ''],
  sugerir_conversa: (e) => ['mais_tarefa', t('Sugeriu outra conversa'), e.titulo || ''],
  // o ícone do tipo de widget e sem o título: o cartão logo abaixo já mostra o título
  mostrar_widget: (e) => [iconeDaFerramenta(e.tipo), t('Mostrou um widget'), ''],
  navegador_abrir: (e) => ['globo', t('Abriu no navegador'), e.url],
  navegador_ler: () => ['globo', t('Leu a página do navegador'), ''],
  navegador_print: () => ['imagem', t('Tirou um print do navegador'), ''],
  navegador_clicar: (e) => ['globo', t('Clicou na página'), e.descricao || (e.ref != null ? `[${e.ref}]` : '')],
  navegador_digitar: (e) => ['globo', t('Digitou na página'), e.ref != null ? `[${e.ref}] "${String(e.texto || '').slice(0, 60)}"` : ''],
  navegador_rolar: (e) => ['globo', t('Rolou a página'), { baixo: t('para baixo'), cima: t('para cima'), topo: t('até o topo'), fim: t('até o fim') }[e.direcao] || ''],
  navegador_voltar: () => ['globo', t('Voltou uma página no navegador'), ''],
};

// no Code, o caminho destes blocos abre o arquivo no Visualizador do painel
const ABREM_ARQUIVO = new Set(['ler_arquivo', 'escrever_arquivo', 'editar_arquivo', 'mostrar_arquivo', 'word_ler', 'word_criar', 'word_alterar', 'excel_ler', 'excel_alterar']);
function alvoDoBloco(nome, alvo, entrada) {
  if (!alvo) return null;
  const texto = String(alvo).slice(0, 200);
  const caminho = entrada?.caminho;
  if (!ABREM_ARQUIVO.has(nome) || !caminho) return el('code', { texto });
  return el('code', { class: 'caminho-clicavel', texto, title: t('Abrir no Visualizador'), role: 'link', tabindex: '0',
    onclick: (ev) => { ev.preventDefault(); ev.stopPropagation(); import('./arquivos.js').then((m) => m.abrirArquivo(caminho)); },
    onkeydown: (ev) => { if (ev.key === 'Enter') { ev.preventDefault(); ev.stopPropagation(); import('./arquivos.js').then((m) => m.abrirArquivo(caminho)); } } });
}

export function descreverFerramenta(nome, entrada = {}) {
  const f = NOMES_FERRAMENTA[nome];
  if (f) return f(entrada || {});
  return ['ferramenta', nome, ''];
}

function textoResultado(conteudo) {
  if (conteudo == null) return '';
  if (typeof conteudo === 'string') return conteudo;
  return conteudo.map((b) => b.type === 'text' ? b.text : b.type === 'image' ? t('[imagem]') : b.type === 'document' ? t('[documento]') : '').join('\n');
}

export function htmlDiff(texto) {
  return (texto || '').split('\n').map((l) => {
    const cls = l.startsWith('+++') || l.startsWith('---') || l.startsWith('@@') ? 'cab' : l.startsWith('+') ? 'add' : l.startsWith('-') ? 'del' : '';
    return cls ? `<span class="${cls}">${esc(l)}</span>` : `${esc(l)}\n`;
  }).join('');
}

function diffSimples(antes, depois) {
  const a = (antes || '').split('\n').map((l) => '-' + l);
  const d = (depois || '').split('\n').map((l) => '+' + l);
  return [...a, ...d].join('\n');
}

// ---------- texto ----------
export function blocoTexto(bloco, { final = true } = {}) {
  const div = el('div', { class: 'resposta' });
  renderizar(div, bloco.text || '', { final });
  const fontes = citacoes(bloco);
  if (fontes.length) {
    const p = div.lastElementChild || div;
    fontes.forEach((f, i) => p.append(el('a', { class: 'citacao', href: f.url, target: '_blank', rel: 'noopener noreferrer', title: f.titulo, texto: String(i + 1) })));
  }
  return div;
}

function citacoes(bloco) {
  const vistos = new Map();
  for (const c of bloco.citations || []) {
    const url = c.url || c.source;
    if (url && !vistos.has(url)) vistos.set(url, { url, titulo: c.title || url });
  }
  return [...vistos.values()];
}

// ---------- raciocínio ----------
export function blocoPensamento(texto, { aberto = false, ativo = false } = {}) {
  const corpo = el('div', { class: 'corpo-pensamento', texto: texto || '' });
  const det = el('details', { class: `pensamento ${ativo ? 'pensando' : ''}`, open: aberto },
    el('summary', {}, el('span', { html: ic('dir', 'class="seta"') }), el('span', { class: 'rotulo-pensando', texto: ativo ? t('Pensando…') : t('Raciocínio') })),
    corpo);
  det._corpo = corpo;
  det.finalizar = () => { det.classList.remove('pensando'); det.querySelector('.rotulo-pensando').textContent = t('Raciocínio'); };
  return det;
}

// ---------- ferramentas ----------
export function blocoFerramenta(bloco) {
  const [icone, verbo, alvo] = descreverFerramenta(bloco.name, bloco.input);
  const desc = el('span', { class: 'desc' }, verbo + (alvo ? ' ' : ''), alvoDoBloco(bloco.name, alvo, bloco.input));
  const detalhe = el('div', { class: 'detalhe' });
  const det = el('details', { class: 'ferramenta', dados: { toolId: bloco.id || '', nome: bloco.name || '' } },
    el('summary', {}, el('span', { class: 'ic', html: ic(icone) }), desc, el('span', { class: 'meta estado-ferramenta' })),
    detalhe);
  det._detalhe = detalhe;
  // o arquivo que o Claude mostrou fica fora do bloco recolhido, sempre à vista
  if (bloco.name === 'mostrar_arquivo') det.companheiro = el('div', { class: 'arquivo-mostrado-vaga' });
  // o widget também fica fora do bloco recolhido (o id deixa a tela guardar o mapa vivo ao redesenhar a conversa)
  if (bloco.name === 'mostrar_widget') det.companheiro = el('div', { class: 'widget-vaga', dados: { widget: bloco.id || '' } });
  det.definirEntrada = (entrada) => {
    bloco.input = entrada || bloco.input;
    detalhe.querySelector('.bloco-entrada')?.remove();
    const pre = entradaLegivel(bloco.name, entrada || {});
    if (pre) detalhe.prepend(el('div', { class: 'bloco-entrada' }, el('div', { class: 'rotulo-detalhe', texto: t('O que ele pediu') }), pre));
    const [icone, v, a] = descreverFerramenta(bloco.name, entrada);
    desc.replaceChildren(v + (a ? ' ' : ''), alvoDoBloco(bloco.name, a, bloco.input) || '');
    // ao vivo o bloco nasce sem entrada: o ícone que depende dela (o tipo do widget, por exemplo) acerta aqui
    const icEl = det.querySelector(':scope > summary > .ic');
    if (icEl && icone) icEl.innerHTML = ic(icone);
  };
  det.definirResultado = (texto, erro = false) => {
    detalhe.querySelector('.bloco-resultado')?.remove();
    det.classList.toggle('erro', !!erro);
    det.classList.remove('rodando');
    if (texto) detalhe.append(el('div', { class: 'bloco-resultado' }, el('div', { class: 'rotulo-detalhe', texto: erro ? t('Erro') : t('Resultado') }), el('pre', { texto: String(texto).slice(0, 6000) })));
    det.querySelector('.arquivo-gerado')?.remove();
    if (det.companheiro && bloco.name === 'mostrar_arquivo') {
      const m = !erro && /\(id ([0-9a-f]{16})\)/.exec(String(texto || ''));
      det.companheiro.replaceChildren(m ? previaArquivo(m[1], String(bloco.input?.caminho || '').split(/[\\/]/).pop() || 'arquivo', bloco.input?.legenda) : '');
    }
    // ao vivo o widget já chegou pelo evento "widget"; reabrindo a conversa, ele vem do servidor
    if (det.companheiro && bloco.name === 'mostrar_widget' && !erro && bloco.id && !det.companheiro.firstChild) det.companheiro.replaceChildren(widgetPorId(bloco.id));
    const gerado = !erro && /^planilha_(criar|pdf)$/.test(bloco.name) && /:\s*([^\n]+?)\s*\(id ([0-9a-f]{16})\)/.exec(String(texto || ''));
    if (gerado) det.append(cartaoGerado(gerado[2], gerado[1]));
  };
  det.definirDiff = (diff) => {
    detalhe.querySelector('.bloco-diff')?.remove();
    if (diff) detalhe.append(el('div', { class: 'bloco-diff' }, el('div', { class: 'rotulo-detalhe', texto: t('Mudanças') }), el('pre', { class: 'diff', html: htmlDiff(diff) })));
  };
  if (bloco.input && Object.keys(bloco.input).length) det.definirEntrada(bloco.input);
  return det;
}

// Arquivo que o Claude mostrou com mostrar_arquivo: imagem, vídeo e áudio na própria conversa; o resto num cartão.
const IMAGENS = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg']);
const VIDEOS = new Set(['mp4', 'webm', 'mov', 'm4v']);
const AUDIOS = new Set(['mp3', 'wav', 'ogg', 'm4a', 'flac']);
async function abrirNoPrograma(id) {
  const r = await fetch(`/api/anexos/${id}/abrir`, { method: 'POST', credentials: 'same-origin' });
  if (!r.ok) { const d = await r.json().catch(() => ({})); alert(d.erro || t('Não deu para abrir.')); }
}
export function previaArquivo(id, nome, legenda) {
  const ext = (nome.split('.').pop() || '').toLowerCase();
  const url = `/api/anexos/${id}`;
  let midia = null;
  if (IMAGENS.has(ext) && ext !== 'svg') {
    midia = el('button', { class: 'arquivo-imagem', type: 'button', title: t('Abrir no programa de imagens'), onclick: () => abrirNoPrograma(id) },
      el('img', { src: url, alt: legenda || nome, loading: 'lazy' }));
  } else if (VIDEOS.has(ext)) midia = el('video', { src: url, controls: true, preload: 'metadata' });
  else if (AUDIOS.has(ext)) midia = el('audio', { src: url, controls: true, preload: 'metadata' });
  const barra = el('div', { class: 'arquivo-mostrado-barra' },
    el('span', { class: 'icone-arq', texto: ext.slice(0, 4) }),
    el('span', { class: 'arquivo-mostrado-nome' }, el('b', { texto: nome }), legenda ? el('small', { texto: legenda }) : null),
    el('a', { class: 'botao pequeno', href: `${url}?baixar=1`, download: nome, html: `${ic('baixar')}${esc(t('Baixar'))}` }),
    el('button', { class: 'botao pequeno', type: 'button', html: `${ic('externo')}${esc(t('Abrir'))}`, title: t('Abre uma cópia no programa do computador'), onclick: () => abrirNoPrograma(id) }));
  return el('figure', { class: `arquivo-mostrado ${midia ? 'com-midia' : ''}` }, midia, barra);
}

// Planilha ou PDF que o Claude gerou: baixar ou abrir no programa do computador.
export function cartaoGerado(id, nome) {
  const ext = (nome.split('.').pop() || '').slice(0, 4);
  return el('div', { class: 'arquivo-gerado' },
    el('span', { class: 'icone-arq', texto: ext }), el('b', { texto: nome }),
    el('a', { class: 'botao pequeno primario', href: `/api/anexos/${id}?baixar=1`, download: nome, html: `${ic('baixar')}${esc(t('Baixar'))}` }),
    el('button', { class: 'botao pequeno', type: 'button', html: `${ic('externo')}${esc(t('Abrir'))}`, title: t('Abre uma cópia no Excel (ou no programa padrão)'),
      onclick: async () => {
        const r = await fetch(`/api/anexos/${id}/abrir`, { method: 'POST', credentials: 'same-origin' });
        if (!r.ok) { const d = await r.json().catch(() => ({})); alert(d.erro || t('Não deu para abrir.')); }
      } }));
}

function entradaLegivel(nome, e) {
  if (nome === 'rodar_comando') return el('pre', { texto: e.comando || '' });
  if (nome === 'editar_arquivo') return el('pre', { class: 'diff', html: htmlDiff(diffSimples(e.trecho_atual, e.trecho_novo)) });
  if (nome === 'escrever_arquivo') return el('pre', { texto: (e.conteudo || '').split('\n').slice(0, 80).join('\n') + ((e.conteudo || '').split('\n').length > 80 ? '\n…' : '') });
  if (nome === 'atualizar_tarefas') return null;
  if (nome === 'excel_alterar' || nome === 'planilha_criar') {
    const ops = (e.operacoes || []).map((o) => `• ${o.acao}${o.aba ? ` [${o.aba}]` : ''}${o.intervalo ? ` ${o.intervalo}` : o.inicio ? ` ${o.inicio}` : ''}`).join('\n');
    return el('pre', { texto: `${e.caminho || e.nome_arquivo || ''}\n${ops}` });
  }
  return el('pre', { texto: JSON.stringify(e, null, 2) });
}

// busca e leitura na web (ferramentas que rodam nos servidores da Anthropic)
export function blocoServidor(bloco) {
  const e = bloco.input || {};
  let icone = 'globo', texto = bloco.name, alvo = '';
  if (bloco.name === 'web_search') { texto = t('Pesquisou na web'); alvo = e.query || ''; }
  else if (bloco.name === 'web_fetch') { texto = t('Leu a página'); alvo = e.url || ''; }
  else if (bloco.type === 'mcp_tool_use') { icone = 'conector'; texto = t('Conector {nome}', { nome: bloco.server_name || '' }); alvo = bloco.name; }
  const det = el('details', { class: 'ferramenta', dados: { toolId: bloco.id || '' } },
    el('summary', {}, el('span', { class: 'ic', html: ic(icone) }), el('span', { class: 'desc' }, texto + ' ', alvo ? el('code', { texto: alvo }) : null)),
    el('div', { class: 'detalhe' }));
  det._detalhe = det.querySelector('.detalhe');
  return det;
}

export function preencherResultadoServidor(det, bloco) {
  const alvo = det?._detalhe;
  if (!alvo) return;
  const c = bloco.content;
  if (bloco.type === 'web_search_tool_result') {
    if (Array.isArray(c)) {
      alvo.replaceChildren(el('div', { class: 'fontes' }, ...c.filter((r) => r.url).slice(0, 12).map((r) =>
        el('a', { class: 'fonte', href: r.url, target: '_blank', rel: 'noopener noreferrer', title: r.title || r.url }, el('span', { html: ic('externo') }), el('span', { texto: r.title || r.url })))));
      det.open = false;
    } else alvo.replaceChildren(el('pre', { texto: t('A busca falhou: {codigo}', { codigo: c?.error_code || t('erro') }) }));
  } else if (bloco.type === 'web_fetch_tool_result') {
    const titulo = c?.content?.title || c?.url || '';
    alvo.replaceChildren(el('pre', { texto: c?.error_code ? t('Não deu para ler: {codigo}', { codigo: c.error_code }) : t('Página lida: {titulo}', { titulo }) }));
  } else if (bloco.type === 'mcp_tool_result') {
    alvo.replaceChildren(el('pre', { texto: textoResultado(c).slice(0, 6000) }));
    if (bloco.is_error) det.classList.add('erro');
  }
}

// ---------- avisos dentro da conversa ----------
export function nota(texto, tipo = '', botao) {
  const icone = tipo === 'erro' ? 'alerta' : tipo === 'info' ? 'info' : 'alerta';
  return el('div', { class: `nota-conversa ${tipo}` }, el('span', { html: ic(icone) }), el('span', { texto }), botao || null);
}

export function divisorCompactacao(bloco) {
  const resumo = String(bloco?.content || '').trim();
  if (!resumo) return el('div', { class: 'compactacao', texto: t('A conversa foi resumida aqui para caber na memória do modelo') });
  return el('details', { class: 'compactacao com-resumo' },
    el('summary', { texto: t('Conversa compactada aqui: daqui para frente o Claude parte deste resumo') }),
    el('div', { class: 'compactacao-resumo', texto: resumo }));
}

// ---------- uma resposta inteira (histórico) ----------
// mensagens: as mensagens do Claude e os resultados de ferramenta daquele turno, em ordem.
export function renderizarTurno(alvo, mensagens) {
  const resultados = new Map();
  for (const m of mensagens) {
    if (m.papel === 'user' && Array.isArray(m.conteudo)) {
      for (const b of m.conteudo) if (b.type === 'tool_result') resultados.set(b.tool_use_id, b);
    }
  }
  const porId = new Map();
  for (const m of mensagens) {
    if (m.papel !== 'assistant' || !Array.isArray(m.conteudo)) continue;
    for (const b of m.conteudo) {
      const no = renderizarBloco(b, porId, resultados);
      if (no) alvo.append(no);
    }
  }
}

export function renderizarBloco(b, porId, resultados) {
  switch (b.type) {
    case 'text':
      return (b.text || '').trim() ? blocoTexto(b) : null;
    case 'thinking':
      return (b.thinking || '').trim() ? blocoPensamento(b.thinking) : null;
    case 'tool_use': {
      if (b.name === 'atualizar_tarefas') return null;
      if (b.name === 'sugerir_conversa' && b.input?.titulo) {
        const caixa = el('div', { class: 'cartao-carregando', dados: { toolId: b.id } });
        import('./fluxo-ui.js').then((m) => caixa.replaceWith(m.cartaoSugestao({ id: b.id, ...b.input })));
        return caixa;
      }
      if (b.name === 'executar_fluxo' || b.name === 'apresentar_plano' || b.name === 'perguntar') {
        // o cartão do fluxo (do plano ou das perguntas) no lugar do bloco de ferramenta; carregado sob demanda
        const r = resultados?.get(b.id);
        // ainda esperando a resposta: o cartão vivo aparece sozinho (sem isso, ao reabrir a conversa, eram dois)
        if ((b.name === 'perguntar' || b.name === 'apresentar_plano') && !r) return null;
        const caixa = el('div', { class: 'cartao-carregando', dados: { toolId: b.id } });
        const texto = r ? textoResultado(r.content) : '';
        import('./fluxo-ui.js').then((m) => {
          caixa.replaceWith(b.name === 'executar_fluxo' ? m.cartaoFluxoSalvo(b.id)
            : b.name === 'perguntar' ? m.cartaoPerguntaSalva(b.input, texto)
              : m.cartaoPlanoSalvo(b.input, texto));
        });
        return caixa;
      }
      const det = blocoFerramenta(b);
      const r = resultados?.get(b.id);
      if (r) det.definirResultado(textoResultado(r.content), r.is_error);
      porId.set(b.id, det);
      if (det.companheiro) { const f = document.createDocumentFragment(); f.append(det, det.companheiro); return f; }
      return det;
    }
    case 'server_tool_use':
    case 'mcp_tool_use': {
      const det = blocoServidor(b);
      porId.set(b.id, det);
      return det;
    }
    case 'web_search_tool_result':
    case 'web_fetch_tool_result':
    case 'mcp_tool_result': {
      const det = porId.get(b.tool_use_id);
      if (det) preencherResultadoServidor(det, b);
      return null;
    }
    case 'compaction':
      return divisorCompactacao(b);
    default:
      return null;
  }
}
