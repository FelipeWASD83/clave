# Install the most useful tools

Nothing here is required to use Clave. These are programs that Claude uses for
bigger tasks. On Windows 10 and 11 the easiest way is **winget**, which already
comes with the system: open **PowerShell** (Start menu > type PowerShell) and
paste the command. Or ask Claude, in Code mode, to install it: it shows the
command and asks for your OK.

## Git: version history

```powershell
winget install --id Git.Git -e
```

Then tell Git your name and e-mail (they appear on the versions you save):

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Tip: if you are going to publish projects on GitHub, use the "noreply" e-mail
that GitHub offers (github.com > Settings > Emails) so your e-mail doesn't
become public.

## GitHub CLI (gh): GitHub from the terminal

```powershell
winget install --id GitHub.cli -e
gh auth login
```

`gh auth login` opens the browser so you can sign in to your GitHub account.
After that, Clave can use that login (Settings > GitHub).

## Python: automations and spreadsheets

```powershell
winget install --id Python.Python.3.13 -e
```

On Windows, use the `python` command (or `py`), never `python3`.

## Node.js: modern websites and tools

```powershell
winget install --id OpenJS.NodeJS.LTS -e
```

## Visual Studio Code: text and code editor (optional)

```powershell
winget install --id Microsoft.VisualStudioCode -e
```

Good for opening and reading the files in the folder, such as `CLAUDE.md`.

## After installing

Close and reopen PowerShell (and Clave) so the new commands show up.
