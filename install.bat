@echo off
rem 首次安装依赖并创建虚拟环境（使用非 Anaconda 的 Python 3.14）
setlocal
if not exist ".venv\Scripts\python.exe" (
    "C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe" -m venv .venv
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
echo 环境已就绪。运行 run.bat 启动应用。
endlocal