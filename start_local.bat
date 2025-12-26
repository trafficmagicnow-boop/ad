@echo off
title Adw Integration LOCAL
color 0A

echo ===================================================
echo   ADW INTEGRATION - LOCAL SERVER
echo ===================================================

echo.
echo [1/2] Killing old processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1

echo.
echo [2/2] Starting Server...
py --version >nul 2>&1
if %errorlevel% neq 0 (
    python server.py
) else (
    py server.py
)

pause
