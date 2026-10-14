# Clave

Um app para Windows que usa o **Claude**, a inteligência artificial da Anthropic,
pela **API**, com a sua própria chave. Parecido com o app do Claude, mas pago por
uso e com um teto de gasto que você define.

> O Clave é um app independente. Ele não é um produto da Anthropic e não tem
> ligação com ela. "Claude" é marca da Anthropic.

## O que ele faz

- **Chat** com o Claude: conversas, projetos, anexos (imagens, PDFs, planilhas,
  textos), versões de cada resposta, prévia de páginas HTML e desenhos SVG.
- **Modo Code**: o Claude trabalha numa pasta do seu computador, lê e cria
  arquivos, mexe em planilhas e roda comandos para automatizar tarefas. Você
  aprova cada mudança (ou libera de vez), vê o antes e depois e pode desfazer.
- **Excel**: lê, cria e altera planilhas (fórmulas, formatação, tabelas,
  gráficos, filtros, listas de opção). Com o Excel instalado, recalcula e
  exporta PDF.
- **Modelos e raciocínio**: Opus 5.5, Sonnet 5.5, Haiku 5.5 e Fable 5.1, com o
  nível de raciocínio de Baixo a Máximo, raciocínio visível e modo rápido.
- **Personalização**: "sobre você", "como responder", estilos prontos e seus,
  projetos com instruções e arquivos fixos.
- **Memória** entre conversas, em arquivos de texto por assunto que você vê,
  edita e apaga, com um editor de memória que muda o que você pedir.
- **Teto de gasto** mensal, gasto por resposta, por dia, por modelo e por
  conversa, e a régua que mostra quanto da memória da conversa já foi usada.
- **GitHub**: anexar arquivos dos seus repositórios e deixar o Claude consultar
  código, issues e pull requests.
- **Busca na web** e **conectores MCP**.
- **Aprender**: lições para quem nunca usou IA, com glossário de termos (API,
  JSON, Git...) e um ajudante que tira dúvidas de cada lição.
- **Modelo de pasta**: uma pasta de trabalho pronta, com regras (CLAUDE.md),
  skills (inclusive ver vídeos) e referências visuais para sites.
- **Botão Atualizar**: baixa a versão nova deste repositório e reinicia.

## Do que você precisa

- Windows 10 ou 11.
- Internet.
- Uma conta na Anthropic com crédito na API (veja abaixo). Quem assina o plano
  Max do Claude ganha crédito mensal na API.

## Instalar

1. Baixe este repositório: botão verde **Code > Download ZIP** no GitHub, ou a
   versão mais nova em **Releases**.
2. Extraia o ZIP numa pasta sua (por exemplo, `Documentos\Clave`).
3. Dê dois cliques em **`instalar.bat`**. Ele:
   - procura o Python 3.10 ou mais novo e, se não achar, oferece instalar pelo
     winget;
   - cria o ambiente do Clave e instala as dependências;
   - baixa o Electron oficial (a janela do app, uns 110 MB), conferido pela
     assinatura publicada;
   - cria os atalhos **Clave** na área de trabalho e no menu Iniciar.
4. Abra pelo atalho **Clave**.

Na primeira vez, o Clave pede a sua chave da API e o teto de gasto do mês.

### Como conseguir a chave da API

1. Entre em **platform.claude.com** (o Console da Anthropic) e crie uma conta.
2. Ponha crédito em **Billing** (ou, se você assina o Max, ative o crédito do
   plano em claude.ai > Settings > Billing > API credits).
3. Em **API Keys**, clique em **Create Key** e copie a chave (`sk-ant-...`).
4. Cole no Clave quando ele pedir (ou em Configurações > Conta e chave).

A chave fica guardada só no seu computador, criptografada pelo Windows.

## Quanto custa

Você paga a Anthropic pelo que usar, por número de tokens. Exemplos aproximados:
uma pergunta curta no Haiku 5.5 custa menos de US$ 0,001; uma resposta média no
Sonnet 5.5, uns US$ 0,01; uma tarefa grande no modo Code, de centavos a alguns
dólares. O Clave mostra o custo de cada resposta e para quando o mês chega no
teto que você definiu.

## Privacidade e segurança

- As mensagens e os arquivos que você manda vão para a Anthropic (é assim que o
  Claude responde). As conversas, a memória, os projetos e o histórico de gasto
  ficam **só no seu computador**, na pasta `dados` do Clave.
- O Clave só aceita conexões do próprio computador, e cada pedido precisa da
  sessão que o atalho cria: nenhuma página da internet consegue mandar o Claude
  mexer nos seus arquivos.
- No modo Code, mudar arquivos e rodar comandos pede o seu OK (dá para ajustar).
  Comandos que apagam ou publicam algo **sempre** pedem, e o modo Plano não
  muda nada. Arquivos sensíveis vão para a lista de protegidos: as ferramentas
  de arquivo nunca mexem neles e comando que os cite pede OK.

## Atualizar

O Clave procura versão nova uma vez por dia. Quando houver, aparece o botão
**Atualizar** na barra da esquerda: ele mostra o que mudou, baixa, guarda a
versão atual (e volta para ela se a nova não abrir) e reinicia. Seus dados não
são tocados.

## Smart App Control (Windows 11)

O Smart App Control do Windows 11 bloqueia programas novos sem assinatura. O
Clave não tem executável próprio de propósito: ele roda no Python oficial e no
Electron oficial, que o Windows reconhece. Se mesmo assim aparecer um aviso de
"Controle de Aplicativo" ao instalar as dependências, tente de novo mais tarde
ou abra uma issue aqui com o nome do arquivo bloqueado.

## Desinstalar

Apague a pasta do Clave e os dois atalhos. Se quiser guardar as conversas antes,
use Configurações > Dados e backup.

## Para quem desenvolve

- `servidor/`: servidor local em Python (biblioteca padrão + SDK oficial
  `anthropic` + `openpyxl`). `servidor/servidor.py --demo --sem-senha` sobe uma
  demonstração com uma API de mentira, sem gastar nada.
- `app/`: a interface (HTML, CSS e JavaScript sem etapa de build).
- `electron/`: a janela do app.
- `tutoriais/`: as lições, em Markdown.
- `modelo-de-pasta/`: o modelo de pasta de trabalho.
- `skills/`: skills que vêm com o Clave (ver-video).
- Testes: `.venv\Scripts\python.exe -m unittest discover -s testes -t testes`.
- Publicar versão: `ferramentas\publicar-versao.ps1` (cria a release no GitHub
  que o botão Atualizar baixa).

Detalhes técnicos e decisões em [`CLAUDE.md`](CLAUDE.md). Histórico em
[`CHANGELOG.md`](CHANGELOG.md).

## Licença

O código do Clave é livre, sob a licença [MIT](LICENSE). As bibliotecas e
fontes em `app/vendor/` têm as licenças delas, no arquivo ao lado de cada uma.
Os prints em `modelo-de-pasta/.claude/referencias-visuais/prints/` são capturas
de sites públicos, guardadas só como referência de estudo; os sites e as marcas
são dos donos deles.
