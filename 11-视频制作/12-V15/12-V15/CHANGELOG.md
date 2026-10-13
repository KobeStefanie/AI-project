# Changelog — 凯凯 · AI 影视制作团队

本项目所有版本变更记录于此。最新版本在最上。

> **版本管理规范**（自 v7.0.3 起强制；v13 起本段即单一真相源，CLAUDE.md 不再重复）：
> - 所有版本条目时间戳**精确到秒**，格式 `YYYY-MM-DD HH:MM:SS UTC+08:00`（例 `2026-05-24 03:43:00 UTC+08:00`），写入时取合并当时的精确时间
> - `assets/visual/changelog.md` 的跨集变化记录同样精确到秒
> - CLAUDE.md / agents / skills 顶部元信息里的「更新时间」字段同样精确到秒
> - v7.0.3 之前的历史条目不追溯（当时未记录精确时间），保留原日期格式

> **🔴 每次升级完成前必做的六件事**（v13 起制度化，缺一件就算没升完）：
> 1. **本文件顶部加新版本条目** —— 改了什么、为什么改、删了什么，写清到下次能据此判断能不能回滚
> 2. **写 `UPGRADE-LOG.md`** —— 上一版 → 本版的新增 / 修改 / 删除文件清单，逐条说明原因
> 3. **写 `V{N}-FEATURE-SUMMARY.md`** —— 特性速查（是什么 / 在哪用 / 在哪找）+ 与上一版的对比表
> 4. **更新 KAIKAI 开场** —— `_shared/user-messages.md > 欢迎 / 初始化`，把本版真正的新亮点写进去（新用户对这套工作流的第一印象全在这里）
> 5. **更新面向人的三份文档** —— `README.md`（版本号 + 亮点）/ `USAGE.md`（新指令、行为变化）/ `AGENTS.md`（agent 数量、流程）
> 6. **一致性自检** —— grep 全项目确认：旧口径零残留、agent 的 skills 路径全部可达、CLAUDE.md 引用的章节与文件都存在、体积没有反弹
>
> 为什么制度化：v11 发版时忘了写 changelog（v11 与 v10 的本文件 MD5 完全相同），导致 v12 升级时只能从别处反推 v11 改了什么；v12 又忘了改 CLAUDE.md 头部版本号。归档不是仪式，是下一次升级的唯一依据。

---

## v14.1 — 2026-09-29 00:00:00 UTC+08:00（稳定化优化 · 输入路由扩展 · 剪辑思维原则 · PRD 归档）

**主题**：在 v14.0 Seedance 3.0 集成完毕后的稳定化轮次。不加新功能，只把访谈中发现的三处不够精确的地方收紧，并新建 `_PRD/` 需求文档，为下一次模型突破后的升级 AI 留好接口。

### 🔧 修复

- **reference-index.template.md 道具占位符重名**：`prop-001` 与 `prop-002` 两行的文件名占位符原本都是 `prop-[道具名].png`，完全相同。修正为 `prop-[道具名A].png` 与 `prop-[道具名B].png`，下游按模板建索引时不再产生重复行。

### ✨ 优化

- **input/选题/ 路由扩展**（CLAUDE.md + ARCHITECTURE.md）：原路由只说「选题素材」，实际上用户从以下材料起笔都很常见：创意碎片、故事标题、故事梗概、多章节小说节选、大纲草稿。现在两处文档都明确「凡能触发编剧起笔的材料一律放 选题/，编剧按内容自行判断深度」，避免用户不确定该放哪里。
- **时长预算原则 + 剪辑思维**（CLAUDE.md [模型授权原则] + shot-design/SKILL.md [第一性原则]）：在「无戏剧断点不拆条」原则后新增「剪辑思维 × 榨干模型能力」段。核心：镜头设计从出口倒推（先想切出去接什么、给下一条留什么），「榨干」是把最值得放大的瞬间坐实而不是填满秒数。附反例——两人对话平均分时间 vs 给 B 最在乎的回答多一拍。

### 📋 新增

- **`_PRD/V14-PRD.md`**：结构化需求文档，记录用户意图、不可动的设计决策、内容美学偏好、待办候选、更新触发条件，以及面向下一次升级 AI 的访谈协议。下次有模型突破时，升级 AI 应先读此文档再开始任何工作。

---

## v14.0 — 2026-09-09 17:26:47 UTC+08:00（融合开源 Seedance 分镜师 3.0 · 镜头表 · 工艺卡 · 台账 · retake · 查病审核）

**主题**：把开源「Seedance 分镜师 3.0」（完整版 + Lite 版）的工艺内核**器官移植**进我们的 6 agent 架构。保留我们的分工、`~` 指令、目录、175 位色卡、编剧流程、模型无关时长；移植他们的镜头表中间层、提示词结构、五张工艺卡、连续性台账、返工站、查病式审核。用户全权授权：冲突优先用他们的，我判断我们更能出好作品的保留。

**定位修正**：主场是**精品微电影 + MV**（全装档，严谨度拉满）；短剧 / 漫剧 / UGC 为延展方向（轻装档）。

### 🎯 八大块

1. **分镜两步制 + 镜头表**：`~prompt` 先出 `outputs/epNN/02-shot-table.md`（场级空间地图块 + 场阐述 + 逐镜十项 + 条末结束状态五字段 + 本场资产需求 + 风险上锁提示）→ **★表确认**（用户逐镜号指着改 / 整场重讲 / 点名控制图）→ 才编译成提示词。想戏和翻译分开：改表是几行字，改提示词是重来。新增 skill `shot-design/`。
2. **提示词改「条头三行 + 围栏四块」**（采 Lite 版形态）：条头给人看——上传（@图片N = 哪张图）/ 承接（缝型 + 从什么状态接）/ 交出（结束状态五字段：位置 / 朝向 / 持物 / 动势 / 情绪）；围栏给模型读——引用声明 → 总述段 → 分段剧情 → 收尾约束。**围栏第一个字就是模型读的第一个字**，用户传完图整段复制即生成、零替换。修掉 V13 三块散文里混着「📤 上传清单」等给人看的标记、用户容易一起粘进去的隐患。B 轨（`镜头N` 无秒数 + 配重语言）为主，A 轨时间戳只给一镜到底的因果段落划分（用户拍板）。
3. **五张工艺卡**：`camera`（六槽运镜句式 + 视场角锚点）/ `blocking`（站位七要素 + 180° 轴线 + 首帧占位锁）/ `performance`（五支柱任务制表演 + 表演档案 + 眼活）/ `lighting`（光向五要素 + 世界内光源五槽 + 物理锁）/ `sound-writing`（声音四要素句式 + 口型纪律 + 密度三档）。我们的九原则是价值观，这五张卡是手艺——「她很难过」写成「泪膜在下睑缘反光却悬而不落」，模型只认可观测的物理事实。分镜师编译时五维必答，不许静默跳过。
4. **连续性台账 `continuity`**（用户点名必须做好）：`assets/continuity-ledger.md` 六块（开账基线 / 逐条落幅五字段 / 状态变化 / 场末快照 / 未解线头 [开]·[关闭于] / 跨集 ending state）+ 12 项状态机 + 缝审计八查 + 「隔夜结痂合法、同刻自愈非法」防误杀通则。追加式永不回改；「窗口可以关，台账不会忘」。
5. **retake 返工站**（`~retake`）：生成后翻车带回来——收案三问 → 诊断（词的问题 / 局部要改 / shot 过载 / 上游根子 / 反物理）→ 五出口（改词 / 局部编辑 / 换 shot / 改输入 / 回上游）。金句入库：「同一条抽满 15–20 次仍不过，问题在 shot 不在词」「一致性崩优先查参考，改词是错方向」「单变量纪律，改不动先 re-roll」。
6. **审核改查病制**：取代 V13 评分门槛（均分≥8 容易在 7.9/8.0 上卡住，且 reviewer 会做品味判断）。只查**五类病**——矛盾 / 断链 / 走样 / 模型雷 / 红线；**只有 blocking 白名单挡线**（死引用 / 同一资产双真相源 / 缝两端状态互斥 / @图片N 对不上 / 规划类控制图被绑成画面参考 / 红线 🔴）；major/minor 修而不挡；**一轮为限 + 熔断**（连续两轮 FAIL 摆给用户裁决）；已确认的上游产物只当只读基准，毛病记「上游观察」。审核报告落盘 `outputs/epNN/review/`。全装档五审核点，轻装档只派资产审 + 成片审。
7. **visual-style 恒定层之源 + 色彩锚三级**：新增 `assets/story/visual-style.md`（通用基准段 + 画质固定项 + 时代锚 + 场域锚句表 + 条件项表）与 `_shared/visual-style-guide.md`。恒定层七件逐字注入每条提示词，一个同义词都不换——换措辞就扩大采样范围导致漂移；「基准句不召唤物件」：外景条零内景陈设（"The room you describe is the room it builds."）。色彩锚从 V13 的「点名才用 / 不点名即兴」升级为**三级**：① 用户点名导演 → 直接取色卡；② 不点名 → agent 必须先查 `director-index.md`，按题材/平台/受众/对标从 175 位里推 2–3 位候选让用户认领；③ 用户明说「自由创作」→ 才自由，且写入 settings 防反复追问。
8. **文件是记忆，Session 不是 + 新手引导 + 全装/轻装档**：任何跨窗口有价值的结论当轮落盘（判据：这个窗口现在被关掉，这条信息会丢吗？）；新增 `assets/story/decisions.md` 记确认与拍板理由，路由判「确认完成」看这张表；API 中断不是事故，断点按产物文件恢复。新增 `~onboard` 新手引导（放什么 → 我问什么 → 你拿到什么 → 去哪生成 → 翻车怎么办一条龙）+ KAIKAI 开场重写；`.project-config.json.loadout` 全装 / 轻装两档随内容类型拍板。

### ⚖️ BGM 冲突裁决（有官方佐证）

3.0 完整版把 BGM 写进提示词；3.0 **Lite 版**写「BGM 默认后期铺、提示词只写『无背景音乐』」——**与我们 V13 完全一致**。V14 采后者：每条收尾约束固定「无任何背景音乐」+ 列出音效/环境声；音乐只由音乐总监做，后期整条铺。吸收他们的技术理由：**不写 BGM 指令的条，模型会自作主张塞配乐——沉默也要写出来**。例外：`content_type=mv` 画面跟音乐走时允许按 sound-writing 有乐句式写 BGM（禁点歌名艺人）。台词 / 音效 / 环境声三要素句式全盘移植。

### 📁 新增 / 重写 / 修改

- 新增 skill 目录 8 个：`shot-design` `camera` `blocking` `performance` `lighting` `sound-writing` `continuity` `retake`（含 references / templates / examples，≈50 文件，秒数一律改读 `max_seconds`，路径映射零残留）
- 新增：`_shared/visual-style-guide.md`、`assets/story/visual-style.md` 与 `decisions.md` 约定、`assets/continuity-ledger.md` 约定、`outputs/epNN/02-shot-table.md` / `review/` / `control-prompts.md` 约定、`_v14升级工作台/`（3 份：工艺层精读提炼 / 融合决策与用户需求 / 资产与前期层精读提炼——升级过程本身也「文件即记忆」）
- 重写：`CLAUDE.md`（单位定义 / 文件即记忆 / 查病审核 / 全装轻装 / 分镜两步 / `~retake` `~onboard` / 色彩锚三级）、`seedance-storyboard-skill/SKILL.md`（编译站）、`agents/storyboard-artist.md`（两步制 + 9 skills 挂载）、`agents/reviewer.md`（查病制）
- 修改：4 个 review skill + `review-methodology.md` 改查病制；`creative-brief-guide.md` 色彩锚三级；`reference-index.template.md` 加短串 / 声线锁 / -vN 变体；art-design 加纯正向 / 七维 / 声线锁 / 角度覆盖 / 道具分级；director / bianju / art-designer 增量；`user-messages.md` 新增 ★表确认 / `~retake` 收案 / 内容类型档位 / `~help` 与 `~status` 更新；`ARCHITECTURE.md` / `file-index.template.md` / `episode-master.template.md` / `path-b-setup.md` 对齐 v14
- 术语对照：他们的「条」= 我们的 Cut；「场」= P0X；地址 `epNN-P0X-CutM`

### ✅ 保留清单（V13 根治成果一项不丢）

6 agent 分工 + reviewer 独立 / `max_seconds` 模型无关时长 / 175 位导演色卡三文件 / 编剧六子流程 + 0.6 故事优先 + 0.7 下游接口 / 故事板手动模式 / 参考图默认单张禁宫格字样 / 音乐隔离 / 画幅一次声明 / [效率去哪儿] / `~` 指令集、路径 A/B、介入模式、反向反馈协议、迷路救援 / 归档六件事制度。

---

## v13.0 — 2026-09-08 22:46:14 UTC+08:00（顽疾根治 · 色彩锚 · 模型授权 · 时长 config 驱动）

**主题**：不加补丁，从结构层根治反复了 5 个版本的老问题；融合 175 位世界导演色卡库提升电影感；把「文档反复叮嘱」改成「可判定检查」，给强模型松绑。

### 🩺 根治四个顽疾（文字叮嘱 → 结构强制）

1. **一致性漂移**：删掉 v12 只写了一半的 `@char-NNN` 编号体系（生产者被要求写、分镜师从未消费），素材引用**只用文件名**一套；reviewer 检查改为可判定的集合运算——【画面内容】里的具名角色 ⊆ 上传清单、具名场景的场景图 ∈ 上传清单
2. **视频提示词混入音乐**：三块散文正文内不得出现 `M\d\d` / BGM / 配乐 / 音乐字样，音乐只以 Cut 块**之外**的独立注脚行出现；reviewer 按文本匹配判 FAIL。删掉 methodology 里与红线拧巴的「背景音乐 @音频1」官方写法
3. **画幅传染**：消除传染源——画幅只在 `video-prompts.md` 顶部全局声明一次，Cut 内一律不写；三层文档防御整段删除
4. **CLAUDE.md 膨胀**：812 行 → 400 行以内。外置：目录树 → `.claude/ARCHITECTURE.md`；路径 B 五问 → `_shared/path-b-setup.md`；找文件速查表模板 → `.claude/templates/file-index.template.md`；初始化 1.5/1.6 采访话术 → `user-messages.md`；创作基准/节奏三档细节改为指针；版本管理规范 → 本文件顶部；「风格提示词放最前」五处 → 一处

### 🚨 修 3 个 P0 阻断 + P1 口径不一

- **路径 B 死锁**：creative-brief.md 由编剧产出，但路径 B 跳过编剧，服化道/分镜师又硬规定缺失即报错——V12 走路径 B 到阶段三必卡死。修法：路径 B 下由**导演在阶段二**产出 creative-brief.md
- **审核归属只迁移一半**：CLAUDE.md 6 处「导演审核」+ 3 个下游 agent「等待导演意见」全部改 reviewer；director.md 清掉「全程质控者」自我定位与审核输入/输出分支
- **三处悬空引用**：`[分镜输出规范 v10.0]` / `[质量综合报告]` / `[工作流程 - MV模式]`——质量报告格式直接写进 reviewer.md（唯一使用者），另两处改指向真实位置
- **分镜格式三套并存**：storyboard-artist 里的 v7 模板删除；`seedance-prompt-review-skill` 验收清单重写为三块散文 + 五条可判定检查；`seedance-storyboard-skill/SKILL.md` 第 294–397 行 v9 方框格式残留清除
- music-director 剧本读取权限统一为「只读导演讲戏本的音乐方向块」；宫格标准统一由 `image_model_config.grid_mode` 决定（默认 single）

### 🎯 用户补充要求（升级中期追加，均已落地）

- **故事板改手动模式**：默认全部单镜；只有 `~storyboard-mode storyboard` 开启才用故事板。导演不再给「建议形态」（改为「镜头合并建议」），分镜师不再自判；未开启却出故事板 → reviewer FAIL。理由写进 SKILL：带标注/曲线/表格的华丽故事板丢进视频模型会被当画面内容一起渲染，错漏百出
- **定镜原则**：`max_seconds` 是上限不是目标，每镜按剧情实际定长；**能合并就合并**——相邻同空间同时间流有因果的剧情合并为一镜并用好上限，剧情原生在同一段视频里比后期拼碎片质量高
- **不给镜头内动作加时间戳**：`[0-3秒]…[4-8秒]…` 是安慰剂，模型不会真按时间戳分配时长；真正影响节奏的是**镜头数量**，改用 `镜头01` / `镜头02` 序号分段
- **音乐硬红线**：绝不生成任何 BGM，音乐只由音乐总监单独做歌，其他 agent 一概不碰。每镜「声音」行正向声明「本镜无任何背景音乐」+ 列出具体音效，reviewer 两步判定
- **提示词不求长**：参考图已交代的外观不再用文字重复；「一段自己都读不完的提示词，说明对这镜要发生什么并不关心」写进 [锁/变分层法]
- **参考图默认单张**：`grid_mode` 默认 `single`；single 时场景/道具提示词不得出现「宫格 / 九宫格 / 3x3 / 格N」字样（防生图工具默认出九宫格）；art-design 的 SKILL / template / examples / review / failure-fix 全部同步
- **初始化确认视频模型与上限**：采访话术让用户填实际秒数（15 / 30…），不预设

### ✍️ 编剧优化（v13，用户授权自主判断）

- **新增 0.6 故事优先**：整条流水线只有编剧决定「这故事值不值得拍」，下游只能忠实执行——剧本平庸，后面再精致也是精致的平庸。三个不要：不为填满流程而产出 / 不把「符合方法论」当成「好」 / 不跳过一句话钩子的检验。自检问题：这个故事我自己会想看吗？
- **新增 0.7 与下游的接口**：① 一场戏 = 一个连续时空单元（跨时间跨地点必须分场，这决定分镜师能否合并成一镜）；② 声音只写同期声，不写「此处响起悲伤钢琴曲」（音乐归音乐总监）
- **采访四轮改为脚手架**：判据从「问了几轮」改为「够不够动笔」；新增「只问用户才能回答的，属于你专业判断的自己定，别把工作推回用户」；**结束前必做最后一问**——把钩子用一句话讲给用户，他犹豫就回去重想
- **剧本设定 14 项重组为 A/B/C 三组**：A 组故事（含新增的「一句话钩子」，排在梗概之前）/ B 组发行配置（问清即可，不在此耗构思精力，与 `_shared` 重复的长说明改指针）/ C 组收尾。原本平铺的 14 项让「填表」和「构思」权重相同，重组后主战场清晰

### 🧭 新增 CLAUDE.md [效率去哪儿] 章节

把用户的感慨写进配置立场：AI 让执行成本趋近于零，省下的时间应该全部花在构思分镜和故事上。绝大多数提示词技巧终将被模型进步吞噬，故事不会。所以这套配置的规则一直在减不在加——技术边界和可判定检查留下，写法偏好和微观配方全部删掉。每个 agent 的自检最终都指向同一个问题：**这一镜的戏是什么？**

### 🗂️ 归档制度化

本文件顶部新增「每次升级完成前必做的六件事」：changelog 条目 / UPGRADE-LOG / FEATURE-SUMMARY / KAIKAI 开场 / README+USAGE+AGENTS / 一致性自检。理由：v11 发版时忘写 changelog（与 v10 文件 MD5 相同），v12 忘改 CLAUDE.md 版本号——归档不是仪式，是下一次升级的唯一依据。

### 🧠 模型授权原则（新增 CLAUDE.md 章节）

- 给标准和判据，不给分步剧本。保留**硬约束**（技术边界如参考图 ≤9、合规红线、可判定自检），删除**软约束**（字数配额「单镜 50–70 词」、写法偏好「宁短勿长」、分秒配方「0–3 秒拍什么」）
- **时长彻底 config 驱动**：全项目清除写死的 15s / 1.2s，一律读 `video_model_config.max_seconds`；`~video-model` 采访话术不再预设任何数字（支持 30s 的模型填 30 即可）
- `_shared/pacing-methodology.md` 三档改为相对描述，逐拍骨架不标秒数；`ai-generation-constraints.md` 再清理一轮过时约束

### 🎨 色彩锚（175 位世界导演色卡融合）

- 新增 `art-design-skill/references/director-color-cards.md`（175 位导演六色 HEX+占比 / 光线 / 摄影 / 调色，约 78KB）、`director-index.md`（按 10 大风格分类的浏览索引，约 26KB）、`director-camera-language.md`（88 位导演运镜语言，约 44KB，**参考不是约束**）
- 只接文本、不接一张图（源库 6.3G 里 8322 张 jpg 全部不接）；按需加载——用户指定导演后只读对应那一段
- 接入点为**可选锚点**：用户说「要芬奇的调子」→ 取 D082 六色进 creative-brief 基准段的「调色板」「光逻辑」；不指定 → 完全不加载，照 V12 自由创作
- 新增指令 `~color <导演名或D0NN>`；`~settings` 增加「色彩锚」项；`creative-brief-guide.md` 新增「色彩锚（可选）」小节与嵌入示例

### 🔧 三个小点

- KAIKAI ASCII 改用标准 block 字符，删掉「如果显示乱码请纠正」的遮羞注释
- 单镜时长上限放开：只由 `~video-model` 填的数字决定
- 取消分秒级内容配方

### ⏱️ 时长预算意识（用户二次澄清后重做，本版最核心设计）

用户第一次说「能合并就合并」，我实现为分镜阶段的一条合并规则。二次澄清后才明白**底层要求是预算意识**：模型单镜上限应当是**从导演拆剧情点就开始参与的核心设计参数**，不是分镜末尾的一条检查。于是重做为四层贯通：

- **原 `[定镜原则]` 扩写为 `[时长预算与定镜]`** 五节：① 先算预算（总时长 ÷ 上限 = 镜头数量级）② 上限决定「一件事用几个镜头讲」③ 在剧情允许时榨干上限 ④ 镜头内用序号分段不用时间戳 ⑤ 交付的是乐高 + 说明书
- **核心洞察写进方法论**：上限 15s 时一个完整戏剧动作常装不进一镜、被迫拆开（每个接缝都要后期对齐）；上限 30s 时一镜到底、没有接缝就没有对齐问题。**同一个剧本在不同上限下分镜方案根本不是一回事**；上限越宽越应主动把戏做长做连续，而非习惯性切碎。未来上限极宽时，分镜概念本身会松动，工作重心从「怎么切」转向「怎么讲」
- **导演侧前移**：`director-skill` 第二步新增「开工前先读两个数字」（上限 + 目标总时长）与「量级自检」（剧情点数远超 总时长÷上限 → 拆太碎，回去合）；第三步改为「时长跟内容走，但在剧情允许时主动往上限靠」并给出 8s+15s=23s≤30s 的具体判例
- **字段更名**：「镜头合并建议」→ **「镜头承载规划」**（可一镜到底（约 Ns）/ 需 N 镜（附原因）/ 可与 P0X 并入一镜），因为要表达的是「这段戏需要多少承载量」而不是「合不合并」。全项目 8 个文件同步
- **时间戳的准确理由**：不只是「让提示词变长」，而是**模型不会真按时间戳分配时长，那是安慰剂；真正影响节奏的是镜头内切了几次**。所以 `镜头01`/`镜头02` 序号分段是替代方案而非妥协——既表达了节奏，又不给模型无效的秒数约束
- **编剧侧补充**：`0.7` 增加反向约束——同一空间、时间连续、动作有因果的戏别硬拆成三场，拆得越碎下游片段越多、接缝越多、质量越低
- **交付心智**：从「一堆镜头 + 提示词」改为「边缘规整的乐高 + 说明书」，检验标准是「用户不做二次创作能否拼出成片」

### 🐛 二轮红队审查发现并修复（投产前最后一轮）

第二轮独立审查（空白上下文、74 文件全量交叉验证）发现 4 条 P0 + 4 条 P1，全部修复。**三条 P0 集中在 `episode-master.template.md`——它是本轮唯一没被 V13 改造彻底的文件**（v7.0.1/v7.0.2 标记、15 秒公式、mixed 模式、画幅构图段原样留存）：

- 🔴 **模板把总时长写死成 15 的倍数**（`约 <N × 15>s`），与同文件另一处「各 Cut 时长之和」自相矛盾；模板正文是分镜师逐字照抄的，用户拿到的说明书数字会是错的 → 改为「各 Cut 时长之和」，并新增「视频模型 / 单镜上限」字段
- 🔴 **模板 4 处保留「混合模式 / mixed」**，与 SKILL 的「判定只有两级」+ 禁忌规则「不在一个剧情点内混用」冲突；分镜师照模板产出 mixed，reviewer 无判据只能 FAIL → **无法收敛的 FAIL 循环** → 删净，模式取值只留 storyboard / single-shot
- 🔴 **模板 2 处要求用户复制「开头的 `[<画幅>构图]`」**，但 V13 已规定 Cut 内不写画幅，且 reviewer 检查④ 会因 Cut 内出现画幅而一票否决 → 操作步骤整体重写为「去 video-prompts.md 复制三块 + 在工具里手动选顶部声明的画幅」
- 🔴 **reviewer 两条一票否决要求 PNG「真实存在」**，但 PNG 由用户拿提示词自己生成，分镜阶段通常还没出图 → **每集分镜必 FAIL 且分镜师无法修复**（他不能凭空造图）→ 改为「校验文件名与 `reference-index.md` 一致」，并顺带补上全项目此前**从未定义**的 PNG/MP4 存放位置（ARCHITECTURE.md 新增「关于 PNG / MP4」小节：参考图 → `assets/visual/images/`、故事板 → `outputs/<集>/storyboards/`、成片片段 → `outputs/<集>/cuts/`）
- 🟡 sed 更名后 `director.md` [输出规范] 的选项文字仍是旧值（「可合并/独立成镜/内部拆为N镜」），与同文件及另三处的新枚举冲突 → 统一
- 🟡 `mv-visual-timeline.md` 无归属：CLAUDE.md 要求音乐总监产出它，但 music-director.md 输出位置、music-design-skill、ARCHITECTURE 目录树三处均无记载 → 补进 agent 输出位置与目录树
- 🟡 「承接」字段契约断链：reviewer 查它、禁忌规则要求它，但三个 Cut 模板都没有这一行（V12 靠表格列承载，改三块散文后落点丢了）→ I2V/V2V/T2V 三模板各补 `⛓️ 承接` 行
- 🟡 两处按序号引用剧本设定项（`第 10-11 项`、`路径 A 第 12 问`），编剧 A/B/C 重排后指向错位，reviewer 会取错评分依据 → 改为按字段名引用（序号会变，字段名不会）

### 📄 文档同步

- CLAUDE.md 头部版本号 v11.0 → v13.0（V12 忘改）
- 本文件：补 v11.0 条目（V11 发版时未写，从 UPGRADE-LOG 反推）；为 v8.0 / v6.0 两段孤儿正文补回标题
- README.md 重写（原自称 v6.1）；USAGE.md / AGENTS.md 更新到 v13（6 个 agent、五问、reviewer）
- **KAIKAI 开场重写**：6 个 agent + 四类交付物 + 本版五个亮点 + 故事优先的收尾话；顶部加「每次升级都要回来更新这段」维护约定
- `.cursor/rules/main.mdc` / `.windsurf/rules/main.md`：5 个 agent → 6 个；补一句「审核阶段切 reviewer 时刻意抛开创作上下文」
- 新增 `UPGRADE-LOG.md`（V12→V13）、`V13-FEATURE-SUMMARY.md`、`故事板/README.md`

### 🐛 收口审查发现并修复

- **`content_type` 从不询问**：V12 的 schema 里有 `narrative | mv | vj` 三条路径，但初始化流程从头到尾没有询问这个字段，导致想做 MV 或纯视觉的用户也会被默认按叙事类走五阶段（编剧阶段完全用不上）。修法：初始化新增第 1.5 步 + `user-messages > 内容类型询问` 话术
- **`storyboard-style-decision-tree.md` 与手动模式潜在冲突**：文件名和 description 里的「AI 决策树」容易被误读为「由 AI 决定用不用故事板」。修法：顶部加前置条件——本文件只在故事板模式下加载，用不用故事板由用户 `~storyboard-mode` 决定
- **`min_seconds` 可能大于 `max_seconds`（会导致所有镜头必然 FAIL）**：`min_seconds` 硬编码默认 4，而 `max_seconds` 由用户填。若某工具上限 < 4 秒，时长检查 `min ≤ t ≤ max` 永远不成立，分镜进入改不出来的 FAIL 死循环。修法：CLAUDE.md 介入模式段 + 采访话术规定「max < 4 时把 min 一并下调为同值」，reviewer 检查③ 增加「min > max 时以 max 为准、不判 FAIL 并提示校正」
- 上一轮红队审查的 4 条 P0 已全修（详见本条目上方各段）；175 条色卡程序化校验通过（六色齐全、占比合计 95–105%、无空字段；D101–D150 源数据本身只有 HEX 无色名，已在文件顶部注明）
- 二轮机械化自检通过：同文件内无重复章节标题、9 个文件的 frontmatter 完整未被插入内容破坏、v13 须知无重复插入、旧名（`[定镜原则]`/`镜头合并建议`/`严禁视频音乐红线`/`@char-`/`导演审核`/`全程质控`）全部零残留、跨文件章节引用与 CLAUDE.md 章节引用全部命中、6 个 agent 的 skills 路径 9/9 可达

### 🗑️ 删除

- `.claude/skills/_backup-pre-storyboard-v5/`（自身 README 授权删除，约 90KB 重复文件）
- `.reference/v5.0/`（v6–v11 均无对应快照，归档纪律未贯彻）
- `assets/reference-index.template.md` 里的 @编号体系
- `V12-FEATURE-SUMMARY.md`（由 V13 版取代）

---

## v12.0 — 2026-07-07 UTC+08:00

**主题**：架构智慧升级——移植 Seedance 2.0 参考文档6个核心设计点，创作与审核分离，提示词组织标准化。

### ✨ 新增能力

1. **锁/变分层心智模型**：恒定层（角色/场景/风格）用@图片引用，可变层（动作/运镜/情绪）写文字——减少冗余，防漂移
2. **reference-index @编号体系**：统一四段格式（char-NNN/scene-NNN/prop-NNN/audio-NNN），服化道维护，分镜师引用
3. **独立 reviewer agent**：审核职责从 director 完全独立，每次空白上下文开始，防自审盲点
4. **3份 failure-fix-table**：分镜师/导演/服化道各一份「失败现象→根因→最小修复」对照表
5. **锚定资产纪律**：场景提示词禁止重新描述已有角色/道具外观（三种合规处理：留空槽/方向描述/场景即资产）
6. **~feedback --learn 机制**：反馈同时固化到对应 skill 末尾「项目特定规则」段，知识跨会话积累

### 🔒 保留 V11 全部已修复 bug

- video_model_config（4个能力标志）+ image_model_config（宫格模式）
- 心智透明原则（场景参考图连续性，每Cut必须带场景@引用）
- 画幅锁定防传染机制（v7.0.2）
- 场景独立@编号规则（九宫格每格独立，不能整张引用）
- 视频提示词严禁音乐描述（严禁BGM/配乐写进正文）

### 📁 文件改动（归档于 UPGRADE-LOG.md）

- 新增：`reviewer.md`、`reference-index.template.md`、3份 failure-fix-table、`UPGRADE-LOG.md`、`V12-FEATURE-SUMMARY.md`
- 修改：`director.md`（移除审核）、`CLAUDE.md`（审核流程+~feedback --learn）、`seedance-storyboard-skill/SKILL.md`、`seedance-prompt-methodology.md`、`art-design-skill/SKILL.md`、`storyboard-artist.md`、`art-designer.md`

---

## v11.0 — 2026-07-06（bug 修复与功能补全；本条目于 v13 补记）

> V11 发版时未写 changelog（V11 与 V10 的 CHANGELOG 文件完全相同）。以下从 `UPGRADE-LOG.md` 的「不动的内容」清单与全项目 `v11.0` 标记反推，未做的不写。

### ✨ 新增

- **image_model_config**：生图工具 + 宫格布局全局配置（single / 2x3 / 2x4 / 3x3 / 自定义），仿 video_model_config 模式；初始化第 1.6 步询问，`~image-model` 更新
- **📋找文件速查表.md**：初始化自动生成的中文导航文件，一眼找到所有产出
- **心智透明原则**：每个 Cut 是独立生成任务，只要发生在具名场景里，场景参考图必须出现在上传清单——无论上一 Cut 是否已引用
- **T2V 判定红线**：画面中有具名角色（无论叠加多少特效/UI）都必须 I2V 传参考图；只有纯环境/纯 UI 全屏才允许 T2V（来自真实崩坏案例）
- **UI 文字生成警告**：世界观专属视觉（系统 UI / 金手指 / 魔法阵）当独立资产设计；画面内文字按装饰性 / 关键信息 / 标签分级，关键信息后期合成
- 内容型道具（关系网 / 信件 / 屏幕）转译为生图可执行的视觉文字
- 歌词事实准确性自检（「苟字非 3 画」案例）；Suno Style 三版变体

### 🔧 修复

- 编剧子流程写文件指令补全（剧本设定 / 大纲 / 角色 / 剧本四个子流程均补内联写入步骤）
- `~角色` 等波浪号指令加「不可用 Skill() 调用」警告，防误调
- storyboard-artist 补读 creative-brief.md 与 image_model_config

---

## v10.0 — 2026-07-05 06:00:00 UTC+08:00（里程碑版本 · 导演视野 · 视觉基准段 · 三块散文 · 疏中紧节奏）

**主题**：融合 V9 的易用性设计 与「Seedance 分镜师2.0」的影像语言深度，打造面向豆瓣9.0+标准的里程碑版本。核心升级：给所有 agent 配备专业电影人的思维工具，同时保持对小白友好。

### 🎬 创作基准（情感蓝图 + 导演视野 + 视觉基准段 三合一）

- V9「情感蓝图」升级为「创作基准」（`assets/story/creative-brief.md`），三个层面：
  - ① 情感蓝图（观众视角：核心感受 + 情感节拍 + 视觉隐喻）
  - ② 导演视野（作者视角：作者风格 + 可挂导演署名锚，如「Fincher式冷峻精密」）
  - ③ 全片视觉风格基准段（技术基准：画风/调色板/质感/光逻辑，可直接嵌入提示词的那段文字）
- **全片视觉风格基准段**是跨资产一致性的根本解决方案：服化道每张提示词开头 + 分镜师每条【氛围与画质】，都逐字嵌入这同一段文字，跨资产风格漂移从源头解决
- 新增 `_shared/creative-brief-guide.md`：方法论文件，含好坏示例

### 🎵 节奏系统升级（疏/中/紧三档 + 气口）

- V9「节奏蓝图」升级为精确三档：
  - 紧档：动作/打斗，3–3.5s/镜，默认4–5镜
  - 中档：常规叙事，3–4s/镜
  - 疏档：文戏/情绪，4–6s/镜，气口单独预算
- **气口**概念引入：反应停顿/留白/沉淀是戏，要单独算进时长，不是填完内容剩下的
- **逐拍骨架**：高密度动作戏（武打/追逐）必须在讲戏后追加逐拍清单，消弭导演叙述与分镜师执行之间的密度鸿沟
- 新增 `_shared/pacing-methodology.md`：完整三档方法论，含自检清单

### 📋 分镜提示词三块散文格式

- 单镜模式提示词升级为【参考设定】【氛围与画质】【画面内容】三块结构：
  - 【参考设定】：每个素材先一句话说明用途，再标文件名（角色外观交给设定图，不重复描述）
  - 【氛围与画质】：嵌入全片视觉风格基准段，跨所有 Cut 复用（不用每条重写）
  - 【画面内容】：只写"动"——具体物理动作 + 运镜，不重描静态信息
- **可跟随性原则（followability > completeness）**：模型跟不住的细节宁可删，单镜50-70词宁短勿塞
- 保留 V9 的小白友好上传清单（写清文件名和槽位）
- 新增后期铺乐注脚格式：【🎵 后期铺乐：M01主题曲，铺在Cut3-8，不进Seedance】

### 🔊 声音三分类明确化

| 类型 | 处理方式 |
|---|---|
| 原生音效/环境音 | 写进提示词【画面内容】，Seedance跟着出 |
| 台词/配音 | 单独生成，作为@audio上传（每镜≤3） |
| 音乐（BGM/主题曲） | **不进提示词**，写在Cut下方的后期铺乐注脚 |

### 📁 统一素材索引

- 新增 `assets/reference-index.md`：所有角色/场景/道具/音频素材的统一清单，含全片视觉风格基准段副本

### 🎨 服化道升级

- art-designer.md：必须先读 `creative-brief.md` 的视觉风格基准段，每张提示词开头嵌入

---

## v9.0 — 2026-07-05 04:00:00 UTC+08:00（创作DNA · 内容类型分支 · 小白友好UX · 适度约束充分授权）

**主题**：以「豆瓣9.0+质量」为核心目标的系统性升级。设计哲学转变：从「规定每一步怎么做」到「给清晰目标和边界，让强大的模型自主发挥」。

### 🎨 情感蓝图（全片创作DNA）

- bianju 阶段第一个产出，在选题研读和创意采访之后、剧本设定之前完成
- 内容：核心情感一句话 + 3-5个情感节拍 + 核心视觉隐喻 + 音乐情绪基调
- 存入 `assets/story/emotion-blueprint.md`，**5个agent全程以此为北极星**
- 不是规则约束，是创作方向的指引

### 🎵 节奏蓝图（导演分析新产物）

- director-skill 第八步，所有剧情点拆解完成后输出
- 简单时间轴表：每个P0X标注情绪等级（⬛低/🟨中/🟥高/🔴峰值）和建议Cut密度
- 存入 `01-director-analysis.md` 末尾，供分镜师参考（不是强制规则，是创作信息）

### 🎬 内容类型分支（三条工作流程路径）

- 新增 `.project-config.json.content_type` 字段（narrative / mv / vj）
- **叙事类（narrative）**：短片/微电影/电影/叙事MV → 现有五阶段流程 + 情感蓝图
- **MV音乐驱动（mv）**：音乐先行，支持**Gemini音频分析现有歌曲**（Claude本身不处理音频）
  - 新增 `.claude/skills/_shared/gemini-audio-analysis-guide.md`：完整引导文档（含Gemini提示词模板）
  - 已有歌曲 → Gemini分析 → 音乐结构文档 → 音乐总监做视觉编排 → 导演/服化道/分镜
- **纯视觉（vj）**：演出视觉/装置/循环视觉，跳过编剧，导演直接做视觉语言Brief

### 👁️ 分镜UX重构（最重要的易用性改进）

废弃「素材对应表 @图片N」方案，改为**每个Cut独立上传清单**格式：
- 每个Cut包含：生成模式标注 + 上传清单（写明文件名和槽位）+ 可直接复制的提示词文本
- 不再需要用户记忆「@图片1是谁，@图片5是哪个场景」
- 新增 **V2V生成模式**（视频续接）标注：标有V2V的Cut告诉用户上传上一段视频实现帧级连续
- 三种生成模式：T2V（纯文本）/ I2V（图像参考首帧锁定）/ V2V（视频续接无缝衔接）

### 🎭 故事板模式彻底变可选

- 删除四级优先判定hierarchy，分镜师完全自主判断用不用故事板
- 提供直观的"什么时候故事板更好"参考，不是规则
- 同一集混合使用（复杂场景用故事板，简单镜头用单镜）完全没问题

### 🧠 设计哲学升级

- **适度约束**：只对真正需要硬约束的事设规则（时长/格式/合规）
- **充分授权**：创意决策完全交给模型（Claude Opus 4.8/Fable 5级别的模型有足够的判断力）
- 目标：让AI agent像一个有创作能力的专业团队，而不是一个执行清单的机器

---

## v8.0 — 2026-07-05 02:00:00 UTC+08:00（视频时长硬约束 · 补全 v7 遗留文件；本标题于 v13 补回）

**主题**：修复长期存在的「分镜提示词单 Cut 时长超出视频模型生成上限」问题，同时补全 v7.0 系列遗留的缺失文件，以「4 -V7（新增故事板功能）」为基础构建 V8。

### 🚨 核心 Bug 修复：视频时长硬约束（你报告的主要问题）

- **漏洞 · Cut 时长超限**：
  - **现象**：分镜师在写视频提示词时，单个 Cut 的标注时长可达几十秒，而 Seedance 2.0 最多支持 15 秒，导致用户去生成工具操作时直接失败，提示词全部作废
  - **根因**：方法论里的时长上限（15s）只是文字描述，没有被设计为「必须从项目配置读取」的硬约束；AI 在生成时会无视这条说明
  - **修复方案 — 三层联动**：
    1. **项目配置层**（`.project-config.json`）：新增 `video_model_config` 字段（`primary_model` / `max_seconds` / `min_seconds`），成为全局单一真相源
    2. **采访机制层**（`CLAUDE.md` [初始化] 步骤 1.5）：项目启动时若 `video_model_config` 不存在，立即采访用户「用哪个模型 + 最长几秒」，写入配置后才继续；随时可用 `~video-model` 更新
    3. **执行层**（`seedance-storyboard-skill/SKILL.md` 步骤一 + 视频提示词表生成逻辑）：故事板模式 + 单镜模式都从配置文件读 `max_seconds`，每 Cut 标注时长不得超过该值，写完自检
    4. **审核层**（`seedance-prompt-review-skill/SKILL.md`）：时长约束审核改为「先读 max_seconds → 逐条检查 → 超限一票否决 FAIL」
    5. **方法论层**（`seedance-prompt-methodology.md`）：输出参数说明改为动态（从配置读取），不再硬写 4-15s
  - **向后兼容**：配置缺失时默认 max_seconds=15s（Seedance 2.0 当前上限），不破坏已有项目
  - **与时俱进**：以后 Seedance 升级支持 30s / 60s，只需 `~video-model` 告知一次，所有提示词时长约束自动适配

### 📁 文件补全（v7.0 遗留缺失）

- 本版本基于「4 -V7（新增故事板功能）」，该目录已包含 v7.0 完整文件集（相比工作目录「4 -V7」补全了 20+ 关键文件）：
  - `director.md` / `storyboard-artist.md`（原先只存在于 v5.0 归档）
  - `bianju-skill/SKILL.md` / `director-skill/SKILL.md`（原先只有 references/，无主 SKILL.md）
  - `seedance-storyboard-skill/SKILL.md`（v7.0 双轨完整版）
  - `seedance-prompt-review-skill/SKILL.md`（原先只存在于 v5.0 归档）
  - `_shared/user-messages.md`（大量引用但文件缺失）
  - `USAGE.md`、`CHANGELOG.md`、视觉风格画幅字段等

### 🔧 新增指令

- `~video-model`：随时查看或更新视频模型配置（模型名 + max_seconds）；模型升级后的标准操作

---

## v7.0.3 — 2026-05-24 03:43:00 UTC+08:00（画幅传染防御 · 关键漏洞修复 · 固化版本）

**主题**：用户追问「故事板 16:9 OK，但不能传染最终视频」时做红队审查，发现一个**关键漏洞**——视频提示词从未显式声明画幅，会被 16:9 横版的 P0X-storyboard.png 参考图直接传染。漏修后所有非 16:9 项目（9:16 抖音 / 1:1 朋友圈 / 21:9 院线等）都会废。

### 🚨 关键漏洞修复

- **漏洞 · 画幅传染**：
  - **现象**：项目 settings.aspect_ratio = 9:16，但 video-prompts.md 表头无画幅列；每条 Cut 描述只写动作不写画幅；Seedance 看到 16:9 横版的 P0X-storyboard.png 参考图 → 倾向输出 16:9 视频 → 与 9:16 项目错位 → 视频废
  - **影响**：v7.0.2 之前所有非 16:9 项目（抖音 / 小红书 / 视频号 / TikTok / 朋友圈 / 院线 / 21:9 等）都受影响。**这是直接让产品不能用的 P0 级 bug**
  - **三层防御** 全部修复：
    1. **方法论层**（`seedance-prompt-methodology.md` [第一性原则]）新增「🔴 画幅锁定铁律」段：每条 Seedance 视频提示词必须开头显式声明画幅（即使有参考图）
    2. **执行层**（`seedance-storyboard-skill/SKILL.md` 视频提示词写作规则 5+154）：故事板模式 + 单镜模式都必须在 video-prompts.md 上方加全局声明 + 每条 Cut「描述」列开头写 `[<画幅>构图]` 指令
    3. **审核层**（`seedance-prompt-review-skill/SKILL.md`）新增[画幅锁定合规性] 一票否决项：审核必查「全局声明 / 每条 Cut 画幅指令 / 用户操作清单提工具选画幅」3 项
    4. **模板层**（`episode-master.template.md` §四视频提示词表）：表上方加「画幅锁定声明」框 + 表内示例 Cut 描述列加 `[9:16 竖版构图]` 占位 + 5 种画幅替换指南
    5. **用户操作层**（episode-master.template.md §7.1+§7.2 + USAGE.md）：每个生视频步骤加「🔴 画幅锁定关键步骤」明确「在 Seedance 工具里手动选 settings.aspect_ratio，不要用默认」
    6. **故事板层**（`universal-storyboard-methodology.md` M4 模块）新增「🔴 Cut 缩略图镜头框按 settings.aspect_ratio 画」约束（项目 9:16 时缩略图是竖矩形）
- **故障排除补 2 条 v7.0.2 防传染条目**：「项目非 16:9 但 Seedance 输出 16:9」+「视频提示词复粘到 Seedance 不知道选什么画幅」

### 🎯 设计原则强化

- **三层防御 = 文档声明 + 提示词写法 + 用户手动操作**：单层防御不够（用户可能漏看声明 / 复粘时漏 `[<画幅>构图]` / 在 Seedance 用默认画幅），三层都到位才能防住
- **漏洞发现教训**：用户追问「画幅不能传染」时，单纯改文档"措辞"是不够的——必须查实际写作流程是否真的把 aspect_ratio 写进了视频提示词。我之前 v7.0.2 只改了「故事板大图措辞」+ 「episode-master 字段」，没下到提示词正文层 → 留下了 P0 漏洞

### 🔁 关于「现在真的好用 / 易用 / 能用 / 无 bug 了吗」

**这次审查发现的漏洞证明**：每次说"无 bug"都只对那时已知的范围而言。但目前已发现的所有问题（v7.0.1 的 14 个 + v7.0.1 修复回归的 6 个 + v7.0.2 的 4 项需求 + v7.0.3 的 1 个关键漏洞）都已修复。

| 维度 | 现状 | 评估 |
|---|---|---|
| **能用** | 26 + 1 = 27 个问题修完；3 路径闭环；交付物可直接用 | ✅ 能用 |
| **易用** | 五问采访 + 智能推荐 + 13 条故障排除 + 工具选择说明 | ✅ 易用 |
| **好用** | 双轨模式 + 5 候选风格 + 跨集自动沿用 + Partial regen + 反向反馈 + 全套指令 | ✅ 好用 |
| **无 bug** | 已发现的全部修复；剩余风险只能运行时观察发现 | ⚠️ **目前已知无 bug；不保证零未知 bug** |

**底线诚实陈述**：这次又发现一个 P0 级漏洞证明——再做几轮审查，可能还能发现一些。但每发现一个都能在小时级修完。**现在的状态可以放心固化使用**——任何运行中发现的问题用 ~feedback 反馈，下个版本继续迭代。

---

## v7.0.2 — 2026-05-24（用户驱动的体验加强 · 画幅 / 跨集 / 工具）

**主题**：用户在三轮审查后追加 4 项需求 — 画幅不应固定（10 候选）、跨集累积风险防御、新增 Image2 生图工具、再次确认"好用易用能用能产出高质量提示词"。逐项落地。

### 🎯 新增能力

- **视觉画幅成为一等公民**：`settings.aspect_ratio` 字段从隐式存在升级为路径 B 启动**第 5 问**必问 + 路径 A 编剧 SKILL.md 第 10 项必填子字段
  - 10 候选：1:1 / 2:3 / 3:2 / 3:4 / 4:3 / 9:16 / 16:9 / 9:21 / 21:9 / Auto（用户附图全集）
  - **平台智能推荐**：抖音/快手/小红书/视频号/TikTok → 9:16；B站/YouTube TV/院线 → 16:9；朋友圈/Instagram → 1:1；电影院线 → 21:9
  - **故事板大图与最终视频画幅解耦**：故事板复合图本身保留 16:9 横版（信息密度最大化是 11 案例硬规律），但**最终视频按 settings.aspect_ratio**，故事板里每个 Cut 缩略图的镜头框也按 aspect_ratio 画
- **跨集累积风险防御**：episode-master.md `§9.3 给下一集的核心交接` 强化为**恒定 8 字段** `to_next_episode` 段（YAML 块）
  - 8 字段：`storyboard_style / visual_style_keywords / aspect_ratio / last_shot_summary / last_emotion / last_time_space / assets_to_reuse / music_leitmotif / unresolved_threads`
  - 续集分镜师**只读这一段**而非全文，做到 50 集也不累积——传递的不是历史，是核心交接信号
- **新增 Image2 作为推荐生图工具**：在用户面对的所有工具列表（USAGE.md 顶部声明 / 工作流 / 故障排除 + episode-master.template.md §三 + §7.1）加入
  - 三工具定位：**Image2** 文字+画面细节控制更精确（首选）/ **Nano Banana Pro** 多图参考+人物一致性优异 / **即梦** 中文语义好
  - **提示词通用**：三个工具复粘同一份提示词即可（不需要改提示词内容）

### 🔧 联动修改

- `CLAUDE.md` 路径 B 从「四问」升级为「五问」（加画幅）+ 改 schema 骨架；路径 A 提示也改为「五项」；解释「为什么必须有视觉风格 + 画幅」
- `_shared/user-messages.md` 新增第 5 问视觉画幅完整话术（A/B/C 三选一 + 平台推荐表 + 兜底默认 9:16 竖版）
- `bianju-skill/SKILL.md` 第 10 项加 `aspect_ratio` 子字段定义（路径 A 编剧采访同步问到画幅）
- `seedance-storyboard-skill/SKILL.md` 第 107 行画幅措辞从「永远 16:9 横版」改为「故事板大图（复合图）默认 16:9 横版（为信息密度），最终视频按 settings.aspect_ratio」
- `references/universal-storyboard-methodology.md` §5.6 标题从「永远 16:9」改为「默认 16:9（与最终视频画幅解耦）」+ 更新具体描述为 10 候选；§8.3 返工指标语义澄清
- `seedance-prompt-review-skill/SKILL.md` 审核条「画幅强调」从单值检查改为「16:9 + aspect_ratio」双值检查
- `references/storyboard-style-decision-tree.md` 维度 1.5 优化为「只读 §9.3 to_next_episode.storyboard_style」（不读全文）
- `agents/storyboard-artist.md` 协作模式加注「续集只读 §9.3 to_next_episode 段」
- `templates/episode-master.template.md` 「视觉画幅」字段从 3 个候选扩展为 10 个候选 + 加「故事板大图画幅」字段说明解耦关系；§9.3 强化为 8 字段 YAML；§三 + §7.1 工具列表加 Image2
- `USAGE.md` 顶部声明 + 工作流第 1/1.5 步 + 故障排除全部加 Image2

### 🎯 设计原则沉淀

- **解耦原则**：故事板大图画幅（信息密度服务）与最终视频画幅（用户平台服务）是两件事，不应捆绑
- **常量原则**：跨集传递信号必须是恒定字段集（不论 N 多大都是 8 字段），避免累积导致信息过载
- **通用提示词原则**：底层提示词应在多个工具间通用，工具差异通过 README 说明而非分叉提示词

### 🔁 关于"是否做到好用 / 易用 / 能用 / 能产出高质量提示词"

逐项确认（基于 v7.0.2 后的状态）：

| 维度 | 现状 | 评估 |
|---|---|---|
| **能用** | 14 + 6 + 6 = 26 个 bug 修完；3 路径（编剧/服化道/分镜师）闭环；交付物完整可复制粘贴到 Image2 / Suno / Seedance | ✅ 能用 |
| **易用** | 路径 A 自然采访 / 路径 B 五问 + 智能推荐（用户回车默认即可） / 工具选择有说明 / 故障排除表 13 条覆盖典型问题 | ✅ 易用 |
| **好用** | 双轨模式（故事板 / 单镜 / 混合）+ 5 候选风格 + 跨集自动沿用 + Partial regen + 反向反馈 + ~feedback / ~settings / ~mode 全套指令 | ✅ 好用 |
| **产出高质量提示词** | 11 案例工业级提示词作为基准（每个案例 800-1500 字 + 5 候选风格 + 6 必备 4 可选模块 + M6 衔接 + 反向校验）+ 审核 skill 评分 1-10 强制把关 | ✅ 高质量 |

**剩余风险**：LLM 解释边缘案例的差异 / 平台行为变化 / 真实跑流程发现的人因问题——这些只能通过运行观察 + 迭代修复，不属于"现在能不能用"。

---

## v7.0.1 — 2026-05-24（万能故事板升级 · 架构审查 bug 修复）

**主题**：在 v7.0 升级合并后立即启动专业架构师视角的正式 bug 审查，10 维度（文件完整性 / 流程闭环 / 上下游接口 / 用户体验 / 产物质量 / 边界场景 / 跨集复用 / 项目设置缺失 / 文档质量 / 死代码）发现 14 个 bug 并全数修复。

### 🐛 高优先级修复（影响"能用 + 好用"）

- **Bug 1 · 剪辑步骤路径错**：`USAGE.md` 第 4 步剪辑指引仍指向旧路径 `02-seedance-prompts.md`，新项目用户找不到镜头时长建议
  - 修复：改为 `video-prompts.md`（v7.0+）+ 加 `episode-master.md` §六衔接表 检查跨段过渡
- **Bug 4 · 故事板产物文件命名矛盾（最严重）**：`seedance-storyboard-skill/SKILL.md` 第 94+112 行说写单文件聚合 `storyboard-prompts.md`，与其他所有文档使用的按 P0X 分散 `storyboards/P0X-storyboard-prompt.md` 矛盾——分镜师不知道实际产出哪个
  - 修复：SKILL.md 统一改为分散式 `storyboards/P0X-storyboard-prompt.md`（每个 P0X 一份独立 .md，便于逐个迭代 + 用户单文件复制操作）；用户操作清单改为写入 `episode-master.md`
- **Bug 9/10/11/12 · 双轨指令缺持久化**：`~storyboard-mode` 和 `~storyboard-style` 在 CLAUDE.md 只定义了「指令格式」，没说写到哪里、分镜师怎么读到——用户操作完全失效
  - 修复：扩展 `.project-config.json` schema 加 `storyboard_overrides`（含 global / 单集双层）+ `storyboard_style` 字段；CLAUDE.md 定义指令完整执行流程（参数解析 → 写入配置 → 回复用户）；分镜师 SKILL.md [双轨模式判定] 改为 4 级优先级（单集锁定 > 全局锁定 > 导演建议 > AI 决策树自决）
- **Bug 19 · 风格决策树 fallback 与审核硬约束冲突**：决策树第 4 维度返回 `adopt_project_style:{visual_style}` 非标值，但审核 skill 要求「5 候选之一」→ 项目 visual_style = "水墨风" 时直接 FAIL
  - 修复：决策树维度 4 改为「映射到最近 5 候选 + 提示词描述层叠加 visual_style 特征关键词」；伪代码补全映射表（水墨→epic_realism / 赛博朋克→cinematic_realism 等）；自检 checklist 加「主风格名严格在 5 候选之内」
- **Bug 23 · 路径 B 启动缺 visual_style 字段**：路径 B 三问骨架完全没问视觉风格，但下游服化道 / 分镜师 / 故事板决策树第 4 维度都依赖
  - 修复：路径 B 增加第 4 问视觉风格（含 A 直接录入 / B 推荐 3 候选 / C 待服化道补 三选一）；`_shared/user-messages.md` 补完整话术；CLAUDE.md 改「三问」为「四问」+ 解释「为什么必须有视觉风格」

### 🐛 中优先级修复（影响"易用 + 维护性"）

- **Bug 3/15 · USAGE.md 承诺无法实现**：第 290 行写"删除单个 P0X-storyboard-prompt.md → ~prompt 后告诉 KAIKAI 仅重生 P0X"但 `~prompt` 没定义此能力
  - 修复：改写为「删除单文件 → 用 `~feedback <集数> 仅重生 P0X` 走反向反馈机制」（复用既有 v6 能力）
- **Bug 5/8 · 孤儿模板文件**：`templates/seedance-prompts-template.md` 是 v6.1 格式（output 指向 02-seedance-prompts.md），v7.0 SKILL.md 文件结构图已不列它
  - 修复：删除孤儿模板（备份在 `_backup-pre-storyboard-v5/` 中保留）
- **Bug 13 · storyboard-artist 历史兼容措辞歧义**：第 87 行「v6.1 项目的 02-seedance-prompts.md 仍可读取」可能让分镜师误以为可选择性输出旧名
  - 修复：明确「v7.0+ 分镜师**只产出**新命名；审核 skill 兼容读旧名仅针对存量项目」
- **Bug 14 · 故障排除表完全没覆盖 v7.0 场景**
  - 修复：USAGE.md 故障排除表加 5 条 v7.0 条目（故事板大图模糊 / 风格不像 / Seedance 不复刻 Cut / 大图被压竖版 / 双轨锁定没生效）

### 🐛 低优先级修复（命名一致性）

- **Bug 16 · universal-storyboard-methodology.md 第 339 行**："v5 必须强制要求" → "v7.0 必须强制要求"
- **Bug 20 · transition-mechanism.md 第 23-24 行**："v5 新增" → "v7.0 新增"
- **Bug 22 · _backup-pre-storyboard-v5/README.md**：v5 命名统一为 v7.0；目录名保留原名（回滚路径不变）并加说明注解

### 🔧 修改文件清单

- `CLAUDE.md`（schema 扩展 + 指令执行流程 + 路径 B 四问）
- `USAGE.md`（剪辑步骤路径 + 故障排除 + partial regen）
- `.claude/agents/storyboard-artist.md`（历史兼容措辞）
- `.claude/skills/seedance-storyboard-skill/SKILL.md`（命名统一 + 4 级优先级）
- `.claude/skills/seedance-storyboard-skill/references/storyboard-style-decision-tree.md`（fallback 映射）
- `.claude/skills/seedance-storyboard-skill/references/universal-storyboard-methodology.md`（v5 → v7.0）
- `.claude/skills/seedance-storyboard-skill/references/transition-mechanism.md`（v5 → v7.0）
- `.claude/skills/_shared/user-messages.md`（第 4 问话术）
- `.claude/skills/_backup-pre-storyboard-v5/README.md`（v5 → v7.0 + 目录名说明）

### 🗑️ 删除文件

- `.claude/skills/seedance-storyboard-skill/templates/seedance-prompts-template.md`（孤儿 v6.1 模板，备份保留）

### 🔁 修复后回归（用户追问"确定没问题"触发的二轮审查）

在 14 个 bug 修复后做修复回归发现 6 个二阶问题，全数追加修复：

- **R1（高） · Bug 3/15 的修复方案需要分镜师配合**：`~feedback` 是个通道，分镜师默认收到反馈会重生全部 P0X
  - 修复：`storyboard-artist.md` 协作模式加 **Partial regen 检测**（步骤 2）：检测 `storyboards/` 目录现状，已存在部分 P0X-storyboard-prompt.md → 进入 partial regen 模式仅生成缺失文件
- **R3（高） · 老项目 `.project-config.json` 缺新字段时分镜师会卡住**：双轨判定优先级 1+2 字段不存在时行为未定义
  - 修复：SKILL.md [双轨模式判定] 明确「**字段不存在 → 跳过本级进入下一级**，不要报错」+ 注明 v6.1 老项目兼容路径
- **R5（中） · ~settings 不能改双轨字段会让用户困惑**：用户可能误以为一站式
  - 修复：`CLAUDE.md` ~settings 段加注「双轨锁定 / 故事板风格请用 ~storyboard-mode / ~storyboard-style」
- **R6（中） · 跨集风格统一 vs ~storyboard-style 优先级不明**：决策树 §一 没体现跨集沿用，伪代码也没参数
  - 修复：决策树升级为 **5 维度**（新增维度 1.5「跨集风格沿用」，仅 ep02+ 触发）；伪代码加 `previous_episode_style` + `current_episode` 参数；自检 checklist + frontmatter description 同步更新
- **R7（中） · episode-master 模板不支持 SKILL.md 允许的「按 P0X 粒度混合」**：模板「模式」字段是单值
  - 修复：episode-master.template.md 「本集模式」加 `mixed` 选项；模板使用注意从「双模式」扩展为「三种模式」（纯故事板 / 纯单镜 / 混合）；§七 用户操作清单允许混合时同时填 7.1+7.2

R2 / R4 / R8 验证通过无需修复：episode-master.template.md 已有 §七用户操作清单 ✓；路径 A 视觉风格通过编剧采访第三轮 + 设定 11 项第 9 项问 ✓；ASMR 单镜路径完整可用 ✓。

### 🎯 审查方法论沉淀

本次审查借鉴 `skill-creator` 的「Progressive Disclosure」「解释为什么不是 MUST」「Principle of Lack of Surprise」原则作为审查维度。所有 SKILL.md 文档 < 500 行 ✓，符合最佳实践。

**重要教训**：被用户追问"确定吗"是关键时刻——专业架构师此时应该做修复回归（验证修复本身是否引入新 bug），而不是简单确认。本轮 R1-R8 验证确实又发现 6 个二阶问题，证明追问是有价值的。

完整 bug 报告 + 修复细节见本次审查会话。

---

## v7.0 — 2026-05-24（万能故事板升级）

**主题**：吸收 11 个工业级故事板案例精华，把分镜师阶段从「单镜模式」扩展为「双轨模式（万能故事板 + 单镜）」

### ✨ 新增能力

- **双轨模式**（分镜师默认行为升级）：
  - **故事板模式**（v7.0 新增）：每个剧情点 P0X 输出一份万能故事板提示词 → 用户去 Nano Banana / 即梦生 P0X-storyboard.png 高密度复合图 → 视频提示词每 Cut 单图引用 P0X-storyboard.png
  - **单镜模式**（沿用 v6.1）：视频提示词每 Cut 多图引用 character/scene/prop 各自参考图
  - **判定优先级**：用户 `~storyboard-mode` 显式指定 > 导演讲戏本「建议形态」字段 > AI 决策树
- **万能故事板 6 必备 + 4 可选模块**：
  - M1 元数据 / M2 角色 / M3 场景 / M4 分镜网格 Cut 1-N / M5 底部辅助声音设计 / M6 衔接 frontmatter（必备）
  - O1 风格说明 / O2 道具特写 / O3 转场设计 / O4 配色板（可选）
  - 详见 `seedance-storyboard-skill/references/universal-storyboard-methodology.md`
- **故事板风格 4 维度决策树**（用户偏好 / 题材 / 场景复杂度 / 项目 visual_style 联合决策）：
  - 5 候选风格：cinematic_realism / disney_3d_animation / epic_realism / commercial_clean / black_white_manga_lineart
  - AI 自决，主动告知用户【模式选择】+【故事板风格判定】
  - 详见 `seedance-storyboard-skill/references/storyboard-style-decision-tree.md`
- **衔接机制**（防止 AI 跨段画面割裂）：
  - 每个 P0X 的 frontmatter 必填 `from_previous` + `to_next` 字段
  - 跳跃风险标记 → 提示导演/用户在剪辑期补镜或转场
  - 详见 `seedance-storyboard-skill/references/transition-mechanism.md`
- **episode-master.md 全片总览**（v7.0 新增分镜师必输出）：
  - 含本集大纲 / 衔接表 / 资产清单 / 用户操作说明
  - 模板：`seedance-storyboard-skill/templates/episode-master.template.md`
- **导演讲戏本「建议形态」字段**（v7.0 新增）：
  - 每个剧情点 P0X 给出「故事板 / 单镜 / 随他」三选一建议及一句话理由
  - 仅建议，分镜师保留决策权
- **新指令**：
  - `~storyboard-mode <storyboard|single-shot> [<集数|global>]` 手动锁定双轨形态
  - `~storyboard-style <名>` 手动锁定故事板风格

### 🔧 联动修改

- **`seedance-storyboard-skill/SKILL.md`** 完整重写——双轨流程 / 风格决策树调用 / 衔接机制 / Cut 1-N 编号 / episode-master 输出说明 / 用户操作引导
- **`seedance-prompt-review-skill/SKILL.md`** 重写审核 checklist——故事板模式 6 必备模块齐备 / 可选模块合理性 / 衔接字段完整性 / Cut 1-N 编号 / 时长约束 / episode-master 存在性 / 整体连贯性
- **`storyboard-artist.md`** 升级 description + 分镜格式 + 镜头模板 + 输出位置三件套 + 协作铁律（保留单镜兼容、加入故事板专有规则、底线条款）
- **`director.md`** 阶段二讲戏加「建议形态」输出 / 阶段五审核加双轨审核维度 / 新增 [建议形态字段] 段
- **`CLAUDE.md`** 文件结构 / 资产归档规则 / 单集进度判断 / 工作流程 [分镜编写阶段] / 指令集（含 ~storyboard-mode 与 ~mode 区分注释）/ 版本号 v6.1 → v7.0
- **`_shared/user-messages.md`** `~help` 手册新增【分镜双轨控制】段
- **`USAGE.md`** 标题升至 v7.0 / 卡 4 阶段速查加双轨说明 / 提示词使用流程更新双轨产物路径 / 常用指令加 ~storyboard-mode 与 ~storyboard-style

### 📂 文件清单

**新增**（11 个）：
- `.claude/skills/seedance-storyboard-skill/references/universal-storyboard-methodology.md`
- `.claude/skills/seedance-storyboard-skill/references/storyboard-style-decision-tree.md`
- `.claude/skills/seedance-storyboard-skill/references/transition-mechanism.md`
- `.claude/skills/seedance-storyboard-skill/examples/universal-storyboard-example-cinematic.md`
- `.claude/skills/seedance-storyboard-skill/examples/universal-storyboard-example-animation.md`
- `.claude/skills/seedance-storyboard-skill/examples/universal-storyboard-example-commercial.md`
- `.claude/skills/seedance-storyboard-skill/examples/universal-storyboard-example-comedy-lineart.md`
- `.claude/skills/seedance-storyboard-skill/templates/episode-master.template.md`
- `.claude/skills/_backup-pre-storyboard-v5/`（v6.1 状态完整备份）
- `outputs/<集数>/storyboards/`（运行时按需创建）
- `outputs/<集数>/episode-master.md`（运行时按需创建）

**修改**（10 个）：
- `CLAUDE.md`、`CHANGELOG.md`、`USAGE.md`
- `.claude/agents/storyboard-artist.md`、`.claude/agents/director.md`
- `.claude/skills/seedance-storyboard-skill/SKILL.md`
- `.claude/skills/seedance-prompt-review-skill/SKILL.md`
- `.claude/skills/_shared/user-messages.md`

**输出文件路径变化**：
- `outputs/<集数>/02-seedance-prompts.md` → 变为历史兼容（v6.1 项目仍可读，v7.0+ 不再产出）
- `outputs/<集数>/video-prompts.md`（双轨视频提示词表，新主产物）
- `outputs/<集数>/episode-master.md`（全片总览，新增）
- `outputs/<集数>/storyboards/P0X-storyboard-prompt.md`（仅故事板模式产出）

### 🎯 设计原则（v7.0 沉淀）

- **手段服务目的**：故事板是手段不是目的——一切为「让 AI 产出高质量 15s 片段」服务。如果某 P0X 用单镜更适合（长镜头抒情等），主动选用单镜模式，不为故事板而故事板。
- **建议非命令**：导演给「建议形态」字段，分镜师保留决策权。AI 决策树给候选，用户保留覆盖权。
- **风格解耦**：故事板大图自身风格（5 候选）与视频画面风格（项目 visual_style）解耦。
- **衔接靠设计层**：跨段连贯性靠 from_previous + to_next 描述层呼应，不依赖 AI 跨段像素对齐。
- **历史兼容不留代价**：v6.1 项目仍能读 02-seedance-prompts.md，但 v7.0+ 项目走双轨新路径，老路径不再产出。

---

## v6.1 — 2026-05-22

**主题**：AI 约束现代化 + 联动净化 + CLAUDE.md 再瘦身

### ✨ 能力更新

- **`_shared/ai-generation-constraints.md` 大改**（配合 Seedance 2.0 + image2image 能力升级）：
  - 删除 1.3 节拍密度上限、1.4 头尾安全区、1.5 文字和精确细节难还原
  - 删除 2.1 跨图人物一致性需参考图、2.2 文字 OCR 不可靠、2.3 复杂姿态/肢体扭曲
  - 修改 1.2：仅保留「禁止配乐/背景音乐」（Suno 双轨冲突），删除「禁止对白/旁白」
  - 重编号 2.4→2.1（仅保留风格漂移约束）
  - 重写第四节「红绿灯速查」、第五节「自检清单」、第六节「与其他共享文件的关系」

### 🔧 联动修改（9 个文件）

- **`director-skill/SKILL.md`** — 删除节拍密度约束 + 头尾安全区段；修复 [创作五原则]→[创作九原则]
- **`seedance-storyboard-skill/SKILL.md`** — 删除节拍密度/头尾安全区引用
- **`seedance-storyboard-skill/seedance-prompt-methodology.md`** — 删除节拍密度 + 头尾安全区 + 禁忌规则中的节拍过密；BGM 段加「本项目不使用」标注
- **`script-analysis-review-skill/SKILL.md`** — 评分表删除节拍密度列/头尾安全区行
- **`seedance-prompt-review-skill/SKILL.md`** — 删除动作可执行性中 1拍≈2.5秒引用
- **`review-methodology.md`** — 合并 film-rating-rubric.md 全部行业 8 维评分内容；修复示例中的过期引用
- **`_shared/film-rating-rubric.md`** → **删除**（内容已合并到 review-methodology.md）
- **`bianju-skill/references/format-templates.md`** — 删除 6 处节拍密度行（节拍密度极高→信息密度极高）
- **`director-skill/templates/director-analysis-template.md`** — 更新 ai-generation-constraints 引用

### 🐛 Bug 修复（6 个）

- **audience-engagement-guide.md 章节编号错误**：八→十一→九→十 修复为 八→九→十→十一；全局 10 处 `第十一节`→`第八节`
- **分集标签机制 3 处重复**：提取为 `_shared/episode-tagging.md`（新建），art-designer.md / music-director.md / art-design-skill SKILL.md 改为引用
- **README.md 版本号过期**：v5.0 → v6.1
- **seedance-prompts-template.md 模板示例与红线冲突**：`@音频1 | 背景音乐` → `@音频1 | 环境音效/语音参考（本项目不用于背景音乐）`
- **CLAUDE.md [创作五原则]→[创作九原则]**：全局统一为 [创作九原则]

### 📉 CLAUDE.md 瘦身

- **[创作九原则] 段**：~78 行 → ~28 行（移除所有「责任分布」块——已下沉到各 agent/skill 文件）
- **[工作流程] 段**：~199 行 → ~14 行（移除「第X步」枚举细节——各 agent 文件已有完整流程）
- 净减少约 **235 行**

### 📂 文件清单

**新增**：
- `.claude/skills/_shared/episode-tagging.md`

**删除**：
- `.claude/skills/_shared/film-rating-rubric.md`（合并入 review-methodology.md）

**修改**：
- `CLAUDE.md`、`CHANGELOG.md`、`README.md`
- `.claude/skills/_shared/ai-generation-constraints.md`、`review-methodology.md`、`audience-engagement-guide.md`
- `.claude/skills/director-skill/SKILL.md`、`director-skill/templates/director-analysis-template.md`
- `.claude/skills/seedance-storyboard-skill/SKILL.md`、`seedance-storyboard-skill/seedance-prompt-methodology.md`、`seedance-storyboard-skill/templates/seedance-prompts-template.md`
- `.claude/skills/script-analysis-review-skill/SKILL.md`
- `.claude/skills/seedance-prompt-review-skill/SKILL.md`
- `.claude/skills/art-design-skill/SKILL.md`
- `.claude/skills/bianju-skill/references/format-templates.md`
- `.claude/agents/art-designer.md`、`.claude/agents/music-director.md`

### 🎯 设计原则（v6.1 沉淀）

- **最低 token 成本原则**：CLAUDE.md 每行都向「制片人需要知道什么」严格审计——agent 自身方法论下沉到 skill，不重复
- **约束即抑制原则**：AI 技术约束须随模型能力同步演进——过时的约束不是在保护产出，而是在压制能力
- **单一真相源原则**：分集标签不再 3 处重复；film-rating-rubric 不再游离于 review-methodology 之外

## v6.0 — 2026-05-22（对标爆款 · 反向反馈环 · 瘦身；本标题于 v13 补回）

**主题**：对标爆款机制 + 反向反馈环 + CLAUDE.md 瘦身

### ✨ 新增能力

- **对标爆款机制**（编剧采访 + 路径 B 启动 + `~settings` 三处接入）：
  - 必问项第 12 题（编剧采访）/ 第 3 问（路径 B）：用户三选一回答
    - **A 有对标**：用户给 1-5 个账号/视频/作品名 → 写入 `script-settings.md > 对标爆款` 段，标注"取哪一面 / 不要照搬哪一面"
    - **B 没有但要推荐**：编剧/制片人基于题材+平台+画像 推 3-5 个候选让用户认领
    - **C 不要对标**：写入「无（用户主动声明）」，下游切换"通用爆款逻辑"模式不再做对标气质评分
  - `_shared/audience-engagement-guide.md` 加第十一节「对标爆款使用方法」（含气质提取方法 / 抄袭红线 / 多对标处理 / 评分标准）
  - 3 个业务审核 skill 的「受众适配」维度加「对标气质相似度」子项（仅在有对标时启用）
  - `_shared/review-methodology.md` 加「子项：对标气质相似度」段统一评分标准
- **反向反馈环** `outputs/<集数>/feedback-to-upstream.md`：
  - CLAUDE.md 新增 [反向反馈协议] 段（写入格式 / 三类写入源 / 制片人处理时机 / 三个原则）
  - 5 个 agent 的协作铁律全部加「反向反馈通道」条款
  - 新指令 `~feedback <文本>`：用户主动给上游 agent 提改进意见
  - 制片人在每个阶段开始前**主动检查**未处理反馈并转达上游
  - `~status` 显示「未处理上游反馈：N 条」
- **用户消息单一真相源** `.claude/skills/_shared/user-messages.md`（v6 新增）：
  - 集中存放所有"对用户说的话"模板（欢迎 / 介入模式 / 路径 B 三问 / 各阶段完成通知 / 迷路救援 / status & help / 反馈通道 / settings / 错误兜底等）
  - CLAUDE.md 改用 `见 user-messages.md > <锚点>` 引用，逻辑与文案彻底解耦
  - 改话术不动主控，迭代主控不会误改用户体验

### 🔧 优化

- **CLAUDE.md 瘦身**：从 475 行 / 58.7KB 减到 382 行 / 55.4KB（净减 93 行；其中加入了新协议 ~30 行，实际话术抽离收益 ~120 行）
- **路径 B 启动补设定**：从 2 问扩到 3 问（加对标爆款），用户回答更结构化
- **AGENTS.md / USAGE.md 指令速查同步更新**

### 📂 文件清单

**新增**：
- `.claude/skills/_shared/user-messages.md`（用户话术单一真相源）
- `outputs/<集数>/feedback-to-upstream.md`（每集运行时按需创建）
- `.reference/v5.0/`（v5.0 完整快照归档，18 个文件）

**修改**：
- `CLAUDE.md` — 瘦身 + [反向反馈协议] + 路径 B 三问 + ~feedback 指令 + 引用 user-messages
- `USAGE.md` — v6.0 头部 + 卡 2 三问 + 卡 3 加 ~feedback + 阶段速查加 ~feedback / ~settings
- `AGENTS.md` — 指令速查表加 ~settings / ~feedback / 对标说明
- 5 个 agent 文件 — 协作铁律全部加「反向反馈通道」
- `bianju-skill/SKILL.md` — 创意采访加第 12 题对标爆款（三种回答路径）
- `_shared/audience-engagement-guide.md` — 加第十一节「对标爆款使用方法」
- `_shared/review-methodology.md` — 加「子项：对标气质相似度」
- 3 个业务审核 skill — 「受众适配」加对标气质子项

### 🎯 设计原则（v6 沉淀）

- **解耦原则**：逻辑与文案分离（CLAUDE.md vs user-messages.md）；同阶段闭环 vs 跨阶段反馈分开（director 审核 vs feedback-to-upstream）
- **三态原则**：对标 / 反馈 / 配置都允许"明确声明无"作为有效状态——避免凭空推断
- **不积累原则**：反馈池每次进阶段先清理；归档每次升版做快照

---

## v5.0 — 2026-05-17（封版）

**主题**：流量审视维度入主线 + 链路完整性修复

### ✨ 新增能力

- **创作九原则**（5 → 9）：
  - #7 细节即灵魂（90% 高级感来自被认真对待的细节）
  - #8 反流水线（拒绝套路化处理）
  - #9 为流量服务（艺术性 + 平台规则 = 被看到）
- **受众参与度共享方法论** `_shared/audience-engagement-guide.md`：
  - 7 大平台规律对照表（抖音/快手/小红书/视频号/B站/YouTube/TikTok/院线影展）
  - 马斯洛需求层次应用于内容设计
  - 完播率三段式优化（前 3 秒 / 中段钩子链 / 结尾设计）
  - 互动率金字塔（关注 > 分享 > 收藏/评论 > 点赞 > 完播）
  - 目标受众画像模板（写给一个具体的人）
- **3 个业务审核 skill 加「受众适配」必评维度**（不是补充视角，是评分列）
- **音乐设计 skill 加第九节「受众适配性自检」**（导演审核音乐时使用）
- **编剧采访模板加两个必问项**：目标平台 + 受众画像，写入 `script-settings.md`
- **`~settings` 指令**：用户可随时查看/修改目标平台/受众画像/视觉风格
- **路径 B 启动补设定**：跳过编剧的项目也会被引导补全目标平台/受众画像

### 🔧 修复

- **链路修复**：服化道 + 分镜师 agent 的 [输入源] 现在显式读取 `script-settings.md` —— 之前漏读，导致"受众适配"评分变空话
- **路径 B `script-settings.md` 缺失问题**：通过启动前两问补全机制解决

### 📂 文件清单（新增）

- `assets/visual/changelog.md`（前一轮已建）
- `.claude/skills/_shared/audience-engagement-guide.md`（282 行）
- `CHANGELOG.md`（本文件）

---

## v4.0 — 2026-05-17（中间版本）

**主题**：音乐总监深度吸收 + 五原则 +1

### ✨ 新增能力

- **创作六原则**（5 → 6）：加 #6 克制的表达（潜台词冰山）
- **音乐总监 references 大扩展**：
  - `parody-adaptation.md`（改编已有歌方法论）
  - `vocal-pronunciation-tricks.md`（双语 AI 歌手发音诡计）
- **SKILL.md 第七节加 3 点**：Style 字段真实容量（1000 上限/200 推荐）/ Vocal Persona / Exclude Styles
- **SKILL.md 第八节红线加避免艺人名/商标**（带 6 个对照案例）

---

## v3.0 — 2026-05-16

**主题**：AI 生成约束 + 资产归档优化

### ✨ 新增能力

- **`_shared/ai-generation-constraints.md`**：AI 生图生视频技术约束清单（防方法论违反硬约束）
- **「丝滑过渡」彻底重写为设计层**：不是要求 AI 跨段帧粘合，而是用呼应描述制造观众脑中连贯感
- **资产归档规则**：明确 agent 直接产出到目标位置 + 导演审核 PASS 才接受（不做两步同步）
- **`assets/visual/changelog.md`** 跨集变体集中归档

### 🔧 修复

- 删除 CLAUDE.md 五原则 #2 中"分镜师让相邻提示词最后一帧/第一帧呼应"这一 AI 不可达的硬约束
- 全量扫描确保零残留"AI 不可达"的硬要求

---

## v2.0 — 2026-05-16

**主题**：服化道关键道具 + 音乐双文档 + 山音知识吸收

### ✨ 新增能力

- **创作五原则**（新增整段）：开头抓人 / 丝滑过渡 / 马上交代 / 超绝创意 / 一发入魂 OST
- **全 agent 协作铁律**（新增整段）：角色边界 / 主动修世界观 bug / 采访协议
- **关键道具资产**：服化道兼任 → 新增 `assets/visual/prop-prompts.md`
- **视频提示词禁配乐红线**：seedance 提示词禁止描述背景音乐（避免与后期 Suno 双轨冲突）
- **音乐双文档**：原创音乐 `music-design.md`（少而精）+ 市面推荐 `music-recommendations.md`（多而精）
- **bianju-skill 大扩展**：横截面理论 + 戏剧动作 + 写作红线 + 4 类格式系统 + 5 个 references 文件（皮克斯 22 条 / 台词十原则 / 选题工具库 / 角色深度方法论 / 格式模板）
- **director-skill 加关键道具识别 + 剧本医生自检**
- **seedance-storyboard-skill references**：动画 12 原则
- **`_shared/film-rating-rubric.md`**：行业 8 维评分参考

---

## v1.0 — 2026-05-15

**主题**：5 个 agent + 5 阶段 + 双步审核架构搭建

### ✨ 初始能力

- 5 个 agent（编剧 / 导演 / 服化道 / 音乐总监 / 分镜师）
- 5 阶段流程（编剧创作 → 导演分析 → 服化道 → 音乐设计 → 分镜编写）
- 双步审核（业务审核 + 合规审核）
- 介入模式（autonomous / key_node / full_control）
- 路径 A（从选题创作）vs 路径 B（跳过编剧）
- Resumable Subagents 机制
- 4 个 _shared 文件骨架：review-methodology.md（其他后续版本添加）
- 完整的指令集（`~write` / `~start` / `~design` / `~music` / `~prompt` / `~status` / `~help` / `~mode` / `~skip music`）
- 跨工具兼容（Claude Code + Codex + Cursor + Windsurf）

---

## 待办（下轮迭代候选）

以下 3 项在 v5.0 规划时被明确"本轮不做"，留作下轮迭代候选：

1. **对标爆款机制**：编剧采访加「对标爆款」字段（用户提供 3-5 个想对标的账号/视频链接），写入 script-settings.md，所有 agent 心里有标杆
2. **反向反馈环**：下游 agent 发现上游问题时可写入 `outputs/<集数>/feedback-to-upstream.md` 由制片人转达
3. **标题/封面/元数据产出**：最后交付阶段生成 `outputs/<集数>/03-distribution-meta.md`（5 个备选标题 + 3 个封面设计建议）

其他潜在改进点：
- 介入模式触发条件更明确（autonomous / key_node / full_control 的边界更清晰）
- 多语言项目（英文/双语）的支持优化
- 商业化项目的标准合规模板

---

## 版本号规则

- **主版本（v5 → v6）**：原则升级 / 架构大改 / 新增 agent
- **次版本（v5.0 → v5.1）**：能力扩展 / 新增 skill / 新增 references
- **补丁版本（v5.0 → v5.0.1）**：bug 修复 / 文案修订 / 链路修补

每次版本升级时在本文件顶部追加新段落。
