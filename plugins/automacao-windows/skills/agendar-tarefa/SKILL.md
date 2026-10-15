---
name: agendar-tarefa
description: Use when the person wants a script or program to run on its own at a set time (every day, every week, at startup), through the Windows Task Scheduler.
---

# Schedule a task in Windows

First ask: is it a **script** (or program) or a **request for Claude**? A request for Claude (e.g. "every day at 8am summarize the emails in folder X") fits better as a **Clave routine** (left sidebar > Routines), which already has a spending cap and permission rules.

## For a script
1. Confirm the script works by running it by hand first.
2. Show the command before running it and explain each part. Use a folder of your own in the Task Scheduler, so the person can find it later:

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"C:\path\to\meu-script.ps1`" -Valendo"
$trigger = New-ScheduledTaskTrigger -Daily -At 18:00
Register-ScheduledTask -TaskPath "\My automations\" -TaskName "Organize Downloads" -Action $action -Trigger $trigger -Description "Created with Clave"
```

   Other triggers: `-Weekly -DaysOfWeek Monday,Friday -At 9:00`, `-AtLogOn`.
3. Test it right away: `Start-ScheduledTask -TaskPath "\My automations\" -TaskName "Organize Downloads"` and check the result (the script's log).
4. Teach how to turn it off and delete it:
   - in the **Task Scheduler** app (Start menu), folder "My automations";
   - or `Disable-ScheduledTask` / `Unregister-ScheduledTask` with the same names (deleting asks for the person's OK in Clave).

## Care
- The task runs as the user who created it and only while the PC is on.
- Nothing that needs administrator rights unless the person understands why.
- A scheduled script must keep a log: it is the only way to know what it did on its own.
