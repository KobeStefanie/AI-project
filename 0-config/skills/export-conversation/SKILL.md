---
name: export-conversation
description: "导出当前会话的完整对话历史到文档。可以导出为 Markdown 或 Word 文档格式。触发条件：用户提到'导出对话'、'保存对话'、'对话历史'、'整理对话'、'会话记录'等。支持自定义输出格式和文件名。"
---

# 对话历史导出工具

## 功能说明

将当前 Claude Code 会话的完整对话历史导出为文档，支持以下格式：
- Markdown (.md) - 默认格式，轻量级纯文本
- Word (.docx) - 适合分享和打印的专业文档

## 使用方法

### 基本用法

```bash
# 导出为 Markdown（默认）
python scripts/export_conversation.py

# 导出为 Word 文档
python scripts/export_conversation.py --format docx

# 指定输出文件名
python scripts/export_conversation.py --output "我的对话-2024-01-01.md"
```

### 参数说明

- `--format` / `-f`: 输出格式，可选 `md` 或 `docx`（默认：md）
- `--output` / `-o`: 输出文件路径（默认：conversation-导出.md）
- `--session-id` / `-s`: 指定会话 ID（默认：自动检测当前会话）

## 实现原理

1. 读取 `.claude/projects/` 下的会话 JSONL 文件
2. 解析每条消息的角色、内容、时间戳
3. 格式化为可读的文档结构
4. 保存为指定格式

## 输出格式示例

### Markdown 格式

```markdown
# 对话历史导出

**会话ID**: abc-123-def
**导出时间**: 2024-01-01 12:00:00

---

## 用户 (12:00:01)

你好，帮我写一段代码

## Claude (12:00:05)

当然，我来帮你写...
```

### Word 格式

使用专业排版，包含：
- 封面页（会话信息）
- 目录
- 格式化的对话内容（带时间戳、角色标识）
- 代码块高亮

## 依赖

- Python 3.x
- `docx` 库（导出 Word 格式时需要）: `npm install -g docx`

## 注意事项

- 导出的文档包含完整对话历史，可能较大
- 工具调用结果默认会被简化显示
- 图片等多媒体内容会转为文本描述
