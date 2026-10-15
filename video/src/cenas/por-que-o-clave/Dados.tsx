// Cena 5: "Na API, por padrão, as suas mensagens não são usadas para treinar modelos. E as suas conversas ficam no
// seu computador." Fonte: privacy.claude.com (dados da API não treinam modelos por padrão; apagados em até 30 dias).
import {useLinha} from '../../linha';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {Entra, Fundo, Nota, Rotulo, Sobe} from '../../componentes/Base';
import {Icone} from '../../componentes/Icones';
import {COR, MONO, SANS} from '../../tema';

const C = 'dados';

const Item: React.FC<{inicio: number; icone: string; texto: string; detalhe: string}> = ({inicio, icone, texto, detalhe}) => (
  <Entra inicio={inicio} distancia={26}>
    <div style={{display: 'flex', alignItems: 'center', gap: 22, padding: '18px 26px', borderRadius: 14, background: COR.tinta3, marginBottom: 16}}>
      <Icone nome={icone} tamanho={40} cor={COR.tintaAcao} />
      <div style={{fontFamily: SANS, fontSize: 32, color: COR.tintaTexto, flex: 1}}>{texto}</div>
      <div style={{fontFamily: MONO, fontSize: 22, color: COR.tintaTexto3}}>{detalhe}</div>
    </div>
  </Entra>
);

export const Dados: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T} = useLinha();
  const tNa = quando(C, 'na');
  const tMensagens = quando(C, 'mensagens');
  const tNao = quando(C, 'nao');
  const tConversas = quando(C, 'conversas');
  const tFicam = quando(C, 'ficam');
  const tComputador = quando(C, 'computador');
  const tela = interpolate(f - (tConversas - 8), [0, 14], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 140px', gap: 100}}>
        <div style={{flex: 1}}>
          <Entra inicio={tNa}>
            <Icone nome="escudo" tamanho={110} cor={COR.tintaAcao} espessura={1.6} />
          </Entra>
          <div style={{marginTop: 26}}>
            <Rotulo texto={T('Na API, por padrão')} inicio={tNa + 4} cor={COR.tintaAcao} tamanho={28} />
          </div>
          <div style={{marginTop: 22}}>
            <Sobe texto={T('Suas mensagens não treinam modelos.')} inicio={tMensagens} tamanho={92} cor={COR.tintaTexto} />
          </div>
          <div style={{marginTop: 28, fontFamily: SANS, fontSize: 32, color: COR.tintaTexto2, opacity: interpolate(f - tNao - 10, [0, 12], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>
            {T('E a Anthropic apaga do servidor dela em até 30 dias.')}
          </div>
        </div>
        <div style={{flex: '0 0 720px', opacity: tela, transform: `translateY(${(1 - tela) * 40}px)`}}>
          <div style={{border: `3px solid ${COR.tintaTexto3}`, borderRadius: 24, padding: 34, background: COR.tinta2}}>
            <Item inicio={tConversas} icone="janela" texto={T('Conversas')} detalhe="clave.db" />
            <Item inicio={tFicam} icone="memoria" texto={T('Memória')} detalhe={T('arquivos .md')} />
            <Item inicio={tFicam + 8} icone="grafico" texto={T('Histórico de gasto')} detalhe={T('por dia')} />
            <Item inicio={tComputador - 4} icone="chave" texto={T('Sua chave')} detalhe={T('criptografada')} />
          </div>
          <div style={{margin: '0 auto', width: 160, height: 40, background: COR.tintaTexto3, clipPath: 'polygon(20% 0, 80% 0, 100% 100%, 0 100%)', opacity: 0.6}} />
          <div style={{textAlign: 'center', marginTop: 18}}>
            <Rotulo texto={T('no seu computador')} inicio={tComputador} cor={COR.tintaTexto2} tamanho={26} />
          </div>
        </div>
      </AbsoluteFill>
      <Nota texto={T('Fonte: política de dados da Anthropic (privacy.claude.com). Mensagens sinalizadas por violar regras podem ficar mais tempo.')} inicio={tNao} claro={false} />
    </Fundo>
  );
};
