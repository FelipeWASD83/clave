// As abas Arquivos e Visualizador do painel lateral (modo Code).
//   - Arquivos: a árvore da pasta do trabalho, com filtro, busca em todas as pastas, teclado, menu do botão direito,
//     arrastar para a caixa de texto e atualização sozinha quando algo muda no disco.
//   - Visualizador: abre os arquivos em guias pequenas (até 8): código com cores e números de linha, Markdown,
//     imagens, PDF, áudio, vídeo, planilhas, Word, JSON e as mudanças que o Claude fez nesta conversa.
// O servidor (servidor/explorador.py, rotas /api/arquivos/...) não deixa nada sair da pasta do trabalho.
import { api } from './api.js';
import { ic } from './icones.js';
import { el, esc, aviso, confirmar, perguntarTexto, menu, copiarTexto, dataHora, numero } from './ui.js';
import { colorirCodigo, renderizar } from './markdown.js';
import { htmlDiff } from './blocos.js';
import { registrarAba, abrirPainel, contextoAtual, fileiraDeGuias } from './painel.js';
import { t, localidade } from './i18n.js';

// ---------- ícones próprios (mesmo traço de 24x24 dos outros) ----------
const ICONES = {
  trava: '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
  'pasta-aberta': '<path d="M4 19V7.5A2.5 2.5 0 0 1 6.5 5H9l2 2h6.5A2.5 2.5 0 0 1 20 9.5V11"/><path d="M4 19l2.2-6.3A2.5 2.5 0 0 1 8.6 11H21l-2.3 6.4a2.5 2.5 0 0 1-2.4 1.6z"/>',
  codigo: '<path d="M8.5 8 4.5 12l4 4M15.5 8l4 4-4 4M13.5 5.5l-3 13"/>',
  tabela: '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 9.5h17M3.5 14.5h17M9.5 9.5v10"/>',
  musica: '<path d="M9 18V5.5l11-2V16"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="16" r="2.5"/>',
  video: '<rect x="3" y="6" width="13" height="12" rx="2"/><path d="m16 10.5 5-3v9l-5-3z"/>',
  documento: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M8.5 13h7M8.5 16.5h5"/>',
  pdf: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><rect x="8" y="12" width="8" height="5" rx="1"/>',
  compactado: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M11 5v1.5M11 8.5V10M11 12v1.5"/><rect x="9.8" y="15" width="2.4" height="3" rx=".6"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  quebra: '<path d="M4 6h16M4 12h12.5a3.5 3.5 0 0 1 0 7H13"/><path d="m15 16.5-2.5 2.5 2.5 2.5M4 18h5"/>',
  mudancas: '<path d="M12 4.5v7M8.5 8h7M8.5 17h7"/><rect x="3.5" y="3" width="17" height="18" rx="2.5"/>',
  caber: '<path d="M4 9V5a1 1 0 0 1 1-1h4M15 4h4a1 1 0 0 1 1 1v4M20 15v4a1 1 0 0 1-1 1h-4M9 20H5a1 1 0 0 1-1-1v-4"/>',
  'nova-pasta': '<path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2h7.5A2.5 2.5 0 0 1 21 9.5v7a2.5 2.5 0 0 1-2.5 2.5h-13A2.5 2.5 0 0 1 3 16.5z"/><path d="M12 10.5v5M9.5 13h5"/>',
  'novo-arquivo': '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M12 11.5v6M9 14.5h6"/>',
  recolher: '<path d="m7 11 5-5 5 5M7 18l5-5 5 5"/>',
  cima: '<path d="m6 15 6-6 6 6"/>',
};
function icone(nome) {
  if (!ICONES[nome]) return ic(nome);
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONES[nome]}</svg>`;
}

// ---------- tipos de arquivo ----------
const IMAGENS = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'ico', 'svg', 'avif']);
const AUDIOS = new Set(['mp3', 'wav', 'ogg', 'oga', 'm4a', 'aac', 'flac', 'opus', 'weba']);
const VIDEOS = new Set(['mp4', 'webm', 'mov', 'm4v', 'ogv', 'mkv']);
const PLANILHAS = new Set(['xlsx', 'xlsm', 'csv', 'tsv']);
const MARKDOWN = new Set(['md', 'markdown', 'mdx']);
const COMPACTADOS = new Set(['zip', 'rar', '7z', 'gz', 'tgz', 'bz2', 'xz', 'tar', 'iso', 'cab']);
// binários conhecidos: nem tenta ler como texto
const BINARIOS = new Set([...COMPACTADOS, 'exe', 'dll', 'msi', 'sys', 'bin', 'dat', 'db', 'sqlite', 'sqlite3', 'pyc', 'pyd',
  'class', 'jar', 'o', 'obj', 'lib', 'so', 'dylib', 'woff', 'woff2', 'ttf', 'otf', 'eot', 'psd', 'ai', 'aep', 'prproj',
  'flp', 'blend', 'fbx', 'glb', 'xls', 'doc', 'ppt', 'pptx', 'odt', 'ods', 'odp', 'apk', 'lnk', 'mid', 'midi', 'wasm',
  'pdb', 'npy', 'pt', 'safetensors', 'ckpt', 'onnx', 'yyz']);
const CODIGO = new Set(['py', 'js', 'mjs', 'cjs', 'jsx', 'ts', 'tsx', 'css', 'scss', 'less', 'html', 'htm', 'json', 'c', 'h',
  'cpp', 'hpp', 'cs', 'java', 'kt', 'go', 'rs', 'rb', 'php', 'lua', 'sql', 'swift', 'sh', 'ps1', 'bat', 'cmd', 'gml', 'vue',
  'svelte', 'xml', 'yml', 'yaml', 'toml', 'ini']);

function extensao(nome) {
  const i = String(nome || '').lastIndexOf('.');
  return i > 0 ? nome.slice(i + 1).toLowerCase() : '';
}
function tipoVista(nome) {
  const e = extensao(nome);
  if (IMAGENS.has(e)) return 'imagem';
  if (e === 'pdf') return 'pdf';
  if (AUDIOS.has(e)) return 'audio';
  if (VIDEOS.has(e)) return 'video';
  if (PLANILHAS.has(e)) return 'planilha';
  if (e === 'docx') return 'docx';
  if (MARKDOWN.has(e)) return 'markdown';
  if (e === 'html' || e === 'htm') return 'html';
  if (e === 'json') return 'json';
  if (BINARIOS.has(e)) return 'binario';
  return 'texto';
}
function iconeDoArquivo(nome) {
  const e = extensao(nome);
  const v = tipoVista(nome);
  if (v === 'imagem') return 'imagem';
  if (v === 'pdf') return 'pdf';
  if (v === 'audio') return 'musica';
  if (v === 'video') return 'video';
  if (v === 'planilha') return 'tabela';
  if (v === 'docx' || v === 'markdown') return 'documento';
  if (COMPACTADOS.has(e)) return 'compactado';
  if (CODIGO.has(e)) return 'codigo';
  return 'arquivo';
}

const NOMES_LINGUAGEM = {
  python: 'Python', javascript: 'JavaScript', typescript: 'TypeScript', json: 'JSON', xml: 'HTML/XML', css: 'CSS',
  scss: 'SCSS', less: 'Less', markdown: 'Markdown', yaml: 'YAML', ini: 'INI/TOML', bash: 'Shell', powershell: 'PowerShell',
  dos: 'Batch', c: 'C', cpp: 'C++', csharp: 'C#', java: 'Java', kotlin: 'Kotlin', go: 'Go', rust: 'Rust', ruby: 'Ruby',
  php: 'PHP', lua: 'Lua', sql: 'SQL', swift: 'Swift', r: 'R', perl: 'Perl', vbnet: 'VB', objectivec: 'Objective-C',
  diff: 'Diff', graphql: 'GraphQL', makefile: 'Makefile', wasm: 'WebAssembly',
};
function nomeCodificacao(c) {
  return { 'utf-8': 'UTF-8', 'utf-8-sig': t('UTF-8 com BOM'), 'utf-16': 'UTF-16', cp1252: 'Windows-1252' }[c] || c || '';
}

// ---------- funções puras (o testes/test_5_0_arquivos.py roda o trecho entre as marcas no Node) ----------
// PURAS-INICIO

// Organiza (recua) um JSON válido sem passar pelo JSON.parse + JSON.stringify: cada número, texto e chave sai do jeito
// que está escrito no arquivo. O caminho de ida e volta trocava 1234567890123456789 por 1234567890123456800 e 10.50
// por 10.5, escrevia "é" como "é" e punha as chaves numéricas na frente das outras. O resultado tem o mesmo
// formato do JSON.stringify(valor, null, 2). Só chame com um texto que o JSON.parse aceitou.
function organizarJson(texto, recuo = 2) {
  const s = String(texto);
  const n = s.length;
  const saida = [];
  const recuos = [''];
  const quebra = (nivel) => {
    while (recuos.length <= nivel) recuos.push(recuos[recuos.length - 1] + ' '.repeat(recuo));
    return '\n' + recuos[nivel];
  };
  const branco = (c) => c === ' ' || c === '\t' || c === '\n' || c === '\r';
  let nivel = 0;
  for (let i = 0; i < n;) {
    const c = s[i];
    if (c === '"') {
      let j = i + 1;
      while (j < n && s[j] !== '"') j += s[j] === '\\' ? 2 : 1;
      saida.push(s.slice(i, j + 1));
      i = j + 1;
    } else if (c === '{' || c === '[') {
      let j = i + 1;
      while (j < n && branco(s[j])) j++;
      if (s[j] === (c === '{' ? '}' : ']')) { saida.push(c, s[j]); i = j + 1; }  // {} e [] ficam juntos
      else { nivel++; saida.push(c, quebra(nivel)); i++; }
    } else if (c === '}' || c === ']') {
      nivel = Math.max(0, nivel - 1);
      saida.push(quebra(nivel), c);
      i++;
    } else if (c === ',') { saida.push(',', quebra(nivel)); i++; }
    else if (c === ':') { saida.push(': '); i++; }
    else if (branco(c)) i++;
    else {  // número, true, false, null: como estão escritos
      let j = i + 1;
      while (j < n && !branco(s[j]) && s[j] !== ',' && s[j] !== ':' && s[j] !== ']' && s[j] !== '}') j++;
      saida.push(s.slice(i, j));
      i = j;
    }
  }
  return saida.join('');
}

// %XX de um endereço vira o caractere; um % solto ("100%.png", que o decodeURIComponent recusa) fica como está
function decodificarCaminho(s) {
  try { return decodeURIComponent(s); } catch {
    return String(s).replace(/(?:%[0-9A-Fa-f]{2})+/g, (m) => { try { return decodeURIComponent(m); } catch { return m; } });
  }
}

// o caminho (relativo à pasta do trabalho, com /) de um link ou imagem relativa de um Markdown que mora em `base`
function resolverRelativo(base, href) {
  const limpo = decodificarCaminho(String(href || '').split('#')[0].split('?')[0]);
  const partes = (limpo.startsWith('/') ? limpo.slice(1) : (base ? base + '/' : '') + limpo).split('/');
  const saida = [];
  for (const p of partes) { if (p === '..') saida.pop(); else if (p && p !== '.') saida.push(p); }
  return saida.join('/');
}

// Uma célula de planilha que é número (fica à direita, com dígitos do mesmo tamanho): também no jeito brasileiro
// (vírgula decimal, ponto de milhar), com moeda na frente ou atrás e porcentagem. Data, telefone com traço e texto
// com número no meio continuam texto.
function pareceNumero(valor) {
  let s = String(valor ?? '').replace(/[  ]/g, ' ').trim();
  if (!s || s.startsWith('=')) return false;
  s = s.replace(/^([+-]?)\s*(?:R\$|US\$|\$|€|£)\s*/, '$1').replace(/\s*(?:%|€|R\$)$/, '');
  return /^[+-]?\d+(?:[.,]\d+)?(?:e[+-]?\d+)?$/i.test(s)     // 42  42,50  3.14  1e5
    || /^[+-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?$/.test(s)          // 1.234.567,89
    || /^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$/.test(s)          // 1,234,567.89
    || /^[+-]?\d{1,3}(?: \d{3})+(?:,\d+)?$/.test(s)           // 1 234,56
    || /^[+-]?[.,]\d+$/.test(s);                               // .5  ,5
}
// PURAS-FIM

// ---------- utilidades ----------
function tamanho(n) {
  if (n === null || n === undefined) return '';
  const un = ['B', 'KB', 'MB', 'GB', 'TB'];
  let v = Number(n), i = 0;
  while (v >= 1024 && i < un.length - 1) { v /= 1024; i++; }
  return `${i ? v.toLocaleString(localidade(), { maximumFractionDigits: v < 10 ? 1 : 0 }) : v} ${un[i]}`;
}
function semAcento(s) { return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); }
function nomeDe(caminho) { const c = String(caminho || ''); return c.slice(c.lastIndexOf('/') + 1) || c; }
function paiDe(caminho) { const c = String(caminho || ''); const i = c.lastIndexOf('/'); return i < 0 ? '' : c.slice(0, i); }
function ancestrais(caminho) {
  const partes = String(caminho || '').split('/');
  const lista = [];
  for (let i = 1; i < partes.length; i++) lista.push(partes.slice(0, i).join('/'));
  return lista;
}
function consulta(obj) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(obj)) if (v !== undefined && v !== null && v !== '' && v !== false) p.set(k, String(v));
  return p.toString();
}
function raizAtual() { return contextoAtual()?.pasta || null; }
function conversaAtual() { return contextoAtual()?.conversaId || null; }

// caminho absoluto dentro da pasta do trabalho vira relativo (com /); o resto fica como veio (o servidor recusa)
function relativo(caminho) {
  let c = String(caminho || '').trim().replace(/\\/g, '/');
  const raiz = String(raizAtual() || '').replace(/\\/g, '/').replace(/\/+$/, '');
  if (raiz) {
    const baixo = c.toLowerCase(), r = raiz.toLowerCase();
    if (baixo === r) return '';
    if (baixo.startsWith(r + '/')) c = c.slice(raiz.length + 1);
  }
  return c.replace(/^(\.\/)+/, '').replace(/\/+$/, '');
}
function absoluto(rel) {
  const raiz = String(raizAtual() || '').replace(/[\\/]+$/, '');
  return rel ? `${raiz}\\${String(rel).replace(/\//g, '\\')}` : raiz;
}
function mencionar(rel) {
  window.dispatchEvent(new CustomEvent('clave:inserir-texto', { detail: { texto: '`' + (rel || '.') + '`' } }));
}

async function abrirNoPrograma(rel) {
  const raiz = raizAtual();
  try {
    await api('/arquivos/abrir', { metodo: 'POST', corpo: { raiz, caminho: rel } });
  } catch (e) {
    if (e.codigo !== 'executavel') { aviso(e.message, 'erro'); return; }
    const ok = await confirmar(t('Este arquivo é um programa ou script: abrir vai executá-lo no seu computador. Só abra se você sabe o que ele faz.'),
      { titulo: t('Abrir um programa?'), sim: t('Abrir mesmo assim'), perigo: true });
    if (!ok) return;
    try { await api('/arquivos/abrir', { metodo: 'POST', corpo: { raiz, caminho: rel, confirmado: true } }); }
    catch (e2) { aviso(e2.message, 'erro'); }
  }
}
async function revelarNoExplorador(rel) {
  try { await api('/arquivos/revelar', { metodo: 'POST', corpo: { raiz: raizAtual(), caminho: rel } }); }
  catch (e) { aviso(e.message, 'erro'); }
}

// guarda pequena preferência no navegador do app (sem armazenamento: tudo bem)
function lerPref(chave, padrao) {
  try { const v = localStorage.getItem('clave:' + chave); return v === null ? padrao : JSON.parse(v); } catch { return padrao; }
}
function gravarPref(chave, valor) {
  try { localStorage.setItem('clave:' + chave, JSON.stringify(valor)); } catch { /* tudo bem */ }
}

// O menu do ui.js só conhece os ícones do icones.js: os nossos entram no lugar de um ícone de mesmo tamanho
// depois que o menu aparece (assim a posição calculada por ele não muda).
function abrirMenu(ancora, itens, opcoes) {
  const proprios = [];
  const lista = itens.map((it) => {
    if (it === '-' || !ICONES[it.icone]) return it;
    proprios.push(it);
    return { ...it, icone: 'circulo' };
  });
  const m = menu(ancora, lista, opcoes);
  if (m && proprios.length) {
    const botoes = [...m.querySelectorAll('button')];
    lista.filter((it) => it !== '-' && !it.titulo).forEach((it, i) => {
      const original = itens.find((x) => x !== '-' && x.texto === it.texto && x.acao === it.acao);
      if (original && ICONES[original.icone] && botoes[i]?.firstElementChild) botoes[i].firstElementChild.innerHTML = icone(original.icone);
    });
  }
  return m;
}

// menu do botão direito na posição do mouse (o menu do ui.js se ancora num elemento)
function menuNoPonto(x, y, itens) {
  const ancora = el('span', { style: `position:fixed;left:${x}px;top:${y}px;width:1px;height:1px` });
  document.body.append(ancora);
  abrirMenu(ancora, itens);
  ancora.remove();
}

function vazio(iconeNome, titulo, texto, ...extras) {
  const botoes = extras.filter(Boolean);
  return el('div', { class: 'painel-vazio' }, el('span', { html: icone(iconeNome) }),
    titulo ? el('h3', { texto: titulo }) : null, texto ? el('p', { texto }) : null,
    botoes.length ? el('div', { class: 'vis-botoes' }, ...botoes) : null);
}

// "1 item" e "3 itens": o singular é outra frase; cada uma vem pronta (t() com o texto escrito, para o teste de
// tradução achar as duas chaves)
function contar(n, um, varios) {
  return Number(n) === 1 ? um() : varios(numero(n));
}

// os botões Copiar e Prévia dos blocos de código do Markdown (na conversa quem cuida é a tela da conversa)
function ligarBlocosDeCodigo(raizEl) {
  raizEl.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-acao]');
    if (!b || !raizEl.contains(b)) return;
    const bloco = b.closest('.bloco-codigo');
    const codigo = bloco?.querySelector('code')?.textContent || '';
    if (b.dataset.acao === 'copiar-codigo') copiarTexto(codigo, b);
    else if (b.dataset.acao === 'previa') import('./previa.js').then((m) => m.abrirPrevia({ codigo, lingua: bloco?.dataset.lingua || 'html' }));
  });
}

// =====================================================================================================
// ABA ARQUIVOS
// =====================================================================================================

let arvoreInst = null;  // a aba Arquivos montada (o visualizador pede para revelar um arquivo nela)

registrarAba({
  id: 'arquivos', titulo: () => t('Arquivos'), icone: 'arquivos', modos: ['code'], atalho: 'Ctrl+Shift+E',
  tecla: (e) => (e.ctrlKey || e.metaKey) && e.shiftKey && !e.altKey && (e.key === 'E' || e.key === 'e' || e.code === 'KeyE'),
  montar(caixa, ctx) { arvoreInst = montarArquivos(caixa, ctx); return arvoreInst; },
});

function montarArquivos(caixa) {
  const A = {
    raiz: null, conversa: null, geracao: 0, ocultos: !!lerPref('arq-ocultos', false),
    pastas: new Map(),        // caminho da pasta -> { itens, modificado, cortado, total, escondidos, erro }
    abertas: new Set(),       // pastas abertas na árvore
    indice: new Map(),        // caminho -> item (da última vez que desenhou)
    linhasEl: new Map(),      // caminho -> elemento da linha
    ordem: [],                // caminhos na ordem da tela (para as setas)
    sel: null, filtro: '', busca: null, mudados: new Set(), pastasMudadas: new Set(), visivel: false, relogio: null, conferindo: false,
  };

  // ---------- montagem ----------
  const filtro = el('input', {
    class: 'entrada arq-filtro', type: 'search', placeholder: t('Filtrar (Enter procura em tudo)'),
    'aria-label': t('Filtrar os arquivos; Enter procura em todas as pastas'), spellcheck: 'false', autocomplete: 'off',
  });
  const botaoOcultos = el('button', { class: 'icone-botao', type: 'button', html: icone('olho') });
  const barra = el('div', { class: 'painel-barra arq-barra' },
    el('label', { class: 'arq-filtro-caixa' }, el('span', { html: icone('busca'), 'aria-hidden': 'true' }), filtro),
    el('button', { class: 'icone-botao', type: 'button', title: t('Atualizar a lista'), 'aria-label': t('Atualizar a lista'), html: icone('refazer'), onclick: () => atualizarTudo(true) }),
    botaoOcultos,
    el('button', { class: 'icone-botao', type: 'button', title: t('Mais ações'), 'aria-label': t('Mais ações'), 'aria-haspopup': 'menu', html: icone('pontos'),
      onclick: (e) => abrirMenu(e.currentTarget, itensDaRaiz(), { alinhar: 'direita' }) }));
  const cabeca = el('div', { class: 'arq-raiz' });
  const arvore = el('div', { class: 'arq-arvore', role: 'tree', tabindex: '0', 'aria-label': t('Arquivos da pasta do trabalho'), 'data-foco': '' });
  const rodape = el('div', { class: 'arq-rodape', role: 'status', 'aria-live': 'polite' });
  const conteudo = el('div', { class: 'arq-conteudo' }, cabeca, arvore, rodape);
  caixa.append(barra, conteudo);

  function marcarOcultos() {
    botaoOcultos.setAttribute('aria-pressed', String(A.ocultos));
    botaoOcultos.classList.toggle('ativo', A.ocultos);
    const txt = A.ocultos ? t('Esconder as pastas de sistema (.git, node_modules...)') : t('Mostrar as pastas de sistema (.git, node_modules...)');
    botaoOcultos.title = txt;
    botaoOcultos.setAttribute('aria-label', txt);
  }
  marcarOcultos();
  botaoOcultos.addEventListener('click', () => {
    A.ocultos = !A.ocultos;
    gravarPref('arq-ocultos', A.ocultos);
    marcarOcultos();
    atualizarTudo(false, true);
  });

  // ---------- dados ----------
  async function listar(dir) {
    const gen = A.geracao;
    const antes = A.pastas.get(dir);
    if (!antes?.itens) { A.pastas.set(dir, { itens: null }); desenhar(); }
    try {
      const r = await api(`/arquivos/lista?${consulta({ raiz: A.raiz, caminho: dir, ocultos: A.ocultos ? 1 : '' })}`);
      if (gen !== A.geracao) return;
      A.pastas.set(dir, { itens: r.itens, modificado: r.modificado, cortado: r.cortado, total: r.total, escondidos: r.escondidos });
    } catch (e) {
      if (gen !== A.geracao) return;
      if (dir && e.status === 404) {  // a pasta sumiu: fecha ela
        A.pastas.delete(dir); A.abertas.delete(dir); guardarAbertas();
      } else A.pastas.set(dir, { erro: e.message });
    }
    desenhar();
  }

  async function carregarMudados() {
    const gen = A.geracao;
    if (!A.raiz || !A.conversa) { A.mudados = new Set(); A.pastasMudadas = new Set(); desenhar(); return; }
    try {
      const r = await api(`/arquivos/mudancas?${consulta({ raiz: A.raiz, conversa: A.conversa })}`);
      if (gen !== A.geracao) return;
      A.mudados = new Set(r.arquivos || []);
      A.pastasMudadas = new Set([...A.mudados].flatMap(ancestrais));  // as pastas fechadas também ganham a marca
      desenhar();
    } catch { /* sem a lista: só não marca */ }
  }

  function guardarAbertas() {
    if (A.raiz) gravarPref('arq-abertas:' + A.raiz.toLowerCase(), [...A.abertas].slice(0, 200));
  }

  // recarrega o que está à vista; `tudo` também esquece as pastas fechadas (abrem de novo do zero)
  async function atualizarTudo(avisar = false, tudo = false) {
    if (!A.raiz) return;
    if (A.busca) { buscar(A.busca.termo); return; }
    if (tudo) for (const dir of [...A.pastas.keys()]) if (dir && !A.abertas.has(dir)) A.pastas.delete(dir);
    const visiveis = [...A.pastas.keys()].filter((d) => d === '' || A.abertas.has(d));
    await Promise.all(visiveis.map((d) => listar(d)));
    carregarMudados();
    if (avisar) aviso(t('Lista de arquivos atualizada.'));
  }

  // confere a data das pastas abertas e lista de novo só as que mudaram
  async function conferir() {
    if (!A.raiz || A.conferindo || document.visibilityState !== 'visible' || A.busca) return;
    const pastas = [...A.pastas.entries()].filter(([d, p]) => p.itens && (d === '' || A.abertas.has(d)));
    if (!pastas.length) return;
    A.conferindo = true;
    const gen = A.geracao;
    try {
      const r = await api('/arquivos/mtimes', { metodo: 'POST', corpo: { raiz: A.raiz, caminhos: pastas.map(([d]) => d) } });
      if (gen !== A.geracao) return;
      for (const [d, p] of pastas) {
        const m = r.mtimes?.[d];
        if (m === null || m === undefined) {
          if (d === '') { A.pastas.set('', { erro: t('A pasta do trabalho não existe mais.') }); desenhar(); }
          else { A.pastas.delete(d); A.abertas.delete(d); desenhar(); }
        } else if (m !== p.modificado) await listar(d);
      }
    } catch { /* o servidor fechou: o próximo ciclo tenta de novo */ }
    finally { A.conferindo = false; }
  }

  function ligarRelogio() {
    clearInterval(A.relogio);
    A.relogio = A.visivel ? setInterval(conferir, 4000) : null;
  }

  // ---------- desenho ----------
  function linhasVisiveis() {
    const saida = [];
    const andar = (dir, nivel) => {
      const p = A.pastas.get(dir);
      if (!p) return;
      if (p.erro) { saida.push({ especial: 'erro', texto: p.erro, nivel, dir }); return; }
      if (!p.itens) { saida.push({ especial: 'carregando', nivel, dir }); return; }
      if (!p.itens.length && dir !== '') saida.push({ especial: 'vazia', nivel, dir });
      for (const item of p.itens) {
        saida.push({ item, nivel });
        if (item.tipo === 'pasta' && A.abertas.has(item.caminho)) andar(item.caminho, nivel + 1);
      }
      if (p.cortado) saida.push({ especial: 'cortado', nivel, dir, total: p.total });
    };
    andar('', 1);
    if (!A.filtro) return saida;
    const f = semAcento(A.filtro);
    const bate = new Set(), manter = new Set();
    for (const l of saida) {
      if (l.item && semAcento(l.item.nome).includes(f)) {
        bate.add(l.item.caminho);
        for (const a of ancestrais(l.item.caminho)) manter.add(a);
      }
    }
    return saida.filter((l) => l.item && (bate.has(l.item.caminho) || manter.has(l.item.caminho)));
  }

  function nomeComDestaque(nome) {
    const span = el('span', { class: 'arq-nome' });
    const f = A.filtro ? semAcento(A.filtro) : '';
    const i = f ? semAcento(nome).indexOf(f) : -1;
    if (i < 0) { span.textContent = nome; return span; }
    span.append(nome.slice(0, i), el('mark', { texto: nome.slice(i, i + f.length) }), nome.slice(i + f.length));
    return span;
  }

  function linhaEl(l, i) {
    if (l.especial) {
      const textos = {
        carregando: t('Carregando…'), vazia: t('(pasta vazia)'), erro: l.texto,
        cortado: t('Mostrando 2.000 de {total} itens. Use a busca para achar o resto.', { total: numero(l.total) }),
      };
      return el('div', { class: `arq-linha especial ${l.especial}`, role: 'none', style: `--nivel:${l.nivel - 1}` },
        el('span', { class: 'arq-seta' }), el('span', { class: 'arq-nome', texto: textos[l.especial] }));
    }
    const it = l.item;
    const pasta = it.tipo === 'pasta';
    const aberta = pasta && A.abertas.has(it.caminho);
    const sel = A.sel === it.caminho;
    const dica = pasta ? it.nome : `${it.nome}\n${tamanho(it.tamanho)} · ${dataHora(it.modificado)}\n${t('Clique duas vezes para abrir')}`;
    const linha = el('div', {
      class: `arq-linha ${pasta ? 'pasta' : 'arquivo'}${it.oculto ? ' oculto' : ''}${sel ? ' sel' : ''}`,
      role: 'treeitem', id: `arq-l-${i}`, 'aria-level': String(l.nivel), 'aria-selected': String(sel),
      'aria-expanded': pasta ? String(aberta) : null, draggable: 'true', title: dica,
      dados: { caminho: it.caminho }, style: `--nivel:${l.nivel - 1}`,
    },
    el('span', { class: 'arq-seta', html: pasta ? icone('dir') : '' }),
    el('span', { class: 'arq-icone', html: icone(pasta ? (aberta ? 'pasta-aberta' : 'pasta') : iconeDoArquivo(it.nome)) }),
    nomeComDestaque(it.nome),
    it.link ? el('span', { class: 'arq-marca', title: it.fora ? t('Atalho para fora da pasta do trabalho') : t('Atalho (link)'), html: icone('link') }) : null,
    it.protegido ? el('span', { class: 'arq-marca protegido', title: t('Protegido ({padrao}): o Claude não lê', { padrao: it.protegido }), html: icone('trava') }) : null,
    A.mudados.has(it.caminho) ? el('span', { class: 'arq-mudou', title: t('O Claude mudou este arquivo nesta conversa') }, el('span', { class: 'sr', texto: t('mudado pelo Claude') }))
      : pasta && !aberta && A.pastasMudadas?.has(it.caminho) ? el('span', { class: 'arq-mudou dentro', title: t('O Claude mudou arquivos aqui dentro nesta conversa') }, el('span', { class: 'sr', texto: t('com arquivos mudados pelo Claude') })) : null);
    return linha;
  }

  function desenhar() {
    if (!A.raiz) {
      cabeca.hidden = true; rodape.hidden = true; barra.hidden = true;
      arvore.replaceChildren(vazio('pasta', t('Nenhuma pasta escolhida'), t('Escolha a pasta do trabalho no começo da conversa para ver os arquivos dela aqui.')));
      arvore.classList.add('sem-pasta');
      return;
    }
    cabeca.hidden = false; rodape.hidden = false; barra.hidden = false;
    arvore.classList.remove('sem-pasta');
    const nomeRaiz = A.raiz.split(/[\\/]/).filter(Boolean).pop() || A.raiz;
    cabeca.replaceChildren(el('span', { html: icone('pasta-aberta') }), el('b', { texto: nomeRaiz, title: A.raiz }));
    if (A.busca) return desenharBusca();
    const raizP = A.pastas.get('');
    if (raizP?.erro) {
      arvore.replaceChildren(vazio('alerta', t('Não deu para abrir a pasta'), raizP.erro,
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Tentar de novo'), onclick: () => listar('') })));
      rodape.textContent = '';
      return;
    }
    const linhas = linhasVisiveis();
    A.indice = new Map(); A.linhasEl = new Map(); A.ordem = [];
    const frag = document.createDocumentFragment();
    linhas.forEach((l, i) => {
      const e = linhaEl(l, i);
      if (l.item) { A.indice.set(l.item.caminho, l.item); A.linhasEl.set(l.item.caminho, e); A.ordem.push(l.item.caminho); }
      frag.append(e);
    });
    if (raizP?.itens && !raizP.itens.length) frag.append(el('div', { class: 'arq-vazia-raiz' }, t('A pasta está vazia.')));
    else if (A.filtro && !A.ordem.length) frag.append(el('div', { class: 'arq-vazia-raiz' }, t('Nada com "{termo}" nas pastas abertas. Aperte Enter para procurar em todas.', { termo: A.filtro })));
    arvore.replaceChildren(frag);
    marcarAtivo();
    if (raizP?.itens) {
      const partes = [contar(raizP.total ?? raizP.itens.length, () => t('1 item'), (n) => t('{n} itens', { n }))];
      if (raizP.escondidos && !A.ocultos) partes.push(t('{n} de sistema escondidos', { n: raizP.escondidos }));
      rodape.textContent = partes.join(' · ');
    } else rodape.textContent = '';
  }

  function marcarAtivo() {
    const linha = A.sel ? A.linhasEl.get(A.sel) : null;
    if (linha) arvore.setAttribute('aria-activedescendant', linha.id);
    else arvore.removeAttribute('aria-activedescendant');
  }

  function selecionar(caminho, { rolar = true } = {}) {
    const antiga = A.sel ? A.linhasEl.get(A.sel) : null;
    if (antiga) { antiga.classList.remove('sel'); antiga.setAttribute('aria-selected', 'false'); }
    A.sel = caminho;
    const nova = caminho ? A.linhasEl.get(caminho) : null;
    if (nova) {
      nova.classList.add('sel'); nova.setAttribute('aria-selected', 'true');
      if (rolar) nova.scrollIntoView({ block: 'nearest' });
    }
    marcarAtivo();
  }

  function alternarPasta(caminho, abrir) {
    const aberta = A.abertas.has(caminho);
    if (abrir === undefined) abrir = !aberta;
    if (abrir === aberta) return;
    if (abrir) {
      A.abertas.add(caminho);
      if (!A.pastas.get(caminho)?.itens) listar(caminho);
    } else A.abertas.delete(caminho);
    guardarAbertas();
    desenhar();
  }

  // abre as pastas até o arquivo, seleciona e mostra
  async function revelar(caminho) {
    const rel = relativo(caminho);
    if (!A.raiz || !rel) return;
    if (A.busca) sairDaBusca();
    if (A.filtro) { A.filtro = ''; filtro.value = ''; }
    if (!A.pastas.get('')?.itens) await listar('');
    for (const pai of ancestrais(rel)) {
      A.abertas.add(pai);
      if (!A.pastas.get(pai)?.itens) await listar(pai);
    }
    guardarAbertas();
    desenhar();
    selecionar(rel);
    arvore.focus({ preventScroll: true });
  }

  // ---------- busca em todas as pastas ----------
  async function buscar(termo) {
    termo = String(termo || '').trim();
    if (!termo) { sairDaBusca(); return; }
    const gen = A.geracao;
    A.busca = { termo, carregando: true };
    desenhar();
    try {
      const r = await api(`/arquivos/busca?${consulta({ raiz: A.raiz, termo, ocultos: A.ocultos ? 1 : '' })}`);
      if (gen !== A.geracao || A.busca?.termo !== termo) return;
      A.busca = { termo, resultados: r.resultados, cortado: r.cortado, esgotou: r.tempo_esgotado };
    } catch (e) {
      if (gen !== A.geracao) return;
      A.busca = { termo, erro: e.message };
    }
    desenhar();
  }
  function sairDaBusca() { A.busca = null; desenhar(); }

  function desenharBusca() {
    const b = A.busca;
    A.indice = new Map(); A.linhasEl = new Map(); A.ordem = [];
    const topo = el('div', { class: 'arq-busca-topo' },
      el('span', { texto: b.carregando ? t('Procurando "{termo}"…', { termo: b.termo })
        : b.erro ? b.erro
          : b.resultados.length ? contar(b.resultados.length, () => t('1 resultado para "{termo}"', { termo: b.termo }), (n) => t('{n} resultados para "{termo}"', { n, termo: b.termo }))
            : t('Nada com "{termo}" no nome.', { termo: b.termo }) }),
      el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Voltar para a árvore'), onclick: () => { filtro.value = A.filtro = ''; sairDaBusca(); arvore.focus(); } }));
    const itens = (b.resultados || []).map((r, i) => {
      const pasta = r.tipo === 'pasta';
      const item = { ...r, nome: r.nome };
      A.indice.set(r.caminho, item); A.ordem.push(r.caminho);
      const linha = el('div', {
        class: `arq-linha resultado ${pasta ? 'pasta' : 'arquivo'}${A.sel === r.caminho ? ' sel' : ''}`, role: 'treeitem',
        id: `arq-l-${i}`, 'aria-level': '1', 'aria-selected': String(A.sel === r.caminho), draggable: 'true', title: r.caminho,
        dados: { caminho: r.caminho }, style: '--nivel:0',
      },
      el('span', { class: 'arq-icone', html: icone(pasta ? 'pasta' : iconeDoArquivo(r.nome)) }),
      el('span', { class: 'arq-nome' }, nomeDestacadoBusca(r.nome, b.termo)),
      el('span', { class: 'arq-onde', texto: paiDe(r.caminho) || t('(na raiz)') }));
      A.linhasEl.set(r.caminho, linha);
      return linha;
    });
    const fim = [];
    if (b.cortado) fim.push(el('div', { class: 'arq-vazia-raiz', texto: t('Mostrando os primeiros 200. Escreva mais do nome para achar o resto.') }));
    if (b.esgotou) fim.push(el('div', { class: 'arq-vazia-raiz', texto: t('A busca parou no tempo limite: a pasta é grande. Escreva mais do nome.') }));
    arvore.replaceChildren(topo, ...itens, ...fim);
    rodape.textContent = '';
    marcarAtivo();
  }
  function nomeDestacadoBusca(nome, termo) {
    if (/[*?[]/.test(termo)) return nome;
    const i = semAcento(nome).indexOf(semAcento(termo));
    if (i < 0) return nome;
    const f = el('span');
    f.append(nome.slice(0, i), el('mark', { texto: nome.slice(i, i + termo.length) }), nome.slice(i + termo.length));
    return f;
  }

  // ---------- ações ----------
  function itemDe(caminho) { return A.indice.get(caminho) || null; }
  function pastaAlvo(caminho) {
    if (caminho === null || caminho === undefined) return '';
    const it = itemDe(caminho);
    return it && it.tipo === 'pasta' ? caminho : paiDe(caminho);
  }

  async function criar(tipo, onde) {
    const pasta = onde ?? '';
    const nome = await perguntarTexto(tipo === 'pasta' ? t('Nova pasta') : t('Novo arquivo'), {
      rotulo: pasta ? t('Dentro de {pasta}', { pasta }) : t('Na pasta do trabalho'),
      placeholder: tipo === 'pasta' ? t('nome-da-pasta') : t('notas.txt'),
    });
    if (!nome) return;
    try {
      const r = await api('/arquivos/criar', { metodo: 'POST', corpo: { raiz: A.raiz, pasta, nome, tipo } });
      if (pasta) A.abertas.add(pasta);
      guardarAbertas();
      await listar(pasta);
      selecionar(r.caminho);
      arvore.focus({ preventScroll: true });
    } catch (e) { aviso(e.message, 'erro'); }
  }

  async function renomear(caminho) {
    const it = itemDe(caminho);
    if (!it) return;
    const nome = await perguntarTexto(t('Renomear'), { valor: it.nome, rotulo: t('Novo nome') });
    if (!nome || nome === it.nome) return;
    try {
      const r = await api('/arquivos/renomear', { metodo: 'POST', corpo: { raiz: A.raiz, caminho, nome } });
      if (A.abertas.has(caminho)) {  // pasta aberta: as de dentro mudam de nome também
        for (const d of [...A.abertas]) if (d === caminho || d.startsWith(caminho + '/')) { A.abertas.delete(d); A.abertas.add(r.caminho + d.slice(caminho.length)); }
        for (const d of [...A.pastas.keys()]) if (d === caminho || d.startsWith(caminho + '/')) A.pastas.delete(d);
      }
      guardarAbertas();
      visualizadorRenomeou(caminho, r.caminho);
      if (A.busca) await buscar(A.busca.termo); else await listar(paiDe(caminho));
      for (const d of A.abertas) if (d.startsWith(r.caminho) && !A.pastas.get(d)?.itens) listar(d);
      selecionar(r.caminho);
      arvore.focus({ preventScroll: true });
    } catch (e) { aviso(e.message, 'erro'); }
  }

  async function paraLixeira(caminho) {
    const it = itemDe(caminho);
    if (!it) return;
    const ok = await confirmar(it.tipo === 'pasta'
      ? t('A pasta "{nome}" e tudo o que tem dentro vão para a Lixeira do Windows. Dá para recuperar por lá.', { nome: it.nome })
      : t('"{nome}" vai para a Lixeira do Windows. Dá para recuperar por lá.', { nome: it.nome }),
    { titulo: t('Mandar para a Lixeira?'), sim: t('Mandar para a Lixeira'), perigo: true });
    if (!ok) return;
    const i = A.ordem.indexOf(caminho);
    try {
      await api('/arquivos/lixeira', { metodo: 'POST', corpo: { raiz: A.raiz, caminho } });
      for (const d of [...A.abertas]) if (d === caminho || d.startsWith(caminho + '/')) A.abertas.delete(d);
      for (const d of [...A.pastas.keys()]) if (d === caminho || d.startsWith(caminho + '/')) A.pastas.delete(d);
      guardarAbertas();
      visualizadorApagou(caminho);
      if (A.busca) await buscar(A.busca.termo); else await listar(paiDe(caminho));
      const vizinho = A.ordem[Math.min(i, A.ordem.length - 1)];
      if (vizinho) selecionar(vizinho);
      aviso(t('"{nome}" foi para a Lixeira.', { nome: it.nome }));
      arvore.focus({ preventScroll: true });
    } catch (e) { aviso(e.message, 'erro'); }
  }

  function abrir(caminho) {
    const it = itemDe(caminho);
    if (!it) return;
    if (it.tipo === 'pasta') {
      if (A.busca) { revelar(caminho).then(() => alternarPasta(caminho, true)); return; }
      alternarPasta(caminho);
    } else abrirArquivo(caminho);
  }

  function itensDoItem(caminho) {
    const it = itemDe(caminho);
    if (!it) return itensDaRaiz();
    const pasta = it.tipo === 'pasta';
    const dentro = pasta ? caminho : paiDe(caminho);
    return [
      pasta ? { texto: A.abertas.has(caminho) ? t('Fechar a pasta') : t('Abrir a pasta'), icone: 'pasta', acao: () => abrir(caminho) }
        : { texto: t('Abrir no visualizador'), icone: 'olho', acao: () => abrirArquivo(caminho) },
      { texto: pasta ? t('Abrir no Explorador') : t('Abrir com o programa padrão'), icone: 'externo', acao: () => abrirNoPrograma(caminho) },
      { texto: t('Mostrar no Explorador'), icone: 'pasta', acao: () => revelarNoExplorador(caminho) },
      { texto: t('Copiar caminho'), icone: 'copiar', acao: () => copiarTexto(absoluto(caminho)) },
      { texto: t('Mencionar na conversa'), icone: 'chat', acao: () => mencionar(caminho) },
      '-',
      { texto: t('Renomear'), sub: 'F2', icone: 'lapis', acao: () => renomear(caminho) },
      { texto: t('Novo arquivo'), icone: 'novo-arquivo', acao: () => criar('arquivo', dentro) },
      { texto: t('Nova pasta'), icone: 'nova-pasta', acao: () => criar('pasta', dentro) },
      '-',
      { texto: t('Mandar para a Lixeira'), sub: 'Delete', icone: 'lixo', acao: () => paraLixeira(caminho) },
    ];
  }
  function itensDaRaiz() {
    return [
      { texto: t('Novo arquivo'), icone: 'novo-arquivo', acao: () => criar('arquivo', '') },
      { texto: t('Nova pasta'), icone: 'nova-pasta', acao: () => criar('pasta', '') },
      '-',
      { texto: t('Recolher todas as pastas'), icone: 'recolher', acao: () => { A.abertas.clear(); guardarAbertas(); desenhar(); } },
      { texto: t('Abrir a pasta no Explorador'), icone: 'externo', acao: () => abrirNoPrograma('') },
      { texto: t('Copiar o caminho da pasta'), icone: 'copiar', acao: () => copiarTexto(A.raiz) },
    ];
  }
  // ---------- eventos da árvore ----------
  arvore.addEventListener('click', (e) => {
    const linha = e.target.closest('.arq-linha[data-caminho]');
    if (!linha) return;
    // o segundo clique de um clique duplo não fecha de novo a pasta que o primeiro abriu (como no Explorador)
    if (e.detail > 1) return;
    const c = linha.dataset.caminho;
    selecionar(c, { rolar: false });
    if (A.busca) { abrir(c); return; }
    if (itemDe(c)?.tipo === 'pasta') alternarPasta(c);
  });
  arvore.addEventListener('dblclick', (e) => {
    const linha = e.target.closest('.arq-linha[data-caminho]');
    if (linha && itemDe(linha.dataset.caminho)?.tipo === 'arquivo' && !A.busca) abrirArquivo(linha.dataset.caminho);
  });
  arvore.addEventListener('contextmenu', (e) => {
    e.preventDefault();
    const linha = e.target.closest('.arq-linha[data-caminho]');
    if (linha) selecionar(linha.dataset.caminho, { rolar: false });
    menuNoPonto(e.clientX, e.clientY, (linha ? itensDoItem(linha.dataset.caminho) : itensDaRaiz()));
  });
  arvore.addEventListener('dragstart', (e) => {
    const linha = e.target.closest('.arq-linha[data-caminho]');
    if (!linha) return;
    e.dataTransfer.setData('text/plain', '`' + linha.dataset.caminho + '`');
    e.dataTransfer.effectAllowed = 'copy';
  });
  arvore.addEventListener('focus', () => {
    if (!A.sel && A.ordem.length) selecionar(A.ordem[0]);
  });
  arvore.addEventListener('keydown', (e) => {
    if (!A.raiz) return;
    const i = A.ordem.indexOf(A.sel);
    const it = A.sel ? itemDe(A.sel) : null;
    const ir = (j) => { if (A.ordem.length) selecionar(A.ordem[Math.max(0, Math.min(A.ordem.length - 1, j))]); };
    switch (e.key) {
      case 'ArrowDown': ir(i < 0 ? 0 : i + 1); break;
      case 'ArrowUp': ir(i < 0 ? 0 : i - 1); break;
      case 'Home': ir(0); break;
      case 'End': ir(A.ordem.length - 1); break;
      case 'PageDown': ir(i + 15); break;
      case 'PageUp': ir(i - 15); break;
      case 'ArrowRight':
        if (it?.tipo === 'pasta' && !A.busca) {
          if (!A.abertas.has(A.sel)) alternarPasta(A.sel, true);
          else if (A.ordem[i + 1]?.startsWith(A.sel + '/')) ir(i + 1);
        }
        break;
      case 'ArrowLeft':
        if (A.busca) break;
        if (it?.tipo === 'pasta' && A.abertas.has(A.sel)) alternarPasta(A.sel, false);
        else if (A.sel && paiDe(A.sel)) selecionar(paiDe(A.sel));
        break;
      case 'Enter': if (A.sel) abrir(A.sel); break;
      case 'F2': if (A.sel) renomear(A.sel); break;
      case 'Delete': if (A.sel) paraLixeira(A.sel); break;
      case 'ContextMenu': {
        const linha = A.sel ? A.linhasEl.get(A.sel) : null;
        const r = (linha || arvore).getBoundingClientRect();
        menuNoPonto(r.left + 24, r.bottom - 4, (A.sel ? itensDoItem(A.sel) : itensDaRaiz()));
        break;
      }
      case 'Escape': if (A.busca || A.filtro) { filtro.value = A.filtro = ''; sairDaBusca(); } else return; break;
      default:
        if (e.key === 'F10' && e.shiftKey) {
          const linha = A.sel ? A.linhasEl.get(A.sel) : null;
          const r = (linha || arvore).getBoundingClientRect();
          menuNoPonto(r.left + 24, r.bottom - 4, (A.sel ? itensDoItem(A.sel) : itensDaRaiz()));
          break;
        }
        // letra solta: pula para o próximo nome que começa com ela
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && /\S/.test(e.key)) {
          const l = semAcento(e.key);
          const n = A.ordem.length;
          for (let k = 1; k <= n; k++) {
            const c = A.ordem[(i + k + n) % n];
            if (semAcento(nomeDe(c)).startsWith(l)) { selecionar(c); break; }
          }
          break;
        }
        return;
    }
    e.preventDefault();
  });

  filtro.addEventListener('input', () => {
    A.filtro = filtro.value.trim();
    if (A.busca && A.busca.termo !== A.filtro) A.busca = null;
    desenhar();
  });
  filtro.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); buscar(filtro.value); }
    else if (e.key === 'Escape' && (filtro.value || A.busca)) { e.preventDefault(); e.stopPropagation(); filtro.value = A.filtro = ''; sairDaBusca(); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); arvore.focus(); if (A.ordem.length) selecionar(A.ordem[0]); }
  });

  // o Claude escreveu arquivos: atualiza o que está à vista e as marcas do que ele mudou
  window.addEventListener('clave:arquivos-mudaram', () => { if (A.raiz) atualizarTudo(false); });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && A.visivel) conferir(); });

  // ---------- contexto (pasta e conversa) ----------
  function definir(ctx) {
    const raiz = ctx?.modo === 'code' ? (ctx.pasta || null) : null;
    const conversa = ctx?.conversaId || null;
    if (raiz !== A.raiz) {
      A.geracao++;
      A.raiz = raiz; A.conversa = conversa;
      A.pastas = new Map(); A.indice = new Map(); A.linhasEl = new Map(); A.ordem = [];
      A.sel = null; A.busca = null; A.filtro = ''; filtro.value = ''; A.mudados = new Set(); A.pastasMudadas = new Set();
      A.abertas = new Set(raiz ? (lerPref('arq-abertas:' + raiz.toLowerCase(), []) || []) : []);
      desenhar();
      if (raiz) {
        listar('');
        for (const d of A.abertas) listar(d);
        carregarMudados();
      }
      return;
    }
    if (conversa !== A.conversa) { A.conversa = conversa; carregarMudados(); }
  }

  definir(contextoAtual());
  return {
    abrir: (args) => { if (args?.revelar) revelar(args.revelar); },
    mostrar: () => { A.visivel = true; ligarRelogio(); conferir(); },
    esconder: () => { A.visivel = false; ligarRelogio(); },
    contexto: definir,
    revelar,
  };
}

// =====================================================================================================
// ABA VISUALIZADOR
// =====================================================================================================

const MAX_GUIAS = 8;
let visInst = null;

registrarAba({
  id: 'visualizador', titulo: () => t('Visualizador'), icone: 'olho', modos: ['code'], botao: false,
  montar(caixa, ctx) { visInst = montarVisualizador(caixa, ctx); return visInst; },
});

// Abre um arquivo da pasta do trabalho no visualizador (de qualquer lugar do app). `caminho` pode ser relativo à
// pasta ou completo (dentro dela); `linha` rola até a linha e marca ela.
export function abrirArquivo(caminho, { linha } = {}) {
  if (!raizAtual()) { aviso(t('Abra um trabalho no Code com uma pasta para ver os arquivos.'), 'erro'); return; }
  const inst = abrirPainel('visualizador', { caminho: relativo(caminho), linha: Number(linha) || null });
  if (!inst) aviso(t('O visualizador só existe nos trabalhos do Code.'), 'erro');
}

// a árvore avisa quando renomeia ou manda para a Lixeira um arquivo que está aberto aqui
function visualizadorRenomeou(antigo, novo) { visInst?.renomeou(antigo, novo); }
function visualizadorApagou(caminho) { visInst?.apagou(caminho); }

function montarVisualizador(caixa) {
  const V = { raiz: null, conversa: null, abertos: [], ativo: null, visivel: false, relogio: null, conferindo: false };

  const guias = el('div', { class: 'vis-guias', role: 'tablist', 'aria-label': t('Arquivos abertos') });
  const fileira = fileiraDeGuias(guias);  // roda do mouse rola de lado, borda esmaecida quando sobra guia escondida
  const titulo = el('div', { class: 'vis-titulo' });
  const controles = el('div', { class: 'vis-controles' });
  const geral = el('div', { class: 'vis-controles' });
  const barra = el('div', { class: 'painel-barra vis-barra' }, titulo, controles, el('span', { class: 'espaco' }), geral);
  const avisoEl = el('div', { class: 'vis-aviso', role: 'status', 'aria-live': 'polite', hidden: true });
  const busca = montarBusca();
  const corpo = el('div', { class: 'vis-corpo', tabindex: '0', 'data-foco': '', 'aria-label': t('Conteúdo do arquivo') });
  const rodape = el('div', { class: 'vis-rodape' });
  const area = el('div', { class: 'vis-area' }, barra, avisoEl, busca.elemento, corpo, rodape);
  const vazioEl = vazio('olho', t('Nenhum arquivo aberto'), t('Clique duas vezes num arquivo da aba Arquivos para ver aqui. Código, textos, imagens, PDF, planilhas, Word, áudio e vídeo.'));
  caixa.append(guias, area, vazioEl);

  caixa.addEventListener('keydown', (e) => {
    const ctrl = e.ctrlKey || e.metaKey;
    if (ctrl && !e.shiftKey && !e.altKey && (e.key === 'f' || e.key === 'F')) {
      const a = atual();
      if (a?.vista?.busca !== false && a?.vista) { e.preventDefault(); busca.abrir(); }
    } else if (ctrl && !e.shiftKey && (e.key === 'g' || e.key === 'G') && atual()?.vista?.irParaLinha) {
      e.preventDefault(); busca.abrir(':');
    }
  });

  function atual() { return V.abertos.find((a) => a.caminho === V.ativo) || null; }

  // ---------- avisos curtos em cima do conteúdo ----------
  let avisoTempo = null;
  function mostrarAviso(texto, { tipo = '', fica = false, acao = null } = {}) {
    clearTimeout(avisoTempo);
    if (!texto) { avisoEl.hidden = true; avisoEl.replaceChildren(); return; }
    avisoEl.className = `vis-aviso ${tipo}`;
    avisoEl.replaceChildren(...[el('span', { html: icone(tipo === 'aviso' ? 'alerta' : 'info') }), el('span', { class: 'vis-aviso-texto', texto }), acao].filter(Boolean));
    avisoEl.hidden = false;
    if (!fica) avisoTempo = setTimeout(() => { avisoEl.hidden = true; }, 4000);
  }

  // ---------- guias ----------
  function desenharGuias() {
    vazioEl.hidden = V.abertos.length > 0;
    area.hidden = !V.abertos.length;
    guias.hidden = !V.abertos.length;
    guias.replaceChildren(...V.abertos.map((a) => {
      const ativa = a.caminho === V.ativo;
      const botao = el('button', {
        class: 'vis-guia-nome', type: 'button', role: 'tab', 'aria-selected': String(ativa), tabindex: ativa ? '0' : '-1',
        title: a.caminho, onclick: () => ativar(a.caminho),
      }, el('span', { html: icone(iconeDoArquivo(a.nome)) }), el('span', { class: 'rotulo', texto: a.nome }),
      a.sumiu ? el('span', { class: 'sr', texto: t('(apagado)') }) : null);
      const fecharB = el('button', { class: 'vis-guia-fechar', type: 'button', title: t('Fechar'), 'aria-label': t('Fechar {nome}', { nome: a.nome }), html: icone('x'), onclick: (e) => { e.stopPropagation(); fechar(a.caminho); } });
      const g = el('div', { class: `vis-guia${ativa ? ' ativa' : ''}${a.sumiu ? ' sumiu' : ''}` }, botao, fecharB);
      g.addEventListener('auxclick', (e) => { if (e.button === 1) { e.preventDefault(); fechar(a.caminho); } });
      return g;
    }));
    fileira.mostrar(guias.querySelector('.ativa'));
  }
  guias.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    const i = V.abertos.findIndex((a) => a.caminho === V.ativo);
    const prox = V.abertos[(i + (e.key === 'ArrowRight' ? 1 : -1) + V.abertos.length) % V.abertos.length];
    if (prox) { ativar(prox.caminho); guias.querySelector('.vis-guia.ativa .vis-guia-nome')?.focus(); }
  });

  function abrirCaminho(caminho, linha) {
    if (!V.raiz) return;
    if (!caminho) { aviso(t('Escolha um arquivo, não a pasta inteira.'), 'erro'); return; }
    let a = V.abertos.find((x) => x.caminho === caminho);
    if (!a) {
      a = { caminho, nome: nomeDe(caminho), forcar: false, usado: Date.now(), modo: null };
      V.abertos.push(a);
      while (V.abertos.length > MAX_GUIAS) {  // fecha a guia usada há mais tempo (nunca a que está abrindo)
        const velha = V.abertos.filter((x) => x !== a).sort((x, y) => x.usado - y.usado)[0];
        V.abertos.splice(V.abertos.indexOf(velha), 1);
        velha.vista?.destruir?.();
      }
    }
    ativar(caminho, { linha });
  }

  function ativar(caminho, { linha } = {}) {
    const a = V.abertos.find((x) => x.caminho === caminho);
    if (!a) return;
    const anterior = atual();
    if (anterior && anterior !== a) {
      anterior.rolagem = [corpo.scrollTop, corpo.scrollLeft];
      // arquivo enorme fora de vista não fica ocupando memória: lê de novo quando voltar para ele
      if (anterior.vista?.pesada) { anterior.vista.destruir?.(); anterior.vista = null; anterior.carregado = false; }
    }
    V.ativo = caminho;
    a.usado = Date.now();
    desenharGuias();
    busca.fechar();
    mostrarAviso('');
    if (!a.carregado) carregar(a, { linha, voltar: linha ? null : a.rolagem });
    else {
      mostrarVista(a);
      if (linha) a.vista?.irParaLinha?.(linha);
      else if (a.rolagem) requestAnimationFrame(() => { corpo.scrollTop = a.rolagem[0]; corpo.scrollLeft = a.rolagem[1]; });
      if (a.marcaVelha) conferirMarca(a);
    }
  }

  function fechar(caminho) {
    const i = V.abertos.findIndex((x) => x.caminho === caminho);
    if (i < 0) return;
    const [a] = V.abertos.splice(i, 1);
    a.vista?.destruir?.();
    if (V.ativo === caminho) {
      V.ativo = null;
      const prox = V.abertos[Math.min(i, V.abertos.length - 1)];
      if (prox) ativar(prox.caminho);
      else { corpo.replaceChildren(); busca.fechar(); desenharGuias(); }
    } else desenharGuias();
  }

  // ---------- carregar e mostrar ----------
  function urlBruto(a) {
    return `/api/arquivos/bruto/${encodeURIComponent(a.nome)}?${consulta({ raiz: V.raiz, caminho: a.caminho, forcar: a.forcar ? 1 : '', v: a.info?.modificado })}`;
  }
  async function pedir(rota, a, extra = {}) {
    return api(`/arquivos/${rota}?${consulta({ raiz: V.raiz, caminho: a.caminho, forcar: a.forcar ? 1 : '', ...extra })}`);
  }

  async function carregar(a, { linha, manter = false, voltar = null } = {}) {
    const gen = (a.geracao = (a.geracao || 0) + 1);
    const ativa = () => a.geracao === gen && V.ativo === a.caminho && V.abertos.includes(a);
    if (!manter) {
      corpo.replaceChildren(el('div', { class: 'vis-carregando' }, el('span', { class: 'giro', 'aria-hidden': 'true' }), t('Abrindo {nome}…', { nome: a.nome })));
      controles.replaceChildren();
      rodape.textContent = '';
      desenharTitulo(a);
    }
    const rolagem = manter ? [corpo.scrollTop, corpo.scrollLeft] : voltar;
    let vista;
    try {
      const conversaPedida = V.conversa;
      a.info = await pedir('info', a, { conversa: conversaPedida });
      a.sumiu = false;
      a.marcaVelha = conversaPedida !== V.conversa;  // a conversa trocou enquanto lia: a marca é da outra
      if (a.info.tipo === 'pasta') vista = vistaMensagem('pasta', t('Isto é uma pasta'), t('Abra a pasta na aba Arquivos para ver o que tem dentro.'));
      else if (a.info.protegido && !a.forcar) vista = vistaProtegido(a);
      else vista = await montarVista(a);
    } catch (e) {
      if (e.status === 404) { a.sumiu = true; vista = vistaMensagem('alerta', t('O arquivo não está mais lá'), t('Ele foi apagado, movido ou renomeado.'), el('button', { class: 'botao pequeno', type: 'button', texto: t('Fechar esta guia'), onclick: () => fechar(a.caminho) })); }
      else if (e.codigo === 'protegido') vista = vistaProtegido(a, e.message);
      else vista = vistaMensagem('alerta', t('Não deu para abrir este arquivo'), e.message, el('button', { class: 'botao pequeno', type: 'button', texto: t('Tentar de novo'), onclick: () => carregar(a) }));
    }
    if (a.geracao !== gen) { vista?.destruir?.(); return; }
    a.vista?.destruir?.();
    a.vista = vista;
    a.carregado = true;
    if (a.mudancasLigado && !a.info?.mudou) a.mudancasLigado = false;
    if (!ativa()) return;
    desenharGuias();
    mostrarVista(a);
    if (rolagem) requestAnimationFrame(() => { corpo.scrollTop = rolagem[0]; corpo.scrollLeft = rolagem[1]; });
    if (linha) vista.irParaLinha?.(linha);
    if (busca.aberta() && busca.termo()) busca.refazer();
    if (a.marcaVelha) conferirMarca(a);
  }

  async function montarVista(a) {
    const tipo = tipoVista(a.nome);
    if (tipo === 'imagem') return vistaImagem(a);
    if (tipo === 'pdf') return vistaPdf(a);
    if (tipo === 'audio' || tipo === 'video') return vistaMidia(a, tipo);
    if (tipo === 'binario') return vistaBinario(a);
    if (tipo === 'planilha') return vistaPlanilha(a, await pedir('planilha', a));
    if (tipo === 'docx') return vistaDocx(a, await pedir('docx', a));
    const d = await pedir('conteudo', a);
    a.info.modificado = d.modificado;
    if (d.binario) return vistaBinario(a, d);
    if (tipo === 'markdown') return vistaMarkdown(a, d);
    if (tipo === 'json') return vistaJson(a, d);
    if (tipo === 'html') return vistaHtml(a, d);
    return vistaTexto(a, d);
  }

  function desenharTitulo(a) {
    titulo.replaceChildren(...[
      el('span', { class: 'vis-titulo-icone', html: icone(iconeDoArquivo(a.nome)) }),
      el('span', { class: 'vis-titulo-textos' },
        el('b', { texto: a.nome, title: a.caminho }),
        paiDe(a.caminho) ? el('small', { texto: paiDe(a.caminho), title: a.caminho }) : null),
      a.info?.protegido ? el('span', { class: 'vis-trava', title: t('Protegido ({padrao})', { padrao: a.info.protegido }), html: icone('trava') }) : null,
    ].filter(Boolean));
  }

  function mostrarVista(a) {
    desenharTitulo(a);
    const v = a.vista;
    controles.replaceChildren(...(a.mudancasLigado ? [] : v?.controles || []));
    desenharGeral(a);
    if (a.mudancasLigado) mostrarMudancas(a);
    else {
      corpo.replaceChildren(v.elemento);
      corpo.classList.toggle('sem-rolagem', !!v.semRolagem);
      rodape.textContent = v.rodape || '';
      rodape.hidden = !v.rodape;
      v.aoMostrar?.();
    }
    if (v?.aviso) mostrarAviso(v.aviso, { tipo: 'aviso', fica: true, acao: v.acaoAviso || null });
  }

  function desenharGeral(a) {
    const itens = [];
    if (a.info?.mudou && V.conversa) {
      itens.push(el('button', {
        class: `botao pequeno vis-mudancas${a.mudancasLigado ? ' ligado' : ''}`, type: 'button', 'aria-pressed': String(!!a.mudancasLigado),
        title: t('Ver o que o Claude mudou neste arquivo nesta conversa'),
        html: `${icone('mudancas')}<span>${esc(t('Mudanças do Claude'))}</span>`,
        onclick: () => { a.mudancasLigado = !a.mudancasLigado; busca.fechar(); mostrarVista(a); },
      }));
    }
    if (a.vista?.busca !== false && a.vista?.buscavel) {
      itens.push(el('button', { class: 'icone-botao', type: 'button', title: t('Procurar no arquivo (Ctrl+F)'), 'aria-label': t('Procurar no arquivo'), html: icone('busca'), onclick: () => busca.abrir() }));
    }
    itens.push(el('button', { class: 'icone-botao', type: 'button', title: t('Abrir com o programa padrão'), 'aria-label': t('Abrir com o programa padrão'), html: icone('externo'), onclick: () => abrirNoPrograma(a.caminho) }));
    itens.push(el('button', { class: 'icone-botao', type: 'button', title: t('Mais ações'), 'aria-label': t('Mais ações'), 'aria-haspopup': 'menu', html: icone('pontos'),
      onclick: (e) => abrirMenu(e.currentTarget, [
        { texto: t('Recarregar'), icone: 'refazer', acao: () => carregar(a, { manter: true }) },
        { texto: t('Mostrar na aba Arquivos'), icone: 'pasta', acao: () => { abrirPainel('arquivos', { revelar: a.caminho }); } },
        { texto: t('Mostrar no Explorador'), icone: 'pasta', acao: () => revelarNoExplorador(a.caminho) },
        { texto: t('Copiar caminho'), icone: 'copiar', acao: () => copiarTexto(absoluto(a.caminho)) },
        { texto: t('Mencionar na conversa'), icone: 'chat', acao: () => mencionar(a.caminho) },
        '-',
        { texto: t('Fechar esta guia'), icone: 'x', acao: () => fechar(a.caminho) },
      ], { alinhar: 'direita' }) }));
    geral.replaceChildren(...itens);
  }

  // ---------- mudanças do Claude ----------
  async function mostrarMudancas(a) {
    corpo.replaceChildren(el('div', { class: 'vis-carregando' }, el('span', { class: 'giro', 'aria-hidden': 'true' }), t('Procurando as mudanças…')));
    corpo.classList.remove('sem-rolagem');
    rodape.hidden = true;
    let d;
    try { d = await pedir('mudancas', a, { conversa: V.conversa }); }
    catch (e) { corpo.replaceChildren(vistaMensagem('alerta', t('Não deu para ver as mudanças'), e.message).elemento); return; }
    if (!a.mudancasLigado || V.ativo !== a.caminho) return;
    const cab = el('div', { class: 'vis-mudancas-cab' });
    let conteudoEl;
    if (!d.mudou) {
      conteudoEl = vistaMensagem('info', t('Sem mudanças nesta conversa'), t('O Claude não mexeu neste arquivo aqui.')).elemento;
    } else if (d.igual) {
      conteudoEl = vistaMensagem('feito', t('Igual ao que era antes'), t('O Claude mexeu neste arquivo, mas ele voltou a ser como era (as mudanças foram desfeitas).')).elemento;
    } else if (d.binario || d.grande) {
      conteudoEl = vistaMensagem('arquivo', d.binario ? t('Arquivo binário mudou') : t('Arquivo grande demais para comparar'),
        t('Antes: {antes}. Agora: {agora}.', { antes: d.criado ? t('não existia') : tamanho(d.tamanho_antes), agora: d.apagado ? t('apagado') : tamanho(d.tamanho_depois) })).elemento;
    } else {
      const linhas = d.diff.split('\n');
      const mais = linhas.filter((l) => l.startsWith('+') && !l.startsWith('+++')).length;
      const menos = linhas.filter((l) => l.startsWith('-') && !l.startsWith('---')).length;
      cab.append(
        el('span', { texto: d.criado ? t('O Claude criou este arquivo nesta conversa.') : d.apagado ? t('O Claude apagou este arquivo nesta conversa.') : t('Antes da primeira mudança do Claude nesta conversa, comparado com agora.') }),
        el('span', { class: 'vis-contagem' }, el('span', { class: 'mais', texto: `+${numero(mais)}` }), el('span', { class: 'menos', texto: `-${numero(menos)}` })));
      conteudoEl = el('pre', { class: 'diff vis-diff', html: htmlDiff(d.diff) + (d.diff_cortado ? `\n${esc(t('[... a comparação foi cortada: é grande demais ...]'))}` : '') });
    }
    corpo.replaceChildren(...(cab.childNodes.length ? [cab] : []), conteudoEl);
  }

  // ---------- as vistas ----------
  function vistaMensagem(ic_, tituloTxt, texto, ...extras) {
    return { elemento: el('div', { class: 'vis-mensagem' }, vazio(ic_, tituloTxt, texto, ...extras)), busca: false, semRolagem: true };
  }

  function vistaProtegido(a, motivo) {
    const padrao = a.info?.protegido || '';
    return {
      busca: false, semRolagem: true,
      elemento: el('div', { class: 'vis-mensagem' }, vazio('trava', t('Arquivo protegido'),
        motivo || t('Este arquivo está na lista de protegidos ({padrao}): ele pode ter senhas ou chaves. O Claude não lê arquivos assim.', { padrao }),
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Mostrar mesmo assim'), onclick: () => { a.forcar = true; carregar(a); } }))),
    };
  }

  function vistaBinario(a, dados) {
    const info = a.info || {};
    const tam = dados?.tamanho ?? info.tamanho;
    const tipo = extensao(a.nome) ? extensao(a.nome).toUpperCase() : t('sem extensão');
    return {
      busca: false, semRolagem: true,
      rodape: `${tipo} · ${tamanho(tam)}`,
      elemento: el('div', { class: 'vis-mensagem' }, vazio(iconeDoArquivo(a.nome), a.nome,
        t('Este tipo de arquivo não dá para mostrar aqui ({tipo}, {tamanho}). Modificado em {data}.', { tipo, tamanho: tamanho(tam), data: dataHora(info.modificado) }),
        el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Abrir com o programa padrão'), onclick: () => abrirNoPrograma(a.caminho) }),
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Mostrar no Explorador'), onclick: () => revelarNoExplorador(a.caminho) }))),
    };
  }

  function avisoCorte(d) {
    return d.cortado ? t('O arquivo tem {tamanho}: mostrando só os primeiros 2 MB.', { tamanho: tamanho(d.tamanho) }) : null;
  }
  function botaoAbrirPrograma(a) {
    return el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Abrir com o programa padrão'), onclick: () => abrirNoPrograma(a.caminho) });
  }

  // segmentado de duas opções (Formatado / Código...); .marcar(valor) acerta o botão apertado
  function segmentado(rotulo, opcoes, atualV, aoMudar) {
    const caixaS = el('div', { class: 'segmentado vis-seg', role: 'group', 'aria-label': rotulo });
    for (const [valor, texto] of opcoes) {
      caixaS.append(el('button', { type: 'button', 'aria-pressed': String(valor === atualV), texto, dados: { valor },
        onclick: () => { caixaS.marcar(valor); aoMudar(valor); } }));
    }
    caixaS.marcar = (valor) => caixaS.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.valor === valor)));
    return caixaS;
  }

  function vistaTexto(a, d, { linguagem, prefixo = [], textoMostrado } = {}) {
    const texto = textoMostrado ?? d.texto;
    const lingua = linguagem || d.linguagem || 'plaintext';
    const cod = vistaCodigo(texto, lingua);
    const nLinhas = cod.linhas;
    const partes = [contar(nLinhas, () => t('1 linha'), (n) => t('{n} linhas', { n })), NOMES_LINGUAGEM[lingua] || t('Texto puro'), nomeCodificacao(d.codificacao)];
    if (d.crlf !== undefined) partes.push(d.crlf ? 'CRLF' : 'LF');
    partes.push(tamanho(d.tamanho));
    if (cod.semCor) partes.push(t('sem cores (arquivo grande)'));
    const quebraB = el('button', {
      class: `icone-botao${cod.quebra() ? ' ativo' : ''}`, type: 'button', 'aria-pressed': String(cod.quebra()),
      title: t('Quebrar as linhas compridas'), 'aria-label': t('Quebrar as linhas compridas'), html: icone('quebra'),
      onclick: () => { const v = !cod.quebra(); cod.quebra(v); quebraB.setAttribute('aria-pressed', String(v)); quebraB.classList.toggle('ativo', v); },
    });
    return {
      elemento: cod.elemento, buscavel: true, irParaLinha: cod.irParaLinha, pesada: nLinhas > 5000,
      controles: [...prefixo, quebraB], rodape: partes.filter(Boolean).join(' · '),
      aviso: avisoCorte(d), acaoAviso: d.cortado ? botaoAbrirPrograma(a) : null,
    };
  }

  function vistaMarkdown(a, d) {
    a.modo = a.modo || 'formatado';
    const formatado = el('div', { class: 'resposta vis-md' });
    renderizar(formatado, d.texto);
    ligarLinksRelativos(formatado, a);
    ligarBlocosDeCodigo(formatado);
    const fonte = vistaTexto(a, d, { linguagem: 'markdown' });
    const v = {
      buscavel: true,
      controles: [],
      aviso: avisoCorte(d), acaoAviso: d.cortado ? botaoAbrirPrograma(a) : null,
    };
    const aplicar = () => {
      const f = a.modo === 'formatado';
      seg.marcar(a.modo);
      v.elemento = f ? formatado : fonte.elemento;
      v.rodape = f ? contar((d.texto.match(/\S+/g) || []).length, () => t('1 palavra'), (n) => t('{n} palavras', { n })) + ' · ' + tamanho(d.tamanho) : fonte.rodape;
      v.controles = [seg, ...(f ? [] : fonte.controles)];
    };
    const seg = segmentado(t('Ver'), [['formatado', t('Formatado')], ['codigo', t('Código')]], a.modo, (m) => { a.modo = m; aplicar(); busca.fechar(); mostrarVista(a); });
    aplicar();
    // ir para uma linha só existe no código: troca para ele antes
    v.irParaLinha = (n) => {
      if (a.modo !== 'codigo') { a.modo = 'codigo'; aplicar(); mostrarVista(a); }
      fonte.irParaLinha(n);
    };
    return v;
  }

  // links e imagens com caminho relativo dentro do Markdown apontam para os arquivos da pasta
  function ligarLinksRelativos(raizEl, a) {
    const base = paiDe(a.caminho);
    const resolver = (href) => resolverRelativo(base, href);
    const relativoSimples = (u) => u && !/^[a-z][a-z0-9+.-]*:/i.test(u) && !u.startsWith('#') && !u.startsWith('//');
    raizEl.querySelectorAll('img').forEach((img) => {
      const src = img.getAttribute('src') || '';
      if (relativoSimples(src)) {
        const alvo = resolver(src);
        img.src = `/api/arquivos/bruto/${encodeURIComponent(nomeDe(alvo))}?${consulta({ raiz: V.raiz, caminho: alvo })}`;
        img.loading = 'lazy';
      }
    });
    raizEl.querySelectorAll('a[href]').forEach((link) => {
      const href = link.getAttribute('href') || '';
      if (!relativoSimples(href)) return;
      link.removeAttribute('target');
      link.addEventListener('click', (e) => { e.preventDefault(); abrirCaminho(resolver(href)); });
    });
  }

  function vistaJson(a, d) {
    let bonito = null;
    if (!d.cortado && d.texto.length < 3_000_000) {
      // o JSON.parse só confere que é JSON; quem organiza mantém cada número e texto como está no arquivo
      try { JSON.parse(d.texto); bonito = organizarJson(d.texto); } catch { bonito = null; }
    }
    if (bonito === null || bonito === d.texto) return vistaTexto(a, d, { linguagem: 'json' });
    a.modo = a.modo || 'formatado';
    const v = {};
    const aplicar = () => {
      const base = vistaTexto(a, d, { linguagem: 'json', textoMostrado: a.modo === 'formatado' ? bonito : d.texto, prefixo: [seg] });
      Object.assign(v, base);
    };
    const seg = segmentado(t('Ver'), [['formatado', t('Organizado')], ['original', t('Original')]], a.modo, (m) => { a.modo = m; aplicar(); busca.fechar(); mostrarVista(a); });
    aplicar();
    return v;
  }

  function vistaHtml(a, d) {
    const ver = el('button', { class: 'botao pequeno', type: 'button', html: `${icone('olho')}<span>${esc(t('Ver como página'))}</span>`,
      title: t('Abre na Prévia (os arquivos de fora da página, como CSS e imagens, podem não aparecer)'),
      onclick: () => import('./previa.js').then((m) => m.abrirPrevia({ codigo: d.texto, lingua: 'html' })) });
    return vistaTexto(a, d, { linguagem: 'xml', prefixo: [ver] });
  }

  function vistaDocx(a, d) {
    const doc = el('div', { class: 'resposta vis-md vis-docx' });
    renderizar(doc, d.texto);
    ligarBlocosDeCodigo(doc);
    return {
      elemento: doc, buscavel: true, controles: [],
      rodape: contar((d.texto.match(/\S+/g) || []).length, () => t('1 palavra'), (n) => t('{n} palavras', { n })),
      aviso: t('Só o texto do documento: imagens e parte da formatação ficam de fora. Para ver como está de verdade, abra no Word.'),
      acaoAviso: botaoAbrirPrograma(a),
    };
  }

  function vistaImagem(a) {
    a.modo = a.modo || 'caber';
    const img = el('img', { src: urlBruto(a), alt: a.nome, draggable: 'false', decoding: 'async' });
    const quadro = el('div', { class: `vis-imagem ${a.modo}` }, img);
    const v = { elemento: quadro, buscavel: false, busca: false, rodape: tamanho(a.info?.tamanho) };
    img.addEventListener('load', () => {
      v.rodape = `${numero(img.naturalWidth)} × ${numero(img.naturalHeight)} px · ${extensao(a.nome).toUpperCase()} · ${tamanho(a.info?.tamanho)}`;
      if (V.ativo === a.caminho && !a.mudancasLigado) { rodape.textContent = v.rodape; rodape.hidden = false; }
    });
    img.addEventListener('error', () => {
      quadro.replaceChildren(vazio('imagem', t('Não deu para mostrar esta imagem'), t('O arquivo pode estar estragado ou num formato que o app não abre.'), botaoAbrirPrograma(a)));
    });
    v.controles = [segmentado(t('Tamanho'), [['caber', t('Caber')], ['real', '100%']], a.modo, (m) => {
      a.modo = m; quadro.className = `vis-imagem ${m}`;
    })];
    return v;
  }

  function vistaPdf(a) {
    const quadro = el('iframe', { class: 'vis-pdf', src: urlBruto(a), title: t('PDF: {nome}', { nome: a.nome }) });
    return { elemento: quadro, busca: false, semRolagem: true, controles: [], rodape: `PDF · ${tamanho(a.info?.tamanho)}` };
  }

  function vistaMidia(a, tipo) {
    const midia = el(tipo === 'video' ? 'video' : 'audio', { src: urlBruto(a), controls: true, preload: 'metadata', 'aria-label': a.nome });
    const caixaM = el('div', { class: `vis-midia ${tipo}` },
      tipo === 'audio' ? el('span', { class: 'vis-midia-icone', html: icone('musica') }) : null,
      tipo === 'audio' ? el('b', { texto: a.nome }) : null, midia);
    const v = { elemento: caixaM, busca: false, semRolagem: tipo === 'video', controles: [], rodape: `${extensao(a.nome).toUpperCase()} · ${tamanho(a.info?.tamanho)}` };
    midia.addEventListener('loadedmetadata', () => {
      if (!Number.isFinite(midia.duration)) return;
      const s = Math.round(midia.duration);
      const dur = s >= 3600 ? `${Math.floor(s / 3600)}:${String(Math.floor(s / 60) % 60).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}` : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
      v.rodape = [dur, tipo === 'video' && midia.videoWidth ? `${midia.videoWidth} × ${midia.videoHeight}` : null, extensao(a.nome).toUpperCase(), tamanho(a.info?.tamanho)].filter(Boolean).join(' · ');
      if (V.ativo === a.caminho && !a.mudancasLigado) { rodape.textContent = v.rodape; rodape.hidden = false; }
    });
    midia.addEventListener('error', () => {
      caixaM.replaceChildren(vazio(tipo === 'video' ? 'video' : 'musica', t('Este formato não toca aqui'), t('O app toca MP4, WebM, MP3, WAV, OGG e outros formatos comuns. Abra este com o programa padrão.'), botaoAbrirPrograma(a)));
    });
    v.destruir = () => { try { midia.pause(); midia.removeAttribute('src'); midia.load(); } catch { /* já saiu */ } };
    return v;
  }

  function vistaPlanilha(a, d) {
    a.aba = Math.min(a.aba || 0, d.abas.length - 1);
    const v = { buscavel: true, controles: [] };
    const tabelaDe = (aba) => {
      if (!aba.linhas.length) return vazio('tabela', t('Aba vazia'), t('Não tem nada escrito nesta aba.'));
      const cols = Math.max(1, aba.colunas);
      const letra = (n) => { let s = ''; n += 1; while (n > 0) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = Math.floor((n - 1) / 26); } return s; };
      const thead = el('thead', {}, el('tr', {}, el('th', { class: 'canto', 'aria-hidden': 'true' }), ...Array.from({ length: cols }, (_, j) => el('th', { scope: 'col', texto: letra(j) }))));
      const tbody = el('tbody');
      aba.linhas.forEach((linha, i) => {
        const tr = el('tr', {}, el('th', { scope: 'row', texto: String(i + 1) }));
        for (let j = 0; j < cols; j++) {
          const valor = linha[j] ?? '';
          const numeroV = pareceNumero(valor);
          tr.append(el('td', { class: `${numeroV ? 'num' : ''}${String(valor).startsWith('=') ? ' formula' : ''}`, texto: valor, title: valor.length > 40 ? valor : null }));
        }
        tbody.append(tr);
      });
      return el('div', { class: 'vis-tabela-caixa' }, el('table', { class: 'vis-tabela' }, thead, tbody));
    };
    const aplicar = () => {
      const aba = d.abas[a.aba];
      v.elemento = el('div', { class: 'vis-planilha' }, tabelaDe(aba));
      const partes = [];
      if (d.tipo === 'csv') partes.push(t('Separador: {sep}', { sep: { ';': t('ponto e vírgula'), ',': t('vírgula'), '\t': t('tabulação'), '|': '|' }[aba.separador] || aba.separador }));
      partes.push(contar(aba.linhas.length, () => t('1 linha mostrada'), (n) => t('{n} linhas mostradas', { n })));
      if (aba.total_linhas) partes.push(t('{n} na aba', { n: numero(aba.total_linhas) }));
      v.rodape = partes.join(' · ');
      v.aviso = aba.cortado ? t('Mostrando só as primeiras {linhas} linhas e {colunas} colunas. Para ver tudo, abra no Excel.', { linhas: d.linhas_max, colunas: d.colunas_max }) : null;
      v.acaoAviso = aba.cortado ? botaoAbrirPrograma(a) : null;
      v.controles = d.abas.length > 1 ? [seletorAbas] : [];
    };
    const seletorAbas = el('div', { class: 'vis-abas-planilha', role: 'tablist', 'aria-label': t('Abas da planilha') },
      ...d.abas.map((aba, i) => el('button', { type: 'button', role: 'tab', 'aria-selected': String(i === a.aba), texto: aba.nome, title: aba.nome,
        onclick: (e) => {
          a.aba = i;
          e.currentTarget.parentElement.querySelectorAll('button').forEach((b, k) => b.setAttribute('aria-selected', String(k === i)));
          aplicar(); busca.fechar(); mostrarAviso(''); mostrarVista(a);
        } })));
    aplicar();
    return v;
  }

  // ---------- busca dentro do arquivo (Ctrl+F) ----------
  function montarBusca() {
    const campo = el('input', { class: 'entrada vis-busca-campo', type: 'search', placeholder: t('Procurar no arquivo (ou :número da linha)'), 'aria-label': t('Procurar no arquivo'), spellcheck: 'false' });
    const contagem = el('span', { class: 'vis-busca-contagem', 'aria-live': 'polite' });
    const anterior = el('button', { class: 'icone-botao', type: 'button', title: t('Anterior (Shift+Enter)'), 'aria-label': t('Resultado anterior'), html: icone('cima') });
    const proximo = el('button', { class: 'icone-botao', type: 'button', title: t('Próximo (Enter)'), 'aria-label': t('Próximo resultado'), html: icone('baixo') });
    const fecharB = el('button', { class: 'icone-botao', type: 'button', title: t('Fechar (Esc)'), 'aria-label': t('Fechar a busca'), html: icone('x') });
    const elemento = el('div', { class: 'vis-busca', role: 'search', hidden: true }, campo, contagem, anterior, proximo, fecharB);
    const B = { achados: [], i: -1, termo: '', tempo: null };
    const temRealce = typeof CSS !== 'undefined' && CSS.highlights && typeof Highlight !== 'undefined';

    function limpar() {
      if (temRealce) { CSS.highlights.delete('vis-busca'); CSS.highlights.delete('vis-busca-atual'); }
      B.achados = []; B.i = -1;
    }
    // o texto que está à vista, com o lugar de cada pedaço (as linhas de código são blocos: uma busca não junta duas)
    function mapa() {
      const alvo = corpo;
      const nos = [], inicios = [];
      let texto = '', blocoAnterior = null;
      const andar = document.createTreeWalker(alvo, NodeFilter.SHOW_TEXT, {
        acceptNode: (n) => (n.parentElement?.closest('.n, .vis-mudancas-cab, script, style') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT),
      });
      for (let n = andar.nextNode(); n; n = andar.nextNode()) {
        const bloco = n.parentElement?.closest('.lin, p, li, td, th, h1, h2, h3, h4, h5, h6, pre, blockquote, tr') || null;
        if (blocoAnterior && bloco !== blocoAnterior) texto += '\n';
        blocoAnterior = bloco;
        nos.push(n); inicios.push(texto.length);
        texto += n.data;
      }
      return { texto, nos, inicios };
    }
    function ponto(m, pos) {
      let lo = 0, hi = m.nos.length - 1;
      while (lo < hi) { const meio = (lo + hi + 1) >> 1; if (m.inicios[meio] <= pos) lo = meio; else hi = meio - 1; }
      const n = m.nos[lo];
      return [n, Math.max(0, Math.min(n.data.length, pos - m.inicios[lo]))];
    }
    function procurar(manterPosicao = false) {
      const termo = campo.value;
      B.termo = termo;
      limpar();
      if (/^:\s*\d+$/.test(termo.trim())) {
        contagem.textContent = t('Enter vai para a linha');
        return;
      }
      if (!termo) { contagem.textContent = ''; return; }
      const m = mapa();
      const fonte = semAcento(m.texto), alvo = semAcento(termo);
      // semAcento troca "é" por "e" sem mudar o tamanho na maioria dos casos; quando muda, cai na busca simples
      const igual = fonte.length === m.texto.length;
      const base = igual ? fonte : m.texto.toLowerCase();
      const procura = igual ? alvo : termo.toLowerCase();
      let pos = base.indexOf(procura);
      while (pos >= 0 && B.achados.length < 20000) {
        B.achados.push([pos, pos + procura.length]);
        pos = base.indexOf(procura, pos + Math.max(1, procura.length));
      }
      B.mapa = m;
      if (!B.achados.length) { contagem.textContent = t('Nada'); elemento.classList.add('sem-resultado'); return; }
      elemento.classList.remove('sem-resultado');
      if (temRealce) {
        const ranges = B.achados.slice(0, 5000).map(([a, b]) => { const r = new Range(); r.setStart(...ponto(m, a)); r.setEnd(...ponto(m, b)); return r; });
        CSS.highlights.set('vis-busca', new Highlight(...ranges));
      }
      ir(manterPosicao ? Math.max(0, Math.min(B.i, B.achados.length - 1)) : 0);
    }
    function ir(i) {
      if (!B.achados.length) return;
      B.i = (i + B.achados.length) % B.achados.length;
      const [a, b] = B.achados[B.i];
      const r = new Range();
      r.setStart(...ponto(B.mapa, a)); r.setEnd(...ponto(B.mapa, b));
      if (temRealce) CSS.highlights.set('vis-busca-atual', new Highlight(r));
      const alvoEl = r.startContainer.parentElement?.closest('.lin, td, p, li, h1, h2, h3, h4, pre') || r.startContainer.parentElement;
      alvoEl?.scrollIntoView({ block: 'center', inline: 'nearest' });
      contagem.textContent = t('{i} de {n}', { i: numero(B.i + 1), n: B.achados.length >= 20000 ? `${numero(20000)}+` : numero(B.achados.length) });
    }
    function linhaDigitada() {
      const m = /^:\s*(\d+)$/.exec(campo.value.trim());
      if (!m) return false;
      const fn = atual()?.vista?.irParaLinha;
      if (fn) fn(Number(m[1])); else aviso(t('Este arquivo não tem números de linha.'), 'erro');
      return true;
    }
    campo.addEventListener('input', () => { clearTimeout(B.tempo); B.tempo = setTimeout(() => procurar(), 180); });
    campo.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        if (linhaDigitada()) return;
        if (B.termo !== campo.value) procurar();
        else ir(B.i + (e.shiftKey ? -1 : 1));
      } else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); fechar(); corpo.focus({ preventScroll: true }); }
    });
    anterior.addEventListener('click', () => ir(B.i - 1));
    proximo.addEventListener('click', () => { if (B.termo !== campo.value) procurar(); else ir(B.i + 1); });
    fecharB.addEventListener('click', () => { fechar(); corpo.focus({ preventScroll: true }); });
    function abrir(inicio) {
      elemento.hidden = false;
      if (inicio !== undefined) campo.value = inicio;
      else {
        const sel = String(getSelection?.() || '').trim();
        if (sel && !sel.includes('\n') && sel.length < 200) campo.value = sel;
      }
      campo.focus(); campo.select();
      if (inicio === undefined && campo.value) procurar();
      if (inicio !== undefined) { campo.setSelectionRange(campo.value.length, campo.value.length); contagem.textContent = t('Escreva o número e aperte Enter'); }
    }
    function fechar() { clearTimeout(B.tempo); elemento.hidden = true; contagem.textContent = ''; elemento.classList.remove('sem-resultado'); limpar(); }
    return {
      elemento, abrir, fechar,
      aberta: () => !elemento.hidden,
      termo: () => campo.value,
      refazer: () => procurar(true),
    };
  }

  // ---------- conferir se o arquivo mudou no disco (a cada 2 s, só com a aba à vista) ----------
  async function conferir() {
    const a = atual();
    if (!a || !a.carregado || a.sumiu || V.conferindo || document.visibilityState !== 'visible') return;
    V.conferindo = true;
    try {
      const r = await api('/arquivos/mtimes', { metodo: 'POST', corpo: { raiz: V.raiz, caminhos: [a.caminho] } });
      const m = r.mtimes?.[a.caminho];
      if (V.ativo !== a.caminho) return;
      if (m === null || m === undefined) avisarSumiu(a);
      else if (a.info && m !== a.info.modificado) {
        await carregar(a, { manter: true });
        mostrarAviso(t('Atualizado: o arquivo mudou no disco.'));
      }
    } catch { /* o servidor fechou: tenta de novo no próximo ciclo */ }
    finally { V.conferindo = false; }
  }
  function ligarRelogio() {
    clearInterval(V.relogio);
    V.relogio = V.visivel ? setInterval(conferir, 2000) : null;
  }
  function avisarSumiu(a) {
    a.sumiu = true;
    desenharGuias();
    mostrarAviso(t('O arquivo foi apagado ou movido. O que aparece aqui é a última versão vista.'), { tipo: 'aviso', fica: true,
      acao: el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Fechar esta guia'), onclick: () => fechar(a.caminho) }) });
  }

  // a guia mudou: a que está à vista lê de novo agora; as outras, quando aparecerem
  function lerDeNovo(a, texto) {
    a.carregado = false;
    if (a.caminho === V.ativo && V.visivel) { carregar(a, { manter: true }); mostrarAviso(texto); }
  }

  // Lista vazia: o Claude rodou um comando e não dá para saber o que ele mexeu. Confere a data de cada guia aberta
  // e lê de novo só a que mudou (sem isso, todo comando recarregava a guia e o vídeo que tocava voltava ao começo).
  async function conferirAbertos() {
    const alvos = V.abertos.filter((a) => a.carregado && a.info && !a.sumiu);
    if (!alvos.length) return;
    const raiz = V.raiz;
    let r;
    try { r = await api('/arquivos/mtimes', { metodo: 'POST', corpo: { raiz, caminhos: alvos.map((a) => a.caminho) } }); }
    catch { return; }  // o servidor fechou: o relógio da guia à vista confere de novo daqui a pouco
    if (raiz !== V.raiz) return;
    for (const a of alvos) {
      if (!V.abertos.includes(a) || !a.carregado || !a.info) continue;  // fechou ou já está lendo de novo
      const m = r.mtimes?.[a.caminho];
      if (m === null || m === undefined) {
        if (a.caminho === V.ativo && V.visivel) avisarSumiu(a);
        else a.carregado = false;  // quando aparecer, mostra que o arquivo não está mais lá
      } else if (m !== a.info.modificado) lerDeNovo(a, t('Atualizado: o arquivo mudou no disco.'));
    }
  }

  // o Claude escreveu arquivos: lê de novo as guias da lista; sem lista (um comando), só as que mudaram no disco
  window.addEventListener('clave:arquivos-mudaram', (e) => {
    if (!V.raiz) return;
    const lista = (e.detail?.caminhos || []).map(relativo).filter(Boolean);
    if (!lista.length) { conferirAbertos(); return; }
    for (const a of V.abertos) if (lista.includes(a.caminho)) lerDeNovo(a, t('Atualizado: o Claude mudou este arquivo.'));
  });

  // ---------- contexto ----------
  function definir(ctx) {
    const raiz = ctx?.modo === 'code' ? (ctx.pasta || null) : null;
    const conversa = ctx?.conversaId || null;
    if (raiz !== V.raiz) {
      for (const a of V.abertos) a.vista?.destruir?.();
      V.abertos = []; V.ativo = null; V.raiz = raiz; V.conversa = conversa;
      corpo.replaceChildren(); busca.fechar(); mostrarAviso('');
      desenharGuias();
      return;
    }
    if (conversa !== V.conversa) {
      // a marca "o Claude mudou" é de cada conversa: confere só ela, sem montar a vista de novo (a primeira mensagem
      // de um trabalho novo cria a conversa, e o vídeo que estava tocando voltava ao começo)
      V.conversa = conversa;
      for (const a of V.abertos) a.marcaVelha = true;
      const a = atual();
      if (a && V.visivel) conferirMarca(a);
    }
  }

  async function conferirMarca(a) {
    if (!a.carregado || !a.info) return;  // ainda está lendo: no fim da leitura ela confere a marca de novo
    a.marcaVelha = false;
    const conversa = V.conversa;
    let info;
    try { info = await pedir('info', a, { conversa }); }
    catch { lerDeNovo(a, ''); return; }  // sumiu ou não abre mais: a leitura mostra o porquê
    if (!V.abertos.includes(a) || conversa !== V.conversa || !a.carregado || !a.info) return;
    if (info.modificado !== a.info.modificado) { lerDeNovo(a, t('Atualizado: o arquivo mudou no disco.')); return; }
    const comparando = a.mudancasLigado;
    a.info.mudou = info.mudou;
    a.mudancasLigado = false;  // a comparação aberta era da outra conversa
    if (V.ativo !== a.caminho) return;
    if (comparando) mostrarVista(a);
    else desenharGeral(a);
  }

  definir(contextoAtual());
  desenharGuias();
  return {
    abrir: (args) => { if (args?.caminho !== undefined) abrirCaminho(args.caminho, args.linha); },
    mostrar: () => {
      V.visivel = true; ligarRelogio();
      fileira.mostrar(guias.querySelector('.ativa'));  // as guias podem ter mudado com a aba escondida
      const a = atual();
      if (a && !a.carregado) carregar(a, { manter: true });
      else {
        if (a?.marcaVelha) conferirMarca(a);
        conferir();
      }
    },
    esconder: () => { V.visivel = false; ligarRelogio(); },
    redimensionar: () => fileira.mostrar(guias.querySelector('.ativa')),
    contexto: definir,
    renomeou(antigo, novo) {
      for (const a of V.abertos) {
        if (a.caminho === antigo || a.caminho.startsWith(antigo + '/')) {
          const n = novo + a.caminho.slice(antigo.length);
          if (V.ativo === a.caminho) V.ativo = n;
          a.caminho = n; a.nome = nomeDe(n); a.carregado = false; a.sumiu = false;
        }
      }
      desenharGuias();
      const a = atual();
      if (a && V.visivel) carregar(a, { manter: true });
    },
    apagou(caminho) {
      for (const a of [...V.abertos]) if (a.caminho === caminho || a.caminho.startsWith(caminho + '/')) fechar(a.caminho);
    },
  };
}

// ---------- a vista de código: cores, números de linha, quebra de linha e ir para uma linha ----------
const LIMITE_CORES = 400 * 1024;
const LINHAS_POR_BLOCO = 400;

// divide o HTML colorido em linhas, fechando e reabrindo os <span> que atravessam a quebra
function dividirHtml(html) {
  const linhas = [];
  const abertos = [];
  let atual = '';
  const re = /<span[^>]*>|<\/span>|\n|[^<\n]+|</g;
  let m;
  while ((m = re.exec(html))) {
    const p = m[0];
    if (p.startsWith('<span')) { abertos.push(p); atual += p; }
    else if (p === '</span>') { abertos.pop(); atual += p; }
    else if (p === '\n') { atual += '</span>'.repeat(abertos.length); linhas.push(atual); atual = abertos.join(''); }
    else atual += p;
  }
  linhas.push(atual + '</span>'.repeat(abertos.length));
  return linhas;
}

function vistaCodigo(texto, lingua) {
  let linhas = String(texto).split(/\r\n|\r|\n/);
  if (linhas.length > 1 && linhas[linhas.length - 1] === '') linhas.pop();
  const junto = linhas.join('\n');
  const semCor = junto.length > LIMITE_CORES && lingua !== 'plaintext';
  const code = el('code', { class: !semCor && lingua && lingua !== 'plaintext' ? `language-${lingua}` : '', texto: junto });
  if (!semCor) colorirCodigo(el('pre', {}, code));
  const html = dividirHtml(code.innerHTML);
  const digitos = String(html.length).length;
  const caixaC = el('div', { class: 'vis-codigo', style: `--digitos:${digitos}`, role: 'region', 'aria-label': t('Código') });
  for (let i = 0; i < html.length; i += LINHAS_POR_BLOCO) {
    const partes = [];
    for (let j = i; j < Math.min(html.length, i + LINHAS_POR_BLOCO); j++) {
      partes.push(`<div class="lin" data-n="${j + 1}"><span class="n" aria-hidden="true">${j + 1}</span><span class="c">${html[j]}</span></div>`);
    }
    const bloco = el('div', { class: 'bloco-lin', style: `contain-intrinsic-size: auto ${Math.min(LINHAS_POR_BLOCO, html.length - i) * 21}px` });
    bloco.innerHTML = partes.join('');
    caixaC.append(bloco);
  }
  let quebrando = !!lerPref('vis-quebra', false);
  caixaC.classList.toggle('quebra', quebrando);
  return {
    elemento: caixaC, linhas: html.length, semCor,
    quebra(v) {
      if (v === undefined) return quebrando;
      quebrando = !!v; gravarPref('vis-quebra', quebrando); caixaC.classList.toggle('quebra', quebrando);
      return quebrando;
    },
    irParaLinha(n) {
      const alvo = Math.max(1, Math.min(html.length, Number(n) || 1));
      requestAnimationFrame(() => {
        const linha = caixaC.querySelector(`.lin[data-n="${alvo}"]`);
        if (!linha) return;
        caixaC.querySelectorAll('.lin.alvo').forEach((x) => x.classList.remove('alvo'));
        linha.scrollIntoView({ block: 'center' });
        linha.classList.add('alvo');
        setTimeout(() => linha.classList.remove('alvo'), 2600);
      });
    },
  };
}
