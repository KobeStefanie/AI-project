#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话模拟训练API服务器
端口: 8772
功能: Phase 4 - 对话模拟训练系统后端
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sys
import os
import json
from datetime import datetime
from pathlib import Path
import uuid
import anthropic
import time

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).parent.parent
VISITORS_DIR = PROJECT_ROOT / 'data' / 'visitors'
TRAINING_SESSIONS_DIR = PROJECT_ROOT / 'data' / 'training_sessions'
TRAINING_PERSONAS_DIR = PROJECT_ROOT / 'data' / 'training_personas'
PROMPTS_DIR = PROJECT_ROOT / 'data' / 'config' / 'prompts'

# 确保目录存在
TRAINING_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
TRAINING_PERSONAS_DIR.mkdir(parents=True, exist_ok=True)

# API配置（来自CLAUDE.md）
API_KEY = "sk-d285143ff8b40377e38294cc41f2f86b518349f3f6278328c439bfed7d89fdde"
BASE_URL = "https://www.catkingai.com"
MODEL = "claude-opus-4-8"

client = anthropic.Anthropic(
    api_key=API_KEY,
    base_url=BASE_URL
)

# ==================== 工具函数 ====================

def load_visit_data(visitor_id: str, visit_id: str) -> dict:
    """加载真实来访记录"""
    visit_path = VISITORS_DIR / visitor_id / 'visits' / f'{visit_id}.json'
    if not visit_path.exists():
        return None
    with open(visit_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_visitor_profile(visitor_id: str) -> dict:
    """加载来访者档案"""
    profile_path = VISITORS_DIR / visitor_id / 'profile.json'
    if not profile_path.exists():
        return None
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_session(session_data: dict) -> str:
    """保存训练会话数据"""
    session_id = session_data['session_id']
    file_path = TRAINING_SESSIONS_DIR / f'{session_id}.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    return str(file_path)

def load_session(session_id: str) -> dict:
    """加载训练会话数据"""
    file_path = TRAINING_SESSIONS_DIR / f'{session_id}.json'
    if not file_path.exists():
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_persona(persona_data: dict) -> str:
    """保存虚拟人设"""
    persona_id = persona_data['persona_id']
    file_path = TRAINING_PERSONAS_DIR / f'{persona_id}.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(persona_data, f, ensure_ascii=False, indent=2)
    return str(file_path)

# ==================== API端点 ====================

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "healthy", "port": 8772, "service": "simulation_training_api"})

@app.route('/api/generate_persona_from_visit', methods=['POST'])
def generate_persona_from_visit():
    """从真实档案生成人设"""
    try:
        data = request.json
        visitor_id = data.get('visitor_id')
        visit_id = data.get('visit_id')

        if not visitor_id or not visit_id:
            return jsonify({"error": "缺少visitor_id或visit_id"}), 400

        # 加载数据
        visit_data = load_visit_data(visitor_id, visit_id)
        if not visit_data:
            return jsonify({"error": f"未找到访谈记录: {visitor_id}/{visit_id}"}), 404

        profile_data = load_visitor_profile(visitor_id)
        if not profile_data:
            return jsonify({"error": f"未找到档案: {visitor_id}"}), 404

        # 构建Prompt（Prompt 1）
        # 从case_data中读取对话内容和咨询师复盘
        case_data = visit_data.get('case_data', {})
        dialogue_text = case_data.get('dialogue', visit_data.get('dialogue', ''))
        counselor_review = case_data.get('counselor_review', visit_data.get('counselor_review', ''))

        # 从profile_data.basic_info中读取基本信息
        basic_info = profile_data.get('basic_info', {})
        age = basic_info.get('age', '未知')
        gender = basic_info.get('gender', '未知')
        complaint = visit_data.get('visit_summary', {}).get('complaint', basic_info.get('initial_complaint', '未知'))

        prompt = f"""你是一位专业的心理咨询案例模拟专家。请根据以下真实接访记录，生成一个一致的来访者人设，用于对话模拟训练。

【真实接访记录】
逐字稿/对话内容：
{dialogue_text}

咨询师复盘：
{counselor_review}

来访者基本信息：
年龄：{age}
性别：{gender}
主诉：{complaint}

---

请输出JSON格式的人设（严格按此结构）：

{{
  "name": "匿名称呼（如'李先生'）",
  "age": 数字,
  "gender": "男/女",
  "core_issues": ["核心问题1", "核心问题2", "核心问题3"],
  "emotional_state": "情绪状态描述（3-5个词）",
  "key_phrases": ["来访者典型语句1", "典型语句2", "典型语句3"],
  "background_summary": "背景概述（100字以内）",
  "defense_mechanisms": ["防御机制1", "防御机制2"],
  "expectations": {{
    "explicit": "显性期待",
    "implicit": "隐性期待"
  }}
}}

【要求】
1. ⚠️ 严格基于真实记录，不编造不存在的信息
2. key_phrases必须来自真实逐字稿原文
3. 捕捉来访者的独特性（语言风格、情绪特征）
4. 为后续对话模拟提供一致性依据
5. 如果某项信息真实记录中没有，标注为null，不猜测

【验证】
输出前检查：
- [ ] core_issues是否有原文支持？
- [ ] key_phrases是否真实出现过？
- [ ] 是否编造了不存在的背景信息？"""

        # 调用Claude API
        message = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        # 解析JSON
        try:
            # 尝试提取JSON（可能在markdown代码块中）
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            persona = json.loads(json_str)
        except Exception as e:
            return jsonify({
                "error": "解析人设JSON失败",
                "detail": str(e),
                "raw_response": response_text
            }), 500

        # 返回结果（含token统计）
        return jsonify({
            "persona": persona,
            "tokens": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_custom_persona', methods=['POST'])
def save_custom_persona():
    """保存自定义虚拟人设"""
    try:
        persona_data = request.json

        # 生成persona_id
        if 'persona_id' not in persona_data:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            persona_data['persona_id'] = f'persona_custom_{timestamp}'

        # 添加元数据
        if 'created_at' not in persona_data:
            persona_data['created_at'] = datetime.now().isoformat()
        persona_data['created_by'] = 'user'

        # 保存
        file_path = save_persona(persona_data)

        return jsonify({
            "persona_id": persona_data['persona_id'],
            "file_path": file_path
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/list_personas', methods=['GET'])
def list_personas():
    """列出所有虚拟人设"""
    try:
        personas = []
        for file_path in TRAINING_PERSONAS_DIR.glob('*.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                persona_data = json.load(f)
                personas.append({
                    "persona_id": persona_data['persona_id'],
                    "name": persona_data['persona']['name'],
                    "tags": persona_data.get('tags', []),
                    "created_at": persona_data.get('created_at')
                })

        return jsonify({"personas": personas})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """开始训练会话"""
    try:
        data = request.json
        persona = data.get('persona')
        approach = data.get('approach', '存在主义')
        persona_source = data.get('persona_source', {})

        if not persona:
            return jsonify({"error": "缺少persona数据"}), 400

        # 生成session_id
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = str(uuid.uuid4())[:6]
        session_id = f'session_{timestamp}_{random_suffix}'

        # 创建session数据结构
        session_data = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "duration_seconds": 0,
            "approach": approach,
            "model_used": MODEL,
            "persona_source": persona_source,
            "visitor_persona": persona,
            "dialogue": [],
            "final_report": None,
            "cost_info": {
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "estimated_cost_usd": 0
            }
        }

        # 保存
        save_session(session_data)

        return jsonify({
            "session_id": session_id,
            "created_at": session_data['created_at']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat_stream', methods=['POST'])
def chat_stream():
    """对话流式输出（AI扮演来访者）"""
    try:
        data = request.json
        session_id = data.get('session_id')
        user_msg = data.get('user_msg')

        if not session_id or not user_msg:
            return jsonify({"error": "缺少session_id或user_msg"}), 400

        # 加载session
        session = load_session(session_id)
        if not session:
            return jsonify({"error": f"未找到会话: {session_id}"}), 404

        # 添加用户消息到对话历史
        turn_seq = len(session['dialogue']) + 1
        counselor_turn = {
            "seq": turn_seq,
            "role": "counselor",
            "content": user_msg,
            "timestamp": datetime.now().isoformat(),
            "supervision_feedback": None
        }
        session['dialogue'].append(counselor_turn)

        # 构建Prompt（Prompt 2：AI扮演来访者）
        persona = session['visitor_persona']
        dialogue_history = '\n'.join([
            f"[{turn['role']}] {turn['content']}"
            for turn in session['dialogue'][-10:]  # 最近10轮
        ])

        prompt = f"""你正在扮演一位来访者，参与心理咨询对话模拟训练。

【来访者人设（严格遵循）】
姓名：{persona['name']}
年龄：{persona['age']}
性别：{persona['gender']}
核心问题：{', '.join(persona['core_issues'])}
情绪状态：{persona['emotional_state']}
防御机制：{', '.join(persona.get('defense_mechanisms', []))}
典型语句：{', '.join(persona['key_phrases'])}
背景：{persona['background_summary']}

【对话历史】
{dialogue_history}

【咨询师刚才说】
{user_msg}

---

请以来访者身份自然回应，注意：

1. **人设一致性**：
   - 保持情绪状态一致（{persona['emotional_state']}）
   - 使用人设中的语言模式
   - 展现防御机制：{', '.join(persona.get('defense_mechanisms', []))}

2. **真实性**：
   - 根据咨询师的回应调整情绪（好的共情会让来访者更开放）
   - 不要刻意配合，模拟真实来访者的自然反应
   - 如果咨询师技术不当（过早给建议、打断），自然表现出抗拒或困惑

3. **回应长度**：
   - 50-150字，符合真实对话节奏
   - 不要一次性倾泻太多信息（除非咨询师引导得当）

4. **口语化表达**：
   - 用生活化语言，避免专业术语
   - 可以有停顿、重复、叹气等真实表现
   - 例："我...我也不知道该怎么说...就是觉得...（叹气）很难受"

【禁止】
- 不要主动"顿悟"（咨询没到那个阶段）
- 不要说"你这个问题问得很好"等不自然的话
- 不要展开人设中没有的新议题
- 不要突然变得积极乐观（除非咨询确实推进到那个阶段）

【输出格式】
直接输出来访者的话，不要加"来访者："等前缀。"""

        # SSE流式输出
        def generate():
            full_response = ""
            input_tokens = 0
            output_tokens = 0

            with client.messages.stream(
                model=MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"

                # 获取token统计
                message = stream.get_final_message()
                input_tokens = message.usage.input_tokens
                output_tokens = message.usage.output_tokens

            # 保存AI回应到session
            client_turn = {
                "seq": turn_seq + 1,
                "role": "client",
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            }
            session['dialogue'].append(client_turn)

            # 更新cost_info
            session['cost_info']['total_input_tokens'] += input_tokens
            session['cost_info']['total_output_tokens'] += output_tokens
            # Opus定价：$15/1M input, $75/1M output
            cost = (input_tokens / 1_000_000 * 15) + (output_tokens / 1_000_000 * 75)
            session['cost_info']['estimated_cost_usd'] += cost

            save_session(session)

            # 发送token统计
            yield f"data: {json.dumps({'tokens': {'input': input_tokens, 'output': output_tokens}}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return Response(generate(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/supervise_turn', methods=['POST'])
def supervise_turn():
    """异步督导评估（单轮）"""
    try:
        data = request.json
        session_id = data.get('session_id')
        turn_seq = data.get('turn_seq')

        if not session_id or not turn_seq:
            return jsonify({"error": "缺少session_id或turn_seq"}), 400

        # 加载session
        session = load_session(session_id)
        if not session:
            return jsonify({"error": f"未找到会话: {session_id}"}), 404

        # 获取对话上下文
        if turn_seq > len(session['dialogue']):
            return jsonify({"error": "turn_seq超出范围"}), 400

        recent_dialogue = session['dialogue'][max(0, turn_seq-10):turn_seq+1]  # 最近10轮
        counselor_turn = session['dialogue'][turn_seq-1]
        client_turn = session['dialogue'][turn_seq] if turn_seq < len(session['dialogue']) else None

        if not client_turn:
            return jsonify({"error": "缺少来访者回应"}), 400

        # 构建督导Prompt（Prompt 3）
        persona = session['visitor_persona']
        approach = session['approach']

        recent_history = '\n'.join([
            f"[{turn['role']}] {turn['content']}"
            for turn in recent_dialogue
        ])

        prompt = f"""你是一位资深心理咨询督导，正在实时评估学员的技术运用。

【流派】
{approach}

【来访者人设】
{json.dumps(persona, ensure_ascii=False, indent=2)}

【对话上下文（最近10轮）】
{recent_history}

【学员刚才的回应】
{counselor_turn['content']}

【来访者的反应】
{client_turn['content']}

---

请评估这一轮咨询回应（基于{approach}流派视角），输出详细的结构化分析：

【输出JSON格式】
{{
  "technique_used": "技术名称（如：简单反映）",
  "quality_score": 数字（0-10）,
  "comment": "即时反馈（30字以内）",
  "better_example": "更好的说法示例（可选）",
  "client_emotion": "来访者的情绪分析（怎么说）",
  "client_motivation": "来访者的动机分析（想要什么）",
  "counselor_emotion": "咨询师的情绪判断（怎么说）",
  "counselor_motivation": "咨询师的动机/意图（想干嘛）",
  "theoretical_basis": "理论依据（该流派的理论支持）"
}}

【评分标准】
- 9-10分：技术运用精准，显著推进咨询进程
- 7-8分：技术正确，有效但可优化
- 5-6分：技术识别对，但执行不到位
- 3-4分：技术不当或时机不对
- 0-2分：严重错误（如：伤害性回应、违反伦理）

【要求】
- 基于该流派的理论框架评估
- client_emotion: 分析来访者说话时的情绪状态（焦虑、悲伤、愤怒等）
- client_motivation: 分析来访者此刻的深层需求（被理解、被接纳、寻求建议等）
- counselor_emotion: 判断咨询师回应的情绪基调（共情、中立、好奇等）
- counselor_motivation: 分析咨询师的意图（建立关系、探索问题、引导觉察等）
- theoretical_basis: 说明该技术在{approach}流派中的理论依据
- 所有分析简洁明确，每项15-30字
- ⚠️ 不编造学员没用过的技术"""

        # 调用Claude API
        message = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        # 解析JSON
        try:
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text.strip()

            supervision = json.loads(json_str)
        except Exception as e:
            # 如果解析失败，返回原文
            supervision = {
                "technique_used": "未识别",
                "quality_score": 5,
                "comment": "督导反馈解析失败",
                "better_example": None,
                "_raw_response": response_text
            }

        # 保存到session
        session['dialogue'][turn_seq-1]['supervision_feedback'] = supervision

        # 更新cost_info
        session['cost_info']['total_input_tokens'] += message.usage.input_tokens
        session['cost_info']['total_output_tokens'] += message.usage.output_tokens
        cost = (message.usage.input_tokens / 1_000_000 * 15) + (message.usage.output_tokens / 1_000_000 * 75)
        session['cost_info']['estimated_cost_usd'] += cost

        save_session(session)

        return jsonify({
            "supervision": supervision,
            "tokens": {
                "input": message.usage.input_tokens,
                "output": message.usage.output_tokens
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/list_sessions', methods=['GET'])
def list_sessions():
    """列出训练记录"""
    try:
        sessions = []
        for file_path in TRAINING_SESSIONS_DIR.glob('*.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

                # 兼容旧数据：如果final_report不存在或为None，从dialogue计算
                final_report = session_data.get('final_report')
                if final_report and isinstance(final_report, dict):
                    total_turns = final_report.get('total_turns', 0)
                    overall_score = final_report.get('overall_score', 0)
                else:
                    total_turns = len(session_data.get('dialogue', []))
                    overall_score = 0

                sessions.append({
                    "session_id": session_data.get('session_id', 'unknown'),
                    "created_at": session_data.get('created_at', ''),
                    "visitor_name": session_data.get('visitor_persona', {}).get('name', '未知'),
                    "approach": session_data.get('approach', '未知'),
                    "total_turns": total_turns,
                    "overall_score": overall_score,
                    "duration_seconds": session_data.get('duration_seconds', 0),
                    "estimated_cost_usd": session_data.get('cost_info', {}).get('estimated_cost_usd', 0)
                })

        # 按时间倒序
        sessions.sort(key=lambda x: x['created_at'], reverse=True)

        return jsonify({"sessions": sessions})

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/get_session', methods=['GET'])
def get_session():
    """获取单次训练详情"""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({"error": "缺少session_id"}), 400

        session = load_session(session_id)
        if not session:
            return jsonify({"error": f"未找到会话: {session_id}"}), 404

        return jsonify(session)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/end_session', methods=['POST'])
def end_session():
    """结束会话并生成报告（Prompt 4暂时简化为占位符）"""
    try:
        data = request.json
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({"error": "缺少session_id"}), 400

        # 加载session
        session = load_session(session_id)
        if not session:
            return jsonify({"error": f"未找到会话: {session_id}"}), 404

        # 计算时长
        start_time = datetime.fromisoformat(session['created_at'])
        end_time = datetime.now()
        session['duration_seconds'] = int((end_time - start_time).total_seconds())

        # 生成简化的最终报告（完整的Prompt 4稍后实现）
        total_turns = len(session['dialogue'])
        techniques_summary = []

        # 统计技术使用
        technique_stats = {}
        for turn in session['dialogue']:
            if turn.get('supervision_feedback'):
                tech = turn['supervision_feedback'].get('technique_used', '未识别')
                score = turn['supervision_feedback'].get('quality_score', 5)
                if tech not in technique_stats:
                    technique_stats[tech] = {"count": 0, "scores": []}
                technique_stats[tech]['count'] += 1
                technique_stats[tech]['scores'].append(score)

        for tech, stats in technique_stats.items():
            avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
            techniques_summary.append({
                "technique": tech,
                "count": stats['count'],
                "avg_score": round(avg_score, 1)
            })

        # 计算总分
        all_scores = [
            turn['supervision_feedback']['quality_score']
            for turn in session['dialogue']
            if turn.get('supervision_feedback')
        ]
        overall_score = int(sum(all_scores) / len(all_scores)) if all_scores else 0

        session['final_report'] = {
            "overall_score": overall_score,
            "total_turns": total_turns,
            "techniques_summary": techniques_summary,
            "highlights": ["报告生成功能完善中"],
            "core_issues": ["报告生成功能完善中"],
            "improvement_suggestions": {
                "P0": ["完整报告生成功能将在后续版本实现"],
                "P1": [],
                "P2": []
            },
            "next_training_focus": "继续训练"
        }

        save_session(session)

        return jsonify({
            "session_id": session_id,
            "final_report": session['final_report']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/session_detail/<session_id>', methods=['GET'])
def session_detail(session_id):
    """获取训练详情（与get_session相同，但用RESTful路径）"""
    try:
        session = load_session(session_id)
        if not session:
            return jsonify({"error": f"未找到会话: {session_id}"}), 404
        return jsonify(session)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete_session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除训练记录"""
    try:
        file_path = TRAINING_SESSIONS_DIR / f'{session_id}.json'
        if not file_path.exists():
            return jsonify({"error": f"未找到会话: {session_id}"}), 404

        # 删除文件
        file_path.unlink()

        return jsonify({"message": "删除成功", "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export_excel/<session_id>', methods=['GET'])
def export_excel(session_id):
    """导出训练记录为Excel"""
    try:
        session = load_session(session_id)
        if not session:
            return jsonify({"error": f"未找到会话: {session_id}"}), 404

        # 导入生成Excel的代码
        import sys
        sys.path.append(str(PROJECT_ROOT / 'src'))
        from generate_training_excel import generate_training_excel

        # 生成Excel
        excel_path = generate_training_excel(session)

        # 返回文件
        from flask import send_file
        return send_file(excel_path, as_attachment=True, download_name=f'训练记录_{session_id}.xlsx')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("对话模拟训练API服务器")
    print("端口: 8772")
    print("API文档: http://localhost:8772/health")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8772, debug=False)
