# Checks the Git of the projects in this folder (each subfolder of the root is a project).
# - Creates Git in the ones that don't have it yet (with the root .gitignore) and saves a first version.
# - Lists the ones with unsaved changes and the ones with no copy on GitHub.
# Sends nothing to the internet: sending (git push) is your decision.
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host 'Git is not installed. See _organizacao\instalar-ferramentas.md.'
    exit 1
}
$ignorar = @('.claude', '_organizacao', '_originais', 'node_modules')
$semGitHub = @()
$sujos = @()
Get-ChildItem -LiteralPath $raiz -Directory -Force | Where-Object { $ignorar -notcontains $_.Name -and -not $_.Name.StartsWith('.') } | ForEach-Object {
    $p = $_.FullName
    if (-not (Test-Path (Join-Path $p '.git'))) {
        Write-Host "-> creating Git in $($_.Name)"
        git -C $p init -q
        if (-not (Test-Path (Join-Path $p '.gitignore'))) { Copy-Item (Join-Path $raiz '.gitignore') (Join-Path $p '.gitignore') }
        git -C $p add -A
        git -C $p commit -q -m 'First version' 2>$null
        if ($LASTEXITCODE -ne 0) { Write-Host '   (did not save the version: set your name in Git, see the tools guide)' }
    }
    if (git -C $p status --porcelain) { $sujos += $_.Name }
    if (-not (git -C $p remote)) { $semGitHub += $_.Name }
}
Write-Host ''
if ($sujos) { Write-Host "With unsaved changes: $($sujos -join ', ')" } else { Write-Host 'No project has unsaved changes.' }
if ($semGitHub) { Write-Host "No copy on GitHub: $($semGitHub -join ', ')" } else { Write-Host 'All projects have a copy on GitHub.' }
