#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用pdfplumber更好地提取PDF中文内容
"""
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    print("正在安装 pdfplumber...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'pdfplumber'])
    import pdfplumber

import json
import re

def extract_pdf_with_pdfplumber(pdf_path, output_path):
    """使用pdfplumber提取PDF内容"""
    print(f"开始提取PDF: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"总页数: {total_pages}")

        # 提取目录结构
        toc_pages = []

        with open(output_path, 'w', encoding='utf-8') as out:
            out.write(f"# 循环提问 系统式治疗案例教程\n\n")
            out.write(f"> 共 {total_pages} 页\n\n")
            out.write("---\n\n")

            for i, page in enumerate(pdf.pages):
                # 提取文本
                text = page.extract_text()

                if text and len(text.strip()) > 10:
                    # 清理文本
                    text = text.strip()

                    # 检测是否为标题页
                    lines = text.split('\n')
                    first_line = lines[0].strip() if lines else ""

                    # 如果是章节标题，使用二级标题
                    if re.match(r'^第?[一二三四五六七八九十\d]+[章节部分]', first_line) or \
                       re.match(r'^[Ⅰ-Ⅹ]+\.', first_line) or \
                       i < 20:  # 前20页可能包含目录
                        out.write(f"\n## 【第{i+1}页】\n\n")
                    else:
                        out.write(f"\n### 第{i+1}页\n\n")

                    out.write(text)
                    out.write("\n\n---\n\n")

                # 每10页显示进度
                if (i + 1) % 10 == 0:
                    print(f"已处理: {i+1}/{total_pages} 页")

        print(f"\n✓ 提取完成！保存到: {output_path}")
        print(f"✓ 文件大小: {len(open(output_path, 'r', encoding='utf-8').read())} 字符")

if __name__ == "__main__":
    pdf_path = "循环提问  系统式治疗案例教程_13374365(1).pdf"
    output_path = "book_content.md"
    extract_pdf_with_pdfplumber(pdf_path, output_path)
