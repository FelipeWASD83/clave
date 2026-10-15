// Uma janela do Clave com os prints de verdade do app (ferramentas/telas.py), com câmera (zoom e pan), cursor que
// anda e clica, e destaque no que a fala cita. As coordenadas são as do print: pontos de uma tela de 1440 × 810.
import {Easing, Img, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {useLinha, type Ret} from '../linha';
import {COR, MOLA, SANS} from '../tema';
import {Logo} from './Base';

const LW = 1440;
const LH = 810;
const BARRA = 34; // a barra de título da janela

export type Quadro = {tela: string; de: number}; // a partir de `de`, mostra este print (com uma fusão curta)
export type Foco = {de: number; r?: Ret | null; zoom?: number; dur?: number}; // r vazio: a tela inteira
export type Ponto = {em: number; x: number; y: number; clique?: boolean; duplo?: boolean}; // o cursor chega em (x, y) no quadro `em`
export type Marca = {de: number; ate?: number; r: Ret; escurece?: boolean; folga?: number};

type Estado = {cx: number; cy: number; z: number};
const INTEIRA: Estado = {cx: LW / 2, cy: LH / 2, z: 1};
const suave = Easing.inOut(Easing.cubic);

const prender = (e: Estado): Estado => {
  const z = Math.max(1, e.z);
  const mw = LW / (2 * z);
  const mh = LH / (2 * z);
  return {z, cx: Math.min(LW - mw, Math.max(mw, e.cx)), cy: Math.min(LH - mh, Math.max(mh, e.cy))};
};

const alvoDe = (f: Foco): Estado => {
  if (!f.r) return INTEIRA;
  const [x, y, w, h] = f.r;
  const z = f.zoom ?? Math.min(2.2, Math.max(1, Math.min(LW / (w + 220), LH / (h + 160))));
  return prender({cx: x + w / 2, cy: y + h / 2, z});
};

const misturar = (a: Estado, b: Estado, t: number): Estado =>
  prender({cx: a.cx + (b.cx - a.cx) * t, cy: a.cy + (b.cy - a.cy) * t, z: Math.exp(Math.log(a.z) + (Math.log(b.z) - Math.log(a.z)) * t)});

// a câmera em `de` de cada foco: para começar cada movimento de onde o anterior parou de verdade
const cameraEm = (focos: Foco[], f: number): Estado => {
  const ordem = [...focos].sort((a, b) => a.de - b.de);
  let partida = INTEIRA;
  let atual = INTEIRA;
  for (let i = 0; i < ordem.length; i++) {
    const k = ordem[i];
    if (f < k.de) break;
    const dur = k.dur ?? 20;
    const alvo = alvoDe(k);
    const fimDeste = Math.min(f, ordem[i + 1]?.de ?? Infinity);
    atual = misturar(partida, alvo, suave(Math.min(1, (fimDeste - k.de) / dur)));
    partida = atual;
  }
  return atual;
};

const Seta: React.FC<{escala: number}> = ({escala}) => (
  <svg width={30} height={36} viewBox="0 0 30 36" style={{transform: `scale(${escala})`, transformOrigin: '3px 3px', filter: 'drop-shadow(0 3px 5px rgba(0,0,0,.35))'}}>
    <path d="M3 3 L3 29 L10 22.5 L14.5 33 L19 31 L14.6 20.8 L24 20.8 Z" fill="#fff" stroke="#1f1d1a" strokeWidth={2} strokeLinejoin="round" />
  </svg>
);

export const Tela: React.FC<{
  quadros: Quadro[];
  focos?: Foco[];
  cursor?: Ponto[];
  marcas?: Marca[];
  x?: number;
  y?: number;
  largura?: number;
  entra?: number;
}> = ({quadros, focos = [], cursor = [], marcas = [], x = 220, y = 168, largura = 1480, entra = 0}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {tela} = useLinha();
  const W = largura;
  const H = (largura * LH) / LW;
  const s0 = W / LW;
  const cam = cameraEm(focos, f);
  const mapa = (px: number, py: number) => ({x: W / 2 + cam.z * s0 * (px - cam.cx), y: H / 2 + cam.z * s0 * (py - cam.cy)});
  const chegada = spring({frame: f - entra, fps, config: MOLA, durationInFrames: 18});

  // cursor: anda até cada ponto nos 16 quadros antes dele
  let cur: {x: number; y: number} | null = null;
  let aperto = 1;
  const ripples: {x: number; y: number; t: number}[] = [];
  if (cursor.length) {
    const p0 = cursor[0];
    if (f >= p0.em - 14) {
      let px = p0.x;
      let py = p0.y;
      for (let i = 1; i < cursor.length; i++) {
        const a = cursor[i - 1];
        const b = cursor[i];
        const mov = Math.min(18, Math.max(6, b.em - a.em - 2));
        const t = suave(Math.min(1, Math.max(0, (f - (b.em - mov)) / mov)));
        if (f >= b.em - mov) {
          px = a.x + (b.x - a.x) * t;
          py = a.y + (b.y - a.y) * t;
        }
      }
      cur = mapa(px, py);
      for (const p of cursor) {
        const cliques = p.clique ? (p.duplo ? [p.em, p.em + 6] : [p.em]) : [];
        for (const c of cliques) {
          if (f >= c && f < c + 16) {
            const m = mapa(p.x, p.y);
            ripples.push({x: m.x, y: m.y, t: (f - c) / 16});
          }
          if (f >= c && f < c + 8) aperto = Math.min(aperto, interpolate(f - c, [0, 3, 8], [1, 0.8, 1]));
        }
      }
    }
  }
  const opCursor = cursor.length ? interpolate(f, [cursor[0].em - 14, cursor[0].em - 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 0;

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: W,
        height: H + BARRA,
        borderRadius: 14,
        overflow: 'hidden',
        background: '#1a1815',
        boxShadow: '0 40px 90px rgba(20,15,8,.38), 0 0 0 1.5px rgba(0,0,0,.25)',
        opacity: chegada,
        transform: `translateY(${(1 - chegada) * 50}px) scale(${0.97 + chegada * 0.03})`,
      }}
    >
      {/* barra de título genérica do Windows */}
      <div style={{height: BARRA, display: 'flex', alignItems: 'center', gap: 10, padding: '0 14px', color: '#d9d1c2', fontFamily: SANS, fontSize: 15}}>
        <Logo tamanho={20} inicio={-100} />
        <span>Clave</span>
        <svg style={{marginLeft: 'auto'}} width={150} height={14} viewBox="0 0 150 14" fill="none" stroke="#a39a8a" strokeWidth={1.4}>
          <path d="M8 7h12" />
          <rect x={66} y={1.5} width={11} height={11} rx={1.5} />
          <path d="M126 1.5l11 11M137 1.5l-11 11" />
        </svg>
      </div>
      <div style={{position: 'relative', width: W, height: H, overflow: 'hidden', background: COR.papel}}>
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: W,
            height: H,
            transformOrigin: '0 0',
            transform: `translate(${W / 2 - cam.z * s0 * cam.cx}px, ${H / 2 - cam.z * s0 * cam.cy}px) scale(${cam.z})`,
          }}
        >
          {quadros.map((q, i) => (
            <Img
              key={q.tela + i}
              src={tela(q.tela)}
              style={{
                position: 'absolute',
                inset: 0,
                width: W,
                height: H,
                opacity: i === 0 ? 1 : interpolate(f, [q.de, q.de + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
              }}
            />
          ))}
        </div>
        {marcas.map((m, i) => {
          if (f < m.de || (m.ate !== undefined && f > m.ate + 10)) return null;
          const folga = m.folga ?? 6;
          const a = mapa(m.r[0] - folga, m.r[1] - folga);
          const b = mapa(m.r[0] + m.r[2] + folga, m.r[1] + m.r[3] + folga);
          const entrada = interpolate(f - m.de, [0, 10], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
          const saida = m.ate === undefined ? 1 : interpolate(f - m.ate, [0, 10], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          const o = entrada * saida;
          const cresce = 1 + (1 - entrada) * 0.08;
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: a.x,
                top: a.y,
                width: b.x - a.x,
                height: b.y - a.y,
                borderRadius: 12,
                border: `3px solid ${COR.acao}`,
                boxShadow: `0 0 0 6px rgba(29,95,102,${0.18 * o}), 0 0 26px rgba(29,95,102,${0.35 * o})${m.escurece ? `, 0 0 0 4000px rgba(24,20,15,${0.32 * o})` : ''}`,
                opacity: o,
                transform: `scale(${cresce})`,
              }}
            />
          );
        })}
        {ripples.map((r, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: r.x - 30 * r.t - 6,
              top: r.y - 30 * r.t - 6,
              width: 12 + 60 * r.t,
              height: 12 + 60 * r.t,
              borderRadius: '50%',
              border: `3px solid ${COR.acao}`,
              opacity: 0.7 * (1 - r.t),
            }}
          />
        ))}
        {cur && (
          <div style={{position: 'absolute', left: cur.x - 3, top: cur.y - 3, opacity: opCursor}}>
            <Seta escala={aperto} />
          </div>
        )}
      </div>
    </div>
  );
};

// atalhos para montar focos e cursores a partir de um retângulo
export const centro = (r: Ret): [number, number] => [r[0] + r[2] / 2, r[1] + r[3] / 2];
export const juntar = (...rs: Ret[]): Ret => {
  const x0 = Math.min(...rs.map((r) => r[0]));
  const y0 = Math.min(...rs.map((r) => r[1]));
  const x1 = Math.max(...rs.map((r) => r[0] + r[2]));
  const y1 = Math.max(...rs.map((r) => r[1] + r[3]));
  return [x0, y0, x1 - x0, y1 - y0];
};
export const ponto = (r: Ret, em: number, clique = true, dx = 0, dy = 0): Ponto => {
  const [cx, cy] = centro(r);
  return {em, x: cx + dx, y: cy + dy, clique};
};

