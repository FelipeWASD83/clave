// Tours com setinhas: escurece a tela, destaca um elemento e mostra um balão apontando para ele, com Voltar,
// Próximo e Pular. Cada tour roda uma vez (fica em cfg.tours_vistos) e dá para refazer em Aprender.
// Os alvos são seletores CSS; passo cujo alvo não existe na tela é pulado sem erro.
import { t } from './i18n.js';
import { cfg, salvarConfig, ouvir } from './estado.js';
import { el } from './ui.js';

// os passos de cada tour (funções: o texto é traduzido na hora de mostrar)
const TOURS = {
  geral: () => [
    { titulo: t('Boas-vindas ao Clave'), texto: t('Um tour rápido pelo que tem em cada lugar. Leva um minuto; dá para pular e refazer depois em Aprender.') },
    { alvo: '.lateral .nova-conversa', titulo: t('Nova conversa'), texto: t('Começa uma conversa no chat. Atalho: Ctrl + Shift + O.') },
    { alvo: '.lateral .nova-conversa + .nova-conversa', titulo: t('Novo trabalho no Code'), texto: t('No modo Code o Claude trabalha numa pasta do seu computador: lê e cria arquivos, mexe em planilhas e roda comandos, sempre com o seu OK.') },
    { alvo: '.compositor textarea', titulo: t('Escreva aqui'), texto: t('Peça como pediria a uma pessoa. Digite / para ver os atalhos (comandos, skills e fluxos).') },
    { alvo: '[data-tour="anexo"]', titulo: t('Anexos'), texto: t('Imagens, PDFs, planilhas e arquivos de texto. Dá também para arrastar ou colar.') },
    { alvo: '[data-tour="modelo"]', titulo: t('Modelo'), texto: t('Haiku para o simples (rápido e baratíssimo), Sonnet para o dia a dia, Opus para o difícil.') },
    { alvo: '[data-tour="esforco"]', titulo: t('Raciocínio'), texto: t('Quanto o Claude pensa antes de responder. Mais raciocínio resolve coisas difíceis, mas custa mais.') },
    { alvo: '[data-tour="web"]', titulo: t('Busca na web'), texto: t('Vem ligada: o Claude pesquisa na internet quando a resposta pedir algo atual. Clique para desligar nesta conversa.') },
    { alvo: '.painel-uso', titulo: t('Seu uso'), texto: t('Tokens, dias seguidos, o mapa de calor e a projeção: em que dia o teto do mês acaba no seu ritmo.') },
    { alvo: '.lateral [data-secao="fluxos"]', titulo: t('Fluxos e agentes'), texto: t('Tarefas grandes divididas em etapas, cada uma num modelo. Sempre pedem o seu OK antes, com o custo estimado.') },
    { alvo: '.lateral [data-secao="rotinas"]', titulo: t('Rotinas'), texto: t('Pedidos que o Claude faz sozinho no horário que você escolher.') },
    { alvo: '.lateral [data-secao="plugins"]', titulo: t('Plugins'), texto: t('Pacotes de skills, agentes e comandos para tipos de trabalho: escritório, escrita, programação e mais.') },
    { alvo: '.lateral [data-secao="aprender"]', titulo: t('Aprender'), texto: t('Lições curtas do zero e um glossário. Cada lição tem um ajudante para tirar dúvidas.') },
    { alvo: '.lateral [data-secao="precos"]', titulo: t('Preços e planos'), texto: t('Quanto custa cada modelo e se a API sai mais barata que a assinatura para o seu jeito de usar.') },
    { alvo: '[data-tour="gasto"]', titulo: t('Gasto do mês'), texto: t('Quanto você já gastou e o teto. Chegando nele, o Clave para (ou só avisa, se você preferir).') },
    { alvo: '.lateral [data-secao="config"]', titulo: t('Configurações'), texto: t('Sua chave da API, o teto, a personalização, o idioma e tudo mais.') },
  ],
  code: () => [
    { alvo: '.painel-ambientes .ambientes-lista', titulo: t('Ambiente'), texto: t('A pasta em que o Claude trabalha. Ele só mexe dentro dela. Troque aqui ou escolha outra.') },
    { alvo: '.ambiente-auto', titulo: t('Modo automático'), texto: t('Liga o modo Livre: o Claude muda arquivos e roda comandos sem perguntar. Apagar e publicar continuam pedindo OK.') },
    { alvo: '[data-tour="permissao"]', titulo: t('Permissões'), texto: t('Quanta liberdade ele tem: Perguntar, Aceitar edições, Plano (só lê e apresenta o plano) ou Livre.') },
    { alvo: '.contexto-code', titulo: t('O que ele sabe da pasta'), texto: t('Regras da pasta (CLAUDE.md) e skills que ele vai seguir.') },
  ],
  // 5.0: o painel do lado direito do Code
  mesa: () => [
    { alvo: '.botoes-painel', titulo: t('O painel do Code'), texto: t('Abre ao lado da conversa, com a largura que você quiser (arraste a borda). Ctrl + J abre e fecha.') },
    { alvo: '.botoes-painel [data-aba="arquivos"]', titulo: t('Arquivos'), texto: t('A pasta inteira: abra qualquer arquivo no visualizador, renomeie, crie ou mande para a Lixeira.') },
    { alvo: '.botoes-painel [data-aba="console"]', titulo: t('Console'), texto: t('O PowerShell de verdade, já na pasta. O botão "Mandar para o Claude" leva o resultado para a conversa.') },
    { alvo: '.botoes-painel [data-aba="navegador"]', titulo: t('Navegador'), texto: t('Você e o Claude usam o mesmo. O botão Locais abre os sites que estão rodando no seu computador. Para clicar ou digitar num site, ele pede OK.') },
    { alvo: '.botoes-painel [data-aba="tarefas"]', titulo: t('Tarefas'), texto: t('O que está rodando em segundo plano: respostas, fluxos, rotinas, servidores e downloads, com o botão Parar.') },
  ],
  precos: () => [
    { alvo: '.cartoes-modelos', titulo: t('Os modelos'), texto: t('Para que serve cada um. Clique num cartão para ver o que mudou e o preço.') },
    { alvo: '.uso-topo .uso-painel', titulo: t('Sua projeção'), texto: t('No ritmo dos últimos dias, quanto o mês vai fechar e quando o teto acaba.') },
    { alvo: '.estimativa', titulo: t('API ou assinatura?'), texto: t('Diga como você usa o Claude normal e veja quanto isso custaria na API, modelo por modelo.') },
  ],
  fluxos: () => [
    { alvo: '.abas', titulo: t('Fluxos, agentes e histórico'), texto: t('Os fluxos prontos, os agentes que fazem as etapas e tudo o que já rodou.') },
    { alvo: '.grade-cartoes .cartao', titulo: t('Um fluxo pronto'), texto: t('Mostra as etapas e o modelo de cada uma, com o custo estimado. Use no chat ou no Code; ele sempre pede OK antes de rodar.') },
  ],
};

// os tours de cada tela, na ordem (cada visita mostra o primeiro que a pessoa ainda não viu)
const DA_TELA = { novo: ['geral'], code: ['code', 'mesa'], precos: ['precos'], fluxos: ['fluxos'] };

let aberto = null;
let agendado = false;

// Um tour aberto ou para abrir: o cartão do modelo novo espera ele fechar (main.js chama de novo no clave:tour-fechou).
export function tourVindo() { return Boolean(aberto) || agendado; }

// Com uma janela aberta (o aviso do Haiku, o cartão do modelo), o tour espera ela fechar para não abrir por cima.
function quandoSemJanela(fn) {
  const camada = document.getElementById('camada');
  if (!camada || !camada.children.length) { fn(); return; }
  const obs = new MutationObserver(() => { if (!camada.children.length) { obs.disconnect(); fn(); } });
  obs.observe(camada, { childList: true });
}

export function tourDaTela(tela) {
  const vistos = cfg().tours_vistos || [];
  const id = (DA_TELA[tela] || []).find((x) => !vistos.includes(x));
  if (!id || aberto || agendado || !cfg().configurado) return;
  if (id !== 'geral' && !(cfg().tours_vistos || []).includes('geral')) return;  // o geral vem primeiro
  agendado = true;
  setTimeout(() => quandoSemJanela(() => { agendado = false; iniciarTour(id); }), 700);  // espera a tela terminar de desenhar
}

export async function refazerTours() {
  await salvarConfig({ tours_vistos: [] });
  location.hash = '#/novo';
  setTimeout(() => iniciarTour('geral'), 900);
}

async function marcarVisto(id) {
  const vistos = new Set(cfg().tours_vistos || []);
  if (vistos.has(id)) return;
  vistos.add(id);
  try { await salvarConfig({ tours_vistos: [...vistos] }); } catch { /* fica para a próxima */ }
}

// o alvo só conta como visível com folga dentro da área que rola (que pode começar abaixo do cabeçalho);
// fora disso ele vai para o meio, com o que está em volta
function trazerParaVista(alvo) {
  const r = alvo.getBoundingClientRect();
  let topo = 0, base = innerHeight;
  for (let p = alvo.parentElement; p; p = p.parentElement) {
    if (/(auto|scroll)/.test(getComputedStyle(p).overflowY)) {
      const c = p.getBoundingClientRect();
      topo = Math.max(0, c.top);
      base = Math.min(innerHeight, c.bottom);
      break;
    }
  }
  if (r.top < topo + 16 || r.bottom > base - 16) alvo.scrollIntoView({ block: 'center', inline: 'nearest' });
}

export function iniciarTour(id) {
  if (aberto || !TOURS[id]) return;
  const passos = TOURS[id]().filter((p) => !p.alvo || document.querySelector(p.alvo));
  if (!passos.length) return;
  let i = 0;
  const destaque = el('div', { class: 'tour-destaque' });
  const seta = el('div', { class: 'tour-seta' });
  const titulo = el('h3');
  const texto = el('p');
  const contador = el('span', { class: 'tour-contador' });
  const voltar = el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Voltar') });
  const proximo = el('button', { class: 'botao pequeno primario', type: 'button' });
  const pular = el('button', { class: 'tour-pular', type: 'button', texto: t('Pular o tour') });
  const balao = el('div', { class: 'tour-balao', role: 'dialog', 'aria-modal': 'true', 'aria-live': 'polite' },
    seta, titulo, texto, el('div', { class: 'tour-acoes' }, contador, pular, voltar, proximo));
  const camada = el('div', { class: 'tour-camada' }, destaque, balao);
  document.body.append(camada);
  aberto = camada;

  // a tela termina de carregar depois que o tour abre (o banner e os painéis chegam por fetch e empurram o resto):
  // quando a página muda, o alvo volta para a vista; quando ela rola, o destaque e o balão acompanham
  let quadro = 0;
  function acompanhar(trazer) {
    if (quadro) return;
    quadro = requestAnimationFrame(() => {
      quadro = 0;
      const p = passos[i];
      const alvo = p?.alvo && document.querySelector(p.alvo);
      if (trazer && alvo) trazerParaVista(alvo);
      posicionar();
    });
  }
  const mudou = new MutationObserver((lista) => { if (lista.some((m) => !camada.contains(m.target))) acompanhar(true); });
  mudou.observe(document.body, { childList: true, subtree: true });
  // o alvo também pode crescer sem mudar o DOM (uma lista que abre com animação)
  const cresceu = new ResizeObserver(() => acompanhar(true));
  const rolou = () => acompanhar(false);
  addEventListener('scroll', rolou, true);

  function fechar() {
    camada.remove();
    aberto = null;
    mudou.disconnect();
    cresceu.disconnect();
    removeEventListener('scroll', rolou, true);
    removeEventListener('resize', posicionar);
    removeEventListener('keydown', teclas, true);
    marcarVisto(id);
    dispatchEvent(new CustomEvent('clave:tour-fechou', { detail: id }));  // o cartão de modelo novo espera por isto
  }
  function teclas(e) {
    if (e.key === 'Escape') { e.preventDefault(); fechar(); }
    else if (e.key === 'ArrowRight' || e.key === 'Enter') { e.preventDefault(); ir(1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); ir(-1); }
  }
  function ir(d) {
    if (i + d >= passos.length) return fechar();
    i = Math.max(0, i + d);
    mostrar();
  }
  function mostrar() {
    const p = passos[i];
    titulo.textContent = p.titulo;
    texto.textContent = p.texto;
    contador.textContent = t('{n} de {total}', { n: i + 1, total: passos.length });
    voltar.hidden = i === 0;
    proximo.textContent = i === passos.length - 1 ? t('Concluir') : t('Próximo');
    const alvo = p.alvo && document.querySelector(p.alvo);
    if (alvo) trazerParaVista(alvo);
    cresceu.disconnect();
    if (alvo) cresceu.observe(alvo);
    requestAnimationFrame(posicionar);
    proximo.focus({ preventScroll: true });
  }
  function posicionar() {
    const p = passos[i];
    const alvo = p.alvo && document.querySelector(p.alvo);
    const margem = 8;
    if (!alvo) {  // sem alvo: balão no meio, destaque escondido
      destaque.style.cssText = 'display:none';
      camada.classList.add('sem-alvo');
      balao.style.left = `${Math.max(16, (innerWidth - balao.offsetWidth) / 2)}px`;
      balao.style.top = `${Math.max(16, (innerHeight - balao.offsetHeight) / 2.4)}px`;
      seta.hidden = true;
      return;
    }
    camada.classList.remove('sem-alvo');
    const r = alvo.getBoundingClientRect();
    destaque.style.cssText = `display:block;left:${r.left - margem}px;top:${r.top - margem}px;width:${r.width + margem * 2}px;height:${r.height + margem * 2}px`;
    // o balão vai à direita do alvo; sem espaço, embaixo; sem espaço, em cima
    const bw = balao.offsetWidth, bh = balao.offsetHeight, folga = 18;
    let lado, x, y;
    if (r.right + folga + bw <= innerWidth - 12) { lado = 'direita'; x = r.right + folga; y = r.top + r.height / 2 - bh / 2; }
    else if (r.bottom + folga + bh <= innerHeight - 12) { lado = 'baixo'; x = r.left + r.width / 2 - bw / 2; y = r.bottom + folga; }
    else { lado = 'cima'; x = r.left + r.width / 2 - bw / 2; y = r.top - folga - bh; }
    x = Math.min(Math.max(12, x), innerWidth - bw - 12);
    y = Math.min(Math.max(12, y), innerHeight - bh - 12);
    balao.style.left = `${x}px`;
    balao.style.top = `${y}px`;
    seta.hidden = false;
    seta.className = `tour-seta ${lado}`;
    // a seta aponta para o meio do alvo
    if (lado === 'direita') seta.style.cssText = `top:${Math.min(bh - 22, Math.max(10, r.top + r.height / 2 - y - 8))}px;left:-8px`;
    else if (lado === 'baixo') seta.style.cssText = `left:${Math.min(bw - 22, Math.max(10, r.left + r.width / 2 - x - 8))}px;top:-8px`;
    else seta.style.cssText = `left:${Math.min(bw - 22, Math.max(10, r.left + r.width / 2 - x - 8))}px;bottom:-8px`;
  }
  voltar.addEventListener('click', () => ir(-1));
  proximo.addEventListener('click', () => ir(1));
  pular.addEventListener('click', fechar);
  camada.addEventListener('click', (e) => { if (e.target === camada) ir(1); });
  addEventListener('resize', posicionar);
  addEventListener('keydown', teclas, true);
  mostrar();
}

// quem acabou de passar pelas boas-vindas cai no início: o tour geral começa ali
ouvir('estado', () => { if (location.hash.replace(/^#\/?/, '').split('/')[0] in { '': 1, novo: 1 }) tourDaTela('novo'); });
