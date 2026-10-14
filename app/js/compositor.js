// A caixa de texto: anexos, escolha de modelo e raciocínio, busca na web, GitHub, permissões e a régua de contexto.
import { enviarArquivo } from './api.js';
import { estado, cfg, modeloInfo } from './estado.js';
import { ic } from './icones.js';
import { el, menu, aviso, escolherArquivos, tokens, usd } from './ui.js';
import { escolherDoGitHub } from './github.js';

const DESC_ESFORCO = {
  low: 'Rápido e barato. Bom para perguntas simples e conversa.',
  medium: 'Equilíbrio entre qualidade e custo.',
  high: 'Pensa mais. Bom para tarefas difíceis e código.',
  xhigh: 'Para problemas complexos. Mais lento e mais caro.',
  max: 'Sem limite de raciocínio. Só quando a qualidade vale o custo.',
};
const PERMISSOES = {
  perguntar: ['Perguntar', 'Lê sozinho; pede seu OK para editar e rodar comandos.'],
  aceitar_edicoes: ['Aceitar edições', 'Edita arquivos sozinho; pede OK para rodar comandos.'],
  plano: ['Plano', 'Só lê e propõe um plano. Não muda nada.'],
  livre: ['Livre', 'Faz tudo sozinho, menos apagar ou publicar, que sempre pedem OK.'],
};

export function opcoesPadrao(modo, ajustes = {}) {
  const c = cfg();
  const base = {
    modelo: modo === 'code' ? c.modelo_code : c.modelo_chat,
    esforco: modo === 'code' ? c.esforco_code : c.esforco_chat,
    pensar: true,
    mostrar_raciocinio: c.mostrar_raciocinio !== false,
    busca_web: !!c.busca_web,
    github: !!c.github_ferramentas && !!c.github_origem,
    rapido: false,
    permissao: c.permissao_code || 'perguntar',
  };
  return { ...base, ...ajustes };
}

export function criarCompositor({ modo = 'chat', opcoes, aoEnviar, aoParar, pasta = null, skills = [], placeholder }) {
  const op = { ...opcoes };
  let anexos = [];  // {id, nome, tipo, url?}
  let rodando = false;

  const area = el('textarea', { rows: 1, placeholder: placeholder || (modo === 'code' ? 'Peça uma tarefa (use / para chamar uma skill)' : 'Escreva para o Claude…'), 'aria-label': 'Mensagem' });
  const pendentes = el('div', { class: 'anexos-pendentes', hidden: true });
  const botaoEnviar = el('button', { class: 'enviar', type: 'button', 'aria-label': 'Enviar', title: 'Enviar', html: ic('enviar') });
  const chipModelo = el('button', { class: 'chip', type: 'button', title: 'Modelo' });
  const chipEsforco = el('button', { class: 'chip', type: 'button', title: 'Raciocínio' });
  const chipWeb = el('button', { class: 'chip', type: 'button', title: 'Deixar o Claude pesquisar na web', html: `${ic('globo')}<span>Web</span>` });
  const chipGit = el('button', { class: 'chip', type: 'button', title: 'Ferramentas do GitHub', html: `${ic('ramo')}<span>GitHub</span>` });
  const chipPerm = el('button', { class: 'chip', type: 'button', title: 'Permissões do modo Code' });
  const chipAnexo = el('button', { class: 'chip', type: 'button', title: 'Anexar arquivo', 'aria-label': 'Anexar arquivo', html: ic('clipe') });
  const reguaNivel = el('div', { class: 'regua-nivel' });
  const reguaTexto = el('span', { class: 'meta', texto: '' });
  const custoTexto = el('span', { class: 'meta', texto: '' });
  const regua = el('div', { class: 'regua', title: 'Quanto da memória do modelo esta conversa já ocupa' },
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
    const nomeEsf = (estado.info?.esforcos || []).find((e) => e.id === op.esforco)?.nome || 'Médio';
    chipEsforco.innerHTML = `${ic('cerebro')}<span>${m.esforco === false ? 'Padrão' : (pensa ? nomeEsf : 'Sem pensar')}</span>${op.rapido && m.rapido ? ic('raio') : ''}${ic('baixo', 'class="seta"')}`;
    chipWeb.classList.toggle('ligado', !!op.busca_web);
    chipWeb.setAttribute('aria-pressed', String(!!op.busca_web));
    chipGit.classList.toggle('ligado', !!op.github);
    chipGit.setAttribute('aria-pressed', String(!!op.github));
    const p = PERMISSOES[op.permissao] || PERMISSOES.perguntar;
    chipPerm.innerHTML = `${ic('escudo')}<span>${p[0]}</span>${ic('baixo', 'class="seta"')}`;
    chipPerm.classList.toggle('ligado', op.permissao === 'livre');
  }

  chipModelo.addEventListener('click', () => {
    const itens = [{ titulo: 'Modelo' }];
    for (const m of estado.info?.modelos || []) {
      itens.push({
        texto: m.nome, marcado: m.id === op.modelo,
        sub: `${m.resumo ? m.resumo + ' ' : ''}US$ ${String(m.entrada).replace('.', ',')} / ${String(m.saida).replace('.', ',')} por milhão de tokens`,
        acao: () => { op.modelo = m.id; if (m.esforco_padrao && !m.esforco === false) { /* mantém o esforço escolhido */ } desenharChips(); },
      });
    }
    menu(chipModelo, itens, { acima: true });
  });

  chipEsforco.addEventListener('click', () => {
    const m = modeloInfo(op.modelo);
    const itens = [];
    if (m.esforco !== false) {
      itens.push({ titulo: 'Quanto ele pensa' });
      for (const e of estado.info?.esforcos || []) {
        const bloqueado = !op.pensar && m.desliga_pensamento && ['xhigh', 'max'].includes(e.id);
        itens.push({ texto: e.nome + (e.id === m.esforco_padrao ? ' (padrão do modelo)' : ''), sub: DESC_ESFORCO[e.id], marcado: e.id === op.esforco, desligado: bloqueado,
          acao: () => { op.esforco = e.id; desenharChips(); } });
      }
      itens.push('-');
    }
    if (m.desliga_pensamento) {
      itens.push({ texto: op.pensar ? '✓ Pensar antes de responder' : 'Pensar antes de responder', sub: 'Desligado, responde mais rápido e gasta menos (até o nível Alto).',
        acao: () => { op.pensar = !op.pensar; if (!op.pensar && ['xhigh', 'max'].includes(op.esforco)) op.esforco = 'high'; desenharChips(); } });
    } else if (m.pensamento_sempre) {
      itens.push({ texto: 'Este modelo sempre pensa', sub: 'O raciocínio não desliga; o nível acima controla quanto.', desligado: true });
    }
    itens.push({ texto: op.mostrar_raciocinio ? '✓ Mostrar o raciocínio' : 'Mostrar o raciocínio', sub: 'Mostra um resumo do que ele pensou. Custa o mesmo.',
      acao: () => { op.mostrar_raciocinio = !op.mostrar_raciocinio; desenharChips(); } });
    if (m.rapido) {
      itens.push({ texto: op.rapido ? '✓ Modo rápido' : 'Modo rápido', sub: 'Até 2,5x mais rápido, pelo dobro do preço.',
        acao: () => { op.rapido = !op.rapido; desenharChips(); } });
    }
    menu(chipEsforco, itens, { acima: true });
  });

  chipWeb.addEventListener('click', () => { op.busca_web = !op.busca_web; desenharChips(); });
  chipGit.addEventListener('click', () => { op.github = !op.github; desenharChips(); });
  chipPerm.addEventListener('click', () => {
    menu(chipPerm, [{ titulo: 'Permissões' }, ...Object.entries(PERMISSOES).map(([id, [nome, sub]]) => ({
      texto: nome, sub, marcado: op.permissao === id, acao: () => { op.permissao = id; desenharChips(); },
    }))], { acima: true });
  });

  chipAnexo.addEventListener('click', () => {
    const itens = [{ texto: 'Arquivo do computador', sub: 'Imagens, PDFs, textos e código', icone: 'arquivo', acao: async () => adicionarArquivos(await escolherArquivos()) }];
    if (estado.info?.github?.origem) itens.push({ texto: 'Arquivos do GitHub', sub: 'De um dos seus repositórios', icone: 'ramo', acao: async () => {
      const novos = await escolherDoGitHub();
      for (const a of novos || []) adicionarAnexo(a);
    } });
    menu(chipAnexo, itens, { acima: true });
  });

  async function adicionarArquivos(lista) {
    for (const f of lista || []) {
      if (f.size > 30 * 1024 * 1024) { aviso(`${f.name}: maior que 30 MB.`, 'erro'); continue; }
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
    if (arquivos.length) { e.preventDefault(); adicionarArquivos(arquivos.map((f, i) => f.name ? f : new File([f], `colado-${i + 1}.png`, { type: f.type }))); }
  });

  function ajustarAltura() {
    area.style.height = 'auto';
    area.style.height = Math.min(area.scrollHeight, innerHeight * 0.4) + 'px';
    botaoEnviar.disabled = !rodando && !area.value.trim() && !anexos.length;
  }
  area.addEventListener('input', () => { ajustarAltura(); sugerirSkills(); });

  area.addEventListener('keydown', (e) => {
    const porCtrl = cfg().enviar_com === 'ctrl_enter';
    if (e.key === 'Enter' && !e.isComposing && ((porCtrl && (e.ctrlKey || e.metaKey)) || (!porCtrl && !e.shiftKey && !e.ctrlKey))) {
      e.preventDefault();
      enviar();
    }
    if (e.key === 'Escape' && rodando) aoParar?.();
  });

  botaoEnviar.addEventListener('click', () => (rodando ? aoParar?.() : enviar()));

  async function enviar() {
    if (rodando) return;
    const texto = area.value.trim();
    if (!texto && !anexos.length) return;
    const lista = anexos.slice();
    const ok = await aoEnviar?.(texto, lista, { ...op });
    if (ok !== false) {
      area.value = '';
      anexos = [];
      desenharAnexos();
      ajustarAltura();
    }
  }

  function sugerirSkills() {
    if (modo !== 'code' || !skills.length) return;
    const m = /^\/([\w.-]*)$/.exec(area.value);
    if (!m) return;
    const itens = skills.filter((s) => s.nome.startsWith(m[1])).slice(0, 10).map((s) => ({
      texto: '/' + s.nome, sub: s.descricao.slice(0, 120), acao: () => { area.value = `/${s.nome} `; area.focus(); ajustarAltura(); },
    }));
    if (itens.length) menu(area, [{ titulo: 'Skills desta pasta' }, ...itens], { acima: true });
  }

  desenharChips();
  ajustarAltura();

  return {
    elemento,
    focar() { area.focus(); },
    definirTexto(t) { area.value = t; ajustarAltura(); area.focus(); },
    opcoes: () => ({ ...op }),
    definirRodando(sim) {
      rodando = sim;
      botaoEnviar.classList.toggle('parar', sim);
      botaoEnviar.innerHTML = ic(sim ? 'parar' : 'enviar');
      botaoEnviar.title = sim ? 'Parar (Esc)' : 'Enviar';
      botaoEnviar.setAttribute('aria-label', botaoEnviar.title);
      ajustarAltura();
    },
    definirContexto(usado, limite = 1_000_000) {
      const pct = limite ? Math.min(100, (usado / limite) * 100) : 0;
      reguaNivel.style.width = `${Math.max(pct, usado ? 0.6 : 0)}%`;
      reguaNivel.classList.toggle('alto', pct > 60);
      reguaTexto.textContent = usado ? `${tokens(usado)} de ${tokens(limite)} tokens` : 'conversa nova';
    },
    definirCusto(v) { custoTexto.textContent = v ? usd(v) : ''; if (!cfg().mostrar_custo) custoTexto.textContent = ''; },
    definirSkills(lista) { skills = lista || []; },
  };
}

export function cartaoAnexo(a, aoTirar) {
  const imagem = a.tipo?.startsWith('image/');
  const ext = (a.nome || '').split('.').pop().slice(0, 4);
  return el('span', { class: 'anexo-cartao', title: a.nome },
    imagem ? el('img', { src: a.url || `/api/anexos/${a.id}`, alt: '' }) : el('span', { class: 'icone-arq', texto: a.tipo === 'application/pdf' ? 'pdf' : ext || 'arq' }),
    el('span', { class: 'nome', texto: a.nome }),
    aoTirar ? el('button', { class: 'tirar', type: 'button', 'aria-label': `Tirar ${a.nome}`, html: ic('x'), onclick: aoTirar }) : null);
}
