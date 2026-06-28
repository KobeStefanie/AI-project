---
name: psych-s1-homepage-integration
description: 心理咨询-S1项目所有功能必须集成到主页，未集成视为未完工
metadata:
  type: project
---

# 心理咨询-S1 主页集成要求

## 核心原则
**设计的所有功能必须集成到主页（index.html）里面。一旦没有集成到主页，视为没有完工或错误。**

## 项目路径
- **主页**: `D:\AI-项目\4-心理咨询-S1\output\index.html`
- **功能页面**: `D:\AI-项目\4-心理咨询-S1\output\接访记录\*.html`

## 工作流程
1. 用户总是从 `http://localhost:8888/index.html` 开始
2. 点击主页的功能卡片进入相应页面
3. 不要让用户直接访问功能页面的URL

## 测试流程
- ✅ 从主页点击进入功能页面
- ❌ 直接给用户功能页面的URL

**Why**: 主页是系统的统一入口，未集成到主页的功能用户无法发现和使用，等同于不存在。

**How to apply**: 每次新增功能页面后，立即在主页添加对应的链接卡片；测试时从主页开始操作，不要直接访问子页面URL。

相关记忆：[[psych-counseling-s1]]
