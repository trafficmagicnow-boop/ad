@echo off
title Adw Integration Server + Public Access
color 0A

echo ===================================================
echo   ADW INTEGRATION - INSTANT DEPLOYMENT
echo ===================================================
echo.
echo [1/2] Starting Local Server...
start /B python server.py > server_log.txt 2>&1

echo Server running. waiting for initialization...
timeout /t 3 >nul

echo.
echo [2/2] Creating Public Link (via localhost.run)...
echo.
echo ---------------------------------------------------
echo   IMPORTANT: Look for the URL below (e.g. https://xyz.lhr.life)
echo   Give that URL to your buyer.
echo   Don't close this window!
echo ---------------------------------------------------
echo.

:: This command attempts to tunnel port 8000 to the public internet
ssh -R 80:localhost:8000 nokey@localhost.run

echo.
echo Tunnel closed. Exiting...
taskkill /F /IM python.exe >nul
pause
