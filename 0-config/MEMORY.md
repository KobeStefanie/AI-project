## profile（用户画像与协作风格）
- [用户档案](profile/user-profile.md) — 角色、技术栈偏好、项目组织规范、当前主要项目
- [协作风格](profile/collaboration-style.md) — 沟通方式、代码编写习惯、版本与文档同步规则、工具使用偏好
- [我的开发习惯](profile/我的开发习惯.md) — 开发习惯全集：沟通/项目组织/版本管理/代码风格/PWA规范/任务管理/工具使用

## rules（规则与行为约定）
- [项目目录规范](rules/project-rules.md) — 项目存放位置、命名格式、内部结构、新建流程
- [浏览器自动化偏好](rules/browser-automation-preference.md) — 浏览器操作直接执行不询问用户
- [自动打开预览](rules/auto-open-preview.md) — 静态 HTML 预览文件生成后自动浏览器打开
- [Git 自动推送 GitHub](rules/git-auto-push-github.md) — 每次 commit 后 post-commit hook 自动推送到 GitHub
- [CatKingAI 优先使用](rules/catkingai-preferred-api.md) — 自研 API 网关，默认首选，调用其他 API 需先征得同意
- [Memory 默认存储位置](rules/memory-default-location.md) — 所有 memory 权威源为 D:\AI-项目\0-config，不得擅自变更
- [技能存储规范](rules/skills-storage-rules.md) — 技能安装后存储位置、文件命名、0-config规则维护
- [删除文件必须使用回收站](rules/file-deletion-must-use-recycle-bin.md) — ⚠️ 禁止直接 rm 删除，必须移到回收站确保可恢复

## projects（项目状态与技术参考）
- [心理咨询-S1](projects/psych-counseling-s1.md) — D:\AI-项目\4-心理咨询-S1\，初始搭建阶段
- [几米创作](projects/jimmy-creation.md) — D:\AI-项目\5-几米创作\，初始搭建阶段
- [灵感收集器](projects/inspiration-collector.md) — 跨端灵感捕获与整理项目，PLAN 阶段，执行前需确认
- [Token 追踪系统紧急补救](projects/token-tracker-rescue.md) — 代理服务器故障恢复、配置备份还原、API 配置紧急修复方案
- [iOS PWA 限制与应对](projects/ios-pwa-limitations.md) — iOS 18.2 自签 HTTPS + 私网的书签存储隔离、HTTP 数据不持久化、默认浏览器陷阱及完整应对方案
- [时间管理助手同步要点](projects/time-planner-sync-ios.md) — 同步架构、iOS 自签证书限制、SW 缓存陷阱、调试排查口诀
- [音频转录指南](projects/audio-transcription-guide.md) — FunASR SenseVoiceSmall + ct-punc 第一方案，faster-whisper 备选
- [Office 文件读取策略](projects/office-file-reading-strategy.md) — Python 读 docx/pptx/xlsx + Node.js 生成 docx，PowerShell 兜底

## memory（记忆系统）
- [Memory 索引](memory/MEMORY.md)
- [JavaScript 函数加载顺序修复](memory/js-function-load-order-fix.md) — HTML 生成顺序导致按钮失效的根因与解决方案
- [Context 压缩对话整理规则](memory/context-compact-workflow.md) — 压缩前整理保存、压缩后自动读取
- [对话历史导出技能](memory/export-conversation-skill.md) — Claude Code 会话导出为 Markdown/Word 文档
- [心理咨询-S1 首页集成要求](memory/psych-s1-homepage-integration.md) — 所有功能页面必须集成到主页面才视为完工

## skills（技能）
- [export-conversation](skills/export-conversation/SKILL.md) — 导出对话历史为 Markdown/Word 文档

## tools（工具脚本）
- [doubao-vision](tools/doubao-vision.js) — 豆包视觉识别命令行工具
- [.doubao-env](tools/.doubao-env) — 豆包 API 密钥与端点配置
