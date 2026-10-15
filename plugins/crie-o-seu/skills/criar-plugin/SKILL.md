---
name: criar-plugin
description: Use quando a pessoa quiser juntar skills, agentes e comandos num pacote (plugin) para reaproveitar em outro computador ou compartilhar com outras pessoas, no formato do Claude Code.
---

# Criar um plugin

Um plugin é uma pasta que junta skills, agentes e comandos. O formato é o mesmo dos plugins do Claude Code.

## Estrutura

```
meu-plugin/
├── .claude-plugin/plugin.json
├── skills/<nome>/SKILL.md
├── agents/<nome>.md
├── commands/<nome>.md
└── README.md
```

`plugin.json` (só `name` é obrigatório):

```json
{
  "name": "meu-plugin",
  "version": "1.0.0",
  "description": "O que o plugin traz, em uma frase",
  "author": {"name": "Seu nome"}
}
```

No Clave dá para pôr também `fluxos/*.json` (modelos de fluxo); o Claude Code ignora essa pasta.

## Testar no Clave
Barra da esquerda > **Plugins** > **Instalar de uma pasta** > escolha a pasta do plugin. As skills aparecem como `/meu-plugin:nome`.

## Compartilhar
- Suba a pasta num repositório **público** do GitHub. Quem usa o Clave instala em Plugins > **Instalar do GitHub** com `seu-usuario/repositorio`; no Claude Code, com `/plugin marketplace add`.
- Para vários plugins num repositório só, crie `.claude-plugin/marketplace.json` na raiz:

```json
{"name": "minha-loja", "owner": {"name": "Seu nome"},
 "plugins": [{"name": "meu-plugin", "source": "./meu-plugin"}]}
```

- Nunca ponha senha, chave ou dado pessoal num plugin: ele fica público.
