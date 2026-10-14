# Leia primeiro: a sua pasta de trabalho com o Claude

Esta pasta foi criada a partir do **modelo do Clave**. Ela já vem preparada para
o Claude trabalhar bem aqui dentro, no **modo Code do Clave** ou no **Claude
Code** (o programa da Anthropic para programar).

## O que tem aqui

| Arquivo ou pasta | Para quê |
|---|---|
| `CLAUDE.md` | As regras da pasta, que o Claude lê sozinho. A seção 0 (Sobre mim) é sua: ajuste quando quiser. |
| `.claude/skills/` | Procedimentos prontos (ver vídeos, revisar código, visual de sites e outros). |
| `.claude/referencias-visuais/` | Biblioteca de referências para sites e apps não ficarem com cara genérica. |
| `.claude/launch.json` e `PORTAS.md` | Como rodar cada projeto web e em que porta (o Claude preenche). |
| `_organizacao/` | Scripts de manutenção e o guia de instalação de ferramentas. |

## Como usar

1. **Cada projeto é uma subpasta**: `orcamento-da-casa`, `site-da-loja`,
   `planilhas-do-trabalho`. Peça ao Claude: "crie um projeto novo para X".
2. Trabalhe pelo modo Code do Clave escolhendo **esta pasta** (ou a subpasta do
   projeto): as regras e as skills daqui valem para as subpastas.
3. Na primeira vez, rode `/inicializar-pasta` (se já houver projetos aqui) para
   o Claude montar o mapa dos projetos.

## Personalize

- Abra o `CLAUDE.md` e complete a seção **0. Sobre mim**: quanto mais o Claude
  souber sobre você, melhores as respostas.
- Mude qualquer regra que não combine com você. O arquivo é seu.
- Repetiu uma tarefa e ficou bom? Peça ao Claude para transformar em skill.

## Ferramentas úteis

O guia `_organizacao/instalar-ferramentas.md` explica como instalar Git, GitHub
CLI, Python e Node.js, se você precisar. O Claude também pode fazer isso por
você (ele pede o seu OK antes).
