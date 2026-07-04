#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案例数据v1.0到v2.0迁移脚本
将单流派结构迁移到多流派架构
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def migrate_case_to_v2(case_data):
    """
    将v1.0案例数据迁移到v2.0结构

    v1.0结构：扁平的字段（tags, crisis_level, techniques_used等）
    v2.0结构：analyses对象包含多个流派，每个流派有独立的分析
    """

    # 检查是否已经是v2.0格式
    if case_data.get("version") == "2.0" and "analyses" in case_data:
        print(f"  案例 {case_data.get('case_id')} 已经是v2.0格式，跳过")
        return case_data

    # 创建v2.0结构
    v2_case = {
        "case_id": case_data.get("case_id"),
        "version": "2.0",
        "source_file": case_data.get("source_file"),
        "created_at": case_data.get("created_at"),
        "last_modified": datetime.now().isoformat(),

        # 流派无关的核心数据
        "basic_info": case_data.get("basic_info", {}),
        "session_info": case_data.get("session_info", {}),
        "dialogue": case_data.get("dialogue", ""),

        # 多流派分析容器
        "analyses": {},

        # 历次感悟记录
        "supervision_records": case_data.get("supervision_records", []),

        # 模拟对话记录
        "simulation_sessions": case_data.get("simulation_sessions", [])
    }

    # 如果存在旧的分析数据，迁移到daguanpai流派下
    if any(key in case_data for key in ["tags", "crisis_level", "keywords", "techniques_used", "ai_analysis"]):
        v2_case["analyses"]["daguanpai"] = {
            "tags": case_data.get("tags", {}),
            "crisis_level": case_data.get("crisis_level", ""),
            "crisis_evidence": case_data.get("crisis_evidence", ""),
            "keywords": case_data.get("keywords", []),
            "techniques_used": case_data.get("techniques_used", []),
            "ai_analysis": case_data.get("ai_analysis", {})
        }
        print(f"  案例 {case_data.get('case_id')} 迁移完成：v1.0 → v2.0（大观学派分析已迁移）")
    else:
        print(f"  案例 {case_data.get('case_id')} 迁移完成：v1.0 → v2.0（无分析数据）")

    return v2_case


def migrate_all_cases(source_dir, backup_dir=None, dry_run=False):
    """
    迁移指定目录下的所有案例文件

    Args:
        source_dir: 案例文件所在目录
        backup_dir: 备份目录（可选，如果提供则先备份）
        dry_run: 是否为演练模式（不实际写入文件）
    """
    source_path = Path(source_dir)

    if not source_path.exists():
        print(f"错误：源目录不存在：{source_dir}")
        return False

    # 备份
    if backup_dir and not dry_run:
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        print(f"备份目录：{backup_path}")

    # 查找所有JSON文件
    json_files = list(source_path.glob("*.json"))

    if not json_files:
        print(f"警告：在 {source_dir} 中未找到JSON文件")
        return True

    print(f"\n找到 {len(json_files)} 个案例文件")
    print("=" * 60)

    success_count = 0
    skip_count = 0
    error_count = 0

    for json_file in json_files:
        try:
            print(f"\n处理：{json_file.name}")

            # 读取原文件
            with open(json_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)

            # 备份原文件
            if backup_dir and not dry_run:
                backup_file = Path(backup_dir) / json_file.name
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(case_data, f, ensure_ascii=False, indent=2)
                print(f"  已备份到：{backup_file}")

            # 迁移数据
            v2_case = migrate_case_to_v2(case_data)

            # 检查是否需要更新
            if v2_case == case_data:
                skip_count += 1
                continue

            # 写入新文件
            if not dry_run:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(v2_case, f, ensure_ascii=False, indent=2)
                print(f"  已更新：{json_file}")
            else:
                print(f"  [演练模式] 将更新：{json_file}")

            success_count += 1

        except Exception as e:
            print(f"  错误：处理 {json_file.name} 时出错：{e}")
            error_count += 1
            continue

    # 总结
    print("\n" + "=" * 60)
    print(f"迁移完成！")
    print(f"  成功迁移：{success_count} 个")
    print(f"  跳过：{skip_count} 个")
    print(f"  失败：{error_count} 个")

    return error_count == 0


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='案例数据v1.0到v2.0迁移工具')
    parser.add_argument('--source', '-s',
                        default='data/cases/processed',
                        help='源目录（默认：data/cases/processed）')
    parser.add_argument('--backup', '-b',
                        help='备份目录（可选）')
    parser.add_argument('--dry-run', '-d',
                        action='store_true',
                        help='演练模式（不实际写入文件）')

    args = parser.parse_args()

    print("案例数据迁移工具 v1.0 → v2.0")
    print("=" * 60)

    if args.dry_run:
        print("[演练模式] 不会修改任何文件")
        print("=" * 60)

    # 执行迁移
    success = migrate_all_cases(
        source_dir=args.source,
        backup_dir=args.backup,
        dry_run=args.dry_run
    )

    if success:
        print("\n[成功] 迁移成功！")
        return 0
    else:
        print("\n[失败] 迁移过程中出现错误")
        return 1


if __name__ == "__main__":
    sys.exit(main())
