// Ilustrações genéricas para o que não é o Clave: um navegador (o Console da Anthropic desenhado como esquema, sem
// logo, cores nem layout de ninguém) e uma pasta do Windows. E o cursor solto, para essas ilustrações.
import {Easing, interpolate, useCurrentFrame} from 'remotion';
import {useLinha} from '../linha';
import {COR, MONO, SANS} from '../tema';
import {Icone} from './Icones';

const suave = Easing.inOut(Easing.cubic);

// uma barra cinza no lugar de texto que não importa
export const Traco: React.FC<{w: number | string; h?: number; cor?: string; estilo?: React.CSSProperties}> = ({w, h = 14, cor = COR.papel3, estilo}) => (
  <div style={{width: w, height: h, borderRadius: h / 2, background: cor, flex: 'none', ...estilo}} />
);

// o endereço é digitado a partir de `digita` (ou aparece pronto, se não tiver)
export const Navegador: React.FC<{
  largura: number;
  altura: number;
  endereco: string;
  digita?: number;
  destacaEndereco?: number;
  children?: React.ReactNode;
  estilo?: React.CSSProperties;
}> = ({largura, altura, endereco, digita, destacaEndereco, children, estilo}) => {
  const f = useCurrentFrame();
  const n = digita === undefined ? endereco.length : Math.round(interpolate(f - digita, [0, endereco.length * 1.2], [0, endereco.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const destaque = destacaEndereco === undefined ? 0 : interpolate(f - destacaEndereco, [0, 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const pisca = digita !== undefined && n < endereco.length && Math.floor(f / 8) % 2 === 0;
  return (
    <div
      style={{
        width: largura,
        height: altura,
        borderRadius: 16,
        overflow: 'hidden',
        background: '#fdfbf6',
        border: `2px solid ${COR.linha}`,
        boxShadow: '0 30px 70px rgba(40,30,15,.18)',
        display: 'flex',
        flexDirection: 'column',
        ...estilo,
      }}
    >
      <div style={{height: 62, flex: 'none', display: 'flex', alignItems: 'center', gap: 18, padding: '0 22px', background: COR.papel2, borderBottom: `2px solid ${COR.linha}`}}>
        <svg width={86} height={20} viewBox="0 0 86 20" fill="none" stroke={COR.texto3} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 4 8 10l6 6M8 10h0" />
          <path d="M38 4l6 6-6 6" />
          <path d="M76 6a6 6 0 1 0 1.5 5M77.5 3v4h-4" />
        </svg>
        <div
          style={{
            flex: 1,
            height: 40,
            borderRadius: 20,
            background: '#fdfbf6',
            border: `2px solid ${destaque > 0 ? COR.acao : COR.linha}`,
            boxShadow: destaque > 0 ? `0 0 0 ${6 * destaque}px rgba(29,95,102,.18)` : 'none',
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            padding: '0 18px',
            fontFamily: MONO,
            fontSize: 24,
            color: COR.texto,
          }}
        >
          <Icone nome="trava" tamanho={20} cor={COR.texto3} />
          <span>
            {endereco.slice(0, n)}
            {pisca && <span style={{display: 'inline-block', width: 2, height: 24, background: COR.texto, verticalAlign: 'middle', marginLeft: 2}} />}
          </span>
        </div>
      </div>
      <div style={{flex: 1, position: 'relative', overflow: 'hidden'}}>{children}</div>
    </div>
  );
};

// a legenda das ilustrações (o Console da Anthropic é desenhado, não copiado)
export const Legenda: React.FC<{x: number; y: number; claro?: boolean}> = ({x, y, claro = true}) => {
  const {T} = useLinha();
  return (
    <div style={{position: 'absolute', left: x, top: y, display: 'flex', alignItems: 'center', gap: 10, fontFamily: MONO, fontSize: 21, color: claro ? COR.texto3 : COR.tintaTexto3}}>
      <Icone nome="info" tamanho={22} cor={claro ? COR.texto3 : COR.tintaTexto3} />
      {T('ilustração: a tela real pode mudar')}
    </div>
  );
};

// o menu do esquema do Console: barras genéricas e só os itens que a lição cita, com o nome que ela usa
export const MenuConsole: React.FC<{itens: {nome: string; ativo?: number; posicao: number}[]}> = ({itens}) => {
  const f = useCurrentFrame();
  const linhas = [150, 120, 170, 110, 140, 130];
  return (
    <div style={{width: 280, flex: 'none', borderRight: `2px solid ${COR.papel3}`, padding: '34px 24px', display: 'flex', flexDirection: 'column', gap: 26}}>
      <Traco w={120} h={22} cor={COR.linha} />
      <div style={{height: 10}} />
      {linhas.map((w, i) => {
        const item = itens.find((x) => x.posicao === i);
        if (!item) return <Traco key={i} w={w} />;
        const ativo = item.ativo !== undefined && f >= item.ativo;
        return (
          <div
            key={i}
            style={{
              margin: '-10px -12px',
              padding: '8px 12px',
              borderRadius: 10,
              background: ativo ? COR.acaoSuave : 'transparent',
              fontFamily: SANS,
              fontWeight: 500,
              fontSize: 26,
              color: ativo ? COR.acao : COR.texto2,
            }}
          >
            {item.nome}
          </div>
        );
      })}
    </div>
  );
};

// cursor solto (coordenadas do quadro do vídeo), para as ilustrações
export type PontoLivre = {em: number; x: number; y: number; clique?: boolean; duplo?: boolean};

export const CursorLivre: React.FC<{pontos: PontoLivre[]}> = ({pontos}) => {
  const f = useCurrentFrame();
  if (!pontos.length || f < pontos[0].em - 14) return null;
  let x = pontos[0].x;
  let y = pontos[0].y;
  for (let i = 1; i < pontos.length; i++) {
    const a = pontos[i - 1];
    const b = pontos[i];
    const mov = Math.min(18, Math.max(6, b.em - a.em - 2));
    if (f >= b.em - mov) {
      const t = suave(Math.min(1, (f - (b.em - mov)) / mov));
      x = a.x + (b.x - a.x) * t;
      y = a.y + (b.y - a.y) * t;
    }
  }
  let aperto = 1;
  const ondas: {x: number; y: number; t: number}[] = [];
  for (const p of pontos) {
    for (const c of p.clique ? (p.duplo ? [p.em, p.em + 6] : [p.em]) : []) {
      if (f >= c && f < c + 16) ondas.push({x: p.x, y: p.y, t: (f - c) / 16});
      if (f >= c && f < c + 8) aperto = Math.min(aperto, interpolate(f - c, [0, 3, 8], [1, 0.8, 1]));
    }
  }
  const o = interpolate(f, [pontos[0].em - 14, pontos[0].em - 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <>
      {ondas.map((r, i) => (
        <div key={i} style={{position: 'absolute', left: r.x - 8 - 36 * r.t, top: r.y - 8 - 36 * r.t, width: 16 + 72 * r.t, height: 16 + 72 * r.t, borderRadius: '50%', border: `3px solid ${COR.acao}`, opacity: 0.7 * (1 - r.t)}} />
      ))}
      <svg
        width={36}
        height={44}
        viewBox="0 0 30 36"
        style={{position: 'absolute', left: x - 4, top: y - 4, opacity: o, transform: `scale(${aperto})`, transformOrigin: '4px 4px', filter: 'drop-shadow(0 3px 5px rgba(0,0,0,.35))'}}
      >
        <path d="M3 3 L3 29 L10 22.5 L14.5 33 L19 31 L14.6 20.8 L24 20.8 Z" fill="#fff" stroke="#1f1d1a" strokeWidth={2} strokeLinejoin="round" />
      </svg>
    </>
  );
};

// uma pasta do Windows, genérica: o caminho no topo e a lista de itens
export const Pasta: React.FC<{
  largura: number;
  caminho: string;
  itens: {nome: string; pasta?: boolean}[];
  destaque?: {nome: string; de: number};
  estilo?: React.CSSProperties;
}> = ({largura, caminho, itens, destaque, estilo}) => {
  const f = useCurrentFrame();
  return (
    <div style={{width: largura, borderRadius: 14, overflow: 'hidden', background: '#fdfbf6', border: `2px solid ${COR.linha}`, boxShadow: '0 30px 70px rgba(40,30,15,.18)', ...estilo}}>
      <div style={{height: 56, display: 'flex', alignItems: 'center', gap: 14, padding: '0 22px', background: COR.papel2, borderBottom: `2px solid ${COR.linha}`, fontFamily: SANS, fontSize: 24, color: COR.texto2}}>
        <Icone nome="pasta" tamanho={26} cor={COR.acao} />
        {caminho}
      </div>
      <div style={{padding: '10px 0'}}>
        {itens.map((it) => {
          const ativo = destaque && destaque.nome === it.nome && f >= destaque.de;
          return (
            <div
              key={it.nome}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 16,
                padding: '0 24px',
                height: 46,
                fontFamily: SANS,
                fontSize: 24,
                color: COR.texto,
                background: ativo ? COR.acaoSuave : 'transparent',
              }}
            >
              <Icone nome={it.pasta ? 'pasta' : 'arquivo'} tamanho={24} cor={it.pasta ? '#b08a3e' : COR.texto3} />
              {it.nome}
            </div>
          );
        })}
      </div>
    </div>
  );
};
