#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成案例总览Tab的辅助函数
"""

def generate_overview_tab_content(case_data: dict, case_id: str, basic_info: dict, dialogue: str) -> str:
    """生成案例总览Tab的HTML内容"""

    html = """        <!-- 案例总览Tab内容 -->
        <div class="tab-content active" id="tab-overview">
            <!-- 基本信息（可折叠） -->
            <div class="collapsible-section mb-4">
                <div class="collapsible-header" onclick="toggleCollapsible(this)">
                    <h2 class="text-xl font-bold text-blue-900">
                        <i class="fa fa-user-circle"></i> 基本信息
                    </h2>
                    <i class="fa fa-chevron-down collapsible-arrow text-gray-600"></i>
                </div>
                <div class="collapsible-content">
                    <div class="grid grid-cols-2 gap-3 text-sm">
"""

    html += f"""                        <div><strong>代号：</strong>{basic_info.get('代号', '')}</div>
                        <div><strong>性别：</strong>{basic_info.get('性别', '')}</div>
                        <div><strong>年龄：</strong>{basic_info.get('年龄', '')}</div>
                        <div><strong>职业：</strong>{basic_info.get('职业', '')}</div>
                        <div><strong>婚姻：</strong>{basic_info.get('婚姻状况', '')}</div>
"""

    html += """                    </div>
                </div>
            </div>

"""

    # 录音资料
    audio_files = case_data.get('audio_files', [])
    if audio_files:
        html += """            <!-- 录音资料 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-orange-900 mb-3"><i class="fa fa-microphone"></i> 录音资料</h2>
                <div class="space-y-3">
"""
        for audio in audio_files:
            filename = audio.get('filename', '')
            size = audio.get('size', 0)
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"

            html += f"""                    <div class="bg-orange-50 border border-orange-200 rounded-lg p-4">
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
        html += """                </div>
            </div>

"""

    # 逐字稿
    transcripts = case_data.get('transcripts', [])
    if transcripts:
        html += """            <!-- 逐字稿 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-green-900 mb-3"><i class="fa fa-file-text-o"></i> 逐字稿</h2>
                <div class="space-y-3">
"""
        for transcript in transcripts:
            transcript_id = transcript.get('id', '')
            content = transcript.get('content', '')
            audio_filename = transcript.get('audio_filename', '')
            created_at = transcript.get('created_at', '')

            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                created_str = created_at

            audio_tag = f'<span class="text-xs text-blue-600 ml-2"><i class="fa fa-link"></i> {audio_filename}</span>' if audio_filename else ''

            html += f"""                    <details class="bg-green-50 border border-green-200 rounded-lg">
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
        html += """                </div>
            </div>

"""

    # 督导资料
    supervision_files = case_data.get('supervision_files', [])
    if supervision_files:
        html += """            <!-- 督导资料 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-amber-900 mb-3"><i class="fa fa-folder-open"></i> 督导资料</h2>
                <div class="space-y-3">
"""
        for supervision in supervision_files:
            filename = supervision.get('filename', '')
            title = supervision.get('title', filename)
            note = supervision.get('note', '')
            uploaded_at = supervision.get('uploaded_at', '')

            try:
                from datetime import datetime
                dt = datetime.fromisoformat(uploaded_at.replace('Z', '+00:00'))
                uploaded_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                uploaded_str = uploaded_at

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

            html += f"""                    <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
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
        html += """                </div>
            </div>

"""

    # 完整对话记录
    html += f"""            <!-- 完整对话记录 -->
            <div class="mb-6">
                <h2 class="text-xl font-bold text-gray-900 mb-3"><i class="fa fa-comments"></i> 完整对话记录</h2>
                <div class="bg-gray-50 rounded-lg p-4">
                    <pre class="whitespace-pre-wrap text-sm text-gray-800 font-mono">{dialogue}</pre>
                </div>
            </div>
        </div>

"""

    return html


if __name__ == '__main__':
    # 测试
    test_data = {
        'case_id': 'TEST001',
        'basic_info': {'代号': '测试', '性别': '女', '年龄': '25岁', '职业': '学生', '婚姻状况': '未婚'},
        'dialogue': '这是测试对话',
        'audio_files': [],
        'transcripts': [],
        'supervision_files': []
    }

    result = generate_overview_tab_content(test_data, 'TEST001', test_data['basic_info'], test_data['dialogue'])
    print("生成成功，长度:", len(result))
