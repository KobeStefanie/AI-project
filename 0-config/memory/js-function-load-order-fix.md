---
name: js-function-load-order-fix
description: JavaScript函数定义必须在调用前 - HTML生成顺序问题的根本解决方案
metadata:
  type: feedback
  project: 心理咨询-S1
  date: 2026-06-29
---

# JavaScript函数加载顺序问题修复

## 问题现象

流派分析页面的"编辑"、"上传Word"、"下载Word"按钮点击无效，浏览器控制台报错：
```
Uncaught ReferenceError: switchTab is not defined
Uncaught ReferenceError: toggleEdit is not defined
Uncaught ReferenceError: uploadApproachWord is not defined
```

## 根本原因

**HTML生成顺序错误导致JavaScript函数未定义**：

1. `get_html_template()` 生成 `<head>` 和 `<body>` 开始标签
2. 页面内容在中间生成，包含按钮的 `onclick="switchTab(...)"` 属性
3. `get_html_footer()` 在页面底部才定义JavaScript函数

**结果**：按钮在第216行就调用函数，但函数在第1845行才定义。

## 为什么每次都出现

- 每次运行 `generate_visit_details.py` 都会按这个错误顺序生成HTML
- HTML中的 `onclick` 属性是同步执行的，不是事件监听器
- 必须在HTML解析到按钮时，函数已经在全局作用域中定义

## 解决方案

**将所有JavaScript函数定义移到 `<head>` 标签内**：

```python
def get_html_template():
    return """<!DOCTYPE html>
<html>
<head>
    ...
    <script>
        // 在head中定义所有函数
        function switchTab(tabName) { ... }
        function toggleEdit(approachName) { ... }
        function uploadApproachWord(...) { ... }
        // ... 所有其他函数
    </script>
</head>
<body>
"""

def get_html_footer():
    return """
</body>
</html>
"""
```

## 技术要点

1. **函数定义优先级**：
   - inline事件处理器 (`onclick="func()"`) 要求函数在全局作用域已定义
   - 必须在HTML解析到调用点之前定义函数

2. **推荐做法**：
   - 将JavaScript放在 `<head>` 中
   - 或使用 `DOMContentLoaded` 后再绑定事件监听器（不用onclick属性）

3. **避免的错误**：
   - ❌ 在页面底部定义函数，顶部就调用
   - ❌ 认为浏览器会"等待"所有JavaScript加载完
   - ✅ 函数先定义，后调用

## 修改的文件

- `D:\AI-项目\4-心理咨询-S1\src\generate_visit_details.py`
  - `get_html_template()`: 第27-305行，包含所有JavaScript函数
  - `get_html_footer()`: 第308-313行，只有结束标签

## **Why**：为什么会反复出现

这不是"按钮丢失"，而是**HTML生成逻辑本身有问题**。每次生成HTML都会重现，因为：
- Python代码的结构决定了生成顺序
- 没有从根本上修复模板结构

## **How to apply**：如何应对类似问题

遇到 `XXX is not defined` 错误时：

1. **立即检查**：函数定义在HTML的哪个位置？调用在哪个位置？
2. **HTML生成逻辑**：查看Python代码如何组装HTML
3. **根本性修复**：调整模板结构，不要打补丁
4. **测试验证**：重新生成HTML后，检查浏览器控制台是否还有错误

**记住**：这类问题不是"内容丢失"，而是"顺序错误"。修复时要调整生成逻辑，而不是手动编辑生成的HTML。
