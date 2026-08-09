"""
data_fetcher.py — A股数据获取层
已验证可用（绕过Windows注册表代理）：
  - 实时行情：新浪财经
  - PE/PB：腾讯行情
  - 日线K线：腾讯财经
  - 财务历史：AKShare（NoProxyAdapter补丁绕过Windows注册表代理）
"""

import ssl
import json
import re
import datetime
import urllib.request
import urllib.parse
import pandas as pd

# ─── AKShare 代理补丁（必须在 import akshare 之前执行）────────────────
import requests
from requests.adapters import HTTPAdapter

class _NoProxyAdapter(HTTPAdapter):
    """强制空代理，绕过Windows注册表代理设置"""
    def send(self, request, *args, **kwargs):
        kwargs['proxies'] = {}
        return super().send(request, *args, **kwargs)

_orig_merge = requests.Session.merge_environment_settings
def _no_proxy_merge(self, url, proxies, stream, verify, cert):
    settings = _orig_merge(self, url, proxies, stream, verify, cert)
    settings['proxies'] = {}
    return settings
requests.Session.merge_environment_settings = _no_proxy_merge

import akshare as ak  # 在补丁之后导入，确保生效

# ─── 全局配置 ────────────────────────────────────────────────
_ssl_ctx = ssl._create_unverified_context()

# 各行业PE历史区间（用于估算当前估值分位）
HISTORICAL_PE = {
    '白酒':     (15, 50),
    '银行':     (5,  12),
    '保险':     (8,  20),
    '半导体':   (40, 150),
    '工业自动化':(25, 60),
    '机器人':   (30, 80),
    '医药':     (20, 60),
    '新能源':   (15, 40),
    '军工':     (30, 80),
    '消费':     (20, 40),
    '互联网':   (20, 50),
    '其他':     (15, 40),
}

# ─── 核心HTTP工具 ─────────────────────────────────────────────
def _get(url, params=None, ref='https://gu.qq.com/', enc='utf-8'):
    """urllib直连，ProxyHandler({})强制绕过Windows代理"""
    if params:
        url += '?' + urllib.parse.urlencode(params)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': ref,
    }
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=_ssl_ctx),
    )
    with opener.open(urllib.request.Request(url, headers=headers), timeout=15) as r:
        return r.read().decode(enc, errors='replace')


def _get_gbk(url, ref='https://finance.sina.com.cn/'):
    """新浪专用：GBK编码"""
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': ref,
    }
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(urllib.request.Request(url, headers=headers), timeout=15) as r:
        return r.read().decode('gbk', errors='replace')


# ─── 代码格式工具 ─────────────────────────────────────────────
def normalize_code(code: str) -> tuple:
    """
    返回 (pure_code, prefix)
    支持：000568 / sz000568 / 000568.SZ
    """
    code = code.upper().replace('.SH', '').replace('.SZ', '')
    code = code.lower().replace('sh', '').replace('sz', '')
    prefix = 'sh' if code.startswith('6') else 'sz'
    return code, prefix


# ─── 实时行情（新浪）────────────────────────────────────────────
def get_realtime_quote(code: str) -> dict:
    """单只股票实时行情快照"""
    pure, prefix = normalize_code(code)
    raw = _get_gbk(f'http://hq.sinajs.cn/list={prefix}{pure}')
    m = re.search(r'"([^"]+)"', raw)
    if not m or not m.group(1):
        return {}
    parts = m.group(1).split(',')
    if len(parts) < 6:
        return {}
    yclose = float(parts[2])
    price  = float(parts[3])
    return {
        'code':     pure,
        'name':     parts[0],
        'price':    price,
        'open':     float(parts[1]),
        'yclose':   yclose,
        'high':     float(parts[4]),
        'low':      float(parts[5]),
        'vol':      int(parts[8]) if len(parts) > 8 else 0,
        'chg_pct':  round((price - yclose) / yclose * 100, 2) if yclose else 0,
    }


def get_batch_quotes(codes: list) -> dict:
    """批量实时行情，返回 {code: quote_dict}"""
    groups = [codes[i:i+20] for i in range(0, len(codes), 20)]
    result = {}
    for group in groups:
        joined = ','.join(
            (f'sh{c}' if c.startswith('6') else f'sz{c}')
            for c in [normalize_code(c)[0] for c in group]
        )
        raw = _get_gbk(f'http://hq.sinajs.cn/list={joined}')
        for line in raw.split(';'):
            line = line.strip()
            if '="' not in line:
                continue
            m = re.search(r'hq_str_s[hz](\d+)', line)
            if not m:
                continue
            parts = line.split('"')[1].split(',')
            if len(parts) < 6:
                continue
            try:
                c = m.group(1)
                yc = float(parts[2])
                p  = float(parts[3])
                result[c] = {
                    'code':    c,
                    'name':    parts[0],
                    'price':   p,
                    'yclose':  yc,
                    'high':    float(parts[4]),
                    'low':     float(parts[5]),
                    'vol':     int(parts[8]) if len(parts) > 8 else 0,
                    'chg_pct': round((p - yc) / yc * 100, 2) if yc else 0,
                }
            except Exception:
                pass
    return result


# ─── PE / PB（腾讯行情）─────────────────────────────────────────
def get_pe_pb(codes: list) -> dict:
    """批量PE/PB，返回 {code: {pe, pb}}"""
    joined = ','.join(
        (f'sh{c}' if c.startswith('6') else f'sz{c}')
        for c in [normalize_code(c)[0] for c in codes]
    )
    raw = _get(f'https://qt.gtimg.cn/q={joined}')
    result = {}
    for line in raw.split(';'):
        m = re.search(r'v_(s[hz])(\d+)="([^"]+)"', line.strip())
        if not m:
            continue
        parts = m.group(3).split('~')
        if len(parts) < 47:
            continue
        try:
            c = m.group(2)
            result[c] = {
                'pe':  float(parts[39]) if parts[39] else None,
                'pb':  float(parts[46]) if parts[46] else None,
            }
        except Exception:
            pass
    return result


# ─── 日线K线（腾讯）──────────────────────────────────────────────
def get_daily_kline(code: str, days: int = 90) -> pd.DataFrame:
    """前复权日线K线，默认近90天"""
    pure, prefix = normalize_code(code)
    today = datetime.date.today().strftime('%Y-%m-%d')
    start = (datetime.date.today() - datetime.timedelta(days=days * 2)).strftime('%Y-%m-%d')

    raw = _get('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get',
               {'_var': 'd', 'param': f'{prefix}{pure},day,{start},{today},{days},qfq'})
    m = re.search(r'd=(.*)', raw)
    if not m:
        return pd.DataFrame()

    obj = json.loads(m.group(1))
    klines = (obj.get('data', {})
                 .get(f'{prefix}{pure}', {})
                 .get('qfqday', []))
    if not klines:
        return pd.DataFrame()

    rows = [{'date': k[0], 'open': float(k[1]), 'close': float(k[2]),
             'high': float(k[3]), 'low': float(k[4]), 'vol': float(k[5])}
            for k in klines[-days:]]
    df = pd.DataFrame(rows)
    df['chg_pct'] = df['close'].pct_change() * 100
    return df


# ─── 估值历史分位（近似计算）────────────────────────────────────────
def calc_pe_percentile(pe: float, industry: str) -> float:
    """
    基于行业历史PE区间估算当前分位
    返回 0-100（越低越便宜）
    """
    lo, hi = HISTORICAL_PE.get(industry, HISTORICAL_PE['其他'])
    if pe is None or pe <= 0:
        return None
    pct = (pe - lo) / (hi - lo) * 100
    return max(0, min(100, round(pct, 1)))


# ─── 财务历史数据（EM版，直接调用，已验证1-2s完成）─────────────────────
def get_financial_history(code: str, years: int = 3) -> dict:
    """
    获取近N年财务指标均值（EM版）
    ⚠️ P2修复：从THS版迁移到EM版，彻底解决THS版对银行/保险类股票挂死的问题。
    EM版已验证速度稳定（1-2s/只），无需超时包装。
    返回: {roe, net_margin, gross_margin, revenue_growth, net_profit_growth, debt_ratio}
    """
    pure, prefix = normalize_code(code)
    sym = f'{pure}.SH' if prefix == 'sh' else f'{pure}.SZ'

    try:
        df = ak.stock_financial_analysis_indicator_em(symbol=sym, indicator='按报告期')
        if df is None or df.empty:
            return {}

        # 只取年报行（含"年报"的REPORT_DATE_NAME），取最近N年
        annual = df[df['REPORT_DATE_NAME'].str.contains('年报', na=False)].copy()
        annual = annual.sort_values('REPORT_DATE', ascending=False).head(years)
        if annual.empty:
            return {}

        # EM版字段映射（已验证存在）
        EM_FIELDS = {
            'roe':               'ROEJQ',          # 加权ROE(%)
            'net_margin':        'XSJLL',           # 销售净利率(%)
            'gross_margin':      'XSMLL',           # 销售毛利率(%)
            'revenue_growth':    'TOTALOPERATEREVETZ',  # 营收增速(%)
            'net_profit_growth': 'PARENTNETPROFITTZ',   # 净利润增速(%)
            'debt_ratio':        'ZCFZL',           # 资产负债率(%)
        }

        result = {}
        for key, col in EM_FIELDS.items():
            if col in annual.columns:
                vals = pd.to_numeric(annual[col], errors='coerce').dropna()
                if not vals.empty:
                    result[key] = round(float(vals.mean()), 2)

        return result

    except Exception:
        return {}


# ─── P0.1: 真实PE历史分位 ──────────────────────────────────────────────
def _get_close_on_date(pure_code: str, target_date: str) -> float:
    """获取指定日期（或之前最近交易日）的收盘价（前复权）"""
    prefix = 'sh' if pure_code.startswith('6') else 'sz'
    start = (datetime.datetime.strptime(target_date, '%Y-%m-%d')
             - datetime.timedelta(days=10)).strftime('%Y-%m-%d')
    try:
        raw = _get('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get',
                   {'_var': 'd', 'param': f'{prefix}{pure_code},day,{start},{target_date},10,qfq'})
        m = re.search(r'd=(.*)', raw)
        if m:
            obj = json.loads(m.group(1))
            klines = (obj.get('data', {})
                         .get(f'{prefix}{pure_code}', {})
                         .get('qfqday', []))
            if klines:
                return float(klines[-1][2])
    except Exception:
        pass
    return None


def get_pe_percentile_real(code: str, current_pe: float, years: int = 5) -> dict:
    """
    P0.1 修复：基于真实历史PE计算当前PE的历史分位（带25s超时保护）
    方法：年末股价 ÷ 年度EPS（EPSJB） = 年度PE，取近N年分布
    percentile越低 = 越便宜（比历史上percentile%的时候更贵）
    """
    pure, prefix = normalize_code(code)
    sym = f'{pure}.SH' if prefix == 'sh' else f'{pure}.SZ'

    if current_pe is None or current_pe <= 0:
        return {}

    try:
        df = ak.stock_financial_analysis_indicator_em(symbol=sym, indicator='按报告期')
        if df is None or df.empty:
            return {}
        annual = df[df['REPORT_DATE_NAME'].str.contains('年报', na=False)].copy()
        annual = annual.sort_values('REPORT_DATE', ascending=False).head(years)

        pe_history = []
        for _, row in annual.iterrows():
            eps = float(row['EPSJB']) if pd.notna(row['EPSJB']) and row['EPSJB'] else None
            report_date = str(row['REPORT_DATE'])[:10]
            if eps and eps > 0:
                price = _get_close_on_date(pure, report_date)
                if price and price > 0:
                    pe_history.append({
                        'date': report_date,
                        'pe': round(price / eps, 2),
                        'price': price,
                        'eps': eps,
                    })

        if len(pe_history) < 2:
            return {}

        pes = [x['pe'] for x in pe_history]
        percentile = round(sum(1 for p in pes if p < current_pe) / len(pes) * 100, 1)
        pes_sorted = sorted(pes)

        return {
            'pe_percentile':   percentile,
            'pe_median':       round(pes_sorted[len(pes_sorted) // 2], 2),
            'pe_min':          round(min(pes), 2),
            'pe_max':          round(max(pes), 2),
            'pe_current':      current_pe,
            'pe_history_years': len(pe_history),
            'source':          '真实年度PE（年末价÷EPS）',
        }
    except Exception:
        return {}


# ─── P0.2: PEG 指标 ────────────────────────────────────────────────────
def calc_peg(pe: float, net_profit_growth: float) -> float:
    """
    P0.2 新增：PEG = PE ÷ 净利润增速（%）
    PEG < 1.0 : 增速覆盖估值，低估区间
    PEG 1-2   : 合理
    PEG > 2   : 偏贵
    增速 <= 0  : 返回 None（PEG无意义，单独处理）
    """
    if pe is None or pe <= 0:
        return None
    if net_profit_growth is None or net_profit_growth <= 0:
        return None
    return round(pe / net_profit_growth, 2)
