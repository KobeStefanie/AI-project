@echo off
chcp 65001 >nul
title 时间管理助手 · 静态服务器（6371）

where node >nul 2>nul
if errorlevel 1 (
    echo [错误] 没找到 node 命令。请先安装 Node.js: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

REM 在新窗口启动同步服务（端口 6372），日志独立，互不干扰
start "时间管理助手 · 同步服务（6372）" cmd /k "cd /d "%~dp0" && node sync-server.js"

REM 当前窗口启动静态服务（端口 6371）
cd /d "%~dp0src"

echo ================================================
echo  时间管理助手 · 静态服务器（端口 6371）
echo  目录: %CD%
echo  另一个窗口已启动同步服务（端口 6372）
echo ================================================
echo.

node server.js

echo.
echo ================================================
echo  静态服务器已停止。同步服务窗口仍在运行，需手动关闭。
echo  按任意键关闭本窗口...
echo ================================================
pause >nul
