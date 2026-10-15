---
titulo: Maps and itineraries
trilha: 7. Visual answers
ordem: 62
duracao: 6 min
resumo: Places on a map, the line that connects the points, a day-by-day trip itinerary and what to do when an address doesn't show up.
---

The **map** widget marks places on a real map, numbered, with the list beside it. It's good for planning an outing, a trip, the day's visits, or just for seeing where things are in relation to each other.

## What the map shows

- **Up to 30 places**, numbered in the order of the list. Click an item in the list and the map moves to it and opens a balloon with the description.
- **The route**: when you ask for it, a line connects the points in the order of the list. Careful: it's a **straight line** from one point to the next, not the way along the streets. It shows the order of the visit, not the path.
- **Show all points**: the button below + and -, in the corner of the map, frames them all again.
- **Open in map**, inside the balloon, and the button next to each item in the list open that place on the OpenStreetMap website, in your browser.
- **Zoom**: in the chat, click the map before using the mouse wheel (so the wheel keeps scrolling the chat when you're just passing by). In **Full screen**, the wheel zooms right away.
- **Copy as text**: copies the list of places with an OpenStreetMap link for each one, handy for sending to whoever is coming along.

## How to ask

Name the places (or what you're looking for) and whether you want the route connecting the points:

```experimentar
Show on a map, with the route in the order of the visit, a one-day walking tour of Rome: Colosseum, Roman Forum, Pantheon, Trevi Fountain and Piazza Navona. For each place, one sentence about what to see and how long to stay.
```

## A trip itinerary

For a trip of several days, one map per day works better than a single map with everything: each day keeps just a few points, and the line shows the order for that day. In the same answer, Claude can add other widgets: a **timeline** with morning, afternoon and evening, and a **checklist** of what to sort out before you go.

```experimentar
Plan a 3-day itinerary in Buenos Aires for a couple who love good food and walking, on a mid-range budget. For each day, a map with the route in the order of the visit and a timeline with morning, afternoon and evening. At the end, a checklist of what to sort out before the trip. Check the opening hours on the web and tell me the date you saw them.
```

Haiku is enough for a short itinerary. A long trip, with several cities and stretches of travel, does better on Sonnet.

Three things to watch:

- **The time between places is an estimate.** The map doesn't calculate a route and doesn't see traffic, roadworks or closed streets. For the real way there, use your usual maps app; **Open in map** helps you find the point.
- **Opening hours, tickets and entry rules change.** Check the official website before you go. Travel documents (passport, visa): only official sources.
- **Check that each point landed in the right place.** Zoom in or click **Open in map**. A point in the wrong place? Ask it to use the full address of that place.

## How an address becomes a point

Claude sends each place in one of two ways:

- **With coordinates** (latitude and longitude): the point goes straight onto the map.
- **With the address**: Clave looks the address up in **Nominatim**, OpenStreetMap's address search service, and puts the point where it found it.

Nominatim is free and has usage rules, which Clave follows: one search per second and up to 15 addresses per map. So a map with 10 new addresses takes about 10 seconds to appear. What has already been found stays saved on your computer for about six months, and the second time is instant.

The address that goes on the map is sent to that service. Send only the address: the name and phone number of whoever lives there aren't needed (see [Passwords, keys and personal data](#/aprender/segredos-e-dados)).

## When an address isn't found

If Nominatim doesn't find an address, that point is left out and the map shows up with the others. Claude gets the list of what was left out and should tell you in its answer. If no point is found at all, the map doesn't appear, and Claude is told to send more complete addresses or the coordinates.

What to do:

1. **Complete the address**: street, number, neighborhood, city and country. "120 Main Street" exists in many cities; "120 Main Street, [city], [state], [country]" is just one place.
2. **Use the name of the place with the city**: "Louvre Museum, Paris" usually works better than half an address.
3. **Send the coordinates**: in most maps apps, right-clicking the place (or pressing and holding, on a phone) shows the latitude and longitude. Copy them and paste them into the request: "point 3 is at [latitude], [longitude]".
4. **Change the text before trying again**: a "not found" is remembered for one day, so asking again with exactly the same address, letter for letter, gives the same result.
5. **More than 15 addresses?** The ones past that are left out. Split them into two maps or send coordinates.

Without internet, the address search fails and the map has no streets drawn, but the list of places stays on the card. Areas you've already seen stay saved for at least 7 days.

## The map comes from OpenStreetMap

Clave's maps come from **OpenStreetMap**, a map of the world made by volunteers and free to use, as long as you say where it came from. That's why every map carries, in its bottom corner, the credit **© OpenStreetMap** (with a link to the copyright page) and the name of **Leaflet**, the piece that draws the map on screen. If you take a screenshot of the map to send or publish, keep the credit visible or write "© OpenStreetMap contributors": that's the condition for using it.

Clave follows the service's rules: it downloads only the map pieces that are on screen, keeps each one for at least 7 days and identifies itself in every request. The credits are also in **Settings > Updates & about**.

## More ideas

```experimentar
I want to visit 4 parks in a big city on a Saturday, starting downtown in the morning and heading back at night. Pick a city you know well, show the parks on a map with the route in the order that avoids going back and forth, and tell me how long to stay at each one.
```

For deliveries and work visits, see the delivery map recipe in [For a small business](#/aprender/receitas-pequeno-negocio).
