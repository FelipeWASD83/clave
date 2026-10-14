// Primeira vez: o que é o Clave, a chave da API, o teto de gasto e um pouco sobre você.
import { api } from './api.js';
import { estado, salvarConfig, carregarEstado } from './estado.js';
import { ic } from './icones.js';
import { el, janela, aviso } from './ui.js';

export function boasVindas() {
  let passo = 0;
  const dados = { teto: 20, nome: '', sobre: '' };
  const corpo = el('div', { style: 'display:grid;gap:16px' });
  const barra = el('div', { class: 'passos' });
  const voltar = el('button', { class: 'botao', type: 'button', texto: 'Voltar' });
  const seguir = el('button', { class: 'botao primario', type: 'button', texto: 'Começar' });
  const pular = el('button', { class: 'botao fantasma', type: 'button', texto: 'Pular' });
  const passos = [inicio, chave, teto, sobre, pronto];

  const { fechar, elemento } = janela({ titulo: 'Boas-vindas ao Clave', corpo: el('div', { style: 'display:grid;gap:18px' }, barra, corpo), classe: 'boas-vindas' });
  elemento.append(el('div', { class: 'janela-rodape' }, pular, el('span', { style: 'flex:1' }), voltar, seguir));
  voltar.addEventListener('click', () => { if (passo > 0) { passo -= 1; desenhar(); } });
  pular.addEventListener('click', () => { if (passo < passos.length - 1) { passo += 1; desenhar(); } });
  seguir.addEventListener('click', async () => {
    seguir.disabled = true;
    try {
      const ok = await passos[passo].avancar?.();
      if (ok === false) return;
      if (passo === passos.length - 1) { await concluir(); fechar(); return; }
      passo += 1; desenhar();
    } catch (e) { aviso(e.message, 'erro'); } finally { seguir.disabled = false; }
  });

  async function concluir() {
    await salvarConfig({ configurado: true, teto_mensal_usd: dados.teto, nome: dados.nome, sobre_voce: dados.sobre });
    window.dispatchEvent(new HashChangeEvent('hashchange'));  // redesenha a tela com o nome novo
  }

  function desenhar() {
    barra.replaceChildren(...passos.map((_, i) => el('i', { class: i <= passo ? 'feito' : '' })));
    voltar.hidden = passo === 0;
    pular.hidden = passo === 0 || passo === passos.length - 1;
    const p = passos[passo];
    corpo.replaceChildren(...p());
    seguir.textContent = p.botao || 'Continuar';
    setTimeout(() => corpo.querySelector('input, textarea')?.focus(), 30);
  }

  function inicio() {
    return [
      el('p', { class: 'grande', texto: 'O Clave é um jeito de usar o Claude, a inteligência artificial da Anthropic, direto do seu computador.' }),
      el('ul', { class: 'passo-a-passo' },
        el('li', { texto: 'Converse, tire dúvidas, escreva textos e analise arquivos, fotos e PDFs.' }),
        el('li', { texto: 'No modo Code, peça para ele trabalhar numa pasta: organizar arquivos, criar planilhas, sites e automações.' }),
        el('li', { texto: 'Você paga só o que usar, direto para a Anthropic, e define um teto por mês.' })),
      el('p', { class: 'ajuda', texto: 'São 4 passos rápidos. Nunca usou nada parecido? Tudo bem: tem lições em "Aprender", na barra da esquerda.' }),
    ];
  }
  inicio.botao = 'Começar';

  function chave() {
    if (estado.info.demo) return [el('p', { class: 'grande', texto: 'Este é o modo demonstração: o Claude responde com textos de exemplo e nada é cobrado. Pode seguir.' })];
    const input = el('input', { class: 'entrada mono', type: 'password', placeholder: 'sk-ant-...', autocomplete: 'off' });
    chave.input = input;
    return [
      el('p', { class: 'grande', texto: 'Para o Claude responder, o Clave precisa da sua chave da API da Anthropic. É como uma senha que diz de qual conta sai o pagamento.' }),
      el('ol', { class: 'passo-a-passo' },
        el('li', {}, 'Entre em ', el('a', { href: 'https://platform.claude.com', target: '_blank', rel: 'noopener', texto: 'platform.claude.com' }), ' e crie uma conta (ou entre com a sua).'),
        el('li', { texto: 'Coloque créditos (ou, se você assina o Claude Max, ative o crédito mensal incluso no plano).' }),
        el('li', { texto: 'Vá em API Keys, clique em Create Key, dê um nome (ex.: Clave) e copie a chave.' }),
        el('li', { texto: 'Cole aqui embaixo.' })),
      el('label', { class: 'campo' }, el('span', { texto: 'Sua chave' }), input,
        el('small', { texto: 'Ela fica guardada só neste computador, criptografada pelo Windows. Nunca mostre a chave para ninguém.' })),
      el('a', { href: '#/aprender/chave-da-api', texto: 'Passo a passo com mais detalhes', onclick: () => fechar() }),
      estado.info.tem_chave ? el('p', { class: 'ajuda', texto: `Já existe uma chave salva (${estado.info.chave}). Pode deixar em branco.` }) : null,
    ];
  }
  chave.avancar = async () => {
    if (estado.info.demo) return true;
    const v = chave.input?.value.trim();
    if (!v) {
      if (estado.info.tem_chave) return true;
      aviso('Cole a chave ou clique em Pular (dá para colar depois em Configurações).', 'erro');
      return false;
    }
    await api('/chave', { metodo: 'POST', corpo: { chave: v } });
    await carregarEstado();
    aviso('Chave conferida e salva.');
    return true;
  };

  function teto() {
    const opcoes = [5, 20, 50, 100, 200];
    const grupo = el('div', { class: 'opcoes-teto', role: 'group', 'aria-label': 'Teto por mês' }, ...opcoes.map((v) =>
      el('button', { type: 'button', 'aria-pressed': String(dados.teto === v), texto: `US$ ${v}`, onclick: () => { dados.teto = v; desenhar(); } })));
    return [
      el('p', { class: 'grande', texto: 'Quanto você quer gastar, no máximo, por mês? Quando chegar lá, o Clave para de responder até o mês virar.' }),
      grupo,
      el('ul', { class: 'passo-a-passo' },
        el('li', { texto: 'Uma conversa curta custa de menos de 1 centavo (Haiku) a alguns centavos (Opus).' }),
        el('li', { texto: 'Quem assina o Claude Max ganha crédito na API todo mês (US$ 100 no Max 5x). Se for o seu caso, use esse valor.' }),
        el('li', { texto: 'Dá para mudar quando quiser em Configurações > Limite de gasto.' })),
    ];
  }

  function sobre() {
    const nome = el('input', { class: 'entrada', placeholder: 'Como o Claude deve te chamar', value: dados.nome });
    const txt = el('textarea', { class: 'area', placeholder: 'Ex.: Sou estudante de enfermagem, não sei programar, prefiro respostas curtas e com exemplos.' });
    txt.value = dados.sobre;
    nome.addEventListener('input', () => { dados.nome = nome.value.trim(); });
    txt.addEventListener('input', () => { dados.sobre = txt.value.trim(); });
    return [
      el('p', { class: 'grande', texto: 'Conte um pouco sobre você. O Claude lê isto no começo de cada conversa e acerta melhor o tom e o nível das respostas.' }),
      el('label', { class: 'campo' }, el('span', { texto: 'Nome' }), nome),
      el('label', { class: 'campo' }, el('span', { texto: 'Sobre você e como prefere as respostas' }), txt),
      el('p', { class: 'ajuda', texto: 'Opcional. Tudo isso fica em Configurações > Personalização.' }),
    ];
  }

  function pronto() {
    return [
      el('p', { class: 'grande', texto: 'Pronto! Algumas dicas para começar:' }),
      el('ul', { class: 'passo-a-passo' },
        el('li', {}, 'Primeira vez com IA? Comece pela lição ', el('a', { href: '#/aprender/o-que-e-o-claude', texto: 'O que é o Claude', onclick: () => concluir().then(fechar) }), '.'),
        el('li', { texto: 'Escreva como se falasse com uma pessoa: contexto, o que você quer e o formato da resposta.' }),
        el('li', {}, 'Para automatizar coisas no computador, use o ', el('b', { texto: 'Novo trabalho no Code' }), ' na barra da esquerda.')),
      el('div', { class: 'nota-conversa info' }, el('span', { html: ic('info') }), 'O Clave não é um app da Anthropic: é um app independente que usa a API oficial dela.'),
    ];
  }
  pronto.botao = 'Abrir o Clave';

  desenhar();
}
