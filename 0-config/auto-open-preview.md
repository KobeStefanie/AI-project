---
name: auto-open-preview
description: 静态预览 HTML 文件生成后自动在浏览器中打开
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 09401a78-3a4f-4c9c-ac1d-bac3c6df653d
---

# 静态预览自动打开

## 规则

所有项目中生成的静态预览 HTML 文件（如 `preview-*.html`），完成后必须自动用浏览器打开给用户查看，无需等待用户手动要求。

**Why:** 用户每次都要看效果，手动打开多一步操作，应自动完成。

**How to apply:** 静态 HTML 预览文件写入完成后，立即执行 `start "" "<文件路径>"` 在默认浏览器中打开。不做这个操作就是漏项。
