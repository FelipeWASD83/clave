import type {Api} from '../linha';

export type Som = {arquivo: string; quadro: number; volume: number};

// Um vídeo: as cenas (na ordem do roteiro em roteiros/<id>.json), folgas a mais e os efeitos sonoros.
export type DefVideo = {
  id: string; // o mesmo do roteiro e da pasta public/narracao/<id>
  composicao: string; // prefixo do id da composição no Remotion (PorQueOClave → PorQueOClavePtBR e PorQueOClaveEn)
  cenas: Record<string, React.FC>;
  extra?: Record<string, number>; // quadros a mais no fim de cada cena
  telas?: boolean; // usa prints do app (public/telas/<lingua>)
  trilha?: number; // volume da trilha (padrão 0.32)
  abaixaTrilha?: number; // quanto a trilha cai enquanto a voz fala (0 a 1; padrão 0)
  // o quadro da capa (a imagem que aparece antes de dar play): um quadro com o título legível
  capa: (api: Api, em: (cena: string, relativo: number) => number, duracao: number) => number;
  // em(cena, quadro relativo) dá o quadro absoluto
  sons: (api: Api, em: (cena: string, relativo: number) => number) => Som[];
};
