# Bug 修复日志

本文件记录时间管理助手项目从启动至今的所有 Bug 修复历史，便于回溯问题根源和验证修复效果。

---

## v108 (2026-10-09)

### 编码调整：GFP 2.1「演出」改名「影片」，新增 2.8「演出」，追溯历史

**需求**（用户 2026-10-09）：原 2.1 演出改为影片，2.8 为演出，历史一并更改

**设计决定**：历史 2.1 的 8 条记录（蜘蛛侠、龙餐馆、黑暗骑士、爱在黎明时等）都是看电影，所以**编码不变、只改名称**；2.8 演出目前没有历史数据

**用户确认的归类**（AskUserQuestion）：
- 2.1 名称用「影片」（消息里先说"电影"后说"影片"，已确认）
- 2.6 小资里的电影 → 2.1：w29「爱在黄昏日落时」2h、w40「电影【康斯坦丁】」2h
- w28 7/6 2.1「吃饭」2h → 2.3 社交
- w34 8/23 0.0「去看电影」0.5h → 0.4 出行

**改动**：
- `src/app-core.js:45-50`：`DEFAULT_CONFIG.gfpNames` 改为 `影片/运动/社交/旅行/游戏/小资/钢琴/演出/(空)/其他`，`gfpOn[7] = true`
- `tools/migrate-v108-film-show.js`：dry-run / `--apply`，`codeSchema = 108` 幂等；config 只改 gfpNames[0]、gfpNames[7]、gfpOn[7]
- 版本号 v107 → v108（三处）
- 未改 app.js 逻辑：名称、启用开关、统计都从配置读，10 项结构不变

**数据迁移结果**（w22-w41，13 格 = 6.5h，备份 `backups/pre-v108-film-show-20261009-1922/`）：

| 变化 | 时长 | 内容 |
|---|---|---|
| 2.6 → 2.1 影片 | 4h | w29 爱在黄昏日落时、w40 电影【康斯坦丁】 |
| 2.1 → 2.3 社交 | 2h | w28 7/6 吃饭 |
| 0.0 → 0.4 出行 | 0.5h | w34 8/23 去看电影 |

- dry-run 显示 w28「吃饭」是 4 格 2h（提问时按截图上下文说成 3h，以脚本统计为准）
- 20 周 config：2.1 演出 → 影片，2.8 新增演出并启用
- 迁移后 2.1 影片合计 17h

**验证**：
- ✅ apply 前复查：备份后无新推送（`diff -rq` 一致）
- ✅ **旧代码兼容检查**（WORKFLOW 需求5 v1.4）：v107 `normalizeConfigNames` 读迁移后配置不改动，2.8 识别为启用，统计 gfpDetail[7] 正常、checkInvest = 0
- ✅ 重跑 0 周 0 格（幂等）
- ✅ 逐格对比备份：只有 13 个目标格变化（title 不变），config 只有 gfpNames[0]/[7]、gfpOn[7] 变化，其他 0 差异
- ✅ 模拟旧数据客户端 `pullAllWeeks`，**v108 新代码和 v107 旧代码各跑一次**：都是 20 周应用、失败 0，13 格全部变为新编码，20 周配置全部为 影片/…/演出，无写请求
- ✅ `node --check` app-core.js / app.js / service-worker.js 通过
- ⏳ 桌面、iPhone 实测

**回退方法**：
1. 数据：用备份的 `sync-data/` 覆盖（先备份当前版本），再把 cell.updatedAt、config.updatedAt、weekUpdatedAt 调到比当前新
2. 代码：用备份目录的 `src/`

---

## v107 (2026-10-09)

### 体验优化：日程格弹窗「允许编码」按大类分行显示

**需求**（用户 2026-10-09 18:04 iPhone 截图）：v106 的允许编码提示是一整段连续文字（QW … · GFP … · Proc … · Rest … · 4 MW），手机上难找；要求按大类分行

**改动**：
- `src/app.js:1340-1346`：`code-hint` 改为标题「允许编码」+ 5 行（QW / GFP / Proc / Rest / MW），每行左侧大类名、右侧该类启用的编码；内容仍走 `escapeHtml`
- `src/styles.css:357-361`：新增 `.code-hint-title` / `.code-hint-row`（flex 两栏，行间虚线分隔，大类名固定 34px 宽）
- 版本号 v106 → v107（三处）。手机已在 v106，不升版本 SW 不会更新 app.js / styles.css

**验证**：
- ✅ `node --check` app.js / service-worker.js 通过
- ✅ 静态服务实际返回的 app.js、styles.css 含新代码，SW `CACHE_NAME = time-planner-v107`
- ✅ iPhone 实测分行效果 + 回归测试通过（用户 2026-10-09 确认"没问题了"）

---

## v106 (2026-10-09)

### Bug：第 41 周 QW 1.3 / 1.4 名称对调（1.3 显示注会变现、1.4 显示读书）

**症状**（用户 2026-10-09）：w41 统计里 1.3 应为「读书」、1.4 应为「注会变现」，显示反了

**根本原因**（两个叠加）：
1. `DEFAULT_CONFIG.qwNames` 一直是早期默认值 `新媒体运营/心理咨询/注会变现/读书/投资/造音师`，与实际使用的 `AI/心理咨询/读书/注会变现/投资/自我管理` 不一致（1.3/1.4 正好相反）
2. v105 迁移把服务端 config 展开成 10 项后，**还在跑 v104 的客户端**拉取时，v104 `normalizeConfigNames` 判断 `qwNames.length !== 7` → 用旧默认值整体覆盖，并把 `meta.config` 记为服务端时间戳。之后升到 v105，LWW 判定"本地不旧"，不再拉取，错误名称留在本地
- 格子编码本身没错：服务端 1.3 = 看书 / 杀死一只知更鸟 / 理解人性，1.4 = 成本 / 恒邦 / 简历，只是标签错
- gfp / proc / rest 的默认值与实际一致，被 v104 重置后结果相同，所以只有 QW 出错（模拟比对确认只有 qwNames 有差异）

**修复方案**：
- `src/app-core.js:43-44`：`DEFAULT_CONFIG.qwNames` 改为实际名称 `AI/心理咨询/读书/注会变现/投资/自我管理`
- `tools/fix-v105-cfg-repull.js`：只刷新服务端 20 周的 `config.updatedAt` 和 `weekUpdatedAt`（qwNames 前 6 项必须与预期一致才动），让已污染的客户端重新拉取
- 版本号 v105 → v106（三处），让已加载 v105 的设备拿到新默认值

**影响文件**：
- `src/app-core.js:43-44`
- `src/service-worker.js:1,14,63`、`src/app.js:239`、`src/时间管理助手.html:245`
- `tools/fix-v105-cfg-repull.js`（新增）
- `sync-data/2026/w22~w41.json`（只改时间戳，备份 `backups/pre-v105-cfg-repull-20261009-1726/`）

**验证**：
- ✅ 复现：v104 代码拉取 v105 服务端 w41 → 本地 qwNames 变成旧默认值（1.3 注会变现 / 1.4 读书）
- ✅ 服务端 20 周 qwNames 本来就正确；补丁写入后除两个时间戳外与备份 0 差异
- ✅ 模拟被污染的客户端（20 周本地旧默认 + 旧 meta.config）用 v106 代码 `pullAllWeeks`：20 周应用、失败 0，20/20 周恢复为正确名称
- ✅ 真机：iPhone 升级 v106 + 拉取全部周，历史周显示正确（用户 2026-10-09 18:04 确认）

**排查弯路**：v105 的"模拟旧数据客户端拉取"用的是 v105 代码，没测"v104 代码拉 v105 数据"这条路径，所以漏掉了。**下次**：改配置结构后，要用**上一版代码**拉一次新数据，看旧客户端会不会改坏本地

**追加改动：新周配置沿用此前最近一周**（用户 2026-10-09：新周没有配置时自动沿用上周，而不是默认值）：
- 旧逻辑只看紧挨着的上一周，上一周没有配置（如中间隔了没打开的周）就直接用 `DEFAULT_CONFIG`
- `src/app-core.js` 新增 `findLatestConfigBefore(year, week)`：扫描本机 `tm_YYYY_wNN_config`，取早于本周的最近一份；`getConfig` 改为调用它，本机一份配置都没有时才用默认值
- vm 单测 7/7：上周有配置沿用、隔 3 个空周取最近、跨年取 2025 w52、不取未来周、无配置用默认值、本周已有配置不受影响、继承后写入新周

**⚠️ 已知隐患**：
- ~~`DEFAULT_CONFIG.startTime = '7:00'`，实际 20 周都是 `9:00`~~ 已于 v106 修复（用户确认）：`app-core.js` 的 `DEFAULT_CONFIG.startTime`、`buildTimeSlots` 兜底、`TIME_SLOTS` 初值，`app.js` 5 处 `|| '7:00'` 兜底，全部改为 `9:00`；验证：空本机 `getConfig` → 9:00，时段 9:00-9:30 … 1:30-2:00
- `diag-config.html` / `fix-config.html` 里写死的还是旧 QW 名称，已有"已过时，勿用"横幅，不要点它们的修复

---

## v105 (2026-10-09)

### 功能升级：四大类统一 10 个子类（x.1~x.9 + x.0 其他）+ 子类启用开关

**需求**（用户 2026-10-09）：QW / GFP / Proc / Rest 都是 10 个子类，「其他」统一为 x.0；空位可停用；历史数据迁移

**设计决定**：
- x.0 存为数字 `0/1/2/3`（与 v104 的 0.0 同理，1.0 存进去就是 1），显示用 `subCode(prefix, 9)` 生成 `x.0`
- 新增 `qwOn/gfpOn/procOn/restOn`（10 项布尔），下标 9 固定启用；旧配置没有开关时「名字非空即启用」
- 停用只禁止新录入，历史格子照常计数和显示（`visibleSubs` = 启用的 + 明细有数据的）

**改动**：
- `app-core.js`：`DEFAULT_CONFIG` 四类 10 项 + `*On`；新增 `SUB_N`、`codeToSub`、`isSubEnabled`、`visibleSubs`、`expandTo10`；`normalizeConfigNames` 支持 v103→v104→v105 链式升级；`calcDailyStats/calcWeeklyStats` 明细统一 10 项，裸 0~3 计入下标 9
- `app.js`：`validateCode` 接受 `x.0~x.9` 与裸 0~3，停用子类拒绝新录入（原值保留不拦）；统计表 / 左栏 / 移动端明细 / Excel / 周对比改用 `visibleSubs`；配置页加启用复选框；`reclassifyDisabledSubs`：停用正在使用的子类时询问是否改为 x.0
- `review-engine.js`：`calculateStats` 与日程格事件汇总中裸 0~3 记为 `x.0`
- `review-ui.js`：三处读 config 先 `normalizeConfigNames`，明细编码用 `subCode`
- `diag-config.html` / `fix-config.html`：加「已过时，勿用」横幅（它们的「修复」会把配置改回旧长度）
- `tools/migrate-v105-ten-subcats.js`：dry-run / `--apply`，`codeSchema = 105` 幂等，config 直接调前端的 `normalizeConfigNames`
- 版本号 v104 → v105（三处）

**数据迁移结果**（w22-w41，95 格 = 47.5h，备份 `backups/pre-v105-ten-subcats-20261009-1606/`）：

| 变化 | 格数 / 时长 | 内容 |
|---|---|---|
| 1.7 → 1.0 QW 其他 | 33 格 / 16.5h | 闲鱼、履约到期通知书、报税、注销纽莱福各 2h，开票 1.5h 等 |
| 3.5 → 3.0 Proc 其他 | 56 格 / 28h | 被垃圾毁掉的一天 11h、远离垃圾 10.5h、人人有责 6.5h |
| 2.8 → 2.0 GFP 其他 | 6 格 / 3h | 与阿凯吃饭 2h、打扫卫生 1h |

- 20 周 config 全部展开为 10 项，原有名称原位保留，「其他」移到下标 9
- 1.7 里的「锻炼 / 运动」各 0.5h 按规则进了 1.0，未单独改（用户可手动改 2.2）

**验证**：
- ✅ apply 前 `diff -rq` 备份与当前 sync-data 一致（无 v104 那种中途推送）
- ✅ 重跑迁移：0 周 0 格（幂等）
- ✅ 逐格对比备份：只有 95 个目标格变化（code + updatedAt/By），其他 cells / keyitems / review / 非名称 config 0 差异
- ✅ 模拟旧数据客户端（灌入备份数据 + 旧 syncmeta）连真实同步服务 `pullAllWeeks`：20 周应用、失败 0；本地 1.7/2.8/3.5 = 33/6/56 → 0，1/2/3 = 33/6/56；config 落地为 10 项 + `qwOn`；无任何写请求
- ✅ 用 v105 `calcDailyStats` 统计 w22-w41：大类总数迁移前后一致（QW 1580 / GFP 435 / Proc 917 / Rest 1683 / MW 43 格），x.0 明细 33/6/56，checkLoss/checkInvest = 0
- ✅ `node --check` 六个 JS 通过；`test-merge-logic.js` 6/6
- ⚠️ `test-offline-queue.js` 在 [3] 报 `document is not defined`（测试桩缺 DOM，与本次无关，未修）
- ✅ iPhone 已随 v106/v107 升级并拉取全部周，历史周正常（用户 2026-10-09 确认）；桌面端未单独确认

**⚠️ 已知隐患**：
- **v104 设备看 v105 数据**：v104 的 `normalizeConfigNames` 不认 10 项、`calcDailyStats` 不认裸 1/2/3 的子类，会显示错位或漏进明细。只是显示问题。规避：各设备先升 v105 再拉取
- **v104 设备推送旧编码**：没拉取就编辑会把 1.7 / 2.8 / 3.5 推回服务端，迁移脚本靠 `codeSchema` 跳过，不能兜底。规避：升级后先「⬇ 拉取全部周」再编辑

**回退方法**：
1. 数据：用备份的 `sync-data/` 覆盖（先备份当前版本）
2. 代码：用备份目录的 `src/`、`tools/`、`sync-server.js`，或 `git checkout`
3. 回退数据后把 cell.updatedAt、config.updatedAt、weekUpdatedAt 调到比当前新，客户端才会拉回

---

## v104 (2026-10-09)

### 功能升级：GFP 新增 2.7 钢琴、休息新增 0.9 发呆/放空 + 0.0 其他

**需求**（用户 2026-10-09）：
- GFP：新增 2.7 钢琴，原 2.7 其他改为 2.8；2.3 约会改名社交
- 休息：0.9 改为发呆/放空，「其他」用 0.0
- 历史数据全部迁移

**设计决定**：休息「其他」用 0.0，不用 1.0。编码按数字存储，1.0 会变成 1，和 QW 冲突；0.10 会变成 0.1，和睡觉撞。0.0 存为数字 `0`，显示为 `0.0`，录入 `0` 或 `0.0` 都可以。旧数据里的纯 0 也会自动归入「其他」。

**改动**：
- `app-core.js`：
  - `DEFAULT_CONFIG` 的 gfpNames 改为 8 项，restNames 改为 10 项（下标 9 = 0.0）
  - 新增 `SUB_COUNT`、`subCode(prefix, idx)`、`normalizeConfigNames()`：旧配置 7/9 项读取时自动升级，保留自定义名，不回写
  - `calcDailyStats/calcWeeklyStats`：gfpDetail[8]、restDetail[10]，dec=0 计入 restDetail[9]
- `app.js`：
  - `validateCode`：接受 0 / 0.0 / 2.8
  - 新增 `fmtCode()`，0 显示为 0.0（周表、移动端、编码输入框、剪贴板提示、Excel）
  - 统计表、左栏、移动端明细、配置页、Excel 的循环改为按名称数组长度，并用 `subCode` 生成编码
  - 周对比两处行列表补 2.8 / 0.0
  - 历史周用服务端原始 config 时先 `normalizeConfigNames`
- `review-engine.js`：breakdown 和日程格事件里，纯 0 记为 `0.0`
- `review-ui.js`：`getCodeLabel` 支持 0 / 0.0；三处读 config 后先 normalize；明细行编码用 `subCode`
- `tools/migrate-v104-piano-daze.js`：默认 dry-run，`--apply` 才写入；用 `codeSchema = 104` 保证幂等
- 版本号 v103 → v104（三处）

**数据迁移结果**（w22-w41，共 463 格 = 231.5h）：

| 变化 | 格数 / 时长 | 内容 |
|---|---|---|
| 2.6 小资（含「琴」）→ 2.7 钢琴 | 211 格 / 105.5h | 练琴 63.5h、钢琴 16h、弹琴 13.5h 等 |
| 2.7 其他 → 2.8 其他 | 6 格 / 3h | 与阿凯吃饭、打扫卫生 |
| 0.9 其他 → 0.0 其他 | 246 格 / 123h | 回家休息 102h、摸鱼 4.5h 等 |
| 0.9 发呆 | 4 格 / 2h | 保留 |

- 用户确认的归类：凝神、享受音乐、拼凑钢琴 → 0.0 其他；去练琴/去学琴保留 0.4 出行；讨论钢琴和卡农保留 0.8 社交
- 20 周 config 全部升级为 8 / 10 项。w32/w33 原本就把 2.3 叫「社交」，保持不变

**验证**：
- ✅ vm 单测 15 项通过：
  - 统计明细
  - 配置升级：保留自定义名、幂等、约会→社交
  - validateCode：0 / 0.0 / 2.8 合法，2.9 / 1.0 拒绝
  - fmtCode
  - 复盘 breakdown
- ✅ 迁移重跑结果为 0 周 0 格（幂等）
- ✅ 逐格对比备份：
  - 19 周只有目标格和 config 名称变化
  - w40 另有差异，原因见下方「排查记录」，与迁移无关
- ✅ 模拟旧数据客户端连真实同步服务跑 `pullAllWeeks`：
  - 20 周全部应用，失败 0
  - 本地 2.6 含琴 211 → 0，2.7 = 211，2.8 = 6，0.9 = 4，0 = 246
  - w39 统计 checkInvest = 0
- ✅ 已被 v105~v107 覆盖：iPhone 升 v107 拉取全部周后历史周正常（用户 2026-10-09 确认）

**排查记录：w40 对比差异**：
- **现象**：逐格对比时，w40 的 238 格以及 keyitems / review / archived 都和备份不同
- **原因**：备份在 12:16，iPhone（`1678d395`）12:37 推送了 w40 的复盘、归档和全量格子，迁移在 12:57。差异来自那次推送：格子的 title/code/updatedAt 都没变，只有 updatedBy 变了；review 和 archived 是新数据
- **影响**：迁移本身没问题。但备份里的 w40 比 12:37 旧，回退 w40 会丢掉那次复盘和归档
- **下次**：apply 前重新比对一次 `weekUpdatedAt`；备份和 apply 中间有推送的话，先重新备份

**⚠️ 已知隐患**：
- **v103 设备看 v104 数据**：v103 的 `calcDailyStats` 只认 2.1~2.7，2.8 只计入 GFP 总数，不进明细；配置 8 项会被 v103 当成长度异常，显示默认 7 项名称。只是显示问题，不改服务端数据。规避：各设备先升 v104 再拉取
- **v103 设备推送旧编码**：v103 设备上没拉取的格子，如果之后被编辑，会推送旧编码（如 0.9 回家休息）。迁移脚本靠 `codeSchema` 跳过已迁移的周，不能兜底。规避：升级后先「⬇ 拉取全部周」再编辑

**回退方法**：
1. 数据：用 `backups/pre-gfp-piano-rest-daze-20261009-1216/sync-data/` 覆盖（先备份当前版本）。w40 需要单独处理，保留 12:37 iPhone 推送的 review / archived
2. 代码：`git checkout` 上一版本，或使用备份目录里的 `src/`
3. 回退数据后，需把 cell.updatedAt 调到比当前新，客户端才会拉回旧值

---

## v103 (2026-10-09)

### Bug：同一 Wi-Fi 下 iPhone 连不上同步服务（timeout → Load failed）

**症状**：电脑和 iPhone 在同一 Wi-Fi，两个服务都在跑，手机同步面板：
1. 服务器 IP 显示 `26.104.213.44`，测试连接 `timeout`
2. 手动改成 `10.10.3.41` 后，报 `Load failed`

**根本原因**（两个叠加）：
1. **IP 选错**：电脑有两块网卡，Radmin VPN `26.104.213.44` 和 WLAN `10.10.3.41`。`sync-server.js` 的 `getLanIPs()` 按 `os.networkInterfaces()` 顺序返回，VPN 排第一。客户端把 `lanIPs[0]` 自动存成 `lastIP` 并回填到「服务器 IP」框，于是手机一直在连 VPN 地址。手机不在 Radmin VPN 里，所以 timeout
2. **证书不含新 IP**：`certs/leaf-cert-chain.pem` 的 SAN 只有 `127.0.0.1 / 26.104.213.44 / 192.168.43.161` 和主机名，没有 `10.10.3.41`。iOS 对 HTTPS 证书严格校验，IP 不在 SAN 里直接 `Load failed`

**排查过程中的误判**：一度判断是 Windows 防火墙拦截，新建了入站规则「时间管理助手」（TCP 6443/6444，允许）。事后看 `Load failed` 已说明 TCP 能通、卡在 TLS，防火墙不是主因。规则保留，无害。

**修复方案**：
- **证书**：`node tools/gen-cert/gen-leaf.js` 重签 leaf，SAN 加入 `10.10.3.41`，重启两个服务。CA 不变，iPhone 无需重装
- **`sync-server.js` `getLanIPs()`**：过滤 `169.254.*`；私有网段（10 / 172.16-31 / 192.168）+ 物理网卡排前，VPN/虚拟网卡（Radmin、VMware、Hyper-V、WSL、Tailscale 等）排后
  ```js
  // 旧：按系统枚举顺序 → [{26.104.213.44 Radmin VPN}, {10.10.3.41 WLAN}]
  // 新：按 rank 排序    → [{10.10.3.41 WLAN}, {26.104.213.44 Radmin VPN}]
  ```
- **`src/app.js` `handleApplyIP()`**：连接成功后把服务端返回的电脑名（`DESKTOP-QRG0JNN`）存为 `hostname`。之后 `buildUrls` 的尝试顺序为 `DESKTOP-QRG0JNN.local` → `DESKTOP-QRG0JNN` → `lastIP`。`.local` 已在证书 SAN 里，换 Wi-Fi 后 IP 变了也不用重签证书
- 版本号 v102 → v103（SW / app.js / html 三处）

**影响文件**：
- `sync-server.js`：`getLanIPs()` 及新增 `VIRTUAL_IFACE_RE` / `isPrivateIPv4`
- `src/app.js`：`handleApplyIP()` 连接成功分支；`EXPECTED_CACHE_NAME`
- `src/service-worker.js`：第 1 行注释、`CACHE_NAME`、install 日志
- `src/时间管理助手.html`：`#version-info`
- `certs/leaf-*`（不入库）

**验证**：
- ✅ 重签后证书 SAN 含 `10.10.3.41`，gen-leaf 自校验通过
- ✅ 重启服务后 iPhone 连接成功（用户确认"好了"）
- ✅ 新 `getLanIPs()` 在本机实测返回 `[10.10.3.41 WLAN, 26.104.213.44 Radmin VPN]`；`node --check` 通过
- ⏳ `sync-server.js` 改动需**重启同步服务**才生效
- ⏳ iPhone 升到 v103 后点一次「保存并连接」，日志出现「已记住电脑名」
- ⏳ `.local` 在 iOS 上能否解析未在本网络实测；不通时会退到 `lastIP`

**⚠️ 已知隐患（未修，用户 2026-10-09 决定暂不做 v104）**：
- **触发条件**：手机点了「保存并连接」，`handleApplyIP` 把电脑名存成 `hostname`
- **后果**：`buildUrls` 的顺序变成 `DESKTOP-QRG0JNN.local` → `DESKTOP-QRG0JNN` → `lastIP`。每个地址超时 4s（`app-core.js` `FETCH_TIMEOUT_MS`），而 `_tryFetch` 每次都从第一个开始、不记成功的地址。iOS 解析不了 `.local` 时，每次推送、拉取、30s 心跳都要先白等最多 8s；「拉取全部周」是串行的，会更慢
- **规避**：在 v104 之前不要点「保存并连接」，直接用「服务器 IP」框填 IP + 「测试连接」。已经点过的话，把框里改回 IP，再点「保存设置」
- **修法（v104 待做）**：`_tryFetch` 记住上次成功的 base，下次先试它，失败再走完整列表；只有换网络后的第一次会慢

**以后换 Wi-Fi 连不上时**：
1. 先看手机报错：`timeout` = 地址不通（IP 错 / 不在同一网段）；`Load failed` = 证书不含这个地址
2. `Load failed` → 电脑跑 `node tools/gen-cert/gen-leaf.js`，重启 `启动服务器.bat`
3. 注意：gen-leaf 只写入**当前**网卡 IP，本次重签后 `192.168.43.161`（旧热点）已不在 SAN 里，回到那个网络需要再跑一次

---

## 复盘中心 (2026-09-29，仅桌面端，未改主应用、未升级版本号)

### Bug：对话中点"查看详情"，历史报告覆盖当前界面，无法返回

**症状**：自由对话进行中，点左侧历史复盘的「查看详情」，主区域立刻变成历史报告；顶部「2. 自由对话」点了没反应，回不到对话。

**根本原因**：
- `viewHistory` 调用 `switchStage(3)`，并把历史报告写进当前复盘共用的 `#report-content`
- 顶部 `.stage-btn` 只是进度指示，没有绑定点击事件，所以无法切回
- 内存里的 `chatMessages` 和 `#chat-messages` DOM 实际没被清空，只是看不到

**修复方案**：
- `review-center.html` 新增 `#history-view-modal` 弹窗；`viewHistory` 改为把内容写进 `#history-view-content` 后打开弹窗，不再切换阶段、不碰 `#report-content`。点遮罩或「关闭，回到当前复盘」即可返回
- `review-ui.js` 新增 `initStageNav()`：顶部阶段按钮可点击，只能去已有内容的阶段（有对话才能去 2，有报告才能去 3），切换不清空数据
- 顺带修复 `renderReport` 里 `## 标题` 被替换成字面 `$2` 的问题（正则只有一个捕获组，改为 `$1`）

**验证**：`node --check` 通过；浏览器端待用户验证。

### Bug：AI 说"第 39 周清单里没有钢琴"，但日程格里有

**症状**：用户第 39 周日程格里有「钢琴 4h + 弹钢琴 1h」（2.6），AI 复盘时断言"那周清单里没有钢琴"。

**根本原因**：`buildDataContext` 给 AI 的每周素材只有关键事项区的前 12 条（`keyItems`），日程格里的具体事件从未传给 AI。w39 关键事项是：成本模版升级、心理学、报价、中秋摸鱼等，本来就没有钢琴，AI 据此判断成了"没做"。

**修复方案**（`src/review-engine.js`）：
- `buildDataContext` 按「事件名 + 分类代码」汇总每周日程格的小时数（每格 0.5h），按时长倒序存到 `weekDetails[].events`
- `formatContextForPrompt` 每周多输出一行「日程格全部事件（按时长）」，原来的"做了"改名为"关键事项（摘录）"，并加一条规则：判断做没做必须看日程格全部事件，两处都没有才能说没做

**验证**：`node --check` 通过；用 sync-data/2026/w39.json 实测，事件汇总里有 `钢琴(2.6) 4h`、`弹钢琴(2.6) 1h`，共 53 个事件。浏览器端待用户验证。

### Bug：周期数据对比表主行是明细和的 2 倍

**症状**：第 37 周 QW 显示 93.0h，但 1.1~1.7 明细相加只有 46.5h；GFP/拖延/休息/MW 主行同样翻倍。

**根本原因**：`AppCore.calcWeeklyStats` 的 totals 是半小时格数。`review-ui.js` 的明细行做了 `× 0.5` 换算成小时，但主行直接把格数当小时显示，差值列也跟着翻倍。

**修复方案**：`generateCompareTableHTML`（报告内嵌表）和 `renderCompareTable`（弹窗表）的主行值统一 `× 0.5`；「凌晨工作次数」是次数，不换算。

**影响文件**：`src/review-ui.js`

**验证步骤**：用 sync-data 的 w37-w39 真实数据计算，各大类小时数 = 明细之和（w37：QW 46.5 / GFP 9 / 拖延 21.5 / 休息 38.5 / MW 3.5），五类合计 119h = 7 天 × 17h

### Bug：AI 说"这是第一次复盘"，重复问上次问过的问题

**症状**：历史复盘里有「2026年9月 (第35-38周)」，但这次复盘 37-40 周时，AI 又问了上次问过的「第37周要崩又自救，怎么接住自己的」，还说"数据里显示这是第一次复盘"。

**根本原因**：
1. `review-engine.js` 的 `getPreviousReview` 只认 `weekRange[1] < startWeek` 的记录。上次 35-38 和这次 37-40 有重叠（38 ≥ 37），所以被过滤掉，prompt 里就写成了"无历史复盘记录，这是第一次"
2. 即使找到上次记录，prompt 也只带用户的话（userWords），不带 AI 当时问过的问题，AI 不知道哪些已经问过
3. `saveReviewRecord` 的 key 只按月份算（`tm_review_2026_m09`），同月再次保存会覆盖上次的复盘

**修复方案**：
- 过滤条件改为 `weekRange[0] < startWeek`，允许周范围重叠
- 从 `conversationLog` 提取上次的「问—答」对（最多 12 组）写入 prompt，并标注"不要重复问"
- key 改为 `tm_review_YYYY_mMM_wA-B`，旧 key 仍能被列表识别

**影响文件**：`src/review-engine.js`（saveReviewRecord、getPreviousReview、formatContextForPrompt）

**验证步骤**：Node 模拟 localStorage：已有 35-38 周记录 → 以 37 周为起点能找到上次记录和问答对；保存 37-40 周后两条记录并存

---

## v102 (2026-09-29)

### Bug：手机显示「推送成功」，桌面端数据不变

**症状**：iPhone 同步面板显示 `✓ 推送成功 (cells=68 items=5 st=3)`，桌面端 W40 没有任何变化。

**排查证据**：
- 服务端 `sync-data/2026/w40.json`：`weekUpdatedAt` 为 18:16:18，说明推送已到达；但 68 个 cell 中最新的 `updatedAt` 仍是 16:26:39，其余是 13:12:39
- 手机在此之前有一段时间处于「同步已关闭」状态（v101 排查截图）

**根本原因**：
`app-core.js` 的 `_handleSaveChange` 开头有 `if (!cfg.enabled) return;`。同步关闭期间修改格子，`syncmeta` 里对应的 `updatedAt` 不会更新。重新开启同步后，`pushWeek` 用的仍是旧时间戳（`meta.cells[k]`），推上去的内容虽然变了，时间戳却和桌面本地相同。桌面拉取时判断 `serverTs > localTs` 不成立，于是跳过。

**修复方案**：
```js
// 修复前
var cfg = getSyncConfig();
if (!cfg.enabled) return;
...
if (cfg.autoSync) _schedulePush(year, week);

// 修复后：无论同步开关状态如何都打时间戳，只有开启时才推送
var cfg = getSyncConfig();
...
if (cfg.enabled && cfg.autoSync) _schedulePush(year, week);
```

**存量数据修复**：备份到 `backups/pre-v102-w40-20260929-1821/`，把 w40 中手机写入的 76 条（cells 68 / keyitems 5 / keyitemStatus 3）`updatedAt` 和 `weekUpdatedAt` 刷新为当前时间。config 未改，以桌面端为准。

**影响文件**：`src/app-core.js`（`_handleSaveChange`）、`src/service-worker.js` / `src/app.js` / `src/时间管理助手.html`（版本号 v102）、`sync-data/2026/w40.json`（存量数据，不入库）

**验证步骤**：
1. Node vm 模拟：同步关闭时保存 → meta 已打时间戳，且不发起推送；开启后保存 → 发起推送（已通过）
2. 桌面刷新或点「⬇ 立即拉取」→ W40 显示手机端内容
3. 手机关闭同步 → 改一格 → 开启同步 → 推送 → 桌面能收到

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
