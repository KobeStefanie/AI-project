import PyPDF2
import sys

def extract_pdf_structure(pdf_path):
    """提取PDF的目录结构和基本信息"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # 基本信息
            num_pages = len(reader.pages)
            print(f"总页数: {num_pages}")
            print(f"\n{'='*50}\n")

            # 提取目录（如果有）
            if reader.outline:
                print("目录结构:\n")
                extract_outline(reader.outline)
            else:
                print("此PDF没有目录书签。\n")

            print(f"\n{'='*50}\n")
            print("前10页内容预览:\n")

            # 提取前10页的文本来分析章节
            for i in range(min(10, num_pages)):
                page = reader.pages[i]
                text = page.extract_text()
                print(f"\n--- 第 {i+1} 页 ---")
                # 只显示每页前500字符
                print(text[:500] if text else "(无法提取文本)")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

def extract_outline(outline, level=0):
    """递归提取目录"""
    for item in outline:
        if isinstance(item, list):
            extract_outline(item, level + 1)
        else:
            indent = "  " * level
            try:
                title = item.title if hasattr(item, 'title') else str(item)
                print(f"{indent}- {title}")
            except:
                pass

if __name__ == "__main__":
    pdf_path = "循环提问  系统式治疗案例教程_13374365(1).pdf"
    extract_pdf_structure(pdf_path)
