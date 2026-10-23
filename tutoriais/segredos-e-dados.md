---
titulo: Senhas, chaves e dados pessoais: o que nunca colar
trilha: 8. Usar com segurança
ordem: 71
duracao: 7 min
resumo: A chave da API, senhas, cartões e documentos: o que vai para a Anthropic, o que fica no computador e como trabalhar sem expor nada.
---

Tudo o que você escreve ou anexa numa conversa vai para a Anthropic (é assim que o Claude responde) e fica guardado na conversa, no seu computador. Para quase tudo, isso é ótimo. Para senha, chave e número de cartão, não.

## O que nunca colar na conversa

- A sua [chave da API](#/aprender/glossario/chave-da-api) e qualquer outra chave ou [token de acesso](#/aprender/glossario/token-de-acesso).
- Senhas de qualquer conta, inclusive a senha de app do e-mail.
- Número de cartão, código de segurança, senha do banco, código que chegou por SMS.
- Documentos completos de outras pessoas (RG, CPF, exames, contratos), a não ser que seja mesmo necessário.

Por quê:

- vai para a Anthropic junto com a mensagem;
- fica gravado na conversa, num arquivo comum do seu computador, sem a [criptografia](#/aprender/glossario/criptografia) que protege a chave;
- entra no backup das conversas e na conversa exportada;
- com a [memória](#/aprender/memoria) ligada, pode virar uma anotação;
- e o Claude não precisa disso: para entrar num serviço existe um jeito melhor (veja abaixo).

**Colou sem querer?** Troque a senha (ou apague a chave no Console, como explicado abaixo). Apagar a conversa tira o texto do Clave, mas ele já foi enviado, e os backups que você baixou antes continuam com ele.

## A chave da API

Em Configurações > Conta e chave, o Clave guarda a chave criptografada pelo Windows, presa ao seu usuário: copiada para outro computador, ela não abre.

- Nunca mostre a chave: nada de print, mensagem, e-mail, site, script ou GitHub. Quem tem a chave gasta o seu crédito.
- Chave que foi parar num repositório público do GitHub está vazada, mesmo que você apague depois: o histórico do [Git](#/aprender/glossario/git) guarda as versões antigas.
- **Vazou?** Entre no Console da Anthropic (platform.claude.com), abra **API Keys** e apague a chave. Crie outra e cole em Configurações > Conta e chave > **Colar uma chave nova** > **Conferir e salvar**.
- Use o **teto do mês** (Configurações > Limite de gasto) e, para uma trava extra, um workspace com limite de gasto no Console. A lição [Sua chave da API](#/aprender/chave-da-api) explica, e [Acompanhar e travar o gasto](#/aprender/acompanhar-o-gasto) mostra como notar um gasto estranho.

## Senhas que um programa precisa

Às vezes uma automação precisa entrar no e-mail ou num site. A senha não vai na conversa nem dentro do código: vai para o **Gerenciador de Credenciais do Windows**, o cofre de senhas que já vem no Windows. Você digita a senha uma vez, numa janela do próprio programa, e o programa pega de lá.

```experimentar-code
Vou precisar de uma senha de site num script desta pasta. Não me peça a senha aqui na conversa. Guarde a senha no Gerenciador de Credenciais do Windows (biblioteca keyring), crie um configurar.bat que pergunta a senha numa janela e faça o script ler de lá. Nunca escreva a senha em log nem na tela.
```

A lição [Um app de pedidos sem IA](#/aprender/app-de-pedidos-sem-ia) mostra esse jeito num exemplo completo, e [Automatizar sem pagar a IA toda vez](#/aprender/automatizar-sem-ia) explica quando um programa assim vale a pena.

## Senhas que o Clave guarda

- **E-mail** (Configurações > Conectores > E-mail): use uma **senha de app**, uma senha só para o Clave que você apaga quando quiser, nunca a sua senha normal. Ela fica guardada criptografada neste computador, só para o e-mail.
- **GitHub** e **conectores**: o token também fica criptografado e serve só para entrar no próprio serviço.
- **Zapier**: libere só as ações de que você precisa.
- **Navegador do Code**: os sites em que você entrar por ele continuam logados. **Apagar os dados do navegador** (Configurações > Modo Code) apaga esses logins e cookies.
- **Sair da conta** (Configurações > Atualizações e sobre) apaga deste computador a chave, todas essas senhas e os dados do navegador do Code.

## Cartões e compras

O Claude nunca precisa do número do seu cartão. No navegador do modo Code, ele pode abrir e ler as páginas de uma loja, mas **senha, código de acesso e cartão quem digita é você**: o Clave não deixa o Claude preencher esses campos. Na hora de pagar ou de entrar numa conta, ele pede e você assume.

## Arquivos protegidos no modo Code

Em Configurações > Modo Code fica a lista **Arquivos e pastas protegidos**. Ela já vem com os arquivos de senha e chave mais comuns de quem programa (`.env`, `*.key`, `*.pem`, `*.pfx`, as pastas `.ssh` e `.aws`) e com a pasta `.git`, onde mora o histórico do Git.

- As ferramentas de arquivo **nunca** leem nem mudam o que está na lista.
- Um comando que cite um desses arquivos **sempre** pede o seu OK.
- Ponha ali o que for sensível, um por linha: `senhas.txt`, `documentos/**`.

A lista protege bem contra engano, mas um comando não tem como saber tudo o que vai tocar. O jeito mais seguro é deixar senhas e documentos **fora da pasta de trabalho**: no modo Code, as ferramentas de arquivo pedem o seu OK toda vez para ler ou mudar qualquer coisa fora dela (menos no modo **Livre**, que não pergunta), a não ser que uma [regra de permissão](#/aprender/permissoes) sua libere.

## Dados pessoais e documentos

Antes de mandar uma planilha de clientes, um contrato ou um exame, pense no que o Claude precisa de verdade:

- troque nomes por "Cliente 1", "Cliente 2";
- tire as colunas de CPF, telefone e endereço se a pergunta é sobre vendas;
- mande só a página do contrato que importa;
- num print, corte o que não tem a ver.

```experimentar
Quero te mandar uma planilha de clientes para analisar as vendas do ano. Quais colunas eu deveria tirar ou trocar antes, para não expor dados pessoais, sem estragar a análise?
```

No modo Code tem um truque: um [script](#/aprender/glossario/script) que roda no seu computador mexe nos dados **sem mandar nada para a Anthropic**. Só vai o que o Claude lê ou o que o comando mostra na tela. Então peça um programa que faça o serviço sem mostrar os dados:

```experimentar-code
Crie um script que faça uma cópia de clientes.xlsx chamada clientes-sem-dados.xlsx, trocando os nomes por Cliente 1, Cliente 2... e apagando as colunas de CPF, telefone e endereço. Leia só a primeira linha da planilha (os nomes das colunas) e não mostre nenhum outro dado na tela.
```

## O que vai para onde

| O quê | Sai do computador? | Onde fica guardado |
|---|---|---|
| Suas mensagens e anexos | vão para a Anthropic a cada resposta | na conversa, no seu computador |
| O que o Claude lê no modo Code, o que um comando mostra na tela, o que ele vê no navegador do Code | vai para a Anthropic | na conversa |
| Memórias | só o que ele lê numa conversa | em arquivos de texto, no seu computador |
| Chave da API, senha de app do e-mail, tokens do GitHub e dos conectores | cada um só para entrar no próprio serviço | criptografados, no seu computador |
| Histórico de gasto e configurações | não saem | no seu computador |
| Seus arquivos no GitHub | só o que você pedir para enviar | no GitHub |

Os widgets também usam a internet: os mapas vêm do OpenStreetMap, e as fotos de outros sites só carregam quando você clica (o motivo está em [Quando uma página ou arquivo tenta dar ordens ao Claude](#/aprender/injecao-de-instrucoes)).

Pelo que a Anthropic informa, por padrão o que passa pela API não é usado para treinar modelos (veja [Por que usar o Clave](#/aprender/por-que-o-clave)). Mesmo assim, a regra continua: mande só o necessário. Mais detalhes em [Segurança e privacidade](#/aprender/seguranca-e-privacidade).
