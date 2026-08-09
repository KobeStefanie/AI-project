#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析API服务器
端口: 8771
功能: 提供HTTP API用于触发AI流派分析
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import io
from pathlib import Path
import json
from datetime import datetime
import threading

# Windows GBK兼容性处理 - 使用更安全的方式
# 不强制包装stdout，避免subprocess环境下的冲突

# 导入AI分析服务
sys.path.insert(0, str(Path(__file__).parent))
from ai_analysis_service import AIAnalysisService

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).parent.parent
VISITORS_DIR = PROJECT_ROOT / 'data' / 'visitors'
CASES_DIR = PROJECT_ROOT / 'data' / 'cases' / 'processed'


def load_visit_data(visitor_id: str, visit_id: str) -> dict:
    """
    兼容两种数据格式读取访谈数据：
    1. 新格式：data/visitors/{visitor_id}/visits/{visit_id}.json
    2. 旧格式：data/cases/processed/{case_id}.json
    """
    # 优先尝试新格式（data/visitors/）
    new_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
    if new_path.exists():
        with open(new_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['_source'] = 'visitors'
        return data

    # 回退到旧格式（data/cases/processed/）
    # visitor_id 可能直接就是 case_id（如 C20260616001）
    for case_id in [visitor_id, visit_id]:
        old_path = CASES_DIR / f'{case_id}.json'
        if old_path.exists():
            with open(old_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data['_source'] = 'cases'
            return data

    return None

# 全局AI服务实例（懒加载）
_ai_service = None
_service_lock = threading.Lock()


def get_ai_service():
    """获取AI服务实例（线程安全的单例）"""
    global _ai_service
    if _ai_service is None:
        with _service_lock:
            if _ai_service is None:
                try:
                    _ai_service = AIAnalysisService()
                    print("[AI分析API] AI服务初始化成功")
                except Exception as e:
                    print(f"[AI分析API] AI服务初始化失败: {str(e)}")
                    raise
    return _ai_service


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        service = get_ai_service()
        return jsonify({
            'success': True,
            'status': 'healthy',
            'model': service.model
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/approaches', methods=['GET'])
def get_approaches():
    """获取所有启用的流派"""
    try:
        service = get_ai_service()
        approaches = service.get_enabled_approaches()
        return jsonify({
            'success': True,
            'approaches': approaches
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_single():
    """
    分析单个流派

    POST /api/analyze
    Body: {
        "visitor_id": "V20260616001",
        "visit_id": "visit_001",
        "approach_id": "daguanpai"
    }
    """
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        approach_id = data.get('approach_id')

        if not all([visitor_id, visit_id, approach_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 兼容两种数据格式读取
        visit_data = load_visit_data(visitor_id, visit_id)
        if visit_data is None:
            return jsonify({
                'success': False,
                'error': f'找不到数据：visitor_id={visitor_id}, visit_id={visit_id}'
            }), 404

        # 兼容新旧格式提取字段
        source = visit_data.get('_source', 'visitors')
        if source == 'cases':
            visitor_profile = {**visit_data.get('basic_info', {}), **visit_data.get('session_info', {})}
            transcript = visit_data.get('dialogue', '')
            counselor_review = visit_data.get('case_summary', '')
        else:
            visitor_profile = visit_data.get('visitor_profile', {})
            case_data_obj = visit_data.get('case_data', {})
            transcript = (case_data_obj.get('dialogue') or
                          case_data_obj.get('transcript') or
                          visit_data.get('transcript') or
                          visit_data.get('dialogue') or '')
            counselor_review = case_data_obj.get('counselor_review_html', '')

        if not transcript:
            return jsonify({
                'success': False,
                'error': '没有找到逐字稿/对话内容（dialogue/transcript字段为空）'
            }), 400

        # 执行分析
        service = get_ai_service()
        result = service.analyze_with_approach(
            approach_id,
            visitor_profile,
            transcript,
            counselor_review
        )

        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

        # 保存结果
        saved = service.save_analysis_to_visit(
            visitor_id,
            visit_id,
            approach_id,
            result['analysis_text']
        )

        # 保存后自动重新生成HTML（后台异步，不阻塞响应）
        try:
            import subprocess as _sp
            _flags = _sp.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            _sp.Popen(
                [sys.executable, str(PROJECT_ROOT / 'src' / 'generate_visit_details.py')],
                cwd=str(PROJECT_ROOT),
                creationflags=_flags,
                stdout=_sp.DEVNULL,
                stderr=_sp.DEVNULL
            )
        except Exception as _e:
            print(f"[HTML生成] 触发失败: {_e}")

        return jsonify({
            'success': True,
            'approach_id': approach_id,
            'saved': saved,
            'metadata': result['metadata']
        })

    except Exception as e:
        print(f"[API错误] {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyze_all', methods=['POST'])
def analyze_all():
    """
    分析所有启用的流派（异步后台执行）

    POST /api/analyze_all
    Body: {
        "visitor_id": "V20260616001",
        "visit_id": "visit_001",
        "approach_ids": ["daguanpai", "cbt"]  // 可选，不提供则分析所有启用的流派
    }
    """
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')
        approach_ids = data.get('approach_ids')  # 可选

        if not all([visitor_id, visit_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        # 兼容两种数据格式读取
        visit_data = load_visit_data(visitor_id, visit_id)
        if visit_data is None:
            return jsonify({
                'success': False,
                'error': f'找不到数据：visitor_id={visitor_id}, visit_id={visit_id}'
            }), 404

        source = visit_data.get('_source', 'visitors')
        if source == 'cases':
            visitor_profile = {**visit_data.get('basic_info', {}), **visit_data.get('session_info', {})}
            transcript = visit_data.get('dialogue', '')
            counselor_review = visit_data.get('case_summary', '')
        else:
            visitor_profile = visit_data.get('visitor_profile', {})
            case_data_obj = visit_data.get('case_data', {})
            transcript = (case_data_obj.get('dialogue') or
                          case_data_obj.get('transcript') or
                          visit_data.get('transcript') or
                          visit_data.get('dialogue') or '')
            counselor_review = case_data_obj.get('counselor_review_html', '')

        if not transcript:
            return jsonify({
                'success': False,
                'error': '没有找到逐字稿/对话内容'
            }), 400

        # 后台异步执行分析
        def background_analysis():
            try:
                service = get_ai_service()
                results = service.analyze_all_approaches(
                    visitor_profile,
                    transcript,
                    counselor_review,
                    approach_ids
                )

                # 保存所有结果
                for aid, result in results.items():
                    if 'error' not in result:
                        service.save_analysis_to_visit(
                            visitor_id,
                            visit_id,
                            aid,
                            result['analysis_text']
                        )

                print(f"[AI分析API] {visitor_id}/{visit_id} 全部流派分析完成")

            except Exception as e:
                print(f"[AI分析API] 后台分析失败: {str(e)}")

        # 启动后台线程
        thread = threading.Thread(target=background_analysis)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'AI分析已在后台启动',
            'visitor_id': visitor_id,
            'visit_id': visit_id,
            'approach_count': len(approach_ids) if approach_ids else '全部启用流派'
        })

    except Exception as e:
        print(f"[API错误] {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analysis_status', methods=['GET'])
def get_analysis_status():
    """
    查询分析状态

    GET /api/analysis_status?visitor_id=V20260616001&visit_id=visit_001
    """
    try:
        visitor_id = request.args.get('visitor_id')
        visit_id = request.args.get('visit_id')

        if not all([visitor_id, visit_id]):
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400

        visit_json_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
        if not visit_json_path.exists():
            return jsonify({
                'success': False,
                'error': f'Visit文件不存在: {visit_id}'
            }), 404

        with open(visit_json_path, 'r', encoding='utf-8') as f:
            visit_data = json.load(f)

        # 检查哪些流派已有分析
        existing_analyses = visit_data.get('case_data', {}).get('approach_analyses_html', {})

        service = get_ai_service()
        all_approaches = service.get_enabled_approaches()

        status = []
        for approach in all_approaches:
            aid = approach['id']
            status.append({
                'approach_id': aid,
                'approach_name': approach['name_short'],
                'has_analysis': aid in existing_analyses,
                'last_updated': visit_data.get('metadata', {}).get('last_ai_analysis')
            })

        return jsonify({
            'success': True,
            'visitor_id': visitor_id,
            'visit_id': visit_id,
            'status': status
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat_about_analysis():
    """
    与AI督导对话（针对特定流派的分析报告）
    POST /api/chat
    Body: {
        "approach_id": "psychodynamic",
        "approach_name": "精神动力学",
        "messages": [{"role": "user", "content": "..."}],
        "analysis_text": "..."
    }
    Returns: SSE text/event-stream
    """
    import requests as _requests
    from flask import Response, stream_with_context

    try:
        data = request.json
        approach_name = data.get('approach_name', '心理咨询督导')
        messages = data.get('messages', [])
        analysis_text = data.get('analysis_text', '')
        insights_text = data.get('insights_text', '').strip()

        if not messages:
            return jsonify({'success': False, 'error': '缺少消息内容'}), 400

        # 感悟上下文段落（有内容才加入）
        insights_section = ''
        if insights_text:
            insights_section = f"""

以下是咨询师之前保存的历次感悟与思考（请结合这些已有认知来回应，保持对话连贯性）：

---
{insights_text}
---"""

        system_content = f"""你是一位资深的{approach_name}取向心理督导，拥有深厚的理论功底和丰富的临床经验。

以下是本次咨询的{approach_name}视角AI分析报告：

---
{analysis_text}
---{insights_section}

请基于以上分析报告{' 和历次感悟' if insights_text else ''}，与咨询师进行专业的督导对话。你的职责是：
1. 帮助咨询师深入理解分析报告中的理论概念和临床发现
2. 解答咨询师对分析内容的具体疑问，并衔接其已有感悟
3. 提供更具体、可操作的临床应用建议
4. 引导咨询师反思自己的咨询实践和个人成长
5. 保持{approach_name}理论视角的一致性和专业严谨性

回应风格：专业而平易近人，聚焦于来访者的具体情况，避免泛泛而谈。每次回应300字以内，精准有力。
请使用纯文本输出，禁止使用任何Markdown格式符号（**粗体**、*斜体*、# 标题、- 列表符号等一律不用），直接用中文句子表达。"""

        api_url = "https://www.catkingai.com/v1/messages"
        api_key = "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-opus-4-8",
            "max_tokens": 1500,
            "system": system_content,
            "messages": messages,
            "stream": True
        }

        def generate():
            try:
                resp = _requests.post(
                    api_url, headers=headers, json=payload,
                    timeout=120, proxies={'http': None, 'https': None}, stream=True
                )
                for line in resp.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: ') and line != 'data: [DONE]':
                            try:
                                chunk = json.loads(line[6:])
                                if chunk.get('type') == 'content_block_delta':
                                    text = chunk.get('delta', {}).get('text', '')
                                    if text:
                                        yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
                            except Exception:
                                pass
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/supervisor_chat', methods=['POST'])
def supervisor_chat():
    """
    跨流派综合督导对话（SSE流式）
    POST /api/supervisor_chat
    Body: {
        "messages": [{"role": "user", "content": "..."}],
        "analyses_dict": {"精神动力学": "...", "CBT": "..."},
        "all_insights_text": "合并的所有感悟文本"
    }
    Returns: SSE text/event-stream
    """
    import requests as _requests
    from flask import Response, stream_with_context

    try:
        data = request.json
        messages = data.get('messages', [])
        analyses_dict = data.get('analyses_dict', {})
        all_insights_text = data.get('all_insights_text', '').strip()

        if not messages:
            return jsonify({'success': False, 'error': '缺少消息内容'}), 400

        # 构建多流派分析摘要
        analyses_section = ''
        if analyses_dict:
            parts = []
            for approach_name, analysis_text in analyses_dict.items():
                if analysis_text and analysis_text.strip():
                    # 截取前1500字避免上下文过长
                    trimmed = analysis_text.strip()[:1500]
                    parts.append(f"【{approach_name}视角】\n{trimmed}")
            if parts:
                analyses_section = '\n\n---\n\n'.join(parts)

        # 构建感悟摘要
        insights_section = ''
        if all_insights_text:
            insights_section = f"""

以下是咨询师在各流派感悟区保存的历次学习记录：

---
{all_insights_text[:2000]}
---"""

        approach_count = len(analyses_dict)
        system_content = f"""你是一位拥有20年临床经验的整合取向心理督导，精通精神动力学、CBT、人本、存在主义、IFS内在家庭系统、大观危机干预、拉康精神分析、荣格分析心理学等多种流派理论。

本次咨询已完成 {approach_count} 个流派的AI分析，汇总如下：

{analyses_section if analyses_section else '（尚无流派分析内容）'}{insights_section}

你的督导职责（跨流派整合视角）：
1. 整合各流派的发现，找出共识与分歧——不同流派对来访者的理解是否一致？
2. 从更宏观的视角识别来访者的核心议题（超越单一流派的概念框架）
3. 指出咨询师在本次咨询中最值得深挖的成长点
4. 提供综合策略建议——下次咨询应优先关注什么？用哪个流派的视角切入最有价值？
5. 如有感悟记录，结合咨询师的学习轨迹给出个性化建议

回应风格：整合、深刻、有温度。每次回应400字以内，聚焦实质，避免流水账式地罗列各流派观点。
请使用纯文本输出，禁止使用任何Markdown格式符号（**粗体**、*斜体*、# 标题、- 列表符号等一律不用），直接用中文句子表达。"""

        api_url = "https://www.catkingai.com/v1/messages"
        api_key = "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-opus-4-8",
            "max_tokens": 2000,
            "system": system_content,
            "messages": messages,
            "stream": True
        }

        def generate():
            try:
                resp = _requests.post(
                    api_url, headers=headers, json=payload,
                    timeout=120, proxies={'http': None, 'https': None}, stream=True
                )
                for line in resp.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: ') and line != 'data: [DONE]':
                            try:
                                chunk = json.loads(line[6:])
                                if chunk.get('type') == 'content_block_delta':
                                    text = chunk.get('delta', {}).get('text', '')
                                    if text:
                                        yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
                            except Exception:
                                pass
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    try:
        print("=" * 60)
        print("AI分析API服务器 - 端口 8771")
        print("=" * 60)
    except Exception:
        pass

    app.run(
        host='0.0.0.0',
        port=8771,
        debug=False,
        threaded=True
    )
