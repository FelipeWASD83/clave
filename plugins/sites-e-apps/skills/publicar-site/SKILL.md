---
name: publicar-site
description: Use quando a pessoa quiser pôr uma página ou site no ar, de graça ou com domínio próprio. Explica as opções e faz o passo a passo, sempre pedindo OK antes de publicar.
---

# Publicar um site

Publicar deixa o site visível para qualquer pessoa na internet. Antes:
- passe pela skill `sites-e-apps:checklist-web`;
- confirme que não há senha, chave, dado pessoal nem arquivo privado na pasta que vai subir.

## Opções (sites só de HTML, CSS e JavaScript)
| Opção | Bom para | Como |
|---|---|---|
| **GitHub Pages** | quem já usa ou quer aprender GitHub | repositório público, Settings > Pages > branch `main` |
| **Cloudflare Pages** | rápido, domínio próprio fácil | painel da Cloudflare > Workers e Pages > Criar > enviar a pasta |
| **Netlify** | arrastar e soltar a pasta | app.netlify.com > Add new site > Deploy manually |

Recomende uma pelo que a pessoa já usa; sem preferência, Cloudflare Pages ou Netlify (enviar a pasta pelo navegador, sem comando).

## Passo a passo
- Prefira guiar pelo painel do serviço (a pessoa faz login no navegador dela). Não peça nem digite senha.
- Se for por comando (ex.: `npx wrangler pages deploy`), mostre o comando e explique: no Clave, comando que publica sempre pede OK.
- Domínio próprio: compre num registrador (ex.: Registro.br para `.com.br`) e aponte o DNS como o serviço indicar.

## Depois
Abra o endereço publicado e confira que carregou, no computador e no celular.
