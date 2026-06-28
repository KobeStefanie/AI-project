#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查标签库中是否有重复的标签显示名称"""

import json
import sys
import io
from collections import defaultdict

# Windows UTF-8 输出支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 读取标签库
with open('data/config/tags_library.json', 'r', encoding='utf-8') as f:
    tags_library = json.load(f)

print("=" * 70)
print("检查关系标签重复情况")
print("=" * 70)

# 检查关系标签
for category, data in tags_library['relation_tags'].items():
    print(f"\n【{category}】")

    # 记录每个显示名称对应的完整标签
    display_names = defaultdict(list)

    for subcategory, tags in data['children'].items():
        for tag in tags:
            # 提取显示名称（最后一级）
            display_name = tag.split('-')[-1]
            display_names[display_name].append(tag)

    # 找出重复的
    has_duplicate = False
    for display_name, full_tags in sorted(display_names.items()):
        if len(full_tags) > 1:
            has_duplicate = True
            print(f"  ❌ 重复显示名称: {display_name}")
            for full_tag in full_tags:
                print(f"     - {full_tag}")

    if not has_duplicate:
        print(f"  ✓ 无重复")

print("\n" + "=" * 70)
print("检查症状标签重复情况")
print("=" * 70)

# 检查症状标签
for category, data in tags_library['symptom_tags'].items():
    print(f"\n【{category}】")

    display_names = defaultdict(list)
    children = data['children']

    if isinstance(children, list):
        # 直接是数组
        for tag in children:
            display_name = '-'.join(tag.split('-')[1:])  # 去掉一级分类
            display_names[display_name].append(tag)
    else:
        # 有子分类
        for subcategory, tags in children.items():
            for tag in tags:
                display_name = '-'.join(tag.split('-')[1:])  # 去掉一级分类
                display_names[display_name].append(tag)

    has_duplicate = False
    for display_name, full_tags in sorted(display_names.items()):
        if len(full_tags) > 1:
            has_duplicate = True
            print(f"  ❌ 重复显示名称: {display_name}")
            for full_tag in full_tags:
                print(f"     - {full_tag}")

    if not has_duplicate:
        print(f"  ✓ 无重复")

print("\n" + "=" * 70)
