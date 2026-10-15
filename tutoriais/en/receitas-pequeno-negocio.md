---
titulo: For a small business
trilha: 9. Recipes by area
ordem: 82
duracao: reference
resumo: Price list, quotes and proposals, follow-ups, orders without AI, posts and a delivery map, with the cheapest model that can handle it.
---

Ready-made requests for anyone running a small business: a shop, a bakery, a repair shop, a service provider. Click the button on each recipe: the request goes into the text box (of a new chat or of Code mode), and you replace what's in square brackets and the examples with your business's details before sending.

Several recipes use the **Sales** plugin, which comes with Clave and is already on (you can turn it on and off in **Plugins**, in the left sidebar). Its commands start with `/sales:`; see [Plugins and slash commands](#/aprender/plugins-e-comandos).

Clave starts on **Haiku 5.5**, the cheapest, and it handles almost everything here. The model advisor tells you when a task needs another one (see [The right model for the lowest price](#/aprender/modelo-certo-mais-barato)).

| Recipe | Where | Model |
|---|---|---|
| Price list with margin | chat | Haiku |
| Quote and proposal in Word and PDF | Code mode | Haiku (Sonnet for a big proposal) |
| Follow up with who didn't answer | chat | Haiku |
| Answer a customer | chat | Haiku |
| Orders in the spreadsheet (and an app without AI) | Code mode | Haiku |
| Social media posts | chat, with a widget | Haiku |
| Delivery map | chat, with a widget | Haiku |
| Sales report | chat or Code mode | Haiku (Sonnet for a big spreadsheet) |

## 1. Price list with margin

```experimentar
Create a price list spreadsheet for my bakery with the columns Product, Ingredient cost, Packaging, Total cost, Target margin (%) and Sale price, with formulas so I only have to change the costs and the margin. Fill it in with 5 sample products and highlight in red the products with a margin below 30%.
```

- **What it does:** creates the [spreadsheet](#/aprender/glossario/planilha) with the [formulas](#/aprender/glossario/formula) ready and shows **Download** and **Open**. Excel does the calculating, when you open the file. With Excel installed, it also exports the list to PDF to send to customers.
- **Model:** Haiku is enough.
- **Good to know:** the sample values are made up on purpose. Replace them with your real costs; Claude should never guess the price of something you sell. More in [Excel with Claude](#/aprender/excel).

## 2. Quote and proposal in Word and PDF (Code mode)

Choose the folder where you keep your proposals and send:

```experimentar-code
/sales:proposal for the client Example Market LLC: 20 boxes of coffee (500 g) at $8.90 each and 10 packs of sugar (5 kg) at $6.50 each, 5% off for payment upfront, shipping paid by the client, valid for 15 days and delivery in 5 business days.
```

- **What it does:** asks only for what's missing (your company's details, for example), checks every number two different ways and delivers the Word file and the PDF in the folder. If there is an old proposal or a template in the folder, it follows the same layout. It never invents a price, deadline or condition: whatever is missing becomes a marked field, and it lists those fields at the end.
- **Model:** Haiku is enough for a simple proposal. With many items and conditions, Sonnet.
- **Best tool:** it's Code mode because the file is created in your folder. Afterwards, `/sales:follow-up` (the next recipe) takes care of the messages to whoever got the proposal.

## 3. Follow up with who didn't answer

```experimentar
/sales:follow-up Example Market got proposal 2026-041, for $4,380.00, 3 days ago. It's valid until the 30th and nobody has answered. The contact is their buyer, by email.
```

- **What it does:** writes the messages on a 2, 5 and 10 day cadence: short, polite, with one clear request, without inventing urgency or offering a discount you didn't authorize. If information is missing (what was sent, when, for how much), it asks first.
- **Model:** Haiku is enough.
- **Good to know:** it writes, you send. With your e-mail connected in Settings > Connectors, it can send through there, but every send shows you the whole email and waits for your OK.

## 4. Answer a customer

```experimentar
/sales:answer-client A customer asked for 10% off an order of $1,200.00. I can give at most 5% if she pays upfront. Answer in the shop's tone: friendly and direct.
```

- **What it does:** uses only the facts you give it (it never promises a refund, discount or deadline on its own) and delivers two versions: a short one, for a text message, and a complete one, for email. Below them, a note with what to check before sending.
- **Model:** Haiku is enough.
- **Best tool:** a [project](#/aprender/projetos) with the shop's tone and the return policy saves you repeating it in every request.

## 5. Orders in the spreadsheet (and an app without AI)

To enter today's orders in one go, in Code mode, in the spreadsheet's folder:

```experimentar-code
/sales:orders Today's orders are in the file orders-chat.txt (I copied the messages from the chat app). Put them in the orders.xlsx spreadsheet in this folder, one row per item.
```

- **What it does:** reads the text and shows you the rows and the doubtful fields before writing. It doesn't touch the original spreadsheet without making a copy.
- **Model:** Haiku is enough.
- **Best tool:** does this happen every day, always in the same format? Instead of paying Claude every time, ask **once** for a program that does the job **without AI**. The `/sales:automate` command starts there, and the lesson [An order app without AI](#/aprender/app-de-pedidos-sem-ia) shows the whole path, from the email to the website. See also [Automate without paying the AI every time](#/aprender/automatizar-sem-ia).

## 6. Social media posts

```experimentar
Write 8 Instagram posts for my bakery for next month: 2 a week, alternating product, behind the scenes, tip and testimonial. For each one, the text (5 lines at most and up to 2 emojis), 5 hashtags and a photo idea. Show the posting calendar on a timeline.
```

- **What it does:** writes the texts, suggests a photo for each post and draws the calendar in a timeline **widget**. It does **not** create photos: the idea is for you to shoot or put together in your image editor.
- **Model:** Haiku is enough.
- **Best tool:** a [project](#/aprender/projetos) with your audience, the brand's tone and the price list. That way the posts come out in your style and nobody invents a price.

## 7. Delivery map

```experimentar
Tomorrow I have these deliveries, leaving from the shop at [shop address]:
[paste the addresses, one per line, with the neighborhood and city]

Show the points on a map and suggest a delivery order that avoids going back and forth.
```

- **What it does:** marks the points on a map **widget** and suggests the delivery order. The maps come from OpenStreetMap, over the internet. More in the lesson on [maps and itineraries](#/aprender/mapas-e-roteiros).
- **Model:** Haiku is enough.
- **Watch out:** it doesn't see traffic, roadwork or closed streets. Check the route in a navigation app before you leave. And send only the address: the customer's name and phone number aren't needed here (see [Passwords, keys and personal data](#/aprender/segredos-e-dados)).

## 8. Sales report

Attach the sales spreadsheet and send:

```experimentar
/sales:report from the sales spreadsheet I attached, comparing this month with last month.
```

- **What it does:** totals by period, product and customer, average ticket, the biggest customers and the comparison with the previous period, starting with a summary in plain language. It checks the totals before delivering and doesn't touch the original spreadsheet.
- **Model:** Haiku is enough. A big spreadsheet, Sonnet.
- **Best tool:** want the report every week without asking? A [routine](#/aprender/rotinas) in Code mode, in the sales folder, does it on schedule. If the calculation is always the same, a program without AI does it for free.

## Tips for the business

- **Prices, deadlines and conditions are yours:** Claude uses what you give it and marks what's missing. Be suspicious of any number you didn't provide.
- **The commands also have Portuguese names** (`/vendas:proposta`, for example). Either one works.
- **Read anything before it goes to a customer.** Claude helps a lot, but your name is on it.
