# Instalar as ferramentas mais úteis

Nada aqui é obrigatório para usar o Clave. São programas que o Claude usa em
tarefas maiores. No Windows 10 e 11, o jeito mais fácil é o **winget**, que já
vem no sistema: abra o **PowerShell** (menu Iniciar > digite PowerShell) e cole
o comando. Ou peça ao Claude, no modo Code, para instalar: ele mostra o comando
e pede o seu OK.

## Git: histórico de versões

```powershell
winget install --id Git.Git -e
```

Depois, diga ao Git o seu nome e e-mail (aparecem nas versões que você salvar):

```powershell
git config --global user.name "Seu Nome"
git config --global user.email "seu-email@exemplo.com"
```

Dica: se for publicar projetos no GitHub, use o e-mail "noreply" que o GitHub
oferece (github.com > Settings > Emails) para o seu e-mail não ficar público.

## GitHub CLI (gh): o GitHub pelo terminal

```powershell
winget install --id GitHub.cli -e
gh auth login
```

O `gh auth login` abre o navegador para você entrar na sua conta do GitHub.
Depois disso o Clave consegue usar esse login (Configurações > GitHub).

## Python: automações e planilhas

```powershell
winget install --id Python.Python.3.13 -e
```

No Windows, use o comando `python` (ou `py`), nunca `python3`.

## Node.js: sites modernos e ferramentas

```powershell
winget install --id OpenJS.NodeJS.LTS -e
```

## Visual Studio Code: editor de texto e código (opcional)

```powershell
winget install --id Microsoft.VisualStudioCode -e
```

Bom para abrir e ler os arquivos da pasta, como o `CLAUDE.md`.

## Depois de instalar

Feche e abra de novo o PowerShell (e o Clave) para os comandos novos
aparecerem.
