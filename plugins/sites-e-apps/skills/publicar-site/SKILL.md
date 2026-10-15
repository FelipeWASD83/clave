---
name: publicar-site
description: Use when the person wants to put a page or site online, for free or with their own domain. Explains the options and does the step by step, always asking for OK before publishing.
---

# Publish a site

Publishing makes the site visible to anyone on the internet. Before:
- go through the skill `sites-e-apps:checklist-web`;
- confirm there is no password, key, personal data or private file in the folder that will go up.

## Options (sites made only of HTML, CSS and JavaScript)
| Option | Good for | How |
|---|---|---|
| **GitHub Pages** | people who already use GitHub or want to learn it | public repository, Settings > Pages > `main` branch |
| **Cloudflare Pages** | fast, own domain is easy | Cloudflare dashboard > Workers & Pages > Create > upload the folder |
| **Netlify** | drag and drop the folder | app.netlify.com > Add new site > Deploy manually |

Recommend one based on what the person already uses; with no preference, Cloudflare Pages or Netlify (uploading the folder through the browser, no commands).

## Step by step
- Prefer to guide through the service's dashboard (the person logs in in their own browser). Don't ask for or type a password.
- If it is done by command (e.g. `npx wrangler pages deploy`), show the command and explain it: in Clave, a command that publishes always asks for OK.
- Own domain: buy it from a registrar (e.g. Registro.br for `.com.br`) and point the DNS as the service indicates.

## Afterwards
Open the published address and check that it loaded, on the computer and on the phone.
