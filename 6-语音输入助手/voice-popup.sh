#!/bin/bash
# 语音输入悬浮窗 - 快速启动脚本
# 用法: voice  或  ./voice-popup.sh

HTML_FILE="D:\\AI-项目\\6-语音输入助手\\voice-popup.html"

# 尝试找到 Chrome/Edge
CHROME=""
for browser in \
  "/c/Program Files/Google/Chrome/Application/chrome.exe" \
  "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
  "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
  "/c/Program Files/Microsoft/Edge/Application/msedge.exe" \
  "chrome" "edge"; do
  if command -v "$browser" &>/dev/null || [ -f "$browser" ]; then
    CHROME="$browser"
    break
  fi
done

if [ -z "$CHROME" ]; then
  echo "请安装 Chrome 或 Edge 浏览器"
  exit 1
fi

# 以 app 模式打开（无地址栏、最小化窗口）
start "" "$CHROME" --app="file:///${HTML_FILE}" --window-size=400,320 --window-position=100,100
