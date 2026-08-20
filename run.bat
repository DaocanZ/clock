@echo off
rem 启动"我的时钟"应用（隔离 Anaconda 路径，避免 PySide6 DLL 冲突）
setlocal
set "PATH=%PATH:;C:\ProgramData\anaconda3=%;;C:\ProgramData\anaconda3\Scripts=;"
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境，请先运行 install.bat
    pause
    exit /b 1
)
".venv\Scripts\python.exe" main.py
endlocal