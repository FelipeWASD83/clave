---
name: pesquisa-tecnica
description: Research in depth before deciding a technical question - which library to use, whether an approach holds up, whether something still works in the current version, whether it runs on the user's system and hardware. Use before choosing a dependency, API, format, engine or architecture; when the answer depends on a version, a changelog or something that changed; and when an error smells like a breaking change. Do not use for a simple factual question or for something that reading the project itself answers.
argument-hint: "[topic or decision]"
allowed-tools: WebSearch WebFetch Read Grep Glob Bash
---

# Technical research before deciding

The goal is not to produce a document. It is to **reach a recommendation that
holds up**, and to be able to defend it when the user asks "why not the other
one?" three messages later.

The general rule applies: **confirmed fact, inference and speculation are
different things** and must not be mixed. And the worst possible result here is
filling a gap with plausibility.

Topic: `$ARGUMENTS`

## 0. Look at the project before looking at the internet

Researching before knowing the terrain produces an incompatible
recommendation. So, first:

- Read the project's documentation (`CLAUDE.md`, `README.md`) and the
  decisions that have already been made.
- See what is already installed and in which version: `package.json`,
  `package-lock.json`, `requirements.txt`, `import`/`require` spread through
  the code.
- Check whether the project **already solves this** in some way. Swapping
  something that works for a personal preference is forbidden: if the
  replacement is worth it, the reason has to appear in the report.
- Note the restrictions that already exist: runtime, build and **deploy
  target**. The project's own documentation and its line in the map (section 8
  of the root `CLAUDE.md`) say how it runs and how it is published, and that
  eliminates candidates before the first search (a Cloudflare Worker doesn't
  run the Node API; an Electron app doesn't have a website's restrictions;
  static hosting doesn't run a backend).

If the decision doesn't belong to any project in the folder, ask which project
it belongs to before continuing.

## 1. Write the decision questions

Before the first search, list what needs to be answered in order to decide.
Typically:

- What are the 2–4 real candidates? (Not ten. Ten options is escaping the choice.)
- What exactly does each one solve, and what does it **not** solve?
- Is it alive? Last release, last commit, open issues piling up?
- Does it run on the user's system (section 0 of `CLAUDE.md`)? On Windows: no WSL, no "only works on Linux"?
- Weight: bundle size, transitive dependencies, build time.
- Does the license allow its use, including in a **commercial** project, if any
  project in this folder is one?
- If it involves local AI or a GPU: does it fit in the graphics card and in
  the memory of the user's computer (section 0 of `CLAUDE.md`; if it isn't
  there, ask)?
- What is the cost of leaving later, if it goes wrong?

That map is the list of searches. Without it, you get five similar searches.

## 2. Search in layers

1. **Terrain**: what it is, the vocabulary, which alternatives are actually used today.
2. **Primary source**: open the **official documentation** and the
   **repository**. A blog tutorial is the origin of most detail errors: it is
   usually one or two major versions behind and teaches an API that no longer exists.
3. **Changelog and releases**: read what changed. This is where the breaking
   change shows up that explains why the example from the internet doesn't run.
4. **Friction**: actively look for people who complain: open issues, "problems
   with", "alternatives to", threads from people who migrated away. If every
   source praises it, only marketing material was read.
5. **Current state**: include the year in the query when currency matters.
   Confirm today's stable version, not the one that was live when the model was trained.

Stop when new searches stop bringing new information, not when a number is
reached. If the last search still revealed something unknown, it isn't over.

## 3. Verify for real: the part only someone with a terminal can do

There is a terminal here. So, whenever possible, **don't believe: test.**

- Check the real published version (`npm view <package> version`,
  `pip index versions <package>`) instead of repeating the tutorial's version.
- Build the smallest possible example in a disposable folder **outside the
  project's folder**, install the candidate and run it. If it doesn't run in
  10 lines, that is data.
- Windows: use `python`, never `python3`. Example commands in PowerShell.
- If the candidate depends on compiling something native, test that: it is
  where most things break on Windows.
- **Do not install anything inside a user's project during the research.**
  The research is disposable; the installation only happens after the user approves.

What was tested becomes **confirmed**. What was only read remains what the
source said, and that has to be visible in the report.

## 4. Recommend, don't push a catalog

One recommendation, with a reason. Compare only what changes the decision, not
a twelve-row table with features the user will never use.

Weigh, when relevant: solves the real problem, ease of use, compatibility with
what already exists in the project, weight, future maintenance, reliability,
cost of leaving. **Do not choose by what is technically more sophisticated.**
For a small tool, "use no library at all" is a valid answer and often the
right one.

If the options truly tie, say that they tie and which criterion breaks the tie,
and do not pretend there is a clear winner.

## 5. Deliver

**Always generate the file**, at `docs/pesquisa-<topic-in-kebab-case>.md`
inside the project's folder (create `docs/` if it doesn't exist). In the chat
goes only the short summary: the recommendation, the reason in two lines, and
what the user needs to decide. Don't repeat the whole file in the chat.

Structure of the file:

```markdown
# Research: <topic>
Date: YYYY-MM-DD · Project: <folder>

## Question
<the decision that had to be made, in one sentence>

## Recommendation
<what to use and why, in up to 5 lines>

## Candidates evaluated
<one block per candidate: what it is, current version, license, pros, cons,
why it was or wasn't chosen>

## What I tested
<command run and real result. If I tested nothing, write "I did not test" and why>

## Risks and what could go wrong
<including the cost of switching later>

## Confirmed / inference / uncertain
Confirmed: <what is in the primary source or was tested here>
Inference: <what I deduced by putting confirmed things together>
Uncertain: <single source, old information, or what I didn't find>

## Sources
<links, with what each one supports>
```

Rules for the file:

- Written in English, explaining **what the thing does and what changes for the
  user**: no lecture on the internals of a web library.
- "I did not find reliable data about X" is useful information and goes in the file.
- No `node_modules/`, `dist/` or test folder left over afterwards. Clean up the
  disposable folder used in the tests.

## 6. Afterwards

The result feeds **section 5 of the folder rules** (plan before code): the
recommendation becomes the plan's approach, and the risks become the item "what
could break". Don't start implementing together with the research: research,
plan, approval, code.

If the user later asks something the research didn't cover, say so and research
again. Don't improvise on top of what you already have.
