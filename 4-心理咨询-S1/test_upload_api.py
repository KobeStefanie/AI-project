#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Word上传API
"""

import requests

# 测试文件
test_file = 'test_color.docx'

# 上传
with open(test_file, 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:8765/', files=files)

print('响应状态:', response.status_code)
print('=' * 80)

if response.status_code == 200:
    data = response.json()
    if data.get('success'):
        print('✓ 上传成功')
        print('\n返回的HTML:')
        print('=' * 80)
        html = data.get('html', '')
        print(html[:500])  # 显示前500字符
        print('...')
        print('=' * 80)

        # 检查是否包含颜色
        if 'color:' in html:
            print('\n✓ 包含文字颜色')
        else:
            print('\n✗ 不包含文字颜色')

        if 'background-color:' in html:
            print('✓ 包含背景颜色')
        else:
            print('✗ 不包含背景颜色')
    else:
        print('✗ 上传失败:', data.get('error'))
else:
    print('✗ 服务器错误')
    print(response.text)
