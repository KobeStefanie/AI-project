"""
修复生成的HTML文件中的JavaScript双大括号问题
"""
import os
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "案例库" / "cases"

def fix_html_file(file_path):
    """修复HTML文件中的JavaScript双大括号"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 只在<script>标签内替换双大括号
    import re

    def fix_script(match):
        script_content = match.group(1)
        # 替换 {{ 为 {，}} 为 }
        fixed = script_content.replace('{{', '{').replace('}}', '}')
        return f'<script>{fixed}</script>'

    # 查找所有<script>标签并修复
    fixed_content = re.sub(r'<script>(.*?)</script>', fix_script, content, flags=re.DOTALL)

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)

    print(f"[OK] 修复完成: {file_path.name}")

def main():
    print("=" * 60)
    print("  修复JavaScript双大括号工具")
    print("=" * 60)

    html_files = list(OUTPUT_DIR.glob("*.html"))

    if not html_files:
        print("未找到HTML文件")
        return

    for html_file in html_files:
        fix_html_file(html_file)

    print("\n" + "=" * 60)
    print(f"  完成！共修复 {len(html_files)} 个文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
