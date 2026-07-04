---
name: git-auto-push-github
description: 每次 git commit 后自动推送到 GitHub 仓库
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f304e012-20dd-40ad-87c0-1694a411ea4d
---

# Git 自动推送 GitHub

## 规则

`D:\AI-项目\` 仓库已配置 post-commit hook，每次提交后自动推送（`git push origin`）。

**远程仓库：** `https://github.com/KobeStefanie/AI-project.git`

**How it works:**
- `.git/hooks/post-commit` 在每次 `git commit` 后触发
- 后台执行 `git push origin <current-branch>`，不阻塞终端
- 日志输出到 `.git/hook-push.log`

**How to apply:**
- 每次在 `D:\AI-项目\` 下提交后，无需手动 `git push`
- 如推送失败，检查 `.git/hook-push.log` 排查
- 如 GitHub 认证过期，需重新配置凭据

## 关联记忆

- [[project-rules]] — 项目目录规范
