#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速AI分析测试
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from ai_analysis_service import AIAnalysisService

# CatKing AI配置
API_KEY = "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde"
BASE_URL = "https://www.catkingai.com"

print("="*60)
print("快速AI分析测试")
print("="*60)

# 构造极简测试数据
test_profile = {
    "name": "测试来访者",
    "age": 25,
    "gender": "女"
}

test_transcript = """
来访者：我最近感觉很焦虑，总是担心工作做不好。
咨询师：能具体说说是什么让你感到焦虑吗？
来访者：就是老板给我安排了一个新项目，我怕自己搞砸。
咨询师：听起来你对这个项目有些担心。之前有过类似的经历吗？
来访者：有的，上次项目我就没做好，被批评了。
"""

print("\n初始化AI服务...")
service = AIAnalysisService(api_key=API_KEY, base_url=BASE_URL)

print("正在调用 Claude API 进行测试分析...")
print("（使用大观学派，限制2000 tokens输出）\n")

result = service.analyze_with_approach(
    approach_id='daguanpai',
    visitor_profile=test_profile,
    transcript=test_transcript,
    counselor_review="",
    max_tokens=2000
)

if 'error' in result:
    print(f"❌ 分析失败: {result['error']}")
    sys.exit(1)

print("="*60)
print("✅ AI分析成功！")
print("="*60)
print(f"模型: {result['metadata']['model']}")
print(f"输入tokens: {result['metadata']['input_tokens']}")
print(f"输出tokens: {result['metadata']['output_tokens']}")
print(f"\n分析结果预览（前500字符）：")
print("-" * 60)
print(result['analysis_text'][:500] + "...")
print("-" * 60)
