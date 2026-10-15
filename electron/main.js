// Janela do Clave (Electron). Sobe o servidor Python (servidor/iniciar.py), espera ele responder e
// abre a interface numa janela própria. Fechar a janela fecha tudo.
const { app, BrowserWindow, Menu, Notification, dialog, ipcMain, shell, nativeTheme } = require('electron');
const { spawn, execFile } = require('child_process');
const fs = require('fs');
const http = require('http');
const net = require('net');
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
  servidor = spawn(py, [path.join(RAIZ, 'servidor', 'iniciar.py'), '--porta', String(porta), '--sem-janela', '--pai', String(process.pid)], {
    cwd: RAIZ,
    env: { ...process.env, CLAVE_LANCADOR: '1', PYTHONUTF8: '1' },
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
  janela.once('ready-to-show', () => janela.show());
  janela.on('close', salvarEstadoJanela);
  janela.on('focus', () => janela?.flashFrame(false));
  janela.on('closed', () => { janela = null; });
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
ipcMain.handle('clave:reiniciar', () => {
  // app.exit não passa pelo before-quit: o servidor tem que ser parado aqui
  saindo = true; salvarEstadoJanela(); pararServidor();
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

app.on('before-quit', () => { saindo = true; salvarEstadoJanela(); pararServidor(); });
app.on('window-all-closed', () => app.quit());

app.whenReady().then(async () => {
  if (!primeiraInstancia) return;
  Menu.setApplicationMenu(null);
  try {
    porta = await escolherPorta();
    subirServidor();
    if (!await esperarServidor()) throw new Error(`O servidor não respondeu. Veja o registro em ${path.join(LOGS, 'servidor.log')}.`);
    await abrirJanela();
  } catch (e) {
    saindo = true;
    pararServidor();
    dialog.showErrorBox('Clave não abriu', String(e.message || e));
    app.exit(1);
  }
});
