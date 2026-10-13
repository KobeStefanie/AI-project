# Bug 修复日志

> 新记录加在最上面。排查问题前先搜本文件有没有同类记录。
> 补建于 2026-10-09（全局规则：所有项目必须有 BUG_FIX_LOG.md）。

---

## 2026-10-13

### Bug：候选池页一直显示"加载行情……"

**症状**：打开 127.0.0.1:5077/#watch，页面停在转圈，没有报错

**根本原因**：
1. 界面后台还是改代码之前启动的旧进程，没有 /api/watchlist 路由，返回 404（curl 实测 HTTP 404，/api/meta 正常）。浏览器拿到的是新的 app.js（静态文件每次重读），后端路由却是旧的
2. loadWatch 没有捕获异常，api() 抛错后页面停在"加载行情……"，错误被吞掉

**修复方案**：web/app.js loadWatch 加 try/catch，失败时显示错误；是 404 时提示"关掉黑窗口重新双击 启动界面.bat"

**影响文件**：
- `scripts/web/app.js` loadWatch 开头

**验证步骤**：
1. 不重开后台、刷新候选池页 → 应显示红框提示而不是一直转
2. 重开 启动界面.bat 后刷新 → 显示空候选池和"加入"输入框

**排查弯路**：无。下次改了后端路由出现 404 或一直转，先查后台有没有重开

### Bug：访谈开场报 502「Upstream stream ended without a response」

**症状**：10:44 新开"A. 个股访谈"，右下角红色提示 `AI 调用失败：Error code: 502 - {'error': {'message': 'Upstream stream ended without a response', 'type': 'server_error'}}`；data/interviews/20261013-104430.json 只有隐藏的开场引导，没有 AI 回复

**根本原因**：CatKing 中转偶发 502（上游模型连接中断），不是密钥或代码问题。事后同一密钥、同一访谈上下文连调 4 次全部成功（3.8~8.7 秒）。代码层面的问题：OpenAI SDK 默认只自动重试 2 次，偶发故障直接抛给用户；`_raise` 把 503 当成"模型不可用"，提示会误导

**修复方案**：
- 新增 `MAX_RETRIES = 4`，传给 OpenAI / Anthropic 客户端的 `max_retries`（SDK 自带指数退避，只对 5xx/超时/连接错误重试）
- `_raise`：404/model_not_found 才提示"模型不可用"；≥500 提示"中转临时出错，已自动重试 N 次，稍后点重试"

**影响文件**：
- `scripts/ai_client.py`（MAX_RETRIES 常量、_raise、两处客户端构造）

**验证步骤**：
1. httpx.MockTransport 模拟前 2 次 502、第 3 次 200 → `chat()` 正常返回，共 3 次请求 ✅
2. 模拟一直 502 → 共 5 次请求后抛出新文案 ✅
3. 界面需重开（关黑窗口，双击 启动界面.bat）才生效

**下次先查**：5xx 先直接重调一次 `ai_client.chat`，能通就是中转偶发；401/403 才是密钥问题（见下方 10-12 记录）

---

<!-- 记录模板：

## vXX (YYYY-MM-DD)

### Bug：[一句话描述]

**症状**：[用户看到的现象 / 原始报错]

**根本原因**：[代码或配置层面的根因]

**修复方案**：[具体改了什么，必要时附代码对比]

**影响文件**：
- `路径/文件名:行号`

**验证步骤**：
1. [如何复现]
2. [如何确认已修复]

**排查弯路**（如有）：[走错的方向 + 下次先查什么]

**⚠️ 已知隐患**（如有）：[触发条件 / 后果 / 临时规避 / 计划修法]

-->

## 2026-10-12

### 已知隐患：界面改了后端代码不会自动生效

**触发条件**：界面运行中（启动界面.bat 的黑窗口开着）修改 scripts/*.py。app.py 以 `debug=False` 运行，不热重载
**后果**：改动不生效，看起来像"没修好"。例：coach.py 18:31 的提示词改动，对 18:26 启动的界面进程无效
**例外**：config/.env 每次调用 AI 都重读，换密钥不用重启；web/ 下的 html/js 刷新浏览器即可
**规避**：改完后端提醒用户关掉黑窗口重新双击
**下次先查**：用户说"还是老样子"时，先 `netstat -ano | grep 5077` + 看进程启动时间是否早于文件修改时间

### Bug：AI 回复的 **粗体** 在界面显示成星号；回复里出现内部条目 id（如 pick2）

**根本原因**：前端 nl2br 只转义和换行，不处理 Markdown；coach.py 提示词把 [id] 交给模型时没说明不能在正文里用
**修复方案**：web/app.js `nl2br` 在转义之后把 `**x**` 转为 `<b>`（先转义，仍不会执行 AI 返回的 HTML）；coach.py INTERVIEW_SYSTEM 增加"正文说条目名称，id 只用在 SUGGEST 里"
**影响文件**：scripts/web/app.js:4、scripts/coach.py INTERVIEW_SYSTEM"访谈方式"
**验证步骤**：重开界面后做一次访谈，回复里粗体正常、不出现 pick/hold 等 id（⚠️ 尚未在浏览器实测）

### 已知隐患：config/.env 的 AI 密钥失效，访谈和复盘点评不可用（✅ 已于同日修复：用户提供新密钥，claude-sonnet-4-6 实测可用，单次约10~15秒）

**症状**：界面"开始访谈"/"让 Claude 点评"报"模型 claude-sonnet-4-6 不可用"

**根本原因**：CatKing 中转返回 503 `model_not_found`；查询模型列表返回 403 `GROUP_DELETED`（"API Key 所属分组已删除"）。是密钥本身在服务商那边被停用，不是代码问题。layer2 产业链 AI（screener.py `_ai`）同样受影响

**临时规避**：行情、K线、跟盘手写、交易系统编辑都不依赖 AI，可正常用

**计划修法**：用户在 config/.env 填新的密钥。scripts/ai_client.py 支持两种：`ANTHROPIC_API_KEY`(+`ANTHROPIC_BASE_URL`) 或 `OPENAI_API_KEY`(+`OPENAI_API_BASE`)，可选 `AI_MODEL`；每次调用重读 .env，改完不用重启界面

**下次先查**：报"不可用/403"时先跑 `client.models.list()` 看错误码，403=密钥问题，503=模型名问题

### 已知隐患：腾讯日K接口返回 HTTP 501

**症状**：`get_daily_kline('000977')` 报 `urllib.error.HTTPError: HTTP Error 501: Not Implemented`

**根本原因**：web.ifzq.gtimg.cn/appstock/app/fqkline/get 接口拒绝请求（原因未查明，可能是接口下线或参数变更）

**临时规避**：新脚本 daily_track.py 改用 AKShare `stock_zh_a_daily`（新浪源，前复权），已验证可用

**影响范围**：`scripts/data_fetcher.py:189 get_daily_kline`、`scripts/stock_ai.py:78 get_stock_daily` 都依赖该接口，目前不可用

**计划修法**：两个函数统一改为 AKShare stock_zh_a_daily

---

### Bug：PE历史分位为0%时，报告详情和终端输出显示"N/A"

**症状**：screening_20261012_1700.md 中东阿阿胶、华东医药、恒瑞医药摘要表显示分位0%，详情页却显示"历史分位：N/A%"，终端也显示"PE分位N/A"。容易误读成"数据缺失"，实际是"处于5年最低位"

**根本原因**：用 `x or 'N/A'` / `if pct` 判断空值，Python 把 0.0 当成假值

**修复方案**：三处统一改为 `is not None` 判断
```python
# 修复前
历史分位：{l1.get('pe_percentile') or 'N/A'}%
pct_s = f"{pct:.0f}%" if pct else 'N/A'
# 修复后
历史分位：{f'{pct_v:.0f}%' if pct_v is not None else 'N/A'}
pct_s = f"{pct:.0f}%" if pct is not None else 'N/A'
```

**影响文件**：
- `scripts/run_analysis.py:93-94`（报告详情页）
- `scripts/run_analysis.py:192`（--quick 终端排名表）
- `scripts/run_analysis.py:219`（终端快速预览）

**验证步骤**：
1. 单元验证：0.0→"0%"，20.0→"20%"，None→"N/A"（已通过）
2. 回归：跑 `python run_analysis.py --quick 000423`，详情页应显示"历史分位：0%"

**⚠️ 已知隐患**：`r['l3'].get('roe_3y_avg')`、`peg` 在 run_analysis.py:193-196 也用 `if roe` / `if peg` 判断，ROE 或 PEG 恰好为 0 时同样会显示 N/A（触发概率低，暂不修）

---

## 补建前的修复记录

补建前的修复只零散记录在 PROJECT_STATUS.md 第 18、29-30、84-85 行（PE 历史分位由写死改为真实 5 年数据、PEG 指标接入），未按本模板整理。以后再遇到同类问题时，按需补成完整记录。

---
