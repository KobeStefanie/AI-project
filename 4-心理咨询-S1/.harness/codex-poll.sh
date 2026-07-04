#!/bin/bash
# Codex 任务手动查询脚本（查询指定任务）
# 用法: bash codex-poll.sh [job_id]

set -e

# 获取任务ID
if [ -z "$1" ]; then
    # 未指定，使用最新任务
    if [ ! -f ".harness/codex-jobs/latest.json" ]; then
        echo "❌ 没有待查询的任务"
        exit 1
    fi
    JOB_ID=$(cat ".harness/codex-jobs/latest.json")
else
    JOB_ID="$1"
fi

JOB_DIR=".harness/codex-jobs/$JOB_ID"

if [ ! -d "$JOB_DIR" ]; then
    echo "❌ 任务不存在: $JOB_ID"
    exit 1
fi

echo "📋 任务ID: $JOB_ID"
echo ""

# 显示状态
if [ -f "$JOB_DIR/status.json" ]; then
    echo "📊 状态信息："
    cat "$JOB_DIR/status.json" | python3 -m json.tool 2>/dev/null || cat "$JOB_DIR/status.json"
    echo ""
fi

# 显示结果
if [ -f "$JOB_DIR/result.txt" ]; then
    echo "✅ 任务已完成"
    echo ""
    echo "📄 结果内容："
    echo "----------------------------------------"
    cat "$JOB_DIR/result.txt"
    echo "----------------------------------------"
elif [ -f "$JOB_DIR/response.json" ]; then
    echo "⏳ 任务进行中或等待处理"
    echo ""
    echo "📡 响应信息："
    cat "$JOB_DIR/response.json" | python3 -m json.tool 2>/dev/null || cat "$JOB_DIR/response.json"
else
    echo "❌ 未找到任务信息"
fi

exit 0
