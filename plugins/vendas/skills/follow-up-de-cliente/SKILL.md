---
name: follow-up-de-cliente
description: Use to write follow-up e-mails or messages to clients: a proposal that got no answer, a quote about to expire, or after a sale (thanks, delivery, satisfaction, reorder). Short and polite, one clear call to action, on a 2, 5 and 10 day cadence.
---

# Client follow-up

Write everything the person reads in their language. The messages go in the client's language (in Brazil, Portuguese).

## 1. Context, only from what the person gives
- **Who:** company, contact name, how they are addressed ("você" or "o senhor / a senhora"; copy what the previous messages used).
- **What was sent and when:** proposal number, date, total, validity, the main item.
- **History:** last contact, objections already raised (price, deadline, freight), channel (e-mail or WhatsApp).
- **Goal of this message:** get an answer, book a call, close, ask for feedback, get a reorder.

Never invent: no fake urgency ("últimas unidades", "preço sobe amanhã") unless the person says it is true, no discount or gift they did not authorize, no deadline they did not confirm.

## 2. Cadence after a proposal
Count from the day the proposal was sent. Ask whether the office counts calendar days or business days (dias úteis) and say which you used.

| When | Goal | Tone |
|---|---|---|
| Day 2 | Confirm it arrived and offer to clarify | light |
| Day 5 | Add something useful: answer the likely doubt, remind the strongest point, offer a short call with two time options | helpful |
| Day 10 | Close the loop: remind the validity and ask directly whether to move on or come back later | respectful, last one |

- If the proposal expires before day 10, the last message goes out before it expires.
- After the third message with no answer, stop. Suggest a note to try again in 30 to 60 days. Never more than 3 messages in a row without an answer.

## 3. Cadence after a sale
- Day 0 or 1: thanks, and what happens next (nota fiscal, delivery date, boleto due dates).
- 2 or 3 days after delivery: did everything arrive right? Who to call if not.
- After the product's usual cycle (e.g. 30 days): one single ask, either satisfaction, reorder or a referral.

## 4. How each message is written
- **E-mail subject:** specific, with the client and the proposal ("Proposta 2026-041 - Uniformes: ficou alguma dúvida?"). Not "Follow-up" alone, no capital letters shouting, no "URGENTE".
- 3 to 6 lines. The first line says why you are writing.
- Repeat the key data (number, total, validity) so the client doesn't have to search.
- **One** call to action, easy to answer: a yes or no, or two times for a call.
- Signature: seller's name, company, phone.
- **WhatsApp version:** 2 or 3 lines, no subject, friendly but professional.

Example of a day 5 e-mail (Portuguese):

> Assunto: Proposta 2026-041: posso ajudar a decidir?
>
> Oi, Carla! Na proposta dos 120 kits (R$ 8.640,00, válida até 30/10), o prazo de entrega é o ponto que mais pesa, então confirmo: 10 dias úteis depois do pedido.
> Se ajudar, falamos 10 minutos amanhã às 10h ou às 15h. Qual fica melhor?
>
> Marcos, Exemplo Distribuidora, (11) 0000-0000

## 5. With Clave's e-mail tools
If `email_ler` and `email_enviar` are in your tool list:
- Use `email_ler` to find the original proposal and check whether the client already answered. Never send a follow-up to someone who already replied.
- Draft every message first and show them all.
- Send only after the person approves **each** e-mail; Clave asks for an OK on every send. Never send in a batch, never send "to test".
- If the tool can reply in the original thread, prefer that: the client sees the history.

Without those tools: deliver the texts ready to copy, each with its subject, plus a table: date to send | client | channel | message.

## 6. Keep track
Offer a follow-up spreadsheet (in Code mode with `excel_alterar`, in chat with `planilha_criar`): Cliente | Proposta | Valor | Enviada em | Follow-up 1 | Follow-up 2 | Follow-up 3 | Status (aguardando, respondeu, fechou, perdeu) | Motivo da perda.
- Dates with formulas in English with commas: `=D2+2` for calendar days, `=WORKDAY(D2,2)` for business days.
- Status as a dropdown list (`validacao_lista`).

If the person wants a daily list of "who is due today", that part needs no AI: offer the skill `vendas:automacao-sem-ia`. AI is worth it only to write the message itself.

## Before saying it's done
- [ ] Each message has one call to action and the right client name, proposal number, total and validity.
- [ ] Nothing promised that the person did not confirm.
- [ ] The cadence dates are right (weekends skipped if they use business days).
- [ ] Nothing was sent without the person's approval of that specific message.
