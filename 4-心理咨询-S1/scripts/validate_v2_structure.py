#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证所有案例数据的v2.0结构合规性
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.approaches_manager import ApproachesManager


def validate_case_file(case_path, manager):
    """验证单个案例文件"""
    issues = []

    try:
        with open(case_path, 'r', encoding='utf-8') as f:
            case_data = json.load(f)

        # 检查是否是接访记录格式（active案例）
        if 'status' in case_data and case_data.get('status') == 'active':
            # 这是接访记录格式，不是案例库格式，跳过验证
            return {
                'valid': True,
                'issues': [],
                'case_id': case_data.get('case_id', 'UNKNOWN'),
                'skipped': True,
                'reason': '接访记录格式（进行中案例）'
            }

        # 检查必需字段
        required_fields = ['case_id', 'version', 'basic_info', 'session_info', 'dialogue', 'analyses']
        for field in required_fields:
            if field not in case_data:
                issues.append(f"缺少必需字段: {field}")

        # 检查版本
        if case_data.get('version') != '2.0':
            issues.append(f"版本不是2.0: {case_data.get('version')}")

        # 检查analyses结构
        if 'analyses' in case_data:
            validation_result = manager.validate_case_analyses(case_data)
            if not validation_result['valid']:
                issues.extend(validation_result['issues'])

        # 检查supervision_records字段
        if 'supervision_records' not in case_data:
            issues.append("缺少 supervision_records 字段")
        elif not isinstance(case_data['supervision_records'], list):
            issues.append("supervision_records 必须是数组类型")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'case_id': case_data.get('case_id', 'UNKNOWN')
        }

    except Exception as e:
        return {
            'valid': False,
            'issues': [f"文件读取错误: {str(e)}"],
            'case_id': 'ERROR'
        }


def main():
    """主函数"""
    print("案例数据v2.0结构验证工具")
    print("=" * 60)

    # 初始化流派管理器
    manager = ApproachesManager()

    # 查找所有案例文件
    processed_dir = project_root / "data" / "cases" / "processed"
    active_dir = project_root / "data" / "cases" / "active"

    all_cases = []
    if processed_dir.exists():
        all_cases.extend(list(processed_dir.glob("*.json")))
    if active_dir.exists():
        all_cases.extend(list(active_dir.glob("*.json")))

    if not all_cases:
        print("未找到案例文件")
        return 0

    print(f"找到 {len(all_cases)} 个案例文件\n")

    valid_count = 0
    invalid_count = 0
    skipped_count = 0

    for case_file in all_cases:
        print(f"验证: {case_file.name}")
        result = validate_case_file(case_file, manager)

        if result.get('skipped'):
            print(f"  [跳过] {result['case_id']} - {result.get('reason', '未知原因')}")
            skipped_count += 1
        elif result['valid']:
            print(f"  [通过] {result['case_id']}")
            valid_count += 1
        else:
            print(f"  [失败] {result['case_id']}")
            for issue in result['issues']:
                print(f"    - {issue}")
            invalid_count += 1
        print()

    # 总结
    print("=" * 60)
    print(f"验证完成！")
    print(f"  通过: {valid_count} 个")
    print(f"  跳过: {skipped_count} 个")
    print(f"  失败: {invalid_count} 个")

    if invalid_count == 0:
        print("\n[成功] 所有案例数据结构符合v2.0规范")
        return 0
    else:
        print(f"\n[警告] {invalid_count} 个案例需要修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
