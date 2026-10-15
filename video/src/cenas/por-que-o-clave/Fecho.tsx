// Cena 9: "O Clave é código aberto e gratuito. Você só paga o que usar. É só baixar no GitHub."
// Sem o endereço do repositório na tela (decisão do dono do repositório): a fala cita o GitHub e basta.
import {useLinha} from '../../linha';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {Entra, Fundo, Logo, Sobe} from '../../componentes/Base';
import {COR, SANS} from '../../tema';

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
  const {quando, T} = useLinha();
  const tO = quando(C, 'o');
  const tClave = quando(C, 'clave');
  const tCodigo = quando(C, 'codigo');
  const tGratuito = quando(C, 'gratuito');
  const tVoce = quando(C, 'voce');
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 44}}>
          <Logo tamanho={170} inicio={tO} />
          <Sobe texto="Clave" inicio={tClave} tamanho={200} cor={COR.tintaTexto} />
        </div>
        <div style={{display: 'flex', gap: 22, marginTop: 50}}>
          <Selo texto={T('Código aberto (MIT)')} inicio={tCodigo} />
          <Selo texto={T('Gratuito')} inicio={tGratuito} />
          <Selo texto={T('Para Windows')} inicio={tGratuito + 6} />
        </div>
        <div style={{marginTop: 54}}>
          <Sobe texto={T('Você só paga o que usar.')} inicio={tVoce} tamanho={64} peso={400} cor={COR.tintaTexto2} italico passo={2} />
        </div>
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
        {T('O Clave é um app independente, sem ligação com a Anthropic. Claude é marca da Anthropic.')}
      </div>
    </Fundo>
  );
};
