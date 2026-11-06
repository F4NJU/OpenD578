@echo off
setlocal
cd /d "%~dp0"
echo Arreter le moteur du banc avant de lancer ces essais.
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto finish
)
".venv\Scripts\python.exe" ensure_environment.py
if errorlevel 1 goto finish
".venv\Scripts\python.exe" run_base_tests.py %*
echo Un code 2 indique une qualification incomplete, pas une panne du poste.
:finish
pause
