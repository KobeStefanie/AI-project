# Codex 启动钩子配置说明

## 功能概述

本项目配置了启动钩子（startup hook），让 Claude Code（Codex）在每次会话启动时自动：

1. **读取三大件文件**
   - `PROJECT_STATUS.md` - 项目状态、进度、待办事项
   - `WORKFLOW.md` - 当前工作流版本、标准流程
   - `CLAUDE.md` - 项目原则、验证流程

2. **自动汇报项目状态**
   - 当前进度和阶段
   - 主线任务和阻塞问题
   - 关键指标（KPI）
   - P0/P1 优先级待办事项

3. **无需手动询问**
   - 不会再出现"我们做到哪了"的重复提问
   - Codex 启动即了解项目全貌
   - 直接进入工作状态

## 文件结构

```
.claude/
├── settings.json          # 项目级配置，定义启动钩子
└── hooks/
    ├── startup.js         # 启动钩子脚本（Node.js）
    └── README.md          # 本说明文档
```

## 配置文件

### `.claude/settings.json`

```json
{
  "hooks": {
    "startup": {
      "script": "node .claude/hooks/startup.js",
      "description": "读取三大件并汇报项目状态"
    }
  }
}
```

## 启动钩子工作流程

### 执行时机
- 每次在此项目目录下启动 Codex 会话时
- 无论是通过 CLI、Web、还是 VSCode 扩展

### 执行步骤

1. **读取三大件**
   ```
   ✅ 已读取: PROJECT_STATUS.md, WORKFLOW.md, CLAUDE.md
   ```

2. **解析关键信息**
   - 项目进度、当前阶段
   - 主线任务、阻塞问题
   - 关键指标、P0/P1 待办

3. **生成状态汇报**
   ```
   ## 📍 当前状态（2026/09/25）
   
   **项目进度**: 45%
   **当前阶段**: 成本体系建设期·第一版数据分析完成
   **主线任务**: 优化PPT呈现（基于4-8月实际Excel数据）
   
   ## ⚡ 下一步行动（按优先级）
   
   ### P0（立即执行）
   1. 根据老板反馈优化PPT
   2. 制定数据质量改善计划（9-11月）
   ```

## 手动测试

如果想在不启动新会话的情况下测试钩子，可以运行：

```bash
node .claude/hooks/startup.js
```

## 自定义配置

### 修改汇报内容

编辑 [startup.js](startup.js)，找到 `generateReport()` 函数，可以调整：
- 显示的指标数量（当前显示前5个）
- 待办事项数量（当前 P0/P1 各显示前3个）
- 输出格式和样式

### 添加新的数据源

在 `parseProjectStatus()` 或 `parseWorkflow()` 函数中添加新的解析逻辑。

## 故障排查

### 如果启动钩子没有执行

1. **检查配置文件**
   ```bash
   cat .claude/settings.json
   ```
   确认 `hooks.startup` 配置正确

2. **手动测试脚本**
   ```bash
   node .claude/hooks/startup.js
   ```
   查看是否有错误输出

3. **检查文件权限**
   ```bash
   ls -la .claude/hooks/startup.js
   ```
   确保脚本有执行权限

4. **查看 Codex 日志**
   - VSCode: 查看 Output 面板 → Claude Code
   - CLI: 使用 `--verbose` 参数

### 如果读取失败

- 确认三大件文件存在于项目根目录
- 检查文件编码是否为 UTF-8
- 确认文件内容格式符合预期

## 最佳实践

### 保持三大件更新

启动钩子的效果取决于三大件的更新频率：

- **PROJECT_STATUS.md**: 任务完成后立即更新
- **WORKFLOW.md**: 需求变更时更新
- **CLAUDE.md**: 发现新的工作原则时更新

### 会话结束时更新

遵循全局 CLAUDE.md 中的规定：
- 用户说"要休息了"、"今天先这样"时
- 立即更新 PROJECT_STATUS.md
- 下次启动时钩子会读取最新状态

## 与全局 CLAUDE.md 的关系

本启动钩子实现了全局 `~/.claude/CLAUDE.md` 中定义的"项目工作流强制规范"：

### 每次会话启动（强制执行）

**步骤1：读取三大核心文件**（2-3分钟，强制执行）✅
```bash
1. PROJECT_STATUS.md  → 了解当前进度、焦点、待办
2. WORKFLOW.md        → 了解当前工作流版本、标准流程
3. CLAUDE.md          → 了解项目原则、验证流程
```

**步骤2：立即汇报**（不等用户发话）✅
- 启动钩子自动输出当前状态和下一步行动

**步骤3：等待用户回应**✅
- Codex 启动后已完成状态汇报，等待用户指令

### 解决的问题

- ✅ 不再需要每次启动都问"我们做到哪了"
- ✅ 不再凭记忆回答项目状态
- ✅ 不再等用户说明当前进度
- ✅ 读完文件后主动汇报，而不是说"等你指令"

## 技术实现

### 为什么用 Node.js

- Codex 的钩子系统基于 Node.js
- 跨平台兼容（Windows/macOS/Linux）
- 无需额外依赖，使用内置模块

### 核心依赖

```javascript
const fs = require('fs');      // 文件读取
const path = require('path');  // 路径处理
```

### 解析策略

- **正则匹配**: 提取标题、列表项
- **状态机**: 跟踪当前解析的章节（关键指标、待办事项等）
- **容错处理**: 文件不存在或格式错误时不中断

## 更新日志

### 2026-09-25
- ✅ 初始版本创建
- ✅ 实现三大件读取和解析
- ✅ 实现状态汇报功能
- ✅ 测试通过

## 相关文档

- [PROJECT_STATUS.md](../../PROJECT_STATUS.md) - 项目状态模板
- [WORKFLOW.md](../../WORKFLOW.md) - 工作流定义
- [CLAUDE.md](../../CLAUDE.md) - 项目工作指引
- [~/.claude/CLAUDE.md](~/.claude/CLAUDE.md) - 全局工作原则

## 许可

本配置是项目管理规范的一部分，仅用于本项目内部。
