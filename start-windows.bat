@echo off
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Install Python 3.11 or 3.12 and try again.
    pause
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 (
  pause
  exit /b 1
)
echo Open http://127.0.0.1:8080 after the server starts.
python -m app.server
pause
