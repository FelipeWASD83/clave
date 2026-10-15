// "Primeira automação": arrumar a pasta Downloads no modo Code.
// Bate com as lições tutoriais/primeira-automacao.md e modo-code.md.
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {Entra, Fundo, Logo, Passo, Rotulo, Sobe} from '../../componentes/Base';
import {Icone} from '../../componentes/Icones';
import {Tela, juntar, ponto} from '../../componentes/Tela';
import {useLinha} from '../../linha';
import {COR, MONO, SANS} from '../../tema';

const aparece = (f: number, de: number, dur = 10) => interpolate(f - de, [0, dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

// os arquivos soltos da abertura (os mesmos da pasta de exemplo dos prints) e a subpasta de cada um
const SOLTOS: Record<string, [string, number][]> = {
  'pt-BR': [
    ['boleto-outubro.pdf', 0], ['foto-praia.jpg', 1], ['gastos-2026.xlsx', 2], ['setup-impressora.exe', 3], ['curriculo.docx', 0],
    ['IMG_2041.jpg', 1], ['fotos-viagem.zip', 4], ['lista-convidados.csv', 2], ['receita-bolo.txt', 0], ['convite.png', 1],
    ['musica.mp3', 4], ['instalador-zoom.msi', 3],
  ],
  en: [
    ['invoice-october.pdf', 0], ['beach-photo.jpg', 1], ['expenses-2026.xlsx', 2], ['printer-setup.exe', 3], ['resume.docx', 0],
    ['IMG_2041.jpg', 1], ['trip-photos.zip', 4], ['guest-list.csv', 2], ['cake-recipe.txt', 0], ['invitation.png', 1],
    ['song.mp3', 4], ['zoom-installer.msi', 3],
  ],
};
const SUBPASTAS = ['Documentos', 'Imagens', 'Planilhas', 'Instaladores', 'Outros'];
const ICONES = ['arquivo', 'imagem', 'grafico', 'instalador', 'zip'];

// ---------- 1. a pasta bagunçada vira cinco subpastas ----------
export const Abre: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T, lingua} = useLinha();
  const C = 'abre';
  const tSua = quando(C, 'sua');
  const tArrumar = quando(C, 'arrumar');
  const tSem = quando(C, 'sem');
  const soltos = SOLTOS[lingua];
  const X0 = 1000;
  const Y0 = 190;
  const tileW = 150;
  const gap = 18;
  const tileX = (i: number) => X0 + i * (tileW + gap);
  const tileY = 760;
  const conta = [0, 0, 0, 0, 0];
  return (
    <Fundo tipo="tinta">
      <AbsoluteFill style={{padding: '0 0 0 160px', justifyContent: 'center'}}>
        <div style={{width: 760}}>
          <Rotulo texto={T('Tutorial')} inicio={tSua - 4} cor={COR.tintaAcao} tamanho={28} />
          <div style={{marginTop: 20}}>
            <Sobe texto={T('Primeira automação')} inicio={tSua} tamanho={112} cor={COR.tintaTexto} />
          </div>
          <div style={{marginTop: 30}}>
            <Sobe texto={T('Arrumar a pasta Downloads, sem risco de perder nada.')} inicio={tArrumar} tamanho={48} peso={400} cor={COR.tintaTexto2} italico passo={2} />
          </div>
        </div>
      </AbsoluteFill>
      {SUBPASTAS.map((nome, i) => (
        <div key={nome} style={{position: 'absolute', left: tileX(i), top: tileY, width: tileW, opacity: aparece(f, tSem - 16 + i * 3), textAlign: 'center'}}>
          <div style={{height: 120, borderRadius: 18, background: COR.tinta2, border: `1.5px solid ${COR.tintaLinha}`, display: 'grid', placeItems: 'center'}}>
            <Icone nome="pasta" tamanho={58} cor="#c9a25a" />
          </div>
          <div style={{marginTop: 12, fontFamily: SANS, fontSize: 22, color: COR.tintaTexto2}}>{T(nome)}</div>
        </div>
      ))}
      {soltos.map(([nome, destino], i) => {
        const col = i % 3;
        const lin = Math.floor(i / 3);
        const x = X0 + col * 270 + (lin % 2 ? 40 : 0);
        const y = Y0 + lin * 120 + ((i * 37) % 30);
        const giro = ((i * 53) % 13) - 6;
        const nasce = aparece(f, tArrumar - 10 + i * 2, 8);
        const vai = interpolate(f - (tSem + i * 2), [0, 16], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
        if (vai >= 1) conta[destino] += 1;
        const dx = tileX(destino) + tileW / 2 - 110;
        const dy = tileY + 40;
        return (
          <div
            key={nome}
            style={{
              position: 'absolute',
              left: x + (dx - x) * vai,
              top: y + (dy - y) * vai,
              transform: `rotate(${giro * (1 - vai)}deg) scale(${1 - 0.6 * vai})`,
              opacity: nasce * (1 - vai * vai),
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              background: COR.tinta3,
              border: `1.5px solid ${COR.tintaLinha}`,
              borderRadius: 12,
              padding: '10px 16px',
              fontFamily: MONO,
              fontSize: 21,
              color: COR.tintaTexto,
              whiteSpace: 'nowrap',
            }}
          >
            <Icone nome={ICONES[destino]} tamanho={24} cor={COR.tintaAcao} />
            {nome}
          </div>
        );
      })}
      {SUBPASTAS.map((nome, i) =>
        conta[i] ? (
          <div key={`n-${nome}`} style={{position: 'absolute', left: tileX(i) + tileW - 30, top: tileY - 14, width: 40, height: 40, borderRadius: 20, background: COR.tintaAcao, color: COR.tinta, display: 'grid', placeItems: 'center', fontFamily: MONO, fontSize: 22, fontWeight: 500}}>
            {conta[i]}
          </div>
        ) : null,
      )}
    </Fundo>
  );
};

// ---------- 2. Novo trabalho no Code e a pasta ----------
export const Novo: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'novo';
  const tBarra = quando(C, 'barra');
  const tNovo = quando(C, 'novo');
  const tEscolha = quando(C, 'escolha');
  const tDownloads = quando(C, 'downloads');
  const a0 = (n: string) => alvo('code-0-antes', n);
  const a1 = (n: string) => alvo('code-1-inicio', n);
  const a2 = (n: string) => alvo('code-2-menu', n);
  const a3 = (n: string) => alvo('code-3-pasta', n);
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 1')} titulo={T('Novo trabalho no Code')} inicio={tBarra} claro />
      <Tela
        entra={tBarra - 10}
        quadros={[
          {tela: 'code-0-antes', de: 0},
          {tela: 'code-1-inicio', de: tNovo + 6},
          {tela: 'code-2-menu', de: tEscolha + 10},
          {tela: 'code-3-pasta', de: tDownloads + 4},
        ]}
        focos={[
          {de: tEscolha - 2, r: juntar(a1('escolher'), a2('outra')), zoom: 1.5},
          {de: tDownloads + 6, r: juntar(a3('selo'), a3('caixa')), zoom: 1.45},
        ]}
        cursor={[
          ponto(a0('novo'), tBarra + 4, false, 160, 140),
          ponto(a0('novo'), tNovo + 2),
          ponto(a1('escolher'), tEscolha + 6),
          ponto(a2('outra'), tDownloads - 4),
        ]}
        marcas={[
          {de: tNovo - 2, ate: tEscolha - 6, r: a0('novo')},
          {de: tEscolha + 2, ate: tDownloads - 10, r: a1('escolher')},
          {de: tDownloads - 8, ate: tDownloads + 2, r: a2('outra')},
          {de: tDownloads + 10, r: a3('selo')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 3. a permissão em Perguntar ----------
export const Permissao: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'permissao';
  const tDeixe = quando(C, 'deixe');
  const tPerguntar = quando(C, 'perguntar');
  const tLe = quando(C, 'le');
  const a3 = (n: string) => alvo('code-3-pasta', n);
  const b = (n: string) => alvo('code-3b-permissoes', n);
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Passo 2')} titulo={T('A permissão em Perguntar')} inicio={tDeixe} claro={false} />
      <Tela
        entra={tDeixe - 10}
        quadros={[
          {tela: 'code-3-pasta', de: 0},
          {tela: 'code-3b-permissoes', de: tPerguntar + 6},
        ]}
        focos={[
          {de: 0, r: juntar(a3('selo'), a3('caixa')), zoom: 1.45, dur: 1},
          {de: tDeixe + 4, r: a3('permissao'), zoom: 2},
          {de: tPerguntar + 8, r: juntar(b('menu'), b('permissao')), zoom: 1.6},
        ]}
        cursor={[ponto(a3('permissao'), tDeixe + 8, false, 90, 50), ponto(a3('permissao'), tPerguntar), ponto(b('perguntar'), tLe, false, 120)]}
        marcas={[
          {de: tDeixe + 10, ate: tPerguntar + 4, r: a3('permissao')},
          {de: tLe - 4, r: b('perguntar')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 4. o pedido: o plano primeiro ----------
export const Pedido: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'pedido';
  const tPeca = quando(C, 'peca');
  const tSeparar = quando(C, 'separar');
  const tMostrar = quando(C, 'mostrar');
  const tEnvia = tMostrar + 46;
  const a = (n: string) => alvo('code-4-pedido', n);
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 3')} titulo={T('Peça o plano primeiro')} inicio={tPeca} claro />
      <Tela
        entra={tPeca - 10}
        quadros={[
          {tela: 'code-3-pasta', de: 0},
          {tela: 'code-4-pedido', de: tSeparar - 2},
        ]}
        focos={[{de: tPeca + 2, r: a('caixa'), zoom: 1.55}]}
        cursor={[ponto(a('caixa'), tPeca + 2, false, 200), ponto(a('caixa'), tSeparar - 6, true, 200), ponto(a('enviar'), tEnvia)]}
        marcas={[
          {de: tSeparar + 4, ate: tEnvia - 6, r: a('caixa')},
          {de: tEnvia - 4, r: a('enviar')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 5. os passos e a contagem ----------
export const Plano: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'plano';
  const tOlha = quando(C, 'olha');
  const tPassos = quando(C, 'passos');
  const tConta = quando(C, 'conta');
  const tConfira = quando(C, 'confira');
  const a = (n: string) => alvo('code-5-plano', n);
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Passo 4')} titulo={T('Confira o plano')} inicio={tOlha} claro={false} />
      <Tela
        entra={tOlha - 10}
        quadros={[{tela: 'code-5-plano', de: 0}]}
        focos={[{de: tPassos - 4, r: a('tarefas'), zoom: 1.5}, {de: tConta - 2, r: a('tabela'), zoom: 1.6}, {de: tConfira + 4, r: juntar(a('tabela'), a('tarefas')), zoom: 1.15}]}
        marcas={[
          {de: tOlha + 2, ate: tPassos - 6, r: a('passo')},
          {de: tPassos + 2, ate: tConta - 6, r: a('tarefas')},
          {de: tConta + 6, r: a('tabela')},
        ]}
      />
    </Fundo>
  );
};

// ---------- 6. "pode fazer": o cartão de aprovação ----------
export const Aprova: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'aprova';
  const tResponda = quando(C, 'responda');
  const tCartao = quando(C, 'cartao');
  const tMostra = quando(C, 'mostra');
  const tPermitir = quando(C, 'permitir');
  const tRecusar = quando(C, 'recusar');
  const tClica = tRecusar + 40;
  const tComando = tClica + 34;
  const s = (n: string) => alvo('code-6-aprova-script', n);
  const c = (n: string) => alvo('code-7-aprova-comando', n);
  const p = (n: string) => alvo('code-5b-pode', n);
  return (
    <Fundo tipo="papel">
      <Passo rotulo={T('Passo 5')} titulo={T('Leia e aprove')} inicio={tResponda} claro />
      <Tela
        entra={tResponda - 10}
        quadros={[
          {tela: 'code-5b-pode', de: 0},
          {tela: 'code-6-aprova-script', de: tCartao - 6},
          {tela: 'code-7-aprova-comando', de: tClica + 12},
        ]}
        focos={[
          {de: 0, r: p('caixa'), zoom: 1.6, dur: 1},
          {de: tCartao - 4, r: s('cartao'), zoom: 1.18},
          {de: tPermitir - 6, r: juntar(s('permitir'), s('recusar')), zoom: 1.6},
          {de: tClica + 12, r: c('cartao'), zoom: 1.25},
        ]}
        cursor={[
          ponto(p('enviar'), tResponda + 2, false, -60, 20),
          ponto(p('enviar'), tResponda + 14),
          ponto(s('permitir'), tPermitir, false),
          ponto(s('recusar'), tRecusar, false),
          ponto(s('permitir'), tClica),
          ponto(c('permitir'), tComando),
        ]}
        marcas={[
          {de: tMostra, ate: tPermitir - 8, r: s('previa'), folga: 2},
          {de: tPermitir, ate: tRecusar - 4, r: s('permitir')},
          {de: tRecusar, ate: tClica - 6, r: s('recusar')},
          {de: tClica + 16, ate: tComando + 12, r: c('previa'), folga: 2},
        ]}
      />
    </Fundo>
  );
};

// ---------- 7. pronto: conferir e pedir ajuste ----------
// "Desfazer mudanças" não entra aqui: ele só volta o que as ferramentas de arquivo escreveram, e nesta tarefa quem
// moveu os arquivos foi o script (um comando). Prometer o botão aqui seria prometer o que ele não faz.
export const Pronto: React.FC = () => {
  const {quando, T, alvo} = useLinha();
  const C = 'pronto';
  const tPronto = quando(C, 'pronto');
  const tClique = quando(C, 'clique');
  const tGostou = quando(C, 'gostou');
  const tAjuste = quando(C, 'ajuste');
  const a = (n: string) => alvo('code-8-pronto', n);
  return (
    <Fundo tipo="tinta">
      <Passo rotulo={T('Passo 6')} titulo={T('Confira o resultado')} inicio={tPronto} claro={false} />
      <Tela
        entra={tPronto - 10}
        quadros={[{tela: 'code-8-pronto', de: 0}]}
        focos={[{de: tClique, r: a('pasta'), zoom: 2}, {de: tGostou, r: a('fim'), zoom: 1.2}, {de: tAjuste, r: a('caixa'), zoom: 1.6}]}
        cursor={[ponto(a('pasta'), tClique + 2, false, -120, 60), ponto(a('pasta'), tClique + 14), ponto(a('caixa'), tAjuste + 8)]}
        marcas={[
          {de: tPronto + 4, ate: tClique - 4, r: a('fim'), folga: 2},
          {de: tClique + 8, ate: tGostou - 4, r: a('pasta')},
          {de: tAjuste + 6, r: a('caixa'), folga: 2},
        ]}
      />
    </Fundo>
  );
};

// ---------- 8. o script fica ----------
export const Fecho: React.FC = () => {
  const f = useCurrentFrame();
  const {quando, T} = useLinha();
  const C = 'fecho';
  const tScript = quando(C, 'script');
  const tRoda = quando(C, 'roda');
  const gira = interpolate(f - tRoda, [0, 30], [0, 360], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic)});
  return (
    <Fundo tipo="papel">
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', flexDirection: 'column'}}>
        <Entra inicio={tScript} distancia={30}>
          <div style={{display: 'flex', alignItems: 'center', gap: 20, fontFamily: MONO, fontSize: 40, color: COR.texto, background: '#fbf8f1', border: `2px solid ${COR.linha}`, borderRadius: 20, padding: '24px 36px'}}>
            <Icone nome="terminal" tamanho={44} cor={COR.acao} />
            {T('organizar-downloads.ps1')}
            <div style={{transform: `rotate(${gira}deg)`, display: 'grid', placeItems: 'center', marginLeft: 10}}>
              <Icone nome="repetir" tamanho={40} cor={COR.acao} />
            </div>
          </div>
        </Entra>
        <div style={{marginTop: 40}}>
          <Sobe texto={T('Rode de novo quando quiser.')} inicio={tRoda} tamanho={60} peso={400} cor={COR.texto2} italico passo={2} />
        </div>
        <div style={{display: 'flex', alignItems: 'center', gap: 26, marginTop: 90, opacity: aparece(f, tRoda + 10, 14)}}>
          <Logo tamanho={90} inicio={tRoda + 6} />
          <div style={{fontFamily: SANS, fontSize: 64, color: COR.texto, fontWeight: 500}}>Clave</div>
        </div>
      </AbsoluteFill>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 46, textAlign: 'center', fontFamily: SANS, fontSize: 22, color: COR.texto3, opacity: aparece(f, tRoda, 14)}}>
        {T('O Clave é um app independente, sem ligação com a Anthropic. Claude é marca da Anthropic.')}
      </div>
    </Fundo>
  );
};
