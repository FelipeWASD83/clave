---
titulo: A website from scratch to the browser
trilha: 6. The Code workspace
ordem: 54
duracao: 10 min
resumo: A complete example: Claude builds a website, starts a local server, opens it in Clave's browser, you ask for a change and turn the server off at the end.
---

This lesson brings the whole Code workspace together in a real job: Claude builds a one-page website, leaves a [local server](#/aprender/tarefas-em-segundo-plano) running, opens the website in Clave's [browser](#/aprender/navegador), you take a look, ask for a change, check it, and at the end you turn the server off from the Tasks tab.

## Before you start

- **Use the Clave window**, opened with the **Clave** shortcut on your desktop. The panel's browser only exists there.
- **Permission mode**: **Ask** (the default) or **Accept edits**. In **Plan** it only reads: it doesn't create the files or start the server.
- **Model**: a one-page website comes out well on the default model. For a bigger website, the model advisor tells you if it's worth moving up.

## 1. A folder for the website

Click **New Code task** > **Choose environment** (or **Choose the working folder**) > **Create a folder from the template…** and give it a name like `my-website`. The [folder template](#/aprender/modelo-de-pasta) brings quality rules and visual references that help the website look good.

Prefer an empty folder? Create one in File Explorer and pick it with **Another folder…**.

## 2. Ask for the website and the preview

```experimentar-code
Create in this folder a one-page website for Example Bakery, a neighborhood bakery: a header with the name and a tagline, a section with 4 treats (name, short description and price), the opening hours and a "Place an order" button that takes you down to a contact section. Use only HTML, CSS and JavaScript, with nothing to install. Then start a local server in the background and open the website in Clave's browser so I can see it.
```

What happens, step by step:

1. **It writes the files** (`index.html`, a style file and, if needed, a JavaScript one). In Ask mode, each file asks for your OK. To avoid approving them one by one, use **More options > Allow for this task**.
2. **It asks to start the server.** The card says **Leave running in the background** and shows the command, something like `python -m http.server 8000` (Python is already on your computer, because Clave uses it). Read it and click **Allow**.
3. **The website shows up.** The address appears in the command's output (`http://localhost:8000`), the Browser tab opens on its own with the **Claude is using the browser** banner, and it checks the page, sometimes with a screenshot. Since the address is on your own computer (`localhost`), opening and reading don't ask for OK: the site card only shows up for sites outside your computer.
4. **It tells you what it did.** In the left sidebar you'll see **1 running**: that's the server, which stays on after the reply.

## 3. Take a look yourself

The website is real, and it's yours:

- Scroll the page and click the **Place an order** button.
- Drag the panel's edge to make the browser narrower: it gives you an idea of how the website looks on a small screen.
- Open the **Files** tab to see what it created. Double-click a file to open it in the Viewer.
- Want to see it in your everyday browser? Click **Open in your computer's browser**. It works while the server is on, and only on your computer.

## 4. Ask for a change

In the same conversation, write something like:

> Change the colors to shades of pink and brown, make the name in the header bigger and put the prices in bold. Then check it in the browser.

- Each file's card shows the before and after: red goes away, green comes in.
- You don't need to start the server again: it always hands out the newest version of the files.
- It may open the page again to check. If the change doesn't show up for you, click **Reload** on the browser bar (or press **F5** with the page or the browser bar in focus).
- Don't like it? **Undo changes**, below the reply, puts the files back the way they were. Reload the page to see it.

Want it to test the button itself? Ask: "click Place an order and check that the page scrolls down to the contact section". In Ask mode, each click asks for your OK. To let it click without asking only on your local website, use **More options > Always in this folder…** on the card, with the rule `Navegador(clicar:localhost)` (it applies on any port; `Navegador(clicar:localhost:8000)` only on 8000).

## 5. Turn the server off

1. Press **Ctrl + Shift + Y**, or click **1 running** in the left sidebar: the **Tasks** tab opens.
2. On the command's card you see the command, how long it has been running and the address with **Open in browser**.
3. Click **Stop**. The card moves to **Recently finished**, as **Stopped**.

If you reload the browser now, it shows **This page could not be opened**. That's expected: the website only exists while the server is on. The files are still in the folder.

Forgot to turn it off? Closing Clave turns it off too. To see the website another day, open the same task and ask: "start the website's server again and open it in the browser".

## When something goes wrong

### The server didn't start

The step in the conversation says the command finished right away, or the browser shows "Nothing answered at that address".

- In the Tasks tab, under **Recently finished**, the command shows up as **Failed**. **View log** shows what it wrote.
- Claude usually reads the error and tries another way on its own. If it doesn't, ask: "the server didn't start, check what happened".
- If the error says `python` is not recognized, ask it to try `py` instead of `python`.
- If you denied the card, or you're in **Plan** mode, the command doesn't run: switch to **Ask** and ask again.
- If the conversation already has 5 commands running in the background, stop one in the Tasks tab.

### The port is in use

The log shows something with "10048", "address already in use" or "EADDRINUSE": there's already another server on that [port](#/aprender/glossario/porta).

- Click **Local**, in the browser, to see what's running and on which port.
- If it's a Clave server you no longer use, stop it in the Tasks tab. If it's one you started in the Console, press **Ctrl + C** in that console.
- Or just ask: "use another port, 8001".

### The tab says "The browser only works in the Clave window"

Clave is open in a regular browser, not in its own window. This happens when it was opened some other way, or when its window couldn't be downloaded: the window is a separate program, about 110 MB, that comes from the internet during installation and with some updates.

- Close Clave and open it again with the **Clave** shortcut on your desktop (or with `Clave.bat`, in the Clave folder), while connected to the internet.
- Meanwhile, the tab itself lists the servers on your computer and opens the website in your everyday browser. Only Claude can't check the website.

### Other snags

- **The change didn't show up**: click **Reload** on the browser bar.
- **"Nothing answered at that address"** after a while: the server stopped. Check the Tasks tab and ask it to start the server again.
- **Claude doesn't open the browser**: check **Settings > Code mode > Let Claude use the Code browser**.

## And to put it on the internet?

The local server only exists on your computer. Publishing the website (doing the [deploy](#/aprender/glossario/deploy)) is another step, with an account on a hosting service. The lesson [Build web pages and small apps](#/aprender/paginas-e-apps) explains the path.
