# Bug 修复日志

本文件记录时间管理助手项目从启动至今的所有 Bug 修复历史，便于回溯问题根源和验证修复效果。

---

## v101 (2026-09-29)

### Bug：iPhone「拉取全部周」19 周全部失败，历史周停在旧编码

**症状**：iPhone 同步面板点「⬇ 拉取全部周」，日志约每 4 秒一行，最终「共 19 周，更新 0 周，失败 19 周」；已绑定设备中手机「最后同步」一直显示 20480 分钟前。

**排查证据**：
- 服务端正常：用手机令牌直连 `https://26.104.213.44:6444/weeks/2026/{22,37,40}` 均 200，1~38ms
- 问题在客户端 SW：用 vm 模拟 v100 的 fetch 事件，同步 API 请求被拦截，缓存未命中时抛 `Body is unusable: Body has already been read`

**根本原因**：
1. `service-worker.js` 的 fetch 事件对**所有 GET**（包括 6444 端口的同步 API）都做 cache-first SWR：拉取可能拿到旧快照，也可能失败
2. `cacheFirstSWR` 调用 `cache.put(request, sanitizeForCache(resp))` 时没有 clone。`sanitizeForCache` 用 `new Response(response.body)` 接管了原始流，返回给页面的 `resp` 和缓存副本共用同一个 body，页面 `res.json()` 失败，随后 URL fallback 超时（4s）
3. （附带）`sync-server.js` 的 `authenticate` 用 `findDeviceByToken` 又读了一遍 devices.json，改的是另一份副本，`lastSyncAt` 从未真正写盘
4. （附带）`pullAllWeeks` 的 catch 吞掉了错误信息，面板看不到原因

**修复方案**：
```js
// service-worker.js：只接管同源静态资源 + 白名单 CDN
if (url.origin !== location.origin && !CDN_HOSTS.includes(url.hostname)) return;
if (SYNC_API_RE.test(url.pathname) || req.headers.has('X-Device-Token')) return;
// 缓存前 clone
cache.put(request, sanitizeForCache(resp.clone()))

// sync-server.js：在同一份 data 中查找设备
const dev = data.devices.find(d => d.token === token);

// app-core.js pullAllWeeks：记录 firstError；app.js 面板显示「首个失败原因」
```

**影响文件**：`src/service-worker.js`（CDN_HOSTS/SYNC_API_RE、fetch 过滤、clone、版本号）、`src/app.js`（EXPECTED_CACHE_NAME、首个失败原因日志）、`src/app-core.js`（pullAllWeeks.firstError）、`src/时间管理助手.html`（版本号）、`sync-server.js`（authenticate）

**验证步骤**：
1. 语法检查 4 个文件通过；vm 模拟 SW：v101 同步 API / 非白名单跨域不拦截，同源静态资源页面与缓存都能读取；v100 对照复现 `Body is unusable`
2. iPhone：打开页面，右下角变成 v101（卡旧版本就访问 `/sw-cleanup.html`）→ 同步面板勾选「启用同步」→ 保存 → 点「⬇ 拉取全部周」→ 应显示「失败 0 周」→ 打开 W31 等历史周，看到 0.x 编码
3. `sync-server.js` 修复需重启同步服务才生效（不影响数据）；生效后手机的「最后同步」会显示为刚刚

---

## v100 (2026-09-29)

### Bug: 切换到历史周看不到服务端新数据

**症状**：v99 迁移后，只有第 39、40 周显示新的休息细分；切到第 31 周等历史周，仍显示旧的编码 0。服务端数据已确认正确。

**根本原因**：
- 启动时只自动拉取「本周 + 上周」（w40、w39）
- 点 ◀ ▶ 切周只执行 `renderAll()`，读的是本机 localStorage 旧副本，不请求服务端
- `syncClient.setCurrentWeek()` 只在启动时调用一次，30s 心跳也一直只拉本周

**修复方案**：`app.js` 的 `renderAll()` 末尾新增 `syncViewedWeek()`：查看的周变化时调用 `setCurrentWeek` 并 `pullWeek` 该周，有变化就重新渲染；首次渲染仍交给启动流程（先 flush 离线队列再拉）。

**影响文件**：`src/app.js`（renderAll + syncViewedWeek），版本号三处 v99 → v100

**验证步骤**：
1. 用 Node 模拟 w31 为迁移前旧数据的客户端，连接真实同步服务执行 `pullAllWeeks`：19 周全部拉取，w31 纯 0 由 219 格变 0 格，0.9 为 204 格；服务端数据未被改动
2. 浏览器切到第 31 周，1~2 秒内应自动变为 0.9/0.1 等细分编码

---

## v99 (2026-09-29)

### 功能升级：休息（Rest）细分为 0.1~0.9 + 历史数据重分类

**需求**：休息参照 QW 分细项管理：0.1 睡觉、0.2 吃喝、0.3 散步、0.4 出行、0.5 刷手机、0.6 卫生、0.7 游戏、0.8 社交、0.9 其他。历史 code=0 的数据按新分类重新归类。

**改动**：
- `app-core.js`：`DEFAULT_CONFIG.restNames`（9 项）；`getConfig/saveConfig` 补齐 restNames；`calcDailyStats/calcWeeklyStats` 新增 `restDetail[9]`；syncClient 新增 `pullAllWeeks()`
- `app.js`：`validateCode` 接受 0.1~0.9，纯 0 提示细分；编码提示；桌面统计表、左栏、移动端当日/本周明细、配置页（可改名）、Excel 导出、周对比表与导出均加入休息明细；同步面板新增「⬇ 拉取全部周」
- `styles.css`：`.detail-rest`、`.lp-rest`
- `review-engine.js`：0.x 计入 totalRest 和 breakdown
- `review-ui.js`：`getCodeLabel` 支持 0.x；两个周对比表的「休息时间」可展开明细
- `tools/migrate-rest-subcat.js`：迁移脚本（默认 dry-run，`--apply` 写入，幂等）
- 版本号：v98 → v99（三处同步）

**数据迁移结果**（w22-w40）：1562 格 = 781h 全部由 0 改为 0.x，其他 2822 格和 keyitems/review/config 逐项比对未变动。

**回退方法**：
1. 数据：用 `backups/pre-rest-subcat-20260929-1300/sync-data/` 覆盖 `sync-data/`（覆盖前再备份当前版本）
2. 代码：`git checkout` 本次提交之前的版本，或使用备份目录里的 `src/`
3. 客户端：数据回退后需把 backup 里的 cell.updatedAt 调到比当前更新，否则客户端不会拉回旧值

**验证步骤**：
1. 桌面访问主页，右下角显示 v99
2. 同步面板点「⬇ 拉取全部周」，查看各周休息明细是否出现
3. 新录入编码 0 → 提示细分；0.1~0.9 正常保存
4. iPhone：更新到 v99 后点「拉取全部周」，确认填表/保存/同步/离线启动正常

---

## v98 (2026-09-15)

### Bug: iPhone 离线无法启动 PWA（白屏 5+ 分钟）

**症状**：
- Service Worker v97 已注册且激活
- 缓存显示 16 个资源已存储
- 断开 Wi-Fi 后从主屏幕启动 → 完全白屏，等待 5-6 分钟无响应

**根本原因**：
- manifest.json 的 `start_url` 是 `./?iphone`（带查询参数）
- Service Worker install 时缓存的是 `./`（不带参数）
- `cache.match(request)` 默认严格匹配完整 URL 包括查询参数
- 结果：请求 `/?iphone` 无法命中缓存 `/`，导致离线时无法返回 HTML

**修复方案**：
在 `service-worker.js` 的 `cacheFirstSWR` 函数中，`cache.match` 调用时添加 `{ ignoreSearch: true }` 选项：

```javascript
// 修复前
return cache.match(request).then(cached => {

// 修复后
return cache.match(request, { ignoreSearch: true }).then(cached => {
```

**影响文件**：
- `src/service-worker.js` (line 107)
- 版本号升级：v97 → v98

**验证步骤**：
1. 访问主页等待 SW v98 注册
2. 下拉刷新确保缓存更新
3. 访问 `/sw-version-check.html` 确认 v98 已激活
4. 断开 Wi-Fi，从主屏幕启动
5. 预期：秒开，无白屏

---

## v97 (2026-09-15)

### Bug: Service Worker 完全无法注册

**症状**：
- 访问 `/sw-version-check.html` 显示"Service Worker 未注册"
- PWA 无法离线使用
- 检查页面显示 SW 状态为 null

**根本原因**：
`app.js` 的 `registerServiceWorker()` 函数中存在临时调试代码（lines 211-218），包含：
- 强制注销所有 Service Worker 的代码
- `return;` 语句跳过了下面的正常注册逻辑
- 该调试代码是之前为了排查同步问题临时添加，忘记删除

**修复方案**：
删除整个临时调试代码块（9 行）：

```javascript
// 删除这段
// ========== 临时禁用 Service Worker（调试同步问题）==========
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function(regs) {
    regs.forEach(function(reg) { reg.unregister(); });
    console.log('[临时] 已禁用 Service Worker，强制从服务器加载');
  });
}
return; // 这个 return 阻止了下面的注册代码执行
```

**影响文件**：
- `src/app.js` (lines 211-218 删除)

**验证步骤**：
1. 清除旧 SW（访问 `/sw-cleanup.html`）
2. 访问主页
3. 访问 `/sw-version-check.html`
4. 预期：显示 "✅ Service Worker v97 已激活"

---

## v96 及之前

### Bug: iOS Safari Cache API 拒绝存储响应

**症状**：
- Service Worker install 阶段部分文件缓存失败
- iOS 设备离线时无法打开应用

**根本原因**：
- 服务器返回 `Cache-Control: no-store` 响应头
- iOS Safari 严格遵循规范，拒绝 `cache.put()` 带有 `no-store` 的响应

**修复方案**：
1. 服务端 `server.js` 改为 `Cache-Control: public, max-age=0`
2. Service Worker 添加 `sanitizeForCache()` 函数额外剥离限制性缓存头

**影响文件**：
- `src/server.js`
- `src/service-worker.js`

---

## 修复流程规范

每次修复 Bug 后必须执行以下步骤：

### 1. 更新版本号（三处同步）
```bash
# service-worker.js
- 第 1 行注释：// time-planner vXX
- 第 14 行常量：const CACHE_NAME = 'time-planner-vXX';
- 第 58 行日志：console.log('[sw] install vXX 开始...');

# app.js
- 第 195 行：var EXPECTED_CACHE_NAME = 'time-planner-vXX';

# 时间管理助手.html
- 第 244 行：<div id="version-info">vXX</div>
```

### 2. 更新本修复日志
- 在文件顶部添加新版本记录
- 记录症状、根本原因、修复方案、影响文件、验证步骤

### 3. 提交到 Git（仅暂存区内容）
```bash
git add src/service-worker.js src/app.js src/时间管理助手.html BUG_FIX_LOG.md
git commit -m "fix: [简短描述Bug] (vXX)"
```

### 4. 强制验证（必须通过）
- [ ] 访问 `/sw-version-check.html` 确认新版本已激活
- [ ] 执行 Bug 复现步骤，确认已修复
- [ ] Windows 桌面端测试基本功能
- [ ] iPhone 测试离线启动和同步
- [ ] 检查控制台无报错

### 5. 通知用户测试
告知用户：
1. 新版本号
2. 修复了什么问题
3. 如何验证修复效果
4. 需要清除旧 SW 的情况说明

---

## 注意事项

1. **版本号必须三处同步**，否则会触发无限刷新循环
2. **每次改 SW 代码都必须升级版本号**，否则浏览器不会更新
3. **用户端需要"下拉刷新"才能触发 SW 更新检查**
4. **复现步骤必须在修复日志中记录**，便于回归测试
5. **根本原因分析到代码层面**，不能只写"缓存问题"这种笼统描述
