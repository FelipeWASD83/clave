---
titulo: Updating Clave and backing up
trilha: 4. Going further
ordem: 35
duracao: 3 min
resumo: How to get new versions and keep a copy of your conversations.
---

## Updating

Clave looks for a new version once a day, when it opens. If there is one, the **Update** button appears at the bottom of the left sidebar. You can also check right away in **Settings > Updates & about**.

When you click **Update and restart**:

1. it shows what changed in the new version;
2. it downloads the version from GitHub and checks the package;
3. it keeps the current version (if the new one doesn't open, it goes back to the previous one on its own);
4. it restarts.

Your conversations, settings, memories and key **are not touched**: they stay in the `dados` folder, which the update doesn't change.

## Backing up your conversations

In **Settings > Data & backup**:

- **Download chat backup**: a file with your conversations, projects, routines and spending history.
- **Import backup**: brings everything back (on a new computer, for example).

Attached files, the key and the [memory](#/aprender/memoria) are not included in the backup. You create the key again in the Console; send the attachments again if you need them. The memory lives in the `dados\memoria` folder: the copy of the `dados` folder, just below, takes it along.

To be safe, also keep a copy of Clave's `dados` folder on an external hard drive or in the cloud from time to time (with Clave closed).

What about the files of your own work, in the Code mode folders? That's a different story: see [Undo, backup and Git: your safety net](#/aprender/rede-de-seguranca).

## Signing out and uninstalling

In **Settings > Updates & about**, at the bottom:

- **Sign out**: deletes the API key, the saved passwords (e-mail, GitHub, connectors) and the Code browser's data (the sites' logins and cookies), sets every setting back to default and turns routines off. Your conversations, projects and memory stay. Then the welcome screens and the tours show up again, like the first time. It's for handing the computer to someone else or starting over with another key.
- **Uninstall**: Clave closes and deletes its folder (with the conversations, which live inside it), the shortcuts and the routines' tasks in the Windows Task Scheduler. This can't be undone: if you want to keep your conversations, download the backup first.
