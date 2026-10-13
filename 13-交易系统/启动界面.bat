@echo off
chcp 65001 >nul
cd /d "%~dp0scripts"
echo 正在启动，浏览器会自动打开 http://127.0.0.1:5077
echo 关闭这个窗口 = 关闭界面
start "" http://127.0.0.1:5077
python app.py
pause
