// Ponte entre a página e o Electron: só estas funções ficam disponíveis para a interface (window.clave).
const { contextBridge, ipcRenderer } = require('electron');

// ouvir um canal e devolver a função que para de ouvir
function ouvir(canal, fn) {
  const h = (_e, dado) => fn(dado);
  ipcRenderer.on(canal, h);
  return () => ipcRenderer.removeListener(canal, h);
}

contextBridge.exposeInMainWorld('clave', {
  app: true,
  versaoElectron: process.versions.electron,
  escolherPasta: (titulo) => ipcRenderer.invoke('clave:escolher-pasta', titulo),
  abrirPasta: (caminho) => ipcRenderer.invoke('clave:abrir-pasta', caminho),
  abrirExterno: (url) => ipcRenderer.invoke('clave:abrir-externo', url),
  reiniciar: () => ipcRenderer.invoke('clave:reiniciar'),
  sair: () => ipcRenderer.invoke('clave:sair'),
  notificar: (titulo, corpo) => ipcRenderer.invoke('clave:notificar', String(titulo || ''), String(corpo || '')),
  // pedidos do Electron para a tela: um texto ('nova-conversa', 'configuracoes') ou um objeto ({ tipo: 'navegador', ... })
  aoPedir: (fn) => ouvir('clave:pedido', fn),
  // o navegador do modo Code (a aba Navegador do painel)
  navegador: {
    // rect = { x, y, width, height } da área da página, em pixels de CSS; null esconde
    posicionar: (rect) => ipcRenderer.invoke('clave:nav-posicionar', rect ? {
      x: Number(rect.x), y: Number(rect.y), width: Number(rect.width), height: Number(rect.height),
    } : null),
    // foto da página (data: URL) e esconde a vista, para algo do app aparecer por cima
    congelar: () => ipcRenderer.invoke('clave:nav-congelar'),
    ir: (url) => ipcRenderer.invoke('clave:nav-ir', String(url || '')),
    voltar: () => ipcRenderer.invoke('clave:nav-voltar'),
    avancar: () => ipcRenderer.invoke('clave:nav-avancar'),
    recarregar: () => ipcRenderer.invoke('clave:nav-recarregar'),
    parar: () => ipcRenderer.invoke('clave:nav-parar'),
    estado: () => ipcRenderer.invoke('clave:nav-estado'),
    // { url, titulo, carregando, podeVoltar, podeAvancar, erro, visivel } a cada mudança
    aoMudar: (fn) => ouvir('clave:nav-mudou', fn),
  },
});
