#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用 PyMuPDF 提取PDF中文内容（最佳方案）
"""

try:
    import fitz  # PyMuPDF
except ImportError:
    print("正在安装 PyMuPDF...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'PyMuPDF'])
    import fitz

import json
import re

def extract_pdf_with_pymupdf(pdf_path, output_path, toc_path):
    """使用PyMuPDF提取PDF内容"""
    print(f"[INFO] 开始提取PDF: {pdf_path}")

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"[INFO] 总页数: {total_pages}")

    # 提取目录结构
    toc = doc.get_toc()  # 返回 [(level, title, page), ...]
    toc_data = []
    for level, title, page in toc:
        toc_data.append({
            "level": level,
            "title": title,
            "page": page
        })

    # 保存目录JSON
    with open(toc_path, 'w', encoding='utf-8') as f:
        json.dump(toc_data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 目录已保存到: {toc_path}")

    # 提取全文内容
    with open(output_path, 'w', encoding='utf-8') as out:
        # 写入标题
        title = doc.metadata.get('title', '循环提问 系统式治疗案例教程')
        out.write(f"# {title}\n\n")
        out.write(f"> 共 {total_pages} 页\n\n")
        out.write("---\n\n")

        # 逐页提取
        for page_num in range(total_pages):
            page = doc[page_num]

            # 提取文本（sort=True 保持阅读顺序）
            text = page.get_text("text", sort=True)

            if text and len(text.strip()) > 10:
                # 清理多余空行
                text = re.sub(r'\n{3,}', '\n\n', text.strip())

                # 检测是否为章节标题页
                first_line = text.split('\n')[0].strip()
                if re.match(r'^第?[一二三四五六七八九十\d]+[章节部分]', first_line) or \
                   re.match(r'^[Ⅰ-Ⅹ]+\.', first_line):
                    out.write(f"\n## 【第{page_num+1}页】{first_line}\n\n")
                else:
                    out.write(f"\n## 【第{page_num+1}页】\n\n")

                out.write(text)
                out.write("\n\n---\n\n")

            # 每10页显示进度
            if (page_num + 1) % 10 == 0:
                print(f"[PROGRESS] 已处理: {page_num+1}/{total_pages} 页")

    doc.close()

    # 统计信息
    import os
    file_size = os.path.getsize(output_path)
    print(f"\n[SUCCESS] 提取完成！")
    print(f"[SUCCESS] 保存到: {output_path}")
    print(f"[SUCCESS] 文件大小: {file_size:,} 字节 ({file_size/1024:.1f} KB)")

if __name__ == "__main__":
    pdf_path = "循环提问  系统式治疗案例教程_13374365(1).pdf"
    output_path = "book_content.md"
    toc_path = "toc.json"

    extract_pdf_with_pymupdf(pdf_path, output_path, toc_path)
