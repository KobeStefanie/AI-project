#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本：v1.0 → v2.0
将单流派结构迁移到多流派嵌套结构
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 路径配置
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "cases" / "processed"
BACKUP_DIR = PROJECT_ROOT / "data" / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")

# 需要迁移到 analyses.daguanpai 的字段
ANALYSIS_FIELDS = [
    "tags",
    "crisis_level",
    "crisis_evidence",
    "keywords",
    "techniques_used",
    "ai_analysis"
]

# 保留在根级别的字段
ROOT_FIELDS = [
    "case_id",
    "source_file",
    "created_at",
    "basic_info",
    "session_info",
    "dialogue",
    "supervision_records"
]


def backup_cases():
    """备份现有案例到备份目录"""
    print(f"📦 开始备份案例到: {BACKUP_DIR}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    case_files = list(PROCESSED_DIR.glob("*.json"))
    for case_file in case_files:
        backup_file = BACKUP_DIR / case_file.name
        shutil.copy2(case_file, backup_file)
        print(f"   ✓ 备份: {case_file.name}")

    print(f"✅ 备份完成，共 {len(case_files)} 个案例\n")
    return case_files


def migrate_case_to_v2(case_data):
    """将单个案例从v1.0迁移到v2.0结构"""

    # 构建v2.0结构
    v2_case = {
        "case_id": case_data["case_id"],
        "version": "2.0",
        "source_file": case_data["source_file"],
        "created_at": case_data["created_at"],
        "last_modified": datetime.now().isoformat(),
        "basic_info": case_data["basic_info"],
        "session_info": case_data["session_info"],
        "dialogue": case_data["dialogue"]
    }

    # 构建大观学派分析
    daguanpai_analysis = {}
    for field in ANALYSIS_FIELDS:
        if field in case_data:
            daguanpai_analysis[field] = case_data[field]

    # 添加分析对象
    v2_case["analyses"] = {
        "daguanpai": daguanpai_analysis
    }

    # 添加感悟记录（保留原有的，应该是空数组）
    v2_case["supervision_records"] = case_data.get("supervision_records", [])

    # 添加模拟会话（新功能，初始为空）
    v2_case["simulation_sessions"] = []

    return v2_case


def migrate_all_cases(case_files):
    """迁移所有案例文件"""
    print("🔄 开始迁移案例结构...")

    success_count = 0
    for case_file in case_files:
        try:
            # 读取原始案例
            with open(case_file, 'r', encoding='utf-8') as f:
                v1_case = json.load(f)

            # 迁移到v2.0
            v2_case = migrate_case_to_v2(v1_case)

            # 写回文件
            with open(case_file, 'w', encoding='utf-8') as f:
                json.dump(v2_case, f, ensure_ascii=False, indent=2)

            print(f"   ✓ 迁移: {case_file.name} → v2.0")
            success_count += 1

        except Exception as e:
            print(f"   ✗ 失败: {case_file.name} - {str(e)}")

    print(f"✅ 迁移完成，成功 {success_count}/{len(case_files)} 个案例\n")


def verify_migration(case_files):
    """验证迁移结果"""
    print("🔍 验证迁移结果...")

    all_valid = True
    for case_file in case_files:
        try:
            with open(case_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)

            # 检查必需字段
            checks = [
                ("version", case_data.get("version") == "2.0"),
                ("analyses", "analyses" in case_data),
                ("daguanpai", "daguanpai" in case_data.get("analyses", {})),
                ("supervision_records", "supervision_records" in case_data),
                ("simulation_sessions", "simulation_sessions" in case_data),
                ("last_modified", "last_modified" in case_data)
            ]

            case_valid = all(check[1] for check in checks)

            if case_valid:
                print(f"   ✓ {case_file.name}: 结构正确")
            else:
                print(f"   ✗ {case_file.name}: 结构异常")
                for check_name, check_result in checks:
                    if not check_result:
                        print(f"      - 缺失或错误: {check_name}")
                all_valid = False

        except Exception as e:
            print(f"   ✗ {case_file.name}: 读取失败 - {str(e)}")
            all_valid = False

    if all_valid:
        print("✅ 所有案例验证通过\n")
    else:
        print("⚠️  部分案例验证失败\n")

    return all_valid


def main():
    """主函数"""
    print("=" * 60)
    print("📋 案例数据迁移：v1.0 → v2.0")
    print("=" * 60)
    print()

    # Step 1: 备份
    case_files = backup_cases()

    if not case_files:
        print("⚠️  未找到需要迁移的案例文件")
        return

    # Step 2: 迁移
    migrate_all_cases(case_files)

    # Step 3: 验证
    is_valid = verify_migration(case_files)

    # 总结
    print("=" * 60)
    if is_valid:
        print("🎉 迁移完成！")
        print(f"   备份位置: {BACKUP_DIR}")
        print(f"   迁移案例: {len(case_files)} 个")
    else:
        print("⚠️  迁移完成但存在问题，请检查上述错误")
        print(f"   如需回滚，请从备份恢复: {BACKUP_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
