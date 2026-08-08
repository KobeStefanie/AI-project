#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 修复全局CLAUDE.md中clean_text函数的BUG

with open("C:/Users/Administrator/.claude/CLAUDE.md", 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 修复第716行（粗体）- 索引715
if 715 < len(lines):
    old_line = lines[715]
    if "r''" in old_line and "**" in old_line:
        lines[715] = old_line.replace("r''", r"r'\1'")
        print("Fixed line 716: bold")
    else:
        print(f"Line 716 not match: {old_line.strip()}")

# 修复第718行（斜体）- 索引717
if 717 < len(lines):
    old_line = lines[717]
    if "r''" in old_line and "\\*([^*]+)\\*" in old_line:
        lines[717] = old_line.replace("r''", r"r'\1'")
        print("Fixed line 718: italic")
    else:
        print(f"Line 718 not match: {old_line.strip()}")

# 写回文件
with open("C:/Users/Administrator/.claude/CLAUDE.md", 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nGlobal CLAUDE.md fixed")
