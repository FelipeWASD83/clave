# Confere o Git dos projetos desta pasta (cada subpasta da raiz é um projeto).
# - Cria o Git em quem ainda não tem (com o .gitignore da raiz) e salva uma primeira versão.
# - Lista quem tem mudança não salva e quem não tem cópia no GitHub.
# Não envia nada para a internet: enviar (git push) é decisão sua.
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host 'O Git não está instalado. Veja _organizacao\instalar-ferramentas.md.'
    exit 1
}
$ignorar = @('.claude', '_organizacao', '_originais', 'node_modules')
$semGitHub = @()
$sujos = @()
Get-ChildItem -LiteralPath $raiz -Directory -Force | Where-Object { $ignorar -notcontains $_.Name -and -not $_.Name.StartsWith('.') } | ForEach-Object {
    $p = $_.FullName
    if (-not (Test-Path (Join-Path $p '.git'))) {
        Write-Host "-> criando Git em $($_.Name)"
        git -C $p init -q
        if (-not (Test-Path (Join-Path $p '.gitignore'))) { Copy-Item (Join-Path $raiz '.gitignore') (Join-Path $p '.gitignore') }
        git -C $p add -A
        git -C $p commit -q -m 'Primeira versão' 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Host '   (não salvou a versão: configure seu nome no Git, veja o guia de ferramentas)' }
    }
    if (git -C $p status --porcelain) { $sujos += $_.Name }
    if (-not (git -C $p remote)) { $semGitHub += $_.Name }
}
Write-Host ''
if ($sujos) { Write-Host "Com mudança não salva: $($sujos -join ', ')" } else { Write-Host 'Nenhum projeto com mudança não salva.' }
if ($semGitHub) { Write-Host "Sem cópia no GitHub: $($semGitHub -join ', ')" } else { Write-Host 'Todos os projetos têm cópia no GitHub.' }
