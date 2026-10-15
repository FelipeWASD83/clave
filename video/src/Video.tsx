// O vídeo inteiro: as nove cenas em sequência, a folha em cada troca, a narração de cada cena e os efeitos.
import {AbsoluteFill, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {Audio} from '@remotion/media';
import {Folha} from './componentes/Troca';
import {Apresenta} from './cenas/Apresenta';
import {Aprender} from './cenas/Aprender';
import {Code} from './cenas/Code';
import {Custo} from './cenas/Custo';
import {Dados} from './cenas/Dados';
import {Fecho} from './cenas/Fecho';
import {Fluxo} from './cenas/Fluxo';
import {Gancho} from './cenas/Gancho';
import {Limite} from './cenas/Limite';
import {CENAS, DURACAO, FPS, TROCA, cena, quando} from './tema';

const COMPONENTES: Record<string, React.FC> = {
  gancho: Gancho,
  apresenta: Apresenta,
  custo: Custo,
  limite: Limite,
  dados: Dados,
  fluxo: Fluxo,
  code: Code,
  aprender: Aprender,
  fecho: Fecho,
};

export type PropsVideo = {trilha?: boolean};

// efeito sonoro num quadro absoluto: cena + quadro relativo
const em = (id: string, relativo: number) => cena(id).de + relativo;

const SONS: {arquivo: string; quadro: number; volume: number}[] = [
  // a folha em cada troca
  ...CENAS.slice(1).map((c) => ({arquivo: 'sons/folha.wav', quadro: c.de - 2, volume: 0.5})),
  // gancho: o relógio do limite fazendo tique a cada segundo
  {arquivo: 'sons/toque.wav', quadro: em('gancho', quando('gancho', 'limite') - 2), volume: 0.4},
  ...Array.from({length: 4}, (_, i) => ({arquivo: 'sons/tique.wav', quadro: em('gancho', quando('gancho', 'Volte') + i * FPS), volume: 0.5})),
  // apresentação: a marca chega
  {arquivo: 'sons/selo.wav', quadro: em('apresenta', quando('apresenta', 'Conheça')), volume: 0.45},
  ...['Windows', 'Clód', 'chave'].map((p) => ({arquivo: 'sons/toque.wav', quadro: em('apresenta', quando('apresenta', p)), volume: 0.3})),
  // custo: a impressora imprimindo cada linha do recibo
  ...[quando('custo', 'Mil'), quando('custo', 'custo'), quando('custo', 'resposta'), quando('custo', 'teto')].map((q) => ({
    arquivo: 'sons/impressora.wav',
    quadro: em('custo', q),
    volume: 0.35,
  })),
  // limite: os dois riscos
  ...[quando('limite', 'horas'), quando('limite', 'semanal')].map((q) => ({arquivo: 'sons/toque.wav', quadro: em('limite', q), volume: 0.4})),
  // fluxo: cada etapa e o clique em "Rodar o fluxo"
  ...['Opus', 'Sonnet', 'Ráicu'].map((p) => ({arquivo: 'sons/toque.wav', quadro: em('fluxo', quando('fluxo', p)), volume: 0.28})),
  {arquivo: 'sons/toque.wav', quadro: em('fluxo', quando('fluxo', 'aprovar')), volume: 0.5},
  // code: arquivos, o "Permitir", o desfazer e a rotina
  ...['planilhas', 'arquivos', 'scripts'].map((p) => ({arquivo: 'sons/toque.wav', quadro: em('code', quando('code', p)), volume: 0.25})),
  {arquivo: 'sons/toque.wav', quadro: em('code', quando('code', 'aprova')), volume: 0.5},
  {arquivo: 'sons/toque.wav', quadro: em('code', quando('code', 'horário')), volume: 0.4},
  // fecho: a marca
  {arquivo: 'sons/selo.wav', quadro: em('fecho', quando('fecho', 'O')), volume: 0.5},
];

export const Video: React.FC<PropsVideo> = ({trilha = true}) => {
  const {durationInFrames} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: '#1f1d1a'}}>
      {CENAS.map((c, i) => {
        const Cena = COMPONENTES[c.id];
        const ultima = i === CENAS.length - 1;
        return (
          <Sequence key={c.id} from={c.de} durationInFrames={c.dura + (ultima ? 0 : TROCA)} name={`${i + 1} ${c.id}`}>
            <Folha comTroca={i > 0}>
              <Cena />
            </Folha>
          </Sequence>
        );
      })}
      {CENAS.map((c) => (
        <Sequence key={`fala-${c.id}`} from={c.de + c.fala} name={`fala ${c.id}`} layout="none">
          <Audio src={staticFile(c.arquivo)} volume={1} />
        </Sequence>
      ))}
      {SONS.map((s, i) => (
        <Sequence key={`som-${i}`} from={s.quadro} name={`som ${s.arquivo}`} layout="none">
          <Audio src={staticFile(s.arquivo)} volume={s.volume} />
        </Sequence>
      ))}
      {trilha && (
        <Audio
          src={staticFile('sons/trilha.wav')}
          volume={(q) => 0.32 * interpolate(q, [0, 45, durationInFrames - 75, durationInFrames - 5], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}
        />
      )}
    </AbsoluteFill>
  );
};

export {DURACAO};
