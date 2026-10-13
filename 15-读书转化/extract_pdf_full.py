#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提取PDF完整内容并保存为Markdown格式
"""
import PyPDF2
import re
import sys
import io

# 设置标准输出为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def clean_text(text):
    """清理提取的文本"""
    if not text:
        return ""
    # 移除多余的空白
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()

def extract_pdf_content(pdf_path, output_path):
    """提取PDF完整内容并保存为Markdown"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)

            print(f"开始提取PDF内容...")
            print(f"总页数: {total_pages}")

            with open(output_path, 'w', encoding='utf-8') as out:
                out.write(f"# 循环提问 系统式治疗案例教程\n\n")
                out.write(f"> 共 {total_pages} 页\n\n")
                out.write("---\n\n")

                # 提取每一页
                for page_num in range(total_pages):
                    page = reader.pages[page_num]
                    text = page.extract_text()

                    if text and len(text.strip()) > 10:
                        cleaned_text = clean_text(text)
                        out.write(f"\n## 第 {page_num + 1} 页\n\n")
                        out.write(cleaned_text)
                        out.write("\n\n---\n\n")

                    # 每10页显示进度
                    if (page_num + 1) % 10 == 0:
                        print(f"已处理: {page_num + 1}/{total_pages} 页")

            print(f"\n✓ 提取完成！保存到: {output_path}")
            print(f"✓ 总页数: {total_pages}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    pdf_path = "循环提问  系统式治疗案例教程_13374365(1).pdf"
    output_path = "book_content.md"
    extract_pdf_content(pdf_path, output_path)
