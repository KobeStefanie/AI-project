"""
app.py — 本地界面（访谈 / 跟盘 / 交易系统）
启动：cd scripts && python app.py   然后浏览器打开 http://127.0.0.1:5077
只监听本机 127.0.0.1，无登录；不要改成 0.0.0.0 暴露到局域网
"""
import re
import sys
import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, jsonify, request, send_file, send_from_directory
import store
import render_md
import coach
import ai_client
from data_fetcher import normalize_code

app = Flask(__name__, static_folder=str(Path(__file__).parent / 'web'))
_kline_cache = {}  # {code: (trade_date, chart_data)}


def err(msg, code=400):
    return jsonify({'error': msg}), code


@app.errorhandler(ai_client.AIError)
def _ai_err(e):
    return err(str(e), 502)


@app.errorhandler(ValueError)
def _val_err(e):
    return err(str(e))


@app.get('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.get('/api/meta')
def meta():
    return jsonify({'ai': ai_client.status(), 'checks': store.CHECKS, 'max_stocks': store.MAX_STOCKS,
                    'max_watch': store.MAX_WATCH,
                    'statuses': store.STATUSES, 'topics': store.interview_topics()})


# ─── 持仓 ────────────────────────────────────────────────
@app.get('/api/positions')
def positions():
    return jsonify(store.load_positions())


@app.post('/api/positions/<code>')
def save_position(code):
    code = normalize_code(code)[0]
    allp = store.load_positions()
    if code not in allp and len(allp) >= store.MAX_STOCKS:
        return err(f'铁律：最多持有 {store.MAX_STOCKS} 只，已满')
    d = request.get_json()
    pos = allp.get(code, {'trades': []})
    for k in ('name', 'thesis', 'invalidation', 'first_buy_date'):
        if k in d:
            pos[k] = (d[k] or '').strip() or None
    for k in ('capital', 'first_buy_price'):
        if k in d:
            pos[k] = float(d[k]) if d[k] not in (None, '') else None
    if 'trades' in d:
        trades = []
        for t in d['trades']:
            if t.get('side') not in ('buy', 'sell') or float(t['price']) <= 0 or int(t['shares']) <= 0:
                raise ValueError('成交记录：方向必须是买/卖，价格和股数必须大于 0')
            trades.append({'date': t.get('date', ''), 'side': t['side'], 'price': float(t['price']),
                           'shares': int(t['shares']), 'note': t.get('note', '')})
        pos['trades'] = trades
    store.save_position(code, pos)
    return jsonify(pos)


# ─── 候选池 ──────────────────────────────────────────────
def _code6(code: str) -> str:
    code = normalize_code(code)[0]
    if not re.fullmatch(r'\d{6}', code):
        raise ValueError('股票代码要是 6 位数字，如 600690')
    return code


@app.get('/api/watchlist')
def watchlist():
    """候选池 + 实时行情 + 最近一次系统筛选结论（行情失败不影响列表显示）"""
    from data_fetcher import get_batch_quotes
    w = store.load_watchlist()
    try:
        quotes = get_batch_quotes(list(w)) if w else {}
    except Exception:
        quotes = {}
    out = []
    for code, c in w.items():
        q = quotes.get(code, {})
        out.append({**c, 'code': code, 'price': q.get('price'), 'chg_pct': q.get('chg_pct'),
                    'screen': coach.screen_row(code)})
    return jsonify({'items': out, 'max': store.MAX_WATCH})


@app.post('/api/watchlist/<code>')
def save_watch(code):
    code = _code6(code)
    d = request.get_json() or {}
    if code not in store.load_watchlist() and not d.get('name'):
        # 新增时没填名称，用行情接口取，不手猜
        from data_fetcher import get_realtime_quote
        try:
            d['name'] = get_realtime_quote(code).get('name')
        except Exception:
            pass
    return jsonify(store.save_watch(code, d))


@app.post('/api/watchlist/<code>/remove')
def remove_watch(code):
    store.remove_watch(_code6(code))
    return jsonify({'ok': True})


# ─── 手机同步（这些接口只在本机 127.0.0.1 界面上，手机访问不到）──────
@app.get('/api/mobile')
def mobile_status():
    import mobile_server
    return jsonify(mobile_server.status())


@app.post('/api/mobile/pair')
def mobile_pair_code():
    import mobile_server
    if not mobile_server._state['running']:
        return err('手机同步服务没有启动：' + (mobile_server._state['error'] or '未知原因'))
    return jsonify(mobile_server.new_pair_code())


@app.post('/api/mobile/devices/<dev_id>/revoke')
def mobile_revoke(dev_id):
    import mobile_server
    mobile_server.revoke(dev_id)
    return jsonify({'ok': True})


@app.post('/api/mobile/trades/<tid>')
def mobile_trade(tid):
    """确认或拒绝手机录入的成交；确认后才写进持仓"""
    import mobile_server
    ok = bool((request.get_json() or {}).get('confirm'))
    return jsonify(mobile_server.decide_trade(tid, ok))


# ─── 跟盘 ────────────────────────────────────────────────
@app.get('/api/journal/<code>')
def journal(code):
    return jsonify(store.load_journal(normalize_code(code)[0]))


@app.post('/api/journal/<code>/refresh')
def refresh(code):
    import daily_track
    code = normalize_code(code)[0]
    date, snap, df = daily_track.refresh(code)
    _kline_cache[code] = (date, daily_track.kline_for_chart(df))
    return jsonify({'date': date, 'snapshot': snap})


@app.get('/api/kline/<code>')
def kline(code):
    import daily_track
    code = normalize_code(code)[0]
    if code not in _kline_cache:
        df = daily_track.get_kline(code)
        _kline_cache[code] = (str(df['date'].iloc[-1]), daily_track.kline_for_chart(df))
    return jsonify(_kline_cache[code][1])


@app.post('/api/journal/<code>/<date>')
def save_journal(code, date):
    code = normalize_code(code)[0]
    datetime.date.fromisoformat(date)  # 格式不对会抛 ValueError
    d = request.get_json() or {}
    base = d.pop('base_rev', None)  # 页面加载时的版本号，防止旧页面盖掉手机刚同步的内容
    e = store.save_journal(code, date, fields=d, base_rev=int(base) if base is not None else None)
    render_md.render_journal(code)
    return jsonify(e)


@app.post('/api/journal/<code>/<date>/comment')
def comment(code, date):
    code = normalize_code(code)[0]
    text = coach.review_comment(code, date)
    e = store.save_journal(code, date, fields={'ai_comment': text})
    render_md.render_journal(code)
    return jsonify(e)


# ─── 交易系统 ─────────────────────────────────────────────
@app.get('/api/system')
def system():
    return jsonify(store.load_system())


@app.post('/api/system/item')
def system_item():
    item = store.update_system_item(request.get_json())
    render_md.render_system()
    return jsonify(item)


# ─── 访谈 ────────────────────────────────────────────────
@app.get('/api/interviews')
def interviews():
    return jsonify(store.list_interviews())


@app.get('/api/interviews/<iid>')
def interview(iid):
    iv = store.load_interview(iid)
    return jsonify(iv) if iv else err('访谈不存在', 404)


@app.post('/api/interviews/<iid>/delete')
def delete_interview(iid):
    # 移到回收站（可恢复），不直接删除
    return jsonify({'moved': store.delete_interview(iid)})


@app.get('/api/interviews/<iid>/pdf')
def interview_pdf(iid):
    iv = store.load_interview(iid)
    if not iv:
        return err('访谈不存在', 404)
    import export_pdf
    out = export_pdf.export_interview(iv)
    return send_file(out, mimetype='application/pdf', as_attachment=True, download_name=out.name)


@app.post('/api/interviews')
def new_interview():
    topic = request.get_json().get('topic') or '自由聊'
    iv = store.new_interview(topic)
    store.add_message(iv, 'user', coach.opening_prompt(topic), hidden=True)
    try:
        coach.interview_reply(iv)
    finally:
        store.save_interview(iv)  # AI 失败也保留这次访谈，可以稍后重试
    render_md.render_interview(iv)
    return jsonify(iv)


@app.post('/api/interviews/<iid>/message')
def send_message(iid):
    iv = store.load_interview(iid)
    if not iv:
        return err('访谈不存在', 404)
    text = (request.get_json().get('content') or '').strip()
    if text:  # 空内容 = 重试上一次失败的回复
        store.add_message(iv, 'user', text)
    if iv['messages'] and iv['messages'][-1]['role'] == 'assistant':
        return err('没有需要回复的消息')
    store.save_interview(iv)
    reply = coach.interview_reply(iv)
    store.save_interview(iv)
    render_md.render_interview(iv)
    return jsonify(reply)


@app.post('/api/interviews/<iid>/apply')
def apply_suggestion(iid):
    """采纳建议：交易系统条目写成 🟡 草案；个股逻辑写入 position.json。✅ 只能在交易系统页由用户确认"""
    d = request.get_json()
    src = f'访谈 {iid}'
    if d.get('watch'):
        if d.get('field') not in ('reason', 'buy_condition'):
            return err('field 只能是 reason 或 buy_condition')
        code = _code6(d['watch'])
        if code not in store.load_watchlist():
            return err(f'候选池里没有 {code}，先在"候选池"页加进去')
        store.save_watch(code, {d['field']: d['content']})
        return jsonify({'ok': True})
    if d.get('code'):
        if d.get('field') not in ('thesis', 'invalidation'):
            return err('field 只能是 thesis 或 invalidation')
        code = normalize_code(d['code'])[0]
        pos = store.load_positions().get(code)
        if pos is None:
            return err(f'持仓里没有 {code}')
        pos[d['field']] = d['content']
        store.save_position(code, pos)
        return jsonify({'ok': True})
    item = store.update_system_item({**d, 'status': 'draft', 'source': src})
    render_md.render_system()
    return jsonify(item)


if __name__ == '__main__':
    import mobile_server
    print('界面地址：http://127.0.0.1:5077')
    # 手机同步服务单独一个局域网 HTTPS 端口，只有配对过的手机能访问；失败不影响电脑界面
    if mobile_server.start():
        print('手机同步：' + '  '.join(mobile_server.status()['urls']) + '（在界面"手机同步"页配对）')
    else:
        print('手机同步未启动：' + str(mobile_server._state['error']))
    app.run(host='127.0.0.1', port=5077, debug=False)
