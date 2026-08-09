"""
screener.py — 三层选股模型
层1：量化筛选（真实PE历史分位 + PEG + PB + ROE）  ← P0修复
层2：产业链位置与护城河（AI分析）
层3：财务快照（含真实PE历史区间 + PEG）
"""

import os
import sys
import datetime
from pathlib import Path
from dotenv import load_dotenv
from data_fetcher import (
    get_batch_quotes, get_pe_pb, get_daily_kline,
    get_financial_history, normalize_code,
    get_pe_percentile_real, calc_peg,      # P0新增
)

load_dotenv(Path(__file__).parent.parent / 'config' / '.env')

# ─── AI客户端 ────────────────────────────────────────────────────
def _ai(prompt: str, system: str = '', model: str = 'claude-sonnet-4-6') -> str:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_API_BASE'),
    )
    msgs = []
    if system:
        msgs.append({'role': 'system', 'content': system})
    msgs.append({'role': 'user', 'content': prompt})
    return client.chat.completions.create(
        model=model, messages=msgs, temperature=0.2
    ).choices[0].message.content


# ─── 层1：量化筛选 ───────────────────────────────────────────────────
SCREENING_RULES = {
    'pe_percentile_max': 60,   # 真实PE历史分位上限
    'peg_max':           2.5,  # PEG上限
    'pb_max':            10,   # PB绝对上限
    # ROE门槛已行业化，见 INDUSTRY_ROE_THRESHOLD
}

# ── ROE行业化（P2回测发现：统一12%误杀重资产行业）────────────────
INDUSTRY_ASSET_TYPE = {
    '白酒':     'light',    # 品牌消费，轻资产，护城河来自品牌
    '消费':     'light',
    '医药':     'medium',   # 研发密集，中等资产
    '工业自动化': 'medium',
    '机器人':   'medium',
    '新能源':   'medium',
    '军工':     'medium',
    '半导体':   'heavy',    # 晶圆代工：固定资产巨大，ROE天然偏低
    '银行':     'heavy',    # 杠杆经营，ROE口径不同
    '保险':     'heavy',
    '公用事业': 'heavy',
    '其他':     'medium',
}

INDUSTRY_ROE_THRESHOLD = {
    'light':  20,   # 轻资产：ROE>20%（护城河体现在高ROE）
    'medium': 12,   # 中等资产：ROE>12%
    'heavy':  8,    # 重资产：ROE>8%（关注趋势，非绝对值）
}

INDUSTRY_MAP = {
    '600519': '白酒', '000858': '白酒', '000568': '白酒', '002304': '白酒',
    '603369': '白酒', '000596': '白酒',
    '600036': '银行', '601398': '银行', '601939': '银行', '600000': '银行',
    '601288': '银行', '002142': '银行',
    '601318': '保险', '601601': '保险', '601628': '保险',
    '688981': '半导体', '688041': '半导体', '002371': '半导体', '688012': '半导体',
    '300124': '工业自动化', '002747': '机器人',
    '300274': '新能源', '002594': '新能源', '300750': '新能源', '601012': '新能源',
    '512660': '军工', '600893': '军工', '000768': '军工',
    '600276': '医药', '000963': '医药',
    '600900': '公用事业', '601985': '公用事业', '600905': '公用事业',
}

def get_industry(code: str) -> str:
    pure, _ = normalize_code(code)
    return INDUSTRY_MAP.get(pure, '其他')

def get_roe_threshold(industry: str) -> int:
    """根据行业资产密集度返回ROE门槛"""
    asset_type = INDUSTRY_ASSET_TYPE.get(industry, 'medium')
    return INDUSTRY_ROE_THRESHOLD[asset_type]


def layer1_quantitative(code: str, quote: dict, valuation: dict,
                        fin: dict, pe_hist: dict) -> dict:
    """
    层1：量化筛选（P0修复版）
    - ROE：真实历史年均值
    - PE历史分位：真实年度PE分布（非hardcoded区间）
    - PEG：PE ÷ 净利润增速（增速负时标注风险）
    - PB：绝对值上限
    """
    industry = get_industry(code)
    pe      = valuation.get('pe')
    pb      = valuation.get('pb')
    roe     = fin.get('roe')
    growth  = fin.get('net_profit_growth')

    reasons = []
    passed  = True

    # ── ROE（行业化门槛，P2修复）──────────────────────────────────
    min_roe = get_roe_threshold(industry)
    asset_type = INDUSTRY_ASSET_TYPE.get(industry, 'medium')
    if roe is not None:
        if roe < min_roe:
            reasons.append(f'ROE={roe:.1f}%（<{min_roe}%，{industry}/{asset_type}）')
            passed = False
        else:
            reasons.append(f'ROE={roe:.1f}%✓（{industry}门槛{min_roe}%）')
    else:
        reasons.append('ROE:待补充')

    # ── 真实PE历史分位（P0修复）─────────────────────────────────
    pe_pct = pe_hist.get('pe_percentile')
    if pe_pct is None:
        reasons.append('PE分位:数据不足')
    elif pe_pct > SCREENING_RULES['pe_percentile_max']:
        reasons.append(f'PE真实分位{pe_pct:.0f}%（>60%，偏贵）')
        passed = False
    else:
        pe_med = pe_hist.get('pe_median', '?')
        reasons.append(f'PE真实分位{pe_pct:.0f}%✓（历史中位{pe_med}x）')

    # ── PEG（P0新增）────────────────────────────────────────────
    peg = calc_peg(pe, growth)
    if peg is not None:
        if peg > SCREENING_RULES['peg_max']:
            reasons.append(f'PEG={peg:.2f}（>{SCREENING_RULES["peg_max"]}，估值贵于增速）')
            passed = False
        else:
            reasons.append(f'PEG={peg:.2f}✓')
    elif growth is not None and growth <= 0:
        reasons.append(f'净利润增速{growth:.1f}%（负增长，PEG无意义，需谨慎）')
        # 负增长本身不直接否决，但作为重要警示
    else:
        reasons.append('PEG:增速数据待补充')

    # ── PB ─────────────────────────────────────────────────────
    if pb is None:
        reasons.append('PB:缺失')
    elif pb > SCREENING_RULES['pb_max']:
        reasons.append(f'PB={pb:.1f}x（>{SCREENING_RULES["pb_max"]}）')
        passed = False
    else:
        reasons.append(f'PB={pb:.2f}x✓')

    return {
        'pass':         passed,
        'pe':           pe,
        'pb':           pb,
        'roe':          roe,
        'peg':          peg,
        'net_growth':   growth,
        'pe_percentile': pe_pct,
        'pe_hist':      pe_hist,
        'industry':     industry,
        'reason':       ' | '.join(reasons),
    }


# ─── 层2：AI产业链与护城河分析 ────────────────────────────────────────
def layer2_supply_chain(code: str, name: str, industry: str) -> dict:
    """
    层2：AI生成产业链位置 + 护城河评分
    """
    prompt = f"""对A股股票 {name}（{code}，{industry}行业）进行产业链分析。

输出格式（严格JSON，无其他文字）：
{{
  "supply_chain_position": "<上游/中游/下游/品牌消费，一句话>",
  "upstream_dependencies": ["<上游依赖1>", "<上游依赖2>"],
  "downstream_customers": ["<客户类型1>", "<客户类型2>"],
  "competitive_moat": "<护城河描述，50字>",
  "moat_score": <1-5整数，5最强>,
  "structural_risk": "<最大结构性风险，30字>",
  "policy_alignment": "<与中国政策方向的关系，支持/中性/逆风>",
  "long_term_outlook": "<3-5年前景，乐观/中性/谨慎>"
}}"""

    try:
        raw = _ai(prompt, system='你是A股产业链分析专家，输出严格JSON。')
        import json, re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        pass
    return {
        'supply_chain_position': '分析失败',
        'moat_score': 0,
        'structural_risk': '未知',
        'policy_alignment': '未知',
        'long_term_outlook': '未知',
    }


# ─── 层3：财务快照（P0修复版）────────────────────────────────────────
def layer3_financial(code: str, pe: float, pb: float,
                     pe_hist: dict, fin: dict = None) -> dict:
    """
    层3：财务快照（P0修复版）
    pe_hist: get_pe_percentile_real() 返回的真实PE历史
    fin:     get_financial_history() 返回的财务数据
    """
    if fin is None:
        fin = get_financial_history(code)

    pe_pct = pe_hist.get('pe_percentile')
    peg    = calc_peg(pe, fin.get('net_profit_growth'))

    # PE历史分位定性评价
    if pe_pct is None:
        val_label = '分位待计算'
    elif pe_pct <= 20:
        val_label = '历史极低位 ★★★★★'
    elif pe_pct <= 35:
        val_label = '历史低位 ★★★★'
    elif pe_pct <= 50:
        val_label = '历史中低位 ★★★'
    elif pe_pct <= 65:
        val_label = '历史中位 ★★'
    else:
        val_label = '历史高位 ★'

    # PEG评价
    if peg is None:
        peg_label = '负增长（PEG无意义）' if (fin.get('net_profit_growth') or 0) < 0 else '增速待补充'
    elif peg < 1.0:
        peg_label = f'{peg:.2f}（增速覆盖估值，低估）'
    elif peg < 2.0:
        peg_label = f'{peg:.2f}（合理）'
    else:
        peg_label = f'{peg:.2f}（偏贵）'

    return {
        'pe_ttm':           pe,
        'pb':               pb,
        'pe_percentile':    pe_pct,
        'pe_median':        pe_hist.get('pe_median'),
        'pe_min':           pe_hist.get('pe_min'),
        'pe_max':           pe_hist.get('pe_max'),
        'pe_history_years': pe_hist.get('pe_history_years'),
        'pe_source':        pe_hist.get('source'),
        'valuation_label':  val_label,
        'peg':              peg,
        'peg_label':        peg_label,
        'roe_3y_avg':       fin.get('roe'),
        'net_margin':       fin.get('net_margin'),
        'gross_margin':     fin.get('gross_margin'),
        'revenue_growth':   fin.get('revenue_growth'),
        'net_profit_growth':fin.get('net_profit_growth'),
        'debt_ratio':       fin.get('debt_ratio'),
    }


# ─── 综合打分（P0修复版）──────────────────────────────────────────────
def composite_score(l1: dict, l2: dict, l3: dict) -> float:
    """
    综合评分（0-100）P0修复版
    权重：真实PE分位35% + PEG15% + 护城河30% + PB估值20%
    """
    # 真实PE分位得分（分位越低=越便宜=得分越高）
    pe_pct = l3.get('pe_percentile') if l3.get('pe_percentile') is not None else 50
    pe_score = max(0, 100 - pe_pct) * 0.35

    # PEG得分（PEG越低=增速越覆盖估值=得分越高）
    peg = l3.get('peg')
    if peg is not None and peg > 0:
        peg_score = max(0, min(100, (3.0 - peg) / 3.0 * 100)) * 0.15
    else:
        peg_score = 40 * 0.15  # 无PEG数据给中性分

    # 护城河分
    moat = (l2.get('moat_score', 0) / 5) * 100 * 0.30

    # PB估值分
    pb = l3.get('pb') or 5
    pb_score = max(0, min(100, (10 - pb) / 10 * 100)) * 0.20

    return round(pe_score + peg_score + moat + pb_score, 1)


# ─── 主入口：筛选一组股票 ─────────────────────────────────────────────
def screen_stocks(stock_dict: dict, verbose: bool = True, quick: bool = False) -> list:
    """
    stock_dict: {code: name, ...}
    quick=True  → 跳过Layer2 AI分析，只做量化筛选（快速宽扫描，约30s/12只）
    quick=False → 完整三层分析，含AI产业链评估（约8-10min/12只）
    返回按综合评分排序的结果列表
    """
    codes = list(stock_dict.keys())
    pure_codes = [normalize_code(c)[0] for c in codes]

    mode_label = '快速量化扫描（跳过AI分析）' if quick else '完整三层分析（含AI）'
    if verbose:
        print(f'[数据采集] 正在获取 {len(codes)} 只股票数据...（{mode_label}）')

    quotes     = get_batch_quotes(pure_codes)
    valuations = get_pe_pb(pure_codes)

    # Layer2占位（quick模式下跳过AI调用）
    _empty_l2 = {
        'supply_chain_position': '（快速模式，跳过）',
        'moat_score': 0,
        'structural_risk': '待分析',
        'policy_alignment': '待分析',
        'long_term_outlook': '待分析',
    }

    results = []
    for code, name in stock_dict.items():
        pure, _ = normalize_code(code)
        quote    = quotes.get(pure, {})
        val      = valuations.get(pure, {})
        industry = get_industry(pure)
        current_pe = val.get('pe')

        if verbose:
            print(f'  分析 {name}({pure})...')

        # 财务历史 + 真实PE历史分位（P0修复）
        fin     = get_financial_history(pure)
        pe_hist = get_pe_percentile_real(pure, current_pe)

        l1 = layer1_quantitative(pure, quote, val, fin, pe_hist)
        l2 = _empty_l2 if quick else layer2_supply_chain(pure, name, industry)
        l3 = layer3_financial(pure, current_pe, val.get('pb'), pe_hist, fin)
        score = composite_score(l1, l2, l3)

        results.append({
            'code':     pure,
            'name':     name,
            'price':    quote.get('price', 0),
            'chg_pct':  quote.get('chg_pct', 0),
            'industry': industry,
            'score':    score,
            'l1_pass':  l1['pass'],
            'l1':       l1,
            'l2':       l2,
            'l3':       l3,
            'quick':    quick,
        })

    return sorted(results, key=lambda x: x['score'], reverse=True)
