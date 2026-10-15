> Esta é a cópia em português do [`CLAUDE.md`](CLAUDE.md) desta pasta. A referência é o `CLAUDE.md` em inglês; se os dois divergirem, vale o inglês.

# CLAUDE.md: video (os vídeos do Clave)

Subprojeto do Clave: vídeos curtos em motion graphics, 1920×1080, 30 fps, cada um em **português do Brasil e em
inglês**, feitos em código com **Remotion 4** (React):

| Vídeo (id) | O que é | Bate com |
|---|---|---|
| `por-que-o-clave` | ~87 s de argumento: pagar pelo uso, sem limite de 5 horas, dados no computador, o modelo certo para cada tarefa, modo Code e rotinas, lições do zero | README "Por que você deveria usar o Clave", lição `por-que-o-clave.md` |
| `chave-da-api` | tutorial: conta no Console, crédito (e o crédito do plano Max), API Keys > Create Key, copiar a `sk-ant-`, colar em Configurações > Conta e chave, o teto do mês, as regras de ouro | lição `chave-da-api.md` |
| `primeiros-passos` | tutorial: o `instalar.bat` e o atalho, a janela de boas-vindas, a primeira conversa, o botão do modelo, o custo da resposta, o painel "Seu uso" | README (instalação), lição `primeira-conversa.md` |
| `primeira-automacao` | tutorial: Novo trabalho no Code, a pasta Downloads, o modo Perguntar, o plano primeiro, os passos e a contagem, o cartão de aprovação, pedir um ajuste | lições `primeira-automacao.md` e `modo-code.md` |

O texto de cada vídeo é o mesmo da lição dele (nomes de menus, passos, números): **mudou a lição, conferir o roteiro
em `roteiros/` e as telas.** Os identificadores do código, os nomes de arquivo e os comentários são em português de
propósito.

## Como rodar

```powershell
npm install                                   # uma vez (node_modules fora do git)
python -m venv .venv                          # uma vez, para a voz
.venv\Scripts\pip install edge-tts==7.3.1
npm run narrar                                # a narração de todos os vídeos, nos dois idiomas (precisa de internet; só refaz fala que mudou)
npm run sons                                  # os efeitos e a trilha
npm run telas                                 # os prints do app de verdade, nos dois idiomas (~4 min; sobe a demonstração sozinho, ver abaixo)
npm run studio                                # o Remotion Studio, para ver e ajustar
npm run videos                                # renderiza os 8 MP4 e as 8 capas (~5 min cada)
npm run video:chave-da-api                    # um vídeo, nos dois idiomas (também video:primeiros-passos, video:primeira-automacao, video:por-que-o-clave)
npm run video                                 # só o "Por que usar o Clave" em português (como antes): saida/por-que-o-clave.pt-BR.mp4 e saida/por-que-o-clave.mp4
npm run capas                                 # só as capas
```

O `ferramentas/videos.py` aceita os mesmos filtros: `python ferramentas/videos.py chave-da-api --lingua en`.
O `ferramentas/narrar.py` também (`--forcar` refaz até a fala que não mudou).

Saída:

- `saida/<id>.<pt-BR|en>.mp4`: H.264 (yuv420p, faixa de TV), AAC a -16 LUFS (loudnorm em duas passadas), `+faststart`, **no máximo ~15
  MB**: o CRF começa em 23 e sobe de 2 em 2 até caber. `saida/por-que-o-clave.mp4` é cópia do português, com o
  nome do anexo da release v2.0.0 (o link do README antes da 4.3). `saida/` fica fora do git.
- `capas/<id>.<pt-BR|en>.jpg`: 1280 px, o quadro que `capa` escolhe em `src/videos/<vídeo>.ts` (com o título
  legível). **As capas ficam no git**; os MP4, não.

## Como está montado

- `roteiros/<id>.json`: a fala de cada cena, por idioma. `{marca}` logo antes de uma palavra marca a hora em que ela
  é dita. O português usa grafia de pronúncia para nomes em inglês (decisão 1).
- `ferramentas/narrar.py`: as vozes (`pt-BR-ThalitaMultilingualNeural` a +6%, `en-US-AvaMultilingualNeural` a
  +3%), um MP3 por cena em `public/narracao/<id>/<lingua>/` e o `tempos.json` ali, com o tempo de cada palavra e de
  cada marca. Ele casa as marcas com as palavras que a voz devolve (a voz às vezes junta ou separa palavras, como em
  "A P I"); marca que ele não consegue pôr para o script mostrando as palavras que ouviu.
- `src/Root.tsx`: duas composições por vídeo (`ChaveDaApiPtBR`, `ChaveDaApiEn`...), mais uma capa de cada
  (`...Capa`), e `PorQueOClave` (o nome antigo, em português). O `calculateMetadata` lê a narração (e o
  `alvos.json` das telas) de `public/` antes de renderizar, então a duração segue a fala.
- `src/Video.tsx`: qualquer vídeo: as cenas em sequência, a folha em cada troca, a narração, os efeitos e a trilha.
  `src/videos/<vídeo>.ts`: quais cenas, quadros a mais por cena, o quadro da capa e os efeitos sonoros.
- `src/linha.tsx`: o que uma cena pede: `quando(cena, marca)` (o quadro de uma marca, então as animações ficam
  presas à fala nos dois idiomas), `T('texto em português')` (o texto da tela; o inglês fica em `src/i18n/en.ts`,
  com o português como chave, como no app; **tradução faltando quebra a renderização em inglês, de propósito**),
  `alvo(tela, nome)` (onde fica uma coisa num print) e `tela(nome)`.
- `src/tema.ts`: cores e fontes do app (papel, tinta, verde-azulado; Source Serif 4 e IBM Plex) e o `montarCenas`
  (cada cena dura a fala mais `TROCA`, `ANTES`, `DEPOIS` e os quadros a mais dela).
- `src/cenas/<vídeo>/`: as cenas. `src/componentes/`: Base (fundo, logo, texto que sobe, rótulo, nota, `Passo`),
  Icones, Troca (a folha), **Tela** (uma janela do Clave com os prints de verdade: câmera com zoom e pan, cursor que
  anda e clica e caixas de destaque, tudo nas coordenadas do print) e **Esquema** (um navegador genérico e uma pasta
  do Windows genérica para o que não é o Clave, e um cursor solto).
- `ferramentas/sons.py`: toque, tique, impressora, folha, selo, clique de mouse, digitação e uma trilha calma de
  acordes, tudo sintetizado em numpy (sem amostra de ninguém).
- `ferramentas/telas.py` e `ferramentas/demo_tutorial.py`: os prints (seção abaixo).

## Os prints do app

O `npm run telas` tira as telas que os tutoriais mostram, nos dois idiomas, do **modo demonstração do próprio app**
(API de mentira, nada é cobrado, nenhuma chave): sobe o `demo_tutorial.py` na porta **8051** com uma pasta de dados
temporária nova, um Edge sem janela na porta de depuração **9351**, passa pelo app como uma pessoa passaria e grava
`public/telas/<lingua>/<tela>.png` (1440 × 810 pontos com densidade 2) e o `alvos.json` (o retângulo de tudo o que a
narração cita, medido na página, para o zoom, o cursor e o destaque caírem no lugar certo em cada idioma). No fim
derruba os dois processos e apaga a pasta temporária. `public/telas/` fica fora do git (~15 MB, regenerável).

- O `demo_tutorial.py` roda o `servidor.py --demo` sem mudança, mas troca, no próprio processo, a função que monta
  as respostas da API de mentira: nas mensagens dos tutoriais (os presentes de jardinagem da lição, a pasta
  Downloads) o Claude de mentira responde como o de verdade responderia, no idioma da mensagem (olha a pasta, mostra
  os passos e a contagem, escreve o `organizar-downloads.ps1`/`organize-downloads.ps1`, pede o OK e roda). Não mexe
  em nenhum arquivo do Clave.
- A demonstração roda com o `USERPROFILE` apontando para a pasta temporária, para o modo Code não pegar o CLAUDE.md
  nem as skills de quem grava.
- Retoques, só nos prints: o caminho temporário aparece como `C:\Users\Ana\...`; o passo da chave das boas-vindas e
  Configurações > Conta e chave aparecem como fora da demonstração (a demonstração esconde o campo da chave), com uma
  chave falsa no campo de senha (bolinhas); o custo de cada resposta é recalculado com a tabela de preços do próprio
  Clave (`servidor/custo.py`; a demonstração grava zero); antes do print do painel "Seu uso", três semanas de uso de
  exemplo (Haiku e Sonnet, centavos) entram no banco temporário.

## Decisões que não se desfazem sem motivo

1. **Grafia de pronúncia na fala em português, nome certo na tela.** A voz em português lê "Claude" como "Cloud" e
   "Haiku" sem o H. Na fala vai "Clód", "Ráicu", "A P I" e "Guít Râb"; a tela mostra Claude, Haiku, API e GitHub.
   "pela A P I" antes de "não" virou "PIN": por isso a fala de privacidade começa com "Na A P I". "API Keys", nome em inglês na
   tela, é falado em inglês ("abra a página êi pi ai kís"): "A P I Keys" saía "API Case" e "PayCase". "platform.claude.com" nunca é falado (o Whisper ouve "cloud.com"): a fala diz "o endereço é este aqui" e a
   tela digita. Conferido transcrevendo com o Whisper.
2. **Todo número tem fonte e o que é estimativa diz que é**: preços da página oficial da Anthropic de 14/10/2026
   (mensagem curta sem raciocínio: Haiku 5.5 ≈ US$ 0,40 por mil, Sonnet 5.5 ≈ US$ 7,20 por mil); a política de dados
   de privacy.claude.com; a estimativa do fluxo (US$ 0,19 a 1,23) é a que o próprio Clave calculou num fluxo de
   verdade; o crédito do plano Max (US$ 100 no Max 5x, US$ 200 no Max 20x) é o da lição.
3. **Nada que imite o app ou o site da Anthropic.** O cartão de "Limite atingido" é genérico; o Console do vídeo da
   chave é um esquema (barras cinza no lugar do layout, as nossas cores, sem logo, só os nomes que a lição usa:
   Billing, API Keys, Create Key) com a legenda "ilustração: a tela real pode mudar"; a chave é falsa e mascarada
   (`sk-ant-•••••`). Todo fecho diz que o Clave é independente e que Claude é marca da Anthropic.
4. **A narração, os prints e os MP4 não vão para o git** (`.gitignore` daqui): a voz é gerada por um serviço da
   Microsoft, os prints se refazem e os MP4 são grandes. As capas (`capas/`) e a `capa.jpg` ficam. Os 8 MP4 ficam na
   release `videos` (ver o CLAUDE.md principal), e desde a 4.3 o README aponta para lá com as capas de `capas/`
   (o vídeo do "Por que" e a seção Vídeos, cada um na língua do README com link para a outra). A release v2.0.0
   continua com o `por-que-o-clave.mp4` (português) para os README antigos, com a `capa.jpg`. Regravou?
   `gh release upload videos saida/<id>.<lingua>.mp4 --clobber`. Publicar é decisão do dono do repositório.
5. **Remotion fixado em 4.0.534** (versão exata no `package.json`). Grátis para pessoa física e empresa de até 3
   pessoas.
6. **Sem o endereço do repositório na tela** (decisão do dono do repositório, 14/10/2026): os fechos mostram a marca;
   a fala diz "é só baixar no GitHub" e basta.
7. **Telas de verdade, não desenho,** para tudo o que é o Clave: prints da demonstração, com zoom, cursor e destaque.
   Desenho só para o que não é o Clave (o Console, a pasta do Windows, os passos do instalador: o instalador só
   escreve em português, então o vídeo mostra os quatro passos dele como lista, no idioma do vídeo).
8. **Nada em português no vídeo em inglês, e vice-versa**: o texto da tela passa pelo `T()` (tradução faltando = erro
   na renderização), os prints são tirados com o app em cada idioma e os arquivos e respostas da demonstração existem
   nos dois. A voz em inglês é a `en-US-AvaMultilingualNeural` (a irmã "Multilingual" da voz em português).
9. **15 MB por vídeo**: x264 `-preset slow -tune animation`, CRF de 23 para cima, `yuv420p` na faixa de TV (o Remotion
   entrega faixa cheia, `yuvj420p`, que alguns players mostram com o contraste errado), AAC a 128 kbps, `+faststart`
   (eles são baixados e tocados direto no app). Em CRF 23 eles ficam entre 7 e 9,5 MB.
10. **Nos tutoriais a trilha abaixa sob a voz** (`trilha: 0.26` e `abaixaTrilha: 0.6` em `src/videos/*.ts`; o de
   argumento fica em 0.32, sem abaixar): eles falam mais. Mesmo assim, com qualquer trilha embaixo, o Whisper ouviu
   "Download Claude" onde a voz em inglês diz "Download Clave" (sem trilha ele ouviu certo), então a fala virou
   "Download the Clave app". No de argumento em português, "usa o Clód pela A P I" saía "Cloud API": uma vírgula
   depois de "Clód" resolveu. O `remotion render ... --codec wav` renderiza só o áudio em ~25 s, e é o jeito rápido de
   testar uma fala com a trilha antes de renderizar o vídeo.

## Armadilhas

- **O Chrome que o Remotion baixa é barrado pelo Smart App Control** ("spawn UNKNOWN"). O `remotion.config.ts`
  aponta para o Edge do Windows, que roda. O `videos.py` chama o `node_modules\.bin\remotion.cmd` pelo `cmd /c`.
- O `edge-tts` usa o serviço de leitura em voz alta do Edge: precisa de internet e pode mudar sem aviso. Se ele
  parar, a narração antiga continua em `public/narracao/` até alguém rodar `npm run narrar` de novo.
- Texto que sobe palavra por palavra (`Sobe`) separa as palavras com margem, não com espaço: espaço no fim de um
  `inline-block` some.
- A capa é um quadro congelado dentro de uma composição do tamanho do vídeo: numa composição de 1 quadro, todo
  `<Sequence>` depois do quadro 0 é cortado e a capa sai em branco.
- O `telas.py` usa as portas 8051 e 9351; se tiver outra coisa nelas, passe `--porta` e `--porta-edge`. O app muda a
  cada versão: se um print quebrar ("não achei o alvo..."), o que mudou foi o seletor no `roteiro()`. Depois de uma
  mudança no app, rode `npm run telas` de novo e olhe as telas antes de renderizar.
- Editar estes arquivos pelo Git Bash com heredoc come as barras invertidas: use um script `.py` ou o editor.
