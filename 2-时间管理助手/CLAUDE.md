# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

时间管理助手是一个仿 Excel 周计划表的 PWA 应用，支持 Windows 桌面 + iPhone + 华为安卓。核心是 7 天 × 34 半小时格的时间表，搭配分类代码系统（0.x=Rest, 1.x=QW, 2.x=GFP, 3.x=Proc, 4=MW）进行自动统计与着色。

### 分类编码（v105 起：四大类统一 10 个子类）

| 大类 | 编码 | 子类（配置字段） |
|---|---|---|
| Rest 休息 | 0.1~0.9、0.0 | 睡觉/吃喝/散步/出行/刷手机/卫生/游戏/社交/发呆/放空 + 0.0 其他 |
| QW | 1.1~1.9、1.0 | AI/心理咨询/**读书(1.3)**/**注会变现(1.4)**/投资/自我管理，1.7~1.9 空位停用，1.0 其他 |
| GFP | 2.1~2.9、2.0 | 影片/运动/社交/旅行/游戏/小资/钢琴/演出（v108：2.1 演出改名影片，2.8 新增演出），2.9 空位停用，2.0 其他 |
| Proc | 3.1~3.9、3.0 | 睡懒觉/刷手机/拖延/无效社交，3.5~3.9 空位停用，3.0 其他 |
| MW | 4 | 无子类 |

- 每类名称数组 `xNames` 固定 10 项，**下标 0~8 = x.1~x.9，下标 9 = x.0「其他」**；`xOn`（10 项布尔）为启用开关，下标 9 固定启用
- x.0 **存为数字 `0/1/2/3`**，显示用 `subCode(prefix, 9)` / `fmtCode()` 补 `.0`；录入 `1` / `1.0` 都合法。数字存储下 1.0 就是 1，所以 4 永远是 MW、不存在 4.x
- 停用只禁止新录入，历史格子照常统计；展示循环一律用 `visibleSubs(config, cat, detail)`，编码解析用 `codeToSub()`，不要再写死 7 / 8 / 9 / 5
- 旧配置（任意长度）读取时由 `normalizeConfigNames()` 自动展开为 10 项并补 `xOn`，「其他」移到下标 9
- **`DEFAULT_CONFIG` 必须与实际使用的配置一致**（v106 教训：旧默认 1.3 注会变现 / 1.4 读书与实际相反，回退默认时名称对调）。默认起始时间 9:00。用户改了子类名称时，同步改 `DEFAULT_CONFIG`
- 改配置结构 / 编码格式时，必须用**上一版代码**拉一次新数据，确认旧客户端不会改坏本地（WORKFLOW 需求5 第 6 步）
- v108 历史迁移（2026-10-09，`tools/migrate-v108-film-show.js`，13 格）：2.6 里的电影→2.1、w28 吃饭 2.1→2.3、去看电影 0.0→0.4，备份在 `backups/pre-v108-film-show-20261009-1922/`
- v105 历史迁移（2026-10-09，`tools/migrate-v105-ten-subcats.js`，95 格）：1.7→1.0、2.8→2.0、3.5→3.0，备份在 `backups/pre-v105-ten-subcats-20261009-1606/`
- v104：0.0 = 休息「其他」（存为 `0`）；不能用 0.10（会变成 0.1）
- 历史数据已于 2026-10-09 用 `tools/migrate-v104-piano-daze.js` 迁移（2.6 含「琴」→2.7、2.7→2.8、0.9 非发呆→0.0），备份在 `backups/pre-gfp-piano-rest-daze-20261009-1216/`
- 同名"刷手机"：`0.5` = 正常休息，`3.2` = 内耗，分析时必须区分
- 历史 w22-w40 的 code=0 已于 2026-09-29 用 `tools/migrate-rest-subcat.js` 迁移，迁移前备份在 `backups/pre-rest-subcat-20260929-1300/`

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
  - 统计计算（`calcDailyStats`, `calcWeeklyStats`），明细数组 `qwDetail` / `gfpDetail` / `procDetail` / `restDetail` 均为 10 项（v105，下标 9 = x.0）
  - JSON 导出/导入（`exportAllData`, `importAllData`）
  - 同步客户端 `syncClient`：推送/拉取/心跳/WebSocket/离线队列/配对绑定；`pullAllWeeks()`（v99）串行拉取服务端全部周
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
| `tm_YYYY_wNN_config` | `{ qwNames[], gfpNames[], procNames[], restNames[], standard, startTime }`（旧周无 `restNames` 时 `getConfig` 读取补默认值） |
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
- **Service Worker 版本号同步**：修改 `service-worker.js` 的 `CACHE_NAME` 时，**必须同步修改** `app.js` 中的 `EXPECTED_CACHE_NAME`，否则 3 秒版本自检发现不匹配会触发 `window.location.reload()` 无限循环
- 手机端仅红框内（关键事项区 + 日程区）可编辑，统计/校验/明细区只读自动计算
- 桌面端周配置（QW 名称、GFP 名称、起始时间、标准数）由 Windows 端确认，手机端只读共享
- 颜色规则：HTML 用 CSS class（`cat-rest`/`cat-qw`/`cat-gfp`/`cat-proc`/`cat-mw`），Excel 导出直接写 RGB 值
- **iOS 同步协议**（v2.13.2 修正）：iOS 不再强制 HTTP。页面用 HTTPS 访问时同步也走 HTTPS 6444 端口，避免 Mixed Content 阻塞。`getEffectiveProtocol()` 已改为跟随页面协议，新增网络请求时保持此逻辑
- **新周配置继承**：`getConfig()` 在新周无配置时，用 `findLatestConfigBefore()` 沿用此前最近一个有配置的周（隔空周、跨年都能找到）并保存；本机一份配置都没有时才用 `DEFAULT_CONFIG`（v106）
- **心跳自动拉取**：30s 心跳 ping `/info` 后会自动 pull 当前周数据（v2.13.1），作为 WebSocket 断开时的兜底
- **切周自动拉取**（v100）：`renderAll()` 末尾的 `syncViewedWeek()` 在查看的周变化时 `setCurrentWeek` + `pullWeek`，心跳也随之跟随当前查看的周；首次渲染不拉，交给启动流程（先 flush 离线队列）
- **改分类编码 / 批量改历史数据**：按 WORKFLOW.md 需求5 执行（备份 → dry-run → apply → 逐格对比 → 客户端拉取验证）。服务端改数据必须刷新 `cell.updatedAt` 和 `weekUpdatedAt`，否则客户端 LWW 合并会忽略
- **新增编码的消费点**：`validateCode`、`calcDailyStats`、桌面统计表、左栏、移动端明细、配置页、Excel 导出、周对比（两处行列表）、`review-engine.calculateStats` 与日程格事件汇总、`review-ui.getCodeLabel` 与周对比明细，缺一处就会漏统计。v105 起这些点都走 `codeToSub` / `visibleSubs` / `subCode`，改编码规则优先改这三个函数
- **拉取数据变化判断**：`_applyServerWeekToLocal` 通过 `serverWeekUpdatedAt` 快速跳过无变化数据，返回 `false` 时不触发 UI 刷新，避免页面频繁重绘
- **Cache-Control 与 SW 的互斥**（v2.13.2 重要教训）：`Cache-Control: no-store` 会阻止 Service Worker Cache API 存储响应（iOS Safari 严格遵守）。服务器必须用 `public, max-age=0` 才能让 SW 缓存正常工作。SW 中 `sanitizeForCache()` 额外剥离限制性头以防万一
- **SW 拦截范围**（v101）：fetch 事件只接管同源静态资源和 `CDN_HOSTS` 白名单；同步 API（`SYNC_API_RE`：/weeks /info /devices /pair /events，或带 `X-Device-Token` 的请求）一律直连网络。`cache.put` 前必须 `resp.clone()`，因为 `sanitizeForCache` 会接管 body，不 clone 会让页面读不到响应。新增 CDN 依赖时要加进 `CDN_HOSTS`，否则离线不可用
- **同步关闭也要打时间戳**（v102）：`_handleSaveChange` 不能因为 `!cfg.enabled` 提前 return，否则关闭期间的修改会带着旧 `updatedAt` 推上去，对端 LWW 判定“不新”后跳过。只有 `_schedulePush` 受开关控制
- **lanIPs 顺序**（v103）：客户端把 `/info` 返回的 `lanIPs[0]` 存为 `lastIP`，`getLanIPs()` 必须保证真实局域网 IP 排第一（私有网段 + 物理网卡优先，VPN/虚拟网卡垫底，169.254 过滤）
- **sync-server 鉴权里改设备字段**（v101）：必须在 `authenticate` 已加载的同一份 `data.devices` 中查找并修改，再 `saveDevices(data)`；`findDeviceByToken` 会重新读文件，只能用于只读查询

## 常见问题排查

### 同步不工作
1. 确认两个服务器都在运行（`netstat -ano | grep 6372`）
2. 确认同步面板「启用局域网同步」已勾选并保存
3. 确认「尝试 URL」显示正确的地址（桌面 `http://127.0.0.1:6372`，iPhone 自动跟随页面协议：HTTPS 页面走 `https://<LAN IP>:6444`）
4. **先清 Service Worker 缓存**（`sw-cleanup.html` 或 DevTools Unregister），否则旧代码可能还在运行
5. 检查服务端数据：`curl http://127.0.0.1:6372/weeks`
6. 检查 `sync-data/` 目录下 JSON 文件是否有数据
7. **iPhone Mixed Content**：如果页面 HTTPS 但同步走 HTTP，Safari 会阻止——确保 `getEffectiveProtocol()` 跟随页面协议（v2.13.2 已修复）

### iPhone 同一 Wi-Fi 下连不上（v103）
先看手机日志的报错类型，两种原因排查方向不同：
- **`timeout`**：地址不通。核对手机填的 IP 是不是 `ipconfig` 里 **WLAN** 那行。电脑装了 Radmin VPN（`26.104.213.44`），它不是局域网地址；v103 前 `/info` 的 lanIPs 会把 VPN 排第一，手机被自动回填成 VPN 地址
- **`Load failed`**：证书不含该地址。查 SAN：`openssl x509 -in certs/leaf-cert-chain.pem -noout -text | grep -A1 "Subject Alternative"`；不含当前 IP 就跑 `node tools/gen-cert/gen-leaf.js`，再重启两个服务（CA 不变，iPhone 不用重装）
- gen-leaf 只写**当前**网卡 IP，换回旧网络要重签
- ⚠️ v103「保存并连接」成功后会记住电脑名，之后先试 `.local`；但 `_tryFetch` 不记成功的地址，iOS 解析不了 `.local` 时每次请求白等最多 8s。修复前（截至 v107 仍未修），手机直接填 IP，不点「保存并连接」（详见 BUG_FIX_LOG.md v103「已知隐患」）
- 防火墙已有入站规则「时间管理助手」（TCP 6443/6444），一般不用再动

### 服务端数据已改，但历史周仍显示旧数据
- 先确认版本 ≥ v100（v99 及以前切周不拉取，只有本周/上周会自动同步）
- 同步面板点「⬇ 拉取全部周」强制同步所有周
- 拉取全部周大量失败 → 看面板「首个失败原因」（v101 起）；确认版本 ≥ v101（v100 及以前 SW 会拦截同步 API 导致失败）；再用手机令牌直连服务端，排除服务端问题
- 仍不更新 → 检查服务端对应 cell 的 `updatedAt` 是否大于本地 `tm_YYYY_wNN_syncmeta.cells[key]`

### 页面频繁刷新
- Service Worker `CACHE_NAME` 与 `EXPECTED_CACHE_NAME` 不一致 → 3 秒自检强制 reload
- 心跳拉取总是触发 `renderAll` → 检查 `_applyServerWeekToLocal` 是否正确返回 `false`

### 二维码不显示
- 确认 `src/qrcode-generator.js` 存在（v2.13.1 已本地化，不依赖 CDN）

### iPhone 离线打不开
1. 检查 `Cache-Control` 响应头：必须是 `public, max-age=0` 或类似允许缓存的头，**绝不能**是 `no-store`
2. 确认 SW 已注册且版本匹配（`CACHE_NAME` = `EXPECTED_CACHE_NAME`）
3. 确认 SW install 阶段缓存了 HTML 文件（检查 `Promise.allSettled` 结果）
4. 用 Safari Web Inspector 查看 Cache Storage 是否有 `time-planner-vXX` 条目
5. **先在线访问一次并下拉刷新**，让 SW 填充缓存，再切飞行模式测试

### iPhone 同步面板秒关
- Service Worker 无限重载循环 → 用 `sw-cleanup.html` 清理
- 心跳频繁触发 `renderAll` → 检查数据变化判断逻辑

## 复盘中心开发红线（🚨 不可违反）

复盘中心是**桌面专用**功能，**严禁影响手机端**主应用的任何功能。这是项目的核心约束，违反即为失败。

### 红线 1：平台隔离 - 绝对红线

- ✅ **仅桌面端可用**：复盘中心只能在 Windows/Mac 浏览器访问
- ❌ **严禁影响手机端**：任何改动不得影响 iPhone/安卓的时间管理助手功能
- ⚠️ **验证机制**：每次改动后必须在手机端测试基本功能（填表、保存、同步、离线启动）

### 红线 2：架构隔离 - 完全独立

```
复盘中心（review-center.html）
  - 独立 HTML 页面
  - 独立 JS 文件（review-engine.js, review-ui.js）
  - 独立路由（/review-center）
  - 只读数据，不写入 LocalStorage
  
时间管理助手（时间管理助手.html）
  - 主应用，读写 LocalStorage
  - 手机端 + 桌面端
  - Service Worker 缓存
```

### 红线 3：数据关系 - 只读访问

- 复盘中心 **只读** LocalStorage 中的时间管理数据（`tm_YYYY_wNN_*` 系列 key）
- 复盘中心 **不修改** 任何主应用使用的 key
- 复盘中心可以有自己的存储 key（如 `tm_longterm_goals`, `tm_review_*`），但与主应用完全隔离

### 红线 4：Service Worker 隔离 - 已实现

```javascript
// service-worker.js lines 132-138 已有的隔离代码
if (url.origin === location.origin) {
  if (url.pathname.includes('review-center')
      || url.pathname.includes('review-engine')
      || url.pathname.includes('review-ui')) {
    return; // 复盘中心完全不走 SW，不缓存，不离线
  }
}
```

- 复盘中心文件不会被 Service Worker 缓存
- 复盘中心离线不可用（桌面端必然在线，无需离线支持）
- 手机端即使误访问复盘中心也不会影响 SW 缓存

### 红线 5：手机端入口隔离

```css
/* styles.css - 手机端隐藏复盘中心按钮 */
@media (max-width: 768px) {
  #btn-review-center { display: none !important; }
  #btn-week-compare { display: none !important; }
}
```

- 主应用只在**桌面端**工具栏显示"📊 复盘中心"按钮
- 手机端通过 CSS 媒体查询完全隐藏该按钮
- 即使手机端直接访问 URL，也只是复盘中心自己打不开，不会影响主应用

### 开发流程约束（强制执行）

**每次修改复盘中心代码后，必须执行以下步骤**：

1. **修改前检查红线清单**：
   - [ ] 修改是否只涉及 `review-center.html` / `review-engine.js` / `review-ui.js`？
   - [ ] 是否保证不修改 `app.js` / `app-core.js`？
   - [ ] 是否保证不写入 `tm_YYYY_wNN_*` 系列 LocalStorage key？
   - [ ] 是否保证 Service Worker 不缓存复盘中心文件？
   - [ ] 手机端是否看不到复盘中心入口？

2. **桌面端测试**：复盘中心功能正常

3. **手机端测试（强制执行，缺一不可）**：
   - [ ] 填表正常
   - [ ] 保存正常
   - [ ] 同步正常
   - [ ] 离线启动正常
   - [ ] 无新增报错

4. **如果手机端任何一项异常** → **立即回退代码**

### 禁止行为（违反即失败）

- ❌ 在 `app.js` / `app-core.js` 中添加复盘中心相关代码
- ❌ 在 `时间管理助手.html` 中引用 `review-*.js` 文件
- ❌ 修改 `tm_YYYY_wNN_*` 开头的 LocalStorage key 结构
- ❌ 让 Service Worker 缓存复盘中心文件
- ❌ 在手机端显示复盘中心入口按钮
- ❌ 修改复盘中心代码后不测试手机端主应用

### 验收标准

复盘中心开发成功的标志：
- ✅ 桌面端复盘中心功能正常
- ✅ 手机端主应用功能完全不受影响
- ✅ 手机端看不到复盘中心入口
- ✅ Service Worker 缓存中没有复盘中心文件
- ✅ 复盘中心只读数据，不写入主应用的 LocalStorage key

---

## Bug 修复工作流（强制执行）

每次修复 Bug 后**必须**按以下流程执行，确保修复记录完整且版本同步正确。

### 1. 同步更新版本号（三处强制同步）

**必须同时修改以下三个文件**，否则会触发 SW 无限刷新循环：

```javascript
// src/service-worker.js
- 第 1 行注释：// time-planner vXX
- CACHE_NAME 常量：const CACHE_NAME = 'time-planner-vXX';
- install 日志：console.log('[sw] install vXX 开始...');

// src/app.js
- EXPECTED_CACHE_NAME 常量：var EXPECTED_CACHE_NAME = 'time-planner-vXX';

// src/时间管理助手.html
- 页面右下角版本号：<div id="version-info">vXX</div>
```

**版本号规则**：
- 修复 Bug / 改 SW 代码 → 必须升级版本号（v97 → v98 → v99）
- 只改 UI 样式不涉及 SW → 可以不升级，但建议升级避免混淆

### 2. 更新 Bug 修复日志

在 `BUG_FIX_LOG.md` 文件**顶部**添加新版本记录，必须包含：

- **版本号和日期**：`## vXX (YYYY-MM-DD)`
- **Bug 标题**：简短描述问题
- **症状**：用户看到的现象（截图 / 报错信息）
- **根本原因**：代码层面的根因分析（不能只写"缓存问题"这种笼统描述）
- **修复方案**：具体改了什么代码，附带代码片段对比
- **影响文件**：列出所有修改的文件和行号
- **验证步骤**：如何复现和验证修复效果（便于回归测试）

### 3. 验证修复效果（必须全部通过）

**强制验证清单**：
- [ ] 访问 `/sw-version-check.html` 确认新版本已激活
- [ ] 缓存列表显示正确的资源数量
- [ ] 执行 Bug 原始复现步骤，确认已修复
- [ ] Windows 桌面端测试基本功能（填表、保存、统计）
- [ ] iPhone 测试离线启动（断 Wi-Fi 从主屏幕启动）
- [ ] iPhone 测试同步功能（推送、拉取）
- [ ] 检查浏览器控制台无新增报错

**如果任何一项未通过**：不得提交代码，继续调试直到全部通过。

### 4. 提交到 Git

仅提交与本次修复相关的文件（不要混入其他改动）：

```bash
# 查看当前修改
git status

# 添加修复相关文件
git add src/service-worker.js src/app.js src/时间管理助手.html BUG_FIX_LOG.md

# 提交（使用中文简洁描述）
git commit -m "fix: [Bug简短描述] (vXX)"

# 示例
git commit -m "fix: iPhone离线无法启动PWA白屏问题 (v98)"
```

**注意**：
- 不要提交未暂存的其他文件
- 提交信息用中文，简洁说明修复了什么
- 括号中标注版本号便于追溯

### 5. 通知用户测试

修复完成后告知用户：

```markdown
✅ Bug 已修复（vXX）

**问题**：[用户能理解的简短描述]

**如何验证**：
1. 访问主页（会自动更新到 vXX）
2. 等待 3 秒看到右下角 vXX 版本号
3. [具体验证步骤]

**需要清除旧 SW 吗**：
- 如果版本号自动升级 → 不需要
- 如果卡在旧版本 → 访问 /sw-cleanup.html 清理后重试
```

### 6. 特殊情况处理

**版本号冲突**：
- 如果 `service-worker.js` 和 `app.js` 版本号不一致 → 3 秒后强制刷新循环
- 解决：立即修正版本号，用户需清除 SW 重新加载

**SW 注册失败**：
- 检查 `app.js` 的 `registerServiceWorker()` 是否有 `return;` 跳过注册
- 检查是否有临时调试代码未删除

**离线无法打开**：
- 检查 `cache.match` 是否使用 `{ ignoreSearch: true }`（解决查询参数匹配问题）
- 检查 `manifest.json` 的 `start_url` 是否与缓存的 URL 匹配
- 检查 `Cache-Control` 响应头是否为 `public, max-age=0`（不能是 `no-store`）

### 7. 禁止行为

**绝对禁止**：
- ❌ 改了 `service-worker.js` 但忘记升级版本号
- ❌ 版本号只改一处（三处必须同步）
- ❌ 不更新 `BUG_FIX_LOG.md` 就提交代码
- ❌ 未验证就告诉用户"已修复"
- ❌ 在 `registerServiceWorker()` 中留下调试代码
- ❌ 提交时混入无关文件的改动

### 8. Bug 修复记录查询

所有历史 Bug 修复记录在 `BUG_FIX_LOG.md` 文件中，包括：
- 问题症状和复现步骤
- 根本原因分析
- 修复方案和代码对比
- 验证步骤

**遇到类似问题时先查这个文件**，避免重复踩坑。
