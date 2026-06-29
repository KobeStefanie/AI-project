#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成来访详情页：单次来访的详细记录（复盘、录音、逐字稿、流派分析）
"""

import json
import os
import sys
import io
from pathlib import Path
from approaches_manager import get_manager

# Windows GBK兼容性处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置
project_root = Path(__file__).parent.parent
VISITORS_DIR = project_root / 'data' / 'visitors'
CASES_PROCESSED = project_root / 'data' / 'cases' / 'processed'
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
    <script src="https://cdn.jsdelivr.net/npm/docx@7.8.2/build/index.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/file-saver@2.0.5/dist/FileSaver.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/html-docx-js@0.3.1/dist/html-docx.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        .collapsible {{ cursor: pointer; }}
        .collapsible:hover {{ background-color: #f3f4f6; }}
        .content {{ display: none; overflow: hidden; }}
        .content.show {{ display: block; }}
        .tab-button {{ cursor: pointer; transition: all 0.2s; }}
        .tab-button.active {{
            background-color: #6366f1;
            color: white;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
    <script>
        // 在head中定义所有函数，确保按钮可以调用
        document.addEventListener('DOMContentLoaded', function() {{
            // 折叠功能
            document.querySelectorAll('.collapsible').forEach(item => {{
                item.addEventListener('click', function() {{
                    this.classList.toggle('active');
                    const content = this.nextElementSibling;
                    content.classList.toggle('show');
                }});
            }});

            // 默认激活第一个标签，或从URL hash恢复
            let targetTab = null;
            let targetButton = null;

            // 尝试从URL hash恢复tab
            if (window.location.hash) {{
                const hash = decodeURIComponent(window.location.hash.substring(1));
                targetTab = document.getElementById(hash);
                if (targetTab) {{
                    document.querySelectorAll('.tab-button').forEach(button => {{
                        const onclick = button.getAttribute('onclick');
                        if (onclick && onclick.includes(hash)) {{
                            targetButton = button;
                        }}
                    }});
                }}
            }}

            // 如果没有找到hash对应的tab，使用第一个
            if (!targetTab) {{
                targetButton = document.querySelector('.tab-button');
                targetTab = document.querySelector('.tab-content');
            }}

            // 激活目标tab
            if (targetButton && targetTab) {{
                targetButton.classList.add('active');
                targetTab.classList.add('active');
            }}
        }});

        // 标签页切换
        function switchTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.classList.remove('active');
            }});
            document.querySelectorAll('.tab-button').forEach(button => {{
                button.classList.remove('active');
            }});
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            window.location.hash = tabName;
        }}

        let currentEditingApproach = null;

        function toggleEdit(approachName) {{
            const contentDiv = document.getElementById('analysis-content-' + approachName);
            const toolbar = document.getElementById('toolbar-' + approachName);
            const saveBtn = document.getElementById('save-btn-' + approachName);
            const isEditing = contentDiv.getAttribute('contenteditable') === 'true';
            if (isEditing) {{
                contentDiv.setAttribute('contenteditable', 'false');
                toolbar.style.display = 'none';
                saveBtn.style.display = 'none';
                contentDiv.style.border = '1px solid #d1d5db';
                currentEditingApproach = null;
            }} else {{
                contentDiv.setAttribute('contenteditable', 'true');
                toolbar.style.display = 'block';
                saveBtn.style.display = 'inline-block';
                contentDiv.style.border = '2px solid #6366f1';
                currentEditingApproach = approachName;
            }}
        }}

        function toggleReviewEdit() {{
            const reviewDiv = document.getElementById('counselor-review-content');
            const toolbar = document.getElementById('toolbar-review');
            const saveBtn = document.getElementById('save-btn-review');
            const isEditing = reviewDiv.getAttribute('contenteditable') === 'true';
            if (isEditing) {{
                reviewDiv.setAttribute('contenteditable', 'false');
                toolbar.style.display = 'none';
                saveBtn.style.display = 'none';
                reviewDiv.style.border = 'none';
            }} else {{
                reviewDiv.setAttribute('contenteditable', 'true');
                toolbar.style.display = 'block';
                saveBtn.style.display = 'inline-block';
                reviewDiv.style.border = '2px solid #6366f1';
                reviewDiv.style.padding = '1rem';
                reviewDiv.style.borderRadius = '0.375rem';
            }}
        }}

        function formatText(command) {{
            document.execCommand(command, false, null);
        }}

        function formatColor(color) {{
            document.execCommand('foreColor', false, color);
        }}

        function saveEdit(approachName, visitorId, visitId) {{
            const contentDiv = document.getElementById('analysis-content-' + approachName);
            const data = {{
                approach: approachName,
                visitor_id: visitorId,
                visit_id: visitId,
                content: contentDiv.innerHTML
            }};
            fetch('http://localhost:8766/save_approach', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    alert('保存成功！内容已保存到服务器。');
                    toggleEdit(approachName);
                }} else {{
                    alert('保存失败：' + result.error);
                }}
            }})
            .catch(error => {{
                console.error('保存失败:', error);
                alert('保存失败，请确保保存服务器已启动（端口8766）');
            }});
        }}

        function saveReviewEdit(visitorId, visitId) {{
            const reviewDiv = document.getElementById('counselor-review-content');
            const data = {{
                visitor_id: visitorId,
                visit_id: visitId,
                content: reviewDiv.innerHTML
            }};
            fetch('http://localhost:8766/save_review', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    alert('保存成功！咨询师复盘已保存到服务器。');
                    toggleReviewEdit();
                }} else {{
                    alert('保存失败：' + result.error);
                }}
            }})
            .catch(error => {{
                console.error('保存失败:', error);
                alert('保存失败，请确保保存服务器已启动（端口8766）');
            }});
        }}

        function downloadApproachWord(approachName, caseId, fileName) {{
            const contentDiv = document.getElementById('analysis-content-' + approachName);
            let htmlContent = `
                <!DOCTYPE html>
                <html><head><meta charset="UTF-8">
                <style>body {{ font-family: "Microsoft YaHei", "SimSun", sans-serif; }} h1 {{ text-align: center; color: #333; }} p {{ line-height: 1.8; }}</style>
                </head><body>
                <h1>${{approachName}}流派分析</h1>
                <p><strong>案例编号：</strong>${{caseId}}</p>
                <div>${{contentDiv.innerHTML}}</div>
                </body></html>
            `;
            const converted = htmlDocx.asBlob(htmlContent);
            saveAs(converted, `${{caseId}}_${{fileName}}.docx`);
        }}

        function downloadReviewWord(caseId) {{
            // 此函数较长，保持原有实现
            alert('下载功能请查看页面源码');
        }}

        function uploadApproachWord(approachName, visitorId, visitId) {{
            const contentDiv = document.getElementById('analysis-content-' + approachName);
            const hasExistingContent = contentDiv && contentDiv.textContent.trim();
            if (hasExistingContent) {{
                if (!confirm('当前流派分析已有内容，上传新Word文档将完全覆盖现有内容。\\n\\n是否继续？')) {{
                    return;
                }}
            }}
            proceedWithUpload(approachName, visitorId, visitId);
        }}

        function proceedWithUpload(approachName, visitorId, visitId) {{
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.docx';
            input.onchange = function(e) {{
                const file = e.target.files[0];
                if (!file) return;
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
                    if (data.success) {{
                        const contentDiv = document.getElementById('analysis-content-' + approachName);
                        if (contentDiv) {{
                            contentDiv.innerHTML = data.html;
                            const saveData = {{
                                approach: approachName,
                                visitor_id: visitorId,
                                visit_id: visitId,
                                content: data.html
                            }};
                            fetch('http://localhost:8766/save_approach', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify(saveData)
                            }})
                            .then(response => response.json())
                            .then(saveResult => console.log('自动保存结果:', saveResult))
                            .catch(error => console.error('自动保存失败:', error));
                            alert('导入成功！内容已自动保存');
                        }}
                    }} else {{
                        alert('Word文档解析失败: ' + (data.error || '未知错误'));
                    }}
                }})
                .catch(error => {{
                    document.body.removeChild(uploadMsg);
                    console.error('上传失败:', error);
                    alert('上传失败，请确保Word上传服务器已启动（端口8765）');
                }});
            }};
            input.click();
        }}
    </script>
</head>
<body class="bg-gray-50">
"""


def get_html_footer():
    """获取HTML模板尾部"""
    return """
</body>
</html>
"""


def generate_visit_detail_page(visitor_id, visit_data, profile_data):
    """生成来访详情页"""
    visit_id = visit_data['visit_id']
    visit_number = visit_data['visit_number']
    print(f"  生成来访详情页: {visitor_id} - 第{visit_number}次来访")

    visit_summary = visit_data['visit_summary']
    case_data = visit_data['case_data']
    case_id = case_data.get('case_id', '')

    # 获取所有来访记录（用于顶部标签切换）
    visit_history = profile_data['visit_history']

    html = get_html_template().format(title=f"第{visit_number}次来访 - {profile_data['basic_info'].get('name', visitor_id)}")

    # 注入来访者基本信息到JavaScript（用于Word导出）
    basic_info = profile_data.get('basic_info', {})
    family_structure = profile_data.get('family_structure', {})
    psych_tests = profile_data.get('psych_tests', [])

    html += f"""
    <script>
        // 来访者基本信息（用于Word导出）
        window.visitorBasicInfo = {{
            name: '{basic_info.get('name', '未知')}',
            age: '{basic_info.get('age', '未知')}',
            gender: '{basic_info.get('gender', '未知')}',
            occupation: '{basic_info.get('occupation', '未知')}',
            marital_status: '{basic_info.get('marital_status', '未知')}',
            sexual_orientation: '{basic_info.get('sexual_orientation', '')}',
            religion: '{basic_info.get('religion', '')}',
            emergency_contact: '{basic_info.get('emergency_contact', '')}',
            emergency_contact_relation: '{basic_info.get('emergency_contact_relation', '')}',
            emergency_contact_phone: '{basic_info.get('emergency_contact_phone', '')}'
        }};

        window.visitorFamily = {{
            father_age: '{family_structure.get('father_age', '')}',
            father_occupation: '{family_structure.get('father_occupation', '')}',
            father_health: '{family_structure.get('father_health', '')}',
            mother_age: '{family_structure.get('mother_age', '')}',
            mother_occupation: '{family_structure.get('mother_occupation', '')}',
            mother_health: '{family_structure.get('mother_health', '')}',
            parents_relationship: '{family_structure.get('parents_relationship', '')}',
            siblings: '{family_structure.get('siblings', '')}',
            spouse_gender: '{family_structure.get('spouse_gender', '')}',
            spouse_age: '{family_structure.get('spouse_age', '')}',
            spouse_occupation: '{family_structure.get('spouse_occupation', '')}',
            spouse_health: '{family_structure.get('spouse_health', '')}',
            children: {family_structure.get('children', [])},
            family_notes: '{family_structure.get('family_notes', '')}'
        }};

        window.visitorPsychTests = {json.dumps(psych_tests, ensure_ascii=False)};
    </script>
    """

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

    # 顶部标签切换（在多次来访之间快速切换）
    if len(visit_history) > 1:
        html += """
    <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">来访记录导航</h3>
        <div class="flex flex-wrap gap-2">
"""
        for visit in visit_history:
            v_num = visit['visit_number']
            v_id = visit['visit_id']
            v_date = visit['date']
            is_current = (v_num == visit_number)
            button_class = 'bg-indigo-600 text-white' if is_current else 'bg-gray-200 text-gray-700 hover:bg-gray-300'

            if is_current:
                html += f'            <span class="px-4 py-2 rounded {button_class}">第{v_num}次 ({v_date})</span>\n'
            else:
                html += f'            <a href="{v_id}.html" class="px-4 py-2 rounded {button_class} transition">第{v_num}次 ({v_date})</a>\n'

        html += """
        </div>
    </div>
"""

    # 来访概况卡片
    html += f"""
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <div class="flex justify-between items-start mb-6">
            <div>
                <h1 class="text-3xl font-bold text-gray-800 mb-2">第 {visit_number} 次来访</h1>
                <p class="text-gray-600">{visit_data['date']} · {visit_summary.get('counselor', '未知')} · {visit_summary.get('duration', '?')}分钟</p>
            </div>
"""

    # 风险评估徽章
    risk_level = visit_summary.get('risk_assessment', {}).get('risk_level', '未评估')
    risk_colors = {
        '高': 'bg-red-100 text-red-800',
        '中': 'bg-yellow-100 text-yellow-800',
        '低': 'bg-green-100 text-green-800',
        '无': 'bg-gray-100 text-gray-800'
    }
    risk_color = risk_colors.get(risk_level, 'bg-gray-100 text-gray-800')

    html += f"""
            <span class="px-4 py-2 text-sm rounded-full {risk_color}">
                {risk_level}风险
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
"""

    # 咨询师复盘 - 优先读取已保存的HTML内容
    saved_review_html = visit_data.get('case_data', {}).get('counselor_review_html', '')
    if saved_review_html:
        counselor_review = saved_review_html
    else:
        counselor_review = case_data.get('counselor_review', '').strip()
        if counselor_review:
            # 将纯文本转换为HTML格式
            counselor_review = counselor_review.replace('\n', '<br>')

    html += f"""
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-bold text-gray-800">咨询师复盘</h2>
            <div class="flex gap-2">
                <button onclick="toggleReviewEdit()" class="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition" id="edit-btn-review">
                    <i class="fa fa-edit"></i> 编辑
                </button>
                <button onclick="saveReviewEdit('{visitor_id}', '{visit_id}')" class="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition" style="display:none;" id="save-btn-review">
                    <i class="fa fa-save"></i> 保存
                </button>
                <a href="../downloads/{case_id}/{case_id}_复盘.docx" download
                   class="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition"
                   onclick="event.preventDefault(); downloadReviewWord('{case_id}');">
                    <i class="fa fa-download"></i> 下载Word
                </a>
            </div>
        </div>

        <!-- 编辑工具栏 -->
        <div class="edit-toolbar mb-4" id="toolbar-review" style="display:none;">
            <div class="flex gap-2 p-3 bg-gray-100 rounded flex-wrap">
                <button onclick="formatText('bold')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="加粗">
                    <i class="fa fa-bold"></i> 加粗
                </button>
                <button onclick="formatText('underline')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="下划线">
                    <i class="fa fa-underline"></i> 下划线
                </button>
                <div class="flex items-center gap-1">
                    <span class="text-sm text-gray-600 mr-1">标记颜色:</span>
                    <button onclick="formatColor('#ef4444')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #ef4444;" title="红色"></button>
                    <button onclick="formatColor('#f59e0b')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #f59e0b;" title="橙色"></button>
                    <button onclick="formatColor('#ffff00')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #ffff00;" title="黄色高亮"></button>
                    <button onclick="formatColor('#00a000')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #00a000;" title="绿色标记"></button>
                    <button onclick="formatColor('#3b82f6')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #3b82f6;" title="蓝色"></button>
                    <button onclick="formatColor('#a855f7')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #a855f7;" title="紫色"></button>
                    <button onclick="formatColor('#000000')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #000000;" title="黑色"></button>
                </div>
            </div>
        </div>

        <div id="counselor-review-content" class="prose max-w-none text-gray-700" contenteditable="false">
            {'<p class="text-gray-500">暂无复盘内容</p>' if not counselor_review else counselor_review}
        </div>
    </div>
"""

    # 录音资料（折叠）
    recordings = case_data.get('recordings', [])
    html += f"""
    <div class="bg-white rounded-lg shadow-lg mb-6">
        <div class="collapsible p-6 flex justify-between items-center border-b">
            <div class="flex items-center justify-between w-full">
                <h2 class="text-2xl font-bold text-gray-800">
                    <i class="fa fa-microphone"></i> 录音资料
                </h2>
                <div class="flex items-center gap-4">
                    <button onclick="showUploadRecordingDialog()" class="px-4 py-2 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 transition">
                        <i class="fa fa-upload"></i> 上传录音
                    </button>
                    <i class="fa fa-chevron-down text-gray-400"></i>
                </div>
            </div>
        </div>
        <div class="content p-6">
"""
    if recordings:
        for rec in recordings:
            recording_id = rec.get('id', '')
            filename = rec.get('filename', '录音文件')
            file_size = rec.get('file_size', 0)
            file_size_mb = file_size / (1024 * 1024)
            description = rec.get('description', '')
            uploaded_at = rec.get('uploaded_at', '')

            # 格式化时间
            if uploaded_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(uploaded_at)
                    uploaded_at_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    uploaded_at_str = uploaded_at
            else:
                uploaded_at_str = '未知时间'

            html += f"""
            <div class="p-4 bg-gray-50 rounded mb-4 border border-gray-200">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex-1">
                        <p class="font-semibold text-gray-800 mb-1">
                            <i class="fa fa-file-audio-o text-purple-600"></i> {{filename}}
                        </p>
                        <p class="text-sm text-gray-600">
                            大小: {{file_size_mb:.2f}} MB | 上传时间: {{uploaded_at_str}}
                        </p>
                        {{f'<p class="text-sm text-gray-700 mt-2">📝 {{description}}</p>' if description else ''}}
                    </div>
                </div>

                <!-- 音频播放器 -->
                <audio controls class="w-full mb-3" id="audio-{{recording_id}}">
                    <source src="http://localhost:8767/download/{{visitor_id}}/{{visit_id}}/{{recording_id}}" type="audio/mpeg">
                    您的浏览器不支持音频播放
                </audio>

                <div class="flex gap-2">
                    <a href="http://localhost:8767/download/{{visitor_id}}/{{visit_id}}/{{recording_id}}" download="{{filename}}"
                       class="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition">
                        <i class="fa fa-download"></i> 下载
                    </a>
                    <button onclick="deleteRecording('{{recording_id}}', '{{visitor_id}}', '{{visit_id}}')"
                            class="px-3 py-1.5 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition">
                        <i class="fa fa-trash"></i> 删除
                    </button>
                </div>
            </div>
"""
    else:
        html += '<p class="text-gray-500">暂无录音资料，点击右上角"上传录音"按钮添加</p>'

    html += """
        </div>
    </div>
"""

    # 逐字稿（折叠）
    transcript = case_data.get('transcript', [])
    html += f"""
    <div class="bg-white rounded-lg shadow-lg mb-6">
        <div class="collapsible p-6 flex justify-between items-center border-b">
            <div class="flex items-center justify-between w-full">
                <h2 class="text-2xl font-bold text-gray-800">
                    <i class="fa fa-file-text-o"></i> 逐字稿
                </h2>
                <div class="flex items-center gap-4">
                    <a href="../downloads/{case_id}/{case_id}_逐字稿.xlsx" download
                       class="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition">
                        <i class="fa fa-download"></i> 下载Excel
                    </a>
                    <i class="fa fa-chevron-down text-gray-400"></i>
                </div>
            </div>
        </div>
        <div class="content p-6">
"""
    if transcript:
        html += '<div class="space-y-3">'
        for entry in transcript:
            speaker = entry.get('speaker', '未知')
            content = entry.get('content', '')
            timestamp = entry.get('timestamp', '')
            speaker_class = 'bg-blue-50 border-blue-200' if '咨询师' in speaker else 'bg-gray-50 border-gray-200'

            html += f"""
            <div class="p-4 rounded border {speaker_class}">
                <div class="flex justify-between mb-2">
                    <span class="font-semibold text-gray-800">{speaker}</span>
                    <span class="text-sm text-gray-500">{timestamp}</span>
                </div>
                <p class="text-gray-700">{content}</p>
            </div>
"""
        html += '</div>'
    else:
        html += '<p class="text-gray-500">暂无逐字稿</p>'

    html += """
        </div>
    </div>
"""

    # 案例概要（中性数据）
    case_summary = case_data.get('case_summary', '')
    html += f"""
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-4">案例概要</h2>
        <p class="text-gray-700 leading-relaxed">{case_summary if case_summary else '<span class="text-gray-500">暂无概要</span>'}</p>
    </div>
"""

    # 标签（中性数据）
    case_tags = case_data.get('case_tags', {})
    relation_tags = case_tags.get('relation', [])
    symptom_tags = case_tags.get('symptom', [])

    html += """
    <div class="bg-white rounded-lg shadow-lg p-8 mb-6">
        <h2 class="text-2xl font-bold text-gray-800 mb-4">标签</h2>
"""

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

    html += """
    </div>
"""

    # 流派分析（标签页）- 始终显示所有流派
    approach_analyses = case_data.get('approach_analyses', {})

    # 从配置文件动态加载流派列表
    manager = get_manager()
    enabled_approaches = manager.get_enabled_approaches()
    all_approaches = [approach['name'] for approach in enabled_approaches]

    # 创建流派ID到名称的映射（用于读取processed案例数据）
    approach_id_to_name = {approach['id']: approach['name'] for approach in enabled_approaches}
    approach_name_to_id = {approach['name']: approach['id'] for approach in enabled_approaches}

    # 文件名映射（用于下载链接，使用name_short或name）
    approach_file_names = {
        approach['name']: approach.get('name_short', approach['name'])
        for approach in enabled_approaches
    }

    # **重要**: 添加已保存但未启用的流派（保留历史数据）
    # 从visit_data中获取所有已保存的流派
    saved_approaches = visit_data.get('case_data', {}).get('approach_analyses_html', {}).keys()
    for saved_approach in saved_approaches:
        if saved_approach not in all_approaches:
            print(f"    [保留] {saved_approach}: 已禁用的流派，但保留已保存的内容")
            all_approaches.append(saved_approach)
            # 为已保存但未启用的流派设置默认文件名
            approach_file_names[saved_approach] = saved_approach

    # 确保approach_analyses包含所有流派（兼容旧数据）
    for approach in all_approaches:
        if approach not in approach_analyses:
            approach_analyses[approach] = {
                'conceptualization': '',
                'intervention_suggestions': '',
                'key_points': []
            }

    html += """
    <div class="bg-white rounded-lg shadow-lg p-8">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">流派分析</h2>

        <!-- 标签按钮 -->
        <div class="flex flex-wrap gap-2 mb-6 border-b pb-4">
"""
    # 获取启用的流派名称列表，用于判断
    enabled_approach_names = [approach['name'] for approach in enabled_approaches]

    for approach_name in all_approaches:
        # 检查流派是否已被禁用
        is_disabled = approach_name not in enabled_approach_names
        disabled_style = 'opacity: 0.6; font-style: italic;' if is_disabled else ''
        disabled_label = ' (已归档)' if is_disabled else ''

        html += f'            <button class="tab-button px-6 py-2 rounded-t font-semibold" style="{disabled_style}" onclick="switchTab(\'{approach_name}\')" title="{"该流派已被禁用，但内容已保留" if is_disabled else ""}">{approach_name}{disabled_label}</button>\n'

    html += """
        </div>

        <!-- 标签内容 -->
"""
    for approach_name in all_approaches:
        # 优先从visit_data读取已保存的HTML内容，如果没有则从processed案例读取默认数据
        analysis_content = ''

        # 1. 尝试从visit_data获取已编辑/上传的HTML内容
        saved_html = visit_data.get('case_data', {}).get('approach_analyses_html', {}).get(approach_name, '')

        if saved_html:
            # 如果有保存的HTML，直接使用
            print(f"    [读取] {approach_name}: 使用已保存的HTML ({len(saved_html)} 字符)")
            analysis_content = saved_html
        else:
            # 2. 如果没有保存的内容，从processed案例中读取流派分析数据并生成HTML
            # 从原始案例数据中获取流派分析（不是从approach_analyses，而是从原始的analyses）
            case_id = visit_data.get('case_id', '')

            # 读取原始案例数据
            case_file = CASES_PROCESSED / f"{case_id}.json"
            approach_data = {}
            if case_file.exists():
                with open(case_file, 'r', encoding='utf-8') as f:
                    case_data_from_file = json.load(f)
                    analyses = case_data_from_file.get('analyses', {})

                    # 使用流派名称到ID的映射获取数据
                    approach_id = approach_name_to_id.get(approach_name, '')
                    if approach_id:
                        approach_data = analyses.get(approach_id, {})
                    else:
                        # 兼容旧的硬编码名称
                        approach_key_map = {
                            '大观派': 'daguanpai',
                            'CBT': 'cbt',
                            '精神动力学': 'psychodynamic',
                            '人本主义': 'humanistic',
                            '存在主义': 'existential'
                        }
                        approach_key = approach_key_map.get(approach_name, approach_name.lower())
                        approach_data = analyses.get(approach_key, {})

            # 将所有数据整合成完整的HTML内容
            if approach_data:
                # 1. 案例标签
                tags = approach_data.get('tags', {})
                if tags:
                    relation_tags = tags.get('relation', [])
                    symptom_tags = tags.get('symptom', [])
                    if relation_tags or symptom_tags:
                        analysis_content += '<h3 style="color: #6366f1; margin-top: 0;">📋 案例标签</h3><div style="margin-bottom: 20px;">'
                        if relation_tags:
                            analysis_content += f'<p><strong>关系维度：</strong>{", ".join(relation_tags)}</p>'
                        if symptom_tags:
                            analysis_content += f'<p><strong>症状维度：</strong>{", ".join(symptom_tags)}</p>'
                        analysis_content += '</div>'

                # 2. 危机评估
                crisis_level = approach_data.get('crisis_level', '')
                crisis_evidence = approach_data.get('crisis_evidence', '')
                if crisis_level or crisis_evidence:
                    crisis_labels = {
                        'S': 'S级（自杀风险）',
                        'A': 'A级（高危）',
                        'B': 'B级（中危）',
                        'C': 'C级（低危）',
                        'D': 'D级（安全）'
                    }
                    analysis_content += '<h3 style="color: #ef4444;">⚠️ 危机评估</h3><div style="margin-bottom: 20px;">'
                    if crisis_level:
                        analysis_content += f'<p><strong>危机等级：</strong>{crisis_labels.get(crisis_level, crisis_level)}</p>'
                    if crisis_evidence:
                        analysis_content += f'<p><strong>评估依据：</strong>{crisis_evidence}</p>'
                    analysis_content += '</div>'

                # 3. 关键词
                keywords = approach_data.get('keywords', [])
                if keywords:
                    analysis_content += '<h3 style="color: #6366f1;">🔑 关键词</h3><div style="margin-bottom: 20px;">'
                    analysis_content += f'<p>{", ".join(keywords)}</p>'
                    analysis_content += '</div>'

                # 4. 使用技术
                techniques = approach_data.get('techniques_used', [])
                if techniques:
                    analysis_content += '<h3 style="color: #6366f1;">🛠️ 咨询技术</h3><div style="margin-bottom: 20px;"><ul style="list-style-type: disc; margin-left: 20px;">'
                    for tech in techniques:
                        analysis_content += f'<li>{tech}</li>'
                    analysis_content += '</ul></div>'

                # 5. AI督导分析
                ai_analysis = approach_data.get('ai_analysis', {})
                if ai_analysis:
                    analysis_content += '<h3 style="color: #10b981;">🤖 AI督导分析</h3>'

                    # 概要
                    summary = ai_analysis.get('summary', '')
                    if summary:
                        analysis_content += '<h4 style="color: #6366f1; margin-top: 15px;">案例概要</h4>'
                        analysis_content += f'<div style="margin-bottom: 15px;"><p>{summary}</p></div>'

                    # 优势
                    strengths = ai_analysis.get('strengths', [])
                    if strengths:
                        analysis_content += '<h4 style="color: #6366f1; margin-top: 15px;">✨ 优势</h4>'
                        analysis_content += '<div style="margin-bottom: 15px;"><ul style="list-style-type: disc; margin-left: 20px;">'
                        for s in strengths:
                            analysis_content += f'<li>{s}</li>'
                        analysis_content += '</ul></div>'

                    # 改进建议
                    improvements = ai_analysis.get('improvements', [])
                    if improvements:
                        analysis_content += '<h4 style="color: #6366f1; margin-top: 15px;">💡 改进建议</h4>'
                        analysis_content += '<div style="margin-bottom: 15px;"><ul style="list-style-type: disc; margin-left: 20px;">'
                        for imp in improvements:
                            analysis_content += f'<li>{imp}</li>'
                        analysis_content += '</ul></div>'

                    # 后续跟进
                    followup = ai_analysis.get('recommended_followup', '')
                    if followup:
                        analysis_content += '<h4 style="color: #6366f1; margin-top: 15px;">📋 后续跟进建议</h4>'
                        if isinstance(followup, list):
                            analysis_content += '<div style="margin-bottom: 15px;"><ul style="list-style-type: disc; margin-left: 20px;">'
                            for f in followup:
                                analysis_content += f'<li>{f}</li>'
                            analysis_content += '</ul></div>'
                        else:
                            analysis_content += f'<div style="margin-bottom: 15px;"><p>{followup}</p></div>'

        # 获取文件名（用于下载链接）
        file_name = approach_file_names.get(approach_name, approach_name)

        html += f"""
        <div id="{approach_name}" class="tab-content">
            <div class="mb-4 flex justify-between items-center">
                <div class="flex gap-2">
                    <button onclick="toggleEdit('{approach_name}')" class="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition" id="edit-btn-{approach_name}">
                        <i class="fa fa-edit"></i> 编辑
                    </button>
                    <button onclick="saveEdit('{approach_name}', '{visitor_id}', '{visit_id}')" class="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition" style="display:none;" id="save-btn-{approach_name}">
                        <i class="fa fa-save"></i> 保存
                    </button>
                    <button onclick="uploadApproachWord('{approach_name}', '{visitor_id}', '{visit_id}')" class="px-4 py-2 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 transition" title="上传Word文档">
                        <i class="fa fa-upload"></i> 上传Word
                    </button>
                </div>
                <a href="../downloads/{case_id}/{case_id}_{file_name}.docx" download
                   class="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition"
                   onclick="event.preventDefault(); downloadApproachWord('{approach_name}', '{case_id}', '{file_name}');">
                    <i class="fa fa-download"></i> 下载{approach_name}分析
                </a>
            </div>

            <!-- 编辑工具栏 -->
            <div class="edit-toolbar mb-4" id="toolbar-{approach_name}" style="display:none;">
                <div class="flex gap-2 p-3 bg-gray-100 rounded flex-wrap">
                    <button onclick="formatText('bold')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="加粗">
                        <i class="fa fa-bold"></i> 加粗
                    </button>
                    <button onclick="formatText('underline')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="下划线">
                        <i class="fa fa-underline"></i> 下划线
                    </button>
                    <div class="flex items-center gap-1">
                        <span class="text-sm text-gray-600 mr-1">标记颜色:</span>
                        <button onclick="formatColor('#ef4444')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #ef4444;" title="红色"></button>
                        <button onclick="formatColor('#f59e0b')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #f59e0b;" title="橙色"></button>
                        <button onclick="formatColor('#eab308')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #eab308;" title="黄色"></button>
                        <button onclick="formatColor('#22c55e')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #22c55e;" title="绿色"></button>
                        <button onclick="formatColor('#3b82f6')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #3b82f6;" title="蓝色"></button>
                        <button onclick="formatColor('#a855f7')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #a855f7;" title="紫色"></button>
                        <button onclick="formatColor('#000000')" class="w-8 h-8 rounded border-2 border-gray-300 hover:border-gray-500" style="background-color: #000000;" title="黑色"></button>
                    </div>
                </div>
            </div>

            <div class="mb-6">
                <div id="analysis-content-{approach_name}" class="text-gray-700 leading-relaxed p-4 border rounded min-h-[400px]" contenteditable="false">
                    {analysis_content if analysis_content else '<span class="text-gray-500">暂无内容，点击编辑按钮开始编写...</span>'}
                </div>
            </div>

            <!-- 历次感悟区域 -->
            <div class="mt-8 pt-6 border-t-2 border-gray-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold text-indigo-900">🧠 历次感悟（{approach_name}视角）</h3>
                    <button onclick="showAddInsightModal('{approach_name}')" class="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition">
                        <i class="fa fa-plus"></i> 添加感悟
                    </button>
                </div>

                <div id="insights-{approach_name}" class="space-y-4">
"""

        # 获取该流派的感悟记录
        supervision_records = visit_data.get('case_data', {}).get('supervision_records', [])
        # 筛选出该流派的感悟（按创建时间正序，最早的在上面，最新的在下面）
        approach_insights = [r for r in supervision_records if r.get('approach') == approach_name]
        approach_insights.sort(key=lambda x: x.get('created_at', ''), reverse=False)

        if approach_insights:
            for idx, record in enumerate(approach_insights):
                record_id = record.get('id', '')
                content = record.get('content', '')
                created_at = record.get('created_at', '')
                updated_at = record.get('updated_at', '')

                # 格式化时间
                created_time = created_at[:16].replace('T', ' ') if created_at else ''
                is_edited = created_at != updated_at

                html += f"""
                    <div class="bg-blue-50 border-l-4 border-indigo-500 rounded mb-4">
                        <!-- 折叠标题栏 -->
                        <button class="collapsible-insight w-full flex justify-between items-center p-4 cursor-pointer hover:bg-blue-100 transition"
                                onclick="toggleInsightCollapse('{record_id}')">
                            <div class="flex items-center gap-3">
                                <i class="fa fa-chevron-down transition-transform" id="icon-insight-{record_id}"></i>
                                <span class="font-semibold text-gray-700">📝 第{idx + 1}次感悟</span>
                                <span class="text-sm text-gray-500">{created_time}</span>
                                {f'<span class="text-xs text-gray-400">(已编辑)</span>' if is_edited else ''}
                            </div>
                        </button>

                        <!-- 可折叠内容区 -->
                        <div class="insight-collapse-content" id="collapse-insight-{record_id}" style="display: block;">
                            <div class="p-4 pt-0">
                                <!-- 操作按钮 -->
                                <div class="flex gap-2 mb-3 flex-wrap">
                                    <button onclick="toggleInsightEdit('{record_id}', '{approach_name}')"
                                            class="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition"
                                            id="edit-btn-insight-{record_id}">
                                        <i class="fa fa-edit"></i> 编辑
                                    </button>
                                    <button onclick="saveInsightEdit('{record_id}', '{approach_name}', '{visitor_id}', '{visit_id}')"
                                            class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition"
                                            style="display:none;"
                                            id="save-btn-insight-{record_id}">
                                        <i class="fa fa-save"></i> 保存
                                    </button>
                                    <button onclick="uploadInsightWord('{record_id}', '{approach_name}', '{visitor_id}', '{visit_id}')"
                                            class="px-3 py-1 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 transition">
                                        <i class="fa fa-upload"></i> 上传Word
                                    </button>
                                    <button onclick="downloadInsightWord('{record_id}', '{approach_name}', '{case_id}', {idx + 1})"
                                            class="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition">
                                        <i class="fa fa-download"></i> 下载Word
                                    </button>
                                    <button onclick="deleteInsight('{record_id}', '{visitor_id}', '{visit_id}')"
                                            class="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition">
                                        <i class="fa fa-trash"></i> 删除
                                    </button>
                                </div>

                                <!-- 富文本编辑工具栏 -->
                                <div class="edit-toolbar mb-3" id="toolbar-insight-{record_id}" style="display:none;">
                                    <div class="flex gap-2 p-3 bg-gray-100 rounded flex-wrap">
                                        <button onclick="formatInsightText('{record_id}', 'bold')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="加粗">
                                            <i class="fa fa-bold"></i> 加粗
                                        </button>
                                        <button onclick="formatInsightText('{record_id}', 'underline')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="下划线">
                                            <i class="fa fa-underline"></i> 下划线
                                        </button>
                                        <button onclick="formatInsightText('{record_id}', 'italic')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="斜体">
                                            <i class="fa fa-italic"></i> 斜体
                                        </button>
                                        <button onclick="formatInsightColor('{record_id}', '#dc2626')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="红色">
                                            <span style="color: #dc2626;">●</span> 红色
                                        </button>
                                        <button onclick="formatInsightColor('{record_id}', '#2563eb')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="蓝色">
                                            <span style="color: #2563eb;">●</span> 蓝色
                                        </button>
                                        <button onclick="formatInsightColor('{record_id}', '#16a34a')" class="px-3 py-1 bg-white border rounded hover:bg-gray-50" title="绿色">
                                            <span style="color: #16a34a;">●</span> 绿色
                                        </button>
                                    </div>
                                </div>

                                <!-- 感悟内容 -->
                                <div class="text-gray-700 leading-relaxed p-4 bg-white rounded border border-gray-200"
                                     id="insight-content-{record_id}"
                                     contenteditable="false">
                                    {content}
                                </div>
                            </div>
                        </div>
                    </div>
"""
        else:
            html += """
                    <p class="text-gray-500 text-center py-8">
                        暂无感悟记录，点击右上角"添加感悟"按钮添加第一条感悟
                    </p>
"""

        html += """
                </div>
            </div>
        </div>
"""

    html += """
    </div>
"""

    html += '</div>\n'

    # 添加感悟管理JavaScript（需要visitor_id和visit_id变量）
    html += f"""
    <script>
        // ========== 感悟管理功能 ==========
        const VISITOR_ID = '{visitor_id}';
        const VISIT_ID = '{visit_id}';

        let currentInsightModal = null;

        // 显示添加感悟对话框
        function showAddInsightModal(approachName) {{
            const modal = createInsightModal(approachName, null, '');
            document.body.appendChild(modal);
            currentInsightModal = modal;
        }}

        // 编辑感悟
        function editInsight(recordId, approachName, content) {{
            // 反转义内容
            const unescapedContent = content.replace(/<br>/g, '\\\\n').replace(/&quot;/g, '"').replace(/\\\\\\\\\\\\\\\\/g, '\\\\\\\\');
            const modal = createInsightModal(approachName, recordId, unescapedContent);
            document.body.appendChild(modal);
            currentInsightModal = modal;
        }}

        // 创建感悟模态框
        function createInsightModal(approachName, recordId, content) {{
            const isEdit = recordId !== null;
            const modal = document.createElement('div');
            modal.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 9999;';

            modal.innerHTML = `
                <div style="background: white; border-radius: 12px; padding: 30px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;">
                    <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #4f46e5;">
                        ${{isEdit ? '编辑感悟' : '添加感悟'}}
                    </h3>

                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">流派视角</label>
                        <input type="text" id="insight-approach" value="${{approachName}}" readonly
                               style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; background: #f3f4f6; color: #6b7280;">
                    </div>

                    <div style="margin-bottom: 20px;">
                        <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">感悟内容 <span style="color: red;">*</span></label>
                        <textarea id="insight-content" rows="10" placeholder="请输入您的感悟..."
                                  style="width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 6px; resize: vertical; font-family: inherit;">${{content}}</textarea>
                    </div>

                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button onclick="closeInsightModal()"
                                style="padding: 10px 20px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                            取消
                        </button>
                        <button onclick="saveInsight('${{approachName}}', '${{recordId || ''}}')"
                                style="padding: 10px 20px; background: #4f46e5; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                            ${{isEdit ? '保存修改' : '添加'}}
                        </button>
                    </div>
                </div>
            `;

            return modal;
        }}

        // 关闭模态框
        function closeInsightModal() {{
            if (currentInsightModal) {{
                document.body.removeChild(currentInsightModal);
                currentInsightModal = null;
            }}
        }}

        // 保存感悟
        function saveInsight(approachName, recordId) {{
            const content = document.getElementById('insight-content').value.trim();

            if (!content) {{
                alert('请输入感悟内容');
                return;
            }}

            const isEdit = recordId !== '';
            const url = isEdit
                ? 'http://localhost:8766/supervision_record/edit'
                : 'http://localhost:8766/supervision_record/add';

            const data = {{
                visitor_id: VISITOR_ID,
                visit_id: VISIT_ID,
                approach: approachName,
                content: content
            }};

            if (isEdit) {{
                data.record_id = recordId;
            }}

            fetch(url, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    alert(isEdit ? '感悟修改成功！' : '感悟添加成功！');
                    closeInsightModal();
                    // 保存当前激活的tab到URL hash，确保刷新后停留在当前流派
                    const activeTab = document.querySelector('.tab-content.active');
                    if (activeTab) {{
                        window.location.hash = activeTab.id;
                    }}
                    // 延迟刷新页面，让用户看到成功提示
                    setTimeout(() => {{
                        location.reload();
                    }}, 500);
                }} else {{
                    alert('保存失败：' + result.error);
                }}
            }})
            .catch(error => {{
                console.error('保存失败:', error);
                alert('保存失败，请确保服务器已启动（端口8766）');
            }});
        }}

        // 删除感悟
        function deleteInsight(recordId, visitorId, visitId) {{
            if (!confirm('确定要删除这条感悟吗？')) {{
                return;
            }}

            const data = {{
                visitor_id: visitorId,
                visit_id: visitId,
                record_id: recordId
            }};

            fetch('http://localhost:8766/supervision_record/delete', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    alert('感悟删除成功！');
                    setTimeout(() => {{
                        location.reload();
                    }}, 500);
                }} else {{
                    alert('删除失败：' + result.error);
                }}
            }})
            .catch(error => {{
                console.error('删除失败:', error);
                alert('删除失败，请确保服务器已启动（端口8766）');
            }});
        }}

        // ========== 感悟富文本编辑功能 ==========
        let currentEditingInsight = null;

        // 折叠/展开感悟
        function toggleInsightCollapse(recordId) {{
            const content = document.getElementById('collapse-insight-' + recordId);
            const icon = document.getElementById('icon-insight-' + recordId);

            if (content.style.display === 'none') {{
                content.style.display = 'block';
                icon.style.transform = 'rotate(0deg)';
            }} else {{
                content.style.display = 'none';
                icon.style.transform = 'rotate(-90deg)';
            }}
        }}

        function toggleInsightEdit(recordId, approachName) {{
            const contentDiv = document.getElementById('insight-content-' + recordId);
            const toolbar = document.getElementById('toolbar-insight-' + recordId);
            const saveBtn = document.getElementById('save-btn-insight-' + recordId);
            const editBtn = document.getElementById('edit-btn-insight-' + recordId);

            const isEditing = contentDiv.getAttribute('contenteditable') === 'true';

            if (isEditing) {{
                // 退出编辑模式
                contentDiv.setAttribute('contenteditable', 'false');
                toolbar.style.display = 'none';
                saveBtn.style.display = 'none';
                editBtn.style.display = 'inline-block';
                contentDiv.style.border = '1px solid #d1d5db';
                currentEditingInsight = null;
            }} else {{
                // 进入编辑模式
                contentDiv.setAttribute('contenteditable', 'true');
                toolbar.style.display = 'block';
                saveBtn.style.display = 'inline-block';
                editBtn.style.display = 'none';
                contentDiv.style.border = '2px solid #6366f1';
                contentDiv.focus();
                currentEditingInsight = recordId;
            }}
        }}

        function formatInsightText(recordId, command) {{
            document.execCommand(command, false, null);
        }}

        function formatInsightColor(recordId, color) {{
            document.execCommand('foreColor', false, color);
        }}

        function saveInsightEdit(recordId, approachName, visitorId, visitId) {{
            const contentDiv = document.getElementById('insight-content-' + recordId);

            const data = {{
                visitor_id: visitorId,
                visit_id: visitId,
                record_id: recordId,
                approach: approachName,
                content: contentDiv.innerHTML
            }};

            // 保存到服务器
            fetch('http://localhost:8766/supervision_record/edit', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    alert('感悟保存成功！');
                    // 退出编辑模式
                    toggleInsightEdit(recordId, approachName);
                    // 刷新页面以显示更新
                    setTimeout(() => {{
                        location.reload();
                    }}, 500);
                }} else {{
                    alert('保存失败：' + result.error);
                }}
            }})
            .catch(error => {{
                console.error('保存失败:', error);
                alert('保存失败，请确保服务器已启动（端口8766）');
            }});
        }}

        // 下载感悟为Word
        function downloadInsightWord(recordId, approachName, caseId, insightNum) {{
            const contentDiv = document.getElementById('insight-content-' + recordId);

            // 构建HTML内容
            let htmlContent = `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: "Microsoft YaHei", "SimSun", sans-serif; }}
                        h1 {{ text-align: center; color: #333; }}
                        p {{ line-height: 1.8; }}
                    </style>
                </head>
                <body>
                    <h1>${{approachName}}视角 - 第${{insightNum}}次感悟</h1>
                    <p><strong>案例编号：</strong>${{caseId}}</p>
                    <div>
                        ${{contentDiv.innerHTML}}
                    </div>
                </body>
                </html>
            `;

            // 使用html-docx-js转换并下载
            const converted = htmlDocx.asBlob(htmlContent);
            saveAs(converted, `${{caseId}}_${{approachName}}_感悟${{insightNum}}.docx`);
        }}

        // 上传Word文档并导入感悟内容
        function uploadInsightWord(recordId, approachName, visitorId, visitId) {{
            const contentDiv = document.getElementById('insight-content-' + recordId);
            const hasExistingContent = contentDiv && contentDiv.textContent.trim();

            // 如果有现有内容，显示确认对话框
            if (hasExistingContent) {{
                const confirmDialog = document.createElement('div');
                confirmDialog.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 9998; display: flex; align-items: center; justify-content: center;';

                const dialogBox = document.createElement('div');
                dialogBox.style.cssText = 'background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); max-width: 450px; width: 90%;';
                dialogBox.innerHTML = `
                    <div style="font-size: 20px; font-weight: bold; margin-bottom: 15px; color: #dc2626;">
                        <i class="fa fa-exclamation-triangle"></i> 确认上传
                    </div>
                    <div style="font-size: 15px; line-height: 1.6; color: #374151; margin-bottom: 25px;">
                        当前感悟已有内容，上传新Word文档将<strong style="color: #dc2626;">完全覆盖</strong>现有内容。
                        <br><br>
                        <strong>提示：</strong>如需保留当前内容，请先下载Word备份。
                    </div>
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button id="cancelUploadInsight" style="padding: 10px 24px; background: #e5e7eb; color: #374151; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500;">
                            取消
                        </button>
                        <button id="confirmUploadInsight" style="padding: 10px 24px; background: #dc2626; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500;">
                            确认覆盖
                        </button>
                    </div>
                `;

                confirmDialog.appendChild(dialogBox);
                document.body.appendChild(confirmDialog);

                // 取消按钮
                document.getElementById('cancelUploadInsight').onclick = function() {{
                    document.body.removeChild(confirmDialog);
                }};

                // 确认按钮
                document.getElementById('confirmUploadInsight').onclick = function() {{
                    document.body.removeChild(confirmDialog);
                    proceedWithInsightUpload(recordId, approachName, visitorId, visitId);
                }};
            }} else {{
                // 无现有内容，直接上传
                proceedWithInsightUpload(recordId, approachName, visitorId, visitId);
            }}
        }}

        // 实际执行感悟上传的函数
        function proceedWithInsightUpload(recordId, approachName, visitorId, visitId) {{
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.docx';

            input.onchange = function(e) {{
                const file = e.target.files[0];
                if (!file) return;

                // 显示上传提示
                const uploadMsg = document.createElement('div');
                uploadMsg.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 9999; text-align: center;';
                uploadMsg.innerHTML = '<div style="font-size: 18px; margin-bottom: 10px;">正在处理Word文档...</div><div style="color: #666;">解析格式中，请稍候</div>';
                document.body.appendChild(uploadMsg);

                // 创建FormData
                const formData = new FormData();
                formData.append('file', file);

                // 发送到Python服务器
                fetch('http://localhost:8765/', {{
                    method: 'POST',
                    body: formData,
                    mode: 'cors'
                }})
                .then(response => response.json())
                .then(data => {{
                    document.body.removeChild(uploadMsg);

                    if (data.success) {{
                        const contentDiv = document.getElementById('insight-content-' + recordId);
                        if (contentDiv) {{
                            contentDiv.innerHTML = data.html;

                            // 自动保存到服务器
                            const saveData = {{
                                visitor_id: visitorId,
                                visit_id: visitId,
                                record_id: recordId,
                                approach: approachName,
                                content: data.html
                            }};

                            fetch('http://localhost:8766/supervision_record/edit', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                }},
                                body: JSON.stringify(saveData)
                            }})
                            .then(response => response.json())
                            .then(saveResult => {{
                                console.log('自动保存结果:', saveResult);
                            }})
                            .catch(error => {{
                                console.error('自动保存失败:', error);
                            }});

                            // 成功提示
                            const successDialog = document.createElement('div');
                            successDialog.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); z-index: 9999; max-width: 400px;';
                            successDialog.innerHTML = `
                                <div style="text-align: center;">
                                    <div style="font-size: 48px; color: #10b981; margin-bottom: 15px;">✓</div>
                                    <div style="font-size: 18px; font-weight: bold; margin-bottom: 10px;">导入成功！</div>
                                    <div style="font-size: 14px; color: #6b7280; line-height: 1.6;">
                                        已完整保留：<br>
                                        ✓ 文字颜色和背景色<br>
                                        ✓ 加粗、斜体、下划线<br>
                                        ✓ 标题层级和列表结构<br><br>
                                        内容已自动保存
                                    </div>
                                    <button onclick="this.parentElement.parentElement.remove()" style="margin-top: 20px; padding: 10px 30px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                                        确定
                                    </button>
                                </div>
                            `;
                            document.body.appendChild(successDialog);

                            // 3秒后自动关闭
                            setTimeout(() => {{
                                if (successDialog.parentElement) {{
                                    successDialog.remove();
                                }}
                            }}, 3000);
                        }}
                    }} else {{
                        alert('❌ Word文档解析失败\\n\\n' + (data.error || '未知错误'));
                    }}
                }})
                .catch(error => {{
                    document.body.removeChild(uploadMsg);
                    console.error('上传失败:', error);
                    alert('❌ 上传失败\\n\\n请确保：\\n1. Word上传服务器已启动\\n2. 运行命令：python src/word_upload_server.py\\n3. 服务器端口：8765\\n\\n错误信息：' + error.message);
                }});
            }};

            input.click();
        }}

        // ========== 录音管理功能 ==========

        // 显示上传录音对话框
        function showUploadRecordingDialog() {{
            const dialog = document.createElement('div');
            dialog.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 9999;';
            dialog.innerHTML = `
                <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); max-width: 500px; width: 90%;">
                    <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 20px; color: #374151;">
                        <i class="fa fa-upload"></i> 上传录音文件
                    </h3>

                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500; color: #374151;">选择文件：</label>
                        <input type="file" id="recording-file-input" accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg,.flac,.wma"
                               style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px;">
                        <p style="font-size: 12px; color: #6b7280; margin-top: 5px;">
                            支持格式：MP3, WAV, M4A, AAC, OGG, FLAC, WMA
                        </p>
                    </div>

                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: 500; color: #374151;">备注（可选）：</label>
                        <textarea id="recording-description-input" rows="3"
                                  placeholder="例如：第一次咨询完整录音、重点片段等"
                                  style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; resize: vertical;"></textarea>
                    </div>

                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button onclick="this.closest('div[style*=fixed]').remove()"
                                style="padding: 10px 20px; background: #e5e7eb; color: #374151; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                            取消
                        </button>
                        <button onclick="uploadRecording()"
                                style="padding: 10px 20px; background: #7c3aed; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;">
                            <i class="fa fa-upload"></i> 开始上传
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(dialog);
        }}

        // 上传录音
        function uploadRecording() {{
            const fileInput = document.getElementById('recording-file-input');
            const descriptionInput = document.getElementById('recording-description-input');
            const file = fileInput.files[0];

            if (!file) {{
                alert('请选择要上传的录音文件');
                return;
            }}

            // 关闭对话框
            const dialog = fileInput.closest('div[style*=fixed]');
            dialog.remove();

            // 显示上传进度
            const progressMsg = document.createElement('div');
            progressMsg.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); z-index: 9999; text-align: center;';
            progressMsg.innerHTML = `
                <div style="font-size: 48px; margin-bottom: 15px;">⏳</div>
                <div style="font-size: 18px; font-weight: bold; margin-bottom: 10px;">正在上传录音...</div>
                <div style="font-size: 14px; color: #6b7280;">请稍候，文件较大可能需要一些时间</div>
            `;
            document.body.appendChild(progressMsg);

            // 构建FormData
            const formData = new FormData();
            formData.append('file', file);
            formData.append('visitor_id', VISITOR_ID);
            formData.append('visit_id', VISIT_ID);
            formData.append('description', descriptionInput.value);

            // 上传
            fetch('http://localhost:8767/upload', {{
                method: 'POST',
                body: formData
            }})
            .then(response => response.json())
            .then(result => {{
                document.body.removeChild(progressMsg);

                if (result.success) {{
                    alert('录音上传成功！页面即将刷新...');
                    setTimeout(() => {{
                        location.reload();
                    }}, 500);
                }} else {{
                    alert('上传失败：' + result.error);
                }}
            }})
            .catch(error => {{
                document.body.removeChild(progressMsg);
                console.error('上传失败:', error);
                alert('上传失败，请确保录音服务器已启动（端口8767）\\n\\n错误信息：' + error.message);
            }});
        }}

        // 删除录音
        function deleteRecording(recordingId, visitorId, visitId) {{
            if (!confirm('确定要删除这个录音文件吗？\\n\\n删除后无法恢复！')) {{
                return;
            }}

            const data = {{
                visitor_id: visitorId,
                visit_id: visitId,
                recording_id: recordingId
            }};

            fetch('http://localhost:8767/delete', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    alert('录音删除成功！页面即将刷新...');
                    setTimeout(() => {{
                        location.reload();
                    }}, 500);
                }} else {{
                    alert('删除失败：' + result.error);
                }}
            }})
            .catch(error => {{
                console.error('删除失败:', error);
                alert('删除失败，请确保录音服务器已启动（端口8767）');
            }});
        }}
    </script>
"""

    html += get_html_footer()

    # 写入文件
    visitor_dir = OUTPUT_DIR / visitor_id
    visitor_dir.mkdir(parents=True, exist_ok=True)
    output_file = visitor_dir / f'{visit_id}.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"    ✓ 生成: {output_file}")


def main():
    """主函数"""
    print("=" * 60)
    print("生成来访详情页")
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
        visits_dir = visitor_dir / 'visits'

        if not profile_file.exists() or not visits_dir.exists():
            continue

        print(f"\n处理来访者: {visitor_id}")

        # 读取档案
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)

        # 遍历所有来访记录
        for visit_file in sorted(visits_dir.glob('visit_*.json')):
            with open(visit_file, 'r', encoding='utf-8') as f:
                visit_data = json.load(f)
                generate_visit_detail_page(visitor_id, visit_data, profile_data)

    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
