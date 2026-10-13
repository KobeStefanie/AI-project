"""
ai_client.py — 界面用的大模型调用
配置在 config/.env，二选一（都填时优先 Anthropic）：
  方式1 Anthropic 格式：ANTHROPIC_API_KEY（必填）、ANTHROPIC_BASE_URL（中转地址，可选）
  方式2 OpenAI 兼容格式：OPENAI_API_KEY（必填）、OPENAI_API_BASE（中转地址，可选）
  AI_MODEL  可选，默认 claude-opus-5-5（2026-10-13 用户指定，界面/选股/stock_ai 统一用这个）
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).parent.parent / 'config' / '.env'
DEFAULT_MODEL = 'claude-opus-5-5'
MAX_RETRIES = 3  # SDK 对 5xx/超时自动重试（指数退避），默认只有 2 次
TIMEOUT = 240    # Opus 5.5 经 CatKing 中转，短回复实测约 70 秒，长回复要留余量


def model_name() -> str:
    """当前使用的模型：config/.env 的 AI_MODEL 优先，否则用默认值"""
    load_dotenv(ENV_FILE, override=True)
    return os.getenv('AI_MODEL') or DEFAULT_MODEL


class AIError(Exception):
    pass


def _env() -> dict:
    # 每次重读，改了 .env 不用重启界面；只读 config/.env，不借用系统里其他程序的密钥
    model = model_name()
    if os.getenv('ANTHROPIC_API_KEY'):
        return {'kind': 'anthropic', 'key': os.getenv('ANTHROPIC_API_KEY'),
                'base': os.getenv('ANTHROPIC_BASE_URL') or None, 'model': model}
    return {'kind': 'openai', 'key': os.getenv('OPENAI_API_KEY'),
            'base': os.getenv('OPENAI_API_BASE') or None, 'model': model}


def status() -> dict:
    e = _env()
    return {'configured': bool(e['key']), 'kind': e['kind'], 'base': e['base'] or '官方地址', 'model': e['model']}


def _raise(e: Exception, model: str):
    code = getattr(e, 'status_code', None)
    if code in (401, 403):
        raise AIError(f'AI 密钥无效或已被服务商停用（HTTP {code}），请在 config/.env 更换密钥') from e
    if code == 404 or 'model_not_found' in str(e):
        raise AIError(f'模型 {model} 不可用（HTTP {code}）：检查 config/.env 的密钥和 AI_MODEL') from e
    if code and code >= 500:
        # 中转服务偶发 502「Upstream stream ended without a response」，SDK 已自动重试过，再点一次重试一般就好
        raise AIError(f'AI 中转服务临时出错（HTTP {code}），已自动重试 {MAX_RETRIES} 次仍失败，稍等片刻再点"重试"') from e
    raise AIError(f'AI 调用失败：{str(e)[:200]}') from e


def chat(messages: list, system: str = '', temperature: float = 0.4, max_tokens: int = 1500) -> str:
    e = _env()
    if not e['key']:
        raise AIError('未配置 AI：请在 config/.env 填写 ANTHROPIC_API_KEY 或 OPENAI_API_KEY')
    try:
        if e['kind'] == 'anthropic':
            from anthropic import Anthropic
            client = Anthropic(api_key=e['key'], base_url=e['base'], timeout=TIMEOUT, max_retries=MAX_RETRIES)
            kw = {'system': system} if system else {}
            r = client.messages.create(model=e['model'], messages=messages,
                                       temperature=temperature, max_tokens=max_tokens, **kw)
            return ''.join(b.text for b in r.content if b.type == 'text')
        from openai import OpenAI
        client = OpenAI(api_key=e['key'], base_url=e['base'], timeout=TIMEOUT, max_retries=MAX_RETRIES)
        msgs = ([{'role': 'system', 'content': system}] if system else []) + messages
        r = client.chat.completions.create(model=e['model'], messages=msgs,
                                           temperature=temperature, max_tokens=max_tokens)
        return r.choices[0].message.content or ''
    except AIError:
        raise
    except Exception as ex:
        _raise(ex, e['model'])
