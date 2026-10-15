---
titulo: Your API key and what it costs
trilha: 1. First steps
ordem: 2
duracao: 6 min
resumo: How to create your Anthropic account, get your key, add credit and avoid spending more than you want.
video: chave-da-api
---

Clave talks to Claude through Anthropic's [API](#/aprender/glossario/api). To do that, it needs your [API key](#/aprender/glossario/chave-da-api): a long password that tells Anthropic which account the payment comes out of.

## How payment works

There is no monthly fee. You put **credit** on your Anthropic account and each answer takes a tiny bit off, depending on the size of the text (counted in [tokens](#/aprender/glossario/token)). A short question on Haiku costs less than a cent; a long conversation on Opus costs a few cents.

**Do you subscribe to Claude Max?** The Max plan gives monthly API credit ($100 on Max 5x, $200 on Max 20x). To turn it on: on claude.ai, open **Settings > Billing > API credits** and link a Console organization. That credit doesn't carry over from one month to the next.

## Step by step to get the key

1. Go to **platform.claude.com** (Anthropic's Console) and create an account, or sign in to yours.
2. Add credit under **Billing** (or turn on the Max plan credit, as explained above).
3. In the menu, open **API Keys** and click **Create Key**. Give it a name, like "Clave".
4. Copy the key (it starts with `sk-ant-`). It only shows in full once: if you lose it, just create another.
5. In Clave, open **Settings > Account & key**, paste it and click **Check and save**.

Clave checks the key with Anthropic before saving it, and stores it **encrypted, on this computer only**.

## Golden rules for the key

- **Never show the key to anyone** and never paste it into websites or chats. Whoever has the key spends your credit.
- If you think it leaked, delete it in the Console (API Keys) and create another.
- You don't need to keep the key anywhere else: if you lose it, create a new one.

## So you don't spend more than you want

Clave has a **monthly cap**: when the total reaches it, Clave stops answering until the month rolls over (or only warns you, if you prefer). Set it up in **Settings > Spending limit** and follow along in **Usage & spend**, in the left sidebar. The little "inkwell" in the corner of the sidebar shows how much of the month is already used.

Two important details:

- Clave can only see what **it** spends. If the same Anthropic account is used by other programs, enter that spending in **Usage & spend** so the cap is accurate.
- For a limit that even Clave can't get past, create a *workspace* with a spending limit in the Console and use a key from that workspace.

## Tips to spend less

- Use **Haiku 5.5** for simple questions: it costs 40 times less than Opus.
- Reasoning at **Low** or **Medium** handles most things.
- Changed the subject? **Start a new chat**: a long conversation makes every answer more expensive.

```experimentar
Explain to me, with example numbers, how much it would cost to use AI to answer 30 emails a day for a month.
```
