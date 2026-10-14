// Conversa com o servidor local do Clave.

export class ErroApi extends Error {
  constructor(msg, status, codigo) { super(msg); this.status = status; this.codigo = codigo; }
}

export async function api(caminho, { metodo = 'GET', corpo, bruto = false } = {}) {
  const opcoes = { method: metodo, headers: {}, credentials: 'same-origin' };
  if (corpo !== undefined) {
    opcoes.headers['Content-Type'] = 'application/json';
    opcoes.body = JSON.stringify(corpo);
  }
  let r;
  try {
    r = await fetch('/api' + caminho, opcoes);
  } catch {
    throw new ErroApi('O Clave não está respondendo. Ele pode ter sido fechado: abra de novo pelo atalho.', 0, 'offline');
  }
  if (bruto) {
    if (!r.ok) throw new ErroApi(`Erro ${r.status}`, r.status);
    return r;
  }
  let dados = {};
  try { dados = await r.json(); } catch { /* resposta sem JSON */ }
  if (!r.ok) {
    if (r.status === 401) document.dispatchEvent(new CustomEvent('clave:sessao'));
    throw new ErroApi(dados.erro || `Erro ${r.status}`, r.status, dados.codigo);
  }
  return dados;
}

export async function enviarArquivo(arquivo, caminho = '/anexos') {
  const r = await fetch('/api' + caminho, {
    method: 'POST', credentials: 'same-origin',
    headers: { 'X-Nome-Arquivo': encodeURIComponent(arquivo.name || 'arquivo'), 'Content-Type': 'application/octet-stream' },
    body: arquivo,
  });
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) throw new ErroApi(dados.erro || `Erro ${r.status}`, r.status);
  return dados.anexo;
}

// Lê os eventos de uma execução (texto chegando, ferramentas, custo). Reconecta se a conexão cair.
export function acompanhar(execucaoId, aoEvento) {
  let desde = 0, parado = false, controle = null;
  async function ciclo() {
    while (!parado) {
      controle = new AbortController();
      let terminou = false;
      try {
        const r = await fetch(`/api/execucoes/${execucaoId}/eventos?desde=${desde}`, { signal: controle.signal, credentials: 'same-origin' });
        if (r.status === 404) { aoEvento({ tipo: 'fim', status: 'sumiu' }); return; }
        const leitor = r.body.getReader();
        const dec = new TextDecoder();
        let buffer = '';
        while (true) {
          const { value, done } = await leitor.read();
          if (done) break;
          buffer += dec.decode(value, { stream: true });
          let i;
          while ((i = buffer.indexOf('\n\n')) >= 0) {
            const bloco = buffer.slice(0, i); buffer = buffer.slice(i + 2);
            for (const linha of bloco.split('\n')) {
              if (!linha.startsWith('data: ')) continue;
              const ev = JSON.parse(linha.slice(6));
              desde = ev.seq + 1;
              aoEvento(ev);
              if (ev.tipo === 'fim') terminou = true;
            }
          }
        }
      } catch (e) {
        if (parado) return;
      }
      if (terminou) return;
      await new Promise((ok) => setTimeout(ok, 800));
    }
  }
  ciclo();
  return { parar() { parado = true; controle?.abort(); } };
}
