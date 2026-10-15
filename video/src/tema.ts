// Identidade do Clave (a mesma do app: papel, tinta e um verde-azulado de ação) e o relógio dos vídeos.
// A linha do tempo sai da narração: cada cena dura o que a fala dela dura, mais as folgas daqui.
import {loadFont as carregarSerifa} from '@remotion/google-fonts/SourceSerif4';
import {loadFont as carregarSans} from '@remotion/google-fonts/IBMPlexSans';
import {loadFont as carregarMono} from '@remotion/google-fonts/IBMPlexMono';

export const {fontFamily: SERIFA} = carregarSerifa('normal', {weights: ['400', '500', '600'], subsets: ['latin', 'latin-ext']});
export const {fontFamily: SANS} = carregarSans('normal', {weights: ['400', '500', '600'], subsets: ['latin', 'latin-ext']});
export const {fontFamily: MONO} = carregarMono('normal', {weights: ['400', '500'], subsets: ['latin', 'latin-ext']});

// cores do app (app/css/base.css)
export const COR = {
  papel: '#f6f1e7',
  papel2: '#eee7d9',
  papel3: '#e5dccb',
  linha: '#d9cfbd',
  texto: '#1f1d1a',
  texto2: '#4b463e',
  texto3: '#6e665a',
  acao: '#1d5f66',
  acaoSuave: '#d4e4e1',
  tinta: '#1f1d1a',
  tinta2: '#2b2824',
  tinta3: '#38342e',
  tintaLinha: '#4a453d',
  tintaTexto: '#ede6d8',
  tintaTexto2: '#b3aa9a',
  tintaTexto3: '#958c7d',
  tintaAcao: '#73c0bb',
  erro: '#a3392b',
  erroClaro: '#e0806f',
  sucesso: '#3b7444',
  sucessoClaro: '#86c08e',
};

export const FPS = 30;
export const LARGURA = 1920;
export const ALTURA = 1080;

// a troca de cena (a folha passando) dura TROCA quadros e acontece por cima do fim da cena anterior
export const TROCA = 16;
const ANTES = 10; // da folha assentar até a fala começar
const DEPOIS = 22; // da fala acabar até a próxima folha

export type Lingua = 'pt-BR' | 'en';
export type Palavra = {t: number; d: number; texto: string};
export type CenaNarrada = {id: string; arquivo: string; duracao: number; texto: string; palavras: Palavra[]; marcas: Record<string, number>};
export type Narracao = {video: string; lingua: Lingua; voz: string; cenas: CenaNarrada[]};
export type Cena = {id: string; de: number; dura: number; fala: number; arquivo: string; marcas: Record<string, number>};

// extra: quadros a mais no fim de uma cena (para a tela respirar depois da fala)
export const montarCenas = (narracao: Narracao, extra: Record<string, number> = {}): {cenas: Cena[]; duracao: number} => {
  let de = 0;
  const cenas = narracao.cenas.map((c, i) => {
    const fala = (i === 0 ? 0 : TROCA) + ANTES;
    const dura = fala + Math.ceil(c.duracao * FPS) + DEPOIS + (extra[c.id] ?? 0);
    const cena = {id: c.id, de, dura, fala, arquivo: c.arquivo, marcas: c.marcas};
    de += dura;
    return cena;
  });
  return {cenas, duracao: de};
};

// molas: um vocabulário só de movimento
export const MOLA = {damping: 200, mass: 0.7, stiffness: 160};
export const MOLA_VIVA = {damping: 13, mass: 0.7, stiffness: 150};
