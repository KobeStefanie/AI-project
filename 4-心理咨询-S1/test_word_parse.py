#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Word文档解析，输出详细的调试信息
"""

import sys
from docx import Document
from docx.shared import RGBColor
from docx.enum.text import WD_COLOR_INDEX
from docx.enum.dml import MSO_THEME_COLOR_INDEX

def test_parse_word(docx_path):
    """测试解析Word文档"""
    print("=" * 80)
    print(f"测试文件: {docx_path}")
    print("=" * 80)

    doc = Document(docx_path)

    for i, para in enumerate(doc.paragraphs):
        print(f"\n【段落 {i+1}】")
        print(f"样式: {para.style.name}")
        print(f"文本: {para.text[:50]}...")

        for j, run in enumerate(para.runs):
            if not run.text.strip():
                continue

            print(f"\n  [Run {j+1}] 文本: '{run.text}'")
            print(f"    加粗: {run.bold}")
            print(f"    斜体: {run.italic}")
            print(f"    下划线: {run.underline}")

            # 检查字体颜色
            if run.font.color:
                print(f"    颜色对象存在: True")
                print(f"    颜色类型: {run.font.color.type if hasattr(run.font.color, 'type') else 'N/A'}")

                if run.font.color.rgb:
                    print(f"    RGB颜色: {run.font.color.rgb}")
                else:
                    print(f"    RGB颜色: None")

                if hasattr(run.font.color, 'theme_color') and run.font.color.theme_color:
                    print(f"    主题颜色: {run.font.color.theme_color}")
                else:
                    print(f"    主题颜色: None")
            else:
                print(f"    颜色对象: None")

            # 检查高亮色
            if run.font.highlight_color:
                print(f"    高亮色: {run.font.highlight_color}")
            else:
                print(f"    高亮色: None")

            # 检查底纹/填充
            if hasattr(run, '_element') and run._element.rPr is not None:
                shd = run._element.rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}shd')
                if shd is not None:
                    fill = shd.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                    print(f"    底纹填充: {fill}")
                else:
                    print(f"    底纹填充: None")

        print("\n" + "-" * 80)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_parse_word(sys.argv[1])
    else:
        print("用法: python test_word_parse.py <word文件路径>")
        print("\n请将Word文档拖到此窗口，或输入完整路径")
