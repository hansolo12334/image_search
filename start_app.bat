@echo off
chcp 65001

echo 正在激活 Conda 环境...
call "D:\anaconda\Library\bin\conda.bat" activate fishenv

if %ERRORLEVEL% NEQ 0 (
    echo 激活环境失败
    pause
    exit /b %ERRORLEVEL%
)
echo 正在启动 Uvicorn...
uvicorn app:app

