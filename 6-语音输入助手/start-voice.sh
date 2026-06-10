#!/bin/bash
# VoiceType 启动脚本
# 启动本地服务 + 打开语音输入窗口

SERVER_JS="D:/AI-项目/6-语音输入助手/voice-server.js"
PORT=19876

# 检查服务是否已在运行
if curl -s http://127.0.0.1:$PORT/health > /dev/null 2>&1; then
  echo "Server already running"
else
  echo "Starting VoiceType server..."
  node "$SERVER_JS" &
  sleep 2
fi

# 打开 Chrome 弹窗
powershell.exe -NoProfile -Command "Start-Process 'chrome' -ArgumentList '--app=http://127.0.0.1:$PORT/popup','--window-size=380,260'" 2>/dev/null

echo "VoiceType ready! Speak and text will auto-paste."
