// Cena 4: "Sem janela de cinco horas. Sem limite semanal."
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {Entra, Fundo, Nota, Rotulo} from '../componentes/Base';
import {Icone} from '../componentes/Icones';
import {COR, SANS, SERIFA, quando} from '../tema';

const C = 'limite';

const Bloco: React.FC<{inicio: number; risco: number; icone: string; grande: string; legenda: string}> = ({inicio, risco, icone, grande, legenda}) => {
  const f = useCurrentFrame();
  const r = interpolate(f - risco, [0, 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
  return (
    <Entra inicio={inicio} distancia={50} escala>
      <div
        style={{
          position: 'relative',
          width: 640,
          height: 420,
          borderRadius: 28,
          background: COR.papel2,
          border: `2px solid ${COR.linha}`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
        }}
      >
        <div style={{opacity: 1 - r * 0.55, display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
          <Icone nome={icone} tamanho={70} cor={COR.texto3} />
          <div style={{fontFamily: SERIFA, fontSize: 170, fontWeight: 500, letterSpacing: '-0.04em', lineHeight: 1.05, color: COR.texto}}>{grande}</div>
          <div style={{fontFamily: SANS, fontSize: 32, color: COR.texto3}}>{legenda}</div>
        </div>
        <svg style={{position: 'absolute', inset: 0}} width="640" height="420" viewBox="0 0 640 420">
          {r > 0 && <line x1="70" y1="350" x2={70 + 500 * r} y2={350 - 280 * r} stroke={COR.erro} strokeWidth="16" strokeLinecap="round" />}
        </svg>
      </div>
    </Entra>
  );
};

export const Limite: React.FC = () => {
  const tSem = quando(C, 'Sem');
  const tHoras = quando(C, 'horas');
  const tSem2 = quando(C, 'Sem', 1);
  const tSemanal = quando(C, 'semanal');
  return (
    <Fundo tipo="papel">
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
        <Rotulo texto="Na API" inicio={tSem - 6} cor={COR.acao} tamanho={30} />
        <div style={{display: 'flex', gap: 80, marginTop: 40}}>
          <Bloco inicio={tSem} risco={tHoras} icone="relogio" grande="5 h" legenda="janela de uso" />
          <Bloco inicio={tSem2} risco={tSemanal} icone="calendario" grande="7 dias" legenda="limite da semana" />
        </div>
      </AbsoluteFill>
      <Nota texto="Na API o limite é de pedidos por minuto, folgado para uma pessoa." inicio={tSem2} claro />
    </Fundo>
  );
};
