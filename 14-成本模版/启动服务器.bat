@echo off
chcp 65001 > nul
echo.
echo ============================================
echo   胚布报价计算器 - 本地服务器
echo ============================================
echo.
echo 正在启动服务器...
echo.

cd /d "%~dp0"

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)

:found
set IP=%IP: =%

echo 服务器已启动！
echo.
echo ============================================
echo 📱 手机访问地址（手机和电脑要在同一WiFi）：
echo.
echo    http://%IP%:8000/胚布报价计算器.html
echo.
echo ============================================
echo.
echo 💡 使用方法：
echo    1. 确保手机和电脑连接同一个WiFi
echo    2. 在手机浏览器输入上面的地址
echo    3. 按 Ctrl+C 停止服务器
echo.
echo ============================================
echo.

python -m http.server 8000
