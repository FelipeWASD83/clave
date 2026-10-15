// Primeira vez: o que é o Clave, a chave da API, o teto de gasto e um pouco sobre você.
import { api } from './api.js';
import { estado, salvarConfig, carregarEstado } from './estado.js';
import { ic } from './icones.js';
import { el, janela, aviso, frase, usd } from './ui.js';
import { t } from './i18n.js';

export function boasVindas() {
  let passo = 0;
  const dados = { teto: 20, nome: '', sobre: '' };
  const corpo = el('div', { style: 'display:grid;gap:16px' });
  const barra = el('div', { class: 'passos' });
  const voltar = el('button', { class: 'botao', type: 'button', texto: t('Voltar') });
  const seguir = el('button', { class: 'botao primario', type: 'button', texto: t('Começar') });
  const pular = el('button', { class: 'botao fantasma', type: 'button', texto: t('Pular') });
  const passos = [inicio, chave, teto, sobre, pronto];

  const { fechar, elemento } = janela({ titulo: t('Boas-vindas ao Clave'), corpo: el('div', { style: 'display:grid;gap:18px' }, barra, corpo), classe: 'boas-vindas' });
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
    seguir.textContent = p.botao || t('Continuar');
    setTimeout(() => corpo.querySelector('input, textarea')?.focus(), 30);
  }

  function inicio() {
    return [
      el('p', { class: 'grande', texto: t('O Clave é um jeito de usar o Claude, a inteligência artificial da Anthropic, direto do seu computador.') }),
      el('ul', { class: 'passo-a-passo' },
        el('li', { texto: t('Converse, tire dúvidas, escreva textos e analise arquivos, fotos e PDFs.') }),
        el('li', { texto: t('No modo Code, peça para ele trabalhar numa pasta: organizar arquivos, criar planilhas, sites e automações.') }),
        el('li', { texto: t('Você paga só o que usar, direto para a Anthropic, e define um teto por mês.') })),
      el('p', { class: 'ajuda', texto: t('São 4 passos rápidos. Nunca usou nada parecido? Tudo bem: tem lições em "Aprender", na barra da esquerda.') }),
    ];
  }
  inicio.botao = t('Começar');

  function chave() {
    if (estado.info.demo) return [el('p', { class: 'grande', texto: t('Este é o modo demonstração: o Claude responde com textos de exemplo e nada é cobrado. Pode seguir.') })];
    const input = el('input', { class: 'entrada mono', type: 'password', placeholder: 'sk-ant-...', autocomplete: 'off' });
    chave.input = input;
    return [
      el('p', { class: 'grande', texto: t('Para o Claude responder, o Clave precisa da sua chave da API da Anthropic. É como uma senha que diz de qual conta sai o pagamento.') }),
      el('ol', { class: 'passo-a-passo' },
        el('li', {}, frase(t('Entre em {link} e crie uma conta (ou entre com a sua).'), { link: el('a', { href: 'https://platform.claude.com', target: '_blank', rel: 'noopener', texto: 'platform.claude.com' }) })),
        el('li', { texto: t('Coloque créditos (ou, se você assina o Claude Max, ative o crédito mensal incluso no plano).') }),
        el('li', { texto: t('Vá em API Keys, clique em Create Key, dê um nome (ex.: Clave) e copie a chave.') }),
        el('li', { texto: t('Cole aqui embaixo.') })),
      el('label', { class: 'campo' }, el('span', { texto: t('Sua chave') }), input,
        el('small', { texto: t('Ela fica guardada só neste computador, criptografada pelo Windows. Nunca mostre a chave para ninguém.') })),
      el('a', { href: '#/aprender/chave-da-api', texto: t('Passo a passo com mais detalhes'), onclick: () => fechar() }),
      estado.info.tem_chave ? el('p', { class: 'ajuda', texto: t('Já existe uma chave salva ({chave}). Pode deixar em branco.', { chave: estado.info.chave }) }) : null,
    ].filter(Boolean);  // sem chave salva, o null virava o texto "null" embaixo do campo
  }
  chave.avancar = async () => {
    if (estado.info.demo) return true;
    const v = chave.input?.value.trim();
    if (!v) {
      if (estado.info.tem_chave) return true;
      aviso(t('Cole a chave ou clique em Pular (dá para colar depois em Configurações).'), 'erro');
      return false;
    }
    await api('/chave', { metodo: 'POST', corpo: { chave: v } });
    await carregarEstado();
    aviso(t('Chave conferida e salva.'));
    return true;
  };

  function teto() {
    const opcoes = [5, 20, 50, 100, 200];
    const grupo = el('div', { class: 'opcoes-teto', role: 'group', 'aria-label': t('Teto por mês') }, ...opcoes.map((v) =>
      el('button', { type: 'button', 'aria-pressed': String(dados.teto === v), texto: usd(v, 0), onclick: () => { dados.teto = v; desenhar(); } })));
    return [
      el('p', { class: 'grande', texto: t('Quanto você quer gastar, no máximo, por mês? Quando chegar lá, o Clave para de responder até o mês virar.') }),
      grupo,
      el('ul', { class: 'passo-a-passo' },
        el('li', { texto: t('Uma conversa curta custa de menos de 1 centavo (Haiku) a alguns centavos (Opus).') }),
        el('li', { texto: t('Quem assina o Claude Max ganha crédito na API todo mês (US$ 100 no Max 5x). Se for o seu caso, use esse valor.') }),
        el('li', { texto: t('Dá para mudar quando quiser em Configurações > Limite de gasto.') })),
    ];
  }

  function sobre() {
    const nome = el('input', { class: 'entrada', placeholder: t('Como o Claude deve te chamar'), value: dados.nome });
    const txt = el('textarea', { class: 'area', placeholder: t('Ex.: Sou estudante de enfermagem, não sei programar, prefiro respostas curtas e com exemplos.') });
    txt.value = dados.sobre;
    nome.addEventListener('input', () => { dados.nome = nome.value.trim(); });
    txt.addEventListener('input', () => { dados.sobre = txt.value.trim(); });
    return [
      el('p', { class: 'grande', texto: t('Conte um pouco sobre você. O Claude lê isto no começo de cada conversa e acerta melhor o tom e o nível das respostas.') }),
      el('label', { class: 'campo' }, el('span', { texto: t('Nome') }), nome),
      el('label', { class: 'campo' }, el('span', { texto: t('Sobre você e como prefere as respostas') }), txt),
      el('p', { class: 'ajuda', texto: t('Opcional. Tudo isso fica em Configurações > Personalização.') }),
    ];
  }

  function pronto() {
    return [
      el('p', { class: 'grande', texto: t('Pronto! Algumas dicas para começar:') }),
      el('ul', { class: 'passo-a-passo' },
        el('li', {}, frase(t('Primeira vez com IA? Comece pela lição {link}.'), { link: el('a', { href: '#/aprender/o-que-e-o-claude', texto: t('O que é o Claude'), onclick: () => concluir().then(fechar) }) })),
        el('li', { texto: t('Escreva como se falasse com uma pessoa: contexto, o que você quer e o formato da resposta.') }),
        el('li', {}, frase(t('Para automatizar coisas no computador, use o {botao} na barra da esquerda.'), { botao: el('b', { texto: t('Novo trabalho no Code') }) }))),
      el('div', { class: 'nota-conversa info' }, el('span', { html: ic('info') }), t('O Clave não é um app da Anthropic: é um app independente que usa a API oficial dela.')),
    ];
  }
  pronto.botao = t('Abrir o Clave');

  desenhar();
}
