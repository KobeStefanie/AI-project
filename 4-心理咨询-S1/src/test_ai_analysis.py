#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析功能测试脚本
用途：测试AI分析服务的基本功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from ai_analysis_service import AIAnalysisService


def test_api_key():
    """测试1：检查API Key是否配置"""
    print("\n" + "="*60)
    print("测试1：检查API Key配置")
    print("="*60)

    api_key = os.environ.get('ANTHROPIC_API_KEY', '')

    if not api_key:
        print("❌ 未找到 ANTHROPIC_API_KEY 环境变量")
        print("\n请设置环境变量：")
        print("  Windows: set ANTHROPIC_API_KEY=your_api_key")
        print("  Linux/Mac: export ANTHROPIC_API_KEY=your_api_key")
        return False
    else:
        print(f"✅ API Key 已配置（长度: {len(api_key)} 字符）")
        return True


def test_prompt_loading():
    """测试2：检查Prompt模板加载"""
    print("\n" + "="*60)
    print("测试2：检查Prompt模板")
    print("="*60)

    try:
        # 不需要API Key也能测试Prompt加载
        from ai_analysis_service import PROMPTS_DIR, APPROACH_PROMPT_MAP

        approaches = ['daguanpai', 'cbt', 'psychodynamic', 'humanistic', 'existential', 'ifs']

        for approach_id in approaches:
            try:
                prompt_file = APPROACH_PROMPT_MAP.get(approach_id)
                prompt_path = PROMPTS_DIR / prompt_file

                if not prompt_path.exists():
                    print(f"❌ {approach_id}: 文件不存在 {prompt_path}")
                    return False

                with open(prompt_path, 'r', encoding='utf-8') as f:
                    prompt = f.read()

                print(f"✅ {approach_id}: {len(prompt)} 字符")
            except Exception as e:
                print(f"❌ {approach_id}: {str(e)}")
                return False

        return True

    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        return False


def test_approach_config():
    """测试3：检查流派配置"""
    print("\n" + "="*60)
    print("测试3：检查流派配置")
    print("="*60)

    try:
        # 不需要API Key也能测试配置加载
        from ai_analysis_service import APPROACHES_DIR
        import json

        approaches = []
        for config_file in APPROACHES_DIR.glob('*.json'):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if config.get('enabled', True):
                    approaches.append(config)
            except Exception as e:
                print(f"Warning: Failed to load {config_file}: {e}")

        approaches = sorted(approaches, key=lambda x: x.get('sort_order', 999))

        print(f"✅ 找到 {len(approaches)} 个启用的流派:")
        for approach in approaches:
            print(f"  - {approach['name_short']} ({approach['id']})")

        return True

    except Exception as e:
        print(f"❌ 加载失败: {str(e)}")
        return False


def test_small_analysis():
    """测试4：小规模AI分析测试"""
    print("\n" + "="*60)
    print("测试4：AI分析功能（最小化测试）")
    print("="*60)

    # 使用预配置的CatKing AI
    api_key = "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde"
    base_url = "https://www.catkingai.com"

    try:
        service = AIAnalysisService(api_key=api_key, base_url=base_url)

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

        print("正在调用 Claude API 进行测试分析...")
        print("（这将消耗少量tokens，约1000-2000 tokens）")

        # 只测试大观学派（最熟悉的流派）
        result = service.analyze_with_approach(
            approach_id='daguanpai',
            visitor_profile=test_profile,
            transcript=test_transcript,
            counselor_review="",
            max_tokens=2000  # 限制输出，节省成本
        )

        if 'error' in result:
            print(f"❌ 分析失败: {result['error']}")
            return False

        print("✅ AI分析成功！")
        print(f"  - 输入tokens: {result['metadata']['input_tokens']}")
        print(f"  - 输出tokens: {result['metadata']['output_tokens']}")
        print(f"  - 模型: {result['metadata']['model']}")
        print(f"\n分析结果预览（前200字符）：")
        print("-" * 60)
        print(result['analysis_text'][:200] + "...")
        print("-" * 60)

        return True

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "🔬" * 30)
    print("AI分析功能测试")
    print("🔬" * 30)

    tests = [
        ("Prompt模板", test_prompt_loading),
        ("流派配置", test_approach_config),
    ]

    results = []

    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {test_name}")

    all_passed = all(success for _, success in results)

    if all_passed:
        print("\n🎉 基础测试通过！")
        print("\n" + "="*60)
        print("开始实际AI分析测试...")
        print("="*60)
        test_small_analysis()
    else:
        print("\n❌ 部分测试失败，请检查配置")
        sys.exit(1)


if __name__ == '__main__':
    main()
