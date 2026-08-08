---
name: storyboard-style-decision-tree
description: 万能故事板「自身风格」的 AI 决策树。基于 5 个维度（用户偏好 → 跨集沿用 → 题材 → 复杂度 → settings.visual_style）从 5 候选风格中选最合适的。供分镜师在「故事板模式」下使用。
---

# 万能故事板风格决策树

> 注意：本决策树决定的是「故事板**自身**的画面风格」（即 Nano Banana 生成的故事板大图长什么样），不是最终视频的风格。最终视频风格依然遵循 `settings.visual_style`。

## 一、5 维度联合决策（按优先级）

```
维度 1（最高优先级）：用户显式覆盖
   ├─ 读 .project-config.json.storyboard_style，存在且在 5 候选内 → 直接采用
   ├─ 用户已用 ~storyboard-style <名> 指令 → 写入 storyboard_style 后采用
   └─ 否则 → 进入维度 1.5

维度 1.5（v7.0.1 新增 / v7.0.2 优化）：跨集风格沿用（仅 ep02+ 续集触发）
   ├─ 本集 ≥ ep02 且上一集 outputs/<前集>/episode-master.md 存在
       → **只读其 §9.3 to_next_episode.storyboard_style 字段**（不读全文，v7.0.2 跨集累积防御）
   ├─ 字段存在且在 5 候选内 → 直接采用（保持项目风格一致）
   ├─ 字段缺失 → 反向反馈让上一集补全 §9.3，**不要猜测**
   └─ 本集是 ep01 → 进入维度 2

维度 2：题材判断（从剧本/导演讲戏本提取）
   ├─ 喜剧 / 情景喜剧 + 群戏 + 高夸张表情 → black_white_manga_lineart
   ├─ 仙侠 / 古装 / 奇幻 / 战争史诗 → epic_realism
   ├─ 动画 / settings.visual_style 含 "3d" 或 "动画" → disney_3d_animation
   ├─ 广告 / 电商 / 产品 / 品牌 → commercial_clean
   └─ 其他 → 进入维度 3

维度 3：场景复杂度
   ├─ 超高（≥ 3 主要角色 + 多机位 + 多场景） → cinematic_realism
   └─ 否则 → 进入维度 4

维度 4：fallback 映射到最近 5 候选
   └─ 按 §四 规则把 settings.visual_style 映射到最近的 5 候选风格之一
     （主风格名仍在 5 候选内；项目 visual_style 的特征关键词在提示词描述层叠加）
```

**关键设计**：维度 1（用户显式锁定）优先于维度 1.5（跨集沿用）——用户在 ep02 用 `~storyboard-style` 可以**主动切换**故事板风格（即使会与 ep01 不一致）。但 AI 不能自决切换跨集风格，必须沿用。

**AI 必须主动告知用户**：分镜师阶段开场输出：

```
【故事板风格判定】
本片故事板风格 = <风格名>
判定理由：维度 X 命中——<具体理由>

如需覆盖请用：~storyboard-style <名>
可选风格：cinematic_realism / disney_3d_animation / epic_realism / commercial_clean / black_white_manga_lineart
```

---

## 二、5 候选风格规格

### 风格 1：`cinematic_realism`（写实电影感）

**适用题材**：都市情感 / 现实剧情 / 短片 / 真人题材主流

**画面特征**：
- 写实摄影质感，浅景深
- 真实光影：晨光 / 黄昏 / 雨夜 / 路灯
- 电影色调：冷暖对比、增强情绪
- 35mm-85mm 焦距为主
- 真人形象（卡通化避免）
- 自然环境细节丰富

**故事板大图风格描述（提示词中写）**：
```
整体写实电影感分镜板，深色背景配合精细排版。
角色三视图采用真人摄影风格，皮肤质感真实，发型清晰。
场景透视图含真实光影和环境细节。
分镜网格中每镜采用电影色调（冷暖对比），16:9 横版。
专业故事板排版，类似工业级影视分镜。
```

**典型项目**：
- 都市情感剧情短片（"错过之后"系列）
- 现实题材纪录片
- 院线短片
- 商业广告中的剧情向故事

### 风格 2：`disney_3d_animation`（迪士尼 3D 动画感）

**适用题材**：动画短片 / 儿童向 / 治愈系 / 想象力题材

**画面特征**：
- 3D CG 渲染质感（皮克斯 / 迪士尼）
- 色彩饱和、温暖梦幻
- 角色头身比 1:5 - 1:6，大眼睛、可爱化
- 柔和环境光，星光粒子、魔法效果
- 反重力 / 想象力场景常见

**故事板大图风格描述**：
```
整体迪士尼 3D 动画风格分镜板，柔和暖色背景。
角色三视图采用皮克斯 / 迪士尼 3D 渲染风格，圆润可爱，大眼睛。
场景透视图含魔法效果（如发光、星光、粒子）。
分镜网格中每镜采用动画风格的明亮饱和色，16:9 横版。
温暖梦幻、富有想象力，类似工业级动画分镜。
```

**典型项目**：
- 「会发光的画笔」儿童短片
- 治愈系动画
- 节日主题动画
- 教育类动画

### 风格 3：`epic_realism`（史诗写实）

**适用题材**：仙侠 / 古装 / 奇幻 / 战争史诗 / 武侠 / 玄幻

**画面特征**：
- 写实质感 + 奇幻元素融合
- 戏剧光影：能量光效、月光、火光、神圣光柱
- 史诗色调：金红 / 暗银 / 血红 / 雷紫
- 角色衣着精致：盔甲、长袍、披风、法器
- 大场面：山谷、祭坛、战场、神殿

**故事板大图风格描述**：
```
整体史诗写实分镜板，深沉戏剧背景。
角色三视图采用写实质感，含奇幻元素（如灵气、剑芒、法术光效）。
场景透视图含史诗大场面（祭坛 / 战场 / 山谷 / 神殿）。
分镜网格中每镜采用戏剧光影（金红 / 暗银 / 雷紫），16:9 横版。
史诗大气，类似工业级电影级分镜。
```

**典型项目**：
- 仙侠短片（断剑 / 法杖 / 灵兽题材）
- 战争奇幻（魔法师 + 战车 + 法阵）
- 古装情节短片
- 玄幻短剧

### 风格 4：`commercial_clean`（商业干净风）

**适用题材**：电商 / 品牌广告 / 产品宣传 / 概念美术

**画面特征**：
- 干净背景（多为白底 / 浅灰底）
- 产品摆放精致、光影柔和
- 色彩克制，有十六进制色板锚定
- 现代家居 / 极简办公场景
- 强调产品与用户场景的关系

**故事板大图风格描述**：
```
整体商业干净风格分镜板，浅色背景配合极简排版。
产品资产图采用精致渲染（产品摄影质感）。
场景透视图含现代家居 / 极简办公环境，光影柔和。
分镜网格中每镜采用商业广告色调（暖白 / 浅灰 / 木色），16:9 横版。
专业商业品牌分镜，类似电商详情页和广告概念板。
色板严格锚定项目十六进制色值。
```

**典型项目**：
- 扫地机 / 洗碗机 / 电饭煲电商短片
- 品牌概念广告
- 产品发布会概念美术
- B2B 服务介绍

### 风格 5：`black_white_manga_lineart`（黑白线稿漫画风）

**适用题材**：喜剧 / 搞笑 / 群戏 / 夸张表情 / 段子向

**画面特征**：
- 黑白线稿（无颜色或少量斑点色）
- 表情夸张，类似日漫 / 美漫
- 动作线条强调（漫画速度线）
- 角色头身比 1:4，更卡通化
- 简洁背景突出动作和表情

**故事板大图风格描述**：
```
整体黑白线稿漫画风分镜板，白色背景。
角色三视图采用日漫 / 美漫线稿风格，表情夸张。
表情包采用 emoji 化的高夸张度（开心 / 愤怒 / 惊讶 / 哭喊）。
场景透视图采用简洁线稿（无颜色，仅黑白）。
分镜网格中每镜采用漫画连环画风格，含动作速度线，16:9 横版。
喜剧搞笑节奏感强，类似四格漫画的工业级分镜。
```

**典型项目**：
- 「猫主子打翻杯子」家庭喜剧
- 老板与员工搞笑短剧
- 段子向情景剧
- 反转喜剧

---

## 三、AI 自决伪代码

```python
def decide_storyboard_style(
    user_override: str | None,    # 用户 ~storyboard-style 指令（或 .project-config.json.storyboard_style）
    previous_episode_style: str | None,  # 上一集 episode-master.md 的「故事板风格」字段（v7.0.1 新增）
    current_episode: str,          # 本集集数（"ep01" / "ep02" / ...）
    script_genre: str,             # 编剧/导演讲戏本的题材判断
    scene_complexity: str,         # 场景复杂度: low / medium / high / ultra_high
    settings_visual_style: str,    # 项目 settings.visual_style
) -> str:
    CANDIDATES = ["cinematic_realism", "disney_3d_animation", "epic_realism",
                  "commercial_clean", "black_white_manga_lineart"]
    
    # 维度 1：用户显式覆盖（最高优先级）
    if user_override and user_override in CANDIDATES:
        return user_override
    
    # 维度 1.5：跨集风格沿用（v7.0.1 新增；ep02+ 才触发）
    if current_episode != "ep01" and previous_episode_style and previous_episode_style in CANDIDATES:
        return previous_episode_style
    
    # 维度 2：题材判断
    if "喜剧" in script_genre or "情景喜剧" in script_genre or "搞笑" in script_genre:
        if "群戏" in script_genre or scene_complexity == "high":
            return "black_white_manga_lineart"
    
    if any(k in script_genre for k in ["仙侠", "古装", "奇幻", "战争史诗", "武侠", "玄幻"]):
        return "epic_realism"
    
    if "动画" in script_genre or "3d" in settings_visual_style.lower() or "动画" in settings_visual_style:
        return "disney_3d_animation"
    
    if any(k in script_genre for k in ["广告", "电商", "产品", "品牌"]):
        return "commercial_clean"
    
    # 维度 3：场景复杂度
    if scene_complexity == "ultra_high":
        return "cinematic_realism"
    
    # 维度 4：fallback 映射到最近 5 候选（§四规则）
    # 主风格名必须在 5 候选内（审核 skill 硬约束），visual_style 的特征关键词在提示词描述层叠加
    style_lower = settings_visual_style.lower()
    if any(k in style_lower for k in ["水墨", "国画", "工笔", "史诗", "奇幻"]):
        return "epic_realism"
    if any(k in style_lower for k in ["赛博", "cyberpunk", "霓虹", "未来", "科幻"]):
        return "cinematic_realism"
    if any(k in style_lower for k in ["卡通", "动漫", "二次元", "治愈"]):
        return "disney_3d_animation"
    if any(k in style_lower for k in ["极简", "高级灰", "性冷淡", "莫兰迪"]):
        return "commercial_clean"
    if any(k in style_lower for k in ["喜剧", "漫画", "线稿"]):
        return "black_white_manga_lineart"
    # 真正无法识别 → 默认 cinematic_realism（最通用）
    return "cinematic_realism"
```

---

## 四、风格不在 5 候选内的处理

如果项目 settings.visual_style 是「水墨」「赛博朋克」「蒸汽朋克」等不在 5 候选风格内的，AI 应：

1. 主风格名（用于 episode-master.md「故事板风格」字段 + 审核 skill 的「5 候选之一」硬约束）：从 5 候选中选最接近的——
   - 水墨 / 国画 / 工笔 → `epic_realism`
   - 赛博朋克 / 霓虹 / 科幻 → `cinematic_realism`
   - 卡通 / 动漫 / 治愈 → `disney_3d_animation`
   - 极简 / 高级灰 / 莫兰迪 → `commercial_clean`
   - 漫画 / 线稿 → `black_white_manga_lineart`
2. 在故事板大图**风格描述层**（不是风格名）叠加项目 visual_style 的特征关键词，让 Nano Banana 生图时呈现混搭质感
3. 主动告知用户：「本片故事板主风格 = `cinematic_realism`（叠加 cyberpunk 霓虹特征），5 候选风格中无完美匹配项；如不满意请用 `~storyboard-style` 指令显式指定」

**为什么主风格名必须在 5 候选**：审核 skill `seedance-prompt-review-skill` 第 95 行硬约束「故事板风格在 5 候选之一」一票否决。脱离 5 候选会直接 FAIL。叠加特征关键词放在「整体风格段」的描述里，不影响主风格名。

---

## 五、跨集风格统一

同一个项目的所有集数，故事板风格**必须统一**（避免 P01 用 cinematic_realism、P02 用 disney_3d 这种割裂感）。

实现方式：
- 第 1 集判定结果记录到 `outputs/<集 1>/episode-master.md` 的「故事板风格」字段
- 后续集数分镜师启动时，**先读上一集 episode-master.md** 沿用相同风格
- 仅当用户主动用 `~storyboard-style <名>` 显式切换时才换风格

---

## 六、自检 checklist

- [ ] 已检查用户是否用 `~storyboard-style` 显式覆盖
- [ ] 已从剧本/导演讲戏本提取 script_genre
- [ ] 已评估 scene_complexity（low / medium / high / ultra_high）
- [ ] 已读 settings.visual_style
- [ ] 已按 5 维度决策树跑出风格名（含 v7.0.1 新增维度 1.5 跨集风格沿用）
- [ ] 已主动向用户输出「【故事板风格判定】」段
- [ ] 主风格名严格在 5 候选之内（不要出现 `adopt_project_style:xxx` 这种非标值）
- [ ] 跨集时已读上一集 episode-master.md 沿用风格
