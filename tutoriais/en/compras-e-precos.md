---
titulo: Compare products and prices
trilha: 7. Visual answers
ordem: 61
duracao: 6 min
resumo: Web search, the products widget and the comparison widget, and what to watch out for with prices and links before you buy.
---

Before you buy something, Claude can do the boring part: look for options, gather price, store and rating, and put everything side by side. It **doesn't buy anything**: you're the one who decides and pays, in the store.

## How it works

1. You say what you want, how much you can spend and what matters to you (size, brand, warranty, delivery time).
2. It searches the web. For that, the **Web** button in the text box has to be on (it's on by default). Each search shows up as a **Searched the web** step: click it to see the pages the search found.
3. It builds a **products widget** and, if you ask, a **comparison widget** with the details side by side.
4. It writes, in a few lines, which one it would pick and why.

Haiku, the cheapest model, handles this (see [The right model for the lowest price](#/aprender/modelo-certo-mais-barato)). Each search costs $0.01, on top of the tokens of the pages it reads; a comparison like this usually comes to a few US cents (this is an estimate).

## The products widget

Each option comes on a card with name, price, store, rating (when it found one) and a short note, like "free shipping". The cheapest option gets the **Cheapest** tag (only among prices in the same currency). At the top, **Lowest price** and **Original order** rearrange the list.

The date comes at the bottom: **Prices seen on [day]; check them in the store.** The widget doesn't even appear without that date. It's the day the search found the price, not today's price.

The **View in store** button opens the page in your usual browser. It only shows up when Claude has the real link: it's told never to make up a product link, and without the right link the product shows up without the button.

Photos only appear when you click **Show images** (the reason is in [Widgets](#/aprender/widgets)).

```experimentar
I want to buy wireless earbuds to use on the bus, for under $80. Search the web and show me 4 options in a products widget, with price, store, rating and the date you saw each price. Then tell me which one you'd pick and why, in 3 lines.
```

## The comparison widget

Price is only one criterion. To see the rest, ask for a comparison: a table with up to 6 columns (the options) and one row per criterion. Claude marks the best of each row with a star, and the **Best in** footer counts how many rows each option won.

```experimentar
Compare side by side, in a comparison widget, 3 robot vacuums under $400: price, suction power, whether it mops, battery time, noise, warranty and buyer ratings. Search the web, mark the best of each row and tell me the date you saw the data.
```

Say which criteria matter to you. "I'll use it in a small apartment, with a cat that sheds" changes the answer much more than "which is the best vacuum".

## Prices change: check in the store

The price in the widget is a snapshot from the day of the search, and sometimes not even that:

- the page the search read may be out of date;
- sales end, stock runs out, and the price changes with your address, shipping, coupons and payment method;
- the rating may be for another version of the product, or from another store;
- Claude may misread a number on the page.

Before you pay, open the store's page and check **price, shipping, delivery time and the exact model** (color, size, voltage). If the store's price is very different from the widget, trust the store.

## Links: only what the page showed

A product link only deserves trust if it came from a page the search really showed. Before clicking:

1. Rest the mouse on **View in store**: the address appears. Check that it's the website of the store the card names (`storename.com`, not `storename-deals.xyz`).
2. Click the **Searched the web** step and see whether that site is among the pages the search found. The small numbers in the middle of the text also lead to the sources.
3. When in doubt, don't click: go to the store's site through the address you already know, or through the site's own search.

A link that doesn't show up anywhere in the search may have been made up, may be wrong or may have come from a page trying to push a fake site. A deal that's too good with a strange link is a well-known old scam. More in [When a page or file tries to give Claude orders](#/aprender/injecao-de-instrucoes).

## Checking the page with Claude, in Code mode

In Code mode, Clave's [browser](#/aprender/navegador) (only in the Clave window) lets Claude open the product page and read what's written on it. The page shows up in the **Browser** tab of the side panel, and you see the same thing it sees. Before it uses the store's site for the first time in the task, it shows a card with the store's address and waits for your OK (except in **Auto** mode); once the site is allowed, it opens, reads, takes screenshots and scrolls on its own. Clicking and typing wait for your OK every time in **Ask** and **Accept edits** modes; and passwords, access codes and cards are typed by you. It can look at the page, but the purchase is yours.

```experimentar-code
Open this product's page in the browser: [paste the store link]. Read the price, the payment options and the delivery time shown on the page and tell me in 5 lines. Don't click anything.
```

When the site card shows up, click **Allow**: the site stays allowed until the reply finishes, and it opens and reads the page without asking again.

## Tips

- **Give context**: who it's for, where you'll use it, what you already have. A good comparison depends on good criteria.
- **Always ask for the date and the store of each price.** Without a date, you don't know if the price is from today or from months ago.
- **One purchase per chat**: the earbuds in one chat, the vacuum in another. It's cheaper and Claude gets less confused (see [Lean conversations](#/aprender/conversas-enxutas)).
- **Be suspicious of praise without reasons**: if the answer hypes a store or a product without showing why, ask "where did that information come from?".
