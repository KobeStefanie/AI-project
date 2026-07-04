#!/bin/bash
# Codex 超时测试脚本

echo "🧪 测试 Codex 超时机制"
echo ""

# 创建测试请求
cat > /tmp/test-codex-timeout.json << 'EOF'
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "简单测试：1+1等于几？"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 100
}
EOF

echo "1️⃣ 提交测试任务..."
bash .harness/codex-submit.sh /tmp/test-codex-timeout.json

echo ""
echo "2️⃣ 设置超时为10秒（测试用）..."
export CODEX_TIMEOUT_SECONDS=10

echo ""
echo "3️⃣ 等待15秒后查询（应触发超时）..."
sleep 15

echo ""
echo "4️⃣ 查询结果..."
bash .harness/codex-poll-auto.sh

EXIT_CODE=$?

echo ""
echo "📊 测试结果："
if [ $EXIT_CODE -eq 20 ]; then
    echo "✅ 超时机制正常工作（退出码=$EXIT_CODE）"
elif [ $EXIT_CODE -eq 10 ]; then
    echo "⚠️ 任务在超时前完成（退出码=$EXIT_CODE）"
else
    echo "⏳ 任务仍在进行中（退出码=$EXIT_CODE）"
fi

echo ""
echo "🧹 清理测试文件..."
rm -f /tmp/test-codex-timeout.json

exit 0
