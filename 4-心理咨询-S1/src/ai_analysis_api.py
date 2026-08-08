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
