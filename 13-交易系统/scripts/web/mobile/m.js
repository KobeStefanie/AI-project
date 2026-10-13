// 手机端：离线写复盘 → 本地队列（localStorage）→ 联网后推送到电脑 → 再拉最新数据
// 冲突：按字段比较修改时间，新的覆盖旧的（电脑 data/journal 里每个字段带 _meta.ts）
// 所有文本经 esc() 转义后插入，不执行任何 HTML
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const LS = { token: 'tj_token', data: 'tj_data', queue: 'tj_queue', offset: 'tj_offset', lastSync: 'tj_last_sync', dev: 'tj_dev' };
const load = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
const save = (k, v) => localStorage.setItem(k, JSON.stringify(v));
const ui = { tab: 'journal', code: null, date: null, syncing: false };
const today = () => { const d = new Date(); return new Date(d - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10); };
// 用电脑时间打时间戳：手机时钟偏了也不会让旧内容"变新"（上次拉取时记下的偏差）
const stamp = () => Date.now() + (load(LS.offset, 0) || 0);

function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.style.display = 'block';
  clearTimeout(t._h); t._h = setTimeout(() => t.style.display = 'none', 3000);
}

// ─── 队列 ──────────────────────────────────────────────
// { journal: {"代码|日期|字段": {code,date,field,value,ts}}, watch: {"代码|字段": {...}}, trades: [{id,...}] }
function queue() { return load(LS.queue, { journal: {}, watch: {}, trades: [] }); }
function queueCount(q = queue()) { return Object.keys(q.journal).length + Object.keys(q.watch).length + q.trades.length; }
function enqueue(kind, key, item) { const q = queue(); q[kind][key] = { ...item, ts: stamp() }; save(LS.queue, q); badge(); syncSoon(); }

// 页面上看到的 = 电脑数据 + 还没上传的本地修改
function jv(code, date, field) {
  const q = queue().journal[`${code}|${date}|${field}`];
  if (q) return q.value;
  const s = load(LS.data, null)?.stocks.find(x => x.code === code);
  return s?.journal?.[date]?.[field];
}
function wv(code, field) {
  const q = queue().watch[`${code}|${field}`];
  return q ? q.value : load(LS.data, null)?.watch.find(x => x.code === code)?.[field];
}

// ─── 同步 ──────────────────────────────────────────────
async function api(path, body) {
  const ctl = new AbortController(); const h = setTimeout(() => ctl.abort(), 15000);
  try {
    const r = await fetch(path, { method: body ? 'POST' : 'GET', signal: ctl.signal, cache: 'no-store',
      headers: { 'Content-Type': 'application/json', 'X-Token': load(LS.token, '') }, body: body ? JSON.stringify(body) : undefined });
    const d = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
    if (r.status === 401 && d.unpaired) { localStorage.removeItem(LS.token); throw new Error(d.error); }
    if (!r.ok) throw new Error(d.error || `HTTP ${r.status}`);
    return d;
  } catch (e) {
    throw new Error(e.name === 'AbortError' ? '连不上电脑（超时）' : e.message === 'Failed to fetch' || e.message === 'Load failed' ? '连不上电脑（离线或不在同一 Wi-Fi）' : e.message);
  } finally { clearTimeout(h); }
}

let _soon;
function syncSoon() { clearTimeout(_soon); _soon = setTimeout(() => sync(true), 2500); }

async function sync(quiet = false) {
  if (ui.syncing || !load(LS.token, '')) { badge(); return; }
  ui.syncing = true; badge();
  try {
    const q = queue();
    if (queueCount(q)) {
      const sent = { journal: Object.values(q.journal), watch: Object.values(q.watch), trades: q.trades };
      const res = await api('/m/api/push', sent);
      // 只移除推送时那一版；推送期间又改过的（ts 变了）留着下次再推
      const now = queue(), bad = [];
      for (const r of res.journal) { const it = q.journal[r.key]; if (now.journal[r.key]?.ts === it?.ts) delete now.journal[r.key]; if (!r.ok) bad.push(r.why); else if (r.skipped) bad.push(r.skipped); }
      for (const r of res.watch) { const it = q.watch[r.key]; if (now.watch[r.key]?.ts === it?.ts) delete now.watch[r.key]; if (!r.ok) bad.push(r.why); else if (r.skipped) bad.push(r.skipped); }
      const done = new Set(res.trades.map(r => r.id));
      res.trades.filter(r => !r.ok).forEach(r => bad.push('成交：' + r.why));
      now.trades = now.trades.filter(t => !done.has(t.id));
      save(LS.queue, now);
      if (bad.length) toast([...new Set(bad)].join('；'));
    }
    const t0 = Date.now(), d = await api('/m/api/pull');
    save(LS.offset, d.server_time - Math.round((t0 + Date.now()) / 2));
    save(LS.data, d); save(LS.lastSync, new Date().toLocaleString());
    if (!quiet) toast('已同步');
    render();
  } catch (e) {
    if (!quiet) toast(e.message);
    ui.lastError = e.message;
  } finally { ui.syncing = false; badge(); }
}

function badge() {
  const b = $('#sync-badge'), n = queueCount();
  if (!load(LS.token, '')) { b.className = 'err'; b.textContent = '未配对'; return; }
  if (ui.syncing) { b.className = 'wait'; b.textContent = '同步中…'; return; }
  if (n) { b.className = 'wait'; b.textContent = `${n} 项待上传`; return; }
  b.className = 'ok'; b.textContent = '已同步';
}
// ─── 页面 ──────────────────────────────────────────────
function render() {
  document.querySelectorAll('nav button').forEach(b => b.classList.toggle('on', b.dataset.tab === ui.tab));
  const d = load(LS.data, null);
  if (!load(LS.token, '') && ui.tab !== 'setup') ui.tab = 'setup';
  if (ui.tab !== 'setup' && !d) { $('#main').innerHTML = '<div class="card">还没从电脑拉过数据。连上同一 Wi-Fi 后点"同步"页的"立即同步"。</div>'; return; }
  ({ journal: renderJournal, trades: renderTrades, watch: renderWatch, setup: renderSetup })[ui.tab](d);
}

function stockPicker(d) {
  if (!ui.code || !d.stocks.some(s => s.code === ui.code)) ui.code = d.stocks[0]?.code;
  return `<label for="m-code">股票</label><select id="m-code">${d.stocks.map(s =>
    `<option value="${esc(s.code)}" ${s.code === ui.code ? 'selected' : ''}>${esc(s.name)}（${esc(s.code)}）</option>`).join('')}</select>`;
}

function renderJournal(d) {
  if (!d.stocks.length) { $('#main').innerHTML = '<div class="card">电脑上还没有持仓。</div>'; return; }
  const s = d.stocks.find(x => x.code === ui.code) || d.stocks[0]; ui.code = s.code;
  const dates = [...new Set([today(), ...Object.keys(s.journal)])].sort().reverse();
  if (!ui.date || !dates.includes(ui.date)) ui.date = dates[0];
  const v = f => jv(s.code, ui.date, f) ?? '';
  const checks = v('checks') || {};
  const ai = s.journal[ui.date]?.ai_comment;
  const last = s.last;
  $('#main').innerHTML = `<div class="card">${stockPicker(d)}
      <label for="m-date">日期</label><select id="m-date">${dates.map(x => `<option ${x === ui.date ? 'selected' : ''}>${x}</option>`).join('')}</select>
      <div class="muted" style="margin-top:8px">${last ? `电脑最近行情 ${esc(last.date)}：<b class="${last.chg_pct >= 0 ? 'up' : 'down'}">${esc(last.price)}（${last.chg_pct > 0 ? '+' : ''}${esc(last.chg_pct)}%）</b>，抓取于 ${esc(last.fetched)}<br>` : '电脑还没刷新过行情<br>'}
      ${s.stop ? `止损 ${esc(s.stop)}　预警 ${esc((s.warns || []).join(' / '))}　持股 ${esc(s.shares ?? '—')} 股` : ''}<br>
      手机上看到的行情不是实时的，以券商 App 为准。</div></div>
    <div class="card"><h2>我的想法与操作</h2>
      <label for="f-thoughts">我的想法（怎么想就怎么写）</label><textarea id="f-thoughts">${esc(v('thoughts'))}</textarea>
      <label for="f-operations">今日操作（没操作写"无"）</label><textarea id="f-operations" style="min-height:60px">${esc(v('operations'))}</textarea></div>
    <div class="card"><h2>今日复盘</h2>
      <div class="muted">持股逻辑：${esc(s.thesis || '未录入')}<br>证伪条件：${esc(s.invalidation || '未录入')}</div>
      ${d.checks.map((c, i) => `<label class="chk"><input type="checkbox" id="chk${i}" ${checks[c] ? 'checked' : ''}> ${esc(c)}</label>`).join('')}
      <label for="f-did_right">做对了什么</label><textarea id="f-did_right" style="min-height:60px">${esc(v('did_right'))}</textarea>
      <label for="f-improve">要改什么</label><textarea id="f-improve" style="min-height:60px">${esc(v('improve'))}</textarea>
      <button class="btn" id="btn-save">保存（离线也能存）</button>
      <p class="muted">保存后先存在手机里，连上电脑自动上传。Claude 点评在电脑上点。</p></div>
    <div class="card"><h2>Claude 点评</h2>${ai ? `<div class="ai">${esc(ai)}</div>` : '<p class="muted">还没有。回到电脑上点"让 Claude 点评"。</p>'}</div>`;
  $('#m-code').onchange = e => { ui.code = e.target.value; ui.date = null; render(); };
  $('#m-date').onchange = e => { ui.date = e.target.value; render(); };
  $('#btn-save').onclick = () => {
    const before = f => jv(s.code, ui.date, f) ?? (f === 'checks' ? {} : '');
    let n = 0;
    for (const f of ['thoughts', 'operations', 'did_right', 'improve']) {
      const val = $(`#f-${f}`).value;
      if (val !== before(f)) { enqueue('journal', `${s.code}|${ui.date}|${f}`, { code: s.code, date: ui.date, field: f, value: val }); n++; }
    }
    const ck = {}; d.checks.forEach((c, i) => ck[c] = $(`#chk${i}`).checked);
    const old = before('checks') || {};
    if (d.checks.some(c => !!old[c] !== ck[c])) { enqueue('journal', `${s.code}|${ui.date}|checks`, { code: s.code, date: ui.date, field: 'checks', value: ck }); n++; }
    toast(n ? `已保存 ${n} 项，${navigator.onLine ? '正在上传' : '离线，联网后上传'}` : '没有改动');
  };
}

function renderTrades(d) {
  if (!d.stocks.length) { $('#main').innerHTML = '<div class="card">电脑上还没有持仓。</div>'; return; }
  const q = queue().trades;
  const st = { pending: ['待电脑确认', 'wait'], confirmed: ['已写入持仓', 'ok'], rejected: ['电脑已拒绝', 'no'] };
  const name = c => d.stocks.find(s => s.code === c)?.name || c;
  const row = (t, s) => `<div style="border-top:1px solid #e2e8f0;padding:8px 0;font-size:15px">${esc(t.date)} ${esc(name(t.code))}
    ${t.side === 'buy' ? '<b class="up">买</b>' : '<b class="down">卖</b>'} ${esc(t.price)} × ${esc(t.shares)} 股
    <span class="tag ${s[1]}">${s[0]}</span>${t.note ? `<div class="muted">${esc(t.note)}</div>` : ''}</div>`;
  $('#main').innerHTML = `<div class="card"><h2>记一笔成交</h2>${stockPicker(d)}
      <div class="row"><div><label for="t-date">日期</label><input id="t-date" type="date" value="${today()}"></div>
        <div><label for="t-side">方向</label><select id="t-side"><option value="buy">买</option><option value="sell">卖</option></select></div></div>
      <div class="row"><div><label for="t-price">价格</label><input id="t-price" type="number" inputmode="decimal" step="any"></div>
        <div><label for="t-shares">股数</label><input id="t-shares" type="number" inputmode="numeric" step="100" value="100"></div></div>
      <label for="t-note">备注</label><select id="t-note"><option>正T</option><option>倒T</option><option>加仓</option><option>底仓</option><option>止损</option><option>其他</option></select>
      <button class="btn" id="btn-trade">记下（离线也能记）</button>
      <p class="muted">手机记的成交不会直接改持仓：同步后在电脑"手机同步"页确认才写入，防止误录改了止损基准。</p></div>
    <div class="card"><h2>记录</h2>${q.map(t => row(t, ['待上传', 'wait'])).join('')}${d.trades.map(t => row(t, st[t.status] || ['', ''])).join('') || (q.length ? '' : '<p class="muted">还没有</p>')}</div>`;
  $('#m-code').onchange = e => { ui.code = e.target.value; };
  $('#btn-trade').onclick = () => {
    const price = parseFloat($('#t-price').value), shares = parseInt($('#t-shares').value, 10);
    if (!(price > 0) || !(shares > 0)) { toast('价格和股数要大于 0'); return; }
    const t = { id: 'm' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8), code: $('#m-code').value, date: $('#t-date').value,
      side: $('#t-side').value, price, shares, note: $('#t-note').value };
    const qq = queue(); qq.trades.push(t); save(LS.queue, qq); badge(); syncSoon();
    toast('已记下'); render();
  };
}

function renderWatch(d) {
  $('#main').innerHTML = (d.watch.map(w => `<div class="card" data-code="${esc(w.code)}"><h2>${esc(w.name || w.code)}（${esc(w.code)}）</h2>
      <label for="w-${esc(w.code)}-reason">为什么关注</label><textarea id="w-${esc(w.code)}-reason">${esc(wv(w.code, 'reason'))}</textarea>
      <label for="w-${esc(w.code)}-buy_condition">买入条件</label><textarea id="w-${esc(w.code)}-buy_condition">${esc(wv(w.code, 'buy_condition'))}</textarea>
      <button class="btn btn-w">保存</button></div>`).join('') || '<div class="card">候选池是空的。加股票、移出股票在电脑上做。</div>') +
    '<p class="muted">手机上只能补写理由和条件；加入、移出候选池在电脑上做。</p>';
  document.querySelectorAll('.btn-w').forEach(b => b.onclick = () => {
    const code = b.closest('[data-code]').dataset.code; let n = 0;
    for (const f of ['reason', 'buy_condition']) {
      const val = $(`#w-${code}-${f}`).value;
      if (val !== (wv(code, f) ?? '')) { enqueue('watch', `${code}|${f}`, { code, field: f, value: val }); n++; }
    }
    toast(n ? '已保存' : '没有改动');
  });
}

function renderSetup() {
  const paired = !!load(LS.token, '');
  $('#main').innerHTML = `<div class="card"><h2>${paired ? '已配对' : '和电脑配对'}</h2>
    ${paired ? `<p class="muted">设备名：${esc(load(LS.dev, '手机'))}<br>上次同步：${esc(load(LS.lastSync, '从未'))}<br>待上传：${queueCount()} 项
      ${ui.lastError ? `<br>上次失败原因：${esc(ui.lastError)}` : ''}</p>
      <button class="btn" id="btn-sync">立即同步</button>
      <button class="btn red" id="btn-unpair">解除配对（待上传的内容会保留）</button>`
    : `<p class="muted">在电脑界面打开"手机同步"页，点"生成配对码"，5 分钟内在这里输入。</p>
      <label for="p-code">配对码（6 位数字）</label><input id="p-code" inputmode="numeric" maxlength="6" autocomplete="one-time-code">
      <label for="p-name">这台手机叫什么</label><input id="p-name" value="${esc(load(LS.dev, '我的手机'))}" maxlength="20">
      <button class="btn" id="btn-pair">配对</button>`}</div>
    <div class="card"><h2>怎么用</h2><p class="muted">1. 用 Safari 打开本页，点分享 →"添加到主屏幕"<br>2. 没网时照常写复盘、记成交，内容存在手机里<br>
      3. 回到和电脑同一个 Wi-Fi，打开本页会自动上传（右上角显示"已同步"）<br>4. 回电脑上看复盘、点 Claude 点评、确认成交<br>
      电脑界面要开着（双击 启动界面.bat），手机才能同步。<br>⚠️ 别清 Safari 的网站数据，没上传的内容会丢。</p></div>`;
  if (paired) {
    $('#btn-sync').onclick = () => sync(false);
    $('#btn-unpair').onclick = () => { if (confirm('解除配对？待上传内容会保留，重新配对后继续上传。')) { localStorage.removeItem(LS.token); render(); badge(); } };
  } else {
    $('#btn-pair').onclick = async () => {
      try {
        const name = $('#p-name').value.trim() || '手机';
        const r = await api('/m/api/pair', { code: $('#p-code').value.trim(), name });
        save(LS.token, r.token); save(LS.dev, name); toast('配对成功'); ui.tab = 'journal'; await sync(false);
      } catch (e) { toast(e.message); }
      badge();
    };
  }
}

document.querySelectorAll('nav button').forEach(b => b.onclick = () => { ui.tab = b.dataset.tab; render(); });
window.addEventListener('online', () => sync(true));
document.addEventListener('visibilitychange', () => { if (!document.hidden) sync(true); });
setInterval(() => { if (queueCount() && navigator.onLine) sync(true); }, 60000);
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(e => console.warn('SW 注册失败', e));
render(); badge(); sync(true);
