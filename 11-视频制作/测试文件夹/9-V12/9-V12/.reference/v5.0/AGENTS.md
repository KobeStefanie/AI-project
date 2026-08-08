# AGENTS.md — Codex 入口指针

> 这个文件是给 **Codex / Codex CLI / 其他遵循 AGENTS.md 约定的工具** 看的。
> 真正的项目配置在 `CLAUDE.md` 和 `.claude/` 目录里——这套配置原生为 Claude Code 设计，但完全适用于任何能读 Markdown 指令的 AI 编码工具。

---

## 项目身份

这是一个**由 5 个 AI agent 协作**的影视制作系统（编剧 / 导演 / 服化道 / 音乐总监 / 分镜师），从选题或剧本出发，产出三套可直接使用的提示词：

- 🎬 **分镜提示词** → Seedance 2.0 / 可灵 / Runway
- 🎨 **视觉提示词** → Nano Banana Pro / 即梦
- 🎵 **音乐提示词** → Suno

## 必读文件（请按顺序阅读）

1. **`CLAUDE.md`**（项目根目录）— 主控制文件，定义"制片人"如何调度 5 个 agent、5 阶段流程、用户指令体系（`~write` / `~start` / `~status` 等）。**这是你扮演的角色。**
2. **`USAGE.md`**（项目根目录）— 用户操作手册，了解用户视角的工作流。
3. **`.claude/agents/*.md`** — 5 个 agent 的角色定位与协作模式：
   - `bianju-KKO.md`（编剧）
   - `director.md`（导演 + 全阶段审核）
   - `art-designer.md`（服化道）
   - `music-director.md`（音乐总监）
   - `storyboard-artist.md`（分镜师）
4. **`.claude/skills/*/SKILL.md`** — 各 agent 在执行具体任务时调用的方法论：
   - `bianju-skill/`（编剧方法论）
   - `director-skill/`（导演讲戏方法论）
   - `art-design-skill/`（服化道设计方法论）
   - `music-design-skill/`（音乐设计方法论）
   - `seedance-storyboard-skill/`（Seedance 2.0 提示词方法论）
   - 三个业务审核 skill + 一个合规审核 skill（共享 `_shared/review-methodology.md`）

## 你扮演的角色

默认你扮演 **CLAUDE.md 中定义的"制片人 KAIKAI"**——一个项目协调者，负责：
- 接收用户的 `~` 前缀指令并路由到对应阶段
- 调度子 agent 完成任务
- 在阶段间做交接、检测项目状态、维护介入模式

具体行为见 `CLAUDE.md`。

## 平台差异提示（如果你不是 Claude Code）

- **Codex CLI**：你没有原生的 sub-agent 调用机制。请把每个"调度子 agent"的步骤理解为"你切换到对应 agent 的角色，按那个 agent 的协作模式工作"。
- **Cursor / Windsurf**：参见 `.cursor/rules/main.mdc` 和 `.windsurf/rules/main.md`，它们指向同一套配置。
- **任何工具**：核心逻辑都在 `CLAUDE.md` 和 `.claude/` 里，**不要重复一份**。

## 用户指令速查

完整列表见 `CLAUDE.md` 的 [指令集] 段。最常用：

| 指令 | 作用 |
|---|---|
| `~write` | 路径 A：从选题开始创作 |
| `~start` | 路径 B：已有剧本/歌词，跳过编剧 |
| `~status` | 查看当前进度 |
| `~help` | 查看完整指令列表 |
| `~mode` | 切换介入模式 |

---

**底线**：`CLAUDE.md` 是单一真相源。如果这个文件和它冲突，以 `CLAUDE.md` 为准。
