// Janela do Clave (Electron). Sobe o servidor Python (servidor/iniciar.py), espera ele responder e
// abre a interface numa janela própria. Fechar a janela fecha tudo.
//
// Também é aqui que mora o navegador do modo Code: uma WebContentsView numa sessão própria
// ('persist:clave-navegador'), desenhada por cima da janela no lugar que a aba Navegador pede. A interface manda
// nela pelo preload (window.clave.navegador) e o servidor Python manda por uma ponte HTTP em 127.0.0.1 com porta e
// token aleatórios (CLAVE_PONTE_URL e CLAVE_PONTE_TOKEN, passados para o servidor no ambiente). As regras (sites
// liberados e negados) moram no Python (servidor/navegador.py); aqui ficam as travas que precisam da página: clique e
// digitação só na página e no elemento aprovados ("esperado"), campo de senha e de cartão recusados, prazo por ação,
// página em branco, apagar os dados da sessão e nenhum certificado de cliente entregue sozinho.
const { app, BrowserWindow, Menu, Notification, WebContentsView, dialog, ipcMain, nativeImage, session, shell, nativeTheme } = require('electron');
const { spawn, execFile } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const net = require('net');
const os = require('os');
const path = require('path');

const RAIZ = path.resolve(__dirname, '..');
const DADOS = process.env.CLAVE_DADOS || path.join(RAIZ, 'dados');
const LOGS = path.join(DADOS, 'logs');
const ESTADO_JANELA = path.join(DADOS, 'janela.json');
const ICONE = path.join(RAIZ, 'app', 'img', process.platform === 'win32' ? 'icone.ico' : 'icone.png');

let janela = null;
let servidor = null;
let porta = 0;
let saindo = false;

const primeiraInstancia = app.requestSingleInstanceLock();
if (!primeiraInstancia) {
  // o Clave já está aberto: a outra janela vem para a frente e esta sai sem subir nada
  app.exit(0);
} else {
  app.on('second-instance', () => {
    if (janela) { if (janela.isMinimized()) janela.restore(); janela.show(); janela.focus(); }
  });
}

app.setAppUserModelId('com.clave.app');
app.setName('Clave');

function python() {
  const candidatos = process.platform === 'win32'
    ? [path.join(RAIZ, '.venv', 'Scripts', 'pythonw.exe'), path.join(RAIZ, '.venv', 'Scripts', 'python.exe')]
    : [path.join(RAIZ, '.venv', 'bin', 'python')];
  return candidatos.find((p) => fs.existsSync(p));
}

// Reabre pelo ferramentas/abrir.pyw quando ele existe: se a atualização trocou a versão do
// Electron, é ele que baixa a nova antes de abrir.
function reabrir() {
  const pyw = path.join(RAIZ, '.venv', 'Scripts', 'pythonw.exe');
  const abrir = path.join(RAIZ, 'ferramentas', 'abrir.pyw');
  if (process.platform === 'win32' && fs.existsSync(pyw) && fs.existsSync(abrir)) app.relaunch({ execPath: pyw, args: [abrir] });
  else app.relaunch();
}

function portaLivre(p) {
  return new Promise((ok) => {
    const s = net.createServer();
    s.once('error', () => ok(false));
    s.once('listening', () => s.close(() => ok(true)));
    s.listen(p, '127.0.0.1');
  });
}

async function escolherPorta() {
  for (let p = 8040; p < 8070; p += 1) if (await portaLivre(p)) return p;
  throw new Error('Nenhuma porta livre entre 8040 e 8069.');
}

function saude() {
  return new Promise((ok) => {
    const req = http.get({ host: '127.0.0.1', port: porta, path: '/api/saude', timeout: 1500, headers: { Host: `127.0.0.1:${porta}` } }, (r) => {
      r.resume();
      ok(r.statusCode === 401 || r.statusCode === 200);
    });
    req.on('error', () => ok(false));
    req.on('timeout', () => { req.destroy(); ok(false); });
  });
}

async function esperarServidor(limiteMs = 45000) {
  const inicio = Date.now();
  while (Date.now() - inicio < limiteMs) {
    if (servidor && servidor.exitCode !== null) return false;
    if (await saude()) return true;
    await new Promise((r) => setTimeout(r, 250));
  }
  return false;
}

function subirServidor() {
  const py = python();
  if (!py) throw new Error('O ambiente Python do Clave não foi instalado. Rode o instalar.bat da pasta do Clave.');
  fs.mkdirSync(LOGS, { recursive: true });
  const log = fs.openSync(path.join(LOGS, 'servidor.log'), 'a');
  const env = { ...process.env, CLAVE_LANCADOR: '1', PYTHONUTF8: '1' };
  if (ponte.porta) { env.CLAVE_PONTE_URL = `http://127.0.0.1:${ponte.porta}`; env.CLAVE_PONTE_TOKEN = ponte.token; }
  servidor = spawn(py, [path.join(RAIZ, 'servidor', 'iniciar.py'), '--porta', String(porta), '--sem-janela', '--pai', String(process.pid)], {
    cwd: RAIZ,
    env,
    windowsHide: true,
    stdio: ['ignore', log, log],
  });
  servidor.on('exit', (codigo) => {
    servidor = null;
    if (!saindo && janela) {
      dialog.showMessageBox(janela, {
        type: 'error', title: 'Clave',
        message: 'O servidor do Clave parou.',
        detail: `Código ${codigo}. O registro está em ${path.join(LOGS, 'servidor.log')}.`,
        buttons: ['Abrir de novo', 'Fechar'],
      }).then(({ response }) => { if (response === 0) { reabrir(); } app.exit(0); });
    }
  });
}

function pararServidor() {
  if (!servidor) return;
  const pid = servidor.pid;
  servidor = null;
  if (process.platform === 'win32') execFile('taskkill', ['/PID', String(pid), '/T', '/F'], () => {});
  else { try { process.kill(pid); } catch { /* já tinha saído */ } }
}

// Fechar com calma: pede ao servidor para sair (ele fecha os consoles e os comandos em segundo plano poupando os
// programas com janela), espera o supervisor terminar por até 3 s e, se ainda estiver de pé, derruba a árvore como antes.
function pararServidorComCalma(limiteMs = 3000) {
  const proc = servidor;
  if (!proc) return Promise.resolve();
  return new Promise((pronto) => {
    let feito = false;
    const fim = () => { if (feito) return; feito = true; clearTimeout(relogio); pararServidor(); pronto(); };
    const relogio = setTimeout(fim, limiteMs);
    proc.once('exit', () => { if (servidor === proc) servidor = null; fim(); });
    let segredo = '';
    try { segredo = lerSegredoSessao(); } catch { return fim(); }
    const req = http.request({
      host: '127.0.0.1', port: porta, path: '/api/sair', method: 'POST', timeout: 1500,
      headers: { Host: `127.0.0.1:${porta}`, Origin: `http://127.0.0.1:${porta}`, Cookie: `clave_sessao=${segredo}`, 'Content-Length': 0 },
    }, (r) => r.resume());
    req.on('error', fim);
    req.on('timeout', () => { req.destroy(); fim(); });
    req.end();
  });
}

function lerEstadoJanela() {
  try { return JSON.parse(fs.readFileSync(ESTADO_JANELA, 'utf8')); } catch { return { width: 1280, height: 860 }; }
}

function salvarEstadoJanela() {
  if (!janela) return;
  try {
    const b = janela.getNormalBounds();
    fs.writeFileSync(ESTADO_JANELA, JSON.stringify({ ...b, maximizada: janela.isMaximized() }));
  } catch { /* não é importante */ }
}

function menuDeContexto(wc, params) {
  const itens = [];
  if (params.misspelledWord) {
    for (const s of params.dictionarySuggestions.slice(0, 5)) itens.push({ label: s, click: () => wc.replaceMisspelling(s) });
    if (params.dictionarySuggestions.length) itens.push({ type: 'separator' });
  }
  if (params.isEditable) itens.push({ role: 'cut', label: 'Recortar' });
  if (params.selectionText || params.isEditable) itens.push({ role: 'copy', label: 'Copiar' });
  if (params.isEditable) itens.push({ role: 'paste', label: 'Colar' }, { role: 'selectAll', label: 'Selecionar tudo' });
  if (params.linkURL && /^https?:/.test(params.linkURL) && !params.linkURL.startsWith(`http://127.0.0.1:${porta}`)) {
    itens.push({ type: 'separator' }, { label: 'Abrir link no navegador', click: () => shell.openExternal(params.linkURL) });
  }
  if (itens.length) Menu.buildFromTemplate(itens).popup({ window: janela });
}

function lerSegredoSessao() {
  return fs.readFileSync(path.join(DADOS, 'sessao.key'), 'ascii').trim();
}

async function abrirJanela() {
  const est = lerEstadoJanela();
  janela = new BrowserWindow({
    x: est.x, y: est.y, width: est.width || 1280, height: est.height || 860,
    minWidth: 420, minHeight: 480,
    title: 'Clave',
    icon: fs.existsSync(ICONE) ? ICONE : undefined,
    backgroundColor: nativeTheme.shouldUseDarkColors ? '#1c1b18' : '#f6f1e7',
    autoHideMenuBar: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      spellcheck: true,
    },
  });
  if (est.maximizada) janela.maximize();
  janela.setMenuBarVisibility(false);
  janela.webContents.session.setSpellCheckerLanguages(['pt-BR']);
  const origem = `http://127.0.0.1:${porta}`;
  janela.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/.test(url) && !url.startsWith(origem)) shell.openExternal(url);
    else if (url.startsWith(origem + '/previa/')) shell.openExternal(url);
    return { action: 'deny' };
  });
  janela.webContents.on('will-navigate', (e, url) => {
    if (!url.startsWith(origem)) { e.preventDefault(); if (/^https?:/.test(url)) shell.openExternal(url); }
  });
  janela.webContents.on('context-menu', (_e, params) => menuDeContexto(janela.webContents, params));
  janela.webContents.on('before-input-event', (_e, input) => {
    if (input.type === 'keyDown' && input.key === 'F12' && !app.isPackaged) janela.webContents.toggleDevTools();
  });
  // a interface recarregou (F5, troca de idioma): a aba Navegador some com ela, então a vista também some até a
  // aba nova pedir de novo
  janela.webContents.on('did-start-navigation', (d) => { if (d.isMainFrame && !d.isSameDocument) esconderVista(); });
  janela.once('ready-to-show', () => janela.show());
  janela.on('close', salvarEstadoJanela);
  janela.on('focus', () => janela?.flashFrame(false));
  janela.on('closed', () => { janela = null; vista = null; });
  await janela.loadURL(`${origem}/?t=${encodeURIComponent(lerSegredoSessao())}`);
}

ipcMain.handle('clave:escolher-pasta', async (_e, titulo) => {
  const r = await dialog.showOpenDialog(janela, { title: titulo || 'Escolher pasta', properties: ['openDirectory', 'createDirectory'] });
  return r.canceled ? null : r.filePaths[0];
});
ipcMain.handle('clave:abrir-pasta', async (_e, caminho) => {
  if (typeof caminho !== 'string' || !fs.existsSync(caminho) || !fs.statSync(caminho).isDirectory()) return false;
  return (await shell.openPath(caminho)) === '';
});
ipcMain.handle('clave:abrir-externo', async (_e, url) => {
  if (typeof url !== 'string' || !/^https?:\/\//.test(url)) return false;
  await shell.openExternal(url);
  return true;
});
ipcMain.handle('clave:reiniciar', async () => {
  // app.exit não passa pelo before-quit: o servidor tem que ser parado aqui
  saindo = true; salvarEstadoJanela();
  await pararServidorComCalma();
  fecharPonte();
  reabrir(); app.exit(0);
});
ipcMain.handle('clave:sair', () => app.quit());
// notificação do Windows (a interface só pede quando a janela está em segundo plano); clicar traz a janela
ipcMain.handle('clave:notificar', (_e, titulo, corpo) => {
  if (!Notification.isSupported() || (janela && janela.isFocused())) return false;
  const n = new Notification({ title: titulo.slice(0, 80) || 'Clave', body: corpo.slice(0, 200), icon: fs.existsSync(ICONE) ? ICONE : undefined });
  n.on('click', () => { if (janela) { if (janela.isMinimized()) janela.restore(); janela.show(); janela.focus(); } });
  n.show();
  if (janela && !janela.isFocused()) janela.flashFrame(true);
  return true;
});

// Certificado de cliente: sem tratar este evento, o Electron entrega sozinho o primeiro certificado do Windows (um
// e-CPF, por exemplo) a qualquer site que peça, inclusive a uma página que o Claude abriu no navegador do Code. O
// Clave nunca escolhe um: a conexão segue sem certificado (callback vazio). Vale para todas as vistas; a interface
// do Clave (http em 127.0.0.1) nunca pede certificado.
app.on('select-client-certificate', (event, _wc, _url, _lista, callback) => {
  event.preventDefault();
  callback();
});

// =====================================================================================================
// O navegador do modo Code
// =====================================================================================================
const PARTICAO = 'persist:clave-navegador';
const MUNDO = 1077;                                   // mundo isolado dos scripts do Clave (a página não mexe neles)
const LIMITES_PADRAO = { x: 0, y: 0, width: 1100, height: 800 };
let vista = null;
const nav = { visivel: false, erro: null, limites: null, congelando: 0, esperas: new Set(), navs: 0 };
let sessaoPronta = false;

const espera = (ms) => new Promise((r) => setTimeout(r, ms));
const httpOk = (url) => typeof url === 'string' && /^https?:\/\/[^\s]+$/i.test(url.trim());

// rótulos do menu da página no idioma do Clave (a configuração diz qual)
let idiomaCache = { quando: 0, ingles: false };
function emIngles() {
  try {
    const arq = path.join(DADOS, 'config.json');
    const quando = fs.statSync(arq).mtimeMs;
    if (quando !== idiomaCache.quando) idiomaCache = { quando, ingles: JSON.parse(fs.readFileSync(arq, 'utf8')).idioma === 'en' };
  } catch { /* sem configuração: português */ }
  return idiomaCache.ingles;
}
const r = (pt, en) => (emIngles() ? en : pt);

function prepararSessao() {
  if (sessaoPronta) return;
  sessaoPronta = true;
  const ses = session.fromPartition(PARTICAO);
  // câmera, microfone, localização, notificações, tela cheia...: nada. Só copiar para a área de transferência
  // (os botões "copiar" dos sites de documentação) passa.
  ses.setPermissionRequestHandler((_wc, permissao, decidir) => decidir(permissao === 'clipboard-sanitized-write'));
  ses.setPermissionCheckHandler((_wc, permissao) => permissao === 'clipboard-sanitized-write');
  ses.setDevicePermissionHandler(() => false);
  // sem "Electron/" e sem "Clave/" no navegador: vários sites recusam navegador que não reconhecem
  ses.setUserAgent(ses.getUserAgent().replace(/\s(Clave|clave|Electron)\/\S+/g, ''));
  // download: o Electron mostra a janela de salvar do Windows; quando acaba, a interface avisa
  ses.on('will-download', (_e, item) => {
    item.once('done', (_ev, estado) => pedirTela({ tipo: 'navegador', acao: 'download', nome: item.getFilename(), estado }));
  });
}

function pedirTela(pedido) {
  if (janela && !janela.isDestroyed()) janela.webContents.send('clave:pedido', pedido);
}

function paginaVazia() {
  const u = vista ? vista.webContents.getURL() : '';
  return !u || u === 'about:blank';
}

function estadoNav() {
  const wc = vista?.webContents;
  const url = wc && !paginaVazia() ? wc.getURL() : '';
  return {
    url, titulo: url ? wc.getTitle() : '', carregando: !!wc && wc.isLoading(),
    podeVoltar: !!wc && wc.navigationHistory.canGoBack(), podeAvancar: !!wc && wc.navigationHistory.canGoForward(),
    erro: nav.erro, visivel: nav.visivel, limites: nav.visivel ? nav.limites : null,
  };
}

// o mesmo estado para a ponte: lá "erro" é o código de erro da ação, então o erro de carga da página vai como
// erro_carga (senão um { erro: null } do estado apagaria o erro da ação ao juntar os dois)
function estadoPonte() {
  const { erro, ...resto } = estadoNav();
  return { ...resto, erro_carga: erro };
}

let avisoMarcado = null;
function avisarMudanca() {
  // vários eventos chegam juntos (começou, navegou, título): manda um só
  if (avisoMarcado) return;
  avisoMarcado = setTimeout(() => {
    avisoMarcado = null;
    if (janela && !janela.isDestroyed()) janela.webContents.send('clave:nav-mudou', estadoNav());
  }, 30);
}

function criarVista() {
  if (vista) return vista;
  if (!janela || janela.isDestroyed()) throw new Error('sem_janela');
  prepararSessao();
  vista = new WebContentsView({
    webPreferences: { partition: PARTICAO, sandbox: true, contextIsolation: true, nodeIntegration: false, webviewTag: false, spellcheck: true },
  });
  vista.setBackgroundColor('#ffffff');
  vista.setBounds(foraDaJanela(null));  // nasce fora da área da janela até a aba pedir um lugar
  janela.contentView.addChildView(vista);
  const wc = vista.webContents;
  wc.setWindowOpenHandler(({ url }) => {
    // janela nova e target=_blank abrem na mesma página
    if (httpOk(url)) setImmediate(() => wc.loadURL(url).catch(() => {}));
    return { action: 'deny' };
  });
  // só http e https: file:, javascript:, mailto: (abriria o programa de e-mail sem clique nenhum) e afins não passam
  const barrar = (e, url) => { if (!httpOk(url)) e.preventDefault(); };
  wc.on('will-navigate', barrar);
  wc.on('will-redirect', barrar);
  wc.on('did-start-navigation', (d) => {
    if (!d.isMainFrame || d.isSameDocument) return;
    nav.navs = (nav.navs || 0) + 1;
    nav.erro = null;
    avisarMudanca();
  });
  for (const ev of ['did-start-loading', 'did-stop-loading', 'did-navigate', 'did-navigate-in-page', 'page-title-updated']) wc.on(ev, avisarMudanca);
  wc.on('did-fail-load', (_e, codigo, descricao, url, principal) => {
    if (!principal || codigo === -3) return;  // -3: outra navegação tomou o lugar (redirecionamento, download)
    nav.erro = { codigo: descricao || String(codigo), numero: codigo, url };
    avisarMudanca();
  });
  wc.on('render-process-gone', (_e, d) => {
    if (d.reason === 'clean-exit') return;
    nav.erro = { codigo: 'travou', url: wc.getURL() };
    avisarMudanca();
  });
  wc.on('context-menu', (_e, p) => menuDaPagina(wc, p));
  wc.on('before-input-event', (e, input) => teclaNaPagina(e, input, wc));
  return vista;
}

// Esconder a vista é tirá-la da área da janela, do mesmo tamanho, em vez de setVisible(false): escondida assim, a
// página continua "à vista" para o Chromium e segue desenhando (com setVisible(false) ela parava de pintar e voltava
// em branco depois de mudar de tamanho, e a primeira foto falhava).
function foraDaJanela(lim) {
  return { x: -30000, y: 0, width: Math.max(320, lim?.width || LIMITES_PADRAO.width), height: Math.max(240, lim?.height || LIMITES_PADRAO.height) };
}

function mostrarVista(limites) {
  const v = criarVista();
  nav.congelando = 0;
  v.setBounds(limites);
  nav.limites = limites;
  nav.visivel = true;
  for (const fim of nav.esperas) fim();
}

function esconderVista() {
  if (!vista || !nav.visivel) return;
  // o teclado não pode ficar numa página que saiu de vista: volta para a interface do Clave
  if (vista.webContents.isFocused() && janela && !janela.isDestroyed()) janela.webContents.focus();
  vista.setBounds(foraDaJanela(nav.limites));
  nav.visivel = false;
}

function menuDaPagina(wc, p) {
  const itens = [];
  if (p.linkURL && httpOk(p.linkURL)) {
    itens.push({ label: r('Abrir o link aqui', 'Open link here'), click: () => wc.loadURL(p.linkURL).catch(() => {}) },
      { label: r('Abrir o link no navegador do computador', 'Open link in your browser'), click: () => shell.openExternal(p.linkURL) },
      { label: r('Copiar o endereço do link', 'Copy link address'), click: () => require('electron').clipboard.writeText(p.linkURL) },
      { type: 'separator' });
  }
  if (p.isEditable) itens.push({ role: 'cut', label: r('Recortar', 'Cut') });
  if (p.selectionText || p.isEditable) itens.push({ role: 'copy', label: r('Copiar', 'Copy') });
  if (p.isEditable) itens.push({ role: 'paste', label: r('Colar', 'Paste') }, { role: 'selectAll', label: r('Selecionar tudo', 'Select all') });
  if (itens.length && itens[itens.length - 1].type !== 'separator') itens.push({ type: 'separator' });
  itens.push(
    { label: r('Voltar', 'Back'), enabled: wc.navigationHistory.canGoBack(), click: () => wc.navigationHistory.goBack() },
    { label: r('Avançar', 'Forward'), enabled: wc.navigationHistory.canGoForward(), click: () => wc.navigationHistory.goForward() },
    { label: r('Recarregar', 'Reload'), click: () => wc.reload() },
    { label: r('Abrir esta página no navegador do computador', 'Open this page in your browser'), enabled: httpOk(wc.getURL()), click: () => shell.openExternal(wc.getURL()) },
    { type: 'separator' },
    { label: r('Inspecionar', 'Inspect'), click: () => wc.inspectElement(p.x, p.y) });
  Menu.buildFromTemplate(itens).popup({ window: janela });
}

function teclaNaPagina(e, input, wc) {
  if (input.type !== 'keyDown') return;
  const ctrl = input.control || input.meta;
  const k = input.key;
  if (ctrl && input.shift && (k === 'L' || k === 'l')) { e.preventDefault(); janela?.webContents.focus(); pedirTela({ tipo: 'navegador', acao: 'tecla', key: 'L', shift: true }); }
  else if (ctrl && !input.shift && (k === 'j' || k === 'J')) { e.preventDefault(); janela?.webContents.focus(); pedirTela({ tipo: 'navegador', acao: 'tecla', key: 'j', shift: false }); }
  else if (ctrl && !input.shift && (k === 'l' || k === 'L')) { e.preventDefault(); janela?.webContents.focus(); pedirTela({ tipo: 'navegador', acao: 'focar-endereco' }); }
  else if (k === 'F5' || (ctrl && (k === 'r' || k === 'R'))) { e.preventDefault(); wc.reload(); }
  else if (input.alt && k === 'ArrowLeft') { e.preventDefault(); if (wc.navigationHistory.canGoBack()) wc.navigationHistory.goBack(); }
  else if (input.alt && k === 'ArrowRight') { e.preventDefault(); if (wc.navigationHistory.canGoForward()) wc.navigationHistory.goForward(); }
  else if (k === 'Escape' && wc.isLoading()) wc.stop();
  else if (k === 'F12') { e.preventDefault(); wc.toggleDevTools(); }
}

function irPara(url) {
  if (!httpOk(url)) return { erro: 'url_invalida' };
  const wc = criarVista().webContents;
  nav.erro = null;
  wc.loadURL(url.trim()).catch(() => { /* o erro chega pelo did-fail-load */ });
  avisarMudanca();
  return { ok: true };
}

// ---------- pedidos da interface (só a janela do Clave fala aqui; a página do navegador não tem preload) ----------
const daJanela = (e) => !!janela && e.sender === janela.webContents;
ipcMain.handle('clave:nav-posicionar', (e, ret) => {
  if (!daJanela(e)) return false;
  if (!ret) { esconderVista(); return true; }
  const z = janela.webContents.getZoomFactor() || 1;
  const n = (v) => (Number.isFinite(Number(v)) ? Number(v) : NaN);
  const lim = { x: Math.round(n(ret.x) * z), y: Math.round(n(ret.y) * z), width: Math.round(n(ret.width) * z), height: Math.round(n(ret.height) * z) };
  if (![lim.x, lim.y, lim.width, lim.height].every(Number.isFinite) || lim.width < 2 || lim.height < 2) { esconderVista(); return true; }
  mostrarVista(lim);
  return true;
});
// foto da página para a interface pôr no lugar enquanto algo do app fica por cima; depois esconde a vista
ipcMain.handle('clave:nav-congelar', async (e) => {
  if (!daJanela(e)) return null;
  if (!vista || !nav.visivel) { esconderVista(); return null; }
  const meu = Date.now() + Math.random();
  nav.congelando = meu;
  let url = null;
  try {
    const img = await Promise.race([vista.webContents.capturePage(), espera(180).then(() => null)]);
    if (img && !img.isEmpty()) url = 'data:image/jpeg;base64,' + img.toJPEG(88).toString('base64');
  } catch { /* sem foto */ }
  if (nav.congelando === meu) { esconderVista(); nav.congelando = 0; }
  return url;
});
ipcMain.handle('clave:nav-ir', (e, url) => (daJanela(e) ? irPara(String(url || '')) : { erro: 'origem' }));
ipcMain.handle('clave:nav-voltar', (e) => { if (daJanela(e) && vista?.webContents.navigationHistory.canGoBack()) vista.webContents.navigationHistory.goBack(); });
ipcMain.handle('clave:nav-avancar', (e) => { if (daJanela(e) && vista?.webContents.navigationHistory.canGoForward()) vista.webContents.navigationHistory.goForward(); });
ipcMain.handle('clave:nav-recarregar', (e) => { if (daJanela(e) && vista) { nav.erro = null; vista.webContents.reload(); } });
ipcMain.handle('clave:nav-parar', (e) => { if (daJanela(e) && vista) vista.webContents.stop(); });
ipcMain.handle('clave:nav-estado', (e) => (daJanela(e) ? estadoNav() : null));

// ---------- scripts que rodam na página, num mundo isolado (a página não vê nem muda as funções deles) ----------
const KIT = String.raw`
const __limpa = (s) => String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
function __percorrer(raiz, fn) {
  const w = document.createTreeWalker(raiz, NodeFilter.SHOW_ELEMENT);
  let n = w.nextNode();
  while (n) {
    if (fn(n) === false) return false;
    if (n.shadowRoot && __percorrer(n.shadowRoot, fn) === false) return false;
    n = w.nextNode();
  }
  return true;
}
// Os números da última leitura ficam numa lista DESTE mundo isolado (window aqui não é o window da página), não num
// atributo no DOM: a página não vê a lista, não põe número nos elementos dela e não troca um número de lugar (um
// atributo, mesmo com nome aleatório, apareceria para um MutationObserver da página na primeira leitura).
function __achar(ref) {
  const lista = window.__claveRefs;
  const e = lista && lista[Number(ref)];
  return e && e.isConnected ? e : null;
}
// o clique e a digitação só valem na página e no elemento que a pessoa aprovou
function __confere(e, esperado) {
  if (!esperado || typeof esperado !== 'object' || !esperado.url) return { erro: 'sem_conferencia' };
  let quer;
  try { quer = new URL(String(esperado.url)); } catch { return { erro: 'sem_conferencia' }; }
  if (location.origin !== quer.origin || location.pathname !== quer.pathname) return { erro: 'pagina_mudou', url: location.href };
  if (!e) return { erro: 'ref_sumiu' };
  const d = __descrever(e);
  if (d.papel !== String(esperado.papel || '') || d.nome !== String(esperado.nome || '')) return { erro: 'elemento_mudou', ...d };
  return null;
}
// o texto dos rótulos do campo (label, aria-labelledby): "<label>Senha</label><input name=c1>" é campo de senha
function __rotulos(e) {
  const partes = [];
  if (e.labels) for (const l of e.labels) partes.push(l.textContent || '');
  const ids = e.getAttribute('aria-labelledby');
  if (ids) for (const id of ids.split(/\s+/)) { const x = id && document.getElementById(id); if (x) partes.push(x.textContent || ''); }
  return partes.join(' ');
}
function __visivel(e) {
  const r = e.getBoundingClientRect();
  if (r.width < 1 || r.height < 1) return false;
  if (e.checkVisibility && !e.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false;
  return true;
}
function __dentroDe(n, alvo) {
  while (n) { if (n === alvo) return true; n = n.parentNode || n.host; }
  return false;
}
function __tipo(e) {
  if (e.tagName === 'INPUT') return (e.getAttribute('type') || 'text').toLowerCase();
  return e.tagName === 'SELECT' ? 'select' : e.tagName === 'TEXTAREA' ? 'textarea' : '';
}
function __sensivel(e) {
  const tipo = __tipo(e);
  if (tipo === 'password') return 'senha';
  const ac = (e.getAttribute('autocomplete') || '').toLowerCase();
  if (/(^|\s)(current-password|new-password|one-time-code)(\s|$)/.test(ac)) return 'senha';
  if (/(^|\s)cc-[a-z-]+/.test(ac)) return 'cartao';
  if (e.tagName !== 'INPUT' && e.tagName !== 'TEXTAREA' && !e.isContentEditable) return '';
  const pistas = [e.getAttribute('name'), e.id, e.getAttribute('aria-label'), e.getAttribute('placeholder'),
    e.getAttribute('title'), e.getAttribute('data-testid'), e.getAttribute('data-test'), __rotulos(e)]
    .filter(Boolean).join(' ').toLowerCase();
  if (/(card.?num|cardnumber|credit.?card|debit.?card|\bcc.?(num|number|exp|csc|cvv)|ccnum|cvv|cvc|\bcsc\b|security.?code|card.?code|card.?holder|cart[aã]o|c[oó]digo.?de.?seguran)/.test(pistas)) return 'cartao';
  if (/(password|passwd|passcode|pass.?phrase|senha|\bpin\b|\botp\b|2fa|one.?time|c[oó]digo.?de.?acesso|access.?code)/.test(pistas)) return 'senha';
  return '';
}
function __papel(e) {
  const r = e.getAttribute('role');
  if (r) return r;
  const tag = e.tagName;
  if (tag === 'A') return 'link';
  if (tag === 'BUTTON' || tag === 'SUMMARY') return 'button';
  if (tag === 'SELECT') return e.multiple ? 'listbox' : 'combobox';
  if (tag === 'TEXTAREA') return 'textbox';
  if (tag === 'INPUT') {
    return { checkbox: 'checkbox', radio: 'radio', submit: 'button', button: 'button', reset: 'button', image: 'button',
      range: 'slider', number: 'spinbutton', search: 'searchbox', file: 'file' }[__tipo(e)] || 'textbox';
  }
  if (e.isContentEditable) return 'textbox';
  return 'generic';
}
function __nome(e) {
  let s = __limpa(e.getAttribute('aria-label'));
  if (!s && e.getAttribute('aria-labelledby')) {
    s = __limpa(e.getAttribute('aria-labelledby').split(/\s+/).map((id) => { const x = document.getElementById(id); return x ? (x.innerText || x.textContent) : ''; }).join(' '));
  }
  if (!s && e.labels && e.labels.length) {
    // o texto do rótulo sem o próprio campo (um select dentro do label traria todas as opções junto)
    s = __limpa([...e.labels].map((l) => {
      const c = l.cloneNode(true);
      c.querySelectorAll('select, input, textarea, button, option, datalist').forEach((x) => x.remove());
      return c.textContent;
    }).join(' '));
  }
  const tag = e.tagName, tipo = __tipo(e);
  if (!s && tag === 'INPUT' && ['submit', 'button', 'reset'].includes(tipo)) s = __limpa(e.value);
  if (!s && tag === 'INPUT' && tipo === 'image') s = __limpa(e.getAttribute('alt'));
  if (!s && !['INPUT', 'TEXTAREA', 'SELECT'].includes(tag)) s = __limpa(e.innerText || e.textContent);
  if (!s) s = __limpa(e.getAttribute('placeholder')) || __limpa(e.getAttribute('title'));
  if (!s && e.querySelector) { const img = e.querySelector('img[alt], svg[aria-label]'); if (img) s = __limpa(img.getAttribute('alt') || img.getAttribute('aria-label')); }
  if (!s) s = __limpa(e.getAttribute('name') || e.id);
  return s.length > 100 ? s.slice(0, 99) + '…' : s;
}
function __descrever(e) {
  const tag = e.tagName, tipo = __tipo(e), sens = __sensivel(e);
  const d = { papel: __papel(e), nome: __nome(e), tipo };
  if (sens) d.sensivel = sens;
  if (tag === 'A' && e.href && !/^javascript:/i.test(e.href)) d.href = String(e.href).slice(0, 200);
  if (tipo === 'checkbox' || tipo === 'radio') d.marcado = !!e.checked;
  else if (e.getAttribute('aria-checked') !== null) d.marcado = e.getAttribute('aria-checked') === 'true';
  else if (tag === 'SELECT') d.valor = [...e.selectedOptions].map((o) => __limpa(o.textContent)).join(', ').slice(0, 120);
  else if (!sens && (tag === 'TEXTAREA' || (tag === 'INPUT' && !['submit', 'button', 'reset', 'image', 'file', 'hidden'].includes(tipo)))) d.valor = String(e.value || '').slice(0, 120);
  else if (!sens && e.isContentEditable) d.valor = __limpa(e.innerText).slice(0, 120);
  if (e.disabled || e.getAttribute('aria-disabled') === 'true') d.desativado = true;
  return d;
}
function __campo(e) {
  // um combobox ou um contêiner com o campo de verdade dentro: digita no campo
  if (e.tagName === 'INPUT' || e.tagName === 'TEXTAREA' || e.isContentEditable) return e;
  return (e.querySelector && e.querySelector('input:not([type=hidden]), textarea, [contenteditable=""], [contenteditable="true"]')) || e;
}
`;

const SELETOR = 'a[href], button, input, select, textarea, summary, [role=button], [role=link], [role=checkbox], [role=radio], ' +
  '[role=tab], [role=menuitem], [role=menuitemcheckbox], [role=menuitemradio], [role=option], [role=switch], [role=combobox], ' +
  '[role=textbox], [role=searchbox], [role=slider], [role=spinbutton], [contenteditable=""], [contenteditable="true"], [onclick], ' +
  '[tabindex]:not([tabindex="-1"])';

const script = (corpo, ...args) => `(() => {${KIT}\nreturn (${corpo})(${args.map((a) => JSON.stringify(a)).join(', ')});\n})()`;

const LER = `() => {
  const refs = [null], marcados = new Set();
  const itens = []; let cortados = 0;
  const marcadoAcima = (e) => { for (let p = e.parentElement; p; p = p.parentElement) if (marcados.has(p)) return p; return null; };
  __percorrer(document, (e) => {
    if (!e.matches(${JSON.stringify(SELETOR)})) return;
    if (__tipo(e) === 'hidden') return;
    if (e.closest('[aria-hidden="true"], [inert]')) return;
    let vis = __visivel(e);
    if (!vis && e.labels && [...e.labels].some(__visivel)) vis = true;
    if (!vis) return;
    const pai = marcadoAcima(e);
    if (pai && (pai.tagName === 'A' || pai.tagName === 'BUTTON' || /^(button|link)$/.test(pai.getAttribute('role') || ''))) return;
    if (itens.length >= 300) { cortados++; return; }
    const ref = itens.length + 1;
    refs[ref] = e;
    marcados.add(e);
    itens.push({ ref, ...__descrever(e) });
  });
  window.__claveRefs = refs;
  let texto = document.body ? (document.body.innerText || '') : '';
  texto = texto.replace(/[ \\t]+\\n/g, '\\n').replace(/\\n{3,}/g, '\\n\\n').trim();
  const se = document.scrollingElement || document.documentElement;
  return { url: location.href, titulo: document.title, texto: texto.slice(0, 20000), texto_cortado: texto.length > 20000,
    texto_total: texto.length, elementos: itens, elementos_cortados: cortados,
    rolagem: { y: Math.round(se.scrollTop), altura: se.scrollHeight, janela: innerHeight } };
}`;

const DESCREVER = `(ref) => {
  const e = __achar(ref);
  if (!e) return { erro: 'ref_sumiu' };
  return { url: location.href, titulo: document.title, ...__descrever(e) };
}`;

const PREPARAR_CLIQUE = `(ref, esperado) => {
  const e = __achar(ref);
  const ruim = __confere(e, esperado);
  if (ruim) return ruim;
  const d = __descrever(e);
  if (e.tagName === 'SELECT') return { erro: 'lista', ...d };
  if (__tipo(e) === 'file') return { erro: 'arquivo', ...d };
  let alvo = e;
  if (!__visivel(e) && e.labels) { const l = [...e.labels].find(__visivel); if (l) alvo = l; }
  alvo.scrollIntoView({ block: 'center', inline: 'center', behavior: 'instant' });
  const r = alvo.getBoundingClientRect();
  const x = r.left + r.width / 2, y = r.top + r.height / 2;
  const dentro = r.width >= 1 && r.height >= 1 && x >= 0 && y >= 0 && x < innerWidth && y < innerHeight;
  let topo = dentro ? document.elementFromPoint(x, y) : null;
  while (topo && topo.shadowRoot) { const d2 = topo.shadowRoot.elementFromPoint(x, y); if (!d2 || d2 === topo) break; topo = d2; }
  window.__claveAlvo = alvo;
  window.__claveClique = null;
  if (!window.__claveOuvindoClique) {
    window.__claveOuvindoClique = true;
    // um clique do mouse que chegue atrasado, depois que o Clave já clicou direto no elemento, é barrado: senão o
    // elemento receberia dois cliques (duas compras, dois envios)
    const barrar = (ev) => {
      if (!ev.isTrusted || !(window.__claveBarrarMouse > Date.now())) return false;
      ev.preventDefault(); ev.stopImmediatePropagation();
      return true;
    };
    for (const tipo of ['pointerdown', 'mousedown', 'pointerup', 'mouseup']) window.addEventListener(tipo, barrar, true);
    window.addEventListener('click', (ev) => {
      if (barrar(ev) || !ev.isTrusted) return;
      const caminho = ev.composedPath ? ev.composedPath() : [ev.target];
      window.__claveClique = window.__claveAlvo && caminho.includes(window.__claveAlvo) ? 'alvo' : 'outro';
    }, true);
  }
  return { x, y, dentro, acerta: !!topo && __dentroDe(topo, alvo), ...d };
}`;

const CLIQUE_CONFERIR = `() => window.__claveClique || null`;
const CLIQUE_DIRETO = `(barrarMouse) => {
  const a = window.__claveAlvo;
  if (!a || !a.isConnected) return false;
  if (barrarMouse) window.__claveBarrarMouse = Date.now() + 1500;
  a.click();
  return true;
}`;

const DIGITAR_PREPARAR = `(ref, texto, esperado) => {
  const e = __achar(ref);
  const ruim = __confere(e, esperado);
  if (ruim) return ruim;
  const d = __descrever(e);
  if (d.sensivel === 'senha') return { erro: 'campo_senha', ...d };
  if (d.sensivel === 'cartao') return { erro: 'campo_cartao', ...d };
  if (e.tagName === 'SELECT') {
    if (e.disabled) return { erro: 'desativado', ...d };
    const quer = __limpa(texto).toLowerCase();
    const ops = [...e.options];
    const op = quer && (ops.find((o) => __limpa(o.textContent).toLowerCase() === quer || String(o.value).toLowerCase() === quer)
      || ops.find((o) => __limpa(o.textContent).toLowerCase().includes(quer)));
    if (!op) return { erro: 'opcao_nao_achada', opcoes: ops.slice(0, 40).map((o) => __limpa(o.textContent)), ...d };
    e.value = op.value; op.selected = true;
    e.dispatchEvent(new Event('input', { bubbles: true }));
    e.dispatchEvent(new Event('change', { bubbles: true }));
    return { escolhido: __limpa(op.textContent), ...d };
  }
  const c = __campo(e);
  const cd = c === e ? d : __descrever(c);
  if (cd.sensivel === 'senha') return { erro: 'campo_senha', ...cd };
  if (cd.sensivel === 'cartao') return { erro: 'campo_cartao', ...cd };
  const tipo = __tipo(c);
  const textual = c.tagName === 'TEXTAREA' || c.isContentEditable
    || (c.tagName === 'INPUT' && !['checkbox', 'radio', 'submit', 'button', 'reset', 'image', 'file', 'range', 'color', 'hidden'].includes(tipo));
  if (!textual) return { erro: 'nao_digitavel', ...d };
  if (c.disabled || c.readOnly || c.getAttribute('aria-readonly') === 'true') return { erro: 'desativado', ...d };
  c.scrollIntoView({ block: 'center', behavior: 'instant' });
  c.focus();
  if (typeof c.select === 'function' && 'value' in c) c.select();
  else { const s = getSelection(); const rg = document.createRange(); rg.selectNodeContents(c); s.removeAllRanges(); s.addRange(rg); }
  window.__claveCampo = c;
  window.__claveAntes = 'value' in c && !c.isContentEditable ? String(c.value) : String(c.innerText || '');
  window.__claveTecla = false;
  window.__claveBarrarTexto = 0;
  window.__claveBarrarEnter = 0;
  if (!window.__claveOuvindoTecla) {
    window.__claveOuvindoTecla = true;
    // depois do plano B (o Clave pôs o texto ou o Enter direto), o texto ou o Enter do teclado que chegar atrasado é
    // barrado: senão o campo ficaria com o texto em dobro ou o formulário seria enviado duas vezes
    window.addEventListener('keydown', (ev) => {
      if (ev.key !== 'Enter' || !ev.isTrusted) return;
      if (window.__claveBarrarEnter > Date.now()) { ev.preventDefault(); ev.stopImmediatePropagation(); return; }
      window.__claveTecla = true;
    }, true);
    window.addEventListener('beforeinput', (ev) => {
      if (ev.isTrusted && window.__claveBarrarTexto > Date.now()) { ev.preventDefault(); ev.stopImmediatePropagation(); }
    }, true);
  }
  return { ok: true, ...d };
}`;

const DIGITAR_CONFERIR = `(texto) => {
  const c = window.__claveCampo;
  if (!c || !c.isConnected) return { sumiu: true };
  const valor = 'value' in c && c.tagName !== 'SELECT' && !c.isContentEditable ? String(c.value) : String(c.innerText || '');
  const igual = (a) => String(a).replace(/\\s+/g, ' ').trim();
  // igual ao pedido, ou mudou (campo com máscara reescreve o que entra: "31999" vira "(31) 999")
  const ok = igual(valor) === igual(texto) || (valor !== window.__claveAntes && igual(valor) !== '');
  return { ok, valor: valor.slice(0, 200) };
}`;

const DIGITAR_DIRETO = `(texto) => {
  const c = window.__claveCampo;
  if (!c || !c.isConnected) return false;
  c.focus();
  if ('value' in c && !c.isContentEditable) {
    const proto = c.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(c, texto);
    c.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: texto }));
    c.dispatchEvent(new Event('change', { bubbles: true }));
  } else {
    const s = getSelection(); const rg = document.createRange(); rg.selectNodeContents(c); s.removeAllRanges(); s.addRange(rg);
    if (!document.execCommand('insertText', false, texto)) { c.textContent = texto; c.dispatchEvent(new InputEvent('input', { bubbles: true })); }
  }
  window.__claveBarrarTexto = Date.now() + 1500;
  return true;
}`;

const TECLA_CONFERIR = `() => !!window.__claveTecla`;
const ENTER_DIRETO = `() => {
  const c = window.__claveCampo;
  if (!c || !c.isConnected) return false;
  window.__claveBarrarEnter = Date.now() + 1500;
  const o = { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true };
  const seguiu = c.dispatchEvent(new KeyboardEvent('keydown', o));
  c.dispatchEvent(new KeyboardEvent('keypress', o));
  c.dispatchEvent(new KeyboardEvent('keyup', o));
  const f = c.form;
  if (seguiu && f) { if (f.requestSubmit) f.requestSubmit(); else f.submit(); }
  return true;
}`;

const ROLAR = `(direcao) => {
  const se = document.scrollingElement || document.documentElement;
  let el = se;
  if (se.scrollHeight <= innerHeight + 4) {
    let area = 0;
    for (const e of document.querySelectorAll('body *')) {
      if (e.scrollHeight <= e.clientHeight + 4) continue;
      const oy = getComputedStyle(e).overflowY;
      if (oy !== 'auto' && oy !== 'scroll' && oy !== 'overlay') continue;
      const r = e.getBoundingClientRect();
      if (r.width * r.height > area) { area = r.width * r.height; el = e; }
    }
  }
  const tela = el === se ? innerHeight : el.clientHeight;
  const passo = Math.max(40, Math.round(tela * 0.85));
  if (direcao === 'baixo') el.scrollBy({ top: passo, behavior: 'instant' });
  else if (direcao === 'cima') el.scrollBy({ top: -passo, behavior: 'instant' });
  else if (direcao === 'topo') el.scrollTo({ top: 0, behavior: 'instant' });
  else el.scrollTo({ top: el.scrollHeight, behavior: 'instant' });
  return { y: Math.round(el.scrollTop), altura: el.scrollHeight, janela: tela, url: location.href };
}`;

async function naPagina(codigo, { limite = 8000, gesto = false } = {}) {
  const wc = vista?.webContents;
  if (!wc) throw new Error('sem_pagina');
  return Promise.race([
    wc.executeJavaScriptInIsolatedWorld(MUNDO, [{ code: codigo }], gesto),
    espera(limite).then(() => { throw new Error('tempo_script'); }),
  ]);
}

// depois de um clique ou de um Enter: espera a página reagir (se começou a carregar, até terminar)
async function esperarAssentar(urlAntes) {
  const wc = vista.webContents;
  await espera(400);
  const fim = Date.now() + 15000;
  while (Date.now() < fim && wc.isLoading()) await espera(150);
  return { navegou: wc.getURL() !== urlAntes, ...estadoPonte() };
}

async function carregar(url, limiteMs) {
  const wc = criarVista().webContents;
  nav.erro = null;
  let falha = null;
  const fim = Date.now() + limiteMs;  // um prazo só para tudo: a ponte também tem o dela
  const carga = wc.loadURL(url).then(() => 'ok', (e) => { falha = e; return 'falhou'; });
  const resultado = await Promise.race([carga, espera(limiteMs).then(() => 'tempo')]);
  if (resultado === 'falhou') {
    const codigo = String(falha?.code || falha?.message || '');
    if (codigo.includes('ERR_ABORTED')) {
      // outra navegação tomou o lugar (redirecionamento por script, download): espera ela, dentro do mesmo prazo
      await espera(300);
      while (Date.now() < fim && wc.isLoading()) await espera(150);
    } else {
      return { erro: 'carregar', detalhe: falha?.code || codigo, url };
    }
  }
  if (nav.erro) return { erro: 'carregar', detalhe: nav.erro.codigo, url };
  return { ok: true, tempo_esgotado: resultado === 'tempo', ...estadoPonte() };
}

// a foto da página como PNG. A janela do Clave pode estar atrás de outras ou a aba escondida: aí o Chromium ainda não
// tem um quadro pronto e a primeira captura falha ("UnknownVizError", "surface not available"). Tenta de novo e, se
// não der, pede a foto pelo protocolo de depuração, que desenha um quadro novo para isso.
async function fotoDaPagina(wc) {
  let ultimoErro = 'print_vazio';
  for (let tentativa = 0; tentativa < 3; tentativa += 1) {
    try {
      // cada tentativa tem prazo: um capturePage que nunca responde não segura a fila da ponte
      const img = await Promise.race([wc.capturePage({ x: 0, y: 0, width: 0, height: 0 }, { stayHidden: !nav.visivel }),
        espera(3000).then(() => { throw new Error('capturePage sem resposta'); })]);
      if (img && !img.isEmpty()) return img;
    } catch (e) { ultimoErro = String(e?.message || e); }
    wc.invalidate();
    await espera(250);
  }
  const dbg = wc.debugger;
  const jaLigado = dbg.isAttached();
  try {
    if (!jaLigado) dbg.attach('1.3');
    const r = await Promise.race([dbg.sendCommand('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false }),
      espera(6000).then(() => null)]);
    if (r?.data) return nativeImage.createFromBuffer(Buffer.from(r.data, 'base64'));
  } catch (e) { ultimoErro = String(e?.message || e); } finally {
    if (!jaLigado) { try { dbg.detach(); } catch { /* já solto */ } }
  }
  throw new Error(ultimoErro);
}

async function tirarPrint() {
  if (!vista || paginaVazia()) return { erro: 'sem_pagina' };
  let img;
  try { img = await fotoDaPagina(vista.webContents); } catch (e) { return { erro: 'print_vazio', detalhe: String(e.message || e) }; }
  if (img.getSize().width > 1280) img = img.resize({ width: 1280, quality: 'good' });
  let png = img.toPNG();
  let largura = png.readUInt32BE(16), altura = png.readUInt32BE(20);
  if (largura > 1280) {
    img = nativeImage.createFromBuffer(png).resize({ width: 1280, quality: 'good' });
    png = img.toPNG();
    largura = png.readUInt32BE(16); altura = png.readUInt32BE(20);
  }
  return { png: png.toString('base64'), largura, altura, ...estadoPonte() };
}

const mudouDePagina = (wc, navsAntes, urlAntes) => (nav.navs || 0) !== navsAntes || wc.getURL() !== urlAntes;

// espera uma condição na página por até `ms`, perguntando de pouco em pouco (o evento do mouse ou do teclado chega
// ao processo da página depois de um tempo que varia com a carga do computador)
async function esperarNaPagina(codigo, ms, pronto, wc, navsAntes, urlAntes) {
  const fim = Date.now() + ms;
  for (;;) {
    if (mudouDePagina(wc, navsAntes, urlAntes)) return { navegou: true };
    let v;
    try { v = await naPagina(codigo, { limite: 1000 }); } catch { return { navegou: true }; }
    if (pronto(v)) return { valor: v };
    if (Date.now() >= fim) return { valor: v, esgotou: true };
    await espera(60);
  }
}

async function clicar(ref, esperado) {
  if (!vista || paginaVazia()) return { erro: 'sem_pagina' };
  const wc = vista.webContents;
  const navsAntes = nav.navs || 0, urlAntes = wc.getURL();
  const p = await naPagina(script(PREPARAR_CLIQUE, ref, esperado));
  if (!p || p.erro) return p || { erro: 'ref_sumiu' };
  let metodo = 'direto', ondeCaiu = null, mandouMouse = false;
  if (nav.visivel && p.dentro && p.acerta && !mudouDePagina(wc, navsAntes, urlAntes)) {
    // clique de verdade, com o mouse, no meio do elemento
    const x = Math.round(p.x), y = Math.round(p.y);
    wc.sendInputEvent({ type: 'mouseMove', x, y });
    wc.sendInputEvent({ type: 'mouseDown', x, y, button: 'left', clickCount: 1 });
    wc.sendInputEvent({ type: 'mouseUp', x, y, button: 'left', clickCount: 1 });
    mandouMouse = true;
    const r = await esperarNaPagina(`(${CLIQUE_CONFERIR})()`, 1200, (v) => v === 'alvo' || v === 'outro', wc, navsAntes, urlAntes);
    if (r.navegou) { metodo = 'mouse'; ondeCaiu = 'navegou'; } else if (!r.esgotou) { metodo = 'mouse'; ondeCaiu = r.valor; }
  }
  if (metodo === 'direto') {
    // o mouse não chegou (vista escondida, elemento coberto ou fora da tela): clica direto no elemento. Se o mouse
    // foi mandado e ainda não chegou, o clique dele que chegar atrasado é barrado (nada de dois cliques)
    let foi = false;
    try { foi = await naPagina(`(${CLIQUE_DIRETO})(${mandouMouse})`, { limite: 3000, gesto: true }); } catch { foi = true; /* navegou no meio */ }
    if (!foi) return mudouDePagina(wc, navsAntes, urlAntes) ? { erro: 'pagina_mudou', url: wc.getURL() } : { erro: 'ref_sumiu' };
  }
  const depois = await esperarAssentar(urlAntes);
  const base = { metodo, papel: p.papel, nome: p.nome, tipo: p.tipo };
  // o mouse acertou outro elemento (algo apareceu por cima, a página mexeu o botão): não é sucesso, e não clica de
  // novo (o outro elemento já recebeu um clique)
  if (ondeCaiu === 'outro') return { ...base, ...depois, erro: 'clique_em_outro' };
  return { ok: true, coberto: !!(p.dentro && !p.acerta), clique: ondeCaiu, ...base, ...depois };
}

async function digitar(ref, texto, enter, esperado) {
  if (!vista || paginaVazia()) return { erro: 'sem_pagina' };
  const wc = vista.webContents;
  const navsAntes = nav.navs || 0, urlAntes = wc.getURL();
  const p = await naPagina(script(DIGITAR_PREPARAR, ref, texto, esperado));
  if (!p || p.erro) return p || { erro: 'ref_sumiu' };
  const base = { papel: p.papel, nome: p.nome, tipo: p.tipo };
  if (p.escolhido !== undefined) return { ok: true, escolhido: p.escolhido, ...base, ...(await esperarAssentar(urlAntes)) };
  let metodo = 'teclado';
  try { await Promise.race([wc.insertText(texto), espera(3000)]); } catch { /* cai no plano B abaixo */ }
  // espera o texto aparecer no campo (até 1 s) antes do plano B, para não digitar duas vezes
  const conf = await esperarNaPagina(script(DIGITAR_CONFERIR, texto), 1000, (v) => !!v && (v.ok || v.sumiu), wc, navsAntes, urlAntes);
  if (!conf.navegou && (!conf.valor || (!conf.valor.ok && !conf.valor.sumiu))) {
    metodo = 'direto';
    await naPagina(script(DIGITAR_DIRETO, texto), { limite: 3000, gesto: true });
  }
  if (enter && !mudouDePagina(wc, navsAntes, urlAntes)) {
    wc.sendInputEvent({ type: 'keyDown', keyCode: 'Return' });
    wc.sendInputEvent({ type: 'char', keyCode: '\r' });
    wc.sendInputEvent({ type: 'keyUp', keyCode: 'Return' });
    const viu = await esperarNaPagina(`(${TECLA_CONFERIR})()`, 1000, (v) => v === true, wc, navsAntes, urlAntes);
    if (!viu.navegou && viu.valor !== true) {
      // o Enter do teclado não chegou: envia direto (e um Enter atrasado é barrado)
      try { await naPagina(`(${ENTER_DIRETO})()`, { limite: 3000, gesto: true }); } catch { /* navegou no meio */ }
    }
  }
  return { ok: true, metodo, ...base, ...(await esperarAssentar(urlAntes)) };
}

// tira a página da frente (um site negado não fica aberto); a pessoa ainda pode voltar pelo botão
async function emBranco() {
  if (!vista) return { ok: true, ...estadoPonte() };
  const wc = vista.webContents;
  try { wc.stop(); } catch { /* nada carregando */ }
  await Promise.race([wc.loadURL('about:blank').catch(() => {}), espera(5000)]);
  nav.erro = null;
  avisarMudanca();
  return { ok: true, ...estadoPonte() };
}

// "Sair da conta" e o botão das Configurações: apaga cookies, logins (inclusive o cache de autenticação HTTP),
// armazenamento, service workers e cache da sessão do navegador do Code, e o histórico da vista
async function limparDados() {
  if (vista) {
    await emBranco();
    try { vista.webContents.navigationHistory.clear(); } catch { /* sem histórico */ }
  }
  const ses = session.fromPartition(PARTICAO);
  if (typeof ses.clearData === 'function') await ses.clearData();
  else await ses.clearStorageData();
  await ses.clearCache();
  await ses.clearAuthCache();
  try { await ses.clearHostResolverCache(); } catch { /* não é importante */ }
  avisarMudanca();
  return { ok: true };
}

async function voltarPagina() {
  if (!vista || !vista.webContents.navigationHistory.canGoBack()) return { erro: 'sem_voltar' };
  const wc = vista.webContents;
  const urlAntes = wc.getURL();
  wc.navigationHistory.goBack();
  return { ok: true, ...(await esperarAssentar(urlAntes)) };
}

async function pedirMostrar(claude) {
  if (!janela || janela.isDestroyed()) return { visivel: false };
  pedirTela({ tipo: 'navegador', acao: 'mostrar', claude: !!claude });
  // espera a aba aparecer e pôr a vista no lugar (sem página aberta ela não põe: aí não adianta esperar muito)
  const limite = paginaVazia() ? 300 : 1500;
  if (!nav.visivel) {
    await new Promise((ok) => {
      const fim = () => { nav.esperas.delete(fim); clearTimeout(tm); ok(); };
      const tm = setTimeout(fim, limite);
      nav.esperas.add(fim);
    });
    await espera(nav.visivel ? 120 : 0);  // um respiro para a página desenhar no tamanho novo
  }
  return { visivel: nav.visivel };
}

async function acaoDaPonte(d) {
  switch (d.acao) {
    case 'estado': return estadoPonte();
    case 'mostrar': return pedirMostrar(d.claude);
    case 'abrir':
      if (!httpOk(d.url)) return { erro: 'url_invalida' };
      return carregar(String(d.url).trim(), 20000);
    case 'ler':
      if (!vista || paginaVazia()) return { erro: 'sem_pagina' };
      return { ...(await naPagina(script(LER), { limite: 15000 })), carregando: vista.webContents.isLoading() };
    case 'descrever':
      if (!vista || paginaVazia()) return { erro: 'sem_pagina' };
      return naPagina(script(DESCREVER, Number(d.ref)));
    case 'print': return tirarPrint();
    // o servidor manda a página e o elemento que a pessoa aprovou ("esperado"): sem isso, nada é clicado
    case 'clicar': return clicar(Number(d.ref), d.esperado);
    case 'digitar': return digitar(Number(d.ref), String(d.texto ?? ''), !!d.enter, d.esperado);
    case 'em_branco': return emBranco();
    case 'limpar': return limparDados();
    case 'rolar':
      if (!vista || paginaVazia()) return { erro: 'sem_pagina' };
      if (!['baixo', 'cima', 'topo', 'fim'].includes(d.direcao)) return { erro: 'direcao' };
      return naPagina(script(ROLAR, d.direcao));
    case 'voltar': return voltarPagina();
    case 'avancar':
      if (!vista || !vista.webContents.navigationHistory.canGoForward()) return { erro: 'sem_avancar' };
      {
        const urlAntes = vista.webContents.getURL();
        vista.webContents.navigationHistory.goForward();
        return { ok: true, ...(await esperarAssentar(urlAntes)) };
      }
    default: return { erro: 'acao_desconhecida' };
  }
}

// ---------- a ponte HTTP para o servidor Python ----------
const ponte = { porta: 0, token: crypto.randomBytes(32).toString('hex'), servidor: null, fila: Promise.resolve() };
const ARQ_PONTE = path.join(DADOS, 'ponte.json');

function mesmoToken(a) {
  const h = (s) => crypto.createHash('sha256').update(String(s || '')).digest();
  return crypto.timingSafeEqual(h(a), h(ponte.token));
}

function enfileirar(fn) {
  const p = ponte.fila.then(fn, fn);
  ponte.fila = p.catch(() => {});
  return p;
}

// prazo de cada ação na fila (um pouco menor que o do servidor Python, para a resposta chegar limpa): um capturePage
// ou um insertText que nunca responde não trava o navegador do Claude para sempre
const PRAZO_ACAO = {
  estado: 4000, mostrar: 4000, descrever: 10000, abrir: 26000, ler: 17000, print: 19000, clicar: 26000,
  digitar: 26000, rolar: 10000, voltar: 22000, avancar: 22000, em_branco: 10000, limpar: 35000,
};

function comPrazo(promessa, acao) {
  let tm = null;
  const prazo = new Promise((ok) => { tm = setTimeout(() => ok({ erro: 'tempo_esgotado', detalhe: String(acao || '') }), PRAZO_ACAO[acao] || 15000); });
  return Promise.race([Promise.resolve(promessa), prazo]).finally(() => clearTimeout(tm));
}

function atenderPonte(req, res) {
  const responder = (status, obj) => {
    const corpo = Buffer.from(JSON.stringify(obj));
    res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': corpo.length, 'Cache-Control': 'no-store' });
    res.end(corpo);
  };
  const host = String(req.headers.host || '');
  if (host !== `127.0.0.1:${ponte.porta}` && host !== `localhost:${ponte.porta}`) return responder(403, { erro: 'host' });
  if (req.headers.origin) return responder(403, { erro: 'origem' });          // página da web nunca fala aqui
  if (!mesmoToken(req.headers['x-clave-token'])) return responder(401, { erro: 'token' });
  if (req.method !== 'POST' || req.url !== '/navegador') return responder(404, { erro: 'rota' });
  if (!/^application\/json/i.test(String(req.headers['content-type'] || ''))) return responder(415, { erro: 'tipo' });
  const pedacos = [];
  let tamanho = 0;
  req.on('data', (c) => { tamanho += c.length; if (tamanho > 1024 * 1024) req.destroy(); else pedacos.push(c); });
  req.on('end', async () => {
    let d;
    try { d = JSON.parse(Buffer.concat(pedacos).toString('utf8') || '{}'); } catch { return responder(400, { erro: 'json' }); }
    if (!d || typeof d !== 'object') return responder(400, { erro: 'json' });
    try {
      responder(200, await enfileirar(() => (janela && !janela.isDestroyed() ? comPrazo(acaoDaPonte(d), d.acao) : { erro: 'sem_janela' })));
    } catch (e) {
      const msg = String(e?.message || e);
      responder(200, { erro: msg === 'sem_janela' || msg === 'sem_pagina' ? msg : 'interno', detalhe: msg });
    }
  });
}

function iniciarPonte() {
  return new Promise((ok) => {
    const s = http.createServer(atenderPonte);
    s.on('error', () => ok(false));
    s.listen(0, '127.0.0.1', () => {
      ponte.porta = s.address().port;
      ponte.servidor = s;
      // os testes da janela (CLAVE_TESTE_DEMO=1) acham a ponte por este arquivo, só do dono; ele some ao fechar
      if (process.env.CLAVE_TESTE_DEMO === '1') {
        try {
          fs.mkdirSync(DADOS, { recursive: true });
          fs.writeFileSync(ARQ_PONTE, JSON.stringify({ url: `http://127.0.0.1:${ponte.porta}`, token: ponte.token }), { mode: 0o600 });
          if (process.platform === 'win32') execFile('icacls', [ARQ_PONTE, '/inheritance:r', '/grant:r', `${os.userInfo().username}:F`], { windowsHide: true }, () => {});
        } catch { /* sem o arquivo, só o teste não acha a ponte */ }
      }
      ok(true);
    });
  });
}

function fecharPonte() {
  try { ponte.servidor?.close(); } catch { /* já fechada */ }
  try { fs.unlinkSync(ARQ_PONTE); } catch { /* não existia */ }
}
process.on('exit', () => { try { fs.unlinkSync(ARQ_PONTE); } catch { /* não existia */ } });

let fechandoComCalma = false;
app.on('before-quit', (e) => {
  saindo = true; salvarEstadoJanela();
  if (servidor && !fechandoComCalma) {
    // segura o fechamento até o servidor sair com calma (ou o prazo acabar) e fecha de novo
    e.preventDefault();
    fechandoComCalma = true;
    pararServidorComCalma().then(() => { fecharPonte(); app.quit(); });
    return;
  }
  pararServidor(); fecharPonte();
});
app.on('window-all-closed', () => app.quit());

app.whenReady().then(async () => {
  if (!primeiraInstancia) return;
  Menu.setApplicationMenu(null);
  try {
    porta = await escolherPorta();
    await iniciarPonte();  // sem a ponte o app abre do mesmo jeito; só o Claude fica sem o navegador
    subirServidor();
    if (!await esperarServidor()) throw new Error(`O servidor não respondeu. Veja o registro em ${path.join(LOGS, 'servidor.log')}.`);
    await abrirJanela();
  } catch (e) {
    saindo = true;
    pararServidor();
    fecharPonte();
    dialog.showErrorBox('Clave não abriu', String(e.message || e));
    app.exit(1);
  }
});
