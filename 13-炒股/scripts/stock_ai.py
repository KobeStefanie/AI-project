"""
AI 炒股助手 - 核心脚本
功能：调用 AI 分析股票，结合腾讯/东方财富 API 获取真实 A 股行情数据
数据层：使用 urllib 直连（绕过 Windows 注册表代理，无需注册账号）
"""

import os
import sys
import json
import datetime
import ssl
import urllib.request
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd

# 加载配置
env_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(env_path)

AI_BASE = os.getenv("OPENAI_API_BASE", "https://www.catkingai.com/v1")
AI_KEY  = os.getenv("OPENAI_API_KEY", "")

# SSL 上下文（允许自签名，避免 Windows 证书链问题）
_ssl_ctx = ssl._create_unverified_context()

def _http_get(url: str, params: dict = None, headers: dict = None, encoding="utf-8") -> str:
    """urllib 直连，完全绕过系统代理（包括 Windows 注册表代理）"""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    if headers:
        default_headers.update(headers)
    req = urllib.request.Request(url, headers=default_headers)
    # ProxyHandler({}) 强制不使用任何代理；HTTPSHandler 注入 SSL 上下文
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}),
        urllib.request.HTTPSHandler(context=_ssl_ctx),
    )
    with opener.open(req, timeout=15) as resp:
        return resp.read().decode(encoding, errors="replace")


# ─────────────────────────────────────────
# 1. AI 客户端
# ─────────────────────────────────────────
def get_ai_client():
    from openai import OpenAI
    return OpenAI(api_key=AI_KEY, base_url=AI_BASE)


def ask_ai(prompt: str, model: str = "claude-sonnet-4-6", system: str = None) -> str:
    """调用 AI 分析"""
    client = get_ai_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=0.3,
    )
    return resp.choices[0].message.content


# ─────────────────────────────────────────
# 2. 行情数据（腾讯财经直连，urllib 绕代理）
# ─────────────────────────────────────────
def _sina_prefix(code: str) -> tuple:
    """返回 (纯代码, sh/sz前缀)"""
    code = code.replace(".SH","").replace(".SZ","").replace(".sh","").replace(".sz","")
    prefix = "sh" if code.startswith("6") else "sz"
    return code, prefix


def get_stock_daily(code: str, start: str, end: str = None) -> pd.DataFrame:
    """
    获取日线行情（前复权），主源：腾讯财经
    code: 000001 / 600519 / 000001.SZ / 600519.SH 均可
    start/end: YYYYMMDD 或 YYYY-MM-DD
    """
    if end is None:
        end = datetime.date.today().strftime("%Y%m%d")

    # 格式化为 YYYY-MM-DD
    s = f"{start[:4]}-{start[4:6]}-{start[6:8]}" if "-" not in start else start
    e = f"{end[:4]}-{end[4:6]}-{end[6:8]}"   if "-" not in end   else end

    pure, prefix = _sina_prefix(code)
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {
        "_var": "x",
        "param": f"{prefix}{pure},day,{s},{e},500,qfq",
    }
    raw = _http_get(url, params=params, headers={"Referer": "https://gu.qq.com/"})

    # 响应格式: x={"code":0,"data":{"sh600519":{"qfqday":[...]}}}
    raw = raw.lstrip("x=")
    obj = json.loads(raw)
    klines = (obj.get("data", {})
                 .get(f"{prefix}{pure}", {})
                 .get("qfqday", []))

    if not klines:
        return pd.DataFrame()

    rows = []
    for k in klines:
        # [date, open, close, high, low, volume, ...]
        rows.append({
            "日期":      k[0],
            "开盘":      float(k[1]),
            "收盘":      float(k[2]),
            "最高":      float(k[3]),
            "最低":      float(k[4]),
            "成交量(手)": float(k[5]) if len(k) > 5 else 0,
        })

    df = pd.DataFrame(rows)
    # 计算涨跌幅
    df["涨跌幅%"] = df["收盘"].pct_change() * 100
    df["涨跌幅%"] = df["涨跌幅%"].round(2)

    # 股票名从实时行情拿
    try:
        q = get_realtime_quote(code)
        df.attrs["name"] = q.get("名称", pure)
    except Exception:
        df.attrs["name"] = pure
    return df


def get_realtime_quote(code: str) -> dict:
    """获取实时行情快照（新浪财经接口，urllib直连 gbk）"""
    import re
    code = code.replace(".SH","").replace(".SZ","").replace(".sh","").replace(".sz","")
    prefix = "sh" if code.startswith("6") else "sz"
    url = f"http://hq.sinajs.cn/list={prefix}{code}"
    # 新浪返回 gbk，单独处理编码
    req = urllib.request.Request(url, headers={
        "Referer": "https://finance.sina.com.cn/",
        "User-Agent": "Mozilla/5.0",
    })
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=10) as resp:
        text = resp.read().decode("gbk", errors="replace").strip()

    m = re.search(r'"([^"]+)"', text)
    if not m or not m.group(1):
        return {"代码": code, "名称": "", "现价": 0, "涨跌幅%": 0}
    parts = m.group(1).split(",")
    if len(parts) < 6:
        return {"代码": code, "名称": parts[0] if parts else code, "现价": 0, "涨跌幅%": 0}
    name   = parts[0]
    open_  = float(parts[1])
    close_ = float(parts[2])   # 昨收
    price  = float(parts[3])
    high   = float(parts[4])
    low    = float(parts[5])
    vol    = int(parts[8]) if len(parts) > 8 else 0
    chg_pct = round((price - close_) / close_ * 100, 2) if close_ else 0
    return {
        "代码": f"{prefix}{code}",
        "名称": name,
        "现价": price,
        "涨跌幅%": chg_pct,
        "最高": high,
        "最低": low,
        "开盘": open_,
        "昨收": close_,
        "成交量(手)": vol,
        "总市值(亿)": 0,
    }
    m = re.search(r'"([^"]+)"', text)
    if not m or not m.group(1):
        return {"代码": code, "名称": "", "现价": 0, "涨跌幅%": 0}
    parts = m.group(1).split(",")
    if len(parts) < 6:
        return {"代码": code, "名称": parts[0] if parts else code, "现价": 0, "涨跌幅%": 0}
    name   = parts[0]
    open_  = float(parts[1])
    close_ = float(parts[2])   # 昨收
    price  = float(parts[3])
    high   = float(parts[4])
    low    = float(parts[5])
    vol    = int(parts[8]) if len(parts) > 8 else 0  # 手数
    chg_pct = round((price - close_) / close_ * 100, 2) if close_ else 0
    return {
        "代码": f"{prefix}{code}",
        "名称": name,
        "现价": price,
        "涨跌幅%": chg_pct,
        "最高": high,
        "最低": low,
        "开盘": open_,
        "昨收": close_,
        "成交量(手)": vol,
        "总市值(亿)": 0,  # 新浪接口无总市值，留空
    }


# ─────────────────────────────────────────
# 3. AI + 数据 联合分析
# ─────────────────────────────────────────
ANALYST_SYSTEM = """你是一位专业的 A 股投资分析师，擅长技术分析与基本面分析。
分析时请：
1. 给出明确的判断（看多/看空/中性）及置信度
2. 列出关键支撑位和压力位（具体价位）
3. 建议操作策略（止损位、目标位）
4. 说明主要风险点
语言简洁专业，用中文回答。"""


def analyze_stock(code: str, days: int = 60):
    """一键 AI 分析某只股票（默认近60交易日）"""
    end = datetime.date.today().strftime("%Y%m%d")
    # 往前推约3个月
    start = (datetime.date.today() - datetime.timedelta(days=days * 2)).strftime("%Y%m%d")

    print(f"\n[数据] 正在获取 {code} 行情数据...")
    df = get_stock_daily(code, start, end)
    if df.empty:
        print("[ERR] 未获取到数据，请检查股票代码")
        return None

    df = df.tail(days)
    name = df.attrs.get("name", code)
    print(f"[OK] 获取到 {name}（{code}）{len(df)} 条日线数据")

    # 简单技术指标
    closes = df["收盘"].values
    ma5  = df["收盘"].rolling(5).mean().iloc[-1]
    ma20 = df["收盘"].rolling(20).mean().iloc[-1]
    ma60 = df["收盘"].rolling(min(60, len(df))).mean().iloc[-1]
    latest = closes[-1]
    high_60 = df["最高"].max()
    low_60  = df["最低"].min()

    recent_str = df.tail(30)[["日期","开盘","收盘","最高","最低","成交量(手)","涨跌幅%"]].to_string(index=False)

    prompt = f"""
股票：{name}（{code}）

【技术指标（已计算）】
最新收盘价：{latest:.2f}
MA5：{ma5:.2f}  MA20：{ma20:.2f}  MA60：{ma60:.2f}
近{days}日最高：{high_60:.2f}  最低：{low_60:.2f}
均线多头排列：{"是" if ma5 > ma20 > ma60 else "否"}

【近30交易日 K 线数据】
{recent_str}

请基于以上数据进行技术分析，给出操作建议。
"""
    print("\n[AI] AI 分析中...\n")
    result = ask_ai(prompt, system=ANALYST_SYSTEM)
    sep = "=" * 60
    print(sep)
    print(f"【{name} 分析报告】")
    print(sep)
    print(result)
    print(sep)
    return result


def chat_stock(question: str):
    """纯 AI 问答"""
    print("\n[AI] AI 回答中...\n")
    answer = ask_ai(question, system=ANALYST_SYSTEM)
    print(answer)
    return answer


def show_quote(code: str):
    """显示实时行情"""
    q = get_realtime_quote(code)
    chg = q["涨跌幅%"]
    sign = "+" if chg >= 0 else "-"
    print(f"\n{'='*40}")
    print(f"  {q['名称']}（{q['代码']}）")
    print(f"  现价：{q['现价']:.2f}  {sign}{abs(chg):.2f}%")
    print(f"  今开：{q['开盘']:.2f}  昨收：{q['昨收']:.2f}")
    print(f"  最高：{q['最高']:.2f}  最低：{q['最低']:.2f}")
    print(f"  总市值：{q['总市值(亿)']} 亿")
    print(f"{'='*40}\n")
    return q


# ─────────────────────────────────────────
# 4. 命令行入口
# ─────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：")
        print("  python stock_ai.py test              # 测试 AI 连接")
        print("  python stock_ai.py quote 600519      # 实时行情")
        print("  python stock_ai.py analyze 600519    # AI 技术分析")
        print("  python stock_ai.py chat '问题'       # AI 问答")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "test":
        print("测试 AI API 连接...")
        r = ask_ai("用一句话介绍你自己，用中文回答")
        print(f"AI：{r}")
        print("\n测试行情数据...")
        q = get_realtime_quote("600519")
        print(f"茅台现价：{q['现价']} 涨跌幅：{q['涨跌幅%']}%")
        print("\n[OK] 全部测试通过！")

    elif cmd == "quote" and len(sys.argv) >= 3:
        show_quote(sys.argv[2])

    elif cmd == "analyze" and len(sys.argv) >= 3:
        days = int(sys.argv[3]) if len(sys.argv) >= 4 else 60
        analyze_stock(sys.argv[2], days=days)

    elif cmd == "chat" and len(sys.argv) >= 3:
        chat_stock(sys.argv[2])

    else:
        print(f"未知命令：{cmd}")
