#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成来访详情页 - 修复版（支持多流派Tab界面）
"""

import json
import os
import sys
import io
from pathlib import Path

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
project_root = Path(__file__).parent.parent
VISITORS_DIR = project_root / 'data' / 'visitors'
APPROACHES_DIR = project_root / 'data' / 'config' / 'approaches'
OUTPUT_DIR = project_root / 'output' / '来访者库'


def extract_crisis_level_display(crisis_assessment):
    """从危机评估数据中提取显示用的危机等级描述"""
    if not crisis_assessment:
        return "未评估", "bg-gray-100 text-gray-800"

    # 尝试从危机评估备注中提取等级描述
    remark = crisis_assessment.get('危机评估备注', '')
    if remark and '最终落脚点：' in remark:
        # 提取 "最终落脚点：X - 描述 (等级)" 格式
        import re
        match = re.search(r'最终落脚点：[A-Z0-9]+ - (.+?) \((.+?)\)', remark)
        if match:
            description = match.group(1)  # 如 "L-敌意/报复"
            level_category = match.group(2)  # 如 "中度危机"

            # 根据等级类别确定颜色
            color_map = {
                '轻度危机': 'bg-green-100 text-green-800',
                '中度危机': 'bg-yellow-100 text-yellow-800',
                '重度危机': 'bg-red-100 text-red-800',
                '急迫危机': 'bg-red-200 text-red-900'
            }
            color = color_map.get(level_category, 'bg-gray-100 text-gray-800')

            # 返回格式：等级类别 - 描述
            return f"{level_category} - {description}", color

    # 降级：只返回最终评级代码
    final_grade = crisis_assessment.get('最终评级', '')
    if final_grade:
        # 根据代码推断等级
        if final_grade in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            return f"轻度危机 ({final_grade})", 'bg-green-100 text-green-800'
        elif final_grade in ['H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'R1']:
            return f"中度危机 ({final_grade})", 'bg-yellow-100 text-yellow-800'
        elif final_grade in ['S', 'T', 'U', 'V', 'W']:
            return f"重度危机 ({final_grade})", 'bg-red-100 text-red-800'
        elif final_grade in ['X', 'Y', 'Z']:
            return f"急迫危机 ({final_grade})", 'bg-red-200 text-red-900'

    return "未评估", "bg-gray-100 text-gray-800"


def load_approaches():
    """加载所有流派配置"""
    approaches = []

    if not APPROACHES_DIR.exists():
        print(f"警告: 流派配置目录不存在: {APPROACHES_DIR}")
        return approaches

    for approach_file in APPROACHES_DIR.glob('*.json'):
        try:
            with open(approach_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                approaches.append(config)
        except Exception as e:
            print(f"警告: 无法加载流派配置 {approach_file.name}: {e}")

    # 排序：enabled=true在前，然后按sort_order排序
    approaches.sort(key=lambda x: (not x.get('enabled', False), x.get('sort_order', 999)))

    return approaches


def generate_approach_tabs_html(visit_data, approaches, case_id):
    """生成流派分析Tab界面的HTML"""

    case_data = visit_data.get('case_data', {})
    approach_analyses = case_data.get('approach_analyses', {})

    # Tab按钮
    tabs_html = '<div class="flex flex-wrap gap-2 mb-6 border-b pb-4">\n'

    for i, approach in enumerate(approaches):
        approach_id = approach.get('id', '')
        approach_name = approach.get('name', '')
        approach_color = approach.get('color', '#6366f1')
        approach_icon = approach.get('icon', '📋')
        is_enabled = approach.get('enabled', False)

        # 第一个Tab默认激活
        active_class = 'active' if i == 0 else ''

        # 处理图标：如果是 fa-xxx 格式，用 Font Awesome；否则用 emoji
        if approach_icon.startswith('fa-'):
            icon_html = f'<i class="fa {approach_icon}"></i>'
        else:
            icon_html = approach_icon

        # 如果未启用，显示灰色
        if not is_enabled:
            tabs_html += f'    <button class="tab-button {active_class} px-6 py-2 rounded-t font-semibold opacity-50" onclick="switchTab(\'tab-{approach_id}\')" style="background-color: #e5e7eb; color: #6b7280;">\n'
            tabs_html += f'        {icon_html} {approach_name} <span class="text-xs">(待启用)</span>\n'
        else:
            tabs_html += f'    <button class="tab-button {active_class} px-6 py-2 rounded-t font-semibold" onclick="switchTab(\'tab-{approach_id}\')">\n'
            tabs_html += f'        {icon_html} {approach_name}\n'

        tabs_html += '    </button>\n'

    tabs_html += '</div>\n\n'

    # Tab内容
    content_html = ''

    for i, approach in enumerate(approaches):
        approach_id = approach.get('id', '')
        approach_name = approach.get('name', '')
        is_enabled = approach.get('enabled', False)

        # 第一个Tab默认激活
        active_class = 'active' if i == 0 else ''

        content_html += f'<div id="tab-{approach_id}" class="tab-content {active_class}">\n'

        # 获取该流派的分析数据
        approach_data = approach_analyses.get(approach_id, {})

        if not is_enabled:
            # 未启用的流派显示占位符
            # 处理图标显示
            icon = approach.get("icon", "📋")
            if icon.startswith('fa-'):
                icon_display = f'<i class="fa {icon}" style="font-size: 4rem;"></i>'
            else:
                icon_display = f'<div class="text-6xl">{icon}</div>'

            content_html += '    <div class="p-8 text-center bg-gray-50 rounded">\n'
            content_html += f'        <div class="mb-4">{icon_display}</div>\n'
            content_html += f'        <h3 class="text-xl font-semibold text-gray-700 mb-2">{approach_name}</h3>\n'
            content_html += f'        <p class="text-gray-500 mb-4">{approach.get("description", "")}</p>\n'
            content_html += '        <div class="inline-block px-4 py-2 bg-yellow-100 text-yellow-800 rounded">\n'
            content_html += '            此流派暂未启用，待学习后可添加分析内容\n'
            content_html += '        </div>\n'
            content_html += '    </div>\n'
        elif not approach_data or not any(approach_data.values()):
            # 已启用但无数据
            # 处理图标显示
            icon = approach.get("icon", "📋")
            if icon.startswith('fa-'):
                icon_display = f'<i class="fa {icon}" style="font-size: 4rem;"></i>'
            else:
                icon_display = f'<div class="text-6xl">{icon}</div>'

            content_html += '    <div class="p-8 text-center bg-gray-50 rounded">\n'
            content_html += f'        <div class="mb-4">{icon_display}</div>\n'
            content_html += f'        <h3 class="text-xl font-semibold text-gray-700 mb-2">{approach_name}</h3>\n'
            content_html += '        <p class="text-gray-500 mb-4">暂无分析内容</p>\n'
            content_html += f'        <a href="../downloads/{case_id}/{case_id}_{approach_name}.md" class="inline-block px-4 py-2 bg-gray-400 text-white rounded cursor-not-allowed" disabled>\n'
            content_html += '            <i class="fa fa-download"></i> 下载Markdown (暂无数据)\n'
            content_html += '        </a>\n'
            content_html += '    </div>\n'
        else:
            # 有数据，显示分析内容 + 下载按钮
            content_html += '    <div class="prose max-w-none">\n'

            # 下载按钮（顶部右侧）
            content_html += f'        <div class="flex justify-end mb-4">\n'
            content_html += f'            <a href="../downloads/{case_id}/{case_id}_{approach_name}.md" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition flex items-center gap-2" download>\n'
            content_html += '                <i class="fa fa-download"></i> 下载Markdown\n'
            content_html += '            </a>\n'
            content_html += '        </div>\n'

            # 根据流派字段定义渲染内容
            fields = approach.get('fields', {})

            for field_key, field_config in fields.items():
                field_label = field_config.get('label', field_key)
                field_value = approach_data.get(field_key, '')

                if field_value:
                    content_html += f'        <h3 class="text-lg font-semibold text-gray-800 mt-4 mb-2">{field_label}</h3>\n'

                    if isinstance(field_value, list):
                        content_html += '        <ul class="list-disc list-inside space-y-1">\n'
                        for item in field_value:
                            content_html += f'            <li class="text-gray-700">{item}</li>\n'
                        content_html += '        </ul>\n'
                    else:
                        content_html += f'        <p class="text-gray-700 whitespace-pre-wrap">{field_value}</p>\n'

            content_html += '    </div>\n'

        content_html += '</div>\n\n'

    return tabs_html + content_html


def generate_visit_detail_page(visitor_id, visit_data):
    """生成单个来访详情页"""

    visit_id = visit_data.get('visit_id', '')
    visit_number = visit_data.get('visit_number', 1)
    visit_summary = visit_data.get('visit_summary', {})
    case_data = visit_data.get('case_data', {})
    case_id = case_data.get('case_id', '')

    # 加载流派配置
    approaches = load_approaches()

    if not approaches:
        print(f"警告: 未找到任何流派配置，使用默认配置")
        approaches = [
            {
                'id': 'daguanpai',
                'name': '大观学派（危机干预）',
                'icon': '🚨',
                'enabled': True,
                'description': '大观学派危机干预体系',
                'fields': {
                    'conceptualization': {'label': '案例概念化'},
                    'intervention_suggestions': {'label': '干预建议'},
                    'key_points': {'label': '关键要点'}
                }
            }
        ]

    # 构建HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>第{visit_number}次来访 - {visitor_id}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .tab-button {{
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }}
        .tab-button:hover {{
            background-color: #f3f4f6;
        }}
        .tab-button.active {{
            background-color: #6366f1;
            color: white;
            border-bottom: 2px solid #6366f1;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .collapsible {{
            cursor: pointer;
        }}
        .collapsible:hover {{
            background-color: #f3f4f6;
        }}
        .content {{
            display: none;
            overflow: hidden;
        }}
        .content.show {{
            display: block;
        }}
    </style>
</head>
<body class="bg-gray-50">

    <!-- 顶部导航 -->
    <div class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <a href="./profile.html" class="text-indigo-600 hover:text-indigo-800 flex items-center">
                    <i class="fa fa-arrow-left mr-2"></i> 返回来访者档案
                </a>
                <div class="flex gap-2">
                    <a href="../index.html" class="text-gray-600 hover:text-gray-800">
                        <i class="fa fa-home"></i> 来访者库
                    </a>
                </div>
            </div>
        </div>
    </div>

    <!-- 主内容 -->
    <div class="max-w-7xl mx-auto px-6 py-8">

        <!-- 来访概况 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <div class="flex items-center justify-between mb-6">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800 mb-2">第 {visit_number} 次来访</h1>
                    <p class="text-gray-600">{visit_data.get('date', '')} · {visit_summary.get('counselor', '未知')} · {visit_summary.get('duration', '?')}分钟</p>
                </div>
"""

    # 风险评估徽章 - 从crisis_assessment中提取
    crisis_assessment = case_data.get('crisis_assessment', {})
    crisis_display, risk_color = extract_crisis_level_display(crisis_assessment)

    html += f"""
                <span class="px-4 py-2 text-sm rounded-full {risk_color}">
                    {crisis_display}
                </span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div class="p-4 bg-gray-50 rounded">
                    <p class="text-sm text-gray-600 mb-2">本次诉求</p>
                    <p class="text-gray-800">{visit_summary.get('complaint', '暂无')}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded">
                    <p class="text-sm text-gray-600 mb-2">咨询结果</p>
                    <p class="text-gray-800">{visit_summary.get('outcome', '暂无')}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded">
                    <p class="text-sm text-gray-600 mb-2">布置任务</p>
                    <p class="text-gray-800">{visit_summary.get('homework', '暂无')}</p>
                </div>
                <div class="p-4 bg-gray-50 rounded">
                    <p class="text-sm text-gray-600 mb-2">下一步计划</p>
                    <p class="text-gray-800">{visit_summary.get('next_step', '暂无')}</p>
                </div>
            </div>

            <div class="p-4 bg-blue-50 rounded">
                <p class="text-sm text-gray-600 mb-2">症状变化</p>
                <p class="text-lg font-semibold text-blue-800">{visit_summary.get('symptom_change', '持平')}</p>
            </div>
        </div>

        <!-- 咨询师复盘 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-2xl font-bold text-gray-800">咨询师复盘</h2>
                <a href="../downloads/{case_id}/{case_id}_复盘.docx" class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition flex items-center gap-2" download>
                    <i class="fa fa-download"></i> 下载Word
                </a>
            </div>
            <div class="prose max-w-none text-gray-700">
                {case_data.get('counselor_review', '<p class="text-gray-500">暂无复盘内容</p>').replace(chr(10), '<br>')}
            </div>
        </div>

        <!-- 咨询结果 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">咨询结果</h2>
            <p class="text-gray-700 leading-relaxed">{case_data.get('consultation_result', '<span class="text-gray-500">暂无咨询结果</span>').replace(chr(10), '<br>')}</p>
        </div>

        <!-- 布置任务 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">布置任务</h2>
            <p class="text-gray-700 leading-relaxed">{case_data.get('assigned_tasks', '<span class="text-gray-500">暂无布置任务</span>').replace(chr(10), '<br>')}</p>
        </div>

        <!-- 下一步计划 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">下一步计划</h2>
            <p class="text-gray-700 leading-relaxed">{case_data.get('next_step_plan', '<span class="text-gray-500">暂无下一步计划</span>').replace(chr(10), '<br>')}</p>
        </div>

        <!-- 症状变化 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">症状变化</h2>
            <p class="text-gray-700 leading-relaxed">{case_data.get('symptom_changes', '<span class="text-gray-500">暂无症状变化记录</span>').replace(chr(10), '<br>')}</p>
        </div>

        <!-- 案例概要 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">案例概要</h2>
            <p class="text-gray-700 leading-relaxed">{case_data.get('case_summary', '<span class="text-gray-500">暂无概要</span>')}</p>
        </div>

        <!-- 标签 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <h2 class="text-2xl font-bold text-gray-800 mb-4">标签</h2>
"""

    # 标签
    case_tags = case_data.get('case_tags', {})
    relation_tags = case_tags.get('relation', [])
    symptom_tags = case_tags.get('symptom', [])

    if relation_tags:
        html += '<div class="mb-4"><h3 class="text-lg font-semibold text-gray-700 mb-2">关系标签</h3><div class="flex flex-wrap gap-2">'
        for tag in relation_tags:
            html += f'<span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">{tag}</span>'
        html += '</div></div>'

    if symptom_tags:
        html += '<div><h3 class="text-lg font-semibold text-gray-700 mb-2">症状标签</h3><div class="flex flex-wrap gap-2">'
        for tag in symptom_tags:
            html += f'<span class="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">{tag}</span>'
        html += '</div></div>'

    if not relation_tags and not symptom_tags:
        html += '<p class="text-gray-500">暂无标签</p>'

    html += f"""
        </div>

        <!-- 逐字稿 -->
        <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-2xl font-bold text-gray-800">逐字稿</h2>
                <a href="../downloads/{case_id}/{case_id}_逐字稿.xlsx" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition flex items-center gap-2" download>
                    <i class="fa fa-download"></i> 下载Excel
                </a>
            </div>
            <p class="text-gray-500">点击上方按钮下载完整逐字稿</p>
        </div>

        <!-- 流派分析（多Tab界面） -->
        <div class="bg-white rounded-lg shadow-lg p-8">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-gray-800">流派分析</h2>
            </div>
"""

    # 插入流派Tab界面
    html += generate_approach_tabs_html(visit_data, approaches, case_id)

    html += """
        </div>

    </div>

    <script>
        // Tab切换功能
        function switchTab(tabId) {
            // 隐藏所有Tab内容
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // 移除所有按钮的active状态
            document.querySelectorAll('.tab-button').forEach(button => {
                button.classList.remove('active');
            });

            // 显示选中的Tab
            const selectedTab = document.getElementById(tabId);
            if (selectedTab) {
                selectedTab.classList.add('active');
            }

            // 激活对应的按钮
            event.target.classList.add('active');
        }

        // 折叠功能
        document.querySelectorAll('.collapsible').forEach(item => {
            item.addEventListener('click', function() {
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                content.classList.toggle('show');
            });
        });
    </script>

</body>
</html>
"""

    return html


def main():
    """主函数"""
    print("=" * 60)
    print("生成来访详情页（多流派Tab版本）")
    print("=" * 60)

    # 遍历所有来访者
    for visitor_dir in sorted(VISITORS_DIR.iterdir()):
        if not visitor_dir.is_dir():
            continue

        visitor_id = visitor_dir.name
        visits_dir = visitor_dir / 'visits'

        if not visits_dir.exists():
            continue

        print(f"\n处理来访者: {visitor_id}")

        # 遍历所有来访
        for visit_file in sorted(visits_dir.glob('visit_*.json')):
            with open(visit_file, 'r', encoding='utf-8') as f:
                visit_data = json.load(f)

            visit_id = visit_data.get('visit_id', '')
            visit_number = visit_data.get('visit_number', 1)

            # 生成HTML
            html = generate_visit_detail_page(visitor_id, visit_data)

            # 保存文件
            output_dir = OUTPUT_DIR / visitor_id
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f'{visit_id}.html'

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f"  [OK] 第{visit_number}次来访: {output_file.relative_to(project_root)}")

    print("\n" + "=" * 60)
    print("[SUCCESS] 所有来访详情页生成完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
