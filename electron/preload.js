// Ponte entre a página e o Electron: só estas funções ficam disponíveis para a interface (window.clave).
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('clave', {
  app: true,
  versaoElectron: process.versions.electron,
  escolherPasta: (titulo) => ipcRenderer.invoke('clave:escolher-pasta', titulo),
  abrirPasta: (caminho) => ipcRenderer.invoke('clave:abrir-pasta', caminho),
  abrirExterno: (url) => ipcRenderer.invoke('clave:abrir-externo', url),
  reiniciar: () => ipcRenderer.invoke('clave:reiniciar'),
  sair: () => ipcRenderer.invoke('clave:sair'),
  aoPedir: (fn) => ipcRenderer.on('clave:pedido', (_e, pedido) => fn(pedido)),
});
