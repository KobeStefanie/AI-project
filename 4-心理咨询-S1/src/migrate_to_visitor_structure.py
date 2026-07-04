#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移工具：将现有案例数据迁移到来访者为中心的新结构
"""

import json
import os
import sys
import io
from pathlib import Path
from datetime import datetime
import shutil

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置
OLD_CASES_DIR = project_root / 'data' / 'cases' / 'processed'
NEW_VISITORS_DIR = project_root / 'data' / 'visitors'


def extract_visitor_id_from_case_id(case_id):
    """
    从案例ID提取来访者ID
    案例ID格式：C20260616001
    来访者ID格式：V20260616001（假设同一天的案例是同一来访者的不同来访）

    这里采用简单策略：每个案例对应一个独立的来访者
    """
    # 将 C 替换为 V
    return case_id.replace('C', 'V')


def parse_case_title(case_title):
    """
    解析案例标题，提取风险类型和人群
    格式：[风险类型]-[人群]-案例ID-标题
    例如：[自杀风险]-[青少年]-C20260616001-善良女孩的求助
    """
    parts = case_title.split('-')
    if len(parts) >= 4:
        risk_type = parts[0].strip('[]')
        population = parts[1].strip('[]')
        return risk_type, population
    return None, None


def create_visitor_profile(case_data, visitor_id, visit_number=1):
    """
    从案例数据创建来访者档案
    """
    case_title = case_data.get('case_title', '')
    risk_type, population = parse_case_title(case_title)

    # 从案例ID提取日期
    case_id = case_data.get('case_id', '')
    date_str = case_id[1:9]  # 提取 YYYYMMDD
    visit_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    # 提取基本信息
    case_summary = case_data.get('case_summary', '')

    # 从案例标题提取姓名（如果有）
    name_parts = case_title.split('-')
    visitor_name = name_parts[-1] if len(name_parts) > 0 else '未命名来访者'

    # 读取原始案例的 basic_info（首次接访的基本信息）
    original_basic_info = case_data.get('basic_info', {})

    # 读取会话信息
    session_info = case_data.get('session_info', {})

    # 读取来访主诉和咨询目标（如果有）
    intake_info = case_data.get('intake_info', {})
    chief_complaint = intake_info.get('主诉', case_summary)  # 如果没有主诉，使用案例摘要
    counseling_goal = intake_info.get('咨询目标', '')

    # 读取家庭结构
    family_structure = case_data.get('家庭结构', {})

    # 使用原始案例的基本信息，如果没有则使用默认值
    profile = {
        "visitor_id": visitor_id,
        "basic_info": {
            "name": original_basic_info.get('代号', visitor_name),
            "age": original_basic_info.get('年龄', '未知'),
            "gender": original_basic_info.get('性别', '未知'),
            "occupation": original_basic_info.get('职业', '未知'),
            "marital_status": original_basic_info.get('婚姻状况', '未知'),
            "sexual_orientation": original_basic_info.get('性取向', ''),
            "religion": original_basic_info.get('宗教信仰', ''),
            "emergency_contact": original_basic_info.get('紧急联系人', ''),
            "contact_phone": original_basic_info.get('联系电话', ''),
            "background": case_summary,
            "initial_complaint": chief_complaint,
            "initial_assessment": f"存在{risk_type}" if risk_type else "待评估",
            "counseling_goal": counseling_goal,
            "medication": original_basic_info.get('用药情况', ''),
            "notes": original_basic_info.get('来访备注', '')
        },
        "family_structure": {
            "father": family_structure.get('父亲情况', ''),
            "mother": family_structure.get('母亲情况', ''),
            "parents_relationship": family_structure.get('父母关系', ''),
            "siblings": family_structure.get('兄弟姐妹', ''),
            "spouse_children": family_structure.get('配偶子女情况', '')
        },
        "session_info": {
            "first_session_date": session_info.get('接访日期', visit_date),
            "channel": session_info.get('咨询渠道', '未知'),
            "counselor": session_info.get('咨询师姓名', '咨询师A')
        },
        "overall_progress": {
            "symptom_trend": [
                {
                    "visit_number": visit_number,
                    "date": visit_date,
                    "severity": 7 if risk_type == "自杀风险" else 5,  # 初始严重程度
                    "description": f"{risk_type}，需要持续关注" if risk_type else "初次评估"
                }
            ],
            "risk_trend": [
                {
                    "visit_number": visit_number,
                    "date": visit_date,
                    "risk_level": "高" if risk_type == "自杀风险" else "中",
                    "risk_type": risk_type if risk_type else "待评估"
                }
            ],
            "treatment_progress": "初次来访，建立咨访关系阶段",
            "therapeutic_relationship": "初步建立信任"
        },
        "visit_history": [
            {
                "visit_number": visit_number,
                "visit_id": f"visit_{visit_number:03d}",
                "date": visit_date,
                "counselor": "咨询师A",  # 默认值
                "duration": 50,  # 默认50分钟
                "main_issue": risk_type if risk_type else "情绪困扰",
                "risk_level": "高" if risk_type == "自杀风险" else "中"
            }
        ],
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "total_visits": 1
        }
    }

    return profile


def create_visit_record(case_data, visitor_id, visit_number=1):
    """
    从案例数据创建来访记录
    """
    case_id = case_data.get('case_id', '')
    date_str = case_id[1:9]
    visit_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

    case_title = case_data.get('case_title', '')
    risk_type, _ = parse_case_title(case_title)

    # 转换流派分析数据：从 analyses 转换为 approach_analyses
    # 原始格式: {"daguanpai": {"ai_analysis": {...}}}
    # 目标格式: {"大观派": {"conceptualization": "...", "intervention_suggestions": "...", "key_points": [...]}}
    approach_analyses = {}
    analyses = case_data.get('analyses', {})

    for approach_key, approach_data in analyses.items():
        # 映射流派名称
        approach_name_map = {
            'daguanpai': '大观派',
            'cbt': '认知行为疗法',
            'psychodynamic': '精神动力学',
            'humanistic': '人本主义'
        }
        approach_name = approach_name_map.get(approach_key, approach_key)

        # 提取AI分析内容
        ai_analysis = approach_data.get('ai_analysis', {})

        # 构建流派分析内容
        approach_analyses[approach_name] = {
            "conceptualization": ai_analysis.get('summary', ''),
            "intervention_suggestions": '\n'.join(ai_analysis.get('recommended_followup', [])) if isinstance(ai_analysis.get('recommended_followup'), list) else ai_analysis.get('recommended_followup', ''),
            "key_points": ai_analysis.get('strengths', []) + ai_analysis.get('improvements', [])
        }

    visit_record = {
        "visit_id": f"visit_{visit_number:03d}",
        "visitor_id": visitor_id,
        "visit_number": visit_number,
        "date": visit_date,
        "visit_summary": {
            "complaint": "详见案例概要和咨询师复盘",
            "outcome": "建立咨访关系，完成初步评估",
            "homework": "记录情绪日记",
            "next_step": "下次继续深入探讨",
            "counselor": "咨询师A",
            "duration": 50,
            "risk_assessment": {
                "risk_level": "高" if risk_type == "自杀风险" else "中",
                "risk_type": risk_type if risk_type else "待评估",
                "risk_factors": ["情绪波动", "人际关系困难"] if risk_type else []
            },
            "symptom_change": "持平"  # 第一次来访，无法对比
        },
        "case_data": {
            "case_id": case_id,
            "case_summary": case_data.get('case_summary', ''),
            "case_tags": case_data.get('case_tags', {}),
            "counselor_review": case_data.get('dialogue', ''),  # 使用dialogue字段作为复盘内容
            "recordings": case_data.get('recordings', []),
            "transcript": case_data.get('transcript', []),
            "approach_analyses": approach_analyses,
            "supervision_records": case_data.get('supervision_records', [])  # 保留督导记录
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    }

    return visit_record


def migrate_case_to_visitor(case_file):
    """
    迁移单个案例到来访者结构
    """
    print(f"\n处理案例: {case_file.name}")

    # 读取案例数据
    with open(case_file, 'r', encoding='utf-8') as f:
        case_data = json.load(f)

    case_id = case_data.get('case_id', case_file.stem)
    visitor_id = extract_visitor_id_from_case_id(case_id)

    print(f"  案例ID: {case_id}")
    print(f"  来访者ID: {visitor_id}")

    # 创建来访者目录
    visitor_dir = NEW_VISITORS_DIR / visitor_id
    visits_dir = visitor_dir / 'visits'
    visits_dir.mkdir(parents=True, exist_ok=True)

    # 创建来访者档案
    profile = create_visitor_profile(case_data, visitor_id, visit_number=1)
    profile_file = visitor_dir / 'profile.json'
    with open(profile_file, 'w', encoding='utf-8') as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 创建档案: {profile_file}")

    # 创建来访记录
    visit_record = create_visit_record(case_data, visitor_id, visit_number=1)
    visit_file = visits_dir / 'visit_001.json'
    with open(visit_file, 'w', encoding='utf-8') as f:
        json.dump(visit_record, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 创建来访记录: {visit_file}")

    return visitor_id


def main():
    """
    主函数：迁移所有案例
    """
    print("=" * 60)
    print("数据迁移工具：案例 → 来访者为中心")
    print("=" * 60)

    # 检查源目录
    if not OLD_CASES_DIR.exists():
        print(f"错误: 找不到案例目录 {OLD_CASES_DIR}")
        return

    # 创建目标目录
    NEW_VISITORS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n源目录: {OLD_CASES_DIR}")
    print(f"目标目录: {NEW_VISITORS_DIR}")

    # 获取所有案例文件
    case_files = list(OLD_CASES_DIR.glob('*.json'))
    print(f"\n找到 {len(case_files)} 个案例文件")

    if not case_files:
        print("没有找到案例文件，退出")
        return

    # 迁移每个案例
    migrated_visitors = []
    for case_file in case_files:
        try:
            visitor_id = migrate_case_to_visitor(case_file)
            migrated_visitors.append(visitor_id)
        except Exception as e:
            print(f"  ✗ 迁移失败: {e}")
            import traceback
            traceback.print_exc()

    # 总结
    print("\n" + "=" * 60)
    print(f"迁移完成! 共创建 {len(migrated_visitors)} 个来访者档案")
    print("=" * 60)
    print("\n来访者列表:")
    for visitor_id in migrated_visitors:
        visitor_dir = NEW_VISITORS_DIR / visitor_id
        print(f"  - {visitor_id}: {visitor_dir}")

    print("\n下一步:")
    print("  1. 检查生成的 profile.json 和 visit_001.json")
    print("  2. 手动完善基本信息（年龄、性别、职业等）")
    print("  3. 运行生成器生成新的HTML页面")


if __name__ == '__main__':
    main()
