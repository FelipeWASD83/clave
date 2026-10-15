---
name: pagina-simples
description: Use to create a page or a small app that runs in the browser (calculator, list, form, presentation page), in a single HTML file, that works on phone and computer.
---

# Simple page

## Before writing
- Understand who it is for and what the person needs to do on the page. Choose a look that fits that (a bakery page doesn't look like a bank dashboard). With no style request, choose yourself and state the choice in one line.
- In a bigger project (several pages, data, login), warn that an organized folder is worth more than a single file.

## How to do it
- One `index.html` with the CSS and JavaScript inside. No library from the internet, unless it saves a lot of work; if you use one, say which and why.
- Works on phones: `<meta name="viewport" content="width=device-width, initial-scale=1">`, a layout that adjusts, buttons with a touch area of at least 44 px.
- Accessible: text with enough contrast, `alt` on images, a label on every form field, usable with the keyboard.
- Data the person types stays in their own browser (`localStorage`) and nothing goes to the internet without them knowing.
- Colors and sizes in CSS variables at the top, with a comment in the person's language, so they can change a color.

## Deliver
- In chat: an ```html block with the whole page (the person sees the preview next to it).
- In Code mode: save the file and offer to open it with `excel_abrir` (opens in the default browser).
- Before saying it's done, go through the skill `sites-e-apps:checklist-web`.
- Explain how to use the page, not how the code works.
