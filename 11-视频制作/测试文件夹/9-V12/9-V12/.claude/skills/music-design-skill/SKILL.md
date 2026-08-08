---
name: music-design-skill
description: 音乐设计方法论技能，用于整体音乐方案设计、配乐情绪指令、OST 主题曲歌词创作、Suno 提示词工程，以及**双文档输出**（原创音乐 music-design.md 少而精 + 市面已有音乐推荐 music-recommendations.md 多而精，含多平台搜索名/服务于本项目的理由/推荐使用片段/版权提示）。涵盖音乐策略选择（极简型/标准型/丰富型）、词作风格库（中文项目优先唐恬风+方文山风+第三种差异化风格；英文项目从 Bob Dylan/Taylor Swift/Frank Ocean 等不同轨迹词人中选）、Suno meta-tag 规范（[Verse]/[Chorus]/[Instrumental] 等）、Style 描述粒度要求（推荐 200 字符内、具体到乐器/BPM/人声特征/Vocal Persona）、Exclude Styles 负向控制、严禁使用艺人名/商标。**改编场景**（用户带已有歌旋律重写歌词）需调用 references/parody-adaptation.md。**英文项目和发音矫正**需调用 references/vocal-pronunciation-tricks.md。核心理念：少即是多、不为"显得专业"堆音乐、不纠结精准时长（视频 15 秒分段剪辑）。当音乐总监 agent 进入阶段四音乐设计、需要写 Suno 提示词、创作歌词、改编已有歌、或编写市面音乐推荐清单时，都应触发此 skill。
---

# 音乐设计方法论技能

[技能说明]
    音乐总监 agent 在阶段四执行音乐设计的完整方法论。包含**五类内容**：
    1. **音乐策略选择**：极简型 / 标准型 / 丰富型（克制审美）
    2. **词作风格库**：中文/英文词作高手参考与调用规则
    3. **Suno 提示词工程**：Style 描述、Lyrics 结构、Meta-tag 规范
    4. **双文档输出机制**：原创音乐（少而精）+ 市面已有音乐推荐（多而精）
    5. **工作流程**：从研读上下文到双文档产出的六步法

    本 skill 不重复 agent 的"角色定位"和"协作模式"——那些保留在 `music-director.md` 中。

[文件结构]
    music-design-skill/
    ├── SKILL.md                                    # 本文件
    └── references/                                  # 扩展素材（按需加载）
        ├── suno-advanced-tags.md                   # Suno 进阶 metatags 大全（结构/人声/动态/氛围/音效）
        ├── chinese-prosody.md                      # 中文词作韵律（四声、押韵、唐恬风、方文山风等）
        ├── vocal-pronunciation-tricks.md           # 让 AI 歌手唱对发音（双语通用，英文项目必备）
        └── parody-adaptation.md                    # 改编已有歌的方法论（用户带旋律要求重写歌词时调用）

---

## 一、专业底蕴（你能调用的风格库）

### 风格覆盖面（迄今所有主流与小众）

**华语**：中国风/古风、民谣、民乐（笛/箫/古筝/二胡/琵琶）、中国摇滚、黄金年代港台流行、粤语流行、台语/闽南语歌谣、城市民谣

**亚洲**：J-Pop、City Pop、K-Pop、Anison、动画 OST（Joe Hisaishi / Yuki Kajiura / Yoko Kanno / RADWIMPS）、民族音乐、佛曲/梵唱

**西方**：
- Classical / Romantic / Minimalism（Reich / Satie / Glass / Arvo Pärt / Max Richter）
- Jazz / Blues / Soul / R&B
- Folk / Country / Americana
- Rock（软摇 / 硬摇 / Indie / Punk / Post-rock）
- Pop（80s / Synth / Bedroom / Hyperpop）
- Hip-Hop / Trap / Drill / Lo-fi
- Electronic（House / Techno / Dubstep / IDM / Ambient / Drum&Bass）
- Cinematic / Trailer
- Score（Hans Zimmer / Max Richter / Jonny Greenwood / Mica Levi）
- 拉丁 / 弗拉明戈 / 雷鬼顿 / Bossa Nova
- Goth / Dark Wave / Synth Pop / Neo-folk

**跨界**：A Cappella、Choral、电影手法型环境音乐、ASMR、场景化音效（Sound Design）

要点：能辨识并调用子风格、各代表性乐手/作品、招牌乐器、典型 BPM 与调式。

---

## 二、词作人素养（中英文双库）

### 中文词作核心风格（优先调用）

**唐恬风**（金句凝练 / 事件叙事型 / 化叙事为意象 / 情绪不外露但击中要害）
- 代表作：《孤勇者》《赢》《誓言》《魂》
- 特征：高高举起轻轻放下、为后半句造势、**拒绝"高级感"堆词**

**方文山风**（画面感强 / 意象拼贴 / 中国风古典意境 / 以象代言）
- 代表作：《青花瓷》《菊花台》《东风破》《千里之外》
- 特征：象征物堆叠、古风词汇重染色彩、宝藏在细节

**其他可调用**：
- 林夕的哲思口语型
- 黄伟文的总体叙事型
- 罗大佑的时代反思型
- 互联网作词人的现代口语型

### 英文词作参考（按项目需要调用）

| 类型 | 词人 |
|------|------|
| 叙事诗意型 | Bob Dylan、Leonard Cohen、Joni Mitchell、Nick Cave |
| 当代叙事型 | Taylor Swift（场景化叙事）、Phoebe Bridgers、Mitski、Lana Del Rey、Hozier |
| 现代 R&B / 灵魂 | Frank Ocean、SZA、Daniel Caesar |
| 摇滚诗意 | Thom Yorke（Radiohead）、Florence Welch、Patti Smith |
| 拉丁 | Jorge Drexler（叙事）、Mon Laferte（焚烧型） |

**调用原则**：根据歌曲需求选适合原型，**不为试而试**。

---

## 三、核心信条："少即是多"

大多数高级影视作品音乐用得**克制**，关键在精不在多。

### 工作重心 — 只讲剧情/人物/情绪，不纠结时长

**项目现实**：视频生成模型单条最长 ≈ 15 秒，用户后期会手工剪辑并调整镜头时长。

**因此你的工作重心是**：

✅ 联剧情：这段音乐服务哪个剧情点？叙事作用是什么？
✅ 联人物：这是谁的心声？谁的主题？人物弧光如何被音乐塑造？
✅ 联情绪：这里是铺垫、递进、转折还是高潮？情绪关键词是什么？
✅ 联画面：闭眼能看到什么画面听到这段音乐？

**而不是**：

❌ 纠结"这段该 28.5 秒还是 32 秒"——时长仅作为大致估计（如"约 30 秒"/"约 1 分钟"）
❌ 要求 Suno 生成精准时长的音乐——让音乐完整表达，用户剪辑时会 trim/loop
❌ 为了"对拍镜头"而牺牲音乐的叙事完整性

---

## 四、音乐策略（三选一，优先极简）

| 策略 | 适用 | 内容 |
|------|------|------|
| **极简型** | 大部分短片 | 只用 1 首 OST 主题曲 |
| **标准型** | 中等复杂度 | 1 首主题曲 + 2-4 段关键配乐 |
| **丰富型** | 仅在剧情确实需要时 | 主题曲 + 多段配乐 + 氛围音效 |

**反复自问**（决定策略前）：
- 这个故事真的需要这么多音乐吗？
- 哪些段落用静默/环境音反而更有力量？
- 一首贯穿全片的主题曲能否撑起情绪？

**默认偏好**：优先选极简型，除非剧情明确要求丰富配乐。

---

## 五、工作流程（五步法）

### 第一步：研读上下文

1. 读取剧本和导演分析，提取情绪曲线和关键剧情节点
2. 读取剧本设定理解整体基调和目标媒介
3. 浏览 `input/选题/` 和 `input/参考/` 寻找用户的音乐线索（参考歌曲、参考片）
4. **改编场景识别**：如果用户提供了"已有歌的旋律 + 要求重写歌词"的诉求（参考歌不是单纯"想要这种风格"，而是"用这首歌的旋律但换词"），切换到 [改编场景特殊流程] —— 详见 `references/parody-adaptation.md`，本场景下歌词必须严丝合缝贴合原歌的音节数/重音/押韵/拖音元音，与普通歌词创作的方法论不同。

### 第二步：决定音乐策略

按"少即是多"原则反复自问，选定策略（极简型 / 标准型 / 丰富型）。

### 第三步：撰写**原创**整体方案 + 逐段指令

写入 `assets/music/music-design.md`（少而精）。逐段指令格式见第六节 [原创音乐输出规范]。

### 第四步：如有人声歌曲 → 创作 3 版歌词

**写词前必做：提炼精神内核（v11.0 新增）**
剧情细节是素材，精神内核是灵魂。不能直接从剧情搬细节进歌词——必须先回答这个问题：
> 这部片子/这个角色的内心里，最根本的是什么？如果用一句话概括它最想说的话，是什么？

提炼方式：
- 从剧情、人物弧光、情感曲线中找规律，不是找事件
- 问"这个故事的本质矛盾是什么"（比如：外表工具人/内心清醒人的生存博弈）
- 这个内核才是词应该传达的东西；剧情细节（如"三千斤铁"、"账房书案"）是具体化这个内核的素材，不是词的目的本身

举例：
- 剧情素材：苟道书房先生被御史审问铁料账目
- ❌ 词的错误路径：把"铁料""账本""御史"直接堆进词里 → 故事摘要不是词
- ✅ 词的正确路径：精神内核是"在看透规则的前提下选择低头求活，清醒比反抗更沉重" → 以这个为骨，把"铁料""账本"作为具象意象填充进去

---

1. 三版**风格必须迥异**（不是同一词人的不同作品，而是不同轨迹的词人）
2. 每版给出明确的风格定位（引用 references/chinese-prosody.md 中的词人风格决策树）
3. 每版写完后，**必须先过两份自检清单再输出**（见下方「歌词双自检」）
4. 写入 `assets/music/lyrics-drafts.md`
5. 输出三版时附上**选择辅助说明**（每版一行：适合什么场合/平台/情绪，帮用户做有依据的选择而非凭感觉）
6. 输出"⚠️ 等待用户确认采用哪一版"，**停下来等用户选**

**为什么必须三版**：用户最难判断的不是"歌词写得好不好"，而是"这种风格是不是我要的"。三版让用户在风格层面做选择，比让你猜更可靠。

---

### 【歌词双自检】（每版歌词输出前必须执行，内部完成，不展示给用户）

#### ✅ 清单一：好唱性自检（参照 references/chinese-prosody.md）

逐行过以下8项，有任何一项不通过则修改后再输出：

| # | 检查项 | 说明 |
|---|--------|------|
| 1 | **每段内句末押韵** | 副歌每行末字必须在同一辙；Verse 可换辙但段内须一致（参照13辙系统） |
| 2 | **每行字数均衡** | 同段落中各行字数差距不超过 ±2 字；超出须调整或用连读处理 |
| 3 | **声调与旋律走向匹配** | 旋律上行处避免纯降调字（去声）结尾；旋律下行处避免上声字单独收尾 |
| 4 | **拖音位置落开口元音** | 长音/拖音必须落在 a / o / e 等开口音上，避免 ü / i 等闭口音 |
| 5 | **多音字/生僻字已处理** | 参照 references/vocal-pronunciation-tricks.md 改写或注音 |
| 6 | **气口/换气位置自然** | 每 2-3 行内有可自然停顿的位置；不出现连续 5 行以上无停顿 |
| 7 | **高音区字选开口元音** | 若有旋律高潮段（副歌顶点），该行关键字须为开口大元音 |
| 8 | **重复段有微变化** | 副歌第二次反复时，至少有一行有细微文字变化（不是纯复制粘贴） |

#### 🐛 清单二：意象/内容逻辑 bug 检查（无对应 reference，此处为完整规则）

逐条检查，发现 bug 必须修改，不可带 bug 输出：

| # | 检查项 | 典型 bug 示例 |
|---|--------|-------------|
| 1 | **时间线一致性** | 同一场景里"昨日"和"明天"无理由混用；全歌时态跳跃无叙事逻辑 |
| 2 | **空间一致性** | 同一情境"窗边"+"草原"+"地铁"无过渡地混出现，破坏画面感 |
| 3 | **意象系统一致性** | 全歌的意象是否属于同一情感语境圈（"海""水""漂流"为一圈；"钢铁""机器""冷"为另一圈；无故混用须有意图）|
| 4 | **隐喻不互斥** | 把主角比作"脆弱的花"又比作"钢铁战士"——两套隐喻直接冲突（除非是刻意对比，须显性处理）|
| 5 | **人称一致性** | 我/你/他/我们在各段的指代是否清晰；无来由的视角切换会让听众困惑 |
| 6 | **情感方向一致性** | 同一段（Verse/Chorus）内情绪方向不能无理由180°反转 |
| 7 | **空洞词密度** | 检查是否有"永远/无尽/宇宙/灵魂"等虚大词；如有，问"能否替换为具体画面/动作？" |
| 8 | **歌词与Style标注一致性** | 歌词情绪（悲伤离别）vs Suno Style（upbeat pop）是否匹配；不匹配则改歌词或改Style |
| 9 | **因果/逻辑成立** | "因为..."型歌词，因果关系是否成立；"但是..."型转折，转折是否有足够张力 |
| 10 | **🔴 事实准确性（v11.0 新增）** | 歌词中出现的具体事实性声明（汉字笔画数、历史数据、角色特征、具体数字）必须准确。"苟道三画"——苟字实际8画，不是3画，经不起推敲，听起来有感觉但存在事实错误。检查方法：凡是歌词里出现"X字/X画/X年/X次"等量词精确描述，必须核实。如不确定，改成意象化描述（"苟字写满纸"）而非精确声明（"苟字三画"）。|

### 第五步：用户确认歌词版本后

1. 删除未选中的两版，只保留终选版本
2. **为有词歌曲输出至少 3 个 Suno Style 提示词变体（v11.0 新增）**：
   同一套歌词，用不同的风格参数生成会产生完全不同的听感，用户可以多试几个方向。
   每个变体必须在以下维度上有实质差异（不是换个顺序的同一堆词）：
   - 乐器组合（民乐 vs 电子 vs 弦乐 vs 吉他）
   - 人声风格（沙哑 vs 空灵 vs 浑厚 vs 少年感）
   - 节拍/BPM（慢板抒情 vs 中速叙事 vs 快节奏推进）
   - 整体氛围（古风悲情 vs 现代都市感 vs 戏曲融合 vs 电影感）

   输出格式（每个变体一块）：
   ```
   【Suno Style 变体 A】主方向：[一句话概括风格]
   Style: [完整 Style 描述，200字符内]
   Vocal Persona: [人声角色描述]
   适合的情绪/场景：[一句话说明何时用这个方向]

   【Suno Style 变体 B】主方向：...
   【Suno Style 变体 C】主方向：...
   ```

3. 把终选歌词嵌入终选 Suno Style 变体（用户选完风格后才合并），写入 `assets/music/music-design.md`

### 第六步：撰写**市面推荐**音乐清单（双文档机制的另一份）

为什么这一步：用户希望最终拿到两份音乐资产——原创（少而精）+ 市面已有歌曲推荐（多而精），自由选择使用，或两者结合（如主题曲用原创、转场配乐用市面成品）。

写入 `assets/music/music-recommendations.md`。每个用途至少推荐 3 首（A/B/C 备选），格式见第六节 [市面推荐输出规范]。

**核心要求**：
- **多而精**：每个用途多推几首（3-5 首），但每首都要说清"为什么服务本项目"，不要堆砌
- **多平台搜索名**：给出网易云 / QQ 音乐 / Spotify / Apple Music 各自的搜索词，避免变体名导致用户搜不到
- **推荐使用片段**：精确到秒（如"1:23-2:05 副歌段"），用户剪辑时一秒就能定位
- **服务本项目的理由**：1-2 句，说清这首歌为什么打中本项目的剧情/人物/情绪
- **版权提示**：每首歌结尾必须加一句版权风险提示（"此推荐为创意参考，最终使用前请自行核实版权和授权"）

**适用：纯配乐项目也要做这一步**（推荐市面已有的纯音乐/Score）。

---

## 六、输出规范（双文档）

### 文档 1：`assets/music/music-design.md`（原创音乐）

#### [整体音乐方案] 部分

- 音乐策略：极简型 / 标准型 / 丰富型 + **选择理由**
- 整体基调：情绪关键词 + 风格定位
- 音乐清单（编号 M1, M2... 含类型、时长估计、用途）

#### [原创音乐 - 逐段指令] 部分

每条音乐 = 一个独立模块，格式：

```markdown
## M01 - <用途说明，如"女主走进雨中的孤独主题">
- 对应剧情：<剧情点编号 / 场景描述>
- 服务人物：<谁的主题 / 谁的心声>
- 情绪作用：<铺垫/递进/转折/高潮/收束，以及为什么>
- 类型：纯配乐 / OST 主题曲（人声）/ 氛围音效
- 时长估计：<粗略范围，如"约 30-60 秒"/"约 2-3 分钟"，仅供参考>
- 情绪：<3-5 个情绪词>
- 风格描述：<通用音乐描述，1-2 句>
- 参考作品/乐手：<2-3 个参考点>

━━━ 🎵 复制这里到 Suno ━━━
Style: <主风格>, <sub-genre>, <key instruments>, <BPM 范围>, <人声类型/性别/音色>, <mood/atmosphere>, <年代/地域如适用>

[歌词区块或 Instrumental 标记]
━━━ 复制到此为止 ━━━
```

### [歌词三版] 部分（仅当方案含人声歌曲时）

**中文项目默认格式**：

```markdown
## OST 歌词 - 三版风格

### 版本 A：唐恬风（叙事凝练 / 高起低走 / 拒绝堆词）
[Verse 1]
...
[Pre-Chorus]
...
[Chorus]
...
[Verse 2]
...
[Bridge]
...
[Outro]
...

### 版本 B：方文山风（意象拼贴 / 古风画面 / 以象代言）
（同上结构）

### 版本 C：<第三种轨迹完全不同的风格，如现代口语 / 诗意摇滚 / 其他>
（同上结构）

⚠️ 等待用户确认采用哪一版
```

**英文项目**：三版各指定一位参考词人（如 版本 A=Leonard Cohen 叙事诗意型 / 版本 B=Frank Ocean R&B 意识流型 / 版本 C=Phoebe Bridgers 匿名描述型）。

### 文档 2：`assets/music/music-recommendations.md`（市面已有音乐推荐）

每集独立分块，格式：

```markdown
# ===== ep01 =====

## R01 - <用途，如「孤独主题（女主第一次意识到孤独）」>

对应剧情：P05（女主深夜独自走过空旷街道）
对应原创编号：M01（如有原创版本同用途；无原创版本则不写此行）

### 推荐 A：《歌名》/ 演唱者
- 词作人 / 作曲：xxx / xxx
- 核心情绪：3-5 个情绪词（如：孤独、城市夜晚、克制的悲伤）
- 服务于本项目的理由（1-2 句）：xxx
- 多平台搜索名：
  - 网易云：「歌名 演唱者」
  - QQ 音乐：「歌名 演唱者」
  - Spotify：「Song Title - Artist」（如有英文标题）
  - Apple Music：「Song Title - Artist」
- 推荐使用片段：1:23-2:05（副歌段，约 42 秒）
- 替代方案：如版权问题不可用，类似的还有《XX》《XX》
- ⚠️ 版权提示：此推荐为创意参考，最终使用前请自行核实版权和授权

### 推荐 B：《歌名》/ 演唱者
（同上结构）

### 推荐 C：《歌名》/ 演唱者
（同上结构）

## R02 - <用途>
（同 R01 结构）

# ===== ep02 =====
（本集复用 ep01 的市面推荐，无新增）
```

**编号规范**：用途编号统一用 `R` 前缀（Recommendation），与原创音乐 `M` 前缀区分。

**推荐 vs 原创的对应关系**：
- 同一个用途下可以**同时**有原创版本（M01）和市面推荐版本（R01）——用户二选一
- 也可以**只有**原创版本（用户决定全用原创）
- 也可以**只有**市面推荐版本（如转场配乐用市面成品省事）
- 由音乐总监根据剧情判断哪种更合适，但默认两套都给

---

## 七、Suno 提示词质量标准

### Style 描述

- **平台真实容量**：Suno V4.5+ 的 Style 字段支持上限 ~1000 字符；但**推荐控制在 200 字符以内**——超过 200 字符后，Suno 容易"困惑"（不是字段满了，而是同时塞太多概念会让模型抓不到重点）。例外：电影级 cinematic 段落或叙事性极强的歌，可适度突破到 400-500 字符，但必须每个词都精准。
- 逐项逗号分隔
- **先为后辅**（先主风格，再细节修饰）
- 包含：主风格、子流派、关键乐器、BPM 范围、人声特征、情绪/氛围、年代/地域（如适用）

**对照**：
| ❌ 抽象 | ✅ 具体 |
|--------|--------|
| `sad piano` | `sparse felt-piano, sustained low strings, 58 BPM, breathy female vocal in chest voice, intimate close-mic, late autumn dusk atmosphere` |
| `good emotional` | `melancholic, sparse piano, breathy female vocal, 65 BPM, late-night intimacy` |

**为什么必须具体到这个粒度**：Suno 的 Style 解析是"按词检索-组合"，模糊词如 "good"/"nice"/"emotional" 会被忽略或误读；具体词（乐器型号、BPM 数字、年代）能被准确命中。

### Vocal Persona（构建人声角色，不只是性别）

写 Suno Style 时，**不要只写 "male vocal" 或 "female vocal"**——要构建一个完整的"人声角色"，告诉 Suno 这个歌手是谁、有什么经历、怎么唱。

| ❌ 弱 | ✅ 强 |
|------|------|
| `female vocal` | `a weathered torch singer with smoky alto, slight rasp, who starts vulnerable and builds to devastating power by the bridge` |
| `male vocal` | `a tired troubadour with grainy baritone, conversational delivery in verses, controlled belt in choruses, like someone telling you a story over whiskey` |
| `child singer` | `a 12-year-old girl with crystalline soprano, untrained but pure, conveys innocence without sentimentality` |

**为什么重要**：人声 persona 描述（vs 单纯性别）能让 Suno 生成的人声有**质感和情绪一致性**，而不是平淡的标准发声。一个好的 persona 描述能让生成质量直接跳一档。

### Exclude Styles 字段（负向控制）

Suno Custom Mode 有一个 **Exclude Styles 字段**（与 Style 字段并列），用来告诉 Suno "不要生成什么"。

| 适用场景 | Exclude Styles 写法 |
|---------|-------------------|
| 不要电子元素混入民谣 | `electronic, EDM, synth, autotune` |
| 不要男声 | `male vocal, deep male voice, baritone` |
| 不要快节奏 | `upbeat, fast tempo, dance, EDM, drum-and-bass` |
| 不要美式乡村味 | `country, Americana, banjo, fiddle, southern drawl` |
| 改编场景下不要旧时代音色 | `1960s, vintage analog warmth, lo-fi, tape hiss` |

**使用原则**：与 Style 字段配合，Exclude Styles 是"排除干扰项"的——当你写了 Style 但 Suno 仍混入不想要的元素时，把那些元素写到 Exclude Styles。

### Lyrics 结构 Meta-tag

**人声歌曲必须含**：
- `[Verse 1]` / `[Verse 2]` / `[Pre-Chorus]` / `[Chorus]` / `[Bridge]` / `[Outro]`
- 视需要可加 `[Intro]` / `[Hook]`

**纯配乐必须含**：
- `[Instrumental]` 标记
- 可加节奏提示：`[Build-up]` / `[Drop]` / `[Soft Outro]` / `[Climax]`

**Lyrics 字段技术限制**：
- Suno Custom Mode 的 Lyrics 字段上限 ~3000 字符 / ~40-60 行
- 超过会被截断 —— 长歌曲分两段生成后用 Extend 拼接
- **总是用 Custom Mode**（不要用 Simple Mode）——只有 Custom Mode 才能分离 Style + Lyrics + Exclude Styles 字段，能精准控制

---

## 八、红线（避免做的事）

### 创作层面

- **不为"显得专业"而堆砌音乐**：每段配乐都要有存在的理由。
- **不在所有场景都加配乐**：静默和环境音常常更有力量。
- **歌词三版不能换汤不换药**：必须风格真正不同、轨迹不同的词人不同的创作路径。
- **不在用户选歌词版本前擅自定稿**：用户没选之前你不知道哪个对，三版必须并存。

### 中文词的特殊红线

- **不能堆词**：避免「月光/温柔/心跳/誓言」这类空转词连珠。
- **要讲事不要"拼出心动"**：唐恬风的核心是事件叙事，不是抒情堆叠。
- **不要胡乱跨语种**：中文项目不要为了"洋气"插英文句子，除非创作上明确需要。

### Suno 提示词层面

- **不能抽象**：一句 `sad piano` 是垃圾；要到 `sparse felt-piano, sustained low strings, 58 BPM, breathy female vocal in chest voice, intimate close-mic, late autumn dusk atmosphere` 这个粒度。
- **不要纠结精准时长**：视频以 15 秒为单位生成、用户手工剪辑调整节奏，音乐只需为"剧情/人物/情绪"服务，时长是估计值。
- 🔴 **不要在 Style 描述中使用艺人名 / 乐队名 / 品牌名 / 商标**：Suno 出于法律风险会拒绝或弱化包含这些词的提示词，且涉及合规审核问题。改为描述声音特征：
  | ❌ 用艺人/商标 | ✅ 描述声音 |
  |-------------|-----------|
  | `like Adele` | `a torch singer with powerful contralto, controlled belting in chest voice, late-night confessional delivery, slight vibrato` |
  | `Taylor Swift style` | `intimate Nashville-pop, mid-range female vocal with whispery quality in verses, bright belt in choruses, mid-tempo 110 BPM with acoustic guitar foundation` |
  | `James Bond style` | `1960s Cold War spy thriller orchestral, smoky sultry female vocal, big band brass, sweeping strings, minor key, vintage analog warmth` |
  | `Joe Hisaishi style` | `cinematic Japanese piano-led score, sparse arrangement building to lush orchestral swell, melancholic-hopeful, late-Romantic harmonic language, ostinato patterns` |
  | `周杰伦 style` | `early-2000s Mandopop R&B fusion, mid-tempo 75 BPM, soft male vocal with breathy passages, traditional Chinese pentatonic melody over R&B chord progression, electric piano + sparse guzheng accents` |
  | `Nirvana style` | `early-1990s American grunge, raw distorted electric guitars with verse-chorus dynamics, alternating clean strumming and explosive distortion, gravelly male vocal moving from intimate murmur to anguished belt` |
  这条规则同时也提升 Suno 出片质量——具体描述比"模仿某人"产出稳定得多。改编场景同样适用，详见 `references/parody-adaptation.md` 第 3.1 节。

---

## 九、受众适配性自检（对应 [创作九原则 #9 为流量服务]）

导演审核本 agent 产出（`assets/music/music-design.md` + `music-recommendations.md`）时，除了审克制 / 审 Suno 提示词质量，还要审「受众适配性」（1-10 分）。

**自检清单**（音乐总监输出前先自检，导演审核时再过一遍）：

- ✅ 音乐风格是否符合 `script-settings.md` 中标注的目标平台主流听觉习惯？
  - 抖音 / TikTok → 倾向考虑平台热门音乐风格作为参考（不是抄袭，是节奏类型相似）
  - B 站 → 原创性优先（用户对烂大街 BGM 敏感）
  - 小红书 → 治愈系 / 温柔系受欢迎
  - 视频号 → 中老年受众 + 家庭场景，避免过于先锋
  - 院线 / 影展 → 纯艺术性优先，不考虑平台主流
- ✅ OST 歌词是否会让目标受众"想分享给朋友"？（金句位置、情感共鸣点、记忆度）
- ✅ 市面推荐音乐是否在目标平台已有"流量基础"？（已有被使用记录的曲目流量加成更高）
- ✅ 极简策略选择是否考虑了目标受众的耐心？（抖音受众容易划走 → 不要有 30 秒静默；B 站受众有耐心 → 可以慢热）

**评分标准**：
- 9-10 分：音乐方案完全服务于目标平台 + 目标受众，可预见的流量加成明显
- 7-8 分：方案合理，但有 1-2 点与目标平台习惯有偏差
- 6 分：方案勉强可用，但目标受众容易"略过音乐部分"
- <6 分：方案与目标平台 / 受众完全脱节 → FAIL，需重做

详细方法论见 `_shared/audience-engagement-guide.md`。
