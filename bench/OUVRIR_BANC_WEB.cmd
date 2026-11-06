@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto failure
)
".venv\Scripts\python.exe" ensure_environment.py
if errorlevel 1 goto failure
start "" ".venv\Scripts\pythonw.exe" "%~dp0web_launcher.py"
exit /b 0
:failure
echo Python 3.11 ou plus recent est requis. Lire le message ci-dessus.
pause
exit /b 1
