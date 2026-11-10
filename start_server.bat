@echo off
echo ==========================================
echo   Speed Lightning Payout Server Setup
echo ==========================================
cd /d %~dp0
echo Installing dependencies (npm install)...
call npm install
echo.
echo Starting server...
node server.js
pause
