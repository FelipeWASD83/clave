---
name: organizar-arquivos
description: Use to tidy up a messy folder (Downloads, Documents, photos): sorts by type or date, shows a preview before moving, never deletes and leaves a way to undo.
---

# Organize files

## 1. Look first
- List the folder (with subfolders, if it makes sense) and count: how many files of each type, the biggest, the oldest.
- Ignore system and hidden files (`desktop.ini`, `Thumbs.db`, those that start with `~$`).

## 2. Propose the organization
Suggest a criterion and show how it would look, before moving anything. Example for Downloads:

| Folder | What goes there |
|---|---|
| Documents | .pdf .docx .xlsx .txt .csv |
| Images | .jpg .png .webp .heic |
| Installers | .exe .msi |
| Archives | .zip .rar .7z |
| Videos and audio | .mp4 .mov .mp3 .wav |
| Other | everything else |

Ask whether the person also wants to split by year (e.g. `Images\2026`).

## 3. Move with a log
- Move, don't delete. Duplicate with the same name at the destination: add ` (2)` to the name, never overwrite.
- Save `organizacao-AAAA-MM-DD.csv` with the source and destination of each file.
- Next to it, create `desfazer-organizacao.ps1`, which reads the CSV and puts everything back.
- For many folders or to repeat every month, make a script with the skill `automacao-windows:script-powershell-seguro`.

## 4. Wrap up
Say how many files went to each folder, where the log and the undo script are, and what was left out (and why).
