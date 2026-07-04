#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度检查Word文档的XML结构，找出颜色信息的存储位置
"""

import sys
from docx import Document
from lxml import etree

def analyze_word_xml(docx_path):
    """分析Word文档的XML结构"""
    print("=" * 80)
    print(f"分析文件: {docx_path}")
    print("=" * 80)

    doc = Document(docx_path)

    for i, para in enumerate(doc.paragraphs):
        # 只查看前3个段落
        if i >= 3:
            break

        print(f"\n【段落 {i+1}】 {para.text[:50]}...")

        for j, run in enumerate(para.runs):
            if not run.text.strip():
                continue

            print(f"\n  [Run {j+1}] '{run.text[:30]}'")

            # 获取run的XML元素
            r_element = run._element
            rPr = r_element.rPr

            if rPr is not None:
                # 打印完整的rPr XML
                print(f"    完整的rPr XML:")
                xml_str = etree.tostring(rPr, encoding='unicode', pretty_print=True)
                for line in xml_str.split('\n'):
                    if line.strip():
                        print(f"      {line}")
            else:
                print(f"    rPr: None (无格式)")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_word_xml(sys.argv[1])
    else:
        print("用法: python test_word_xml.py <word文件路径>")
