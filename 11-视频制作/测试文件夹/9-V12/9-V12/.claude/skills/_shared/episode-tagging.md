# 分集标签机制（路由标记规范）

> 供服化道和音乐总监使用。本文件定义项目在 `assets/visual/` 和 `assets/music/` 下的"分集分块"写入规范，确保制片人的项目状态检测能正确路由。

## 核心规则

每个 agent 在完成本集产出后，**必须在对应资产文件的末尾追加一个本集标记块**：
- 服化道 → `assets/visual/character-prompts.md` / `scene-prompts.md` / `prop-prompts.md`
- 音乐总监 → `assets/music/music-design.md` / `music-recommendations.md`

**即使本集全部复用前集素材（无新增内容），也必须写入标记块**——否则制片人检测不到标签，会认为该阶段未完成而卡住路由。

## 标签格式

### 服化道（视觉资产）
```markdown
## ep01
[本集人物/场景/道具提示词内容]
```

全复用示例：
```markdown
## ep01（本集全部复用 ep00，无新增）
```

无关键道具示例：
```markdown
## ep01（本集无关键道具）
```

### 音乐总监（音乐资产）
```markdown
# ===== ep01 =====
[本集音乐方案内容]
```

全复用示例：
```markdown
# ===== ep01 =====（本集复用 ep00 主题曲，无新增）
```

跳过音乐示例：
```markdown
# ===== ep01 =====
（本集跳过音乐设计）
```

## 路由原理

制片人启动时扫描各资产文件的标签：
- 没有对应集的标签 = 该集该阶段未完成 → 路由到该阶段
- 有标签 = 已完成 → 跳过进入下一阶段

## 谁需要遵守

- `art-designer` — 服化道 agent
- `music-director` — 音乐总监 agent
- `art-design-skill` — 服化道 skill
- `music-design-skill` — 音乐设计 skill
