# Desinstala o Clave: espera o app fechar, tira os atalhos que apontam para esta pasta, o que o Electron guarda em
# %APPDATA%\Clave e a pasta do Clave inteira (com as conversas, que moram em dados\). As tarefas das rotinas no
# Agendador o servidor já tirou antes de chamar este script.
# O servidor copia este arquivo para o %TEMP% e roda de lá, porque a pasta dele vai ser apagada.
param(
    [string]$Pasta = '',
    [int]$Processo = 0,
    [string]$Mensagem = '',
    [string]$MensagemSobrou = '',
    [string]$MensagemParou = '',
    [string[]]$Atalhos = @(),
    [string]$DadosElectron = '',
    [switch]$SemJanela,
    [string]$Config = ''  # o servidor manda tudo num .json (servidor/desinstalador.py), sem briga de aspas
)
$ErrorActionPreference = 'Continue'
if ($Config) {
    $c = Get-Content -LiteralPath $Config -Raw -Encoding UTF8 | ConvertFrom-Json
    $Pasta = [string]$c.Pasta; $Processo = [int]$c.Processo; $Mensagem = [string]$c.Mensagem
    $MensagemSobrou = [string]$c.MensagemSobrou; $MensagemParou = [string]$c.MensagemParou
    $Atalhos = @($c.Atalhos | Where-Object { $_ }); $DadosElectron = [string]$c.DadosElectron
    if ($c.SemJanela) { $SemJanela = [switch]::Present }
}
if (-not $Pasta) { Write-Output 'parou: falta a pasta'; exit 1 }

function Avisar([string]$texto) {
    if ($SemJanela -or -not $texto) { return }
    try {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show($texto, 'Clave') | Out-Null
    } catch { }
}

function Parar([string]$motivo) {
    Write-Output "parou: $motivo"
    Avisar $MensagemParou
    exit 1
}

$Pasta = [IO.Path]::GetFullPath($Pasta).TrimEnd('\')

# trava de segurança: só apaga uma pasta que é, sem dúvida, uma instalação do Clave
$perigosas = @($env:USERPROFILE, $env:SystemRoot, $env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:APPDATA,
    $env:LOCALAPPDATA, [Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('MyDocuments')) |
    Where-Object { $_ } | ForEach-Object { [IO.Path]::GetFullPath($_).TrimEnd('\') }
if ($Pasta.Length -lt 8 -or $Pasta -match '^[A-Za-z]:\\?$' -or ($perigosas -contains $Pasta)) { Parar 'pasta perigosa' }
if (-not (Test-Path -LiteralPath (Join-Path $Pasta 'versao.json')) -or
    -not (Test-Path -LiteralPath (Join-Path $Pasta 'servidor\servidor.py'))) { Parar 'a pasta nao parece o Clave' }
if (Test-Path -LiteralPath (Join-Path $Pasta '.git')) { Parar 'copia de desenvolvimento (tem .git)' }

# 1. espera o app fechar (o servidor manda o número do processo dele) e o que mais rodar de dentro da pasta
if ($Processo) { Wait-Process -Id $Processo -Timeout 30 -ErrorAction SilentlyContinue }
# (o programa mora na pasta, como o Electron e o Python do .venv, ou é a janela do Edge que o modo sem Electron abre
# com o perfil em dados\janela-edge; um editor aberto na pasta não entra)
function DaPasta {
    $eu = $PID
    $perfilEdge = $Pasta + '\dados\janela-edge'
    @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
        $_.ProcessId -ne $eu -and (
            ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($Pasta + '\', [StringComparison]::OrdinalIgnoreCase)) -or
            ($_.CommandLine -and $_.CommandLine.IndexOf($perfilEdge, [StringComparison]::OrdinalIgnoreCase) -ge 0))
    })
}
$limite = (Get-Date).AddSeconds(30)
$vivos = @()
do {
    $vivos = DaPasta
    if (-not $vivos.Count) { break }
    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $limite)
foreach ($p in $vivos) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }

# 2. os atalhos que apontam para esta pasta (os de outra instalação ficam)
if (-not $Atalhos.Count) {
    $Atalhos = @((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Clave.lnk'),
        (Join-Path ([Environment]::GetFolderPath('Programs')) 'Clave.lnk'))
}
$shell = New-Object -ComObject WScript.Shell
foreach ($a in $Atalhos) {
    if (-not (Test-Path -LiteralPath $a)) { continue }
    $lnk = $shell.CreateShortcut($a)
    $alvo = "$($lnk.TargetPath) $($lnk.Arguments) $($lnk.WorkingDirectory)"
    if ($alvo.IndexOf($Pasta + '\', [StringComparison]::OrdinalIgnoreCase) -ge 0 -or
        $lnk.WorkingDirectory.TrimEnd('\') -ieq $Pasta) {
        Remove-Item -LiteralPath $a -Force -ErrorAction SilentlyContinue
    }
}

# 3. o que o Electron guarda fora da pasta (cache e tamanho da janela)
if (-not $DadosElectron) { $DadosElectron = Join-Path $env:APPDATA 'Clave' }
if (Test-Path -LiteralPath $DadosElectron) { Remove-Item -LiteralPath $DadosElectron -Recurse -Force -ErrorAction SilentlyContinue }

# 4. a pasta do Clave (tenta de novo por alguns segundos: o antivírus ou o Windows às vezes seguram um arquivo)
for ($i = 0; $i -lt 10 -and (Test-Path -LiteralPath $Pasta); $i++) {
    Remove-Item -LiteralPath $Pasta -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $Pasta) { Start-Sleep -Seconds 1 }
}
if (Test-Path -LiteralPath $Pasta) {
    Avisar $MensagemSobrou
    exit 2
}
Avisar $Mensagem
exit 0
