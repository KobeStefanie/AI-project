"""
coach.py — 访谈教练 & 复盘点评的提示词与调用
原则：
  - 用户的规则来自 CLAUDE.md 铁律 + data/trading_system.json，原样发给模型，不让模型凭空编
  - 模型给的是"建议"，只能把条目提为 🟡 草案；✅ 只能由用户在界面上点"确认"
"""
import re
import json
import store
import ai_client

ROOT = store.ROOT


def _iron_rules() -> str:
    """取 CLAUDE.md 的"决策原则"整章，原文发给模型"""
    text = (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')
    m = re.search(r'^## 决策原则.*?(?=^## )', text, re.S | re.M)
    return m.group(0).strip() if m else ''


def _system_text() -> str:
    lines = []
    for m in store.load_system()['modules']:
        lines.append(m['title'])
        for it in m['items']:
            lines.append(f"  [{it['id']}] {store.STATUSES[it['status']]} {it['name']}：{it.get('content') or '（空）'}")
    return '\n'.join(lines)


def _positions_text() -> str:
    pos = store.load_positions()
    if not pos:
        return '无持仓'
    rows = []
    for code, p in pos.items():
        rows.append(f"{p.get('name')}（{code}）：首次买入价 {p.get('first_buy_price') or '未录入'}，"
                    f"持股逻辑 {p.get('thesis') or '未录入'}，证伪条件 {p.get('invalidation') or '未录入'}")
    return '\n'.join(rows)


def _latest_snapshots() -> str:
    rows = []
    for code in store.load_positions():
        j = store.load_journal(code)
        date, e = next(((d, e) for d, e in j.items() if 'snapshot' in e), (None, None))
        if e:
            s = e['snapshot']
            rows.append(f"{s['name']} {date}：收 {s['price']}（{s['chg_pct']:+.2f}%），PE {s['pe']}，"
                        f"MA5 {s['ind'].get('ma5')}，MA20 {s['ind'].get('ma20')}，MA60 {s['ind'].get('ma60')}，"
                        f"ATR14 {s['ind']['atr14']}，20日区间 {s['ind']['low20']}~{s['ind']['high20']}")
    return '\n'.join(rows) or '无'


def _screen_facts() -> str:
    """最近一次系统筛选的关键结论（来源文件名一起给模型，方便它引用）"""
    files = sorted((ROOT / 'output').glob('screening_*.md'))
    for f in reversed(files):
        t = f.read_text(encoding='utf-8')
        if any(code in t for code in store.load_positions()):
            m = re.search(r'#### 层1：量化筛选(.*?)#### 层2', t, re.S)
            n = re.search(r'#### 层3：财务快照(.*?)---', t, re.S)
            return f"来源 {f.relative_to(ROOT).as_posix()}：\n" + (m.group(1).strip() if m else '') + '\n' + (n.group(1).strip() if n else '')
    return '无'


def screen_row(code: str):
    """最近一份含该股票的筛选报告里，它在摘要表的那一行：PE分位、综合分、是否通过层1"""
    pat = re.compile(rf'^\| \*\*(.+?)\*\* {code} \|(.+)\|\s*$', re.M)
    for f in sorted((ROOT / 'output').glob('screening_*.md'), reverse=True):
        m = pat.search(f.read_text(encoding='utf-8'))
        if m:
            cols = [c.strip() for c in m.group(2).split('|')]
            # 列：行业 现价 今日 PE-TTM PE历史分位 PB 护城河 综合分 通过？
            return {'file': f.relative_to(ROOT).as_posix(), 'pe_pct': cols[4], 'score': cols[7].strip('*'),
                    'pass': '✅' in cols[8], 'date': f.stem[10:18]}
    return None


def _watch_text() -> str:
    w = store.load_watchlist()
    if not w:
        return '空（还没有候选股）'
    rows = []
    for code, c in w.items():
        sr = screen_row(code)
        sr_txt = (f"系统筛选（{sr['file']}）：PE历史分位 {sr['pe_pct']}，综合分 {sr['score']}，"
                  f"{'通过' if sr['pass'] else '未通过'}层1") if sr else '系统筛选：还没跑过'
        rows.append(f"{c.get('name') or code}（{code}）：关注理由 {c.get('reason') or '未写'}；"
                    f"买入条件 {c.get('buy_condition') or '未写'}；{sr_txt}")
    return '\n'.join(rows)


INTERVIEW_SYSTEM = """你是用户的股票交易教练，正在和用户做一对一访谈。用简体中文。

## 你的目标
提升用户自己的能力：帮他把模糊的想法说清楚，搭出符合他风险偏好和操作习惯的交易系统。你不是替他选股，也不是给他喊单。

## 访谈方式
- 每轮只问 1~2 个问题，问题要具体、能回答。不要一次抛一串问题。
- 先复述你理解的他的意思（一句话），再给专业意见，再追问。
- 他说得模糊（"感觉会涨""应该没问题"）时，追问到可观察、可验证的程度。
- 他的想法和铁律冲突时，当场指出，引用铁律原文。
- 给专业意见时明确写"我的建议："，和他的想法分开。
- 每次回复控制在 250 字以内，口语化，不要用大标题。
- 正文里引用交易系统条目时说条目名称，不要说 [pick2] 这类内部 id（id 只用在 SUGGEST 里）。

## 数据纪律（极其重要）
- 只能使用下面"已知数据"里的数字。没有的数字，说"这个数据我这里没有"，不要凭记忆说某只股票的营收、ROE、订单。
- 不预测短期涨跌，不给具体买卖点（做T参考价已由系统按 ATR 计算，可以引用）。

## 沉淀规则
当他就某个条目给出了清楚的回答，在回复末尾单独一行输出（可多行，每行一个）：
[[SUGGEST {"item_id":"条目id","content":"一句话规则，尽量用他的原话"}]]
新条目（交易系统里没有的）用：
[[SUGGEST {"module_id":"模块id","name":"条目名","content":"规则"}]]
如果是个股的持股逻辑或证伪条件，用：
[[SUGGEST {"code":"股票代码","field":"thesis或invalidation","content":"他的原话"}]]
如果是候选池里某只股票的关注理由或买入条件，用：
[[SUGGEST {"watch":"股票代码","field":"reason或buy_condition","content":"他的原话"}]]
只在他真的说清楚了时才输出，不要替他编。用户会自己决定是否采纳。

## 候选池（最多 5 只，用户自己增减）
- 候选池是"准备买、还没买"的股票。持仓最多 3 只，新买入只能从候选池里挑。
- 聊到候选股时，帮他把"为什么关注"和"到什么条件才买"说成可验证的话（估值、基本面事实），不能是"感觉要涨了"。
- 候选股没通过系统筛选时如实说，但由他决定留不留。候选池满 5 只还想加新的，先问他换掉哪只、为什么。
- 不替他往候选池里加股票，不推荐具体股票进池。

## 铁律（CLAUDE.md 原文，最高优先级）
{rules}

## 他目前的交易系统（[id] 状态 名称：内容）
{system}

## 已知数据
持仓：
{positions}
候选池：
{watch}
最新行情（系统接口抓取）：
{snapshots}
系统筛选结论：
{screen}
"""

REVIEW_SYSTEM = """你是用户的股票交易教练，正在点评他今天的跟盘复盘。用简体中文，200 字以内，口语化。

点评顺序：
1. 他今天的操作和想法有没有违反铁律或他自己的交易系统（引用具体条目），有就直说
2. 他的想法里哪些是基于估值/基本面，哪些是基于情绪或短期走势（底仓只能看前者）
3. 一个具体的、明天就能执行的改进点

不预测涨跌，不编数据，只用下面给出的内容。用户还没写想法和操作时，提醒他先写，不要硬点评。

## 铁律（CLAUDE.md 原文）
{rules}

## 他的交易系统
{system}
"""


def _fmt(tpl: str, **kw) -> str:
    for k, v in kw.items():
        tpl = tpl.replace('{' + k + '}', v)  # 不用 str.format，避免模板里的 JSON 花括号被解析
    return tpl


def parse_suggestions(text: str):
    """把回复里的 [[SUGGEST {...}]] 摘出来，返回 (正文, 建议列表)"""
    sugs = []
    for raw in re.findall(r'\[\[SUGGEST (\{.*?\})\]\]', text):
        try:
            sugs.append(json.loads(raw))
        except json.JSONDecodeError:
            pass
    clean = re.sub(r'\n?\[\[SUGGEST \{.*?\}\]\]', '', text).strip()
    return clean, sugs


def interview_reply(iv: dict) -> dict:
    system = _fmt(INTERVIEW_SYSTEM, rules=_iron_rules(), system=_system_text(),
                  positions=_positions_text(), watch=_watch_text(), snapshots=_latest_snapshots(), screen=_screen_facts())
    history = [{'role': m['role'], 'content': m['content']} for m in iv['messages']]
    text = ai_client.chat(history, system=system)
    clean, sugs = parse_suggestions(text)
    store.add_message(iv, 'assistant', clean)
    iv['messages'][-1]['suggestions'] = sugs
    return iv['messages'][-1]


def opening_prompt(topic: str) -> str:
    """开场引导：发给模型，但不在界面显示"""
    outline = store.OUTLINE_FILE.read_text(encoding='utf-8')
    m = re.search(rf'^## {re.escape(topic[:1])}\. .*?(?=^## |\Z)', outline, re.S | re.M)
    qs = m.group(0) if m else '（自由聊，从他目前最想理清的事情开始）'
    return (f'开始访谈，主题：{topic}。参考问题库：\n{qs}\n'
            '先用一两句话说明这次聊什么、为什么重要，然后只问第一个问题。')


def review_comment(code: str, date: str) -> str:
    e = store.load_journal(code).get(date, {})
    s = e.get('snapshot', {})
    pos = store.load_positions().get(code, {})
    checks = e.get('checks', {})
    user = '\n'.join([
        f"股票：{pos.get('name')}（{code}） 日期：{date}",
        f"行情：收 {s.get('price')}（{s.get('chg_pct')}%），均线 {s.get('ind', {})}" if s else '行情：未刷新',
        f"系统提示：{'；'.join(s.get('alerts', [])) or '无'}",
        f"持股逻辑：{pos.get('thesis') or '未录入'}；证伪条件：{pos.get('invalidation') or '未录入'}",
        f"我的想法：{e.get('thoughts') or '（没写）'}",
        f"今日操作：{e.get('operations') or '（没写）'}",
        '自查：' + '；'.join(f"{c} {'✓' if checks.get(c) else '✗'}" for c in store.CHECKS),
        f"做对了什么：{e.get('did_right') or '（没写）'}",
        f"要改什么：{e.get('improve') or '（没写）'}",
    ])
    system = _fmt(REVIEW_SYSTEM, rules=_iron_rules(), system=_system_text())
    return ai_client.chat([{'role': 'user', 'content': user}], system=system, max_tokens=800)
