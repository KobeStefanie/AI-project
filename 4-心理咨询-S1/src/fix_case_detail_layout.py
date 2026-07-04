#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复案例详情页布局，添加正确的区域顺序和下载按钮
按照"案例中性原则"重新组织内容
"""

import sys
import io

# Windows GBK 兼容处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 读取原文件
with open('generate_case_library.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到并替换"完整对话记录"这一整块，改为正确的布局顺序
old_section = '''    # 添加完整对话记录到案例总览Tab
    html += f"""            <!-- 完整对话记录 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-gray-900 mb-3"><i class="fa fa-comments"></i> 完整对话记录</h2>
                <div class="bg-gray-50 rounded-lg p-4">
                    <pre class="whitespace-pre-wrap text-sm text-gray-800 font-mono">{dialogue}</pre>
                </div>
            </div>
        </div>

"""'''

# 新的内容：咨询师复盘 + 录音 + 逐字稿 + 案例概要 + 标签
new_section = '''    # 获取中性数据
    case_summary = case_data.get('case_summary', '暂无概要')
    case_tags = case_data.get('case_tags', {})
    relation_tags = case_tags.get('relation', [])
    symptom_tags = case_tags.get('symptom', [])

    # 添加咨询师复盘（原"完整对话记录"）
    html += f"""            <!-- 咨询师复盘 -->
            <div class="mb-6">
                <div class="flex items-center justify-between mb-3">
                    <h2 class="text-xl font-bold text-gray-900"><i class="fa fa-comments"></i> 咨询师复盘</h2>
                    <a href="../downloads/{case_id}/{case_id}_复盘.docx"
                       download
                       class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition">
                        <i class="fa fa-download"></i> 下载Word
                    </a>
                </div>
                <div class="bg-gray-50 rounded-lg p-4">
                    <pre class="whitespace-pre-wrap text-sm text-gray-800 font-mono">{dialogue}</pre>
                </div>
            </div>

            <!-- 录音资料（可折叠，空也显示） -->
            <div class="collapsible-section collapsed mb-4">
                <div class="collapsible-header" onclick="toggleCollapsible(this)">
                    <div class="flex items-center justify-between flex-1">
                        <h2 class="text-xl font-bold text-orange-900">
                            <i class="fa fa-microphone"></i> 🎙️ 录音资料
                        </h2>
                        <div class="flex items-center gap-2">
                            <a href="../downloads/{case_id}/{case_id}_录音.mp3"
                               download
                               onclick="event.stopPropagation()"
                               class="px-3 py-1 bg-orange-600 text-white text-sm rounded hover:bg-orange-700 transition">
                                <i class="fa fa-download"></i> 下载MP3
                            </a>
                            <i class="fa fa-chevron-down collapsible-arrow text-gray-600"></i>
                        </div>
                    </div>
                </div>
                <div class="collapsible-content">
                    <p class="text-sm text-gray-500 text-center py-4">暂无录音资料</p>
                </div>
            </div>

            <!-- 逐字稿（可折叠，空也显示） -->
            <div class="collapsible-section collapsed mb-4">
                <div class="collapsible-header" onclick="toggleCollapsible(this)">
                    <div class="flex items-center justify-between flex-1">
                        <h2 class="text-xl font-bold text-green-900">
                            <i class="fa fa-file-text"></i> 📝 逐字稿
                        </h2>
                        <div class="flex items-center gap-2">
                            <a href="../downloads/{case_id}/{case_id}_逐字稿.xlsx"
                               download
                               onclick="event.stopPropagation()"
                               class="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition">
                                <i class="fa fa-download"></i> 下载Excel
                            </a>
                            <i class="fa fa-chevron-down collapsible-arrow text-gray-600"></i>
                        </div>
                    </div>
                </div>
                <div class="collapsible-content">
                    <p class="text-sm text-gray-500 text-center py-4">暂无逐字稿</p>
                </div>
            </div>

            <!-- 案例概要（中性） -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-indigo-900 mb-3"><i class="fa fa-file-text-o"></i> 案例概要</h2>
                <div class="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                    <p class="text-sm text-gray-800 leading-relaxed">{case_summary}</p>
                </div>
            </div>

            <!-- 标签（中性） -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-purple-900 mb-3"><i class="fa fa-tags"></i> 标签</h2>
                <div class="space-y-3">
                    <!-- 关系标签 -->
                    <div>
                        <h3 class="text-sm font-semibold text-gray-700 mb-2">关系标签：</h3>
                        <div class="flex flex-wrap gap-2">
"""

    # 添加关系标签
    if relation_tags:
        for relation_tag in relation_tags:
            html += f'                            <span class="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">{{relation_tag}}</span>\\n'.replace('{relation_tag}', relation_tag)
    else:
        html += '                            <span class="text-sm text-gray-400">暂无关系标签</span>\\n'

    html += """                        </div>
                    </div>
                    <!-- 症状标签 -->
                    <div>
                        <h3 class="text-sm font-semibold text-gray-700 mb-2">症状标签：</h3>
                        <div class="flex flex-wrap gap-2">
"""

    # 添加症状标签
    if symptom_tags:
        for symptom_tag in symptom_tags:
            html += f'                            <span class="px-3 py-1 bg-red-100 text-red-700 text-sm rounded-full">{{symptom_tag}}</span>\\n'.replace('{symptom_tag}', symptom_tag)
    else:
        html += '                            <span class="text-sm text-gray-400">暂无症状标签</span>\\n'

    html += """                        </div>
                    </div>
                </div>
            </div>
        </div>

"""'''

# 执行替换
if old_section in content:
    content = content.replace(old_section, new_section)
    print("✅ 成功替换案例详情页布局")
else:
    print("❌ 未找到目标代码段")
    print("请检查 generate_case_library.py 文件")
    sys.exit(1)

# 保存修改后的文件
with open('generate_case_library.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n修改完成！新增内容：")
print("  1. 咨询师复盘（带Word下载按钮）")
print("  2. 录音资料（可折叠，带MP3下载按钮）")
print("  3. 逐字稿（可折叠，带Excel下载按钮）")
print("  4. 案例概要（中性）")
print("  5. 标签（中性 - 关系标签 + 症状标签）")
