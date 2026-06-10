' VoiceType - VBS 启动器（完全无命令行窗口闪烁）
CreateObject("WScript.Shell").Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""D:\AI-项目\6-语音输入助手\VoiceType.ps1""", 0, False
