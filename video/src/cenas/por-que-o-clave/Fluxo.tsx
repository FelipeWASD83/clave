// Cena 6: "Escolha o modelo certo para cada tarefa. Ou junte todos num fluxo: o Opus planeja, o Sonnet faz,
// o Haiku confere. E você vê o preço antes de aprovar."
// A estimativa do cartão é a que o próprio Clave calculou num fluxo de verdade (teste de 14/10/2026).
import {useLinha} from '../../linha';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Entra, Fundo, Rotulo, Sobe} from '../../componentes/Base';
import {Icone} from '../../componentes/Icones';
import {COR, MOLA, MONO, SANS, SERIFA} from '../../tema';

const C = 'fluxo';

const MODELOS = [
  {nome: 'Haiku 5.5', papel: 'rápido e barato', palavra: 'modelo', custo: 1, cabeca: 1},
  {nome: 'Sonnet 5.5', papel: 'o dia a dia', palavra: 'certo', custo: 2, cabeca: 2},
  {nome: 'Opus 5.5', papel: 'o mais capaz', palavra: 'tarefa', custo: 3, cabeca: 3},
];

const Pontos: React.FC<{n: number}> = ({n}) => (
  <div style={{display: 'flex', gap: 10}}>
    {[1, 2, 3].map((i) => (
      <div key={i} style={{width: 22, height: 22, borderRadius: 11, background: i <= n ? COR.acao : COR.papel3}} />
    ))}
  </div>
);

const ETAPAS = [
  {n: 1, nome: 'Planejar', modelo: 'Opus 5.5', agente: 'planejador', palavra: 'opus'},
  {n: 2, nome: 'Fazer', modelo: 'Sonnet 5.5', agente: 'executor', palavra: 'sonnet'},
  {n: 3, nome: 'Conferir', modelo: 'Haiku 5.5', agente: 'revisor', palavra: 'raicu'},
];

export const Fluxo: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {quando, T} = useLinha();
  const tEscolha = quando(C, 'escolha');
  const tOu = quando(C, 'ou');
  const tFluxo = quando(C, 'fluxo');
  const tPreco = quando(C, 'preco');
  const tAprovar = quando(C, 'aprovar');
  const troca = spring({frame: f - tOu, fps, config: MOLA, durationInFrames: 18});
  const cartao = spring({frame: f - (tFluxo - 6), fps, config: MOLA, durationInFrames: 18});
  const aperta = interpolate(f - tAprovar, [0, 4, 10], [1, 0.94, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const aprovado = f >= tAprovar + 4;
  return (
    <Fundo tipo="papel">
      <AbsoluteFill style={{padding: '110px 140px'}}>
        {/* título 1 e título 2 trocam de lugar */}
        <div style={{position: 'relative', height: 120}}>
          <div style={{position: 'absolute', opacity: 1 - troca, transform: `translateY(${-troca * 30}px)`}}>
            <Sobe texto={T('O modelo certo para cada tarefa.')} inicio={tEscolha} tamanho={86} cor={COR.texto} />
          </div>
          <div style={{position: 'absolute', opacity: troca}}>
            <Sobe texto={T('Ou todos juntos, num fluxo.')} inicio={tOu} tamanho={86} cor={COR.texto} />
          </div>
        </div>

        {/* os três modelos lado a lado */}
        <div style={{display: 'flex', gap: 40, marginTop: 120, opacity: 1 - troca, transform: `scale(${1 - troca * 0.06})`}}>
          {MODELOS.map((m) => (
            <Entra key={m.nome} inicio={quando(C, m.palavra)} distancia={40} estilo={{flex: 1}}>
              <div style={{background: COR.papel2, border: `2px solid ${COR.linha}`, borderRadius: 22, padding: '48px 48px 44px'}}>
                <Icone nome="faisca" tamanho={48} cor={COR.acao} />
                <div style={{fontFamily: SERIFA, fontSize: 70, fontWeight: 500, marginTop: 18, color: COR.texto}}>{m.nome}</div>
                <div style={{fontFamily: SANS, fontSize: 32, color: COR.texto3, marginTop: 6}}>{T(m.papel)}</div>
                <div
                  style={{
                    borderTop: `1.5px solid ${COR.linha}`,
                    marginTop: 34,
                    paddingTop: 26,
                    display: 'grid',
                    gridTemplateColumns: 'auto 1fr',
                    rowGap: 16,
                    columnGap: 26,
                    alignItems: 'center',
                    fontFamily: MONO,
                    fontSize: 24,
                    color: COR.texto3,
                  }}
                >
                  <span>{T('inteligência')}</span>
                  <Pontos n={m.cabeca} />
                  <span>{T('custo')}</span>
                  <Pontos n={m.custo} />
                </div>
              </div>
            </Entra>
          ))}
        </div>

        {/* o cartão do fluxo, igual ao do app: proposta com etapas, estimativa e o OK */}
        <div
          style={{
            position: 'absolute',
            left: 140,
            right: 140,
            top: 280,
            opacity: cartao,
            transform: `translateY(${(1 - cartao) * 50}px)`,
            background: '#fbf8f1',
            border: `2px solid ${COR.linha}`,
            borderRadius: 24,
            boxShadow: '0 30px 70px rgba(40,30,15,.16)',
            overflow: 'hidden',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 22, padding: '28px 40px', borderBottom: `2px solid ${COR.linha}`}}>
            <Icone nome="fluxo" tamanho={46} cor={COR.acao} />
            <div>
              <Rotulo texto={T('Fluxo proposto')} inicio={tFluxo - 6} cor={COR.texto3} tamanho={20} />
              <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 36, color: COR.texto, marginTop: 2}}>{T('Planejar, fazer e conferir')}</div>
            </div>
          </div>
          {ETAPAS.map((e) => {
            const t = quando(C, e.palavra);
            const s = spring({frame: f - t, fps, config: MOLA, durationInFrames: 14});
            return (
              <div key={e.n} style={{display: 'flex', alignItems: 'center', gap: 26, padding: '22px 40px', borderBottom: `1.5px solid ${COR.papel3}`, opacity: 0.25 + s * 0.75}}>
                <div style={{width: 52, height: 52, borderRadius: 26, background: s > 0.5 ? COR.acao : COR.papel3, color: COR.papel, display: 'grid', placeItems: 'center', fontFamily: MONO, fontSize: 26}}>{e.n}</div>
                <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 36, color: COR.texto, width: 260}}>{T(e.nome)}</div>
                <div
                  style={{
                    fontFamily: MONO,
                    fontSize: 28,
                    color: COR.acao,
                    background: COR.acaoSuave,
                    borderRadius: 10,
                    padding: '6px 16px',
                    transform: `translateX(${(1 - s) * 40}px)`,
                  }}
                >
                  {e.modelo}
                </div>
                <div style={{fontFamily: SANS, fontSize: 28, color: COR.texto3}}>{T('agente ' + e.agente)}</div>
              </div>
            );
          })}
          <div style={{display: 'flex', alignItems: 'center', gap: 30, padding: '28px 40px', background: COR.papel2}}>
            <div style={{fontFamily: SANS, fontSize: 30, color: COR.texto2, opacity: interpolate(f - tPreco, [0, 8], [0.25, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
              {T('Estimativa')} <span style={{fontFamily: MONO, color: COR.texto, background: f >= tPreco ? COR.acaoSuave : 'transparent', borderRadius: 8, padding: '2px 10px'}}>{T('US$ 0,19 a 1,23')}</span>
              <span style={{marginLeft: 26}}>{T('Teto')}</span> <span style={{fontFamily: MONO, color: COR.texto}}>{T('US$ 1,50')}</span>
            </div>
            <div style={{marginLeft: 'auto', fontFamily: SANS, fontSize: 30, color: COR.texto3, padding: '14px 26px'}}>{T('Recusar')}</div>
            <div
              style={{
                fontFamily: SANS,
                fontWeight: 600,
                fontSize: 30,
                color: COR.papel,
                background: aprovado ? COR.sucesso : COR.acao,
                borderRadius: 12,
                padding: '16px 30px',
                transform: `scale(${aperta})`,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                boxShadow: aprovado ? `0 0 0 8px ${COR.acaoSuave}` : 'none',
              }}
            >
              {aprovado && <Icone nome="certo" tamanho={30} cor={COR.papel} espessura={2.6} />}
              {aprovado ? T('Rodando') : T('Rodar o fluxo')}
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </Fundo>
  );
};
