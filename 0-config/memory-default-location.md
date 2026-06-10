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

1. 所有项目的 memory 文件，默认储存位置均为 `D:\AI-项目\0-config\`。该目录是 memory 的权威源（source of truth）。
2. **每次全局 `.claude` memory 有更新（新增/修改/删除），必须同步更新 `D:\AI-项目\0-config\` 中对应文件，保持两端内容完全一致。**

**Why:** 用户要求统一管理，避免记忆散落在各处，防止系统重装或用户目录清空导致记忆丢失。

**How to apply:**
- 修改 memory 后立即执行同步：`cp` 覆盖到 `D:\AI-项目\0-config\`
- 同步后校验 MD5 一致，确保文件数量和内容完全匹配
- `D:\AI-项目\0-config\` 为权威源，不得擅自变更为其他位置
- 该目录下的 MEMORY.md 索引也必须保持同步

## 关联记忆

- [[skills-storage-rules]] — 技能存储规范（原备份规则已被此记忆覆盖）
- [[project-rules]] — 项目目录规范
