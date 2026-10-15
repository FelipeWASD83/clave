---
titulo: For home and personal life
trilha: 9. Recipes by area
ordem: 83
duracao: reference
resumo: Compare before you buy, a trip itinerary, a room floor plan, the household budget, a meal plan with a shopping list and what to watch.
---

Ready-made requests for life outside work. Click **Send to a new chat**: the request goes into the text box, and you swap the details (budget, city, measurements, what's in square brackets) for yours before sending.

Many recipes here use [widgets](#/aprender/widgets): cards Claude draws in the chat when they help more than text (products and prices, maps, recommendations, drawings and floor plans, charts, comparisons, timelines and checklists). They're on by default; the switch is in **Settings > Features > Widgets**.

Clave starts on **Haiku 5.5**, the cheapest, and it handles almost everything here. The model advisor tells you when a task needs another one (see [The right model for the lowest price](#/aprender/modelo-certo-mais-barato)).

| Recipe | Where | Model |
|---|---|---|
| Compare before you buy | chat, with a products widget | Haiku |
| Trip itinerary | chat, with a map widget | Haiku (Sonnet for a long trip) |
| Floor plan of a room | chat, with a drawing | Haiku |
| Household budget | chat, spreadsheet and chart | Haiku |
| Meal plan and shopping list | chat, with a checklist | Haiku |
| What to watch | chat, with a recommendations widget | Haiku |
| Understand a document | chat | Haiku (Sonnet for a long contract) |

## 1. Compare before you buy

```experimentar
I want to buy an air fryer for under $150 for a family of 4. Search the web and show me 4 options in a products widget, with the price, the store and the date you saw each price. Tell me which one you'd pick and why.
```

- **What it does:** searches the web and builds a **products widget** with photo, price and store, and writes which one it would pick. The price is what the search found, on the day it searched: check it in the store before you pay. You're the one who decides and pays. More in the lesson on [comparing products and prices](#/aprender/compras-e-precos).
- **Model:** Haiku is enough. Each search costs $0.01, on top of the tokens of the pages it reads; a comparison like this usually comes to a few US cents (this is an estimate).
- **Good to know:** the photos come from other sites and, for safety, only load when you click them. You can change this in **Settings > Features > Widgets > Photos from other sites**, but the recommended choice is to leave it as it is. Why, and what else a page can try: [When a page or file tries to give Claude orders](#/aprender/injecao-de-instrucoes).

## 2. Trip itinerary

```experimentar
Plan a 3-day itinerary in Lisbon for a couple who love good food and walking, on a mid-range budget. For each day: morning, afternoon and evening, with the walking time between places. Show the places on a map and check the opening hours on the web, telling me the date you saw them.
```

- **What it does:** builds the itinerary day by day and marks the places on a **map widget** (the maps come from OpenStreetMap, over the internet). More in the lesson on [maps and itineraries](#/aprender/mapas-e-roteiros).
- **Model:** Haiku is enough for a short itinerary. A long trip, with several cities and stretches of travel, does better on Sonnet.
- **Watch out:** opening hours, ticket prices and entry rules change. Check the official website before you go, and check travel documents (passport, visa) only with an official source.

## 3. Floor plan of a room

```experimentar
My bedroom is 3 m by 3.5 m. The door is in the corner of one of the 3 m walls and the window is in the middle of the opposite wall. I want to fit a full-size bed (1.37 by 1.91 m), a wardrobe 1.60 m wide and 0.55 m deep, and a 1 m desk. Draw the floor plan seen from above with two different layouts and tell me which one leaves more free space to walk around.
```

- **What it does:** draws the floor plans in a **drawing widget**, seen from above and with the measurements, and compares the two. You can attach a photo of the room as well. More in the lesson on [floor plans, drawings and charts](#/aprender/plantas-e-desenhos).
- **Model:** Haiku is enough for one room. Lots of constraints (many pieces of furniture, outlets, a pillar in the middle) do better on Sonnet.
- **Watch out:** it's a sketch to think about the layout, not a design project. Measure again before buying furniture, and construction, walls and wiring are a job for a professional.

## 4. Household budget

```experimentar
Create a monthly household budget spreadsheet with the sheets Income, Fixed costs (rent, electricity, water, internet), Variable costs (groceries, transportation, entertainment) and Summary. In Summary, the total of each sheet, how much is left at the end of the month and a pie chart of spending by category. Fill it in with sample values for me to replace with mine.
```

- **What it does:** creates the [spreadsheet](#/aprender/glossario/planilha) with the formulas and the chart, and shows **Download** and **Open**. More in [Excel with Claude](#/aprender/excel).
- **Model:** Haiku is enough.
- **Best tool:** just want to see where the money went? Attach the statement your bank lets you download as a spreadsheet or CSV and ask for "a chart of my spending by category": it draws the **chart** in the chat. Before attaching, delete what the analysis doesn't need, like the account number and ID numbers (see [Passwords, keys and personal data](#/aprender/segredos-e-dados)). It helps you organize, but it isn't a financial advisor.

## 5. Meal plan and shopping list

```experimentar
Suggest 5 quick dinners for the week (30 minutes each at most) for 2 people, without pork. Then combine the ingredients into a single shopping list, grouped by supermarket section, as a checklist.
```

- **What it does:** writes the recipes and puts the ingredients together in a **checklist widget**, already grouped by supermarket section.
- **Model:** Haiku is enough. With no thinking (in the second button of the text box, uncheck **Think before responding**) it's even cheaper.
- **Watch out:** allergies, or a diet for health reasons: say so right in the request and check the labels, because it can make mistakes.
- **Best tool:** want a list that stays saved and that you tick off at the store? Ask for a small shopping list app (see [Build web pages and small apps](#/aprender/paginas-e-apps)).

## 6. What to watch

```experimentar
I like short thriller series, with few seasons, and I don't like horror. Recommend 5 series and 3 movies in a recommendations widget, with one sentence about each and where I can stream them in [your country]. Check on the web where each one is available and tell me the date you saw it.
```

- **What it does:** builds a **recommendations widget** with the covers and the reason for each pick. Name in the request titles you've already watched and liked: the suggestions get much better.
- **Model:** Haiku is enough.
- **Good to know:** streaming catalogs change every month; that's why the request asks it to check on the web and give the date. The covers come from other sites and only load with a click, like the product photos.

## 7. Understand a document

Attach the PDF or a photo and send:

```experimentar
I attached the lease I'm being asked to sign. Explain in plain words what each clause says, highlight fees and penalties, rent increases and what happens if I move out before the end of the term, and give me a list of questions to ask before signing.
```

- **What it does:** reads the document and turns the legalese into everyday words. It also works with a utility bill, a letter from the bank or a medicine leaflet.
- **Model:** Haiku is enough for a bill or a short letter. A long contract does better on Sonnet.
- **Watch out:** it doesn't replace a lawyer, an accountant or a doctor in a serious decision; it helps you understand and prepare your questions. If you can, cover ID numbers and account numbers before attaching (see [Passwords, keys and personal data](#/aprender/segredos-e-dados)).

## Tips for home

- **Prices and hours come from the search, with a date:** always ask for the store and the day it saw them, and check before you pay or leave the house.
- **New subject, new chat:** the trip in one chat, the budget in another. It's cheaper and Claude gets less confused (see [Lean chats](#/aprender/conversas-enxutas)).
- **Prefer answers in text only?** Turn off widgets in **Settings > Features > Widgets**.
