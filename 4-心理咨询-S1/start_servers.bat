@echo off
chcp 65001 >nul
REM 心理咨询案例系统 - 服务启动脚本 (Windows)

echo ======================================================================
echo   心理咨询案例系统 - 启动所有服务
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/5] 启动流派配置服务器 (端口 8003)...
start /B python src\config_server.py
timeout /t 1 /nobreak >nul

echo [2/5] 启动录音管理服务器 (端口 8004)...
start /B python src\audio_server.py
timeout /t 1 /nobreak >nul

echo [3/5] 启动逐字稿管理服务器 (端口 8005)...
start /B python src\transcript_server.py
timeout /t 1 /nobreak >nul

echo [4/5] 启动督导资料管理服务器 (端口 8006)...
start /B python src\supervision_server.py
timeout /t 1 /nobreak >nul

echo [5/5] 启动单案例处理服务器 (端口 8007)...
start /B python src\case_processor_server.py
timeout /t 1 /nobreak >nul

echo.
echo ======================================================================
echo   所有服务已启动
echo ======================================================================
echo.
echo √ 流派配置服务：    http://localhost:8003
echo √ 录音管理服务：    http://localhost:8004
echo √ 逐字稿管理服务：  http://localhost:8005
echo √ 督导资料管理服务：http://localhost:8006
echo √ 单案例处理服务：  http://localhost:8007
echo.
echo √ 项目首页：        %cd%\output\index.html
echo √ 单案例处理：      %cd%\output\case-processor.html
echo √ 案例库索引：      %cd%\output\案例库\index.html
echo.
echo 按任意键打开项目首页...
pause >nul

start "" "%cd%\output\index.html"

echo.
echo 服务正在运行中...
echo 关闭此窗口将停止所有服务
echo.
pause
