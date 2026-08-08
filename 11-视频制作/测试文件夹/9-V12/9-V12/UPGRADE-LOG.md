# V11 → V12 升级日志

> 升级日期：2026-07-07  
> 基础版本：V11（8 -V11/）  
> 升级版本：V12（9-V12/）  
> 升级目标：移植 Seedance 2.0 参考文档的6个核心设计点，提升架构智慧和制作质量

---

## 不动的内容（V11 已修复，V12 原样保留）

- ✅ video_model_config（4个能力标志：image_ref/video_ref/audio_ref/full_context）
- ✅ image_model_config（primary_model + grid_mode）
- ✅ 心智透明原则（场景参考图连续性：每Cut必须带场景@引用）
- ✅ 画幅锁定防传染机制（v7.0.2）
- ✅ 场景九宫格独立@编号规则
- ✅ 视频提示词严禁背景音乐描述

---

## 新增文件（7个）

### `.claude/agents/reviewer.md`（升级点3）
- **改了什么**：新建独立审核 agent，从 director agent 中完全拆分出审核职责
- **为什么改**：director 既创作又审核是自审，有盲点；独立 reviewer 每次空白上下文开始，更客观

### `assets/reference-index.template.md`（升级点2）
- **改了什么**：设计完整的四段格式模板（顶部风格段/角色段/场景段/道具段/音频段）+ @编号体系
- **为什么改**：V11 reference-index.md 是空壳，各 agent 各自乱引用；新格式统一所有 @编号

### `.claude/skills/seedance-storyboard-skill/references/failure-fix-table.md`（升级点4）
- **改了什么**：新建分镜师常见失败模式对照表（10条）
- **为什么改**：快速诊断常见错误，不靠reviewer反馈找根因

### `.claude/skills/director-skill/references/failure-fix-table.md`（升级点4）
- **改了什么**：新建导演常见失败模式对照表（8条）

### `.claude/skills/art-design-skill/references/failure-fix-table.md`（升级点4）
- **改了什么**：新建服化道常见失败模式对照表（8条）

### `UPGRADE-LOG.md`（本文件）
### `V12-FEATURE-SUMMARY.md`（新增特性速查）

---

## 修改文件（8个）

### `.claude/agents/director.md`
- **frontmatter**：skills 从5个减为1个（只保留 director-skill，移除4个review skill）
- **description**：删除"审核"职责描述
- **[任务]**：删除阶段二自审/三/四/五审核/收官复盘，只保留阶段二执行
- **[角色]**：改为单一职责（创作）
- **[协作模式]**：skill加载自检改为1个skill，删除"审核FAIL等待重审"流程
- **[质量综合报告]**：整段删除（已移至 reviewer.md）

### `CLAUDE.md`
- **[审核工作流]**：`director 两步审核` → `reviewer agent 两步审核`；目的说明加入"创作与审核分离"
- **[指令集]** `~feedback`：新增 `~feedback --learn` 分支（反馈固化到对应skill末尾）

### `.claude/skills/seedance-storyboard-skill/SKILL.md`
- **新增 [锁/变分层法] 段落**：在 [技能说明] 之后插入，作为写提示词的第一步思考框架
- 包含：恒定层/可变层定义 + 自检方式 + ⚠️说明（不等于省略场景@引用）

### `.claude/skills/seedance-storyboard-skill/seedance-prompt-methodology.md`
- **[第一性原则]** 段落：在「参考图已见原则」后追加「锁/变分层法」配套说明

### `.claude/skills/art-design-skill/SKILL.md`
- **第三步（场景环境提示词）**：在「视觉风格统一」规则后追加「锚定资产纪律」段落
- 包含：3种合规处理方式（留空槽/方向描述/场景即资产）+ 自检

### `.claude/agents/storyboard-artist.md`
- **[协作模式] 第4步**：追加 `遇到问题先查 failure-fix-table.md`

### `.claude/agents/art-designer.md`
- **[协作铁律]**：追加「锚定资产纪律」和「同步维护 reference-index」两条规则

### `CHANGELOG.md`（顶部追加 v12.0 条目）
