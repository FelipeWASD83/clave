import {Composition} from 'remotion';
import {ALTURA, DURACAO, FPS, LARGURA} from './tema';
import {Video} from './Video';

export const Raiz: React.FC = () => (
  // 16:9 em 1080p, com narração (README do GitHub, YouTube, release)
  <Composition id="PorQueOClave" component={Video} durationInFrames={DURACAO} fps={FPS} width={LARGURA} height={ALTURA} defaultProps={{trilha: true}} />
);
