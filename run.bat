@echo off
rem Launch "My Clock" app. Restore this comment file to ASCII to avoid codepage issues.
setlocal
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py
endlocal