---
titulo: Busca na web e conectores
trilha: 4. Ir além
ordem: 36
duracao: 4 min
resumo: Deixar o Claude pesquisar na internet e ligar serviços externos pelo padrão MCP.
---

## Busca na web

Sem a busca, o Claude só sabe o que aprendeu até a data de corte dele (meados de 2026) e não sabe o que aconteceu ontem. Por isso a busca na web vem ligada: ele **pesquisa e lê páginas** sozinho quando a resposta precisa de algo atual. Para uma conversa sem busca, clique no botão **Web** da caixa de texto (ele apaga só ali); para desligar de vez, vá em Configurações > Recursos. As fontes aparecem na resposta (números pequenos ao lado das frases e a lista de sites).

Cada pesquisa custa US$ 0,01, além dos tokens das páginas lidas.

```experimentar
Quais foram as principais notícias de tecnologia desta semana? Cite as fontes.
```

## E-mail

Em **Configurações > Conectores > E-mail**, ligue a sua caixa de e-mail. Daí o Claude lê, procura e resume os seus e-mails e escreve respostas. **Enviar sempre mostra o e-mail inteiro e espera o seu OK.**

- **Gmail**: ligue a verificação em duas etapas na Conta Google e crie uma **senha de app** em myaccount.google.com/apppasswords (16 letras). Cole essa senha, não a sua senha normal.
- **Yahoo, Zoho e o e-mail do site da empresa** (hospedagem): também com senha de app ou a senha da caixa, e os servidores IMAP e SMTP que o provedor informa.
- **Outlook.com e Microsoft 365** não aceitam mais senha por fora. Use **Outlook do computador** (o Outlook clássico instalado, já com a sua conta) ou o Zapier.

```experimentar
Resuma os e-mails não lidos de hoje e me diga quais precisam de resposta.
```

## Zapier

O Zapier liga o Claude a centenas de apps (Planilhas e Agenda do Google, WhatsApp Business, CRMs) sem programar. Em **Configurações > Conectores > Zapier** tem o passo a passo: você cria o servidor em mcp.zapier.com, escolhe as ações que quer liberar e cola o endereço no Clave. É um serviço de fora, com plano grátis limitado.

Para algo que se repete sempre do mesmo jeito, compare antes com um programa sem IA: veja [Um app de pedidos sem IA](#/aprender/app-de-pedidos-sem-ia).

## Conectores (MCP)

[MCP](#/aprender/glossario/mcp) é um padrão para ligar a IA a outros serviços. Um conector dá ao Claude ferramentas novas: consultar a documentação de um programa, buscar num sistema, ler um banco de dados.

Em **Configurações > Conectores**, adicione o nome e o endereço (https://...) de um servidor MCP. Quem se conecta é a própria Anthropic, então:

- só funcionam servidores **públicos na internet** (não os que rodam no seu computador);
- use só serviços em que você confia: o que o Claude manda para eles sai do seu controle.

Um exemplo público e gratuito é o DeepWiki (`https://mcp.deepwiki.com/mcp`), que explica projetos do GitHub.

```experimentar
Use o conector DeepWiki para me explicar, em linguagem simples, o que faz o projeto anthropics/anthropic-sdk-python.
```
