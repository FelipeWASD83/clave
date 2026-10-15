---
name: automacao-sem-ia
description: Use when the person wants something done repeatedly (every day, every e-mail that arrives, every new order, every few minutes) and the steps are always the same. Builds a small Python program that runs WITHOUT AI through the Windows Task Scheduler, costing zero tokens per run, instead of a routine that calls Claude every time.
---

# Automation without AI

Write everything the person reads in their language. This needs Code mode (a working folder); in chat, explain the plan and ask the person to open Code mode in the folder where the automation will live.

**Why:** a Clave routine calls Claude on every run, and it runs at most once an hour ("Every N hours", from 1 to 24). Checking every hour is 24 calls a day, about 730 a month, and each one pays for the instructions and for what it reads, even when nothing new arrived. Checking every 15 minutes is not possible with a routine at all. A program with fixed rules, run by the Windows Task Scheduler, does the same job in seconds for zero tokens, as often as needed. Show the person this comparison in plain words before building. If you put a money value on it, use the prices on Clave's Pricing & plans page and say it is an estimate.

## 1. Understand the repeated task
Ask, at most 4 things at a time:
- What starts it (a new e-mail, a file in a folder, a time of day) and how often?
- The input: where it comes from, and 2 or 3 real examples, including an unusual one.
- The output: where the result goes (spreadsheet, folder, a website's API or form, an e-mail) and an example of a correct result.
- What must never happen (a duplicated row, an e-mail sent to a client by mistake, a file deleted).

Write it back in one line and confirm it: "Every 15 min: new e-mails in the Pedidos folder from @cliente.com.br → one row per item in Pedidos.xlsx → the e-mail moves to Processados".

## 2. Does it really need AI?
- **Predictable input** (a form, a system notification, a fixed subject, an export, the same supplier's PDF, a CSV): no AI. Rules do it: column names, fixed positions, regular expressions.
- **Free text that varies a lot** (clients writing orders their own way, complaints to classify): say clearly that rules will miss cases, and offer:
  1. **Hybrid:** the program does everything predictable and sends only what the rules can't read to the cheapest model in Clave's list (Haiku), through the API with the `anthropic` package, a short prompt and a daily call limit written in the program. The API key goes to the Credential Manager like any password.
  2. **Review list:** the program puts what it can't read in an "A revisar" folder or sheet; a person handles it, or a Clave routine once a day (1 call a day instead of 24 for an hourly routine).
  3. **Fix the source:** ask the senders to use a form or a spreadsheet template. Often the best fix.
- Never use AI just to check whether something new arrived: that is exactly what the program does for free.

## 3. Build the program
A folder of its own (e.g. `automacoes\pedidos\`) with `pedidos.py`, `config.json` (folders, server, sheet; **no passwords**), `estado.json` (ids already processed), `pedidos.log`, `.venv\` only if it needs packages, and `LEIA-ME.txt` (section 6).

Standard library first:
- **E-mail:** `imaplib` + `email`, IMAP over SSL (port 993). Use UIDs, read with `BODY.PEEK[]` (doesn't mark as read) and move what was processed to another mail folder. Gmail needs 2-step verification and an **app password**. A company e-mail at a hosting provider usually takes the normal password (server and port from the provider). **Outlook.com and Microsoft 365 no longer accept a password or an app password over IMAP** (only OAuth sign-in, since 2024): say so before starting; a simple way out is an Outlook rule that forwards those e-mails to a mailbox that accepts IMAP.
- **Excel:** `openpyxl`. Append after the last row; never rewrite the sheet. Saving loses images, shapes and macros, so the program writes to a sheet or file of its own. Excel open on the file (`PermissionError`): log it and leave the item for the next run. Copy the file to `backup\` once a day.
- **CSV that opens right in Excel in Brazil:** `csv` with `delimiter=";"` and `encoding="utf-8-sig"`.
- **A website:** its official API (with a token) through `urllib.request` or `requests`; for a form, send the same fields the form sends. Respect the site's terms of use.
- **A site with no API and no form:** Playwright, as a last resort (it breaks when the site changes). `p.chromium.launch(channel="msedge")` uses the Edge already installed, with no browser download.
- **WhatsApp:** don't automate WhatsApp Web (against WhatsApp's terms; the number can be banned). The official way is the WhatsApp Business Platform, which needs a Meta business account.

**Passwords and keys** never go in the program, `config.json`, the log or the chat. Use the `keyring` package (Windows Credential Manager). The person stores the password in a PowerShell window of their own, not through you:
`.\.venv\Scripts\python.exe -m keyring set pedidos-email vendas@empresa.com.br` (it asks for the password; nothing shows while typing). It appears in Control Panel > Credential Manager > Windows Credentials.

Every program follows this skeleton (write the log messages in the person's language):

```python
import argparse, json, logging, sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
import keyring

PASTA = Path(__file__).resolve().parent  # the scheduler starts in another folder
CONFIG = json.loads((PASTA / "config.json").read_text(encoding="utf-8"))
ESTADO = PASTA / "estado.json"  # ids already processed: an item is never done twice

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--testar", action="store_true", help="reads and logs what it would do; writes nothing")
    testar = ap.parse_args().testar
    saidas = [RotatingFileHandler(PASTA / "pedidos.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")]
    if sys.stderr:  # pythonw.exe has no console
        saidas.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, handlers=saidas, format="%(asctime)s %(levelname)s %(message)s")
    senha = keyring.get_password(CONFIG["servico"], CONFIG["usuario"])
    if not senha:
        logging.error("Password not found in the Credential Manager"); return 1
    feitos = set(json.loads(ESTADO.read_text(encoding="utf-8"))) if ESTADO.exists() else set()
    novos = [i for i in ler_entrada(senha) if i["id"] not in feitos]
    logging.info("%d new item(s)%s", len(novos), " [TEST]" if testar else "")  # one line even when 0: it is alive
    for item in novos:
        try:
            if testar:
                logging.info("would do: %s", resumo(item)); continue
            processar(item)  # never deletes: moves to Processados
            feitos.add(item["id"])
            ESTADO.write_text(json.dumps(sorted(feitos)), encoding="utf-8")  # only after the output is saved
        except Exception:  # one bad item doesn't stop the others; it stays for the next run
            logging.exception("error in %s", item["id"])
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## 4. Install and test
1. In the automation folder: `py -3 -m venv .venv` (or `python -m venv .venv`), then `.\.venv\Scripts\python.exe -m pip install openpyxl keyring` (only what it uses).
2. If Windows blocks a package ("Uma política de Controle de Aplicativo bloqueou este arquivo", from Smart App Control), tell the person and choose another way. Never suggest turning off Windows protections.
3. The person stores the password (section 3). Then run with `--testar` on real data, show the person what it would do and adjust.
4. One real run by hand; check the output (`excel_ler`) and the log. Run again: nothing duplicated.

## 5. Schedule it in the Windows Task Scheduler
Show the commands before running them and explain each part. Use a folder of its own (`\Automacoes\`); `\Clave\` belongs to Clave's routines.

```powershell
$pasta = "C:\path\to\automacoes\pedidos"
$acao = New-ScheduledTaskAction -Execute "$pasta\.venv\Scripts\pythonw.exe" -Argument "`"$pasta\pedidos.py`"" -WorkingDirectory $pasta
$quando = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 15)
$opcoes = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskPath "\Automacoes\" -TaskName "Pedidos para planilha" -Action $acao -Trigger $quando -Settings $opcoes -Description "No AI. Log: $pasta\pedidos.log"
```

- `pythonw.exe` runs with no window; with no end date the repetition goes on forever; `IgnoreNew` skips a run while the previous one is still going.
- `schtasks /Create ... /SC MINUTE /MO 15` does the same, but quoting paths with spaces in `/TR` from PowerShell is error-prone; the commands above avoid it.
- Test it now: `schtasks /Run /TN "Automacoes\Pedidos para planilha"`, wait a few seconds and read the log.
- It runs while the computer is on and the person is signed in to Windows. Running with no one signed in needs the Windows password stored in the task: explain it and let the person decide.

## 6. Hand it over in plain language
Tell the person, and write the same in `LEIA-ME.txt`, in their language:
- What it does and how often.
- **See what it did:** open `pedidos.log` in Notepad; the last lines are the latest runs.
- **Pause:** Task Scheduler (Start menu) > folder Automacoes > right click > Disable, or `schtasks /Change /TN "Automacoes\Pedidos para planilha" /DISABLE` (`/ENABLE` to resume).
- **Remove:** `schtasks /Delete /TN "Automacoes\Pedidos para planilha" /F` (Clave asks for an OK before deleting). The folder can stay.
- **Password changed:** run the `keyring set` command again.
- **When it will stop working:** the sender changes the format, the password changes, the sheet is renamed or moved. The log shows the error; then ask Claude to adjust the program.

## Before saying it's done
- [ ] `--testar` ran on real data and the person saw the result.
- [ ] One real run checked in the output and in the log; a second run duplicated nothing.
- [ ] No password, token or key in any file of the folder, including the log.
- [ ] The task ran once through the scheduler and the log shows that run.
- [ ] `LEIA-ME.txt` written, and the person knows where the log is and how to pause it.
