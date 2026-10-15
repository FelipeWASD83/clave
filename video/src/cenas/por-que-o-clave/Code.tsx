// Cena 7: "No modo Code, o Claude trabalha nas suas pastas: planilhas, arquivos, scripts. Você aprova cada mudança,
// e pode desfazer. Com as rotinas, ele trabalha sozinho, no horário que você escolher."
import {useLinha} from '../../linha';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Entra, Fundo, Rotulo, Sobe} from '../../componentes/Base';
import {Icone} from '../../componentes/Icones';
import {COR, MOLA, MONO, SANS} from '../../tema';

const C = 'code';

const Arquivo: React.FC<{inicio: number; icone: string; nome: string; o: string}> = ({inicio, icone, nome, o}) => (
  <Entra inicio={inicio} distancia={24}>
    <div style={{display: 'flex', alignItems: 'center', gap: 20, padding: '16px 24px', borderRadius: 14, background: COR.tinta2, border: `1.5px solid ${COR.tintaLinha}`, marginBottom: 14}}>
      <Icone nome={icone} tamanho={38} cor={COR.tintaAcao} />
      <div style={{fontFamily: MONO, fontSize: 30, color: COR.tintaTexto}}>{nome}</div>
      <div style={{marginLeft: 'auto', fontFamily: SANS, fontSize: 24, color: COR.tintaTexto3}}>{o}</div>
    </div>
  </Entra>
);

const Botao: React.FC<{texto: string; tipo: 'primario' | 'normal' | 'leve'; apertado?: number; icone?: string}> = ({texto, tipo, apertado, icone}) => {
  const f = useCurrentFrame();
  const {T} = useLinha();
  const a = apertado === undefined ? 1 : interpolate(f - apertado, [0, 4, 10], [1, 0.93, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const feito = apertado !== undefined && f >= apertado + 4;
  return (
    <div
      style={{
        fontFamily: SANS,
        fontWeight: tipo === 'primario' ? 600 : 500,
        fontSize: 27,
        padding: '13px 24px',
        borderRadius: 11,
        transform: `scale(${a})`,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: tipo === 'primario' ? (feito ? COR.sucesso : COR.acao) : tipo === 'normal' ? COR.papel2 : 'transparent',
        color: tipo === 'primario' ? COR.papel : COR.texto2,
        border: tipo === 'normal' ? `1.5px solid ${COR.linha}` : '1.5px solid transparent',
      }}
    >
      {icone && <Icone nome={feito && tipo === 'primario' ? 'certo' : icone} tamanho={26} cor="currentColor" espessura={2.2} />}
      {feito && tipo === 'primario' ? T('Permitido') : texto}
    </div>
  );
};

export const Code: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {quando, T} = useLinha();
  const tNo = quando(C, 'no');
  const tTrabalha = quando(C, 'trabalha');
  const tPlanilhas = quando(C, 'planilhas');
  const tArquivos = quando(C, 'arquivos');
  const tScripts = quando(C, 'scripts');
  const tVoce = quando(C, 'voce');
  const tAprova = quando(C, 'aprova');
  const tDesfazer = quando(C, 'desfazer');
  const tRotinas = quando(C, 'rotinas');
  const tHorario = quando(C, 'horario');
  const sai = spring({frame: f - (tRotinas - 6), fps, config: MOLA, durationInFrames: 16});
  const rotina = spring({frame: f - tRotinas, fps, config: MOLA, durationInFrames: 18});
  const liga = interpolate(f - tHorario, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{flexDirection: 'row', alignItems: 'center', padding: '0 140px', gap: 100}}>
        <div style={{flex: '0 0 700px'}}>
          <Rotulo texto={T('Modo Code')} inicio={tNo} cor={COR.tintaAcao} tamanho={28} />
          <div style={{marginTop: 22}}>
            <Sobe texto={T('O Claude trabalha nas suas pastas.')} inicio={tTrabalha} tamanho={84} cor={COR.tintaTexto} />
          </div>
          <div style={{marginTop: 50}}>
            <Arquivo inicio={tPlanilhas} icone="grafico" nome={T('vendas.xlsx')} o={T('fórmulas e gráfico')} />
            <Arquivo inicio={tArquivos} icone="pasta" nome={T('contratos/')} o={T('organiza e renomeia')} />
            <Arquivo inicio={tScripts} icone="terminal" nome="backup.ps1" o={T('script para repetir')} />
          </div>
        </div>

        <div style={{flex: 1, position: 'relative', height: 800}}>
          {/* o cartão de aprovação, como no app */}
          <div style={{position: 'absolute', inset: 0, opacity: 1 - sai}}>
          <Entra inicio={tVoce} distancia={50}>
            <div style={{background: '#fbf8f1', borderRadius: 22, border: `2px solid ${COR.linha}`, boxShadow: '0 30px 80px rgba(0,0,0,.45)', overflow: 'hidden', transform: `translateY(${-sai * 40}px)`}}>
              <div style={{padding: '28px 36px', fontFamily: SANS, fontSize: 34, color: COR.texto, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 16}}>
                <Icone nome="arquivo" tamanho={36} cor={COR.acao} />
                {T('Quer mudar')} <span style={{fontFamily: MONO, fontWeight: 500}}>{T('vendas.xlsx')}</span>
              </div>
              <div style={{fontFamily: MONO, fontSize: 26, borderTop: `1.5px solid ${COR.linha}`, borderBottom: `1.5px solid ${COR.linha}`}}>
                <div style={{background: '#f3dcd5', color: COR.erro, padding: '12px 36px'}}>− E2  Total</div>
                <div style={{background: '#dcead9', color: COR.sucesso, padding: '12px 36px'}}>{T('+ E2  Total com frete')}</div>
                <div style={{background: '#dcead9', color: COR.sucesso, padding: '12px 36px'}}>+ E3  =C3*D3+F3</div>
              </div>
              <div style={{display: 'flex', gap: 14, padding: '24px 36px'}}>
                <Botao texto={T('Permitir')} tipo="primario" apertado={tAprova} icone="certo" />
                <Botao texto={T('Mais opções')} tipo="normal" />
                <Botao texto={T('Recusar')} tipo="leve" />
              </div>
            </div>
            <Entra inicio={tDesfazer - 2} distancia={20} estilo={{marginTop: 26}}>
              <div style={{display: 'inline-flex'}}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    fontFamily: SANS,
                    fontSize: 28,
                    color: COR.tintaTexto,
                    border: `1.5px solid ${COR.tintaLinha}`,
                    borderRadius: 12,
                    padding: '14px 24px',
                    background: COR.tinta2,
                  }}
                >
                  <Icone nome="desfazer" tamanho={30} cor={COR.tintaAcao} />
                  {T('Desfazer mudanças')}
                </div>
              </div>
            </Entra>
          </Entra>
          </div>

          {/* a rotina */}
          <div style={{position: 'absolute', inset: 0, top: 80, opacity: rotina, transform: `translateY(${(1 - rotina) * 60}px)`}}>
            <div style={{background: '#fbf8f1', borderRadius: 22, border: `2px solid ${COR.linha}`, boxShadow: '0 30px 80px rgba(0,0,0,.45)', padding: '36px 40px'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
                <div style={{width: 76, height: 76, borderRadius: 18, background: COR.acaoSuave, display: 'grid', placeItems: 'center'}}>
                  <Icone nome="calendario" tamanho={44} cor={COR.acao} />
                </div>
                <div>
                  <Rotulo texto={T('Rotina')} inicio={tRotinas} cor={COR.texto3} tamanho={20} />
                  <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 38, color: COR.texto, marginTop: 2}}>{T('Resumo da semana')}</div>
                </div>
                <div style={{marginLeft: 'auto', width: 92, height: 50, borderRadius: 25, background: liga > 0.5 ? COR.acao : COR.papel3, position: 'relative'}}>
                  <div style={{position: 'absolute', top: 5, left: 5 + liga * 42, width: 40, height: 40, borderRadius: 20, background: '#fff'}} />
                </div>
              </div>
              <div style={{marginTop: 28, fontFamily: SANS, fontSize: 30, color: COR.texto2, lineHeight: 1.4}}>
                {T('Leia as planilhas novas da pasta Vendas e me diga o que precisa da minha atenção.')}
              </div>
              <div style={{display: 'flex', gap: 16, marginTop: 28, fontFamily: MONO, fontSize: 26}}>
                <div style={{background: f >= tHorario ? COR.acaoSuave : COR.papel2, color: COR.texto, borderRadius: 10, padding: '10px 18px'}}>{T('toda segunda, 08:00')}</div>
                <div style={{background: COR.papel2, color: COR.texto3, borderRadius: 10, padding: '10px 18px'}}>{T('teto US$ 0,50')}</div>
              </div>
              <div style={{marginTop: 22, fontFamily: SANS, fontSize: 24, color: COR.texto3}}>{T('Roda até com o Clave fechado, pelo Agendador de Tarefas do Windows.')}</div>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </Fundo>
  );
};
