# Harness 自动化使用说明

## 📁 已安装文件

```
.harness/
├── codex-submit.sh           # 提交任务脚本
├── codex-poll.sh             # 手动查询脚本
├── codex-poll-auto.sh        # 自动轮询脚本（配合 /loop）
├── test-codex-timeout.sh     # 超时测试脚本
└── codex-jobs/               # 任务存储目录
    └── latest.json           # 最新任务ID
```

## 🚀 快速开始

### 1. 准备请求文件

```bash
cat > /tmp/my_question.json << 'EOF'
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "你是代码审查专家"
    },
    {
      "role": "user",
      "content": "请审查以下代码的安全性：\n\n[粘贴代码]"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 2000
}
EOF
```

### 2. 提交任务

```bash
cd "D:\AI-项目\4-心理咨询-S1"
bash .harness/codex-submit.sh /tmp/my_question.json
```

**输出示例**：
```
🚀 正在提交任务到 Codex...
✅ Codex任务已提交: 20260629123456-789
⏳ 预计60-120秒完成
```

### 3. 自动等待结果（推荐）

告诉 Claude：
```
/loop 1m 运行 bash .harness/codex-poll-auto.sh；
如果退出码=10则报告完成并CronDelete当前任务，
如果退出码=20则报告超时/失败并CronDelete当前任务，
如果退出码=0则继续等待
```

### 4. 手动查询（可选）

```bash
# 查询最新任务
bash .harness/codex-poll-auto.sh

# 查询指定任务
bash .harness/codex-poll.sh 20260629123456-789
```

## 📊 退出码说明

| 退出码 | 含义 | 说明 |
|--------|------|------|
| 0 | 继续等待 | 任务仍在进行中 |
| 10 | ✅ 完成 | 任务成功完成，可以停止循环 |
| 20 | ❌ 失败/超时 | 任务失败或超过5分钟，停止循环 |

## 🎯 实战示例

### 示例1：代码安全审查

```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "审查以下登录功能的安全性：\n\n```javascript\nfunction login(username, password) {\n  const query = `SELECT * FROM users WHERE username='${username}' AND password='${password}'`;\n  return db.query(query);\n}\n```\n\n请检查：\n1. SQL注入风险\n2. 密码存储方式\n3. 其他安全问题"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 2000
}
```

### 示例2：架构决策建议

```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "技术选型建议：\n\n场景：心理咨询系统的音频存储\n需求：\n- 录音文件大小：5-50MB\n- 访问频率：低\n- 保存时长：5年\n- 成本敏感\n\n请对比以下方案：\n1. 本地文件系统\n2. 阿里云OSS\n3. 腾讯云COS\n\n给出推荐方案和理由。"
    }
  ],
  "temperature": 0.5,
  "max_tokens": 3000
}
```

### 示例3：Bug根因分析

```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "Bug分析：\n\n**现象**：用户上传Word文档后刷新页面，内容丢失\n\n**错误日志**：\n```\nTypeError: Cannot read property 'buffer' of undefined\nat saveDocument (utils.js:42)\n```\n\n**相关代码**：\n```javascript\nasync function saveDocument(file) {\n  const buffer = file.buffer;\n  const base64 = buffer.toString('base64');\n  await db.save({content: base64});\n}\n```\n\n请分析根本原因和修复方案。"
    }
  ],
  "temperature": 0.3,
  "max_tokens": 2000
}
```

## ⚙️ 高级配置

### 自定义超时时间

```bash
# 设置10分钟超时
export CODEX_TIMEOUT_SECONDS=600
bash .harness/codex-poll-auto.sh
```

### 查看历史任务

```bash
ls -lh .harness/codex-jobs/
```

### 清理旧任务（保留最近10个）

```bash
cd .harness/codex-jobs
ls -t | tail -n +11 | xargs rm -rf
```

## 🔧 测试

### 测试超时机制

```bash
bash .harness/test-codex-timeout.sh
```

### 测试基本流程

```bash
# 1. 创建测试请求
cat > /tmp/test.json << 'EOF'
{
  "model": "gpt-4",
  "messages": [{"role": "user", "content": "1+1=?"}],
  "temperature": 0.3,
  "max_tokens": 50
}
EOF

# 2. 提交
bash .harness/codex-submit.sh /tmp/test.json

# 3. 等待60秒
sleep 60

# 4. 查询
bash .harness/codex-poll-auto.sh
```

## ⚠️ 注意事项

1. **代码长度限制**：单次请求中的代码不要超过500行
2. **JSON格式**：确保JSON格式正确，使用双引号
3. **API密钥**：确保 CatKingAI API 可访问
4. **网络连接**：需要稳定的网络连接

## 🐛 故障排查

### 问题1：提交失败

**检查**：
```bash
cat .harness/codex-jobs/*/response.json
```

**常见原因**：
- JSON格式错误
- API密钥无效
- 网络连接问题

### 问题2：一直显示"进行中"

**检查任务状态**：
```bash
cat .harness/codex-jobs/latest.json
cat .harness/codex-jobs/*/status.json
```

**可能原因**：
- Codex API响应慢（正常，继续等待）
- 超时设置过短（增大 CODEX_TIMEOUT_SECONDS）

### 问题3：结果为空

**检查响应**：
```bash
cat .harness/codex-jobs/*/response.json | python3 -m json.tool
```

## 📞 获取帮助

如有问题，请查看：
- 完整文档：`.claude/Harness自动化-微信分享版-v2.0.md`
- 任务目录：`.harness/codex-jobs/`

---

**版本**: v1.0  
**创建时间**: 2026-06-29  
**项目**: 心理咨询-S1
