# V12 新增特性速查表

> 从 V11 升级到 V12 新增了什么？未来做 V13 前先看这里。

---

## 特性1：锁/变分层心智模型

**是什么**：写分镜提示词时，脑内先把信息分两层——恒定层（角色外观/场景/风格）用@图片引用解决，可变层（动作/运镜/情绪增量）才写文字。

**在哪用**：分镜师写每条 Cut 提示词时自动执行这个思考框架。

**在哪找**：
- `.claude/skills/seedance-storyboard-skill/SKILL.md` → `[锁/变分层法]`
- `.claude/skills/seedance-storyboard-skill/seedance-prompt-methodology.md` → `[第一性原则]` 里的「锁/变分层法」

**注意**：不等于省略场景@引用——心智透明原则依然有效（每Cut必须带场景图）。

---

## 特性2：reference-index @编号体系

**是什么**：全片素材统一索引，服化道每产出一个角色/场景/道具，立即在此追加编号记录；分镜师引用时用 @char-001 / @scene-002 等编号，不重复描述外观。

**在哪用**：服化道每次产出时维护；分镜师每次写 Cut 时查引用。

**在哪找**：
- `assets/reference-index.md`（实际索引文件，每集维护）
- `assets/reference-index.template.md`（四段标准格式模板）

**四段结构**：顶部视觉风格基准段 / 角色段 / 场景段 / 道具段 / 音频段。

---

## 特性3：独立 reviewer agent（防自审）

**是什么**：审核职责从 director agent 完全独立为单独的 reviewer agent。director 专注创作，reviewer 专注审核，每次空白上下文开始，更客观。

**在哪用**：制片人在每个阶段完成后调用 reviewer agent 而不是 director 做审核。

**在哪找**：
- `.claude/agents/reviewer.md`（新建）
- `.claude/agents/director.md`（已删除审核职责）

---

## 特性4：3份失败修复对照表

**是什么**：结构化的「失败现象→根因→优先修复动作→二次修复」表格。遇到问题查表，不靠审核反馈猜根因。

**在哪找**：
- 分镜师：`.claude/skills/seedance-storyboard-skill/references/failure-fix-table.md`（10条）
- 导演：`.claude/skills/director-skill/references/failure-fix-table.md`（8条）
- 服化道：`.claude/skills/art-design-skill/references/failure-fix-table.md`（8条）

---

## 特性5：锚定资产纪律

**是什么**：场景提示词里不得重新描述已有角色/道具外观。三种处理：留空槽 / 方向描述 / 场景即资产。

**在哪用**：服化道写场景提示词时自动执行。

**在哪找**：
- `.claude/skills/art-design-skill/SKILL.md` → 第三步场景设计末尾的 `🔴 锚定资产纪律`
- `.claude/agents/art-designer.md` → 协作铁律最后两条

---

## 特性6：~feedback --learn 规则固化

**是什么**：在原有 `~feedback` 基础上新增 `--learn` 参数。用户提交反馈时，制片人同时把规则固化到对应 agent 的 skill 文件末尾，下次不再犯同类错误。

**怎么用**：
```
~feedback --learn 分镜师每次写连续对话场景时，下一个Cut要记得带场景参考图
```

**在哪找**：
- `CLAUDE.md` → `[指令集]` → `~feedback --learn` 段落
- 执行后会在对应 skill 文件末尾追加「项目特定规则」段

---

## V12 vs V11 快速对比

| 维度 | V11 | V12 |
|-----|-----|-----|
| 审核架构 | director 既创作又审核（自审） | director 创作，reviewer 审核（分离） |
| 提示词组织 | 无明确框架（易重复描述） | 锁/变分层（恒定层@引用，可变层写文字） |
| 素材引用 | 各agent自行命名引用（混乱） | 统一@编号体系（reference-index） |
| 场景提示词 | 可能重新描述已知角色外观（漂移） | 锚定资产纪律（禁止重新描述） |
| 失败诊断 | 靠审核反馈（慢） | failure-fix-table（快速查表） |
| 知识积累 | 用户纠正=一次性，下次还犯 | ~feedback --learn（固化到skill） |
| 不变的核心 | — | 心智透明/画幅锁定/视频模型配置/音乐红线等所有V11已修复bug |
