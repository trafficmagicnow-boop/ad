@echo off
title Adw Integration Public Launcher V4
color 0B

echo ===================================================
echo   ADW INTEGRATION - PUBLIC DEPLOYMENT (V4)
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
echo Using: %PY_CMD%

echo.
echo [2/3] Starting Server...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
start "Adw Server" cmd /c "%PY_CMD% server.py"

echo Waiting 5 seconds...
timeout /t 5 >nul

echo.
echo [3/3] Creating Public URL...
echo ---------------------------------------------------
echo   ВАЖНО: Сейчас появится ссылка https://...
echo   Скопируй её и отправь баеру!
echo   НЕ ЗАКРЫВАЙ это окно!
echo ---------------------------------------------------
echo.

:: localhost.run - no password required, most reliable
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:8000 nokey@localhost.run

echo.
echo Connection closed. Restarting in 5 sec...
timeout /t 5
goto :3
