// As composições: cada vídeo em português (…PtBR) e em inglês (…En), 16:9 em 1080p, e a capa de cada um (…Capa).
// A duração sai da narração (public/narracao/<vídeo>/<lingua>/tempos.json), lida antes de renderizar.
import {Composition, staticFile, type CalculateMetadataFunction} from 'remotion';
import {ALTURA, FPS, LARGURA, type Lingua} from './tema';
import {Capa, Video, montarLinha, type PropsVideo} from './Video';
import {VIDEOS} from './videos';

const lerJson = async (caminho: string, obrigatorio: boolean) => {
  const r = await fetch(staticFile(caminho));
  if (!r.ok) {
    if (obrigatorio) throw new Error(`falta ${caminho}: rode ${caminho.startsWith('telas') ? 'npm run telas' : 'npm run narrar'}`);
    return null;
  }
  return r.json();
};

const carregar = async (props: PropsVideo): Promise<PropsVideo> => {
  const def = VIDEOS[props.video];
  const narracao = await lerJson(`narracao/${props.video}/${props.lingua}/tempos.json`, true);
  const alvos = def.telas ? await lerJson(`telas/${props.lingua}/alvos.json`, true) : null;
  return {...props, narracao, alvos};
};

const doVideo: CalculateMetadataFunction<PropsVideo> = async ({props}) => {
  const completos = await carregar(props);
  return {durationInFrames: montarLinha(completos).duracao, props: completos};
};

// a capa tem a duração do vídeo (as cenas só aparecem dentro dela), mas mostra sempre o mesmo quadro: renderize o quadro 0
const daCapa: CalculateMetadataFunction<PropsVideo> = async ({props}) => {
  const completos = await carregar(props);
  return {durationInFrames: montarLinha(completos).duracao, props: completos};
};

const LINGUAS: [Lingua, string][] = [
  ['pt-BR', 'PtBR'],
  ['en', 'En'],
];

export const Raiz: React.FC = () => (
  <>
    {Object.values(VIDEOS).flatMap((def) =>
      LINGUAS.flatMap(([lingua, sufixo]) => [
        <Composition
          key={def.composicao + sufixo}
          id={def.composicao + sufixo}
          component={Video}
          calculateMetadata={doVideo}
          durationInFrames={300}
          fps={FPS}
          width={LARGURA}
          height={ALTURA}
          defaultProps={{video: def.id, lingua, trilha: true} as PropsVideo}
        />,
        <Composition
          key={def.composicao + sufixo + 'Capa'}
          id={def.composicao + sufixo + 'Capa'}
          component={Capa}
          calculateMetadata={daCapa}
          durationInFrames={1}
          fps={FPS}
          width={LARGURA}
          height={ALTURA}
          defaultProps={{video: def.id, lingua, trilha: false} as PropsVideo}
        />,
      ]),
    )}
    {/* o nome de antes (npm run video, README): o vídeo em português */}
    <Composition
      id="PorQueOClave"
      component={Video}
      calculateMetadata={doVideo}
      durationInFrames={300}
      fps={FPS}
      width={LARGURA}
      height={ALTURA}
      defaultProps={{video: 'por-que-o-clave', lingua: 'pt-BR', trilha: true} as PropsVideo}
    />
  </>
);
