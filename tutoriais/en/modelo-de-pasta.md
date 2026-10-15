---
titulo: The folder template (recommended)
trilha: 4. Going further
ordem: 30
duracao: 7 min
resumo: A ready-made folder with rules, skills and visual references that makes Claude work much better.
---

**Strong recommendation:** if you are going to use Code mode for more than a one-off task, start with a folder created from the **template**. It is the difference between an assistant you have to explain everything to every time and one that already knows how you work.

The template was built from the working folder of someone who uses Claude every day on dozens of projects, with what really worked and nothing personal.

## What comes inside

- **CLAUDE.md**: the folder's rules, which Claude reads on its own. It already includes tested good practices: plan before changing things, don't make up results, check before saying you are done, one project per folder, keep versions with Git, explain in simple language. At the top there is an **About me** section that Clave fills in with your answers.
- **Skills** (ready-made procedures):
  - *ver-video*: Claude "watches" videos (a file or a link from YouTube, TikTok, Instagram...) by taking frames and transcribing the speech. [See the lesson](#/aprender/ver-videos).
  - *direcao-visual* and *revisar-visual*: decide how a website should look before building it, and check the result with screenshots.
  - *checklist-web* and *entregar-site*: everything that has to be right before saying a website is ready or publishing it.
  - *revisar-codigo*: looks for what was left half-done or only pretends to work.
  - *pesquisa-tecnica*: research before choosing a tool or library.
  - *gml*: for people who make games in GameMaker.
  - *inicializar-pasta*: sets up the folder and the project map the first time.
- **Visual references**: a library of well-made websites, with screenshots and what to take from each one, so the sites Claude builds don't end up looking like a "generic AI site".
- **Guides**: READ-ME-FIRST, PORTAS (for web projects) and instalar-ferramentas (Git, GitHub, Python, Node).

## How to create one

1. **New Code task** > **Create folder with the template**.
2. Choose where to create it (Documents, for example) and the folder name.
3. Answer the questions about yourself: they go into the CLAUDE.md.
4. Done: Clave already opens Code mode in the new folder.

Each of your projects becomes a **subfolder** inside it (`home-budget`, `shop-website`...). The parent folder's rules and skills apply to all of them.

## After creating it

Open the `CLAUDE.md` (in a text editor, or ask Claude to show it) and adjust whatever you like. It is yours: the more it reflects your way of working, the better the answers.

```experimentar-code
Read the CLAUDE.md in this folder and explain to me, in short bullet points, the rules you are going to follow here. Then ask me what I want to change.
```

## It also works in Claude Code

The template uses the same files as Claude Code (Anthropic's official program for coding). If you ever use Claude Code, open the same folder in it: the rules and skills work just the same.
