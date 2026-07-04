#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流派名称迁移脚本
将旧的硬编码流派名称迁移到新的配置化流派名称
"""

import json
import sys
import io
from pathlib import Path
from approaches_manager import get_manager

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
PROJECT_ROOT = Path(__file__).parent.parent
VISITORS_DIR = PROJECT_ROOT / 'data' / 'visitors'

# 旧名称到新名称的映射
OLD_TO_NEW_MAPPING = {
    '大观派': '大观学派（危机干预）',
    'CBT': '认知行为疗法 (CBT)',
    '精神动力学': '精神动力学',
    '人本主义': '人本主义',
    '存在主义': '存在主义',
    '测试流派': None  # 删除不存在的流派
}


def migrate_visit_file(visit_json_path):
    """迁移单个visit.json文件"""
    try:
        with open(visit_json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 检查是否有approach_analyses_html字段
        approach_analyses_html = visit_data.get('case_data', {}).get('approach_analyses_html', {})

        if not approach_analyses_html:
            return False

        # 迁移数据
        migrated = False
        new_approach_analyses_html = {}

        for old_name, content in approach_analyses_html.items():
            new_name = OLD_TO_NEW_MAPPING.get(old_name, old_name)

            if new_name is None:
                # 删除不存在的流派
                print(f"  删除: {old_name}")
                migrated = True
                continue

            if new_name != old_name:
                print(f"  迁移: {old_name} → {new_name}")
                migrated = True

            new_approach_analyses_html[new_name] = content

        if migrated:
            # 更新数据
            visit_data['case_data']['approach_analyses_html'] = new_approach_analyses_html

            # 写回文件
            with open(visit_json_path, 'w', encoding='utf-8') as f:
                json.dump(visit_data, f, ensure_ascii=False, indent=2)

            return True

        return False

    except Exception as e:
        print(f"  ✗ 处理失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("流派名称迁移")
    print("=" * 60)

    # 显示映射关系
    print("\n映射关系:")
    for old_name, new_name in OLD_TO_NEW_MAPPING.items():
        if new_name is None:
            print(f"  {old_name} → [删除]")
        else:
            print(f"  {old_name} → {new_name}")

    print("\n开始扫描...")

    # 扫描所有来访者目录
    migrated_count = 0
    total_count = 0

    for visitor_dir in VISITORS_DIR.iterdir():
        if not visitor_dir.is_dir():
            continue

        visits_dir = visitor_dir / 'visits'
        if not visits_dir.exists():
            continue

        for visit_file in visits_dir.glob('*.json'):
            total_count += 1
            print(f"\n检查: {visitor_dir.name}/{visit_file.name}")

            if migrate_visit_file(visit_file):
                migrated_count += 1
                print(f"  ✓ 已迁移")
            else:
                print(f"  - 无需迁移")

    print("\n" + "=" * 60)
    print(f"迁移完成！")
    print(f"总文件数: {total_count}")
    print(f"已迁移: {migrated_count}")
    print("=" * 60)


if __name__ == '__main__':
    main()
