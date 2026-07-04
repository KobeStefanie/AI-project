---
name: export-conversation-skill
description: 对话历史导出技能——将 Claude Code 会话导出为 Markdown 或 Word 文档，清晰展示问答内容
metadata:
  type: project
---

# 对话历史导出技能

## 位置

- **运行时副本**: `C:\Users\Administrator\.claude\skills\export-conversation\`
- **权威源**: `D:\AI-项目\0-config\skills\export-conversation\`
- **存储目录**: `D:\AI-项目\A-skills\export-conversation\`

## 功能

将当前 Claude Code 会话的完整对话历史导出为文档：

1. **Markdown 格式** (默认)
   - 轻量级纯文本
   - 包含 emoji 角色标识 👤用户 / 🤖Claude
   - 自动添加时间戳

2. **Word 格式**
   - 专业排版，带彩色背景和边框
   - 用户消息：蓝色标题 + 浅蓝背景
   - Claude 消息：绿色标题 + 浅绿背景
   - 自动过滤工具调用记录

## 使用方法

```bash
# 导出为 Markdown
python C:/Users/Administrator/.claude/skills/export-conversation/scripts/export_conversation.py

# 导出为 Word 文档
python C:/Users/Administrator/.claude/skills/export-conversation/scripts/export_conversation.py --format docx

# 自定义文件名
python C:/Users/Administrator/.claude/skills/export-conversation/scripts/export_conversation.py -o "对话记录.md"
```

## 技术实现

- Python 脚本解析 `.claude/projects/` 下的 JSONL 会话文件
- 自动检测最近修改的会话文件
- Word 导出使用 Node.js docx 库（需要 `npm install -g docx`）
- 已修复 Windows 控制台编码问题

**Why:** 用户需要整理和保存与 Claude 的对话历史，便于回顾、分享和存档。

**How to apply:** 
- 在对话中说"导出对话"、"保存对话历史"、"整理对话"时使用此技能
- Word 格式适合正式分享和打印
- Markdown 格式适合技术文档和版本控制

## 关联记忆

- [[skills-storage-rules]] — 技能存储规范
- [[memory-default-location]] — Memory 默认存储位置
