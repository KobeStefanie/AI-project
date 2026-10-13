# 通用书籍知识转化系统 - 工作指引

**项目类型**：知识管理 / 技能开发  
**创建时间**：2026-09-22  
**最后更新**：2026-09-23 01:00

---

## 🎯 项目目标

**核心定位**：建立一个**领域无关**的通用书籍知识吸收与转化系统，将任意领域的书籍（心理学、历史、营养学、医学、技术等）转化为结构化的 Claude 技能。

**5大转化目的类型**：

| 目的类型 | 说明 | 适用书籍示例 |
|---------|------|-------------|
| **1. 技能学习** | 学习可操作的技能 | 《循环提问》《Python编程》《如何谈判》 |
| **2. 知识吸收** | 理解领域知识体系 | 《人类简史》《营养学概论》《经济学原理》 |
| **3. 实践指导** | 获得行动指南和决策支持 | 《如何阅读一本书》《饮食指南》《理财手册》 |
| **4. 参考查询** | 作为工具书随时查询 | 《医学手册》《法律条文》《编程API参考》 |
| **5. 思维启发** | 获得思考框架和视角 | 《思考快与慢》《原则》《系统思考》 |

**长期愿景**：建立一个专业、可复用、标准化的"书籍→技能"转化流水线，支持大批量、多领域书籍快速转化。

---

## 💎 核心资产说明

### 主要资产类型

1. **转化流程和模板**
   - PDF提取脚本：[extract_pdf_better.py](extract_pdf_better.py)
   - skill-from-book 技能：[.agents/skills/skill-from-book/](.agents/skills/skill-from-book/)
   - 标准化工作流：[WORKFLOW.md](WORKFLOW.md)

2. **已转化的技能**
   - 存储位置：[.agents/skills/](.agents/skills/)
   - 命名规范：`[purpose]-[domain]-[book-slug]/`
   - 示例：
     - `skill-psychology-circular-questioning/`（技能学习类）
     - `knowledge-history-sapiens/`（知识吸收类）
     - `practice-nutrition-diet-guide/`（实践指导类）

3. **书籍索引与元信息**
   - [BOOKS_INDEX.md](BOOKS_INDEX.md) - 多维标签索引
   - [books/metadata/](books/metadata/) - 每本书的YAML元信息
   - [relationships/](relationships/) - 书籍关联关系图

4. **质量标准**
   - 提取质量标准
   - 技能文件结构规范（按目的类型灵活选择）
   - 验收标准

---

## 🔧 工作原则

### 原则1：遵循 skill-from-book 的6 Phase工作流

**严格顺序**（不可跳跃）：
```
Phase 1: 分析（只提取目录，不读全文）
Phase 2: 规划（设计文件结构，规划提取任务）
Phase 3: 提取（使用子代理并行提取）
Phase 4: 指南（创建 guidelines.md）
Phase 5: 工作流（提议并创建 workflows）
Phase 6: 最终化（验证和测试）
```

**关键规定**：
- ✅ Phase 1-2 在主会话完成（不读书籍全文）
- ✅ Phase 3 必须使用子代理（Agent tool）
- ✅ Phase 5 必须先提议，经用户确认后再创建
- ❌ 主会话绝不直接读取书籍完整内容

---

### 原则2：信息真实性原则（继承自全局 CLAUDE.md）

**绝不编造**：
- ✅ 所有内容必须来源于书籍原文
- ✅ 不确定的内容标注"待确认"
- ❌ 不能为了"完整性"编造书中不存在的内容
- ❌ 不能"推测"作者的观点

**强制溯源**：
- 提取的每个知识点，能追溯到书籍的具体章节
- 示例和案例必须来自原书
- 原则和规则必须有书中依据

---

### 原则3：目的驱动（Purpose-Driven）

**核心理念**：技能结构由"为什么读这本书"决定，而非"读什么书"。

**5大目的类型与对应技能结构**：

| 目的类型 | 技能结构 | 必需目录 | 可选目录 |
|---------|---------|---------|---------|
| **技能学习** | 学习可操作的技能 | workflows/, references/ | checklists/ |
| **知识吸收** | 理解知识体系 | references/ | mind-maps/ |
| **实践指导** | 获得行动指南 | checklists/, decision-trees/, references/ | workflows/ |
| **参考查询** | 工具书查询 | index/, quick-reference/, references/ | - |
| **思维启发** | 思考框架和视角 | frameworks/, perspectives/, references/ | case-studies/ |

**目的类型选择决策树**：
1. 书中有明确的"步骤"、"流程"、"操作方法" → **技能学习**
2. 书以"概念"、"理论"、"知识体系"为主 → **知识吸收**
3. 书提供"检查清单"、"决策指南"、"行动建议" → **实践指导**
4. 书是"手册"、"词典"、"条目式"组织 → **参考查询**
5. 书强调"思维方式"、"原则"、"框架" → **思维启发**

**验证方式**：
- 用真实使用场景测试技能
- 确保 [guidelines.md](guidelines.md) 能正确路由到相关文件
- 技能结构与阅读目的匹配

---

### 原则4：标准化与可复用

**流程标准化**：
- 所有书籍遵循相同的6 Phase流程
- 使用统一的文件命名规范
- 使用统一的模板和脚本

**知识模块化**：
- 每个文件 50-200 行
- 一个文件一个主题
- 避免重复内容

**质量可控**：
- 明确的验收标准
- 可重复的验证流程
- 失败案例记录和改进

---

## ✅ 验证流程

### 提取质量验证

**PDF提取验证**：
1. 检查 `book_content.md` 文件大小（应 > 100KB）
2. 随机抽查10页，检查乱码率（应 < 5%）
3. 验证目录完整性（toc.json 包含所有章节）

**知识提取验证**：
1. 每个必需文件（knowledge.md, rules.md, examples.md）已创建
2. 文件大小在 50-200 行范围内
3. 内容已转化（不是原文复制）
4. 交叉引用正确（[[file-name]]链接有效）

---

### 技能功能验证

**使用场景测试**：
1. 准备5个真实使用场景的查询
2. 通过 guidelines.md 路由到文件
3. 检查返回的文件是否正确和完整
4. 调整 guidelines.md 直到路由正确

**工作流验证**：
1. 每个工作流包含清晰的步骤
2. 步骤可执行（不抽象）
3. 有明确的退出标准
4. 引用的文件存在且正确

---

## 📂 文档管理规则

### 创建规则

**技能文件结构**（根据目的类型灵活选择）：

#### 1. 技能学习类
```
skill-[domain]-[book-slug]/
├── SKILL.md              # 总览
├── guidelines.md         # 使用指南
├── progress.md           # 进度追踪
├── workflows/            # 必需：操作流程
│   ├── [task-1].md
│   └── [task-2].md
├── references/           # 必需：知识库
│   ├── [category]/
│   │   ├── knowledge.md
│   │   ├── rules.md
│   │   └── examples.md
└── checklists/           # 可选：检查清单
```

#### 2. 知识吸收类
```
knowledge-[domain]-[book-slug]/
├── SKILL.md
├── guidelines.md
├── progress.md
├── references/           # 必需：知识库
│   ├── [category]/
│   │   ├── concepts.md
│   │   ├── theories.md
│   │   └── connections.md
└── mind-maps/            # 可选：思维导图
```

#### 3. 实践指导类
```
practice-[domain]-[book-slug]/
├── SKILL.md
├── guidelines.md
├── progress.md
├── checklists/           # 必需：检查清单
│   ├── [scenario-1].md
│   └── [scenario-2].md
├── decision-trees/       # 必需：决策树
│   ├── [decision-1].md
│   └── [decision-2].md
└── references/           # 必需：知识库
    └── [category]/
```

#### 4. 参考查询类
```
reference-[domain]-[book-slug]/
├── SKILL.md
├── guidelines.md
├── index/                # 必需：索引
│   ├── by-topic.md
│   ├── by-keyword.md
│   └── by-use-case.md
├── quick-reference/      # 必需：速查表
│   ├── [table-1].md
│   └── [table-2].md
└── references/           # 必需：详细内容
    └── [category]/
```

#### 5. 思维启发类
```
thinking-[domain]-[book-slug]/
├── SKILL.md
├── guidelines.md
├── frameworks/           # 必需：思维框架
│   ├── [framework-1].md
│   └── [framework-2].md
├── perspectives/         # 必需：视角
│   ├── [perspective-1].md
│   └── [perspective-2].md
└── references/           # 必需：知识库
    └── [category]/
```

**命名规范**：
- 技能名：`[purpose]-[domain]-[book-slug]`
  - 示例：`skill-psychology-circular-questioning`
  - 示例：`knowledge-history-sapiens`
  - 示例：`practice-nutrition-diet-guide`
- 分类文件夹：名词复数，如 `core-concepts/`, `techniques/`
- Markdown文件：小写，连字符，如 `knowledge.md`, `decision-tree.md`

---

### 更新规则

**何时更新**：
- ✅ 发现书籍内容理解错误 → 更新对应的 references/ 文件
- ✅ 用户反馈路由错误 → 更新 guidelines.md
- ✅ 工作流不清晰 → 优化 workflows/ 文件
- ✅ 发现新的使用场景 → 补充到 guidelines.md

**更新流程**：
1. 确认需要更新的文件
2. 读取当前内容
3. 进行修改
4. 验证修改效果
5. 更新 PROJECT_STATUS.md 记录变更

---

### 归档规则

**完成的技能**：
- 验证通过后，保持在 `.agents/skills/[skill-name]/`
- 在 `BOOKS_INDEX.md` 中记录元信息
- 不移动或重命名

**中间文件**：
- `book_content.md` - 保留，可能需要重新提取
- `toc.json` - 保留，作为书籍结构参考
- `extract_*.py` - 保留，可复用

**废弃文件**：
- 测试脚本 → 移到 `archive/` 目录
- 失败的提取 → 移到 `archive/failed/`
- 不使用 `rm` 命令，使用 PowerShell Remove-Item

---

## 🚫 禁止事项

### 内容相关

❌ **绝对禁止**：
- 编造书中不存在的内容（案例、理论、技术）
- 混淆不同书籍的内容
- 添加非书籍来源的"补充知识"
- 主会话直接读取书籍全文（Phase 3必须用子代理）

### 流程相关

❌ **绝对禁止**：
- 跳过 Phase（必须按1→2→3→4→5→6顺序）
- Phase 5 不征求用户确认就创建工作流
- 不读三大核心文件就开始工作
- 任务完成不更新 PROJECT_STATUS.md

### 文件管理相关

❌ **绝对禁止**：
- 使用 `rm` 命令删除文件（必须用 PowerShell Remove-Item）
- 文件超过 300 行不拆分
- 不按命名规范创建文件
- 创建重复的文件（如同一内容多个文件）

---

## 🔄 特殊场景处理

### 场景1：PDF提取失败或乱码

**原因分析**：
- 编码问题（GBK vs UTF-8）
- PDF格式特殊（扫描版、加密）
- 库的兼容性问题

**处理步骤**：
1. 尝试 `pdfplumber` 库（当前使用）
2. 如仍失败，尝试 `pypdf` 或 `PyMuPDF`
3. 如全部失败，请求用户提供可提取的版本
4. 记录失败原因到 PROJECT_STATUS.md 风险清单

---

### 场景2：书籍结构不适合标准模板

**示例**：
- 纯案例集（没有理论章节）
- 纯理论书（没有实践指导）
- 参考手册（条目式，非章节式）

**处理步骤**：
1. 在 Phase 1 分析时识别特殊结构
2. 调整 Phase 2 的文件结构设计
3. 保持 workflows/ 和 references/ 两大目录
4. 灵活调整 references/ 内部分类
5. 记录特殊处理方式到 WORKFLOW.md

---

### 场景3：多本书需要合并为一个技能

**触发条件**：
- 同一主题的系列书籍
- 基础+进阶配套书籍
- 理论+实践配套书籍

**处理步骤**：
1. 先单独转化每本书
2. 在 Phase 2 规划合并结构
3. 使用子代理重新组织内容
4. 在 SKILL.md 中注明内容来源
5. BOOKS_INDEX.md 记录多本书对应一个技能

---

## 📊 质量标准

### 提取质量

**合格标准**：
- PDF 提取无乱码（乱码率 < 5%）
- 目录完整（与书籍目录一致）
- 内容完整（无大段缺失）
- 编码正确（UTF-8）

### 技能质量

**合格标准**：
- 所有必需文件已创建
- 文件大小符合规范（50-200行）
- 内容已转化（不是原文复制）
- guidelines.md 路由正确率 > 90%
- 至少3个工作流
- 通过5个真实场景测试

**优秀标准**：
- 包含丰富的示例
- 工作流步骤详细可执行
- 包含练习和自我评估材料
- 交叉引用完整
- 用户反馈积极

---

## 🔗 关联文件

- [PROJECT_STATUS.md](PROJECT_STATUS.md) - 项目状态跟踪
- [WORKFLOW.md](WORKFLOW.md) - 工作流与需求管理
- [全局 CLAUDE.md](C:\Users\Administrator\.claude\CLAUDE.md) - 全局工作原则

---

## 📝 项目特定记忆点

### 关键学习

1. **PDF提取编码问题**：PyPDF2 对中文支持不好，pdfplumber 更好
2. **主会话不读全文**：遵循 skill-from-book 规范，Phase 3 必须用子代理
3. **工作流必须提议**：Phase 5 先列出候选工作流，用户选择后再创建

### 待验证的假设

1. 子代理并行提取是否比串行快？（第一本书完成后评估）
2. 50-200 行的文件大小是否合适？（根据使用反馈调整）
3. 6 Phase 流程是否适用于所有类型的书籍？（遇到特殊书籍时调整）

---

**制定时间**：2026-09-22  
**制定原因**：建立标准化的"书籍→技能"转化流程，支持大批量书籍处理  
**适用范围**：本项目下所有书籍转化任务
