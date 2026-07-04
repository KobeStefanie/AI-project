"""
为案例JSON文件添加中性字段：case_summary 和 case_tags
"""
import json
import os
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "cases" / "processed"

def add_neutral_fields(case_file):
    """为案例添加中性的 case_summary 和 case_tags 字段"""
    with open(case_file, 'r', encoding='utf-8') as f:
        case_data = json.load(f)

    # 如果已经有这些字段，跳过
    if 'case_summary' in case_data and 'case_tags' in case_data:
        print(f"[OK] {case_data['case_id']} 已有中性字段，跳过")
        return

    # 从第一个流派的数据中提取
    analyses = case_data.get('analyses', {})
    if not analyses:
        print(f"[SKIP] {case_data['case_id']} 没有分析数据，跳过")
        return

    # 获取第一个流派的数据
    first_approach = list(analyses.values())[0]

    # 提取 summary（从 ai_analysis.summary）
    case_summary = first_approach.get('ai_analysis', {}).get('summary', '')

    # 提取 tags
    case_tags = first_approach.get('tags', {})

    # 插入到 dialogue 之后
    new_case_data = {}
    for key, value in case_data.items():
        new_case_data[key] = value
        if key == 'dialogue':
            new_case_data['case_summary'] = case_summary
            new_case_data['case_tags'] = case_tags

    # 保存
    with open(case_file, 'w', encoding='utf-8') as f:
        json.dump(new_case_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] {case_data['case_id']} 已添加中性字段")

def main():
    print("=" * 60)
    print("  添加中性字段工具")
    print("=" * 60)

    # 遍历所有processed案例
    case_files = list(PROCESSED_DIR.glob("*.json"))

    if not case_files:
        print("未找到案例文件")
        return

    for case_file in case_files:
        add_neutral_fields(case_file)

    print("\n" + "=" * 60)
    print(f"  完成！共处理 {len(case_files)} 个案例")
    print("=" * 60)

if __name__ == "__main__":
    main()
