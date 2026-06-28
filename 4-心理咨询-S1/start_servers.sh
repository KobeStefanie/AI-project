#!/bin/bash
# 心理咨询案例系统 - 服务启动脚本

echo "======================================================================"
echo "  心理咨询案例系统 - 启动所有服务"
echo "======================================================================"
echo ""

cd "$(dirname "$0")"

echo "[1/4] 启动流派配置服务器 (端口 8003)..."
python src/config_server.py &
CONFIG_PID=$!
sleep 1

echo "[2/4] 启动录音管理服务器 (端口 8004)..."
python src/audio_server.py &
AUDIO_PID=$!
sleep 1

echo "[3/4] 启动逐字稿管理服务器 (端口 8005)..."
python src/transcript_server.py &
TRANSCRIPT_PID=$!
sleep 1

echo "[4/4] 启动督导资料管理服务器 (端口 8006)..."
python src/supervision_server.py &
SUPERVISION_PID=$!
sleep 1

echo ""
echo "======================================================================"
echo "  所有服务已启动"
echo "======================================================================"
echo ""
echo "✓ 流派配置服务：    http://localhost:8003  (PID: $CONFIG_PID)"
echo "✓ 录音管理服务：    http://localhost:8004  (PID: $AUDIO_PID)"
echo "✓ 逐字稿管理服务：  http://localhost:8005  (PID: $TRANSCRIPT_PID)"
echo "✓ 督导资料管理服务：http://localhost:8006  (PID: $SUPERVISION_PID)"
echo ""
echo "✓ 项目首页：        file://$(pwd)/output/index.html"
echo "✓ 案例库索引：      file://$(pwd)/output/案例库/index.html"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 保存PID到文件
echo "$CONFIG_PID $AUDIO_PID $TRANSCRIPT_PID $SUPERVISION_PID" > .server_pids

# 捕获Ctrl+C信号
trap "echo ''; echo '正在停止所有服务...'; kill $CONFIG_PID $AUDIO_PID $TRANSCRIPT_PID $SUPERVISION_PID 2>/dev/null; rm -f .server_pids; echo '所有服务已停止'; exit" SIGINT SIGTERM

# 等待所有后台进程
wait
