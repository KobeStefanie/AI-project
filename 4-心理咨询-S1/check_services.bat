@echo off
chcp 65001 >nul
echo ============================================================
echo   心理咨询-S1 服务状态检查
echo   %date% %time%
echo ============================================================
echo.
echo   端口     服务名称              状态
echo   ------   -------------------   ----------

set PORTS=5001 8003 8004 8005 8006 8007 8765 8766 8767 8768 8769 8770

:: 端口与服务名称映射
set DESC_5001=案例数据API
set DESC_8003=配置管理
set DESC_8004=音频管理
set DESC_8005=转录服务
set DESC_8006=督导管理
set DESC_8007=案例处理
set DESC_8765=Word上传
set DESC_8766=流派分析保存
set DESC_8767=录音管理
set DESC_8768=接访记录
set DESC_8769=逐字稿上传
set DESC_8770=来访者列表

set RUNNING=0
set TOTAL=0

for %%p in (%PORTS%) do (
    set /a TOTAL+=1
    set FOUND=0
    for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":%%p " ^| findstr "LISTENING"') do (
        set FOUND=1
        set /a RUNNING+=1
    )
    call set name=%%DESC_%%p%%
    if !FOUND!==1 (
        echo    [%%p]    !name!                  [RUNNING]
    ) else (
        echo    [%%p]    !name!                  [STOPPED]
    )
)

echo.
echo ============================================================
echo   总计: !RUNNING!/!TOTAL! 服务运行中
echo ============================================================
echo.
echo   前端入口: output\index.html
echo   流派配置: output\案例库\config-approaches.html
echo.
pause
