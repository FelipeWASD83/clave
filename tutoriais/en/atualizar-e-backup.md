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

- **Download backup**: a file with your conversations, projects and spending history.
- **Import backup**: brings everything back (on a new computer, for example).

Attached files and the key are not included in the backup. You create the key again in the Console; send the attachments again if you need them.

To be safe, also keep a copy of Clave's `dados` folder on an external hard drive or in the cloud from time to time (with Clave closed).

## Signing out and uninstalling

In **Settings > Updates & about**, at the bottom:

- **Sign out**: deletes the API key and the saved passwords (e-mail, GitHub, connectors), sets every setting back to default and turns routines off. Your conversations, projects and memory stay. Then the welcome screens and the tours show up again, like the first time. It's for handing the computer to someone else or starting over with another key.
- **Uninstall**: Clave closes and deletes its folder (with the conversations, which live inside it), the shortcuts and the routines' tasks in the Windows Task Scheduler. This can't be undone: if you want to keep your conversations, download the backup first.
