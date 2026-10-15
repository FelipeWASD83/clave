---
name: entregar-site
description: Delivery checklist before publishing a client's website or putting anything live. Use when the user talks about publishing, uploading, delivering, "it's ready for the client", deploying to Cloudflare, or touching something that is already in production.
argument-hint: "[project]"
disable-model-invocation: true
---

# Website delivery

This touches money and reputation. A bug in a personal project is an annoyance;
a broken contact form on a client's website is a lost client with nobody ever
finding out why.

Project: `$0`

## 0. First of all: is it production?

Check in the project map (section 8 of the root rules) whether this project is
marked as a **client's** or as **already live**. If it is, any change here is a
change in production:

- **Confirm with the user before touching anything.** This is not a rhetorical
  question, it is a lock.
- If the project has a `COMO-PUBLICAR.md` (the "how to publish" guide) or a
  `README.md`, **read it first**: that site's publishing process takes priority
  over this skill.
- Never touch an `_originais/` folder: it is a client's irreplaceable raw
  material, and there is no copy here.
- Never remove a folder that section 7 marked as a live demo or as a
  dependency of another project, even if it looks like a duplicate.

If the root rules say nothing about this project, **ask whether it is a
client's** before continuing. Finding that out after publishing is no use.

## 1. Run it and look

Start it through `.claude/launch.json` and go through the whole of
`revisar-visual`: screenshots at 1440 and at 390, clean console, zero 404s in
the network. It is manual too: open `.claude/skills/revisar-visual/SKILL.md`
and follow it. Then the `checklist-web`.

If the agent's app has a project preview (Claude Code Desktop does, through
`launch.json`), the server already starts there: use that instead of starting
it by hand.

## 2. What only matters at delivery

Things that don't show up during development and show up for the client:

**Links and navigation**
- [ ] Every internal link leads to a page that exists. No leftover `href="#"`.
- [ ] The menu works on every page, not only on the home page.
- [ ] External links open in a new tab (`target="_blank"` with `rel="noopener"`).
- [ ] `404.html` exists and has a way back to the home page.

**What shows up when it is shared on WhatsApp**
- [ ] A specific `<title>` per page: not "Document" and not the same name repeated on all of them.
- [ ] `<meta name="description">` on each page.
- [ ] Open Graph: `og:title`, `og:description`, `og:image` (an image of at least
      1200×630, with an **absolute** URL, not a relative one: with a relative one the preview breaks).
- [ ] Test the preview for real, don't trust that you wrote the tag.

**Identity**
- [ ] The favicon exists and is not the browser's default.
- [ ] Name, phone, e-mail, tax ID and address **checked against the client's
      material**, character by character. A wrong phone number is the worst
      possible mistake here.
- [ ] The WhatsApp link is in the format `https://wa.me/<country code and number, digits only>` and tested.
- [ ] No leftover placeholder text: "Lorem ipsum", "Your text here",
      "company@example.com", "(000) 000-0000".

**Contact form**, if there is one
- [ ] Send a real test and **confirm that it arrived**. A form that doesn't
      send is the most expensive and quietest defect of a small-business website.
- [ ] Required fields are validated, an invalid e-mail is refused.
- [ ] There is a success message and an error message.

**Weight and search**
- [ ] No giant image served straight from the client's phone (4 MB of JPEG in
      a banner). Resize and compress, **as a new copy, never over the original**.
- [ ] `robots.txt` and `sitemap.xml` exist and point to the right domain.
- [ ] Run Lighthouse through the agent's browser tool and report the numbers.
      Don't chase 100; report whatever is red.

**Hygiene**
- [ ] Zero debugging `console.log`.
- [ ] No API key in the front end.
- [ ] No internal comment visible in the HTML ("fix this later",
      "client hasn't paid yet").

## 3. Publish

- Follow the project's `COMO-PUBLICAR.md`. If it doesn't exist, ask how that
  site is published: **do not invent a deploy process.**
- **Publishing is the user's decision** (section 7 of the root rules): show the
  command and wait, unless the user has released that project in writing. A
  client's project **never** goes up without an order from the user in the
  conversation.
- After publishing, **open the production URL** and check: the page loads, the
  favicon shows up, an internal link works, the share preview is right. A
  deploy that "worked" in the terminal and a 404 live happens all the time.

## 4. Report

```
Live at: <URL>
Checked in production: <what I actually opened and tested>
Fixed before going up: <list>
Left pending: <what couldn't be done, and why>
Needs the client: <information that was missing and only the client has>
```

If any item could not be verified, say it was not verified. Do not mark as
done what was not tested.
