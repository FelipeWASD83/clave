// "Como pegar a chave da API": as cenas. Bate com a lição tutoriais/chave-da-api.md.
// O Console da Anthropic aparece só como esquema genérico (decisão 3 do CLAUDE.md): barras no lugar do layout,
// só os nomes que a lição cita (Billing, API Keys, Create Key) e a legenda "ilustração".
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Entra, Fundo, Logo, Passo, Rotulo, Sobe} from '../../componentes/Base';
import {CursorLivre, Legenda, MenuConsole, Navegador, Traco} from '../../componentes/Esquema';
import {Icone} from '../../componentes/Icones';
import {Tela, juntar, ponto} from '../../componentes/Tela';
import {useLinha} from '../../linha';
import {COR, MOLA, MONO, SANS, SERIFA} from '../../tema';

const CHAVE_FALSA = 'sk-ant-•••••';
const aparece = (f: number, de: number, dur = 10) => interpolate(f - de, [0, dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

const Aviso: React.FC<{texto: string; inicio: number; claro: boolean; icone?: string}> = ({texto, inicio, claro, icone = 'info'}) => (
  <Entra inicio={inicio} distancia={20}>
    <div style={{display: 'flex', alignItems: 'center', gap: 16, fontFamily: SANS, fontSize: 30, color: claro ? COR.texto2 : COR.tintaTexto2}}>
      <Icone nome={icone} tamanho={34} cor={claro ? COR.acao : COR.tintaAcao} />
      {texto}
    </div>
  </Entra>
);

// ---------- 1. a chave liga o Clave à sua conta ----------
export const Abre: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T} = useLinha();
  const C = 'abre';
  const tChave = quando(C, 'chave');
  const tClave = quando(C, 'clave');
  const tConta = quando(C, 'conta');
  const tPegar = quando(C, 'pegar');
  const fio = interpolate(f - tConta, [0, 18], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  const caixa: React.CSSProperties = {background: COR.tinta2, border: `1.5px solid ${COR.tintaLinha}`, borderRadius: 24, padding: '36px 44px', display: 'flex', alignItems: 'center', gap: 26, width: 520};
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{padding: '0 160px', justifyContent: 'center'}}>
        <Rotulo texto={T('Tutorial')} inicio={tChave - 4} cor={COR.tintaAcao} tamanho={28} />
        <div style={{marginTop: 20}}>
          <Sobe texto={T('Sua chave da API')} inicio={tChave} tamanho={128} cor={COR.tintaTexto} />
        </div>
        <div style={{display: 'flex', alignItems: 'center', marginTop: 90}}>
          <Entra inicio={tClave} distancia={30}>
            <div style={caixa}>
              <Logo tamanho={96} inicio={tClave} />
              <div style={{fontFamily: SERIFA, fontSize: 64, color: COR.tintaTexto}}>Clave</div>
            </div>
          </Entra>
          <div style={{flex: 1, position: 'relative', height: 80, margin: '0 -2px'}}>
            <div style={{position: 'absolute', left: 0, top: 39, height: 3, width: `${fio * 100}%`, background: COR.tintaAcao}} />
            <div
              style={{
                position: 'absolute',
                left: '50%',
                top: 8,
                transform: `translateX(-50%) scale(${0.8 + 0.2 * fio})`,
                opacity: fio,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                background: COR.tinta3,
                border: `1.5px solid ${COR.tintaAcao}`,
                borderRadius: 32,
                padding: '10px 22px',
                fontFamily: MONO,
                fontSize: 30,
                color: COR.tintaTexto,
                whiteSpace: 'nowrap',
              }}
            >
              <Icone nome="chave" tamanho={32} cor={COR.tintaAcao} />
              {CHAVE_FALSA}
            </div>
          </div>
          <Entra inicio={tConta} distancia={30}>
            <div style={caixa}>
              <div style={{width: 96, height: 96, borderRadius: 48, background: COR.tinta3, display: 'grid', placeItems: 'center', flex: 'none'}}>
                <Icone nome="usuario" tamanho={54} cor={COR.tintaTexto2} />
              </div>
              <div style={{fontFamily: SANS, fontSize: 36, fontWeight: 500, color: COR.tintaTexto, lineHeight: 1.2}}>{T('Sua conta na Anthropic')}</div>
            </div>
          </Entra>
        </div>
        <div style={{marginTop: 70}}>
          <Aviso texto={T('Leva uns 2 minutos.')} inicio={tPegar} claro={false} icone="relogio" />
        </div>
      </AbsoluteFill>
    </Fundo>
  );
};

// ---------- 2. a conta no Console ----------
export const Conta: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T} = useLinha();
  const C = 'conta';
  const tCrie = quando(C, 'crie');
  const tConsole = quando(C, 'console');
  const tEndereco = quando(C, 'endereco');
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 1')} titulo={T('Crie a sua conta no Console')} inicio={tCrie} claro />
      <Entra inicio={tConsole - 6} distancia={50} estilo={{position: 'absolute', left: 260, top: 190}}>
        <Navegador largura={1400} altura={760} endereco="platform.claude.com" digita={tEndereco - 4} destacaEndereco={tEndereco}>
          <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
            {/* um cartão de entrada genérico: barras no lugar dos textos */}
            <div style={{width: 520, borderRadius: 20, border: `2px solid ${COR.papel3}`, padding: '44px 46px', display: 'flex', flexDirection: 'column', gap: 22, opacity: aparece(f, tEndereco + 24, 12)}}>
              <Traco w={260} h={26} cor={COR.linha} />
              <Traco w={360} />
              <div style={{height: 8}} />
              <div style={{height: 58, borderRadius: 12, border: `2px solid ${COR.papel3}`}} />
              <div style={{height: 58, borderRadius: 12, background: COR.texto2, opacity: 0.85}} />
              <Traco w={200} estilo={{alignSelf: 'center'}} />
            </div>
          </AbsoluteFill>
        </Navegador>
      </Entra>
      <Legenda x={260} y={990} />
    </Fundo>
  );
};

// ---------- 3. crédito em Billing, e o crédito do Max ----------
export const Credito: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {quando, T} = useLinha();
  const C = 'credito';
  const tBilling = quando(C, 'billing');
  const tCada = quando(C, 'cada');
  const tMax = quando(C, 'max');
  const tPlano = quando(C, 'plano');
  const tAtive = quando(C, 'ative');
  const saldo = spring({frame: f - (tBilling + 14), fps, config: MOLA, durationInFrames: 24});
  const gasta = interpolate(f - tCada, [0, 40], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Passo 2')} titulo={T('Ponha crédito')} inicio={tBilling} claro={false} />
      <Entra inicio={tBilling - 4} distancia={50} estilo={{position: 'absolute', left: 160, top: 190}}>
        <Navegador largura={980} altura={700} endereco="platform.claude.com">
          <div style={{display: 'flex', height: '100%'}}>
            <MenuConsole itens={[{nome: 'Billing', posicao: 2, ativo: tBilling}, {nome: 'API Keys', posicao: 4}]} />
            <div style={{flex: 1, padding: '40px 44px', display: 'flex', flexDirection: 'column', gap: 26}}>
              <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 40, color: COR.texto}}>Billing</div>
              <div style={{borderRadius: 18, border: `2px solid ${COR.papel3}`, padding: '28px 30px', display: 'flex', flexDirection: 'column', gap: 18}}>
                <Traco w={160} />
                <div style={{height: 22, borderRadius: 11, background: COR.papel3, overflow: 'hidden'}}>
                  <div style={{height: '100%', width: `${(saldo * (1 - 0.06 * gasta)) * 100}%`, background: COR.acao, borderRadius: 11}} />
                </div>
                <div style={{display: 'flex', alignItems: 'center', gap: 14, alignSelf: 'flex-start', marginTop: 6, background: COR.acao, color: COR.papel, borderRadius: 12, padding: '12px 22px', fontFamily: SANS, fontWeight: 600, fontSize: 26}}>
                  <Icone nome="mais" tamanho={26} cor={COR.papel} espessura={2.4} />
                  {T('crédito')}
                </div>
              </div>
              <Traco w={420} />
              <Traco w={300} />
            </div>
          </div>
        </Navegador>
      </Entra>
      <Legenda x={160} y={920} claro={false} />
      <div style={{position: 'absolute', left: 1200, top: 190, width: 600}}>
        <Entra inicio={tCada} distancia={24}>
          <div style={{fontFamily: SANS, fontSize: 32, color: COR.tintaTexto2, lineHeight: 1.4}}>{T('Cada resposta desconta um pouquinho do crédito.')}</div>
        </Entra>
        <Entra inicio={tMax} distancia={40} estilo={{marginTop: 50}}>
          <div style={{background: COR.tinta2, border: `1.5px solid ${COR.tintaLinha}`, borderRadius: 22, padding: '34px 38px'}}>
            <div style={{fontFamily: SERIFA, fontSize: 46, color: COR.tintaTexto}}>{T('Assina o Max?')}</div>
            <div style={{marginTop: 18, fontFamily: SANS, fontSize: 28, color: COR.tintaTexto2, lineHeight: 1.45, opacity: aparece(f, tPlano)}}>
              {T('O plano já vem com crédito mensal na API:')}
              <div style={{display: 'flex', gap: 14, marginTop: 14, fontFamily: MONO, fontSize: 26}}>
                <span style={{background: COR.tinta3, borderRadius: 10, padding: '6px 14px', color: COR.tintaTexto}}>{T('US$ 100 no Max 5x')}</span>
                <span style={{background: COR.tinta3, borderRadius: 10, padding: '6px 14px', color: COR.tintaTexto}}>{T('US$ 200 no Max 20x')}</span>
              </div>
            </div>
            <div style={{marginTop: 26, opacity: aparece(f, tAtive)}}>
              <div style={{fontFamily: SANS, fontSize: 24, color: COR.tintaTexto3}}>{T('Para ativar:')}</div>
              <div style={{marginTop: 8, fontFamily: MONO, fontSize: 25, color: COR.tintaAcao}}>claude.ai › Settings › Billing › API credits</div>
              <div style={{marginTop: 18, fontFamily: SANS, fontSize: 23, color: COR.tintaTexto3}}>{T('O crédito do plano não acumula de um mês para o outro.')}</div>
            </div>
          </div>
        </Entra>
      </div>
    </Fundo>
  );
};

// ---------- 4. API Keys > Create Key, com um nome ----------
export const Criar: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {quando, T} = useLinha();
  const C = 'criar';
  const tMenu = quando(C, 'menu');
  const tKeys = quando(C, 'apikeys');
  const tCreate = quando(C, 'create');
  const tNome = quando(C, 'nome');
  const janela = spring({frame: f - (tCreate + 6), fps, config: MOLA, durationInFrames: 16});
  const nome = 'Clave';
  const letras = Math.round(interpolate(f - tNome, [4, 16], [0, nome.length], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  // posições no quadro (o navegador fica em left 260, top 190; menu de 280 de largura; barra de 62)
  const itemKeys = {x: 354, y: 566};
  const botao = {x: 260 + 1400 - 150, y: 190 + 62 + 66};
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 3')} titulo={T('Crie a chave')} inicio={tMenu} claro />
      <Entra inicio={tMenu - 6} distancia={50} estilo={{position: 'absolute', left: 260, top: 190}}>
        <Navegador largura={1400} altura={760} endereco="platform.claude.com">
          <div style={{display: 'flex', height: '100%'}}>
            <MenuConsole itens={[{nome: 'Billing', posicao: 2}, {nome: 'API Keys', posicao: 4, ativo: tKeys}]} />
            <div style={{flex: 1, padding: '40px 44px', display: 'flex', flexDirection: 'column', gap: 24, opacity: aparece(f, tKeys + 4, 8)}}>
              <div style={{display: 'flex', alignItems: 'center'}}>
                <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 40, color: COR.texto}}>API Keys</div>
                <div
                  style={{
                    marginLeft: 'auto',
                    background: f >= tCreate ? COR.acao : COR.texto2,
                    color: COR.papel,
                    borderRadius: 12,
                    padding: '14px 26px',
                    fontFamily: SANS,
                    fontWeight: 600,
                    fontSize: 26,
                    transform: `scale(${interpolate(f - tCreate, [0, 3, 9], [1, 0.94, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})})`,
                  }}
                >
                  Create Key
                </div>
              </div>
              {[0, 1].map((i) => (
                <div key={i} style={{display: 'flex', alignItems: 'center', gap: 30, padding: '20px 0', borderBottom: `2px solid ${COR.papel3}`}}>
                  <Traco w={170} />
                  <Traco w={220} cor={COR.papel2} />
                  <Traco w={120} cor={COR.papel2} estilo={{marginLeft: 'auto'}} />
                </div>
              ))}
            </div>
            {/* a janela de criar: só o campo do nome */}
            <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', background: `rgba(40,30,15,${0.18 * janela})`, opacity: janela}}>
              <div style={{width: 620, background: '#fdfbf6', borderRadius: 20, border: `2px solid ${COR.linha}`, padding: '38px 42px', transform: `translateY(${(1 - janela) * 30}px)`, boxShadow: '0 30px 60px rgba(40,30,15,.2)'}}>
                <div style={{fontFamily: SANS, fontWeight: 600, fontSize: 34, color: COR.texto}}>Create Key</div>
                <Traco w={240} estilo={{marginTop: 26}} />
                <div style={{marginTop: 14, height: 62, borderRadius: 12, border: `2px solid ${f >= tNome ? COR.acao : COR.linha}`, display: 'flex', alignItems: 'center', padding: '0 20px', fontFamily: SANS, fontSize: 30, color: COR.texto}}>
                  {nome.slice(0, letras)}
                  {f >= tNome && letras < nome.length + 1 && Math.floor(f / 8) % 2 === 0 && <span style={{width: 2, height: 30, background: COR.texto, marginLeft: 2}} />}
                </div>
                <div style={{display: 'flex', justifyContent: 'flex-end', gap: 14, marginTop: 30}}>
                  <Traco w={110} h={48} cor={COR.papel2} />
                  <Traco w={140} h={48} cor={COR.texto2} />
                </div>
              </div>
            </AbsoluteFill>
          </div>
        </Navegador>
      </Entra>
      <Legenda x={260} y={990} />
      <CursorLivre
        pontos={[
          {em: tMenu + 10, x: 900, y: 600},
          {em: tKeys, x: itemKeys.x, y: itemKeys.y, clique: true},
          {em: tCreate, x: botao.x, y: botao.y, clique: true},
          {em: tNome, x: 960, y: 620, clique: true},
        ]}
      />
    </Fundo>
  );
};

// ---------- 5. copiar a chave (sk-ant-, inteira uma vez só) ----------
export const Copiar: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T} = useLinha();
  const C = 'copiar';
  const tCopie = quando(C, 'copie');
  const tComeca = quando(C, 'comeca');
  const tUma = quando(C, 'uma');
  const tPerdeu = quando(C, 'perdeu');
  const sublinha = interpolate(f - tComeca, [0, 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const tClique = tCopie + 20;
  const copiado = f >= tClique + 4;
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Passo 4')} titulo={T('Copie a chave')} inicio={tCopie - 6} claro={false} x={260} />
      <Entra inicio={tCopie - 8} distancia={40} estilo={{position: 'absolute', left: 260, top: 300, width: 1400}}>
        <div style={{background: COR.tinta2, border: `1.5px solid ${COR.tintaLinha}`, borderRadius: 26, padding: '50px 56px'}}>
          <div style={{fontFamily: SANS, fontSize: 28, color: COR.tintaTexto3}}>{T('Sua chave nova')}</div>
          <div style={{display: 'flex', alignItems: 'center', gap: 24, marginTop: 20}}>
            <div style={{flex: 1, height: 96, borderRadius: 16, background: COR.tinta3, display: 'flex', alignItems: 'center', padding: '0 32px', fontFamily: MONO, fontSize: 46, color: COR.tintaTexto, position: 'relative'}}>
              <span style={{position: 'relative'}}>
                sk-ant-
                <span style={{position: 'absolute', left: 0, right: 0, bottom: -8, height: 5, borderRadius: 3, background: COR.tintaAcao, transform: `scaleX(${sublinha})`, transformOrigin: 'left'}} />
              </span>
              <span style={{color: COR.tintaTexto2}}>{'•'.repeat(22)}</span>
            </div>
            <div
              style={{
                width: 96,
                height: 96,
                borderRadius: 16,
                background: copiado ? COR.tintaAcao : COR.tinta3,
                display: 'grid',
                placeItems: 'center',
                transform: `scale(${interpolate(f - tClique, [0, 3, 9], [1, 0.9, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})})`,
              }}
            >
              <Icone nome={copiado ? 'certo' : 'copiar'} tamanho={44} cor={copiado ? COR.tinta : COR.tintaTexto} espessura={2.2} />
            </div>
          </div>
          <div style={{marginTop: 42, display: 'flex', flexDirection: 'column', gap: 22}}>
            <Aviso texto={T('Ela começa com sk-ant-.')} inicio={tComeca} claro={false} icone="chave" />
            <Aviso texto={T('Só aparece inteira uma vez: copie agora.')} inicio={tUma} claro={false} icone="alerta" />
            <Aviso texto={T('Perdeu? É só criar outra.')} inicio={tPerdeu} claro={false} icone="repetir" />
          </div>
        </div>
      </Entra>
      <Legenda x={260} y={990} claro={false} />
      <CursorLivre pontos={[{em: tCopie + 8, x: 1300, y: 700}, {em: tCopie + 20, x: 1560, y: 452, clique: true}]} />
    </Fundo>
  );
};

// ---------- 6. colar no Clave: Configurações > Conta e chave > Conferir e salvar ----------
export const Colar: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'colar';
  const tNo = quando(C, 'no');
  const tConfig = quando(C, 'config');
  const tConta = quando(C, 'conta');
  const tCole = quando(C, 'cole');
  const tConferir = quando(C, 'conferir');
  const tCripto = quando(C, 'cripto');
  const a0 = (n: string) => alvo('conta-0-antes', n);
  const a1 = (n: string) => alvo('conta-1-vazia', n);
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 5')} titulo={T('Cole no Clave')} inicio={tNo} claro />
      <Tela
        entra={tNo - 8}
        quadros={[
          {tela: 'conta-0-antes', de: 0},
          {tela: 'conta-1-vazia', de: tConfig + 6},
          {tela: 'conta-2-colada', de: tCole + 4},
          {tela: 'conta-3-salva', de: tConferir + 8},
        ]}
        focos={[
          {de: tCole - 4, r: juntar(a1('campo'), a1('salvar'))},
          {de: tCripto, r: alvo('conta-3-salva', 'salva'), zoom: 1.4},
        ]}
        cursor={[
          ponto(a0('configuracoes'), tConfig - 10, false, 40, -60),
          ponto(a0('configuracoes'), tConfig),
          ponto(a1('aba'), tConta),
          ponto(a1('campo'), tCole),
          ponto(a1('salvar'), tConferir),
        ]}
        marcas={[
          {de: tConfig - 2, ate: tConta - 4, r: a0('configuracoes')},
          {de: tConta, ate: tCole - 6, r: a1('aba')},
          {de: tCole, ate: tConferir - 4, r: a1('campo')},
          {de: tConferir, ate: tConferir + 18, r: a1('salvar')},
          {de: tCripto, r: alvo('conta-3-salva', 'salva')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 7. o teto em Limite de gasto ----------
export const Teto: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'teto';
  const tLimite = quando(C, 'limite');
  const tTeto = quando(C, 'teto');
  const tChegou = quando(C, 'chegou');
  const a = (n: string) => alvo('limite-1', n);
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Passo 6')} titulo={T('Defina um teto por mês')} inicio={tLimite} claro={false} />
      <Tela
        entra={tLimite - 10}
        quadros={[
          {tela: 'conta-3-salva', de: 0},
          {tela: 'limite-1', de: tLimite + 6},
        ]}
        focos={[{de: tTeto - 2, r: juntar(a('teto'), a('ao_atingir')), zoom: 1.6}]}
        cursor={[ponto(a('aba'), tLimite - 8, false, 60, 40), ponto(a('aba'), tLimite), ponto(a('teto'), tTeto, true, -120, 0)]}
        marcas={[
          {de: tLimite, ate: tTeto - 4, r: a('aba')},
          {de: tTeto + 6, ate: tChegou - 4, r: a('teto')},
          {de: tChegou, r: a('ao_atingir')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 8. as regras de ouro ----------
export const Regras: React.FC = () => {
  const {quando, T} = useLinha();
  const C = 'regras';
  const tDuas = quando(C, 'duas');
  const tNunca = quando(C, 'nunca');
  const tVazou = quando(C, 'vazou');
  const tApague = quando(C, 'apague');
  const tOutra = quando(C, 'outra');
  const Cartao: React.FC<{inicio: number; icone: string; titulo: string; children?: React.ReactNode}> = ({inicio, icone, titulo, children}) => (
    <Entra inicio={inicio} distancia={40} estilo={{flex: 1}}>
      <div style={{background: '#fbf8f1', border: `2px solid ${COR.linha}`, borderRadius: 26, padding: '48px 50px', minHeight: 420}}>
        <div style={{width: 96, height: 96, borderRadius: 22, background: COR.acaoSuave, display: 'grid', placeItems: 'center'}}>
          <Icone nome={icone} tamanho={54} cor={COR.acao} />
        </div>
        <div style={{fontFamily: SERIFA, fontSize: 52, fontWeight: 500, color: COR.texto, marginTop: 30, lineHeight: 1.12, letterSpacing: '-0.01em'}}>{titulo}</div>
        {children}
      </div>
    </Entra>
  );
  return (
    <Fundo tipo="papel">
      <AbsoluteFill style={{padding: '0 160px', justifyContent: 'center'}}>
        <Sobe texto={T('Duas regras de ouro')} inicio={tDuas} tamanho={86} cor={COR.texto} />
        <div style={{display: 'flex', gap: 50, marginTop: 70}}>
          <Cartao inicio={tNunca} icone="olhoFechado" titulo={T('Nunca mostre a chave para ninguém.')}>
            <div style={{fontFamily: SANS, fontSize: 30, color: COR.texto3, marginTop: 22, lineHeight: 1.4}}>{T('Quem tem a chave gasta o seu crédito.')}</div>
          </Cartao>
          <Cartao inicio={tVazou} icone="alerta" titulo={T('Vazou? Troque.')}>
            <div style={{display: 'flex', flexDirection: 'column', gap: 16, marginTop: 26}}>
              <Entra inicio={tApague} distancia={16}>
                <div style={{display: 'flex', alignItems: 'center', gap: 14, fontFamily: SANS, fontSize: 30, color: COR.texto2}}>
                  <Icone nome="lixo" tamanho={32} cor={COR.erro} /> {T('Apague no Console (API Keys)')}
                </div>
              </Entra>
              <Entra inicio={tOutra} distancia={16}>
                <div style={{display: 'flex', alignItems: 'center', gap: 14, fontFamily: SANS, fontSize: 30, color: COR.texto2}}>
                  <Icone nome="mais" tamanho={32} cor={COR.acao} /> {T('Crie outra e cole no Clave')}
                </div>
              </Entra>
            </div>
          </Cartao>
        </div>
      </AbsoluteFill>
    </Fundo>
  );
};

// ---------- 9. pronto ----------
export const Fecho: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T} = useLinha();
  const C = 'fecho';
  const tPronto = quando(C, 'pronto');
  const tAgora = quando(C, 'agora');
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 40}}>
          <Logo tamanho={150} inicio={tPronto} />
          <Sobe texto="Clave" inicio={tPronto + 4} tamanho={180} cor={COR.tintaTexto} />
        </div>
        <Entra inicio={tPronto + 10} distancia={20} estilo={{marginTop: 40}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 14, fontFamily: MONO, fontSize: 30, color: COR.tintaTexto, border: `1.5px solid ${COR.tintaLinha}`, background: COR.tinta2, borderRadius: 40, padding: '12px 28px'}}>
            <Icone nome="chave" tamanho={30} cor={COR.tintaAcao} />
            {CHAVE_FALSA}
            <Icone nome="certo" tamanho={30} cor={COR.sucessoClaro} espessura={2.4} />
          </div>
        </Entra>
        <div style={{marginTop: 50}}>
          <Sobe texto={T('Agora é só conversar.')} inicio={tAgora} tamanho={64} peso={400} cor={COR.tintaTexto2} italico passo={2} />
        </div>
      </AbsoluteFill>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 46, textAlign: 'center', fontFamily: SANS, fontSize: 22, color: COR.tintaTexto3, opacity: aparece(f, tAgora, 14)}}>
        {T('O Clave é um app independente, sem ligação com a Anthropic. Claude é marca da Anthropic.')}
      </div>
    </Fundo>
  );
};
