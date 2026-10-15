// "Primeiros passos" (README: instalação; lição tutoriais/primeira-conversa.md).
import {Abre, Boas, Conversa, Fecho, Instalar, Modelo, Resposta, Uso} from '../cenas/primeiros-passos/Cenas';
import type {DefVideo, Som} from './tipos';

const clique = (quadro: number): Som => ({arquivo: 'sons/clique.wav', quadro, volume: 0.6});
const teclas = (quadro: number): Som => ({arquivo: 'sons/teclas.wav', quadro, volume: 0.45});

export const primeirosPassos: DefVideo = {
  id: 'primeiros-passos',
  composicao: 'PrimeirosPassos',
  cenas: {abre: Abre, instalar: Instalar, boas: Boas, conversa: Conversa, modelo: Modelo, resposta: Resposta, uso: Uso, fecho: Fecho},
  extra: {instalar: 20, boas: 14, conversa: 16, modelo: 44, resposta: 18, uso: 18, fecho: 50},
  telas: true,
  trilha: 0.26,
  abaixaTrilha: 0.6,
  capa: ({quando}, em) => em('abre', quando('abre', 'um') + 20),
  sons: ({quando}, em) => [
    ...['do', 'primeira'].map((m) => ({arquivo: 'sons/toque.wav', quadro: em('abre', quando('abre', m)), volume: 0.3})),
    clique(em('instalar', quando('instalar', 'instalar') - 2)),
    clique(em('instalar', quando('instalar', 'instalar') + 4)),
    ...[0, 1, 2, 3].map((i) => ({arquivo: 'sons/tique.wav', quadro: em('instalar', quando('instalar', 'prepara') + i * 10 + 8), volume: 0.4})),
    {arquivo: 'sons/toque.wav', quadro: em('instalar', quando('instalar', 'atalho')), volume: 0.35},
    clique(em('boas', quando('boas', 'chave') - 6)),
    teclas(em('boas', quando('boas', 'chave'))),
    clique(em('boas', quando('boas', 'teto') - 6)),
    clique(em('boas', quando('boas', 'nome') - 6)),
    clique(em('conversa', quando('conversa', 'clique') + 6)),
    clique(em('conversa', quando('conversa', 'escreva'))),
    teclas(em('conversa', quando('conversa', 'escreva') + 4)),
    clique(em('modelo', quando('modelo', 'botao'))),
    clique(em('modelo', quando('modelo', 'opus') + 34)),
    clique(em('resposta', quando('resposta', 'enter'))),
    {arquivo: 'sons/toque.wav', quadro: em('resposta', quando('resposta', 'quanto')), volume: 0.3},
    {arquivo: 'sons/selo.wav', quadro: em('fecho', quando('fecho', 'pronto') - 12), volume: 0.45},
  ],
};
