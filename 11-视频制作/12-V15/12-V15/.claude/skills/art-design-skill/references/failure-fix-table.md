---
name: art-design-failure-fix-table
description: 服化道常见失败模式对照表（v12.0）。人物/场景/道具设计遇到问题先查此表。
---

# 服化道失败修复对照表

| # | 失败现象 | 根因 | 优先修复动作 | 二次修复 |
|---|---------|-----|-------------|---------|
| 1 | 人物提示词里有关键词堆叠（如"优雅,知性,气质"） | 违反叙事描述式原则 | 改成完整段落叙述：「她站在...，身着...，眼神...」 | 参考 art-design-skill/examples/ 下的示例 |
| 2 | 场景提示词里出现了「一个穿白衬衫的男人」等角色外貌描述 | 违反锚定资产纪律（v12.0） | 改用留空槽：「画面中有人物，留空等后期引用」，或方向描述：「靠窗坐着一个背影」 | 检查 art-design-skill/SKILL.md [锚定资产纪律] |
| 3 | 人物提示词没有「左半边面部特写+右半边三视图+白底」格式 | 输出格式规范未执行 | 按标准格式重写：明确说明「左侧：面部特写；右侧：正/侧/背三视图；纯白背景」 | 参考 art-design-skill/examples/character-prompt-examples.md |
| 4 | 视觉风格基准段没有嵌入提示词开头 | visual-style.md 未读或层 1 通用基准段未复制 | 打开 assets/story/visual-style.md，把「层 1 通用基准段」逐字复制到每张提示词第一段（一字不许改写、精简、换同义词） | 如 visual-style.md 不存在，降级读 creative-brief.md 的「全片视觉风格基准段」（v13 老项目）；仍缺则停下告知制片人先让上游补齐 |
| 4b | 角色板或道具板里出现了某个空间的陈设（柜台、月份牌、灯箱） | 把层 2 场域锚句错嵌进了角色/道具板 | 删掉场域锚句——**只有场景板**嵌本场景所属那一句；角色板/道具板的年代形制从字段表「时代与世界锚」落 | 参考 `_shared/visual-style-guide.md > 取用规则` |
| 4c | 外景条里出现了内景陈设（或反之） | 全片只用了一句总锚句，或场景嵌错了场域 | 按场景所属场域改嵌对应那一句；场景对不上任何场域 → 停下请导演补该场域锚句，不要自己即兴编 | 参考 `_shared/visual-style-guide.md > 场域划分纪律` |
| 5 | grid_mode=single 却出了宫格图 / 提示词里有「九宫格、3x3、格1」字样 | 沿用旧版宫格模板 | 每个场景、每个道具各写一条独立提示词；删掉所有宫格字样 | 读 .project-config.json.image_model_config.grid_mode 确认；NxM 时格数 = N×M 不随场景数变 |
| 6 | reference-index.md 没有同步更新 | 漏写文件名记录 | 打开 assets/reference-index.md，为本次新增的角色/场景/道具各追加一行（文件名 \| 一句话用途 \| 首次出现集数） | 参考 assets/reference-index.template.md |
| 7 | 跨集变体（如换装/老化）没有在 assets/visual/changelog.md 记录 | 跨集变体归档流程遗漏 | 在 changelog.md 追加变体记录：`ep0X | 角色名 | 变体描述 | 触发剧情` | 参考 `.claude/ARCHITECTURE.md > 资产归档规则` |
| 8 | 关键道具提示词缺少多角度展示或比例参考 | 道具格式规范未执行 | 补写：正面+侧面+顶视（视道具选择），角落加比例参考物（硬币/手掌） | 参考 art-design-skill/SKILL.md 第四步关键道具格式 |

## 项目特定规则（~feedback --learn 累积）

（由 `~feedback --learn` 指令自动追加）
