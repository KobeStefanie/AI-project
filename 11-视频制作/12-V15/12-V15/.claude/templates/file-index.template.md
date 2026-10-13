# 📋 凯凯AI影视项目 · 找文件速查表
> 制片人自动生成，每次启动自动覆盖。打开这个文件就能找到所有产出。

<!--
生成规则（制片人读，写入产物时删掉本注释块）：
- 只列**实际存在**的文件；不存在的整行不写，避免用户点进去是空的
- 有几集列几集
- 故事板模式：single 布局文件名是 P0X-CutN-storyboard-prompt.md，宫格布局是 P0X-storyboard-prompt.md，按 image_model_config.grid_mode 列
- 进度符号：✅ 完成 / 🔄 进行中 / ⏳ 未开始 / ⏭ 已跳过
-->

---

## 🎬 视频生成提示词（最常用）
- **ep01 镜头表**（整集每一镜的设计图纸，确认后才编提示词；改镜头回这里改）→ outputs/ep01/02-shot-table.md
- **ep01 视频提示词**（逐 Cut：条头写传哪几张图，围栏整段复制即生成）→ outputs/ep01/video-prompts.md
- **ep01 说明书**（生成顺序 / 每条传什么 / 试片看什么 / 翻车回哪）→ outputs/ep01/episode-master.md
- **ep01 控制图提示词**（仅点名要过控制图时才有）→ outputs/ep01/control-prompts.md

## 🖼️ 生图参考提示词（生成角色/场景/道具参考图）
- **人物** → assets/visual/character-prompts.md
- **场景** → assets/visual/scene-prompts.md
- **道具** → assets/visual/prop-prompts.md
- **素材清单**（文件名 / 短串 / 声线锁——生成的 PNG 按这里的名字存到 assets/visual/images/）→ assets/reference-index.md

## 🎨 故事板提示词（仅故事板模式的集数）
- **ep01 P01** → outputs/ep01/storyboards/P01-storyboard-prompt.md

## 🎵 音乐
- **原创音乐方案 + Suno 提示词** → assets/music/music-design.md
- **市面音乐推荐** → assets/music/music-recommendations.md
- **歌词草稿**（如有 OST）→ assets/music/lyrics-drafts.md

## 📝 剧本 & 创作文档
- **分集剧本** → script/ep01-xxx.md
- **创作基准**（情感蓝图 + 导演视野）→ assets/story/creative-brief.md
- **风格基准**（通用基准段 / 场域锚句 / 色彩锚——每条提示词开头逐字用的那段）→ assets/story/visual-style.md
- **剧本设定**（平台 / 受众 / 对标 / 视觉风格 / 画幅 / 色彩锚 / 档位）→ assets/story/script-settings.md
- **确认与拍板记录**（每次你点头的结论和理由）→ assets/story/decisions.md
- **角色档案** → assets/story/character-profiles.md
- **故事大纲** → assets/story/story-outline.md

## 🧾 连续性台账
- **跨镜跨集人物状态账本**（每个 Cut 结束时谁在哪、拿什么、什么情绪；未解线头）→ assets/continuity-ledger.md

## 📊 审核与质量报告
- **ep01 审核报告**（每个审核点一份，问题定位 + 证据 + 回哪修）→ outputs/ep01/review/
- **ep01 整片复盘** → outputs/ep01/00-quality-report.md

---
## 🗺️ 当前进度
| 阶段 | ep01 |
|------|------|
| 编剧 | ✅ / 🔄 / ⏳ / ⏭ |
| 导演分析 | |
| 服化道 | |
| 音乐 | |
| 镜头表（★表确认） | |
| 分镜编译 | |

台账：最后登记到 epNN-P0X
未处理上游反馈：N 条（见 outputs/epXX/feedback-to-upstream.md）
