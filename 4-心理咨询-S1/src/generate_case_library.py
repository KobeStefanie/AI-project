#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
案例库HTML自动生成脚本
功能：读取JSON案例和索引文件，自动生成HTML案例库（索引页+详情页）
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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


# ==================== 配置 ====================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CASES_PROCESSED = DATA_DIR / "cases" / "processed"
INDEX_DIR = DATA_DIR / "index"
OUTPUT_DIR = PROJECT_ROOT / "output" / "案例库"
TAGS_LIBRARY = DATA_DIR / "config" / "tags_library.json"
APPROACHES_DIR = DATA_DIR / "config" / "approaches"
APPROACHES_DIR = DATA_DIR / "config" / "approaches"

# 危机等级颜色映射
CRISIS_COLORS = {
    "S": {"bg": "red", "label": "自杀风险"},
    "L": {"bg": "orange", "label": "生命危险"},
    "M": {"bg": "yellow", "label": "中度危机"},
    "C": {"bg": "blue", "label": "慢性困扰"},
    "Z": {"bg": "green", "label": "正常范围"}
}

# 人群分类映射
AGE_GROUPS = {
    "青少年": ["青少年", "初中", "高中", "学生", "14岁", "15岁", "16岁", "17岁", "18岁"],
    "中年": ["中年", "40", "50", "更年期", "企业主"],
    "老年": ["老年", "60", "70", "80", "退休"]
}


# ==================== 工具函数 ====================

def load_approaches_config() -> List[Dict]:
    """加载所有流派配置，按 sort_order 排序"""
    approaches = []
    if not APPROACHES_DIR.exists():
        return approaches

    for json_file in APPROACHES_DIR.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                approach_data = json.load(f)
                approaches.append(approach_data)
        except Exception as e:
            sp(f"[WARN] 跳过流派配置文件 {json_file.name}：{e}")

    # 按 sort_order 排序
    approaches.sort(key=lambda x: x.get('sort_order', 999))
    return approaches


def load_all_cases() -> List[Dict]:
    """加载所有已处理的案例JSON"""
    cases = []
    if not CASES_PROCESSED.exists():
        return cases

    for json_file in CASES_PROCESSED.glob("C*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                case_data = json.load(f)
                cases.append(case_data)
        except Exception as e:
            sp(f"[WARN] 跳过文件 {json_file.name}：{e}")

    # 按案例编号排序
    cases.sort(key=lambda x: x.get('case_id', ''))
    return cases


def load_crisis_stats() -> Dict:
    """加载危机等级统计"""
    crisis_file = INDEX_DIR / "crisis_levels.json"
    if crisis_file.exists():
        with open(crisis_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"S": [], "L": [], "M": [], "C": [], "Z": []}


def load_tags_library() -> Dict:
    """加载统一标签库"""
    if TAGS_LIBRARY.exists():
        with open(TAGS_LIBRARY, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_all_tags_from_indexes() -> Dict:
    """从索引文件加载所有标签及对应的案例"""
    relation_tags = {}
    symptom_tags = {}

    # 加载关系标签索引
    relation_file = INDEX_DIR / "relation_tags.json"
    if relation_file.exists():
        with open(relation_file, 'r', encoding='utf-8') as f:
            relation_tags = json.load(f)

    # 加载症状标签索引
    symptom_file = INDEX_DIR / "symptom_tags.json"
    if symptom_file.exists():
        with open(symptom_file, 'r', encoding='utf-8') as f:
            symptom_tags = json.load(f)

    return {
        'relation': relation_tags,
        'symptom': symptom_tags
    }


def classify_age_group(age_str: str) -> str:
    """根据年龄描述分类人群"""
    age_lower = age_str.lower()
    for group, keywords in AGE_GROUPS.items():
        for keyword in keywords:
            if keyword in age_lower:
                return group
    return "未分类"


def get_primary_symptom(case_data: Dict) -> str:
    """获取主要症状（用于文件名）"""
    # v2.0: 从 analyses.daguanpai.tags 读取
    analyses = case_data.get('analyses', {})
    daguanpai = analyses.get('daguanpai', {})
    tags = daguanpai.get('tags', {})
    symptoms = tags.get('symptom', [])

    if not symptoms:
        return "心理问题"

    # 提取第一个症状的主要部分
    first_symptom = symptoms[0]
    parts = first_symptom.split('-')
    if len(parts) >= 2:
        return parts[1]  # 返回子类
    return first_symptom


def generate_case_detail_html(case_data: Dict, approaches: List[Dict]) -> str:
    """生成案例详情页HTML"""

    case_id = case_data.get('case_id', '')
    basic_info = case_data.get('basic_info', {})
    session_info = case_data.get('session_info', {})
    dialogue = case_data.get('dialogue', '')

    # v2.0: 读取所有流派的分析数据
    analyses = case_data.get('analyses', {})

    # 找到第一个有数据的流派用于显示头部信息（危机等级等）
    first_approach_data = {}
    for approach in approaches:
        approach_id = approach.get('id', '')
        if approach_id in analyses and analyses[approach_id]:
            first_approach_data = analyses[approach_id]
            break

    # 如果没有任何流派有数据，使用空字典
    crisis_level = first_approach_data.get('crisis_level', '')
    crisis_evidence = first_approach_data.get('crisis_evidence', '')

    # 提取标题（对话第一行）
    title_lines = dialogue.split('\n', 1)
    title = title_lines[0] if title_lines else case_id

    # 危机等级样式
    crisis_info = CRISIS_COLORS.get(crisis_level, {"bg": "gray", "label": "未评估"})
    crisis_bg = crisis_info['bg']
    crisis_label = crisis_info['label']

    # 根据危机等级生成完整的CSS类名（Tailwind需要完整类名）
    crisis_bg_class = f"bg-{crisis_bg}-50"
    crisis_border_class = f"border-{crisis_bg}-500"
    crisis_text_class = f"text-{crisis_bg}-800"
    crisis_badge_bg = f"bg-{crisis_bg}-100"
    crisis_badge_text = f"text-{crisis_bg}-800"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>案例：{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css">
    <style>
        .tab-btn {{
            padding: 12px 24px;
            border-bottom: 3px solid transparent;
            color: #6B7280;
            cursor: pointer;
            background: none;
            border-top: none;
            border-left: none;
            border-right: none;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{
            color: #1F2937;
            background: #F9FAFB;
        }}
        .tab-btn.active {{
            border-bottom-color: #3B82F6;
            color: #1F2937;
            font-weight: 600;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
    </style>
</head>
<body class="bg-gray-50 p-8">
    <div class="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-8">
        <!-- 返回按钮 -->
        <div class="mb-4">
            <a href="../index.html" class="text-blue-600 hover:text-blue-800">
                <i class="fa fa-arrow-left"></i> 返回案例库
            </a>
        </div>

        <!-- 案例头部 -->
        <div class="border-b pb-4 mb-6">
            <div class="flex items-center justify-between mb-3">
                <h1 class="text-3xl font-bold text-gray-800">{title}</h1>
                <span class="px-4 py-2 {crisis_badge_bg} {crisis_badge_text} font-bold rounded-lg text-lg">{crisis_level}级 - {crisis_label}</span>
            </div>
            <div class="text-sm text-gray-600 space-x-4">
                <span><strong>案例编号：</strong>{case_id}</span>
                <span><strong>日期：</strong>{session_info.get('接访日期', '')}</span>
                <span><strong>时长：</strong>{session_info.get('通话时长', '')}</span>
                <span><strong>渠道：</strong>{session_info.get('咨询渠道', '')}</span>
            </div>
        </div>

        <!-- 基本信息 -->
        <div class="mb-6">
            <h2 class="text-xl font-bold text-blue-900 mb-3">📋 基本信息</h2>
            <div class="bg-blue-50 rounded-lg p-4 grid grid-cols-2 gap-3 text-sm">
                <div><strong>代号：</strong>{basic_info.get('代号', '')}</div>
                <div><strong>性别：</strong>{basic_info.get('性别', '')}</div>
                <div><strong>年龄：</strong>{basic_info.get('年龄', '')}</div>
                <div><strong>职业：</strong>{basic_info.get('职业', '')}</div>
                <div><strong>婚姻：</strong>{basic_info.get('婚姻状况', '')}</div>
            </div>
        </div>

        <!-- 录音资料 -->
"""

    # 生成录音区域
    audio_files = case_data.get('audio_files', [])
    if audio_files:
        html += f"""        <div class="mb-6">
            <h2 class="text-xl font-bold text-orange-900 mb-3">🎙️ 录音资料</h2>
            <div class="space-y-3">
"""
        for audio in audio_files:
            filename = audio.get('filename', '')
            uploaded_at = audio.get('uploaded_at', '')
            size = audio.get('size', 0)
            # 格式化文件大小
            if size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            html += f"""                <div class="bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-2">
                            <i class="fa fa-file-audio-o text-orange-600"></i>
                            <span class="font-medium text-gray-800">{filename}</span>
                        </div>
                        <span class="text-sm text-gray-500">{size_str}</span>
                    </div>
                    <audio controls class="w-full" preload="metadata">
                        <source src="http://localhost:8004/api/audio/file/{case_id}/{filename}" type="audio/mpeg">
                        您的浏览器不支持音频播放
                    </audio>
                </div>
"""
        html += """            </div>
        </div>

"""

    # 生成逐字稿区域
    transcripts = case_data.get('transcripts', [])
    if transcripts:
        html += f"""        <div class="mb-6">
            <h2 class="text-xl font-bold text-green-900 mb-3">📝 逐字稿</h2>
            <div class="space-y-3">
"""
        for transcript in transcripts:
            transcript_id = transcript.get('id', '')
            content = transcript.get('content', '')
            audio_filename = transcript.get('audio_filename', '')
            created_at = transcript.get('created_at', '')

            # 格式化日期
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                created_str = created_at

            audio_tag = f'<span class="text-xs text-blue-600 ml-2"><i class="fa fa-link"></i> {audio_filename}</span>' if audio_filename else ''

            html += f"""                <details class="bg-green-50 border border-green-200 rounded-lg">
                    <summary class="p-4 cursor-pointer hover:bg-green-100 transition">
                        <span class="font-medium text-gray-800">逐字稿 {transcript_id}</span>
                        {audio_tag}
                        <span class="text-xs text-gray-500 ml-2">{created_str}</span>
                    </summary>
                    <div class="p-4 pt-0">
                        <pre class="whitespace-pre-wrap font-mono text-sm text-gray-700 bg-white p-4 rounded border border-green-200">{content}</pre>
                    </div>
                </details>
"""
        html += """            </div>
        </div>

"""

    html += """        <!-- 流派Tab导航 -->
        <div class="border-b mb-6">
            <div class="flex gap-2">
"""

    # 生成督导资料区域
    supervision_files = case_data.get('supervision_files', [])
    if supervision_files:
        html += f"""        <div class="mb-6">
            <h2 class="text-xl font-bold text-amber-900 mb-3">📋 督导资料</h2>
            <div class="space-y-3">
"""
        for supervision in supervision_files:
            filename = supervision.get('filename', '')
            title = supervision.get('title', filename)
            note = supervision.get('note', '')
            uploaded_at = supervision.get('uploaded_at', '')

            # 格式化日期
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
                uploaded_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                uploaded_str = uploaded_at

            # 获取文件图标
            ext = filename.split('.')[-1].lower() if '.' in filename else ''
            file_icons = {
                'txt': 'fa-file-text-o',
                'md': 'fa-file-code-o',
                'pdf': 'fa-file-pdf-o',
                'doc': 'fa-file-word-o',
                'docx': 'fa-file-word-o',
                'jpg': 'fa-file-image-o',
                'jpeg': 'fa-file-image-o',
                'png': 'fa-file-image-o'
            }
            file_icon = file_icons.get(ext, 'fa-file-o')

            note_html = f'<p class="text-xs text-gray-600 mt-1">{note}</p>' if note else ''

            html += f"""                <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3 flex-1">
                            <i class="fa {file_icon} text-amber-600 text-2xl"></i>
                            <div>
                                <p class="font-medium text-gray-800">{title}</p>
                                <p class="text-xs text-gray-500">{filename} · {uploaded_str}</p>
                                {note_html}
                            </div>
                        </div>
                        <a href="http://localhost:8006/api/supervision/file/{case_id}/{filename}"
                           target="_blank"
                           class="px-4 py-2 bg-amber-600 text-white rounded hover:bg-amber-700 transition">
                            <i class="fa fa-download"></i> 下载
                        </a>
                    </div>
                </div>
"""
        html += """            </div>
        </div>

"""

    html += """        <!-- 流派Tab导航 -->
        <div class="border-b mb-6">
            <div class="flex gap-2">
"""

    # 生成流派Tab按钮（显示所有流派，不过滤enabled状态）
    for i, approach in enumerate(approaches):
        approach_id = approach.get('id', '')
        approach_name = approach.get('name', '')
        approach_icon = approach.get('icon', 'fa-circle')
        active_class = 'active' if i == 0 else ''
        html += f"""                <button class="tab-btn {active_class}" data-tab="{approach_id}">
                    <i class="fa {approach_icon}"></i> {approach_name}
                </button>
"""

    html += f"""            </div>
        </div>

"""

    # 动态生成所有流派的Tab内容
    for i, approach in enumerate(approaches):
        approach_id = approach.get('id', '')
        approach_name = approach.get('name', '')
        active_class = 'active' if i == 0 else ''

        # 获取该流派的分析数据
        approach_analysis = analyses.get(approach_id, {})

        # 如果该流派有分析数据，显示完整内容
        if approach_analysis:
            approach_crisis_level = approach_analysis.get('crisis_level', '')
            approach_crisis_evidence = approach_analysis.get('crisis_evidence', '')
            approach_keywords = approach_analysis.get('keywords', [])
            approach_techniques = approach_analysis.get('techniques_used', [])
            approach_ai_analysis = approach_analysis.get('ai_analysis', {})

            # 危机等级样式
            approach_crisis_info = CRISIS_COLORS.get(approach_crisis_level, {"bg": "gray", "label": "未评估"})
            approach_crisis_bg = approach_crisis_info['bg']
            approach_crisis_label = approach_crisis_info['label']
            approach_crisis_bg_class = f"bg-{approach_crisis_bg}-50"
            approach_crisis_border_class = f"border-{approach_crisis_bg}-500"

            html += f"""        <!-- {approach_name}Tab内容 -->
        <div class="tab-content {active_class}" id="tab-{approach_id}">
            <!-- 危机评估 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-red-900 mb-3">⚠️ 危机评估</h2>
                <div class="{approach_crisis_bg_class} border-l-4 {approach_crisis_border_class} rounded p-4 text-sm">
                    <div class="font-semibold mb-2">{approach_crisis_level}级 - {approach_crisis_label}</div>
                    <div class="text-gray-700">
                        <strong>证据：</strong>{approach_crisis_evidence}
                    </div>
                </div>
            </div>

            <!-- 关键词 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-purple-900 mb-3">🏷️ 关键词</h2>
                <div class="flex flex-wrap gap-2">
"""
            # 添加关键词标签
            for keyword in approach_keywords[:15]:
                html += f'                    <span class="px-3 py-1 bg-purple-100 text-purple-700 text-sm rounded-full">{keyword}</span>\n'

            html += f"""                </div>
            </div>

            <!-- 使用技术 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-green-900 mb-3">🛠️ 使用技术</h2>
                <div class="bg-green-50 rounded-lg p-4">
                    <ul class="list-disc list-inside space-y-1 text-sm">
"""
            for technique in approach_techniques:
                html += f'                        <li>{technique}</li>\n'

            html += f"""                    </ul>
                </div>
            </div>

            <!-- AI分析 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-indigo-900 mb-3">🤖 AI督导分析</h2>

                <!-- 案例摘要 -->
                <div class="mb-4">
                    <h3 class="font-semibold text-gray-800 mb-2">📝 案例摘要</h3>
                    <p class="text-sm text-gray-700 bg-gray-50 p-3 rounded">{approach_ai_analysis.get('summary', '')}</p>
                </div>

                <!-- 咨询师优势 -->
                <div class="mb-4">
                    <h3 class="font-semibold text-green-800 mb-2">✅ 咨询师优势</h3>
                    <ul class="list-disc list-inside space-y-1 text-sm text-gray-700">
"""
            for strength in approach_ai_analysis.get('strengths', []):
                html += f'                        <li>{strength}</li>\n'

            html += f"""                    </ul>
                </div>

                <!-- 改进建议 -->
                <div class="mb-4">
                    <h3 class="font-semibold text-orange-800 mb-2">💡 改进建议</h3>
                    <ul class="list-disc list-inside space-y-1 text-sm text-gray-700">
"""
            for improvement in approach_ai_analysis.get('improvements', []):
                html += f'                        <li>{improvement}</li>\n'

            html += f"""                    </ul>
                </div>

                <!-- 下次咨询建议 -->
                <div>
                    <h3 class="font-semibold text-blue-800 mb-2">📅 下次咨询建议</h3>
                    <p class="text-sm text-gray-700 bg-blue-50 p-3 rounded">{approach_ai_analysis.get('recommended_followup', '')}</p>
                </div>
            </div>
        </div>

"""
        else:
            # 该流派暂无分析数据，显示占位符
            html += f"""        <!-- {approach_name}Tab内容 -->
        <div class="tab-content {active_class}" id="tab-{approach_id}">
            <div class="bg-gray-100 text-gray-500 rounded-lg p-8 text-center">
                <i class="fa fa-info-circle text-4xl mb-3"></i>
                <p>该流派分析暂未添加</p>
            </div>
        </div>

"""

    # 生成历次感悟区域
    supervision_records = case_data.get('supervision_records', [])
    html += f"""        <!-- 历次感悟 -->
        <div class="mb-6">
            <div class="flex items-center justify-between mb-3">
                <h2 class="text-xl font-bold text-teal-900">💭 历次感悟</h2>
                <button onclick="openAddRecordModal()" class="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition">
                    <i class="fa fa-plus"></i> 添加感悟
                </button>
            </div>
"""

    if supervision_records:
        # 按创建时间倒序排列（最新的在前）
        sorted_records = sorted(supervision_records, key=lambda x: x.get('created_at', ''), reverse=True)

        for record in sorted_records:
            record_id = record.get('record_id', '')
            content = record.get('content', '')
            approach = record.get('approach')
            created_at = record.get('created_at', '')
            updated_at = record.get('updated_at', '')

            # 格式化时间
            try:
                created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = created_dt.strftime('%Y-%m-%d %H:%M')
            except:
                created_str = created_at

            try:
                updated_dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                updated_str = updated_dt.strftime('%Y-%m-%d %H:%M')
            except:
                updated_str = updated_at

            # 流派标签
            approach_badge = ''
            if approach:
                approach_badge = f'<span class="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">{approach}</span>'
            else:
                approach_badge = '<span class="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">无流派标注</span>'

            # 时间显示（如果创建和修改时间不同，显示"已编辑"）
            time_info = f'创建：{created_str}'
            if created_str != updated_str:
                time_info += f' · 编辑：{updated_str}'

            # 转义内容中的特殊字符，防止破坏HTML结构
            content_escaped = content.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n')

            html += f"""            <div class="bg-teal-50 border border-teal-200 rounded-lg p-4 mb-3">
                <div class="flex items-start justify-between mb-2">
                    <div class="flex items-center gap-2">
                        {approach_badge}
                        <span class="text-xs text-gray-500">{time_info}</span>
                    </div>
                    <div class="flex gap-2">
                        <button onclick='openEditRecordModal("{record_id}", "{content_escaped}", "{approach if approach else ""}")'
                                class="text-blue-600 hover:text-blue-800 text-sm">
                            <i class="fa fa-edit"></i> 编辑
                        </button>
                        <button onclick='deleteRecord("{record_id}")'
                                class="text-red-600 hover:text-red-800 text-sm">
                            <i class="fa fa-trash"></i> 删除
                        </button>
                    </div>
                </div>
                <div class="text-sm text-gray-800 whitespace-pre-wrap">{content}</div>
            </div>
"""
    else:
        html += """            <div class="bg-gray-100 text-gray-500 rounded-lg p-6 text-center">
                <i class="fa fa-info-circle text-2xl mb-2"></i>
                <p>还没有添加任何感悟，点击右上角"添加感悟"按钮开始记录</p>
            </div>
"""

    html += """        </div>

        <!-- 完整对话记录 -->
        <div class="mb-6">
            <h2 class="text-xl font-bold text-gray-900 mb-3">💬 完整对话记录</h2>
            <div class="bg-gray-50 rounded-lg p-4">
                <pre class="whitespace-pre-wrap text-sm text-gray-800 font-mono">{dialogue}</pre>
            </div>
        </div>

        <!-- 返回按钮 -->
        <div class="text-center mt-8">
            <a href="../../index.html" class="inline-block px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 mr-3">
                <i class="fa fa-home"></i> 返回项目主页
            </a>
            <a href="../index.html" class="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <i class="fa fa-arrow-left"></i> 返回案例库
            </a>
        </div>
    </div>

    <!-- 添加/编辑感悟模态框 -->
    <div id="recordModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div class="p-6 border-b">
                <h3 class="text-xl font-bold text-gray-800" id="modalTitle">添加历次感悟</h3>
            </div>
            <div class="p-6">
                <div class="mb-4">
                    <label class="block text-sm font-semibold text-gray-700 mb-2">流派视角（可选）</label>
                    <select id="recordApproach" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500">
                        <option value="">不标注流派</option>
                        <option value="大观学派">大观学派</option>
                        <option value="CBT">CBT（认知行为疗法）</option>
                        <option value="精神动力学">精神动力学</option>
                        <option value="人本主义">人本主义</option>
                        <option value="存在主义">存在主义</option>
                    </select>
                </div>
                <div class="mb-4">
                    <label class="block text-sm font-semibold text-gray-700 mb-2">感悟内容</label>
                    <textarea id="recordContent" rows="8" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500" placeholder="记录你对这个案例的理解、感悟、思考..."></textarea>
                </div>
            </div>
            <div class="p-6 border-t flex justify-end gap-3">
                <button onclick="closeRecordModal()" class="px-6 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition">
                    取消
                </button>
                <button onclick="saveRecord()" class="px-6 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition">
                    <i class="fa fa-save"></i> 保存
                </button>
            </div>
        </div>
    </div>

    <script>
        const CASE_ID = '{case_id}';
        let editingRecordId = null;

        // Tab切换
        document.querySelectorAll('.tab-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                const tabId = btn.dataset.tab;
                // 切换按钮状态
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // 切换内容
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.getElementById('tab-' + tabId).classList.add('active');
            }});
        }});

        // 打开添加感悟模态框
        function openAddRecordModal() {{
            editingRecordId = null;
            document.getElementById('modalTitle').textContent = '添加历次感悟';
            document.getElementById('recordApproach').value = '';
            document.getElementById('recordContent').value = '';
            document.getElementById('recordModal').classList.remove('hidden');
        }}

        // 打开编辑感悟模态框
        function openEditRecordModal(recordId, content, approach) {{
            editingRecordId = recordId;
            document.getElementById('modalTitle').textContent = '编辑历次感悟';
            document.getElementById('recordApproach').value = approach || '';
            document.getElementById('recordContent').value = content;
            document.getElementById('recordModal').classList.remove('hidden');
        }}

        // 关闭模态框
        function closeRecordModal() {{
            document.getElementById('recordModal').classList.add('hidden');
            editingRecordId = null;
        }}

        // 保存感悟
        async function saveRecord() {{
            const approach = document.getElementById('recordApproach').value || null;
            const content = document.getElementById('recordContent').value.trim();

            if (!content) {{
                alert('请输入感悟内容');
                return;
            }}

            const update = {{
                case_id: CASE_ID,
                content: content,
                approach: approach
            }};

            if (editingRecordId) {{
                // 编辑模式
                update.type = 'supervision_record_edit';
                update.record_id = editingRecordId;
            }} else {{
                // 添加模式
                update.type = 'supervision_record_add';
            }}

            // 读取现有的 pending_updates.json
            let updates = [];
            try {{
                const response = await fetch('http://localhost:5001/api/pending_updates');
                if (response.ok) {{
                    updates = await response.json();
                }}
            }} catch (e) {{
                // 文件不存在，使用空数组
            }}

            // 添加新的更新
            updates.push(update);

            // 保存到 pending_updates.json
            try {{
                const response = await fetch('http://localhost:5001/api/pending_updates', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(updates)
                }});

                if (response.ok) {{
                    closeRecordModal();
                    showNotification('感悟已保存到待处理队列');
                }} else {{
                    alert('保存失败，请重试');
                }}
            }} catch (e) {{
                alert('无法连接到服务器：' + e.message);
            }}
        }}

        // 删除感悟
        async function deleteRecord(recordId) {{
            if (!confirm('确定要删除这条感悟吗？此操作不可恢复。')) {{
                return;
            }}

            const update = {{
                type: 'supervision_record_delete',
                case_id: CASE_ID,
                record_id: recordId
            }};

            // 读取现有的 pending_updates.json
            let updates = [];
            try {{
                const response = await fetch('http://localhost:5001/api/pending_updates');
                if (response.ok) {{
                    updates = await response.json();
                }}
            }} catch (e) {{
                // 文件不存在，使用空数组
            }}

            // 添加删除请求
            updates.push(update);

            // 保存到 pending_updates.json
            try {{
                const response = await fetch('http://localhost:5001/api/pending_updates', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(updates)
                }});

                if (response.ok) {{
                    showNotification('删除请求已保存到待处理队列');
                }} else {{
                    alert('删除失败，请重试');
                }}
            }} catch (e) {{
                alert('无法连接到服务器：' + e.message);
            }}
        }}

        // 显示提示消息
        function showNotification(message) {{
            const notification = document.createElement('div');
            notification.className = 'fixed top-4 right-4 bg-teal-600 text-white px-6 py-4 rounded-lg shadow-lg z-50';
            notification.innerHTML = `
                <div class="flex items-center gap-3">
                    <i class="fa fa-check-circle"></i>
                    <div>
                        <p class="font-semibold">${{message}}</p>
                        <p class="text-sm mt-1">请在终端运行：<code class="bg-teal-700 px-2 py-1 rounded">python src/process_updates.py</code></p>
                    </div>
                </div>
            `;
            document.body.appendChild(notification);

            setTimeout(() => {{
                notification.remove();
            }}, 8000);
        }}

        // 点击模态框外部关闭
        document.getElementById('recordModal').addEventListener('click', (e) => {{
            if (e.target.id === 'recordModal') {{
                closeRecordModal();
            }}
        }});
    </script>
</body>
</html>"""

    return html


def generate_index_html(cases: List[Dict], crisis_stats: Dict, tags_index: Dict, tags_library: Dict) -> str:
    """生成案例库索引页HTML"""

    # 统计数据
    total_cases = len(cases)
    last_update = datetime.now().strftime("%Y-%m-%d")

    # 提取所有使用的标签（从索引中获取）
    relation_tags_used = list(tags_index['relation'].keys())
    symptom_tags_used = list(tags_index['symptom'].keys())

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>心理咨询案例库</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css">
    <style>
        .filter-card {{
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.2s;
            margin-bottom: 8px;
        }}
        .filter-card-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: #F9FAFB;
            cursor: pointer;
            user-select: none;
        }}
        .filter-card-header:hover {{
            background: #F3F4F6;
        }}
        .filter-card.expanded .filter-card-header {{
            background: #EFF6FF;
            border-bottom: 1px solid #BFDBFE;
        }}
        .filter-card-body {{
            display: none;
            padding: 16px;
            background: white;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }}
        .filter-card.expanded .filter-card-body {{
            display: grid;
        }}
        .filter-arrow {{
            margin-left: auto;
            transition: transform 0.2s;
            font-size: 12px;
            color: #9CA3AF;
        }}
        .filter-card.expanded .filter-arrow {{
            transform: rotate(90deg);
        }}
        .filter-checkbox {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
        }}
        .filter-checkbox:hover {{
            background: #F3F4F6;
        }}
        .filter-checkbox input[type="checkbox"] {{
            width: 16px;
            height: 16px;
            cursor: pointer;
        }}
        .selected-tags-box {{
            background: #F3F4F6;
            border: 1px dashed #D1D5DB;
            border-radius: 8px;
            padding: 12px;
            min-height: 40px;
            margin-bottom: 16px;
        }}
        .selected-tag {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: #3B82F6;
            color: white;
            border-radius: 16px;
            font-size: 12px;
            margin: 2px;
        }}
        .selected-tag .remove-btn {{
            cursor: pointer;
            font-weight: bold;
            opacity: 0.8;
        }}
        .selected-tag .remove-btn:hover {{
            opacity: 1;
        }}
    </style>
</head>
<body class="bg-gray-50">
    <div class="container mx-auto p-6">
        <!-- 头部 -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">
                <i class="fa fa-folder-open text-blue-600"></i> 心理咨询案例库
            </h1>
            <p class="text-gray-600">真实案例记录与学习资料 | 案例总数: {total_cases}</p>
            <p class="text-sm text-gray-500 mt-2">最后更新: {last_update}</p>
        </div>

        <!-- 统计面板 -->
        <div class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
"""

    # 添加危机等级统计
    for level, info in CRISIS_COLORS.items():
        count = len(crisis_stats.get(level, []))
        bg_color = info['bg']
        label = info['label']
        # 生成完整的CSS类名
        stat_bg = f"bg-{bg_color}-50"
        stat_border = f"border-{bg_color}-500"
        stat_text = f"text-{bg_color}-800"
        stat_number = f"text-{bg_color}-600"
        html += f"""            <div class="{stat_bg} border-l-4 {stat_border} rounded-lg p-3">
                <div class="{stat_text} text-xs font-semibold">{level} - {label}</div>
                <div class="text-2xl font-bold {stat_number}">{count}</div>
            </div>
"""

    html += """        </div>

        <!-- 搜索筛选 -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <!-- 关键词搜索 -->
            <div class="mb-4">
                <label class="block text-sm font-semibold text-gray-700 mb-2">
                    <i class="fa fa-search"></i> 关键词搜索
                </label>
                <input type="text" id="searchInput" placeholder="搜索关键词..."
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            </div>

            <!-- 已选标签显示框 -->
            <div class="mb-4">
                <h3 class="text-sm font-semibold text-gray-700 mb-2">已选:</h3>
                <div id="selectedTagsBox" class="selected-tags-box">
                    <span class="text-xs text-gray-400">未选择任何标签</span>
                </div>
            </div>

            <!-- 一、关系标签大分类 -->
            <div class="mb-6">
                <h3 class="text-base font-bold text-gray-800 mb-3">
                    <i class="fa fa-link"></i> 关系标签
                </h3>
                <div class="grid grid-cols-2 gap-3" id="relationCategoriesGrid">
"""

    # 从统一标签库生成关系标签子分类卡片
    if tags_library:
        for category_name, category_data in tags_library.get("relation_tags", {}).items():
            icon = category_data.get("icon", "🏠")
            children = category_data.get("children", {})

            # 收集所有标签
            all_tags = []
            for sub_category, tags in children.items():
                for tag in tags:
                    parts = tag.split('-')
                    if len(parts) >= 3:
                        display_name = '-'.join(parts[2:])
                    else:
                        display_name = parts[-1]
                    all_tags.append((tag, display_name))

            count = len(all_tags)
            html += f"""                    <div class="filter-card" data-category="{category_name}">
                        <div class="filter-card-header" onclick="toggleFilterCard(this)">
                            <span>{icon}</span>
                            <span class="font-semibold text-gray-700">{category_name}</span>
                            <span class="text-xs text-gray-500">{count}项</span>
                            <span class="filter-arrow">▶</span>
                        </div>
                        <div class="filter-card-body">
"""

            for tag, display_name in all_tags:
                html += f"""                            <label class="filter-checkbox">
                                <input type="checkbox" value="{tag}" onchange="filterCases()">
                                <span>{display_name}</span>
                            </label>
"""

            html += """                        </div>
                    </div>
"""

    html += """                </div>
            </div>

            <!-- 二、精神症状标签大分类 -->
            <div class="mb-6">
                <h3 class="text-base font-bold text-gray-800 mb-3">
                    <i class="fa fa-stethoscope"></i> 精神症状标签
                </h3>
                <div class="grid grid-cols-2 gap-3" id="symptomCategoriesGrid">
"""

    # 从统一标签库生成症状标签子分类卡片
    if tags_library:
        for category_name, category_data in tags_library.get("symptom_tags", {}).items():
            icon = category_data.get("icon", "💊")
            children = category_data.get("children", [])

            # 收集所有标签
            all_tags = []
            if isinstance(children, list):
                for tag in children:
                    parts = tag.split('-')
                    display_name = '-'.join(parts[1:])
                    all_tags.append((tag, display_name))
            elif isinstance(children, dict):
                for sub_category, tags in children.items():
                    if isinstance(tags, list):
                        for tag in tags:
                            parts = tag.split('-')
                            if len(parts) >= 3:
                                display_name = '-'.join(parts[2:])
                            else:
                                display_name = '-'.join(parts[1:])
                            all_tags.append((tag, display_name))

            count = len(all_tags)
            html += f"""                    <div class="filter-card" data-category="{category_name}">
                        <div class="filter-card-header" onclick="toggleFilterCard(this)">
                            <span>{icon}</span>
                            <span class="font-semibold text-gray-700">{category_name}</span>
                            <span class="text-xs text-gray-500">{count}项</span>
                            <span class="filter-arrow">▶</span>
                        </div>
                        <div class="filter-card-body">
"""

            for tag, display_name in all_tags:
                html += f"""                            <label class="filter-checkbox">
                                <input type="checkbox" value="{tag}" onchange="filterCases()">
                                <span>{display_name}</span>
                            </label>
"""

            html += """                        </div>
                    </div>
"""

    html += """                </div>
            </div>

            <!-- 人群筛选 -->
            <div class="mb-4">
                <label class="block text-sm font-semibold text-gray-700 mb-2">
                    <i class="fa fa-users"></i> 人群
                </label>
                <select id="ageFilter" class="w-full px-4 py-2 border border-gray-300 rounded-lg" onchange="filterCases()">
                    <option value="">全部人群</option>
                    <option value="青少年">青少年</option>
                    <option value="中年">中年</option>
                    <option value="老年">老年</option>
                </select>
            </div>

            <!-- 危机等级筛选 -->
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">
                    <i class="fa fa-exclamation-triangle"></i> 危机等级
                </label>
                <select id="crisisFilter" class="w-full px-4 py-2 border border-gray-300 rounded-lg" onchange="filterCases()">
                    <option value="">全部等级</option>
"""

    for level, info in CRISIS_COLORS.items():
        html += f'                    <option value="{level}">{level} - {info["label"]}</option>\n'

    html += """                </select>
            </div>
        </div>

        <!-- 案例列表 -->
        <div id="caseList" class="space-y-4">

"""

    # 添加每个案例卡片
    for case in cases:
        case_id = case.get('case_id', '')
        basic_info = case.get('basic_info', {})
        session_info = case.get('session_info', {})

        # v2.0: 从 analyses.daguanpai 读取
        analyses = case.get('analyses', {})
        daguanpai_analysis = analyses.get('daguanpai', {})

        crisis_level = daguanpai_analysis.get('crisis_level', '')
        keywords = daguanpai_analysis.get('keywords', [])
        techniques = daguanpai_analysis.get('techniques_used', [])
        ai_analysis = daguanpai_analysis.get('ai_analysis', {})

        # 提取标题
        dialogue = case.get('dialogue', '')
        title_lines = dialogue.split('\n', 1)
        title = title_lines[0] if title_lines else case_id

        # 人群分类
        age_group = classify_age_group(basic_info.get('年龄', ''))

        # 主要症状
        primary_symptom = get_primary_symptom(case)

        # 危机等级样式
        crisis_info = CRISIS_COLORS.get(crisis_level, {"bg": "gray", "label": "未评估"})
        crisis_bg = crisis_info['bg']
        crisis_label = crisis_info['label']

        # 生成完整的CSS类名
        crisis_badge_bg = f"bg-{crisis_bg}-100"
        crisis_badge_text = f"text-{crisis_bg}-800"

        # 生成文件名
        filename = f"[{primary_symptom}]-[{age_group}]-{case_id}-{title}.html"

        # 关键词字符串（用于搜索）
        keywords_str = ' '.join(keywords)

        # 摘要
        summary = ai_analysis.get('summary', '')[:200]

        # 亮点（第一个优势）
        strengths = ai_analysis.get('strengths', [])
        highlight = strengths[0] if strengths else ''

        # v2.0: 获取标签从 analyses.daguanpai.tags
        case_tags = daguanpai_analysis.get('tags', {})
        relation_tags = case_tags.get('relation', [])
        symptom_tags = case_tags.get('symptom', [])
        relation_tags_str = '|||'.join(relation_tags)  # 使用特殊分隔符
        symptom_tags_str = '|||'.join(symptom_tags)

        html += f"""            <!-- 案例: {case_id} -->
            <div class="case-card bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition"
                 data-crisis="{crisis_level}"
                 data-age="{age_group}"
                 data-keywords="{keywords_str}"
                 data-relation-tags="{relation_tags_str}"
                 data-symptom-tags="{symptom_tags_str}">
                <div class="flex justify-between items-start mb-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                            <h3 class="text-xl font-bold text-gray-800">{title}</h3>
                            <span class="px-3 py-1 {crisis_badge_bg} {crisis_badge_text} font-bold rounded-lg text-sm">{crisis_level}级</span>
                        </div>
                        <div class="text-sm text-gray-600 mb-3">
                            <span><i class="fa fa-calendar"></i> {session_info.get('接访日期', '')}</span>
                            <span class="ml-4"><i class="fa fa-clock-o"></i> {session_info.get('通话时长', '')}</span>
                            <span class="ml-4"><i class="fa fa-phone"></i> {session_info.get('咨询渠道', '')}</span>
                        </div>
                        <div class="text-sm text-gray-700 mb-3">
                            <strong>案例编号：</strong>{case_id}
                        </div>
                        <p class="text-gray-600 text-sm mb-3">
                            {summary}...
                        </p>
                        <div class="flex flex-wrap gap-2 mb-3">
"""

        # 添加关键词标签（最多6个）
        for keyword in keywords[:6]:
            html += f'                            <span class="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded font-medium">{keyword}</span>\n'

        html += f"""                        </div>
                        <div class="text-xs text-gray-500">
                            <strong>核心技术：</strong>{', '.join(techniques[:4])}
                        </div>
                    </div>
                </div>
                <div class="border-t pt-3 flex justify-between items-center">
                    <div class="text-xs text-green-600">
                        <i class="fa fa-lightbulb-o"></i> <strong>亮点：</strong>{highlight[:50]}...
                    </div>
                    <a href="cases/{filename}"
                       class="text-blue-600 hover:text-blue-800 font-semibold text-sm">
                        <i class="fa fa-eye"></i> 查看详情
                    </a>
                </div>
            </div>

"""

    html += """        </div>

        <!-- 无结果提示 -->
        <div id="noResults" class="text-center text-gray-500 py-8 hidden">
            <i class="fa fa-search text-4xl mb-2"></i>
            <p>没有找到匹配的案例</p>
        </div>

        <!-- 返回主页按钮 -->
        <div class="text-center mt-8">
            <a href="../index.html" class="inline-block px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
                <i class="fa fa-home"></i> 返回项目主页
            </a>
        </div>
    </div>

    <script>
        // 展开/收起面板
        function toggleFilterCard(headerElement) {
            const card = headerElement.parentElement;
            card.classList.toggle('expanded');
        }

        const searchInput = document.getElementById('searchInput');
        const crisisFilter = document.getElementById('crisisFilter');
        const ageFilter = document.getElementById('ageFilter');
        const caseCards = document.querySelectorAll('.case-card');
        const noResults = document.getElementById('noResults');
        const selectedTagsBox = document.getElementById('selectedTagsBox');

        // 更新已选标签显示
        function updateSelectedTags() {
            const selectedTags = [];

            // 收集关系标签
            document.querySelectorAll('#relationCategoriesGrid input[type="checkbox"]:checked').forEach(cb => {
                const label = cb.parentElement.textContent.trim();
                selectedTags.push({ value: cb.value, label: label, type: 'relation' });
            });

            // 收集症状标签
            document.querySelectorAll('#symptomCategoriesGrid input[type="checkbox"]:checked').forEach(cb => {
                const label = cb.parentElement.textContent.trim();
                selectedTags.push({ value: cb.value, label: label, type: 'symptom' });
            });

            // 更新显示
            if (selectedTags.length === 0) {
                selectedTagsBox.innerHTML = '<span class="text-xs text-gray-400">未选择任何标签</span>';
            } else {
                selectedTagsBox.innerHTML = selectedTags.map(tag =>
                    `<span class="selected-tag">
                        ${tag.label}
                        <span class="remove-btn" onclick="removeTag('${tag.value}')">×</span>
                    </span>`
                ).join('');
            }
        }

        // 移除标签
        function removeTag(tagValue) {
            const checkbox = document.querySelector(`input[type="checkbox"][value="${tagValue}"]`);
            if (checkbox) {
                checkbox.checked = false;
                updateSelectedTags();
                filterCases();
            }
        }

        function filterCases() {
            const searchTerm = searchInput.value.toLowerCase();
            const crisisValue = crisisFilter.value;
            const ageValue = ageFilter.value;

            // 获取选中的关系标签
            const selectedRelationTags = [];
            document.querySelectorAll('#relationCategoriesGrid input[type="checkbox"]:checked').forEach(cb => {
                selectedRelationTags.push(cb.value);
            });

            // 获取选中的症状标签
            const selectedSymptomTags = [];
            document.querySelectorAll('#symptomCategoriesGrid input[type="checkbox"]:checked').forEach(cb => {
                selectedSymptomTags.push(cb.value);
            });

            // 更新已选标签显示
            updateSelectedTags();

            let visibleCount = 0;

            caseCards.forEach(card => {
                const keywords = card.dataset.keywords.toLowerCase();
                const crisis = card.dataset.crisis;
                const age = card.dataset.age;
                const relationTags = card.dataset.relationTags.split('|||').filter(t => t);
                const symptomTags = card.dataset.symptomTags.split('|||').filter(t => t);

                const matchSearch = !searchTerm || keywords.includes(searchTerm);
                const matchCrisis = !crisisValue || crisis === crisisValue;
                const matchAge = !ageValue || age.includes(ageValue);

                // 关系标签筛选：如果选中了任何标签，案例必须包含至少一个选中的标签
                const matchRelation = selectedRelationTags.length === 0 ||
                    selectedRelationTags.some(tag => relationTags.includes(tag));

                // 症状标签筛选：如果选中了任何标签，案例必须包含至少一个选中的标签
                const matchSymptom = selectedSymptomTags.length === 0 ||
                    selectedSymptomTags.some(tag => symptomTags.includes(tag));

                if (matchSearch && matchCrisis && matchAge && matchRelation && matchSymptom) {
                    card.style.display = '';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            noResults.classList.toggle('hidden', visibleCount > 0);
        }

        searchInput.addEventListener('input', filterCases);
        crisisFilter.addEventListener('change', filterCases);
        ageFilter.addEventListener('change', filterCases);
    </script>
</body>
</html>"""

    return html


def generate_case_library():
    """生成完整的案例库"""

    sp("")
    sp("=" * 70)
    sp("  案例库HTML生成工具")
    sp("=" * 70)
    sp("")

    # 1. 加载数据
    sp("[LOAD] 加载流派配置...")
    approaches = load_approaches_config()
    sp(f"[OK] 找到 {len(approaches)} 个流派")

    sp("[LOAD] 加载案例数据...")
    cases = load_all_cases()
    sp(f"[OK] 找到 {len(cases)} 个案例")

    sp("[LOAD] 加载危机等级统计...")
    crisis_stats = load_crisis_stats()

    sp("[LOAD] 加载标签索引...")
    tags_index = load_all_tags_from_indexes()
    sp(f"[OK] 关系标签: {len(tags_index['relation'])} 个")
    sp(f"[OK] 症状标签: {len(tags_index['symptom'])} 个")

    sp("[LOAD] 加载统一标签库...")
    tags_library = load_tags_library()

    # 2. 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    case_detail_dir = OUTPUT_DIR / "cases"
    case_detail_dir.mkdir(exist_ok=True)

    # 3. 生成详情页
    sp("")
    sp("[GEN] 生成案例详情页...")
    for case in cases:
        case_id = case.get('case_id', '')
        basic_info = case.get('basic_info', {})

        # 提取标题
        dialogue = case.get('dialogue', '')
        title_lines = dialogue.split('\n', 1)
        title = title_lines[0] if title_lines else case_id

        # 人群分类
        age_group = classify_age_group(basic_info.get('年龄', ''))

        # 主要症状
        primary_symptom = get_primary_symptom(case)

        # 生成HTML
        html_content = generate_case_detail_html(case, approaches)

        # 保存文件
        filename = f"[{primary_symptom}]-[{age_group}]-{case_id}-{title}.html"
        output_file = case_detail_dir / filename
        output_file.write_text(html_content, encoding='utf-8')

        sp(f"  ✅ {filename}")

    # 4. 生成索引页
    sp("")
    sp("[GEN] 生成案例库索引页...")
    index_html = generate_index_html(cases, crisis_stats, tags_index, tags_library)
    index_file = OUTPUT_DIR / "index.html"
    index_file.write_text(index_html, encoding='utf-8')
    sp(f"  ✅ index.html")

    # 5. 完成报告
    sp("")
    sp("=" * 70)
    sp("  生成完成")
    sp("=" * 70)
    sp(f"  案例总数：{len(cases)}")
    sp(f"  关系标签：{len(tags_index['relation'])} 个")
    sp(f"  症状标签：{len(tags_index['symptom'])} 个")
    sp(f"  输出目录：{OUTPUT_DIR}")
    sp(f"  索引页面：{index_file}")
    sp("")
    sp("[TIP] 在浏览器中打开索引页面查看案例库")
    sp("")


def main():
    generate_case_library()


if __name__ == "__main__":
    main()
