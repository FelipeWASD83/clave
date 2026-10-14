---
titulo: Busca na web e conectores
trilha: 4. Ir além
ordem: 36
duracao: 4 min
resumo: Deixar o Claude pesquisar na internet e ligar serviços externos pelo padrão MCP.
---

## Busca na web

Sem a busca, o Claude só sabe o que aprendeu até a data de corte dele (meados de 2026) e não sabe o que aconteceu ontem. Ligue o botão **Web** na caixa de texto para ele **pesquisar e ler páginas** quando precisar. As fontes aparecem na resposta (números pequenos ao lado das frases e a lista de sites).

Cada pesquisa custa US$ 0,01, além dos tokens das páginas lidas. Para deixar ligada sempre: Configurações > Recursos.

```experimentar
Quais foram as principais notícias de tecnologia desta semana? Cite as fontes.
```

## Conectores (MCP)

[MCP](#/aprender/glossario/mcp) é um padrão para ligar a IA a outros serviços. Um conector dá ao Claude ferramentas novas: consultar a documentação de um programa, buscar num sistema, ler um banco de dados.

Em **Configurações > Conectores**, adicione o nome e o endereço (https://...) de um servidor MCP. Quem se conecta é a própria Anthropic, então:

- só funcionam servidores **públicos na internet** (não os que rodam no seu computador);
- use só serviços em que você confia: o que o Claude manda para eles sai do seu controle.

Um exemplo público e gratuito é o DeepWiki (`https://mcp.deepwiki.com/mcp`), que explica projetos do GitHub.

```experimentar
Use o conector DeepWiki para me explicar, em linguagem simples, o que faz o projeto anthropics/anthropic-sdk-python.
```
