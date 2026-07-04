#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成来访者库：以来访者为中心的案例库生成器
"""

import json
import os
import sys
import io
import subprocess
from pathlib import Path
from datetime import datetime

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
project_root = Path(__file__).parent.parent
VISITORS_DIR = project_root / 'data' / 'visitors'
OUTPUT_DIR = project_root / 'output' / '来访者库'
DOWNLOADS_DIR = OUTPUT_DIR / 'downloads'


def get_html_template():
    """获取HTML模板头部"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .collapsible {{ cursor: pointer; }}
        .collapsible:hover {{ background-color: #f3f4f6; }}
        .content {{ display: none; overflow: hidden; }}
        .content.show {{ display: block; }}
        .timeline-item {{ position: relative; padding-left: 2rem; }}
        .timeline-item:before {{
            content: '';
            position: absolute;
            left: 0.4rem;
            top: 2rem;
            bottom: -1rem;
            width: 2px;
            background: #e5e7eb;
        }}
        .timeline-item:last-child:before {{ display: none; }}
        .timeline-dot {{
            position: absolute;
            left: 0;
            top: 0.5rem;
            width: 1rem;
            height: 1rem;
            border-radius: 50%;
            background: white;
            border: 2px solid #6366f1;
        }}
        .tab-button {{ cursor: pointer; transition: all 0.2s; }}
        .tab-button.active {{
            background-color: #6366f1;
            color: white;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
</head>
<body class="bg-gray-50">
"""


def get_html_footer():
    """获取HTML模板尾部"""
    return """
    <script>
        // 折叠功能
        document.querySelectorAll('.collapsible').forEach(item => {
            item.addEventListener('click', function() {
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                content.classList.toggle('show');
            });
        });

        // 标签页切换
        function switchTab(tabName) {
            // 隐藏所有标签内容
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            // 移除所有按钮的active状态
            document.querySelectorAll('.tab-button').forEach(button => {
                button.classList.remove('active');
            });
            // 显示选中的标签内容
            document.getElementById(tabName).classList.add('active');
            // 激活选中的按钮
            event.target.classList.add('active');
        }

        // 删除来访者档案
        function deleteVisitor(visitorId, visitorName) {
            if (!confirm(`确定要删除来访者 "${visitorName}" (${visitorId}) 的所有档案吗？\\n\\n此操作将删除：\\n- 所有来访记录\\n- 所有分析内容\\n- 所有生成的页面\\n\\n此操作不可恢复！`)) {
                return;
            }

            // 显示删除中提示
            const loadingMsg = document.createElement('div');
            loadingMsg.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 9999; text-align: center;';
            loadingMsg.innerHTML = '<div style="font-size: 18px; margin-bottom: 10px;">正在删除档案...</div><div style="color: #666;">请稍候</div>';
            document.body.appendChild(loadingMsg);

            // 调用删除API（使用8768端口，与接访记录服务器统一）
            fetch('http://localhost:8768/api/delete_visitor', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ visitor_id: visitorId })
            })
            .then(response => response.json())
            .then(data => {
                document.body.removeChild(loadingMsg);

                if (data.success) {
                    alert('删除成功！\\n\\n' + data.message);
                    window.location.reload();
                } else {
                    alert('删除失败：' + (data.error || '未知错误'));
                }
            })
            .catch(error => {
                document.body.removeChild(loadingMsg);
                console.error('删除失败:', error);
                alert('删除失败，请确保接访记录服务器已启动（端口8768）\\n\\n错误信息：' + error.message);
            });
        }

        // 默认激活第一个标签
        window.addEventListener('DOMContentLoaded', function() {
            const firstTab = document.querySelector('.tab-button');
            if (firstTab) {
                firstTab.classList.add('active');
                const firstContent = document.querySelector('.tab-content');
                if (firstContent) {
                    firstContent.classList.add('active');
                }
            }
        });
    </script>
</body>
</html>
"""


def extract_crisis_level_display(crisis_assessment):
    """从危机评估数据中提取显示用的危机等级描述"""
    if not crisis_assessment:
        return "未评估", "bg-gray-100 text-gray-800"

    # 等级代码到描述的映射
    level_descriptions = {
        'A': '事理不平',
        'B': '人际困扰',
        'C': '无解决方案',
        'D': '忧思苦恼',
        'E': '痛苦绝望',
        'F': '冷漠',
        'G': '精神困扰',
        'H': '对环境负向观',
        'I': '对他人负向观',
        'J': '对自己负向观',
        'K': '深度焦虑、恐慌、畏惧、强迫',
        'L': '对自己/他人/社会的敌意',
        'M': '对生命的敌意',
        'N': '家庭责任瓦解',
        'O': '生存信念瓦解',
        'P': '重郁、大哭或狂躁',
        'Q1': '不快乐',
        'Q2': '活不下去',
        'R1': '太痛苦了',
        'R2': '死了算了',
        'S1': '自杀动机-过去',
        'S2': '自杀动机-现在',
        'S3': '自杀动机-未来',
        'T': '自杀意念',
        'U': '目的性自杀',
        'V1': '自伤经验',
        'V2': '无法制止自杀的处境',
        'W1': '自杀安排',
        'W2': '临终安排',
        'X': '立刻去死',
        'Y': '病发失控',
        'Z': '自杀行为'
    }

    # 等级代码到危机类别和颜色的映射
    def get_level_info(code):
        if code in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
            return '轻度危机', 'bg-green-100 text-green-800'
        elif code in ['H', 'I', 'J']:
            return '轻度危机', 'bg-green-100 text-green-800'
        elif code in ['K', 'L', 'M', 'N', 'O']:
            return '中度危机', 'bg-yellow-100 text-yellow-800'
        elif code in ['P', 'Q1', 'Q2', 'R1', 'R2']:
            return '中度危机', 'bg-yellow-100 text-yellow-800'
        elif code in ['S1', 'S2', 'S3', 'T', 'U']:
            return '重度危机', 'bg-red-100 text-red-800'
        elif code in ['V1', 'V2', 'W1', 'W2']:
            return '重度危机', 'bg-red-100 text-red-800'
        elif code in ['X', 'Y', 'Z']:
            return '急迫危机', 'bg-red-200 text-red-900'
        return None, 'bg-gray-100 text-gray-800'

    # 检查是否为AI自动生成的评级（检查备注中是否包含"大观学派连续评估"）
    remark = crisis_assessment.get('危机评估备注', '')
    is_ai_generated = '大观学派连续评估' in remark or '最终落脚点：' in remark

    # 如果是AI生成的评级，优先使用用户手动勾选的等级
    if is_ai_generated:
        selected_levels = crisis_assessment.get('选中等级', [])
        if selected_levels and len(selected_levels) > 0:
            # 按严重程度排序，找到最严重的等级
            level_order = ['Z', 'Y', 'X', 'W2', 'W1', 'V2', 'V1', 'U', 'T', 'S3', 'S2', 'S1',
                          'R2', 'R1', 'Q2', 'Q1', 'P', 'O', 'N', 'M', 'L', 'K',
                          'J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']

            # 找到选中等级中最严重的
            most_severe = None
            for code in level_order:
                if code in selected_levels:
                    most_severe = code
                    break

            if most_severe and most_severe in level_descriptions:
                description = level_descriptions[most_severe]
                level_category, color = get_level_info(most_severe)
                if level_category:
                    # 只显示最严重的等级
                    return f"{level_category} - {most_severe}-{description}", color

    # 使用用户手动选择的最终评级（如果存在且非空）
    final_grade = crisis_assessment.get('最终评级', '').strip()
    if final_grade and final_grade in level_descriptions:
        description = level_descriptions[final_grade]
        level_category, color = get_level_info(final_grade)
        if level_category:
            return f"{level_category} - {final_grade}-{description}", color

    # 如果没有最终评级，使用选中等级列表的最严重等级
    selected_levels = crisis_assessment.get('选中等级', [])
    if selected_levels and len(selected_levels) > 0:
        # 按严重程度排序，找到最严重的等级
        level_order = ['Z', 'Y', 'X', 'W2', 'W1', 'V2', 'V1', 'U', 'T', 'S3', 'S2', 'S1',
                      'R2', 'R1', 'Q2', 'Q1', 'P', 'O', 'N', 'M', 'L', 'K',
                      'J', 'I', 'H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']

        # 找到选中等级中最严重的
        most_severe = None
        for code in level_order:
            if code in selected_levels:
                most_severe = code
                break

        if most_severe and most_severe in level_descriptions:
            description = level_descriptions[most_severe]
            level_category, color = get_level_info(most_severe)
            if level_category:
                return f"{level_category} - {most_severe}-{description}", color

    return "未评估", "bg-gray-100 text-gray-800"


def generate_visitor_index():
    """生成来访者库首页"""
    print("\n生成来访者库首页...")

    html = get_html_template().format(title="来访者库")

    html += """
    <div class="container mx-auto px-4 py-8">
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-800 mb-2">来访者库</h1>
            <p class="text-gray-600">以来访者为中心的咨询案例管理系统</p>
        </div>
"""

    # 获取所有来访者
    visitors = []
    if VISITORS_DIR.exists():
        for visitor_dir in sorted(VISITORS_DIR.iterdir()):
            if visitor_dir.is_dir():
                profile_file = visitor_dir / 'profile.json'
                if profile_file.exists():
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                        visitors.append(profile)

    print(f"  找到 {len(visitors)} 个来访者")

    # 生成来访者卡片
    html += '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">\n'

    for profile in visitors:
        visitor_id = profile['visitor_id']
        basic_info = profile['basic_info']
        visit_history = profile['visit_history']
        total_visits = len(visit_history)

        # 获取最近一次来访的危机评估
        last_visit = visit_history[-1] if visit_history else {}
        last_date = last_visit.get('date', '未知')

        # 从最近一次来访的JSON文件中读取危机评估数据
        crisis_display = "未评估"
        risk_color = "bg-gray-100 text-gray-800"

        if last_visit:
            visit_id = last_visit.get('visit_id', '')
            if visit_id:
                visit_file = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
                if visit_file.exists():
                    try:
                        with open(visit_file, 'r', encoding='utf-8') as f:
                            visit_data = json.load(f)
                            crisis_assessment = visit_data.get('case_data', {}).get('crisis_assessment', {})
                            crisis_display, risk_color = extract_crisis_level_display(crisis_assessment)
                    except Exception as e:
                        print(f"  警告: 读取 {visit_file} 失败: {e}")

        html += f"""
        <div class="block bg-white rounded-lg shadow hover:shadow-lg transition p-6 relative">
            <div class="flex justify-between items-start mb-4">
                <a href="{visitor_id}/profile.html" class="flex-1">
                    <h3 class="text-xl font-semibold text-gray-800">{basic_info.get('name', visitor_id)}</h3>
                </a>
                <div class="flex items-center gap-2">
                    <span class="px-3 py-1 text-sm rounded-full {risk_color}">
                        {crisis_display}
                    </span>
                    <button onclick="event.preventDefault(); deleteVisitor('{visitor_id}', '{basic_info.get('name', visitor_id)}')"
                            class="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
                            title="删除档案">
                        <i class="fa fa-trash"></i>
                    </button>
                </div>
            </div>
            <a href="{visitor_id}/profile.html" class="block">
                <div class="space-y-2 text-sm text-gray-600">
                    <p><i class="fa fa-user"></i> {basic_info.get('age', '未知')} · {basic_info.get('gender', '未知')}</p>
                    <p><i class="fa fa-briefcase"></i> {basic_info.get('occupation', '未知')}</p>
                    <p><i class="fa fa-calendar"></i> 共 {total_visits} 次来访</p>
                    <p><i class="fa fa-clock-o"></i> 最近: {last_date}</p>
                </div>
                <div class="mt-4 pt-4 border-t">
                    <p class="text-sm text-gray-500 line-clamp-2">{basic_info.get('background', '')[:100]}...</p>
                </div>
            </a>
        </div>
"""

    html += '</div>\n'
    html += '</div>\n'
    html += get_html_footer()

    # 写入文件
    output_file = OUTPUT_DIR / 'index.html'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✓ 生成: {output_file}")
    return output_file


def generate_visitor_profile_page(profile_data):
    """生成来访者档案页面"""
    visitor_id = profile_data['visitor_id']
    print(f"\n生成来访者档案页: {visitor_id}")

    basic_info = profile_data['basic_info']
    overall_progress = profile_data.get('overall_progress', {})
    visit_history = profile_data['visit_history']

    html = get_html_template().format(title=f"{basic_info.get('name', visitor_id)} - 来访者档案")

    # 导航栏
    html += """
    <div class="bg-white shadow-sm mb-6">
        <div class="container mx-auto px-4 py-4">
            <a href="../index.html" class="text-indigo-600 hover:text-indigo-800">
                <i class="fa fa-arrow-left"></i> 返回来访者库
            </a>
        </div>
    </div>
"""

    html += '<div class="container mx-auto px-4 py-8">\n'

    # 【第一部分】来访者档案
    html += f"""
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <div class="flex justify-between items-start mb-6">
            <div>
                <h1 class="text-3xl font-bold text-gray-800 mb-2">{basic_info.get('name', visitor_id)}</h1>
                <p class="text-gray-600">来访者档案 · {visitor_id}</p>
            </div>
            <div class="flex gap-2">
                <a href="comparison.html" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition">
                    <i class="fa fa-bar-chart"></i> 对比视图
                </a>
                <button onclick="deleteVisitor('{visitor_id}', '{basic_info.get('name', visitor_id)}')" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition">
                    <i class="fa fa-trash"></i> 删除档案
                </button>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="p-4 bg-gray-50 rounded">
                <p class="text-sm text-gray-600 mb-1">年龄 / 性别</p>
                <p class="text-lg font-semibold">{basic_info.get('age', '未知')} · {basic_info.get('gender', '未知')}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded">
                <p class="text-sm text-gray-600 mb-1">职业</p>
                <p class="text-lg font-semibold">{basic_info.get('occupation', '未知')}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded">
                <p class="text-sm text-gray-600 mb-1">婚姻状况</p>
                <p class="text-lg font-semibold">{basic_info.get('marital_status', '未知')}</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div class="p-4 bg-gray-50 rounded">
                <p class="text-sm text-gray-600 mb-1">性取向</p>
                <p class="text-lg font-semibold">{basic_info.get('sexual_orientation', '未填写') if basic_info.get('sexual_orientation') else '未填写'}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded">
                <p class="text-sm text-gray-600 mb-1">宗教信仰</p>
                <p class="text-lg font-semibold">{basic_info.get('religion', '未填写') if basic_info.get('religion') else '未填写'}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded">
                <p class="text-sm text-gray-600 mb-1">来访者联系电话</p>
                <p class="text-lg font-semibold">{basic_info.get('contact_phone', '未填写') if basic_info.get('contact_phone') else '未填写'}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded">
                <p class="text-sm text-gray-600 mb-1">紧急联系人</p>
                <p class="text-lg font-semibold">{basic_info.get('emergency_contact', '未填写') if basic_info.get('emergency_contact') else '未填写'}</p>
            </div>
            <div class="p-4 bg-gray-50 rounded">
                <p class="text-sm text-gray-600 mb-1">紧急联系人电话</p>
                <p class="text-lg font-semibold">{basic_info.get('emergency_contact_phone', '未填写') if basic_info.get('emergency_contact_phone') else '未填写'}</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div class="p-4 bg-indigo-50 rounded">
                <p class="text-sm text-gray-600 mb-1">总来访次数</p>
                <p class="text-2xl font-bold text-indigo-600">{len(visit_history)} 次</p>
            </div>
            <div class="p-4 bg-indigo-50 rounded">
                <p class="text-sm text-gray-600 mb-1">累计通话时长</p>
                <p class="text-2xl font-bold text-indigo-600">{sum(visit.get('duration', 0) for visit in visit_history)} 分钟</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="p-4 bg-blue-50 rounded">
                <p class="text-sm text-gray-600 mb-1">首次接访日期</p>
                <p class="text-base font-semibold text-blue-800">{profile_data.get('session_info', {}).get('first_session_date', '未知')}</p>
            </div>
            <div class="p-4 bg-blue-50 rounded">
                <p class="text-sm text-gray-600 mb-1">咨询渠道</p>
                <p class="text-base font-semibold text-blue-800">{profile_data.get('session_info', {}).get('channel', '未知')}</p>
            </div>
            <div class="p-4 bg-blue-50 rounded">
                <p class="text-sm text-gray-600 mb-1">咨询师</p>
                <p class="text-base font-semibold text-blue-800">{profile_data.get('session_info', {}).get('counselor', '未知')}</p>
            </div>
        </div>

        <div class="mb-6">
            <div class="flex justify-between items-center mb-3">
                <h3 class="text-lg font-semibold text-gray-800">背景信息</h3>
                <div class="flex gap-2">
                    <button onclick="editProfileField('background', '背景信息')" class="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                        <i class="fa fa-edit"></i> 编辑
                    </button>
                    <button onclick="uploadWordForProfileField('background', '背景信息')" class="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700">
                        <i class="fa fa-upload"></i> 上传Word
                    </button>
                    <button onclick="downloadProfileField('background', '背景信息')" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                        <i class="fa fa-download"></i> 下载
                    </button>
                </div>
            </div>
            <div id="background-content" class="text-gray-700 leading-relaxed whitespace-pre-wrap">{basic_info.get('background', '暂无')}</div>
        </div>

        <div class="mb-6">
            <div class="flex justify-between items-center mb-3">
                <h3 class="text-lg font-semibold text-gray-800">来访主诉</h3>
                <div class="flex gap-2">
                    <button onclick="editProfileField('initial_complaint', '来访主诉')" class="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                        <i class="fa fa-edit"></i> 编辑
                    </button>
                    <button onclick="uploadWordForProfileField('initial_complaint', '来访主诉')" class="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700">
                        <i class="fa fa-upload"></i> 上传Word
                    </button>
                    <button onclick="downloadProfileField('initial_complaint', '来访主诉')" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                        <i class="fa fa-download"></i> 下载
                    </button>
                </div>
            </div>
            <div id="initial_complaint-content" class="text-gray-700 leading-relaxed whitespace-pre-wrap">{basic_info.get('initial_complaint', '暂无')}</div>
        </div>

        <div class="mb-6">
            <div class="flex justify-between items-center mb-3">
                <h3 class="text-lg font-semibold text-gray-800">整体咨询目标</h3>
                <div class="flex gap-2">
                    <button onclick="editProfileField('counseling_goal', '整体咨询目标')" class="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                        <i class="fa fa-edit"></i> 编辑
                    </button>
                    <button onclick="uploadWordForProfileField('counseling_goal', '整体咨询目标')" class="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700">
                        <i class="fa fa-upload"></i> 上传Word
                    </button>
                    <button onclick="downloadProfileField('counseling_goal', '整体咨询目标')" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                        <i class="fa fa-download"></i> 下载
                    </button>
                </div>
            </div>
            <div id="counseling_goal-content" class="text-gray-700 leading-relaxed whitespace-pre-wrap">{basic_info.get('counseling_goal', '待设定') if basic_info.get('counseling_goal') else '待设定'}</div>
        </div>

        <div class="mb-6">
            <div class="flex justify-between items-center mb-3">
                <h3 class="text-lg font-semibold text-gray-800">咨询进度</h3>
                <div class="flex gap-2">
                    <button onclick="editProfileField('counseling_progress', '咨询进度')" class="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700">
                        <i class="fa fa-edit"></i> 编辑
                    </button>
                    <button onclick="uploadWordForProfileField('counseling_progress', '咨询进度')" class="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700">
                        <i class="fa fa-upload"></i> 上传Word
                    </button>
                    <button onclick="downloadProfileField('counseling_progress', '咨询进度')" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
                        <i class="fa fa-download"></i> 下载
                    </button>
                </div>
            </div>
            <div id="counseling_progress-content" class="text-gray-700 leading-relaxed whitespace-pre-wrap">{basic_info.get('counseling_progress', '暂无') if basic_info.get('counseling_progress') else '暂无'}</div>
        </div>

        <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-3"><i class="fa fa-users text-pink-600"></i> 家庭结构</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="p-3 bg-gray-50 rounded">
                    <p class="text-sm text-gray-600 mb-1">父亲情况</p>
                    <p class="text-gray-800">{profile_data.get('family_structure', {}).get('father', '未填写') if profile_data.get('family_structure', {}).get('father') else '未填写'}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded">
                    <p class="text-sm text-gray-600 mb-1">母亲情况</p>
                    <p class="text-gray-800">{profile_data.get('family_structure', {}).get('mother', '未填写') if profile_data.get('family_structure', {}).get('mother') else '未填写'}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded">
                    <p class="text-sm text-gray-600 mb-1">父母关系</p>
                    <p class="text-gray-800">{profile_data.get('family_structure', {}).get('parents_relationship', '未填写') if profile_data.get('family_structure', {}).get('parents_relationship') else '未填写'}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded">
                    <p class="text-sm text-gray-600 mb-1">兄弟姐妹</p>
                    <p class="text-gray-800">{profile_data.get('family_structure', {}).get('siblings', '未填写') if profile_data.get('family_structure', {}).get('siblings') else '未填写'}</p>
                </div>
                <div class="p-3 bg-gray-50 rounded md:col-span-2">
                    <p class="text-sm text-gray-600 mb-1">配偶/子女情况</p>
                    <p class="text-gray-800">{profile_data.get('family_structure', {}).get('spouse_children', '未填写') if profile_data.get('family_structure', {}).get('spouse_children') else '未填写'}</p>
                </div>
            </div>
        </div>

        <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-3">用药情况</h3>
            <p class="text-gray-700 leading-relaxed">{basic_info.get('medication', '暂无') if basic_info.get('medication') else '暂无'}</p>
        </div>

        <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-3">来访备注</h3>
            <p class="text-gray-700 leading-relaxed">{basic_info.get('notes', '暂无') if basic_info.get('notes') else '暂无'}</p>
        </div>

        <div>
            <h3 class="text-lg font-semibold text-gray-800 mb-3">整体进展评估</h3>
            <p class="text-gray-700 mb-4">{overall_progress.get('treatment_progress', '暂无')}</p>
            <p class="text-gray-700">{overall_progress.get('therapeutic_relationship', '暂无')}</p>
        </div>
    </div>
"""

    # 【第二部分】来访时间线 + 来访概况列表
    html += """
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">来访历史</h2>
        <div class="space-y-6">
"""

    # 生成时间线
    for visit in visit_history:
        visit_num = visit['visit_number']
        visit_id = visit['visit_id']
        date = visit['date']
        counselor = visit.get('counselor', '未知')
        duration = visit.get('duration', '?')
        main_issue = visit.get('main_issue', '未知')

        # 从visit的JSON文件中读取危机评估数据
        crisis_display = "未评估"
        risk_color = "bg-gray-100 text-gray-800"

        visit_file = VISITORS_DIR / profile_data['visitor_id'] / 'visits' / f'{visit_id}.json'
        if visit_file.exists():
            try:
                with open(visit_file, 'r', encoding='utf-8') as f:
                    visit_data = json.load(f)
                    crisis_assessment = visit_data.get('case_data', {}).get('crisis_assessment', {})
                    crisis_display, risk_color = extract_crisis_level_display(crisis_assessment)
            except Exception as e:
                print(f"  警告: 读取 {visit_file} 失败: {e}")

        html += f"""
        <div class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="bg-gray-50 rounded-lg p-6 hover:shadow-md transition">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="text-lg font-semibold text-gray-800">第 {visit_num} 次来访</h3>
                        <p class="text-sm text-gray-600">{date} · {counselor} · {duration}分钟</p>
                    </div>
                    <span class="px-3 py-1 text-sm rounded-full {risk_color}">
                        {crisis_display}
                    </span>
                </div>
                <p class="text-gray-700 mb-4"><strong>主要问题：</strong>{main_issue}</p>
                <a href="{visit_id}.html" class="inline-block px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition">
                    <i class="fa fa-file-text-o"></i> 查看详细记录
                </a>
            </div>
        </div>
"""

    html += """
        </div>
    </div>
"""

    html += '</div>\n'

    # 添加profile字段编辑功能的JavaScript
    html += f"""
    <script>
        const VISITOR_ID = '{visitor_id}';

        // 编辑profile字段
        function editProfileField(fieldName, fieldTitle) {{
            const contentDiv = document.getElementById(fieldName + '-content');
            const currentContent = contentDiv.textContent;

            const textarea = document.createElement('textarea');
            textarea.className = 'w-full p-3 border rounded';
            textarea.rows = 10;
            textarea.value = currentContent;

            const saveBtn = document.createElement('button');
            saveBtn.className = 'mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 mr-2';
            saveBtn.innerHTML = '<i class="fa fa-save"></i> 保存';
            saveBtn.onclick = () => saveProfileField(fieldName, fieldTitle, textarea.value, contentDiv);

            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'mt-2 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700';
            cancelBtn.innerHTML = '<i class="fa fa-times"></i> 取消';
            cancelBtn.onclick = () => {{
                contentDiv.innerHTML = currentContent;
            }};

            contentDiv.innerHTML = '';
            contentDiv.appendChild(textarea);
            contentDiv.appendChild(saveBtn);
            contentDiv.appendChild(cancelBtn);
        }}

        // 保存profile字段
        function saveProfileField(fieldName, fieldTitle, content, contentDiv) {{
            fetch('http://localhost:8768/api/update_profile_field', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    visitor_id: VISITOR_ID,
                    field_name: fieldName,
                    content: content
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    contentDiv.textContent = content;
                    alert('保存成功！');
                }} else {{
                    alert('保存失败：' + (data.error || '未知错误'));
                }}
            }})
            .catch(error => {{
                console.error('保存失败:', error);
                alert('保存失败，请确保接访记录服务器已启动（端口8768）');
            }});
        }}

        // 上传Word文档到profile字段
        function uploadWordForProfileField(fieldName, fieldTitle) {{
            const contentDiv = document.getElementById(fieldName + '-content');
            const hasExistingContent = contentDiv && contentDiv.textContent.trim() && contentDiv.textContent !== '暂无' && contentDiv.textContent !== '待设定';

            // 如果有现有内容，显示确认对话框
            if (hasExistingContent) {{
                if (!confirm('当前' + fieldTitle + '已有内容，上传新Word文档将完全覆盖现有内容。\\n\\n是否继续？')) {{
                    return;
                }}
            }}

            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.docx';
            input.onchange = (e) => {{
                const file = e.target.files[0];
                if (!file) return;

                // 显示上传提示
                const uploadMsg = document.createElement('div');
                uploadMsg.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 9999; text-align: center;';
                uploadMsg.innerHTML = '<div style="font-size: 18px; margin-bottom: 10px;">正在处理Word文档...</div><div style="color: #666;">解析格式中，请稍候</div>';
                document.body.appendChild(uploadMsg);

                const formData = new FormData();
                formData.append('file', file);

                fetch('http://localhost:8765/', {{
                    method: 'POST',
                    body: formData,
                    mode: 'cors'
                }})
                .then(response => response.json())
                .then(data => {{
                    document.body.removeChild(uploadMsg);
                    if (data.success && data.html) {{
                        // 从HTML中提取纯文本
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = data.html;
                        const textContent = tempDiv.textContent || tempDiv.innerText || '';

                        // 保存到服务器
                        saveProfileField(fieldName, fieldTitle, textContent, contentDiv);
                    }} else {{
                        alert('Word解析失败：' + (data.error || '未知错误'));
                    }}
                }})
                .catch(error => {{
                    document.body.removeChild(uploadMsg);
                    console.error('上传失败:', error);
                    alert('上传失败，请确保Word上传服务器已启动（端口8765）\\n\\n错误信息：' + error.message);
                }});
            }};
            input.click();
        }}

        // 下载profile字段为Word
        function downloadProfileField(fieldName, fieldTitle) {{
            const contentDiv = document.getElementById(fieldName + '-content');
            const content = contentDiv.textContent;

            if (!content || content === '暂无' || content === '待设定') {{
                alert('没有内容可以下载');
                return;
            }}

            const html = `<html><head><meta charset="utf-8"><title>${{fieldTitle}}</title></head><body><h1>${{fieldTitle}}</h1><p>${{content.replace(/\\n/g, '<br>')}}</p></body></html>`;
            const blob = new Blob([html], {{type: 'application/msword'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${{VISITOR_ID}}_${{fieldTitle}}.doc`;
            a.click();
            URL.revokeObjectURL(url);
        }}
    </script>
    """

    html += get_html_footer()

    # 写入文件
    visitor_dir = OUTPUT_DIR / visitor_id
    visitor_dir.mkdir(parents=True, exist_ok=True)
    output_file = visitor_dir / 'profile.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✓ 生成: {output_file}")
    return output_file


def main():
    """主函数"""
    print("=" * 60)
    print("生成来访者库")
    print("=" * 60)

    # 生成首页
    generate_visitor_index()

    # 生成每个来访者的档案页
    if VISITORS_DIR.exists():
        for visitor_dir in sorted(VISITORS_DIR.iterdir()):
            if visitor_dir.is_dir():
                profile_file = visitor_dir / 'profile.json'
                if profile_file.exists():
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        profile_data = json.load(f)
                        generate_visitor_profile_page(profile_data)

    # 生成来访详情页
    print("\n生成来访详情页...")
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(project_root / 'src' / 'generate_visit_details.py')],
            cwd=str(project_root / 'src'),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print("  ✓ 来访详情页生成完成")
        else:
            print(f"  ✗ 来访详情页生成失败: {result.stderr}")
    except Exception as e:
        print(f"  ✗ 调用来访详情页生成脚本失败: {e}")

    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)
    print(f"\n首页: {OUTPUT_DIR / 'index.html'}")


if __name__ == '__main__':
    main()
