@echo off
chcp 65001 >nul
title REBORN CFG - Multi-Protocol Subscription Checker 2026
cd /d "%~dp0"

echo ================================================================
echo    ⚡ REBORN CFG - Multi-Protocol Subscription Checker 2026
echo    Hysteria2 ^| VLESS Reality ^| VMESS ^| Shadowsocks ^| Trojan
echo ================================================================
echo.

IF EXIST "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "source\hysteria2_subscription_checker.py" %*
) ELSE (
    python "source\hysteria2_subscription_checker.py" %*
)

echo.
echo ================================================================
echo Работа чекера завершена. Результаты сохранены в папке results\
echo Нажмите любую клавишу для закрытия...
pause >nul
