// 前端：所有文本都经 esc() 转义后再插入，避免 AI 回复或用户输入里的 HTML 被执行
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// 先转义再处理 **粗体**，AI 回复里的其他 HTML 依然不会被执行
const nl2br = s => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').replace(/\n/g, '<br>');
const state = { meta: null, positions: {}, code: null, date: null, journal: {}, iv: null };

async function api(path, body) {
  const opt = body === undefined ? {} : { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body) };
  const r = await fetch(path, opt);
  const data = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
  if (!r.ok) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}

function toast(msg, ok = true) {
  const t = $('#toast');
  t.textContent = msg;
  t.className = `fixed bottom-6 right-6 px-4 py-3 rounded shadow text-white max-w-md ${ok ? 'bg-slate-800' : 'bg-red-600'}`;
  clearTimeout(t._h);
  t._h = setTimeout(() => t.classList.add('hidden'), ok ? 2500 : 6000);
}

async function busy(btn, fn) {
  const old = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 处理中';
  try { return await fn(); } catch (e) { toast(e.message, false); } finally { btn.disabled = false; btn.innerHTML = old; }
}

// ─── 导航 ──────────────────────────────────────────────
function show(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  $(`#page-${page}`).classList.remove('hidden');
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.page === page));
  location.hash = page;
  ({ journal: loadJournal, watch: loadWatch, interview: loadInterviews, system: loadSystem, position: loadPositions, mobile: loadMobile })[page]();
}
document.querySelectorAll('.nav-btn').forEach(b => b.onclick = () => show(b.dataset.page));

// ─── 每日跟盘 ───────────────────────────────────────────
async function loadJournal() {
  state.positions = await api('/api/positions');
  const codes = Object.keys(state.positions);
  if (!codes.length) { $('#journal-detail').innerHTML = '<div class="bg-white rounded p-6">还没有持仓，先去"持仓设置"添加。</div>'; return; }
  if (!state.code || !codes.includes(state.code)) state.code = codes[0];
  $('#stock-tabs').innerHTML = codes.map(c => `<button role="tab" aria-selected="${c === state.code}" data-code="${c}"
    class="px-3 py-1 rounded ${c === state.code ? 'bg-slate-800 text-white' : 'bg-white'}">${esc(state.positions[c].name || c)}</button>`).join('');
  $('#stock-tabs').querySelectorAll('button').forEach(b => b.onclick = () => { state.code = b.dataset.code; state.date = null; loadJournal(); });
  state.journal = await api(`/api/journal/${state.code}`);
  const dates = Object.keys(state.journal);
  const today = new Date().toISOString().slice(0, 10);
  if (!dates.includes(today)) dates.unshift(today);
  if (!state.date || !dates.includes(state.date)) state.date = dates[0];
  $('#date-list').innerHTML = dates.map(d => `<li><button data-d="${d}" class="w-full text-left px-3 py-2 rounded text-sm
    ${d === state.date ? 'bg-slate-800 text-white' : 'bg-white hover:bg-slate-50'}">${d}${state.journal[d]?.ai_comment ? ' <i class="fa fa-check-circle text-green-500"></i>' : ''}</button></li>`).join('');
  $('#date-list').querySelectorAll('button').forEach(b => b.onclick = () => { state.date = b.dataset.d; loadJournal(); });
  renderEntry();
}

function card(title, body, extra = '') {
  return `<div class="bg-white rounded-lg shadow-sm p-5 ${extra}"><h2 class="font-semibold mb-3">${title}</h2>${body}</div>`;
}

function renderSnapshot(s) {
  if (!s) return card('行情', '<p class="text-slate-500">这一天还没有行情快照，点右上角"刷新行情"。</p>');
  const cls = s.chg_pct >= 0 ? 'up' : 'down';
  const ma = Object.entries(s.ind).filter(([k]) => k.startsWith('ma')).map(([k, v]) =>
    `<span class="mr-4">${k.toUpperCase()} <b>${v}</b> <span class="text-xs ${s.price >= v ? 'up' : 'down'}">${s.price >= v ? '上方' : '下方'}</span></span>`).join('');
  const p = s.position;
  const pos = p ? `<div class="grid grid-cols-4 gap-3 text-sm">
      <div>首次买入价<div class="text-lg font-semibold">${p.first}</div><div class="${p.from_first_pct >= 0 ? 'up' : 'down'}">${p.from_first_pct > 0 ? '+' : ''}${p.from_first_pct}%</div></div>
      <div>止损价（×70%）<div class="text-lg font-semibold text-red-600">${p.stop}</div><div class="text-slate-500">距现价 ${p.to_stop_pct}%</div></div>
      <div>加仓价<div class="text-lg font-semibold">${p.adds.join(' / ')}</div></div>
      <div>持股 / 浮盈<div class="text-lg font-semibold">${p.shares} 股</div><div class="${(p.pnl ?? 0) >= 0 ? 'up' : 'down'}">${p.pnl ?? '—'} 元</div></div>
    </div>${p.warns ? `<div class="grid grid-cols-3 gap-3 text-sm mt-3">
      <div class="rounded p-2 ${s.price <= p.warns[0] ? 'bg-yellow-100 font-semibold' : 'bg-slate-50'}">一级预警 -10%：<b>${p.warns[0]}</b></div>
      <div class="rounded p-2 ${s.price <= p.warns[1] ? 'bg-orange-100 font-semibold' : 'bg-slate-50'}">二级预警 -20%：<b>${p.warns[1]}</b></div>
      <div class="rounded p-2 ${s.price <= p.stop ? 'bg-red-100 font-semibold' : 'bg-slate-50'}">三级止损 -30%：<b class="text-red-600">${p.stop}</b></div>
    </div>` : ''}${p.cash_left !== undefined ? `<div class="text-sm text-slate-500 mt-2">剩余现金 ${p.cash_left} 元</div>` : ''}`
    : '';
  const alerts = s.alerts.map(a => `<div class="bg-amber-50 border border-amber-200 text-amber-800 rounded px-3 py-2 text-sm">${esc(a)}</div>`).join('');
  return card(`${esc(s.name)} <span class="text-sm text-slate-400 font-normal ml-2">抓取于 ${esc(s.fetched)}</span>`, `
    <div class="flex items-end gap-6 mb-4">
      <div class="text-4xl font-bold ${cls}">${s.price}</div>
      <div class="text-xl ${cls}">${s.chg_pct > 0 ? '+' : ''}${s.chg_pct}%</div>
      <div class="text-sm text-slate-500">开 ${s.open}　高 ${s.high}　低 ${s.low}　PE ${s.pe ?? '—'}　PB ${s.pb ?? '—'}</div>
    </div>
    <div class="text-sm mb-2">${ma}</div>
    <div class="text-sm text-slate-600 mb-4">ATR14 <b>${s.ind.atr14}</b>（${s.ind.atr_pct}%）　20日区间 <b>${s.ind.low20} ~ ${s.ind.high20}</b>　量比 ${s.ind.vol_ratio}</div>
    <div id="kline" class="w-full h-72 mb-4" role="img" aria-label="近120日K线图"></div>
    <div class="grid grid-cols-2 gap-3 mb-4 text-sm">
      <div class="bg-red-50 rounded p-3"><b>正T（先卖后买）</b><br>冲高到 <b>${s.t_ref.sell_above}</b> 以上卖一部分，回落 ${s.t_ref.gap} 元以上接回</div>
      <div class="bg-green-50 rounded p-3"><b>倒T（先买后卖，只用做T资金）</b><br>回落到 <b>${s.t_ref.buy_below}</b> 以下买入，反弹 ${s.t_ref.gap} 元以上卖出</div>
    </div>
    <p class="text-xs text-slate-400 mb-3">做T参考 = 今日收盘 ± 半个ATR，是 Claude 的建议规则，尚未经过实盘验证。底仓不动。</p>
    ${pos}<div class="space-y-2 mt-3">${alerts}</div>`);
}

// 字段来自手机时，在标题后标出来（_meta 由后端记录）
function fromPhone(field) {
  const m = state.journal[state.date]?._meta?.[field];
  return m?.src === 'mobile' ? ` <span class="text-xs bg-amber-100 text-amber-800 rounded px-1"><i class="fa fa-mobile"></i> 来自${esc(m.device || '手机')}</span>` : '';
}

function ta(id, label, value, rows = 3, ph = '') {
  label += fromPhone(id.replace(/^f-/, ''));
  return `<label for="${id}" class="block text-sm font-medium mb-1">${label}</label>
    <textarea id="${id}" rows="${rows}" class="w-full border rounded p-2 mb-3" placeholder="${esc(ph)}">${esc(value)}</textarea>`;
}

function renderEntry() {
  const e = state.journal[state.date] || {};
  const pos = state.positions[state.code];
  const checks = e.checks || {};
  const checkHtml = state.meta.checks.map((c, i) => `<label class="flex items-center gap-2 mb-1 text-sm">
    <input type="checkbox" id="chk${i}" ${checks[c] ? 'checked' : ''} class="w-4 h-4"> ${esc(c)}</label>`).join('');
  $('#journal-detail').innerHTML = renderSnapshot(e.snapshot) +
    card('我的想法与操作', ta('f-thoughts', '我的想法（盘前/盘中，怎么想就怎么写）', e.thoughts, 4, '比如：今天跌到20日低点附近，我想……') +
      ta('f-operations', '今日操作（没操作写"无"）', e.operations, 2, '比如：63.2 卖出100股（正T）')) +
    card('今日复盘', `
      <div class="bg-slate-50 rounded p-3 mb-3 text-sm">
        <div><b>持股逻辑：</b>${esc(pos.thesis || '未录入，去"访谈"做一次个股访谈')}</div>
        <div><b>证伪条件：</b>${esc(pos.invalidation || '未录入')}</div>
      </div>
      <div class="mb-3">${fromPhone('checks') ? `<div class="mb-1">自查${fromPhone('checks')}</div>` : ''}${checkHtml}</div>
      ${ta('f-did_right', '做对了什么', e.did_right, 2)}${ta('f-improve', '要改什么', e.improve, 2)}
      <div class="flex gap-2"><button id="btn-save" class="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded">保存</button>
      <button id="btn-comment" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"><i class="fa fa-magic mr-1"></i>保存并让 Claude 点评</button></div>`) +
    card('Claude 点评', e.ai_comment ? `<div class="text-sm leading-7">${nl2br(e.ai_comment)}</div>` : '<p class="text-sm text-slate-500">写完想法和复盘后，点"让 Claude 点评"。</p>');
  $('#btn-save').onclick = () => busy($('#btn-save'), async () => { await saveEntry(); toast('已保存'); loadJournal(); });
  $('#btn-comment').onclick = () => busy($('#btn-comment'), async () => {
    await saveEntry();
    await api(`/api/journal/${state.code}/${state.date}/comment`, {});
    toast('点评完成'); loadJournal();
  });
  if (e.snapshot) drawKline();
}

function saveEntry() {
  const v = id => $(`#f-${id}`).value;
  const checks = {};
  state.meta.checks.forEach((c, i) => checks[c] = $(`#chk${i}`).checked);
  return api(`/api/journal/${state.code}/${state.date}`,
    { thoughts: v('thoughts'), operations: v('operations'), did_right: v('did_right'), improve: v('improve'), checks,
      base_rev: state.journal[state.date]?._rev ?? 0 });
}

async function drawKline() {
  const el = $('#kline');
  if (!el) return;
  const chart = echarts.init(el);
  chart.showLoading();
  let rows;
  try { rows = await api(`/api/kline/${state.code}`); } catch (e) { chart.hideLoading(); el.textContent = 'K线加载失败：' + e.message; return; }
  chart.hideLoading();
  const p = state.journal[state.date]?.snapshot?.position;
  const lines = p ? [{ yAxis: p.stop, name: '止损-30%', lineStyle: { color: '#dc2626' } },
    ...(p.warns || []).map((w, i) => ({ yAxis: w, name: `预警-${(i + 1) * 10}%`, lineStyle: { color: i ? '#ea580c' : '#ca8a04', type: 'dashed' } })),
    ...p.adds.map((a, i) => ({ yAxis: a, name: `加仓${i + 1}`, lineStyle: { color: '#f59e0b' } }))] : [];
  const ma = (k, color) => ({ name: k.toUpperCase(), type: 'line', data: rows.map(r => r[k]), smooth: true, showSymbol: false, lineStyle: { width: 1, color } });
  chart.setOption({
    animation: false, grid: { left: 50, right: 20, top: 30, bottom: 30 },
    legend: { top: 0, data: ['MA5', 'MA10', 'MA20', 'MA60'] }, tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: rows.map(r => r.date) }, yAxis: { scale: true },
    dataZoom: [{ type: 'inside', start: 50, end: 100 }],
    series: [
      { name: 'K线', type: 'candlestick', data: rows.map(r => [r.open, r.close, r.low, r.high]),
        itemStyle: { color: '#dc2626', color0: '#16a34a', borderColor: '#dc2626', borderColor0: '#16a34a' },
        markLine: { symbol: 'none', label: { formatter: '{b} {c}' }, data: lines } },
      ma('ma5', '#f59e0b'), ma('ma10', '#8b5cf6'), ma('ma20', '#2563eb'), ma('ma60', '#64748b'),
    ],
  });
  window.addEventListener('resize', () => chart.resize());
}

$('#btn-refresh').onclick = () => busy($('#btn-refresh'), async () => {
  const r = await api(`/api/journal/${state.code}/refresh`, {});
  state.date = r.date; toast(`已刷新 ${r.date} 行情`); loadJournal();
});
// ─── 候选池 ─────────────────────────────────────────────
async function loadWatch() {
  $('#watch-list').innerHTML = '<div class="text-sm text-slate-400"><i class="fa fa-spinner fa-spin"></i> 加载行情……</div>';
  let items, max;
  try { ({ items, max } = await api('/api/watchlist')); }
  catch (e) {
    // 404 基本都是后端还是旧进程：改了代码没重开界面
    $('#watch-list').innerHTML = `<div class="bg-red-50 border border-red-200 text-red-700 rounded p-4 text-sm">候选池加载失败：${esc(e.message)}${
      e.message.includes('404') ? '<br>后台还是旧版本：关掉黑窗口，重新双击 启动界面.bat，再刷新本页。' : ''}</div>`;
    return;
  }
  $('#watch-count').textContent = `${items.length} / ${max} 只`;
  const row = c => {
    const sr = c.screen;
    const chg = c.chg_pct == null ? '' : `<span class="${c.chg_pct >= 0 ? 'up' : 'down'}">${c.chg_pct > 0 ? '+' : ''}${c.chg_pct}%</span>`;
    const scr = sr ? `系统筛选 ${esc(sr.date)}：PE历史分位 <b>${esc(sr.pe_pct)}</b>，综合分 <b>${esc(sr.score)}</b>，${sr.pass ? '<span class="text-green-600">通过层1</span>' : '<span class="text-red-600">未通过层1</span>'}
      <span class="text-slate-400">（${esc(sr.file)}）</span>` : '系统筛选：还没跑过（命令行 <code>python run_analysis.py ' + esc(c.code) + '</code>）';
    return `<div class="bg-white rounded-lg shadow-sm p-5" data-code="${c.code}">
      <div class="flex items-center gap-3 mb-2">
        <h2 class="font-semibold">${esc(c.name || c.code)}（${c.code}）</h2>
        <span class="text-lg font-semibold">${c.price ?? '—'}</span>${chg}
        ${c.price != null && c.price > 50 ? '<span class="text-xs bg-amber-100 text-amber-800 px-2 rounded">股价 &gt;50，一手超过底仓 5000</span>' : ''}
        <button class="btn-rm-watch ml-auto text-red-600 hover:underline text-sm"><i class="fa fa-minus-circle"></i> 移出</button>
      </div>
      <div class="text-sm text-slate-600 mb-3">${scr}</div>
      <label for="w-${c.code}-reason" class="block text-sm mb-1">为什么关注（赚的是什么钱）</label>
      <textarea id="w-${c.code}-reason" rows="2" class="w-full border rounded p-2 mb-2">${esc(c.reason)}</textarea>
      <label for="w-${c.code}-buy_condition" class="block text-sm mb-1">买入条件（估值/基本面，到什么程度才买底仓）</label>
      <textarea id="w-${c.code}-buy_condition" rows="2" class="w-full border rounded p-2 mb-2">${esc(c.buy_condition)}</textarea>
      <div class="flex items-center gap-2"><span class="text-xs text-slate-400">加入于 ${esc(c.added)}</span>
        <button class="btn-save-watch bg-slate-800 text-white px-4 py-1 rounded ml-auto">保存</button></div></div>`;
  };
  $('#watch-list').innerHTML = (items.map(row).join('') || '<div class="bg-white rounded p-6 text-sm text-slate-500">候选池是空的。</div>') +
    (items.length < max ? `<div class="bg-white rounded-lg shadow-sm p-5 flex gap-2 items-end">
      <div><label for="new-watch" class="block text-sm mb-1">加入候选池（股票代码）</label>
        <input id="new-watch" class="border rounded px-2 py-2" placeholder="如 600690"></div>
      <button id="btn-add-watch" class="border px-4 py-2 rounded"><i class="fa fa-plus"></i> 加入</button>
      <span class="text-sm text-slate-400 ml-2">名称自动从行情接口取</span></div>`
      : `<div class="text-sm text-slate-500">已满 ${max} 只。想加新的，先移出一只。</div>`);
  document.querySelectorAll('.btn-save-watch').forEach(b => b.onclick = () => busy(b, async () => {
    const code = b.closest('[data-code]').dataset.code;
    await api(`/api/watchlist/${code}`, { reason: $(`#w-${code}-reason`).value, buy_condition: $(`#w-${code}-buy_condition`).value });
    toast('已保存');
  }));
  document.querySelectorAll('.btn-rm-watch').forEach(b => b.onclick = () => {
    const code = b.closest('[data-code]').dataset.code;
    if (!confirm(`把 ${code} 移出候选池？\n写过的关注理由和买入条件会一起清掉。`)) return;
    busy(b, async () => { await api(`/api/watchlist/${code}/remove`, {}); toast('已移出'); loadWatch(); });
  });
  const ab = $('#btn-add-watch');
  if (ab) ab.onclick = () => busy(ab, async () => {
    await api(`/api/watchlist/${$('#new-watch').value.trim()}`, {});
    toast('已加入候选池'); loadWatch();
  });
}

// ─── 访谈 ──────────────────────────────────────────────
function sugLabel(s) {
  if (s.watch) return `候选池 ${esc(s.watch)} 的${s.field === 'reason' ? '关注理由' : '买入条件'}`;
  if (s.code) return '个股' + (s.field === 'thesis' ? '持股逻辑' : '证伪条件');
  return '交易系统规则（草案）';
}

async function loadInterviews() {
  $('#topic-select').innerHTML = state.meta.topics.map(t => `<option>${esc(t.key + '. ' + t.title)}</option>`).join('');
  const list = await api('/api/interviews');
  $('#iv-list').innerHTML = list.map(iv => `<li><button data-id="${iv.id}" class="w-full text-left px-4 py-3 border-b hover:bg-slate-50
    ${state.iv?.id === iv.id ? 'bg-blue-50' : ''}"><div class="text-sm font-medium truncate">${esc(iv.topic)}</div>
    <div class="text-xs text-slate-400">${esc(iv.created)} · ${iv.count} 条</div></button></li>`).join('')
    || '<li class="p-4 text-sm text-slate-400">还没有访谈</li>';
  $('#iv-list').querySelectorAll('button').forEach(b => b.onclick = async () => { state.iv = await api(`/api/interviews/${b.dataset.id}`); renderIv(); loadInterviews(); });
  if (state.iv) renderIv();
}

function renderIv() {
  const iv = state.iv;
  $('#iv-title').textContent = iv.topic;
  // 导出走普通下载链接，浏览器直接保存 PDF；后端出错时返回 JSON，会显示在新页面里
  $('#btn-iv-pdf').href = `/api/interviews/${iv.id}/pdf`;
  $('#btn-iv-pdf').classList.remove('hidden');
  $('#btn-iv-del').classList.remove('hidden');
  const msgs = iv.messages.filter(m => !m.hidden);
  const last = iv.messages[iv.messages.length - 1];
  $('#iv-messages').innerHTML = msgs.map((m, i) => {
    const mine = m.role === 'user';
    const sugs = (m.suggestions || []).map((s, j) => `<div class="mt-2 bg-amber-50 border border-amber-200 rounded p-2 text-sm text-slate-700">
      <div class="text-xs text-amber-700 mb-1"><i class="fa fa-lightbulb-o"></i> 可沉淀为${sugLabel(s)}${s.name ? '：' + esc(s.name) : ''}</div>
      <div>${esc(s.content)}</div>
      <button class="btn-apply mt-1 text-blue-600 hover:underline" data-m="${iv.messages.indexOf(m)}" data-s="${j}" ${s.applied ? 'disabled' : ''}>${s.applied ? '已采纳' : '采纳'}</button></div>`).join('');
    return `<div class="flex ${mine ? 'justify-end' : ''}"><div class="max-w-2xl rounded-lg px-4 py-3 leading-7 ${mine ? 'msg-user' : 'msg-ai'}">
      ${nl2br(m.content)}${sugs}<div class="text-xs mt-1 ${mine ? 'text-blue-200' : 'text-slate-400'}">${esc(m.time)}</div></div></div>`;
  }).join('');
  if (last && last.role === 'user') {
    $('#iv-messages').insertAdjacentHTML('beforeend', `<div class="text-sm text-slate-500">Claude 还没回复。<button id="btn-retry" class="text-blue-600 hover:underline">重试</button></div>`);
    $('#btn-retry').onclick = () => busy($('#btn-retry'), () => send(''));
  }
  $('#iv-messages').querySelectorAll('.btn-apply').forEach(b => b.onclick = () => busy(b, async () => {
    const m = state.iv.messages[b.dataset.m], s = m.suggestions[b.dataset.s];
    await api(`/api/interviews/${state.iv.id}/apply`, s);
    s.applied = true;
    toast(s.watch ? '已写入候选池' : s.code ? '已写入持仓的个股逻辑' : '已写入交易系统（🟡 草案），去"交易系统"页确认');
    renderIv();
  }));
  $('#iv-input').disabled = $('#btn-send').disabled = false;
  $('#iv-messages').scrollTop = $('#iv-messages').scrollHeight;
}

async function send(text) {
  if (text) state.iv.messages.push({ role: 'user', content: text, time: '刚刚' });
  renderIv();
  $('#iv-messages').insertAdjacentHTML('beforeend', '<div id="typing" class="text-sm text-slate-400"><i class="fa fa-spinner fa-spin"></i> Claude 正在思考……</div>');
  $('#iv-messages').scrollTop = $('#iv-messages').scrollHeight;
  try { await api(`/api/interviews/${state.iv.id}/message`, { content: text }); }
  catch (e) { toast(e.message, false); }
  state.iv = await api(`/api/interviews/${state.iv.id}`);
  renderIv();
}

$('#btn-send').onclick = () => {
  const text = $('#iv-input').value.trim();
  if (!text || !state.iv) return;
  $('#iv-input').value = '';
  busy($('#btn-send'), () => send(text));
};
$('#iv-input').onkeydown = e => { if (e.key === 'Enter' && e.ctrlKey) $('#btn-send').click(); };
$('#btn-iv-del').onclick = () => {
  const iv = state.iv;
  if (!iv || !confirm(`删除这条访谈？\n${iv.topic}（${iv.created}）\n\n文件会移到回收站，需要时可以从回收站还原。`)) return;
  busy($('#btn-iv-del'), async () => {
    await api(`/api/interviews/${iv.id}/delete`, {});
    state.iv = null;
    $('#iv-title').textContent = '选择或开始一个访谈';
    $('#iv-messages').innerHTML = '';
    $('#btn-iv-pdf').classList.add('hidden');
    $('#btn-iv-del').classList.add('hidden');
    $('#iv-input').disabled = $('#btn-send').disabled = true;
    toast('已移到回收站');
    await loadInterviews();
  });
};
$('#btn-new-iv').onclick = () => busy($('#btn-new-iv'), async () => {
  try { state.iv = await api('/api/interviews', { topic: $('#topic-select').value }); }
  finally { await loadInterviews(); }
});

// ─── 交易系统 ───────────────────────────────────────────
async function loadSystem() {
  const s = await api('/api/system');
  const all = s.modules.flatMap(m => m.items);
  const n = st => all.filter(i => i.status === st).length;
  $('#sys-progress').textContent = `✅ ${n('confirmed')}　🟡 ${n('draft')}　⬜ ${n('todo')}　共 ${all.length} 项`;
  $('#sys-modules').innerHTML = s.modules.map(m => {
    const done = m.items.filter(i => i.status === 'confirmed').length;
    return `<div class="bg-white rounded-lg shadow-sm p-5">
      <div class="flex items-center mb-3"><h2 class="font-semibold">${esc(m.title)}</h2>
        <div class="ml-auto w-24 h-2 bg-slate-100 rounded"><div class="h-2 bg-green-500 rounded" style="width:${done / m.items.length * 100}%"></div></div></div>
      ${m.items.map(it => `<div class="border-t py-2 text-sm">
        <div class="flex gap-2"><span>${state.meta.statuses[it.status]}</span><span class="font-medium">${esc(it.name)}</span>
          <button class="btn-edit ml-auto text-blue-600 hover:underline" data-id="${it.id}">编辑</button>
          ${it.status === 'draft' ? `<button class="btn-confirm text-green-600 hover:underline" data-id="${it.id}">确认</button>` : ''}</div>
        <div class="text-slate-600 ml-6">${esc(it.content || '—')}</div>
        ${it.source ? `<div class="text-xs text-slate-400 ml-6">来源：${esc(it.source)}</div>` : ''}
        <div class="edit-box hidden ml-6 mt-2" id="edit-${it.id}">
          <label class="sr-only" for="ec-${it.id}">内容</label>
          <textarea id="ec-${it.id}" rows="2" class="w-full border rounded p-2">${esc(it.content)}</textarea>
          <div class="flex gap-2 mt-1"><select id="es-${it.id}" class="border rounded px-2" aria-label="状态">
            ${Object.entries(state.meta.statuses).map(([k, v]) => `<option value="${k}" ${k === it.status ? 'selected' : ''}>${v}</option>`).join('')}</select>
            <button class="btn-save-item bg-slate-800 text-white px-3 rounded" data-id="${it.id}">保存</button></div></div>
      </div>`).join('')}</div>`;
  }).join('');
  $('#sys-log').innerHTML = s.changelog.slice(0, 30).map(c => `<li><span class="text-slate-400">${esc(c.time)}</span> ${esc(c.note)}</li>`).join('');
  const today = new Date().toISOString().slice(0, 10);
  document.querySelectorAll('.btn-edit').forEach(b => b.onclick = () => $(`#edit-${b.dataset.id}`).classList.toggle('hidden'));
  document.querySelectorAll('.btn-confirm').forEach(b => b.onclick = () => busy(b, async () => {
    const it = all.find(i => i.id === b.dataset.id);
    await api('/api/system/item', { item_id: it.id, content: it.content, status: 'confirmed', source: `${today} 本人确认` });
    toast('已确认'); loadSystem();
  }));
  document.querySelectorAll('.btn-save-item').forEach(b => b.onclick = () => busy(b, async () => {
    const id = b.dataset.id, status = $(`#es-${id}`).value;
    await api('/api/system/item', { item_id: id, content: $(`#ec-${id}`).value.trim(), status,
      source: status === 'confirmed' ? `${today} 本人确认` : `${today} 本人编辑` });
    toast('已保存'); loadSystem();
  }));
}

// ─── 持仓设置 ───────────────────────────────────────────
async function loadPositions() {
  state.positions = await api('/api/positions');
  const codes = Object.keys(state.positions);
  const f = (code, k, label, type = 'text', ph = '') => `<div><label for="p-${code}-${k}" class="block text-sm mb-1">${label}</label>
    <input id="p-${code}-${k}" type="${type}" step="any" value="${esc(state.positions[code]?.[k] ?? '')}" placeholder="${esc(ph)}" class="w-full border rounded px-2 py-2"></div>`;
  const form = code => {
    const p = state.positions[code];
    return `<div class="bg-white rounded-lg shadow-sm p-5" data-code="${code}">
      <h2 class="font-semibold mb-3">${esc(p.name)}（${code}）</h2>
      <div class="grid grid-cols-4 gap-3 mb-3">
        ${f(code, 'first_buy_price', '首次买入价（止损基准）', 'number')}${f(code, 'first_buy_date', '首次买入日期', 'date')}
        ${f(code, 'capital', '这只股票的总资金（元）', 'number', '按规则每只 10000')}${f(code, 'name', '名称')}</div>
      <label for="p-${code}-thesis" class="block text-sm mb-1">持股逻辑（为什么买）</label>
      <textarea id="p-${code}-thesis" rows="2" class="w-full border rounded p-2 mb-3">${esc(p.thesis)}</textarea>
      <label for="p-${code}-invalidation" class="block text-sm mb-1">证伪条件（出现什么说明买错了）</label>
      <textarea id="p-${code}-invalidation" rows="2" class="w-full border rounded p-2 mb-3">${esc(p.invalidation)}</textarea>
      <div class="text-sm font-medium mb-1">成交记录（含做T的每一笔）</div>
      <table class="w-full text-sm mb-2"><thead><tr class="text-left text-slate-500"><th>日期</th><th>方向</th><th>价格</th><th>股数</th><th>备注</th><th></th></tr></thead>
        <tbody class="trades">${(p.trades || []).map(tradeRow).join('')}</tbody></table>
      <div class="flex gap-2"><button class="btn-add-trade border px-3 py-1 rounded"><i class="fa fa-plus"></i> 加一笔</button>
        <button class="btn-save-pos bg-slate-800 text-white px-4 py-1 rounded ml-auto">保存</button></div></div>`;
  };
  $('#pos-forms').innerHTML = codes.map(form).join('') + (codes.length < state.meta.max_stocks ? `
    <div class="bg-white rounded-lg shadow-sm p-5 flex gap-2 items-end"><div><label for="new-code" class="block text-sm mb-1">新增持仓代码</label>
      <input id="new-code" class="border rounded px-2 py-2" placeholder="如 600690"></div>
      <div><label for="new-name" class="block text-sm mb-1">名称</label><input id="new-name" class="border rounded px-2 py-2"></div>
      <button id="btn-new-pos" class="border px-4 py-2 rounded">添加</button>
      <span class="text-sm text-slate-400 ml-2">铁律：最多 ${state.meta.max_stocks} 只（当前 ${codes.length} 只）</span></div>` : '');
  document.querySelectorAll('.btn-add-trade').forEach(b => b.onclick = () => b.closest('[data-code]').querySelector('.trades').insertAdjacentHTML('beforeend', tradeRow({})));
  document.querySelectorAll('.btn-save-pos').forEach(b => b.onclick = () => busy(b, async () => {
    const box = b.closest('[data-code]'), code = box.dataset.code, v = k => $(`#p-${code}-${k}`).value;
    const trades = [...box.querySelectorAll('.trades tr')].map(tr => {
      const [date, side, price, shares, note] = [...tr.querySelectorAll('input,select')].map(i => i.value);
      return { date, side, price, shares, note };
    }).filter(t => t.price && t.shares);
    await api(`/api/positions/${code}`, { name: v('name'), first_buy_price: v('first_buy_price'), first_buy_date: v('first_buy_date'),
      capital: v('capital'), thesis: v('thesis'), invalidation: v('invalidation'), trades });
    toast('已保存。去"每日跟盘"点刷新行情，止损价会重新计算'); loadPositions();
  }));
  const nb = $('#btn-new-pos');
  if (nb) nb.onclick = () => busy(nb, async () => {
    await api(`/api/positions/${$('#new-code').value.trim()}`, { name: $('#new-name').value.trim() });
    loadPositions();
  });
}

document.addEventListener('click', e => { const b = e.target.closest('.btn-del-trade'); if (b) b.closest('tr').remove(); });

function tradeRow(t) {
  return `<tr><td><input type="date" value="${esc(t.date)}" class="border rounded px-1" aria-label="日期"></td>
    <td><select class="border rounded px-1" aria-label="方向"><option value="buy" ${t.side !== 'sell' ? 'selected' : ''}>买</option><option value="sell" ${t.side === 'sell' ? 'selected' : ''}>卖</option></select></td>
    <td><input type="number" step="any" value="${esc(t.price)}" class="border rounded px-1 w-24" aria-label="价格"></td>
    <td><input type="number" step="100" value="${esc(t.shares)}" class="border rounded px-1 w-24" aria-label="股数"></td>
    <td><input value="${esc(t.note)}" class="border rounded px-1 w-full" placeholder="底仓/正T/倒T/加仓" aria-label="备注"></td>
    <td><button class="btn-del-trade text-red-500 px-2" aria-label="删除这笔"><i class="fa fa-trash"></i></button></td></tr>`;
}

// ─── 手机同步 ───────────────────────────────────────────
async function loadMobile() {
  let m;
  try { m = await api('/api/mobile'); }
  catch (e) { $('#mobile-body').innerHTML = `<div class="bg-red-50 text-red-700 rounded p-4 text-sm">加载失败：${esc(e.message)}${e.message.includes('404') ? '<br>后台还是旧版本：关掉黑窗口，重新双击 启动界面.bat。' : ''}</div>`; return; }
  mobileDot(m.pending.length);
  const name = c => state.positions[c]?.name || c;
  const run = m.running
    ? `<div class="text-green-700"><span class="text-green-500">●</span> 运行中（${esc(m.started)} 启动）</div>
       <div class="mt-2">手机 Safari 打开：${m.urls.map(u => `<code class="bg-slate-100 px-2 py-0.5 rounded">${esc(u)}</code>`).join(' 或 ')}</div>`
    : `<div class="text-red-600"><span>●</span> 没有启动：${esc(m.error || '未知原因')}</div>`;
  $('#mobile-body').innerHTML = card('同步服务', `<div class="text-sm space-y-1">${run}
      <div class="text-slate-500">证书用时间管理助手的 CA 签发（${m.ca_ok ? '已找到' : '<span class="text-red-600">没找到</span>'}：${esc(m.ca_dir)}），iPhone 已信任过这个 CA 就不用再装。
      第一次连要在 Windows 防火墙放行 TCP ${m.port}（专用网络）。</div></div>`) +
    card(`已配对的手机（${m.devices.length} / 3）`, `<div class="text-sm">${m.devices.map(d => `<div class="flex items-center gap-3 border-t py-2">
        <i class="fa fa-mobile text-xl"></i><div class="flex-1"><b>${esc(d.name)}</b><div class="text-xs text-slate-400">配对于 ${esc(d.paired)} · 上次同步 ${esc(d.last_sync || '从未')}</div></div>
        <button class="btn-revoke text-red-600 hover:underline" data-id="${esc(d.id)}">解绑</button></div>`).join('') || '<p class="text-slate-500">还没有。</p>'}
      <div class="flex items-center gap-3 mt-3"><button id="btn-pair-code" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded" ${m.running ? '' : 'disabled'}>生成配对码</button>
      <div id="pair-code" class="text-3xl font-mono tracking-widest"></div></div>
      <p class="text-xs text-slate-400 mt-2">配对码 5 分钟有效、只能用一次，输错 5 次作废。手机丢了就在这里解绑。</p></div>`) +
    card(`待确认的成交（${m.pending.length}）`, m.pending.map(t => `<div class="flex items-center gap-3 border-t py-2 text-sm">
        <div class="flex-1">${esc(t.date)} <b>${esc(name(t.code))}</b> ${t.side === 'buy' ? '<b class="up">买</b>' : '<b class="down">卖</b>'} ${esc(t.price)} × ${esc(t.shares)} 股
        <span class="text-slate-500">${esc(t.note)}</span><div class="text-xs text-slate-400">来自 ${esc(t.device)}，收到于 ${esc(t.received)}</div></div>
        <button class="btn-trade bg-slate-800 text-white px-3 py-1 rounded" data-id="${esc(t.id)}" data-ok="1">确认写入持仓</button>
        <button class="btn-trade border px-3 py-1 rounded" data-id="${esc(t.id)}" data-ok="">拒绝</button></div>`).join('')
      || '<p class="text-sm text-slate-500">没有。</p>') +
    card('同步记录', `<ul class="text-sm text-slate-600 space-y-1">${m.log.map(l => `<li><span class="text-slate-400">${esc(l.time)}</span> ${esc(l.device)}：${esc(l.note)}</li>`).join('') || '<li class="text-slate-500">还没有</li>'}</ul>`);
  const pb = $('#btn-pair-code');
  pb.onclick = () => busy(pb, async () => { const r = await api('/api/mobile/pair', {}); $('#pair-code').textContent = r.code; });
  document.querySelectorAll('.btn-revoke').forEach(b => b.onclick = () => {
    if (!confirm('解绑这台手机？它上面没上传的内容需要重新配对后才能传。')) return;
    busy(b, async () => { await api(`/api/mobile/devices/${b.dataset.id}/revoke`, {}); toast('已解绑'); loadMobile(); });
  });
  document.querySelectorAll('.btn-trade').forEach(b => b.onclick = () => busy(b, async () => {
    await api(`/api/mobile/trades/${b.dataset.id}`, { confirm: !!b.dataset.ok });
    toast(b.dataset.ok ? '已写入持仓。去"每日跟盘"刷新行情，盈亏会重新计算' : '已拒绝'); loadMobile();
  }));
}

function mobileDot(n) {
  const d = $('#mobile-dot');
  d.textContent = n; d.classList.toggle('hidden', !n);
}

// ─── 启动 ──────────────────────────────────────────────
(async () => {
  state.meta = await api('/api/meta');
  const ai = state.meta.ai;
  $('#ai-status').innerHTML = ai.configured ? `<span class="text-green-400">●</span> AI：${esc(ai.model)}` : '<span class="text-red-400">●</span> AI 未配置';
  show(location.hash.slice(1) || 'journal');
  // 侧栏提示手机同步过来的待确认成交
  const poll = () => api('/api/mobile').then(m => mobileDot(m.pending.length)).catch(() => {});
  poll(); setInterval(poll, 60000);
})();
