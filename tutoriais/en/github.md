---
titulo: Git and GitHub for people who have never used them
trilha: 4. Going further
ordem: 33
duracao: 7 min
resumo: Keep versions of your work, have a backup on the internet and connect GitHub to Clave.
---

## Git: the version history

[Git](#/aprender/glossario/git) keeps "snapshots" of your folder over time (the [commits](#/aprender/glossario/commit)). Changed something and broke it? Go back to the previous snapshot. It is the best safety net for working in Code mode, because you can always undo.

You don't need to learn the commands: ask Claude.

```experimentar-code
Does this folder already use Git? If not, explain what it is, turn it on and save a first version of everything. Show me the commands before running them.
```

Then, at the end of each piece of work:

```experimentar-code
Save a version in Git with a message explaining what changed today.
```

## GitHub: Git on the internet

[GitHub](#/aprender/glossario/github) is a website that keeps Git repositories in the cloud. It is useful for:

- **backup**: your computer broke, your work is still there;
- **sharing** projects with other people;
- **working as a team**, with [issues](#/aprender/glossario/issue) and [pull requests](#/aprender/glossario/pull-request).

Repositories can be **private** (only you see them) or **public**. **Never** send passwords, keys or personal data to GitHub, not even in a private repository.

That's what [`.gitignore`](#/aprender/glossario/gitignore) is for: a text file in the folder listing what Git must never keep (for example, `.env` and `*.key`). What's on it doesn't go into the versions and doesn't go to GitHub. What should never leave your computer is in [Passwords, keys and personal data](#/aprender/segredos-e-dados).

```experimentar-code
Check whether this folder has a .gitignore that leaves out passwords, keys and files with personal data. If something is missing, show me what you would add before changing it.
```

## Connect GitHub to Clave

In **Settings > GitHub**:

- If you have the **gh** program (GitHub CLI) installed and logged in, click **Use gh login**.
- Or create a **personal token** on GitHub (Settings > Developer settings > Personal access tokens) and paste it into Clave.

With GitHub connected, you can:

- **Attach files** from a repository to a conversation (paperclip > GitHub files).
- Turn on the **GitHub** button in the text box so Claude can look at your repositories and read code, issues and pull requests.
- (Optional) Let it **create issues, comment and open pull requests**: each action asks for your OK first.

```experimentar
List my GitHub repositories and tell me which ones have been idle the longest.
```

## Send your project to GitHub

In Code mode, ask:

```experimentar-code
I want to keep this folder on GitHub as a private repository. Explain the step-by-step to me and do what you can from here, always showing me the commands first.
```

Clave always asks for your OK before a `git push` (the command that sends things to the internet).
