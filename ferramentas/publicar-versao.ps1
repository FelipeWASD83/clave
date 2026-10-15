# Publica a versão atual do Clave como release no GitHub (é ela que o botão Atualizar baixa).
# Antes: subir a versão em versao.json, package.json e CHANGELOG.md, commitar e dar push.
# Precisa do gh logado (gh auth login) com permissão no repositório.
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
Set-Location $raiz

function Rodar([string]$exe, [string[]]$argumentos) {
    # No PowerShell 5.1, com 'Stop', qualquer linha que o git ou o gh escrevam no stderr vira erro fatal,
    # mesmo quando deu certo. Aqui quem decide é o código de saída.
    $ErrorActionPreference = 'Continue'
    $saida = & $exe @argumentos 2>&1 | ForEach-Object { "$_" }
    return [pscustomobject]@{ codigo = $LASTEXITCODE; saida = (($saida -join "`n").Trim()) }
}

$info = Get-Content (Join-Path $raiz 'versao.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$versao = $info.versao
$repo = $info.repositorio
$pacote = Get-Content (Join-Path $raiz 'package.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($pacote.version -ne $versao) { throw "package.json diz $($pacote.version) e versao.json diz $versao. Acerte antes." }
$changelog = Get-Content (Join-Path $raiz 'CHANGELOG.md') -Raw -Encoding UTF8
if ($changelog -notmatch "## $([regex]::Escape($versao)) ") { throw "O CHANGELOG.md não tem a seção da versão $versao." }

if ((Rodar git @('status', '--porcelain')).saida) { throw 'Há mudanças não commitadas. Commite antes de publicar.' }
$r = Rodar git @('fetch', '-q', 'origin')
if ($r.codigo -ne 0) { throw "Não deu para falar com o GitHub (git fetch): $($r.saida)" }
$local = (Rodar git @('rev-parse', 'HEAD')).saida
$r = Rodar git @('rev-parse', '@{u}')
if ($r.codigo -ne 0) { throw 'Este ramo não está ligado ao GitHub. Rode: git push -u origin main' }
if ($local -ne $r.saida) { throw 'O commit atual ainda não foi enviado (git push) ou está atrás do GitHub.' }
if ((Rodar gh @('release', 'view', "v$versao", '--repo', $repo)).codigo -eq 0) { throw "A release v$versao já existe." }

# notas: só a seção desta versão do CHANGELOG (inglês) e, embaixo, a do CHANGELOG.pt-BR (português)
function SecaoDaVersao([string]$texto) {
    $linhas = $texto -split "`r?`n"
    $achou = $linhas | Where-Object { $_ -match "^## $([regex]::Escape($versao)) " } | Select-Object -First 1
    if (-not $achou) { return @() }
    $inicio = [array]::IndexOf($linhas, $achou)
    $saida = @()
    for ($i = $inicio + 1; $i -lt $linhas.Length; $i++) {
        if ($linhas[$i] -match '^## ') { break }
        $saida += $linhas[$i]
    }
    return $saida
}
$notas = SecaoDaVersao $changelog
$arqPt = Join-Path $raiz 'CHANGELOG.pt-BR.md'
if (Test-Path $arqPt) {
    $pt = SecaoDaVersao (Get-Content $arqPt -Raw -Encoding UTF8)
    if ($pt.Count) { $notas += @('', '---', '', '### Português', '') + $pt }
}
$tmp = Join-Path $env:TEMP "clave-release-$versao"
New-Item -ItemType Directory -Force $tmp | Out-Null
$arqNotas = Join-Path $tmp 'notas.md'
[IO.File]::WriteAllText($arqNotas, (($notas -join "`n").Trim()), [Text.UTF8Encoding]::new($false))
$zip = Join-Path $tmp "clave-$versao.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
$r = Rodar git @('archive', '--format=zip', "--prefix=clave-$versao/", '-o', $zip, 'HEAD')
if ($r.codigo -ne 0) { throw "Não deu para gerar o pacote: $($r.saida)" }
# o mesmo pacote com nome fixo e a pasta "clave/": releases/latest/download/clave.zip aponta sempre para a versão
# mais nova, e é para ele que o link curto do comando de instalação aponta
$fixo = Join-Path $tmp 'clave.zip'
if (Test-Path $fixo) { Remove-Item $fixo -Force }
$r = Rodar git @('archive', '--format=zip', '--prefix=clave/', '-o', $fixo, 'HEAD')
if ($r.codigo -ne 0) { throw "Não deu para gerar o pacote de nome fixo: $($r.saida)" }

Write-Host "Publicando v$versao em $repo com $zip e $fixo"
$r = Rodar gh @('release', 'create', "v$versao", $zip, $fixo, '--repo', $repo, '--title', "Clave $versao", '--notes-file', $arqNotas, '--target', $local)
if ($r.codigo -ne 0) { throw "O gh não criou a release: $($r.saida)" }
Write-Host $r.saida
Write-Host 'Pronto. O botão Atualizar dos outros usuários já enxerga esta versão.'
