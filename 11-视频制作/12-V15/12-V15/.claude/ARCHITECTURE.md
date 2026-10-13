# 项目文件结构（v14.0）

> 本文件是纯参考，从 CLAUDE.md 外置而来。运行时不需要逐字记住，需要定位某个产物时来查。

```
project/
├── input/                               # 📥 用户原始输入（只放不改）
│   ├── 选题/                            # 触发编剧流程的所有原始素材（.md/.txt/.jpg/.png）
│   │                                    #   — 包括但不限于：选题方向、创意碎片、故事标题、
│   │                                    #     故事梗概、故事大纲草稿、多章节小说节选、IP 概念、情绪参考
│   │                                    #   — 凡能触发编剧起笔的材料一律放此，编剧按内容自行判断深度
│   ├── 剧本/                            # 已有剧本/歌词 → 跳过编剧直接导演（ep01-xxx.md）
│   └── 参考/                            # 通用参考素材（风格图、mood board、music-structure.md 等）
├── script/                              # 📝 编剧工作区（AI 生成 + 版本管理）
│   ├── 00_当前状态.md                   # 编剧进度状态（单一真相源；路径 B 在此标记「跳过编剧」）
│   ├── 00_采访记录.md                   # 创意采访完整记录
│   ├── 01_剧本设定/                     # 设定版本管理
│   ├── 02_故事大纲/                     # 大纲版本管理
│   ├── 03_角色开发/                     # 角色版本管理
│   ├── 04_分集剧本/                     # 分集剧本版本管理（短剧模式）
│   ├── 04_完整剧本/                     # 完整剧本版本管理（短片模式）
│   ├── 99_讨论与诊断/                   # 讨论笔记
│   └── ep01-xxx.md                      # ← 编剧终稿（导演输入）
├── assets/                              # 🎨 设计资产归档（终稿 + 跨集共享）
│   ├── story/                           # 叙事资产
│   │   ├── script-settings.md           # 剧本设定终稿（目标平台/受众/对标/视觉风格/画幅/色彩锚/档位）
│   │   ├── story-outline.md             # 故事大纲终稿
│   │   ├── character-profiles.md        # 角色开发终稿
│   │   ├── creative-brief.md            # 创作基准（情感蓝图 + 导演视野）
│   │   │                                #   路径 A 由编剧产出；路径 B 由导演在阶段二补出
│   │   ├── visual-style.md              # 🎯 风格基准 = 恒定层之源（v14）：通用基准段（媒介质感/色域/
│   │   │                                #   光逻辑/镜头性格）+ 画质固定项 + 时代锚 + 场域锚句表 + 条件项表
│   │   │                                #   编剧起草、导演定稿；分镜师逐字注入每条，一个同义词都不换
│   │   └── decisions.md                 # 🎯 确认记录 + 关键拍板理由（v14）：制片人写，防跨窗口翻案重议
│   ├── visual/                          # 视觉资产（服化道产出，跨集累积，按 ## epXX 分段）
│   │   ├── character-prompts.md         #   ↓ 这四个 .md 存的是**提示词**
│   │   ├── scene-prompts.md
│   │   ├── prop-prompts.md
│   │   ├── changelog.md                 # 跨集状态变化归档（换装/老化/场景变体）
│   │   └── images/                      # 🖼 用户拿提示词生成后，把 PNG 存这里（文件名照 reference-index）
│   │       ├── character-<角色名>.png   #   分镜师的上传清单就指这些文件
│   │       ├── scene-<场景名>.png
│   │       └── prop-<道具名>.png
│   ├── music/                           # 音乐资产（音乐总监产出）
│   │   ├── music-design.md              # 原创音乐方案 + Suno 提示词（少而精）
│   │   ├── lyrics-drafts.md             # OST 歌词草稿（三版 → 用户选后只留终选）
│   │   ├── music-recommendations.md     # 市面音乐推荐清单
│   │   └── mv-visual-timeline.md        # 仅 content_type=mv：逐段时间点/情绪/能量/视觉方向（MV 路径第一棒）
│   ├── reference-index.md               # 素材清单（文件名 + 短串 + 声线锁 + 变体 -vN；运行时由服化道创建）
│   ├── reference-index.template.md      # 上面那份的模板
│   └── continuity-ledger.md             # 🎯 连续性台账（v14）：逐条落幅五字段 / 状态变化 / 场末快照 /
│                                        #   未解线头 [开]·[关闭于] / 跨集 ending state / 变更记录
│                                        #   分镜师每编完一个 P0X 更新；追加式永不回改；「窗口可以关，台账不会忘」
├── outputs/                             # 📦 各集最终产出
│   └── ep01/
│       ├── 01-director-analysis.md      # 导演：讲戏本 + 人物/场景/关键道具清单 + 节奏蓝图 + 镜头承载规划
│       ├── 02-shot-table.md             # 🎯 镜头表（v14，分镜师第一步）：场级空间地图块 + 场阐述 +
│       │                                #   逐镜十项 + 条末结束状态五字段 + 本场资产需求 + 风险上锁提示
│       │                                #   ★表确认后冻结——改镜头回头改这里，不在提示词层硬掰
│       ├── control-prompts.md           # 控制图提示词（仅用户在表确认时点名要才产；一集一份）
│       ├── storyboards/                 # 分镜师（仅故事板模式）：P0X-storyboard-prompt.md
│       ├── video-prompts.md             # 分镜师第二步：逐 Cut（条头三行给人看 + 围栏四块给模型读；顶部一处画幅声明）
│       ├── episode-master.md            # 分镜师：说明书（生成顺序 / 每条传什么 / 试片看什么 / 后期三件 / 术语对照）
│       ├── cuts/                        # 🖼 用户生成的视频片段 Cut<N>.mp4（真帧缝从这里截尾帧）
│       ├── review/                      # 🎯 审核报告落盘（v14）：<级别>-report.md，reviewer 写
│       ├── 00-quality-report.md         # reviewer：整片复盘报告（分镜全 PASS 后）
│       └── feedback-to-upstream.md      # 反向反馈池
├── 📋找文件速查表.md                    # 初始化自动生成（模板见 .claude/templates/file-index.template.md）
├── .agent-state.json                    # Resumable Subagents 的 agentId 记录（便利层；文件才是事实层）
├── .project-config.json                 # 项目配置（介入模式 / 内容类型 / 档位 loadout / 视频模型 / 生图模型 / 双轨锁定）
├── CLAUDE.md                            # 制片人主配置（Claude Code 自动加载）
├── AGENTS.md / .cursor/rules / .windsurf/rules   # 跨工具入口，纯指针指向 CLAUDE.md
├── 故事板/                              # V7 故事板功能的设计参考素材（125MB，运行时不加载）
└── .claude/
    ├── ARCHITECTURE.md                  # 本文件
    ├── templates/
    │   └── file-index.template.md       # 找文件速查表模板
    ├── agents/
    │   ├── bianju-KKO.md                # 编剧
    │   ├── director.md                  # 导演
    │   ├── art-designer.md              # 服化道
    │   ├── music-director.md            # 音乐总监
    │   ├── storyboard-artist.md         # 分镜师（两步：镜头表 → ★表确认 → 编译）
    │   └── reviewer.md                  # 审核专员（查病制五类病 + blocking 白名单）
    └── skills/                          # 17 个：流程 6 + 审核 4 + 工艺卡 5 + 横切 2
        ├── _shared/                     # 跨 skill 共享方法论
        │   ├── user-messages.md         # 对用户话术的单一真相源
        │   ├── review-methodology.md    # 4 个审核 skill 共享的查病流程
        │   ├── creative-brief-guide.md  # 创作基准三合一格式 + 色彩锚三级承接
        │   ├── visual-style-guide.md    # 🎯 风格基准四件的写法规范（v14，恒定层之源）
        │   ├── pacing-methodology.md    # 疏/中/紧三档节奏 + 气口
        │   ├── ai-generation-constraints.md  # AI 生图生视频技术硬边界
        │   ├── audience-engagement-guide.md  # 受众参与度 / 平台规律 / 对标爆款
        │   ├── episode-tagging.md       # 分集标签路由规范
        │   ├── gemini-audio-analysis-guide.md  # MV 模式音频分析
        │   └── path-b-setup.md          # 路径 B 启动补设定流程（五问 + creative-brief 补位）
        ├── bianju-skill/
        ├── director-skill/
        ├── art-design-skill/
        │   └── references/
        │       ├── director-color-cards.md      # 175 位导演六色 HEX + 光线/摄影/调色（色彩锚，按需加载）
        │       ├── director-index.md            # 导演浏览索引（按 10 大风格分类）
        │       ├── director-camera-language.md  # 88 位导演运镜语言（参考不是约束）
        │       └── failure-fix-table.md
        ├── music-design-skill/
        ├── shot-design/                 # 🎯 v14：镜头表方法论（逐镜十项 + 场级空间地图块 + master shot）
        ├── seedance-storyboard-skill/   # 编译站：条头三行 + 围栏四块 + 五维接线 + 可判定自检
        ├── camera/                      # 🎯 工艺卡：六槽运镜句式 + 视场角锚点 + 运镜词典
        ├── blocking/                    # 🎯 工艺卡：站位七要素 + 180° 轴线 + 首帧占位锁 + 空间地图块
        ├── performance/                 # 🎯 工艺卡：五支柱任务制表演 + 表演档案 + 眼活强制项
        ├── lighting/                    # 🎯 工艺卡：光向五要素 + 世界内光源五槽 + 物理锁
        ├── sound-writing/               # 🎯 工艺卡：声音四要素句式 + 口型纪律 + 密度三档（BGM 按项目红线）
        ├── continuity/                  # 🎯 横切：12 项状态机 + ledger 六块 + 缝审计八查
        ├── retake/                      # 🎯 横切：生成后返工五出口 + 诊断树（~retake）
        ├── script-analysis-review-skill/
        ├── art-direction-review-skill/
        ├── seedance-prompt-review-skill/
        └── compliance-review-skill/
```

## 资产归档规则（哪个 agent 写哪里）

本项目是「agent 直接产出到目标位置 + reviewer 审核 PASS 才算归档」，不做 outputs→assets 的二次同步。

| 位置 | 归属 agent | 备注 |
|---|---|---|
| `assets/story/visual-style.md` | 编剧起草 → 导演定稿 | 恒定层之源；首集定稿后冻结，改它走 `~settings` 并提醒下游重跑 |
| `assets/story/decisions.md` | 制片人 | 每个 ★确认后当轮追加一行（日期｜对象｜结论｜拍板理由）；路由判「确认完成」看这张表 |
| `outputs/<集>/01-director-analysis.md` | 导演 | 路径 B 首集另产 `assets/story/creative-brief.md` |
| `assets/visual/{character,scene,prop}-prompts.md` | 服化道 | 追加 `## ep<N>` 段；本集无新增也写空标记块（路由信号） |
| `assets/visual/changelog.md` + `assets/reference-index.md` | 服化道 | 写变体时同步一行（含 -vN、短串、声线锁） |
| `assets/music/*.md` | 音乐总监 | 追加 `# ===== ep<N> =====` 段；复用也写标记 |
| `outputs/<集>/02-shot-table.md` | 分镜师（第一步） | **★表确认后冻结**——下游只读；改镜头回这里改，不在编译层硬掰 |
| `outputs/<集>/control-prompts.md` | 分镜师 | 仅用户在表确认时点名要控制图才产（手动模式，同故事板） |
| `outputs/<集>/storyboards/`、`video-prompts.md`、`episode-master.md` | 分镜师（第二步） | video-prompts.md + episode-master.md 同时存在 = 该集完成 |
| `assets/continuity-ledger.md` | 分镜师 | 每编完一个 P0X 即更新；**追加式，永不回改**（登记错走变更记录追加更正行） |
| `outputs/<集>/review/<级别>-report.md` | reviewer | 每个审核点一份；结论 PASS 才交用户确认 |
| `outputs/<集>/00-quality-report.md` | reviewer | 分镜全 PASS 后 |
| `outputs/<集>/feedback-to-upstream.md` | 任何 agent / 用户 | 反向反馈协议 |

FAIL 时 agent 修改后**覆盖原位置**，不建 v2 文件。

## 关于 PNG / MP4（用户生成的产物）

配置只产出**提示词**，图和视频由用户拿提示词去工具生成。约定的存放位置：

| 用户生成的东西 | 存到哪 | 谁引用它 |
|---|---|---|
| 角色 / 场景 / 道具参考图 | `assets/visual/images/`，文件名照 `reference-index.md`（如 `character-林晓.png`） | 分镜师的上传清单 |
| 故事板大图（仅故事板模式） | `outputs/<集>/storyboards/P0X-storyboard.png` | 该 P0X 的 Cut 上传清单 |
| 生成好的视频片段 | `outputs/<集>/cuts/Cut<N>.mp4` | 后期剪辑按编号串接；V2V 的下一镜要上传它 |
| 控制图（站位图/关键帧/白盒，仅点名时） | `outputs/<集>/images/ctrl-*.png`，文件名照 `control-prompts.md` | 对应 Cut 的上传清单 |
| **真帧缝的尾帧**（v14） | 从上一条成片截最后一帧，存 `outputs/<集>/cuts/Cut<N>-endframe.png` | 下一条按条头「承接」行指引上传（条头会写明「上传上一条成片尾帧作 @图片N」） |

**文件名一旦写入 `reference-index.md` 就不要再改**——分镜师的上传清单按名字引用。
reviewer 校验上传清单时，只核对「名字与 reference-index 一致」，**不要求文件已经生成**（分镜阶段用户通常还没出图）。
