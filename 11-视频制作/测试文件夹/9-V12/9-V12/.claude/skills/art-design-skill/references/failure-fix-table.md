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
| 4 | 视觉风格基准段没有嵌入提示词开头 | creative-brief.md 未读或风格段未复制 | 打开 assets/story/creative-brief.md，找到「全片视觉风格基准段」，逐字复制到提示词第一段 | 如 creative-brief.md 不存在，停下来告知制片人先完成创作基准 |
| 5 | 场景宫格格子数与实际场景数不匹配 | 宫格规格选错 | 重新按规则选：≤9场→3×3，10-12场→3×4，13-16场→4×4 | 检查导演场景清单里的场景总数 |
| 6 | reference-index.md 没有同步更新 | 漏写了编号记录 | 打开 assets/reference-index.md，按 template 格式为本次新增的角色/场景/道具各追加一行 | 参考 assets/reference-index.template.md 的格式 |
| 7 | 跨集变体（如换装/老化）没有在 assets/visual/changelog.md 记录 | 跨集变体归档流程遗漏 | 在 changelog.md 追加变体记录：`ep0X | 角色名 | 变体描述 | 触发剧情` | 参考 CLAUDE.md [资产归档规则] 中 changelog.md 维护规则 |
| 8 | 关键道具提示词缺少多角度展示或比例参考 | 道具格式规范未执行 | 补写：正面+侧面+顶视（视道具选择），角落加比例参考物（硬币/手掌） | 参考 art-design-skill/SKILL.md 第四步关键道具格式 |

## 项目特定规则（~feedback --learn 累积）

（由 `~feedback --learn` 指令自动追加）
