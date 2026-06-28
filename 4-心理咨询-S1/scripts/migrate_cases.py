# -*- coding: utf-8 -*-
"""
案例迁移脚本：将旧格式（processed）转换为新格式（active）
"""
import json
import os
from datetime import datetime

# 路径配置
PROCESSED_DIR = r"D:\AI-项目\4-心理咨询-S1\data\cases\processed"
ACTIVE_DIR = r"D:\AI-项目\4-心理咨询-S1\data\cases\active"

# 案例ID映射（旧ID → 新ID）
CASE_ID_MAPPING = {
    "C20260616001": "L003",  # 善良的小女孩
    "C20260620001": "L004",  # 高二女生幻听（L001已存在，改为L004）
    "C20260620002": "L002",  # 女老板
}

def parse_age(age_str):
    """从年龄字符串中提取年龄数字"""
    if isinstance(age_str, int):
        return age_str
    # "16-17岁（高二）" → 16
    # "40-50岁（更年期）" → 45
    # "约14-16岁（青少年）" → 15
    import re
    match = re.search(r'(\d+)', age_str)
    if match:
        return int(match.group(1))
    return None

def estimate_birth_date(age, reference_date):
    """根据年龄估算出生日期"""
    if not age:
        return None
    ref_year = datetime.strptime(reference_date, "%Y-%m-%d").year if isinstance(reference_date, str) else reference_date.year
    birth_year = ref_year - age
    return f"{birth_year}-01-01"  # 使用1月1日作为默认

def extract_chief_complaint(dialogue):
    """从对话中提取主诉（简化版，取前100字）"""
    # 尝试找到描述性内容
    lines = dialogue.split('\n')
    for line in lines:
        if len(line) > 20 and not line.startswith('1、') and not line.startswith('2、'):
            # 清理时间戳等
            cleaned = line.strip()
            if len(cleaned) > 30:
                return cleaned[:100] + "..." if len(cleaned) > 100 else cleaned
    return dialogue[:100] + "..."

def convert_case(old_case):
    """转换单个案例"""
    old_id = old_case['case_id']
    new_id = CASE_ID_MAPPING.get(old_id, old_id)

    # 解析基本信息
    basic = old_case['basic_info']
    session = old_case['session_info']
    analysis = old_case['analyses']['daguanpai']

    # 解析年龄和出生日期
    age = parse_age(basic.get('年龄', ''))
    session_date = session.get('接访日期', datetime.now().strftime("%Y-%m-%d"))
    birth_date = estimate_birth_date(age, session_date)

    # 提取主诉
    chief_complaint = extract_chief_complaint(old_case['dialogue'])

    # 解析会谈时长
    duration_str = session.get('通话时长', '0分钟')
    duration = int(''.join(filter(str.isdigit, duration_str))) if duration_str else 0

    # 构建新格式
    new_case = {
        "case_id": new_id,
        "status": "active",
        "created_at": old_case.get('created_at', datetime.now().isoformat()),
        "last_updated": old_case.get('last_modified', datetime.now().isoformat()),
        "closed_at": None,
        "closure_reason": None,

        "static_info": {
            "代号": new_id,
            "性别": basic.get('性别', ''),
            "出生日期": birth_date,
            "年龄": age,
            "职业": basic.get('职业', ''),
            "婚姻状况": basic.get('婚姻状况', ''),
            "性取向": "",
            "宗教信仰": "",
            "联系方式": "",
            "主诉": chief_complaint,
            "家庭结构": {
                "父亲情况": "",
                "母亲情况": "",
                "父母关系": "",
                "兄弟姐妹": "",
                "配偶子女情况": ""
            },
            "既往史": {
                "有既往咨询史": False,
                "有精神科就诊史": False,
                "既往史详情": ""
            }
        },

        "dynamic_info": {
            "咨询目标": {
                "current": "待更新",
                "history": [
                    {
                        "value": "待更新",
                        "session": 1,
                        "changed_at": session_date + "T00:00:00",
                        "reason": "首次设定"
                    }
                ]
            },
            "用药情况": {
                "current": "待更新",
                "history": [
                    {
                        "value": "待更新",
                        "session": 1,
                        "changed_at": session_date + "T00:00:00",
                        "reason": "首次记录"
                    }
                ]
            },
            "紧急联系人": "",
            "紧急联系电话": "",
            "来访备注": ""
        },

        "sessions": [
            {
                "session_number": 1,
                "date": session_date,
                "咨询师": "待补充",
                "duration": duration,
                "previous_summary": None,
                "dialogue": old_case['dialogue'],
                "summary": analysis.get('ai_analysis', {}).get('summary', ''),
                "relation_tags": analysis.get('tags', {}).get('relation', []),
                "symptom_tags": analysis.get('tags', {}).get('symptom', []),
                "crisis_assessment": {
                    "level": analysis.get('crisis_level', ''),
                    "evidence": analysis.get('crisis_evidence', '')
                },
                "keywords": analysis.get('keywords', []),
                "techniques": analysis.get('techniques_used', []),
                "ai_analysis": {
                    "summary": analysis.get('ai_analysis', {}).get('summary', ''),
                    "strengths": analysis.get('ai_analysis', {}).get('strengths', []),
                    "improvements": analysis.get('ai_analysis', {}).get('improvements', []),
                    "next_suggestion": "\n".join(analysis.get('ai_analysis', {}).get('recommended_followup', []))
                },
                "supervision": {
                    "状态": "未督导",
                    "督导师": "",
                    "督导日期": "",
                    "督导要点": "",
                    "督导建议": ""
                },
                "created_at": session_date + "T00:00:00",
                "updated_at": session_date + "T00:00:00"
            }
        ],

        "closure": {
            "closed_at": None,
            "closed_by": None,
            "closure_reason": None,
            "closure_summary": None,
            "total_sessions": 0
        }
    }

    return new_case

def main():
    """主函数"""
    print("开始迁移案例...")

    # 确保目标目录存在
    os.makedirs(ACTIVE_DIR, exist_ok=True)

    migrated_count = 0

    for old_id, new_id in CASE_ID_MAPPING.items():
        old_file = os.path.join(PROCESSED_DIR, f"{old_id}.json")
        new_file = os.path.join(ACTIVE_DIR, f"{new_id}.json")

        if not os.path.exists(old_file):
            print(f"[WARN] 文件不存在：{old_file}")
            continue

        if os.path.exists(new_file):
            print(f"[WARN] 目标文件已存在，跳过：{new_file}")
            continue

        # 读取旧案例
        with open(old_file, 'r', encoding='utf-8') as f:
            old_case = json.load(f)

        # 转换
        new_case = convert_case(old_case)

        # 保存
        with open(new_file, 'w', encoding='utf-8') as f:
            json.dump(new_case, f, ensure_ascii=False, indent=2)

        print(f"[OK] 迁移成功：{old_id} -> {new_id}")
        migrated_count += 1

    print(f"\n迁移完成！共迁移 {migrated_count} 个案例")

if __name__ == "__main__":
    main()
