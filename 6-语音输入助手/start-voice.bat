@echo off
:: VoiceType - 全局语音输入启动器
:: 启动后按 Ctrl+Shift+M 开始/停止录音，文字自动出现在光标位置

echo ========================================
echo   VoiceType - 全局语音输入
echo ========================================
echo.

cd /d D:\AI-项目\6-语音输入助手

:: 1. 停止旧进程
echo [1/3] Stopping old processes...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im powershell.exe /fi "WINDOWTITLE eq VoiceType*" >nul 2>&1
timeout /t 1 /nobreak >nul

:: 2. 启动 Node.js 服务
echo [2/3] Starting voice server...
start "VoiceType-Server" /MIN node voice-server.js
timeout /t 2 /nobreak >nul

:: 验证服务
curl -s http://127.0.0.1:19876/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Server failed to start!
    pause
    exit /b 1
)
echo   Server: OK

:: 3. 打开 Chrome 弹窗（只用于语音识别，不需要操作它）
echo [3/3] Opening popup...
start chrome --app=http://127.0.0.1:19876/popup --window-size=350,200 --window-position=1200,50
echo   Popup: OK

echo.
echo ========================================
echo   Ready!
echo.
echo   使用方法：
echo   1. 首次使用：点弹窗里的「授权麦克风」按钮
echo   2. 在任意输入框光标处，按 Ctrl+Shift+M 开始录音
echo   3. 说话，说完停顿 2 秒自动粘贴
echo   4. 再次按 Ctrl+Shift+M 可手动停止
echo.
echo   弹窗可以最小化，不需要关
echo ========================================

:: 4. 启动热键监听
echo.
echo Starting hotkey listener (Ctrl+Shift+M)...
echo Keep this window open, minimized is OK.
echo.
start "VoiceType-Hotkey" /MIN powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File hotkey-listener.ps1

pause
