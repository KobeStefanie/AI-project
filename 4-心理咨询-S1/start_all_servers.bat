@echo off
chcp 65001 >nul
echo ============================================================
echo 启动心理咨询-S1所有服务器
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/7] 启动配置服务器 (端口8005)...
start /B python src\config_server.py > logs\config_server.log 2>&1

echo [2/7] 启动Word上传服务器 (端口8765)...
start /B python src\word_upload_server.py > logs\word_upload_server.log 2>&1

echo [3/7] 启动流派分析保存服务器 (端口8766)...
start /B python src\approach_analysis_server.py > logs\approach_analysis_server.log 2>&1

echo [4/7] 启动音频服务器 (端口8004)...
start /B python src\audio_server.py > logs\audio_server.log 2>&1

echo [5/7] 启动督导服务器 (端口8006)...
start /B python src\supervision_server.py > logs\supervision_server.log 2>&1

echo [6/7] 启动转录服务器 (端口未指定)...
start /B python src\transcript_server.py > logs\transcript_server.log 2>&1

echo [7/7] 启动案例处理服务器 (端口未指定)...
start /B python src\case_processor_server.py > logs\case_processor_server.log 2>&1

echo.
echo 等待服务器启动...
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo 所有服务器已启动！
echo ============================================================
echo.
echo 服务器列表：
echo   - 配置服务器:          http://localhost:8005
echo   - Word上传服务器:      http://localhost:8765
echo   - 流派分析保存服务器:  http://localhost:8766
echo   - 音频服务器:          http://localhost:8004
echo   - 督导服务器:          http://localhost:8006
echo   - 转录服务器:          运行中
echo   - 案例处理服务器:      运行中
echo.
echo 日志目录: %CD%\logs\
echo.
pause
