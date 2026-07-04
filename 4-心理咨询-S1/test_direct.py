#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试服务器解析
"""
import sys
sys.path.insert(0, 'src')

from word_upload_server import parse_word_to_html

# 测试文件
docx_path = 'test_color.docx'

print(f'测试文件: {docx_path}')
print('=' * 80)

try:
    html = parse_word_to_html(docx_path)
    print('生成的HTML:')
    print(html)
    print('\n' + '=' * 80)

    # 分析结果
    if 'style="color:' in html or 'style="background-color:' in html:
        print('✓ HTML包含颜色样式')

        # 提取颜色
        import re
        colors = re.findall(r'color:\s*(#[0-9A-Fa-f]{6})', html)
        bg_colors = re.findall(r'background-color:\s*(#[0-9A-Fa-f]{6})', html)

        if colors:
            print(f'  文字颜色: {", ".join(set(colors))}')
        if bg_colors:
            print(f'  背景颜色: {", ".join(set(bg_colors))}')
    else:
        print('✗ HTML不包含颜色样式')

except Exception as e:
    print(f'✗ 错误: {e}')
    import traceback
    traceback.print_exc()
