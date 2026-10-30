@echo off
setlocal
chcp 65001 >nul
title REBORN CFG - Multi-Protocol Subscription Checker 2026
cd /d "%~dp0"

IF EXIST "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "source\hysteria2_subscription_checker.py" %*
) ELSE (
    python "source\hysteria2_subscription_checker.py" %*
)

echo.
echo ----------------------------------------------------------------
echo Нажмите любую клавишу для выхода...
pause >nul
