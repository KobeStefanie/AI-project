#!/bin/bash
# Codex 任务提交脚本
# 用法: bash codex-submit.sh <request.json>

set -e

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 错误: 请提供请求文件路径"
    echo "用法: bash codex-submit.sh <request.json>"
    exit 1
fi

REQUEST_FILE="$1"

if [ ! -f "$REQUEST_FILE" ]; then
    echo "❌ 错误: 文件不存在: $REQUEST_FILE"
    exit 1
fi

# 生成任务ID
JOB_ID="$(date +%Y%m%d%H%M%S)-$$"
JOB_DIR=".harness/codex-jobs/$JOB_ID"

# 创建任务目录
mkdir -p "$JOB_DIR"

# 复制请求文件
cp "$REQUEST_FILE" "$JOB_DIR/request.json"

# 提交到 Codex API
echo "🚀 正在提交任务到 Codex..."

# 调用 Codex API（需要配置 API 端点）
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d @"$REQUEST_FILE" \
    "https://api.catking.ai/v1/chat/completions" \
    2>&1 || echo '{"error": "API调用失败"}')

# 保存响应
echo "$RESPONSE" > "$JOB_DIR/response.json"

# 检查是否成功
if echo "$RESPONSE" | grep -q '"error"'; then
    echo "❌ 提交失败"
    echo "$RESPONSE"
    exit 1
fi

# 保存任务信息
cat > "$JOB_DIR/status.json" << EOF
{
  "job_id": "$JOB_ID",
  "status": "submitted",
  "submit_time": "$(date -Iseconds)",
  "request_file": "$REQUEST_FILE"
}
EOF

# 更新 latest 链接
echo "$JOB_ID" > ".harness/codex-jobs/latest.json"

echo "✅ Codex任务已提交: $JOB_ID"
echo "⏳ 预计60-120秒完成"
echo ""
echo "📁 任务目录: $JOB_DIR"

exit 0
