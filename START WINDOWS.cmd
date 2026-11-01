@echo off
cd /d "%~dp0"
py -3 app.py
if errorlevel 1 (
  echo.
  echo Could not start the app. Install Python 3 with Tcl/Tk and try again.
  pause
)

