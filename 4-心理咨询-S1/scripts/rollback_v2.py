#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回滚脚本：从备份恢复案例数据
"""

import json
import shutil
from pathlib import Path
from datetime import datetime


def rollback_from_backup(backup_dir, target_dir):
    """
    从备份目录恢复案例数据

    Args:
        backup_dir: 备份目录路径
        target_dir: 目标恢复目录
    """
    backup_path = Path(backup_dir)
    target_path = Path(target_dir)

    if not backup_path.exists():
        print(f"错误：备份目录不存在：{backup_dir}")
        return False

    if not target_path.exists():
        print(f"错误：目标目录不存在：{target_dir}")
        return False

    # 查找备份文件
    backup_files = list(backup_path.glob("*.json"))

    if not backup_files:
        print(f"警告：备份目录中没有JSON文件：{backup_dir}")
        return False

    print(f"找到 {len(backup_files)} 个备份文件")
    print("=" * 60)

    success_count = 0
    error_count = 0

    for backup_file in backup_files:
        try:
            target_file = target_path / backup_file.name
            print(f"恢复：{backup_file.name} -> {target_file}")

            # 复制文件
            shutil.copy2(backup_file, target_file)
            success_count += 1

        except Exception as e:
            print(f"  错误：{e}")
            error_count += 1

    print("=" * 60)
    print(f"恢复完成！成功：{success_count}，失败：{error_count}")

    return error_count == 0


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='从备份恢复案例数据')
    parser.add_argument('backup_dir', help='备份目录路径')
    parser.add_argument('--target', '-t',
                        default='data/cases/processed',
                        help='目标恢复目录（默认：data/cases/processed）')

    args = parser.parse_args()

    print("案例数据回滚工具")
    print("=" * 60)
    print(f"备份源：{args.backup_dir}")
    print(f"恢复到：{args.target}")
    print("=" * 60)

    # 确认操作
    confirm = input("\n确认要执行回滚吗？这将覆盖当前数据！(yes/no): ")
    if confirm.lower() != 'yes':
        print("已取消操作")
        return 0

    # 执行回滚
    success = rollback_from_backup(args.backup_dir, args.target)

    if success:
        print("\n[成功] 回滚完成！")
        return 0
    else:
        print("\n[失败] 回滚过程中出现错误")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
