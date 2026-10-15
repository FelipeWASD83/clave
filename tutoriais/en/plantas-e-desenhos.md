---
titulo: Floor plans, drawings and charts
trilha: 7. Visual answers
ordem: 63
duracao: 7 min
resumo: The floor plan of a room with measurements, simple diagrams, charts from a spreadsheet, timelines and checklists.
---

Four widgets are for organizing what you already have on hand: measurements, numbers, dates and tasks. The **drawing** becomes a floor plan or a diagram, the **chart** shows the numbers, the **timeline** puts dates in order and the **checklist** keeps track of what's left to do. What applies to all of them (copy, full screen, download) is in [Widgets](#/aprender/widgets).

## The floor plan of a room

The **drawing** widget makes floor plans seen from above, with measurements. Claude builds the drawing out of simple shapes:

| Shape | Good for |
|---|---|
| rectangle | furniture, a rug, a counter (it can be rotated) |
| circle | a round table, a plant pot, an armchair |
| line and arrow | a window, a door, the walking path |
| polygon | an L-shaped room, a cut corner |
| text | names and notes inside the drawing |
| dimension | the measurement line: the number shows up by itself |

There's a grid behind it, and the footer says how much each square is worth (for example, **Each grid square: 0.5 m**). Measurements can be in meters or centimeters.

The more measurements you give, the better it comes out:

- the size of the room (width and length);
- where the door is, how wide it is and which way it opens;
- where the windows, outlets, air conditioner or a pillar are;
- the width and depth of each piece of furniture;
- what can't change ("the bed stays on the window wall").

A measurement you didn't give, it assumes. Ask it to tell you what it assumed.

```experimentar
My living room is 4 m by 5 m. The front door is 80 cm wide and sits in the corner of one of the 4 m walls; the window takes up the middle of the opposite wall. I want a 2.10 by 0.90 m sofa, a TV on a 1.60 m stand, a round table 1 m across with 4 chairs, and a rug. Draw the floor plan seen from above, with the dimensions of the walls, leaving at least 70 cm to walk between the pieces of furniture. Then tell me whether it really fits.
```

To explore the drawing: **Zoom in**, **Zoom out** and **Show the whole drawing**; drag to move it; click the drawing to zoom with the mouse wheel. On the keyboard, + and - zoom in and out, the arrow keys move it and 0 shows it all.

To change it, ask in the chat: "turn the sofa toward the window", "try a square table". Want to compare? Ask for two or three layouts: each one becomes its own drawing.

To take it with you: **Download image** gives you a **PNG image** (to send to someone or paste into a document) or an **SVG drawing** (scales up without losing quality), with the title and the legend. **Copy as text** lists each shape with its position and size.

### A simple floor plan of a home

The same widget draws several rooms together, so you get an idea of how they fit:

```experimentar
Draw a simple floor plan of a 2-bedroom apartment of 55 m²: an open living room and kitchen, 2 bedrooms, 1 bathroom and a laundry area. Use typical measurements, mark the doors and write the area of each room inside it. It's just so I get an idea of how the rooms fit together.
```

### What the drawing isn't

It's a sketch for thinking about the layout, not a design project. Claude works out the positions, but it can get a calculation wrong or leave two pieces of furniture touching. Clave only checks that the shapes don't stick far out of the drawing; if the door hits the wardrobe, you're the one who notices. Check the dimensions, measure again before buying furniture, and construction, walls, gas and wiring are a job for a professional.

Haiku is enough for one room. Lots of constraints (many pieces of furniture, outlets, a pillar in the middle) do better on Sonnet.

## Simple diagrams

The drawing also does diagrams: boxes and arrows for a step-by-step, a small org chart, the path of an order. In these, measurements don't matter.

```experimentar
Draw a simple diagram, with boxes and arrows, of the path of an order in an online store: order placed, payment approved, picking, shipping, delivery and, if needed, a return. Use one color for the normal path and another for the return.
```

## Charts

The **chart** widget comes in four shapes:

| Shape | Good for |
|---|---|
| **Bars** | comparing amounts: spending by category, sales by salesperson |
| **Lines** | seeing how something changes over time: the electricity bill month by month |
| **Pie** | seeing the parts of a whole: where the paycheck went |
| **Area** | like lines, with the part below filled in: good for volume over time |

Hover the mouse (or use the arrow keys) to see each value. It fits up to 8 series (for example, "this year" and "last year") and up to 60 labels; with more than that, ask it to group them by month or by category. In a pie, more than 12 slices become 11 slices and an "Others".

### From a spreadsheet

In chat, attach the spreadsheet with the paper clip in the text box (.xlsx or .csv) and ask:

```experimentar
I attached the household expenses spreadsheet. Add up the expenses by category and show them in a pie chart. Then, in a line chart, show the total for each month. In 3 lines, tell me what weighed the most.
```

In a big spreadsheet, it reads the first rows and fetches the rest when it needs to. Before attaching a bank statement, delete what the analysis doesn't use, like the account number (see [Passwords, keys and personal data](#/aprender/segredos-e-dados)). In Code mode the same works for a spreadsheet in the folder: "read sales.xlsx and show the sales per month in a bar chart".

### A chart in the chat or in the spreadsheet?

They're two different things:

- The **widget** is for looking and deciding now: it appears right away and you can download it as an image. It doesn't change if you change the spreadsheet later.
- A chart **inside the Excel file** stays with the data and follows along when you change the numbers. Ask "create a spreadsheet with a chart" (see [Excel with Claude](#/aprender/excel)).

## Timelines

The **timeline** widget puts events in order, each one with a date, a title and, if you want, a short description. The date is free text: "1969", "March", "Week 2" or "Day 3, 2 pm" all work. It fits up to 40 events.

Good for the schedule of a renovation or an event, a study plan, the history of a subject or the stages of a process.

```experimentar
Lay out on a timeline the schedule for a birthday party 6 weeks from now: what to do each week (invitations, venue, cake, decorations, party favors) and, on the day of the party, hour by hour.
```

## Checklists

The **checklist** widget is a list to tick off, with up to 60 items. What you tick stays saved: close Clave, open the chat again and the ticks are still there, with the top showing how many are done (**3 of 10 done**). **Copy as text** takes the list with [x] on the done items, ready to paste into a message.

```experimentar
Make a checklist, in the right order, of everything I need to do to get a passport for the first time in [your country]. Check on the web what the official website asks for and tell me the date you saw it.
```

The checklist lives in the chat, on the computer. Want a list that goes with you to the store, on your phone? Copy it as text and send it to yourself, or ask for a small app (see [Build web pages and small apps](#/aprender/paginas-e-apps)).

## Tips

- **Give the numbers.** Claude doesn't guess measurements or values; whatever it assumes, it should tell you.
- **Say what it's for**: "to show the carpenter", "to paste into the report", "so I can decide today". It picks the widget and the level of detail based on that.
- **One subject per chat**: the floor plan in one, the budget in another. It's cheaper and Claude gets less confused (see [Lean conversations](#/aprender/conversas-enxutas)).
