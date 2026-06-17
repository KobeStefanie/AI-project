---
name: office-file-reading-strategy
description: 本机读取/生成 Office 文件（docx/xlsx/pptx）+ 转 PDF 的最优路径
metadata:
  type: reference
---

## 本机可用 & 不可用

| 工具 | 状态 | 用途 |
|------|------|------|
| Python 3.12（系统级） | ✅ | 读取 docx/pptx/xlsx |
| Node.js + docx-js（全局） | ✅ | 生成 .docx |
| PowerShell + .NET ZipFile | ✅ | 解压 docx/pptx/xlsx 读取原始 XML |
| npm | ✅ | 全局依赖管理 |
| pandoc | ❌ | 未安装 |

**Python 路径**：`C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe`
（bash 中必须用完整路径，不能用 `python3`，那指向 Windows Store 存根）

**Node.js docx-js 路径**：`C:\Users\Administrator\AppData\Roaming\npm\node_modules\docx`
（bash 中需 `NODE_PATH="C:/Users/Administrator/AppData/Roaming/npm/node_modules" node script.js`）

## 场景一：读取 .docx 内容

### 方式 A：python-docx（推荐，能提取文字）

```bash
"C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe" << 'PYEOF'
from docx import Document
doc = Document("文件.docx")
for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        print(f"[P{i}] {p.text.strip()}")

# 提取表格
for ti, table in enumerate(doc.tables):
    for ri, row in enumerate(table.rows):
        cells = [cell.text for cell in row.cells]
        print(f"[T{ti}R{ri}] {' | '.join(cells)}")
PYEOF
```

### 方式 B：PowerShell 解压读 XML（兜底，无需依赖）

```powershell
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead('文件.docx')
$doc = [System.IO.StreamReader]::new($zip.GetEntry('word/document.xml').Open())
$xml = $doc.ReadToEnd(); $doc.Close(); $zip.Dispose()
# 提取所有 <w:t> 节点文本，写入 UTF-8 文件再 Read
[System.IO.File]::WriteAllText('D:\temp_content.txt', $text, [System.Text.Encoding]::UTF8)
```

### 如果是纯图片 → 提取图片排 HTML

```powershell
# 从 word/media/ 提取所有图片，写到 HTML 依次展示
```

## 场景二：读取 .pptx 内容

用 python-pptx：

```bash
"C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe" << 'PYEOF'
from pptx import Presentation
prs = Presentation("文件.pptx")
for si, slide in enumerate(prs.slides):
    print(f"\n=== 幻灯片 {si+1} ===")
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                text = para.text.strip()
                if text:
                    print(text)
PYEOF
```

也可以用 PowerShell 解压 pptx（同样是 ZIP），读 `ppt/slides/slide*.xml` 中的 `<a:t>` 节点。

## 场景三：读取 .xlsx 内容

用 openpyxl：

```bash
"C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe" << 'PYEOF'
from openpyxl import load_workbook
wb = load_workbook("文件.xlsx", data_only=True)
for name in wb.sheetnames:
    ws = wb[name]
    print(f"\n=== 工作表: {name} ===")
    for row in ws.iter_rows(values_only=True):
        vals = [str(v) if v is not None else '' for v in row]
        if any(v for v in vals):
            print(' | '.join(vals))
PYEOF
```

## 场景四：生成 .docx

Node.js + docx-js（全局已安装）：

```bash
NODE_PATH="C:/Users/Administrator/AppData/Roaming/npm/node_modules" node << 'NODEEOF'
const { Document, Packer, Paragraph, TextRun } = require('docx');
const fs = require('fs');
// ... 构建 doc
const doc = new Document({ ... });
Packer.toBuffer(doc).then(b => fs.writeFileSync('output.docx', b));
NODEEOF
```

## 核心规则

- **优先 Python 提取文字**（python-docx / python-pptx / openpyxl）
- **PowerShell 是兜底**（当 Python 依赖缺失时，解压 ZIP 读 XML）
- **图片就直接展示图片**，不要试图 OCR
- **终端编码铁律**：中文必乱码 → 先 `WriteAllText` 到 UTF-8 文件，再 Read
- **Python 路径铁律**：bash 中必须用完整路径，`python3` 指向 Windows Store 存根不可用
