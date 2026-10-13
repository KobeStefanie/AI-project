"""
backtest.py — 三层选股标准历史回测
验证：PE历史低分位 + ROE>12% 在过去5年是否有效

方法：
  每年1月初，用前一年年报数据做选股判断
  持有1年，到年底比较实际收益
  与沪深300基准对比

输出：
  - 每只股票每年的"是否被选中"和实际年收益
  - 被选中年份 vs 未被选中年份的平均收益对比
  - vs 沪深300基准的超额收益
"""

import sys
import json
import ssl
import urllib.request
import urllib.parse
import datetime
import re
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── AKShare代理补丁 ────────────────────────────────────────────────────
import requests
from requests.adapters import HTTPAdapter
_orig = requests.Session.merge_environment_settings
def _no_proxy(self, u, p, s, v, c):
    r = _orig(self, u, p, s, v, c); r['proxies'] = {}; return r
requests.Session.merge_environment_settings = _no_proxy
import akshare as ak

# ── HTTP工具 ─────────────────────────────────────────────────────────
_ssl = ssl._create_unverified_context()

def get_price_on(code: str, date_str: str) -> float:
    """获取指定日期最近交易日收盘价（前复权）"""
    pure = code.replace('.SH','').replace('.SZ','')
    prefix = 'sh' if pure.startswith('6') else 'sz'
    start = (datetime.datetime.strptime(date_str, '%Y-%m-%d') -
             datetime.timedelta(days=10)).strftime('%Y-%m-%d')
    try:
        url = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
        params = {'_var': 'd', 'param': f'{prefix}{pure},day,{start},{date_str},10,qfq'}
        url += '?' + urllib.parse.urlencode(params)
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=_ssl))
        with opener.open(urllib.request.Request(
                url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://gu.qq.com/'}),
                timeout=15) as r:
            raw = r.read().decode('utf-8', errors='replace')
        m = re.search(r'd=(.*)', raw)
        if m:
            obj = (json.loads(m.group(1))
                   .get('data', {})
                   .get(f'{prefix}{pure}', {}))
            klines = obj.get('qfqday') or obj.get('day') or []
            if klines:
                return float(klines[-1][2])
    except Exception:
        pass
    return None


def _kline_year(prefix_code: str, year: int) -> list:
    """获取某年全部K线（用于基准计算）"""
    params = {'_var': 'd',
              'param': f'{prefix_code},day,{year}-01-01,{year}-12-31,260,'}
    url = ('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?'
           + urllib.parse.urlencode(params))
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=_ssl))
    try:
        with opener.open(urllib.request.Request(
                url, headers={'User-Agent':'Mozilla/5.0','Referer':'https://gu.qq.com/'}),
                timeout=15) as r:
            raw = r.read().decode('utf-8', errors='replace')
        m = re.search(r'd=(.*)', raw)
        if m:
            obj = json.loads(m.group(1)).get('data', {}).get(prefix_code, {})
            return obj.get('qfqday') or obj.get('day') or []
    except Exception:
        pass
    return []


def get_annual_data(code: str) -> pd.DataFrame:
    """获取股票全历史年报数据（EPS + 加权ROE）"""
    pure = code.replace('.SH','').replace('.SZ','')
    sym = pure + '.SH' if pure.startswith('6') else pure + '.SZ'
    try:
        df = ak.stock_financial_analysis_indicator_em(symbol=sym, indicator='按报告期')
        annual = df[df['REPORT_DATE_NAME'].str.contains('年报', na=False)].copy()
        annual = annual.sort_values('REPORT_DATE').reset_index(drop=True)
        return annual
    except Exception:
        return pd.DataFrame()


def get_roe_from_akshare(code: str) -> dict:
    """从AKShare获取各年ROE（用于历史分位，已有AKShare财务补丁）"""
    pure = code.replace('.SH','').replace('.SZ','')
    start_year = str(datetime.date.today().year - 7)
    try:
        df = ak.stock_financial_analysis_indicator(symbol=pure, start_year=start_year)
        annual = df.iloc[3::4].reset_index(drop=True)  # 取年报
        roe_col = '加权净资产收益率(%)'
        if roe_col not in annual.columns:
            return {}
        return {str(2020 + i): float(v)
                for i, v in enumerate(
                    pd.to_numeric(annual[roe_col], errors='coerce').dropna().tolist()
                ) if not pd.isna(v)}
    except Exception:
        return {}


# ── 核心回测函数 ──────────────────────────────────────────────────────
def backtest_stock(code: str, name: str,
                   test_years: list = None) -> list:
    """
    对单只股票做历史回测
    test_years: 回测年份列表，如 [2021, 2022, 2023, 2024, 2025]
                含义：在 year-01-03 买入，year-12-31 卖出
    """
    if test_years is None:
        test_years = [2021, 2022, 2023, 2024, 2025]

    print(f'  回测 {name}({code})...')

    annual_df = get_annual_data(code)
    if annual_df.empty:
        print(f'    无年报数据，跳过')
        return []

    results = []
    for year in test_years:
        buy_date  = f'{year}-01-03'    # 年初买入
        sell_date = f'{year}-12-31'    # 年末卖出
        prior_year_str = str(year - 1)

        # ── 获取前一年年报EPS ────────────────────────────────────────
        prior_rows = annual_df[
            annual_df['REPORT_DATE'].astype(str).str.startswith(prior_year_str)]
        if prior_rows.empty:
            continue
        eps_row = prior_rows.iloc[-1]
        eps = float(eps_row['EPSJB']) if pd.notna(eps_row['EPSJB']) else None
        if not eps or eps <= 0:
            continue

        # ── 买入价格 ─────────────────────────────────────────────────
        price_buy  = get_price_on(code, buy_date)
        price_sell = get_price_on(code, sell_date)
        if not price_buy or not price_sell:
            continue

        # ── 买入时PE ─────────────────────────────────────────────────
        pe_buy = price_buy / eps

        # ── PE历史分位（用买入日前3年年报数据，无lookahead）───────────
        pe_hist = []
        for h_year in range(year - 3, year):
            h_rows = annual_df[annual_df['REPORT_DATE']
                                .astype(str).str.startswith(str(h_year))]
            if h_rows.empty:
                continue
            h_eps = float(h_rows.iloc[-1]['EPSJB']) if pd.notna(
                h_rows.iloc[-1]['EPSJB']) else None
            if not h_eps or h_eps <= 0:
                continue
            h_price = get_price_on(code, f'{h_year}-12-31')
            if h_price:
                pe_hist.append(h_price / h_eps)

        if len(pe_hist) >= 2:
            pe_pct = round(sum(1 for p in pe_hist if p < pe_buy)
                           / len(pe_hist) * 100, 0)
        else:
            pe_pct = 50   # 无历史数据，给中性值

        # ── ROE（前一年年报）— 修复：使用 ROEJQ 字段 ────────────
        roe = None
        for col in ['ROEJQ', 'WEIGHTAVGROE', 'ROE']:
            if col in eps_row.index and pd.notna(eps_row.get(col)):
                try:
                    roe = float(eps_row[col])
                    break
                except Exception:
                    pass

        # ── 净利润增速（计算PEG）────────────────────────────────────
        net_growth = None
        if 'NETPROFITYOY' in eps_row.index:
            try:
                ng = float(eps_row.get('NETPROFITYOY', float('nan')))
                if not pd.isna(ng):
                    net_growth = round(ng * 100, 1)
            except Exception:
                pass

        # ── 选股决策 ─────────────────────────────────────────────────
        selected = (pe_pct < 40) and (roe is None or roe > 12)

        # ── 年度收益 ─────────────────────────────────────────────────
        annual_ret = round((price_sell - price_buy) / price_buy * 100, 2)

        results.append({
            'year':       year,
            'code':       code,
            'name':       name,
            'pe_buy':     round(pe_buy, 2),
            'pe_pct':     pe_pct,
            'roe':        round(roe, 1) if roe else None,
            'net_growth': net_growth,
            'selected':   selected,
            'price_buy':  price_buy,
            'price_sell': price_sell,
            'annual_ret': annual_ret,
        })

    return results


def get_benchmark_returns(test_years: list = None) -> dict:
    """获取沪深300各年收益（修复版：使用全年K线，sh前缀）"""
    if test_years is None:
        test_years = [2021, 2022, 2023, 2024, 2025]
    rets = {}
    for year in test_years:
        kls = _kline_year('sh000300', year)
        if len(kls) >= 2:
            p1 = float(kls[0][2])
            p2 = float(kls[-1][2])
            rets[year] = round((p2 - p1) / p1 * 100, 2)
    return rets


# ── 主回测运行 ────────────────────────────────────────────────────────
UNIVERSE = {
    '000568': '泸州老窖',
    '000858': '五粮液',
    '600519': '贵州茅台',
    '600036': '招商银行',
    '300124': '汇川技术',
    '300274': '阳光电源',
    '688981': '中芯国际',
    '000568': '泸州老窖',   # dup ok, dict overwrite
}

# 去重
UNIVERSE = {
    '000568': '泸州老窖',
    '000858': '五粮液',
    '600519': '贵州茅台',
    '600036': '招商银行',
    '300124': '汇川技术',
    '300274': '阳光电源',
    '688981': '中芯国际',
}

TEST_YEARS = [2021, 2022, 2023, 2024, 2025]

if __name__ == '__main__':
    print('=' * 65)
    print('A股三层选股回测 2021-2025')
    print('选股标准：PE历史分位 < 40% + ROE > 12%')
    print('=' * 65)

    print('\n[1/3] 获取沪深300基准年收益...')
    benchmark = get_benchmark_returns(TEST_YEARS)
    for y, r in benchmark.items():
        print(f'  沪深300 {y}: {r:+.1f}%')

    print('\n[2/3] 回测各标的...')
    all_results = []
    for code, name in UNIVERSE.items():
        rows = backtest_stock(code, name, TEST_YEARS)
        all_results.extend(rows)

    if not all_results:
        print('无回测数据')
        exit(1)

    df = pd.DataFrame(all_results)

    print('\n[3/3] 汇总分析')
    print('=' * 65)

    # ── 按年汇总：被选中的股票 vs 未被选中 ────────────────────────
    print('\n── 每年被选中的股票组合 vs 未被选中 vs 沪深300 ──')
    print(f'{"年份":<6} {"选中数":<6} {"选中均收益":<12} {"未选中均收益":<14} {"沪深300":<10} {"超额(vs基准)":<12}')
    print('-' * 70)

    for year in TEST_YEARS:
        yr_df = df[df['year'] == year]
        sel = yr_df[yr_df['selected'] == True]['annual_ret']
        not_sel = yr_df[yr_df['selected'] == False]['annual_ret']
        bm = benchmark.get(year, 0)

        sel_avg = sel.mean() if len(sel) > 0 else float('nan')
        not_avg = not_sel.mean() if len(not_sel) > 0 else float('nan')
        alpha = sel_avg - bm if not pd.isna(sel_avg) else float('nan')

        sel_str = f'{sel_avg:+.1f}%' if not pd.isna(sel_avg) else 'N/A'
        not_str = f'{not_avg:+.1f}%' if not pd.isna(not_avg) else 'N/A'
        alp_str = f'{alpha:+.1f}%' if not pd.isna(alpha) else 'N/A'
        print(f'{year:<6} {len(sel):<6} {sel_str:<12} {not_str:<14} {bm:+.1f}%{"":<4} {alp_str}')

    # ── 全期汇总 ──────────────────────────────────────────────────
    all_sel     = df[df['selected'] == True]['annual_ret']
    all_not_sel = df[df['selected'] == False]['annual_ret']
    bm_avg = sum(benchmark.values()) / len(benchmark) if benchmark else 0

    print('\n── 全期汇总（2021-2025合并）──')
    print(f'  被选中组合  样本数={len(all_sel):3d}  平均年收益 = {all_sel.mean():+.1f}%  '
          f'正收益率 = {(all_sel > 0).mean()*100:.0f}%')
    print(f'  未选中组合  样本数={len(all_not_sel):3d}  平均年收益 = {all_not_sel.mean():+.1f}%')
    print(f'  沪深300均值                  平均年收益 = {bm_avg:+.1f}%')
    print(f'  超额收益(选中 vs 基准)        = {all_sel.mean() - bm_avg:+.1f}%')

    # ── 逐股明细 ──────────────────────────────────────────────────
    print('\n── 逐股逐年明细 ──')
    print(f'{"股票":<8} {"年份":<6} {"PE分位":<8} {"ROE":<7} '
          f'{"被选":<5} {"年收益":<8} {"vs基准":<8}')
    print('-' * 65)

    for _, row in df.sort_values(['name','year']).iterrows():
        bm_r = benchmark.get(row['year'], 0)
        alpha = row['annual_ret'] - bm_r
        flag = '✓' if row['selected'] else ' '
        roe_s = f"{row['roe']:.0f}%" if row['roe'] else 'N/A'
        print(f"{row['name']:<8} {row['year']:<6} "
              f"{row['pe_pct']:.0f}%{'':<5} {roe_s:<7} "
              f"{flag:<5} {row['annual_ret']:+.1f}%{'':<3} {alpha:+.1f}%")

    # ── 结论 ──────────────────────────────────────────────────────
    print('\n── 结论 ──')
    sel_avg   = all_sel.mean()
    nosel_avg = all_not_sel.mean()
    print(f'选中组合年均收益 {sel_avg:+.1f}% vs 未选中 {nosel_avg:+.1f}% | '
          f'差值 {sel_avg - nosel_avg:+.1f}%')
    print(f'选中组合年均收益 {sel_avg:+.1f}% vs 沪深300 {bm_avg:+.1f}% | '
          f'超额 {sel_avg - bm_avg:+.1f}%')
    if sel_avg > bm_avg + 3:
        print('验证结果：✅ 筛选标准有效，显著跑赢基准')
    elif sel_avg > bm_avg:
        print('验证结果：⚠️  筛选标准有正超额，但幅度有限')
    else:
        print('验证结果：❌ 筛选标准未能跑赢基准，需要检讨')
