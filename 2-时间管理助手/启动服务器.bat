@echo off
chcp 65001 >nul
title TimePlanner Server Start
set "ROOT=%~dp0"

where node >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install: https://nodejs.org/
    pause
    exit /b 1
)

echo ================================================
echo  TimePlanner - Starting Services
echo ================================================
echo.

:: Clean old processes
echo [1/2] Cleaning old processes...
taskkill /F /IM node.exe >nul 2>&1
powershell -WindowStyle Hidden -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*daemon.ps1*' } | Stop-Process -Force" 2>nul
timeout /t 2 /nobreak >nul
echo        Done.

:: Start silent daemon
echo [2/2] Starting silent daemon (no windows)...
start "TimePlanner-Daemon" /MIN powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%ROOT%daemon.ps1"
timeout /t 5 /nobreak >nul

:: Verify
echo.
powershell -Command "try{$r=Invoke-WebRequest 'http://127.0.0.1:6371/' -UseBasicParsing -TimeoutSec 3;Write-Host 'Static 6371: OK'}catch{Write-Host 'Static 6371: WAITING...'}"
powershell -Command "try{$r=Invoke-WebRequest 'http://127.0.0.1:6372/' -UseBasicParsing -TimeoutSec 3;Write-Host 'Sync  6372: OK'}catch{Write-Host 'Sync  6372: WAITING...'}"

echo.
echo ================================================
echo  Services running. Open http://127.0.0.1:6371/
echo  Daemon auto-restarts on crash. No windows.
echo  Close this window safely.
echo ================================================
pause
