#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理心理咨询案例脚本
功能：扫描指定目录，批量处理所有 Word 文档案例
排除规则：跳过督导文件（文件名包含"督导"）
"""

import os
import sys
import json
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ---- Windows GBK 兼容处理 ----
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def sp(*args, **kwargs):
    """安全 print：自动处理编码问题"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = []
        for a in args:
            s = str(a)
            safe_args.append(s.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
        print(*safe_args, **kwargs)

try:
    from docx import Document
except ImportError:
    sp("[ERR] 缺少依赖：python-docx，请运行：pip install python-docx")
    sys.exit(1)

try:
    import requests
except ImportError:
    sp("[ERR] 缺少依赖：requests，请运行：pip install requests")
    sys.exit(1)


# ==================== 配置 ====================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CASES_ORIGINAL = DATA_DIR / "cases" / "original"
CASES_PROCESSED = DATA_DIR / "cases" / "processed"
INDEX_DIR = DATA_DIR / "index"

# CatKingAI API 配置
CATKINGAI_ENDPOINT = "https://catkingai.com/v1/messages"
CATKINGAI_API_KEY = os.getenv("CATKINGAI_API_KEY", "")

# 排除规则
EXCLUDE_KEYWORDS = ["督导", "supervision", "Supervision"]


# ==================== 工具函数 ====================

def ensure_directories():
    """确保所有必需的目录存在"""
    for dir_path in [CASES_ORIGINAL, CASES_PROCESSED, INDEX_DIR, DATA_DIR / "cases" / "supervision"]:
        dir_path.mkdir(parents=True, exist_ok=True)


def should_skip_file(filename: str) -> bool:
    """判断是否应该跳过该文件"""
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in filename:
            return True
    return False


def extract_date_from_filename(filename: str) -> Optional[str]:
    """从文件名中提取日期（格式：YYYYMMDD）"""
    # 匹配 20260616-xxx.docx 或 20260616_xxx.docx
    match = re.search(r'(\d{8})', filename)
    if match:
        return match.group(1)
    return None


def generate_case_id(date_str: str) -> str:
    """生成案例编号：C + YYYYMMDD（从文件名提取） + 3位序号"""
    prefix = f"C{date_str}"

    # 查找该日期已有的最大序号
    existing_cases = list(CASES_PROCESSED.glob(f"{prefix}*.json"))

    if not existing_cases:
        return f"{prefix}001"

    # 提取序号并找到最大值
    max_seq = 0
    for case_file in existing_cases:
        case_id = case_file.stem
        try:
            seq = int(case_id[-3:])
            max_seq = max(max_seq, seq)
        except ValueError:
            continue

    new_seq = max_seq + 1
    return f"{prefix}{new_seq:03d}"


def read_word_document(file_path: str) -> str:
    """读取 Word 文档内容"""
    try:
        doc = Document(file_path)
        full_text = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text.append(text)

        return "\n".join(full_text)

    except Exception as e:
        raise Exception(f"读取 Word 文档失败：{e}")


def call_ai_analysis(content: str, case_id: str) -> Dict:
    """调用 AI 进行案例分析"""

    prompt = f"""你是一位资深的心理咨询督导师，擅长大观学派希望热线技术。请分析以下接访记录：

【案例内容】
{content}

【分析要求】
请从以下维度进行分析，并以 JSON 格式返回：

1. **基本信息**（basic_info）：
   - 代号（来访者昵称/代号）
   - 性别
   - 年龄（含人群分类：青少年/中年/老年等）
   - 职业
   - 婚姻状况

2. **接访信息**（session_info）：
   - 接访日期（从案例内容中提取，格式：YYYY-MM-DD）
   - 接访次数
   - 通话时长
   - 咨询渠道（电话/线上/面对面等）

3. **关系标签**（relation_tags）：识别涉及的关系类型，使用"大类-子类-细节"格式
   例如："家庭关系-亲子关系-青少年-重男轻女"

4. **精神症状标签**（symptom_tags）：识别精神症状，使用"大类-子类-细节"格式
   例如："行为问题-自杀风险-自杀计划"

5. **危机等级**（crisis_level）：S/L/M/C/Z
   - S: 自杀风险（有明确计划/手段/遗书/失联）
   - L: 生命危险（他杀风险/严重自伤/精神病性症状）
   - M: 中度危机（抑郁/焦虑影响功能/创伤急性期）
   - C: 慢性困扰（长期关系问题/自我成长议题）
   - Z: 正常范围（偶发情绪波动/一般性困惑）

6. **危机判据**（crisis_evidence）：判断危机等级的依据

7. **关键词**（keywords）：提取5-15个核心关键词

8. **使用的技术**（techniques_used）：识别咨询师使用的具体技术

9. **案例摘要**（summary）：200字以内，概括案例核心

10. **咨询师优势**（strengths）：3-5条，具体指出做得好的地方

11. **改进建议**（improvements）：3-5条，建设性建议

12. **下次咨询建议**（recommended_followup）：后续跟进建议

严格按照 JSON 格式输出，不要有其他文字。"""

    sp(f"[AI] 正在调用 AI 分析案例 {case_id}...")

    if not CATKINGAI_API_KEY:
        sp("[WARN] 未配置 CATKINGAI_API_KEY，使用 mock 数据")
        return {
            "basic_info": {},
            "session_info": {},
            "relation_tags": [],
            "symptom_tags": [],
            "crisis_level": "",
            "crisis_evidence": "需要 AI 实际分析",
            "keywords": [],
            "techniques_used": [],
            "summary": "需要 AI 实际分析",
            "strengths": ["需要 AI 实际分析"],
            "improvements": ["需要 AI 实际分析"],
            "recommended_followup": "需要 AI 实际分析"
        }

    try:
        response = requests.post(
            CATKINGAI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {CATKINGAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-opus-4-8",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 4000
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            text = result.get("content", [{}])[0].get("text", "")
            # 尝试提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
            return None
        else:
            sp(f"[ERR] API 调用失败：{response.status_code}")
            return None

    except Exception as e:
        sp(f"[ERR] AI 分析出错：{e}")
        return None


def create_case_json(case_id: str, source_file: str, content: str, ai_analysis: Dict) -> Dict:
    """创建案例 JSON 结构"""
    return {
        "case_id": case_id,
        "source_file": source_file,
        "created_at": datetime.now().isoformat(),
        "basic_info": ai_analysis.get("basic_info", {
            "代号": "",
            "性别": "",
            "年龄": "",
            "职业": "",
            "婚姻状况": ""
        }),
        "session_info": ai_analysis.get("session_info", {
            "接访日期": "",
            "接访次数": "",
            "通话时长": "",
            "咨询渠道": ""
        }),
        "tags": {
            "relation": ai_analysis.get("relation_tags", []),
            "symptom": ai_analysis.get("symptom_tags", [])
        },
        "crisis_level": ai_analysis.get("crisis_level", ""),
        "crisis_evidence": ai_analysis.get("crisis_evidence", ""),
        "keywords": ai_analysis.get("keywords", []),
        "techniques_used": ai_analysis.get("techniques_used", []),
        "dialogue": content,
        "ai_analysis": {
            "summary": ai_analysis.get("summary", ""),
            "strengths": ai_analysis.get("strengths", []),
            "improvements": ai_analysis.get("improvements", []),
            "recommended_followup": ai_analysis.get("recommended_followup", "")
        },
        "supervision_records": []
    }


def update_index(case_id: str, case_data: Dict):
    """更新四大索引"""
    # 1. 关系标签索引
    relation_file = INDEX_DIR / "relation_tags.json"
    relation_index = json.loads(relation_file.read_text(encoding='utf-8')) if relation_file.exists() else {}
    for tag in case_data["tags"]["relation"]:
        relation_index.setdefault(tag, [])
        if case_id not in relation_index[tag]:
            relation_index[tag].append(case_id)
    relation_file.write_text(json.dumps(relation_index, ensure_ascii=False, indent=2), encoding='utf-8')

    # 2. 精神症状标签索引
    symptom_file = INDEX_DIR / "symptom_tags.json"
    symptom_index = json.loads(symptom_file.read_text(encoding='utf-8')) if symptom_file.exists() else {}
    for tag in case_data["tags"]["symptom"]:
        symptom_index.setdefault(tag, [])
        if case_id not in symptom_index[tag]:
            symptom_index[tag].append(case_id)
    symptom_file.write_text(json.dumps(symptom_index, ensure_ascii=False, indent=2), encoding='utf-8')

    # 3. 危机等级索引
    crisis_file = INDEX_DIR / "crisis_levels.json"
    crisis_index = json.loads(crisis_file.read_text(encoding='utf-8')) if crisis_file.exists() else {}
    level = case_data["crisis_level"]
    if level:
        crisis_index.setdefault(level, [])
        if case_id not in crisis_index[level]:
            crisis_index[level].append(case_id)
    # 确保所有等级都存在
    for lvl in ["S", "L", "M", "C", "Z"]:
        crisis_index.setdefault(lvl, [])
    crisis_file.write_text(json.dumps(crisis_index, ensure_ascii=False, indent=2), encoding='utf-8')

    # 4. 关键词索引
    keyword_file = INDEX_DIR / "keywords.json"
    keyword_index = json.loads(keyword_file.read_text(encoding='utf-8')) if keyword_file.exists() else {}
    for kw in case_data["keywords"]:
        keyword_index.setdefault(kw, [])
        if case_id not in keyword_index[kw]:
            keyword_index[kw].append(case_id)
    keyword_file.write_text(json.dumps(keyword_index, ensure_ascii=False, indent=2), encoding='utf-8')

    sp("[OK] 索引更新完成")


def process_single_case(source_file_path: str, date_str: str) -> Optional[str]:
    """处理单个案例，返回案例编号"""

    sp("")
    sp("=" * 60)
    sp(f"[CASE] 开始处理：{Path(source_file_path).name}")
    sp("=" * 60)

    # 1. 生成案例编号（使用文件名日期）
    case_id = generate_case_id(date_str)
    sp(f"[ID] 案例编号：{case_id}（日期来源：文件名 {date_str}）")

    # 2. 读取 Word 文档
    sp("[READ] 读取文档...")
    try:
        content = read_word_document(source_file_path)
        sp(f"[OK] 读取成功（{len(content)} 字符）")
    except Exception as e:
        sp(f"[ERR] {e}")
        return None

    # 3. 保存原始文档
    original_dest = CASES_ORIGINAL / f"{date_str}-{Path(source_file_path).name}"
    shutil.copy2(source_file_path, original_dest)
    sp(f"[SAVE] 原始文档 -> {original_dest.name}")

    # 4. AI 分析
    ai_analysis = call_ai_analysis(content, case_id)
    if not ai_analysis:
        ai_analysis = {
            "basic_info": {},
            "session_info": {},
            "relation_tags": [], "symptom_tags": [],
            "crisis_level": "", "crisis_evidence": "",
            "keywords": [], "techniques_used": [],
            "summary": "", "strengths": [], "improvements": [],
            "recommended_followup": ""
        }

    # 5. 生成 JSON
    case_data = create_case_json(case_id, str(original_dest), content, ai_analysis)

    # 6. 保存 JSON
    processed_file = CASES_PROCESSED / f"{case_id}.json"
    processed_file.write_text(json.dumps(case_data, ensure_ascii=False, indent=2), encoding='utf-8')
    sp(f"[SAVE] 处理结果 -> {processed_file.name}")

    # 7. 更新索引
    update_index(case_id, case_data)

    # 8. 完成报告
    sp(f"[DONE] ✅ {case_id} 处理完成")
    sp(f"  危机等级：{case_data['crisis_level'] or '未判断'}")
    sp(f"  关键词：{', '.join(case_data['keywords'][:5]) or '无'}")
    sp("")

    return case_id


def batch_process(source_dir: str, dry_run: bool = False):
    """批量处理指定目录下的所有案例"""

    sp("")
    sp("=" * 70)
    sp("  批量案例处理工具")
    sp("=" * 70)
    sp(f"源目录：{source_dir}")
    sp(f"模式：{'预览模式（不实际处理）' if dry_run else '实际处理'}")
    sp("")

    # 确保目录存在
    ensure_directories()

    # 扫描文件
    source_path = Path(source_dir)
    if not source_path.exists():
        sp(f"[ERR] 目录不存在：{source_dir}")
        return

    # 查找所有 .docx 文件
    all_files = list(source_path.glob("*.docx"))
    sp(f"[SCAN] 找到 {len(all_files)} 个 .docx 文件")
    sp("")

    # 过滤文件
    to_process = []
    skipped = []

    for file_path in all_files:
        filename = file_path.name

        # 跳过临时文件
        if filename.startswith("~$"):
            continue

        # 检查排除规则
        if should_skip_file(filename):
            skipped.append((filename, "包含排除关键词"))
            continue

        # 提取日期
        date_str = extract_date_from_filename(filename)
        if not date_str:
            skipped.append((filename, "文件名中未找到日期（格式：YYYYMMDD）"))
            continue

        to_process.append((file_path, date_str))

    # 按日期和文件名排序，确保处理顺序一致
    to_process.sort(key=lambda x: (x[1], x[0].name))

    # 显示统计
    sp(f"[FILTER] 筛选结果：")
    sp(f"  - 待处理：{len(to_process)} 个")
    sp(f"  - 已跳过：{len(skipped)} 个")
    sp("")

    if skipped:
        sp("[SKIP] 跳过的文件：")
        for filename, reason in skipped:
            sp(f"  ❌ {filename} ({reason})")
        sp("")

    if not to_process:
        sp("[INFO] 没有需要处理的文件")
        return

    if dry_run:
        sp("[DRY-RUN] 预览待处理文件：")
        # 在预览模式下，模拟序号递增
        date_counters = {}
        for file_path, date_str in to_process:
            # 获取该日期已有的案例数
            prefix = f"C{date_str}"
            existing_cases = list(CASES_PROCESSED.glob(f"{prefix}*.json"))
            base_count = len(existing_cases)

            # 加上当前日期在本次批处理中的计数
            date_counters[date_str] = date_counters.get(date_str, 0) + 1
            seq = base_count + date_counters[date_str]
            case_id = f"{prefix}{seq:03d}"

            sp(f"  📄 {file_path.name} → {case_id}")
        sp("")
        sp(f"[INFO] 预览完成。使用 --run 参数执行实际处理")
        return

    # 实际处理
    sp("[PROCESS] 开始批量处理...")
    sp("")

    success_count = 0
    failed_count = 0
    results = []

    for idx, (file_path, date_str) in enumerate(to_process, 1):
        sp(f"进度：{idx}/{len(to_process)}")
        case_id = process_single_case(str(file_path), date_str)

        if case_id:
            success_count += 1
            results.append((file_path.name, case_id, "成功"))
        else:
            failed_count += 1
            results.append((file_path.name, None, "失败"))

    # 最终报告
    sp("")
    sp("=" * 70)
    sp("  批量处理完成")
    sp("=" * 70)
    sp(f"总计：{len(to_process)} 个文件")
    sp(f"成功：{success_count} 个")
    sp(f"失败：{failed_count} 个")
    sp("")

    if results:
        sp("处理结果：")
        for filename, case_id, status in results:
            if status == "成功":
                sp(f"  ✅ {filename} → {case_id}")
            else:
                sp(f"  ❌ {filename} → {status}")

    sp("")
    sp("[TIP] 下一步：")
    sp("  1. 检查处理结果：data/cases/processed/")
    sp("  2. 查看索引文件：data/index/")
    sp("  3. 生成案例库HTML：python src/generate_case_library.py")
    sp("")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="批量处理心理咨询案例")
    parser.add_argument("source_dir", help="源文件目录路径")
    parser.add_argument("--run", action="store_true", help="实际执行处理（默认为预览模式）")

    args = parser.parse_args()

    batch_process(args.source_dir, dry_run=not args.run)


if __name__ == "__main__":
    main()
