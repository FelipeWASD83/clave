# CLAUDE.md: video (Clave's videos)

A subproject of Clave: short motion graphics videos, 1920×1080, 30 fps, each one in **Brazilian Portuguese and
English**, made in code with **Remotion 4** (React):

| Video (id) | What it is | Matches |
|---|---|---|
| `por-que-o-clave` | ~87 s pitch: pay for what you use, no 5-hour limit, data on your computer, the right model for each task, Code mode and routines, lessons from zero | README "Why you should use Clave", lesson `por-que-o-clave.md` |
| `chave-da-api` | tutorial: account in the Console, credit (and the Max plan credit), API Keys > Create Key, copy `sk-ant-`, paste in Settings > Account & key, the monthly cap, the golden rules | lesson `chave-da-api.md` |
| `primeiros-passos` | tutorial: `instalar.bat` and the shortcut, the welcome window, the first chat, the model button, the cost of an answer, the "Your usage" panel | README (install), lesson `primeira-conversa.md` |
| `primeira-automacao` | tutorial: New Code task, the Downloads folder, Ask mode, plan first, the steps and the count, the approval card, asking for a change | lessons `primeira-automacao.md` and `modo-code.md` |

The text of each video is the same as its lesson (names of menus, steps, numbers): **if the lesson changes, check
the script in `roteiros/` and the screens.** The code identifiers, file names and comments are in Portuguese on
purpose.

## How to run

```powershell
npm install                                   # once (node_modules stays outside git)
python -m venv .venv                          # once, for the voice
.venv\Scripts\pip install edge-tts==7.3.1
npm run narrar                                # the narration of every video, both languages (needs internet; only redoes changed lines)
npm run sons                                  # the sound effects and the music
npm run telas                                 # the screenshots of the real app, both languages (~4 min; starts its own demo, see below)
npm run studio                                # Remotion Studio, to preview and adjust
npm run videos                                # renders all 8 MP4s and the 8 covers (~5 min each)
npm run video:chave-da-api                    # one video, both languages (also video:primeiros-passos, video:primeira-automacao, video:por-que-o-clave)
npm run video                                 # only "Por que usar o Clave" in Portuguese (as before): saida/por-que-o-clave.pt-BR.mp4 and saida/por-que-o-clave.mp4
npm run capas                                 # only the covers
```

`ferramentas/videos.py` accepts the same filters: `python ferramentas/videos.py chave-da-api --lingua en`.
`ferramentas/narrar.py` too (`--forcar` redoes even unchanged lines).

Output:

- `saida/<id>.<pt-BR|en>.mp4`: H.264 (yuv420p, TV range), AAC at -16 LUFS (two-pass loudnorm), `+faststart`, **at most ~15 MB**: the
  CRF starts at 23 and goes up by 2 until it fits. `saida/por-que-o-clave.mp4` is a copy of the Portuguese one,
  the name of the attachment of the v2.0.0 release (README links before 4.3). `saida/` stays outside git.
- `capas/<id>.<pt-BR|en>.jpg`: 1280 px, the frame `capa` picks in `src/videos/<video>.ts` (the title visible).
  **The covers stay in git**; the MP4s don't.

## How it is put together

- `roteiros/<id>.json`: the line of each scene, per language. `{marca}` right before a word marks the moment it is
  spoken. Portuguese uses pronunciation spelling for English names (decision 1).
- `ferramentas/narrar.py`: voices (`pt-BR-ThalitaMultilingualNeural` at +6%, `en-US-AvaMultilingualNeural` at
  +3%), one MP3 per scene in `public/narracao/<id>/<lingua>/`, and `tempos.json` there with the time of every word
  and of every mark. It aligns the marks with the words the voice returns (the voice sometimes joins or splits
  words, as in "A P I"); a mark it can't place stops the script with the words it heard.
- `src/Root.tsx`: two compositions per video (`ChaveDaApiPtBR`, `ChaveDaApiEn`...) plus one cover each
  (`...Capa`), and `PorQueOClave` (the old name, Portuguese). `calculateMetadata` reads the narration (and the
  screens' `alvos.json`) from `public/` before rendering, so the duration follows the speech.
- `src/Video.tsx`: any video: the scenes in sequence, the sheet at each transition, the narration, the effects and
  the music. `src/videos/<video>.ts`: which scenes, extra frames per scene, the cover frame and the sound effects.
- `src/linha.tsx`: what a scene asks for: `quando(cena, marca)` (frame of a mark, so the animations stay tied to
  the speech in both languages), `T('texto em português')` (the screen text; English in `src/i18n/en.ts`, keyed by
  the Portuguese text like the app; **a missing translation breaks the English render on purpose**), `alvo(tela,
  nome)` (where something is on a screenshot) and `tela(nome)`.
- `src/tema.ts`: the app's colors and fonts (paper, ink, teal; Source Serif 4 and IBM Plex) and `montarCenas`
  (each scene lasts its line plus `TROCA`, `ANTES`, `DEPOIS` and its extra frames).
- `src/cenas/<video>/`: the scenes. `src/componentes/`: Base (background, logo, rising text, label, note, `Passo`),
  Icones, Troca (the sheet), **Tela** (a Clave window with the real screenshots: camera with zoom and pan, a cursor
  that moves and clicks, and highlight boxes, all in screenshot coordinates) and **Esquema** (a generic browser and
  a generic Windows folder for what isn't Clave, and a free cursor).
- `ferramentas/sons.py`: chime, tick, printer, sheet, stamp, mouse click, typing and a calm chord track, all
  synthesized in numpy (no one's samples).
- `ferramentas/telas.py` and `ferramentas/demo_tutorial.py`: the screenshots (next section).

## The screenshots of the app

`npm run telas` takes the screens the tutorials show, in both languages, from **the app's own demo mode** (fake API,
nothing charged, no key): it starts `demo_tutorial.py` on port **8051** with a fresh temporary data folder,
a headless Edge on debugging port **9351**, walks through the app like a person would and writes
`public/telas/<lingua>/<tela>.png` (1440 × 810 points at density 2) and `alvos.json` (the rectangle of everything the
narration mentions, measured in the page, so the zoom, the cursor and the highlight land in the right place in each
language). It kills both processes and deletes the temporary folder at the end. `public/telas/` stays outside git
(~15 MB, regenerated).

- `demo_tutorial.py` runs `servidor.py --demo` unchanged, but swaps, in its own process, the function that builds
  the fake API's answers: for the tutorial messages (the gardening gifts of the lesson, the Downloads folder) the
  fake Claude answers like the real one would, in the message's language (looks at the folder, shows the steps and
  the count, writes `organizar-downloads.ps1`/`organize-downloads.ps1`, asks for the OK, runs it). It does not
  touch any Clave file.
- The demo runs with `USERPROFILE` pointing at the temporary folder, so Code mode doesn't pick up the CLAUDE.md or
  the skills of whoever records.
- Retouches, only in the screenshots: the temporary path shows as `C:\Users\Ana\...`; the welcome key step and
  Settings > Account & key show as they do outside the demo (the demo hides the key field), with a fake key in the
  password field (dots); each answer's cost is recalculated with Clave's own price table (`servidor/custo.py`; the
  demo records zero); before the "Your usage" screenshot, three weeks of sample usage (Haiku and Sonnet, cents) go
  into the temporary database.

## Decisions that are not undone without a reason

1. **Pronunciation spelling in the Portuguese speech, correct name on the screen.** The Portuguese voice reads
   "Claude" as "Cloud" and "Haiku" without the H. The speech uses "Clód", "Ráicu", "A P I" and "Guít Râb"; the screen
   shows Claude, Haiku, API and GitHub. "pela A P I" before "não" became "PIN": that is why the privacy line starts
   with "Na A P I". "API Keys", an English name on the screen, is spoken in English
   ("abra a página êi pi ai kís"): "A P I Keys" came out as "API Case" and "PayCase". "platform.claude.com" is never spoken (Whisper hears "cloud.com"): the
   speech says "o endereço é este aqui" and the screen types it. Checked by transcribing with Whisper.
2. **Every number has a source, and what is an estimate says so**: prices from Anthropic's official page of
   2026-10-14 (short message without reasoning: Haiku 5.5 ≈ $0.40 per thousand, Sonnet 5.5 ≈ $7.20 per
   thousand); the data policy from privacy.claude.com; the workflow estimate ($0.19 to $1.23) is the one Clave
   itself calculated on a real workflow; the Max plan credit ($100 on Max 5x, $200 on Max 20x) is the lesson's.
3. **Nothing that imitates Anthropic's app or site.** The "Limit reached" card is generic; the Console in the API
   key video is a schematic (grey bars instead of the layout, our colors, no logo, only the names the lesson uses:
   Billing, API Keys, Create Key) with the caption "illustration: the real page may change"; the key is fake and
   masked (`sk-ant-•••••`). Every closing says Clave is independent and that Claude is a trademark of Anthropic.
4. **The narration, the screenshots and the MP4s do not go to git** (`.gitignore` here): the voice is generated by
   a Microsoft service, the screenshots are regenerated and the MP4s are big. The covers (`capas/`) and `capa.jpg`
   stay. All 8 MP4s live in the `videos` release (see the main CLAUDE.md), and since 4.3 the README points
   there with the covers from `capas/` (the "Why" video and the Videos section, each in the README's language
   with a link to the other). The v2.0.0 release still has `por-que-o-clave.mp4` (Portuguese) for the older
   READMEs, with `capa.jpg`. Re-rendered? `gh release upload videos saida/<id>.<lingua>.mp4 --clobber`.
   Publishing is the repository owner's decision.
5. **Remotion pinned at 4.0.534** (exact version in `package.json`). Free for individuals and companies of up
   to 3 people.
6. **No repository address on the screen** (decision of the repository owner, 2026-10-14): the closings show the
   brand; the speech says "é só baixar no GitHub" ("just download it on GitHub") and that is enough.
7. **Real screens, not drawings,** for everything that is Clave: screenshots of the demo, with zoom, cursor and
   highlight. A drawing only for what isn't Clave (the Console, the Windows folder, the installer's steps: the
   installer prints only Portuguese, so the video shows its four steps as a list in the video's language).
8. **No Portuguese in the English video and vice versa**: the screen text goes through `T()` (missing translation =
   render error), the screenshots are taken with the app in each language and the demo's files and answers exist in
   both. The English voice is `en-US-AvaMultilingualNeural` (the "Multilingual" sibling of the Portuguese voice).
9. **15 MB per video**: x264 `-preset slow -tune animation`, CRF from 23 up, `yuv420p` in TV range (Remotion
   delivers full range, `yuvj420p`, which some players show with the wrong contrast), AAC 128 kbps, `+faststart` (they
   are downloaded and played straight in the app). At CRF 23 they come out between 7 and 9.5 MB.
10. **In the tutorials the music ducks under the voice** (`trilha: 0.26` and `abaixaTrilha: 0.6` in
   `src/videos/*.ts`; the pitch keeps 0.32 with no ducking): they talk more. Even so, with any music under it Whisper
   heard "Download Claude" where the English voice says "Download Clave" (without music it heard it right), so the
   line became "Download the Clave app". In the Portuguese pitch, "usa o Clód pela A P I" came out "Cloud API":
   a comma after "Clód" fixed it. `remotion render ... --codec wav` renders only the audio in ~25 s, which is the
   quick way to test a line with the music before rendering the video.

## Pitfalls

- **The Chrome that Remotion downloads is blocked by Smart App Control** ("spawn UNKNOWN"). `remotion.config.ts`
  points to the Windows Edge, which runs. `videos.py` calls `node_modules\.bin\remotion.cmd` through `cmd /c`.
- `edge-tts` uses Edge's read-aloud service: it needs internet and may change without notice. If it stops, the
  old narration stays in `public/narracao/` until someone runs `npm run narrar` again.
- Text that rises word by word (`Sobe`) separates the words with a margin, not a space: a space at the end of
  an `inline-block` disappears.
- A cover is a frozen frame inside a composition as long as the video: with a 1-frame composition every
  `<Sequence>` after frame 0 is cut and the cover comes out blank.
- `telas.py` uses ports 8051 and 9351; if something else is on them, pass `--porta` and `--porta-edge`. The app
  changes with every version: if a screenshot breaks ("não achei o alvo..."), the selector in `roteiro()` is what
  changed. After a change in the app, run `npm run telas` again and look at the screens before rendering.
- Editing these files from Git Bash with a heredoc eats backslashes: use a `.py` script or the editor.
