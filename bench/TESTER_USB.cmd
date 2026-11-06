@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Lancer d'abord OUVRIR_BANC_WEB pour preparer le banc.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" cps_probe.py %*
pause
