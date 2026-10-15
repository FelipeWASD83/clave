// Um vídeo inteiro: as cenas em sequência, a folha em cada troca, a narração de cada cena, os efeitos e a trilha.
// Serve a todos os vídeos e aos dois idiomas: o que muda vem de src/videos/<vídeo>.ts e da narração.
import {AbsoluteFill, Freeze, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import {Folha} from './componentes/Troca';
import {LinhaProvider, criarApi, type Alvos, type Linha} from './linha';
import {FPS, TROCA, montarCenas, type Lingua, type Narracao} from './tema';
import {VIDEOS} from './videos';

export type PropsVideo = {
  video: string;
  lingua: Lingua;
  trilha?: boolean;
  // preenchidos pelo calculateMetadata do Root (lidos de public/)
  narracao?: Narracao | null;
  alvos?: Alvos | null;
};

export const montarLinha = (p: PropsVideo): {linha: Linha; duracao: number} => {
  const def = VIDEOS[p.video];
  if (!def) throw new Error(`vídeo desconhecido: ${p.video}`);
  if (!p.narracao) throw new Error(`sem narração para ${p.video} (${p.lingua}): rode npm run narrar`);
  const {cenas, duracao} = montarCenas(p.narracao, def.extra);
  return {linha: {lingua: p.lingua, cenas, alvos: p.alvos ?? undefined}, duracao};
};

export const quadroDaCapa = (p: PropsVideo): number => {
  const {linha, duracao} = montarLinha(p);
  const api = criarApi(linha);
  return VIDEOS[p.video].capa(api, (id, rel) => api.cena(id).de + rel, duracao);
};

export const Video: React.FC<PropsVideo> = (props) => {
  const {durationInFrames} = useVideoConfig();
  const def = VIDEOS[props.video];
  const {linha} = montarLinha(props);
  const api = criarApi(linha);
  const em = (id: string, relativo: number) => api.cena(id).de + relativo;
  const sons = [
    // a folha em cada troca
    ...linha.cenas.slice(1).map((c) => ({arquivo: 'sons/folha.wav', quadro: c.de - 2, volume: 0.5})),
    ...def.sons(api, em),
  ];
  // a trilha abaixa enquanto a voz fala (com rampa de 10 quadros), se o vídeo pedir
  const falas = linha.cenas.map((c, i) => [c.de + c.fala, c.de + c.fala + Math.ceil((props.narracao?.cenas[i]?.duracao ?? 0) * FPS)]);
  const abaixa = def.abaixaTrilha ?? 0;
  const sobFala = (q: number) => {
    let m = 0;
    for (const [a, b] of falas) {
      const d = q < a ? a - q : q > b ? q - b : 0;
      m = Math.max(m, 1 - Math.min(1, d / 10));
    }
    return 1 - abaixa * m;
  };
  return (
    <LinhaProvider value={linha}>
      <AbsoluteFill style={{background: '#1f1d1a'}}>
        {linha.cenas.map((c, i) => {
          const Cena = def.cenas[c.id];
          if (!Cena) throw new Error(`o vídeo ${def.id} não tem o componente da cena ${c.id}`);
          const ultima = i === linha.cenas.length - 1;
          return (
            <Sequence key={c.id} from={c.de} durationInFrames={c.dura + (ultima ? 0 : TROCA)} name={`${i + 1} ${c.id}`}>
              <Folha comTroca={i > 0}>
                <Cena />
              </Folha>
            </Sequence>
          );
        })}
        {linha.cenas.map((c) => (
          <Sequence key={`fala-${c.id}`} from={c.de + c.fala} name={`fala ${c.id}`} layout="none">
            <Audio src={staticFile(c.arquivo)} volume={1} />
          </Sequence>
        ))}
        {sons.map((s, i) => (
          <Sequence key={`som-${i}`} from={Math.max(0, s.quadro)} name={`som ${s.arquivo}`} layout="none">
            <Audio src={staticFile(s.arquivo)} volume={s.volume} />
          </Sequence>
        ))}
        {props.trilha !== false && (
          <Audio
            src={staticFile('sons/trilha.wav')}
            volume={(q) => (def.trilha ?? 0.32) * sobFala(q) * interpolate(q, [0, 45, durationInFrames - 75, durationInFrames - 5], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}
          />
        )}
      </AbsoluteFill>
    </LinhaProvider>
  );
};

// a capa: um quadro parado do vídeo (o que o vídeo de cada lição mostra antes do play)
export const Capa: React.FC<PropsVideo> = (props) => (
  <Freeze frame={quadroDaCapa(props)}>
    <Video {...props} trilha={false} />
  </Freeze>
);
