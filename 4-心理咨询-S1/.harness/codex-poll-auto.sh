#!/bin/bash
# Codex 任务自动轮询脚本
# 退出码: 0=继续等待, 10=完成, 20=超时/失败

set -e

# 配置
TIMEOUT_SECONDS=${CODEX_TIMEOUT_SECONDS:-300}  # 默认5分钟超时

# 检查是否有任务
if [ ! -f ".harness/codex-jobs/latest.json" ]; then
    echo "❌ 没有待查询的任务"
    exit 20
fi

JOB_ID=$(cat ".harness/codex-jobs/latest.json")
JOB_DIR=".harness/codex-jobs/$JOB_ID"

if [ ! -d "$JOB_DIR" ]; then
    echo "❌ 任务目录不存在: $JOB_DIR"
    exit 20
fi

# 读取任务信息
STATUS_FILE="$JOB_DIR/status.json"
RESPONSE_FILE="$JOB_DIR/response.json"

if [ ! -f "$STATUS_FILE" ]; then
    echo "❌ 状态文件不存在"
    exit 20
fi

# 检查响应文件
if [ ! -f "$RESPONSE_FILE" ]; then
    echo "❌ 响应文件不存在"
    exit 20
fi

# 解析响应
RESPONSE=$(cat "$RESPONSE_FILE")

# 检查是否有错误
if echo "$RESPONSE" | grep -q '"error"'; then
    echo "❌ Codex任务失败"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 20
fi

# 检查是否完成（有 choices 字段说明已返回结果）
if echo "$RESPONSE" | grep -q '"choices"'; then
    # 提取结果
    RESULT=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'choices' in data and len(data['choices']) > 0:
        print(data['choices'][0]['message']['content'])
    else:
        print('无有效结果')
except:
    print('解析失败')
" 2>/dev/null)

    # 保存结果
    echo "$RESULT" > "$JOB_DIR/result.txt"

    # 更新状态
    cat > "$STATUS_FILE" << EOF
{
  "job_id": "$JOB_ID",
  "status": "done",
  "complete_time": "$(date -Iseconds)"
}
EOF

    echo "✅ Codex任务完成"
    echo ""
    echo "📄 结果内容："
    echo "----------------------------------------"
    echo "$RESULT"
    echo "----------------------------------------"
    echo ""
    echo "💾 结果已保存到: $JOB_DIR/result.txt"

    exit 10
fi

# 检查超时
SUBMIT_TIME=$(grep -oP '"submit_time":\s*"\K[^"]+' "$STATUS_FILE" 2>/dev/null || echo "")
if [ -n "$SUBMIT_TIME" ]; then
    CURRENT_TIME=$(date +%s)
    SUBMIT_TIMESTAMP=$(date -d "$SUBMIT_TIME" +%s 2>/dev/null || echo "$CURRENT_TIME")
    ELAPSED=$((CURRENT_TIME - SUBMIT_TIMESTAMP))

    if [ $ELAPSED -gt $TIMEOUT_SECONDS ]; then
        echo "❌ 超时：Codex任务运行超过 $TIMEOUT_SECONDS 秒"

        # 更新状态
        cat > "$STATUS_FILE" << EOF
{
  "job_id": "$JOB_ID",
  "status": "timeout",
  "timeout_time": "$(date -Iseconds)"
}
EOF
        exit 20
    fi

    echo "⏳ Codex进行中... (已运行 $ELAPSED 秒 / 超时限制 $TIMEOUT_SECONDS 秒)"
else
    echo "⏳ Codex进行中..."
fi

exit 0
