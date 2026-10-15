// Todos os vídeos. O id é o do roteiro (roteiros/<id>.json) e o do arquivo final (saida/<id>.<lingua>.mp4).
import {chaveDaApi} from './chaveDaApi';
import {porQueOClave} from './porQueOClave';
import {primeiraAutomacao} from './primeiraAutomacao';
import {primeirosPassos} from './primeirosPassos';
import type {DefVideo} from './tipos';

export const VIDEOS: Record<string, DefVideo> = Object.fromEntries(
  [porQueOClave, chaveDaApi, primeirosPassos, primeiraAutomacao].map((v) => [v.id, v]),
);
