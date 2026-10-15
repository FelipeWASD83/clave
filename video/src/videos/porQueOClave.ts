// "Por que usar o Clave": nove cenas de argumento, sem prints do app.
import {Apresenta} from '../cenas/por-que-o-clave/Apresenta';
import {Aprender} from '../cenas/por-que-o-clave/Aprender';
import {Code} from '../cenas/por-que-o-clave/Code';
import {Custo} from '../cenas/por-que-o-clave/Custo';
import {Dados} from '../cenas/por-que-o-clave/Dados';
import {Fecho} from '../cenas/por-que-o-clave/Fecho';
import {Fluxo} from '../cenas/por-que-o-clave/Fluxo';
import {Gancho} from '../cenas/por-que-o-clave/Gancho';
import {Limite} from '../cenas/por-que-o-clave/Limite';
import {FPS} from '../tema';
import type {DefVideo} from './tipos';

export const porQueOClave: DefVideo = {
  id: 'por-que-o-clave',
  composicao: 'PorQueOClave',
  cenas: {gancho: Gancho, apresenta: Apresenta, custo: Custo, limite: Limite, dados: Dados, fluxo: Fluxo, code: Code, aprender: Aprender, fecho: Fecho},
  extra: {fecho: 60, custo: 10, code: 8},
  capa: (_api, _em, duracao) => duracao - 13, // o último quadro: a marca, os selos e o slogan
  sons: ({quando}, em) => [
    // gancho: o relógio do limite fazendo tique a cada segundo
    {arquivo: 'sons/toque.wav', quadro: em('gancho', quando('gancho', 'limite') - 2), volume: 0.4},
    ...Array.from({length: 4}, (_, i) => ({arquivo: 'sons/tique.wav', quadro: em('gancho', quando('gancho', 'volte') + i * FPS), volume: 0.5})),
    // apresentação: a marca chega
    {arquivo: 'sons/selo.wav', quadro: em('apresenta', quando('apresenta', 'conheca')), volume: 0.45},
    ...['windows', 'claude', 'chave'].map((p) => ({arquivo: 'sons/toque.wav', quadro: em('apresenta', quando('apresenta', p)), volume: 0.3})),
    // custo: a impressora imprimindo cada linha do recibo
    ...['mil', 'custo', 'resposta', 'teto'].map((p) => ({arquivo: 'sons/impressora.wav', quadro: em('custo', quando('custo', p)), volume: 0.35})),
    // limite: os dois riscos
    ...['horas', 'semanal'].map((p) => ({arquivo: 'sons/toque.wav', quadro: em('limite', quando('limite', p)), volume: 0.4})),
    // fluxo: cada etapa e o clique em "Rodar o fluxo"
    ...['opus', 'sonnet', 'raicu'].map((p) => ({arquivo: 'sons/toque.wav', quadro: em('fluxo', quando('fluxo', p)), volume: 0.28})),
    {arquivo: 'sons/toque.wav', quadro: em('fluxo', quando('fluxo', 'aprovar')), volume: 0.5},
    // code: arquivos, o "Permitir", o desfazer e a rotina
    ...['planilhas', 'arquivos', 'scripts'].map((p) => ({arquivo: 'sons/toque.wav', quadro: em('code', quando('code', p)), volume: 0.25})),
    {arquivo: 'sons/toque.wav', quadro: em('code', quando('code', 'aprova')), volume: 0.5},
    {arquivo: 'sons/toque.wav', quadro: em('code', quando('code', 'horario')), volume: 0.4},
    // fecho: a marca
    {arquivo: 'sons/selo.wav', quadro: em('fecho', quando('fecho', 'o')), volume: 0.5},
  ],
};
