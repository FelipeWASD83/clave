> Esta é a cópia em português do [`CLAUDE.md`](CLAUDE.md) desta pasta. A referência é o `CLAUDE.md` em inglês; se os dois divergirem, vale o inglês.

# CLAUDE.md: video (o vídeo "Por que usar o Clave")

Subprojeto do Clave. Um vídeo de ~87 s em motion graphics, 1920×1080, com narração em português, que
convence a pessoa a usar o Clave e a API: pagar pelo uso, sem limite de 5 horas, dados no computador, o modelo
certo para cada tarefa (fluxos), automação no modo Code e rotinas, lições do zero. Feito em código com
**Remotion 4** (React). O texto é o mesmo argumento da seção "Por que você deveria usar o Clave" do README e da
lição `tutoriais/por-que-o-clave.md`: mudou um, conferir os outros.

## Como rodar

```powershell
npm install                                   # uma vez (node_modules fora do git)
python -m venv .venv                          # uma vez, para a voz
.venv\Scripts\pip install edge-tts==7.3.1
npm run narrar                                # gera a narração (precisa de internet)
npm run sons                                  # gera os efeitos e a trilha
npm run studio                                # abre o Remotion Studio para ver e ajustar
npm run video                                 # renderiza e normaliza o áudio em -16 LUFS: saida/por-que-o-clave.mp4 (~5 min)
npm run capa                                  # um quadro em saida/capa.png
```

## Como está montado

- `ferramentas/narrar.py`: as falas de cada cena, a voz (`pt-BR-ThalitaMultilingualNeural`, a voz neural do
  Edge pelo `edge-tts`) e a velocidade. Grava `public/narracao/<cena>.mp3` e `src/narracao.gerado.json`, com a
  duração de cada fala e **o tempo de cada palavra**.
- `src/tema.ts`: cores e fontes do app (papel, tinta, verde-azulado; Source Serif 4 e IBM Plex), e a linha do
  tempo, calculada a partir da narração: cada cena dura a fala dela mais as folgas (`TROCA`, `ANTES`,
  `DEPOIS`, `EXTRA`). `quando(cena, palavra)` dá o quadro em que a palavra é dita: **as animações ficam presas
  à fala**, então mudar uma fala não desalinha nada.
- `src/Video.tsx`: as cenas em sequência, a folha em cada troca, a narração e a lista de efeitos sonoros.
- `src/cenas/`: Gancho, Apresenta, Custo (a fita de recibo), Limite, Dados, Fluxo, Code, Aprender, Fecho.
- `src/componentes/`: Base (fundo, logo, texto que sobe palavra por palavra, rótulo, nota), Icones (os do
  app), Troca (a folha, a única transição).
- `ferramentas/sons.py`: toque, tique, impressora, folha, selo e uma trilha calma de acordes, tudo sintetizado
  em numpy (sem amostra de ninguém).

## Decisões que não se desfazem sem motivo

1. **Grafia de pronúncia na fala, nome certo na tela.** A voz em português lê "Claude" como "Cloud" e
   "Haiku" sem o H. Na fala vai "Clód", "Ráicu", "A P I" e "Guít Râb"; a tela mostra Claude, Haiku, API e
   GitHub. Conferido transcrevendo a narração com o Whisper. "pela A P I" antes de "não" virou "PIN": por
   isso a fala de privacidade começa com "Na A P I".
2. **Todo número tem fonte e o que é estimativa diz que é**: preços da página oficial da Anthropic de
   14/10/2026 (mensagem curta sem raciocínio: Haiku 5.5 ≈ US$ 0,40 por mil, Sonnet 5.5 ≈ US$ 7,20 por mil);
   a política de dados de privacy.claude.com (API não treina por padrão, apaga em até 30 dias); a estimativa do
   fluxo (US$ 0,19 a 1,23) é a que o próprio Clave calculou num fluxo de verdade.
3. **Nada que imite o app da Anthropic.** O cartão de "Limite atingido" é genérico, e o fecho diz que o Clave é
   independente e que Claude é marca da Anthropic.
4. **A narração e o vídeo não vão para o git** (`.gitignore` daqui): a voz é gerada por um serviço da
   Microsoft e o MP4 é grande. O vídeo pronto é anexo da release **v2.0.0** no GitHub, e o README aponta para
   `releases/download/v2.0.0/por-que-o-clave.mp4` com a `capa.jpg` daqui (o último quadro, 1280 px, a única
   saída que fica no git). Regravou o vídeo? `gh release upload v2.0.0 saida/por-que-o-clave.mp4 --clobber`
   troca o anexo sem mudar o link. O botão Atualizar só baixa anexo `.zip`, então o MP4 na release não
   atrapalha.
5. **Remotion fixado em 4.0.534** (versão exata no `package.json`). Grátis para pessoa física e empresa de
   até 3 pessoas.
6. **Sem o endereço do repositório na tela** (decisão do dono do repositório, 14/10/2026): o fecho mostra a
   marca, os selos e o slogan; a fala diz "é só baixar no GitHub" e basta.

## Armadilhas

- **O Chrome que o Remotion baixa é barrado pelo Smart App Control** ("spawn UNKNOWN"). O `remotion.config.ts`
  aponta para o Edge do Windows, que roda.
- O `edge-tts` usa o serviço de leitura em voz alta do Edge: precisa de internet e pode mudar sem aviso. Se ele
  parar, a narração antiga continua em `public/narracao/` até alguém rodar `npm run narrar` de novo.
- Texto que sobe palavra por palavra (`Sobe`) separa as palavras com margem, não com espaço: espaço no fim de
  um `inline-block` some.
