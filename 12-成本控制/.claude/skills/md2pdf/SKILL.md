---
name: md2pdf
description: 将 Markdown 文件转换为 PDF。适用于：用户要求将 .md 文件转为 PDF、项目文档需要 PDF 版本供外出阅读、文案/创作思考/策划文档更新后同步生成 PDF。任何涉及"把 Markdown 转成 PDF"的需求都应使用此 skill。
allowed-tools:
  - Bash
  - Read
  - Glob
---

# Markdown 转 PDF

## 概述

使用项目中的 `md2pdf.js` 脚本将 Markdown 文件转换为排版精美的 PDF。适用于所有标准的 Markdown 语法：标题、表格、代码块、引用、加粗斜体、行内代码、分隔线。

## 脚本位置

脚本位于 `D:\AI-项目\5-几米创作\md2pdf.js`。如果当前项目不在几米创作中，需先将该脚本复制到当前项目根目录。

依赖条件：
- Node.js（已安装）
- Google Chrome（用于无头渲染 PDF，已安装于 `C:/Program Files/Google/Chrome/Application/chrome.exe`）

## 使用方式

### 单个文件

```bash
cd <项目根目录> && node md2pdf.js "<md文件路径>"
```

### 批量转换

```bash
cd <项目根目录> && \
node md2pdf.js "路径1.md" && \
node md2pdf.js "路径2.md"
```

## 工作流程

1. 确认要转换的 Markdown 文件路径
2. 确认 Chrome 浏览器已安装且路径正确
3. 运行 `node md2pdf.js <路径>`
4. PDF 将生成在与 Markdown 源文件相同的目录下
5. 报告生成结果（文件名、大小）

## 自动触发规则

以下场景应**主动**提出转换 PDF，无需等待用户指令：

1. `0-创作思考/` 下的文档新增或重大更新后
2. `1-文案库/` 下的脚本、旁白、对白等核心文案更新后
3. 项目根目录的策划文档（如 `项目定位.md`）更新后
4. 用户明确表示某个文档需要外出阅读时

> 原因：用户有外出散步时看 PDF 进行独立思考的习惯。

## 脚本能力

`md2pdf.js` 支持以下 Markdown 语法的转换：

- 标题（H1-H4）
- 表格（含表头）
- 代码块与行内代码
- 引用块（blockquote）
- 加粗、斜体
- 分隔线
- YAML front matter（自动去除）

转换流程：Markdown → HTML（内嵌中文字体样式）→ Chrome 无头渲染 → PDF

## 注意事项

- PDF 尺寸为 A4，适合手机和打印阅读
- 中文排版：使用 Microsoft YaHei 字体，行距 1.9
- 表格和代码块设置了 `page-break-inside: avoid` 避免跨页截断
- 如果 Chrome 不可用，会降级生成 HTML 文件并提示用户手动打印
