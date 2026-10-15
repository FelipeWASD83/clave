---
titulo: Widgets: when Claude draws the answer
trilha: 7. Visual answers
ordem: 60
duracao: 7 min
resumo: The eight cards Claude builds in the chat, how to ask for one, what each button does and why photos wait for your click.
---

Not every answer works well as text. Four prices side by side, five places on a trip or the floor plan of a bedroom are much clearer as a picture. That's what **widgets** are for: cards Claude builds right in the chat when they help more than text. The list of steps shows **Showed a widget**, and the card comes right below it.

## The eight types

| Widget | What it shows | An example request |
|---|---|---|
| **Products** | photo, price, store and rating of each option, with the cheapest one marked | "Compare 4 wireless earbuds under $80 in a products widget" |
| **Map** | numbered places on a map, with a line connecting them in order if you want | "Show me on a map the 5 museums I shouldn't miss in Paris" |
| **Recommendations** | series, movies, games, anime, books, music or podcasts, with the reason for each one | "Recommend 5 history podcasts to listen to on the bus" |
| **Drawing** | floor plans seen from above and simple diagrams, with measurements | "Draw the floor plan of my 4 by 5 m living room with the sofa and the TV" |
| **Chart** | bars, lines, pie or area | "Make a pie chart of the expenses I pasted below" |
| **Comparison** | a side-by-side table, with a star on the best of each row | "Compare bus, bike and car for getting to work, side by side" |
| **Timeline** | dates and events in order | "Show the stages of the French Revolution on a timeline" |
| **Checklist** | a list to tick off, which stays saved | "Make a checklist of what to pack for a 3-day beach trip" |

The next lessons in this track show the most useful types in detail: [Compare products and prices](#/aprender/compras-e-precos), [Maps and itineraries](#/aprender/mapas-e-roteiros) and [Floor plans, drawings and charts](#/aprender/plantas-e-desenhos).

## How to ask for one

Most of the time you don't even need to ask: Claude decides on its own when a card helps. To make sure, name the type in the request ("on a map", "in a bar chart", "as a checklist", "in a products widget", "side by side") and say what you want to see in it: the criteria for the comparison, the measurements of the floor plan, the order of the places.

After the widget, Claude writes little. It's told not to repeat in the text what the card already shows, and to comment only on what helps you decide.

Want to change something? Ask in the same chat: "remove the third item", "switch to a line chart", "move the table next to the window". It builds a new card, and the previous one stays above it so you can compare.

Widgets show up in chat and in Code mode. In a [routine](#/aprender/rotinas) or in a step of a [workflow](#/aprender/fluxos-e-agentes) they don't exist, because nobody is watching.

What it costs: the card is made of the data Claude writes, so it costs about the same as an answer of that size. A floor plan with dozens of pieces of furniture costs more than a 5-item checklist. Product prices and addresses need a web search, which costs $0.01 per search (see [Where your credit goes](#/aprender/para-onde-vai-o-credito)).

## The card's buttons

In the top corner of every widget:

- **Copy as text**: copies a text version, to paste into a message, an e-mail or a document. Products go with price, store and link; map places, with an OpenStreetMap link for each one; a chart becomes a table; a checklist comes with [x] on what's already ticked.
- **Full screen**: opens the card large, in a window over the chat. On maps and drawings, the mouse wheel zooms right away there.
- **Download image** (drawings and charts only): **PNG image**, to send or paste into documents, or **SVG drawing**, which scales up without losing quality. The image carries the title at the top and the legend at the bottom.

And each type has its own controls: products can be sorted by **Lowest price** or **Original order**; maps and drawings zoom in, zoom out and go back to showing everything; on a chart, hover the mouse (or use the arrow keys) to see each value; on a checklist, the top shows how many items are done.

The widget is saved with the chat: when you open it again, it's still there, and the checklist keeps what you ticked, even after you close Clave.

## Photos wait for your click

Products and recommendations can have a photo (of the product, of the cover). Those photos live on other websites and, **by default, don't load on their own**: a **Show images** button appears, and they only come in when you click it.

The reason: fetching a photo lets the site it comes from know. A malicious page, read during a search, could get Claude to use as a "photo" an address with pieces of the chat hidden inside it. When the photo loads, the address reaches that site, and the data goes with it. Without your click, nothing leaves on its own. If the answer looks odd (a product you didn't ask for, a store you never mentioned), don't click. More on this in [When a page or file tries to give Claude orders](#/aprender/injecao-de-instrucoes).

Without a photo, the card works the same: in recommendations, Clave draws its own cover with the initials of the title.

The option is in **Settings > Features > Widgets > Photos from other sites**: **Only load when I click (recommended)** or **Always load**. The recommended choice is to leave it as it is.

Maps are different: they load on their own, because the map pieces always come from the same place, OpenStreetMap, and go through Clave. More in [Maps and itineraries](#/aprender/mapas-e-roteiros).

## Where the data comes from

The card only draws what Claude sent. Prices, stores, ratings and addresses: it's told to take them from the web search, with the date it saw them, and never to make up a product link. Without the right link, the product shows up without the store button. The products widget doesn't even appear without the date of the prices.

Even so, it can make mistakes. A widget makes the answer easier to read, not more correct: check what matters before you decide.

## Turning them off

- **For one answer**: ask "answer in text only, no widget".
- **Always**: in **Settings > Features > Widgets**, turn off **Let Claude show widgets**. It applies to new chats and the next replies; the cards that already showed up stay where they are.

## Try it

Three requests that don't need a web search, so they're cheap:

```experimentar
Make a checklist of 12 things to pack for a 3-day beach trip, for a family with two small children.
```

```experimentar
Compare side by side, in a comparison widget, bus, bike and car for getting to a job 5 miles from home: cost per month, time, health, rainy days and where to leave it. Mark the best of each row and tell me, in 2 lines, which one you'd pick.
```

```experimentar
Show in a bar chart how I spend a day: sleep 7 h, work 8 h, commuting 2 h, phone 3 h, meals 1.5 h, exercise 0.5 h and the rest free time. Then tell me, in 3 lines, where I could gain some time.
```
