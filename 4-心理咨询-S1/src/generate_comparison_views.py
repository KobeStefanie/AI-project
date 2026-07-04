#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成对比视图：跨来访的症状、风险趋势对比
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
OUTPUT_DIR = project_root / 'output' / '来访者库'


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
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .chart-container {{ position: relative; height: 300px; }}
    </style>
</head>
<body class="bg-gray-50">
"""


def get_html_footer():
    """获取HTML模板尾部"""
    return """
</body>
</html>
"""


def generate_comparison_page(visitor_id, profile_data):
    """生成对比视图页面"""
    print(f"  生成对比视图: {visitor_id}")

    basic_info = profile_data['basic_info']
    overall_progress = profile_data.get('overall_progress', {})
    visit_history = profile_data['visit_history']

    html = get_html_template().format(title=f"对比视图 - {basic_info.get('name', visitor_id)}")

    # 导航栏
    html += f"""
    <div class="bg-white shadow-sm mb-6">
        <div class="container mx-auto px-4 py-4 flex justify-between items-center">
            <a href="profile.html" class="text-indigo-600 hover:text-indigo-800">
                <i class="fa fa-arrow-left"></i> 返回来访者档案
            </a>
            <a href="../index.html" class="text-gray-600 hover:text-gray-800">
                <i class="fa fa-home"></i> 来访者库
            </a>
        </div>
    </div>
"""

    html += '<div class="container mx-auto px-4 py-8">\n'

    # 页面标题
    html += f"""
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">对比视图</h1>
        <p class="text-gray-600">{basic_info.get('name', visitor_id)} · 跨来访趋势分析</p>
    </div>
"""

    # 症状趋势图
    symptom_trend = overall_progress.get('symptom_trend', [])
    if symptom_trend:
        dates = [item['date'] for item in symptom_trend]
        severity = [item['severity'] for item in symptom_trend]

        html += """
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">
            <i class="fa fa-line-chart"></i> 症状严重程度趋势
        </h2>
        <div class="chart-container">
            <canvas id="symptomChart"></canvas>
        </div>
        <p class="text-sm text-gray-600 mt-4 text-center">
            评分范围：1（轻微） - 10（严重）
        </p>
    </div>

    <script>
    const symptomCtx = document.getElementById('symptomChart').getContext('2d');
    new Chart(symptomCtx, {{
        type: 'line',
        data: {{
            labels: {dates},
            datasets: [{{
                label: '症状严重程度',
                data: {severity},
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.3,
                fill: true
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                y: {{
                    beginAtZero: true,
                    max: 10,
                    ticks: {{
                        stepSize: 1
                    }}
                }}
            }},
            plugins: {{
                legend: {{
                    display: true,
                    position: 'top'
                }}
            }}
        }}
    }});
    </script>
"""

    # 风险趋势图
    risk_trend = overall_progress.get('risk_trend', [])
    if risk_trend:
        risk_dates = [item['date'] for item in risk_trend]
        risk_levels = [item['risk_level'] for item in risk_trend]

        # 将风险等级转换为数值
        risk_map = {'无': 0, '低': 1, '中': 2, '高': 3}
        risk_values = [risk_map.get(level, 0) for level in risk_levels]

        html += f"""
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">
            <i class="fa fa-exclamation-triangle"></i> 风险等级趋势
        </h2>
        <div class="chart-container">
            <canvas id="riskChart"></canvas>
        </div>
        <p class="text-sm text-gray-600 mt-4 text-center">
            风险类型：{risk_trend[0].get('risk_type', '未知')}
        </p>
    </div>

    <script>
    const riskCtx = document.getElementById('riskChart').getContext('2d');
    new Chart(riskCtx, {{
        type: 'line',
        data: {{
            labels: {risk_dates},
            datasets: [{{
                label: '风险等级',
                data: {risk_values},
                borderColor: 'rgb(239, 68, 68)',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.3,
                fill: true,
                stepped: true
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                y: {{
                    beginAtZero: true,
                    max: 3,
                    ticks: {{
                        stepSize: 1,
                        callback: function(value) {{
                            const labels = ['无', '低', '中', '高'];
                            return labels[value];
                        }}
                    }}
                }}
            }},
            plugins: {{
                legend: {{
                    display: true,
                    position: 'top'
                }}
            }}
        }}
    }});
    </script>
"""

    # 来访对比表格
    html += """
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">
            <i class="fa fa-table"></i> 来访对比
        </h2>
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">次数</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">日期</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">主要问题</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">风险等级</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">咨询师</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">时长</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
"""

    for visit in visit_history:
        v_num = visit['visit_number']
        v_id = visit['visit_id']
        v_date = visit['date']
        v_counselor = visit.get('counselor', '未知')
        v_duration = visit.get('duration', '?')
        v_issue = visit.get('main_issue', '未知')
        v_risk = visit.get('risk_level', '未评估')

        risk_colors = {
            '高': 'bg-red-100 text-red-800',
            '中': 'bg-yellow-100 text-yellow-800',
            '低': 'bg-green-100 text-green-800',
            '无': 'bg-gray-100 text-gray-800'
        }
        risk_color = risk_colors.get(v_risk, 'bg-gray-100 text-gray-800')

        html += f"""
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">第 {v_num} 次</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{v_date}</td>
                        <td class="px-6 py-4 text-sm text-gray-900">{v_issue}</td>
                        <td class="px-6 py-4 whitespace-nowrap">
                            <span class="px-2 py-1 text-xs rounded-full {risk_color}">{v_risk}</span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{v_counselor}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{v_duration}分钟</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                            <a href="{v_id}.html" class="text-indigo-600 hover:text-indigo-900">查看详情</a>
                        </td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
        </div>
    </div>
"""

    # 整体评估
    html += f"""
    <div class="bg-white rounded-lg shadow-lg p-8">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">
            <i class="fa fa-stethoscope"></i> 整体评估
        </h2>
        <div class="space-y-4">
            <div class="p-4 bg-blue-50 rounded">
                <h3 class="font-semibold text-gray-800 mb-2">治疗进展</h3>
                <p class="text-gray-700">{overall_progress.get('treatment_progress', '暂无')}</p>
            </div>
            <div class="p-4 bg-green-50 rounded">
                <h3 class="font-semibold text-gray-800 mb-2">咨访关系</h3>
                <p class="text-gray-700">{overall_progress.get('therapeutic_relationship', '暂无')}</p>
            </div>
        </div>
    </div>
"""

    html += '</div>\n'
    html += get_html_footer()

    # 写入文件
    visitor_dir = OUTPUT_DIR / visitor_id
    visitor_dir.mkdir(parents=True, exist_ok=True)
    output_file = visitor_dir / 'comparison.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"    ✓ 生成: {output_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("生成对比视图")
    print("=" * 60)

    if not VISITORS_DIR.exists():
        print(f"错误: 找不到来访者目录 {VISITORS_DIR}")
        return

    # 遍历所有来访者
    for visitor_dir in sorted(VISITORS_DIR.iterdir()):
        if not visitor_dir.is_dir():
            continue

        visitor_id = visitor_dir.name
        profile_file = visitor_dir / 'profile.json'

        if not profile_file.exists():
            continue

        print(f"\n处理来访者: {visitor_id}")

        # 读取档案
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)

        generate_comparison_page(visitor_id, profile_data)

    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
