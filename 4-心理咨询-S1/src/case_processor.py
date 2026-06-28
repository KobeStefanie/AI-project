#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
心理咨询案例处理脚本
功能：读取 Word 文档 → 生成案例编号 → AI 分析 → 生成 JSON → 更新索引
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
CONFIG_DIR = DATA_DIR / "config"
TAGS_LIBRARY_FILE = CONFIG_DIR / "tags_library.json"

# CatKingAI API 配置
CATKINGAI_ENDPOINT = "https://catkingai.com/v1/messages"
CATKINGAI_API_KEY = os.getenv("CATKINGAI_API_KEY", "")

# 标签体系定义
RELATION_TAGS_STRUCTURE = {
    "家庭关系": {
        "亲子关系": ["青少年-叛逆期", "青少年-学业压力", "青少年-自伤行为", "成年子女-原生家庭创伤"],
        "夫妻关系": ["出轨", "性问题", "沟通障碍", "婆媳矛盾影响"],
        "婆媳关系": ["控制型婆婆", "界限模糊", "丈夫夹心"],
        "兄弟姐妹": ["竞争", "偏爱", "成年后疏离"]
    },
    "职场关系": {
        "上下级": ["霸凌", "性骚扰", "晋升冲突"],
        "同事": ["排挤", "竞争", "办公室政治"],
        "职业倦怠": ["过劳", "意义感丧失"]
    },
    "社交关系": {
        "友谊": ["背叛", "依赖", "社交恐惧"],
        "恋爱关系": ["失恋", "亲密恐惧", "依恋问题"]
    },
    "自我关系": {
        "自我认同": ["性别认同", "性取向", "价值观冲突"],
        "自我成长": ["生涯规划", "人生意义探索"]
    }
}

SYMPTOM_TAGS_STRUCTURE = {
    "情绪障碍": {
        "抑郁症": ["轻度", "中度", "重度", "复发"],
        "双相障碍": ["I型", "II型", "循环型"]
    },
    "焦虑障碍": {
        "广泛性焦虑": [],
        "恐惧症": ["社交恐惧", "特定恐惧", "广场恐惧"],
        "惊恐障碍": [],
        "强迫症": ["强迫思维", "强迫行为", "混合型"]
    },
    "创伤相关": {
        "PTSD": ["急性", "慢性", "延迟发作"],
        "复杂性创伤": [],
        "适应障碍": []
    },
    "行为问题": {
        "自杀风险": ["自杀意念", "自杀计划", "自杀未遂"],
        "自伤行为": ["非自杀性自伤", "边缘性人格自伤"],
        "物质滥用": ["酒精", "药物", "赌博", "网络成瘾"]
    },
    "人格障碍": {
        "边缘性人格": [],
        "回避性人格": [],
        "依赖性人格": []
    },
    "其他": ["睡眠障碍", "进食障碍", "躯体化障碍", "性功能障碍"]
}

CRISIS_LEVELS = {
    "S": "自杀风险 - 有明确计划/手段/遗书/失联",
    "L": "生命危险 - 他杀风险/严重自伤/精神病性症状",
    "M": "中度危机 - 抑郁/焦虑影响功能/创伤急性期",
    "C": "慢性困扰 - 长期关系问题/自我成长议题",
    "Z": "正常范围 - 偶发情绪波动/一般性困惑"
}

DAGUAN_TECHNIQUES = [
    "五法宝", "六变三托", "同步同理心", "逆向倒推", "非事件原则",
    "打包", "资源引入", "安全承诺", "危机等级判读", "求助动机评估"
]


# ==================== 工具函数 ====================

def ensure_directories():
    """确保所有必需的目录存在"""
    for dir_path in [CASES_ORIGINAL, CASES_PROCESSED, INDEX_DIR, CONFIG_DIR, DATA_DIR / "cases" / "supervision"]:
        dir_path.mkdir(parents=True, exist_ok=True)


def load_tags_library() -> Dict:
    """加载统一标签库"""
    try:
        if not TAGS_LIBRARY_FILE.exists():
            sp(f"[WARN] 标签库文件不存在：{TAGS_LIBRARY_FILE}")
            return {"relation_tags": {}, "symptom_tags": {}}

        with open(TAGS_LIBRARY_FILE, 'r', encoding='utf-8') as f:
            library = json.load(f)

        sp(f"[OK] 标签库加载成功")
        return library
    except Exception as e:
        sp(f"[ERR] 加载标签库失败：{e}")
        return {"relation_tags": {}, "symptom_tags": {}}


def get_all_valid_tags(tags_library: Dict) -> Dict[str, List[str]]:
    """从标签库中提取所有有效标签"""
    valid_relation_tags = []
    valid_symptom_tags = []

    # 提取关系标签
    for category_name, category_data in tags_library.get("relation_tags", {}).items():
        for sub_category, tags in category_data.get("children", {}).items():
            valid_relation_tags.extend(tags)

    # 提取症状标签
    for category_name, category_data in tags_library.get("symptom_tags", {}).items():
        children = category_data.get("children", [])
        if isinstance(children, list):
            valid_symptom_tags.extend(children)
        elif isinstance(children, dict):
            for sub_category, tags in children.items():
                if isinstance(tags, list):
                    valid_symptom_tags.extend(tags)

    return {
        "relation": valid_relation_tags,
        "symptom": valid_symptom_tags
    }


def validate_tags(ai_tags: Dict, tags_library: Dict) -> Dict:
    """验证 AI 提取的标签是否在统一标签库中"""
    valid_tags_dict = get_all_valid_tags(tags_library)

    validated_relation = []
    unvalidated_relation = []
    validated_symptom = []
    unvalidated_symptom = []

    # 验证关系标签
    for tag in ai_tags.get("relation_tags", []):
        if tag in valid_tags_dict["relation"]:
            validated_relation.append(tag)
        else:
            unvalidated_relation.append(tag)
            validated_relation.append(f"{tag}[需审核]")

    # 验证症状标签
    for tag in ai_tags.get("symptom_tags", []):
        if tag in valid_tags_dict["symptom"]:
            validated_symptom.append(tag)
        else:
            unvalidated_symptom.append(tag)
            validated_symptom.append(f"{tag}[需审核]")

    # 生成验证报告
    validation_report = {
        "validated": {
            "relation": [t for t in validated_relation if "[需审核]" not in t],
            "symptom": [t for t in validated_symptom if "[需审核]" not in t]
        },
        "unvalidated": {
            "relation": unvalidated_relation,
            "symptom": unvalidated_symptom
        },
        "has_issues": len(unvalidated_relation) > 0 or len(unvalidated_symptom) > 0
    }

    return {
        "validated_tags": {
            "relation": validated_relation,
            "symptom": validated_symptom
        },
        "validation_report": validation_report
    }


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


def generate_case_id() -> str:
    """生成案例编号：C + YYYYMMDD + 3位序号"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"C{today}"

    # 查找今天已有的最大序号
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


def call_ai_analysis(content: str, case_id: str) -> Dict:
    """调用 AI 进行案例分析"""

    prompt = f"""你是一位资深的心理咨询督导师，擅长大观学派希望热线技术。请分析以下接访记录：

【案例内容】
{content}

【分析要求】
请从以下维度进行分析，并以 JSON 格式返回：

1. **关系标签**（relation_tags）：识别涉及的关系类型
2. **精神症状标签**（symptom_tags）：识别精神症状
3. **危机等级**（crisis_level）：S/L/M/C/Z
4. **危机判据**（crisis_evidence）：判断依据
5. **关键词**（keywords）：提取5-10个核心关键词
6. **使用的技术**（techniques_used）：
7. **案例摘要**（summary）：200字以内
8. **咨询师优势**（strengths）：3-5条
9. **改进建议**（improvements）：3-5条
10. **下次咨询建议**（recommended_followup）

严格按照 JSON 格式输出，不要有其他文字。"""

    sp(f"[AI] 正在调用 AI 分析案例 {case_id}...")

    if not CATKINGAI_API_KEY:
        sp("[WARN] 未配置 CATKINGAI_API_KEY，使用 mock 数据")
        return {
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
            text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
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


def create_case_json(case_id: str, source_file: str, content: str, ai_analysis: Dict, validation_result: Dict) -> Dict:
    """创建案例 JSON 结构"""
    return {
        "case_id": case_id,
        "source_file": source_file,
        "created_at": datetime.now().isoformat(),
        "basic_info": {
            "代号": "",
            "性别": "",
            "年龄": "",
            "职业": "",
            "婚姻状况": ""
        },
        "session_info": {
            "接访日期": "",
            "接访次数": "",
            "通话时长": "",
            "咨询渠道": ""
        },
        "tags": validation_result["validated_tags"],
        "tags_validation": validation_result["validation_report"],
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
        "supervision_records": [],
        "audio_files": [],
        "transcripts": [],
        "supervision_files": []
    }


def upload_audio_files(case_id: str, case_data: Dict) -> Dict:
    """交互式上传录音文件"""
    sp("")
    sp("[录音上传] 是否要上传录音文件？(y/n): ", end='')
    choice = input().strip().lower()

    if choice != 'y':
        return case_data

    audio_dir = CASES_PROCESSED / case_id / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    while True:
        sp("请输入录音文件路径（留空结束）: ", end='')
        file_path = input().strip()

        if not file_path:
            break

        if not os.path.exists(file_path):
            sp(f"[ERR] 文件不存在：{file_path}")
            continue

        # 复制文件
        filename = os.path.basename(file_path)
        dest_path = audio_dir / filename
        shutil.copy2(file_path, dest_path)

        # 添加到案例数据
        case_data["audio_files"].append({
            "filename": filename,
            "uploaded_at": datetime.now().isoformat(),
            "file_size": os.path.getsize(dest_path)
        })

        sp(f"[OK] 录音已保存：{filename}")

    return case_data


def upload_transcripts(case_id: str, case_data: Dict) -> Dict:
    """交互式上传逐字稿"""
    sp("")
    sp("[逐字稿上传] 是否要添加逐字稿？(y/n): ", end='')
    choice = input().strip().lower()

    if choice != 'y':
        return case_data

    while True:
        sp("")
        sp("请选择输入方式：")
        sp("  1. 手动输入")
        sp("  2. 从文件读取")
        sp("  0. 结束")
        sp("选择: ", end='')
        choice = input().strip()

        if choice == '0':
            break

        transcript_content = ""
        audio_ref = ""

        if choice == '1':
            sp("请输入逐字稿标题: ", end='')
            title = input().strip()
            sp("请输入逐字稿内容（输入 EOF 结束）:")
            lines = []
            while True:
                line = input()
                if line.strip() == 'EOF':
                    break
                lines.append(line)
            transcript_content = "\n".join(lines)

        elif choice == '2':
            sp("请输入逐字稿文件路径: ", end='')
            file_path = input().strip()

            if not os.path.exists(file_path):
                sp(f"[ERR] 文件不存在：{file_path}")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                transcript_content = f.read()

            title = os.path.splitext(os.path.basename(file_path))[0]

        else:
            sp("[ERR] 无效选择")
            continue

        # 询问关联的录音文件
        if case_data["audio_files"]:
            sp("是否关联录音文件？(y/n): ", end='')
            if input().strip().lower() == 'y':
                sp("可用录音文件：")
                for idx, audio in enumerate(case_data["audio_files"], 1):
                    sp(f"  {idx}. {audio['filename']}")
                sp("选择编号: ", end='')
                try:
                    audio_idx = int(input().strip()) - 1
                    if 0 <= audio_idx < len(case_data["audio_files"]):
                        audio_ref = case_data["audio_files"][audio_idx]["filename"]
                except:
                    pass

        # 添加逐字稿
        case_data["transcripts"].append({
            "id": f"T{len(case_data['transcripts']) + 1:03d}",
            "title": title,
            "content": transcript_content,
            "audio_file": audio_ref,
            "created_at": datetime.now().isoformat()
        })

        sp(f"[OK] 逐字稿已添加：{title}")

    return case_data


def upload_supervision_files(case_id: str, case_data: Dict) -> Dict:
    """交互式上传督导资料"""
    sp("")
    sp("[督导资料] 是否要上传督导资料？(y/n): ", end='')
    choice = input().strip().lower()

    if choice != 'y':
        return case_data

    supervision_dir = CASES_PROCESSED / case_id / "supervision"
    supervision_dir.mkdir(parents=True, exist_ok=True)

    while True:
        sp("请输入督导资料文件路径（留空结束）: ", end='')
        file_path = input().strip()

        if not file_path:
            break

        if not os.path.exists(file_path):
            sp(f"[ERR] 文件不存在：{file_path}")
            continue

        # 复制文件
        filename = os.path.basename(file_path)
        dest_path = supervision_dir / filename
        shutil.copy2(file_path, dest_path)

        # 添加到案例数据
        case_data["supervision_files"].append({
            "filename": filename,
            "uploaded_at": datetime.now().isoformat(),
            "file_size": os.path.getsize(dest_path)
        })

        sp(f"[OK] 督导资料已保存：{filename}")

    return case_data


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


def process_case(source_file_path: str) -> Optional[str]:
    """处理一个案例，返回案例编号"""

    sp("")
    sp("=" * 60)
    sp(f"[CASE] 开始处理案例：{source_file_path}")
    sp("=" * 60)
    sp("")

    # 1. 验证文件
    if not os.path.exists(source_file_path):
        sp(f"[ERR] 文件不存在：{source_file_path}")
        return None

    if not source_file_path.endswith('.docx'):
        sp("[ERR] 不支持的文件格式（仅支持 .docx）")
        return None

    # 2. 确保目录存在
    ensure_directories()

    # 3. 加载统一标签库
    tags_library = load_tags_library()

    # 4. 生成案例编号
    case_id = generate_case_id()
    sp(f"[ID] 案例编号：{case_id}")

    # 5. 读取 Word 文档
    sp("[READ] 读取文档...")
    try:
        content = read_word_document(source_file_path)
        sp(f"[OK] 读取成功（{len(content)} 字符）")
    except Exception as e:
        sp(f"[ERR] {e}")
        return None

    # 6. 保存原始文档
    original_dest = CASES_ORIGINAL / f"{case_id}.docx"
    shutil.copy2(source_file_path, original_dest)
    sp(f"[SAVE] 原始文档 -> {original_dest}")

    # 7. AI 分析
    ai_analysis = call_ai_analysis(content, case_id)
    if not ai_analysis:
        ai_analysis = {
            "relation_tags": [], "symptom_tags": [],
            "crisis_level": "", "crisis_evidence": "",
            "keywords": [], "techniques_used": [],
            "summary": "", "strengths": [], "improvements": [],
            "recommended_followup": ""
        }

    # 8. 标签验证
    sp("[VALIDATE] 验证 AI 提取的标签...")
    validation_result = validate_tags(ai_analysis, tags_library)

    if validation_result["validation_report"]["has_issues"]:
        sp("[WARN] 发现需要审核的标签：")
        if validation_result["validation_report"]["unvalidated"]["relation"]:
            sp(f"  关系标签：{', '.join(validation_result['validation_report']['unvalidated']['relation'])}")
        if validation_result["validation_report"]["unvalidated"]["symptom"]:
            sp(f"  症状标签：{', '.join(validation_result['validation_report']['unvalidated']['symptom'])}")
    else:
        sp("[OK] 所有标签验证通过")

    # 9. 生成 JSON
    case_data = create_case_json(case_id, str(original_dest), content, ai_analysis, validation_result)

    # 10. 保存 JSON（初次）
    processed_file = CASES_PROCESSED / f"{case_id}.json"
    processed_file.write_text(json.dumps(case_data, ensure_ascii=False, indent=2), encoding='utf-8')
    sp(f"[SAVE] 处理结果 -> {processed_file}")

    # 11. 交互式上传材料
    case_data = upload_audio_files(case_id, case_data)
    case_data = upload_transcripts(case_id, case_data)
    case_data = upload_supervision_files(case_id, case_data)

    # 12. 重新保存 JSON（包含上传的材料）
    processed_file.write_text(json.dumps(case_data, ensure_ascii=False, indent=2), encoding='utf-8')
    sp(f"[SAVE] 案例数据已更新（包含上传材料）")

    # 13. 更新索引
    update_index(case_id, case_data)

    # 14. 完成报告
    sp("")
    sp("=" * 60)
    sp("[DONE] 案例处理完成！")
    sp("=" * 60)
    sp(f"  案例编号：{case_id}")
    sp(f"  关系标签：{', '.join(case_data['tags']['relation']) or '无'}")
    sp(f"  精神症状：{', '.join(case_data['tags']['symptom']) or '无'}")
    sp(f"  危机等级：{case_data['crisis_level'] or '未判断'}")
    sp(f"  关键词：{', '.join(case_data['keywords']) or '无'}")
    sp(f"  录音文件：{len(case_data['audio_files'])} 个")
    sp(f"  逐字稿：{len(case_data['transcripts'])} 个")
    sp(f"  督导资料：{len(case_data['supervision_files'])} 个")
    if validation_result["validation_report"]["has_issues"]:
        sp(f"  ⚠️  需审核标签数：{len(validation_result['validation_report']['unvalidated']['relation']) + len(validation_result['validation_report']['unvalidated']['symptom'])}")
    sp("")
    sp("[TIP] 下一步：")
    sp(f"  1. 查看分析：{processed_file}")
    sp(f"  2. 重新生成案例库：python src/generate_case_library.py")
    sp("")

    return case_id


def main():
    if len(sys.argv) < 2:
        sp("用法：python case_processor.py <Word文档路径>")
        sp("示例：python case_processor.py D:\\心理咨询师\\1-接访记录\\20260616-案例3.docx")
        sys.exit(1)

    source_file = sys.argv[1]
    case_id = process_case(source_file)
    sys.exit(0 if case_id else 1)


if __name__ == "__main__":
    main()
