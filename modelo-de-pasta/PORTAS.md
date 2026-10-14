# PORTAS.md: portas dos projetos desta pasta

Qual porta cada projeto web usa quando roda no computador. O
`.claude/launch.json` diz como rodar; este arquivo existe para ninguém precisar
abrir JSON para saber se uma porta está livre.

**Criou ou mudou porta? Atualizar o `launch.json` e este arquivo na mesma
tarefa.**

## Faixas

| Tipo de projeto | Faixa |
|---|---|
| Estático servido por `python -m http.server` | 4300–4399 |
| Vite / bundler com servidor próprio | 5170–5199 |
| Backend Python (Flask, FastAPI, servidor próprio) | 8000–8099 |
| Ferramenta e serviço auxiliar | 8700–8799 |

A porta 8040 é do Clave: não usar.

**Porta repetida é bug, não economia:** o que um site guarda no navegador
(`localStorage`, IndexedDB) é separado por porta, então dois projetos na mesma
porta enxergam os dados um do outro.

## Por projeto

| Projeto | Porta | Como sobe | Observação |
|---|---|---|---|
| _(vazio)_ | | | |
