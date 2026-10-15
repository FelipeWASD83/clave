// Cena 2: "Conheça o Clave. Um app para Windows que usa o Claude pela API, com a sua própria chave."
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {Entra, Fundo, Logo, Sobe} from '../componentes/Base';
import {Icone} from '../componentes/Icones';
import {COR, MONO, SANS, SERIFA, quando} from '../tema';

const C = 'apresenta';

const Linha: React.FC<{inicio: number; icone: string; titulo: string; texto: string; extra?: React.ReactNode}> = ({inicio, icone, titulo, texto, extra}) => (
  <Entra inicio={inicio} distancia={36}>
    <div style={{display: 'flex', gap: 30, alignItems: 'center', padding: '30px 0', borderBottom: `1.5px solid ${COR.linha}`}}>
      <div style={{width: 84, height: 84, borderRadius: 18, background: COR.acaoSuave, display: 'grid', placeItems: 'center', flex: 'none'}}>
        <Icone nome={icone} tamanho={46} cor={COR.acao} />
      </div>
      <div>
        <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 40, color: COR.texto}}>{titulo}</div>
        <div style={{fontFamily: SANS, fontSize: 28, color: COR.texto3, marginTop: 4}}>{texto}</div>
      </div>
      {extra}
    </div>
  </Entra>
);

export const Apresenta: React.FC = () => {
  const f = useCurrentFrame();
  const tClave = quando(C, 'Clave');
  const tWindows = quando(C, 'Windows');
  const tClaude = quando(C, 'Clód');
  const tChave = quando(C, 'chave');
  const tConheca = quando(C, 'Conheça');
  const chaveVisivel = interpolate(f - tChave, [6, 26], [0, 8], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <Fundo tipo="papel">
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 140px', gap: 120}}>
        <div style={{flex: '0 0 760px'}}>
          <Logo tamanho={200} inicio={tConheca} />
          <div style={{marginTop: 40}}>
            <Sobe texto="Clave" inicio={tClave} tamanho={220} peso={500} cor={COR.texto} />
          </div>
          <div style={{marginTop: 18}}>
            <Sobe texto="O Claude pela API, com a sua chave." inicio={tClaude} tamanho={52} peso={400} cor={COR.texto2} italico passo={2} />
          </div>
        </div>
        <div style={{flex: 1}}>
          <Linha inicio={tWindows} icone="janela" titulo="App para Windows" texto="Janela própria, instala com dois cliques" />
          <Linha inicio={tClaude} icone="faisca" titulo="O Claude, pela API" texto="Opus, Sonnet, Haiku e Fable, os modelos da Anthropic" />
          <Linha
            inicio={tChave}
            icone="chave"
            titulo="Com a sua chave"
            texto="Criptografada, só no seu PC"
            extra={
              <div style={{marginLeft: 'auto', flex: 'none', whiteSpace: 'nowrap', width: 290, fontFamily: MONO, fontSize: 28, color: COR.texto3, background: COR.papel2, border: `1.5px solid ${COR.linha}`, borderRadius: 10, padding: '10px 18px'}}>
                sk-ant-{'•'.repeat(Math.round(chaveVisivel))}
              </div>
            }
          />
        </div>
      </AbsoluteFill>
    </Fundo>
  );
};
