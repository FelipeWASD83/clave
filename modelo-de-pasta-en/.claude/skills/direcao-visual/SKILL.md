---
name: direcao-visual
description: Defines the visual direction of a website or app before any CSS is written - reads the library of references, builds three truly different directions and settles on one (picks one itself when the user has not defined the look or has delegated the choice; lets the user choose when they ask for it or when the project is a client's). Use when starting any new web project, when redesigning an existing one, or when the user says something looks ugly or generic.
---

# Visual direction before CSS

There is no default look here. Do not reflexively apply the "default AI" look
(dark background with neon, glassmorphism, purple gradient, a single accent
color, a monospaced font for everything) and do not repeat the look of earlier
projects just because it was used before.

But "no default look" does not mean "no direction": without a direction the
result falls into the generic AI default, which is exactly what the user does
not want. So: **decide the direction explicitly, in writing, before the first
CSS rule.** Who settles the choice is in step 3.

## 0. Read the visual library: mandatory

Before anything else in this skill, read `.claude/referencias-visuais/CLAUDE.md`.
It defines how to pick a reference by project type, how to read the print
instead of the link, and how to turn that into numeric decisions. This skill
assumes that reading is done: the three directions in step 2 come from there.

## 1. Gather what defines the look

Take it from the request and from the project, before asking:

- Who is going to use this, and in what situation (phone in the street? monitor at home?).
- Is it the user's personal project, an internal tool, or **a client's**?
  If it is a client's, **the client's identity comes first** and the directions
  only vary inside it.
- What feeling the thing has to convey in 2 seconds.
- Is there a reference the user already liked? A print is worth more than ten adjectives.

Ask only for the **fact** that cannot be deduced **and** blocks the work
(especially if it is a client's), at most 3 questions. For the rest (amount of
content, whether it goes live, where the images come from): assume what is
reasonable, write the assumption next to the directions and carry on. **Taste
is not a question:** if the user didn't say, it is my choice (step 3).

## 2. Build 3 distinct directions

Three **truly different** directions, not three variations of the same thing
with another color. Each one in up to 4 lines:

```
NAME OF THE DIRECTION
Feeling: <what it conveys>
Color: <the role of the colors, not only the hex values>
Typography: <style and contrast between title and body>
Motion: <is there animation? what is its role?>
Reference: <entry in the library + print file>
Decisions: <up to 3 numeric decisions taken from that print>
```

Take the reference from `.claude/referencias-visuais/CLAUDE.md`, choosing the
section from the table in step 1 of that file (the type and frequency of use
decide, not taste; in a client's project, the client's identity comes before
everything). **Cite the print file**, not only the name of the site, and have
looked at the print, not only at the link. If the user already sent a print,
the user's reference takes priority.

## 3. Settle the choice

- **The user asked to choose** ("show me options", "I want to choose") →
  present the three and wait. CSS only after the user's choice (or mix).
- **A client's project** → the three, inside the client's identity, go to the
  user to choose: the decision belongs to the user together with the client.
  Unless the user says I choose.
- **In all other cases** (a personal project with no defined look, "you
  choose", "choose everything", "do it however you think is best") → **I settle
  on one**, say which one and why in up to two lines, show the other two
  briefly (so the user can swap) and carry on. Do not hand this choice back as
  a question.

The settled direction goes into the plan from section 5 of the folder rules as
a decision already made. If the user delegated in so many words ("choose
everything", "do it however you think is best" and the like), there is no
"go ahead?" pause: tell the direction in a few lines and move on to step 4.
Without that phrase, the plan waits for the "go ahead" like any non-trivial
task, it just doesn't carry a pending choice.

## 4. Settle the system before spreading it around

With the direction settled, define everything at once and use it everywhere:

- Spacing scale (4/8/12/16/24/32/48/64).
- Type scale (3 to 5 sizes, not twelve).
- Palette: background, surface, strong text, weak text, border, action, error, success.
- Border radius and shadow: **one** value of each per level, not improvised per component.
- Transition duration: a fast one (150ms) and a normal one (300ms).

Write this as CSS variables at the top of the file, with a comment in plain
English saying what each group controls, so the user can change a color by
hand without understanding the rest.

## 5. Anti-generic rule

If the result could be the website of anything else just by swapping the text,
the direction failed. Each project needs at least **one element that only makes
sense in it**: it can be the treatment of the title, an illustration, the way
the list behaves, the texture of the background. One, done well, is worth more
than five effects.

## 6. Weight is cost

An external font, an animation library and a shader come in only if they pay
for their own weight. An award-winning studio site carries 8 MB because the
product **is** the experience. A tool the user uses every week, no. Three.js/GSAP
in a small project go into the plan with the weight and the reason written
down, never silently.

## 7. Finish by comparing with the reference

Once the direction is settled and the CSS is written, **do not declare it done
without comparing**: capture the result at 1440×900 and put it next to the
reference's print, answering the five questions from step 4 of
`.claude/referencias-visuais/CLAUDE.md` (hierarchy, breathing room, scale
contrast, role of the color, unique element). The skill that carries out this
comparison is `revisar-visual`: it is manual, so open
`.claude/skills/revisar-visual/SKILL.md` and follow its steps 2, 3.5 and 4.
