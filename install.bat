@echo off
rem First-time setup: create venv with non-Anaconda Python 3.14 and install dependencies.
setlocal
if not exist ".venv\Scripts\python.exe" (
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
echo Environment is ready. Run run.bat to start the app.
endlocal