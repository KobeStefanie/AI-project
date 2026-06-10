@echo off
:: 语音输入悬浮窗 - Windows 快捷启动
:: 双击此文件即可打开

set HTML=D:\AI-项目\6-语音输入助手\voice-popup.html

:: 尝试 Chrome
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app="file:///%HTML%" --window-size=400,360
    exit /b 0
)
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --app="file:///%HTML%" --window-size=400,360
    exit /b 0
)

:: 尝试 Edge
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app="file:///%HTML%" --window-size=400,360
    exit /b 0
)
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app="file:///%HTML%" --window-size=400,360
    exit /b 0
)

echo 未找到 Chrome 或 Edge 浏览器，请手动用浏览器打开 voice-popup.html
pause
