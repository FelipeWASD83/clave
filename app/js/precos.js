// Preços e planos: quanto custa cada modelo, a projeção do mês e a conta "API ou assinatura?".
import { api } from './api.js';
import { ic } from './icones.js';
import { el, usd, dataBr, aviso } from './ui.js';

const NOMES_ACABA = {
  ja: () => 'O teto deste mês já foi atingido.',
  neste_ciclo: (a) => `No ritmo atual, o teto acaba em ${dataBr(a.data)} (daqui a ${a.dias} dia${a.dias === 1 ? '' : 's'}).`,
  depois: (a) => a.dias <= 90 ? `No ritmo atual, o teto não acaba neste ciclo (só em ${dataBr(a.data)}).` : 'No ritmo atual, o teto não acaba neste ciclo.',
  sem_ritmo: () => 'Sem gasto nos últimos dias: o teto não está acabando.',
};

// texto da projeção, usado aqui e no painel de uso do início
export function textoProjecao(p) {
  if (!p) return '';
  if (p.pouco_dado && !p.ritmo_dia) return 'Ainda não há uso suficiente para estimar o mês.';
  const base = `No ritmo dos últimos ${Math.round(p.dias_base)} dia${Math.round(p.dias_base) === 1 ? '' : 's'} (${usd(p.ritmo_dia)} por dia), este ciclo fecha em cerca de ${usd(p.previsto_ciclo, 2)}.`;
  const acaba = p.teto && p.acaba ? ' ' + NOMES_ACABA[p.acaba.situacao](p.acaba) : (p.teto ? '' : ' Sem teto definido.');
  return base + acaba;
}

export async function telaPrecos(principal) {
  const d = await api('/precos');
  const atuais = d.modelos.filter((m) => m.atual);
  const antigos = d.modelos.filter((m) => !m.atual);
  const resultado = el('div', { class: 'estimativa-resultado', 'aria-live': 'polite' });

  // ---------- formulário "API ou assinatura?" ----------
  const plano = el('select', { class: 'entrada' }, ...d.planos.map((p) => el('option', { value: p.id, texto: `${p.nome} (${usd(p.preco, 0)} por mês)` })));
  const preco = el('input', { class: 'entrada mono', type: 'number', min: '0', step: '1', value: d.planos[0].preco });
  const modoUso = el('div', { class: 'segmentos', role: 'radiogroup', 'aria-label': 'Como contar o seu uso' });
  let porLimite = true;
  const janelas = el('input', { type: 'range', min: '0', max: '42', step: '1', value: '10' });
  const pct = el('input', { type: 'range', min: '10', max: '100', step: '5', value: '60' });
  const msgs = el('input', { class: 'entrada mono', type: 'number', min: '0', step: '1', value: '30' });
  const perfil = el('select', { class: 'entrada' }, ...Object.entries(d.perfis).map(([id, p]) => el('option', { value: id, texto: `${p.nome}: ${p.descricao}` })));
  const raciocinio = el('input', { type: 'checkbox', checked: true });
  const valorJanelas = el('b', { class: 'mono' });
  const valorPct = el('b', { class: 'mono' });
  const blocoLimite = el('div', { class: 'campos-uso' },
    el('label', { class: 'campo' }, el('span', {}, 'Janelas de 5 horas por semana em que você usa o Claude: ', valorJanelas), janelas,
      el('small', { texto: 'Uma janela é o período de 5 horas do limite. Quem usa todo dia, de manhã e de tarde, tem umas 10 a 14 por semana.' })),
    el('label', { class: 'campo' }, el('span', {}, 'Quanto do limite você gasta em cada uma: ', valorPct), pct,
      el('small', { texto: '100% é bater o limite toda vez.' })));
  const blocoMsgs = el('label', { class: 'campo', hidden: true }, el('span', { texto: 'Mensagens por dia (em média)' }), msgs);
  const botaoModo = (texto, limite) => el('button', { type: 'button', role: 'radio', 'aria-checked': String(limite === porLimite), texto,
    onclick: () => { porLimite = limite; modoUso.querySelectorAll('button').forEach((b, i) => b.setAttribute('aria-checked', String((i === 0) === porLimite))); blocoLimite.hidden = !porLimite; blocoMsgs.hidden = porLimite; calcular(); } });
  modoUso.append(botaoModo('Pelo limite da assinatura', true), botaoModo('Por mensagens por dia', false));

  let espera = null;
  const calcular = () => {
    valorJanelas.textContent = janelas.value;
    valorPct.textContent = `${pct.value}%`;
    clearTimeout(espera);
    espera = setTimeout(async () => {
      const corpo = { plano: plano.value, preco: preco.value, perfil: perfil.value, raciocinio: raciocinio.checked };
      if (porLimite) Object.assign(corpo, { janelas: janelas.value, porcentagem: pct.value });
      else corpo.mensagens_dia = msgs.value;
      try { desenharResultado(await api('/precos/estimar', { metodo: 'POST', corpo })); }
      catch (e) { aviso(e.message, 'erro'); }
    }, 200);
  };
  plano.addEventListener('change', () => { preco.value = d.planos.find((p) => p.id === plano.value).preco; calcular(); });
  [preco, janelas, pct, msgs].forEach((x) => x.addEventListener('input', calcular));
  [perfil, raciocinio].forEach((x) => x.addEventListener('change', calcular));

  function desenharResultado(r) {
    const p = r.plano;
    const maior = Math.max(p.preco, ...r.modelos.map((m) => Math.max(m.custo_mes, m.custo_mes_real || 0)), 0.01);
    const marca = `${(p.preco / maior) * 100}%`;
    resultado.replaceChildren(
      el('p', { class: 'estimativa-resumo' },
        'Isso dá cerca de ', el('b', { texto: `${r.mensagens_mes.toLocaleString('pt-BR')} mensagens por mês` }),
        ` (${r.mensagens_semana.toLocaleString('pt-BR')} por semana). Na API, cada modelo custaria:`),
      el('div', { class: 'comparacao' },
        ...r.modelos.map((m) => {
          const dif = p.preco - m.custo_mes;
          return el('div', { class: `comparacao-linha ${m.mais_barato ? 'barato' : 'caro'}` },
            el('span', { class: 'comparacao-nome', texto: m.nome }),
            el('span', { class: 'comparacao-trilho' },
              el('i', { style: `width:${Math.max(0.6, (m.custo_mes / maior) * 100)}%` }),
              m.custo_mes_real != null ? el('i', { class: 'real', style: `width:${Math.max(0.6, (m.custo_mes_real / maior) * 100)}%`, title: 'Pelo seu uso real no Clave' }) : null,
              el('b', { class: 'comparacao-marca', style: `left:${marca}`, title: `${p.nome}: ${usd(p.preco, 2)}` })),
            el('span', { class: 'comparacao-valor' },
              el('b', { texto: usd(m.custo_mes, 2) }),
              el('small', { texto: dif >= 0 ? `${usd(dif, 2)} a menos que o ${p.nome}` : `${usd(-dif, 2)} a mais que o ${p.nome}` }),
              m.custo_mes_real != null ? el('small', { class: 'real', texto: `pelo seu uso real: ${usd(m.custo_mes_real, 2)}` }) : null));
        })),
      el('p', { class: 'ajuda', html: `A linha tracejada é o preço do ${p.nome} (${usd(p.preco, 2)}).${p.credito_api ? ` O ${p.nome} também dá ${usd(p.credito_api, 0)} de crédito na API por mês, que o Clave pode usar.` : ''}` }));
  }

  // ---------- tabela de modelos ----------
  const cabModelos = ['Modelo', 'Entrada', 'Escreve no cache', 'Lê do cache', 'Saída', ...Object.values(d.perfis).map((p) => `Mensagem ${p.nome.split(' ')[1].replace(/s$/, '')}`)];
  const linhaModelo = (m) => [
    el('span', {}, el('b', { texto: m.nome }), m.longo ? el('small', { class: 'meta', texto: ` · ${m.longo.multiplicador}x acima de ${(m.longo.acima_de / 1000).toLocaleString('pt-BR')} mil tokens` }) : null),
    usd(m.entrada, 2), usd(m.cache_escrita, 2), usd(m.cache_leitura, 2), usd(m.saida, 2),
    ...Object.keys(d.perfis).map((p) => usd(m.por_mensagem[p])),
  ];

  principal.replaceChildren(el('div', { class: 'pagina' }, el('div', { class: 'pagina-corpo' },
    el('div', { class: 'pagina-cab' }, el('div', {}, el('h1', { texto: 'Preços e planos' }),
      el('p', { texto: 'Quanto custa cada modelo, quanto você deve gastar no mês e se a API sai mais barata que a assinatura do Claude para o seu jeito de usar.' }))),

    el('div', { class: 'uso-topo' },
      el('div', { class: 'uso-painel' },
        el('div', { class: 'meta', texto: 'Sua projeção' }),
        el('div', { class: 'uso-valor' }, usd(d.projecao.previsto_ciclo, 2), ' ', el('small', { texto: `até ${dataBr(d.projecao.fim_ciclo)}` })),
        el('p', { class: 'projecao-texto', texto: textoProjecao(d.projecao) }),
        el('p', { class: 'ajuda' }, d.projecao.teto ? `Teto do mês: ${usd(d.projecao.teto, 2)}. ` : '',
          'Assina o Max? O crédito dele na API (US$ 100 no 5x, US$ 200 no 20x) é um bom teto: ',
          el('a', { href: '#/config/limite', texto: 'mudar o teto' }), '.')),
      el('div', { class: 'uso-painel' },
        el('div', { class: 'meta', texto: 'Os planos do Claude' }),
        el('table', { class: 'tabela compacta' }, el('tbody', {}, ...d.planos.map((p) => el('tr', {},
          el('td', {}, el('b', { texto: p.nome }), el('div', { class: 'meta', texto: p.multiplicador === 1 ? 'o uso básico' : `${p.multiplicador}x o uso do Pro` })),
          el('td', { class: 'num' }, usd(p.preco, 0), el('div', { class: 'meta', texto: p.preco_anual ? `${usd(p.preco_anual, 0)} no anual` : 'só mensal' })),
          el('td', { class: 'num' }, p.credito_api ? `${usd(p.credito_api, 0)} de API` : ''))))),
        el('p', { class: 'ajuda', texto: 'Preços conferidos em claude.com/pricing em 14/10/2026. O do Max 20x vem de guias de terceiros (a página oficial diz "a partir de US$ 100"). Mudou? Ajuste o preço na conta abaixo.' }))),

    el('div', { class: 'secao-titulo', texto: 'API ou assinatura?' }),
    el('div', { class: 'estimativa' },
      el('div', { class: 'estimativa-form' },
        el('label', { class: 'campo' }, el('span', { texto: 'Plano que você usa (ou pensa em usar)' }), plano),
        el('label', { class: 'campo' }, el('span', { texto: 'Preço que você paga por mês (US$)' }), preco),
        el('div', { class: 'campo' }, el('span', { texto: 'Como contar o seu uso' }), modoUso),
        blocoLimite, blocoMsgs,
        el('label', { class: 'campo' }, el('span', { texto: 'Tamanho das suas conversas' }), perfil),
        el('label', { class: 'linha-check' }, raciocinio, el('span', { texto: 'Com raciocínio (o Claude pensa antes de responder)' }))),
      resultado),
    el('details', { class: 'notas-estimativa' },
      el('summary', { texto: 'De onde vêm esses números' }),
      el('ul', {},
        el('li', { texto: `A Anthropic não publica o limite das assinaturas em tokens. O único número oficial é um piso: no Pro, pelo menos ${d.mensagens_por_janela} mensagens curtas a cada janela de 5 horas; o Max 5x e o Max 20x dão 5 e 20 vezes isso. A conta usa esse piso, então quem manda mensagens curtas provavelmente usa mais do que ela diz.` }),
        el('li', { texto: 'Além da janela de 5 horas, as assinaturas têm um limite semanal que a Anthropic também não publica.' }),
        el('li', { texto: 'O custo de cada mensagem é uma suposição do tamanho típico (a tabela de modelos mostra o resultado). Quando você já tem 10 respostas ou mais de um modelo no chat do Clave, aparece também a conta pelo seu custo real.' }),
        el('li', { texto: 'No plano, o Claude Code gasta do mesmo limite que o chat. Aqui, o modo Code gasta por uso, como o chat.' }))),

    el('div', { class: 'secao-titulo', texto: 'Preço de cada modelo' }),
    el('p', { class: 'ajuda', texto: 'Em US$ por milhão de tokens (um milhão de tokens são umas 750 mil palavras). As três últimas colunas são o custo de uma mensagem de cada tamanho, com raciocínio.' }),
    tabela(cabModelos, atuais.map(linhaModelo)),
    antigos.length ? el('details', { class: 'notas-estimativa' }, el('summary', { texto: `Modelos anteriores (${antigos.length})` }), tabela(cabModelos, antigos.map(linhaModelo))) : null,
    el('p', { class: 'ajuda' }, 'Preços da página oficial da Anthropic em 14/10/2026. Busca na web: US$ 10 por mil buscas, mais os tokens. ',
      el('a', { href: '#/uso', html: `${ic('grafico')} Ver o seu uso` })))));
  calcular();
  return {};
}

function tabela(cab, linhas) {
  return el('div', { style: 'overflow-x:auto' }, el('table', { class: 'tabela' },
    el('thead', {}, el('tr', {}, ...cab.map((c, i) => el('th', { class: i > 0 ? 'num' : '', texto: c })))),
    el('tbody', {}, ...linhas.map((l) => el('tr', {}, ...l.map((v, i) => el('td', { class: i > 0 ? 'num' : '' }, v instanceof Node ? v : String(v))))))));
}
