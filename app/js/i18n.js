// Tradução da interface. O texto em português fica no código, dentro da função t, e é a chave; o inglês vem
// de app/i18n/en/*.json (um arquivo por tela), juntado pelo servidor em /i18n/en.json. Variáveis vão entre
// chaves no texto e num objeto no segundo argumento ({valor} com { valor: 'US$ 1' }). Chame t na hora de
// desenhar, nunca no topo do módulo: o catálogo só carrega depois que o estado do app chega.
let lingua = 'pt-BR';
let catalogo = {};

export async function carregarIdioma(l) {
  lingua = l === 'en' ? 'en' : 'pt-BR';
  catalogo = {};
  if (lingua === 'en') {
    try { catalogo = await fetch('/i18n/en.json', { cache: 'no-cache' }).then((r) => (r.ok ? r.json() : {})); } catch { catalogo = {}; }
  }
  document.documentElement.lang = lingua;
}

export function idioma() { return lingua; }
export function emIngles() { return lingua === 'en'; }
// para toLocaleString e Intl
export function localidade() { return lingua === 'en' ? 'en-US' : 'pt-BR'; }

export function t(texto, vars) {
  let s = lingua === 'en' ? (catalogo[texto] ?? texto) : texto;
  if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
  return s;
}
