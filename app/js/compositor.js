// A caixa de texto: anexos, escolha de modelo e raciocínio, busca na web, GitHub, permissões e a régua de contexto.
import { api, enviarArquivo } from './api.js';
import { estado, cfg, modeloInfo } from './estado.js';
import { ic } from './icones.js';
import { el, menu, aviso, escolherArquivos, tokens, usd } from './ui.js';
import { escolherDoGitHub } from './github.js';
import { t, localidade } from './i18n.js';

// funções, e não constantes, para o t() rodar depois que o catálogo do idioma carregou
const DESC_ESFORCO = () => ({
  low: t('Rápido e barato. Bom para perguntas simples e conversa.'),
  medium: t('Equilíbrio entre qualidade e custo.'),
  high: t('Pensa mais. Bom para tarefas difíceis e código.'),
  xhigh: t('Para problemas complexos. Mais lento e mais caro.'),
  max: t('Sem limite de raciocínio. Só quando a qualidade vale o custo.'),
});
const PERMISSOES = () => ({
  perguntar: [t('Perguntar'), t('Lê sozinho; pede seu OK para editar e rodar comandos.')],
  aceitar_edicoes: [t('Aceitar edições'), t('Edita arquivos sozinho; pede OK para rodar comandos.')],
  plano: [t('Plano'), t('Só lê e propõe um plano. Não muda nada.')],
  livre: [t('Livre'), t('Faz tudo sozinho, menos apagar ou publicar, que sempre pedem OK.')],
});

export function opcoesPadrao(modo, ajustes = {}) {
  const c = cfg();
  const base = {
    modelo: modo === 'code' ? c.modelo_code : c.modelo_chat,
    esforco: modo === 'code' ? c.esforco_code : c.esforco_chat,
    pensar: true,
    mostrar_raciocinio: c.mostrar_raciocinio !== false,
    busca_web: c.busca_web !== false,
    github: !!c.github_ferramentas && !!c.github_origem,
    rapido: false,
    permissao: c.permissao_code || 'perguntar',
  };
  return { ...base, ...ajustes };
}

const ALIAS_MODELO = { opus: 'claude-opus-5-5', sonnet: 'claude-sonnet-5-5', haiku: 'claude-haiku-5-5', fable: 'claude-fable-5-1' };
const ALIAS_ESFORCO = { baixo: 'low', medio: 'medium', médio: 'medium', alto: 'high', 'muito-alto': 'xhigh', maximo: 'max', máximo: 'max',
  low: 'low', medium: 'medium', high: 'high', xhigh: 'xhigh', max: 'max' };
const ROTULO_TIPO = () => ({ app: t('Do Clave'), comando: t('Comandos'), skill: t('Skills'), fluxo: t('Fluxos prontos') });
// preço por milhão de tokens com a vírgula ou o ponto do idioma (era String(v).replace('.', ','))
const preco = (v) => Number(v).toLocaleString(localidade(), { maximumFractionDigits: 4 });

export function criarCompositor({ modo = 'chat', opcoes, aoEnviar, aoParar, pasta = null, skills = [], placeholder, aoComandoApp }) {
  const op = { ...opcoes };
  let anexos = [];  // {id, nome, tipo, url?}
  let rodando = false;
  let comandos = null;  // carregados na primeira vez que a pessoa digita /

  const area = el('textarea', { rows: 1, placeholder: placeholder || (modo === 'code' ? t('Peça uma tarefa (/ para comandos e skills)') : t('Escreva para o Claude… (/ para comandos)')), 'aria-label': t('Mensagem') });
  const pendentes = el('div', { class: 'anexos-pendentes', hidden: true });
  const botaoEnviar = el('button', { class: 'enviar', type: 'button', 'aria-label': t('Enviar'), title: t('Enviar'), html: ic('enviar') });
  const chipModelo = el('button', { class: 'chip', type: 'button', title: t('Modelo'), dados: { tour: 'modelo' } });
  const chipEsforco = el('button', { class: 'chip', type: 'button', title: t('Raciocínio'), dados: { tour: 'esforco' } });
  const chipWeb = el('button', { class: 'chip', type: 'button', dados: { tour: 'web' }, title: t('Busca na web: o Claude pesquisa quando a resposta precisar. Clique para desligar nesta conversa.'), html: `${ic('globo')}<span>Web</span>` });
  const chipGit = el('button', { class: 'chip', type: 'button', title: t('Ferramentas do GitHub'), html: `${ic('ramo')}<span>GitHub</span>` });
  const chipPerm = el('button', { class: 'chip', type: 'button', title: t('Permissões do modo Code'), dados: { tour: 'permissao' } });
  const chipAnexo = el('button', { class: 'chip', type: 'button', dados: { tour: 'anexo' }, title: t('Anexar arquivo'), 'aria-label': t('Anexar arquivo'), html: ic('clipe') });
  const reguaNivel = el('div', { class: 'regua-nivel' });
  const reguaTexto = el('span', { class: 'meta', texto: '' });
  const custoTexto = el('span', { class: 'meta', texto: '' });
  const regua = el('div', { class: 'regua', title: t('Quanto da memória do modelo esta conversa já ocupa') },
    el('div', { class: 'regua-trilho' }, reguaNivel), reguaTexto, custoTexto);

  const caixa = el('div', { class: 'compositor' }, pendentes, area,
    el('div', { class: 'compositor-barra' }, chipAnexo, chipModelo, chipEsforco, chipWeb,
      estado.info?.github?.origem ? chipGit : null, modo === 'code' ? chipPerm : null,
      el('span', { class: 'espaco' }), botaoEnviar));
  const elemento = el('div', { class: 'compositor-area' }, el('div', { class: 'coluna' }, caixa, regua));

  function desenharChips() {
    const m = modeloInfo(op.modelo);
    chipModelo.innerHTML = `${ic('faisca')}<span>${m.nome || op.modelo}</span>${ic('baixo', 'class="seta"')}`;
    const pensa = op.pensar || !m.desliga_pensamento;
    const nomeEsf = (estado.info?.esforcos || []).find((e) => e.id === op.esforco)?.nome || t('Médio');
    chipEsforco.innerHTML = `${ic('cerebro')}<span>${m.esforco === false ? t('Padrão') : (pensa ? nomeEsf : t('Sem pensar'))}</span>${op.rapido && m.rapido ? ic('raio') : ''}${ic('baixo', 'class="seta"')}`;
    chipWeb.classList.toggle('ligado', !!op.busca_web);
    chipWeb.setAttribute('aria-pressed', String(!!op.busca_web));
    chipGit.classList.toggle('ligado', !!op.github);
    chipGit.setAttribute('aria-pressed', String(!!op.github));
    const perms = PERMISSOES();
    const p = perms[op.permissao] || perms.perguntar;
    chipPerm.innerHTML = `${ic('escudo')}<span>${p[0]}</span>${ic('baixo', 'class="seta"')}`;
    chipPerm.classList.toggle('ligado', op.permissao === 'livre');
  }

  chipModelo.addEventListener('click', () => {
    const itens = [{ titulo: t('Modelo') }];
    for (const m of estado.info?.modelos || []) {
      itens.push({
        texto: m.nome, marcado: m.id === op.modelo,
        sub: `${m.resumo ? m.resumo + ' ' : ''}${t('US$ {entrada} / {saida} por milhão de tokens', { entrada: preco(m.entrada), saida: preco(m.saida) })}`,
        acao: () => { op.modelo = m.id; if (m.esforco_padrao && !m.esforco === false) { /* mantém o esforço escolhido */ } desenharChips(); },
      });
    }
    menu(chipModelo, itens, { acima: true });
  });

  chipEsforco.addEventListener('click', () => {
    const m = modeloInfo(op.modelo);
    const itens = [];
    if (m.esforco !== false) {
      itens.push({ titulo: t('Quanto ele pensa') });
      const descricoes = DESC_ESFORCO();
      for (const e of estado.info?.esforcos || []) {
        const bloqueado = !op.pensar && m.desliga_pensamento && ['xhigh', 'max'].includes(e.id);
        itens.push({ texto: e.id === m.esforco_padrao ? t('{nome} (padrão do modelo)', { nome: e.nome }) : e.nome, sub: descricoes[e.id], marcado: e.id === op.esforco, desligado: bloqueado,
          acao: () => { op.esforco = e.id; desenharChips(); } });
      }
      itens.push('-');
    }
    if (m.desliga_pensamento) {
      itens.push({ texto: (op.pensar ? '✓ ' : '') + t('Pensar antes de responder'), sub: t('Desligado, responde mais rápido e gasta menos (até o nível Alto).'),
        acao: () => { op.pensar = !op.pensar; if (!op.pensar && ['xhigh', 'max'].includes(op.esforco)) op.esforco = 'high'; desenharChips(); } });
    } else if (m.pensamento_sempre) {
      itens.push({ texto: t('Este modelo sempre pensa'), sub: t('O raciocínio não desliga; o nível acima controla quanto.'), desligado: true });
    }
    itens.push({ texto: (op.mostrar_raciocinio ? '✓ ' : '') + t('Mostrar o raciocínio'), sub: t('Mostra um resumo do que ele pensou. Custa o mesmo.'),
      acao: () => { op.mostrar_raciocinio = !op.mostrar_raciocinio; desenharChips(); } });
    if (m.rapido) {
      itens.push({ texto: (op.rapido ? '✓ ' : '') + t('Modo rápido'), sub: t('Até 2,5x mais rápido, pelo dobro do preço.'),
        acao: () => { op.rapido = !op.rapido; desenharChips(); } });
    }
    menu(chipEsforco, itens, { acima: true });
  });

  chipWeb.addEventListener('click', () => { op.busca_web = !op.busca_web; desenharChips(); });
  chipGit.addEventListener('click', () => { op.github = !op.github; desenharChips(); });
  chipPerm.addEventListener('click', () => {
    menu(chipPerm, [{ titulo: t('Permissões') }, ...Object.entries(PERMISSOES()).map(([id, [nome, sub]]) => ({
      texto: nome, sub, marcado: op.permissao === id, acao: () => { op.permissao = id; desenharChips(); },
    }))], { acima: true });
  });

  chipAnexo.addEventListener('click', () => {
    const itens = [{ texto: t('Arquivo do computador'), sub: t('Imagens, PDFs, textos e código'), icone: 'arquivo', acao: async () => adicionarArquivos(await escolherArquivos()) }];
    if (estado.info?.github?.origem) itens.push({ texto: t('Arquivos do GitHub'), sub: t('De um dos seus repositórios'), icone: 'ramo', acao: async () => {
      const novos = await escolherDoGitHub();
      for (const a of novos || []) adicionarAnexo(a);
    } });
    menu(chipAnexo, itens, { acima: true });
  });

  async function adicionarArquivos(lista) {
    for (const f of lista || []) {
      if (f.size > 30 * 1024 * 1024) { aviso(t('{nome}: maior que 30 MB.', { nome: f.name }), 'erro'); continue; }
      try {
        const a = await enviarArquivo(f);
        if (f.type.startsWith('image/')) a.url = URL.createObjectURL(f);
        adicionarAnexo(a);
      } catch (e) { aviso(`${f.name}: ${e.message}`, 'erro'); }
    }
  }

  function adicionarAnexo(a) {
    anexos.push(a);
    desenharAnexos();
  }

  function desenharAnexos() {
    pendentes.hidden = !anexos.length;
    pendentes.replaceChildren(...anexos.map((a, i) => cartaoAnexo(a, () => { anexos.splice(i, 1); desenharAnexos(); })));
  }

  caixa.addEventListener('dragover', (e) => { if (e.dataTransfer?.types?.includes('Files')) { e.preventDefault(); caixa.classList.add('arrastando'); } });
  caixa.addEventListener('dragleave', () => caixa.classList.remove('arrastando'));
  caixa.addEventListener('drop', (e) => {
    if (!e.dataTransfer?.files?.length) return;
    e.preventDefault(); caixa.classList.remove('arrastando');
    adicionarArquivos([...e.dataTransfer.files]);
  });
  area.addEventListener('paste', (e) => {
    const arquivos = [...(e.clipboardData?.files || [])];
    if (arquivos.length) { e.preventDefault(); adicionarArquivos(arquivos.map((f, i) => f.name ? f : new File([f], t('colado-{n}.png', { n: i + 1 }), { type: f.type }))); }
  });

  function ajustarAltura() {
    area.style.height = 'auto';
    area.style.height = Math.min(area.scrollHeight, innerHeight * 0.4) + 'px';
    botaoEnviar.disabled = !rodando && !area.value.trim() && !anexos.length;
  }
  area.addEventListener('input', () => { ajustarAltura(); sugerirComandos(); });

  area.addEventListener('keydown', (e) => {
    const porCtrl = cfg().enviar_com === 'ctrl_enter';
    if (e.key === 'Enter' && !e.isComposing && ((porCtrl && (e.ctrlKey || e.metaKey)) || (!porCtrl && !e.shiftKey && !e.ctrlKey))) {
      e.preventDefault();
      enviar();
    }
    if (e.key === 'Escape' && rodando) aoParar?.();
  });

  botaoEnviar.addEventListener('click', () => (rodando ? aoParar?.() : enviar()));

  // comandos que o próprio app resolve, sem ir para o Claude
  async function comandoDoApp(texto) {
    const m = /^\/([\w-]+)(?:\s+(.*))?$/s.exec(texto);
    if (!m) return false;
    const [, nome, args = ''] = m;
    const limpar = () => { area.value = ''; ajustarAltura(); };
    if (nome === 'novo') { location.hash = modo === 'code' ? '#/code' : '#/novo'; limpar(); return true; }
    if (nome === 'modelo') {
      const alvo = ALIAS_MODELO[args.trim().toLowerCase()] || (estado.info?.modelos || []).find((x) => x.nome.toLowerCase() === args.trim().toLowerCase())?.id;
      if (!alvo) { aviso(t('Use /modelo opus, sonnet, haiku ou fable.'), 'erro'); return true; }
      op.modelo = alvo; desenharChips(); limpar(); aviso(t('Modelo: {nome}.', { nome: modeloInfo(alvo).nome })); return true;
    }
    if (nome === 'esforco' || nome === 'esforço') {
      const alvo = ALIAS_ESFORCO[args.trim().toLowerCase()];
      if (!alvo) { aviso(t('Use /esforco baixo, medio, alto, muito-alto ou maximo.'), 'erro'); return true; }
      op.esforco = alvo; desenharChips(); limpar(); return true;
    }
    if (nome === 'plano') {
      if (modo !== 'code') { aviso(t('O modo Plano é do modo Code.'), 'erro'); return true; }
      op.permissao = 'plano'; desenharChips(); limpar();
      aviso(t('Modo Plano: o Claude investiga e mostra o plano antes de mudar qualquer coisa.'));
      return true;
    }
    const paginas = { memoria: '#/config/memoria', permissoes: '#/permissoes', plugins: '#/plugins' };
    if (paginas[nome]) { location.hash = paginas[nome]; limpar(); return true; }
    if (['custo', 'ajuda'].includes(nome) && aoComandoApp) { limpar(); return aoComandoApp(nome, args); }
    return false;
  }

  async function enviar() {
    if (rodando) return;
    const texto = area.value.trim();
    if (!texto && !anexos.length) return;
    if (!anexos.length && await comandoDoApp(texto)) return;
    const lista = anexos.slice();
    const ok = await aoEnviar?.(texto, lista, { ...op });
    if (ok !== false) {
      area.value = '';
      anexos = [];
      desenharAnexos();
      ajustarAltura();
    }
  }

  async function carregarComandos() {
    if (comandos) return comandos;
    try {
      const q = pasta ? `?pasta=${encodeURIComponent(pasta)}` : '';
      comandos = (await api(`/comandos${q}`)).comandos;
    } catch {
      comandos = skills.map((s) => ({ nome: s.nome, descricao: s.descricao, tipo: 'skill' }));
    }
    return comandos;
  }

  async function sugerirComandos() {
    const m = /^\/([\w.:-]*)( ([\w-]*))?$/.exec(area.value);
    if (!m) return;
    const lista = await carregarComandos();
    let filtrados;
    if (m[2] !== undefined) {
      if (m[1] !== 'fluxo') return;  // "/fluxo " mostra os fluxos prontos
      filtrados = lista.filter((c) => c.tipo === 'fluxo' && c.nome.slice(6).startsWith(m[3] || ''));
    } else {
      filtrados = lista.filter((c) => c.tipo !== 'fluxo' && c.nome.toLowerCase().includes(m[1].toLowerCase()))
        .sort((a, b) => (b.nome.startsWith(m[1]) - a.nome.startsWith(m[1])));
    }
    if (modo !== 'code') filtrados = filtrados.filter((c) => c.nome !== 'plano');
    const itens = [];
    let tipoAtual = null;
    for (const c of filtrados.slice(0, 14)) {
      if (c.tipo !== tipoAtual) { tipoAtual = c.tipo; itens.push({ titulo: ROTULO_TIPO()[c.tipo] || c.tipo }); }
      itens.push({ texto: '/' + c.nome + (c.argumentos ? ` ${c.argumentos}` : ''), sub: (c.descricao || '').slice(0, 120),
        acao: () => { area.value = `/${c.nome} `; area.focus(); ajustarAltura(); if (c.nome === 'fluxo') sugerirComandos(); } });
    }
    if (itens.length) menu(area, itens, { acima: true });
  }

  desenharChips();
  ajustarAltura();

  return {
    elemento,
    focar() { area.focus(); },
    definirTexto(texto) { area.value = texto; ajustarAltura(); area.focus(); },
    opcoes: () => ({ ...op }),
    definirRodando(sim) {
      rodando = sim;
      botaoEnviar.classList.toggle('parar', sim);
      botaoEnviar.innerHTML = ic(sim ? 'parar' : 'enviar');
      botaoEnviar.title = sim ? t('Parar (Esc)') : t('Enviar');
      botaoEnviar.setAttribute('aria-label', botaoEnviar.title);
      ajustarAltura();
    },
    definirContexto(usado, limite = 1_000_000) {
      const pct = limite ? Math.min(100, (usado / limite) * 100) : 0;
      reguaNivel.style.width = `${Math.max(pct, usado ? 0.6 : 0)}%`;
      reguaNivel.classList.toggle('alto', pct > 60);
      reguaTexto.textContent = usado ? t('{usado} de {limite} tokens', { usado: tokens(usado), limite: tokens(limite) }) : t('conversa nova');
    },
    definirCusto(v) { custoTexto.textContent = v ? usd(v) : ''; if (!cfg().mostrar_custo) custoTexto.textContent = ''; },
    definirSkills(lista) { skills = lista || []; comandos = null; },
    definirPermissao(p) { op.permissao = p; desenharChips(); },
  };
}

export function cartaoAnexo(a, aoTirar) {
  const imagem = a.tipo?.startsWith('image/');
  const ext = (a.nome || '').split('.').pop().slice(0, 4);
  return el('span', { class: 'anexo-cartao', title: a.nome },
    imagem ? el('img', { src: a.url || `/api/anexos/${a.id}`, alt: '' }) : el('span', { class: 'icone-arq', texto: a.tipo === 'application/pdf' ? 'pdf' : ext || t('arq') }),
    el('span', { class: 'nome', texto: a.nome }),
    aoTirar ? el('button', { class: 'tirar', type: 'button', 'aria-label': t('Tirar {nome}', { nome: a.nome }), html: ic('x'), onclick: aoTirar }) : null);
}
