// A aba Console do painel (só no modo Code): PowerShells de verdade na pasta da conversa, desenhados pelo xterm.js
// (@xterm/xterm 6.0.0 e @xterm/addon-fit 0.11.0, em app/vendor/xterm, carregados só quando a aba abre pela 1ª vez).
//
// O servidor (servidor/console.py) mantém cada shell num pseudo console do Windows e guarda os últimos ~2 MB da
// saída em pedaços numerados; esta tela lê por SSE a partir do último número que já mostrou, então uma conexão que
// cai volta sem perder nada. Só o console que está na tela fica com a conexão aberta: o navegador abre no máximo 6
// conexões por endereço, e o resto do app precisa delas. Os outros alcançam o que perderam quando aparecem de novo.
import { api } from './api.js';
import { ic } from './icones.js';
import { el, aviso, confirmar } from './ui.js';
import { registrarAba, fecharPainel, ouvirPainel } from './painel.js';
import { t } from './i18n.js';

// borracha (Limpar), no mesmo traço dos ícones de icones.js
const ICONE_LIMPAR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.3 4.6a1.6 1.6 0 0 1 2.3 0l3 3a1.6 1.6 0 0 1 0 2.3L11 18.5H6.8l-2.4-2.4a1.6 1.6 0 0 1 0-2.3z"/><path d="M9.4 9.5l5.3 5.3M11 18.5h9"/></svg>';
const SONDAR_MS = 4000;
const PEDACO_ENTRADA = 32 * 1024;
const LINHAS_PARA_O_CLAUDE = 60;

// ---------- o xterm.js, carregado uma vez ----------
let xterm = null;

function carregarCss() {
  return new Promise((ok) => {
    if (document.querySelector('link[data-xterm]')) { ok(); return; }
    const l = el('link', { rel: 'stylesheet', href: '/vendor/xterm/xterm.css', dados: { xterm: '1' } });
    l.addEventListener('load', ok);
    l.addEventListener('error', ok);
    document.head.append(l);
  });
}

function carregarXterm() {
  if (!xterm) {
    xterm = (async () => {
      const [, a, b] = await Promise.all([carregarCss(), import('../vendor/xterm/xterm.mjs'), import('../vendor/xterm/addon-fit.mjs')]);
      try { await document.fonts.load(`13px ${fonteMono()}`); } catch { /* sem a fonte: o xterm usa a reserva */ }
      return { Terminal: a.Terminal, FitAddon: b.FitAddon };
    })();
    xterm.catch(() => { xterm = null; });  // deixa tentar de novo
  }
  return xterm;
}

// ---------- tema: as cores vêm das variáveis do app (console.css), claro ou escuro ----------
function estiloRaiz() { return getComputedStyle(document.documentElement); }
function fonteMono() { return estiloRaiz().getPropertyValue('--mono').trim() || 'Consolas, monospace'; }

function comAlfa(cor, alfa) {
  const m = /^#([0-9a-f]{6})$/i.exec(cor);
  if (!m) return cor;
  const n = parseInt(m[1], 16);
  return `rgba(${n >> 16}, ${(n >> 8) & 255}, ${n & 255}, ${alfa})`;
}

function temaDoApp() {
  const e = estiloRaiz();
  const v = (nome) => e.getPropertyValue(`--console-${nome}`).trim();
  const acao = e.getPropertyValue('--acao').trim();
  const fraco = e.getPropertyValue('--texto-4').trim();
  return {
    background: v('fundo'), foreground: v('texto'), cursor: acao, cursorAccent: v('fundo'),
    selectionBackground: comAlfa(acao, 0.28), selectionInactiveBackground: comAlfa(fraco, 0.3),
    scrollbarSliderBackground: comAlfa(fraco, 0.35), scrollbarSliderHoverBackground: comAlfa(fraco, 0.55),
    scrollbarSliderActiveBackground: comAlfa(fraco, 0.7),
    black: v('preto'), red: v('vermelho'), green: v('verde'), yellow: v('amarelo'),
    blue: v('azul'), magenta: v('magenta'), cyan: v('ciano'), white: v('branco'),
    brightBlack: v('preto-claro'), brightRed: v('vermelho-claro'), brightGreen: v('verde-claro'), brightYellow: v('amarelo-claro'),
    brightBlue: v('azul-claro'), brightMagenta: v('magenta-claro'), brightCyan: v('ciano-claro'), brightWhite: v('branco-claro'),
  };
}

function opcoesTerminal(modo) {
  const reduz = matchMedia('(prefers-reduced-motion: reduce)').matches;
  return {
    fontFamily: fonteMono(), fontSize: 13, lineHeight: 1.2,
    cursorBlink: !reduz, cursorStyle: 'bar', cursorWidth: 2, cursorInactiveStyle: 'outline',
    scrollback: 5000, convertEol: modo === 'simples', minimumContrastRatio: 4.5,
    rightClickSelectsWord: false, smoothScrollDuration: 0, theme: temaDoApp(),
  };
}

// a mesma pasta do Windows, escrita de jeitos diferentes (maiúsculas, barra no fim, / ou \)
function normalizarPasta(p) { return String(p || '').trim().replace(/\//g, '\\').replace(/\\+$/, '').toLowerCase(); }
function mesmaPasta(a, b) { return normalizarPasta(a) === normalizarPasta(b); }

// Um comando escrito no console sem rodar (quem aperta Enter é a pessoa). No pseudo console, cada quebra de linha
// vai como Shift+Enter no formato win32-input-mode, que o PSReadLine lê como "mais uma linha" (AddLine) em vez de
// rodar a linha: um bloco de várias linhas entra inteiro e só roda no Enter. Tab viraria completar, então vira espaço.
const SHIFT_ENTER = '\x1b[13;28;13;1;16;1_\x1b[13;28;13;0;16;1_';
function comandoParaDigitar(comando) {
  const linhas = String(comando).replace(/\r\n?/g, '\n').replace(/\t/g, '    ').replace(/^\n+|\n+$/g, '').split('\n');
  return { texto: linhas.join(SHIFT_ENTER), linhas: linhas.length };
}

// o texto das últimas linhas, juntando as que o terminal quebrou por largura
function ultimasLinhas(term, n) {
  const buf = term.buffer.active;
  const linhas = [];
  for (let y = 0; y < buf.length; y++) {
    const l = buf.getLine(y);
    if (!l) continue;
    const prox = buf.getLine(y + 1);
    const s = l.translateToString(!(prox && prox.isWrapped));
    if (l.isWrapped && linhas.length) linhas[linhas.length - 1] += s;
    else linhas.push(s);
  }
  while (linhas.length && !linhas[linhas.length - 1].trim()) linhas.pop();
  if (linhas.length > 1 && /^PS [^>]*>\s*$/.test(linhas[linhas.length - 1])) linhas.pop();  // o prompt vazio do fim
  return linhas.slice(-n).join('\n');
}

// ============================================================================================
// Um console (uma subaba): o terminal na tela e a conversa com o shell no servidor
// ============================================================================================
class Sessao {
  constructor(aba, info = {}) {
    this.aba = aba;
    this.id = info.id || null;
    this.idEm = info.id ? 0 : Infinity;  // quando ganhou o id (a sondagem não confunde console novo com sumido)
    this.titulo = info.titulo || t('PowerShell');
    this.pasta = info.pasta || '';
    this.modo = info.modo || 'conpty';
    this.build = info.build || 0;
    this.terminou = !!info.terminou;
    this.codigo = info.codigo ?? null;
    this.ocupado = !!info.ocupado;
    this.desde = 0;
    this.repetirAte = info.id ? (info.proximo || 0) : 0;  // o que já tinha saído antes desta tela: só mostrar
    this.vistoAte = this.repetirAte;                        // e não conta como saída nova na subaba
    this.silencio = 0;
    this.novidade = false;
    this.recebeu = false;
    this.sumiu = false;
    this.lido = false;
    this.removida = false;
    this.geracao = 0;
    this.controle = null;
    this.falhas = 0;
    this.fila = '';
    this.enviando = false;
    this.linha = '';
    this.ultimoCR = false;
    this.term = null;
    this.fit = null;
    this.timerTamanho = null;
    this.pronto = info.id ? Promise.resolve() : null;
    this.area = el('div', { class: 'console-xterm' });
    this.estado = el('div', { class: 'console-estado', hidden: true, role: 'status', 'aria-live': 'polite' });
    this.tela = el('div', { class: 'console-tela', role: 'tabpanel', hidden: true }, this.area, this.estado);
    aba.telas.append(this.tela);
  }

  get conectavel() { return this.id && !this.terminou && !this.removida; }
  // um console que já terminou ainda tem a saída guardada no servidor: lê uma vez (até o aviso de fim)
  get legivel() { return this.id && !this.removida && !this.sumiu && (!this.terminou || !this.lido); }

  // ----- abrir -----
  async garantirTerminal() {
    if (this.term) return;
    const { Terminal, FitAddon } = await carregarXterm();
    if (this.term || this.removida) return;
    this.term = new Terminal(opcoesTerminal(this.modo));
    this.fit = new FitAddon();
    this.term.loadAddon(this.fit);
    this.term.open(this.area);
    this.aplicarModo();
    this.term.textarea?.setAttribute('aria-label', t('Entrada do {titulo}', { titulo: this.titulo }));
    this.term.onData((d) => this.digitou(d));
    this.term.onResize(({ cols, rows }) => this.mudouTamanho(cols, rows));
    this.term.attachCustomKeyEventHandler((e) => this.tecla(e));
    this.area.addEventListener('contextmenu', (e) => this.cliqueDireito(e), true);
    if (this.terminou) this.mostrarFim();
  }

  aplicarModo() {
    if (!this.term) return;
    this.term.options.convertEol = this.modo === 'simples';
    if (this.modo === 'conpty' && this.build) this.term.options.windowsPty = { backend: 'conpty', buildNumber: this.build };
  }

  aplicarInfo(info) {
    this.id = info.id;
    this.idEm = performance.now();
    this.titulo = info.titulo || this.titulo;
    this.pasta = info.pasta || this.pasta;
    this.modo = info.modo || this.modo;
    this.build = info.build || this.build;
    this.ocupado = !!info.ocupado;
    this.aplicarModo();
    this.term?.textarea?.setAttribute('aria-label', t('Entrada do {titulo}', { titulo: this.titulo }));
  }

  // cria o shell no servidor do tamanho que o terminal tem na tela
  async iniciar(pasta) {
    this.pasta = pasta;
    let fim;
    this.pronto = new Promise((ok) => { fim = ok; });
    try {
      this.mostrarEstado(t('Abrindo o PowerShell…'), { carregando: true });
      await this.garantirTerminal();
      this.ajustar();
      const r = await api('/consoles', { metodo: 'POST', corpo: { pasta, cols: this.term?.cols || 100, rows: this.term?.rows || 30 } });
      if (this.removida) { api(`/consoles/${r.id}`, { metodo: 'DELETE' }).catch(() => {}); return; }
      this.aplicarInfo(r.console || r);
      this.aba.desenhar();
      if (this.aba.visivel && this.aba.ativa === this) this.conectar();
      // o painel pode ter mudado de largura enquanto o shell abria: o servidor fica com o tamanho de agora
      if (this.term && (this.term.cols !== r.console?.cols || this.term.rows !== r.console?.rows)) this.mudouTamanho(this.term.cols, this.term.rows);
    } finally { fim(); }
  }

  // ----- mostrar e esconder -----
  async mostrar() {
    await this.garantirTerminal().catch((e) => this.aba.falhaAoCarregar(e));
    if (!this.term || this.removida) return;
    // o painel põe o foco no [data-foco] da aba quando ela abre: que seja a entrada deste terminal
    for (const outro of this.aba.caixa.querySelectorAll('[data-foco]')) delete outro.dataset.foco;
    if (this.term.textarea) this.term.textarea.dataset.foco = '';
    requestAnimationFrame(() => this.ajustar());
    this.conectar();
    if (this.aba.visivel && this.aba.ativa === this) this.term.focus();
  }

  ajustar() {
    if (!this.term || !this.fit || this.tela.hidden || !this.area.offsetWidth || !this.area.offsetHeight) return;
    try { this.fit.fit(); } catch { /* o terminal ainda não tem medida */ }
  }

  mudouTamanho(cols, rows) {
    clearTimeout(this.timerTamanho);
    this.timerTamanho = setTimeout(() => {
      if (!this.conectavel) return;
      api(`/consoles/${this.id}/tamanho`, { metodo: 'POST', corpo: { cols, rows } }).catch(() => { /* o próximo ajuste tenta de novo */ });
    }, 120);
  }

  // ----- a saída (SSE) -----
  conectar() {
    if (!this.legivel || this.controle) return;
    const minha = ++this.geracao;
    const ciclo = async () => {
      while (minha === this.geracao && this.legivel) {
        const controle = new AbortController();
        this.controle = controle;
        let fim = null;
        try {
          const r = await fetch(`/api/consoles/${this.id}/saida?desde=${this.desde}`, { signal: controle.signal, credentials: 'same-origin', cache: 'no-store' });
          if (r.status === 404) { this.controle = null; this.sumiuDoServidor(); return; }
          if (r.status === 401) { this.controle = null; document.dispatchEvent(new CustomEvent('clave:sessao')); return; }
          if (!r.ok || !r.body) throw new Error(String(r.status));
          if (this.falhas) { this.falhas = 0; this.esconderEstado(); }
          const leitor = r.body.getReader();
          const dec = new TextDecoder();
          let buffer = '';
          for (;;) {
            const { value, done } = await leitor.read();
            if (done) break;
            buffer += dec.decode(value, { stream: true });
            let i;
            while ((i = buffer.indexOf('\n\n')) >= 0) {
              const bloco = buffer.slice(0, i);
              buffer = buffer.slice(i + 2);
              for (const linha of bloco.split('\n')) {
                if (!linha.startsWith('data: ')) continue;
                const ev = JSON.parse(linha.slice(6));
                if (ev.fim) fim = ev;
                else if (ev.cortado) aviso(t('A parte mais antiga da saída do {titulo} não foi guardada.', { titulo: this.titulo }));
                else this.chegou(ev);
              }
            }
          }
        } catch {
          if (minha !== this.geracao) return;  // desconectado de propósito
        }
        if (this.controle === controle) this.controle = null;
        if (minha !== this.geracao) return;
        if (fim) { this.acabou(fim.codigo, fim.fechado); return; }
        this.falhas++;
        if (this.falhas >= 2) this.mostrarEstado(t('Reconectando ao console…'), { carregando: true });
        await new Promise((ok) => setTimeout(ok, Math.min(5000, 600 * this.falhas)));
      }
    };
    ciclo();
  }

  desconectar() {
    this.geracao++;
    this.controle?.abort();
    this.controle = null;
  }

  chegou(ev) {
    if (!this.term) return;
    const repetido = ev.seq < this.repetirAte;
    if (repetido) {
      // a saída de antes desta tela abrir: pedidos de posição do cursor que ela tiver já foram respondidos
      this.silencio++;
      this.term.write(ev.dados, () => { this.silencio--; });
    } else this.term.write(ev.dados);
    this.desde = ev.seq + 1;
    if (!this.recebeu) { this.recebeu = true; this.esconderEstado(); }
    if (this.aba.ativa !== this || !this.aba.visivel) { this.novidade = true; this.aba.desenharGuias(); }
  }

  acabou(codigo, fechado) {
    if (this.removida) return;
    this.terminou = true;
    this.lido = true;
    this.codigo = codigo ?? this.codigo ?? null;
    this.ocupado = false;
    this.desconectar();
    this.mostrarFim(fechado);
    if (this.term) {
      this.term.write('\x1b[?25l');  // o cursor some: não tem mais ninguém para receber o que se digitar
      this.term.options.cursorBlink = false;
      this.term.options.disableStdin = true;
    }
    this.aba.desenhar();
  }

  sumiuDoServidor() {
    if (this.removida || this.terminou) return;
    this.sumiu = true;
    this.acabou(null, true);
  }

  // ----- avisos sobre o terminal -----
  mostrarEstado(texto, { carregando = false, botao = null } = {}) {
    this.estado.className = `console-estado ${carregando ? 'carregando' : 'fim'}`;
    // replaceChildren escreveria "null" na tela: só entra o que existe
    this.estado.replaceChildren(...[
      carregando ? el('span', { class: 'console-girando', 'aria-hidden': 'true' }) : el('span', { class: 'console-estado-icone', html: ic('info') }),
      el('span', { class: 'console-estado-texto', texto }),
      botao,
    ].filter(Boolean));
    this.estado.hidden = false;
  }

  esconderEstado() { this.estado.hidden = true; }

  mostrarFim(fechado) {
    let texto;
    if (this.sumiu) texto = t('Este console não existe mais. O Clave pode ter sido reiniciado.');
    else if (this.codigo === null || this.codigo === undefined) texto = fechado ? t('O console foi fechado.') : t('O PowerShell terminou.');
    else texto = t('O PowerShell terminou (código {codigo}).', { codigo: this.codigo });
    this.mostrarEstado(texto, {
      botao: el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Abrir de novo'), onclick: () => this.aba.reiniciar(this, { perguntar: false }) }),
    });
  }

  // ----- a entrada -----
  tecla(e) {
    if (e.type !== 'keydown') return true;
    const ctrl = e.ctrlKey || e.metaKey;
    if (!ctrl || e.altKey) return true;
    const k = (e.key || '').toLowerCase();
    if (e.code === 'Backquote' || e.key === '`' || (k === 'j' && !e.shiftKey)) return false;  // os atalhos do painel sobem até o app
    if (k === 'c' && (e.shiftKey || this.term.hasSelection())) {
      if (this.term.hasSelection()) this.copiar();
      e.preventDefault();
      return false;
    }
    if (k === 'v') return false;  // o navegador cola sozinho (evento paste) e o xterm manda o texto
    return true;
  }

  async copiar() {
    const texto = this.term?.getSelection() || '';
    if (!texto) return;
    try {
      await navigator.clipboard.writeText(texto);
      this.term.clearSelection();
    } catch { aviso(t('Não deu para copiar.'), 'erro'); }
  }

  async colar() {
    if (!this.conectavel) return;
    try {
      const texto = await navigator.clipboard.readText();
      if (texto) this.term.paste(texto);
      this.term.focus();
    } catch { aviso(t('Não deu para ler a área de transferência. Use Ctrl+V.'), 'erro'); }
  }

  // botão direito: copia o que está selecionado; sem seleção, cola (como no console do Windows)
  cliqueDireito(e) {
    e.preventDefault();
    e.stopPropagation();
    if (this.term?.hasSelection()) this.copiar();
    else this.colar();
  }

  digitou(d) {
    if (this.silencio > 0 || !this.conectavel) return;
    if (this.modo === 'simples') this.digitouSimples(d);
    else this.enviar(d);
  }

  // Sem pseudo console, o shell só recebe linhas inteiras e não ecoa o que se digita: a tela mostra o que está
  // sendo digitado e manda a linha no Enter. O PowerShell repete a linha que recebe, então o eco daqui sai antes.
  digitouSimples(d) {
    const limpo = d.replace(/\x1b\[[0-9;?]*[ -/]*[@-~]|\x1bO.|\x1b./g, '');  // setas, foco e teclas especiais
    for (const ch of limpo) {
      if (ch === '\r' || ch === '\n') {
        if (ch === '\n' && this.ultimoCR) { this.ultimoCR = false; continue; }
        this.ultimoCR = ch === '\r';
        if (this.linha) this.term.write('\x1b8\x1b[J');
        this.enviar(`${this.linha}\r\n`);
        this.linha = '';
        continue;
      }
      this.ultimoCR = false;
      if (ch === '\x7f' || ch === '\b') {
        if (this.linha) { this.linha = [...this.linha].slice(0, -1).join(''); this.term.write('\b \b'); }
      } else if (ch === '\x03') {
        if (this.linha) { this.term.write('\x1b8\x1b[J'); this.linha = ''; }
        else aviso(t('No modo simples o Ctrl+C não para um comando. Use Reiniciar.'));
      } else if (ch >= ' ') {
        if (!this.linha) this.term.write('\x1b7');
        this.linha += ch;
        this.term.write(ch);
      }
    }
  }

  // em ordem, um pedido por vez; o que chega enquanto um pedido anda vai junto no próximo
  enviar(dados) {
    if (!this.conectavel || !dados) return;
    this.fila += dados;
    if (!this.enviando) this.esvaziar();
  }

  async esvaziar() {
    this.enviando = true;
    try {
      while (this.fila && this.conectavel) {
        let n = Math.min(this.fila.length, PEDACO_ENTRADA);
        const c = this.fila.charCodeAt(n - 1);
        if (n < this.fila.length && c >= 0xd800 && c <= 0xdbff) n--;  // não parte um emoji ao meio
        const parte = this.fila.slice(0, n);
        this.fila = this.fila.slice(n);
        try {
          await api(`/consoles/${this.id}/entrada`, { metodo: 'POST', corpo: { dados: parte } });
        } catch (e) {
          this.fila = '';
          if (e.status === 404) this.sumiuDoServidor();
          else if (e.status === 409) this.conectar();  // terminou: o SSE traz o fim com o código
          else aviso(e.message, 'erro');
        }
      }
    } finally { this.enviando = false; }
  }

  // ----- fim -----
  async encerrar() {
    this.removida = true;
    this.desconectar();
    clearTimeout(this.timerTamanho);
    await this.pronto?.catch?.(() => {});
    if (this.id) {
      try { await api(`/consoles/${this.id}`, { metodo: 'DELETE' }); } catch (e) { if (e.status !== 404) aviso(e.message, 'erro'); }
    }
    try { this.term?.dispose(); } catch { /* já foi */ }
    this.term = null;
    this.tela.remove();
  }
}

// ============================================================================================
// A aba: as subabas, a barra e os estados vazios
// ============================================================================================
class AbaConsole {
  constructor(caixa, contexto) {
    this.caixa = caixa;
    this.contexto = contexto;
    this.sessoes = [];
    this.ativa = null;
    this.visivel = false;
    this.maximo = 6;
    this.iniciado = null;   // a promessa da primeira carga (xterm e os consoles que já estavam abertos)
    this.carregado = false; // a primeira carga terminou
    this.autoAberto = false; // a primeira carga abriu um console sozinha (abrir({ novo }) logo em seguida não abre outro)
    this.sondagem = 0;
    this.fechouTudo = false;
    this.erro = null;
    this.timerSondar = null;

    this.guias = el('div', { class: 'console-guias', role: 'tablist', 'aria-label': t('Consoles abertos') });
    this.guias.addEventListener('keydown', (e) => this.teclaGuias(e));
    this.botaoNovo = el('button', { class: 'icone-botao console-novo', type: 'button', html: ic('mais'), onclick: () => this.novo() });
    this.botaoLimpar = el('button', { class: 'icone-botao', type: 'button', html: ICONE_LIMPAR, title: t('Limpar a tela'), 'aria-label': t('Limpar a tela'), onclick: () => this.limpar() });
    this.botaoReiniciar = el('button', { class: 'icone-botao', type: 'button', html: ic('refazer'), title: t('Reiniciar o console'), 'aria-label': t('Reiniciar o console'), onclick: () => this.reiniciar() });
    this.botaoMandar = el('button', {
      class: 'botao pequeno console-mandar', type: 'button', title: t('Manda o texto selecionado (ou as últimas {n} linhas) para a caixa de mensagem', { n: LINHAS_PARA_O_CLAUDE }),
      html: `${ic('chat')}<span>${t('Mandar para o Claude')}</span>`, 'aria-label': t('Mandar para o Claude'), onclick: () => this.mandar(),
    });
    this.barra = el('div', { class: 'painel-barra console-barra' },
      el('div', { class: 'console-guias-rolagem' }, this.guias, this.botaoNovo),
      el('span', { class: 'espaco' }), this.botaoLimpar, this.botaoReiniciar, this.botaoMandar);
    this.avisoSimples = el('div', { class: 'console-aviso', role: 'note', hidden: true }, el('span', { html: ic('alerta') }),
      el('p', { texto: t('Modo simples: este Windows não abriu o console completo. Os comandos funcionam, mas sem cores, sem setas e sem programas interativos, e o Ctrl+C não para um comando (use Reiniciar).') }));
    this.telas = el('div', { class: 'console-telas' });
    this.vazio = el('div', { class: 'painel-vazio console-vazio', hidden: true });
    caixa.append(this.barra, this.avisoSimples, this.telas, this.vazio);

    // o painel não chama mostrar() quando reabre na mesma aba depois de fechado: o aviso de abrir e fechar cobre isso
    ouvirPainel(({ aberto, ativa }) => {
      const naTela = aberto && ativa === 'console' && !this.caixa.hidden && !document.getElementById('painel-lateral')?.hidden;
      if (naTela && !this.visivel) this.mostrar();
      else if (!naTela && this.visivel) this.esconder();
    });

    const tema = () => { const novo = temaDoApp(); for (const s of this.sessoes) if (s.term) s.term.options.theme = novo; };
    new MutationObserver(tema).observe(document.documentElement, { attributes: true, attributeFilter: ['data-tema'] });
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', tema);
    this.desenhar();
  }

  // ----- ganchos do painel -----
  mostrar() {
    this.visivel = true;
    if (!this.iniciado) this.iniciado = this.iniciar();
    this.iniciado.then(() => {
      if (!this.visivel) return;
      this.ativa?.mostrar();
      this.sondar();
    });
  }

  esconder() {
    this.visivel = false;
    for (const s of this.sessoes) s.desconectar();
    clearTimeout(this.timerSondar);
    this.timerSondar = null;
  }

  trocarContexto(ctx) {
    this.contexto = ctx;
    this.desenhar();
    if (this.visivel && this.carregado && !this.erro && !this.sessoes.length && ctx?.pasta && !this.fechouTudo) this.novo();
  }

  ajustar() { this.ativa?.ajustar(); }

  // abrirPainel('console', { novo: true, pasta? }) abre mais um console. abrirPainel('console', { comando, pasta? })
  // escreve o comando num console da pasta da conversa (o da tela, se for dela; senão outro dela; senão abre um)
  // SEM apertar Enter: quem roda é a pessoa. Um bloco de várias linhas entra inteiro (Shift+Enter entre as linhas).
  // É o que o botão "Rodar no console" dos blocos de PowerShell usa.
  async abrir(args) {
    await this.iniciado;
    const recemAberto = this.autoAberto;
    this.autoAberto = false;
    if (args?.novo) {
      if (!recemAberto || (args.pasta && !mesmaPasta(args.pasta, this.ativa?.pasta))) await this.novo(args.pasta);
      return;
    }
    if (typeof args?.comando === 'string' && args.comando.trim()) await this.escreverComando(args.comando, args.pasta || this.contexto?.pasta);
  }

  async escreverComando(comando, pasta) {
    const serve = (x) => x && x.conectavel && (!pasta || mesmaPasta(x.pasta, pasta));
    let s = serve(this.ativa) ? this.ativa : [...this.sessoes].reverse().find(serve);
    if (s && s !== this.ativa) this.ativar(s);
    if (!s) s = await this.novo(pasta);
    await s?.pronto;
    if (!s?.term || !s.conectavel) return;
    const { texto, linhas } = comandoParaDigitar(comando);
    if (s.modo === 'simples') {
      // sem pseudo console o shell só recebe linhas inteiras: dá para deixar uma linha pronta, não um bloco
      if (linhas > 1) aviso(t('No modo simples o console recebe uma linha por vez. Copie o bloco e rode linha por linha.'), 'erro');
      else s.digitouSimples(texto);
    } else {
      s.enviar(texto);
    }
    s.term.focus();
  }

  // ----- começo: reencontra os consoles que já estavam abertos (a janela recarregou) -----
  async iniciar() {
    this.carregado = false;
    this.desenhar();
    try {
      await carregarXterm();
    } catch (e) { this.carregado = true; this.falhaAoCarregar(e); return; }
    try {
      const r = await api('/consoles');
      this.maximo = r.maximo || this.maximo;
      const conhecidos = new Set(this.sessoes.map((s) => s.id));
      for (const info of r.consoles || []) if (!conhecidos.has(info.id)) this.sessoes.push(new Sessao(this, info));
    } catch (e) {
      this.carregado = true;
      this.erro = e.message;
      this.desenhar();
      return;
    }
    this.carregado = true;
    if (this.sessoes.length) this.ativar(this.ativa || this.sessoes[this.sessoes.length - 1]);
    else if (this.contexto?.pasta && this.visivel) { await this.novo(); this.autoAberto = this.sessoes.length > 0; }
    this.desenhar();
  }

  falhaAoCarregar(e) {
    console.error(e);
    this.erro = t('Não deu para carregar o terminal. Feche e abra o Clave de novo.');
    this.desenhar();
  }

  // ----- subabas -----
  ativar(s) {
    if (this.ativa && this.ativa !== s) {
      this.ativa.tela.hidden = true;
      this.ativa.desconectar();
    }
    this.ativa = s;
    if (s) {
      s.tela.hidden = false;
      s.novidade = false;
      if (this.visivel) s.mostrar();
    }
    this.desenhar();
  }

  // devolve o console aberto (ou null)
  async novo(pasta = this.contexto?.pasta) {
    if (!pasta) { aviso(t('Escolha o ambiente para abrir um console nele.')); return null; }
    if (this.sessoes.length >= this.maximo) {
      aviso(t('Já tem {n} consoles abertos. Feche um para abrir outro.', { n: this.maximo }), 'erro');
      return null;
    }
    this.fechouTudo = false;
    this.autoAberto = false;
    this.erro = null;
    const s = new Sessao(this, { pasta });
    this.sessoes.push(s);
    this.ativar(s);
    return (await this.comecar(s, pasta)) ? s : null;
  }

  // devolve se o console abriu
  async comecar(s, pasta) {
    try {
      await s.iniciar(pasta);
      return !s.removida;
    } catch (e) {
      const i = this.sessoes.indexOf(s);
      if (i >= 0) this.sessoes.splice(i, 1);
      s.removida = true;
      try { s.term?.dispose(); } catch { /* já foi */ }
      s.tela.remove();
      if (this.ativa === s) this.ativa = null;
      if (this.sessoes.length) { this.ativar(this.sessoes[Math.max(0, i - 1)]); aviso(e.message, 'erro'); }
      else { this.erro = e.message; this.desenhar(); }
      return false;
    }
  }

  // pergunta antes de matar um programa que ainda está rodando no console
  async podeFechar(s, reiniciando) {
    if (!s.conectavel) return true;
    try {
      const r = await api('/consoles');
      const info = (r.consoles || []).find((c) => c.id === s.id);
      if (!info || info.terminou || !info.ocupado) return true;
    } catch { return true; }
    return confirmar(
      reiniciando ? t('Tem um programa rodando no {titulo}. Se reiniciar, ele para no meio.', { titulo: s.titulo })
        : t('Tem um programa rodando no {titulo}. Se fechar, ele para no meio.', { titulo: s.titulo }),
      { titulo: reiniciando ? t('Reiniciar o console?') : t('Fechar o console?'), sim: reiniciando ? t('Reiniciar') : t('Fechar'), perigo: true });
  }

  async fechar(s) {
    if (!(await this.podeFechar(s, false))) return;
    const i = this.sessoes.indexOf(s);
    if (i < 0) return;
    this.sessoes.splice(i, 1);
    if (this.ativa === s) {
      this.ativa = null;
      const prox = this.sessoes[Math.min(i, this.sessoes.length - 1)];
      if (prox) this.ativar(prox);
    }
    if (!this.sessoes.length) this.fechouTudo = true;
    this.desenhar();
    await s.encerrar();
    this.desenhar();
  }

  async reiniciar(s = this.ativa, { perguntar = true } = {}) {
    if (!s || s.reiniciando) return;
    if (perguntar && !(await this.podeFechar(s, true))) return;
    if (!this.sessoes.includes(s)) return;
    const pasta = s.pasta || this.contexto?.pasta;
    s.reiniciando = true;
    await s.encerrar();
    // outro console pode ter fechado (ou este mesmo) enquanto este encerrava: a posição é a de agora
    const i = this.sessoes.indexOf(s);
    if (i < 0) { this.desenhar(); return; }
    const nova = new Sessao(this, { pasta, titulo: s.titulo });
    this.sessoes.splice(i, 1, nova);
    if (this.ativa === s) this.ativa = null;
    this.ativar(nova);
    await this.comecar(nova, pasta);
  }

  limpar() {
    const s = this.ativa;
    if (!s?.term) return;
    s.term.clear();
    // o PSReadLine limpa a tela dele também (Ctrl+L): sem isso, o próximo redesenho do console traria o texto de volta
    if (s.modo === 'conpty' && s.conectavel && !s.ocupado) s.enviar('\x0c');
    s.term.focus();
  }

  async mandar() {
    const s = this.ativa;
    if (!s?.term) return;
    let texto = s.term.getSelection();
    if (!texto.trim()) texto = ultimasLinhas(s.term, LINHAS_PARA_O_CLAUDE);
    texto = texto.replace(/\r/g, '').split('\n').map((l) => l.replace(/\s+$/, '')).join('\n').replace(/^\n+|\n+$/g, '');
    if (!texto.trim()) { aviso(t('O console ainda não tem texto para mandar.')); return; }
    // os consoles valem para o app todo: a saída de um console aberto em outra pasta pode não ter nada a ver com
    // o que esta conversa faz
    const daConversa = this.contexto?.pasta;
    if (s.pasta && daConversa && !mesmaPasta(s.pasta, daConversa)) {
      const ok = await confirmar(
        t('O {titulo} está aberto em {pasta_console}, mas esta conversa trabalha em {pasta_conversa}. Mandar o texto dele para esta conversa mesmo assim?',
          { titulo: s.titulo, pasta_console: s.pasta, pasta_conversa: daConversa }),
        { titulo: t('Mandar de outra pasta?'), sim: t('Mandar mesmo assim') });
      if (!ok) return;
    }
    const maior = Math.max(0, ...(texto.match(/`+/g) || []).map((x) => x.length));
    const cerca = '`'.repeat(Math.max(3, maior + 1));
    window.dispatchEvent(new CustomEvent('clave:inserir-texto', { detail: { texto: `${cerca}text\n${texto}\n${cerca}\n` } }));
    if (matchMedia('(max-width: 900px)').matches) fecharPainel();  // o painel cobre a conversa nas telas estreitas
    aviso(t('O texto do console foi para a caixa de mensagem.'));
  }

  // enquanto a aba está na tela: quem terminou, quem tem programa rodando e quem tem saída nova nas outras subabas
  async sondar() {
    clearTimeout(this.timerSondar);
    if (!this.visivel) return;
    const minha = ++this.sondagem;
    const inicio = performance.now();
    try {
      const r = await api('/consoles');
      if (minha !== this.sondagem) return;
      const lista = new Map((r.consoles || []).map((c) => [c.id, c]));
      for (const s of [...this.sessoes]) {
        if (!s.id || s.removida) continue;
        const info = lista.get(s.id);
        // um console que ganhou o id depois que esta lista foi pedida ainda não está nela
        if (!info) { if (s.idEm < inicio) s.sumiuDoServidor(); continue; }
        s.ocupado = !!info.ocupado;
        if (s !== this.ativa && info.proximo > Math.max(s.desde, s.vistoAte)) s.novidade = true;
        if (info.terminou && !s.terminou && s !== this.ativa) { s.codigo = info.codigo; s.terminou = true; if (s.term) s.mostrarFim(false); }
      }
      this.desenhar();
    } catch { /* o servidor pode estar reiniciando: tenta na próxima */ }
    if (this.visivel && minha === this.sondagem) this.timerSondar = setTimeout(() => this.sondar(), SONDAR_MS);
  }

  // ----- desenho -----
  desenhar() {
    const tem = this.sessoes.length > 0;
    this.telas.hidden = !tem;
    this.vazio.hidden = tem;
    if (!tem) this.mostrarVazio(this.erro ? 'erro' : (this.carregado ? 'nenhum' : 'carregando'));
    this.desenharGuias();
    const s = this.ativa;
    for (const b of [this.botaoLimpar, this.botaoReiniciar, this.botaoMandar]) b.hidden = !tem;
    this.botaoLimpar.disabled = !s?.term;
    this.botaoReiniciar.disabled = !s || !s.pasta;
    this.botaoMandar.disabled = !s?.term;
    this.avisoSimples.hidden = !(s && s.id && s.modo === 'simples' && !s.terminou);
  }

  desenharGuias() {
    const pasta = this.contexto?.pasta;
    // a sondagem redesenha a cada poucos segundos: quem estava com o foco numa subaba continua nela
    const focada = this.guias.contains(document.activeElement)
      ? { i: [...this.guias.children].indexOf(document.activeElement.closest('.console-guia')), fechar: document.activeElement.classList.contains('console-guia-fechar') }
      : null;
    this.guias.replaceChildren(...this.sessoes.map((s) => {
      const atual = s === this.ativa;
      let dica = s.pasta ? t('Aberto em {pasta}', { pasta: s.pasta }) : '';
      if (s.terminou) dica += `\n${s.codigo !== null && s.codigo !== undefined ? t('Terminou (código {codigo})', { codigo: s.codigo }) : t('Terminou')}`;
      else if (s.ocupado) dica += `\n${t('Tem um programa rodando')}`;
      return el('div', { class: `console-guia${atual ? ' atual' : ''}${s.terminou ? ' terminou' : ''}` },
        el('button', {
          type: 'button', role: 'tab', class: 'console-guia-nome', 'aria-selected': String(atual), tabindex: atual ? '0' : '-1',
          title: dica, onclick: () => { if (this.ativa !== s) this.ativar(s); else s.term?.focus(); },
        },
        s.novidade ? el('span', { class: 'console-ponto', title: t('Saída nova'), 'aria-label': t('Saída nova') }) : null,
        el('span', { texto: s.titulo })),
        el('button', {
          type: 'button', class: 'console-guia-fechar', html: ic('x'), tabindex: '-1',
          title: t('Fechar o {titulo}', { titulo: s.titulo }), 'aria-label': t('Fechar o {titulo}', { titulo: s.titulo }), onclick: () => this.fechar(s),
        }));
    }));
    if (focada && focada.i >= 0) this.guias.children[focada.i]?.querySelector(focada.fechar ? '.console-guia-fechar' : '.console-guia-nome')?.focus();
    const cheio = this.sessoes.length >= this.maximo;
    this.botaoNovo.disabled = cheio || !pasta;
    const dica = cheio ? t('Já tem {n} consoles abertos. Feche um para abrir outro.', { n: this.maximo })
      : (pasta ? t('Novo console em {pasta}', { pasta }) : t('Escolha o ambiente para abrir um console nele.'));
    this.botaoNovo.title = dica;
    this.botaoNovo.setAttribute('aria-label', cheio || !pasta ? dica : t('Novo console'));
  }

  teclaGuias(e) {
    if (e.key === 'Delete' && this.ativa && e.target.closest('.console-guia')) { e.preventDefault(); this.fechar(this.ativa); return; }
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    const i = this.sessoes.indexOf(this.ativa);
    if (i < 0) return;
    e.preventDefault();
    e.stopPropagation();
    const prox = this.sessoes[(i + (e.key === 'ArrowRight' ? 1 : -1) + this.sessoes.length) % this.sessoes.length];
    this.ativar(prox);
    this.guias.querySelector('.console-guia.atual .console-guia-nome')?.focus();
  }

  mostrarVazio(tipo) {
    const pasta = this.contexto?.pasta;
    const partes = [];
    if (tipo === 'carregando') {
      partes.push(el('span', { class: 'console-girando grande', 'aria-hidden': 'true' }), el('p', { texto: t('Preparando o console…') }));
    } else if (tipo === 'erro') {
      partes.push(el('span', { html: ic('alerta') }), el('h3', { texto: t('Não deu para abrir o console') }), el('p', { texto: this.erro }));
      partes.push(el('button', { class: 'botao primario', type: 'button', texto: t('Tentar de novo'), onclick: () => this.tentarDeNovo() }));
    } else if (!pasta) {
      partes.push(el('span', { html: ic('terminal') }), el('h3', { texto: t('Console') }), el('p', { texto: t('Escolha o ambiente para abrir um console nele.') }));
    } else {
      partes.push(el('span', { html: ic('terminal') }), el('h3', { texto: t('Nenhum console aberto') }),
        el('p', { class: 'console-vazio-pasta', texto: t('O PowerShell abre na pasta {pasta}.', { pasta }) }),
        el('button', { class: 'botao primario', type: 'button', html: `${ic('mais')}<span>${t('Abrir um console')}</span>`, onclick: () => this.novo() }));
    }
    this.vazio.replaceChildren(...partes);
  }

  async tentarDeNovo() {
    const deuErroNaCarga = !this.carregado || !(await carregarXterm().then(() => true, () => false));
    this.erro = null;
    if (deuErroNaCarga || !this.sessoes.length) {
      // a lista de consoles pode não ter vindo: carrega tudo de novo (reencontra os abertos e abre um se não houver)
      this.iniciado = this.iniciar();
      await this.iniciado;
      return;
    }
    this.desenhar();
  }
}

registrarAba({
  id: 'console', titulo: () => t('Console'), icone: 'terminal', modos: ['code'], atalho: 'Ctrl+`',
  // Ctrl+` no teclado americano; no ABNT2 a mesma tecla (à esquerda do 1) é o Ctrl+'
  tecla: (e) => (e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && (e.code === 'Backquote' || e.key === '`'),
  montar(caixa, contexto) {
    const aba = new AbaConsole(caixa, contexto);
    return {
      abrir: (args) => aba.abrir(args),
      mostrar: () => aba.mostrar(),
      esconder: () => aba.esconder(),
      contexto: (ctx) => aba.trocarContexto(ctx),
      redimensionar: () => aba.ajustar(),
    };
  },
});
