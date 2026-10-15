// 5.0: o Haiku virou o padrão também de quem já usava o Clave. Uma vez, depois de atualizar, a pessoa vê o modelo que
// usava antes e escolhe manter o Haiku ou voltar (o servidor guarda os modelos de antes em cfg.aviso_haiku).
import { cfg, modeloInfo, salvarConfig } from './estado.js';
import { el, janela, aviso } from './ui.js';
import { t } from './i18n.js';

export function avisoHaiku() {
  const antes = cfg().aviso_haiku;
  if (!antes || !cfg().configurado) return Promise.resolve(false);
  if (cfg().modelo_chat !== 'claude-haiku-5-5' || cfg().modelo_code !== 'claude-haiku-5-5') {
    // depois de atualizar, a pessoa já escolheu outro modelo: o aviso não tem mais o que oferecer
    salvarConfig({ aviso_haiku: null }).catch(() => {});
    return Promise.resolve(false);
  }
  const nomes = [...new Set([antes.modelo_chat, antes.modelo_code].filter((m) => m && m !== 'claude-haiku-5-5'))]
    .map((m) => modeloInfo(m).nome || m);
  if (!nomes.length) { salvarConfig({ aviso_haiku: null }).catch(() => {}); return Promise.resolve(false); }
  return new Promise((pronto) => {
    let respondeu = false;
    const responder = async (voltar) => {
      respondeu = true;
      const mudar = { aviso_haiku: null };
      if (voltar) Object.assign(mudar, { modelo_chat: antes.modelo_chat || 'claude-haiku-5-5', modelo_code: antes.modelo_code || 'claude-haiku-5-5' });
      try {
        await salvarConfig(mudar);
        aviso(voltar ? t('Pronto: as conversas novas voltam a usar o modelo de antes.') : t('Pronto: as conversas novas usam o Haiku 5.5.'));
      } catch (e) { aviso(e.message, 'erro'); }
      pronto(true);
    };
    janela({
      titulo: t('O padrão agora é o Haiku 5.5'),
      corpo: el('div', { style: 'display:grid;gap:12px' },
        el('p', { style: 'margin:0', texto: t('Para gastar menos, as conversas novas começam no Haiku 5.5, o modelo mais barato. Antes você usava: {modelos}.', { modelos: nomes.join(', ') }) }),
        el('p', { class: 'ajuda', style: 'margin:0', texto: t('O conselheiro de modelo continua sugerindo um modelo mais forte quando a tarefa pede. Conversas que já existem continuam no modelo delas, e dá para trocar quando quiser em Configurações > Modelos.') })),
      botoes: [
        { texto: t('Voltar para o de antes'), acao: () => responder(true) },
        { texto: t('Manter o Haiku'), classe: 'primario', acao: () => responder(false) },
      ],
      aoFechar: () => { if (!respondeu) { salvarConfig({ aviso_haiku: null }).catch(() => {}); pronto(true); } },
    });
  });
}
