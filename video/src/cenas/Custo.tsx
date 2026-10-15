// Cena 3: "Na API, você paga só o que usa. Mil mensagens curtas no Haiku saem por uns quarenta centavos de dólar.
// E o Clave mostra o custo de cada resposta, com um teto mensal que você mesmo define."
// O elemento da cena é a fita de recibo: cada coisa que você usa vira uma linha com o preço.
// Números: página oficial de preços da Anthropic em 14/10/2026, mensagem curta (8 mil tokens de entrada, quase
// tudo do cache, e 400 de saída) sem raciocínio.
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Fundo, Nota, Rotulo, Sobe} from '../componentes/Base';
import {COR, MOLA, MONO, SANS, quando} from '../tema';

const C = 'custo';

type LinhaRecibo = {inicio: number; texto: string; sub: string; valor: string; destaque?: number};

const Recibo: React.FC<{linhas: LinhaRecibo[]; total: {inicio: number; valor: string}}> = ({linhas, total}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const altura = (inicio: number, h: number) => spring({frame: f - inicio, fps, config: MOLA, durationInFrames: 12}) * h;
  const zigue = Array.from({length: 29}, (_, i) => `${(i / 28) * 100}% ${i % 2 ? 100 : 'calc(100% - 14px)'}`).join(', ');
  return (
    <div style={{position: 'relative', width: 760, flex: 'none'}}>
      {/* a fenda da impressora */}
      <div style={{height: 26, borderRadius: 13, background: '#0f0e0c', boxShadow: 'inset 0 4px 10px rgba(0,0,0,.7)', margin: '0 -24px'}} />
      <div
        style={{
          marginTop: -12,
          background: '#fbf8f1',
          color: COR.texto,
          padding: '34px 40px 46px',
          fontFamily: MONO,
          clipPath: `polygon(0 0, 100% 0, ${zigue}, 0 calc(100% - 14px))`,
          boxShadow: '0 30px 60px rgba(0,0,0,.4)',
        }}
      >
        <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 22, color: COR.texto3, letterSpacing: '0.08em'}}>
          <span>CLAVE · USO</span>
          <span>OUT/2026</span>
        </div>
        <div style={{borderBottom: `2px dashed ${COR.linha}`, margin: '18px 0 6px'}} />
        {linhas.map((l, i) => (
          <div key={i} style={{height: altura(l.inicio, 96), overflow: 'hidden'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', paddingTop: 18}}>
              <div>
                <div style={{fontSize: 27, color: COR.texto}}>{l.texto}</div>
                <div style={{fontSize: 21, color: COR.texto3, marginTop: 4}}>{l.sub}</div>
              </div>
              <div
                style={{
                  fontSize: 30,
                  fontWeight: 500,
                  color: COR.texto,
                  background: l.destaque !== undefined && f >= l.destaque ? COR.acaoSuave : 'transparent',
                  borderRadius: 8,
                  padding: '2px 10px',
                  opacity: l.destaque !== undefined ? interpolate(f - l.destaque, [0, 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 1,
                }}
              >
                {l.valor}
              </div>
            </div>
          </div>
        ))}
        <div style={{height: altura(total.inicio, 84), overflow: 'hidden'}}>
          <div style={{borderBottom: `2px dashed ${COR.linha}`, margin: '20px 0 16px'}} />
          <div style={{display: 'flex', justifyContent: 'space-between', fontSize: 34, fontWeight: 500}}>
            <span>TOTAL</span>
            <span>{total.valor}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export const Custo: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tNa = quando(C, 'Na');
  const tVoce = quando(C, 'você');
  const tMil = quando(C, 'Mil');
  const tQuarenta = quando(C, 'quarenta');
  const tCusto = quando(C, 'custo');
  const tResposta = quando(C, 'resposta');
  const tTeto = quando(C, 'teto');
  const tDefine = quando(C, 'define');
  const barra = spring({frame: f - tTeto - 6, fps, config: MOLA, durationInFrames: 24});
  const caixa = spring({frame: f - tTeto, fps, config: MOLA, durationInFrames: 16});
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 140px', gap: 110}}>
        <div style={{flex: 1}}>
          <Rotulo texto="Pela API" inicio={tNa} cor={COR.tintaAcao} tamanho={28} />
          <div style={{marginTop: 22}}>
            <Sobe texto="Você paga só o que usa." inicio={tVoce} tamanho={104} cor={COR.tintaTexto} />
          </div>
          <div
            style={{
              marginTop: 70,
              opacity: caixa,
              transform: `translateY(${(1 - caixa) * 30}px)`,
              background: COR.tinta2,
              border: `1.5px solid ${COR.tintaLinha}`,
              borderRadius: 18,
              padding: '30px 36px',
              width: 760,
            }}
          >
            <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: SANS, fontSize: 30, color: COR.tintaTexto2}}>
              <span>Teto do mês</span>
              <span style={{fontFamily: MONO, color: COR.tintaTexto}}>
                US$ 0,41 <span style={{color: COR.tintaTexto3}}>de US$ 20,00</span>
              </span>
            </div>
            <div style={{marginTop: 20, height: 14, borderRadius: 7, background: COR.tinta3, overflow: 'hidden'}}>
              <div style={{width: `${barra * 2.05}%`, minWidth: barra > 0.02 ? 14 : 0, height: '100%', borderRadius: 7, background: COR.tintaAcao}} />
            </div>
            <div style={{marginTop: 16, fontFamily: SANS, fontSize: 24, color: COR.tintaTexto3, opacity: interpolate(f - tDefine, [0, 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
              Chegou no teto, o Clave para. Sem susto na fatura.
            </div>
          </div>
        </div>
        {/* a fenda fica parada e o papel cresce para baixo, como numa impressora de verdade */}
        <div style={{height: 720, display: 'flex', alignItems: 'flex-start', paddingTop: 40}}>
        <Recibo
          linhas={[
            {inicio: tMil, texto: '1.000 mensagens curtas', sub: 'Haiku 5.5', valor: '≈ US$ 0,40', destaque: tQuarenta},
            {inicio: tCusto, texto: '1 resposta', sub: 'Haiku 5.5', valor: 'US$ 0,0004'},
            {inicio: tResposta, texto: '1 resposta', sub: 'Sonnet 5.5', valor: 'US$ 0,0072'},
          ]}
          total={{inicio: tTeto, valor: 'US$ 0,41'}}
        />
        </div>
      </AbsoluteFill>
      <Nota texto="Estimativas para mensagem curta, sem raciocínio longo, com os preços da Anthropic de 14/10/2026." inicio={tMil} claro={false} />
    </Fundo>
  );
};
