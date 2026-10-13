import PyPDF2
import sys

def extract_pdf_structure(pdf_path):
    """提取PDF的目录结构和基本信息（UTF-8编码）"""
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
            print("页面文本提取测试（第10-15页）:\n")

            # 尝试提取中间页面的文本
            for i in range(9, min(15, num_pages)):
                page = reader.pages[i]
                text = page.extract_text()
                if text and len(text.strip()) > 10:
                    print(f"\n--- 第 {i+1} 页 ---")
                    print(text[:800])  # 显示前800字符
                    break

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
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
                # 尝试处理编码问题
                if isinstance(title, bytes):
                    title = title.decode('utf-8', errors='ignore')
                print(f"{indent}- {title}")
            except Exception as e:
                print(f"{indent}- (无法显示标题: {e})")

if __name__ == "__main__":
    # 设置UTF-8输出
    sys.stdout.reconfigure(encoding='utf-8')

    pdf_path = "循环提问  系统式治疗案例教程_13374365(1).pdf"
    extract_pdf_structure(pdf_path)
