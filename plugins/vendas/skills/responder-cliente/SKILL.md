---
name: responder-cliente
description: Use to answer a client's message (a question, a complaint, a delay, a price negotiation or a discount request) in the company's tone. Uses only facts the person provides, never invents prices, deadlines or policies, and offers a short and a complete version.
---

# Answer a client

Write everything the person reads in their language. The reply goes in the client's language (in Brazil, Portuguese).

## 1. Read the message carefully
- What does the client want: information, a solution, a discount, a new deadline, to cancel?
- Mood: neutral, irritated, in a hurry. Channel: e-mail or WhatsApp.
- History: order or proposal number, what was already promised, earlier messages if the person pasted them.

## 2. Separate the facts
List what the answer depends on: price, stock, delivery date, order status, nota fiscal, exchange and return policy, warranty, payment.
- Use **only** what the person told you or files they pointed to (price list, policy, order sheet). Read those files.
- A fact is missing: ask the person, or leave a visible placeholder (`[CONFIRMAR PRAZO]`) and point it out.
- **Never promise** a refund, discount, free freight, exchange, credit or date unless the person said the company does it.
- Don't quote laws or legal deadlines from memory. If the client mentions Procon, a lawyer or legal action: reply politely, without admitting fault or promising anything, and tell the person to involve whoever handles this in the company before sending.

## 3. Tone
- If there are earlier replies of the company or a tone guide in the folder (or in CLAUDE.md), follow them. Otherwise: cordial and direct.
- Address the client the way they wrote ("você" or "o senhor / a senhora") and by name. No "Prezado cliente" when you know the name.
- No blaming the client, no internal excuses ("o sistema caiu", "o fornecedor atrasou") unless the person wants them said.

## 4. By type of message
- **Question:** the answer in the first line, details after.
- **Complaint:** name the specific problem (not a generic "lamentamos o transtorno"), say what will be done and when (only what the person confirmed), and give one contact.
- **Delay:** the truth, the new date only if confirmed, and what is being done meanwhile.
- **Price negotiation or discount request:** don't give anything on your own. Prepare options for the person to choose, within limits they set:
  - keep the price and reinforce the value (delivery time, warranty, service, what is included);
  - a conditional discount (payment upfront by Pix, a bigger quantity, a longer delivery time);
  - ask what the competitor's offer includes before matching a price.
  Never mention cost or margin.
- **Request outside the policy:** a polite no and an alternative that the person confirmed exists.

## 5. Deliver two versions
1. **Short** (WhatsApp, 2 to 4 lines).
2. **Complete** (e-mail): subject, greeting with the name, 1 to 3 short paragraphs, the next step with a date when there is one, signature.

Below the versions, a note for the person (not part of the reply) with what to confirm: placeholders, the risky points ("esta resposta não promete reembolso; se a empresa for reembolsar, troque o segundo parágrafo").

Example of a short reply to a discount request (Portuguese):

> Oi, Rafael! Consigo manter os R$ 4.380,00 com entrega em 7 dias úteis. Se o pagamento for à vista no Pix, fica R$ 4.161,00 (5% de desconto). Fecho assim para você?

(Only because, in this example, the person had authorized up to 5% for Pix: R$ 4.380,00 × 0,95 = R$ 4.161,00.)

## 6. Sending
If `email_enviar` is in your tool list, draft the e-mail and send it only after the person approves that message; Clave asks for an OK on every send. Without the tool, deliver the text ready to copy.

## Before saying it's done
- [ ] Every price, date, condition and policy in the reply came from the person or from their files.
- [ ] Client name and order or proposal number are right.
- [ ] One clear next step.
- [ ] Discount math checked, if there is a discount.
- [ ] Placeholders and risky points listed in the note.
