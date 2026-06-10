@echo off
:: 创建计划任务：启动时 + 登录时 + 解锁时自动重启时间管理助手服务
:: 需要管理员权限运行此脚本

set TASK_NAME=TimePlanner-AutoStart
set SCRIPT_PATH=D:\AI-项目\2-时间管理助手\autostart-silent.bat

:: 先删除旧任务
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: 创建任务：启动时触发
schtasks /create /tn "%TASK_NAME%" /tr "\"%SCRIPT_PATH%\"" /sc onstart /ru "%USERNAME%" /rl highest /delay 0000:30 /f

if errorlevel 1 (
    echo [FAIL] 无法创建计划任务（需要管理员权限）
    echo 请右键此文件 → 以管理员身份运行
    pause
    exit /b 1
)

:: 添加：登录时触发
schtasks /change /tn "%TASK_NAME%" /sc onlogon

:: 添加解锁触发器（通过 XML 方式）
echo.
echo [OK] 计划任务 %TASK_NAME% 已创建
echo.
echo 触发条件：
echo   1. 系统启动（延迟30秒）
echo   2. 用户登录
echo.
echo 如需休眠唤醒自动重启，请手动在任务计划程序中添加：
echo   触发器 → 新建 → 开始任务：在工作站解锁时
echo.
echo 或双击运行 setup-task-extra.ps1（需要管理员PowerShell）
pause
