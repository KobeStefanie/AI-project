#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式删除来访者工具
"""

import json
import sys
import io
from pathlib import Path
from api_delete_visitor import delete_visitor, VISITORS_DIR

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def list_visitors():
    """列出所有来访者"""
    visitors = []
    if VISITORS_DIR.exists():
        for visitor_dir in sorted(VISITORS_DIR.iterdir()):
            if visitor_dir.is_dir():
                profile_file = visitor_dir / 'profile.json'
                if profile_file.exists():
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                        visitors.append({
                            'id': profile['visitor_id'],
                            'name': profile['basic_info'].get('name', '未命名'),
                            'visits': len(profile.get('visit_history', [])),
                            'last_date': profile.get('visit_history', [{}])[-1].get('date', '未知') if profile.get('visit_history') else '未知'
                        })
    return visitors


def main():
    """主函数"""
    print("=" * 60)
    print("交互式删除来访者工具")
    print("=" * 60)

    visitors = list_visitors()

    if not visitors:
        print("\n没有找到任何来访者数据")
        return

    print(f"\n共找到 {len(visitors)} 个来访者：\n")

    for i, v in enumerate(visitors, 1):
        print(f"{i}. {v['name']} ({v['id']}) - {v['visits']}次来访，最近:{v['last_date']}")

    print("\n请选择要删除的来访者（输入序号，多个用空格分隔，或输入 'all' 删除全部）：")
    print("输入 'q' 退出")

    choice = input("\n请选择: ").strip().lower()

    if choice == 'q':
        print("\n已取消")
        return

    if choice == 'all':
        confirm = input(f"\n确定要删除全部 {len(visitors)} 个来访者吗？(yes/no): ").strip().lower()
        if confirm != 'yes':
            print("\n已取消")
            return
        to_delete = visitors
    else:
        try:
            indices = [int(x.strip()) for x in choice.split()]
            to_delete = [visitors[i-1] for i in indices if 1 <= i <= len(visitors)]
        except (ValueError, IndexError):
            print("\n输入无效")
            return

    if not to_delete:
        print("\n没有选择任何来访者")
        return

    print("\n将要删除以下来访者：")
    for v in to_delete:
        print(f"  - {v['name']} ({v['id']})")

    confirm = input("\n确认删除吗？(yes/no): ").strip().lower()
    if confirm != 'yes':
        print("\n已取消")
        return

    print("\n开始删除...")
    print("-" * 60)

    success_count = 0
    for v in to_delete:
        result = delete_visitor(v['id'])
        if result['success']:
            success_count += 1
            print(f"✓ {v['name']} ({v['id']})")
        else:
            print(f"✗ {v['name']} ({v['id']}) - {result.get('error', '未知错误')}")

    print("-" * 60)
    print(f"\n完成！成功删除 {success_count}/{len(to_delete)} 个来访者")
    print("\n提示：运行以下命令重新生成来访者库页面：")
    print("  python src/generate_visitor_library.py")


if __name__ == '__main__':
    main()
