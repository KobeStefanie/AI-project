@echo off
chcp 65001 >nul
setlocal
set "ROOT=%~dp0"
set "LOG=%ROOT%autostart.log"

echo [%date% %time%] ========== AutoStart ========== >> "%LOG%"

:: Kill old node and daemon processes
taskkill /F /IM node.exe >nul 2>&1
powershell -WindowStyle Hidden -Command "Get-Process powershell -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*daemon.ps1*' } | Stop-Process -Force" 2>nul
timeout /t 2 /nobreak >nul

:: Start silent daemon (no windows, manages both servers + monitors health)
start "TimePlanner-Daemon" /MIN powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "%ROOT%daemon.ps1"

timeout /t 5 /nobreak >nul

:: Verify
powershell -Command "try{$r=Invoke-WebRequest 'http://127.0.0.1:6371/' -UseBasicParsing -TimeoutSec 3;exit 0}catch{exit 1}" 2>nul
if errorlevel 1 (
    echo [%date% %time%] ERROR: Static server failed to start >> "%LOG%"
) else (
    echo [%date% %time%] OK: Servers running via daemon >> "%LOG%"
)
echo [%date% %time%] ========== Done ========== >> "%LOG%"
