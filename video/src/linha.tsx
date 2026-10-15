// O que toda cena precisa saber do vídeo em que está: o idioma, a linha do tempo (quando cada palavra é dita),
// o texto da tela no idioma certo e onde fica cada coisa nos prints do app.
import {createContext, useContext} from 'react';
import {staticFile} from 'remotion';
import {EN} from './i18n/en';
import {FPS, type Cena, type Lingua} from './tema';

export type Ret = [number, number, number, number]; // x, y, largura, altura, em pontos do print (1440 × 810)
export type Alvos = {largura: number; altura: number; telas: Record<string, Record<string, Ret>>};

export type Linha = {lingua: Lingua; cenas: Cena[]; alvos?: Alvos};

const Contexto = createContext<Linha | null>(null);
export const LinhaProvider = Contexto.Provider;

export const criarApi = (l: Linha) => {
  const cena = (id: string): Cena => {
    const c = l.cenas.find((x) => x.id === id);
    if (!c) throw new Error(`cena sem narração: ${id}`);
    return c;
  };
  return {
    lingua: l.lingua,
    cenas: l.cenas,
    cena,
    // quadro (relativo ao começo da cena) em que a palavra marcada com {marca} começa a ser dita
    quando: (id: string, marca: string): number => {
      const c = cena(id);
      const t = c.marcas[marca];
      if (t === undefined) throw new Error(`a cena ${id} não tem a marca {${marca}} (${l.lingua})`);
      return c.fala + Math.round(t * FPS);
    },
    // o texto da tela: a chave é o português; em inglês, falta de tradução quebra a renderização (de propósito)
    T: (pt: string): string => {
      if (l.lingua === 'pt-BR') return pt;
      const en = EN[pt];
      if (en === undefined) throw new Error(`falta a tradução em src/i18n/en.ts: "${pt}"`);
      return en;
    },
    // o retângulo de um alvo num print do app (medido pelo ferramentas/telas.py)
    alvo: (tela: string, nome: string): Ret => {
      const r = l.alvos?.telas[tela]?.[nome];
      if (!r) throw new Error(`falta o alvo ${tela}/${nome} em public/telas/${l.lingua}/alvos.json (rode npm run telas)`);
      return r;
    },
    tela: (nome: string) => staticFile(`telas/${l.lingua}/${nome}.png`),
  };
};

export type Api = ReturnType<typeof criarApi>;

export const useLinha = (): Api => {
  const l = useContext(Contexto);
  if (!l) throw new Error('cena fora de um vídeo');
  return criarApi(l);
};
