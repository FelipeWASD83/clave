# Instala o que a skill ver-video precisa: ffmpeg e yt-dlp (pelo winget) e um ambiente Python
# com faster-whisper e Pillow em %USERPROFILE%\.claude\ver-video\venv. Pode rodar de novo sem problema.
$ErrorActionPreference = 'Stop'
$raiz = Join-Path $env:USERPROFILE '.claude\ver-video'
$venv = Join-Path $raiz 'venv'

function Tem($nome) { [bool](Get-Command $nome -ErrorAction SilentlyContinue) }

Write-Host '== ver-video: instalando o necessário =='

if (-not (Tem 'winget')) {
    Write-Host 'O winget não está disponível. Instale ffmpeg e yt-dlp manualmente.'
} else {
    if (-not (Tem 'ffmpeg')) {
        Write-Host '-> instalando ffmpeg (winget Gyan.FFmpeg)'
        winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements --silent | Out-Host
    } else { Write-Host 'ffmpeg: ok' }
    if (-not (Tem 'yt-dlp')) {
        Write-Host '-> instalando yt-dlp (winget yt-dlp.yt-dlp)'
        winget install --id yt-dlp.yt-dlp -e --accept-source-agreements --accept-package-agreements --silent | Out-Host
    } else { Write-Host 'yt-dlp: ok' }
}

# Python: o lançador "py" é o mais confiável no Windows; "python" pode ser o atalho da Microsoft Store.
$py = $null
if (Tem 'py') { $py = @('py', '-3') }
elseif (Tem 'python') {
    $v = & python -c "import sys; print(sys.version_info[:2] >= (3, 9))" 2>$null
    if ($v -eq 'True') { $py = @('python') }
}
if (-not $py) {
    if (Tem 'winget') {
        Write-Host '-> instalando Python 3.13 (winget Python.Python.3.13)'
        winget install --id Python.Python.3.13 -e --accept-source-agreements --accept-package-agreements --silent | Out-Host
        $py = @("$env:LOCALAPPDATA\Programs\Python\Python313\python.exe")
    } else { throw 'Python não encontrado. Instale o Python 3.10 ou mais novo em python.org e rode de novo.' }
}

New-Item -ItemType Directory -Force $raiz | Out-Null
if (-not (Test-Path (Join-Path $venv 'Scripts\python.exe'))) {
    Write-Host '-> criando o ambiente Python da skill'
    $pyExe = $py[0]
    $pyArgs = @()
    if ($py.Length -gt 1) { $pyArgs = $py[1..($py.Length - 1)] }
    & $pyExe @pyArgs -m venv $venv
}
$pip = Join-Path $venv 'Scripts\python.exe'
Write-Host '-> instalando faster-whisper, Pillow e numpy (alguns minutos)'
& $pip -m pip install --disable-pip-version-check -q --upgrade pip
& $pip -m pip install --disable-pip-version-check -q faster-whisper pillow numpy

if (Tem 'nvidia-smi') {
    Write-Host '-> placa NVIDIA encontrada: instalando as bibliotecas de GPU (cuBLAS e cuDNN)'
    & $pip -m pip install --disable-pip-version-check -q nvidia-cublas-cu12 'nvidia-cudnn-cu12==9.*'
} else {
    Write-Host 'Sem placa NVIDIA: a transcrição vai rodar no processador (mais devagar, com o modelo small).'
}

& $pip -c "import faster_whisper, PIL, numpy; print('ver-video: tudo pronto')"
