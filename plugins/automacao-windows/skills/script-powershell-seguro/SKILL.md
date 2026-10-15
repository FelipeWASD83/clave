---
name: script-powershell-seguro
description: Use when creating a PowerShell script that the person will run again (organize, rename, copy, generate a report). The script shows what it would do first, keeps a log and never deletes directly.
---

# Safe PowerShell script

## Script rules
- **Dry run by default:** the script starts with `param([switch]$Valendo)` ("Valendo" means "for real"). Without `-Valendo`, it only shows what it would do. Explain this to the person.
- **Never delete:** instead of `Remove-Item`, move to a `_lixeira` folder next to it, with the date in the name. The person decides when to empty it.
- **Log:** every action goes to a `registro-AAAA-MM-DD.csv` file (date, action, source, destination). With it, undoing is possible.
- **Accents and special characters:** save the `.ps1` as UTF-8 **with BOM** (Windows PowerShell 5.1 reads a file without BOM in another encoding and breaks them). If `escrever_arquivo` writes without BOM, warn the person and offer a `.bat` that calls the script.
- **Paths with spaces** always in quotes; use `Join-Path` instead of joining text.
- An error stops the script: `$ErrorActionPreference = 'Stop'` and `try/catch` with a clear message in the person's language.
- Never use `Set-ExecutionPolicy` for the whole computer.

## How to deliver
1. Show the script and explain in 3 to 5 lines what it does.
2. Run it in dry-run mode and show the result.
3. Only run with `-Valendo` after the person's OK.
4. Teach how to run it again with a double click: create a `.bat` next to it:

```bat
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0meu-script.ps1" -Valendo
pause
```

5. If it is meant to run on its own every day, offer the skill `automacao-windows:agendar-tarefa` or a Clave routine.
