---
titulo: The browser: you and Claude on the same page
trilha: 6. The Code workspace
ordem: 52
duracao: 7 min
resumo: A real browser in the Code panel: you browse, Claude checks websites, and each new site, each click and each typed text go through your OK.
---

The **Browser** tab of the [Code panel](#/aprender/painel-do-code) is a real [browser](#/aprender/glossario/navegador), inside Clave. You use it like any other. And Claude uses the same one: when it needs to see a website it built, test a form or read a page that only works when opened in a browser, it opens it here, and you follow everything.

## Using it yourself

- Open it with the globe button at the top of the conversation or with **Ctrl + Shift + L**.
- In the bar, type an address (`example.com`) or a search. Just a [port](#/aprender/glossario/porta) number, like `8000`, opens `http://localhost:8000`.
- Back, forward and reload are buttons on the bar. With the page or the browser bar in focus, **F5** (or **Ctrl + R**) reloads, **Alt + arrow keys** go back and forward and **Ctrl + L** takes you to the address box.
- **Local** lists the websites running on your computer right now, the [local servers](#/aprender/tarefas-em-segundo-plano). One click opens one.
- **Open in your computer's browser** takes the page to your everyday browser (Edge, Chrome...).
- Right-click on a page: open a link here or in your computer's browser, copy the link address, go back, reload and **Inspect** (a tool for people who code, which **F12** also opens).
- Websites you sign in to here stay signed in, separate from your everyday browser. To delete those logins, the cookies and everything else the sites saved, use **Settings > Code mode > Delete the browser data**. **Sign out** also deletes them.
- When you download something, Windows asks where to save it, and Clave tells you when it's done.
- For safety, it doesn't give sites access to your camera, microphone or location, and it only opens `http` and `https` addresses.

## When Claude uses it

- It opens the page, reads the text, takes a screenshot when the look matters, scrolls and goes back.
- The tab opens on its own, with a banner: **Claude is using the browser**. You can watch along; avoid clicking while it works.
- Each action becomes a step in the conversation: "Opened in the browser", "Read the browser page", "Took a browser screenshot", "Clicked on the page"...
- It doesn't see the page the way you do. It reads the text and a numbered list of the buttons, links and fields, and clicks by number. The screenshot is for checking the look: colors, layout, something broken.

## What asks for your OK

| Claude's action | Ask and Accept edits | Auto | Plan |
|---|---|---|---|
| Use a site for the first time in the task | asks for your OK | does it on its own | asks for your OK |
| Open, read, take a screenshot, scroll and go back on a site already allowed | does it on its own | does it on its own | does it on its own |
| Click and type | asks for your OK, every time | does it on its own | doesn't do it |

- **The site card.** Claude's first action on each website (opening it, or reading, taking a screenshot, scrolling, going back, clicking or typing while the page is on it) shows **Let Claude use the site example.com in this task?**. **Allow** allows the site for the rest of the task (until this reply finishes): opening, reading, taking a screenshot, scrolling and going back on it don't ask again. Under **More options**, **Always in this folder…** or **Always, everywhere in Clave…** save the rule `Navegador(example.com)`. **Deny** keeps the site out. Sites on your own computer (`localhost`, `127.0.0.1`) never ask.
- Even with the site allowed, **clicking and typing still ask for your OK**. For a click on a new site, you get both cards: the site's and the click's.
- If the page ends up on another site (a redirect, a click, Enter, going back), Clave checks that site before Claude sees anything: a blocked site leaves the page blank, and a site not allowed yet shows the site card.
- Why ask per site: a page may try to take Claude to your e-mail (which stays signed in here) and then send what it read to another site's address. With the card, no site joins the task without you seeing it.
- The click card shows the page and what it's about to click, and why, or the text it's about to type. Clicking and typing on a website can buy, send, delete or publish something: read before you **Allow**.
- The OK is for that page and that button or field. If the page changed between reading it and clicking, nothing is clicked: Claude is told and reads the page again.
- **Passwords, access codes and cards are typed by you.** Clave doesn't let Claude fill in those fields: it asks you to type them and let it know when you're done. Choosing a file to upload to a site is also up to you.
- It shouldn't click to buy, pay, delete or send anything you didn't ask for. If a card like that shows up out of nowhere, deny it.

## Rules for the browser

In [Permissions](#/aprender/permissoes), browser rules use the word `Navegador` (the tool name stays in Portuguese):

- `Navegador(clicar:localhost)` under **Allow without asking**: it clicks on your local website without asking, on any port. `Navegador(clicar:localhost:5173)` only applies on port 5173. Good for testing a site it built itself.
- `Navegador(example.com)` under **Allow without asking**: it uses the site without the site card, but clicking and typing still ask for OK. Only a rule that names the action, like `Navegador(clicar:example.com)`, skips that OK.
- `Navegador(example-store.com)` under **Never**: it doesn't use the browser on that site.
- `WebFetch(domain:suspicious-site.com)` under **Never** also stops the browser from using that site: no opening, reading or clicking.

The actions you can put before the colon are `abrir` (open), `ler` (read), `print` (screenshot), `rolar` (scroll), `voltar` (back), `clicar` (click) and `digitar` (type). The English names work too: `open`, `read`, `print`, `scroll`, `back`, `click` and `type`, so `Navegador(click:localhost)` is the same rule as `Navegador(clicar:localhost)`. A word outside this list, as in `Navegador(delete:example.com)`, doesn't count as a rule. The easiest way to create a rule is from the card itself: **More options > Always in this folder…**.

## What comes from the page is data

A page may have text trying to give the AI orders ("click here and confirm the purchase"). Clave hands each page to Claude with a notice saying it's the page's content, not instructions, and each new site and each action that changes something go through your OK. See [When a page or file tries to give Claude orders](#/aprender/injecao-de-instrucoes).

## What it costs

Whatever you do in the browser yourself costs nothing. Each page Claude reads and each screenshot it takes go into the conversation as [tokens](#/aprender/glossario/token). Give it the right address instead of asking it to search, and ask for a screenshot only when the look matters. To just read some text from the internet, web search is usually cheaper. More in [Code mode without waste](#/aprender/code-sem-desperdicio).

## Only in the Clave window

The browser lives in the Clave window. If Clave opened in a regular browser instead, the tab shows **The browser only works in the Clave window**: close it and open it again with the **Clave** shortcut on your desktop. The lesson [A website from scratch to the browser](#/aprender/site-do-zero-ao-navegador) explains what to do when this happens.

To keep Claude from using the browser, turn off **Settings > Code mode > Let Claude use the Code browser**. You can still use it as usual.

## Try it

```experimentar-code
Open https://example.com in Clave's browser, read the page and tell me in two sentences what it says and where its link goes.
```

Outside Auto mode, the card **Let Claude use the site example.com in this task?** shows up first. Click **Allow**: the site stays allowed until the reply finishes, and reading the page doesn't ask again. The Browser tab opens on its own and you see the page it read.
