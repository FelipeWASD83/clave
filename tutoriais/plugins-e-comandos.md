---
titulo: Plugins e comandos de barra
trilha: 4. Ir além
ordem: 37
duracao: 5 min
resumo: Pacotes prontos de skills, agentes e fluxos, e os atalhos que começam com /.
---

## Comandos de barra

Digite `/` na caixa de mensagem e aparece a lista de atalhos:

- **Do Clave:** `/novo`, `/modelo haiku`, `/esforco alto`, `/plano` (modo Plano no Code), `/custo`, `/fluxo`, `/memoria`, `/permissoes`, `/plugins`, `/ajuda`.
- **Comandos:** pedidos prontos com espaço para completar, como `/escrita:email para o fornecedor pedindo prazo`.
- **Skills:** chamar uma [skill](#/aprender/glossario/skill) direto, como `/escritorio:excel-avancado`.

Você cria os seus comandos num arquivo `.claude/commands/nome.md` (dentro da pasta ou na sua pasta pessoal). O texto vira a mensagem, e `$ARGUMENTS` é trocado pelo que você escrever depois do comando. Ou peça ao Claude: `/crie-o-seu:nova-skill`.

## Plugins

Um **plugin** junta skills, agentes, comandos e fluxos para um tipo de trabalho. O Clave vem com sete:

| Plugin | Para quê |
|---|---|
| Escritório | Excel, relatório em PDF, limpar e comparar planilhas |
| Automação no Windows | scripts que dá para rodar de novo, Agendador de Tarefas, organizar e renomear arquivos |
| Pesquisa | pesquisar com fontes e comparar opções |
| Escrita | e-mail, revisão de texto, resumo, ata de reunião |
| Sites e apps | páginas num arquivo só, conferência antes de publicar, como publicar |
| Programação | achar a causa de um erro, testes, revisar e explicar código |
| Crie o seu | o Claude te ajuda a criar skills, agentes, comandos e plugins |

Em **Plugins** (barra da esquerda) você liga e desliga cada um. Desligado, nada dele aparece para o Claude.

## Instalar outros

O formato é o mesmo dos plugins do Claude Code, então dá para instalar os que outras pessoas publicam:

- **Instalar do GitHub:** escreva `dono/repositório`. O Clave baixa, mostra o que o plugin traz e só instala depois do seu OK.
- **Instalar de uma pasta:** para um plugin que você fez ou baixou.

Instale só de quem você confia: um plugin traz instruções para o Claude. Os comandos que ele sugerir continuam passando pelas suas [permissões](#/aprender/permissoes).
