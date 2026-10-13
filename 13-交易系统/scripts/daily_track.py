"""
daily_track.py — 持仓每日跟盘（行情快照）
用法：
  python daily_track.py 000977       # 刷新今天的行情快照，并重新生成 Markdown 记录
界面里点"刷新行情"调用的也是这里的 build_snapshot()

数据来源（全部来自接口，不手填）：
  - 实时价：新浪行情 get_realtime_quote()
  - PE/PB：腾讯行情 get_pe_pb()
  - 日线：AKShare stock_zh_a_daily（前复权，用于均线/ATR）
  - 持仓：data/position.json（用户提供，null 字段不计算）
保存：data/journal/{代码}.json（只写 snapshot，不碰用户写的想法/复盘）
"""

import sys
import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')  # Windows 控制台默认 GBK，打印 emoji 会报错

sys.path.insert(0, str(Path(__file__).parent))
from data_fetcher import ak, get_realtime_quote, get_pe_pb, normalize_code
import store

# 风控参数（来源：CLAUDE.md 目标与风控参数，2026-10-12 用户确认）
STOP_RATIO = 0.70             # 止损 = 首次买入价 × 70%
WARN_LEVELS = (0.90, 0.80)    # 跌 10% / 20% 预警，只做提醒，不是加仓价（2026-10-13 用户确认）
ADD_LEVELS = (0.85, 0.75)     # 两批加仓档位（Claude 建议，用户确认 5:3:2 方案时一并确认）
BUCKETS = {'底仓': 0.5, '加仓子弹': 0.3, '做T': 0.2}


def get_kline(code: str, days: int = 250):
    pure, prefix = normalize_code(code)
    start = (datetime.date.today() - datetime.timedelta(days=days * 2)).strftime('%Y%m%d')
    end = datetime.date.today().strftime('%Y%m%d')
    df = ak.stock_zh_a_daily(symbol=f'{prefix}{pure}', start_date=start, end_date=end, adjust='qfq')
    return df.tail(days).reset_index(drop=True)


def calc_indicators(df) -> dict:
    close, high, low, vol = df['close'], df['high'], df['low'], df['volume']
    prev_close = close.shift(1)
    tr = (high - low).combine((high - prev_close).abs(), max).combine((low - prev_close).abs(), max)
    ind = {f'ma{n}': round(close.tail(n).mean(), 2) for n in (5, 10, 20, 60) if len(close) >= n}
    ind['atr14'] = round(tr.tail(14).mean(), 2)
    ind['atr_pct'] = round(ind['atr14'] / close.iloc[-1] * 100, 2)
    ind['high20'] = round(high.tail(20).max(), 2)
    ind['low20'] = round(low.tail(20).min(), 2)
    ind['vol_ratio'] = round(vol.iloc[-1] / vol.iloc[-6:-1].mean(), 2)  # 今日量 / 前5日均量
    # 近20日平均振幅（(最高-最低)/昨收）
    amp = ((high - low) / prev_close * 100).tail(20)
    ind['amp20'] = round(amp.mean(), 2)
    return ind


def kline_for_chart(df, n: int = 120) -> list:
    """图表用：最近 n 根K线 + 均线（均线在完整序列上算，避免开头缺值）"""
    d = df.copy()
    for w in (5, 10, 20, 60):
        d[f'ma{w}'] = d['close'].rolling(w).mean().round(2)
    d = d.tail(n)
    cols = ['open', 'close', 'low', 'high', 'volume', 'ma5', 'ma10', 'ma20', 'ma60']
    return [{'date': str(r['date']), **{c: (None if r[c] != r[c] else float(r[c])) for c in cols}}
            for _, r in d.iterrows()]


def calc_position(pos: dict, price: float):
    """根据持仓记录计算盈亏、止损、加仓价、子弹余额。缺首次买入价返回 None"""
    first = pos.get('first_buy_price')
    capital = pos.get('capital')
    trades = pos.get('trades', [])
    if not first:
        return None
    shares = sum(t['shares'] if t['side'] == 'buy' else -t['shares'] for t in trades)
    cost = sum(t['price'] * t['shares'] if t['side'] == 'buy' else -t['price'] * t['shares'] for t in trades)
    res = {
        'first': first,
        'stop': round(first * STOP_RATIO, 2),
        'warns': [round(first * k, 2) for k in WARN_LEVELS],
        'adds': [round(first * k, 2) for k in ADD_LEVELS],
        'shares': shares,
        'avg_cost': round(cost / shares, 3) if shares else None,
        'pnl': round(price * shares - cost, 2) if shares else None,
        'from_first_pct': round((price / first - 1) * 100, 2),
        'to_stop_pct': round((first * STOP_RATIO / price - 1) * 100, 2),
    }
    if capital:
        res['buckets'] = {k: round(capital * v, 2) for k, v in BUCKETS.items()}
        res['cash_left'] = round(capital - cost, 2)
    return res


def calc_alerts(price: float, p) -> list:
    if not p:
        return ['持仓未录入（缺首次买入价），止损/加仓价无法计算']
    if price <= p['stop']:
        return [f"🔴 三级：跌破止损价 {p['stop']}（首次买入价 -30%），按规则止损，不再加仓"]
    alerts = []
    if price <= p['warns'][1]:
        alerts.append(f"🟠 二级预警：跌破 {p['warns'][1]}（首次买入价 -20%），距止损 {p['to_stop_pct']}%，回头核对持股逻辑和证伪条件")
    elif price <= p['warns'][0]:
        alerts.append(f"🟡 一级预警：跌破 {p['warns'][0]}（首次买入价 -10%），回头核对持股逻辑和证伪条件")
    if price <= p['adds'][1]:
        alerts.append('🟡 已到第2批加仓价')
    elif price <= p['adds'][0]:
        alerts.append('🟡 已到第1批加仓价')
    return alerts


def build_snapshot(code: str) -> dict:
    """抓取行情并计算，返回 (交易日, 快照)。快照里的数字全部来自接口或由接口数据计算"""
    code = normalize_code(code)[0]
    q = get_realtime_quote(code)
    if not q:
        raise RuntimeError(f'取不到 {code} 的实时行情')
    pepb = get_pe_pb([code]).get(code, {})
    df = get_kline(code)
    ind = calc_indicators(df)
    pos = store.load_positions().get(code, {})
    price = q['price']
    half = round(ind['atr14'] / 2, 2)  # 以今日收盘为基准、半个 ATR 为间距，给下一交易日做T参考
    p = calc_position(pos, price)
    trade_date = q.get('date') or datetime.date.today().strftime('%Y-%m-%d')
    kline_date = str(df['date'].iloc[-1])
    snap = {
        'name': q['name'], 'price': price, 'chg_pct': q['chg_pct'],
        'open': q['open'], 'high': q['high'], 'low': q['low'],
        'pe': pepb.get('pe'), 'pb': pepb.get('pb'),
        'ind': ind,
        't_ref': {'sell_above': round(price + half, 2), 'buy_below': round(price - half, 2), 'gap': half},
        'position': p,
        'alerts': calc_alerts(price, p),
        'kline_date': kline_date,
        'fetched': store.now(),
    }
    if kline_date != trade_date:
        snap['alerts'].append(f'日线最新日期为 {kline_date}，指标未含 {trade_date}')
    return trade_date, snap, df


def refresh(code: str) -> tuple:
    trade_date, snap, df = build_snapshot(code)
    store.save_journal(code, trade_date, snapshot=snap)
    import render_md
    render_md.render_journal(code)
    return trade_date, snap, df


def main():
    if len(sys.argv) < 2:
        print('用法：python daily_track.py 000977')
        return
    code = normalize_code(sys.argv[1])[0]
    trade_date, snap, _ = refresh(code)
    print(f"{snap['name']} {trade_date} 收 {snap['price']}（{snap['chg_pct']:+.2f}%）")
    for a in snap['alerts']:
        print('  ' + a)
    print(f'已写入：data/journal/{code}.json，Markdown 已同步到 output/tracking/')


if __name__ == '__main__':
    main()
