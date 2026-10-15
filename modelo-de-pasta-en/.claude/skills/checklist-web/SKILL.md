---
name: checklist-web
description: Checklist of what must be ready before saying that a website or web app works. Always use it before declaring any HTML/CSS/JS deliverable finished, and when reviewing an existing web project.
---

# Checklist: only call it done after this

The user often cannot audit the code to find out what was left half-done.
If I say "done" with an empty handler, they only find out when the app breaks
in front of them. So: go through this list **before** saying I am finished, and
report any item that failed instead of hiding it.

The point is not to paste the whole list into the answer. It is to check it and
mention only what failed or what was decided not to do.

## States: what is missing most often

- [ ] **Empty**: a list with no items, a search with no results, the first visit.
      It shows a message, not a blank area.
- [ ] **Loading**: anything that takes a while shows a spinner, a skeleton or text.
- [ ] **Error**: a fetch that fails, invalid JSON, an API that is down, permission
      denied (camera, microphone, file). It shows what happened and what to do.
- [ ] **Success**: the action confirms that it worked, instead of looking the
      same as before.
- [ ] A button that triggers a slow action stays disabled while it runs, so it
      can't fire twice.

## Functionality

- [ ] No empty handler, no `TODO`, no function that returns a fixed value
      pretending to work.
- [ ] Every visible button, link and field does something. If it is decorative,
      it doesn't look clickable.
- [ ] The user's data survives a refresh (F5), or the user is told that it doesn't.
- [ ] Invalid input doesn't break anything: an empty field, text where a number
      is expected, a negative number, huge text, accented characters and emoji.
- [ ] **Clean console**: zero errors. A known, harmless warning is fine, but
      explain which one.
- [ ] Zero 404s in the network tab (font, icon, image, JSON).

## Mobile and responsive

- [ ] Tested at **390px wide**, not only on the monitor.
- [ ] No horizontal scroll.
- [ ] Touch targets of at least ~44×44px.
- [ ] Text readable without zooming (at least 16px for body text).
- [ ] Nothing essential hidden behind `:hover`: there is no hover on a phone.

## Visual

The numbers in this section are the default: the chosen direction may change
any of them if it says in writing why. Contrast, alternating backgrounds and
`prefers-reduced-motion` are not part of that exception.

- [ ] **Backgrounds alternating by tone** (a rule of the folder): two visible
      blocks in a row are never light/light or dark/dark, footer included,
      **measured** from the computed luminance, not judged by eye.
- [ ] Spacing comes from a scale (4/8/12/16/24/32/48), not from random numbers.
- [ ] At most 2 font families, and they actually load (check the network).
- [ ] Contrast of normal text ≥ 4.5:1 against the background.
- [ ] Clear hierarchy: you can tell what is the title, what is body text and what
      is the main action by looking for 2 seconds.
- [ ] If there is animation, it has a purpose and is short (150–400ms). Long
      animation on something that repeats becomes an annoyance.
- [ ] `prefers-reduced-motion` respected when there is heavy motion.

## Minimum accessibility

- [ ] The main things can be reached and used with the keyboard alone (Tab, Enter, Esc).
- [ ] Keyboard focus is visible.
- [ ] An image that carries information has `alt`; a decorative image has `alt=""`.
- [ ] A modal closes with Esc and returns focus to where it came from.

## Before closing

- [ ] No leftover debugging `console.log`.
- [ ] No API key inside a front-end file.
- [ ] If I edited something that already worked, what worked still works.
- [ ] If I could not verify an item (no browser, no data, no key),
      **say that I didn't verify it** instead of marking it as done.
