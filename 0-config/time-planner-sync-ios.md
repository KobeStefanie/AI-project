---
name: time-planner-sync-ios
description: 时间管理助手同步机制要点与 iOS 特殊限制
metadata: 
  node_type: memory
  type: project
  project: D:\AI-项目\2-时间管理助手
  originSessionId: f330e745-8da5-493c-8c2b-624c620477ba
---

## 同步架构要点

### 服务端
- 静态服务器 `src/server.js`：HTTP 6371 + HTTPS 6443
- 同步服务器 `sync-server.js`：HTTP 6372 + HTTPS 6444
- 自签 CA-leaf 双证书（`certs/` 目录），iPhone 需装 CA 描述文件

### 同步流程
- 保存即推送（debounce 1.5s）→ POST `/weeks/:year/:week/changes`
- 启动自动拉取（2.5s 延迟）→ GET `/weeks/:year/:week`
- WebSocket `/events` 实时推送变更广播
- 心跳 30s ping `/info` + 自动拉取当前周（v2.13.1 新增）
- 合并策略：last-write-wins，按 `updatedAt` 逐粒度比较

### 设备配对
- POST `/pair/start` 生成 6 位配对码（5 分钟有效）
- QR 码内含 `{hostname, ip, port, httpsPort, code}`
- `/pair/confirm` 验证后返回设备令牌 `tok-xxx`
- 后续请求带 `X-Device-Token` 头鉴权
- 127.0.0.1/localhost 免鉴权，无设备时免鉴权

**Why:** 完整理解同步链路，排查问题时能快速定位是客户端、网络、还是服务端。

**How to apply:** 修改同步相关代码时参考此架构，新增端点需考虑鉴权白名单。

## iOS 特殊限制（v2.13.2 更新）

### 同步协议：跟随页面协议（不再强制 HTTP）

- **v2.13.1（已废弃）**：`getEffectiveProtocol()` 检测 iOS UA 强制返回 `'http:'`，试图避开 WKWebView 自签证书跨端口限制
- **v2.13.2 修正**：上述做法导致 HTTPS 页面 → HTTP fetch 被 Safari 当作 **Mixed Content 阻止**
  - iOS Safari 的 Mixed Content 拦截**优先于** WKWebView 自签证书限制
  - 正确做法：iOS 跟随页面协议。HTTPS 页面走 HTTPS 同步（6444），CA 已信任即可
  - [app-core.js](D:\AI-项目\2-时间管理助手\src\app-core.js) `getEffectiveProtocol()` 直接返回 `window.location.protocol`

**Why:** 不能为了解决跨端口证书问题而引入 Mixed Content 阻塞，后者更根本。sync-server 已经支持 HTTPS 6444（同 CA 证书），iOS HTTPS 同步完全可用。

**How to apply:** 修改同步相关代码时，**不要**为 iOS 做协议特判。页面用什么协议，同步就用什么协议。

### Cache-Control: no-store 与 Cache API 互斥（关键教训）

- **`Cache-Control: no-store` 会阻止 Service Worker Cache API 存储响应**
- iOS Safari 的 Cache API 实现**严格遵守**规范：遇到 `no-store` 的 `cache.put()` 直接拒绝
- 后果：SW install 阶段缓存为空 → 离线无内容可返回 → Safari 显示"无法连接互联网"
- **解决方案**：
  - 服务器用 `Cache-Control: public, max-age=0`（允许 Cache API，禁止浏览器 HTTP 缓存）
  - SW 用 `sanitizeForCache()` 剥离残留的限制性缓存头（`no-store`/`no-cache`/`private`）
  - SW install 用 `fetch` + `cache.put(sanitizedResponse)` 替代 `cache.add()`（更精细控制）

**Why:** `no-store` 看似"让 SW 管理缓存"，实则同时禁用了 SW 的缓存能力。

**How to apply:** 静态服务器**永远不要**设置 `Cache-Control: no-store`。让浏览器 HTTP 缓存和 SW Cache API 各司其职。

### Service Worker 缓存陷阱
- SW 采用 cache-first + stale-while-revalidate 策略
- `Ctrl+F5` 不能绕过 SW 缓存
- 修改 `CACHE_NAME` 时必须同步修改 `app.js` 中的 `EXPECTED_CACHE_NAME`
- 版本不匹配 → 3 秒自检强制 reload → 无限重载循环
- 开发调试时用 `sw-cleanup.html` 清理，或浏览器 DevTools 手动 Unregister

**Why:** 两次遇到 SW 缓存导致新代码不生效的问题，容易误判为功能 bug。

**How to apply:** 每次修改 SW 相关代码后，同时 bump `CACHE_NAME` 和 `EXPECTED_CACHE_NAME`。用户反馈"没效果"时，先让他们清 SW 缓存。

### PWA localStorage 隔离
- iOS PWA 安装后，不同协议/端口视为不同源
- HTTP `http://IP:6371` ↔ HTTPS `https://IP:6443` 的 localStorage **不共享**
- 设备令牌、同步配置按源存储，切换协议会导致"丢失"配对
- **v2.13.2 现状**：iPhone 统一用 HTTPS 6443 访问（兼顾 localStorage 持久化 + 同步可用）

**Why:** 用户从 HTTP 切换到 HTTPS 时，token 会"消失"，需要重新配对。

**How to apply:** iPhone 用户统一用 `https://192.168.31.153:6443/时间管理助手.html` 访问。PWA 添加主屏也用此地址。

### 页面频繁刷新
- iOS Safari 对 `window.location.reload()` 和频繁 DOM 重绘敏感
- `renderAll()` 重建整个页面内容，可能触发 PWA 重载
- 心跳拉取必须检查数据是否**真正有变化**再触发 UI 刷新
- `_applyServerWeekToLocal` 用 `serverWeekUpdatedAt` 快速判断跳过

**Why:** 心跳拉取总是触发 renderAll 导致页面频繁刷新，用户无法正常操作。

**How to apply:** 任何自动拉取机制必须先做"有无变化"判断，再决定是否刷新 UI。

## 数据流向调试口诀

排查同步问题时的检查顺序：
1. 服务是否运行？（`netstat -ano | grep 6372`）
2. SW 缓存是否清除？（`sw-cleanup.html`）
3. 同步是否启用？（面板勾选 + 保存）
4. 协议是否匹配？（页面 HTTPS → 同步 HTTPS；页面 HTTP → 同步 HTTP）
5. 服务端数据是否存在？（`curl -k https://127.0.0.1:6444/weeks`）
6. merge 是否真正写入了？（检查 `sync-data/` 文件内容）
7. 离线是否可用？（在线→刷新→切飞行模式→打开页面）

## 离线缓存调试口诀

排查离线打不开时的检查顺序：
1. `curl -k -I https://IP:6443/` → 确认 `Cache-Control` **不是** `no-store`
2. Safari Web Inspector → Cache Storage → 确认 `time-planner-vXX` 有内容（至少 5+ 条目）
3. 在线访问 + 下拉刷新 1 次 → 等 3 秒 → 切飞行模式测试
4. 若仍失败：`sw-cleanup.html` 清缓存 → 重新在线访问 → 重复步骤 3
