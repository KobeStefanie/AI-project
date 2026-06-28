@echo off
echo ========================================
echo 心理咨询案例管理系统
echo ========================================
echo.

echo [1/2] 启动后端API服务器 (端口 5001)...
start "案例管理API" cmd /k "cd /d D:\AI-项目\4-心理咨询-S1 && python src\case_api.py"

timeout /t 2 /nobreak >nul

echo [2/2] 启动前端服务器 (端口 8888)...
start "前端服务" cmd /k "cd /d D:\AI-项目\4-心理咨询-S1\output\接访记录 && python -m http.server 8888"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo 服务启动完成！
echo ========================================
echo.
echo 案例列表: http://localhost:8888/case-list.html
echo 接访记录: http://localhost:8888/intake-record-new.html
echo 后端API: http://localhost:5001/api
echo.
echo 按任意键打开案例列表...
pause >nul

start http://localhost:8888/case-list.html
