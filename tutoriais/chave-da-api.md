---
titulo: Sua chave da API e quanto custa
trilha: 1. Primeiros passos
ordem: 2
duracao: 6 min
resumo: Como criar a conta na Anthropic, pegar a chave, pôr crédito e não gastar mais do que quer.
video: chave-da-api
---

O Clave conversa com o Claude pela [API](#/aprender/glossario/api) da Anthropic. Para isso ele precisa da sua [chave da API](#/aprender/glossario/chave-da-api): uma senha comprida que diz de qual conta sai o pagamento.

## Como funciona o pagamento

Não tem mensalidade. Você coloca **crédito** na sua conta da Anthropic e cada resposta desconta um pouquinho, conforme o tamanho do texto (contado em [tokens](#/aprender/glossario/token)). Uma pergunta curta no Haiku custa menos de um centavo de dólar; uma conversa longa no Opus, alguns centavos.

**Assina o Claude Max?** O plano Max dá crédito mensal na API (US$ 100 no Max 5x, US$ 200 no Max 20x). Para ativar: em claude.ai, abra **Settings > Billing > API credits** e vincule uma organização do Console. Esse crédito não acumula de um mês para o outro.

## Passo a passo para pegar a chave

1. Entre em **platform.claude.com** (o Console da Anthropic) e crie uma conta, ou entre com a sua.
2. Coloque crédito em **Billing** (ou ative o crédito do plano Max, como explicado acima).
3. No menu, abra **API Keys** e clique em **Create Key**. Dê um nome, como "Clave".
4. Copie a chave (ela começa com `sk-ant-`). Ela só aparece inteira uma vez: se perder, é só criar outra.
5. No Clave, abra **Configurações > Conta e chave**, cole e clique em **Conferir e salvar**.

O Clave confere a chave com a Anthropic antes de salvar e guarda ela **criptografada, só neste computador**.

## Regras de ouro da chave

- **Nunca mostre a chave para ninguém** e nunca cole em sites ou conversas. Quem tem a chave gasta o seu crédito.
- Se achar que ela vazou, apague no Console (API Keys) e crie outra.
- Não precisa guardar a chave em outro lugar: se perder, crie uma nova.

## Para não gastar mais do que quer

O Clave tem um **teto por mês**: quando a soma chega lá, ele para de responder até o mês virar (ou só avisa, se você preferir). Configure em **Configurações > Limite de gasto** e acompanhe em **Uso e gasto**, na barra da esquerda. O "tinteiro" no canto da barra mostra quanto do mês já foi.

Dois detalhes importantes:

- O Clave só enxerga o que **ele** gasta. Se a mesma conta da Anthropic é usada por outros programas, informe esse gasto em **Uso e gasto** para o teto ficar certo.
- Para uma trava que nem o Clave consegue passar, crie no Console um *workspace* com limite de gasto e use uma chave desse workspace.

## Dicas para gastar menos

- Use o **Haiku 5.5** para perguntas simples: custa 40 vezes menos que o Opus.
- Raciocínio em **Baixo** ou **Médio** resolve a maior parte das coisas.
- Mudou de assunto? **Comece uma conversa nova**: conversa comprida encarece cada resposta.

```experimentar
Explique para mim, com números de exemplo, quanto custaria usar a IA para responder 30 e-mails por dia durante um mês.
```
