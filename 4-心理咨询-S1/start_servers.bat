@echo off
chcp 65001 >nul
REM 心理咨询案例系统 - 服务启动脚本 (Windows)

echo ======================================================================
echo   心理咨询案例系统 - 启动所有服务
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/8] 启动接访记录服务器 (端口 8768)...
start /B python src\intake_record_server.py
timeout /t 1 /nobreak >nul

echo [2/8] 启动Word解析服务器 (端口 8765)...
start /B python src\word_upload_server.py
timeout /t 1 /nobreak >nul

echo [3/8] 启动案例API服务器 (端口 5001)...
start /B python src\case_api.py
timeout /t 1 /nobreak >nul

echo [4/8] 启动流派配置服务器 (端口 8003)...
start /B python src\config_server.py
timeout /t 1 /nobreak >nul

echo [5/8] 启动录音管理服务器 (端口 8004)...
start /B python src\audio_server.py
timeout /t 1 /nobreak >nul

echo [6/8] 启动逐字稿管理服务器 (端口 8005)...
start /B python src\transcript_server.py
timeout /t 1 /nobreak >nul

echo [7/8] 启动督导资料管理服务器 (端口 8006)...
start /B python src\supervision_server.py
timeout /t 1 /nobreak >nul

echo [8/8] 启动单案例处理服务器 (端口 8007)...
start /B python src\case_processor_server.py
timeout /t 1 /nobreak >nul

echo.
echo ======================================================================
echo   所有服务已启动
echo ======================================================================
echo.
echo √ 接访记录服务：    http://localhost:8768  (核心服务)
echo √ Word解析服务：    http://localhost:8765
echo √ 案例API服务：     http://localhost:5001
echo √ 流派配置服务：    http://localhost:8003
echo √ 录音管理服务：    http://localhost:8004
echo √ 逐字稿管理服务：  http://localhost:8005
echo √ 督导资料管理服务：http://localhost:8006
echo √ 单案例处理服务：  http://localhost:8007
echo.
echo √ 项目首页：        %cd%\output\index.html
echo √ 接访记录：        %cd%\output\接访记录\intake-record-new.html
echo √ 来访者库：        %cd%\output\来访者库\index.html
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
