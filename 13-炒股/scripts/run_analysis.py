"""
run_analysis.py — 三层选股分析主入口
用法：
  python run_analysis.py 000568 000858 600036 300124       # 完整三层分析
  python run_analysis.py --watch-list                      # 使用预设自选池
  python run_analysis.py --quick 600519 000568 000858      # 快速量化扫描（跳过AI）
  python run_analysis.py --quick --top 4                   # 宽扫描候选池，输出Top4供深度研究

两阶段工作流（推荐）：
  阶段1: python run_analysis.py --quick                    # 快速扫描30只股票，约2-3min
  阶段2: python run_analysis.py 600519 000568 002142       # 对Top候选做完整分析
"""

import sys
import os
import json
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from screener import screen_stocks, composite_score

# ─── 预设股票池（按主题分组）────────────────────────────────────────
WATCH_LIST = {
    # 低估值消费
    '000568': '泸州老窖',
    '000858': '五粮液',
    '600519': '贵州茅台',
    # 银行/金融
    '600036': '招商银行',
    '601318': '中国平安',
    # 科技/国产替代
    '688981': '中芯国际',
    '688041': '海光信息',
    '300124': '汇川技术',
    # 新能源
    '300274': '阳光电源',
    '002594': '比亚迪',
    # 军工
    '512660': '军工ETF',
    '600893': '航发动力',
}


# ─── 报告生成 ───────────────────────────────────────────────────────
def generate_report(results: list, title: str = '三层选股分析报告') -> str:
    today = datetime.date.today().strftime('%Y-%m-%d')
    lines = []

    lines.append(f'# {title}')
    lines.append(f'**日期：** {today}  **框架：** 量化筛选 × 产业链分析 × 财务快照\n')

    # ── 摘要表 ────────────────────────────────────────────────────
    passed = [r for r in results if r['l1_pass']]
    failed = [r for r in results if not r['l1_pass']]

    lines.append('---\n')
    lines.append('## 量化筛选摘要\n')
    lines.append(f'扫描：**{len(results)}只** | 通过层1：**{len(passed)}只** | 未通过：**{len(failed)}只**\n')

    lines.append('| 股票 | 行业 | 现价 | 今日 | PE-TTM | PE历史分位 | PB | 护城河 | 综合分 | 通过？|')
    lines.append('|------|------|------|------|--------|-----------|-----|--------|--------|------|')
    for r in results:
        pe_pct = r['l3'].get('pe_percentile')
        pe_pct_str = f"{pe_pct:.0f}%" if pe_pct is not None else 'N/A'
        moat = r['l2'].get('moat_score', '-')
        flag = '✅' if r['l1_pass'] else '❌'
        lines.append(
            f"| **{r['name']}** {r['code']} "
            f"| {r['industry']} "
            f"| {r['price']:.2f} "
            f"| {r['chg_pct']:+.2f}% "
            f"| {r['l3'].get('pe_ttm') or 'N/A'} "
            f"| {pe_pct_str} "
            f"| {r['l3'].get('pb') or 'N/A'} "
            f"| {'★'*moat if isinstance(moat,int) else '-'} "
            f"| **{r['score']}** "
            f"| {flag} |"
        )

    # ── 详细分析（按综合分排序） ──────────────────────────────────
    lines.append('\n---\n')
    lines.append('## 详细分析（按综合评分排序）\n')

    for i, r in enumerate(results, 1):
        pass_label = '✅ 通过三层筛选' if r['l1_pass'] else '❌ 未通过层1量化'
        lines.append(f"### {i}. {r['name']}（{r['code']}）— 综合评分 {r['score']} {pass_label}\n")

        # 层1：量化
        l1 = r['l1']
        lines.append('#### 层1：量化筛选')
        lines.append(f"- 行业：{r['industry']}")
        lines.append(f"- PE-TTM：{l1.get('pe') or 'N/A'}  |  历史分位：{l1.get('pe_percentile') or 'N/A'}%")
        lines.append(f"- PB：{l1.get('pb') or 'N/A'}")
        lines.append(f"- 结论：{l1.get('reason')}\n")

        # 层2：产业链
        l2 = r['l2']
        lines.append('#### 层2：产业链 & 护城河')
        lines.append(f"- 产业链位置：{l2.get('supply_chain_position','N/A')}")

        upstream = l2.get('upstream_dependencies', [])
        if upstream:
            lines.append(f"- 上游依赖：{' / '.join(upstream)}")

        downstream = l2.get('downstream_customers', [])
        if downstream:
            lines.append(f"- 下游客户：{' / '.join(downstream)}")

        lines.append(f"- 护城河：{l2.get('competitive_moat','N/A')} （{'★'*l2.get('moat_score',0)}）")
        lines.append(f"- 结构性风险：{l2.get('structural_risk','N/A')}")
        lines.append(f"- 政策方向：{l2.get('policy_alignment','N/A')}  |  长期展望：{l2.get('long_term_outlook','N/A')}\n")

        # 层3：财务快照
        l3 = r['l3']
        lines.append('#### 层3：财务快照')
        lines.append(f"- PE历史估值位置：{l3.get('valuation_label','N/A')}")
        for key, label in [
            ('roe_3y_avg',    'ROE均值（3年）'),
            ('revenue_growth','营收增速(YoY)'),
            ('gross_margin',  '毛利率'),
            ('debt_ratio',    '资产负债率'),
        ]:
            val = l3.get(key)
            lines.append(f"- {label}：{'⚠️ 待补充' if val is None else f'{val:.1f}%'}")
        lines.append(f"- 数据完整度：{l3.get('data_completeness','')}\n")

    # ── 数据缺口说明 ─────────────────────────────────────────────
    lines.append('---\n')
    lines.append('## 待修复：财务历史数据管道（P0）\n')
    lines.append('当前所有已测试的财务历史数据API均失败：\n')
    lines.append('| API源 | 失败原因 | 所需数据 |')
    lines.append('|-------|---------|---------|')
    lines.append('| Tushare fina_indicator | 无权限（需200积分） | ROE/增速/毛利率 |')
    lines.append('| EastMoney F10 Summary  | 报表名已变更       | ROE/增速/毛利率 |')
    lines.append('| Tencent profit/income  | Controller失效    | 净利润/营收历史 |')
    lines.append('\n**解决方案（待执行）：**')
    lines.append('- 选项A：升级Tushare积分（微信分享积分 → 达200分）')
    lines.append('- 选项B：扫描EastMoney/AKShare源代码找到正确报表名')
    lines.append('- 选项C：安装httpx + 修改AKShare请求层绕过Windows代理\n')

    lines.append('---')
    lines.append(f'*报告生成时间：{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*')

    return '\n'.join(lines)


# ─── 主入口 ──────────────────────────────────────────────────────────
def main():
    args = sys.argv[1:]

    # ── 解析参数 ─────────────────────────────────────────────────────
    quick   = '--quick' in args
    top_n   = None
    if '--top' in args:
        idx = args.index('--top')
        try:
            top_n = int(args[idx + 1])
            args = [a for i, a in enumerate(args) if i not in (idx, idx+1)]
        except (IndexError, ValueError):
            top_n = 5
    args = [a for a in args if a not in ('--quick', '--watch-list')]

    # ── 构建股票池 ────────────────────────────────────────────────────
    if not args and ('--watch-list' in sys.argv[1:] or not sys.argv[1:]):
        stocks = WATCH_LIST
        print(f'使用预设自选池，共 {len(stocks)} 只股票')
    elif args:
        from data_fetcher import normalize_code, get_batch_quotes
        pure_codes = [normalize_code(a)[0] for a in args]
        quotes = get_batch_quotes(pure_codes)
        stocks = {c: quotes.get(c, {}).get('name', c) for c in pure_codes}
        print(f'分析指定股票：{list(stocks.values())}')
    else:
        stocks = WATCH_LIST
        print(f'使用预设自选池，共 {len(stocks)} 只股票')

    mode_str = '阶段1：快速量化扫描' if quick else '完整三层分析'
    print(f'\n开始{mode_str}...\n')
    results = screen_stocks(stocks, verbose=True, quick=quick)

    # ── quick模式：输出Top-N供第二阶段参考 ───────────────────────────
    if quick:
        print('\n' + '='*60)
        print('【阶段1完成】量化筛选排名（不含AI护城河分析）')
        print('='*60)
        print(f'{"排名":<4} {"股票":8} {"代码":8} {"PE分位":8} {"PB":6} {"ROE":8} {"PEG":6} {"评分":6} {"层1"}')
        print('-'*70)
        for i, r in enumerate(results, 1):
            pct  = r['l3'].get('pe_percentile')
            pct_s = f"{pct:.0f}%" if pct else 'N/A'
            roe  = r['l3'].get('roe_3y_avg')
            roe_s = f"{roe:.1f}%" if roe else 'N/A'
            peg  = r['l3'].get('peg')
            peg_s = f"{peg:.2f}" if peg else 'N/A'
            flag = 'OK' if r['l1_pass'] else 'NO'
            print(f"{i:<4} {r['name']:8} {r['code']:8} {pct_s:8} {str(r['l3'].get('pb') or 'N/A'):6} {roe_s:8} {peg_s:6} {r['score']:5.1f}  {flag}")

        if top_n:
            top_codes = [r['code'] for r in results[:top_n]]
            print(f'\n[建议下一步] 对Top{top_n}运行完整分析：')
            print(f'  python run_analysis.py {" ".join(top_codes)}')

    # 生成报告
    report = generate_report(results)

    # 保存
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    out_path = Path(__file__).parent.parent / 'output' / f'screening_{ts}.md'
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(report, encoding='utf-8')

    print(f'\n报告已保存：{out_path}')
    print('\n── 量化筛选快速预览 ──')
    for r in results:
        flag = '✅' if r['l1_pass'] else '❌'
        pct  = r['l3'].get('pe_percentile')
        pct_str = f"PE分位{pct:.0f}%" if pct else 'PE分位N/A'
        print(f"  {'OK' if r['l1_pass'] else 'NO'} {r['name']:8s} {r['code']}  评分:{r['score']:5.1f}  {pct_str}  护城河:{r['l2'].get('moat_score',0)}/5")

    return results, str(out_path)


if __name__ == '__main__':
    main()
