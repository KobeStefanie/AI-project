---
name: user-profile
description: 用户的角色、技术偏好、项目组织规范和协作风格
metadata: 
  node_type: memory
  type: user
  originSessionId: 93086043-6a24-4e4a-91db-27fd5f406318
---

# 用户档案

## 角色
- 独立开发者，偏好离线优先/单HTML/PWA方案
- 能不带后端就不带后端，数据存 LocalStorage
- 中国大陆用户，依赖安装优先用国内镜像

## 项目组织
- 所有项目统一存放 `D:\AI-项目\数字-名称\`
- 命名格式: `N-中文/英文名`（如 `2-时间管理助手`）
- 项目结构: 根目录放 README.md + 需求文档.md + 配置文件，源码进 `src/`
- 跨项目通用文档放 `D:\AI-项目\0-config\`

## 技术栈偏好
- 离线优先 / 单 HTML / LocalStorage / PWA
- 跨平台共用 core（`app-core.js`），不同终端只写 UI
- 不用 `<dialog>` / `prompt()` / `confirm()` / `alert()`，自建 div modal
- 移动端输入框 ≥16px，触控目标 ≥44px
- 版本管理: 语义化版本号 `v主.次.补丁`，有 SW 时同步升缓存版本号

## 当前主要项目
- [[time-planner]] — `D:\AI-项目\2-时间管理助手\`，当前版本 v2.8.0
