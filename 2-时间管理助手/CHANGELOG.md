# CHANGELOG

## v2.13.1 — 2026-05-29（月历视图 + 三件事状态）

新增桌面月历视图和前三件事三态状态标记，同步、导出、导入全链路支持。

### 一、核心数据层（app-core.js）

- **三态状态存储**：新增 `getKeyItemStatus(year, week)` / `saveKeyItemStatus(year, week, status)`
  - LS key: `tm_YYYY_wN_keyitemStatus`，按周存储
  - 键格式同 keyitems: `日期|第一件事` 等
  - 状态值: `todo`（未完成，默认）/ `done`（已完成）/ `ongoing`（持续）
- **导出/导入**：`EXPORT_KEY_RE` 增加 `keyitemStatus` 支持
- **同步层**：push 上传 keyitemStatus、pull 合并 keyitemStatus、meta 跟踪
- **新增常量**：`KEY_ITEM_STATUS_ROWS` / `KEY_ITEM_STATUS_VALUES`

### 二、同步服务（sync-server.js）

- `emptyWeek()` 增加 `keyitemStatus: {}`
- `mergeChanges()` 对 keyitemStatus 做 LWW 合并
- POST /changes 返回增加 `keyitemStatusCount`

### 三、UI 层（app.js + styles.css）

- **桌面月历表**：`renderMonthCalendar()` — 6周×7天网格，自然月导航（上月/下月/本月）
  - 每天显示：日期号 + 三件事（含状态框）+ 小确幸 + 关键词
  - 非本月日期置灰，今天高亮
  - 点击文本进入关键事项编辑，点击状态框切换状态
- **周表/移动端状态框**：前三件事单元格渲染 `ki-status-box`
  - `renderTbody` 前三行 + `renderM_KeyItems` 均显示状态框
  - 点击状态框循环状态（todo→done→ongoing），不触发编辑弹窗
- **工具栏导航**：prev/next/today 根据 desktopView 切换周/月状态
- **CSS**：状态框 `.ki-status-box` 三态样式 + 月历网格 `.month-cell` 样式

### 四、文件改动

- `src/app-core.js`：+70 行（状态存储 + 同步/导出/导入链路）
- `sync-server.js`：+20 行（keyitemStatus 持久化 + LWW 合并）
- `src/app.js`：+160 行（月历渲染 + 状态交互 + 导航适配）
- `src/styles.css`：+50 行（状态框 + 月历样式）
- `src/service-worker.js`：CACHE_NAME v54 → v55
- `需求文档.md`：§1/§4.1/§4.2/§12.4.A/§14.5.1/§20.10/§21.15 更新
- `README.md`：核心功能 + 版本表更新

---

## v2.13.0 — 2026-05-29（阶段 3.4：扫码绑定 + 设备令牌）

实现需求文档 §20.7 阶段 3.4：扫码绑定设备、X-Device-Token 鉴权、设备管理。

### 一、服务端（sync-server.js）

- **设备管理**：`devices.json` 持久化，`loadDevices()`/`saveDevices()`/`findDeviceByToken()`
- **临时配对码**：6 位数字，5 分钟有效，内存存储（`pairCodes` Map）
- **端点**：
  - `POST /pair/start` — 生成配对码，返回 `{pairCode, hostname, lanIPs, port}`
  - `POST /pair/confirm` — 验证配对码 → 创建设备记录 → 返回 `{deviceId, token}`
  - `POST /pair/register-desktop` — 桌面自注册（仅无设备时可用）
  - `GET /devices` — 列出已绑定设备（名称、平台、最后同步）
  - `DELETE /devices/:id` — 解绑设备
- **X-Device-Token 鉴权**：除 `/pair/*`、`GET /`、`GET /info` 外均需令牌；无设备时过渡期豁免
- **lastSyncAt 自动更新**：30s 节流写盘
- **4 台设备上限**

### 二、客户端（app-core.js）

- **令牌管理**：`getDeviceToken()`/`saveDeviceToken()`
- **自动注册**：`init()` 中若无令牌则 1s 后调用 `registerDesktop()`
- **请求头**：所有 fetch 自动附加 `X-Device-Token`
- **配对 API**：`pairStart()`/`pairConfirm()`/`registerDesktop()`/`getDevices()`/`deleteDevice()`

### 三、UI（app.js + HTML）

- 同步面板新增「📱 生成绑定二维码」按钮
- QR 码展示区 + 配对码明文 + 5 分钟倒计时提示
- 已绑定设备列表（名称/平台/最后同步/解绑按钮）
- 使用 `qrcode-generator@1.4.4` CDN 库（SVG 输出）

### 四、文件改动

- `sync-server.js`：+100 行设备/配对/鉴权；4 台上限；`/pair/register-desktop`
- `src/app-core.js`：+40 行令牌/配对 API；fetch 自动加令牌；init 自注册
- `src/app.js`：+70 行配对 UI + 设备列表 + `deleteDevice` 全局函数
- `src/时间管理助手.html`：QR 库 CDN + 配对面板 HTML
- `src/service-worker.js`：CACHE_NAME v50 → v51

---

## v2.12.0 — 2026-05-28（阶段 3.3：WebSocket 实时推送）

实现需求文档 §20.7 阶段 3.3：服务端变更广播 → 客户端实时收到 → 自动拉取。

### 一、服务端（sync-server.js）

- **自实现 RFC6455 WebSocket 握手**：纯 Node `crypto` 模块计算 `Sec-WebSocket-Accept`，零 npm 依赖
- **`WSS /events` 端点**：客户端通过 HTTPS 6444（或 HTTP 6372）升级连接
- **帧编解码**：文本帧 + Ping/Pong 保活（30s 间隔）
- **变更广播**：POST `/weeks/:y/:w/changes` 成功后 `wsBroadcast({type:"week-changed",...})`
- **连接管理**：客户端集合 + 断开自动清理 + `upgrade` 事件监听

### 二、客户端（app-core.js syncClient）

- **`_wsConnect()`**：按协议自适应（HTTPS→wss、HTTP→ws），URL 优先 `.local`（mDNS）
- **自动重连**：指数退避 1s→2s→4s→...→30s 上限
- **消息处理**：收到 `week-changed` → 自动 `pullWeek`；若为当前查看的周 → 派发 `sync-remote-change` CustomEvent
- **生命周期**：`saveSyncConfig` 启用同步时连接、关闭时断开；`init()` 中自动连接
- **`visibilitychange` 补充**：页面回到前台时自动 flush 离线队列（§22.2 修复）

### 三、UI 层（app.js）

- 监听 `sync-remote-change` → 自动 `renderAll()` 刷新当前页

### 四、文件改动

- `sync-server.js`：新增 WebSocket 握手/帧编解码/客户端管理/广播 (~120 行)；POST /changes 成功后广播；启动日志加 WSS /events
- `src/app-core.js`：`_state` 加 `ws`/`wsReconnectTimer`/`wsReconnectDelay`；新增 `_wsConnect`/`_wsDisconnect`/`_wsScheduleReconnect`/`_wsBuildUrl`；`saveSyncConfig`/`init` 集成
- `src/app.js`：`setupSyncUI` 加 `sync-remote-change` 监听
- `src/service-worker.js`：CACHE_NAME v48 → v49
- `CHANGELOG.md`：本文

---

## v2.11.2 — 2026-05-28（Bug 修复：心跳覆盖 disconnected + 启动主动探测）

修复 v2.11.1 心跳检测的两个遗留缺口，彻底解决重启电脑后同步无法自动恢复的问题。

### 问题

v2.11.1 引入的心跳检测仅在 `connected` / `error` 状态执行。但 `init()` 将初始状态设为 `disconnected`，心跳跳过该状态，导致：

1. **服务器晚于页面启动**：页面先打开（status=disconnected），心跳不执行 → 服务器就绪后无法自动发现
2. **autoPull 未改变状态**：若 autoPull 因 URL 为空等原因未执行，状态永久卡在 disconnected
3. **首次心跳等 30s**：`setInterval` 首次回调在 30s 后才触发，重启后恢复太慢

### 修复

- **心跳覆盖 `disconnected` 状态**：`_healthCheckPing()` 仅在 `disabled` / `connecting` 时跳过；`disconnected` / `connected` / `error` 均执行探测
- **首次心跳 1s 后立即执行**：新增 `setTimeout` 在 1s 后跑首次 ping，不等 30s。后续每 30s 照旧
- **`_stopHealthCheck` 同步清除**：同时清理 `setInterval` 和首次 `setTimeout`，避免泄漏
- **提取 `_healthCheckPing` 独立函数**：供 setTimeout 和 setInterval 共用

### 文件改动

- `src/app-core.js`：
  - `_state` 新增 `healthCheckInitTimer`
  - 重构：`_startHealthCheck` 拆出 `_healthCheckPing()`；首次 1s setTimeout + 后续 30s setInterval
  - `_stopHealthCheck` 同时清除两个定时器
  - **`getConfig` 防御性修复**：加载配置时校验 qwNames(7)/gfpNames(5)/procNames(5) 数组长度，异常时回退 DEFAULT_CONFIG
  - **`saveConfig` 防御性修复**：落盘前归一化数组长度，防止脏数据持久化
- `src/app.js`：
  - 新增 `EXPECTED_CACHE_NAME` 常量 + `forceUpdateSW()` 强制更新函数
  - `registerServiceWorker`：3s 后自检 SW 版本，不匹配则自动 `forceUpdateSW`
  - 工具栏新增 `🔄 刷新` 按钮（调用 `forceUpdateSW`）
- `src/时间管理助手.html`：工具栏新增 `btn-refresh` 按钮
- `src/service-worker.js`：CACHE_NAME v41 → v42 → v43
- `sync-server.js`：版本号 v2.11.0 → v2.11.2

---

## v2.11.1 — 2026-05-28（Bug 修复：pull 合并逻辑 + 心跳检测）

修复 v2.11.0 两个待排查 bug（§22.10 / §22.11）。

### 一、§22.11 修复：pull 全量替换导致离线编辑丢失（严重）

**根因**：`_applyServerWeekToLocal` 对 cells / keyitems 从空对象起手重建，服务器返回什么就无条件覆盖本地。用户离线编辑后回到在线 → autoPull 触发 → 服务器返回旧数据 → 本地离线编辑被覆盖。同时 autoPull（800ms）先于离线队列 flush（1500ms），被污染的旧数据又在 flush 时推回服务器，造成双向丢失。

**修复**：

- **cells 合并**：从 `getCells()` 读取现有本地数据，逐 cell 按 `updatedAt` 比较。服务端 ≥ 本地时覆盖；本地更新则保留。服务端清空的格仅当 server timestamp ≥ local 时才删除。
- **keyitems 合并**：同上，逐项按 `updatedAt` 合并。
- **review 合并**：比较 `updatedAt`，仅当服务端 ≥ 本地时才覆盖。
- **autoPull 时序**：延迟 800ms → 2500ms，且先 `flushOfflineQueue()` 完成后再 `pullWeek()`。

### 二、§22.10 修复：重启后同步状态假阳性

**根因**：`_state.status` 仅由最近一次 push/pull/autoPull 结果决定，无周期性可达性验证。autoPull 404（服务器在线无数据）也判为 connected 且永不再探测。启动竞态下 autoPull 失败后状态永久错误。

**修复**：

- **周期性心跳检测**：30s 间隔 ping `/info`。仅在 `connected` / `error` 态执行。成功 → `connected`；失败 → `error` + `lastError`。
- **自动恢复**：心跳成功即从 `error` 恢复到 `connected`。
- **生命周期**：`init()` 时同步启用则自动启动心跳；`saveSyncConfig` 关闭同步时停止。

### 三、文件改动

- `src/app-core.js`：
  - `_applyServerWeekToLocal`：cells/keyitems/review 三段改为逐条按 `updatedAt` 合并
  - `_state` 新增 `healthCheckTimer`
  - 新增 `_startHealthCheck()` / `_stopHealthCheck()`（30s 间隔 `/info` ping）
  - `init()` 启用同步时调用 `_startHealthCheck()`
  - `saveSyncConfig()` 关闭同步时调用 `_stopHealthCheck()`
  - 暴露 `startHealthCheck` / `stopHealthCheck` 到公共 API
- `src/app.js`：
  - `setupSyncUI`：autoPull 延迟 800→2500ms，先 `flushOfflineQueue()` 再 `pullWeek()`
- `src/service-worker.js`：CACHE_NAME v40 → v41

---

## v2.11.0 — 2026-05-28（HTTPS 化 + CA-leaf 证书架构 + 离线变更队列）

继 v2.10.2 离线启动修复后，本版完成两件大事：

1. **HTTPS 全链化**：静态/同步双服务在原 HTTP 端口旁加监听 HTTPS，解决 iPhone PWA 长期被自签 HTTP 卡住启动的痛点。
2. **离线变更队列**：把 v2.10.2 留下的"自动重试推送依赖下次保存"缺口补上，离线编辑全部入队，回到在线立即 flush。

### 一、HTTPS + CA-leaf 证书架构

#### 设计

放弃 v2.10.x 里"一份自签 leaf 直接装手机"的设计，改成 **CA + leaf 两层**：

- **CA**（Time Planner Personal CA，10 年）：一次性装到 iPhone「证书信任设置」，**永久信任**
- **leaf**（DESKTOP-QRG0JNN，2 年）：日常服务器使用；SAN 含 `localhost`、`127.0.0.1`、电脑 mDNS 名（`*.local`）、当前 LAN IP（自动从 `os.networkInterfaces()` 抓取）
- **服务器读取的是 chain**（`leaf-cert-chain.pem` = leaf + CA 拼接），客户端通过 chain 校验链能验签
- **更换 LAN IP / 主机名时只重新生成 leaf**（`node gen-leaf.js`），iPhone 不需要重装 CA

#### 工具链（`tools/gen-cert/`）

- `gen-ca.js`：仅生成 CA 根证书一次（10 年），写出 `ca-cert.pem` + `ca-cert.crt` + `ca-key.pem`
- `gen-leaf.js`：用 CA 私钥签发 leaf 服务器证书（2 年），写出 `leaf-cert.pem` + `leaf-cert-chain.pem` + `leaf-key.pem`，自校验 `checkIssued + verify` 确保 Node TLS 可加载
- `gen-all.js`：一键编排（首次安装跑这个）
- `lib-forge.js`：共享 PEM I/O + ASN.1 helper
- 老 `gen-cert.js` 保留作为废弃 stub，运行立即报错引导用户走新工具

#### 服务器侧

- `src/server.js`：新增 `/cert.crt` `/cert.pem` `/ca.crt` `/ca.pem` 四条 alias 路由，HTTP 6371 也能下载 CA（避免首次访问时 "未信任 HTTPS" 拦截下载）。HTTPS 服务读 `leaf-cert-chain.pem` + `leaf-key.pem`。
- `sync-server.js`：同步加载 leaf chain。
- 双服务双端口：静态 6371/6443，同步 6372/6444。

### 二、iPhone PWA 现状（重要：iOS 18 限制）

> **iOS 17+ 安全策略**：自签 CA + 私网 origin（IP 或 mDNS .local）的 Safari **不允许装 standalone PWA**，即使 CA 已被「完全信任」。"添加到主屏幕"会降级为**普通 Safari 书签**。Apple 在 Safari iOS 17/18 文档中无明文限制，但实测稳定可复现：预览图标短暂显示蓝紫色（manifest+icon 已识别），最终 commit 时降级为灰色网格 + "删除书签"。

**变通方案**：接受书签模式 + Service Worker 离线缓存。功能上 95% 等同 PWA：

- ✅ 离线启动：点书签 → Safari 打开 → SW v39 接管 → 拿缓存 → 秒开（已在 iPhone 18.2 验证）
- ✅ 数据完整：localStorage / IndexedDB 与 standalone 模式共享
- ❌ 顶部仍带 Safari 地址栏（不是独立全屏）
- ❌ 主屏图标是灰色网格（不是 manifest 中的蓝紫色）

如需 standalone PWA 体验，需用 ngrok / Cloudflare Tunnel + Let's Encrypt 真证书（公网域名）。本版不支持。

### 三、离线变更队列（阶段 3.5 落地）

补完 v2.10.2 留下的"离线编辑只在下一次保存时才重试"缺口。

#### 实现

- 新增 `localStorage[tm_sync_pending_queue]`：存 `[{year, week, queuedAt}, ...]`，去重
- `pushWeek` 入口先 `_enqueuePending(year, week)` 入队（去重）→ 成功后 `_dequeuePending` 出队 → 失败保留等下次 flush
- `flushOfflineQueue()`：串行 push 队列里所有周；失败保留，成功出队
- **触发时机**：
  - `init()` 阶段，若已 online 且队列非空 → 1.5s 后自动 flush
  - 监听 `window.addEventListener('online')` → 立即 flush
  - 手动 `syncClient.flushOfflineQueue()` 暴露给 UI 调用
- 状态：`_state.pendingQueueSize` 反映给 UI 状态灯

#### 单测（`tools/test-offline-queue.js`）

8/8 通过：接口暴露、初始空、localStorage 持久化往返、`enabled=false` 时 flush 自动跳过。

### 四、Service Worker v36 → v40 演进

- **v37**：`cache.addAll(ASSETS)` 改为 `cache.addAll(ASSETS.filter(u => !u.startsWith('http')))`，避免 `xlsx-js-style` CDN 不可达时 install 原子失败把整个 SW 拖死（v36 在某些网络下的根因）
- **v38**：`fetch` 拦截器跳过 `/manifest.json` `/icon-192.png` `/icon.svg`，让 Safari 装 PWA 时拿原始网络响应（不被 SW 缓存副本干扰）
- **v39**：随 v2.11.0 发布的初版
- **v40 (hotfix)**：修 `updateSyncDot` 只更新桌面 `id="sync-dot"` 不更新手机端 footer 的 class-only `<span class="sync-dot">`。iPhone 实测表现：「立即推送 ✓ 成功，但状态点一直蓝闪不变绿」根因。改 `querySelectorAll('.sync-dot')` 同步刷新所有 dot。

### 五、UI 临时诊断小标

`app.js` 在 PWA 启动后右下角挂一个 `<div id="sw-diag">`，实时显示：

```
SW✓ time-planner-v40 (10) [queue:N]
```

点击隐藏。便于 iPhone 端用户一眼看出 SW 注册状态、缓存项数、待推送队列大小，无需开 console。后续可作为可关闭 debug 选项保留。

### 六、文件改动

新增：

- `tools/gen-cert/gen-ca.js`
- `tools/gen-cert/gen-leaf.js`
- `tools/gen-cert/gen-all.js`
- `tools/gen-cert/lib-forge.js`
- `tools/test-offline-queue.js`
- `certs/ca-cert.pem` `ca-cert.crt` `ca-key.pem`
- `certs/leaf-cert.pem` `leaf-cert-chain.pem` `leaf-key.pem`

改动：

- `src/server.js`：新增 `/cert.crt` 等 4 条 alias；HTTPS 读 `leaf-cert-chain.pem`
- `sync-server.js`：HTTPS 读 `leaf-cert-chain.pem`
- `src/service-worker.js`：v36 → v39（含 install filter、fetch 跳过 manifest/icon）
- `src/manifest.json`：`start_url ./时间管理助手.html → ./`；新增 `id` `scope`（iOS 17+ 推荐）
- `src/app.js`：`registerServiceWorker` 后挂 `mountSwDiagBadge`；同步 UI（已有）继续工作
- `src/app-core.js`：syncClient 增加 `_loadPendingQueue / _enqueuePending / _dequeuePending / flushOfflineQueue / getPendingQueue`；pushWeek 入口入队、成功出队；init 监听 online 事件；接口暴露 `flushOfflineQueue` `getPendingQueue`
- `tools/gen-cert/gen-cert.js`：废弃 stub，引导用户跑 `gen-all.js`
- `tools/gen-cert/package.json`：依赖 `node-forge`（替代 `selfsigned`）

### 七、验收脚本

```powershell
# 1. 证书生成（首次跑一次）
cd tools\gen-cert
node gen-all.js

# 2. 防火墙放行 HTTPS 端口（管理员 PowerShell）
New-NetFirewallRule -DisplayName 'TimePlanner-Static-HTTPS-6443' -Direction Inbound -Protocol TCP -LocalPort 6443 -Action Allow -Profile Private,Public
New-NetFirewallRule -DisplayName 'TimePlanner-Sync-HTTPS-6444'  -Direction Inbound -Protocol TCP -LocalPort 6444 -Action Allow -Profile Private,Public

# 3. 启服务
node sync-server.js
node src\server.js

# 4. 离线队列单测
node tools\test-offline-queue.js
```

### 八、已知限制

- **iOS 18.2 自签 CA + 私网 origin 装不了真 PWA**（书签模式工作；如要真 PWA 需公网真证书）
- **WebSocket 推送（原计划 3.3）推迟到 v2.12**：HTTPS 上线后必须改 wss://，与 v2.11.0 同期落地略激进，分版本走

---

## v2.10.2 — 2026-05-28（离线启动修复：手机离开 LAN 也能秒开 PWA）

### Bug

用户反馈："手机端出问题了，不再同一 WiFi 的情况下都打不开，大幅降低了外出的手机的记录的实用性。"

### 根因

`service-worker.js` 自 v2.9.1 起对同源资源采用 **network-first** 策略：每次请求 HTML/JS/CSS 都先 `fetch()`。当 iPhone 离开 LAN 后，PWA 的启动 URL（`http://192.168.31.153:6371/...`）变成完全不可达（不是无网络，是路由不通），iOS 的 fetch 不会立即报错而是要等 ~30 秒 TCP 超时才 fallback 到 cache。用户早就以为 PWA 卡死关掉了。

### 修复

把同源策略改为 **cache-first + stale-while-revalidate**：

- 命中缓存 → **立即返回**（0ms，完全不等网络）→ 离线点 PWA 图标也能秒开
- 同时后台静默 `fetch()` 拉新版本，成功就写回缓存供下次使用
- 网络失败 → 吞掉错误，已经返回的缓存版本不受影响

版本更新机制不受影响：浏览器对 SW 源文件本身的 byte 比对独立于 fetch handler，配合 `app.js` 的 `updatefound → SKIP_WAITING → controllerchange → reload` 流，下次回到 LAN 时新版会自动顶上。

### 用户层面变化

- **离线启动**：手机离开 WiFi 一样能秒开 PWA，看到上次同步过的数据，可以继续填写、保存到 localStorage。
- **回到 LAN 后**：任意一次保存触发 debounce push → 自动同步累积的离线编辑（依赖现有 `_emitSaveChange` 流）。
- **同步状态点**：离线期间因 LAN 不可达会变红 / 黄，这是预期，不影响本地操作。

### 已知缺口（留给后续阶段）

- 离线编辑的"自动重试推送"目前依赖下一次保存动作触发；若用户离线编辑后不再修改即关掉应用，那批改动要等下次手动点 ⬆ 立即推送。完整的"离线变更队列 + 在线 flush"放在阶段 3.5。

### 文件改动

- `src/service-worker.js`：`networkFirst()` → `cacheFirstSWR()`；CACHE_NAME `v35` → `v36`

---

## v2.10.1 — 2026-05-28（同步配置自动化：电脑名/端口零填写）

继 v2.10.0 双向同步落地后，把"电脑名 / 端口"两个字段从必填降级为**全自动推导**，绝大多数场景下用户只需勾"启用同步"+点"测试连接"即可。

### 用户层面变化

- 同步面板默认只显示一个 **`同步服务器（自动检测）`** 只读输入框，里面已经填好 `http://<浏览器当前 host>:6372`：
  - 桌面访问 `127.0.0.1:6371` → 自动得到 `http://127.0.0.1:6372`
  - 手机访问 `192.168.31.153:6371` → 自动得到 `http://192.168.31.153:6372`
  - mDNS 访问 `<电脑名>.local:6371` → 自动尝试 `.local` + 裸主机名两条
- 原"电脑名 / 端口 / 缓存 IP"三块字段全部移入 **「高级设置（手动指定）」** 折叠区，默认收起：
  - 顶部多了一个 ✅ **`自动从浏览器地址检测主机名 / 端口`**（默认勾选）
  - 取消勾选才解锁手动输入框，作为"自动检测失败"或"跨网段定向"等高级场景的兜底
- 状态行文案微调：
  - 已关闭 → "勾选「启用同步」后点 \"测试连接\" 即可使用（默认自动检测主机）"
  - 已连接 → 主机名优先显示服务端 `info.hostname`，再回落到 effective host

### 数据迁移

- `tm_sync_config` 已写入老配置的用户：自动继承默认 `autoHost=true`；原 `hostname`/`port` 字段保留但被 autoHost 短路。取消勾选即可回到旧手动模式，原值原样回填。

### 文件改动

- `src/app-core.js`：
  - `DEFAULT_SYNC_CONFIG` 新增 `autoHost: true`
  - 新增 `getEffectiveHost(cfg)` / `getEffectivePort(cfg)`，集中决策"用自动检测还是用手动覆盖"
  - `buildUrls(cfg)` 改为消费上述两个 helper
  - `detectHostname()` 放开 IPv4 与 `localhost`，使其在 `127.0.0.1:6371` / `192.168.x.x:6371` 场景也能正确返回
  - 导出新增的 helper
- `src/时间管理助手.html`：同步面板 DOM 重排，新增 `#sync-detected` 只读框 + `<details class="sync-advanced">` 折叠 + `#sync-auto-host` 复选框
- `src/app.js`：`openSyncModal` / `readSyncModalConfig` 接入 `autoHost`；新增 `toggleSyncManualInputs` 与 `refreshDetectedHost`；`updateSyncStatusUI` 状态文案优化
- `src/styles.css`：新增 `.sync-advanced` 折叠区与 `[readonly]` / `:disabled` 输入框样式
- `src/service-worker.js`：CACHE_NAME `v33` → `v34`

### Hotfix（同日）

- **Bug**：手机端每次重新打开 PWA 都显示空白，必须手点「立即拉取」才能看到上次同步过的数据。
- **根因**：`app.js` 启动 autoPull 的条件是 `cfg.enabled && cfg.autoPull && cfg.hostname`。autoHost 模式下 `cfg.hostname` 保留为空字符串（host 由 `window.location` 推导，不写回 config），所以这个 if 永远为 false，启动自动拉取沉默失效。
- **修复**：把 `cfg.hostname` 替换为 `syncClient.buildUrls(cfg).length > 0`，既兼容老配置（手动 hostname 非空），也兼容新 autoHost。
- **副作用**：每次 PWA 冷启动都会主动从服务器拉一次当前周，因此即便 iOS 在内存压力下清掉了 localStorage，下次打开也能从同步服务恢复完整数据。
- `src/service-worker.js`：CACHE_NAME `v34` → `v35`

---

## v2.10.0 — 2026-05-28（阶段 3.2 客户端集成：保存即同步）

接入 sync-server，客户端层面"按需求文档 §20.10 定义的实施阶段 3.2"全部到位。

### 用户层面变化

桌面工具栏新增 **`☁ 同步`** 按钮（带状态灯 5 色：灰=未启用 / 浅灰=未连接 / 黄=连接中 / 绿=已连接 / 红=错误 / 蓝闪=待推送）：

- 点开弹出**同步面板**：
  - **状态行** + 启用同步 toggle
  - 电脑名 / 端口 / 已缓存 LAN IP（自动填充）
  - **尝试 URL（按顺序 fallback）** 实时预览
  - 5 个动作：测试连接 / ⬇ 立即拉取 / ⬆ 立即推送 / 保存设置 / 关闭
  - 内嵌操作日志（暗色背景，绿成功 / 红失败 / 蓝信息）
- 启用同步后：
  - 任意保存（cells / keyitems / review / config / archive）→ **debounce 1.5s 后自动推送**
  - 启动时若已配置主机名 → **静默拉取当前周**
- 手动 JSON 导出/导入按钮**仍保留**作为兜底通道。

### 数据模型变化

**LocalStorage 新增三种 key**（不影响原有 5 类周数据 key）：

| Key | 内容 |
|---|---|
| `tm_sync_config` | `{ enabled, hostname, port, lastIP, autoSync, autoPull }` |
| `tm_device_id` | 设备唯一 UUID（每首次写入即固化，作为 `updatedBy` 字段） |
| `tm_<year>_w<week>_syncmeta` | 每个 cell / keyitem 的 `updatedAt` 时间戳，per-week 一份 |

### 同步语义（与 sync-server.js merge 规则对齐）

- **保存触发**：`AppCore.onSaveChange` 监听器接收 `(year, week, part, prev, next)`，diff 出真正变化的 cell / keyitem，仅给变化项打上 `updatedAt = Date.now()`。
- **推送 wrap**：本地 `cells = { key: {title, code} }` → 服务端 `{ key: {title, code, updatedAt, updatedBy} }`；keyitems 从纯字符串 → `{value, updatedAt, updatedBy}`。
- **拉取 unwrap**：把服务端的包装层去掉，写回 LocalStorage 的"裸"格式，并把 `updatedAt` 落入 `_syncmeta`。
- **抑制 pull→push 风暴**：`syncClient._applyingPullForWeek` 标志位，pull 期间触发的 saveChange 事件被 `_handleSaveChange` 直接丢弃。
- **失败处理**：3 级 URL fallback（`<电脑名>.local` → `<电脑名>` → 缓存 IP），逐一尝试；任一返回 4xx 直接抛业务错误不再 fallback；网络/超时 4 秒；POST 超时 8 秒。

### 文件改动

| 文件 | 改动 | 行数变化 |
|---|---|---|
| `src/app-core.js` | 5 个 save 函数加 emit 事件；新增 `syncClient` 模块 + `onSaveChange` API | +536 行 |
| `src/app.js` | 末尾新增整段 `setupSyncUI` + 6 个 handler；`init()` 内新增 `setupSyncUI()` 调用 | +200 行 |
| `src/时间管理助手.html` | 工具栏加 `btn-sync`；末尾加 `sync-modal` DOM | +47 行 |
| `src/styles.css` | 同步面板样式（状态点 6 色 + 表单 + 日志 + 手机端 sync-bar） | +70 行 |
| `src/service-worker.js` | `CACHE_NAME` v31→v32 | 1 行 |

### 不在本版本

- WebSocket 实时推送（→ 3.3 / v2.11）
- 扫码绑定 + 设备令牌鉴权（→ 3.4 / v2.12）
- exe 打包 + 开机自启（→ 3.5 / v2.13）
- 离线变更队列与冲突 UI 提示（→ 3.4 一并打磨）
- ~~手机端 footer 的同步按钮~~ → **热修：v33 SW 已补上**。手机端单日页底部新增一行 `☁ 同步设置` 按钮，带状态点，点开后复用同一个同步面板

### 端到端验证清单

按以下顺序操作可确认全链路通：

1. 双击 `启动服务器.bat` → 看到 6371（黑窗）+ 6372（新黑窗）两个进程都活
2. 浏览器访问 `http://127.0.0.1:6371/时间管理助手.html`
3. 工具栏右上能看到「☁ 同步」按钮，状态点为**灰色**（未启用）
4. 点开同步面板 → hostname 输入 `DESKTOP-QRG0JNN`（或你的电脑名）→ 端口 `6372` → 点**测试连接**
5. 日志区出现 `✓ 已连通 → http://...local:6372`，状态变绿，已缓存 IP 自动填入
6. 勾选**启用同步** → 点**保存设置** → 关闭面板，状态点变**浅灰**（已启用未连接）或**绿**
7. 在主表格点一格修改内容保存 → 状态点变**蓝色脉动**（debounce 中）→ 1.5s 后变**绿** → `sync-data/<year>/wXX.json` 文件出现
8. 在另一台设备（手机或第二个浏览器隐身窗）打开同地址 → 配置同样的 hostname/port → 启用同步 → 应该看到刚才那一格的修改自动出现
9. 第二台改另一格 → 第一台不会自动看到（v2.11 加 WS 后才是实时；v2.10 需要刷新或手动拉取）

---

## v2.10.0-alpha — 2026-05-28（阶段 3.1 同步骨架：本地同步服务上线）

**仅服务端骨架**。客户端尚未集成（3.2 任务），用户层面行为暂无变化。可用 curl / Postman 端到端验证。

### 新增文件

- `sync-server.js`（项目根，零 npm 依赖，仅 Node 内置模块）
  - 端口 `6372`，监听 `0.0.0.0`
  - 端点：
    - `GET  /info` — 返回 `{ hostname, hostnameLocal, lanIPs[], port, protocolVersion, hostId, bootAt }`
    - `GET  /weeks` — 列出已存在的所有 `(year, week)`，含 `weekUpdatedAt` / `archived` / `size`
    - `GET  /weeks/:year/:week` — 拉整周快照（含 `config / cells / keyitems / review / archived`）
    - `POST /weeks/:year/:week/changes` — 上传变更（merge 写回，按粒度 last-write-wins）
    - `GET  /` — 自检 HTML 页（端点列表 + 局域网入口）
- `sync-data/` 自动创建：
  - `meta.json` —— `{ hostId(uuid), protocolVersion, createdAt, lastBootAt }`
  - `<year>/w<NN>.json` —— 每周 1 个文件，结构对齐需求文档 §14.3

### 合并语义（3.1 锁定）

| 字段 | 粒度 | 规则 |
|---|---|---|
| `config` | 整体 | 比对 `updatedAt`，新覆盖旧 |
| `cells` | 单格 | 每 `日期\|时段` 各自比对 `updatedAt` |
| `keyitems` | 单项 | 每 `日期\|行名` 各自比对 `updatedAt` |
| `review` | 整体 | 比对 `updatedAt`，新覆盖旧 |
| `archived` | 粘连 | 一旦 `true` 不可回退为 `false` |

### 工程约束

- 写文件统一 "先写 .tmp 再 rename" 原子化，崩溃不会损坏现有数据
- POST body 上限 5 MB，超限直接 413
- CORS 全开（`Access-Control-Allow-Origin: *`），方便客户端从静态服 `6371` 跨端口直连同步服 `6372`
- 端口被占用时直接 `process.exit(1)` 并给出明确换端口提示，不静默漂移
- 不含扫码 / 不含 WebSocket / 不含设备令牌（3.4 / 3.3 任务）

### 启动方式

- 命令行：`node sync-server.js`（默认 6372，可加参数指定端口）
- BAT：`启动服务器.bat` 已升级为同时拉起 **静态服务 6371（当前窗口）+ 同步服务 6372（新开窗口）**
- 桌面快捷方式不变

### 端到端验证

按以下顺序执行均通过：

```powershell
# 主机自我描述
curl http://127.0.0.1:6372/info

# 列周（首次为空）
curl http://127.0.0.1:6372/weeks

# 写一格
curl -X POST http://127.0.0.1:6372/weeks/2026/22/changes ^
  -H "Content-Type: application/json" ^
  -d "{\"cells\":{\"2026-05-25|07:00-07:30\":{\"title\":\"读书\",\"code\":1.4,\"updatedAt\":1700000000000,\"updatedBy\":\"windows\"}}}"

# 读回
curl http://127.0.0.1:6372/weeks/2026/22

# 写新值（旧 updatedAt 不能覆盖）
# 写新值（新 updatedAt 能覆盖）
# archived=true 后无法回退
```

通过 mDNS 主机名 `http://DESKTOP-QRG0JNN.local:6372/info` 也可直达（curl 验证通过）。

### 不在本版本范围

- 客户端集成（同步面板 / 自动推拉）→ 3.2
- WebSocket 实时推送 → 3.3
- 扫码绑定 + 设备令牌 → 3.4
- exe 打包 + 开机自启 → 3.5

---

## v2.9.1 — 2026-05-28（修复 PWA 书签停留旧版 · SW 改 network-first + 自动重载）

用户反馈：书签 `http://127.0.0.1:6371/时间管理助手.html` 总是显示旧版本，要多次刷新或关掉 PWA 才能拿到最新。

### 根因

`service-worker.js` 用纯 cache-first：

```js
// before
event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
```

资源一旦进过缓存，浏览器永远只读缓存。即便发布新版本提升了 `CACHE_NAME`，由于：

1. 第一次刷新时旧 SW 仍在控制页面，照样吐旧 HTML/JS。
2. 浏览器在后台拉到新 `service-worker.js`、安装新 SW、删旧缓存。
3. 新 SW 接管后才能给出新内容 —— **但当前页面已渲染**。

所以书签场景下每发一次新版用户至少要刷两次，否则永远停留在上个版本。

### 修复

#### 1. `service-worker.js` 改为 network-first

- **同源所有 GET（HTML/JS/CSS/JSON/SVG/PNG）**：先 `fetch` 网络，成功则更新缓存返回；失败（离线/服务器宕）回落 `caches.match`。
- **跨域（xlsx-js-style CDN）**：保留 cache-first（CDN URL 内容不变，缓存命中越多越好）。
- 离线场景仍可用：网络失败 → 自动回落最近一次缓存的版本。
- 6371 / 8080 这类本地服务器更是零成本：每次都能拿到刚保存的源文件。

#### 2. SW 增加 `SKIP_WAITING` 消息端口

```js
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});
```

#### 3. `app.js` 加自动更新流

`registerServiceWorker()` 替代原来一行注册：

- 注册前记录 `hadControllerAtStart = !!navigator.serviceWorker.controller`。
- 注册成功后立刻 `reg.update()` 主动检查新版。
- 监听 `updatefound`：新 worker `installed` 且页面已被旧 SW 控制时，发 `SKIP_WAITING` 让新 SW 立即激活。
- 监听 `controllerchange`：仅当 `hadControllerAtStart === true` 时 `window.location.reload()`，避免首次安装陷入循环。

#### 4. 端到端效果

| 场景 | 旧版（cache-first） | 新版（network-first + 自动重载） |
|---|---|---|
| 在线 + 书签打开 | 旧缓存版 | ✅ 实时最新 |
| 离线 + 书签打开 | 旧缓存版 | 旧缓存版（行为一致） |
| 改源文件 → 刷新 | 还是旧的，要再刷 1～2 次 | ✅ 一次就看到新版 |
| 期间检测到新 SW | 下次刷新才生效 | ✅ 后台静默 reload 一次直接到新版 |

### 文件改动

- `src/service-worker.js`：`CACHE_NAME` v30 → v31；重写为 network-first（同源） + cache-first（跨域）；新增 `SKIP_WAITING` message 处理；`activate` 内补 `clients.claim()`。
- `src/app.js`：`init()` 末尾的 SW 注册一行替换为 `registerServiceWorker()`，新增同名函数实现自动更新流。
- `时间管理助手-iPhone/`：同步上述两个文件。

---

## v2.9.0 — 2026-05-27（数据导出 / 导入 JSON · 双端跨设备迁移）

桌面 ↔ 手机数据迁移的过渡方案：手动导出 / 导入 JSON。先于扫码同步落地，作为永久兜底通道。

### 新增能力

- **导出**：`📤 导出数据` 把所有 `tm_YYYY_wNN_*` 周数据打包为单个 JSON 文件下载，文件名 `时间管理助手-数据-YYYYMMDD-HHMM.json`。
- **导入**：`📥 导入数据` 选 JSON 文件 → 弹确认框显示「总条目 / 涉及周列表 / 导出时间」→ 确定后合并写回 LocalStorage。
- 不导出 `tm_viewMode` 等设备级偏好（避免跨设备污染）。

### JSON Schema

```json
{
  "schema": "time-planner-v1",
  "exportedAt": "2026-05-27T15:00:00.000Z",
  "keyCount": 24,
  "data": {
    "tm_2026_w22_cells":    "{...}",
    "tm_2026_w22_keyitems": "{...}",
    "tm_2026_w22_review":   "{...}",
    "tm_2026_w22_config":   "{...}"
  }
}
```

每个 value 是 LocalStorage 原样的字符串（JSON-in-JSON）。导入时仅写回严格匹配 `tm_\d{4}_w\d{1,2}_(config|cells|keyitems|review|archived)$` 的 key，未识别 key 直接丢弃。

### 模式

- **merge**（v2.9.0 默认）：仅按 key 覆盖；本地多余 key 不删。安全、可叠加。
- **replace**（已实现纯函数，UI 暂未暴露）：先删本机所有周 key，再写入。后续若需要"完全照搬另一台设备"再开放按钮。

### 双端入口

- **桌面工具栏**：`📤 导出数据` / `📥 导入数据` 两个按钮，紧邻 `📥 导出 Excel`。
- **手机端 footer**：原「切换到桌面版」按钮上方加一行同样的两个按钮。
- **共用 handler**：`handleExportData` / `handleImportClick` / `handleImportFileChosen`；手机端通过 `data-export-data` / `data-import-data` 属性绑定到同一函数；隐藏的 `<input type=file id="inp-import-file">` 由按钮触发，桌面与手机共用。

### 跨设备迁移流程（典型）

1. 桌面填完 → 点「📤 导出数据」→ 浏览器下载 JSON
2. 通过邮件 / 微信 / AirDrop 把 JSON 发到手机
3. iPhone Safari 打开 PWA → 切手机版 → 点「📥 导入数据」→ 选刚收到的 JSON → 确认 → 完成

反向同理。

### 文件改动

- `src/app-core.js`：新增 `exportAllData / summarizeImport / importAllData` 三个纯函数，导出到 `AppCore`
- `src/时间管理助手.html`：toolbar-right 加 `btn-export-data` / `btn-import-data`，加隐藏 `inp-import-file`
- `src/app.js`：从 `AppCore` 导入三函数；`init()` 绑定按钮；新增 `handleExportData` / `handleImportClick` / `handleImportFileChosen`；`renderM_Footer` 加两个手机端按钮；`bindMobileEvents` 绑 `data-export-data` / `data-import-data`
- `src/styles.css`：`.m-footer-row` 让手机端 footer 按钮分行
- `src/service-worker.js`：缓存版本 v29 → v30
- `时间管理助手-iPhone/`：同步全部修改文件

---

## v2.8.3 — 2026-05-27（保存校验加严：事件名与编码必须同时非空）

iPhone 真机测试 v2.8.2 后追加要求：截图中 7:30-8:00 的格子事件名为空、code=0（浅绿色 Rest 块），用户认为这同样不应允许。

### 新规则（替换 v2.8.2 的 4 条规则为 3 条）

| 标题 | 编码 | 处理 |
|---|---|---|
| 空 | 空 | 清空格子（删除 cells[id]） |
| **空** | **非空** | 禁止：toast「请填写事件名」，事件名框红框聚焦 |
| **非空** | **空** | 禁止：toast「请填写分类编码…」，编码框红框聚焦 |
| 非空 | 非空合法 | ✅ 唯一允许保存的情形 |
| 任意 | 非空非法 | 编码错误（既有逻辑） |

### 实现

`commitCurrentCell` 在 validateCode 之前两条独立拦截：

```js
if (title === '' && codeRaw !== '') {
  showToast('请填写事件名');
  inpT.classList.add('input-error');
  inpT.focus();
  return { ok: false };
}
if (title !== '' && codeRaw === '') {
  showToast('请填写分类编码（0=Rest · 4=MW · 1.x/2.x/3.x）');
  inpC.classList.add('input-error');
  inpC.focus();
  return { ok: false };
}
```

仍是 Windows 与 iPhone 共用的唯一保存入口，单点修复双端生效。

### 文件改动

- `src/app.js` L979-993：commitCurrentCell 新增双向拦截
- `src/service-worker.js`：缓存版本 v28 → v29
- `时间管理助手-iPhone/`：同步上述两个文件，待重新部署到 Netlify

---

## v2.8.2 — 2026-05-27（事件名非空必须填编码 · 双端同源修复）

iPhone 真机测试发现：填了「事件名」但不填「分类编码」也能保存，导致 cells 出现 `{title:'X', code:''}` 脏数据，本日填写进度不计入、统计也异常。

### 根因

`commitCurrentCell` 中：

```js
// before（app.js:993）
var newPayload = (title || codeRaw !== '') ? { title: title, code: code } : null;
```

OR 逻辑导致「title 非空 + code 为空」也被允许保存。

### 修复

在 `validateCode` 之前加一条前置拦截：

```js
if (title !== '' && codeRaw === '') {
  showToast('请填写分类编码（0=Rest · 4=MW · 1.x/2.x/3.x）');
  inpC.classList.add('input-error');
  inpC.focus();
  return { ok: false };
}
```

新规则 4×4 真值表：

| 标题 | 编码 | 处理 |
|---|---|---|
| 空 | 空 | 清空格子（删除 cells[id]） |
| **非空** | **空** | **禁止保存**（toast + 红框聚焦） |
| 空 | 非空合法 | 保存 `{title:'', code}`（纯类别记录，常用于 Rest） |
| 非空 | 非空合法 | 保存 `{title, code}` |
| 任意 | 非空非法 | 编码错误（已有逻辑） |

### 双端同源

`commitCurrentCell` 是 Windows 与 iPhone 共用的唯一保存入口（手机端 `data-cell-id` 单击复用同一份 `cell-modal` 弹窗），改一处即双端生效。

历史脏数据：`{title:'X', code:''}` 在新规则下点开会被弹窗拦截保存，引导用户主动补全编码。

### 文件改动

- `src/app.js` L979-986：commitCurrentCell 前置拦截
- `src/service-worker.js`：缓存版本 v27 → v28
- `时间管理助手-iPhone/`：同步上述两个文件，待重新部署到 Netlify

---

## v2.8.1 — 2026-05-27（手机端：补齐锁定 + 周复盘填写）

按 v2.8.0 遗留 TODO 推进手机端：

### 1. 前一日补齐锁定

新增 `getMobileLockInfo()`：

```js
// 仅在用户停留在「今天所在的 ISO 周」时启用
// 遍历本周一..周日，跳过 >= today 的日期
// 返回第一个 filled < 34 的过去日 { date, filled }；全部补齐则返回 null
```

约束行为：

- **后退按钮**：始终允许（可往前查看历史）
- **前进按钮**：若 newDate > lockDate 则 `showToast('请先把 YYYY-MM-DD 的 34 格补齐')`，不切换
- **今天按钮**：若有 lock，跳到 lockDate 而不是今天，并 toast 提示
- **首次进入兜底**：`renderMobileDay()` 入口若 `mobileState.date > lockDate`，强制归到 lockDate

DateBar 下方追加：

- 黄色锁定 banner：`⚠ 2026-05-26 仅填了 12/34 格，请先补齐才能切到后续日期`
- 当日填写进度：`本日已填 18 / 34 格` + 进度条

### 2. 手机端周复盘填写（替换原只读）

新增 `renderM_Review` + `bindMobileReviewEvents`，与桌面端 `renderReviewPanel` 共享 `getReview/saveReview` 与 `REVIEW_ITEMS`：

| 编号 | 字段 | 类型 |
|---|---|---|
| 1 | 本周关键词 | input |
| 2 | 自我打分 | input |
| 3 | 总体评价 | textarea |
| 4 | 本周读的书 | textarea |
| 5 | 本周看的电影 | textarea |
| 6 | 最有意义的5件工作 | list × 5 |
| 7 | 干的最傻3件事 | list × 3 |
| 8 | 最牛3句话 | list × 3 |
| 9 | 请吃饭的人 | textarea |
| 10 | 赢得奖励时间 | 自动 = balance（只读） |

任一框 `change` 即写回 LocalStorage 并 toast「已保存」。多框 list 用 `data-mrv-list="key" data-mrv-idx="n"` 命名，与桌面端 `data-rv-list` 同结构、同 LocalStorage 字段，桌面 ↔ 手机改动相互可见。

### 3. 文件改动

- `src/app.js`：新增 `getMobileLockInfo`、`dailyFilledCount`、`REVIEW_ITEMS`、`renderM_Review`、`bindMobileReviewEvents`；改造 `renderM_DateBar(ctx, lock, dFilled)`、`renderMobileDay`、`renderMobileWeek`、`bindMobileEvents` 中的日期按钮
- `src/styles.css`：新增 `.m-fill-progress / .m-rv-item / .m-rv-label / .m-rv-input / .m-rv-textarea / .m-rv-list-input / .m-rv-reward / .m-rv-reward-pos / .m-rv-reward-neg`
- `src/service-worker.js`：缓存版本 v26 → v27
- `时间管理助手-iPhone/`：同步上述四个文件，待重新部署到 Netlify

---

## v2.7.10 — 2026-05-27（iPhone 当日汇总数字 bug 修复）

iPhone 真机截图反馈：「标准数」错显为日期字符串 `2026-05-27`、「可用数」NaN；本周累计页的「标准数 × 7」显示 `undefined`。根因与修复：

### Bug 1 — 单日汇总：参数串位

`renderMobileDay` 调用错传了 `ctx.date`：

```js
// before（app.js:1571）
var stats = calcDailyStats(cellsToday, ctx.date, config.standard);
//                                     ^^^^^^^^ 多余参数，把日期当成了 standard
// after
var stats = calcDailyStats(cellsToday, config.standard);
```

`calcDailyStats(dayCells, standard)` 只接受两个形参，多传的 `ctx.date = "2026-05-27"` 被当成 `standard`：

- `s.standard = "2026-05-27"` → 直接渲染成日期串
- `s.available = Math.max(0, potential - "2026-05-27")` → 数字减字符串 = NaN

### Bug 2 — 周累计：`totals.standard` 未累加

`calcWeeklyStats` 的 `t` 初始化里没有 `standard` 字段，循环也没累加：

```js
// app-core.js:168-171
var t = { ..., potential:0, available:0, standard:0, ... };  // 新增 standard:0
// :177
t.potential += d.potential; t.available += d.available; t.standard += d.standard;
```

修复后，weekly `t.standard = standard × 7`（每日叠加），与 mobile week 页「标准数 × 7」展示一致。

### 文件改动

- `src/app.js` L1571：去掉多余参数
- `src/app-core.js` L168-177：totals 初始化与累加补充 `standard`
- `src/service-worker.js`：缓存版本 v25 → v26（强制 iPhone 拉新）
- `时间管理助手-iPhone/`：同步上述三个文件，待重新部署到 Netlify

---

## v2.7.9 — 2026-05-27（Excel 三块布局 · 加粗黑框）

按截图反馈调整 Excel 排版：

### 1. 三块分明的布局

| 块 | 位置 | 大小 |
|---|---|---|
| **A 主时间表** | 左上 cols 0..14 / rows 0..39 | 1 标题 + 5 关键事项 + 34 时段 |
| **B 本周累计** | 左下 cols 0..1 / 从 row 41 起 | 标题 + QW 8 行 + GFP 6 行 + Proc 6 行 + Rest + MW |
| **C 周复盘** | 右上 cols 16..17 / rows 0..N | 标题 + 1～10 项 |

- 列 15 留作空白间隔列（宽度 2）。
- 周复盘的多项条目（6/7/8）：项标题占整行（合并 2 列），下方 N 行写 `1.`、`2.`… 子项。

### 2. 三块外加粗黑框

新增 `applyBlockBorder(ws, r1, c1, r2, c2)`：对块四周边的单元格设置 `style: 'thick' color: #000000` 边框；内部仍保留 `thin #D1D5DB` 浅灰边。

视觉效果：三块互不相连，一眼分清。

### 3. 实现切换

- `doExport` 不再用 `aoa_to_sheet`，改为从空对象起手、逐 cell `placeCell(ws, r, c, value, style)`，便于二维灵活布局（Block C 与 Block A 并排）。
- 通过 `XLSX.utils.encode_range` 设 `!ref` 覆盖所有列（含右侧复盘列），否则导出时可能丢失列 16..17 的内容。
- 合并：标题日期 7 个 + 关键事项 5×7 + 累计/复盘标题各 1 + 复盘多项标题 3 个。

### 文件改动

- `src/app.js`：
  - 新增 `applyBlockBorder / placeCell`。
  - 重写 `doExport` 为三块布局。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v18`。

---

## v2.7.8 — 2026-05-27（保存按钮 · Excel 颜色 · Excel 含复盘累计）

### 1. 显式「💾 保存」按钮

- **配置页**：`← 返回` 旁加 `💾 保存`。点击立即把草稿落盘并同步基线，之后再返回不会再问。
- **填写页**：`📥 导出 Excel` 旁加 `💾 保存`。先把当前焦点 input 的 change 事件触发（捕获未失焦的复盘多框输入），再 toast「已保存到本地」。

### 2. Excel 导出保留单元格颜色 + 包含复盘 / 累计

之前 `XLSX.utils.table_to_book(table)` 只读纯文本表，颜色不带、复盘和累计也不在主 table 里。换成 **xlsx-js-style**（SheetJS 的样式 fork）+ 手工构造 worksheet：

#### 颜色映射

| 分类 | 填充色 | 字色 |
|---|---|---|
| Rest（0） | 浅绿 `#4ADE80` | 黑 |
| QW（1.x） | 深绿 `#16A34A` | 白 |
| GFP（2.x） | 蓝 `#2563EB` | 白 |
| Proc（3.x） | 红 `#DC2626` | 白 |
| MW（4） | 黄 `#FFFF00` | 黑 |

每个时段格按 `getCatClass(code)` 得到 cls，查表染色。空格保留默认（白底黑字、灰边框）。

#### 包含的内容

单 sheet `周计划` 中：

1. **标题行**：年份/周号 + 7 天日期（每天合并 2 列）
2. **关键事项 5 行**（每天合并 2 列）
3. **时段 34 行**（每天 2 列：事件名 + 编码）
4. 空行
5. **本周累计**（QW 7 项 / GFP 5 项 / Proc 5 项 / Rest / MW）
6. 空行
7. **周复盘**（1.关键词 - 10.赢得奖励时间，6/7/8 项展开成多行）

#### 其他

- 列宽：标签列 14，每天事件列 14、编码列 6。
- 全部加细灰色边框 / 中文字体「微软雅黑」/ 居中对齐（左侧标签列与累计/复盘内容左对齐）。
- 文件名：`{year}第{week}周.xlsx`，支持 `showSaveFilePicker` 选择保存位置。

### 文件改动

- `src/app.js`：
  - `init` 绑定 `btn-save-all` / `btn-save-config`；新增 `handleSaveConfig / handleSaveAll`。
  - 重写 `exportExcel` 按需加载 `xlsx-js-style`；重写 `doExport` 手工构造带样式 / 累计 / 复盘的 worksheet。
  - 新增 `EXCEL_CAT_COLOR / EXCEL_BORDER / makeStyle` 辅助。
- `src/时间管理助手.html`：两页 toolbar 各加 `💾 保存` 按钮。
- `src/service-worker.js`：CDN 切到 `xlsx-js-style@1.2.0`；`CACHE_NAME` 升到 `time-planner-v17`。

---

## v2.7.7 — 2026-05-27（配置草稿确认 · 导出确认 · 复盘多框）

针对反馈 3 条：

### 1. 配置页 ⇒ 草稿模式

之前 `change` 事件直接落盘，没有撤销机会。现改为：

- 进入配置页时把当前 config 克隆为 `configDraft`；输入框改动只更新 draft，不触碰本地存储。
- 顶部加橙色提示条「此处修改为草稿，需点 ← 返回 时选择保存才会真正生效」。
- 点 `← 返回` 时若 draft 与原始有差异，弹 confirm「点确定保存 / 点取消放弃」。

实现：`renderConfig` 维护 `configDraft / configOriginal`；`tryLeaveConfig()` 在 `btn-back` 中调用。

### 2. 导出 Excel 加整体保存确认

- 工具栏新增独立按钮「📥 导出 Excel」（蓝灰，与 `确认归档` 分开）。
- 点击后弹 confirm 显示本周数据摘要：

  ```
  本周编号：2026 第 22 周
  已填时段：48 格
  已填关键事项：3 项
  已填复盘条目：5 / 9
  统计：QW … · GFP … · Proc … · Rest … · MW …
  校验：总数 0 / 损益 0 / 投资 0
  ```

- 用户「确定」后才真正生成 .xlsx 下载。
- 「确认归档」按钮的 confirm 也升级为同款详细摘要（明确告知锁定后果）。

实现：新增 `buildWeekSummary()` / `handleExport()`；改写 `handleArchive()`。

### 3. 复盘 N 项内容拆为 N 框

之前「最有意义的5件工作 / 干的最傻3件事 / 最牛3句话」是单 textarea，多项混在一起。改为：

| 项 | 框数 |
|---|---|
| 6. 最有意义的5件工作 | 5 |
| 7. 干的最傻3件事 | 3 |
| 8. 最牛3句话 | 3 |
| 9. 请吃饭的人 | 仍 textarea（数目不固定） |

- 新增 `t: 'list'` + `count` 字段，渲染 N 个独立 input，placeholder 显示 `1.` `2.` …
- 数据存为数组 `review[k] = [...]`。
- **向后兼容**：旧字符串数据按 `\n` 切分自动迁移到数组。
- 任一框 change 时收集所有同 key 的框拼成数组写回。
- `buildWeekSummary` 统计「已填复盘条目」会兼容数组（任一项有内容即计数）。

### 文件改动

- `src/app.js`：
  - `renderConfig` 改用 `configDraft`；新增 `configIsDirty / tryLeaveConfig`；`btn-back` 接入。
  - 新增 `buildWeekSummary / handleExport`；改写 `handleArchive`。
  - `renderReviewPanel` 支持 `t: 'list'`，加 `data-rv-list / data-rv-idx` 写回逻辑。
- `src/时间管理助手.html`：工具栏新增 `<button id="btn-export">📥 导出 Excel</button>`。
- `src/styles.css`：新增 `.rv-list / .rv-list-input` 样式。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v16`。

---

## v2.7.6 — 2026-05-27（关键事项 + 时间表共用统一选区与快捷键）

针对反馈：「快捷键等只作用于了时间表，没作用语第一件事到关键词等填写区域，鼠标移动后也未跟随」。

之前 KI 行（第一件事 / 第二件事 / 第三件事 / 小确幸 / 关键词）用 `data-ki` 单独的 click 处理；时间表行用 `data-cell` + 选区机制。两者互不相通，鼠标拖动从 TS 行进入 KI 行不会扩展选区。

### 统一选区机制

- KI 行也改用 `data-cell` 属性，id 形态 `KI|date|rowName`（与 TS 的 `date|slot` 区分）。
- 新增 `parseAnyCellId / unifiedRow / unifiedCol / idFromUnified` 等 helper。
- 选区索引空间：行 0..4 = KI 五行；行 5..38 = TS 时段。列 = 7 天。
- 鼠标拖动可跨 KI / TS 边界自由扩展；方向键 / Shift+方向键也可跨界。
- 双击或 Enter / F2 进入编辑：KI → 关键事项弹窗；TS → 单元格弹窗（按 id 类型自动派发）。

### 复制 / 粘贴 / 删除 / 向下填充 全面支持 KI

- `clipboard` 改为 `{ kind: 'KI'|'TS', value: ... }`。
- **Ctrl+C**：根据 startId 类型决定剪贴板格式。
- **Ctrl+V**：仅粘贴到 **同种类型**的目标格；类型不匹配自动跳过，toast 显示「跳过 N 个不同类型」。
- **Delete**：选区中 KI 单元格清 keyItems；TS 单元格清 cells。两类都做。
- **Ctrl+D 向下填充**：每列以选区第一行作源；目标行类型不同会自动跳过该格（保证 KI 不覆盖 TS）。

### 撤销栈一同覆盖 KI

- `takeSnapshot()` 同时快照 `cells` 与 `keyItems`。
- KI 弹窗保存 / 清空也接入压栈，可被 Ctrl+Z 撤销。
- 选区批量删 KI 行能完整恢复。

### 文件改动

- `src/app.js`：
  - `renderTbody`：KI 行 `data-ki` → `data-cell="KI|..."`。
  - 新增 `isKeyItemId / parseAnyCellId / unifiedRow / unifiedCol / totalRows / idFromUnified`。
  - `bindCellClicks` 单一 `[data-cell]` 绑定，按类型派发 dblclick / click。
  - `getSelectionRange / forEachSelectedId / moveSelection` 全部走统一 row/col 空间。
  - 新增 `getCellValue / applyToSelection`；`copySelectionToClipboard / pasteClipboardToSelection / deleteSelection / fillDownSelection` 全部按类型分流。
  - `pushUndoSnapshot` 升级为 `takeSnapshot / restoreSnapshot`，覆盖 KI。
  - `openKeyItemEdit / saveKeyItem / clearKeyItem` 接受 id（含 KI| 前缀），并接入撤销。
  - `copyCellFromModal / pasteCellFromModal` 改用新 clipboard 格式。
- `src/styles.css`：移除 KI 行专属 hover outline（避免与选区高亮叠加）。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v15`。

---

## v2.7.5 — 2026-05-27（编码严格校验）

### 编码合法集合

只有以下值能被保存为 `cells[id].code`：

- `''`（空，等同未填写）
- `0` — Rest
- `4` — MW
- `1.1` ~ `1.7` — QW（7 个子分类）
- `2.1` ~ `2.5` — GFP（5 个子分类）
- `3.1` ~ `3.5` — Proc（5 个子分类）

### 拒绝示例

`1.0` `1.8` `1.11` `2.6` `3.7` `0.5` `5` `1` `1.10` 等都会被拒绝并提示具体原因。

### 校验位置

- **弹窗实时校验**：在事件名 / 代码框输入时，代码框非法立即标红（`.input-error`）。
- **保存校验**（`commitCurrentCell`）：非法时不保存、不入栈、不关闭弹窗，顶部 toast 提示具体错误（如「编码超出范围：QW 仅支持 1.1~1.7」），焦点回到代码框并选中。
- **粘贴校验**（`pasteClipboardToSelection`）：剪贴板里若含非法 code（来自历史脏数据），整个粘贴操作被拒绝，toast 提示。
- **`code-hint` 提示行**：动态读取配置里的 QW/GFP/Proc 名称，明确给出每个范围。

### 文件改动

- `src/app.js`：新增 `validateCode(raw)`；`commitCurrentCell` 用新校验；`openCellDialog` 加 `inp-code` 实时 oninput 校验；`pasteClipboardToSelection` 增加剪贴板校验；`code-hint` 文案改进。
- `src/styles.css`：新增 `.cell-form input.input-error` 红边样式。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v14`。

---

## v2.7.4 — 2026-05-27（左侧明细全展示 · Ctrl+Z 撤销 · 移除弹窗向下填充）

### 左侧累计面板：明细全部展示

之前为了"减少噪音"，QW/GFP/Proc 子分类计数为 0 的行会隐藏，导致用户看不到完整 7 个 QW / 5 个 GFP / 5 个 Proc 子项分布。

现按需求文档「明细全部展示」要求，统一展示：
- QW：1.1～1.7 全部 7 行
- GFP：2.1～2.5 全部 5 行
- Proc：3.1～3.5 全部 5 行
- 计数为 0 时显示 `-` 并使用浅灰色（`.lp-zero`），有内容时正常黑色加粗。

### Ctrl+Z 撤销 / Ctrl+Y 重做

- 新增 `undoStack` / `redoStack`（每项都是 `{year, week, cells: 完整快照}`），上限 100。
- 在所有改 `cells` 的入口前压栈：
  - 弹窗保存（仅当内容真的变了）
  - 弹窗清空
  - 选区粘贴 / 删除 / 向下填充
- **Ctrl+Z** = 撤销；**Ctrl+Shift+Z** 或 **Ctrl+Y** = 重做
- 任何新的修改会清空 redo 栈（与 Excel / VS Code 行为一致）
- 撤销 / 重做能跨周回放（栈条目带 `year` / `week`，自动切回原周）

### 移除「向下填充」弹窗按钮

之前 v2.7.0 在弹窗里加的「向下填充 N 格」输入框 + 按钮已被网格 Ctrl+D 完整覆盖，移除以减少 UI 噪音。

弹窗内简化为：保存 / 清空 / 取消 / 复制此格 / 粘贴。

### 文件改动

- `src/app.js`：
  - `renderLeftPanel` 改为全量展示，每个子分类一行（含 0），加 `lp-zero` 标记。
  - 新增 `undoStack / redoStack / pushUndoSnapshot / performUndo / performRedo`。
  - `pasteClipboardToSelection / deleteSelection / fillDownSelection / commitCurrentCell / clearCell` 全部接入压栈。
  - 全局 `keydown` 加 `Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y`。
  - 移除 `saveAndFillDown` 与 `inp-fill-count` 相关绑定。
- `src/时间管理助手.html`：弹窗去掉 `fill-row`；提示行更新含 Ctrl+Z/Y。
- `src/styles.css`：去掉 `.fill-row*`；新增 `.lp-zero` 灰显样式。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v13`。

---

## v2.7.3 — 2026-05-27（选区不再被 click 收回 · 任意框 Enter 保存）

针对 v2.7.2 反馈：
1. 选完区域不能松开鼠标（实际是松开后选区被偷偷收回）
2. Enter 不会保存

### 修复

**选区被 click 收回**

`document.click` 之前用「点击非 cell 区域 → 取消选区」逻辑。但鼠标拖动结束后浏览器派发的 click 事件 target 通常落在 `<table>` / `<tbody>`（不是单元格），导致刚刚拖出的选区被瞬间清空。

改为白名单：点击主表格（`#main-table`）、弹窗（`.modal-box`）、左侧累计、右侧复盘、顶部工具栏内任何位置都**不**清空选区。Esc 仍可清空。

现在的工作流：
- 在起点 mousedown，拖到终点 mouseup → 松开鼠标 → 选区保留 → 直接 Ctrl+C / Ctrl+V / Delete / Ctrl+D。

**弹窗 Enter 保存**

之前事件名输入框 Enter 是「跳到代码框」，用户期望 Enter 保存。现统一：
- **任意框 Enter** = 保存当前格 + 跳下一格
- **Shift + Enter** = 保存 + 跳上一格
- **Ctrl + Enter** = 保存并关闭弹窗（不跳）
- **Tab** = 仍按浏览器默认在事件名 / 代码 / 填充数 间切换

### 文件改动

- `src/app.js`：
  - `document.click` 取消选区改为白名单方式。
  - `openCellDialog` 内 `inp-title` 与 `inp-code` 共用同一个 `modalKeyHandler`，统一 Enter 行为。
- `src/时间管理助手.html`：弹窗 kbd 提示行更新文案。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v12`。

---

## v2.7.2 — 2026-05-27（修复 Excel 选区交互 + 操作反馈）

针对 v2.7.1 反馈「快捷键只能单格操作，希望复制后选区直接粘贴 / 删除」。

实际逻辑早已支持选区批量；问题出在事件竞争：之前 `mousedown`（拖动选区）与 `click`（单击重置选区）同时绑定，鼠标抬起后 click 紧接触发，会把刚刚拖出的选区瞬间收回为单格。

### 修复

- 桌面端**只用 `mousedown`** 处理选区初始化、Shift 扩展、拖动扩展；移除 `click` 事件，避免选区被覆盖。
- 移动端（`pointer: coarse`）保留 `click` → 直接打开编辑弹窗。
- 双击 / Enter / F2 仍可进入编辑弹窗。
- 选区拖动时 `mousedown` 调 `e.preventDefault()`，避免拖选误触发系统文本选择。

### 操作反馈

- Ctrl+C → toast「已复制：xxx 1.3」
- Ctrl+V → toast「已粘贴到 N 格」
- Delete → toast「已清空 N 格」
- Ctrl+V 时若剪贴板为空 → toast「请先 Ctrl+C 复制」

### 文件改动

- `src/app.js`：重写 `bindCellClicks`（移除 click 与 mousedown 冲突）；新增 `showToast`；`copySelectionToClipboard / pasteClipboardToSelection / deleteSelection` 全部接 toast 反馈。
- `src/styles.css`：新增 `.toast` / `.toast-show` 样式。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v11`。

---

## v2.7.1 — 2026-05-27（Excel 风格选区 + 网格快捷键）

针对 v2.7.0 后用户反馈「操作麻烦，希望像 Excel 一样直接快捷键复制粘贴 / 删除 / 向下填充」。

### 网格交互升级（桌面端）

- **单击日程格 = 选中（不再开弹窗）**；选中时蓝色高亮 + 半透明蒙层。
- **双击 = 进入编辑弹窗**；按 `Enter` 或 `F2` 也可进入编辑。
- **Shift + 单击** 或 **鼠标按下并拖动** = 矩形选区，跨日跨时段批量操作。
- **方向键** 移动选区焦点；`Shift + 方向键` 扩展选区。
- **Esc** 取消选区或关闭弹窗。

### Excel 式快捷键（直接作用于选区）

- **Ctrl + C**：复制选区起点格内容到剪贴板（跨弹窗共用）。
- **Ctrl + V**：把剪贴板内容粘贴到选区**所有**格。
- **Ctrl + D**：选区内向下填充——每列以**第一行**作为源，向下复制到选区下方所有行（与 Excel 完全一致）。
- **Delete / Backspace**：清空选区所有格。

### 移动端兼容

- 移动设备（`pointer: coarse`）保持原有「单击 = 直接编辑」行为，不引入选区机制。
- 网格上方的快捷键提示条在移动端自动隐藏。

### 文件改动

- `src/app.js`：
  - 新增 `selection` 模块状态与 `getSelectionRange / forEachSelectedId / applySelectionStyles`。
  - 新增 `copySelectionToClipboard / pasteClipboardToSelection / deleteSelection / fillDownSelection / moveSelection`。
  - `bindCellClicks` 重写：单击=选中 / 双击=编辑 / 鼠标拖动=矩形选区。
  - 全局 `keydown`：Enter/F2 进入编辑、Ctrl+C/V/D、Delete、方向键。
  - 模块级 `currentDateKeys` 暴露给选区计算；`renderAll()` 末尾自动 `applySelectionStyles()`。
- `src/styles.css`：选区样式增强；新增 `.grid-hint` 顶部提示条；禁用日程格文本选择以防止拖选误触。
- `src/时间管理助手.html`：表格上方新增快捷键提示条；弹窗底部提示行同步更新。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v10`。

---

## v2.7.0 — 2026-05-27（核心层抽取 + 单元格录入提速）

### 架构重构

- 新增 `src/app-core.js`，集中管理：
  - 常量（`STORAGE_PREFIX / WEEKDAYS / KEY_ROWS / TIME_SLOTS / DEFAULT_CONFIG`）
  - ISO 周计算（`getISOWeek / getWeekDates / formatDate / dateKey / getPrevWeek / getNextWeek`）
  - LocalStorage 存取（`getCells / saveCells / getKeyItems / saveKeyItems / getReview / saveReview / getConfig / saveConfig / isArchived / setArchived`）
  - 分类与统计（`getCatClass / calcDailyStats / calcWeeklyStats`）
- `src/app.js` 顶部用 `var` 别名引入 `AppCore.*`，保留 UI / 事件绑定逻辑，移除已抽出的 ~160 行重复代码。
- `src/时间管理助手.html`：`<script src="app-core.js">` 在 `<script src="app.js">` 之前。
- `src/service-worker.js`：`CACHE_NAME` 升到 `time-planner-v9`，预缓存清单加入 `app-core.js`。
- 此次重构与同步层无关，但为 §20.7 第三阶段（Windows 同步服务复用核心层）打好基础。

### 单元格录入体验改进

针对「Enter 自动跳下一格」与「批量填充太麻烦」两点反馈：

- **Enter 跳转**
  - 事件名输入框按 Enter → 焦点跳到分类代码框。
  - 分类代码框按 Enter → 保存当前格 + **自动打开同一天下一时段的弹窗**，焦点回到事件名输入框。
  - `Shift + Enter` → 保存并跳到上一时段。
  - 走到 `23:30-00:00` 后再 Enter，仅保存关闭，不跨日。

- **向下填充 N 格**
  - 弹窗新增 `向下填充 [N] 格` 数字框 + `保存并向下填充` 按钮。
  - N=1 等价于普通保存；N>1 时把同一份 `{title, code}` 写到接下来的 N-1 格，遇当日末尾自动截断。
  - 填充完成后焦点跳到第 N+1 格继续录入，无需手动逐格点击。

- **复制上一格**
  - `Ctrl + D`（桌面端）或弹窗内可绑定快捷动作 → 把上一时段的 `{title, code}` 拷贝到当前弹窗输入框。

- 弹窗底部新增键盘提示行（移动端自动隐藏）。

### 文件改动

- `src/app-core.js`：新建。
- `src/app.js`：核心层引用、`parseCellId / shiftCellId / fillFromPrevSlot / commitCurrentCell / saveCellAndAdvance / saveAndFillDown` 等新函数；`openCellDialog` Enter/Ctrl+D 行为重写。
- `src/时间管理助手.html`：弹窗新增「向下填充」行 + 键盘提示行；脚本加载顺序更新。
- `src/styles.css`：新增 `.fill-row` / `.kbd-hint` 样式。
- `src/service-worker.js`：缓存清单 + 版本升级。

---

## v2.6.1 — 2026-05-27（需求文档自查与一致性修复）

仅文档变更，不影响运行时代码。

### A. 数据结构与代码对齐（§14.3）

- 修正周 JSON 的 `cells` 键示例为 `"日期|时段"` 字符串（如 `"2025-12-01|07:00-07:30"`），与 `app.js` 实际格式一致。
- 修正 `keyitems` 键格式为 `"日期|关键事项行名"`（行名为 `第一件事 / 第二件事 / 第三件事 / 小确幸 / 关键词`），与 `app.js` 的 `KEY_ROWS` 常量一致。
- 新增「LocalStorage 与同步 JSON 字段映射」说明，明确同步层负责包装 `{ value, updatedAt, updatedBy }`。

### B. DailyStats 字段补全（§12.4）

- 补全 `filled / qwDetail / gfpDetail / procDetail / validInvest / invalidWaste / checkTotal / checkLoss / checkInvest` 字段。
- 补充字段语义说明与公式对照。

### C. 当日汇总 / 当日校验 拆分一致性（§20.3 / §20.9）

- 章节正文将原「当日校验区」的 8 项，正式拆分为：
  - 当日汇总区：有效投资 / 无效浪费 / 潜力总数 / 标准数 / 可用数。
  - 当日校验区：校验总数 / 校验亏损 / 校验投资。
- §20.3 中将「建议……作为两个独立分组」改为「**必须**……」。
- §20.9 中「红框外只读区域」列表同步更新为五个分组。

### D. 校验描述对称化（§6.3）

- §6.3 GFP 明细补充 `2.1+2.2+2.3+2.4+2.5 = GFP 总数` 的校验项，与 §7 的 QW 校验和 §10 校验投资公式保持对称。

### E. 移动端验收补全（§16.4）

- 新增四条验收：
  - 顶部「单日 / 本周累计」切换条。
  - 当日明细按编码顺序全部展示 + 分组小计。
  - 当日汇总与当日校验作为两个独立分组。
  - 本周累计页本周填写进度三项独立显示（应填写 / 已填写 / 剩余）。

---

## v2.6.0 — 2026-05-26（公式更正：有效投资 = QW + GFP）

### 公式更正

- **有效投资定义更正**：`有效投资 = QW + GFP`（原为 `有效投资 = QW`）。
- 与「赚 = QW + GFP」在数值上相等；二者视角不同：「赚」为收益台账视角，「有效投资」为时间投资视角。
- `校验投资`、`校验亏损`、`校验总数` 公式不变。

### 代码变更

- `src/app.js`：`s.validInvest` 计算改为 `s.qw + s.gfp`。
- `src/service-worker.js`：`CACHE_NAME` 升级到 `time-planner-v7`，强制刷新缓存。

### 文档变更

| 文件 | 说明 |
|---|---|
| `需求文档.md` §8.1 | 有效投资定义改为 `QW + GFP`，补充与「赚」的关系说明 |
| `需求文档.md` §20.3 | 手机端有效投资公式同步更正 |
| `需求文档.md` 附录 | 公式速查 `有效投资 = QW_count + GFP_count` |
| `手机版单日填写静态图-v6.svg` | 当日汇总「有效投资」更正为 19（=QW 16 + GFP 3） |

---

## v2.5.0 — 2026-05-26（手机端可编辑范围明确）

### 需求设计

- **明确手机端可编辑范围**：手机版单日界面中，仅截图红框内区域允许编辑。
- **红框内可编辑内容**：关键事项区（第一件事、第二件事、第三件事、小确幸、关键词）和 7:00-00:00 半小时日程填写区。
- **红框外只读计算**：当日统计、赚/赔/结余、GFP 明细、QW 明细、无效浪费明细、有效投资、潜力/标准/可用、校验区均不可手工编辑。
- **自动刷新要求**：用户修改红框内任一内容后，系统自动刷新红框外所有统计、明细和校验结果。

### 文档变更

| 文件 | 说明 |
|---|---|
| `需求文档.md` | 明确手机端红框内可编辑、红框外只读自动计算 |
| `README.md` | 同步手机端可编辑范围说明；版本表加入 v2.5.0 |
| `CHANGELOG.md` | 新增 v2.5.0 更新记录 |

---

## v2.3.0 — 2026-05-26（手机端单日竖向填写与前一日补齐）

### 需求设计

- **明确手机端填写界面**：iPhone 版与华为安卓版不再以完整周横向表作为主填写界面，而是采用单日竖向填写表。
- **明确单日界面结构**：顶部日期 + 关键事项 + 7:00-00:00 半小时日程 + 当日统计 + 当日明细 + 当日校验。
- **明确前一日补齐规则**：手机端每次打开时先检查前一日是否完成；若前一日未完成，必须先补齐前一日，校验通过后才能回到今日。

### 手机端界面

- 顶部显示第几周、星期、日期。
- 关键事项区显示第一件事、第二件事、第三件事、小确幸、关键词。
- 日程区按 30 分钟一行显示 7:00-00:00。
- 每行显示时间段、事件名称、分类代码，并按代码着色。
- 下方显示当日统计、赚/赔/结余、GFP 明细、项目投入、无效浪费明细、有效投资、潜力/标准/可用、校验区。

### 前一日补齐流程

- 手机端打开时计算今日与前一日。
- 若前一日 `校验总数 !== 0`，进入「请先补齐前一日」模式。
- 补齐模式下日期固定为前一日，当日填写入口锁定。
- 当前一日 `校验总数 = 0`、`校验亏损 = 0`、`校验投资 = 0` 后，允许回到今日填写。
- 若连续多日未填写，后续实现应从最早未完成日期逐日推进补齐。

### 文档变更

| 文件 | 说明 |
|---|---|
| `需求文档.md` | 更新移动端验收；更新 iPhone/华为设计；新增 `20.9 手机端单日填写与前一日补齐规则` |
| `README.md` | 更新 iPhone/华为手机版说明；版本表加入 v2.3.0 |
| `CHANGELOG.md` | 新增 v2.3.0 更新记录 |

---

## v2.2.0 — 2026-05-26（Windows 配置主导与新周开启规则）

### 需求设计

- **明确配置权归属**：所有周配置仅允许在 Windows 桌面版完成；iPhone 版与华为安卓版不提供配置编辑功能。
- **明确配置共享方式**：手机端只读取 Windows 版已确认配置，包括 QW 项目名称、GFP 子类名称、标准数。
- **明确新周开启规则**：每周一首次进入新周时，必须先在 Windows 版完成「本周配置确认」，确认后才允许三端进入该周填写。

### Windows 桌面版规则

- 每周一首次进入新周时，检测本周配置是否已确认。
- 若未确认，显示「本周配置确认」界面。
- 默认带入上一周配置。
- 用户可以选择：
  - 延续上一周配置；
  - 修改后确认；
  - 暂不确认。
- 只有点击「确认延续/确认配置」并写入 `configConfirmed = true` 后，才允许开启新周填写。

### iPhone / 华为手机版规则

- 手机端不提供配置编辑页。
- 手机端进入某周时，先检查 `configConfirmed`。
- 如果本周尚未由 Windows 版确认配置：
  - 日程格不可编辑；
  - 关键事项不可编辑；
  - 周复盘不可编辑；
  - 提示「请先在 Windows 版完成本周配置并确认延续」。
- 如果本周已确认配置，则手机端正常填写，并使用 Windows 版共享配置。

### 文档变更

| 文件 | 说明 |
|---|---|
| `需求文档.md` | 新增 `20.8 每周配置确认与新周开启规则`；补充配置页和三端规则 |
| `README.md` | 补充 Windows 配置确认与手机只读配置说明；版本表加入 v2.2.0 |
| `CHANGELOG.md` | 新增 v2.2.0 更新记录 |

---

## v2.1.0 — 2026-05-26（三端分版设计明确）

### 需求设计

- **明确三端分版设计方向**：应用按 Windows 桌面版、iPhone 手机版、华为安卓手机版三套体验进行设计。
- **确定共用业务核心**：三端共用同一套 LocalStorage 数据结构、ISO 周计算、分类代码、统计公式、校验逻辑、归档导出逻辑。
- **确定表现层分离策略**：第一阶段保留单入口 `时间管理助手.html`，通过 CSS media query + JS 设备模式切换实现不同端体验；第二阶段如复杂度上升，可拆分为 Windows / iPhone / Huawei 三个入口，共用核心逻辑。

### Windows 桌面版

- 维持三栏布局：左侧本周累计 + 中间完整 Excel 风格表格 + 右侧周复盘。
- 以鼠标键盘为主，保留 `Ctrl+C` / `Ctrl+V` / `Delete` / `Enter` 等快捷键。
- 强调信息密度和完整表格呈现。

### iPhone 手机版

- 使用单栏/分 Tab 设计：日程、统计、复盘、配置。
- 不直接照搬桌面三栏宽表格。
- 继续使用自定义 modal，不使用 `<dialog>` / `prompt()`。
- 强化 iPhone Safari、PWA 主屏、刘海屏、软键盘适配。

### 华为安卓手机版

- 使用单栏/分 Tab 设计，接近 iPhone 版。
- 重点兼容安卓浏览器下载能力、返回键行为、横向表格滚动性能。
- Excel 导出按浏览器下载到默认下载目录处理。

### 文档变更

| 文件 | 说明 |
|---|---|
| `需求文档.md` | 新增第 20 章「三端分版设计规范」；更新移动端验收标准 |
| `README.md` | 新增「三端设计策略」章节；版本表加入 v2.1.0 |
| `CHANGELOG.md` | 新增 v2.1.0 更新记录 |

---

## v2.0.0 — 2026-05-26（移动端全面修复）

### 🔴 致命问题修复

- **弹窗系统重构**：将原生 `<dialog>` 元素完全替换为基于 `<div>` 的自定义模态框（`modal-overlay` + `modal-box`）。原因：`<dialog>` 及 `showModal()` 在 iOS 15.4 以下（大量 iPhone 机型）不受支持，导致单元格完全无法编辑。
- **触控编辑改为单击触发**：移除 `dblclick` 事件（移动端不可靠，iOS Safari 将双击识别为缩放手势），改为**单击格子直接打开编辑弹窗**。
- **关键事项编辑去除 `prompt()`**：将「第一件事、第二件事…」等关键事项的编辑方式从 `window.prompt()` 改为独立的 `ki-modal` 弹窗。原因：`prompt()` 在 iOS PWA 独立模式（添加到主屏幕后）会被系统屏蔽。

### 🟠 严重问题修复

- **软键盘适配**：弹窗采用 `position: fixed; top: 0; overflow-y: auto`，内部表单限高 `max-height: 90dvh`，软键盘弹出后内容仍可滚动，不会被遮挡。
- **iOS 主屏图标修复**：新增 `icon-192.png`（192×192 PNG），`apple-touch-icon` 改为指向 PNG；原 SVG 仅作补充。iOS 不支持 SVG 格式的主屏图标。
- **iOS Safari 视口高度修复**：`.main-layout` 高度由 `calc(100vh - 52px)` 改为 `calc(100dvh - 52px)`（动态视口高度），修复 iOS Safari 中 `100vh` 包含地址栏导致底部统计区被截断的问题，旧版浏览器自动回退到 `100vh`。

### 🟡 中等问题修复

- **消除 300ms 点击延迟**：全局添加 `touch-action: manipulation`，移动端浏览器不再等待双击判断。
- **触控目标尺寸**：日程格 `min-height` 从约 22px 增大至 36px，接近 Apple 推荐的 44pt 最小触控尺寸。
- **移动端复制粘贴**：弹窗内新增「复制此格」「粘贴」按钮（仅在触控设备 `pointer: coarse` 时显示），替代键盘 `Ctrl+C/V`。
- **离线导出保障**：Service Worker 缓存列表加入 XLSX CDN 地址，首次联网后即可离线归档导出，缓存版本升至 `v6`。
- **代码输入框优化**：分类代码输入框加 `inputmode="decimal"`，移动端弹出数字键盘而非全键盘。

### 🔵 PWA 细节修复

- **viewport-fit=cover**：视口 meta 加入 `viewport-fit=cover`，支持 iPhone 刘海屏 / Dynamic Island 全面屏适配。
- **Safe Area 内边距**：`body` 加 `padding-bottom: env(safe-area-inset-bottom)` 防止 Home 条遮挡底部内容。
- **manifest.json**：添加 PNG 图标条目；`orientation` 改为 `any`，允许横屏使用。
- **旧 iOS 滚动**：表格容器加 `-webkit-overflow-scrolling: touch` 兼容 iOS 12 及以下的惯性滚动。
- **ESC 键支持**：弹窗打开时按 ESC 可关闭（桌面端体验改善）。
- **点击遮罩关闭**：点击弹窗背景遮罩可关闭弹窗。

### 文件变更

| 文件 | 变更类型 | 说明 |
|---|---|---|
| `src/时间管理助手.html` | 修改 | dialog→div modal；viewport-fit；apple-touch-icon PNG；ki-modal |
| `src/styles.css` | 修改 | modal-overlay/modal-box；touch-action；dvh；safe-area；行高；移动端粘贴按钮 |
| `src/app.js` | 修改 | openModal/closeModal；单击编辑；ki-modal；复制粘贴按钮；ESC支持 |
| `src/manifest.json` | 修改 | PNG图标；orientation:any |
| `src/service-worker.js` | 修改 | v6缓存；预缓存XLSX CDN；加入icon-192.png |
| `src/icon-192.png` | 新增 | 192×192 PNG图标（蓝色背景） |

---

## v1.0.0 — 2026-05-25（初版完成）

- 完整周计划表格（ISO 周、7 列、34 时间格）
- 每日关键事项 5 行
- 分类代码系统（0/1.x/2.x/3.x/4 五大类）
- 自动着色（5 种分类颜色）
- 底部统计区全部计算逻辑
- 左侧本周累计面板
- 右侧周复盘 10 项
- 配置页（QW/GFP 自定义名称、标准数）
- 确认归档 → 导出 `.xlsx`（SheetJS）
- LocalStorage 本地存储
- Service Worker 离线缓存（v5）
- 键盘快捷键 Ctrl+C/V/Delete、Enter 保存
