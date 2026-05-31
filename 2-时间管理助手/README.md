# 2-时间管理助手

仿 Excel 周计划表的时间管理 PWA 应用，支持 Windows / iPhone / 华为安卓。

## 目录结构

```
2-时间管理助手/
├── README.md
├── CHANGELOG.md
├── 需求文档.md
├── 启动服务器.bat        # 双击即启本地静态服务器（端口 6371）
└── src/
    ├── 时间管理助手.html   # 主入口（呈现页 + 配置页 + 手机端单日/累计页）
    ├── styles.css        # 样式（桌面 + 手机）
    ├── app-core.js       # 共享核心：数据存取、ISO 周、统计、JSON 导入导出
    ├── app.js            # UI / 事件 / 桌面 + 手机端逻辑
    ├── server.js         # 内置静态服务器（Node.js 内置模块，零依赖）
    ├── manifest.json     # PWA manifest
    ├── service-worker.js # PWA 缓存（network-first，自动更新）
    ├── icon.svg          # 图标（SVG，浏览器标签页）
    ├── icon-192.png      # 图标（PNG 192×192，iOS/Android 主屏幕）
    ├── mockup.html       # UI 原型（开发参考）
    └── mockup-config.html
```

## 运行方式

### 推荐：双击桌面快捷方式

首次部署后桌面会有 `启动时间管理助手服务器.lnk`，双击即启动本地服务器（端口 6371），保持黑窗开着，然后浏览器访问下面的 URL：

| 设备 | HTTP（开发） | HTTPS（v2.11.0+，iPhone PWA 必经） |
|---|---|---|
| 电脑 | `http://127.0.0.1:6371/` | `https://127.0.0.1:6443/` |
| 同 Wi-Fi 手机 | `http://<电脑名>.local:6371/` | `https://<电脑名>.local:6443/` |
| 手机（mDNS 失败时兜底） | `http://<电脑当前 IP>:6371/` | `https://<电脑当前 IP>:6443/` |

### 命令行启动

```powershell
# 项目根目录运行
./启动服务器.bat

# 或直接 node
node src/server.js          # 静态服务：HTTP 6371 + HTTPS 6443（v2.11.0+）
node sync-server.js         # 同步服务：HTTP 6372 + HTTPS 6444（v2.11.0+）
```

### HTTPS 首次部署（iPhone PWA / 离线启动用）

```powershell
# 1. 生成 CA + leaf 证书（首次跑一次，10 年 CA + 2 年 leaf）
cd tools\gen-cert
npm install
node gen-all.js

# 2. 防火墙放行 HTTPS 端口（管理员 PowerShell）
New-NetFirewallRule -DisplayName 'TimePlanner-Static-HTTPS-6443' -Direction Inbound -Protocol TCP -LocalPort 6443 -Action Allow -Profile Private,Public
New-NetFirewallRule -DisplayName 'TimePlanner-Sync-HTTPS-6444'  -Direction Inbound -Protocol TCP -LocalPort 6444 -Action Allow -Profile Private,Public
```

**iPhone 装 CA**(同 Wi-Fi)：

1. Safari 访问 `http://<电脑 LAN IP>:6371/cert.crt` 下载描述文件
2. 设置 → 通用 → VPN 与设备管理 → 安装"Time Planner Personal CA"
3. 设置 → 通用 → 关于本机 → 证书信任设置 → 打开"Time Planner Personal CA"开关
4. Safari 访问 `https://<电脑 LAN IP>:6443/` → 添加到主屏幕

> **iOS 18 已知限制**：自签 CA 即使「完全信任」，Safari 仍会把"添加到主屏幕"降级为**普通书签**而非 standalone PWA（图标灰色 + 长按显示"删除书签"）。但**Service Worker 离线缓存仍工作**：飞行模式下点书签 → Safari 打开缓存的应用 → 数据可用，95% 等同 PWA 体验。如需独立全屏 PWA，需用 ngrok / Cloudflare Tunnel + Let's Encrypt 真证书。详见 CHANGELOG v2.11.0。

### 直接打开（最简单，但无 PWA 离线 / 同步）

直接用浏览器打开 `src/时间管理助手.html` 即可使用（LocalStorage 存数据），适合临时调试，**不推荐日常使用**——因为 SW 在 `file://` 下不工作。

## 核心功能

- ISO 周显示与切换（上/下/本周）
- 每日关键事项 5 行，前三件事支持评价状态（已完成/持续/未完成），清空文本自动复位
- 桌面端周表/月历视图切换：月历按自然月展示（只读），周表支持冻结窗格 + 行高亮
- 7:00-00:00 半小时日程格（34格×7天）
- 分类代码系统：0=Rest, 1.x=QW, 2.x=GFP, 3.x=Proc, 4=MW
- 自动着色（5 种分类颜色）
- 底部统计：五大分类、赚/赔/结余、GFP明细、项目投入、有效投资/无效浪费、潜力/标准/可用、校验
- 左侧本周累计面板
- 右侧周复盘 10 项
- 配置页（QW/GFP 名称自定义、标准数调整）
- 确认归档 → 导出 `.xlsx`
- PWA 离线可用（Service Worker，缓存含 XLSX 导出库）

## 三端设计策略

项目按 **Windows 桌面版 / iPhone 手机版 / 华为安卓手机版** 三套体验进行设计。

### 共用部分

- 同一套 LocalStorage 数据结构
- 同一套 ISO 周计算逻辑
- 同一套分类代码系统
- 同一套统计、校验、归档、Excel 导出逻辑
- 同一周配置由 Windows 桌面版确认后，iPhone / 华为端共享使用

### Windows 桌面版

- 三栏布局：左侧本周累计 + 中间完整 Excel 表格 + 右侧周复盘
- 以鼠标键盘操作为主
- 保留高信息密度表格
- 支持 `Ctrl+C` / `Ctrl+V` / `Delete` 等快捷键
- 每周一首次进入新周时，必须完成并确认本周配置
- 可选择延续上一周配置或修改后确认
- 确认配置后，才允许三端开启该周填写

### iPhone 手机版

- 单日竖向填写界面：顶部日期 + 关键事项 + 7:00-00:00 日程 + 当日统计/明细/校验
- 不展示完整周横向表作为主填写方式
- 单击格子直接编辑
- 使用自定义 modal，不依赖 `<dialog>` / `prompt()`
- 适配 iPhone Safari、PWA 主屏模式、刘海屏和软键盘
- 移动端复制粘贴使用弹窗内按钮
- 仅红框内的关键事项区和 7:00-00:00 日程填写区可编辑
- 当日统计、收益、明细、校验等红框外区域均为只读，由后台逻辑自动计算
- 不提供配置编辑功能，只读取 Windows 版已确认配置
- 如果本周尚未在 Windows 版确认配置，则进入只读锁定状态
- 如果前一日未完成填写，则强制先补齐前一日，校验通过后回到今日

### 华为安卓手机版

- 单日竖向填写界面，结构与 iPhone 版一致
- 不展示完整周横向表作为主填写方式
- 单击格子直接编辑
- 仅红框内的关键事项区和 7:00-00:00 日程填写区可编辑
- 当日统计、收益、明细、校验等红框外区域均为只读，由后台逻辑自动计算
- Excel 导出使用浏览器下载能力保存到默认下载目录
- 不提供配置编辑功能，只读取 Windows 版已确认配置
- 如果本周尚未在 Windows 版确认配置，则进入只读锁定状态
- 如果前一日未完成填写，则强制先补齐前一日，校验通过后回到今日

详细规范见 `需求文档.md` 第 20 章「三端分版设计规范」。

## 版本

| 版本 | 日期 | 说明 |
|---|---|---|
| v2.13.1 | 2026-05-29 | 月历视图 + 三件事三态状态 + 同步/导出/导入全链路支持 |
| v2.13.0 | 2026-05-29 | 扫码绑定 + 设备令牌（4 台设备上限，X-Device-Token 鉴权） |
| v2.12.0 | 2026-05-28 | WebSocket 实时推送（WSS /events，指数退避自动重连） |
| v2.11.0 | 2026-05-28 | HTTPS 化 + CA-leaf 双层证书 + 离线变更队列（online 事件自动 flush）；iOS 18 自签 CA 限制下书签模式 + SW 离线工作 |
| v2.10.2 | 2026-05-28 | 离线启动修复：SW network-first → cache-first SWR，离开 LAN 也能秒开 PWA |
| v2.10.1 | 2026-05-28 | 同步配置 autoHost：从 `window.location` 自动推导主机/端口，零填写 |
| v2.10.0 | 2026-05-27 | 双向 LAN 同步：`sync-server.js` + 客户端面板 + debounce 自动推送 |
| v2.9.1 | 2026-05-28 | 修复 PWA 书签停留旧版：SW 改 network-first + 自动重载更新流 |
| v2.9.0 | 2026-05-27 | 数据导出 / 导入 JSON（双端跨设备迁移过渡方案） |
| v2.5.0 | 2026-05-26 | 明确手机端仅红框内关键事项区和日程区可编辑，其他区域只读自动计算 |
| v2.3.0 | 2026-05-26 | 明确手机端为单日竖向填写界面，并加入前一日补齐流程 |
| v2.2.0 | 2026-05-26 | 明确每周配置必须由 Windows 版确认，手机端只读共享配置 |
| v2.1.0 | 2026-05-26 | 明确三端分版设计（Windows / iPhone / 华为安卓） |
| v2.0.0 | 2026-05-26 | 移动端全面修复（弹窗、触控、视口、图标、离线导出） |
| v1.0.0 | 2026-05-25 | 初版完成 |

详见 [CHANGELOG.md](./CHANGELOG.md)
