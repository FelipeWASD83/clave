// Configurações: conta, personalização, modelos, recursos, teto de gasto, modo Code, GitHub, conectores, aparência e dados.
import { api } from './api.js';
import { estado, cfg, salvarConfig, carregarEstado } from './estado.js';
import { ic } from './icones.js';
import { el, aviso, chaveLiga, confirmar, janela, escolherArquivos, usd } from './ui.js';
import { checarAtualizacao, abrirAtualizacao } from './atualizar.js';
import { criarMiniChat } from './minichat.js';
import { markdownSeguro } from './markdown.js';
import { t, localidade } from './i18n.js';

const ABAS = () => [
  ['conta', t('Conta e chave')], ['personalizacao', t('Personalização')], ['importar', t('Importar do Claude')], ['memoria', t('Memória')], ['modelos', t('Modelos')],
  ['recursos', t('Recursos')], ['limite', t('Limite de gasto')], ['code', t('Modo Code')], ['github', t('GitHub')],
  ['conectores', t('Conectores')], ['aparencia', t('Aparência')], ['dados', t('Dados e backup')], ['sobre', t('Atualizações e sobre')],
];

export async function telaConfig(principal, aba = 'conta') {
  const abas = ABAS();
  if (!abas.some(([id]) => id === aba)) aba = 'conta';
  const conteudo = el('div', {});
  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' }, el('h1', { texto: t('Configurações') })),
    el('div', { class: 'config' },
      el('nav', { class: 'config-abas', 'aria-label': t('Seções') }, ...abas.map(([id, nome]) => el('a', { href: `#/config/${id}`, 'aria-current': id === aba ? 'page' : null, texto: nome }))),
      conteudo))));
  await SECOES[aba](conteudo);
  return {};
}

const salvar = async (alt, msg) => {
  try { await salvarConfig(alt); if (msg) aviso(msg); } catch (e) { aviso(e.message, 'erro'); }
};

function campo(rotulo, entrada, ajuda) {
  return el('label', { class: 'campo' }, el('span', { texto: rotulo }), entrada, ajuda ? el('small', { texto: ajuda }) : null);
}
function texto(chave, { area = false, placeholder = '', tipo = 'text' } = {}) {
  const e = el(area ? 'textarea' : 'input', { class: area ? 'area' : 'entrada', placeholder, type: area ? null : tipo });
  e.value = cfg()[chave] ?? '';
  e.addEventListener('change', () => salvar({ [chave]: tipo === 'number' ? (e.value === '' ? '' : Number(e.value)) : e.value }, t('Salvo.')));
  return e;
}
function selecao(chave, opcoes) {
  const s = el('select', { class: 'selecao' }, ...opcoes.map(([v, rot]) => el('option', { value: v, texto: rot })));
  s.value = cfg()[chave] ?? opcoes[0][0];
  s.addEventListener('change', () => salvar({ [chave]: s.value }));
  return s;
}
function liga(chave, rotulo, ajuda) {
  return chaveLiga({ rotulo, ajuda, marcado: !!cfg()[chave], aoMudar: (v) => salvar({ [chave]: v }) });
}
function secao(titulo, descricao, ...filhos) {
  return el('section', { class: 'config-secao' }, el('h2', { texto: titulo }), descricao ? el('p', { texto: descricao }) : null, ...filhos);
}
// o jeito de falar (como o controle de tom do ChatGPT): cada linha é um controle, e "Padrão" não muda nada no prompt
function secaoJeitoDeFalar(redesenhar) {
  const controles = estado.info.tom || [];
  const atual = () => ({ ...(cfg().tom || {}) });
  const linhas = controles.map((c) => {
    const s = el('select', { class: 'pilula', 'aria-label': c.nome }, ...c.opcoes.map((o) => el('option', { value: o.valor, texto: o.rotulo })));
    s.value = atual()[c.id] || 'padrao';
    s.addEventListener('change', () => salvar({ tom: { ...atual(), [c.id]: s.value } }, t('Salvo.')));
    return el('label', { class: 'linha-tom' }, el('span', { class: 'textos' }, el('b', { texto: c.nome }), el('small', { texto: c.ajuda })), s);
  });
  const mudou = Object.keys(atual()).length > 0;
  return secao(t('Jeito de falar'), t('Como o Claude conversa com você. Vale para as conversas novas, no chat e no Code.'),
    el('div', { class: 'linhas-tom' }, ...linhas),
    el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap;align-items:center' },
      el('button', { class: 'botao', type: 'button', html: `${ic('faisca')}${t('Ver um exemplo')}`, onclick: () => verExemploTom() }),
      mudou ? el('button', { class: 'botao fantasma', type: 'button', texto: t('Voltar tudo para o padrão'), onclick: async () => { await salvar({ tom: {} }, t('Salvo.')); redesenhar(); } }) : null,
      el('small', { class: 'ajuda', texto: t('O exemplo usa o Haiku 5.5 e custa menos de um centavo.') })));
}

function verExemploTom() {
  const pergunta = el('input', { class: 'entrada', value: t('Me explica rapidinho o que é backup e se eu preciso me preocupar com isso.') });
  const saida = el('div', { class: 'exemplo-tom', hidden: true });
  const custo = el('small', { class: 'ajuda' });
  const perguntar = el('button', { class: 'botao primario', type: 'button', html: `${ic('enviar')}${t('Perguntar')}` });
  perguntar.addEventListener('click', async () => {
    perguntar.disabled = true;
    saida.hidden = false;
    saida.replaceChildren(el('p', { class: 'ajuda', texto: t('O Claude está respondendo…') }));
    custo.textContent = '';
    try {
      const r = await api('/tom/exemplo', { metodo: 'POST', corpo: { tom: cfg().tom || {}, pergunta: pergunta.value } });
      saida.replaceChildren(markdownSeguro(r.resposta || t('(resposta vazia)')));
      saida.firstChild.classList.add('resposta');
      if (r.custo_usd > 0) custo.textContent = t('Custou {valor}.', { valor: usd(r.custo_usd) });
    } catch (e) {
      saida.replaceChildren(el('p', { class: 'ajuda', texto: e.message }));
    } finally { perguntar.disabled = false; }
  });
  janela({ titulo: t('Como o Claude vai falar'), larga: true,
    corpo: el('div', { style: 'display:grid;gap:12px' },
      el('p', { class: 'ajuda', texto: t('Com o jeito de falar e o resto da sua personalização. Troque a pergunta se quiser.') }),
      el('div', { style: 'display:flex;gap:8px' }, pergunta, perguntar),
      saida, custo),
    botoes: [{ texto: t('Fechar') }] });
}

// "Sair da conta": a chave e as senhas saem, a configuração volta ao padrão e a tela recarrega na apresentação
async function sairDaConta() {
  const ok = await confirmar(t('Sair da conta? A chave da API e as senhas salvas (e-mail, GitHub, conectores) são apagadas deste computador, todas as configurações voltam ao padrão e as rotinas são desligadas. As conversas, os projetos e a memória ficam. Depois aparecem a apresentação e os tours de novo, como na primeira vez.'),
    { titulo: t('Sair da conta'), sim: t('Sair da conta'), perigo: true });
  if (!ok) return;
  try {
    await api('/sair-da-conta', { metodo: 'POST' });
    try { localStorage.clear(); sessionStorage.clear(); } catch { /* sem armazenamento, segue */ }
    location.hash = '#/novo';
    location.reload();
  } catch (e) { aviso(e.message, 'erro'); }
}

function desinstalar() {
  janela({ titulo: t('Desinstalar o Clave'),
    corpo: el('div', { style: 'display:grid;gap:12px' },
      el('p', { style: 'margin:0', texto: t('O Clave fecha e apaga a pasta dele (com as conversas, os projetos, a memória e as configurações, que moram lá dentro), os atalhos da área de trabalho e do menu Iniciar e as tarefas das rotinas no Agendador do Windows. Não dá para desfazer.') }),
      el('p', { class: 'ajuda', style: 'margin:0', texto: t('Quer guardar as conversas? Baixe o backup antes: dá para importar numa instalação nova.') }),
      el('a', { class: 'botao', href: '/api/backup', style: 'justify-self:start', html: `${ic('baixar')}${t('Baixar backup das conversas')}` })),
    botoes: [{ texto: t('Cancelar') }, { texto: t('Desinstalar'), classe: 'perigo', acao: async () => {
      await api('/desinstalar', { metodo: 'POST' });
      if (window.clave?.sair) window.clave.sair();
      else document.body.innerHTML = `<p style="padding:40px;font-family:sans-serif">${t('O Clave está sendo desinstalado. Pode fechar esta janela.')}</p>`;
    } }] });
}

const preco = (v) => Number(v).toLocaleString(localidade(), { maximumFractionDigits: 4 });
const modelosOpcoes = () => (estado.info?.modelos || []).map((m) => [m.id, t('{nome} (US$ {entrada} / {saida} por milhão)', { nome: m.nome, entrada: preco(m.entrada), saida: preco(m.saida) })]);
const esforcoOpcoes = () => (estado.info?.esforcos || []).map((e) => [e.id, e.nome]);

const SECOES = {
  async conta(alvo) {
    const info = estado.info;
    const chave = el('input', { class: 'entrada mono', type: 'password', placeholder: 'sk-ant-...', autocomplete: 'off' });
    const status = info.demo
      ? el('div', { class: 'nota-conversa info' }, el('span', { html: ic('info') }), t('Modo demonstração: as respostas são de mentira e nada é cobrado.'))
      : info.tem_chave
        ? el('div', { class: 'item-lista' }, el('span', { html: ic('chave') }), el('span', { class: 'textos' }, el('b', { texto: t('Chave salva') }), el('small', { class: 'mono', texto: info.chave })),
          el('button', { class: 'botao pequeno perigo', type: 'button', texto: t('Apagar'), onclick: async () => {
            if (!await confirmar(t('Apagar a chave deste computador? O Claude para de responder até você colar outra.'), { sim: t('Apagar'), perigo: true })) return;
            await api('/chave', { metodo: 'DELETE' }); await carregarEstado(); SECOES.conta(alvo);
          } }))
        : el('div', { class: 'nota-conversa' }, el('span', { html: ic('alerta') }), t('Nenhuma chave salva ainda.'));
    alvo.replaceChildren(secao(t('Conta e chave da API'),
      t('O Clave conversa com o Claude pela API da Anthropic, usando a sua chave. A chave fica guardada só neste computador, criptografada pelo Windows.'),
      status,
      campo(t('Colar uma chave nova'), chave, t('Ela começa com sk-ant-. O Clave confere com a Anthropic antes de salvar.')),
      el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap' },
        el('button', { class: 'botao primario', type: 'button', texto: t('Conferir e salvar'), onclick: async (e) => {
          const b = e.currentTarget;
          b.disabled = true;
          try { await api('/chave', { metodo: 'POST', corpo: { chave: chave.value.trim() } }); chave.value = ''; await carregarEstado(); aviso(t('Chave salva.')); SECOES.conta(alvo); }
          catch (er) { aviso(er.message, 'erro'); } finally { b.disabled = false; }
        } }),
        el('a', { class: 'botao', href: '#/aprender/chave-da-api', texto: t('Como conseguir uma chave') }))));
  },

  async personalizacao(alvo) {
    const estilos = estado.info.estilos;
    const listaEstilos = el('div', { class: 'lista-itens' });
    const desenharEstilos = () => {
      listaEstilos.replaceChildren(...(cfg().estilos_proprios || []).map((s) => el('div', { class: 'item-lista' },
        el('span', { class: 'textos' }, el('b', { texto: s.nome }), el('small', { texto: s.instrucoes })),
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Editar'), onclick: () => editarEstilo(s) }),
        el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar estilo'), html: ic('lixo'), onclick: async () => {
          await salvar({ estilos_proprios: cfg().estilos_proprios.filter((x) => x.id !== s.id), estilo: cfg().estilo === s.id ? 'normal' : cfg().estilo });
          SECOES.personalizacao(alvo);
        } }))));
    };
    const editarEstilo = (s = null) => {
      const nome = el('input', { class: 'entrada', value: s?.nome || '', placeholder: t('Ex.: Professor paciente') });
      const inst = el('textarea', { class: 'area', placeholder: t('Ex.: Explique com analogias do dia a dia, faça uma pergunta no fim para ver se entendi.') });
      inst.value = s?.instrucoes || '';
      janela({ titulo: s ? t('Editar estilo') : t('Novo estilo'), corpo: el('div', { style: 'display:grid;gap:12px' }, campo(t('Nome'), nome), campo(t('Como o Claude deve escrever'), inst)),
        botoes: [{ texto: t('Cancelar') }, { texto: t('Salvar'), classe: 'primario', acao: async () => {
          if (!nome.value.trim()) { aviso(t('Dê um nome.'), 'erro'); return false; }
          const lista = (cfg().estilos_proprios || []).filter((x) => x.id !== s?.id);
          lista.push({ id: s?.id || 'proprio-' + Date.now().toString(36), nome: nome.value.trim(), instrucoes: inst.value.trim() });
          await salvar({ estilos_proprios: lista });
          SECOES.personalizacao(alvo);
        } }] });
    };
    desenharEstilos();
    alvo.replaceChildren(
      secao(t('Sobre você'), t('O Claude lê isto no começo de cada conversa nova. Quanto mais ele souber, melhor ele acerta o tom e o nível das respostas.'),
        campo(t('Como o Claude deve te chamar'), texto('nome', { placeholder: t('Seu nome ou apelido') })),
        campo(t('Sobre você'), texto('sobre_voce', { area: true, placeholder: t('Ex.: Tenho 34 anos, sou confeiteira, tenho uma loja no Instagram. Não sei programar. Uso Windows e celular Android.') }),
          t('O que você faz, o que sabe, o que não sabe, que programas usa.')),
        campo(t('Como você quer as respostas'), texto('como_responder', { area: true, placeholder: t('Ex.: Respostas curtas e diretas, em português do Brasil, sem palavras difíceis. Quando der passo a passo, numere.') }))),
      secaoJeitoDeFalar(() => SECOES.personalizacao(alvo)),
      secao(t('Estilo das respostas'), t('O jeito de escrever. Vale para as conversas novas.'),
        campo(t('Estilo padrão'), selecao('estilo', Object.entries(estilos).map(([id, s]) => [id, s.nome]))),
        el('div', { class: 'rotulo', texto: t('Seus estilos') }), listaEstilos,
        el('button', { class: 'botao', type: 'button', html: `${ic('mais')}${t('Criar estilo')}`, onclick: () => editarEstilo() })),
      secao(t('Outros'), null, liga('titulos_automaticos', t('Dar título às conversas sozinho'), t('Usa o Haiku 5.5 uma vez por conversa (custa uma fração de centavo).'))));
  },

  async importar(alvo) {
    const NOMES = {
      instrucoes: t('Instruções → Como você quer as respostas'), estilo: t('Estilo de resposta → Como você quer as respostas'),
      identidade: t('Identidade → Sobre você'), carreira: t('Carreira → Sobre você'),
      preferencias: t('Preferências → Memória'), ferramentas: t('Ferramentas e conectores → Memória'),
      projetos: t('Projetos → Projetos do Clave'), rotinas: t('Automações → Rotinas (desligadas, para você conferir)'),
    };
    const { pedido } = await api('/importar/pedido');
    const caixaPedido = el('textarea', { class: 'area mono', readonly: true, style: 'min-height:160px;font-size:12.5px' });
    caixaPedido.value = pedido;
    const resposta = el('textarea', { class: 'area', placeholder: t('Cole aqui a resposta inteira (o bloco de código).'), style: 'min-height:160px' });
    const previa = el('div', { class: 'importar-previa' });
    const ler = async () => {
      try {
        const { itens } = await api('/importar/ler', { metodo: 'POST', corpo: { texto: resposta.value } });
        const marcados = new Set(itens.map((i) => i.id));
        const grupos = Object.keys(NOMES).map((cat) => [cat, itens.filter((i) => i.categoria === cat)]).filter(([, l]) => l.length);
        const botao = el('button', { class: 'botao primario', type: 'button', texto: t('Importar os marcados'), onclick: async () => {
          const escolhidos = itens.filter((i) => marcados.has(i.id));
          if (!escolhidos.length) { aviso(t('Marque pelo menos um item.'), 'erro'); return; }
          const { feito } = await api('/importar/aplicar', { metodo: 'POST', corpo: { itens: escolhidos } });
          await carregarEstado();
          aviso(t('Importado: {r} regras de resposta, {s} sobre você, {m} memórias, {p} projetos e {o} rotinas (desligadas).', { r: feito.respostas, s: feito.sobre_voce, m: feito.memoria, p: feito.projetos, o: feito.rotinas }));
          previa.replaceChildren(el('p', { class: 'ajuda', texto: t('Pronto. Confira em Personalização, Memória, Projetos e Rotinas. As rotinas ficaram desligadas e no Haiku: ligue só as que precisam mesmo de IA toda vez.') }));
        } });
        previa.replaceChildren(
          el('p', { class: 'ajuda', texto: t('Desmarque o que não quiser trazer.') }),
          ...grupos.map(([cat, lista]) => el('div', { class: 'importar-grupo' },
            el('div', { class: 'rotulo', texto: NOMES[cat] }),
            ...lista.map((i) => {
              const caixa = el('input', { type: 'checkbox', checked: true });
              caixa.addEventListener('change', () => (caixa.checked ? marcados.add(i.id) : marcados.delete(i.id)));
              const extra = cat === 'rotinas'
                ? `${i.nome}: ${i.quando_texto || t('horário não informado')}${i.horario_certo ? '' : ' ' + t('(confira o horário)')}`
                : cat === 'projetos' ? i.nome : '';
              return el('label', { class: 'importar-item' }, caixa,
                el('span', {}, extra ? el('b', { texto: extra }) : null, el('span', { texto: cat === 'rotinas' ? (i.prompt || '') : cat === 'projetos' ? (i.detalhes || '') : i.texto })));
            }))),
          botao);
      } catch (e) { aviso(e.message, 'erro'); }
    };
    alvo.replaceChildren(
      secao(t('Importar do Claude ou do ChatGPT'), t('Traga o que o outro assistente já sabe de você: regras, quem você é, projetos, preferências e automações. Nada é enviado a lugar nenhum: você copia, cola lá e cola a resposta aqui.'),
        el('div', { class: 'rotulo', texto: t('1. Copie este pedido') }), caixaPedido,
        el('div', { class: 'linha-botoes' },
          el('button', { class: 'botao', type: 'button', html: `${ic('copiar')}${t('Copiar o pedido')}`, onclick: async () => { await navigator.clipboard.writeText(pedido); aviso(t('Pedido copiado.')); } })),
        el('p', { class: 'ajuda', texto: t('2. Cole numa conversa nova do claude.ai (ou do ChatGPT) e mande. 3. Copie o bloco que ele devolver e cole abaixo.') }),
        resposta,
        el('div', { class: 'linha-botoes' }, el('button', { class: 'botao primario', type: 'button', texto: t('Ler a resposta'), onclick: ler })),
        previa));
  },

  async memoria(alvo) {
    const listaEl = el('div', { class: 'lista-itens' });
    const NOMES_TIPO = { 'sobre-voce': t('Sobre você'), preferencia: t('Preferência'), projeto: t('Projeto'), referencia: t('Referência') };
    const desenharLista = async () => {
      const { arquivos } = await api('/memoria');
      rotulo.textContent = t('Memórias guardadas ({n})', { n: arquivos.filter((a) => !a.indice).length });
      listaEl.replaceChildren(...(arquivos.length ? arquivos.map((a) => {
        const area = el('textarea', { class: 'area mono', style: 'font-size:13px;min-height:140px', hidden: true });
        area.value = a.texto;
        const salvarBt = el('button', { class: 'botao pequeno primario', type: 'button', texto: t('Salvar'), hidden: true, onclick: async () => {
          await api('/memoria', { metodo: 'POST', corpo: { caminho: a.caminho, texto: area.value } }); aviso(t('Salvo.')); desenharLista();
        } });
        const corpo = el('div', { class: 'corpo-mem', texto: a.indice ? a.texto : a.corpo });
        return el('div', { class: `memoria-cartao ${a.indice ? 'indice' : ''}` },
          el('div', { class: 'linha-topo' },
            el('b', { texto: a.indice ? t('Índice (MEMORY.md)') : a.nome }),
            a.tipo ? el('span', { class: 'etiqueta', texto: NOMES_TIPO[a.tipo] || a.tipo }) : null,
            el('button', { class: 'botao pequeno fantasma', type: 'button', texto: t('Editar à mão'), onclick: () => { area.hidden = !area.hidden; salvarBt.hidden = area.hidden; corpo.hidden = !area.hidden; } }),
            el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar {caminho}', { caminho: a.caminho }), title: t('Apagar'), html: ic('lixo'), onclick: async () => {
              const pergunta = a.indice
                ? t('Apagar {caminho}?', { caminho: a.caminho })
                : t('Apagar {caminho}? (Lembre de tirar a linha dele do índice, ou peça ao editor abaixo.)', { caminho: a.caminho });
              if (await confirmar(pergunta, { sim: t('Apagar'), perigo: true })) {
                await api(`/memoria?caminho=${encodeURIComponent(a.caminho)}`, { metodo: 'DELETE' }); desenharLista();
              }
            } })),
          a.descricao ? el('p', { texto: a.descricao }) : null,
          el('code', { class: 'meta', texto: a.caminho }),
          corpo, area, salvarBt);
      }) : [el('p', { class: 'ajuda', texto: t('Nada guardado ainda. Com a memória ligada, o Claude vai anotando o que vale lembrar.') })]));
    };
    const rotulo = el('div', { class: 'rotulo', texto: t('Memórias guardadas') });
    const editor = criarMiniChat({
      tipo: 'memoria',
      titulo: t('Pedir uma mudança ao editor de memória (Sonnet 5.5)'),
      descricao: t('Diga o que quer mudar, em palavras normais. Ele lê as memórias, faz a mudança e conta o que mudou.'),
      placeholder: t('Ex.: Mudei de emprego, agora trabalho como designer. Atualize o que você sabe sobre mim.'),
      sugestoes: [t('O que você sabe sobre mim?'), t('Esqueça tudo sobre o meu antigo emprego'), t('Junte as memórias repetidas')],
      rotuloBotao: t('Pedir mudança'),
      aoTerminar: desenharLista,
    });
    alvo.replaceChildren(secao(t('Memória'),
      t('Com a memória ligada, o Claude guarda o que vale lembrar entre conversas, do mesmo jeito que o Claude Code: um arquivo de texto para cada assunto (quem você é, suas preferências, seus projetos) e um índice que ele lê no começo de cada conversa. Tudo fica neste computador e você pode ler, mudar e apagar aqui.'),
      liga('memoria_ligada', t('Ligar a memória'), t('Vale para as conversas novas, no chat e no Code. Ele nunca deve anotar senhas ou documentos.')),
      editor.elemento,
      rotulo, listaEl));
    desenharLista();
  },

  async modelos(alvo) {
    alvo.replaceChildren(
      secao(t('Modelos'), t('O modelo e o raciocínio de cada conversa nova. Dá para trocar a qualquer momento na caixa de texto.'),
        el('div', { class: 'linha-campos' }, campo(t('Modelo no chat'), selecao('modelo_chat', modelosOpcoes())), campo(t('Raciocínio no chat'), selecao('esforco_chat', esforcoOpcoes()))),
        el('div', { class: 'linha-campos' }, campo(t('Modelo no Code'), selecao('modelo_code', modelosOpcoes())), campo(t('Raciocínio no Code'), selecao('esforco_code', esforcoOpcoes()))),
        liga('mostrar_raciocinio', t('Mostrar o raciocínio'), t('Mostra um resumo do que o Claude pensou antes de responder. Não muda o preço.'))),
      secao(t('Conselheiro de modelo'), t('O Haiku lê a conversa na primeira mensagem e depois a cada 5 e diz qual modelo faz a tarefa pelo menor preço. Cada avaliação custa uma fração de centavo.'),
        liga('conselheiro_modelo', t('Sugerir o modelo certo para cada tarefa'), t('Aparece um aviso na conversa quando outro modelo combina mais com o que você pediu.')),
        liga('trocar_modelo_sozinho', t('Deixar o Clave trocar o modelo sozinho'), t('Em vez de só sugerir, ele troca e avisa, com um botão para voltar. Numa conversa em que você voltar, ele não troca mais.'))),
      secao(t('Mais opções'), null,
        liga('modelos_antigos', t('Mostrar modelos antigos'), t('Modelos anteriores que a Anthropic ainda vende. Costumam ser mais caros e menos inteligentes que os atuais.')),
        el('a', { href: '#/aprender/modelos-e-raciocinio', texto: t('Qual modelo escolher?') })));
  },

  async recursos(alvo) {
    alvo.replaceChildren(
      secao(t('Recursos'), null,
        liga('busca_web', t('Deixar o Claude pesquisar na web'), t('Ele decide sozinho quando a resposta precisa de algo atual e mostra as fontes. Cada busca custa US$ 0,01 além dos tokens. Numa conversa, o botão Web desliga só ali.')),
        liga('cache_automatico', t('Cache automático'), t('Reaproveita o começo da conversa entre uma mensagem e outra e cobra bem menos por ele. Deixe ligado.')),
        liga('compactacao', t('Resumir conversas muito longas'), t('Quando a conversa passa do tamanho abaixo, a Anthropic resume o começo dela para caber e ficar mais barata.')),
        campo(t('Resumir a partir de (tokens)'), texto('compactar_em', { tipo: 'number' }), t('Entre 50 mil e 900 mil. Padrão: 150 mil.')),
        liga('troca_se_recusar', t('Trocar de modelo se ele recusar'), t('Se o filtro de segurança recusar um pedido normal por engano, a Anthropic tenta de novo com outro modelo indicado por ela. Não vale para o Haiku.')),
        el('div', { class: 'campo' }, el('span', { texto: t('Recursos desligados por erro') }),
          el('small', { texto: t('Quando a API recusa um destes recursos para um modelo, o Clave desliga só aquele recurso e segue. Se a Anthropic passar a aceitar, religue aqui.') }),
          el('button', { class: 'botao pequeno', type: 'button', texto: t('Religar tudo'), style: 'justify-self:start', onclick: async () => { await api('/compat', { metodo: 'DELETE' }); aviso(t('Recursos religados.')); } }))),
      secao(t('Widgets'), t('Cartões que o Claude desenha na conversa quando ajudam mais que texto: produtos e preços, mapas, recomendações, desenhos e plantas, gráficos, comparações, linhas do tempo e listas de tarefas.'),
        liga('widgets_ligados', t('Deixar o Claude mostrar widgets'), t('Vale para as conversas novas e as respostas seguintes. Os mapas usam o OpenStreetMap pela internet.')),
        campo(t('Fotos de sites de fora'), selecao('widgets_imagens', [
          ['clicar', t('Só carregar quando eu clicar (recomendado)')],
          ['sempre', t('Carregar sempre')]]),
        t('Fotos de produtos e capas vêm de outros sites. Uma página maliciosa poderia usar o endereço de uma foto para tirar dados da conversa; esperar o clique evita isso.'))));
  },

  async limite(alvo) {
    const o = estado.info.orcamento;
    alvo.replaceChildren(
      secao(t('Limite de gasto'), t('O Clave soma o custo de cada resposta e para (ou avisa) quando o mês chega no teto. Quem tem o plano Max ganha crédito mensal na API (US$ 100 no Max 5x, US$ 200 no Max 20x): um bom teto é esse valor.'),
        el('div', { class: 'item-lista' }, el('span', { html: ic('grafico') }), el('span', { class: 'textos' }, el('b', { texto: t('{valor} gastos neste ciclo', { valor: usd(o.gasto, 2) }) }), el('small', { texto: o.teto ? t('{p}% do teto', { p: o.porcentagem.toFixed(1) }) : t('sem teto') })),
          el('a', { class: 'botao pequeno', href: '#/uso', texto: t('Ver detalhes') })),
        el('div', { class: 'linha-campos' },
          campo(t('Teto por mês (US$)'), texto('teto_mensal_usd', { tipo: 'number', placeholder: t('sem teto') }), t('Deixe vazio para não ter teto.')),
          campo(t('Dia em que o mês vira'), texto('dia_virada', { tipo: 'number' }), t('De 1 a 28. Use o dia em que seu crédito renova.'))),
        campo(t('Quando chegar no teto'), selecao('ao_atingir', [['bloquear', t('Parar de responder até o mês virar')], ['avisar', t('Só avisar e continuar')]])),
        campo(t('Teto por tarefa no modo Code (US$)'), texto('teto_tarefa_code_usd', { tipo: 'number' }), t('Uma tarefa longa no Code pausa ao gastar isso, e você decide se continua. 0 = sem teto.')),
        campo(t('Ações seguidas no modo Code'), texto('max_voltas_code', { tipo: 'number' }), t('Quantas ações (ler, editar, rodar um comando) o Claude faz num envio antes de pausar e pedir "continue". De 10 a 1000.')),
        el('p', { class: 'ajuda', texto: t('Para ter uma trava que nem o Clave consegue passar, crie no Console da Anthropic um workspace com limite de gasto e use uma chave dele.') })));
  },

  async code(alvo) {
    // a caixa cresce até mostrar a lista inteira (16 linhas no máximo, depois rola sem cortar uma linha ao meio)
    const prot = el('textarea', { class: 'area mono', style: 'font-size:13px;field-sizing:content;min-height:calc(6 * 1.5em + 20px);max-height:calc(16 * 1.5em + 20px)' });
    prot.value = (cfg().protegidos || []).join('\n');
    prot.addEventListener('change', () => salvar({ protegidos: prot.value.split('\n').map((x) => x.trim()).filter(Boolean) }, t('Salvo.')));
    alvo.replaceChildren(
      secao(t('Modo Code'), t('No modo Code o Claude trabalha numa pasta do seu computador: lê, cria e edita arquivos e roda comandos.'),
        campo(t('Permissão padrão'), selecao('permissao_code', [
          ['perguntar', t('Perguntar: pede OK para editar e rodar comandos')],
          ['aceitar_edicoes', t('Aceitar edições: só pede OK para comandos')],
          ['plano', t('Plano: só lê e propõe')],
          ['livre', t('Livre: faz tudo (menos apagar ou publicar)')]])),
        liga('pedir_ok_plano', t('Pedir OK antes de tarefas grandes'), t('Antes de mexer em vários arquivos ou fazer algo difícil de desfazer, o Claude mostra o plano e espera você dizer "pode ir", em qualquer modo. Vale para as conversas novas.')),
        liga('carregar_claude_md', t('Ler as regras da pasta (CLAUDE.md e AGENTS.md)'), t('Como no Claude Code: as regras escritas na pasta e nas pastas acima dela valem para o Claude.')),
        liga('navegador_ligado', t('Deixar o Claude usar o navegador do Code'), t('Ele abre páginas, lê, tira print e, com o seu OK, clica e digita. Fora do modo Livre, você libera cada site novo uma vez por tarefa (o seu computador, localhost, não pergunta). Senha e cartão quem digita é você. Só funciona na janela do Clave.')),
        el('div', { class: 'campo' }, el('span', { texto: t('Dados do navegador') }),
          el('small', { texto: t('Apaga cookies, logins, armazenamento e cache do navegador do Code. Os sites vão pedir login de novo. "Sair da conta" também apaga.') }),
          el('button', { class: 'botao pequeno', type: 'button', style: 'justify-self:start', texto: t('Apagar os dados do navegador'), onclick: async (e) => {
            e.currentTarget.disabled = true;
            try {
              const r = await api('/navegador/limpar', { metodo: 'POST' });
              aviso(r.ok ? t('Dados do navegador apagados.') : t('O navegador só existe na janela do Clave.'), r.ok ? '' : 'erro');
            } catch (erro) { aviso(erro.message, 'erro'); } finally { e.currentTarget.disabled = false; }
          } })),
        campo(t('Arquivos e pastas protegidos'), prot, t('Um por linha (ex.: .env, *.key, segredos/**). As ferramentas de arquivo nunca leem nem mudam o que combina com estes padrões, e um comando que cite um deles sempre pede o seu OK.'))),
      secao(t('Regras de permissão'), t('Para liberar ou bloquear ações específicas (um comando, uma pasta, um site), sem mudar o modo inteiro. Mesmo formato do Claude Code.'),
        el('a', { class: 'botao', href: '#/permissoes', html: `${ic('escudo')}${t('Abrir as regras de permissão')}` })));
  },

  async github(alvo) {
    alvo.replaceChildren(el('p', { class: 'ajuda', texto: t('Carregando…') }));
    const g = await api('/github/estado');
    const token = el('input', { class: 'entrada mono', type: 'password', placeholder: t('ghp_... ou github_pat_...') });
    const conectar = async (origem) => {
      try { const r = await api('/github/conectar', { metodo: 'POST', corpo: { origem, token: token.value } }); await carregarEstado(); aviso(origem ? t('Conectado como {login}.', { login: r.usuario?.login }) : t('Desconectado.')); SECOES.github(alvo); }
      catch (e) { aviso(e.message, 'erro'); }
    };
    const conectado = g.origem && g.usuario;
    alvo.replaceChildren(secao(t('GitHub'), t('Conecte para anexar arquivos dos seus repositórios e deixar o Claude ler código, issues e pull requests. Criar issue, comentar e abrir PR sempre pedem o seu OK.'),
      conectado ? el('div', { class: 'item-lista' }, el('span', { html: ic('ramo') }), el('span', { class: 'textos' }, el('b', { texto: g.usuario.login }), el('small', { texto: g.origem === 'gh' ? t('Pelo login do gh') : t('Por token pessoal') })),
        el('button', { class: 'botao pequeno', type: 'button', texto: t('Desconectar'), onclick: () => conectar('') }))
        : g.erro ? el('div', { class: 'nota-conversa erro' }, el('span', { html: ic('alerta') }), g.erro) : null,
      !conectado ? el('div', { style: 'display:grid;gap:12px' },
        g.gh_instalado ? el('button', { class: 'botao primario', type: 'button', texto: t('Usar o login do gh (GitHub CLI)'), onclick: () => conectar('gh') }) : null,
        campo(t('Ou cole um token pessoal'), token, t('Crie em github.com > Settings > Developer settings > Personal access tokens. Para ler, basta a permissão de leitura dos repositórios.')),
        el('button', { class: 'botao', type: 'button', texto: t('Conectar com o token'), onclick: () => conectar('token') }),
        el('a', { href: '#/aprender/github', texto: t('O que é o GitHub e para que serve?') })) : null,
      conectado ? liga('github_ferramentas', t('Ferramentas do GitHub ligadas por padrão'), t('Deixa o Claude consultar seus repositórios durante a conversa (botão GitHub na caixa de texto).')) : null,
      conectado ? liga('github_escrita', t('Permitir criar issue, comentar e abrir PR'), t('Mesmo ligado, cada ação pede o seu OK antes.')) : null));
  },

  async conectores(alvo) {
    // ---- e-mail ----
    const em = cfg().email || {};
    const TIPOS = [['gmail', 'Gmail'], ['outlook', t('Outlook do computador')], ['yahoo', 'Yahoo'], ['zoho', 'Zoho'], ['imap', t('Outro provedor')]];
    let tipo = em.tipo || 'gmail';
    const endereco = el('input', { class: 'entrada', type: 'email', placeholder: t('voce@empresa.com.br'), autocomplete: 'off' });
    endereco.value = em.endereco || '';
    const senha = el('input', { class: 'entrada mono', type: 'password', placeholder: em.ligado && em.tipo !== 'outlook' ? t('(guardada; cole de novo só para trocar)') : t('16 letras, sem espaços'), autocomplete: 'off' });
    const imap = el('input', { class: 'entrada mono', placeholder: 'imap.seuprovedor.com.br' }); imap.value = em.tipo === 'imap' ? em.imap || '' : '';
    const imapPorta = el('input', { class: 'entrada mono', type: 'number', placeholder: '993' }); imapPorta.value = em.tipo === 'imap' ? em.imap_porta || '' : '';
    const smtp = el('input', { class: 'entrada mono', placeholder: 'smtp.seuprovedor.com.br' }); smtp.value = em.tipo === 'imap' ? em.smtp || '' : '';
    const smtpPorta = el('input', { class: 'entrada mono', type: 'number', placeholder: '465' }); smtpPorta.value = em.tipo === 'imap' ? em.smtp_porta || '' : '';
    const camposSenha = el('div', { style: 'display:grid;gap:12px' });
    const camposServidor = el('div', { class: 'linha-campos' }, campo(t('Servidor IMAP'), imap), campo(t('Porta IMAP'), imapPorta), campo(t('Servidor SMTP'), smtp), campo(t('Porta SMTP'), smtpPorta));
    const ajudaTipo = el('p', { class: 'ajuda' });
    const resultado = el('p', { class: 'ajuda' });
    const desenharTipo = () => {
      seg.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === tipo)));
      const outlook = tipo === 'outlook';
      camposSenha.hidden = outlook;
      camposServidor.hidden = tipo !== 'imap';
      ajudaTipo.textContent = {
        gmail: t('No Gmail: ligue a verificação em duas etapas na sua Conta Google e crie uma "senha de app" em myaccount.google.com/apppasswords. Cole aqui as 16 letras (não é a sua senha normal).'),
        outlook: t('Para Outlook.com e Microsoft 365, que não aceitam mais senha por fora: o Clave usa o Outlook clássico instalado neste computador, já com a sua conta. O Outlook novo não deixa outros programas usarem o e-mail; nesse caso, use o Zapier abaixo.'),
        yahoo: t('No Yahoo: em Segurança da conta, gere uma "senha de app" e cole aqui.'),
        zoho: t('No Zoho Mail: ative o IMAP nas configurações e gere uma "senha específica de aplicativo".'),
        imap: t('Provedor de hospedagem (o e-mail do site da empresa): o endereço dos servidores IMAP e SMTP e as portas estão na página de ajuda do provedor. Use a senha da caixa ou uma senha de app, se ele tiver.'),
      }[tipo];
    };
    const seg = el('div', { class: 'segmentado', role: 'group', 'aria-label': t('Tipo de e-mail') },
      ...TIPOS.map(([v, rot]) => el('button', { type: 'button', texto: rot, dados: { v }, onclick: () => { tipo = v; desenharTipo(); } })));
    camposSenha.append(campo(t('Endereço de e-mail'), endereco), campo(t('Senha de app'), senha, t('Fica guardada criptografada neste computador, só para o e-mail.')));
    desenharTipo();
    const blocoEmail = secao(t('E-mail'),
      t('Deixa o Claude ler os seus e-mails e escrever respostas. Ler é livre; enviar sempre mostra o e-mail inteiro e espera o seu OK. No modo Code ele também salva anexos na pasta.'),
      em.ligado ? el('p', { class: 'etiqueta acao', texto: t('Ligado: {conta}', { conta: em.tipo === 'outlook' ? t('Outlook do computador') : em.endereco }) }) : null,
      seg, ajudaTipo, camposSenha, camposServidor,
      el('div', { class: 'linha-botoes' },
        el('button', { class: 'botao primario', type: 'button', texto: t('Salvar e testar'), onclick: async () => {
          resultado.textContent = t('Testando…');
          try {
            const r = await api('/email/salvar', { metodo: 'POST', corpo: { tipo, endereco: endereco.value, senha: senha.value, imap: imap.value, imap_porta: imapPorta.value, smtp: smtp.value, smtp_porta: smtpPorta.value } });
            await carregarEstado();
            resultado.textContent = r.mensagem;
            aviso(r.ok ? t('E-mail ligado.') : t('Salvo, mas o teste falhou: confira os dados.'), r.ok ? '' : 'erro');
          } catch (e) { resultado.textContent = e.message; aviso(e.message, 'erro'); }
        } }),
        em.ligado ? el('button', { class: 'botao', type: 'button', texto: t('Desligar o e-mail'), onclick: async () => {
          await api('/email/desligar', { metodo: 'POST' }); await carregarEstado(); SECOES.conectores(alvo);
        } }) : null),
      resultado);

    // ---- Zapier: Gmail, Planilhas e Agenda do Google, Outlook, WhatsApp e centenas de apps ----
    const urlZapier = el('input', { class: 'entrada mono', placeholder: 'https://mcp.zapier.com/...' });
    const chaveZapier = el('input', { class: 'entrada mono', type: 'password', placeholder: t('só se o Zapier mostrar uma chave'), autocomplete: 'off' });
    const blocoZapier = secao(t('Zapier (Google, Microsoft, WhatsApp e mais)'),
      t('O Zapier liga o Claude a centenas de apps (Gmail, Planilhas e Agenda do Google, Outlook, WhatsApp Business, CRMs) sem você programar nada. É um serviço de fora, com plano grátis limitado: cada ação que o Claude faz por ele conta no seu plano do Zapier.'),
      el('ol', { class: 'passos-ajuda' },
        el('li', { texto: t('Crie uma conta em zapier.com e abra mcp.zapier.com.') }),
        el('li', { texto: t('Clique em "+ New MCP Server", escolha o cliente "Anthropic API" e crie.') }),
        el('li', { texto: t('Na aba Configure, adicione as ações que quer liberar (ex.: Gmail: procurar e-mail; Google Sheets: adicionar linha). Libere só o que precisa.') }),
        el('li', { texto: t('Copie o endereço do servidor (e a chave, se aparecer) e cole abaixo.') })),
      el('div', { class: 'linha-campos' }, campo(t('Endereço do servidor'), urlZapier), campo(t('Chave (opcional)'), chaveZapier)),
      el('button', { class: 'botao', type: 'button', html: `${ic('conector')}${t('Ligar o Zapier')}`, onclick: async () => {
        if (!/^https:\/\//.test(urlZapier.value.trim())) { aviso(t('Cole o endereço https:// que o Zapier mostrou.'), 'erro'); return; }
        if (chaveZapier.value.trim()) await api('/conectores/token', { metodo: 'POST', corpo: { nome: 'zapier', token: chaveZapier.value.trim() } });
        const outros = (cfg().conectores_mcp || []).filter((m) => m.nome !== 'zapier');
        await salvar({ conectores_mcp: [...outros, { nome: 'zapier', url: urlZapier.value.trim(), ligado: true }] }, t('Zapier ligado.'));
        SECOES.conectores(alvo);
      } }));

    const lista = cfg().conectores_mcp || [];
    const nome = el('input', { class: 'entrada', placeholder: t('ex.: deepwiki') });
    const url = el('input', { class: 'entrada mono', placeholder: t('https://mcp.exemplo.com/mcp') });
    const token = el('input', { class: 'entrada mono', type: 'password', placeholder: t('só se o serviço pedir'), autocomplete: 'off' });
    alvo.replaceChildren(blocoEmail, blocoZapier, secao(t('Conectores (MCP)'),
      t('Conectores ligam o Claude a outros serviços (documentação, ferramentas, bancos de dados) que falam o padrão MCP. A Anthropic se conecta direto ao endereço, então só funciona com servidores MCP públicos na internet (não com os do seu computador). Use só serviços em que você confia.'),
      lista.length ? el('div', { class: 'lista-itens' }, ...lista.map((m, i) => el('div', { class: 'item-lista' },
        el('span', { html: ic('conector') }), el('span', { class: 'textos' }, el('b', { texto: m.nome }), el('small', { class: 'mono', texto: m.url })),
        chaveLiga({ rotulo: m.ligado ? t('Ligado') : t('Desligado'), marcado: m.ligado, aoMudar: async (v) => { lista[i] = { ...m, ligado: v }; await salvar({ conectores_mcp: lista }); SECOES.conectores(alvo); } }),
        el('button', { class: 'icone-botao', type: 'button', 'aria-label': t('Apagar conector'), html: ic('lixo'), onclick: async () => { await api('/conectores/token', { metodo: 'POST', corpo: { nome: m.nome, token: '' } }); lista.splice(i, 1); await salvar({ conectores_mcp: lista }); SECOES.conectores(alvo); } }))))
        : el('p', { class: 'ajuda', texto: t('Nenhum conector.') }),
      el('div', { class: 'linha-campos' }, campo(t('Nome'), nome), campo(t('Endereço (URL)'), url)),
      campo(t('Token de acesso (opcional)'), token, t('Fica guardado criptografado neste computador e vai só para esse conector.')),
      el('button', { class: 'botao', type: 'button', html: `${ic('mais')}${t('Adicionar conector')}`, onclick: async () => {
        const n = nome.value.trim().replace(/[^\w-]/g, '-');
        if (!n || !/^https:\/\//.test(url.value.trim())) { aviso(t('Preencha um nome e um endereço https://'), 'erro'); return; }
        if (token.value.trim()) await api('/conectores/token', { metodo: 'POST', corpo: { nome: n, token: token.value.trim() } });
        await salvar({ conectores_mcp: [...lista.filter((m) => m.nome !== n), { nome: n, url: url.value.trim(), ligado: true }] }, t('Conector adicionado.'));
        SECOES.conectores(alvo);
      } })));
  },

  async aparencia(alvo) {
    const tema = el('div', { class: 'segmentado', role: 'group', 'aria-label': t('Tema') }, ...[['sistema', t('Do sistema')], ['claro', t('Claro')], ['escuro', t('Escuro')]].map(([v, rot]) =>
      el('button', { type: 'button', 'aria-pressed': String(cfg().tema === v), texto: rot, onclick: async () => { await salvar({ tema: v }); SECOES.aparencia(alvo); } })));
    const tamanho = el('input', { type: 'range', min: '14', max: '22', step: '1', value: cfg().tamanho_letra || 17 });
    const rotTam = el('span', { class: 'meta', texto: `${tamanho.value}px` });
    tamanho.addEventListener('input', () => { rotTam.textContent = `${tamanho.value}px`; document.documentElement.style.setProperty('--t-leitura', `${tamanho.value}px`); });
    tamanho.addEventListener('change', () => salvar({ tamanho_letra: Number(tamanho.value) }));
    // o idioma troca a interface, as lições, os prompts e o modelo de pasta; a tela recarrega para valer em tudo
    const idiomas = el('div', { class: 'segmentado', role: 'group', 'aria-label': t('Idioma') },
      ...[['pt-BR', 'Português (Brasil)'], ['en', 'English']].map(([v, rot]) =>
        el('button', { type: 'button', 'aria-pressed': String(cfg().idioma === v), texto: rot, onclick: async () => {
          if (cfg().idioma === v) return;
          await salvar({ idioma: v });
          location.reload();
        } })));
    alvo.replaceChildren(secao(t('Aparência'), null,
      el('div', { class: 'campo' }, el('span', { texto: t('Idioma') }), idiomas,
        el('small', { texto: t('Vale para a interface, as lições, o modelo de pasta e o que o Clave diz ao Claude. O Claude responde no idioma em que você escrever.') })),
      el('div', { class: 'campo' }, el('span', { texto: t('Tema') }), tema),
      el('div', { class: 'campo' }, el('span', { texto: t('Tamanho da letra das respostas') }), el('div', { style: 'display:flex;gap:12px;align-items:center' }, tamanho, rotTam)),
      el('div', { class: 'linha-campos' },
        campo(t('Letra das respostas'), selecao('letra_resposta', [['serifa', t('Serifada (de livro)')], ['sans', t('Sem serifa')]])),
        campo(t('Largura da conversa'), selecao('largura_chat', [['estreita', t('Estreita')], ['media', t('Média')], ['larga', t('Larga')]]))),
      campo(t('Enviar mensagem com'), selecao('enviar_com', [['enter', t('Enter (Shift+Enter pula linha)')], ['ctrl_enter', t('Ctrl+Enter (Enter pula linha)')]])),
      liga('mostrar_custo', t('Mostrar o custo de cada resposta'), t('Aparece pequeno, embaixo de cada resposta.')),
      liga('painel_uso_inicio', t('Painel de uso no início'), t('Mostra tokens, dias seguidos, mapa de calor, modelo favorito e a projeção do mês na tela de conversa nova.')),
      liga('notificacoes', t('Notificação do Windows'), t('Avisa quando o Claude termina, pede o seu OK, propõe um fluxo ou quando uma rotina acaba, se a janela do Clave estiver em segundo plano.')),
      !window.clave && 'Notification' in window && Notification.permission !== 'granted' ? el('button', { class: 'botao', type: 'button', texto: t('Deixar o navegador mostrar as notificações'),
        onclick: async () => { await Notification.requestPermission(); SECOES.aparencia(alvo); } }) : null));
  },

  async dados(alvo) {
    alvo.replaceChildren(secao(t('Dados e backup'),
      t('Suas conversas, projetos e gastos ficam num arquivo dentro da pasta dados/ do Clave, neste computador. Nada vai para outro lugar além da própria Anthropic (as mensagens que você manda).'),
      el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap' },
        el('a', { class: 'botao', href: '/api/backup', html: `${ic('baixar')}${t('Baixar backup das conversas')}` }),
        el('button', { class: 'botao', type: 'button', html: `${ic('subir')}${t('Importar backup')}`, onclick: async () => {
          const [f] = await escolherArquivos({ multiplo: false, aceitar: '.json' });
          if (!f) return;
          try {
            const r = await fetch('/api/backup', { method: 'POST', body: f, credentials: 'same-origin' }).then((x) => x.json());
            if (r.erro) throw new Error(r.erro);
            aviso(t('Importado: {conversas} conversa(s), {mensagens} mensagem(ns).', { conversas: r.importado.conversas, mensagens: r.importado.mensagens }));
          } catch (e) { aviso(e.message, 'erro'); }
        } })),
      el('p', { class: 'ajuda', texto: t('O backup leva as conversas, os projetos, as rotinas e o histórico de gasto. Os arquivos anexados, a memória e a chave não vão junto.') })));
  },

  async sobre(alvo) {
    const info = estado.info;
    alvo.replaceChildren(
      secao(t('Atualizações'), null,
        el('div', { class: 'item-lista item-acao' }, el('span', { html: ic('subir') }), el('span', { class: 'textos' }, el('b', { texto: t('Versão {versao}', { versao: info.versao }) }),
          el('small', { texto: info.dev ? t('Cópia de desenvolvimento (atualize com git pull)') : (cfg().ultima_checagem ? t('Última verificação: {quando}', { quando: cfg().ultima_checagem }) : t('Ainda não verificou')) })),
          el('button', { class: 'botao pequeno', type: 'button', texto: t('Procurar atualização'), onclick: async () => { const r = await checarAtualizacao({ forcar: true }); if (r?.nova) abrirAtualizacao(); } })),
        liga('checar_atualizacoes', t('Procurar atualização sozinho'), t('Uma vez por dia, ao abrir. Nunca instala sem você clicar.')),
        liga('baixar_videos', t('Baixar os vídeos das lições sozinho'), t('Em segundo plano, só os do idioma do app (uns 30 MB). Assim a lição já abre com o vídeo pronto. Desligado, ele baixa quando você der play.'))),
      secao(t('Sobre o Clave'), null,
        el('p', { style: 'margin:0', texto: t('O Clave é um app independente para usar o Claude pela API da Anthropic, com a sua chave. Ele não é um produto da Anthropic nem tem ligação com ela. "Claude" é marca da Anthropic.') }),
        el('p', { class: 'ajuda', texto: t('Feito com: marked, DOMPurify, highlight.js, KaTeX, xterm.js, Leaflet, fontes Source Serif 4 e IBM Plex, o SDK oficial da Anthropic para Python e o Electron. Mapas do OpenStreetMap (© colaboradores do OpenStreetMap). As licenças estão na pasta app/vendor.') }),
        el('div', { style: 'display:flex;gap:8px;flex-wrap:wrap' },
          el('a', { class: 'botao', href: '#/aprender', texto: t('Abrir as lições') }),
          el('button', { class: 'botao perigo', type: 'button', html: `${ic('sair')}${t('Fechar o Clave')}`, onclick: async () => {
            if (!await confirmar(t('Fechar o Clave? Respostas em andamento são interrompidas.'), { sim: t('Fechar') })) return;
            if (window.clave?.sair) window.clave.sair(); else { await api('/sair', { metodo: 'POST' }).catch(() => {}); document.body.innerHTML = `<p style="padding:40px;font-family:sans-serif">${t('O Clave foi fechado. Pode fechar esta janela.')}</p>`; }
          } }))),
      secao(t('Sair e desinstalar'), null,
        el('div', { class: 'item-lista item-acao' }, el('span', { html: ic('chave') }),
          el('span', { class: 'textos' }, el('b', { texto: t('Sair da conta') }),
            el('small', { texto: t('Apaga a chave e as senhas, volta tudo ao padrão e mostra a apresentação e os tours de novo. As conversas ficam.') })),
          el('button', { class: 'botao pequeno', type: 'button', texto: t('Sair da conta'), onclick: sairDaConta })),
        el('div', { class: 'item-lista item-acao' }, el('span', { html: ic('lixo') }),
          el('span', { class: 'textos' }, el('b', { texto: t('Desinstalar o Clave') }),
            el('small', { texto: info.dev ? t('Esta é uma cópia de desenvolvimento: apague a pasta à mão, se quiser.') : t('Tira o Clave do computador: a pasta, os atalhos e as tarefas das rotinas.') })),
          el('button', { class: 'botao pequeno perigo', type: 'button', texto: t('Desinstalar'), disabled: !!info.dev, onclick: desinstalar }))));
  },
};
