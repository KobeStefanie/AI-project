#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简API连接测试
"""

import sys
import io
import anthropic

# Windows UTF-8 输出
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

API_KEY = "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde"
BASE_URL = "https://www.catkingai.com"

print("测试API连接...")
print(f"端点: {BASE_URL}")

try:
    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)

    print("发送测试请求...")
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "请用一句话回答：你好"}
        ]
    )

    print("连接成功！")

    # 处理响应内容（可能包含thinking block）
    for block in response.content:
        if hasattr(block, 'text'):
            print(f"回复: {block.text}")
        elif hasattr(block, 'type'):
            print(f"内容类型: {block.type}")

    print(f"使用tokens: {response.usage.input_tokens} 输入, {response.usage.output_tokens} 输出")

except Exception as e:
    print(f"连接失败: {str(e)}")
    import traceback
    traceback.print_exc()
