# 凯凯 · AI 影视制作团队 v14.0

> 一个由 6 个 AI agent 协作的影视制作系统：编剧 / 导演 / 服化道 / 音乐总监 / 分镜师 + 审核专员。
> 从一个想法或一份剧本出发，产出三套**可直接复制粘贴**的提示词：
>
> - 🎬 **视频提示词** → Seedance / 可灵 / Runway / Veo（任何支持参考图的视频模型）
> - 🎨 **参考图提示词** → Nano Banana / 即梦 / Midjourney（角色 / 场景 / 道具各一张）
> - 🎵 **音乐提示词** → Suno（音乐后期铺，不进视频）

---

## 这套系统怎么工作

```
你: 一个灵感 / 一份剧本 + 目标平台 + 受众画像（+ 可选：想要哪位导演的调子）
       ↓
[系统]: 编剧 → 导演 → 服化道 → 音乐 → 分镜，每阶段产出经审核专员两步审核（业务 + 合规）
       ↓
分镜分两步: 先出「镜头表」给你逐镜号确认 ★ → 确认后才翻译成提示词
       ↓
你拿到: 参考图提示词 + 每个镜头的视频提示词 + 音乐方案 + 剪辑顺序说明
       ↓
你去对应 AI 工具生成 → 按说明剪辑 → 后期铺音乐 → 成片
       ↓
哪条不对: ~retake 报修（改词 / 局部编辑 / 换镜头 / 改输入 / 回上游）
```

第一次用，输入 **`~onboard`**，我会一条龙带你走完「放什么 → 我问什么 → 你拿到什么 → 去哪生成 → 翻车怎么办」。

## v14 的六个变化

1. **分镜改两步制**：`~prompt` 不再直接吐提示词。先出一张 `02-shot-table.md` **镜头表**（每镜的运镜/站位/表演/光/声 + 条末「结束状态五字段」），你指着镜号说「第 3 镜太碎，并进第 2 镜」，改完确认 ★ 才编译成提示词。**改表是几行字，改提示词是整条重来。**
2. **提示词形态换成「条头三行 + 围栏四块」**：条头给人看（`上传` / `承接` / `交出`），围栏给模型读（引用声明 → 总述段 → 分段剧情 → 收尾约束）。**围栏第一个字就是模型读的第一个字**——传完图整段复制即生成，不用再挑哪句该删。V13 那种把「📤 上传清单」混在正文里的坑没了。
3. **五张工艺卡**：`camera` / `blocking` / `performance` / `lighting` / `sound-writing`。有人物出镜的镜头五维都得指得到落点。「她很难过」要写成「泪膜在下睑缘反光却悬而不落」——模型只认可观测的物理事实。
4. **连续性台账**：`assets/continuity-ledger.md` 记剧情状态（谁现在什么状态 / 走到哪 / 哪根线还没收），`changelog.md` 继续记资产变体。**窗口可以关，台账不会忘**——跨集穿帮多数死在「上一集忘了自己留过什么」。
5. **生成后翻车有正式通道**：`~retake` 收案三问 → 五个出口。判据很直接：「同一条抽满 15–20 次还不过，问题在镜头不在词」。
6. **审核从评分制改查病制**：不再算「均分 ≥8 放行」，改成找五类病（矛盾 / 断链 / 走样 / 模型雷 / 红线），**只有白名单里的硬伤挡线**，其余修而不挡；一轮为限，连两轮不过就摆给你裁决，不无限自转。

V13 的成果一项没丢：175 位导演色卡（`~color`）、时长由 `~video-model` 驱动、音乐只归音乐总监、参考图默认单张、故事板手动开启。

## 这套配置的立场

> AI 让执行成本趋近于零，省下来的时间应该花在哪？只有一个答案：**构思你的分镜和故事。**
> 绝大多数提示词技巧终将被模型进步吞噬，但故事不会。
> 所以这一版的规则一直在减不在加——技术边界和可判定检查留下，写法偏好和微观配方全部删掉。

详见 `CLAUDE.md` 的 `[效率去哪儿]`。

## 从哪里开始

| 你用的工具 | 你需要做的 |
|------------|-----------|
| **Claude Code** | 直接打开本项目目录，所有配置自动加载 |
| **Codex / Codex CLI** | 自动读 `AGENTS.md`，它指向 `CLAUDE.md` |
| **Cursor / Windsurf** | 自动读 `.cursor/rules/main.mdc` / `.windsurf/rules/main.md`，同样指向 `CLAUDE.md` |

然后看 **[`USAGE.md`](./USAGE.md)**（用户手册）。所有真实配置在 `CLAUDE.md` 和 `.claude/`，其他入口只是指针。

## 项目结构

```
凯凯项目/
├── README.md / USAGE.md / AGENTS.md   ← 给人和跨工具看的
├── CLAUDE.md                          ← 制片人主控（细节全部外置）
├── input/{选题,剧本,参考}/             ← 你放素材的地方
├── script/                            ← 编剧产出
├── assets/                            ← story / visual / music + continuity-ledger.md（连续性台账）
├── outputs/epNN/                      ← 01-director-analysis / 02-shot-table（镜头表）/ video-prompts / episode-master / review/
├── 故事板/                            ← V7 故事板功能的设计参考素材（125MB，运行时不加载）
└── .claude/
    ├── ARCHITECTURE.md                ← 完整目录树 + 哪个 agent 写哪里
    ├── agents/                        ← 6 个 agent
    ├── skills/shot-design/            ← 镜头表（分镜第一步）
    ├── skills/{camera,blocking,performance,lighting,sound-writing}/  ← 五张工艺卡
    ├── skills/{continuity,retake}/    ← 连续性台账 / 返工站
    ├── skills/_shared/                ← 跨 agent 方法论、话术、路径 B 流程
    └── skills/art-design-skill/references/director-*.md   ← 175 位导演色卡 / 索引 / 运镜
```

## 给开发者

- **6 个 agent**：bianju / director / art-designer / music-director / storyboard-artist / **reviewer**（审核独立，每次空白上下文）
- **五阶段 + 三路径**：叙事类五阶段；MV 音乐先行；VJ 无编剧
- **分镜两步制**：`shot-design` 落镜头表 → ★表确认 → `seedance-storyboard-skill` 编译提示词。**两处镜头数打架时以 `02-shot-table.md` 为准**
- **审核查病制**：五类病 + blocking 白名单挡线 + 一轮为限 + 连续两轮 FAIL 熔断
- **文件是记忆，Session 不是**：判据是「这个窗口现在被关掉，这条信息会丢吗」——会丢就当轮落盘
- **分层加载**：CLAUDE.md 只保留调度逻辑；方法论在 skill；模板、示例、参考按需读
- **单一真相源**：主控 `CLAUDE.md`；话术 `_shared/user-messages.md`；恒定层 `assets/story/visual-style.md`；目录树 `ARCHITECTURE.md`；同一规则全项目只定义一处
- **时长、画幅、宫格全部 config 驱动**：`.project-config.json` 的 `video_model_config` / `image_model_config` / `storyboard_overrides` / `loadout`（全装 / 轻装），不在任何文件里写死

变更历史见 [`CHANGELOG.md`](./CHANGELOG.md)，V13→V14 改了什么见 [`UPGRADE-LOG.md`](./UPGRADE-LOG.md)，V14 特性速查见 [`V14-FEATURE-SUMMARY.md`](./V14-FEATURE-SUMMARY.md)。
