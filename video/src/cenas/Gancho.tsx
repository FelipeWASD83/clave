// Cena 1: "Vinte dólares por mês de assinatura. E, mesmo assim: limite atingido. Volte em cinco horas."
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Entra, Fundo, Rotulo} from '../componentes/Base';
import {Icone} from '../componentes/Icones';
import {COR, MOLA, MONO, SANS, SERIFA, quando} from '../tema';

const C = 'gancho';

export const Gancho: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const tVinte = quando(C, 'Vinte');
  const tMes = quando(C, 'mês');
  const tAssinatura = quando(C, 'assinatura');
  const tMesmo = quando(C, 'mesmo');
  const tLimite = quando(C, 'limite');
  const tVolte = quando(C, 'Volte');

  const preco = spring({frame: f - tVinte, fps, config: {damping: 14, mass: 0.8, stiffness: 120}});
  const conta = Math.round(interpolate(f - tVinte, [0, 14], [0, 20], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const sobe = spring({frame: f - tMesmo, fps, config: MOLA, durationInFrames: 22});
  const segundos = Math.max(0, Math.floor((f - tVolte) / fps));
  const resta = 5 * 3600 - 1 - segundos;
  const relogio = `${Math.floor(resta / 3600)}:${String(Math.floor((resta % 3600) / 60)).padStart(2, '0')}:${String(resta % 60).padStart(2, '0')}`;
  const pisca = f >= tVolte ? 0.75 + 0.25 * Math.cos(((f - tVolte) / fps) * Math.PI * 2) : 1;

  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{alignItems: 'center'}}>
        <div
          style={{
            position: 'absolute',
            top: interpolate(sobe, [0, 1], [300, 120]),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            transform: `scale(${interpolate(sobe, [0, 1], [1, 0.62])})`,
            transformOrigin: 'top center',
          }}
        >
          <div style={{display: 'flex', alignItems: 'baseline', gap: 18, opacity: preco, transform: `translateY(${(1 - preco) * 60}px)`}}>
            <span style={{fontFamily: SERIFA, fontSize: 110, color: COR.tintaTexto2}}>US$</span>
            <span style={{fontFamily: SERIFA, fontSize: 300, fontWeight: 500, letterSpacing: '-0.04em', color: COR.tintaTexto, lineHeight: 1}}>{conta}</span>
            <span style={{fontFamily: SERIFA, fontSize: 96, color: COR.tintaTexto2, opacity: interpolate(f - tMes, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
              /mês
            </span>
          </div>
          <div style={{marginTop: 26}}>
            <Rotulo texto="de assinatura, use você muito ou pouco" inicio={tAssinatura} cor={COR.tintaTexto3} tamanho={30} />
          </div>
        </div>

        <Entra inicio={tLimite - 2} distancia={70} escala estilo={{position: 'absolute', top: 470}}>
          <div
            style={{
              width: 900,
              borderRadius: 22,
              background: COR.tinta2,
              border: `1.5px solid ${COR.tintaLinha}`,
              boxShadow: '0 30px 80px rgba(0,0,0,.45)',
              padding: '44px 54px',
              display: 'flex',
              gap: 36,
              alignItems: 'center',
            }}
          >
            <div style={{width: 120, height: 120, borderRadius: 60, background: 'rgba(224,128,111,.14)', display: 'grid', placeItems: 'center', flex: 'none'}}>
              <Icone nome="ampulheta" tamanho={64} cor={COR.erroClaro} />
            </div>
            <div style={{flex: 1}}>
              <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 52, color: COR.tintaTexto}}>Limite atingido</div>
              <div style={{fontFamily: SANS, fontSize: 32, color: COR.tintaTexto2, marginTop: 10, opacity: interpolate(f - tVolte, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
                Volte em
                <span style={{fontFamily: MONO, fontWeight: 500, fontSize: 46, color: COR.erroClaro, marginLeft: 18, opacity: pisca}}>{relogio}</span>
              </div>
            </div>
          </div>
        </Entra>
      </AbsoluteFill>
    </Fundo>
  );
};
