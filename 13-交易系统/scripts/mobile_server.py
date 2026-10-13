"""
mobile_server.py — 手机离线复盘的同步服务（2026-10-13，参考 2-时间管理助手 的同步设计）

和电脑界面（127.0.0.1:5077）分开：
  - 只开一个局域网 HTTPS 端口（默认 5443），只提供手机页面 + /m/api/* 同步接口
  - 除配对外所有接口都要设备令牌（请求头 X-Token），令牌只存哈希
  - 配对码只能在电脑界面（本机）生成，5 分钟有效，输错 5 次作废
  - 只接受局域网/本机地址的请求
  - 手机能写：复盘手写区、候选池的关注理由/买入条件、成交（成交进"待确认"，电脑上确认后才写入持仓）
  - 手机不能：改持仓/止损基准、调 AI、改交易系统
证书：用 2-时间管理助手 的自签 CA（iPhone 已信任）签一张本项目的证书，SAN 覆盖当前局域网 IP
"""
import os
import re
import time
import socket
import hashlib
import secrets
import datetime
import ipaddress
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
import store

PORT = int(os.getenv('MOBILE_PORT', '5443'))
CA_DIR = Path(os.getenv('MOBILE_CA_DIR', r'D:\AI-项目\2-时间管理助手\certs'))
CERT_DIR = store.ROOT / 'certs'
CERT_FILE, KEY_FILE = CERT_DIR / 'mobile-cert.pem', CERT_DIR / 'mobile-key.pem'
WEB_DIR = Path(__file__).parent / 'web' / 'mobile'
MAX_DEVICES = 3
PAIR_TTL = 300
PAIR_MAX_TRIES = 5
JOURNAL_DAYS = 30  # 每只股票下发最近 30 条跟盘

_pair = {'code': None, 'expires': 0, 'tries': 0}
_state = {'running': False, 'error': None, 'started': None}


# ─── 网络与证书 ───────────────────────────────────────────
def lan_ips() -> list:
    """本机局域网 IPv4（只要私网地址，排除 Radmin 等 26.x 虚拟网段）；默认路由的网卡排第一"""
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('223.5.5.5', 53))  # UDP connect 不发包，只用来找默认路由的网卡
        ips.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
        ips.append(info[4][0])
    out = []
    for ip in ips:
        a = ipaddress.ip_address(ip)
        if a.is_private and not a.is_loopback and ip not in out:
            out.append(ip)
    return out


def _cert_covers(ips: list) -> bool:
    from cryptography import x509
    if not CERT_FILE.exists() or not KEY_FILE.exists():
        return False
    c = x509.load_pem_x509_certificate(CERT_FILE.read_bytes())
    if c.not_valid_after_utc < datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30):
        return False
    san = c.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    have = {str(i) for i in san.get_values_for_type(x509.IPAddress)}
    return set(ips) <= have


def ensure_cert(ips: list):
    """证书不存在、快过期、或 IP 变了 → 用 CA 重签。iOS 对用户安装的 CA 要求有效期 ≤825 天，这里签 365 天"""
    if _cert_covers(ips):
        return
    from cryptography import x509
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    ca_cert_f, ca_key_f = CA_DIR / 'ca-cert.pem', CA_DIR / 'ca-key.pem'
    if not ca_cert_f.exists() or not ca_key_f.exists():
        raise RuntimeError(f'找不到 CA 证书：{CA_DIR}（在 config/.env 用 MOBILE_CA_DIR 指定）')
    ca_cert = x509.load_pem_x509_certificate(ca_cert_f.read_bytes())
    ca_key = serialization.load_pem_private_key(ca_key_f.read_bytes(), None)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    host = socket.gethostname()
    names = [x509.DNSName('localhost'), x509.DNSName(host), x509.DNSName(f'{host}.local'),
             x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]
    names += [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ips]
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, '交易系统-手机同步')]))
            .issuer_name(ca_cert.subject).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(minutes=5)).not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName(names), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .sign(ca_key, hashes.SHA256()))
    CERT_DIR.mkdir(exist_ok=True)
    # 证书链 = 本证书 + CA，iOS 校验更稳
    CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM) + ca_cert.public_bytes(serialization.Encoding.PEM))
    KEY_FILE.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL,
                                           serialization.NoEncryption()))


# ─── 设备与配对 ───────────────────────────────────────────
def _hash(tok: str) -> str:
    return hashlib.sha256(tok.encode()).hexdigest()


def load_devices() -> list:
    return store._read(store.DEVICES_FILE, [])


def new_pair_code() -> dict:
    """只由电脑界面（本机）调用"""
    _pair.update(code=f'{secrets.randbelow(10**6):06d}', expires=time.time() + PAIR_TTL, tries=0)
    return {'code': _pair['code'], 'expires_in': PAIR_TTL}


@store._locked
def pair(code: str, name: str) -> str:
    if not _pair['code'] or time.time() > _pair['expires']:
        raise ValueError('配对码已过期，请在电脑上重新生成')
    if not secrets.compare_digest(str(code), _pair['code']):
        _pair['tries'] += 1
        if _pair['tries'] >= PAIR_MAX_TRIES:
            _pair['code'] = None
            raise ValueError('输错次数太多，配对码已作废，请在电脑上重新生成')
        raise ValueError('配对码不对')
    devs = load_devices()
    if len(devs) >= MAX_DEVICES:
        raise ValueError(f'最多绑定 {MAX_DEVICES} 台手机，先在电脑上解绑一台')
    tok = 'tk_' + secrets.token_urlsafe(24)
    devs.append({'id': secrets.token_hex(4), 'name': (name or '手机')[:20], 'hash': _hash(tok),
                 'paired': store.now(), 'last_sync': None})
    store._write(store.DEVICES_FILE, devs)
    _pair['code'] = None  # 一码一用
    return tok


@store._locked
def revoke(dev_id: str):
    devs = load_devices()
    left = [d for d in devs if d['id'] != dev_id]
    if len(left) == len(devs):
        raise ValueError('没有这台设备')
    store._write(store.DEVICES_FILE, left)


def _auth():
    tok = request.headers.get('X-Token', '')
    h = _hash(tok) if tok else ''
    return next((d for d in load_devices() if h and secrets.compare_digest(d['hash'], h)), None)


@store._locked
def _touch(dev_id: str):
    devs = load_devices()
    for d in devs:
        if d['id'] == dev_id:
            d['last_sync'] = store.now()
    store._write(store.DEVICES_FILE, devs)


# ─── 同步数据 ─────────────────────────────────────────────
def load_pending() -> list:
    return store._read(store.PENDING_FILE, [])


def _log(dev: str, note: str):
    log = store._read(store.SYNC_LOG_FILE, [])
    log.insert(0, {'time': store.now(), 'device': dev, 'note': note})
    store._write(store.SYNC_LOG_FILE, log[:100])


def pull_payload() -> dict:
    """下发给手机：持仓概要（止损/预警只读）、最近跟盘、候选池、待确认成交"""
    pos = store.load_positions()
    stocks = []
    for code, p in pos.items():
        j = store.load_journal(code)
        snap_date, snap = next(((d, e['snapshot']) for d, e in j.items() if 'snapshot' in e), (None, None))
        sp = (snap or {}).get('position') or {}
        stocks.append({'code': code, 'name': p.get('name'), 'first_buy_price': p.get('first_buy_price'),
                       'thesis': p.get('thesis'), 'invalidation': p.get('invalidation'),
                       'stop': sp.get('stop'), 'warns': sp.get('warns'), 'shares': sp.get('shares'),
                       'last': {'date': snap_date, 'price': snap.get('price'), 'chg_pct': snap.get('chg_pct'),
                                'fetched': snap.get('fetched')} if snap else None,
                       'journal': {d: {**{k: e.get(k) for k in store.JOURNAL_FIELDS},
                                       'ts': {k: v.get('ts', 0) for k, v in e.get('_meta', {}).items()}}
                                   for d, e in list(j.items())[:JOURNAL_DAYS]}})
    watch = [{'code': c, 'name': w.get('name'), 'reason': w.get('reason'), 'buy_condition': w.get('buy_condition'),
              'ts': {k: v.get('ts', 0) for k, v in w.get('_meta', {}).items()}}
             for c, w in store.load_watchlist().items()]
    trades = [{k: t.get(k) for k in ('id', 'code', 'date', 'side', 'price', 'shares', 'note', 'status')}
              for t in load_pending()[:50]]
    return {'server_time': store.now_ms(), 'checks': store.CHECKS, 'stocks': stocks, 'watch': watch, 'trades': trades}


def _date(s) -> str:
    return datetime.date.fromisoformat(str(s)).isoformat()  # 格式不对抛 ValueError


@store._locked
def apply_push(body: dict, dev: dict) -> dict:
    """手机推送的修改：按字段比较时间戳，新的覆盖旧的（与时间管理助手一致）。返回每条的结果"""
    import render_md
    pos = store.load_positions()
    res = {'journal': [], 'watch': [], 'trades': []}
    touched = set()
    for it in body.get('journal') or []:
        code, field, ts = str(it.get('code')), it.get('field'), int(it.get('ts') or 0)
        key = f"{code}|{it.get('date')}|{field}"
        if code not in pos or field not in store.MOBILE_JOURNAL_FIELDS:
            res['journal'].append({'key': key, 'ok': False, 'why': '持仓里没有这只股票或字段不允许'})
            continue
        date = _date(it['date'])
        val = it.get('value')
        if field == 'checks':
            val = {c: bool((val or {}).get(c)) for c in store.CHECKS}
        else:
            val = str(val or '')[:5000]
        j = store.load_journal(code)
        e = j.get(date, {})
        meta = e.setdefault('_meta', {})
        if ts <= meta.get(field, {}).get('ts', 0):
            res['journal'].append({'key': key, 'ok': True, 'skipped': '电脑上的内容更新，保留电脑版'})
            continue
        e['_rev'] = e.get('_rev', 0) + 1
        e[field] = val
        meta[field] = {'ts': ts, 'src': 'mobile', 'device': dev['name'], 'rev': e['_rev']}
        e['updated'] = store.now()
        j[date] = e
        store._write(store.JOURNAL_DIR / f'{code}.json', dict(sorted(j.items(), reverse=True)))
        touched.add(code)
        res['journal'].append({'key': key, 'ok': True})
    watch = store.load_watchlist()
    for it in body.get('watch') or []:
        code, field, ts = str(it.get('code')), it.get('field'), int(it.get('ts') or 0)
        key = f'{code}|{field}'
        if code not in watch or field not in ('reason', 'buy_condition'):
            res['watch'].append({'key': key, 'ok': False, 'why': '候选池里已没有这只股票'})
            continue
        meta = watch[code].setdefault('_meta', {})
        if ts <= meta.get(field, {}).get('ts', 0):
            res['watch'].append({'key': key, 'ok': True, 'skipped': '电脑上的内容更新，保留电脑版'})
            continue
        watch[code][field] = (str(it.get('value') or '').strip() or None)
        meta[field] = {'ts': ts, 'src': 'mobile', 'device': dev['name']}
        watch[code]['updated'] = store.now()
        res['watch'].append({'key': key, 'ok': True})
    store._write(store.WATCH_FILE, watch)
    pending = load_pending()
    have = {t['id'] for t in pending}
    for t in body.get('trades') or []:
        tid = str(t.get('id', ''))[:40]
        if not re.fullmatch(r'[\w-]{6,40}', tid):
            res['trades'].append({'id': tid, 'ok': False, 'why': 'id 不对'})
            continue
        if tid in have:  # 重复推送（上次没收到回复）直接算成功
            res['trades'].append({'id': tid, 'ok': True})
            continue
        try:
            if str(t.get('code')) not in pos:
                raise ValueError('持仓里没有这只股票')
            if t.get('side') not in ('buy', 'sell') or float(t['price']) <= 0 or int(t['shares']) <= 0:
                raise ValueError('方向必须是买/卖，价格和股数必须大于 0')
            pending.insert(0, {'id': tid, 'code': str(t['code']), 'date': _date(t['date']), 'side': t['side'],
                               'price': float(t['price']), 'shares': int(t['shares']), 'note': str(t.get('note') or '')[:100],
                               'status': 'pending', 'device': dev['name'], 'received': store.now()})
            res['trades'].append({'id': tid, 'ok': True})
        except (KeyError, ValueError, TypeError) as ex:
            res['trades'].append({'id': tid, 'ok': False, 'why': str(ex)})
    store._write(store.PENDING_FILE, pending)
    for code in touched:
        render_md.render_journal(code)
    n = {k: sum(1 for r in v if r['ok'] and not r.get('skipped')) for k, v in res.items()}
    if any(n.values()):
        _log(dev['name'], f"复盘 {n['journal']} 项、候选池 {n['watch']} 项、成交 {n['trades']} 笔")
    return res


@store._locked
def decide_trade(tid: str, ok: bool) -> dict:
    """电脑上确认/拒绝手机录入的成交；确认后才写入 position.json"""
    pending = load_pending()
    t = next((x for x in pending if x['id'] == tid), None)
    if t is None or t['status'] != 'pending':
        raise ValueError('没有这笔待确认成交')
    if ok:
        pos = store.load_positions().get(t['code'])
        if pos is None:
            raise ValueError(f"持仓里没有 {t['code']}")
        pos.setdefault('trades', []).append({'date': t['date'], 'side': t['side'], 'price': t['price'],
                                             'shares': t['shares'], 'note': (t['note'] + '（手机录入）').strip()})
        store.save_position(t['code'], pos)
    t['status'] = 'confirmed' if ok else 'rejected'
    t['decided'] = store.now()
    store._write(store.PENDING_FILE, pending)
    return t


def status() -> dict:
    ips = lan_ips()
    return {**_state, 'port': PORT, 'urls': [f'https://{ip}:{PORT}/' for ip in ips],
            'ca_dir': str(CA_DIR), 'ca_ok': (CA_DIR / 'ca-cert.pem').exists(),
            'devices': [{k: d[k] for k in ('id', 'name', 'paired', 'last_sync')} for d in load_devices()],
            'pending': [t for t in load_pending() if t['status'] == 'pending'],
            'log': store._read(store.SYNC_LOG_FILE, [])[:20]}


# ─── 手机端 HTTP 服务 ─────────────────────────────────────
mapp = Flask(__name__)
mapp.json.ensure_ascii = False


@mapp.before_request
def _lan_only():
    a = ipaddress.ip_address(request.remote_addr or '0.0.0.0')
    if not (a.is_private or a.is_loopback):
        return jsonify({'error': '只允许局域网访问'}), 403
    if request.path.startswith('/m/api/') and request.path != '/m/api/pair':
        dev = _auth()
        if dev is None:
            return jsonify({'error': '未配对或已被电脑解绑，请重新配对', 'unpaired': True}), 401
        request.device = dev


@mapp.after_request
def _headers(r):
    # 不用 no-store：iOS 的 Cache API 拒存 no-store 响应（时间管理助手踩过，见其 BUG_FIX_LOG）
    r.headers['Cache-Control'] = 'no-cache'
    r.headers['X-Content-Type-Options'] = 'nosniff'
    return r


@mapp.errorhandler(ValueError)
def _verr(e):
    return jsonify({'error': str(e)}), 400


@mapp.get('/')
def m_index():
    return send_from_directory(WEB_DIR, 'index.html')


@mapp.get('/<path:name>')
def m_static(name):
    if name not in ('m.js', 'sw.js', 'manifest.json', 'icon.png'):
        return jsonify({'error': 'not found'}), 404
    return send_from_directory(WEB_DIR, name)


@mapp.post('/m/api/pair')
def m_pair():
    d = request.get_json() or {}
    return jsonify({'token': pair(d.get('code', ''), d.get('name', ''))})


@mapp.get('/m/api/pull')
def m_pull():
    _touch(request.device['id'])
    return jsonify(pull_payload())


@mapp.post('/m/api/push')
def m_push():
    res = apply_push(request.get_json() or {}, request.device)
    _touch(request.device['id'])
    return jsonify(res)


def start():
    """由 app.py 在后台线程启动；失败不影响电脑界面"""
    try:
        ips = lan_ips()
        ensure_cert(ips)
        from werkzeug.serving import make_server
        srv = make_server('0.0.0.0', PORT, mapp, threaded=True, ssl_context=(str(CERT_FILE), str(KEY_FILE)))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        _state.update(running=True, error=None, started=store.now())
        return True
    except Exception as e:
        _state.update(running=False, error=str(e)[:200])
        return False
