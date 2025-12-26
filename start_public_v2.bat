@echo off
title Adw Integration Launcher
color 0B

echo ===================================================
echo   ADW INTEGRATION - PUBLIC DEPLOYMENT
echo ===================================================

echo.
echo [1/3] Checking Python (py)...
py --version
if %errorlevel% neq 0 (
    echo [!] 'py' not found, trying 'python'...
    python --version
    if %errorlevel% neq 0 (
        color 0C
        echo ERROR: Python not found! Please install Python from python.org.
        pause
        exit
    )
    set PY_CMD=python
) else (
    set PY_CMD=py
)

echo.
echo [2/3] Starting Server...
:: Kill if already running
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
start "Adw Server" cmd /c "%PY_CMD% server.py"

echo Waiting for server to warm up...
timeout /t 3 >nul

echo.
echo [3/3] Creating Public Link...
echo ---------------------------------------------------
echo   COPY THE URL BELOW (e.g. https://...lhr.life)
echo   IF ASKED "yes/no", TYPE yes AND PRESS ENTER.
echo ---------------------------------------------------
echo.

:tunnel
ssh -o StrictHostKeyChecking=no -R 80:localhost:8000 nokey@localhost.run
echo.
echo Tunnel disconnected. Retrying in 5 seconds...
timeout /t 5
goto tunnel
