// Cena 8: "Nunca usou inteligência artificial? Tem lições em português, do zero."
// O "quem é JASON?" é o exemplo do próprio app: o Claude entende o termo escrito errado e indica a lição.
import {useLinha} from '../../linha';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Entra, Fundo, Sobe} from '../../componentes/Base';
import {Icone} from '../../componentes/Icones';
import {COR, MOLA, MONO, SANS} from '../../tema';

const C = 'aprender';

const LICOES = [
  {n: 'Primeiros passos', titulo: 'O que é o Claude', dura: '4 min'},
  {n: 'Primeiros passos', titulo: 'Como pedir bem', dura: '6 min'},
  {n: 'Automação', titulo: 'Como o modo Code funciona', dura: '7 min'},
  {n: 'Consulta', titulo: 'Glossário: mais de 70 termos', dura: 'A a Z'},
];

export const Aprender: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {quando, T} = useLinha();
  const tNunca = quando(C, 'nunca');
  const tArtificial = quando(C, 'artificial');
  const tTem = quando(C, 'tem');
  const tLicoes = quando(C, 'licoes');
  const tZero = quando(C, 'zero');
  const risco = interpolate(f - tArtificial - 10, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <Fundo tipo="papel">
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 140px', gap: 90}}>
        <div style={{flex: '0 0 760px'}}>
          <Entra inicio={tNunca} distancia={30}>
            <div style={{display: 'flex', justifyContent: 'flex-end'}}>
              <div style={{background: COR.papel2, borderRadius: 22, padding: '20px 30px', fontFamily: SANS, fontSize: 38, color: COR.texto}}>{T('quem é JASON?')}</div>
            </div>
          </Entra>
          <Entra inicio={tArtificial} distancia={30} estilo={{marginTop: 30}}>
            <div style={{fontFamily: SANS, fontSize: 34, color: COR.texto2, lineHeight: 1.45}}>
              {T('Você quis dizer')}{' '}
              <span style={{position: 'relative', color: COR.texto3}}>
                JASON
                <span style={{position: 'absolute', left: -4, right: -4, top: '52%', height: 4, background: COR.erro, transform: `scaleX(${risco})`, transformOrigin: 'left'}} />
              </span>{' '}
              <b style={{color: COR.texto}}>JSON</b>{T(': um jeito de guardar informação em texto que os programas entendem.')}
              <div style={{marginTop: 22, display: 'flex', alignItems: 'center', gap: 12, color: COR.acao, fontWeight: 500}}>
                <Icone nome="livro" tamanho={32} cor={COR.acao} /> {T('Glossário: JSON')}
              </div>
            </div>
          </Entra>
        </div>
        <div style={{flex: 1}}>
          <Sobe texto={T('Lições em português, do zero.')} inicio={tTem} tamanho={78} cor={COR.texto} />
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 22, marginTop: 44}}>
            {LICOES.map((l, i) => {
              const s = spring({frame: f - tLicoes - i * 4, fps, config: MOLA, durationInFrames: 16});
              return (
                <div
                  key={l.titulo}
                  style={{
                    opacity: s,
                    transform: `translateY(${(1 - s) * 40}px) rotate(${(1 - s) * (i % 2 ? 3 : -3)}deg)`,
                    background: '#fbf8f1',
                    border: `2px solid ${COR.linha}`,
                    borderRadius: 18,
                    padding: '26px 28px',
                    minHeight: 170,
                  }}
                >
                  <div style={{fontFamily: MONO, fontSize: 22, color: COR.acao}}>{T(l.n)}</div>
                  <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 32, color: COR.texto, marginTop: 10, lineHeight: 1.2}}>{T(l.titulo)}</div>
                  <div style={{fontFamily: MONO, fontSize: 20, color: COR.texto3, marginTop: 12}}>{T(l.dura)}</div>
                </div>
              );
            })}
          </div>
          <Entra inicio={tZero} distancia={20} estilo={{marginTop: 28}}>
            <div style={{fontFamily: SANS, fontSize: 28, color: COR.texto3}}>
              {T('Com um ajudante que tira dúvida de cada lição por uma fração de centavo.')}
            </div>
          </Entra>
        </div>
      </AbsoluteFill>
    </Fundo>
  );
};
