---
name: checklist-web
description: Use before saying that a page or site is ready. Checks phone, large screens, contrast, links, forms, console errors and image weight.
---

# Checklist before saying "done"

Check each item and say which ones you really checked and which ones you couldn't check.

**It works**
- [ ] Opens with no error in the browser console.
- [ ] All links and buttons go where they say. No forgotten `href="#"`.
- [ ] Form: required fields warn, success and error messages show up.

**On any screen**
- [ ] Phone (390 px wide): nothing is cut off, nothing scrolls sideways, text is readable without zooming.
- [ ] Laptop (1440 px) and wide monitor (2560 px or more): the content is not stretched or lost in a corner.
- [ ] Portrait screen (1080 × 1920): the layout still makes sense.

**Readable and usable**
- [ ] Contrast between text and background of at least 4.5:1 (small text).
- [ ] Images with `alt`; fields with labels; can be navigated with Tab.
- [ ] Tab title (`<title>`) and description (`<meta name="description">`) are right; tab icon.

**Light**
- [ ] Images at the size they are shown (no 5 MB photo in a tiny square), as `.webp` or `.jpg`.
- [ ] No password, key or token in the page's code: anything in the HTML, anyone can see.
