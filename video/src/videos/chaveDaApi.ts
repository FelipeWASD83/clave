// "Como pegar a chave da API" (lição tutoriais/chave-da-api.md).
import {Abre, Colar, Conta, Copiar, Credito, Criar, Fecho, Regras, Teto} from '../cenas/chave-da-api/Cenas';
import type {DefVideo, Som} from './tipos';

const clique = (quadro: number): Som => ({arquivo: 'sons/clique.wav', quadro, volume: 0.6});
const teclas = (quadro: number): Som => ({arquivo: 'sons/teclas.wav', quadro, volume: 0.45});

export const chaveDaApi: DefVideo = {
  id: 'chave-da-api',
  composicao: 'ChaveDaApi',
  cenas: {abre: Abre, conta: Conta, credito: Credito, criar: Criar, copiar: Copiar, colar: Colar, teto: Teto, regras: Regras, fecho: Fecho},
  extra: {criar: 12, colar: 16, teto: 16, fecho: 50},
  telas: true,
  trilha: 0.26,
  abaixaTrilha: 0.6,
  capa: ({quando}, em) => em('abre', quando('abre', 'pegar') + 20), // o título, a chave ligando o Clave à conta
  sons: ({quando}, em) => [
    {arquivo: 'sons/selo.wav', quadro: em('abre', quando('abre', 'chave')), volume: 0.4},
    {arquivo: 'sons/toque.wav', quadro: em('abre', quando('abre', 'conta') + 10), volume: 0.35},
    teclas(em('conta', quando('conta', 'endereco') - 4)),
    {arquivo: 'sons/toque.wav', quadro: em('credito', quando('credito', 'max')), volume: 0.3},
    clique(em('criar', quando('criar', 'apikeys'))),
    clique(em('criar', quando('criar', 'create'))),
    teclas(em('criar', quando('criar', 'nome') + 2)),
    clique(em('copiar', quando('copiar', 'copie') + 20)),
    clique(em('colar', quando('colar', 'config'))),
    clique(em('colar', quando('colar', 'conta'))),
    clique(em('colar', quando('colar', 'cole'))),
    clique(em('colar', quando('colar', 'conferir'))),
    clique(em('teto', quando('teto', 'limite'))),
    clique(em('teto', quando('teto', 'teto'))),
    {arquivo: 'sons/toque.wav', quadro: em('regras', quando('regras', 'nunca')), volume: 0.3},
    {arquivo: 'sons/toque.wav', quadro: em('regras', quando('regras', 'vazou')), volume: 0.3},
    {arquivo: 'sons/selo.wav', quadro: em('fecho', quando('fecho', 'pronto') - 12), volume: 0.45},
  ],
};
