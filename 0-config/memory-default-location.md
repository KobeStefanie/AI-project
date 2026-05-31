---
name: memory-default-location
description: 所有项目 memory 的默认储存位置为 D:\AI-项目\0-config，不得擅自变更
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f304e012-20dd-40ad-87c0-1694a411ea4d
---

# Memory 默认存储位置

## 规则

所有项目的 memory 文件，默认储存位置均为 `D:\AI-项目\0-config\`。该目录是 memory 的权威源（source of truth）。

**Why:** 用户要求统一管理，避免记忆散落在各处，防止系统重装或用户目录清空导致记忆丢失。

**How to apply:**
- 新建或修改 memory 时，必须在 `D:\AI-项目\0-config\` 下写入/更新对应文件
- 同步更新 `~/.claude/projects/C--Users-Administrator/memory/` 下的副本（Claude 运行时读取需要）
- `D:\AI-项目\0-config\` 为权威源，不得擅自变更为其他位置
- 该目录下的 MEMORY.md 索引也应保持同步

## 关联记忆

- [[skills-storage-rules]] — 技能存储规范（原备份规则已被此记忆覆盖）
- [[project-rules]] — 项目目录规范
