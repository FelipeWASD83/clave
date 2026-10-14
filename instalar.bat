@echo off
rem Instala o Clave: Python, dependencias, a janela do app (Electron) e os atalhos.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ferramentas\instalar.ps1" %*
echo.
pause
