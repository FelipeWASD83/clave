// A tela de uma conversa (chat ou Code): histórico, resposta chegando ao vivo, aprovações e versões.
import { api, acompanhar } from './api.js';
import { estado, cfg, avisar, atualizarOrcamento, modeloInfo, ouvir, carregarEstado } from './estado.js';
import { ic } from './icones.js';
import { el, aviso, copiarTexto, menu, usd, confirmar } from './ui.js';
import { criarCompositor, opcoesPadrao, cartaoAnexo } from './compositor.js';
import { renderizar } from './markdown.js';
import {
  renderizarTurno, renderizarBloco, blocoTexto, blocoPensamento, blocoFerramenta, blocoServidor,
  preencherResultadoServidor, nota, divisorCompactacao, descreverFerramenta, htmlDiff,
} from './blocos.js';
import { abrirPrevia } from './previa.js';
import { painelUso, painelAmbientes } from './painel-uso.js';
import { menuConversa } from './lateral.js';
import { pegarRascunho } from './aprender.js';
import { cartaoAprovacao, cartaoPropostaFluxo, cartaoPlano, cartaoSugestao, FluxoVivo, notificar } from './fluxo-ui.js';

function saudacao() {
  const h = new Date().getHours();
  return h >= 5 && h < 12 ? 'Bom dia' : h >= 12 && h < 18 ? 'Boa tarde' : 'Boa noite';
}

const SUGESTOES_CHAT = [
  'Explique o que é uma API como se eu tivesse 12 anos',
  'Me ajude a escrever um e-mail educado pedindo um prazo maior',
  'Crie uma página HTML de um cartão de aniversário animado',
  'Monte uma tabela comparando 3 formas de organizar meus estudos',
];
const SUGESTOES_CODE = [
  'Explique o que tem nesta pasta, em linguagem simples',
  'Organize os arquivos desta pasta em subpastas por tipo (me mostre o plano antes)',
  'Crie um script que renomeia as fotos desta pasta pela data em que foram tiradas',
  'Crie uma página HTML simples com uma lista de tarefas que salva no navegador',
];

export async function novaConversa(principal, { modo = 'chat', projeto = null } = {}) {
  estado.conversaAtual = null;
  const t = new TelaConversa(principal, { modo, projetoId: projeto });
  await t.montarNova();
  return t;
}

export async function abrirConversa(principal, id) {
  estado.conversaAtual = id;
  const t = new TelaConversa(principal, { id });
  await t.montarExistente();
  return t;
}

class TelaConversa {
  constructor(principal, { id = null, modo = 'chat', projetoId = null }) {
    this.principal = principal;
    this.id = id;
    this.modo = modo;
    this.projetoId = projetoId;
    this.pasta = null;
    this.skills = [];
    this.visao = null;
    this.vivo = null;
    this.desligar = [];
  }

  sair() {
    this.vivo?.parar();
    this.desligar.forEach((f) => f());
  }

  // ---------- conversa nova ----------
  async montarNova() {
    this.topo = el('header', { class: 'topo' });
    this.centro = el('div', { class: 'inicio' });
    this.principal.replaceChildren(el('section', { class: 'conversa' }, this.topo, this.centro));
    const projeto = this.projetoId ? await api(`/projetos/${this.projetoId}`).then((r) => r.projeto).catch(() => null) : null;
    this.desenharTopo(this.modo === 'code' ? 'Novo trabalho no Code' : (projeto ? `Nova conversa em ${projeto.nome}` : 'Nova conversa'));
    if (this.modo === 'code') {
      // como no app oficial: começa no último ambiente usado (dá para trocar no painel de ambientes);
      // a lista de pastas recentes muda no servidor a cada trabalho novo, então vem atualizada
      await carregarEstado().catch(() => {});
      const ultima = (cfg().pastas_recentes || [])[0];
      if (ultima && await this.carregarPasta(ultima, { silencioso: true })) return this.desenharInicio();
    }
    this.desenharInicio(projeto);
  }

  async carregarPasta(caminho, { silencioso = false } = {}) {
    if (!caminho) return false;
    try {
      const info = await api(`/pasta-info?caminho=${encodeURIComponent(caminho)}`);
      this.pasta = caminho;
      this.infoPasta = info;
      this.skills = info.skills || [];
      return true;
    } catch (e) {
      if (!silencioso) aviso(e.message, 'erro');
      return false;
    }
  }

  desenharInicio(projeto = null) {
    const nome = cfg().nome ? `, ${cfg().nome.split(' ')[0]}` : '';
    const anterior = this.comp;
    const textoAntes = anterior ? this.centro.querySelector('textarea')?.value : '';
    const permAntes = anterior?.opcoes().permissao;
    const comp = this.criarCompositor();
    if (permAntes) comp.definirPermissao(permAntes);
    const sugestoes = el('div', { class: 'sugestoes' }, ...(this.modo === 'code' ? SUGESTOES_CODE : SUGESTOES_CHAT).map((s) =>
      el('button', { class: 'sugestao', type: 'button', texto: s, onclick: () => comp.definirTexto(s) })));
    const frase = this.modo === 'code' ? 'O que vamos construir?' : (projeto ? `Projeto: ${projeto.nome}` : 'Em que posso ajudar?');
    const ambientes = this.modo === 'code' ? painelAmbientes({
      atual: this.pasta,
      aoEscolher: async (c) => { if (await this.carregarPasta(c)) this.desenharInicio(); },
      auto: comp.opcoes().permissao === 'livre',
      aoAuto: (ligado) => {
        if (ligado) this.permSemAuto = comp.opcoes().permissao;
        comp.definirPermissao(ligado ? 'livre' : (this.permSemAuto && this.permSemAuto !== 'livre' ? this.permSemAuto : 'perguntar'));
        this.desenharInicio();
      },
    }) : null;
    this.centro.replaceChildren(el('div', { class: 'coluna' },
      el('h1', { class: 'saudacao' }, `${saudacao()}${nome}.`, el('br'), el('em', { texto: frase })),
      this.modo === 'code' ? this.chipsDaPasta() : null,
      comp.elemento,
      sugestoes,
      !estado.info.tem_chave ? nota('Falta colar a sua chave da API para o Claude responder.', 'info',
        el('a', { class: 'botao pequeno', href: '#/config/conta', texto: 'Colar a chave' })) : null,
      el('div', { class: 'paineis-inicio' }, painelUso(), ambientes),
      this.modo === 'code' && !(cfg().pastas_recentes || []).length ? el('p', { class: 'ajuda', style: 'text-align:center' }, 'Primeira vez? Veja ',
        el('a', { href: '#/aprender/modo-code', texto: 'como o modo Code funciona' }), '.') : null));
    comp.definirContexto(0);
    const rascunho = textoAntes || pegarRascunho();
    if (rascunho) comp.definirTexto(rascunho);
    comp.focar();
  }

  chipsDaPasta() {
    if (!this.pasta) return el('div', { class: 'contexto-code' }, el('span', { class: 'etiqueta', html: `${ic('pasta')}` }, 'nenhum ambiente escolhido: escolha embaixo'));
    const inst = this.infoPasta?.instrucoes || [];
    return el('div', { class: 'contexto-code' },
      el('span', { class: 'etiqueta', title: this.pasta, html: `${ic('pasta')}` }, this.pasta.length > 48 ? '…' + this.pasta.slice(-46) : this.pasta),
      inst.length ? el('span', { class: 'etiqueta acao', title: inst.map((i) => i.caminho).join('\n'), texto: `${inst.length} arquivo(s) de regras (CLAUDE.md)` }) : el('span', { class: 'etiqueta', texto: 'sem CLAUDE.md' }),
      el('span', { class: 'etiqueta', title: this.skills.map((s) => s.nome).join(', '), texto: `${this.skills.length} skill(s)` }));
  }

  // ---------- conversa existente ----------
  async montarExistente() {
    this.visao = await api(`/conversas/${this.id}`);
    this.modo = this.visao.conversa.modo;
    this.pasta = this.visao.conversa.pasta;
    this.topo = el('header', { class: 'topo' });
    this.mensagensEl = el('div', { class: 'mensagens' });
    this.rolagem = el('div', { class: 'rolagem' }, el('div', { class: 'coluna' }, this.mensagensEl));
    this.tarefasEl = el('div', { class: 'tarefas', hidden: true });
    this.comp = this.criarCompositor();
    this.comp.elemento.querySelector('.coluna').prepend(this.tarefasEl);
    this.principal.replaceChildren(el('section', { class: 'conversa' }, this.topo, this.rolagem, this.comp.elemento));
    this.mensagensEl.addEventListener('click', (e) => this.cliqueNasMensagens(e));
    this.desenharTopo(this.visao.conversa.titulo || 'Nova conversa');
    this.desenharMensagens();
    this.rolarParaBaixo(false);
    if (this.modo === 'code' && this.pasta) {
      api(`/pasta-info?caminho=${encodeURIComponent(this.pasta)}`).then((i) => { this.skills = i.skills || []; this.comp.definirSkills(this.skills); }).catch(() => {});
    }
    if (this.visao.execucao) this.acompanhar(this.visao.execucao, this.visao.execucao_desde || 0);
    this.desligar.push(ouvir('titulo', ({ id, titulo }) => { if (id === this.id) this.desenharTopo(titulo); }));
    this.comp.focar();
  }

  async recarregar() {
    this.visao = await api(`/conversas/${this.id}`);
    this.desenharTopo(this.visao.conversa.titulo || 'Nova conversa');
    this.desenharMensagens();
  }

  desenharTopo(titulo) {
    const h1 = el('h1', { class: 'titulo-editavel', texto: titulo, title: this.id ? 'Clique para renomear' : '' });
    if (this.id) h1.addEventListener('click', async () => {
      const { perguntarTexto } = await import('./ui.js');
      const novo = await perguntarTexto('Renomear conversa', { valor: this.visao?.conversa?.titulo || '' });
      if (novo) { await api(`/conversas/${this.id}`, { metodo: 'PATCH', corpo: { titulo: novo } }); h1.textContent = novo; avisar('conversas-mudaram'); }
    });
    const extras = [];
    if (this.modo === 'code' && this.pasta) {
      extras.push(el('button', { class: 'chip', type: 'button', title: window.clave?.abrirPasta ? 'Abrir a pasta no Explorador' : this.pasta, html: `${ic('pasta')}<span>${this.pasta.split(/[\\/]/).pop()}</span>`,
        onclick: () => window.clave?.abrirPasta ? window.clave.abrirPasta(this.pasta) : aviso(this.pasta) }));
    }
    if (this.visao?.projeto) extras.push(el('a', { class: 'chip', href: `#/projetos/${this.visao.projeto.id}`, html: `${ic('camadas')}<span>${this.visao.projeto.nome}</span>` }));
    if (this.id && cfg().mostrar_custo && this.visao) extras.push(el('span', { class: 'meta', title: 'Gasto total desta conversa', texto: usd(this.visao.gasto) }));
    const mais = this.id ? el('button', { class: 'icone-botao', type: 'button', 'aria-label': 'Opções da conversa', html: ic('pontos'),
      onclick: (e) => menuConversa(e.currentTarget, { ...this.visao.conversa }) }) : null;
    this.topo.replaceChildren(
      el('button', { class: 'icone-botao abrir-lateral', type: 'button', 'aria-label': 'Abrir a barra lateral', html: ic('menu'),
        onclick: () => import('./lateral.js').then((m) => m.alternarLateral()) }),
      h1, ...extras, ...(mais ? [mais] : []));
  }

  criarCompositor() {
    const ajustes = this.visao?.conversa?.ajustes || {};
    const comp = criarCompositor({
      modo: this.modo,
      opcoes: opcoesPadrao(this.modo, ajustes),
      skills: this.skills,
      pasta: this.pasta,
      aoEnviar: (texto, anexos, op) => this.enviar(texto, anexos, op),
      aoParar: () => this.parar(),
      aoComandoApp: (nome, args) => this.comandoApp(nome, args),
    });
    this.comp = comp;
    return comp;
  }

  // ---------- enviar e acompanhar ----------
  async enviar(texto, anexos, op, editarDe = null) {
    try {
      if (!this.id) {
        const corpo = { modo: this.modo, projeto_id: this.projetoId, pasta: this.pasta };
        if (this.modo === 'code' && !this.pasta) { aviso('Escolha o ambiente (a pasta de trabalho) no painel embaixo primeiro.', 'erro'); return false; }
        const { conversa } = await api('/conversas', { metodo: 'POST', corpo });
        await api(`/conversas/${conversa.id}/enviar`, { metodo: 'POST', corpo: { texto, anexos: anexos.map((a) => a.id), opcoes: op } });
        avisar('conversas-mudaram');
        location.hash = `#/c/${conversa.id}`;
        return true;
      }
      const r = await api(`/conversas/${this.id}/enviar`, { metodo: 'POST', corpo: { texto, anexos: anexos.map((a) => a.id), opcoes: op, editar_de: editarDe } });
      await this.recarregar();
      this.acompanhar(r.execucao, 0);
      this.rolarParaBaixo();
      return true;
    } catch (e) {
      aviso(e.message, 'erro');
      if (e.status === 402) atualizarOrcamentoDoServidor();
      return false;
    }
  }

  // comandos de barra do próprio app (/custo, /ajuda...); os outros vão para o servidor
  async comandoApp(nome) {
    if (nome === 'custo') {
      try {
        const u = await api('/uso');
        const conv = this.id ? `Esta conversa: ${usd(this.visao?.gasto || 0)}. ` : '';
        aviso(`${conv}Este mês: ${usd(u.orcamento.gasto)} de ${usd(u.orcamento.teto)}.`);
      } catch (e) { aviso(e.message, 'erro'); }
      return true;
    }
    if (nome === 'ajuda') {
      const { janela } = await import('./ui.js');
      const q = this.pasta ? `?pasta=${encodeURIComponent(this.pasta)}` : '';
      const { comandos } = await api(`/comandos${q}`);
      const grupos = { app: 'Do Clave', comando: 'Comandos', skill: 'Skills', fluxo: 'Fluxos' };
      janela({ titulo: 'Comandos de barra', larga: true, corpo: el('div', { class: 'lista-comandos' },
        el('p', { class: 'ajuda', texto: 'Digite / na caixa de mensagem para ver e escolher. Comandos e skills seus ficam em .claude/commands e .claude/skills (formato do Claude Code).' }),
        ...Object.entries(grupos).map(([tipo, titulo]) => {
          const itens = comandos.filter((c) => c.tipo === tipo);
          return itens.length ? el('div', {}, el('div', { class: 'secao-titulo', texto: titulo }),
            ...itens.map((c) => el('div', { class: 'item-comando' }, el('code', { texto: '/' + c.nome + (c.argumentos ? ' ' + c.argumentos : '') }), el('span', { texto: c.descricao })))) : null;
        })), botoes: [{ texto: 'Fechar', classe: 'primario' }] });
      return true;
    }
    return false;
  }

  async regenerar(mensagemId, op) {
    try {
      const r = await api(`/conversas/${this.id}/regenerar`, { metodo: 'POST', corpo: { mensagem_id: mensagemId, opcoes: op || this.comp.opcoes() } });
      await this.recarregar();
      this.acompanhar(r.execucao, 0);
      this.rolarParaBaixo();
    } catch (e) { aviso(e.message, 'erro'); }
  }

  async parar() {
    if (this.execucaoId) await api(`/execucoes/${this.execucaoId}/parar`, { metodo: 'POST' }).catch(() => {});
  }

  acompanhar(execucaoId, desde) {
    this.vivo?.parar();
    this.execucaoId = execucaoId;
    estado.rodando.set(this.id, execucaoId);
    avisar('rodando');
    this.comp.definirRodando(true);
    const grupo = this.grupoParaContinuar();
    this.vivo = new Vivo(this, grupo, execucaoId, desde);
    // as das etapas de fluxo voltam junto com os eventos do fluxo
    for (const ev of this.visao?.aprovacoes_pendentes || []) if (!ev.de_etapa) this.vivo.pedido(ev);
    if (this.visao?.tarefas?.length) this.desenharTarefas(this.visao.tarefas);
  }

  grupoParaContinuar() {
    const ultimo = this.mensagensEl.lastElementChild;
    if (ultimo?.classList.contains('msg-claude')) return ultimo.querySelector('.blocos') || ultimo;
    const blocos = el('div', { class: 'blocos', style: 'display:grid;gap:12px' });
    const g = el('div', { class: 'msg-claude' }, blocos);
    this.mensagensEl.append(g);
    return blocos;
  }

  async terminou(ev) {
    estado.rodando.delete(this.id);
    avisar('rodando');
    this.comp.definirRodando(false);
    this.vivo = null;
    const estavaNoFim = this.pertoDoFim();
    await this.recarregar().catch(() => {});
    if (estavaNoFim) this.rolarParaBaixo(false);
    avisar('conversas-mudaram');
    setTimeout(() => avisar('conversas-mudaram'), 2500);
    if (ev.status === 'parada' && !ev.pediu_ok) aviso('Resposta interrompida.');
    if (ev.status === 'concluida') notificar('Clave', 'O Claude terminou de responder.');
  }

  desenharTarefas(lista) {
    if (!this.tarefasEl) return;
    this.tarefasEl.hidden = !lista?.length;
    const icone = { pendente: 'circulo', fazendo: 'progresso', feito: 'feito' };
    this.tarefasEl.replaceChildren(...(lista || []).map((t) =>
      el('div', { class: `t ${t.estado}` }, el('span', { html: ic(icone[t.estado] || 'circulo') }), el('span', { texto: t.texto }))));
  }

  // ---------- histórico ----------
  desenharMensagens() {
    const msgs = this.visao.mensagens || [];
    const turnos = [];
    for (const m of msgs) {
      if (m.papel === 'user' && m.tipo === 'normal') turnos.push({ usuario: m, respostas: [] });
      else if (turnos.length) turnos[turnos.length - 1].respostas.push(m);
    }
    const filhos = [];
    turnos.forEach((t, i) => {
      filhos.push(this.elementoUsuario(t.usuario));
      if (t.respostas.length) filhos.push(this.elementoTurno(t, i === turnos.length - 1));
      const meta = t.usuario.meta || {};
      if (meta.erro && !t.respostas.some((r) => r.papel === 'assistant')) {
        filhos.push(nota(meta.erro, 'erro', el('button', { class: 'botao pequeno', type: 'button', texto: 'Tentar de novo', onclick: () => this.regenerar(t.usuario.id) })));
      }
      if (meta.recusa && !t.respostas.length) filhos.push(nota('O Claude recusou este pedido pelas regras de segurança da Anthropic. Reformule ou tente outro modelo.'));
    });
    if (!turnos.length) filhos.push(el('div', { class: 'vazio', texto: 'Conversa vazia.' }));
    this.mensagensEl.replaceChildren(...filhos);
    // régua de contexto e custo
    const ultimaResp = [...msgs].reverse().find((m) => m.papel === 'assistant' && m.uso);
    this.comp.definirContexto(ultimaResp ? contextoDe(ultimaResp.uso) : 0, 1_000_000);
    this.comp.definirCusto(this.visao.gasto);
  }

  elementoUsuario(m) {
    const meta = m.meta || {};
    const blocos = Array.isArray(m.conteudo) ? m.conteudo : [{ type: 'text', text: String(m.conteudo || '') }];
    const anexos = blocos.filter((b) => b.type === 'clave_anexo');
    const texto = meta.exibir || blocos.filter((b) => b.type === 'text' && !String(b.text).startsWith('<modo-do-clave>')).map((b) => b.text).join('\n\n');
    const balao = el('div', { class: 'balao' });
    const cmd = meta.comando || meta.skill;
    if (cmd) balao.append(el('span', { class: 'skill-chamada', texto: `/${cmd} ` }), texto.replace(/^\/\S+\s*/, ''));
    else balao.textContent = texto;
    const irmaos = m.irmaos || [m.id];
    const acoes = el('div', { class: 'acoes-msg' },
      this.navVersoes(irmaos, m.id),
      el('button', { class: 'icone-botao', type: 'button', title: 'Editar e reenviar', 'aria-label': 'Editar', html: ic('lapis'), onclick: () => this.editar(caixa, m, texto) }),
      el('button', { class: 'icone-botao', type: 'button', title: 'Copiar', 'aria-label': 'Copiar', html: ic('copiar'), onclick: (e) => copiarTexto(texto, e.currentTarget) }));
    const caixa = el('div', { class: 'msg-usuario', dados: { id: m.id } },
      anexos.length ? el('div', { class: 'anexos-msg' }, ...anexos.map((a) => a.tipo?.startsWith('image/')
        ? el('img', { class: 'imagem-grande', src: `/api/anexos/${a.id}`, alt: a.nome, loading: 'lazy' })
        : cartaoAnexo({ ...a, tipo: a.tipo }))) : null,
      texto ? balao : null, acoes);
    return caixa;
  }

  editar(caixa, m, textoAtual) {
    const area = el('textarea', { class: 'area', style: 'width:min(640px,100%)' });
    area.value = textoAtual;
    const anexos = (Array.isArray(m.conteudo) ? m.conteudo : []).filter((b) => b.type === 'clave_anexo').map((b) => ({ id: b.id, nome: b.nome, tipo: b.tipo }));
    const editor = el('div', { style: 'display:grid;gap:8px;justify-items:end;width:100%' }, area,
      el('div', { style: 'display:flex;gap:8px' },
        el('button', { class: 'botao pequeno', type: 'button', texto: 'Cancelar', onclick: () => this.desenharMensagens() }),
        el('button', { class: 'botao pequeno primario', type: 'button', texto: 'Enviar', onclick: () => {
          if (!area.value.trim()) return;
          this.enviar(area.value.trim(), anexos, this.comp.opcoes(), m.id);
        } })),
      el('small', { class: 'ajuda', texto: 'Enviar cria uma nova versão a partir daqui; a anterior continua guardada (setas < >).' }));
    caixa.replaceChildren(editor);
    area.focus();
  }

  navVersoes(irmaos, atual) {
    if (!irmaos || irmaos.length < 2) return null;
    const i = irmaos.indexOf(atual);
    const ir = async (alvo) => {
      try { this.visao = await api(`/conversas/${this.id}/folha`, { metodo: 'POST', corpo: { mensagem_id: alvo } }); this.desenharMensagens(); }
      catch (e) { aviso(e.message, 'erro'); }
    };
    return el('span', { class: 'versoes' },
      el('button', { class: 'icone-botao', type: 'button', 'aria-label': 'Versão anterior', html: ic('esq'), disabled: i <= 0, onclick: () => ir(irmaos[i - 1]) }),
      `${i + 1}/${irmaos.length}`,
      el('button', { class: 'icone-botao', type: 'button', 'aria-label': 'Próxima versão', html: ic('dir'), disabled: i >= irmaos.length - 1, onclick: () => ir(irmaos[i + 1]) }));
  }

  elementoTurno(t, ultimo) {
    const blocos = el('div', { class: 'blocos', style: 'display:grid;gap:12px' });
    renderizarTurno(blocos, t.respostas);
    const assistentes = t.respostas.filter((r) => r.papel === 'assistant');
    const primeira = assistentes[0];
    const ultima = assistentes[assistentes.length - 1];
    const custoTurno = assistentes.reduce((s, r) => s + (r.custo_usd || 0), 0);
    const texto = assistentes.flatMap((r) => (Array.isArray(r.conteudo) ? r.conteudo : [])).filter((b) => b.type === 'text').map((b) => b.text).join('\n\n');
    const mudouArquivos = assistentes.some((r) => (r.conteudo || []).some?.((b) => b.type === 'tool_use' && ['escrever_arquivo', 'editar_arquivo', 'excel_alterar', 'excel_no_app'].includes(b.name)));
    const execId = ultima?.execucao_id;
    const notas = [];
    for (const r of assistentes) {
      const meta = r.meta || {};
      if (meta.recusa) notas.push(nota('O Claude recusou parte deste pedido pelas regras de segurança da Anthropic.'));
      if (meta.respondido_por) notas.push(nota(`Respondido pelo ${modeloInfo(meta.respondido_por).nome}, porque o modelo escolhido recusou o pedido.`, 'info'));
      if (meta.stop === 'max_tokens') notas.push(nota('A resposta chegou ao tamanho máximo e foi cortada. Mande "continue".'));
    }
    const nomeModelo = ultima?.modelo ? modeloInfo(ultima.modelo).nome : '';
    const acoes = el('div', { class: 'acoes-msg' },
      primeira ? this.navVersoes(primeira.irmaos, primeira.id) : null,
      el('button', { class: 'icone-botao', type: 'button', title: 'Copiar resposta', 'aria-label': 'Copiar resposta', html: ic('copiar'), onclick: (e) => copiarTexto(texto, e.currentTarget) }),
      el('button', { class: 'icone-botao', type: 'button', title: 'Gerar outra resposta', 'aria-label': 'Gerar outra resposta', html: ic('refazer'), onclick: (e) => this.menuRegenerar(e.currentTarget, t.usuario.id) }),
      mudouArquivos && execId ? el('button', { class: 'botao pequeno fantasma', type: 'button', html: `${ic('desfazer')}Desfazer mudanças`, onclick: () => this.desfazer(execId) }) : null,
      el('span', { class: 'meta', texto: [nomeModelo, cfg().mostrar_custo && custoTurno ? usd(custoTurno) : ''].filter(Boolean).join(' · ') }));
    const meta = (ultima?.meta || {});
    return el('div', { class: 'msg-claude', dados: { turno: t.usuario.id } }, blocos, ...notas,
      meta.interrompida ? nota('Resposta interrompida.', 'info') : null,
      acoes);
  }

  menuRegenerar(ancora, usuarioId) {
    const itens = [{ texto: 'Tentar de novo', sub: 'Com o modelo e o raciocínio escolhidos embaixo', icone: 'refazer', acao: () => this.regenerar(usuarioId) }, '-', { titulo: 'Com outro modelo' }];
    for (const m of estado.info?.modelos || []) itens.push({ texto: m.nome, sub: m.resumo, acao: () => this.regenerar(usuarioId, { ...this.comp.opcoes(), modelo: m.id }) });
    menu(ancora, itens, { acima: true });
  }

  async desfazer(execId) {
    if (!await confirmar('Voltar os arquivos que esta resposta criou ou mudou para como estavam antes dela?', { titulo: 'Desfazer mudanças', sim: 'Desfazer' })) return;
    try {
      const r = await api(`/execucoes/${execId}/desfazer`, { metodo: 'POST' });
      aviso(r.arquivos.length ? `${r.arquivos.length} arquivo(s) voltaram ao que eram.` : 'Nada para desfazer (já tinha sido desfeito).');
    } catch (e) { aviso(e.message, 'erro'); }
  }

  cliqueNasMensagens(e) {
    const b = e.target.closest('button[data-acao]');
    if (!b) return;
    const bloco = b.closest('.bloco-codigo');
    const codigo = bloco?.querySelector('pre code')?.textContent || '';
    if (b.dataset.acao === 'copiar-codigo') copiarTexto(codigo, b);
    if (b.dataset.acao === 'previa') abrirPrevia({ codigo, lingua: bloco.dataset.lingua });
  }

  pertoDoFim() {
    const r = this.rolagem;
    return !r || r.scrollHeight - r.scrollTop - r.clientHeight < 140;
  }

  rolarParaBaixo(suave = true) {
    if (!this.rolagem) return;
    this.rolagem.style.scrollBehavior = suave ? 'smooth' : 'auto';
    this.rolagem.scrollTop = this.rolagem.scrollHeight;
  }
}

function contextoDe(uso) {
  const it = (uso.iterations && uso.iterations.length) ? uso.iterations[uso.iterations.length - 1] : uso;
  return (it.input_tokens || 0) + (it.cache_read_input_tokens || 0) + (it.cache_creation_input_tokens || 0) + (uso.output_tokens || 0);
}

async function atualizarOrcamentoDoServidor() {
  try { const r = await api('/uso'); atualizarOrcamento(r.orcamento); } catch { /* sem efeito */ }
}

// ---------- resposta ao vivo ----------
class Vivo {
  constructor(tela, alvo, execucaoId, desde) {
    this.tela = tela;
    this.alvo = alvo;
    this.chamada = 0;
    this.blocos = new Map();   // "chamada:indice" -> {tipo, el, texto}
    this.ferramentas = new Map(); // tool_use_id -> elemento
    this.indicador = null;
    this.agendado = new Set();
    this.fluxos = new Map();      // fluxo -> FluxoVivo
    this.conexao = acompanhar(execucaoId, (ev) => this.evento(ev));
  }

  parar() { this.conexao?.parar(); }

  chave(i) { return `${this.chamada}:${i}`; }

  mostrarIndicador() {
    if (this.indicador) return;
    this.indicador = blocoPensamento('', { ativo: true });
    this.indicador.querySelector('summary').style.cursor = 'default';
    this.alvo.append(this.indicador);
  }

  tirarIndicador() { this.indicador?.remove(); this.indicador = null; }

  rolar() { if (this.tela.pertoDoFim()) this.tela.rolarParaBaixo(false); }

  pintar(chave) {
    if (this.agendado.has(chave)) return;
    this.agendado.add(chave);
    requestAnimationFrame(() => {
      this.agendado.delete(chave);
      const b = this.blocos.get(chave);
      if (b?.tipo === 'text') { renderizar(b.el, b.texto, { final: false }); this.rolar(); }
    });
  }

  evento(ev) {
    const t = this.tela;
    switch (ev.tipo) {
      case 'chamando':
        this.chamada += 1;
        this.mostrarIndicador();
        break;
      case 'bloco_inicio': {
        const tipo = ev.bloco.type;
        const k = this.chave(ev.indice);
        if (tipo === 'text') {
          this.tirarIndicador();
          const div = el('div', { class: 'resposta' });
          this.alvo.append(div);
          this.blocos.set(k, { tipo, el: div, texto: '' });
        } else if (tipo === 'thinking') {
          const det = blocoPensamento('', { ativo: true, aberto: cfg().mostrar_raciocinio !== false });
          this.blocos.set(k, { tipo, el: det, texto: '' });
        } else if (tipo === 'tool_use') {
          this.tirarIndicador();
          const det = blocoFerramenta({ id: ev.bloco.id, name: ev.bloco.name, input: {} });
          det.classList.add('rodando');
          if (ev.bloco.name !== 'atualizar_tarefas') this.alvo.append(det);
          this.blocos.set(k, { tipo, el: det, texto: '' });
          this.ferramentas.set(ev.bloco.id, det);
        } else if (tipo === 'server_tool_use' || tipo === 'mcp_tool_use') {
          this.tirarIndicador();
          const det = blocoServidor({ ...ev.bloco, input: {} });
          det.classList.add('rodando');
          this.alvo.append(det);
          this.blocos.set(k, { tipo, el: det, texto: '' });
          this.ferramentas.set(ev.bloco.id, det);
        }
        this.rolar();
        break;
      }
      case 'texto': {
        const b = this.blocos.get(this.chave(ev.indice));
        if (b) { b.texto += ev.texto; this.pintar(this.chave(ev.indice)); }
        break;
      }
      case 'pensamento': {
        const b = this.blocos.get(this.chave(ev.indice));
        if (b) {
          if (!b.texto) { this.tirarIndicador(); this.alvo.append(b.el); }
          b.texto += ev.texto;
          b.el._corpo.textContent = b.texto;
          this.rolar();
        }
        break;
      }
      case 'bloco_fim': {
        const k = this.chave(ev.indice);
        const b = this.blocos.get(k);
        const bloco = ev.bloco;
        if (bloco.type === 'text' && b) {
          b.texto = bloco.text || b.texto;
          const novo = blocoTexto(bloco);
          b.el.replaceWith(novo); b.el = novo;
        } else if (bloco.type === 'thinking' && b) {
          b.el.finalizar();
          if (!b.texto.trim()) { b.el.remove(); }
          this.mostrarIndicador();
        } else if (bloco.type === 'tool_use' && b) {
          b.el.definirEntrada(bloco.input || {});
        } else if (bloco.type === 'server_tool_use' || bloco.type === 'mcp_tool_use') {
          b?.el.classList.remove('rodando');
          const det = blocoServidor(bloco);
          b?.el.replaceWith(det);
          if (b) b.el = det;
          this.ferramentas.set(bloco.id, det);
        } else if (['web_search_tool_result', 'web_fetch_tool_result', 'mcp_tool_result'].includes(bloco.type)) {
          const det = this.ferramentas.get(bloco.tool_use_id);
          if (det) { det.classList.remove('rodando'); preencherResultadoServidor(det, bloco); }
        } else if (bloco.type === 'compaction') {
          this.alvo.append(divisorCompactacao());
        }
        this.rolar();
        break;
      }
      case 'aprovacao':
      case 'fluxo_proposta':
      case 'plano_proposto':
        this.tirarIndicador();
        this.pedido(ev);
        break;
      case 'sugestao_conversa': {
        this.tirarIndicador();
        const card = cartaoSugestao(ev, { conversaId: this.tela.id });
        const det = this.achar(ev.id);
        if (det) det.replaceWith(card); else this.alvo.append(card);
        this.rolar();
        break;
      }
      case 'aprovacao_decidida':
        this.tela.mensagensEl.querySelector(`[data-id="${CSS.escape(ev.id)}"]:is(.aprovacao, .fluxo)`)?.remove();
        break;
      case 'fluxo_inicio': {
        this.tirarIndicador();
        this.tirarSalvo(ev.fluxo);
        const f = new FluxoVivo(ev.proposta, { aoParar: () => this.tela.parar() });
        this.fluxos.set(ev.fluxo, f);
        const det = this.achar(ev.fluxo);
        if (det) det.after(f.el); else this.alvo.append(f.el);
        this.rolar();
        break;
      }
      case 'etapa_inicio':
      case 'etapa_evento':
      case 'etapa_fim':
      case 'fluxo_fim':
        this.fluxos.get(ev.fluxo)?.evento(ev);
        if (ev.tipo === 'fluxo_fim') this.mostrarIndicador();
        break;
      case 'modo_mudou':
        t.comp.definirPermissao?.(ev.permissao);
        aviso(`Plano aprovado. Permissão agora: ${{ perguntar: 'Perguntar', aceitar_edicoes: 'Aceitar edições', livre: 'Livre' }[ev.permissao] || ev.permissao}.`);
        break;
      case 'regra_salva':
        aviso(`Regra salva ${ev.escopo === 'pasta' ? 'nesta pasta' : 'no Clave'}: ${ev.regra}`);
        break;
      case 'rotina_parou':
        this.tirarIndicador();
        this.alvo.append(nota(`A rotina parou: precisaria do seu OK para ${ev.motivo || 'uma ação'}${ev.alvo ? ` (${ev.alvo})` : ''}. Para ela fazer isso sozinha, crie uma regra${ev.sugestao ? `, por exemplo ${ev.sugestao}` : ''}.`, '',
          el('a', { class: 'botao pequeno', href: '#/permissoes', texto: 'Abrir permissões' })));
        break;
      case 'ferramenta_rodando': {
        const det = this.achar(ev.id);
        det?.classList.add('rodando');
        break;
      }
      case 'ferramenta_fim': {
        const det = this.achar(ev.id);
        det?.definirResultado?.(ev.resumo, ev.erro);
        det?.classList.remove('rodando');
        this.mostrarIndicador();
        break;
      }
      case 'arquivo_mudou': {
        const dets = [...this.alvo.querySelectorAll('.ferramenta')].filter((d) => ['escrever_arquivo', 'editar_arquivo', 'excel_alterar', 'excel_no_app'].includes(d.dataset.nome));
        dets[dets.length - 1]?.definirDiff?.(ev.diff);
        break;
      }
      case 'tarefas':
        t.desenharTarefas(ev.tarefas);
        break;
      case 'uso':
        t.comp.definirContexto(ev.contexto, 1_000_000);
        atualizarOrcamento(ev.orcamento);
        break;
      case 'alerta_orcamento':
        aviso(ev.porcentagem >= 100 ? 'Você chegou ao teto de gasto deste mês.' : `Você já usou ${ev.porcentagem}% do teto de gasto deste mês.`, ev.porcentagem >= 95 ? 'erro' : '');
        break;
      case 'aviso':
        this.tirarIndicador();
        this.alvo.append(nota(ev.mensagem));
        this.rolar();
        break;
      case 'erro':
        this.tirarIndicador();
        this.alvo.append(nota(ev.mensagem, 'erro', ev.codigo === 'sem_chave'
          ? el('a', { class: 'botao pequeno', href: '#/config/conta', texto: 'Colar a chave' })
          : ev.codigo === 'teto' ? el('a', { class: 'botao pequeno', href: '#/config/limite', texto: 'Ver o teto' }) : null));
        this.rolar();
        break;
      case 'fim':
        this.tirarIndicador();
        t.terminou(ev);
        break;
      default:
        break;
    }
  }

  achar(id) {
    return this.ferramentas.get(id) || this.tela.mensagensEl.querySelector(`.ferramenta[data-tool-id="${CSS.escape(id)}"]`);
  }

  tirarSalvo(fid) {
    const m = this.tela.mensagensEl;
    m.querySelector(`.fluxo.salvo[data-fluxo="${CSS.escape(fid)}"]`)?.remove();
    m.querySelector(`.cartao-carregando[data-tool-id="${CSS.escape(fid)}"]`)?.remove();
  }

  // pedido de decisão: aprovação de ação, proposta de fluxo ou plano pronto
  pedido(ev) {
    const m = this.tela.mensagensEl;
    if (m.querySelector(`[data-id="${CSS.escape(ev.id)}"]:is(.aprovacao, .fluxo)`)) return;
    const execucaoId = ev.execucao || this.tela.execucaoId;
    let card;
    if (ev.tipo === 'fluxo_proposta') { this.tirarSalvo(ev.id); card = cartaoPropostaFluxo(ev, { execucaoId }); }
    else if (ev.tipo === 'plano_proposto') card = cartaoPlano(ev, { execucaoId });
    else card = cartaoAprovacao(ev, { execucaoId, temPasta: this.tela.modo === 'code' });
    const det = this.achar(ev.id);
    if (det) det.after(card); else this.alvo.append(card);
    card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    card.querySelector('button.primario')?.focus({ preventScroll: true });
  }
}

export { renderizarBloco };
