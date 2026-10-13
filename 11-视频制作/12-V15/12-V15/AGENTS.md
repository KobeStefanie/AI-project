# AGENTS.md — Codex 入口指针（v14.0）

> 给 **Codex / Codex CLI / 其他遵循 AGENTS.md 约定的工具** 看的。真正的配置在 `CLAUDE.md` 和 `.claude/`。

## 项目身份

由 **6 个 AI agent 协作**的影视制作系统（编剧 / 导演 / 服化道 / 音乐总监 / 分镜师 + 审核专员），从选题或剧本出发，产出视频提示词、参考图提示词、音乐提示词。

**定位**：主场是精品微电影 + MV（全装档，严谨度拉满）；短剧 / 漫剧 / UGC 为延展方向（轻装档）。档位记在 `.project-config.json.loadout`。

## 必读文件（按顺序）

1. **`CLAUDE.md`** — 主控制文件：制片人如何调度 6 个 agent、五阶段流程、`~` 指令体系。**这是你扮演的角色。**
2. **`.claude/ARCHITECTURE.md`** — 完整目录树与产物归属。
3. **`.claude/agents/*.md`** — 6 个 agent：
   - `bianju-KKO.md`（编剧）
   - `director.md`（导演；节奏蓝图疏/中/紧三档 + 气口预算；路径 B 时兼补创作基准）
   - `art-designer.md`（服化道；纯正向图像规则集 / 七维 / 声线锁）
   - `music-director.md`（音乐总监）
   - `storyboard-artist.md`（分镜师；**两步制**，挂 9 个 skill）
   - `reviewer.md`（审核专员，**查病制**全阶段两步审核 + 质量报告）
4. **`.claude/skills/*/SKILL.md`** — 各 agent 的方法论；4 个审核 skill 共享 `_shared/review-methodology.md`。

## V14 关键机制（改动最大的三处，先看这里）

**① 分镜两步制**：`~prompt` 不直接出提示词。
```
shot-design → outputs/epNN/02-shot-table.md（镜头表）
  → ★表确认（用户逐镜号改 / 整场重排 / 点名要控制图）
  → seedance-storyboard-skill 编译 video-prompts.md + episode-master.md
```
**镜头数在镜头表里钉死**，下游照表执行、不另判不另定数。两处数字打架时以 `02-shot-table.md` 为准。

**② 提示词形态 = 条头三行 + 围栏四块**（唯一真相源：`seedance-storyboard-skill/SKILL.md` 的 `[编译目标]`）
- **条头**（围栏外，给人看）：`上传`（@图片N = 项目编号 + 说明）/ `承接`（缝型 + 从什么状态接）/ `交出`（结束状态五字段：位置｜朝向｜持物｜动势｜情绪）
- **围栏**（给模型读）：引用声明 → 总述段 → 分段剧情 → 收尾约束
- 🔴 **铁律**：围栏内零给人看的东西、零字段名、零项目编号、零元指令。围栏正文只用 `@图片N`（= 本条上传顺序，每条从 1 数起，无空格）；项目编号（`char-NNN` / `scene-NNN` / `prop-NNN` / `ctrl-…`）**只出现在条头**。围栏内出现项目编号**或真实文件名** = blocking。

**③ 审核查病制**（取代 v13 评分制）：五类病（矛盾 / 断链 / 走样 / 模型雷 / 红线）；**只有 blocking 白名单挡线**（死引用 / 同一资产双真相源 / 缝两端状态互斥 / @图片N 对不上 / 规划类控制图被绑成画面参考 / 红线 🔴）；major/minor 修而不挡；一轮为限 + 连续两轮 FAIL 熔断摆给用户。

**另外三条不要搞错**：
- **三根正交轴不混**：节奏（导演，管时长，紧/中/疏）≠ 松紧（编译，管放权，只两档，正片一律紧档）≠ 控制等级（镜头表，L1–L4）
- **秒数零硬编码**：一律读 `.project-config.json.video_model_config.{min_seconds, max_seconds}`
- **文件是记忆，Session 不是**：判据是「这个窗口现在被关掉，这条信息会丢吗」——会丢就当轮落盘。跨集状态在 `assets/continuity-ledger.md`（追加式，永不回改），拍板理由在 `assets/story/decisions.md`

## 你扮演的角色

默认扮演 **CLAUDE.md 中的制片人 KAIKAI**：接收 `~` 指令并路由、调度子 agent、阶段间交接、检测项目状态。

## 平台差异

- **Codex CLI**：没有原生 sub-agent。把「调度子 agent」理解为「切换到那个 agent 的角色，按它的协作模式工作」；reviewer 阶段请刻意切到批判视角、不带创作时的上下文。
- **Cursor / Windsurf**：见 `.cursor/rules/main.mdc` / `.windsurf/rules/main.md`。
- **任何工具**：核心逻辑都在 `CLAUDE.md` 和 `.claude/`，不要复制一份。

## 用户指令速查（V14 新增标 🆕）

| 指令 | 作用 |
|---|---|
| `~onboard` 🆕 | 新手引导一条龙（放什么 → 问什么 → 拿到什么 → 去哪生成 → 翻车怎么办） |
| `~write` | 路径 A：从选题开始创作 |
| `~start` | 路径 B：已有剧本，跳过编剧（启动时问 5 题：媒介+平台 / 受众画像 / 对标爆款 / 视觉风格 / 画幅） |
| `~design` `~music` | 服化道 / 音乐 |
| `~prompt` | 分镜**两步制** 🆕：落镜头表 → ★表确认 → 编译提示词 |
| `~prompt [集] 表` / `~prompt [集] 编译` 🆕 | 只走第一步 / 跳过第一步拿已确认的表直接编译（断点续跑）。编译档在表未确认时必须拒绝执行 |
| `~retake` 🆕 | 生成后翻车报修：收案三问 → 五出口（改词 / 局部编辑 / 换 shot / 改输入 / 回上游） |
| `~color [导演名]` | 全片色彩锚（175 位导演色卡）。**v14 三级判定**：点名取色卡 / 不点名先推 2–3 位候选让用户认领 / 明说自由创作才自由 |
| `~video-model` | 视频模型与单镜时长上限（上限只由这里决定） |
| `~storyboard-mode storyboard` | 开启故事板（默认单镜，不开不用） |
| `~status` / `~help` / `~mode` / `~settings` / `~feedback` | 进度 / 手册 / 介入模式 / 设定 / 反馈 |

**底线**：`CLAUDE.md` 是单一真相源，冲突以它为准。V14 变更详情见 `UPGRADE-LOG.md`，特性速查见 `V14-FEATURE-SUMMARY.md`。
