#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话历史导出工具
将 Claude Code 会话的 JSONL 文件转换为可读文档
"""

import json
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import re

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def find_current_session():
    """自动检测当前会话 ID"""
    # 尝试从环境变量或当前目录推断
    claude_dir = Path.home() / '.claude' / 'projects'

    # 查找最近修改的 .jsonl 文件
    if not claude_dir.exists():
        return None

    project_dirs = [d for d in claude_dir.iterdir() if d.is_dir()]
    if not project_dirs:
        return None

    # 获取所有 .jsonl 文件
    jsonl_files = []
    for proj_dir in project_dirs:
        for file in proj_dir.glob('*.jsonl'):
            if 'subagents' not in str(file):
                jsonl_files.append(file)

    if not jsonl_files:
        return None

    # 返回最近修改的文件
    latest = max(jsonl_files, key=lambda f: f.stat().st_mtime)
    return latest

def parse_jsonl(file_path):
    """解析 JSONL 文件，提取对话消息"""
    messages = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)

                # 处理用户消息
                if data.get('type') == 'user':
                    msg = data.get('message', {})
                    messages.append({
                        'role': msg.get('role', 'user'),
                        'content': msg.get('content', ''),
                        'timestamp': data.get('timestamp'),
                    })

                # 处理助手消息
                elif data.get('type') == 'assistant':
                    msg = data.get('message', {})
                    messages.append({
                        'role': msg.get('role', 'assistant'),
                        'content': msg.get('content', ''),
                        'timestamp': data.get('timestamp'),
                    })

                # 处理工具使用
                elif data.get('type') == 'tool_use':
                    tool_name = data.get('name', 'unknown')
                    messages.append({
                        'role': 'tool',
                        'content': f"[调用工具: {tool_name}]",
                        'timestamp': data.get('timestamp'),
                        'tool_data': data
                    })

                # 处理工具结果
                elif data.get('type') == 'tool_result':
                    messages.append({
                        'role': 'tool_result',
                        'content': data.get('content', '[工具执行结果]'),
                        'timestamp': data.get('timestamp'),
                    })

            except json.JSONDecodeError:
                continue

    return messages

def clean_content(content):
    """清理内容，处理特殊标签"""
    if isinstance(content, list):
        # 处理结构化内容
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    tool_name = item.get('name', 'unknown')
                    parts.append(f"\n[调用工具: {tool_name}]\n")
                elif item.get('type') == 'tool_result':
                    parts.append(f"\n[工具结果]\n")
            else:
                parts.append(str(item))
        return ''.join(parts)
    return str(content)

def export_markdown(messages, output_path, session_id):
    """导出为 Markdown 格式"""
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入头部
        f.write("# 对话历史导出\n\n")
        f.write(f"**会话ID**: {session_id}\n")
        f.write(f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**消息数量**: {len(messages)}\n\n")
        f.write("---\n\n")

        # 写入对话内容
        for i, msg in enumerate(messages, 1):
            role = msg['role']
            content = clean_content(msg['content'])
            timestamp = msg.get('timestamp', '')

            # 角色名称
            role_name = {
                'user': '👤 用户',
                'assistant': '🤖 Claude',
                'system': '⚙️ 系统',
                'tool': '🔧 工具',
                'tool_result': '📋 工具结果'
            }.get(role, role)

            # 时间戳格式化
            time_str = ''
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = f" ({dt.strftime('%H:%M:%S')})"
                except:
                    pass

            f.write(f"## {role_name}{time_str}\n\n")
            f.write(f"{content}\n\n")
            f.write("---\n\n")

def export_docx(messages, output_path, session_id):
    """导出为 Word 文档格式"""
    try:
        # 使用 Node.js 的 docx 库
        import subprocess
        import tempfile

        # 创建临时 JS 文件
        js_code = f"""
const {{ Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType }} = require('docx');
const fs = require('fs');

const messages = {json.dumps(messages, ensure_ascii=False)};
const sessionId = {json.dumps(session_id)};

const children = [];

// 标题
children.push(
    new Paragraph({{
        text: "对话历史导出",
        heading: HeadingLevel.HEADING_1,
        alignment: AlignmentType.CENTER,
        spacing: {{ after: 400 }}
    }}),
    new Paragraph({{
        children: [
            new TextRun({{ text: "会话ID: ", bold: true }}),
            new TextRun(sessionId)
        ],
        spacing: {{ after: 200 }}
    }}),
    new Paragraph({{
        children: [
            new TextRun({{ text: "导出时间: ", bold: true }}),
            new TextRun(new Date().toLocaleString('zh-CN'))
        ],
        spacing: {{ after: 200 }}
    }}),
    new Paragraph({{
        children: [
            new TextRun({{ text: "消息数量: ", bold: true }}),
            new TextRun(String(messages.length))
        ],
        spacing: {{ after: 400 }}
    }})
);

// 对话内容
messages.forEach((msg, i) => {{
    const roleName = {{
        'user': '👤 用户',
        'assistant': '🤖 Claude',
        'system': '⚙️ 系统'
    }}[msg.role] || msg.role;

    const content = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);

    children.push(
        new Paragraph({{
            text: roleName,
            heading: HeadingLevel.HEADING_2,
            spacing: {{ before: 300, after: 200 }}
        }}),
        new Paragraph({{
            children: [new TextRun(content)],
            spacing: {{ after: 300 }}
        }})
    );
}});

const doc = new Document({{
    sections: [{{
        properties: {{
            page: {{
                size: {{
                    width: 12240,
                    height: 15840
                }},
                margin: {{ top: 1440, right: 1440, bottom: 1440, left: 1440 }}
            }}
        }},
        children: children
    }}]
}});

Packer.toBuffer(doc).then(buffer => {{
    fs.writeFileSync({json.dumps(str(output_path))}, buffer);
    console.log("导出成功！");
}});
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(js_code)
            temp_js = f.name

        try:
            result = subprocess.run(['node', temp_js], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"错误: {result.stderr}")
                return False
            return True
        finally:
            os.unlink(temp_js)

    except Exception as e:
        print(f"导出 Word 文档失败: {e}")
        print("提示: 请确保已安装 docx 库: npm install -g docx")
        return False

def main():
    parser = argparse.ArgumentParser(description='导出 Claude Code 对话历史')
    parser.add_argument('-f', '--format', choices=['md', 'docx'], default='md',
                      help='输出格式 (默认: md)')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('-s', '--session-id', help='会话 ID')

    args = parser.parse_args()

    # 查找会话文件
    if args.session_id:
        session_file = Path.home() / '.claude' / 'projects' / args.session_id
        if not session_file.exists():
            print(f"错误: 找不到会话文件 {session_file}")
            sys.exit(1)
    else:
        session_file = find_current_session()
        if not session_file:
            print("错误: 无法自动检测当前会话，请使用 --session-id 指定")
            sys.exit(1)

    print(f"正在读取会话: {session_file.name}")

    # 解析对话
    messages = parse_jsonl(session_file)
    if not messages:
        print("警告: 未找到任何对话消息")
        sys.exit(1)

    print(f"找到 {len(messages)} 条消息")

    # 确定输出文件
    if args.output:
        output_path = Path(args.output)
    else:
        ext = 'md' if args.format == 'md' else 'docx'
        output_path = Path(f"对话导出-{datetime.now().strftime('%Y%m%d-%H%M%S')}.{ext}")

    # 导出
    session_id = session_file.stem

    if args.format == 'md':
        export_markdown(messages, output_path, session_id)
        print(f"✓ 已导出到: {output_path.absolute()}")
    else:
        if export_docx(messages, output_path, session_id):
            print(f"✓ 已导出到: {output_path.absolute()}")
        else:
            print("导出失败")
            sys.exit(1)

if __name__ == '__main__':
    main()
