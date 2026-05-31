# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

时间管理助手是一个仿 Excel 周计划表的 PWA 应用，支持 Windows 桌面 + iPhone + 华为安卓。核心是 7 天 × 34 半小时格的时间表，搭配分类代码系统（0=Rest, 1.x=QW, 2.x=GFP, 3.x=Proc, 4=MW）进行自动统计与着色。

## 启动方式

```powershell
# 一键启动（静态 6371/6443 + 同步 6372/6444）
.\启动服务器.bat

# 或分别启动
node src\server.js          # 静态服务：HTTP 6371 + HTTPS 6443
node sync-server.js         # 同步服务：HTTP 6372 + HTTPS 6444
```

- 电脑访问：`http://127.0.0.1:6371/` 或 `https://127.0.0.1:6443/`
- 同 Wi-Fi 手机：`https://<电脑名>.local:6443/`
- HTTPS 依赖 `certs/` 目录下的证书（首次运行 `cd tools\gen-cert && npm install && node gen-all.js`）

## 架构

```
浏览器端                        Node.js 服务端
┌─────────────────────────┐   ┌──────────────────────────┐
│ 时间管理助手.html (入口) │   │ src/server.js            │
│ ┌─────────────────────┐ │   │ 静态文件服务              │
│ │ app-core.js         │ │   │ HTTP 6371 + HTTPS 6443   │
│ │ 数据层 + 同步客户端  │ │   │ 含 CA 证书下载路由        │
│ │ (window.AppCore)    │ │   └──────────────────────────┘
│ └────────┬────────────┘ │   ┌──────────────────────────┐
│ ┌────────┴────────────┐ │   │ sync-server.js           │
│ │ app.js              │ │   │ 同步 API + WebSocket     │
│ │ UI 层（桌面+移动端） │─┼──▶│ HTTP 6372 + HTTPS 6444   │
│ │ 不在 app-core 中    │ │   │ 数据持久化到 sync-data/   │
│ └─────────────────────┘ │   │ 自实现 RFC6455 WSS       │
│ ┌─────────────────────┐ │   └──────────────────────────┘
│ │ service-worker.js   │ │
│ │ cache-first SWR     │ │
│ │ 离线启动与缓存       │ │
│ └─────────────────────┘ │
│ LocalStorage            │
│ (tm_YYYY_wNN_*)         │
└─────────────────────────┘
```

### 分层职责

- **`app-core.js`** (~1300 行)：纯数据层，无 DOM 操作。导出 `window.AppCore`，包含：
  - 常量（`WEEKDAYS`, `KEY_ROWS`, `TIME_SLOTS`, `DEFAULT_CONFIG`）
  - ISO 周计算（`getISOWeek`, `getWeekDates`, `getPrevWeek`, `getNextWeek`）
  - LocalStorage CRUD（`getCells/saveCells`, `getKeyItems/saveKeyItems`, `getConfig/saveConfig`, `getReview/saveReview`, `getKeyItemStatus/saveKeyItemStatus`）
  - 统计计算（`calcDailyStats`, `calcWeeklyStats`）
  - JSON 导出/导入（`exportAllData`, `importAllData`）
  - 同步客户端 `syncClient`：推送/拉取/心跳/WebSocket/离线队列/配对绑定
  - `onSaveChange` 事件机制：每次 `save*` 后触发，syncClient 订阅以实现保存即推送

- **`app.js`** (~2600 行)：纯 UI 层。启动时从 `AppCore` 解构所有数据函数，负责：
  - 桌面端周表渲染（三栏：左侧累计 + 中间表格 + 右侧复盘）
  - 移动端单日填写视图 + 本周累计视图
  - 弹窗编辑（日程格、关键事项、配置、同步面板）
  - 快捷键（Ctrl+C/V/D/Z、Delete、方向键）
  - Excel 导出（使用 `xlsx-js-style` CDN 库，逐 cell 构造并着色）
  - 冻结表头、月历视图（v2.13.1）

- **`sync-server.js`** (~750 行)：零 npm 依赖的同步 API 服务器。端点包括：
  - `GET /info` — 主机信息
  - `GET /weeks` — 列出所有周
  - `GET /weeks/:y/:w` — 拉取整周快照
  - `POST /weeks/:y/:w/changes` — 上传变更（LWW 按 `updatedAt` 合并）
  - `WSS /events` — WebSocket 变更广播（自实现 RFC6455 握手与帧编解码）
  - `POST /pair/start`, `/pair/confirm`, `/pair/register-desktop` — 设备配对绑定
  - `GET /devices`, `DELETE /devices/:id` — 设备管理
  - 数据持久化到 `sync-data/<year>/wNN.json`，原子写入（先 `.tmp` 再 rename）

### 数据流

1. **填写**：用户在日程格中输入"事件名 | 分类代码" → `saveCells()` → `_emitSaveChange('cells')` → syncClient 的 `_handleSaveChange` 更新 meta 的 `updatedAt` → debounce 1.5s 后 `pushWeek()`
2. **同步**：`pushWeek` 将本地 cells/keyitems/review/config 包装为 `{value, updatedAt, updatedBy}` 格式 POST 到服务端 → 服务端 `mergeChanges` 按 LWW 逐个字段合并 → 写入 JSON 文件 → `wsBroadcast` 通知其他客户端
3. **拉取**：收到 WebSocket `week-changed` 或手动点拉取 → `pullWeek` → `_applyServerWeekToLocal` 逐 cell/keyitem 按 `updatedAt` 比较，服务端版本 ≥ 本地时才覆盖
4. **离线**：push 失败时自动入队到 `tm_sync_pending_queue`（去重），回到在线时由 `online` 事件 / `visibilitychange` / 启动时自动 `flushOfflineQueue` 串行补推

### localStorage Key 体系

| Key 模式 | 内容 |
|---|---|
| `tm_YYYY_wNN_cells` | `{ "日期|时段": {title, code} }` |
| `tm_YYYY_wNN_keyitems` | `{ "日期|行名": "值" }` |
| `tm_YYYY_wNN_keyitemStatus` | `{ "日期|行名": "done|ongoing|todo" }` |
| `tm_YYYY_wNN_review` | `{ keyword, selfScore, ... }` |
| `tm_YYYY_wNN_config` | `{ qwNames[], gfpNames[], procNames[], standard, startTime }` |
| `tm_YYYY_wNN_archived` | `"1"` 或不存在 |
| `tm_YYYY_wNN_syncmeta` | `{ cells:{}, keyitems:{}, ... }` — 每个字段的 `updatedAt` 时间戳 |
| `tm_sync_config` | `{ enabled, autoHost, hostname, port, ... }` |
| `tm_device_id` | 设备 UUID |
| `tm_device_token` | 配对后获得的令牌 |
| `tm_sync_pending_queue` | `[{year, week, queuedAt}]` |

### 证书架构

`tools/gen-cert/` 使用 `node-forge` 纯 JS 生成 CA + leaf 两层证书：
- **CA**（10 年）：一次性安装到 iPhone「证书信任设置」
- **leaf**（2 年）：由 CA 签发，SAN 包含 localhost / 127.0.0.1 / `<主机名>.local` / 当前 LAN IP
- 更换 IP 或主机名时只需重跑 `node gen-leaf.js`，iPhone 无需重装 CA
- 服务端读 `leaf-cert-chain.pem`（leaf + CA 拼接），客户端通过 chain 验证

## 开发注意事项

- 修改 `app-core.js` 的数据存取逻辑后，需同步检查 `sync-server.js` 的 `mergeChanges` 是否也需要更新对应字段
- Service Worker 版本号（`CACHE_NAME`）在每次发布前递增，配合 `app.js` 中的 `EXPECTED_CACHE_NAME` 做版本自检
- 手机端仅红框内（关键事项区 + 日程区）可编辑，统计/校验/明细区只读自动计算
- 桌面端周配置（QW 名称、GFP 名称、起始时间、标准数）由 Windows 端确认，手机端只读共享
- 颜色规则：HTML 用 CSS class（`cat-rest`/`cat-qw`/`cat-gfp`/`cat-proc`/`cat-mw`），Excel 导出直接写 RGB 值
