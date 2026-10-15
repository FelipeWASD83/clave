// A aba Tarefas do painel lateral: o que está rodando em segundo plano (respostas ainda chegando, fluxos, rotinas,
// comandos que o Claude deixou rodando e downloads) e o que terminou há pouco. Também exporta o contador da barra
// lateral (contadorTarefas) e observarTarefas(fn), para outras telas acompanharem a mesma lista.
import { api } from './api.js';
import { ic } from './icones.js';
import { el, aviso, usd } from './ui.js';
import { registrarAba, abrirPainel, contextoAtual, ouvirPainel } from './painel.js';
import { notificar } from './fluxo-ui.js';
import { t, localidade } from './i18n.js';

const RAPIDO = 1500;     // com a aba à vista
const DEVAGAR = 5000;    // só o contador (ou a janela escondida)
const LONGA = 30;        // segundos: tarefa mais longa que isso avisa quando termina com a janela sem foco

const TIPOS = () => ({
  resposta: { icone: 'chat', nome: t('Resposta') },
  fluxo: { icone: 'fluxo', nome: t('Fluxo') },
  rotina: { icone: 'calendario', nome: t('Rotina') },
  comando: { icone: 'terminal', nome: t('Comando') },
  download: { icone: 'baixar', nome: t('Download') },
});
const STATUS = () => ({
  rodando: t('Rodando'), esperando: t('Esperando o seu OK'), concluida: t('Concluída'), erro: t('Deu erro'), parada: t('Parada'),
});
const rodandoAgora = (i) => i.status === 'rodando' || i.status === 'esperando';

// ---------- a lista, buscada num lugar só ----------
const vigia = { dados: null, erro: null, recebidoEm: 0, ouvintes: new Set(), timer: null, buscando: false, abaVisivel: false, antes: null };

function precisaBuscar() { return vigia.abaVisivel || vigia.ouvintes.size > 0; }
function intervalo() { return vigia.abaVisivel && !document.hidden ? RAPIDO : DEVAGAR; }

function agendar(logo = false) {
  clearTimeout(vigia.timer);
  vigia.timer = null;
  if (!precisaBuscar()) return;
  vigia.timer = setTimeout(ciclo, logo ? 0 : intervalo());
}

async function ciclo() {
  if (vigia.buscando) return;
  vigia.buscando = true;
  try {
    const dados = await api('/tarefas');
    vigia.erro = null;
    avisarTerminadas(vigia.antes, dados);
    vigia.antes = new Map(dados.rodando.map((i) => [i.id, i]));
    vigia.dados = dados;
    vigia.recebidoEm = Date.now() / 1000;
  } catch (e) {
    vigia.erro = e.message || String(e);
  } finally {
    vigia.buscando = false;
  }
  for (const fn of vigia.ouvintes) { try { fn(vigia.dados, vigia.erro); } catch (e) { console.error(e); } }
  agendar();
}

document.addEventListener('visibilitychange', () => { if (precisaBuscar()) agendar(!document.hidden); });

// a hora do servidor agora (os tempos vêm dele; o relógio do app pode estar um pouco diferente)
function agoraServidor() {
  if (!vigia.dados) return Date.now() / 1000;
  return vigia.dados.agora + (Date.now() / 1000 - vigia.recebidoEm);
}

// Quem quer acompanhar a lista: fn(dados, erro) a cada busca. Devolve a função que para de ouvir.
export function observarTarefas(fn) {
  vigia.ouvintes.add(fn);
  if (vigia.dados || vigia.erro) { try { fn(vigia.dados, vigia.erro); } catch (e) { console.error(e); } }
  if (!vigia.timer && !vigia.buscando) agendar(true);
  return () => { vigia.ouvintes.delete(fn); if (!precisaBuscar()) agendar(); };
}

// Tarefa longa que terminou: aviso do Windows e na tela quando a janela está sem foco; com foco, só o aviso na tela,
// e só se ela não for da conversa aberta (quem está olhando para a conversa já viu terminar).
function avisarTerminadas(antes, dados) {
  if (!antes) return;
  const ainda = new Set(dados.rodando.map((i) => i.id));
  const semFoco = document.hidden || !document.hasFocus();
  for (const id of antes.keys()) {
    if (ainda.has(id)) continue;
    const item = dados.terminadas.find((i) => i.id === id);
    if (!item || item.status === 'parada') continue;   // sumiu da lista ou alguém parou: nada a avisar
    if ((item.fim ?? dados.agora) - item.inicio <= LONGA) continue;
    if (!semFoco && item.conversa_id && item.conversa_id === contextoAtual()?.conversaId && item.tipo !== 'comando') continue;
    const titulo = item.status === 'erro' ? t('Uma tarefa deu erro') : t('Uma tarefa terminou');
    if (semFoco) notificar(titulo, item.titulo);
    aviso(`${titulo}: ${item.titulo}`, item.status === 'erro' ? 'erro' : '');
  }
}

// ---------- formatação ----------
function duracao(segundos) {
  const s = Math.max(0, Math.floor(segundos));
  if (s < 60) return t('{n} s', { n: s });
  if (s < 3600) return t('{m} min {s} s', { m: Math.floor(s / 60), s: String(s % 60).padStart(2, '0') });
  return t('{h} h {m} min', { h: Math.floor(s / 3600), m: String(Math.floor((s % 3600) / 60)).padStart(2, '0') });
}

function hora(ts) {
  return new Date(ts * 1000).toLocaleTimeString(localidade(), { hour: '2-digit', minute: '2-digit' });
}

function abrirEndereco(url) {
  // o navegador do app (aba do Code); fora dele, o navegador do computador
  if (abrirPainel('navegador', { url })) return;
  if (window.clave?.abrirExterno) window.clave.abrirExterno(url);
  else window.open(url, '_blank', 'noopener');
}

// ---------- um cartão por tarefa ----------
class Cartao {
  constructor(item) {
    this.id = item.id;
    this.aberto = false;
    this.colado = true;           // o registro segue o fim, a não ser que a pessoa role para cima
    this.buscandoRegistro = false;
    this.registroFinal = false;   // já buscou o registro depois que a tarefa terminou
    this.item = null;

    this.icone = el('span', { class: 'tarefa-icone', 'aria-hidden': 'true' });
    this.titulo = el('h4', { class: 'tarefa-titulo' });
    this.etiqueta = el('span', { class: 'tarefa-status' });
    this.meta = el('div', { class: 'tarefa-meta' });
    this.tempo = el('span', { class: 'tarefa-tempo' });
    this.detalhe = el('p', { class: 'tarefa-detalhe' });
    this.comando = el('code', { class: 'tarefa-comando' });
    this.progresso = el('div', { class: 'tarefa-progresso' },
      el('div', { class: 'tarefa-barra', role: 'progressbar', 'aria-valuemin': '0', 'aria-valuemax': '100' }, el('span')),
      el('span', { class: 'tarefa-progresso-texto' }));
    this.urls = el('div', { class: 'tarefa-urls' });
    this.botaoParar = el('button', { class: 'botao pequeno fantasma perigo', type: 'button', onclick: () => this.parar() });
    this.botaoRegistro = el('button', { class: 'botao pequeno fantasma', type: 'button', 'aria-expanded': 'false', onclick: () => this.alternarRegistro() });
    this.botaoConversa = el('button', { class: 'botao pequeno fantasma', type: 'button', onclick: () => this.irParaConversa() });
    this.acoes = el('div', { class: 'tarefa-acoes' }, this.botaoParar, this.botaoRegistro, this.botaoConversa);
    this.aviso = el('p', { class: 'tarefa-registro-aviso', hidden: true });
    this.pre = el('pre', { class: 'tarefa-registro-texto', tabindex: '0', 'aria-label': t('Registro da tarefa') });
    this.pre.addEventListener('scroll', () => { this.colado = this.pre.scrollTop + this.pre.clientHeight >= this.pre.scrollHeight - 8; });
    this.registro = el('div', { class: 'tarefa-registro', hidden: true }, this.aviso, this.pre);
    this.elemento = el('article', { class: 'tarefa' },
      this.icone,
      el('div', { class: 'tarefa-corpo' },
        el('div', { class: 'tarefa-topo' }, this.titulo, this.etiqueta),
        this.meta, this.detalhe, this.comando, this.progresso, this.urls, this.acoes, this.registro));
    this.atualizar(item);
  }

  atualizar(item) {
    const antes = this.item;
    this.item = item;
    const tipo = TIPOS()[item.tipo] || { icone: 'progresso', nome: item.tipo };
    const rodando = rodandoAgora(item);
    this.elemento.dataset.tipo = item.tipo;
    this.elemento.dataset.status = item.status;
    this.elemento.setAttribute('aria-label', `${tipo.nome}: ${item.titulo}`);
    if (!antes || antes.tipo !== item.tipo) this.icone.innerHTML = ic(tipo.icone);
    trocarTexto(this.titulo, item.titulo || tipo.nome);
    this.titulo.title = item.titulo || '';
    trocarTexto(this.etiqueta, item.parando ? t('Parando…') : (STATUS()[item.status] || item.status));

    // tipo · tempo · gasto · conversa
    const partes = [el('span', { texto: tipo.nome }), this.tempo];
    if (typeof item.custo === 'number' && (item.custo > 0 || item.tipo !== 'download')) partes.push(el('span', { texto: usd(item.custo) }));
    if (item.conversa_titulo && item.conversa_existe !== false && item.tipo !== 'resposta' && item.tipo !== 'rotina') {
      partes.push(el('span', { class: 'tarefa-conversa', texto: t('em {conversa}', { conversa: item.conversa_titulo }), title: item.conversa_titulo }));
    }
    const chave = partes.map((p) => (p === this.tempo ? '·' : p.textContent)).join('|');
    if (chave !== this.chaveMeta) {
      this.chaveMeta = chave;
      this.meta.replaceChildren(...partes.flatMap((p, i) => (i ? [el('span', { class: 'ponto', 'aria-hidden': 'true', texto: '·' }), p] : [p])));
    }
    this.tique();

    trocarTexto(this.detalhe, item.detalhe || '');
    this.detalhe.hidden = !item.detalhe;
    trocarTexto(this.comando, item.comando || '');
    this.comando.title = item.comando || '';
    this.comando.hidden = !item.comando;

    // progresso: etapas do fluxo ou porcentagem do download
    const temPassos = item.passos && item.passos.total > 0;
    const temProgresso = typeof item.progresso === 'number';
    this.progresso.hidden = !(temPassos || temProgresso);
    if (!this.progresso.hidden) {
      const pct = Math.round((temProgresso ? item.progresso : item.passos.feitos / item.passos.total) * 100);
      const barra = this.progresso.querySelector('.tarefa-barra');
      barra.firstChild.style.width = `${pct}%`;
      barra.setAttribute('aria-valuenow', String(pct));
      const texto = temPassos ? t('{feitas} de {total} etapas', { feitas: item.passos.feitos, total: item.passos.total }) : `${pct}%`;
      barra.setAttribute('aria-label', texto);
      trocarTexto(this.progresso.querySelector('.tarefa-progresso-texto'), texto);
    }

    // endereços locais de um servidor que o comando subiu
    const urls = rodando ? (item.urls || []) : [];
    const chaveUrls = urls.join(' ');
    if (chaveUrls !== this.chaveUrls) {
      this.chaveUrls = chaveUrls;
      this.urls.replaceChildren(...urls.map((u) => el('button', {
        class: 'tarefa-url', type: 'button', title: t('Abrir {url} no navegador', { url: u }),
        'aria-label': t('Abrir {url} no navegador', { url: u }), onclick: () => abrirEndereco(u),
      }, el('span', { html: ic('globo') }), el('span', { class: 'tarefa-url-texto', texto: u }), el('span', { class: 'tarefa-url-acao', texto: t('Abrir no navegador') }))));
    }
    this.urls.hidden = !urls.length;

    // ações
    this.botaoParar.hidden = !(rodando && item.pode_parar);
    if (!this.botaoParar.hidden && !this.parandoAqui) {
      this.botaoParar.disabled = !!item.parando;
      botaoComIcone(this.botaoParar, 'parar', item.parando ? t('Parando…') : t('Parar'), t('Parar: {titulo}', { titulo: item.titulo }));
    }
    this.botaoRegistro.hidden = !item.registro;
    this.desenharBotaoRegistro();
    // a conversa apagada (conversa_existe false) não tem para onde ir: o cartão fica, o botão some
    const outraConversa = item.conversa_id && item.conversa_existe !== false && item.conversa_id !== contextoAtual()?.conversaId;
    this.botaoConversa.hidden = !outraConversa;
    if (outraConversa) {
      botaoComIcone(this.botaoConversa, 'externo', t('Ir para a conversa'),
        t('Ir para a conversa {conversa}', { conversa: item.conversa_titulo || item.titulo }));
    }
    this.acoes.hidden = this.botaoParar.hidden && this.botaoRegistro.hidden && this.botaoConversa.hidden;

    if (this.aberto && vigia.abaVisivel && (rodando || !this.registroFinal)) this.buscarRegistro();
  }

  // o tempo correndo (rodando) ou quanto levou (terminada)
  tique() {
    const i = this.item;
    if (!i) return;
    const texto = rodandoAgora(i)
      ? duracao(agoraServidor() - i.inicio)
      : t('levou {tempo}, terminou às {hora}', { tempo: duracao((i.fim ?? i.inicio) - i.inicio), hora: hora(i.fim ?? i.inicio) });
    trocarTexto(this.tempo, texto);
  }

  desenharBotaoRegistro() {
    botaoComIcone(this.botaoRegistro, 'lista', this.aberto ? t('Esconder o registro') : t('Ver registro'));
    this.botaoRegistro.setAttribute('aria-expanded', String(this.aberto));
  }

  alternarRegistro(abrir = !this.aberto) {
    this.aberto = abrir;
    this.registro.hidden = !abrir;
    this.desenharBotaoRegistro();
    if (abrir) {
      this.colado = true;
      this.registroFinal = false;
      if (!this.pre.textContent) this.pre.textContent = t('Carregando o registro…');
      this.buscarRegistro();
    }
  }

  async buscarRegistro() {
    if (this.buscandoRegistro) return;
    this.buscandoRegistro = true;
    const terminada = !rodandoAgora(this.item);
    try {
      const d = await api(`/tarefas/${encodeURIComponent(this.id)}?linhas=400`);
      const texto = d.registro || (rodandoAgora(d.tarefa) ? t('Nada por enquanto. O que a tarefa escrever aparece aqui.') : t('Esta tarefa não escreveu nada.'));
      this.aviso.hidden = !d.cortado;
      if (d.cortado) this.aviso.textContent = t('Mostrando só o fim do registro.');
      if (this.pre.textContent !== texto) {
        this.pre.textContent = texto;
        if (this.colado) this.pre.scrollTop = this.pre.scrollHeight;
      }
      if (terminada) this.registroFinal = true;
    } catch (e) {
      this.aviso.hidden = false;
      this.aviso.textContent = e.status === 404 ? t('Esta tarefa saiu da lista.') : t('Não deu para ler o registro: {erro}', { erro: e.message });
      if (e.status === 404) this.registroFinal = true;
    } finally {
      this.buscandoRegistro = false;
    }
  }

  async parar() {
    this.parandoAqui = true;
    this.botaoParar.disabled = true;
    botaoComIcone(this.botaoParar, 'parar', t('Parando…'));
    try {
      const r = await api(`/tarefas/${encodeURIComponent(this.id)}/parar`, { metodo: 'POST' });
      if (r.ja_terminou) aviso(t('Esta tarefa já tinha terminado.'));
    } catch (e) {
      aviso(e.message, 'erro');
      this.botaoParar.disabled = false;
      botaoComIcone(this.botaoParar, 'parar', t('Parar'));
    } finally {
      this.parandoAqui = false;
    }
    agendar(true);
  }

  irParaConversa() {
    if (this.item?.conversa_id && this.item.conversa_existe !== false) location.hash = `#/c/${this.item.conversa_id}`;
  }
}

function trocarTexto(no, texto) { if (no.textContent !== texto) no.textContent = texto; }

// troca o ícone e o texto de um botão só quando mudaram (redesenhar a cada busca piscaria o botão sob o mouse)
function botaoComIcone(botao, icone, rotulo, nomeAcessivel = null) {
  const chave = `${icone}|${rotulo}`;
  if (botao.dataset.desenho !== chave) {
    botao.dataset.desenho = chave;
    botao.innerHTML = `${ic(icone)}<span>${rotulo}</span>`;
  }
  if (nomeAcessivel) botao.setAttribute('aria-label', nomeAcessivel);
  else botao.removeAttribute('aria-label');
}

// ---------- a aba ----------
class AbaTarefas {
  constructor(caixa) {
    this.caixa = caixa;
    this.cartoes = new Map();
    this.pedidoAbrir = null;
    this.resumo = el('span', { class: 'meta tarefas-resumo' });
    this.erro = el('div', { class: 'tarefas-erro', role: 'alert', hidden: true });
    this.carregando = el('p', { class: 'tarefas-carregando', texto: t('Carregando as tarefas…') });
    this.vazio = el('div', { class: 'painel-vazio', hidden: true },
      el('span', { html: ic('tarefas') }),
      el('h3', { texto: t('Nada rodando agora') }),
      el('p', { texto: t('Aqui aparecem as respostas que ainda estão chegando, os fluxos e as rotinas em andamento, os comandos que o Claude deixou rodando (um servidor de teste, por exemplo) e os downloads. Você acompanha o tempo e o gasto, vê o registro e pode parar qualquer um.') }));
    this.listaRodando = el('div', { class: 'tarefas-itens' });
    this.listaTerminadas = el('div', { class: 'tarefas-itens' });
    this.nadaRodando = el('p', { class: 'tarefas-nada', texto: t('Nada rodando agora.') });
    this.secaoRodando = el('section', { class: 'tarefas-secao', 'aria-labelledby': 'tarefas-h-rodando' },
      el('h3', { id: 'tarefas-h-rodando', texto: t('Rodando agora') }), this.nadaRodando, this.listaRodando);
    this.secaoTerminadas = el('section', { class: 'tarefas-secao', 'aria-labelledby': 'tarefas-h-terminadas' },
      el('h3', { id: 'tarefas-h-terminadas' }, t('Terminadas há pouco'), el('small', { texto: t('ficam aqui por 30 minutos') })),
      this.listaTerminadas);
    this.corpo = el('div', { class: 'tarefas-corpo' }, this.carregando, this.vazio, this.secaoRodando, this.secaoTerminadas);
    this.secaoRodando.hidden = true;
    this.secaoTerminadas.hidden = true;
    caixa.append(
      el('div', { class: 'painel-barra' }, el('h2', { texto: t('Tarefas') }), this.resumo, el('span', { class: 'espaco' })),
      this.erro, this.corpo);
    this.sair = observarTarefas((dados, erro) => this.desenhar(dados, erro));
    this.relogio = null;
  }

  desenhar(dados, erro) {
    this.erro.hidden = !erro;
    if (erro) this.erro.textContent = t('Não deu para atualizar a lista: {erro}', { erro });
    if (!dados) {
      this.carregando.hidden = !!erro;
      return;
    }
    this.carregando.hidden = true;
    const { rodando, terminadas } = dados;
    this.vazio.hidden = !!(rodando.length || terminadas.length);
    this.secaoRodando.hidden = !this.vazio.hidden;
    this.secaoTerminadas.hidden = !terminadas.length;
    this.nadaRodando.hidden = !!rodando.length;
    this.resumo.textContent = rodando.length ? t('{n} rodando', { n: rodando.length }) : '';

    // tirar um cartão do lugar e pôr de volta (de Rodando para Terminadas, por exemplo) zera a rolagem do registro
    // aberto: guarda antes e devolve depois (ou vai para o fim, se a pessoa estava acompanhando o fim)
    const rolagens = [...this.cartoes.values()].filter((c) => c.aberto).map((c) => [c, c.pre.scrollTop, c.colado]);
    let mexeu = false;
    const vistos = new Set();
    const montar = (lista, alvo) => {
      const nos = lista.map((item) => {
        vistos.add(item.id);
        let c = this.cartoes.get(item.id);
        if (c) c.atualizar(item);
        else { c = new Cartao(item); this.cartoes.set(item.id, c); }
        return c.elemento;
      });
      const atuais = [...alvo.children];
      if (atuais.length !== nos.length || atuais.some((n, i) => n !== nos[i])) { alvo.replaceChildren(...nos); mexeu = true; }
    };
    montar(rodando, this.listaRodando);
    montar(terminadas, this.listaTerminadas);
    if (mexeu) {
      for (const [c, topo, colado] of rolagens) {
        c.colado = colado;
        c.pre.scrollTop = colado ? c.pre.scrollHeight : topo;
      }
    }
    for (const [id, c] of this.cartoes) if (!vistos.has(id)) { c.elemento.remove(); this.cartoes.delete(id); }

    if (this.pedidoAbrir && this.cartoes.has(this.pedidoAbrir)) {
      const c = this.cartoes.get(this.pedidoAbrir);
      this.pedidoAbrir = null;
      if (!c.aberto) c.alternarRegistro(true);
      c.elemento.scrollIntoView({ block: 'nearest' });
    }
  }

  mostrar() {
    vigia.abaVisivel = true;
    agendar(true);
    clearInterval(this.relogio);
    this.relogio = setInterval(() => { for (const c of this.cartoes.values()) if (rodandoAgora(c.item)) c.tique(); }, 1000);
  }

  esconder() {
    vigia.abaVisivel = false;
    clearInterval(this.relogio);
    this.relogio = null;
    agendar();
  }

  abrir(args) {
    if (args?.id) {
      this.pedidoAbrir = args.id;
      if (vigia.dados) this.desenhar(vigia.dados, vigia.erro);
    }
  }

  contexto() {
    if (vigia.dados) this.desenhar(vigia.dados, vigia.erro);  // o "Ir para a conversa" depende da conversa aberta
  }
}

registrarAba({
  id: 'tarefas', titulo: () => t('Tarefas'), icone: 'tarefas', modos: ['chat', 'code'], atalho: 'Ctrl+Shift+Y',
  tecla: (e) => e.shiftKey && (e.key === 'Y' || e.key === 'y'),
  montar(caixa) {
    const aba = new AbaTarefas(caixa);
    return {
      mostrar: () => aba.mostrar(),
      esconder: () => aba.esconder(),
      abrir: (args) => aba.abrir(args),
      contexto: () => aba.contexto(),
    };
  },
});

// Abre a aba Tarefas (com { id } para já abrir o registro de uma tarefa). Fora da tela de conversa, vai antes para
// a conversa da tarefa mais recente que tem uma (ou para uma conversa nova) e abre a aba quando ela montar.
export function abrirTarefas(args = {}) {
  if (contextoAtual()) { abrirPainel('tarefas', args); return; }
  const alvo = (vigia.dados?.rodando || []).find((i) => i.conversa_id && (i.modo === 'chat' || i.modo === 'code'));
  let feito = false;
  const sair = ouvirPainel(() => {
    if (feito || !contextoAtual()) return;
    feito = true;
    sair();
    setTimeout(() => abrirPainel('tarefas', args), 0);
  });
  setTimeout(() => { if (!feito) { feito = true; sair(); } }, 10000);
  location.hash = alvo ? `#/c/${alvo.conversa_id}` : '#/novo';
}

// O contador da barra lateral: quantas tarefas estão rodando (some quando é zero). Clicar abre a aba Tarefas.
export function contadorTarefas() {
  const texto = el('span', { class: 'contador-tarefas-texto' });
  const botao = el('button', { class: 'contador-tarefas', type: 'button', hidden: true, onclick: () => abrirTarefas() },
    el('span', { class: 'contador-tarefas-anel', 'aria-hidden': 'true' }), texto);
  let sair = null;
  const desenhar = (dados) => {
    if (!botao.isConnected && sair && botao.dataset.montado) { sair(); sair = null; return; }
    if (botao.isConnected) botao.dataset.montado = '1';
    const n = dados?.rodando?.length || 0;
    botao.hidden = n === 0;
    texto.textContent = t('{n} rodando', { n });
    const rotulo = n === 1 ? t('1 tarefa rodando em segundo plano. Abrir a aba Tarefas') : t('{n} tarefas rodando em segundo plano. Abrir a aba Tarefas', { n });
    botao.setAttribute('aria-label', rotulo);
    botao.title = rotulo;
  };
  sair = observarTarefas(desenhar);
  return botao;
}
