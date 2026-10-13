"""
render_md.py — 把 data/ 下的 JSON 渲染成 Markdown（只读视图，以 JSON 为准，不要手改 md）
  跟盘   → output/tracking/{代码}_{名称}.md
  交易系统 → interview/交易系统.md
  访谈   → interview/访谈记录-{id}.md
"""
from pathlib import Path
import store

ROOT = store.ROOT
NOTE = '> 本文件由界面数据自动生成（来源 {src}），请在界面里修改，手改会被覆盖。\n\n'


def _lines(text: str) -> list:
    rows = [s.strip() for s in (text or '').splitlines() if s.strip()]
    return [f'- {s}' for s in rows] or ['- （未填写）']


def render_journal(code: str) -> Path:
    j = store.load_journal(code)
    pos = store.load_positions().get(code, {})
    name = pos.get('name') or next((e['snapshot']['name'] for e in j.values() if 'snapshot' in e), code)
    L = [f'# {name}（{code}）每日跟盘记录', '', NOTE.format(src=f'data/journal/{code}.json').strip(), '']
    for date, e in j.items():
        L += [f'## {date}', '']
        s = e.get('snapshot')
        if s:
            ind = s['ind']
            ma = '  '.join(f"{k.upper()} {v}（{'上' if s['price'] >= v else '下'}）"
                           for k, v in ind.items() if k.startswith('ma'))
            L += ['### 行情',
                  f"- 收盘/现价：{s['price']}（{s['chg_pct']:+.2f}%）  开 {s['open']} 高 {s['high']} 低 {s['low']}",
                  f"- PE-TTM：{s['pe']}  PB：{s['pb']}", '',
                  '### 技术指标（前复权日线计算）', f'- 均线：{ma}',
                  f"- ATR14：{ind['atr14']}（{ind['atr_pct']}%）  近20日平均振幅：{ind['amp20']}%",
                  f"- 20日区间：{ind['low20']} ~ {ind['high20']}  量比（今/前5日均）：{ind['vol_ratio']}", '',
                  '### 下一交易日做T参考（仅限做T资金，底仓不动；规则为 Claude 建议，待实盘验证）',
                  f"- 正T：冲高到 {s['t_ref']['sell_above']} 以上可卖出一部分，回落 {s['t_ref']['gap']} 元以上再接回",
                  f"- 倒T：回落到 {s['t_ref']['buy_below']} 以下可用做T资金买入，反弹 {s['t_ref']['gap']} 元以上卖出", '']
            p = s.get('position')
            L.append('### 持仓与风控')
            if p:
                L += [f"- 首次买入价 {p['first']}  当前较首次 {p['from_first_pct']:+.2f}%",
                      f"- 止损价 {p['stop']}（距现价 {p['to_stop_pct']:+.2f}%）  加仓价 {p['adds'][0]} / {p['adds'][1]}"]
                if p.get('warns'):
                    L.append(f"- 三级线：-10% 预警 {p['warns'][0]} / -20% 预警 {p['warns'][1]} / -30% 止损 {p['stop']}")
                if p['shares']:
                    L.append(f"- 持股 {p['shares']} 股  均价 {p['avg_cost']}  浮动盈亏 {p['pnl']:+.2f} 元")
            L += [f'- {a}' for a in s.get('alerts', [])] + ['']
        checks = e.get('checks', {})
        L += ['### 我的想法', *_lines(e.get('thoughts')), '',
              '### 今日操作', *_lines(e.get('operations')), '',
              '### 今日复盘',
              *[f"- [{'x' if checks.get(c) else ' '}] {c}" for c in store.CHECKS],
              '- 做对了什么：', *_lines(e.get('did_right')),
              '- 要改什么：', *_lines(e.get('improve')), '',
              '### Claude 点评', *_lines(e.get('ai_comment')), '']
    out = ROOT / 'output' / 'tracking' / f'{code}_{name}.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def render_system() -> Path:
    s = store.load_system()
    L = ['# 我的交易系统', '', NOTE.format(src='data/trading_system.json').strip(), '',
         '> ✅ 已确认（你亲口确认，执行时必须遵守） 🟡 草案（Claude 建议，你还没拍板） ⬜ 待访谈', '']
    for m in s['modules']:
        L += [f"## {m['title']}", '| 项目 | 内容 | 状态 | 来源 |', '|---|---|---|---|']
        L += [f"| {it['name']} | {it.get('content') or '—'} | {store.STATUSES[it['status']]} | {it.get('source', '')} |"
              for it in m['items']]
        L.append('')
    L += ['## 版本记录', *[f"- {c['time']} {c['note']}" for c in s['changelog']], '']
    out = ROOT / 'interview' / '交易系统.md'
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def render_interview(iv: dict) -> Path:
    L = [f"# 访谈记录：{iv['topic']}", '', f"开始时间：{iv['created']}", '',
         NOTE.format(src=f"data/interviews/{iv['id']}.json").strip(), '']
    for m in iv['messages']:
        if m.get('hidden'):
            continue
        who = '我' if m['role'] == 'user' else 'Claude'
        L += [f"### {who}（{m['time']}）", '', m['content'], '']
    out = ROOT / 'interview' / f"访谈记录-{iv['id']}.md"
    out.write_text('\n'.join(L), encoding='utf-8')
    return out
