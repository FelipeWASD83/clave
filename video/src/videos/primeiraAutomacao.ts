// "Primeira automação" (lições tutoriais/primeira-automacao.md e modo-code.md).
import {Abre, Aprova, Fecho, Novo, Pedido, Permissao, Plano, Pronto} from '../cenas/primeira-automacao/Cenas';
import type {DefVideo, Som} from './tipos';

const clique = (quadro: number): Som => ({arquivo: 'sons/clique.wav', quadro, volume: 0.6});
const teclas = (quadro: number): Som => ({arquivo: 'sons/teclas.wav', quadro, volume: 0.45});

export const primeiraAutomacao: DefVideo = {
  id: 'primeira-automacao',
  composicao: 'PrimeiraAutomacao',
  cenas: {abre: Abre, novo: Novo, permissao: Permissao, pedido: Pedido, plano: Plano, aprova: Aprova, pronto: Pronto, fecho: Fecho},
  extra: {abre: 20, novo: 22, permissao: 16, pedido: 52, plano: 16, aprova: 92, pronto: 22, fecho: 50},
  telas: true,
  trilha: 0.26,
  abaixaTrilha: 0.6,
  capa: ({quando}, em) => em('abre', quando('abre', 'sem') + 40),
  sons: ({quando}, em) => [
    {arquivo: 'sons/toque.wav', quadro: em('abre', quando('abre', 'arrumar')), volume: 0.3},
    {arquivo: 'sons/folha.wav', quadro: em('abre', quando('abre', 'sem') + 4), volume: 0.35},
    clique(em('novo', quando('novo', 'novo') + 2)),
    clique(em('novo', quando('novo', 'escolha') + 6)),
    clique(em('novo', quando('novo', 'downloads') - 4)),
    clique(em('permissao', quando('permissao', 'perguntar'))),
    clique(em('pedido', quando('pedido', 'separar') - 6)),
    teclas(em('pedido', quando('pedido', 'separar') - 4)),
    clique(em('pedido', quando('pedido', 'mostrar') + 46)),
    clique(em('aprova', quando('aprova', 'responda') + 14)),
    {arquivo: 'sons/toque.wav', quadro: em('aprova', quando('aprova', 'cartao') - 6), volume: 0.35},
    clique(em('aprova', quando('aprova', 'recusar') + 40)),
    clique(em('aprova', quando('aprova', 'recusar') + 74)),
    clique(em('pronto', quando('pronto', 'clique') + 14)),
    {arquivo: 'sons/selo.wav', quadro: em('fecho', quando('fecho', 'roda') + 10), volume: 0.45},
  ],
};
