// Peças que as cenas dividem: fundo, logo, texto que sobe palavra por palavra, rótulo, nota de rodapé e entrada.
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COR, MOLA, MONO, SANS, SERIFA} from '../tema';

export const Fundo: React.FC<{tipo: 'papel' | 'tinta'; children?: React.ReactNode}> = ({tipo, children}) => {
  const f = useCurrentFrame();
  const claro = tipo === 'papel';
  // um grão de papel bem leve e uma luz que anda devagar: o fundo nunca fica parado de todo
  const x = 30 + Math.sin(f / 90) * 12;
  const y = 25 + Math.cos(f / 120) * 10;
  return (
    <AbsoluteFill
      style={{
        background: claro
          ? `radial-gradient(circle at ${x}% ${y}%, #fbf8f1 0%, ${COR.papel} 45%, #efe8da 100%)`
          : `radial-gradient(circle at ${x}% ${y}%, #2a2722 0%, ${COR.tinta} 50%, #171613 100%)`,
        color: claro ? COR.texto : COR.tintaTexto,
        fontFamily: SANS,
      }}
    >
      <AbsoluteFill
        style={{
          opacity: claro ? 0.35 : 0.22,
          backgroundImage:
            'url("data:image/svg+xml;utf8,<svg xmlns=%27http://www.w3.org/2000/svg%27 width=%27160%27 height=%27160%27><filter id=%27g%27><feTurbulence type=%27fractalNoise%27 baseFrequency=%270.9%27 numOctaves=%272%27 stitchTiles=%27stitch%27/><feColorMatrix values=%270 0 0 0 0.5  0 0 0 0 0.45  0 0 0 0 0.4  0 0 0 0.35 0%27/></filter><rect width=%27100%25%27 height=%27100%25%27 filter=%27url(%23g)%27/></svg>")',
        }}
      />
      {children}
    </AbsoluteFill>
  );
};

// o logo do app (app/img/icone.svg): o "C" e as três linhas; "desenha" o traço a partir de `inicio`
export const Logo: React.FC<{tamanho: number; inicio?: number; claro?: boolean}> = ({tamanho, inicio = 0, claro = false}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const caixa = spring({frame: f - inicio, fps, config: MOLA, durationInFrames: 14});
  const traco = interpolate(f - inicio, [4, 26], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const linhas = [0, 1, 2].map((i) => interpolate(f - inicio, [18 + i * 4, 30 + i * 4], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)}));
  return (
    <svg width={tamanho} height={tamanho} viewBox="0 0 64 64" style={{transform: `scale(${0.6 + caixa * 0.4})`, opacity: caixa}}>
      <rect width="64" height="64" rx="14" fill={claro ? COR.papel : '#1f1d1a'} stroke={claro ? 'none' : '#3a362f'} strokeWidth={claro ? 0 : 1} />
      <path
        d="M41 17.5c-3.2-2.4-6.6-3.5-10.3-3.5C21.2 14 14 21.6 14 32s7.2 18 16.7 18c3.9 0 7.3-1.2 10.5-3.7"
        fill="none"
        stroke={claro ? COR.texto : '#efe6d6'}
        strokeWidth="5"
        strokeLinecap="round"
        pathLength={1}
        strokeDasharray="1"
        strokeDashoffset={traco}
      />
      <g stroke={claro ? COR.acao : '#5fb3b0'} strokeWidth="2.4" strokeLinecap="round">
        {[25, 32, 39].map((y, i) => (
          <path key={y} d={`M33 ${y}h${17 * linhas[i]}`} opacity={linhas[i] > 0 ? 1 : 0} />
        ))}
      </g>
    </svg>
  );
};

// texto que sobe palavra por palavra; `inicio` em quadros relativos à cena
export const Sobe: React.FC<{
  texto: string;
  inicio: number;
  tamanho: number;
  fonte?: string;
  peso?: number;
  cor?: string;
  passo?: number;
  estilo?: React.CSSProperties;
  italico?: boolean;
}> = ({texto, inicio, tamanho, fonte = SERIFA, peso = 500, cor, passo = 3, estilo, italico}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const palavras = texto.split(' ');
  return (
    <div style={{fontFamily: fonte, fontSize: tamanho, fontWeight: peso, color: cor, lineHeight: 1.08, letterSpacing: fonte === SERIFA ? '-0.02em' : '-0.01em', fontStyle: italico ? 'italic' : 'normal', ...estilo}}>
      {palavras.map((p, i) => {
        const s = spring({frame: f - inicio - i * passo, fps, config: MOLA, durationInFrames: 16});
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              overflow: 'hidden',
              verticalAlign: 'bottom',
              paddingBottom: '0.08em',
              marginBottom: '-0.08em',
              marginRight: i < palavras.length - 1 ? '0.24em' : 0,
            }}
          >
            <span style={{display: 'inline-block', transform: `translateY(${(1 - s) * 105}%)`, opacity: s}}>{p}</span>
          </span>
        );
      })}
    </div>
  );
};

export const Rotulo: React.FC<{texto: string; inicio: number; cor?: string; tamanho?: number}> = ({texto, inicio, cor, tamanho = 24}) => {
  const f = useCurrentFrame();
  const o = interpolate(f - inicio, [0, 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{fontFamily: MONO, fontSize: tamanho, letterSpacing: '0.08em', textTransform: 'uppercase', color: cor, opacity: o, transform: `translateX(${(1 - o) * -14}px)`}}>
      {texto}
    </div>
  );
};

// nota pequena no pé da tela (de onde vem o número, o que é estimativa)
export const Nota: React.FC<{texto: string; inicio: number; claro: boolean}> = ({texto, inicio, claro}) => {
  const f = useCurrentFrame();
  const o = interpolate(f - inicio, [0, 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 140, right: 140, bottom: 54, fontFamily: MONO, fontSize: 21, color: claro ? COR.texto3 : COR.tintaTexto3, opacity: o * 0.95}}>
      {texto}
    </div>
  );
};

// entrada com mola: sobe e aparece
export const useEntra = (inicio: number, duracao = 16) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - inicio, fps, config: MOLA, durationInFrames: duracao});
};

export const Entra: React.FC<{inicio: number; children: React.ReactNode; distancia?: number; estilo?: React.CSSProperties; escala?: boolean}> = ({
  inicio,
  children,
  distancia = 40,
  estilo,
  escala,
}) => {
  const s = useEntra(inicio);
  return (
    <div style={{opacity: s, transform: `translateY(${(1 - s) * distancia}px) scale(${escala ? 0.94 + s * 0.06 : 1})`, ...estilo}}>{children}</div>
  );
};
