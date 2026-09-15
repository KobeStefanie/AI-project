# Bug 修复日志

本文件记录时间管理助手项目从启动至今的所有 Bug 修复历史，便于回溯问题根源和验证修复效果。

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
