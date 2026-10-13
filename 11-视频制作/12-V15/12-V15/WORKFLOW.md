# 工作流与需求管理 — 《躲进世界的角落里》

**最后更新**：2026-10-10 ｜ **当前工作流版本**：v1.0（ep01 提示词包制作）

> 本文件只管「做哪些事、什么时候做、做到什么算完」。每一站的具体规则在 `CLAUDE.md` 和各 skill 里，这里只放指针不复述（同一规则只定义一处）。

---

## 🎯 当前工作流：ep01 提示词包制作

### 工作流概述
- Claude 当制片人，调度 5 个创作 agent + reviewer，产出终点是「提示词包 + 音乐方案」，不生图、不生视频（CLAUDE.md L24）
- 每站同一个循环：出全量 → 审核或自检 → 交用户 ★确认 → 制片人在 `decisions.md` 确认记录追加一行 → 进下一站（CLAUDE.md L48、L167）
- 本项目配置（`.project-config.json`）：key_node（每阶段完成后等指令）｜ narrative ｜ lite 轻装档 ｜ 即梦/Seedance 单条上限 10 秒 ｜ 一步出图 gpt_image_2.5_flare ｜ 9:16

### 进度总览

| # | 需求 | 指令 | 状态 |
|---|---|---|---|
| 1 | 编剧创作 | `~write` | ✅ 2026-10-08 |
| 2 | 导演分析 | `~start ep01` | ✅ 2026-10-08 ｜ 拆解审 PASS |
| 3 | 服化道设计 | `~design ep01` | ✅ ★资产确认 2026-10-09 |
| 4 | 音乐设计 | `~music ep01` | ✅ ★音乐确认 2026-10-10 |
| 5 | 分镜编写（两步） | `~prompt ep01` | ⏳ ★表确认 2026-10-10 ｜ 第二步编译进行中 |
| 6 | 出图/出片验收 | 用户带图或视频回来 | 按需 |
| 7 | 返工 | `~retake` | 按需 |

---

## 📋 需求清单

### 需求1–3：编剧 / 导演 / 服化道（已完成）
规则见 CLAUDE.md L180–L184。只在用户提修改时重开，走 [内容修订]（CLAUDE.md L195），改完按审核工作流重审一次。

### 需求4：音乐设计
**触发**：用户发 `~music ep01`
**执行步骤**：
1. 进站前查 `outputs/ep01/feedback-to-upstream.md` 有没有待处理项（CLAUDE.md L228）
2. 音乐总监只读讲戏本的音乐方向块，不读剧本（CLAUDE.md L186）
3. 本片约束（decisions.md L20、L25、L46）：只给后半段；入点在「我也不是真的要离开你们」那口气之后（Cut8 内）；「我们都喜欢躲进世界的角落里」允许一次不大的抬升；末句之前收掉；人声身份 = 一个同类，不是孩子也不是父母；三版歌词等用户选
4. 轻装档不派音乐审，音乐总监自检，用户确认时看（CLAUDE.md L52、L133）
**验收标准**：
- `assets/music/music-design.md` 有 `# ===== ep01 =====` 块（CLAUDE.md L156）
- music-design.md 里引用的每个文件盘上都在（`ls` 核过，不凭 agent 汇报）
- 用户选定一版歌词
- `decisions.md` 确认记录追加一行

### 需求5：分镜编写（两步）
**触发**：`~prompt ep01`（也可 `~prompt ep01 表` 只做到表、`~prompt ep01 编译` 从已确认的表续）
**执行步骤**：
1. 第一步 · 镜头表 → `outputs/ep01/02-shot-table.md`；轻装档不派表审，但 ★表确认 必须用户点头（CLAUDE.md L119、L189）
2. 第二步 · 编译 → `video-prompts.md`（顶部声明 9:16 一次）；每个 P0X 编完更新 `assets/continuity-ledger.md`；全集编完出 `episode-master.md`
3. 成片审（seedance-prompt-review + 缝审计批检）→ ★交付确认（CLAUDE.md L190）
**本片硬约束**：
- 12 条的条边界由导演定，分镜师只在条内排镜，不增删条、不改边界和接缝（decisions.md L26）
- 恒定层取 `visual-style.md` v1.1 锚句（feedback-to-upstream #2）
- 每条都要答得出「这条的暖黄在哪、离他多远」（decisions.md L19）
- 用美术做尺度，不用镜头做尺度（decisions.md L18）
- 全片红线 7 条（decisions.md L53–L59）
**验收标准**：`video-prompts.md` 与 `episode-master.md` 同时存在 + 成片审 PASS + `00-quality-report.md` 落盘 + 交付确认记录

### 需求6：出图/出片验收（用户侧动作）
**触发**：用户把生成的图或视频放回项目，或描述生成结果
**执行步骤**：
1. 对照该资产提示词里给用户的检查点逐张核
2. 合格的按 `reference-index.md` 文件名存进 `assets/visual/images/`
3. 不合格 → 需求7
**验收标准**：验收结论写进 PROJECT_STATUS；资产图定稿写进 decisions 确认记录

### 需求7：返工 retake
**触发**：`~retake` 或用户带翻车素材回来
**执行步骤**：按 CLAUDE.md L193 五出口处理；用户报症状要能定位到哪条/哪张 + 哪不对 + 已抽几次（CLAUDE.md L214）
**验收标准**：源文件就地更新并标版本；涉及已审产物的重审一次；属于 Bug 性质的当轮写进 BUG_FIX_LOG.md

---

## 🔄 工作流切换机制

- **v1.0 → v2.0**：ep01 ★交付确认后，进入「用户生成 + 返工」阶段，主循环换成需求6/7
- **做 ep02 或新片**：开新版本，重写需求清单和进度总览
- **出片后人物脸飘**：不切版本，但 `image_pipeline` 改 dual 需用户拍板（decisions.md L47）

---

## 🎬 Claude 工作指引

### 每次启动时
1. 读 `PROJECT_STATUS.md` → `WORKFLOW.md` → `CLAUDE.md`
2. 交叉核对：`decisions.md` 确认记录最后几行 + 盘上产物（CLAUDE.md L143–L160 路由）。和 PROJECT_STATUS 不一致 → 以 decisions + 盘上产物为准，当轮修 PROJECT_STATUS
3. 主动汇报当前状态和下一步，不等用户问

### 执行中
- 用户提需求先对需求清单；对不上 → 问：A 临时一次 / B 改现有需求 / C 新增需求
- 每个 ★确认当轮记 decisions；状态变化当轮改 PROJECT_STATUS；修完 Bug 当轮写 BUG_FIX_LOG

### 收尾
- 更新 PROJECT_STATUS 顶部「当前阶段 / 当前焦点 / 待办」三块和更新日志，不能只追加日志

### 禁止行为
- ❌ 只信 PROJECT_STATUS 判进度，不核 decisions 和盘上产物（2026-10-10 教训）
- ❌ 没看到 `review/` 下的报告文件就说「已过审」（2026-10-09 教训）
- ❌ agent 汇报「已落盘」就当真，不 `ls` 核它引用的文件（2026-10-10 音乐中断教训）
- ❌ 写进提示词的数字没有上游出处；改一个数不查连带项（门把手 160 教训）
- ❌ 用广角、仰角、变形镜头表现「巨大」（decisions.md L18）
- ❌ 碰全片红线 7 条（decisions.md L53–L59）
- ❌ 制片人自己写内容、生图、生视频；创作 agent 自审
- ❌ 不经用户改已确认的上游产物（CLAUDE.md L131）
- ❌ 编造数据；找不到来源就标「待确认」
- ❌ 用 `rm` 删文件；删除必须用户同意并进回收站

---

## 📝 需求变更记录

### v1.0（2026-10-10）
- 首次建立。需求1–7 由 CLAUDE.md v15 五阶段 + retake + 用户侧验收整理而来；建立时 ep01 已走完需求1–3
