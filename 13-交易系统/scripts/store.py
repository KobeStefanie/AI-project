"""
store.py — 本地数据读写（JSON 为准）
  data/position.json         持仓（用户提供）
  data/journal/{代码}.json    每日跟盘：行情快照 + 我的想法/操作/复盘
  data/trading_system.json   我的交易系统（访谈逐步搭建）
  data/interviews/{id}.json  访谈对话
Markdown 版本由 render_md.py 自动生成，供阅读和 Claude Code 查阅
"""
import re
import json
import datetime
import functools
import threading
from pathlib import Path

# 电脑界面和手机同步服务在同一进程的不同线程里写同一批 JSON，读-改-写要串行
LOCK = threading.RLock()


def _locked(fn):
    @functools.wraps(fn)
    def wrap(*a, **kw):
        with LOCK:
            return fn(*a, **kw)
    return wrap

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'
POSITION_FILE = DATA / 'position.json'
JOURNAL_DIR = DATA / 'journal'
SYSTEM_FILE = DATA / 'trading_system.json'
INTERVIEW_DIR = DATA / 'interviews'
OUTLINE_FILE = ROOT / 'interview' / '访谈提纲.md'

WATCH_FILE = DATA / 'watchlist.json'

MAX_STOCKS = 3  # 铁律：最多持有3只（CLAUDE.md 目标与风控参数）
MAX_WATCH = 5   # 候选池最多5只（2026-10-13 用户原话"候选池的股票不能超过5只，可增减"）
WATCH_FIELDS = ('name', 'reason', 'buy_condition')
STATUSES = {'confirmed': '✅', 'draft': '🟡', 'todo': '⬜'}
CHECKS = ['持股逻辑今天仍然成立', '底仓股数没有变化', '做T只用了做T资金', '今天的操作都在计划内，不是情绪驱动']
JOURNAL_FIELDS = ('thoughts', 'operations', 'checks', 'did_right', 'improve', 'ai_comment')
MOBILE_JOURNAL_FIELDS = ('thoughts', 'operations', 'checks', 'did_right', 'improve')  # 手机能改的（AI 点评只在电脑上生成）
FIELD_NAMES = {'thoughts': '我的想法', 'operations': '今日操作', 'checks': '自查', 'did_right': '做对了什么',
               'improve': '要改什么', 'reason': '关注理由', 'buy_condition': '买入条件'}
MOBILE_DIR = DATA / 'mobile'               # 手机同步：设备令牌（只存哈希）、待确认成交、同步日志
DEVICES_FILE = MOBILE_DIR / 'devices.json'
PENDING_FILE = MOBILE_DIR / 'pending_trades.json'
SYNC_LOG_FILE = MOBILE_DIR / 'sync_log.json'


def now() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M')


def _read(path: Path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def _write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


# ─── 持仓 ────────────────────────────────────────────────
def load_positions() -> dict:
    return {k: v for k, v in _read(POSITION_FILE, {}).items() if not k.startswith('_')}


@_locked
def save_position(code: str, pos: dict):
    raw = _read(POSITION_FILE, {})  # 保留 "_说明" 等元信息
    raw[code] = pos
    _write(POSITION_FILE, raw)


# ─── 候选池 ──────────────────────────────────────────────
def load_watchlist() -> dict:
    return _read(WATCH_FILE, {})


@_locked
def save_watch(code: str, fields: dict) -> dict:
    """新增或修改候选股。只改传进来的字段；新增时检查上限和是否已持有"""
    w = load_watchlist()
    if code not in w:
        if code in load_positions():
            raise ValueError(f'{code} 已经在持仓里，不用再放候选池')
        if len(w) >= MAX_WATCH:
            raise ValueError(f'候选池最多 {MAX_WATCH} 只，已满：先移出一只再加')
        w[code] = {'name': None, 'reason': None, 'buy_condition': None, 'added': now()}
    meta = w[code].setdefault('_meta', {})
    for k in WATCH_FIELDS:
        if k in fields:
            v = (fields[k] or '').strip() or None
            if v != w[code].get(k):
                w[code][k] = v
                meta[k] = {'ts': now_ms(), 'src': 'desktop'}
    w[code]['updated'] = now()
    _write(WATCH_FILE, w)
    return w[code]


@_locked
def remove_watch(code: str):
    """移出候选池（只删 JSON 里的一条记录，不涉及文件删除）"""
    w = load_watchlist()
    if code not in w:
        raise ValueError(f'候选池里没有 {code}')
    del w[code]
    _write(WATCH_FILE, w)


# ─── 跟盘日志 ─────────────────────────────────────────────
def load_journal(code: str) -> dict:
    return _read(JOURNAL_DIR / f'{code}.json', {})


def now_ms() -> int:
    """毫秒时间戳（与手机端 Date.now() 同一口径，不受时区影响），用于按字段比较新旧"""
    import time
    return int(time.time() * 1000)


@_locked
def save_journal(code: str, date: str, fields: dict = None, snapshot: dict = None, base_rev: int = None) -> dict:
    """snapshot 只由行情刷新写入；fields 只由用户/AI点评写入，两者互不覆盖。
    每个字段记 _meta（修改时间/来源/版本），供手机同步按字段"新的覆盖旧的"。
    base_rev：电脑页面加载时的版本号；之后手机改过、电脑又要改成别的值 → 拒绝，避免旧页面盖掉手机内容"""
    j = load_journal(code)
    e = j.get(date, {})
    meta = e.setdefault('_meta', {})
    if snapshot is not None:
        e['snapshot'] = snapshot
    changed = [k for k in JOURNAL_FIELDS if fields and k in fields and fields[k] != e.get(k)]
    if base_rev is not None:
        hit = [k for k in changed if meta.get(k, {}).get('src') == 'mobile' and meta[k].get('rev', 0) > base_rev]
        if hit:
            raise ValueError('手机刚同步了新内容（' + '、'.join(FIELD_NAMES.get(k, k) for k in hit) +
                             '），先复制你刚写的内容，刷新页面后再保存')
    if changed:
        e['_rev'] = e.get('_rev', 0) + 1
        for k in changed:
            e[k] = fields[k]
            meta[k] = {'ts': now_ms(), 'src': 'desktop', 'rev': e['_rev']}
    e['updated'] = now()
    j[date] = e
    _write(JOURNAL_DIR / f'{code}.json', dict(sorted(j.items(), reverse=True)))
    return e


# ─── 交易系统 ─────────────────────────────────────────────
def load_system() -> dict:
    return _read(SYSTEM_FILE, {'modules': [], 'changelog': []})


@_locked
def update_system_item(data: dict) -> dict:
    """按 item_id 修改条目；没有 item_id 时在 module_id 下新增。每次修改都写版本记录"""
    s = load_system()
    status = data.get('status', 'draft')
    if status not in STATUSES:
        raise ValueError(f'状态只能是 {list(STATUSES)}')
    all_ids = {it['id'] for m in s['modules'] for it in m['items']}
    item = next((it for m in s['modules'] for it in m['items'] if it['id'] == data.get('item_id')), None)
    if item is None:
        mod = next((m for m in s['modules'] if m['id'] == data.get('module_id')), None)
        if mod is None or not data.get('name'):
            raise ValueError('找不到条目：需要有效的 item_id，或 module_id + name')
        n = len(mod['items']) + 1
        while f"{mod['id']}{n}" in all_ids:
            n += 1
        item = {'id': f"{mod['id']}{n}", 'name': data['name'], 'status': 'todo'}
        mod['items'].append(item)
        old = '新增'
    else:
        old = STATUSES[item['status']]
    item['content'] = data.get('content', item.get('content', ''))
    item['status'] = status
    item['source'] = data.get('source', item.get('source', ''))
    s['changelog'].insert(0, {'time': now(), 'note': f"{item['name']}：{old} → {STATUSES[status]} {item['content']}"})
    _write(SYSTEM_FILE, s)
    return item


# ─── 访谈 ────────────────────────────────────────────────
def interview_topics() -> list:
    text = OUTLINE_FILE.read_text(encoding='utf-8')
    topics = [{'key': m.group(1), 'title': m.group(2).strip()}
              for m in re.finditer(r'^## ([A-Z])\. (.+)$', text, re.M)]
    return topics + [{'key': 'Z', 'title': '自由聊：我的选股思路'}]


def list_interviews() -> list:
    out = []
    for f in sorted(INTERVIEW_DIR.glob('*.json'), reverse=True):
        iv = _read(f, {})
        out.append({'id': iv['id'], 'topic': iv['topic'], 'created': iv['created'],
                    'count': sum(1 for m in iv['messages'] if not m.get('hidden'))})
    return out


def load_interview(iid: str):
    return _read(INTERVIEW_DIR / f'{iid}.json', None)


@_locked
def save_interview(iv: dict):
    _write(INTERVIEW_DIR / f"{iv['id']}.json", iv)


def _to_recycle_bin(path: Path):
    """移到 Windows 回收站（可恢复）。全局规则：禁止直接删除文件"""
    import os
    import subprocess
    # 路径通过环境变量传给 PowerShell，不拼进命令字符串，避免中文/特殊字符注入
    ps = ("Add-Type -AssemblyName Microsoft.VisualBasic; "
          "[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($env:TRASH_PATH, 'OnlyErrorDialogs', 'SendToRecycleBin')")
    r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', ps],
                       env={**os.environ, 'TRASH_PATH': str(path)}, capture_output=True, timeout=30)
    if r.returncode != 0 or path.exists():
        raise ValueError(f'移到回收站失败：{path.name}')


def delete_interview(iid: str) -> list:
    """访谈的 JSON、自动生成的 md、导出的 PDF 一起移到回收站，返回已移走的文件名"""
    if not re.fullmatch(r'\d{8}-\d{6}', iid):
        raise ValueError('访谈 id 格式不对')
    files = [INTERVIEW_DIR / f'{iid}.json', ROOT / 'interview' / f'访谈记录-{iid}.md',
             ROOT / 'output' / 'interviews' / f'访谈记录-{iid}.pdf']
    if not files[0].exists():
        raise ValueError('访谈不存在')
    moved = []
    for f in files:
        if f.exists():
            _to_recycle_bin(f)
            moved.append(f.name)
    return moved


def new_interview(topic: str) -> dict:
    iv = {'id': datetime.datetime.now().strftime('%Y%m%d-%H%M%S'), 'topic': topic,
          'created': now(), 'messages': []}
    save_interview(iv)
    return iv


def add_message(iv: dict, role: str, content: str, hidden: bool = False):
    msg = {'role': role, 'content': content, 'time': now()}
    if hidden:
        msg['hidden'] = True  # 引导语：发给 AI，但界面和记录里不显示
    iv['messages'].append(msg)
