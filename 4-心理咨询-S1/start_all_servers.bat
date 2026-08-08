@echo off
chcp 65001 >nul
echo ============================================================
echo   心理咨询-S1 全部服务器启动
echo ============================================================
echo.

cd /d "%~dp0"

:: 确保日志目录存在
if not exist "logs" mkdir logs

:: ========== HTTP 服务器 (Python http.server) ==========
echo [1/13] 配置服务器 (端口 8003)...
start /B python src\config_server.py > logs\config_server.log 2>&1

echo [2/13] 音频服务器 (端口 8004)...
start /B python src\audio_server.py > logs\audio_server.log 2>&1

echo [3/13] 转录服务器 (端口 8005)...
start /B python src\transcript_server.py > logs\transcript_server.log 2>&1

echo [4/13] 督导服务器 (端口 8006)...
start /B python src\supervision_server.py > logs\supervision_server.log 2>&1

echo [5/13] 案例处理服务器 (端口 8007)...
start /B python src\case_processor_server.py > logs\case_processor_server.log 2>&1

:: ========== Flask 服务器 ==========
echo [6/13] 案例数据 API (端口 5001)...
start /B python src\case_api.py > logs\case_api.log 2>&1

echo [7/13] Word上传服务器 (端口 8765)...
start /B python src\word_upload_server.py > logs\word_upload_server.log 2>&1

echo [8/13] 流派分析保存服务器 (端口 8766)...
start /B python src\approach_analysis_server.py > logs\approach_analysis_server.log 2>&1

echo [9/13] 录音管理服务器 (端口 8767)...
start /B python src\recording_server.py > logs\recording_server.log 2>&1

echo [10/13] 接访记录服务器 (端口 8768)...
start /B python src\intake_record_server.py > logs\intake_record_server.log 2>&1

echo [11/13] 逐字稿上传服务器 (端口 8769)...
start /B python src\transcript_upload_server.py > logs\transcript_upload_server.log 2>&1

echo [12/13] 来访者列表服务器 (端口 8770)...
start /B python src\visitor_list_server.py > logs\visitor_list_server.log 2>&1

echo [13/13] AI分析API服务器 (端口 8771)...
start /B python src\ai_analysis_api.py > logs\ai_analysis_api.log 2>&1

echo.
echo 等待服务器启动 (5秒)...
timeout /t 5 /nobreak >nul

echo.
echo ============================================================
echo   启动完成！服务列表：
echo ============================================================
echo.
echo   HTTP 服务器:
echo     [8003] 配置管理        http://localhost:8003
echo     [8004] 音频管理        http://localhost:8004
echo     [8005] 转录服务        http://localhost:8005
echo     [8006] 督导管理        http://localhost:8006
echo     [8007] 案例处理        http://localhost:8007
echo.
echo   Flask API:
echo     [5001] 案例数据API     http://localhost:5001
echo     [8765] Word上传        http://localhost:8765
echo     [8766] 流派分析保存    http://localhost:8766
echo     [8767] 录音管理        http://localhost:8767
echo     [8768] 接访记录        http://localhost:8768
echo     [8769] 逐字稿上传      http://localhost:8769
echo     [8770] 来访者列表      http://localhost:8770
echo     [8771] AI分析API       http://localhost:8771/health
echo.
echo   前端页面: output\index.html
echo   日志目录: %CD%\logs\
echo.
echo   运行 check_services.bat 查看服务状态
echo.
pause
