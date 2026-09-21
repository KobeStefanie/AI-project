#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取纯净对话记录（只要用户问+AI答）"""
import json
import re
from pathlib import Path

def is_skill_content(text):
    """判断是否是技能描述内容或系统摘要"""
    if not text:
        return True

    # 技能描述的特征
    skill_markers = [
        '# Finance Expert',
        '## Core Concepts',
        '### FinTech Stack',
        'Payment gateways',
        'Banking APIs',
        'Blockchain/crypto',
        'npm install',
        'pip install',
        'Base directory for this skill',
        'Path: userSettings:',
        'When to Use This Skill',
        '## Usage',
        '## How it works',
        '## Overview',
        'MySQL Development Assistant',
        'PostgreSQL Development',
        'Claude Code, Anthropic',
        'gitStatus:',
        'Current branch:',
        'Recent commits:',
        'claudeMd',
        'Codebase and user instructions',
        # 系统摘要特征（英文）
        'This session is being continued',
        'Summary:',
        'Primary Request and Intent:',
        'Key Technical Concepts:',
        'Files and Code Sections:',
        'Errors and Fixes:',
        'Problem Solving:',
        'All User Messages:',
        'Pending Tasks:',
        'Current Work:',
        'Optional Next Step:',
        'If you need specific details from before compaction',
        'read the full transcript at:',
        'Continue the conversation from where it left off',
        'Resume directly',
        'do not acknowledge the summary',
    ]

    for marker in skill_markers:
        if marker in text:
            return True

    # 纯英文段落（超过80%是英文字母）
    if len(text) > 100:
        english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text if c.isalpha())
        if total_chars > 0 and english_chars / total_chars > 0.8:
            return True

    # 过短的内容
    if len(text.strip()) < 10:
        return True

    return False

def clean_content(text):
    """清理内容：移除XML标签"""
    if not text:
        return ""

    # 移除所有XML标签块
    text = re.sub(r'<function_calls>.*?</function_calls>', '', text, flags=re.DOTALL)
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ide_opened_file>.*?</ide_opened_file>', '', text, flags=re.DOTALL)
    text = re.sub(r'<system-reminder>.*?</system-reminder>', '', text, flags=re.DOTALL)
    text = re.sub(r'<local-command-caveat>.*?</local-command-caveat>', '', text, flags=re.DOTALL)
    text = re.sub(r'<command-.*?>.*?</command-.*?>', '', text, flags=re.DOTALL)
    text = re.sub(r'<local-command-stdout>.*?</local-command-stdout>', '', text, flags=re.DOTALL)

    # 移除 Token usage 提示
    text = re.sub(r'Token usage:.*', '', text)

    # 移除多余空行
    text = re.sub(r'\n\n+', '\n\n', text)

    return text.strip()

def extract_conversation():
    """提取纯净对话"""
    jsonl_file = Path("C:/Users/Administrator/.claude/projects/d--AI----12-----/0a05ff18-3a38-48eb-b32f-40cba9024ade.jsonl")

    if not jsonl_file.exists():
        print(f"找不到文件: {jsonl_file}")
        return

    messages = []
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    msg_type = data.get('type')

                    if msg_type == 'user':
                        content = data.get('message', {}).get('content', '')
                        if isinstance(content, list):
                            content = '\n'.join(str(item.get('text', '')) for item in content if isinstance(item, dict))

                        # 清理并检查
                        cleaned = clean_content(content)
                        if cleaned and not is_skill_content(cleaned):
                            messages.append(('user', cleaned))

                    elif msg_type == 'assistant':
                        content = data.get('message', {}).get('content', '')
                        if isinstance(content, list):
                            # 只提取 type='text' 的内容
                            texts = []
                            for item in content:
                                if isinstance(item, dict) and item.get('type') == 'text':
                                    texts.append(str(item.get('text', '')))
                            content = '\n'.join(texts)

                        # 清理并检查
                        cleaned = clean_content(content)
                        if cleaned and not is_skill_content(cleaned):
                            messages.append(('assistant', cleaned))

                except json.JSONDecodeError:
                    continue

    print(f"提取到 {len(messages)} 条有效对话")

    # 生成Markdown
    output = []
    output.append("# 标准成本法在混乱现场的实际应用 - 对话记录")
    output.append("")
    output.append("**日期**：2026年8月27日-29日")
    output.append("**主题**：标准成本法在领料混乱、纱线挂筒场景下的实际应用")
    output.append("")
    output.append("---")
    output.append("")

    for role, content in messages:
        if role == 'user':
            output.append("**用户**：" + content)
        else:
            output.append("**AI**：" + content)

        output.append("")
        output.append("---")
        output.append("")

    # 保存
    output_dir = Path("D:/AI-项目/12-成本控制/织造部成本核算/01-学习资料")
    output_file = output_dir / "对话记录-标准成本法实际应用-20260827.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    size_kb = output_file.stat().st_size / 1024
    print(f"已生成: {output_file}")
    print(f"文件大小: {size_kb:.1f} KB")

if __name__ == "__main__":
    extract_conversation()
