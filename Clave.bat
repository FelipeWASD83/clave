@echo off
rem Abre o Clave. Na primeira vez, roda o instalador.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Primeira vez: instalando o Clave...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ferramentas\instalar.ps1"
  if errorlevel 1 ( pause & exit /b 1 )
)
start "" ".venv\Scripts\pythonw.exe" "%~dp0ferramentas\abrir.pyw"
