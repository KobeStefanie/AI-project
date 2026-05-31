---
name: skills-storage-rules
description: 技能安装后的存储位置、文件命名规范、配置规则——每次安装新技能时必须遵守
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 09401a78-3a4f-4c9c-ac1d-bac3c6df653d
---

# 技能存储规范

## 规则

所有通过 `npx skills add` 安装的技能，其存储/缓存/日志文件必须统一存放在 `D:\AI-项目\A-skills\` 目录下。

**Why:** 用户要求所有技能的数据集中管理，避免散落在各处，便于备份和维护。

**How to apply:** 每次安装新技能后，必须执行以下操作：

1. 在 `D:\AI-项目\A-skills\` 下创建与技能同名的文件夹
2. 在文件夹内创建 `1-{技能名}储存文件` 作为存储标记文件
3. 更新 `D:\AI-项目\A-skills\0-config规则` 文件，将新技能添加到清单中
4. 后续该技能产生的缓存文件按序号递增命名（`2-`、`3-`、`4-` 等）

## 文件命名格式

```
{序号}-{技能名}储存文件    ← 核心持久化数据
{序号}-{技能名}缓存数据    ← 运行时缓存
{序号}-{技能名}临时文件    ← 一次性临时数据
{序号}-{技能名}运行日志    ← 日志记录
```

## 配置文件

- 根配置：`D:\AI-项目\A-skills\0-config规则`
- 该文件包含完整技能清单、分类、存储路径映射表和维护记录
- 新增或删除技能时必须同步更新

## 记忆文件存储

`D:\AI-项目\0-config\` 是所有 memory 文件的**权威源**（source of truth），非备份。`~/.claude/projects/C--Users-Administrator/memory/` 为运行所需副本。

**Why:** 统一管理、防止系统重装或用户目录清空导致记忆丢失。

**How to apply:** 每次新增或修改记忆文件后，在 `D:\AI-项目\0-config\` 写入，再同步到 `~/.claude/...` 运行时副本。参见 [[memory-default-location]]。

## 关联记忆

- [[project-rules]] — 项目目录规范
- [[user-profile]] — 用户档案
