---
name: art-direction-review-skill
description: 服化道审核技能（v14 查病制），用于资产审——审核人物/场景/道具设定提示词。当服化道完成本集设计、提交给下游分镜师前，reviewer 用此 skill 查五类病：与导演清单是否对得上、图像规则集是否纯正向、基准段是否嵌入、锚定资产纪律、声线锁登记、grid_mode 合规、跨集一致。不评分、不设分数门槛；只有 blocking 白名单挡线，major/minor 修而不挡。通用哲学/判定/报告格式引用 _shared/review-methodology.md。
---

> 📌 **源库站名映射**（本卡及其 references / templates / examples 沿用了 Seedance 分镜师 3.0 的旧站名，**均不是真实存在的 skill 名，别去调它们**）：`motion-compile` = `seedance-storyboard-skill` · `script-breakdown` = 导演拆解（`outputs/epNN/01-director-analysis.md`）· `character-design` / `scene-design` / `prop-design` = `art-design-skill` · `control-image` = 控制图（V14 无独立站，分镜师兼做）· `director-grill` = `director-skill`

# 服化道设计审核技能（v14 · 查病制）

[技能说明]
    审核服化道在资产审阶段的产出。目标不是"格式完整就过"，而是"想象生成出来的图能不能用、下游分镜师能不能靠它绑参考"。查病立场、五类病、blocking 白名单、判定与轮次、防误杀、报告格式、回流路由全部见 `_shared/review-methodology.md`，本文只列**资产审查什么**。

[审核对象]
    `assets/visual/character-prompts.md` / `scene-prompts.md` / `prop-prompts.md` 中本集新增内容（扫 `## ep<集数>` 块）+ `assets/reference-index.md` 本集登记增量。
    本集为"全部复用"标记、无新增项 → 直接 PASS。

[只读基准]（永不入审）
    - 导演分析 `outputs/<集>/01-director-analysis.md` 的人物 / 场景 / 关键道具三清单（核心参照）
    - `assets/story/visual-style.md`（缺则 `creative-brief.md` 基准段）——通用基准段四件 + 场域锚句表 + 条件项表
    - `assets/story/decisions.md`（色彩锚拍板）
    - `.project-config.json.image_model_config`（grid_mode）
    - 已有素材（续集时，对账复用/变体）

[脑内预演视角]（前三类病干净后才跑）
    - 人物：想象丢进即梦 / Nano Banana / Gemini，生成的角色是否与导演心中一致、能否一眼与其他角色区分。
    - 场景：想象生成的场景图（single 时每场一张），氛围是否与讲戏本该场景匹配、各场风格是否统一。
    - AI 常见误读（模型雷）："清秀"被理解成女性化外貌；牌匾文字常出错；紧身/暴露描述可能触发生图工具误杀。

---

## 资产审查什么（按五类病归位）

### 图像规则集：纯正向（模型雷，本级重点）
    图像提示词与视频提示词是**两套规则集，禁止串用**——"The rules of one job poison the other."
    - **无负面参数 / 无负向词堆叠 / 无权重语法**：图像提示词里出现 `--no xxx`、成串的「不要…不要…」、`(词:1.4)` 这类权重标记 → 模型雷，命中 major（改向：删负向，把「不要暗」改成正向「高调明亮」）。
    - 纯正向、紧凑散文——把想要的写出来，不靠排除不想要的。
    - 例外：编辑类修图提示词（retake image-surgery）有自己的规则，不在本级。

### 与导演清单一致（走样 / 断链）
    - 逐个对照导演三清单的外观关键词：提示词是否完整覆盖？遗漏/偏离具体列出（走样）。
    - 清单里的角色/场景/道具是否都产出了对应提示词？漏做 = 断链。
    - 核心级新资产在清单里没有 = 拆解遗漏，记「上游观察」回导演补清单，不在本级硬补。

### 基准段嵌入（走样）
    每条提示词开头是否**逐字嵌入** `visual-style.md` 的通用基准段（缺则 creative-brief 基准段）；含色彩锚时六色 HEX 是否照抄未改。未嵌或改写 → 走样 major（换措辞就扩大采样范围导致漂移）。

### 锚定资产纪律（矛盾，可致 blocking）
    场景/道具提示词里出现**已有独立设定图**的角色/道具时，**绝不重新描述其外观**——三种合规处理：留空槽 / 方向描述 / 场景即资产。违反（同一资产在场景图与角色图各画一个、长相打架）= **同一资产双真相源 = blocking**（i2v 出片必串脸）。判据见 `art-design-skill` 的锚定资产纪律段。

### 声线锁登记（断链）
    有台词的角色，在 `reference-index.md` 必须登记**声线锁**（一段条件块：年龄+地域/口音标记；音区与音色；语速与吐字习惯；情绪底色及压力下变化）。有台词却查无声线锁 → 断链 major（下游 sound-writing 无法逐字引用，声音必漂）。口音须写成「类别 + 一两个具体发音特征」，只贴一个地名 = 走样。

### 出图版式（走样）
    - 人物：**两种版式都合法，一集内统一**——① 三面板法（角色表：正/侧/背 + 面部特写 + 表情包 + 五维度文字）或 ② 我们的「左半面部特写 + 右半三视图 + 白底」。混用或版式不全 → major。
    - 道具：四视图法（正/侧/顶或底 + 特写 + 比例参考），白底。
    - 缺白底/缺多角度 → major（下游绑参考图会缺面）。

### grid_mode 合规（走样，single 可致一票否决）
    读 `image_model_config.grid_mode`：
    - `single`（默认）：每场景/每道具一张独立图。场景或道具提示词里出现「宫格 / 九宫格 / 3x3 / 多格 / 格N」字样 → **FAIL**（用户会拿到默认宫格图，与单张工作流冲突）。
    - `NxM`：一张宫格图，格数 = N×M；加查格数与 grid_mode 一致、空格处理、整张能一次生成。

### reference-index 登记（断链）
    本集每个角色/场景/道具是否在 reference-index 登记了：项目编号（char-/scene-/prop-NNN，变体 -vN）、文件名、短串、（角色）声线锁指针。登记与产出包不双向对齐 = 断链。

### 跨集一致（续集时；矛盾 / 走样）
    - 复用素材是否标注"已有"、不重复设计？
    - 变体是否标注与原版关联和差异、编号 -vN？
    - 新设计风格是否与已有素材协调、跨集编号是否延续（不跳号）？
    冲突 → 记 major，编号跳号/变体查无 → 断链。

### 受众适配（走样类的一个角度，命中才记）
    对照 `script-settings.md` 目标平台 + 受众画像：人物是否有让目标受众一眼记住的独有视觉标识？场景视觉密度/美感是否符合目标平台习惯（抖音强反差 vs 小红书精致 vs B站知识感）？有对标爆款时附查视觉气质是否同频（评气质非形似，外形/服装/道具与对标过分一致 → 点抄袭风险）。明显脱节 → 走样 major。判据见 review-methodology 第九节。

---

## 输出（报告格式见 review-methodology 第七节，落 `outputs/<集>/review/assets-report.md`）
    不产评分表、不写分数。只列发现（七字段），按 blocking → major → minor 排，尾附「上游观察」。有 blocking = FAIL 靶向重审一轮；无 blocking = PASS，major/minor 修完随产物交确认时报「审核发现 N 条、已修」。连续两轮 FAIL 或判据分歧 → 熔断交用户。
