---
name: ios-pwa-limitations
description: iOS 18.2 (iPhone 13 Pro Max) 对自签 HTTPS + 私网 PWA 的限制全景，以及时间管理助手的应对方案
metadata: 
  node_type: memory
  type: project
  originSessionId: dcee5a42-f6a1-43bc-86eb-35d67fd3c43b
---

# iOS PWA 限制与应对方案

> 以下内容基于 iPhone 13 Pro Max / iOS 18.2 + 自签 CA 证书 + 局域网私网 IP 的实测结论。

## 限制清单

### 1. iOS 17+ 拒绝自签 CA + 私网 origin 装 standalone PWA【关键】

- **现象**：`apple-mobile-web-app-capable` + `manifest.json (display: standalone)` 的组合下，"添加到主屏幕"预览页短暂显示彩色图标，最终 commit 时降级为**灰色图标 + 普通书签**（长按显示"删除书签"而非"删除 App"）。点击书签 → Safari 打开（顶部带地址栏），非独立全屏模式。
- **根因**：iOS 17+ 安全策略——自签 CA + 私网 origin（IP 或 mDNS `.local`）即使 CA 已被「完全信任」，Safari 仍拒绝 standalone PWA。
- **影响**：无法获得真正独立全屏 PWA 体验（无地址栏、独立任务卡片、彩色主屏图标）。
- **应对**：接受书签形态。功能上 95% 等同 PWA（离线缓存 / 数据同步 / 离线编辑队列均正常）。

### 2. iOS Safari 对 HTTP 网站的 localStorage 不持久化

- **现象**：用 `http://` 地址访问，填入数据后关闭标签页再打开，localStorage 被清空。
- **根因**：iOS Safari 将 HTTP 网站的 localStorage 视为临时数据，关闭标签页即清除。
- **应对**：iPhone **必须用 HTTPS** 访问（`https://192.168.31.153:6443/`）。

### 3. 主屏幕书签的默认浏览器问题

- **现象**：iPhone 设置里「默认浏览器 App」如果不是 Safari（例如设为 Edge），主屏幕书签会用那个浏览器打开。不同浏览器之间 localStorage 完全隔离，导致 Safari 填的数据书签里看不到。
- **应对**：设置 → Safari → 默认浏览器 App → **选 Safari**。

### 4. iOS 不同 origin 之间 localStorage 隔离

- **现象**：用 `http://192.168.31.153:6371/` 和 `https://192.168.31.153:6443/` 是不同 origin，数据不互通。
- **应对**：iPhone 统一用 HTTPS 地址。首次从 HTTP 迁移时，需要导出/导入 JSON 数据。

## 当前 iPhone 端正确配置（v2.13.2）

| 项目 | 值 |
|---|---|
| 地址 | `https://192.168.31.153:6443/时间管理助手.html` |
| 同步端口 | HTTPS 6444（跟随页面协议，无 Mixed Content） |
| 默认浏览器 | Safari（设置 → Safari → 默认浏览器 App） |
| 主屏入口 | Safari 打开 → 分享 → 添加到主屏幕 |
| CA 证书 | 已装 `Time Planner Personal CA`（v2.11.0 部署） |
| 离线缓存 | Service Worker v89 cache-first + SWR，`Cache-Control: public, max-age=0` |
| 数据迁移 | HTTP → HTTPS：导出 JSON → 导入 JSON |

> **v2.13.2 重要变更**：iOS 不再强制 HTTP 同步。HTTPS 页面走 HTTPS 同步（6444），CA 已信任，无 Mixed Content 阻塞。

## 曾尝试但无效的方案

- ❌ 去掉 `manifest.json` 引用 → iOS 仍自动探测根目录 manifest
- ❌ 改 `display` 为 `browser` → 无效
- ❌ 去掉 `apple-mobile-web-app-capable` → 无效
- ❌ 完全禁用 Service Worker（`?nosw`）→ 无效
- ❌ 用 mDNS `.local` 域名 → 存储问题同样存在

## 相关文档

- 需求文档 §22.1「iOS 17+ 自签 CA + 私网 origin 装不了 standalone PWA」
- 需求文档 §21.17「本地 HTTPS 与 CA-leaf 自签证书架构」

## 关联记忆

- [[time-planner]] — 项目主页
- [[project-rules]] — 项目目录规范
