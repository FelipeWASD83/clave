// Cena 9: "O Clave é código aberto e gratuito. Você só paga o que usar. É só baixar no GitHub."
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {Entra, Fundo, Logo, Sobe} from '../componentes/Base';
import {COR, MONO, SANS, quando} from '../tema';
// o endereço do repositório vem do mesmo lugar que o botão Atualizar usa
import versao from '../../../versao.json';

const C = 'fecho';

const Selo: React.FC<{texto: string; inicio: number}> = ({texto, inicio}) => (
  <Entra inicio={inicio} distancia={20}>
    <div style={{fontFamily: SANS, fontSize: 32, color: COR.tintaTexto, border: `1.5px solid ${COR.tintaLinha}`, borderRadius: 40, padding: '12px 30px', background: COR.tinta2}}>
      {texto}
    </div>
  </Entra>
);

export const Fecho: React.FC = () => {
  const f = useCurrentFrame();
  const tO = quando(C, 'O');
  const tClave = quando(C, 'Clave');
  const tCodigo = quando(C, 'código');
  const tGratuito = quando(C, 'gratuito');
  const tVoce = quando(C, 'Você');
  const tBaixar = quando(C, 'baixar');
  const sublinha = interpolate(f - tBaixar - 6, [0, 18], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 44}}>
          <Logo tamanho={170} inicio={tO} />
          <Sobe texto="Clave" inicio={tClave} tamanho={200} cor={COR.tintaTexto} />
        </div>
        <div style={{display: 'flex', gap: 22, marginTop: 50}}>
          <Selo texto="Código aberto (MIT)" inicio={tCodigo} />
          <Selo texto="Gratuito" inicio={tGratuito} />
          <Selo texto="Para Windows" inicio={tGratuito + 6} />
        </div>
        <div style={{marginTop: 54}}>
          <Sobe texto="Você só paga o que usar." inicio={tVoce} tamanho={64} peso={400} cor={COR.tintaTexto2} italico passo={2} />
        </div>
        <Entra inicio={tBaixar} distancia={20} estilo={{marginTop: 60}}>
          <div style={{position: 'relative', fontFamily: MONO, fontSize: 46, color: COR.tintaAcao}}>
            github.com/{versao.repositorio}
            <div style={{position: 'absolute', left: 0, right: 0, bottom: -12, height: 4, background: COR.tintaAcao, transform: `scaleX(${sublinha})`, transformOrigin: 'left'}} />
          </div>
        </Entra>
      </AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 46,
          textAlign: 'center',
          fontFamily: SANS,
          fontSize: 22,
          color: COR.tintaTexto3,
          opacity: interpolate(f - tVoce, [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}),
        }}
      >
        O Clave é um app independente, sem ligação com a Anthropic. Claude é marca da Anthropic.
      </div>
    </Fundo>
  );
};
