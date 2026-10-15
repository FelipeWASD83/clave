// "Primeiros passos": instalar, a janela de boas-vindas e a primeira conversa.
// Bate com o README (instalação) e com a lição tutoriais/primeira-conversa.md.
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Entra, Fundo, Logo, Passo, Rotulo, Sobe} from '../../componentes/Base';
import {CursorLivre, Pasta} from '../../componentes/Esquema';
import {Icone} from '../../componentes/Icones';
import {Tela, juntar, ponto} from '../../componentes/Tela';
import {useLinha} from '../../linha';
import {COR, MOLA, MONO, SANS} from '../../tema';

const aparece = (f: number, de: number, dur = 10) => interpolate(f - de, [0, dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

// ---------- 1. do download à primeira conversa ----------
export const Abre: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {quando, T} = useLinha();
  const C = 'abre';
  const tDo = quando(C, 'do');
  const tPrimeira = quando(C, 'primeira');
  const tUm = quando(C, 'um');
  const etapas = [
    {n: '1', texto: T('Instalar'), de: tDo},
    {n: '2', texto: T('Boas-vindas'), de: tDo + 12},
    {n: '3', texto: T('Primeira conversa'), de: tPrimeira},
  ];
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{padding: '0 160px', justifyContent: 'center'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 28}}>
          <Logo tamanho={84} inicio={tDo - 6} />
          <Rotulo texto={T('Tutorial')} inicio={tDo - 4} cor={COR.tintaAcao} tamanho={28} />
        </div>
        <div style={{marginTop: 26}}>
          <Sobe texto={T('Primeiros passos')} inicio={tDo} tamanho={140} cor={COR.tintaTexto} />
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 0, marginTop: 90}}>
          {etapas.map((e, i) => {
            const s = spring({frame: f - e.de, fps, config: MOLA, durationInFrames: 16});
            return (
              <div key={e.n} style={{display: 'flex', alignItems: 'center'}}>
                {i > 0 && <div style={{width: 90, height: 3, background: COR.tintaLinha, transform: `scaleX(${s})`, transformOrigin: 'left'}} />}
                <div style={{opacity: s, transform: `translateY(${(1 - s) * 24}px)`, display: 'flex', alignItems: 'center', gap: 18, background: COR.tinta2, border: `1.5px solid ${COR.tintaLinha}`, borderRadius: 50, padding: '18px 34px 18px 18px'}}>
                  <div style={{width: 56, height: 56, borderRadius: 28, background: COR.tintaAcao, color: COR.tinta, display: 'grid', placeItems: 'center', fontFamily: MONO, fontSize: 28, fontWeight: 500}}>{e.n}</div>
                  <div style={{fontFamily: SANS, fontSize: 36, fontWeight: 500, color: COR.tintaTexto}}>{e.texto}</div>
                </div>
              </div>
            );
          })}
        </div>
        <Entra inicio={tUm} distancia={20} estilo={{marginTop: 60}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 14, fontFamily: SANS, fontSize: 32, color: COR.tintaTexto2}}>
            <Icone nome="relogio" tamanho={34} cor={COR.tintaAcao} />
            {T('Em um minuto.')}
          </div>
        </Entra>
      </AbsoluteFill>
    </Fundo>
  );
};

// ---------- 2. instalar: o ZIP, o instalar.bat e o atalho ----------
const ITENS_PASTA = [
  {nome: 'app', pasta: true},
  {nome: 'electron', pasta: true},
  {nome: 'ferramentas', pasta: true},
  {nome: 'modelo-de-pasta', pasta: true},
  {nome: 'servidor', pasta: true},
  {nome: 'tutoriais', pasta: true},
  {nome: 'Clave.bat'},
  {nome: 'instalar.bat'},
  {nome: 'README.md'},
];

export const Instalar: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T} = useLinha();
  const C = 'instalar';
  const tBaixe = quando(C, 'baixe');
  const tExtraia = quando(C, 'extraia');
  const tDois = quando(C, 'dois');
  const tInstalar = quando(C, 'instalar');
  const tPrepara = quando(C, 'prepara');
  const tAtalho = quando(C, 'atalho');
  const passos = [
    T('Python 3.10 ou mais novo (se faltar, instala pelo winget)'),
    T('O ambiente do Clave e as dependências'),
    T('A janela do app: o Electron oficial, conferido pelo SHA-256'),
    T('Os atalhos na área de trabalho e no menu Iniciar'),
  ];
  const linhaBat = {x: 220 + 160, y: 330 + 56 + 10 + 7 * 46 + 23};
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 1')} titulo={T('Instale (uma vez só)')} inicio={tBaixe} claro />
      <Entra inicio={tBaixe + 4} distancia={30} estilo={{position: 'absolute', left: 220, top: 190}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 20, background: '#fbf8f1', border: `2px solid ${COR.linha}`, borderRadius: 18, padding: '20px 28px', width: 700}}>
          <Icone nome="zip" tamanho={46} cor={COR.acao} />
          <div style={{fontFamily: SANS, fontSize: 30, color: COR.texto}}>{T('O ZIP do Clave, baixado do GitHub')}</div>
        </div>
      </Entra>
      <Entra inicio={tExtraia} distancia={40} estilo={{position: 'absolute', left: 220, top: 330}}>
        <Pasta largura={700} caminho={T('Documentos › Clave')} itens={ITENS_PASTA} destaque={{nome: 'instalar.bat', de: tDois - 2}} />
      </Entra>
      <Entra inicio={tPrepara - 4} distancia={40} estilo={{position: 'absolute', left: 1000, top: 330, width: 720}}>
        <div style={{background: COR.tinta, borderRadius: 18, padding: '28px 32px', boxShadow: '0 30px 70px rgba(40,30,15,.25)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 14, fontFamily: MONO, fontSize: 26, color: COR.tintaTexto}}>
            <Icone nome="terminal" tamanho={30} cor={COR.tintaAcao} />
            instalar.bat
          </div>
          <div style={{marginTop: 22, display: 'flex', flexDirection: 'column', gap: 16}}>
            {passos.map((p, i) => {
              const de = tPrepara + i * 10;
              const feito = f >= de + 8;
              return (
                <div key={i} style={{display: 'flex', alignItems: 'flex-start', gap: 14, opacity: aparece(f, de, 6), fontFamily: SANS, fontSize: 25, color: COR.tintaTexto2, lineHeight: 1.35}}>
                  <div style={{flex: 'none', marginTop: 2}}>
                    <Icone nome={feito ? 'certo' : 'relogio'} tamanho={28} cor={feito ? COR.sucessoClaro : COR.tintaTexto3} espessura={2.2} />
                  </div>
                  <span>
                    <span style={{fontFamily: MONO, color: COR.tintaTexto3, marginRight: 10}}>{i + 1}/4</span>
                    {p}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </Entra>
      <Entra inicio={tAtalho} distancia={30} estilo={{position: 'absolute', left: 1000, top: 800}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 26}}>
          <div style={{width: 128, height: 128, borderRadius: 26, background: 'rgba(29,95,102,.10)', border: `2px dashed ${COR.acao}`, display: 'grid', placeItems: 'center'}}>
            <Logo tamanho={84} inicio={tAtalho} />
          </div>
          <div>
            <div style={{fontFamily: SANS, fontSize: 36, fontWeight: 600, color: COR.texto}}>Clave</div>
            <div style={{fontFamily: SANS, fontSize: 26, color: COR.texto3, marginTop: 6}}>{T('O atalho na área de trabalho. É por ele que você abre o Clave.')}</div>
          </div>
        </div>
      </Entra>
      <CursorLivre pontos={[{em: tDois - 14, x: 700, y: 600}, {em: tInstalar - 2, x: linhaBat.x, y: linhaBat.y, clique: true, duplo: true}]} />
    </Fundo>
  );
};

// ---------- 3. a janela de boas-vindas: chave, teto e nome ----------
export const Boas: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'boas';
  const tPrimeira = quando(C, 'primeira');
  const tChave = quando(C, 'chave');
  const tTeto = quando(C, 'teto');
  const tNome = quando(C, 'nome');
  const a = (tela: string, n: string) => alvo(tela, n);
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Passo 2')} titulo={T('A janela de boas-vindas')} inicio={tPrimeira} claro={false} />
      <Tela
        entra={tPrimeira - 8}
        quadros={[
          {tela: 'boas-1-inicio', de: 0},
          {tela: 'boas-2-chave', de: tChave - 2},
          {tela: 'boas-3-teto', de: tTeto - 2},
          {tela: 'boas-4-nome', de: tNome - 2},
        ]}
        focos={[{de: tPrimeira + 6, r: a('boas-2-chave', 'janela'), zoom: 1.28}]}
        cursor={[
          ponto(a('boas-1-inicio', 'comecar'), tChave - 18, false, -80, 40),
          ponto(a('boas-1-inicio', 'comecar'), tChave - 6),
          ponto(a('boas-2-chave', 'campo'), tChave + 8, false, 120, 10),
          ponto(a('boas-2-chave', 'continuar'), tTeto - 6),
          ponto(a('boas-3-teto', 'vinte'), tTeto + 10, false),
          ponto(a('boas-3-teto', 'continuar'), tNome - 6),
        ]}
        marcas={[
          {de: tChave + 2, ate: tTeto - 8, r: a('boas-2-chave', 'campo')},
          {de: tTeto + 4, ate: tNome - 8, r: a('boas-3-teto', 'opcoes')},
          {de: tNome + 4, r: a('boas-4-nome', 'nome')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 4. Nova conversa e o pedido ----------
export const Conversa: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'conversa';
  const tClique = quando(C, 'clique');
  const tEscreva = quando(C, 'escreva');
  const a1 = (n: string) => alvo('conversa-1-inicio', n);
  const a2 = (n: string) => alvo('conversa-2-digitada', n);
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 3')} titulo={T('A primeira conversa')} inicio={tClique} claro />
      <Tela
        entra={tClique - 10}
        quadros={[
          {tela: 'conversa-1-inicio', de: 0},
          {tela: 'conversa-2-digitada', de: tEscreva + 6},
        ]}
        focos={[{de: tEscreva, r: a2('caixa'), zoom: 1.6}]}
        cursor={[ponto(a1('nova'), tClique - 4, false, 120, 120), ponto(a1('nova'), tClique + 6), ponto(a1('caixa'), tEscreva, true, -200, -10)]}
        marcas={[
          {de: tClique + 4, ate: tEscreva - 4, r: a1('nova')},
          {de: tEscreva + 10, r: a2('caixa')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 5. o botão do modelo ----------
export const Modelo: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'modelo';
  const tAntes = quando(C, 'antes');
  const tBotao = quando(C, 'botao');
  const tHaiku = quando(C, 'raicu');
  const tSonnet = quando(C, 'sonnet');
  const tOpus = quando(C, 'opus');
  const tEscolhe = tOpus + 34;
  const m = (n: string) => alvo('conversa-3-modelos', n);
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Passo 3')} titulo={T('Escolha o modelo')} inicio={tAntes} claro={false} />
      <Tela
        entra={tAntes - 10}
        quadros={[
          {tela: 'conversa-2-digitada', de: 0},
          {tela: 'conversa-3-modelos', de: tBotao + 4},
          {tela: 'conversa-4-haiku', de: tEscolhe + 4},
        ]}
        focos={[
          {de: tAntes + 4, r: alvo('conversa-2-digitada', 'caixa'), zoom: 1.6},
          {de: tBotao + 6, r: juntar(m('menu'), m('modelo')), zoom: 1.55},
          {de: tEscolhe + 8, r: alvo('conversa-4-haiku', 'caixa'), zoom: 1.6},
        ]}
        cursor={[
          ponto(m('modelo'), tBotao - 12, false, 60, 60),
          ponto(m('modelo'), tBotao),
          ponto(m('haiku'), tHaiku, false, 80),
          ponto(m('sonnet'), tSonnet, false, 80),
          ponto(m('opus'), tOpus, false, 80),
          ponto(m('haiku'), tEscolhe),
        ]}
        marcas={[
          {de: tBotao - 4, ate: tBotao + 6, r: m('modelo')},
          {de: tHaiku, ate: tSonnet - 2, r: m('haiku')},
          {de: tSonnet, ate: tOpus - 2, r: m('sonnet')},
          {de: tOpus, ate: tEscolhe - 6, r: m('opus')},
          {de: tEscolhe + 10, r: alvo('conversa-4-haiku', 'modelo')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 6. Enter, a resposta e o custo dela ----------
export const Resposta: React.FC = () => {
  const {quando, T, alvo, cena} = useLinha();
  const C = 'resposta';
  const tEnter = quando(C, 'enter');
  const tEmbaixo = quando(C, 'embaixo');
  const tQuanto = quando(C, 'quanto');
  const r = (n: string) => alvo('conversa-6-custo', n);
  const tInicio = cena(C).fala;
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 3')} titulo={T('A resposta e o custo dela')} inicio={tInicio} claro />
      <Tela
        entra={tInicio - 10}
        quadros={[
          {tela: 'conversa-4-haiku', de: 0},
          {tela: 'conversa-6-custo', de: tEnter + 10},
        ]}
        focos={[
          {de: 0, r: alvo('conversa-4-haiku', 'caixa'), zoom: 1.6, dur: 1},
          {de: tEnter + 10, r: null},
          {de: tEmbaixo, r: r('meta'), zoom: 1.8},
        ]}
        cursor={[ponto(alvo('conversa-4-haiku', 'enviar'), tEnter - 8, false, -60, 30), ponto(alvo('conversa-4-haiku', 'enviar'), tEnter)]}
        marcas={[{de: tQuanto - 4, r: r('meta'), folga: 8}]}
      />
    </Fundo>
  );
};

// ---------- 7. o painel "Seu uso" ----------
export const Uso: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'uso';
  const tCom = quando(C, 'com');
  const tSeu = quando(C, 'seu');
  const tTokens = quando(C, 'tokens');
  const tDias = quando(C, 'dias');
  const tMes = quando(C, 'mes');
  const p = (n: string) => alvo('conversa-7-painel-uso', n);
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Com o tempo')} titulo={T('O painel Seu uso')} inicio={tCom} claro={false} />
      <Tela
        entra={tCom - 10}
        quadros={[{tela: 'conversa-7-painel-uso', de: 0}]}
        focos={[{de: tSeu, r: p('painel'), zoom: 1.3}, {de: tTokens - 4, r: p('cartoes'), zoom: 1.45}]}
        marcas={[
          {de: tTokens, ate: tDias - 4, r: p('bloco1')},
          {de: tDias, ate: tMes - 4, r: p('bloco2')},
          {de: tMes, r: p('bloco4')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 8. pronto: e as lições ----------
export const Fecho: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T} = useLinha();
  const C = 'fecho';
  const tPronto = quando(C, 'pronto');
  const tLicoes = quando(C, 'licoes');
  return (
    <Fundo tipo="papel">
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 40}}>
          <Logo tamanho={150} inicio={tPronto} />
          <Sobe texto="Clave" inicio={tPronto + 4} tamanho={180} cor={COR.texto} />
        </div>
        <Entra inicio={tLicoes} distancia={24} estilo={{marginTop: 56}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 18, fontFamily: SANS, fontSize: 36, color: COR.texto, background: '#fbf8f1', border: `2px solid ${COR.linha}`, borderRadius: 50, padding: '18px 38px'}}>
            <Icone nome="livro" tamanho={38} cor={COR.acao} />
            <span>
              <b style={{fontWeight: 600}}>{T('Aprender')}</b>
              <span style={{color: COR.texto3}}>{T(': lições do zero, na barra da esquerda')}</span>
            </span>
          </div>
        </Entra>
      </AbsoluteFill>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 46, textAlign: 'center', fontFamily: SANS, fontSize: 22, color: COR.texto3, opacity: aparece(f, tLicoes, 14)}}>
        {T('O Clave é um app independente, sem ligação com a Anthropic. Claude é marca da Anthropic.')}
      </div>
    </Fundo>
  );
};
