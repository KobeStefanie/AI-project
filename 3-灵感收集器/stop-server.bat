@echo off
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3443" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
echo 灵感收集器已停止
timeout /t 2 >nul
