@echo off
cd /d "%~dp0server"
start "灵感收集器" /MIN node src/index.js
echo 灵感收集器已启动（最小化窗口）
echo HTTP:  http://localhost:3000
echo HTTPS: https://localhost:3443
echo.
echo 关闭此窗口不影响服务器运行。
echo 需要停止时双击 stop-server.bat
timeout /t 3 >nul
