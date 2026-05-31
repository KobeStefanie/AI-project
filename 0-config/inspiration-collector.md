---
name: inspiration-collector
description: 灵感收集器（碎碎念）项目状态——跨端灵感捕获与整理工具，当前在 PLAN 阶段
metadata: 
  node_type: memory
  type: project
  originSessionId: 09401a78-3a4f-4c9c-ac1d-bac3c6df653d
---

# 灵感收集器

- **路径**: `D:\AI-项目\3-灵感收集器\`
- **状态**: PLANNING — 执行前需经用户同意
- **版本**: v1.0.0 / 计划 v6
- **技术**: PWA + Express + Claude AI

## 项目定位

想法捕手，不是备忘录。iPhone 快速捕获（语音/文字/图片/视频），Windows 日历回顾 + 主题整理。AI 自动分类/关键词/心情/主题聚合。

## 核心概念

- **灵感碎片**——单条捕获，独立保存（时间戳/心情/上下文）
- **主题**——非破坏性上层容器，碎片保持独立，AI 自动推荐 + 手动管理
- **状态流转**: raw → expanded → realized / archived / abandoned
- **心情**: 7 档（兴奋/平和/低落/困惑/焦虑/受启发/坚定）

## 当前进度

- 需求文档 v6（完整）
- 计划文档 v6（完整）
- 静态预览 4 张（iPhone、Windows日历、列表、时间线）
- 未开始编码

## 下次会话待讨论

- 数据库选型（Turso / SQLite / Supabase）
- 后端部署位置
- 音频/视频存储方案
- 需求文档中 §6.0 待确认事项

## 关联记忆

- [[skills-storage-rules]] — 技能存储规范
- [[auto-open-preview]] — 静态预览自动打开规则
- [[project-rules]] — 项目目录规范
