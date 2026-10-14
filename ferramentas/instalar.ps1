# Instalador do Clave para Windows 10 e 11.
# 1. Acha (ou instala) o Python 3.10+   2. Cria o ambiente .venv e instala as dependências
# 3. Baixa o Electron oficial (a janela do app)   4. Cria os atalhos na área de trabalho e no menu Iniciar
# Pode rodar de novo quando quiser: ele só refaz o que estiver faltando.
param([switch]$SemAtalhos)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Tem($nome) { [bool](Get-Command $nome -ErrorAction SilentlyContinue) }
function Titulo($t) { Write-Host ''; Write-Host "== $t ==" -ForegroundColor Cyan }

function Python-Ok($exe, $args0) {
    try {
        $saida = & $exe @args0 -c "import sys; print(sys.version_info[:2] >= (3, 10))" 2>$null
        return ($saida -eq 'True')
    } catch { return $false }
}

Titulo 'Clave: instalação'
Write-Host "Pasta: $raiz"

# ---------- 1. Python ----------
Titulo '1/4 Python'
$py = $null; $pyArgs = @()
if ((Tem 'py') -and (Python-Ok 'py' @('-3'))) { $py = 'py'; $pyArgs = @('-3') }
elseif ((Tem 'python') -and (Python-Ok 'python' @())) { $py = 'python' }
if (-not $py) {
    Write-Host 'O Python 3.10 ou mais novo não foi encontrado.'
    if (Tem 'winget') {
        $r = Read-Host 'Instalar o Python 3.13 agora pelo winget? (S/n)'
        if ($r -eq '' -or $r -match '^[sSyY]') {
            winget install --id Python.Python.3.13 -e --accept-source-agreements --accept-package-agreements | Out-Host
            $candidato = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'
            if (Test-Path $candidato) { $py = $candidato }
        }
    }
    if (-not $py) {
        Write-Host 'Instale o Python em https://www.python.org/downloads/ (marque "Add python.exe to PATH") e rode este instalador de novo.' -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "Python: $py $pyArgs"

# ---------- 2. Ambiente e dependências ----------
Titulo '2/4 Ambiente do Clave'
$venvPy = Join-Path $raiz '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPy)) {
    Write-Host 'Criando o ambiente .venv...'
    & $py @pyArgs -m venv (Join-Path $raiz '.venv')
}
Write-Host 'Instalando as dependências (pode levar um minuto)...'
& $venvPy -m pip install --disable-pip-version-check -q --upgrade pip
& $venvPy -m pip install --disable-pip-version-check -q -r (Join-Path $raiz 'requirements.txt')
& $venvPy -c "import anthropic, openpyxl; print('Dependências: ok (anthropic', anthropic.__version__ + ')')"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'As dependências não carregaram. Se o Windows mostrou um aviso de "Controle de Aplicativo", veja o README (Smart App Control).' -ForegroundColor Yellow
    exit 1
}

# ---------- 3. Electron ----------
Titulo '3/4 Janela do app (Electron)'
& $venvPy (Join-Path $raiz 'ferramentas\preparar.py') | Out-Host
$electron = (& $venvPy (Join-Path $raiz 'ferramentas\preparar.py') --checar | Select-Object -Last 1)
if (-not $electron) { Write-Host 'Sem o Electron, o Clave abre numa janela do navegador. Tudo funciona igual.' -ForegroundColor Yellow }

# ---------- 4. Atalhos ----------
Titulo '4/4 Atalhos'
if ($SemAtalhos) {
    Write-Host 'Pulando os atalhos (-SemAtalhos).'
} else {
    $shell = New-Object -ComObject WScript.Shell
    $icone = Join-Path $raiz 'app\img\icone.ico'
    $destinos = @(
        (Join-Path ([Environment]::GetFolderPath('Desktop')) 'Clave.lnk'),
        (Join-Path ([Environment]::GetFolderPath('Programs')) 'Clave.lnk')
    )
    foreach ($d in $destinos) {
        $lnk = $shell.CreateShortcut($d)
        # o abrir.pyw confere a versão do Electron antes de abrir (atualização que troca o Electron)
        $lnk.TargetPath = (Join-Path $raiz '.venv\Scripts\pythonw.exe')
        $lnk.Arguments = '"' + (Join-Path $raiz 'ferramentas\abrir.pyw') + '"'
        $lnk.WorkingDirectory = $raiz
        $lnk.IconLocation = $icone
        $lnk.Description = 'Clave: o Claude pela API'
        $lnk.Save()
        Write-Host "Atalho criado: $d"
    }
}

Titulo 'Pronto!'
Write-Host 'Abra o Clave pelo atalho na área de trabalho (ou pelo Clave.bat nesta pasta).'
