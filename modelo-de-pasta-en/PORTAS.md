# PORTAS.md: ports of the projects in this folder

Which port each web project uses when it runs on the computer. The
`.claude/launch.json` says how to run it; this file exists so nobody has to
open JSON to find out whether a port is free.

**Created or changed a port? Update the `launch.json` and this file in the same
task.**

## Ranges

| Type of project | Range |
|---|---|
| Static, served by `python -m http.server` | 4300–4399 |
| Vite / bundler with its own server | 5170–5199 |
| Python backend (Flask, FastAPI, custom server) | 8000–8099 |
| Tool or helper service | 8700–8799 |

Port 8040 belongs to Clave: do not use it.

**A repeated port is a bug, not a saving:** what a website stores in the
browser (`localStorage`, IndexedDB) is separated by port, so two projects on
the same port see each other's data.

## By project

| Project | Port | How it starts | Notes |
|---|---|---|---|
| _(empty)_ | | | |
