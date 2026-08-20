@echo off
rem Build a single .exe for users without Python (uses .venv + PyInstaller).
setlocal
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Run install.bat first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install pyinstaller
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --windowed --onefile --name MyClock --collect-all PySide6.QtMultimedia main.py
echo.
echo Done. The executable is: dist\MyClock.exe
endlocal