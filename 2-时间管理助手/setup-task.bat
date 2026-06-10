@echo off
schtasks /create /tn "TimePlanner-AutoStart" /tr "\"D:\AI-项目\2-时间管理助手\autostart-silent.bat\"" /sc onstart /ru Administrator /rl highest /f
schtasks /create /tn "TimePlanner-AutoLogon" /tr "\"D:\AI-项目\2-时间管理助手\autostart-silent.bat\"" /sc onlogon /ru Administrator /rl highest /f
echo Done.
pause
