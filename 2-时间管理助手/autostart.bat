@echo off
chcp 65001 >nul
cd /d "D:\AI-项目\2-时间管理助手"

:: Kill existing and start fresh silent daemon
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 /nobreak >nul
start "TimePlanner-Daemon" /MIN powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "daemon.ps1"
