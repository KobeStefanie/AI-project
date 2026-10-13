# V13 → V14 升级日志

> 升级日期：2026-09-10
> 基础版本：V13（`10-V13/`）　升级版本：V14（`11-V14/`）
> 目标：把开源「**Seedance 分镜师 3.0**」（完整版 + Lite 版）的工艺内核**器官移植**进我们的 6 agent 架构
> 定位修正：主场是**精品微电影 + MV**（全装档，严谨度拉满）；短剧 / 漫剧 / UGC 为延展方向（轻装档）
> 用户授权原则：冲突优先用他们的；我判断我们更能出好作品的保留（逐条见 CHANGELOG v14.0 的「保留清单」）

**术语对照（全库通行）**：他们的「条」= 我们的 **Cut**；他们的「场」= 我们的 **P0X 剧情点**；地址写法 `epNN-P0X-CutM`（Cut 号全集连续）。

**源库站名 → V14 站名**（移植文件里保留了源库旧名做措辞，8 个入口 SKILL.md 各有一行映射覆盖，见下方「术语债的处理方式」）。

---

## 新增（skill 目录 8 个 + 约定文件 5 项）

### 8 个新 skill

| 路径 | 内容 | 谁调 |
|---|---|---|
| `.claude/skills/shot-design/` | **镜头表中间层**：场级空间地图块 + 场阐述 + 逐镜十项 + 条末结束状态五字段 + 本场资产需求；镜头数在此钉死，是下游唯一真相源 | 分镜师（`~prompt` 第一步） |
| `.claude/skills/camera/` | 六槽运镜句式 + 视场角锚点 + 运动词典 + 角度/景别/情绪对照 | 分镜师 / 导演 / reviewer / retake |
| `.claude/skills/blocking/` | 站位七要素 + 180° 轴线 + 首帧占位锁 + master shot 技法 | 同上 |
| `.claude/skills/performance/` | 五支柱任务制表演 + 表演档案 + 眼活 | 同上 |
| `.claude/skills/lighting/` | 光向五要素 + 世界内光源五槽 + 光锁块 + 物理锁 | 同上 |
| `.claude/skills/sound-writing/` | 声音四要素句式 + 声线锁逐字引用 + 口型纪律 + 密度三档 | 同上 |
| `.claude/skills/continuity/` | `assets/continuity-ledger.md` 六块 + 12 项状态机 + 缝审计八查 | 分镜师 / reviewer / retake |
| `.claude/skills/retake/` | 收案三问 → 五出口（改词 / 局部编辑 / 换 shot / 改输入 / 回上游） | `~retake`，分镜师或服化道 |

每个 skill = `SKILL.md` 入口 + `references/`（按需加载）+ `templates/` + `examples/`，合计约 50 个文件。**移植时统一改造三处**：① 秒数一律改读 `.project-config.json.video_model_config.{min,max}_seconds`（源库写死 Seedance 2.5 / 30s）；② 路径全部映射到我们的目录（`outputs/epNN/…` / `assets/…`）；③ 每个入口顶部加「📌 V14 适配说明」块（条=Cut / 场=P0X / 秒数 config / 路径映射 / 角色对照 / 故事板与控制图手动 / 源库站名映射）。

### 约定与真相源文件

| 路径 | 内容 |
|---|---|
| `assets/story/visual-style.md` | **恒定层之源**：通用基准段 + 画质固定项 + 时代锚 + 场域锚句表 + 条件项表；七件逐字注入每条提示词 |
| `.claude/skills/_shared/visual-style-guide.md` | visual-style 的字段规范与写法方法论 |
| `assets/story/decisions.md` | 确认与拍板理由；路由判「确认完成」看这张表（**文件是记忆，Session 不是**） |
| `assets/continuity-ledger.md` | 连续性台账（用户点名必须做好）；追加式永不回改 |
| `outputs/epNN/02-shot-table.md` / `review/` / `control-prompts.md` | 镜头表 / 审核报告 / 控制图提示词（后者手动可选） |
| `_v14升级工作台/` | 升级过程本身也「文件即记忆」：3 份精读提炼 + `00-断点续跑清单.md`（容灾真相源） |

## 重写（4 项）

- **`CLAUDE.md`**：单位定义（条=Cut / 场=P0X）/ [文件是记忆，Session 不是] / 查病式审核 / 全装轻装两档 / 分镜两步制 / `~retake` `~onboard` / 色彩锚三级
- **`.claude/skills/seedance-storyboard-skill/SKILL.md`**：**380 行，v13.0 → v14.0**。frontmatter 与 H1 去「三块散文」；核心章节 `[编译目标]` 改写为「条头三行 + 围栏四块」；新增 `[三型缝的条头形态]` `[双轨模式判定]`；删虚构路径 `references/templates/spatial-map-template.md`（Glob 证不存在）；`[文件结构]` 只列磁盘实存的 25 个文件；全部秒数改 config 驱动
- **`.claude/agents/storyboard-artist.md`**：两步制（shot-design 落表 → ★表确认 → 编译）+ 9 个 skill 挂载
- **`.claude/agents/reviewer.md`**：评分制 → 查病制（五类病 + blocking 白名单 + 一轮为限 + 熔断）

## 修改（重点，按文件）

**agents/**
- `director.md`：节奏蓝图升级为疏/中/紧三档 + 气口预算；条级主体预算；接缝卡
- `art-designer.md`：纯正向图像规则集 / 七维 / 声线锁登记 / 角度覆盖 / 道具分级
- `bianju-KKO.md`：增量（创作基准与 visual-style 的接口）

**skills/**
- 4 个 review skill + `_shared/review-methodology.md`：评分制 → **查病制**。五类病（矛盾 / 断链 / 走样 / 模型雷 / 红线）；**只有 blocking 白名单挡线**（死引用 / 同一资产双真相源 / 缝两端状态互斥 / @图片N 对不上 / 规划类控制图被绑成画面参考 / 红线 🔴）；major/minor 修而不挡；一轮为限 + 连续两轮 FAIL 熔断摆给用户
- `seedance-prompt-review-skill/SKILL.md`：重构为「一、镜头表审」（★表确认前）+「二、成片审」A 段逐条可判定检查 / B 段缝审计批检 +「三、episode-master 验收」+「四、输出」
- `seedance-storyboard-skill/references/seedance-prompt-methodology.md`：v13 残留「三块散文」→「条头三行 + 围栏四块」，并**补 v13→v14 五行结构映射表**；过期的「v13 素材引用须知」（说「不写 @图片N，用真实文件名」，与 v14 体系直接矛盾）换成 V14 适配说明
- `seedance-storyboard-skill/templates/prompt-template.md`：条头母版 `ep{{NN}}-s{{XX}}-c{{N}}` → `### Cut {{N}} ｜ {{P0X}}`；四种缝型补齐；硬编码「即梦」→ `video_model_config.primary_model`；长度尺补外推规则
- `seedance-storyboard-skill/references/asset-binding.md`：`[控制图绑定]` 标题与 connector 母版路径对齐 V14（控制图无独立站，分镜师兼做）
- `seedance-storyboard-skill/references/dual-track.md`：断链 `script-breakdown 的 duration-pacing.md`（V14 无此站无此文件）→ 双真相源 `_shared/pacing-methodology.md` + `video_model_config`；九段术语换围栏四块术语
- `_shared/creative-brief-guide.md`：色彩锚三级
- `assets/reference-index.template.md`：加短串 / 声线锁 / `-vN` 变体
- `_shared/user-messages.md`：新增 ★表确认 / `~retake` 收案 / 内容类型档位；`~help` 与 `~status` 更新；**KAIKAI 开场重写**（六件事第 4 件）

**文档**
- `CHANGELOG.md`：顶部新增 v14.0 完整条目（八大块 + BGM 冲突裁决 + 定位修正 + 新增重写修改清单 + 保留清单），时间戳精确到秒
- `.claude/ARCHITECTURE.md` / `.claude/templates/file-index.template.md` / `episode-master.template.md` / `_shared/path-b-setup.md`：对齐 v14（8 个新 skill 在列、新增四行导航、真帧缝尾帧约定）
- `README.md` / `USAGE.md` / `AGENTS.md`：重写到 v14

## 删除（1 项）

| 路径 | 为什么 |
|---|---|
| `V13-FEATURE-SUMMARY.md` | 由 `V14-FEATURE-SUMMARY.md` 取代；删前已核与 `10-V13/V13-FEATURE-SUMMARY.md` 字节完全相同（9078B / md5 `588f41c4`），原件安全留存于 `10-V13/`，可随时取回 |

## ⚖️ BGM 冲突裁决（本版唯一「不采纳源库」的重大分歧）

源库 **3.0 完整版**把 BGM 写进提示词；**3.0 Lite 版**写「BGM 默认后期铺、提示词只写『无背景音乐』」——**与我们 V13 完全一致**。V14 采后者。

**但吸收了他们的技术理由**（这条理由本身比结论更值钱）：**不写 BGM 指令的条，模型会自作主张塞配乐——所以沉默也要显式写出来**。落地为：narrative 档每条围栏第 4 块固定「无任何背景音乐」+ 列出音效/环境声；音乐只由音乐总监设计、后期整条铺（Cut 块外的 🎵 后期铺乐注脚，V13 机制保留）。例外：`content_type=mv` 画面跟音乐走时，按 `sound-writing` 有乐句式写 BGM（禁点歌名与艺人）。

拼接工作流是这条裁决的根因：成片是 N 条视频拼接，每条自带 BGM 会与相邻条撞轨、整段没法剪。

## 🏷️ 术语债的处理方式（不做全库重命名）

移植文件里保留了源库站名，精确 grep：`motion-compile` 全库 **77 处 / 27 文件**。

**决策：不做全库重命名**，改为**在 8 个入口 SKILL.md 的 V14 适配说明里各加一行站名映射**。理由：① `references` / `templates` / `examples` 都经入口加载，被入口映射覆盖；② 保留旧名可与源库对读；③ 改 77 处的风险远大于收益。

映射表：

| 源库站名 | V14 真名 |
|---|---|
| `motion-compile` | **`seedance-storyboard-skill`**（分镜师第二步，编译 `video-prompts.md`） |
| `script-breakdown` | **导演拆解**（产物 `outputs/epNN/01-director-analysis.md`） |
| `control-image` | **控制图，V14 无独立站**，分镜师兼做、落 `outputs/epNN/control-prompts.md` |
| `character-design` / `scene-design` / `prop-design` | **`art-design-skill`**（服化道） |
| `director-grill` | **创作基准**（`assets/story/creative-brief.md`，编剧阶段产出） |

每行映射都带一句「**不要真的去调一个叫 motion-compile 的 skill**」+「本映射对本卡的 references / templates 一并生效」。`_v14升级工作台/` 内的 6 处历史参照不改（升级过程记录，非运行时文件）。

## 🔒 章节名保护清单（改名会断下游引用）

`seedance-storyboard-skill/SKILL.md` 的这些章节名**被下游硬引用，不得改名**（括号内为入站引用数）：

`[编译目标]`(10) · `[音乐隔离]`(6) · `[时长预算与定镜]`(6) · `[可判定自检]`(3) · `[底线提醒]`(2) · `[第一性原则]`(2) · `[画幅声明]`(1) · `[锁/变分层法]`(1) · `[落盘与重编号]`(1)

另：`asset-binding.md` 的 `[数量预算]` 与 `[人名与代称 · 六条铁律]`。

🔴 **特别提醒**：`[编译目标]` **不带**「· 四块」后缀。一致性自检脚本用的是 **set 精确成员判定**（`m.group(2) in S[x]`，`S[x]` 是 `set(...)`），不是子串匹配——把标题改成 `[编译目标 · 四块]` 会一次性断掉 9 处入站引用。

## 未动

- `bianju-skill/` 的 references、`music-design-skill/` 的 references、`compliance-review-skill` 红线清单、`audience-engagement-guide.md` 平台表、`episode-tagging.md`、`gemini-audio-analysis-guide.md`
- `art-design-skill/references/` 三份导演色卡（`director-color-cards.md` 78KB / `director-index.md` 26KB / `director-camera-language.md` 44KB）——V13 成果，一项不丢
- `故事板/` 125MB 案例素材（V7 设计参考，运行时不加载）
- 源库的 6.3G 图片素材一张不接（只接文本）
