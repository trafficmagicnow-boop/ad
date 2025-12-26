@echo off
title Adw Integration Launcher V3
color 0B

echo ===================================================
echo   ADW INTEGRATION - PUBLIC DEPLOYMENT (V3)
echo ===================================================

echo.
echo [1/3] Checking Python...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        color 0C
        echo ERROR: Python not found!
        pause
        exit
    )
    set PY_CMD=python
) else (
    set PY_CMD=py
)
echo Using command: %PY_CMD%

echo.
echo [2/3] Starting Server...
:: Kill if already running on 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
start "Adw Server Process" cmd /c "%PY_CMD% server.py"

echo Waiting 5 seconds for server to start...
timeout /t 5 >nul

echo.
echo [3/3] Creating Public Link (via Pinggy)...
echo ---------------------------------------------------
echo   ВНИМАНИЕ: Сейчас внизу появится ссылка https://...
echo   Скопируй её и отправь баеру.
echo   НЕ ЗАКРЫВАЙ ЭТО ОКНО!
echo ---------------------------------------------------
echo.

:: Using pinggy.io as it's more stable for these cases
ssh -p 443 -o StrictHostKeyChecking=no -o "UserKnownHostsFile=/dev/null" -R 0:localhost:8000 a.pinggy.io

echo.
echo Tunnel closed. Restarting in 5 seconds...
timeout /t 5
goto :3
