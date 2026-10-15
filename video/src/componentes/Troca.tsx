// A única transição do vídeo: a cena nova entra como uma folha vinda da direita, com uma linha verde-azulada na borda.
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {COR, TROCA} from '../tema';

export const Folha: React.FC<{children: React.ReactNode; comTroca: boolean}> = ({children, comTroca}) => {
  const f = useCurrentFrame();
  if (!comTroca) return <AbsoluteFill>{children}</AbsoluteFill>;
  const t = interpolate(f, [0, TROCA], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const borda = (1 - t) * 100;
  return (
    <AbsoluteFill style={{clipPath: t >= 1 ? undefined : `inset(0 0 0 ${borda}%)`}}>
      {children}
      {t < 1 && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            left: `calc(${borda}% - 3px)`,
            width: 6,
            background: COR.tintaAcao,
            boxShadow: `0 0 40px 8px rgba(115,192,187,.45)`,
          }}
        />
      )}
    </AbsoluteFill>
  );
};
