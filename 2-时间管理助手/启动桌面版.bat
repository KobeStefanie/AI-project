@echo off
chcp 65001 >nul
setlocal
title TimePlanner Launcher
set "ROOT=%~dp0"

:: Kill any existing daemon before starting a fresh one
powershell -WindowStyle Hidden -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*daemon*' -or $_.CommandLine -like '*daemon.ps1*' } | Stop-Process -Force" 2>nul
timeout /t 1 /nobreak >nul

:: Start the silent daemon (manages both servers, no windows ever)
start "TimePlanner-Daemon" /MIN powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%ROOT%daemon.ps1"

:: Wait for ports
echo Waiting for servers...
set TRIES=0
:LOOP
timeout /t 1 /nobreak >nul
set /a TRIES+=1
powershell -Command "try{$r=Invoke-WebRequest 'http://127.0.0.1:6371/' -UseBasicParsing -TimeoutSec 2;exit 0}catch{exit 1}" 2>nul
if %errorlevel% equ 0 goto READY
if %TRIES% geq 12 goto TIMEOUT
goto LOOP

:READY
echo Servers ready, opening browser...
start "" "http://127.0.0.1:6371/"
echo Launcher done.
timeout /t 2 /nobreak >nul
exit /b 0

:TIMEOUT
echo Timeout - opening browser anyway...
start "" "http://127.0.0.1:6371/"
exit /b 0
