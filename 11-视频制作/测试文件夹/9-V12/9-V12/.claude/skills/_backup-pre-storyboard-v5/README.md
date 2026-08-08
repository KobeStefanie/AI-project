# 备份说明：万能故事板 v7.0 升级前快照

**备份时间**：2026-05-23（v6.1 → v7.0 万能故事板升级前）
**备份原因**：v7.0 升级涉及大改 `seedance-storyboard-skill/SKILL.md` 与 `seedance-prompt-review-skill/SKILL.md`，备份当前 v6.1 状态以便回滚。

**目录名说明**：目录名 `_backup-pre-storyboard-v5` 中的 v5 是升级计划内部代号（「万能故事板 v5」为该 feature 本身的迷代 → 对外以项目版本号发布为 v7.0）。为保证回滚路径不变，目录名保留原名。

## 备份内容

```
_backup-pre-storyboard-v5/
├── README.md                                          # 本文件
├── seedance-prompt-review-skill-SKILL.md.bak          # review skill 的 SKILL.md（10426 bytes）
└── seedance-storyboard-skill/                         # storyboard skill 整个目录
    ├── SKILL.md                                       # 11797 bytes
    ├── seedance-prompt-methodology.md                 # 13802 bytes
    ├── examples/
    │   └── seedance-prompt-examples.md                # 29026 bytes
    ├── references/
    │   └── animation-12-principles.md                 # 9492 bytes
    └── templates/                                     # 空目录
```

## 已知预存 bug（非本次范围，v6.1 备份中存在、v7.0 未修复需后续跟进）

- `seedance-storyboard-skill/SKILL.md` 第 18 行引用 `templates/seedance-prompts-template.md`，但实际文件不存在
- v7.0 升级顺带引入 `templates/episode-master.template.md`；v7.0.1 跟进时已删除 `seedance-prompts-template.md`（孤儿 v6.1 模板）

## 回滚方法

如果 v7.0 升级出现严重问题：

```powershell
# 完整回滚 storyboard-skill
Remove-Item -Path ".claude\skills\seedance-storyboard-skill\*" -Recurse -Force
Copy-Item -Path ".claude\skills\_backup-pre-storyboard-v5\seedance-storyboard-skill\*" -Destination ".claude\skills\seedance-storyboard-skill\" -Recurse -Force

# 回滚 review-skill 的 SKILL.md
Copy-Item -Path ".claude\skills\_backup-pre-storyboard-v5\seedance-prompt-review-skill-SKILL.md.bak" -Destination ".claude\skills\seedance-prompt-review-skill\SKILL.md" -Force
```

## 删除时机

v7.0 稳定运行 1 周后可删除整个 `_backup-pre-storyboard-v5/` 目录。
