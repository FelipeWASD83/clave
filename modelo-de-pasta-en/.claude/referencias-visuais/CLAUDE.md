# Visual library: how to use it

Design reference for **every new website and every redesign** done in this
folder.

**Mandatory reading before proposing a visual direction and before writing the
first line of CSS.** It is not a catalog to admire: it is working material.
Each reference here has a print saved in `prints/`, a suitable use, the
concrete decisions it authorizes and what should **not** be copied from it.

Last check of the links and capture of the prints: **2026-09-01**.

---

## 1. The mistake this file exists to avoid

A reference turns into junk in three ways:

1. **A reference by link.** Writing down "make it like Linear" and never
   opening the print. Result: a generic dark mode that has nothing of Linear.
2. **A reference of the wrong type.** Copying an award-winning studio portfolio
   onto a tool used every day. The studio's product **is** the experience: 8 MB,
   shaders, a 4-second intro. Nobody puts up with that the thirtieth time they
   open the prompt generator.
3. **A reference without translation.** Looking at the print, saying
   "beautiful", and writing CSS the way you always do. A reference that doesn't
   turn into numbers (px, ms, weight, scale) changed nothing.

---

## 2. The procedure, in four steps

### Step 1: Choose by type of project, not by taste

| What I am doing | Section to use |
|---|---|
| Landing page, campaign, showcase, portfolio, launch page | **Spectacle** and **Award winners** |
| App, tool, panel, game with a UI, dashboard, institutional site | **Product** |
| A **real client's** site | The client's identity comes first. The two lists become only execution vocabulary, never a source of direction. |

If the project is used **more than once by the same person**, it is Product,
even if it is beautiful. Frequency of use decides, not the subject.

### Step 2: Analyze the print, not the link

Open the file in `prints/` and really look at it. The link is for checking the
live site afterwards; the reading is done on the print, because that is where
you can measure.

For each chosen reference, answer these five questions **in writing**, before
proposing anything:

```
COMPOSITION  How many columns? What takes up the biggest block of the screen?
             What is in the corners? Where is the emptiness and why is it there?
TYPOGRAPHY   How many families? What is the ratio between the largest and the
             smallest size? Is the weight the contrast, or is it the size?
             Where do mono (monospaced) and serif come in?
SPACING      Is the breathing room bigger vertically or horizontally?
             Is the grid visible (lines, markers) or implicit?
COLOR        How many colors actually exist? Is the color in the background, in
             the text or only in the image? What does the action color do that
             no other does?
MOTION       What moves, when, and what happens if nothing moves?
             Is the animation before or after the first reading?
```

If the answer to any question is "can't tell from the print", open the live
site. Don't invent.

### Step 3: Translate into concrete decisions

The reading above turns into a list of **numeric** decisions, which is already
the start of the system asked for by the `direcao-visual` skill. Format:

```
From <reference>: <what I took> → <decision in the project>

E.g.: From Produx: giant headline in a light weight → h1 at 96px/300, not 48px/700.
E.g.: From Igloo: technical labels in the four corners → metadata in mono 11px,
      tracking 0.08em, fixed at the top and at the bottom.
E.g.: From Linear: a two-color sentence → first clause in pure white,
      the rest in 60% gray, same font, same size.
```

Rule: **at most three decisions come out of each reference.** More than that is
not a reference, it is copying. And decisions that fight each other cannot come
out of different references (Obys's rigid grid + Iventions's diagonal in the
same layout doesn't work: choose one).

### Step 4: Compare the result with the reference at the end

Once the CSS is finished, **capture the result at 1440×900** (the
`revisar-visual` skill does this; or
`python .claude/referencias-visuais/capturar-print.py`) and put the screenshot
next to the reference's print. Objective questions:

- Is the **hierarchy** as clear as the reference's? Can you tell in half a
  second what the most important thing on the screen is?
- Is the **breathing room** comparable, or is mine cramped? Measure: how much
  is left around the main block in the reference, how much in mine.
- Is the **scale contrast** between title and body similar? If the reference
  uses 6× and mine uses 1.8×, I took nothing from it.
- Is the **color** playing the same role, or did I only copy the hex?
- Does mine have **one element that only makes sense in this project**? If
  swapping the text turns it into the site of anything else, the direction failed.

Only declare it done after this comparison. And tell the user, in plain
language, what was taken from which reference, without CSS jargon.

---

## 3. Spectacle: WebGL, shaders, heavy animation

Studio portfolios and brand experiences. **An excellent reference for a landing
page and a campaign; terrible for a tool used every day.**

### Lusion: https://lusion.co
![Lusion](prints/espetaculo-lusion-topo.png)

- **Use when:** the project has an object/product that deserves to be the hero
  and there is a weight budget for it.
- **Decisions it inspires:** the hero is a **framed media block** with a large
  radius, taking up ~90% of the width and leaving a light margin around it,
  instead of an image bleeding across the whole screen; navigation in pills;
  `+` markers in the corners of the block making the grid explicit; a
  medium-weight neo-grotesque typeface (no black weight); an almost-white
  background with a slight cool tone.
- **Do not copy:** the real-time 3D scene. It is their product, not
  decoration: in a personal project it becomes 8 MB to say the same thing an
  image would.

### Obys Agency: https://obys.agency
![Obys](prints/espetaculo-obys-topo.png)

- **Use when:** the content is a list/portfolio and the editorial composition
  has to carry the visual weight.
- **Decisions it inspires:** a text index on the left working as navigation; a
  narrow central column of black-and-white images; a layout switcher
  (`Vertical, Horizontal, Grid`) in the footer as a real feature, not
  decoration; everything in gray, leaving color only where there is a colored image.
- **Do not copy:** the body text at ~11px and the light gray of the project
  list. Beautiful in the print, unreadable for someone who needs to use it.

### basement.studio: https://basement.studio
![basement.studio](prints/espetaculo-basement-studio-topo.png)

- **Use when:** the project has a personality of its own and can afford to be funny.
- **Decisions it inspires:** **a single illustrated scene** as the element that
  only makes sense in that project (here, the basement with the arcade and the
  dog); discreet counters next to menu items (`Showcase (26)`); a mode toggle
  in the center of the footer.
- **Do not copy:** the light nav over a dark scene with no protective strip: in
  the print, half of the items almost vanish into the background.

### Igloo Inc: https://igloo.inc
![Igloo](prints/espetaculo-igloo-topo.png)

- **Use when:** there is a single object to show and the mood is technical,
  cold, silent. (It is a crypto project's site: look at the execution, not the subject.)
- **Decisions it inspires:** a **HUD in the four corners**: logo and copyright
  at the top left, manifesto at the top right, scroll instruction at the
  bottom; everything in a mono font; dimensions and measurements drawn over the
  object; a monochrome palette so the object is the only thing with shape.
- **Do not copy:** sound on by default and the long narrative tied to the scroll.

### By-Kin: https://by-kin.com/
![By-Kin](prints/espetaculo-by-kin-topo.png)

- **Use when:** a small brand with a short, good name that can bear becoming a
  graphic element.
- **Decisions it inspires:** a **giant logotype bleeding off the left margin**
  instead of a small logo in the corner; warm beige + a single orange;
  numbered thumbnails `01 02 03` in a narrow column; an occasional human
  illustration in a corner, with no frame or glow around it.
- **Do not copy:** the extremely low density. It works with 4 pieces of
  information on the screen; with 20 it becomes disorganization.

### Iventions: https://iventions.com/
![Iventions](prints/espetaculo-iventions-topo.png)

- **Use when:** the subject is an event, a party, movement: something with energy.
- **Decisions it inspires:** a background split on the **diagonal** by two flat
  colors; a slightly rotated photo with rounded corners breaking the diagonal;
  a giant wordmark cut by the bottom edge; lime-green pill buttons as the only
  action color.
- **Do not copy:** diagonal + rotation on a text-heavy site. Every crooked
  element charges a reading tax.

### Mat Voyce: https://matvoyce.tv
![Mat Voyce](prints/espetaculo-mat-voyce-topo.png)

- **Use when:** the typography is the content.
- **Decisions it inspires:** two huge words in heavy italic, **misaligned** (one
  at the top left, the other at the bottom right), creating a diagonal without
  drawing any diagonal; pure cyan on cream, and only that; the `SCROLL` label
  as a graphic pill in the corner.
- **Do not copy:** two colors and giant type on a site that has to explain
  something. Here the whole message fits in two words.

### Minh Pham: https://minhpham.design/
![Minh Pham](prints/espetaculo-minh-pham-topo.png)

- **Use when:** there is a good dark photo and the headline needs attitude.
- **Decisions it inspires:** a headline stacked in 4 lines with **one word in
  color** and the rest in beige; a darkened photo in the background with no flat
  overlay (the photo itself is already dark); social icons in a vertical column
  on the left.
- **Do not copy:** the `START` gate before the content: see section 6.

> **Active Theory** (https://activetheory.net) is also a reference in this
> section, but it **has no valid print**: see section 7.

---

## 4. Recent award winners: Awwwards, August 2026

An award-winning site ages fast. This list is of the moment; its value is the
**print**, which keeps being useful even when the site goes offline or changes.

### ERA Residence: https://www.era-residence.com/
![ERA Residence](prints/premiado-era-residence-topo.png)

- **Use when:** real estate, hospitality, an expensive product, something
  aspirational with good photography.
- **Decisions it inspires:** a tall, thin display serif for the name + **script
  only in the signature** (the word "Estepona"), never in body text; a
  `BY DAY / BY NIGHT` toggle as a real control that changes the photo; a
  circular seal with text on an arc as a watermark; the photo taking up the
  bottom 60%, a clean sky holding the title above.
- **Do not copy:** script for anything beyond a single signature word.

### Aardvark Book Club: https://aardvarkbookclub.com
![Aardvark Book Club](prints/premiado-aardvark-book-club-topo.png)

- **Use when:** a physical product, a club, a subscription, something cheerful
  and cheap to produce (shapes + simple renders, no photo studio).
- **Decisions it inspires:** a yellow background with **organic blobs in two
  shades of the same yellow** (texture without an image); a heavy, rounded
  grotesque sans-serif for the title; products floating in light 3D, rotated; a
  handwritten note as a secondary detail; strong pink and orange pill buttons.
- **Do not copy:** a long paragraph in black on saturated yellow: it tires the
  eyes quickly. A title can take it; running text, no.

### Decathlon Yestalgia: https://decathlonyestalgia.com/
![Decathlon Yestalgia](prints/premiado-decathlon-yestalgia-topo.png)

- **Use when:** a campaign with vertical video (phone content) in the center.
- **Decisions it inspires:** a **hard shadow with no blur** and a thick black
  border on buttons and cards; loose stickers (a lightning bolt, hatched arcs)
  scattered without symmetry; a vertical 9:16 video as the hero, centered, with
  a neutral light gray background around it.
- **Do not copy:** the 90s vocabulary when the brand doesn't call for it. Here
  it is intentional (the name is *Yestalgia*); applied by reflex it becomes a costume.

### State of AI in Design 2026: https://stateofaidesign.com/
![State of AI in Design](prints/premiado-state-of-ai-design-topo.png)

- **Use when:** a report, a long article, editorial content that needs a strong cover.
- **Decisions it inspires:** **deliberate asymmetry**: a small caption at the
  bottom left against a giant title on the right; a strip of gradient images
  taking up the top half as texture, with labels (`FOUNDER`,
  `CREATIVE DIRECTOR`) in little white boxes over them; mono only for credits
  and metadata; `Scroll to read` centered in the footer with an arrow.
- **Do not copy:** nothing critical. It is the safest reference in this section
  for reading content.

### Vero: https://verostudio.com/
![Vero](prints/premiado-vero-studio-topo.png)

- **Use when:** fashion, weddings, craft: something with skin, fabric, warm light.
- **Decisions it inspires:** a **typographic mix in a single line**: italic
  ("Custom"), small caps ("SCULPTURE"), italic again ("of your"), small caps
  ("WEDDING DRESS"); a classic serif in capitals for the brand; full-screen
  video with a single warm dominant color; menu and CTA in discreet
  translucent pills in the corners.
- **Do not copy:** autoplay full-screen video with no alternative: it is heavy
  and disappears on a phone with a bad connection.

### NOTHIN': https://www.noth.in
![NOTHIN](prints/premiado-nothin-topo.png)

- **Use when:** the brand name is short and the proposal is radically direct.
- **Decisions it inspires:** **brutal scale contrast**: supporting text at
  ~16px against a wordmark of ~300px on the same screen; black and white, with
  no third color; information pushed into the four corners and the whole middle
  handed over to the word; a black pill button with an arrow as the only point
  of action.
- **Do not copy:** that scale with a long name. It breaks the word and turns
  into soup.

### Produx Design: https://www.produx.design
![Produx](prints/premiado-produx-design-topo.png)

- **Use when:** a brand, a consultancy, something serious that doesn't want to look heavy.
- **Decisions it inspires:** **giant typography in a light weight** (300), which
  gives elegance without shouting, the opposite of the reflex of using bold;
  markers in brackets (`[SCROLL DOWN]`, `[ MENU ]`) as UI framing; only two
  families: a grotesque sans-serif for the sentence, mono for the description;
  near-black (#0d0d0d) instead of pure black.
- **Do not copy:** the medium gray on black of the paragraph. For real
  reading, raise the contrast.

### Miu Miu · A House that we shaped: https://immersivebags.miumiu.com/
![Miu Miu](prints/premiado-miu-miu-immersive-bags-abertura.png)

> This print is the **opening screen** (the site is an experience with an entry
> gate and sound). It is valid as a typographic reference, not as a navigation one.

- **Use when:** a brand campaign with a short sentence to fill the screen.
- **Decisions it inspires:** words distributed on a **scattered grid**: aligned
  on invisible columns, with wide tracking, forming a block without looking like
  a paragraph; flat navy blue as the only color; a small centered supporting
  sentence at the bottom.
- **Do not copy:** the entry gate and the "please turn on your sound".

---

## 5. Product: beautiful because it works

Most of what gets built in a work folder comes from here. **The default for an
app, tool, panel and institutional site.**

### Linear: https://linear.app
![Linear hero](prints/produto-linear-hero.png)
![Linear section](prints/produto-linear-secao.png)

- **Use when:** a tool with a lot of information on the screen; anything that
  needs density without turning into clutter.
- **Decisions it inspires:**
  - **A two-color sentence:** the main clause in pure white, the rest of the
    same sentence in ~60% gray: same font, same size, same weight. It builds
    hierarchy without enlarging anything.
  - **A gray scale with 3–4 levels of text** on an almost-black background
    (#08090a), never pure black.
  - **Lowercase mono labels** for metadata (`FIG 0.1`,
    `POWERING THE COMPANIES BUILDING THE FUTURE`): mono only here, never in body text.
  - **A 3-column grid with thin vertical dividers** separating blocks of
    content; wireframe illustration (thin line, no fill) in place of a screenshot.
  - A strip of client logos on a single line, all at the same optical height.
- **Do not copy:** dark gray in long running text. It works for a supporting
  sentence; it doesn't work for a paragraph that someone needs to read.

### Vercel: https://vercel.com
![Vercel](prints/produto-vercel-topo.png)
![Vercel scroll](prints/produto-vercel-scroll.png)

- **Use when:** a technical product that needs clarity and a pair of CTAs.
- **Decisions it inspires:** a hero in **three columns**: title + buttons on the
  left, visual in the center, three short bullets on the right; a **solid light
  primary button + an outline-only secondary**, both pills, side by side; a
  strip of client logos fixed at the base of the hero; the following sections
  with a framed screenshot of the real interface.
- **Do not copy:** the radial glow of the central graphic. It disappears on a
  bad monitor and in light mode, and carries no information.

### Apple (product pages): https://www.apple.com/macbook-pro/
![Apple top](prints/produto-apple-macbook-pro-topo.png)
![Apple section](prints/produto-apple-macbook-pro-scroll.png)

- **Use when:** you need scroll rhythm: one idea per screen, no rush.
- **Decisions it inspires:** a **sticky secondary nav for the product**
  (`Overview / Tech Specs / Compare`) appearing after the hero; price and CTA in
  a single dark capsule instead of two loose elements; **expandable chips** with
  `+` in a column on the left and the product on the right; a headline with a
  subtle gradient applied to **one part of the sentence**; one idea per screen,
  each section with the same vertical breathing room.
- **Do not copy:** the photographic production. Without a studio, trying to
  imitate that hard light in a homemade render comes out worse than a simple,
  honest photo. Take the **rhythm**, not the resources.

### Stripe: https://stripe.com
*(no print: see section 7)*

- **Use when:** you need to explain something complex (documentation, an API, a
  product with many concepts).
- **Decisions it inspires:** code and explanation side by side at the same
  height; a gradient used as a section signature, not as the background of
  everything; documentation navigation with three visible levels without
  looking like a file tree.
- **Do not copy:** the amount of animated gradient at the top.

---

## 6. What to copy and what not to copy: the general rule

**Copy:** spacing rhythm, typographic hierarchy, the role of color, the
duration and curve of transitions, how the content is sequenced in the scroll,
how the metadata is handled.

**Do not copy, in any project in this folder:**

- An **entry gate** before the content. A real example, captured:

  ![Entry gate](prints/antipadrao-unseen-portao-de-entrada.png)

  This is the home page of Unseen Studio. There is no content at all until you
  click. Acceptable on a studio showcase that a person visits once; a defect in
  anything that gets used again. Minh Pham and Miu Miu do the same.
- **Hijacked scroll** that prevents normal scrolling (several in the Spectacle
  section do this: in the print, the page is 900px tall and the scroll is fake).
- **Sound on by default**, or a request to "turn on your sound".
- A **custom cursor** with no function.
- **Animation that delays the first reading.** Animate after the content is
  readable, not before.
- **Text with low contrast for the sake of style.**
- **Requiring WebGL** for the site to work.

---

## 7. References without a print: open them live

These four are part of the library, but **have no valid print on this
machine**. None of them can be used as visual evidence, cited in place of a
print, or enter the final comparison in step 4. To use any of them, **open the
site in a normal browser** and read from there, or choose another reference.

| Reference | Section | Why it has no print |
|---|---|---|
| **Stripe**: https://stripe.com | Product | On the machine where this library was put together, the antivirus intercepted `stripe.com` (and `docs.stripe.com`) with a "protected mode" screen: the capture came from the antivirus, not from the site. |
| **Active Theory**: https://activetheory.net | Spectacle | The site returns "your browser is not supported" to an automated browser. What shows up is an error screen, not the design, so it is no evidence of anything. |
| **hobro.digital**: https://hobro.digital | Award winners | It is behind Cloudflare's anti-bot check. Solving a CAPTCHA is not something I do. |
| **Uncommon Studio**: https://uncommonstudio.com.au/ | Spectacle | It doesn't render in an automated browser: it comes out as a black screen. It is valid as a reference for a firm grid with planned breaks, but only live. |

Another limitation, visible in the prints: sites with an entry gate were
captured **at the gate** when the automatic click didn't work. This is stated
in each one's entry.

## 8. How to capture a new print

The capture tool is `capturar-print.py`, in this folder. It starts Edge in
headless mode, waits, scrolls the page to trigger the entrance animations,
hides the cookie banner and saves the PNG at 1440×900:

```bash
python .claude/referencias-visuais/capturar-print.py lista.json .claude/referencias-visuais/prints
```

Where `lista.json` is (the field names stay in Portuguese, as the script expects them):

```json
[
  {"arquivo": "produto-exemplo-topo.png", "url": "https://example.com", "espera": 8},
  {"arquivo": "produto-exemplo-secao.png", "url": "https://example.com", "espera": 8, "y": 1400}
]
```

Fields: `arquivo` (the file name to save), `url`, `espera` (seconds to wait after
loading), `y` (scroll to this position before capturing; only works on a site
with real scroll), `clique` (a list of button texts to click before, e.g.
`["enter"]`) and `espera_clique` (seconds to wait after the click).

**File name:** `<section>-<site>-<what>.png`, all lowercase with hyphens. The
section is one of four prefixes, which stay as they are: `espetaculo`
(Spectacle), `premiado` (Award winners), `produto` (Product) and `antipadrao`
(anti-pattern). The files already here end in Portuguese words (`topo` = top,
`secao` = section, `abertura` = opening screen); new ones can end in any short
English word.

A new print **only enters the library together with its text**: suitable use,
the decisions it inspires and what not to copy. A print without those three
becomes decoration.

---

## 9. Galleries: for finding a new reference

- Awwwards: https://www.awwwards.com/websites/sites_of_the_day/
- Awwwards, WebGL filter: https://www.awwwards.com/inspiration_search/webgl/
- Recent.design (formerly Godly): https://recent.design/

When bringing something new from here: capture the print, classify it as
Spectacle / Award winners / Product, and write the three parts of the entry. A
reference that comes in only as a link doesn't count.
