#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为 generate_case_library.py 添加下载按钮功能
"""

import sys
import io

# Windows GBK 兼容处理
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 读取原文件
with open('generate_case_library.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在咨询师复盘区域添加下载按钮（在标题行添加）
old_review_title = '''            <h2 class="text-xl font-bold text-gray-900 mb-3"><i class="fa fa-comments"></i> 咨询师复盘</h2>'''

new_review_title = '''            <div class="flex items-center justify-between mb-3">
                <h2 class="text-xl font-bold text-gray-900"><i class="fa fa-comments"></i> 咨询师复盘</h2>
                <a href="../downloads/{case_id}/{case_id}_复盘.docx"
                   download
                   class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition">
                    <i class="fa fa-download"></i> 下载Word
                </a>
            </div>'''

content = content.replace(old_review_title, new_review_title)

# 2. 在录音资料区域添加下载按钮（在collapsible-header内部）
old_recording_header = '''            <div class="collapsible-header" onclick="toggleCollapsible(this)">
                <h2 class="text-xl font-bold text-orange-900">
                    <i class="fa fa-microphone"></i> 🎙️ 录音资料
                </h2>
                <i class="fa fa-chevron-down collapsible-arrow text-gray-600"></i>
            </div>'''

new_recording_header = '''            <div class="collapsible-header" onclick="toggleCollapsible(this)">
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
            </div>'''

content = content.replace(old_recording_header, new_recording_header)

# 3. 在逐字稿区域添加下载按钮
old_transcript_header = '''            <div class="collapsible-header" onclick="toggleCollapsible(this)">
                <h2 class="text-xl font-bold text-green-900">
                    <i class="fa fa-file-text"></i> 📝 逐字稿
                </h2>
                <i class="fa fa-chevron-down collapsible-arrow text-gray-600"></i>
            </div>'''

new_transcript_header = '''            <div class="collapsible-header" onclick="toggleCollapsible(this)">
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
            </div>'''

content = content.replace(old_transcript_header, new_transcript_header)

# 4. 在流派分析Tab内容添加下载按钮（需要在每个流派Tab的开始位置）
# 搜索 "<!-- {approach_name}Tab内容 -->" 并在其后添加下载按钮
import re

# 在流派Tab内容开始处添加下载按钮
old_tab_content_start = '''        <!-- {approach_name}Tab内容 -->
        <div class="tab-content" id="tab-{approach_id}">
            <!-- 危机评估 -->'''

new_tab_content_start = '''        <!-- {approach_name}Tab内容 -->
        <div class="tab-content" id="tab-{approach_id}">
            <!-- 下载该流派分析 -->
            <div class="mb-4 flex justify-end">
                <a href="../downloads/{case_id}/{case_id}_{approach_name}.md"
                   download
                   class="px-4 py-2 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 transition">
                    <i class="fa fa-download"></i> 下载{approach_name}分析
                </a>
            </div>

            <!-- 危机评估 -->'''

content = content.replace(old_tab_content_start, new_tab_content_start)

# 保存修改后的文件
with open('generate_case_library.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 下载按钮添加完成！")
print("修改位置：")
print("  1. 咨询师复盘 - Word下载按钮")
print("  2. 录音资料 - MP3下载按钮")
print("  3. 逐字稿 - Excel下载按钮")
print("  4. 流派分析 - Markdown下载按钮")
