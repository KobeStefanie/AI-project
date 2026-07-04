---
name: browser-automation-preference
description: 浏览器操作偏好——直接执行不询问
metadata:
  type: feedback
---

# 浏览器自动化操作偏好

用户明确要求：当需要进行浏览器操作时，直接使用 agent-browser 技能执行，不要询问用户来操作。

**Why:** 用户觉得手动操作浏览器很累，希望将这类任务完全委托给 AI 自动化处理。

**How to apply:** 
- 当任务涉及浏览器操作（打开网页、搜索、截图、提取数据、填写表单等）时，直接调用 agent-browser 技能执行
- 不要说"你需要..."或"请打开浏览器..."，而是直接说"我来帮你..."然后执行
- 执行后汇报结果即可

**关联记忆:**
- [[skills-storage-rules]] — agent-browser 技能已安装在 D:\AI-项目\A-skills\agent-browser\
