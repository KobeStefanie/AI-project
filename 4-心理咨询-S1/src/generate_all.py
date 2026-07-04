#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主生成器：一键生成完整的来访者库
包括：首页、来访者档案页、来访详情页、对比视图
"""

import sys
import io
import subprocess
from pathlib import Path

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
project_root = Path(__file__).parent.parent
src_dir = project_root / 'src'


def run_script(script_name):
    """运行生成脚本"""
    script_path = src_dir / script_name
    print(f"\n{'='*60}")
    print(f"运行: {script_name}")
    print('='*60)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(project_root),
        capture_output=False
    )

    if result.returncode != 0:
        print(f"✗ 错误: {script_name} 执行失败")
        return False

    return True


def main():
    """主函数"""
    print("=" * 60)
    print("来访者库 - 主生成器")
    print("=" * 60)
    print("\n此脚本将依次执行以下生成器：")
    print("  1. generate_visitor_library.py  - 来访者库首页 + 档案页")
    print("  2. generate_visit_details.py    - 来访详情页")
    print("  3. generate_comparison_views.py - 对比视图")
    print("  4. generate_downloads.py        - 下载文件")

    input("\n按 Enter 继续...")

    scripts = [
        'generate_visitor_library.py',
        'generate_visit_details.py',
        'generate_comparison_views.py',
        'generate_downloads.py'
    ]

    success_count = 0
    for script in scripts:
        if run_script(script):
            success_count += 1
        else:
            print(f"\n终止执行，因为 {script} 失败")
            break

    print("\n" + "=" * 60)
    if success_count == len(scripts):
        print("✓ 全部生成完成！")
        print("=" * 60)
        print("\n生成的文件：")
        print("  - 来访者库首页: output/来访者库/index.html")
        print("  - 来访者档案页: output/来访者库/V*/profile.html")
        print("  - 来访详情页: output/来访者库/V*/visit_*.html")
        print("  - 对比视图: output/来访者库/V*/comparison.html")
        print("  - 下载文件: output/来访者库/downloads/")
    else:
        print(f"✗ 部分失败 ({success_count}/{len(scripts)} 成功)")
    print("=" * 60)


if __name__ == '__main__':
    main()
