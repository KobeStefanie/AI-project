(function() {
'use strict';

// ===== 共享核心层引用 =====
// 核心常量与逻辑已抽到 app-core.js (window.AppCore)。本文件仅保留 UI/事件绑定。
if (!window.AppCore) {
  console.error('[app.js] window.AppCore 未加载，请确保 app-core.js 在 app.js 之前引入');
  return;
}
var STORAGE_PREFIX = AppCore.STORAGE_PREFIX;
var WEEKDAYS = AppCore.WEEKDAYS;
var KEY_ROWS = AppCore.KEY_ROWS;
var TIME_SLOTS = AppCore.TIME_SLOTS;
var buildTimeSlots = AppCore.buildTimeSlots;
// 当前周的 34 时段字符串数组（每次 renderAll/doExport 前根据本周配置重算）
function refreshTimeSlots() {
  var cfg = getConfig(state.year, state.week);
  TIME_SLOTS = buildTimeSlots(cfg.startTime || '7:00');
}
var DEFAULT_CONFIG = AppCore.DEFAULT_CONFIG;
var getISOWeek = AppCore.getISOWeek;
var getWeekDates = AppCore.getWeekDates;
var formatDate = AppCore.formatDate;
var dateKey = AppCore.dateKey;
var getPrevWeek = AppCore.getPrevWeek;
var getNextWeek = AppCore.getNextWeek;
var sKey = AppCore.sKey;
var getConfig = AppCore.getConfig;
var saveConfig = AppCore.saveConfig;
var getCells = AppCore.getCells;
var saveCells = AppCore.saveCells;
var getKeyItems = AppCore.getKeyItems;
var saveKeyItems = AppCore.saveKeyItems;
var getKeyItemStatus = AppCore.getKeyItemStatus;
var saveKeyItemStatus = AppCore.saveKeyItemStatus;
var KEY_ITEM_STATUS_ROWS = AppCore.KEY_ITEM_STATUS_ROWS;
var KEY_ITEM_STATUS_VALUES = AppCore.KEY_ITEM_STATUS_VALUES;
var getReview = AppCore.getReview;
var saveReview = AppCore.saveReview;
var isArchived = AppCore.isArchived;
var setArchived = AppCore.setArchived;
var getCatClass = AppCore.getCatClass;
var calcDailyStats = AppCore.calcDailyStats;
var calcWeeklyStats = AppCore.calcWeeklyStats;
var exportAllData = AppCore.exportAllData;
var summarizeImport = AppCore.summarizeImport;
var importAllData = AppCore.importAllData;

// ===== DOM =====
var $ = function(id) { return document.getElementById(id); };
var now = new Date();
var today = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
var state = getISOWeek(now);
// v2.13.1：桌面端视图模式（'week' | 'month'）与月历 state
var desktopView = 'week';
var monthState = { year: now.getUTCFullYear(), month: now.getUTCMonth() + 1 }; // 1-12
var frozen = false;

function applyFreeze() {
  document.body.classList.add('frozen');
  // 计算 sticky top 值
  var toolbarH = document.querySelector('.toolbar').offsetHeight;
  var hintH = document.querySelector('.grid-hint').offsetHeight;
  var theadH = document.querySelector('#main-table thead').offsetHeight;
  var t = toolbarH + hintH;
  // thead 冻结在 toolbar + hint 下方
  var ths = document.querySelectorAll('#main-table thead th');
  for (var i = 0; i < ths.length; i++) { ths[i].style.top = t + 'px'; }
  // 关键事项行逐行累加
  var rows = document.querySelectorAll('#main-table tbody .row-keyitem');
  t += theadH;
  for (var j = 0; j < rows.length; j++) {
    var cells = rows[j].querySelectorAll('td');
    for (var k = 0; k < cells.length; k++) { cells[k].style.top = t + 'px'; }
    t += rows[j].offsetHeight;
  }
}

function removeFreeze() {
  document.body.classList.remove('frozen');
  var all = document.querySelectorAll('#main-table thead th, #main-table tbody .row-keyitem td');
  for (var i = 0; i < all.length; i++) { all[i].style.top = ''; }
}

// ===== Modal 开关 =====
function openModal(id) { $(id).classList.add('active'); }
function closeModal(id) { $(id).classList.remove('active'); }

// 点击遮罩关闭
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});

// ===== 初始化 =====
function init() {
  $('btn-prev-week').onclick = function() {
    if (desktopView === 'month') {
      if (monthState.month > 1) monthState.month--;
      else { monthState.year--; monthState.month = 12; }
    } else {
      state = getPrevWeek(state.year, state.week);
    }
    renderAll();
  };
  $('btn-next-week').onclick = function() {
    if (desktopView === 'month') {
      if (monthState.month < 12) monthState.month++;
      else { monthState.year++; monthState.month = 1; }
    } else {
      state = getNextWeek(state.year, state.week);
    }
    renderAll();
  };
  $('btn-today').onclick = function() {
    if (desktopView === 'month') {
      monthState = { year: today.getUTCFullYear(), month: today.getUTCMonth() + 1 };
    }
    state = getISOWeek(today);
    renderAll();
  };
  $('btn-config').onclick = function() { showPage('page-config'); };
  $('btn-refresh').onclick = function() { forceUpdateSW(); };
  $('btn-freeze').onclick = function() {
    frozen = !frozen;
    $('btn-freeze').textContent = frozen ? '📌 已冻结' : '📌 冻结';
    if (frozen) applyFreeze(); else removeFreeze();
  };
  $('btn-back').onclick = function() {
    if (!tryLeaveConfig()) return;
    showPage('page-main');
    renderAll();
  };
  $('btn-archive').onclick = handleArchive;
  $('btn-export').onclick = handleExport;
  $('btn-export-data').onclick = handleExportData;
  $('btn-import-data').onclick = handleImportClick;
  $('inp-import-file').onchange = handleImportFileChosen;
  $('btn-save-all').onclick = handleSaveAll;
  $('btn-save-config').onclick = handleSaveConfig;
  $('btn-save-cell').onclick = function() { saveCellAndAdvance(0); };
  $('btn-clear-cell').onclick = clearCell;
  $('btn-cancel-cell').onclick = function() { closeModal('cell-modal'); };
  $('btn-copy-cell').onclick = copyCellFromModal;
  $('btn-paste-cell').onclick = pasteCellFromModal;
  $('btn-save-ki').onclick = saveKeyItem;
  $('btn-clear-ki').onclick = clearKeyItem;
  $('btn-cancel-ki').onclick = function() { closeModal('ki-modal'); };

  // 视图模式：检测 + 应用（不写 LocalStorage，避免污染用户偏好）
  setupViewModeUI();
  var mode = detectViewMode();
  setViewMode(mode, { persist: false });

  // v2.10.0 同步 UI（在 SW 注册前先就位，让自动重载之后状态灯能立即正确）
  setupSyncUI();

  // v2.13.1 workaround: iOS 书签在有 SW 时隔离 localStorage；?nosw 跳过 SW 注册
  var nosw = (window.location.search || '').indexOf('nosw') >= 0;
  if (nosw && 'serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(function(regs) {
      return Promise.all(regs.map(function(r) { return r.unregister(); }));
    }).then(function() {
      window.location.search = ''; // 去掉 ?nosw 并重载
    });
    return; // 等待重载
  }

  registerServiceWorker();
}

// SW 注册 + 自动更新流：检测到新版本即让其立即激活，并在 controllerchange 时重载一次。
// 首次安装（页面此前没有 controller）不触发 reload，避免空载场景下的循环刷新。
// v2.11.2：新增 EXPECTED_CACHE_NAME 自检，若当前 SW 版本落后则强制注销+重载。
var EXPECTED_CACHE_NAME = 'time-planner-v85';

function forceUpdateSW() {
  if (!('serviceWorker' in navigator)) return;
  // 注销所有旧 SW，然后硬重载页面
  navigator.serviceWorker.getRegistrations().then(function(regs) {
    return Promise.all(regs.map(function(r) { return r.unregister(); }));
  }).then(function() {
    if (typeof console !== 'undefined') console.log('[sw] 旧 SW 已注销，即将重载');
    window.location.reload();
  }).catch(function() {
    window.location.reload(); // 兜底
  });
}

function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;
  var hadControllerAtStart = !!navigator.serviceWorker.controller;
  var hasReloaded = false;
  navigator.serviceWorker.addEventListener('controllerchange', function() {
    if (!hadControllerAtStart) return;
    if (hasReloaded) return;
    hasReloaded = true;
    window.location.reload();
  });
  navigator.serviceWorker.register('./service-worker.js').then(function(reg) {
    try { reg.update(); } catch (e) {}
    if (reg.waiting && navigator.serviceWorker.controller) {
      try { reg.waiting.postMessage({ type: 'SKIP_WAITING' }); } catch (e) {}
    }
    reg.addEventListener('updatefound', function() {
      var nw = reg.installing;
      if (!nw) return;
      nw.addEventListener('statechange', function() {
        if (nw.state === 'installed' && navigator.serviceWorker.controller) {
          try { nw.postMessage({ type: 'SKIP_WAITING' }); } catch (e) {}
        }
      });
    });
    // v2.11.2：SW 版本自检——若当前控制的 SW 缓存名与期望不符，3s 后强制更新
    setTimeout(function() {
      if (!('caches' in window)) return;
      var ctrl = navigator.serviceWorker.controller;
      if (!ctrl) return; // 没有控制中的 SW，首次安装，跳过
      caches.keys().then(function(keys) {
        var found = keys.some(function(k) { return k === EXPECTED_CACHE_NAME; });
        if (!found && keys.length > 0) {
          if (typeof console !== 'undefined') console.warn(
            '[sw] 版本自检失败：期望 ' + EXPECTED_CACHE_NAME + '，当前 ' + keys.join(',') + '。强制更新。'
          );
          forceUpdateSW();
        }
      }).catch(function() {});
    }, 3000);
  }).catch(function(){});

  // v2.11.0 临时诊断：右下角实时显示 SW 状态 + 缓存项数
  // 让 iPhone PWA 离线启动失败时一眼看出是哪一环。
  try { mountSwDiagBadge(); } catch (e) {}
}

function mountSwDiagBadge() {
  if (document.getElementById('sw-diag')) return;
  var d = document.createElement('div');
  d.id = 'sw-diag';
  d.style.cssText = 'position:fixed;right:6px;bottom:6px;z-index:99999;'
    + 'font:11px/1.4 -apple-system,sans-serif;color:#666;'
    + 'background:rgba(255,255,255,.85);padding:4px 7px;border-radius:6px;'
    + 'box-shadow:0 1px 3px rgba(0,0,0,.15);max-width:60vw;'
    + 'opacity:.65;pointer-events:auto;cursor:pointer';
  d.textContent = 'SW: ...';
  d.title = '点击隐藏';
  d.onclick = function() { d.style.display = 'none'; };
  document.body.appendChild(d);
  function refresh() {
    var parts = [];
    var ctrl = navigator.serviceWorker && navigator.serviceWorker.controller;
    parts.push(ctrl ? 'SW✓' : 'SW✗');
    // v2.11.0：附加离线变更队列大小
    try {
      if (syncClient && syncClient.getPendingQueue) {
        var q = syncClient.getPendingQueue();
        if (q && q.length > 0) parts.push('queue:' + q.length);
      }
    } catch (e) {}
    if (window.caches && caches.keys) {
      caches.keys().then(function(keys) {
        var name = keys[0] || '?';
        if (!keys.length) {
          d.textContent = parts.join(' ') + ' cache:0';
          return;
        }
        caches.open(name).then(function(c) {
          c.keys().then(function(reqs) {
            d.textContent = parts.join(' ') + ' ' + name + ' (' + reqs.length + ')';
          });
        });
      });
    } else {
      d.textContent = parts.join(' ') + ' (no caches API)';
    }
  }
  refresh();
  setInterval(refresh, 2000);
}

// 在桌面端工具栏左侧追加「周表 / 月历」视图切换按钮 + 右侧「📱 手机版」
function setupViewModeUI() {
  // 视图切换按钮（周表 / 月历）
  var toolbarLeft = document.querySelector('#page-main .toolbar-left');
  if (toolbarLeft && !document.getElementById('btn-view-week')) {
    var btnWeek = document.createElement('button');
    btnWeek.id = 'btn-view-week';
    btnWeek.className = 'btn-ghost';
    btnWeek.textContent = '周表';
    btnWeek.title = '切换为周表视图';
    btnWeek.onclick = function() { desktopView = 'week'; renderAll(); };
    toolbarLeft.appendChild(btnWeek);

    var btnMonth = document.createElement('button');
    btnMonth.id = 'btn-view-month';
    btnMonth.className = 'btn-ghost';
    btnMonth.textContent = '月历';
    btnMonth.title = '切换为月历视图';
    btnMonth.onclick = function() { desktopView = 'month'; renderAll(); };
    toolbarLeft.appendChild(btnMonth);
  }
  // 手机版切换按钮
  var toolbarRight = document.querySelector('#page-main .toolbar-right');
  if (toolbarRight && !document.getElementById('btn-mobile-mode')) {
    var btn = document.createElement('button');
    btn.id = 'btn-mobile-mode';
    btn.className = 'btn-ghost';
    btn.title = '切换到手机版（iPhone / 安卓）';
    btn.textContent = '📱 手机版';
    btn.onclick = function() {
      var ua = navigator.userAgent || '';
      var target = /Huawei|HUAWEI|HONOR|Android/i.test(ua) ? 'huawei' : 'iphone';
      setViewMode(target);
    };
    toolbarRight.appendChild(btn);
  }
}

function showPage(id) {
  document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
  $(id).classList.add('active');
  if (id === 'page-config') renderConfig();
}

// 模块级当前周日期键，供选区计算使用
var currentDateKeys = [];

// ===== 渲染全部（dispatcher：根据 viewMode + 当前活动页 + 桌面视图选择渲染函数） =====
function renderAll() {
  if (viewMode === 'iphone' || viewMode === 'huawei') {
    // 移动端：根据当前活动的 mobile 页面调度
    var active = document.querySelector('.page-mobile.active');
    if (active && active.id === 'page-mobile-week') renderMobileWeek();
    else renderMobileDay();
    return;
  }
  // v2.13.1：桌面端周表 / 月历视图切换
  if (desktopView === 'month') {
    renderMonthCalendar();
    return;
  }
  renderDesktopAll();
}

// 清除因 startTime 变更等原因产生的过期 slot key 的 cell
function cleanStaleCells(year, week) {
  var cells = getCells(year, week);
  var changed = false;
  for (var ck in cells) {
    var cp = ck.split('|');
    if (cp.length === 2 && TIME_SLOTS.indexOf(cp[1]) < 0) {
      delete cells[ck];
      changed = true;
    }
  }
  if (changed) saveCells(year, week, cells);
  return changed;
}

// ===== 桌面端完整渲染 =====
function renderDesktopAll() {
  var year = state.year, week = state.week;
  $('week-title').textContent = year + '年第' + week + '周';
  refreshTimeSlots();      // 按本周配置重建 34 时段字符串
  var dates = getWeekDates(year, week);
  var dateKeys = dates.map(dateKey);
  currentDateKeys = dateKeys;
  var config = getConfig(year, week);
  var cells = getCells(year, week);
  var keyItems = getKeyItems(year, week);
  var kiStatus = getKeyItemStatus(year, week);

  // 清除因 startTime 变更等导致的过期 slot 数据
  cleanStaleCells(year, week);

  var cellsByDate = {};
  for (var i = 0; i < dateKeys.length; i++) cellsByDate[dateKeys[i]] = {};
  for (var id in cells) {
    var parts = id.split('|');
    if (cellsByDate[parts[0]] && TIME_SLOTS.indexOf(parts[1]) >= 0) cellsByDate[parts[0]][parts[1]] = cells[id];
  }

  var weekStats = calcWeeklyStats(cellsByDate, dateKeys, config.standard);
  renderThead(dates, dateKeys);
  renderTbody(dates, dateKeys, cellsByDate, keyItems, kiStatus, config, weekStats);
  renderLeftPanel(config, weekStats.totals);
  renderReviewPanel(year, week, weekStats.totals);
  updateArchiveBtn(weekStats);
  applySelectionStyles();
  if (frozen) applyFreeze();
}

// ===== Thead =====
function renderThead(dates, dateKeys) {
  var todayK = dateKey(today);
  var h = '<tr><th rowspan="2">' + state.year + '年第' + state.week + '周</th>';
  for (var i = 0; i < 7; i++) h += '<th colspan="2"' + (dateKeys[i] === todayK ? ' style="background:#bfdbfe"' : '') + '>' + WEEKDAYS[i] + '</th>';
  h += '<th rowspan="2">周合计</th></tr><tr>';
  for (var j = 0; j < 7; j++) h += '<th colspan="2"' + (dateKeys[j] === todayK ? ' style="background:#bfdbfe"' : '') + '>' + formatDate(dates[j]) + '</th>';
  h += '</tr>';
  $('thead').innerHTML = h;
}

// ===== Tbody =====
function renderTbody(dates, dateKeys, cellsByDate, keyItems, kiStatus, config, weekStats) {
  var html = '';
  var fmtCell = function(v) { return v === 0 ? '-' : v; };

  // Key item rows（与时间表共用 data-cell 选区机制；id 加 KI| 前缀以区分）
  // v2.13.1：前三件事加状态框
  for (var r = 0; r < KEY_ROWS.length; r++) {
    html += '<tr class="row-keyitem"><td class="col-label">' + KEY_ROWS[r] + '</td>';
    for (var i = 0; i < 7; i++) {
      var k = dateKeys[i] + '|' + KEY_ROWS[r];
      var statusBox = '';
      if (r < 3) {
        var st = kiStatus[k] || '';
        if (st) statusBox = '<span class="ki-status-box ki-status-' + st + '" data-ki-status-key="' + k + '" title="点击切换状态">&nbsp;</span>';
        else statusBox = '<span class="ki-status-box" data-ki-status-key="' + k + '" title="点击设置状态">&nbsp;</span>';
      }
      html += '<td colspan="2" class="cell-event" data-cell="KI|' + k + '">' + statusBox + (keyItems[k] || '') + '</td>';
    }
    html += '<td></td></tr>';
  }

  // Schedule rows
  for (var s = 0; s < TIME_SLOTS.length; s++) {
    var slot = TIME_SLOTS[s];
    html += '<tr><td class="col-label">' + slot + '</td>';
    for (var i2 = 0; i2 < 7; i2++) {
      var dk = dateKeys[i2];
      var cid = dk + '|' + slot;
      var cell = cellsByDate[dk][slot];
      var title = cell ? cell.title : '';
      var code = cell ? cell.code : '';
      var catCls = getCatClass(code);
      html += '<td class="cell-event ' + catCls + '" data-cell="' + cid + '">' + title + '</td>';
      html += '<td class="cell-code ' + catCls + '">' + (code !== '' && code !== null && code !== undefined ? code : '') + '</td>';
    }
    html += '<td></td></tr>';
  }

  // Stats
  html += renderStatsRows(weekStats, config);
  $('tbody').innerHTML = html;
  bindCellClicks();
}

// ===== 统计行 =====
function renderStatsRows(ws, config) {
  var daily = ws.daily, totals = ws.totals;
  var f = function(v) { return v === 0 ? '-' : v; };
  // 该天是否完全空白（一格都没填）→ 该日所有统计 / 校验列显示空白
  var dayEmpty = daily.map(function(d) { return d.filled === 0; });
  // 所有 7 天均空时，合计列也显示空白
  var allEmpty = dayEmpty.every(function(x) { return x; });
  var EMPTY_CELL = '<td colspan="2" class="cell-empty"></td>';
  var EMPTY_CELL_TOTAL = '<td class="cell-empty"></td>';
  // 生成单天统计 td；若该天为空则返回空白单元格
  function dCell(di, content, extraCls) {
    if (dayEmpty[di]) return EMPTY_CELL;
    return '<td colspan="2"' + (extraCls ? ' class="' + extraCls + '"' : '') + '>' + content + '</td>';
  }
  // 生成合计 td
  function tCell(content, extraCls) {
    if (allEmpty) return EMPTY_CELL_TOTAL;
    return '<td' + (extraCls ? ' class="' + extraCls + '"' : '') + '>' + content + '</td>';
  }
  var h = '';

  // Five categories
  var cats = [
    {l:'Guilt Free Play', k:'gfp', c:'stat-gfp', sep:1},
    {l:'Rest', k:'rest', c:'stat-rest'},
    {l:'Mandatory Work', k:'mw', c:'stat-mw'},
    {l:'Quality Work', k:'qw', c:'stat-qw'},
    {l:'Procrastination', k:'proc', c:'stat-proc'}
  ];
  for (var ci = 0; ci < cats.length; ci++) {
    var cat = cats[ci];
    h += '<tr class="stat-row ' + cat.c + (cat.sep ? ' sep-top' : '') + '"><td class="col-label">' + cat.l + '</td>';
    for (var di = 0; di < daily.length; di++) h += dCell(di, f(daily[di][cat.k]));
    h += tCell(f(totals[cat.k])) + '</tr>';
  }

  // 赚
  h += '<tr class="stat-row stat-earn sep-top"><td class="col-label">赚</td>';
  for (var e = 0; e < daily.length; e++) h += dCell(e, f(daily[e].earned));
  h += tCell(f(totals.earned)) + '</tr>';

  // 赔
  h += '<tr class="stat-row stat-lose"><td class="col-label">赔</td>';
  for (var lo = 0; lo < daily.length; lo++) h += dCell(lo, f(daily[lo].lost));
  h += tCell(f(totals.lost)) + '</tr>';

  // 结余
  h += '<tr class="stat-row"><td class="col-label">结余</td>';
  for (var b = 0; b < daily.length; b++) {
    var bc = daily[b].balance >= 0 ? 'bal-pos' : 'bal-neg';
    h += dCell(b, daily[b].balance, bc);
  }
  var tc = totals.balance >= 0 ? 'bal-pos' : 'bal-neg';
  h += tCell(totals.balance, tc) + '</tr>';

  // QW明细（项目投入）
  for (var q = 0; q < 7; q++) {
    h += '<tr class="stat-row detail-qw' + (q === 0 ? ' sep-top' : '') + '"><td class="col-label">1.' + (q+1) + '-' + config.qwNames[q] + '</td>';
    for (var qi = 0; qi < daily.length; qi++) h += dCell(qi, f(daily[qi].qwDetail[q]));
    h += tCell(f(totals.qwDetail[q])) + '</tr>';
  }

  // GFP明细
  for (var g = 0; g < 7; g++) {
    h += '<tr class="stat-row detail-gfp' + (g === 0 ? ' sep-top' : '') + '"><td class="col-label">2.' + (g+1) + '-' + config.gfpNames[g] + '</td>';
    for (var gi = 0; gi < daily.length; gi++) h += dCell(gi, f(daily[gi].gfpDetail[g]));
    h += tCell(f(totals.gfpDetail[g])) + '</tr>';
  }

  // 有效投资
  h += '<tr class="stat-row stat-invest"><td class="col-label">有效投资</td>';
  for (var vi = 0; vi < daily.length; vi++) h += dCell(vi, f(daily[vi].validInvest));
  h += tCell(f(totals.validInvest)) + '</tr>';

  // 无效浪费明细
  for (var p = 0; p < 5; p++) {
    h += '<tr class="stat-row detail-proc' + (p === 0 ? ' sep-top' : '') + '"><td class="col-label">3.' + (p+1) + '-' + config.procNames[p] + '</td>';
    for (var pi = 0; pi < daily.length; pi++) h += dCell(pi, f(daily[pi].procDetail[p]));
    h += tCell(f(totals.procDetail[p])) + '</tr>';
  }

  // 无效浪费
  h += '<tr class="stat-row stat-waste"><td class="col-label">无效浪费</td>';
  for (var wi = 0; wi < daily.length; wi++) h += dCell(wi, f(daily[wi].invalidWaste));
  h += tCell(f(totals.invalidWaste)) + '</tr>';

  // 潜力/标准/可用
  h += '<tr class="stat-row stat-potential sep-top"><td class="col-label">潜力总数</td>';
  for (var pt = 0; pt < daily.length; pt++) h += dCell(pt, f(daily[pt].potential));
  h += tCell(f(totals.potential)) + '</tr>';

  h += '<tr class="stat-row stat-standard"><td class="col-label">标准数</td>';
  for (var st = 0; st < daily.length; st++) h += dCell(st, config.standard);
  h += tCell(config.standard * 7) + '</tr>';

  h += '<tr class="stat-row stat-available"><td class="col-label">可用数</td>';
  for (var av = 0; av < daily.length; av++) h += dCell(av, daily[av].available);
  h += tCell(totals.available) + '</tr>';

  // 校验
  h += '<tr class="stat-row sep-top"><td class="col-label">校验总数</td>';
  for (var ct = 0; ct < daily.length; ct++) h += dCell(ct, daily[ct].checkTotal, daily[ct].checkTotal === 0 ? 'val-ok' : 'val-err');
  h += tCell(totals.checkTotal, totals.checkTotal === 0 ? 'val-ok' : 'val-err') + '</tr>';

  h += '<tr class="stat-row"><td class="col-label">校验亏损</td>';
  for (var cl = 0; cl < daily.length; cl++) h += dCell(cl, daily[cl].checkLoss, daily[cl].checkLoss === 0 ? 'val-ok' : 'val-err');
  h += tCell(totals.checkLoss, totals.checkLoss === 0 ? 'val-ok' : 'val-err') + '</tr>';

  h += '<tr class="stat-row"><td class="col-label">校验投资</td>';
  for (var ci2 = 0; ci2 < daily.length; ci2++) h += dCell(ci2, daily[ci2].checkInvest, daily[ci2].checkInvest === 0 ? 'val-ok' : 'val-err');
  h += tCell(totals.checkInvest, totals.checkInvest === 0 ? 'val-ok' : 'val-err') + '</tr>';

  return h;
}

// ===== v2.13.1：状态框与月历 =====

// 渲染单个状态框 HTML
function renderKiStatusBox(key, status) {
  var st = status || '';
  if (!st) return '<span class="ki-status-box" data-ki-status-key="' + key + '" title="点击设置状态">&nbsp;</span>';
  return '<span class="ki-status-box ki-status-' + st + '" data-ki-status-key="' + key + '" title="点击切换状态">&nbsp;</span>';
}

// 循环切换：白框(未评) → done(绿✓已完成) → ongoing(蓝O持续) → todo(红未完成) → 白框
function cycleKeyItemStatus(key) {
  var ws = getISOWeek(new Date(key.split('|')[0] + 'T00:00:00Z'));
  var status = getKeyItemStatus(ws.year, ws.week);
  var cur = status[key] || '';
  var idx = KEY_ITEM_STATUS_VALUES.indexOf(cur);
  var next;
  if (idx < 0) {
    next = KEY_ITEM_STATUS_VALUES[0]; // 无状态 → done(已完成)
  } else if (idx >= KEY_ITEM_STATUS_VALUES.length - 1) {
    next = ''; // 最后一个 ongoing → 无状态(白框)
  } else {
    next = KEY_ITEM_STATUS_VALUES[idx + 1];
  }
  if (next) { status[key] = next; }
  else { delete status[key]; }
  saveKeyItemStatus(ws.year, ws.week, status);
  setTimeout(function() { renderAll(); }, 0);
}

// 获取自然月的网格日期列表（6 周 × 7 天）
function getMonthGridDates(year, month) {
  var firstDay = new Date(Date.UTC(year, month - 1, 1));
  var startDow = (firstDay.getUTCDay() + 6) % 7;
  var gridStart = new Date(firstDay);
  gridStart.setUTCDate(gridStart.getUTCDate() - startDow);
  var days = [];
  for (var w = 0; w < 6; w++) {
    for (var d = 0; d < 7; d++) {
      var dt = new Date(gridStart);
      dt.setUTCDate(gridStart.getUTCDate() + w * 7 + d);
      days.push({
        dateKey: dateKey(dt),
        day: dt.getUTCDate(),
        inMonth: dt.getUTCMonth() + 1 === month && dt.getUTCFullYear() === year,
        isToday: dateKey(dt) === dateKey(today)
      });
    }
  }
  return days;
}

// 渲染桌面月历视图
function renderMonthCalendar() {
  var days = getMonthGridDates(monthState.year, monthState.month);

  $('week-title').textContent = monthState.year + '年' + monthState.month + '月';

  var h = '<tr><th></th>';
  for (var d = 0; d < 7; d++) h += '<th>' + WEEKDAYS[d] + '</th>';
  h += '</tr>';
  $('thead').innerHTML = h;

  var tbodyH = '';
  for (var w = 0; w < 6; w++) {
    tbodyH += '<tr>';
    for (var d2 = 0; d2 < 7; d2++) {
      var day = days[w * 7 + d2];
      if (d2 === 0) {
        var isoW = getISOWeek(new Date(day.dateKey + 'T00:00:00Z'));
        tbodyH += '<td class="col-label" style="font-size:10px;">W' + isoW.week + '</td>';
      }
      var cellCls = 'month-cell';
      if (!day.inMonth) cellCls += ' month-cell-out';
      if (day.isToday) cellCls += ' month-cell-today';
      tbodyH += '<td class="' + cellCls + '">';
      tbodyH += '<div class="mc-date">' + day.day + '</div>';

      if (day.inMonth) {
        var iso = getISOWeek(new Date(day.dateKey + 'T00:00:00Z'));
        var items = getKeyItems(iso.year, iso.week);
        var kiSt = getKeyItemStatus(iso.year, iso.week);

        var k1 = day.dateKey + '|' + KEY_ROWS[0];
        tbodyH += '<div class="mc-row">' + renderKiStatusBox(k1, kiSt[k1] || '') + '<span class="mc-text' + (items[k1] ? '' : ' mc-empty') + '">' + (items[k1] || '') + '</span></div>';
        var k2 = day.dateKey + '|' + KEY_ROWS[1];
        tbodyH += '<div class="mc-row">' + renderKiStatusBox(k2, kiSt[k2] || '') + '<span class="mc-text' + (items[k2] ? '' : ' mc-empty') + '">' + (items[k2] || '') + '</span></div>';
        var k3 = day.dateKey + '|' + KEY_ROWS[2];
        tbodyH += '<div class="mc-row">' + renderKiStatusBox(k3, kiSt[k3] || '') + '<span class="mc-text' + (items[k3] ? '' : ' mc-empty') + '">' + (items[k3] || '') + '</span></div>';
        var k4 = day.dateKey + '|' + KEY_ROWS[3];
        tbodyH += '<div class="mc-row mc-smallJoy"><span class="mc-label">小确幸：</span><span class="mc-text' + (items[k4] ? '' : ' mc-empty') + '">' + (items[k4] || '') + '</span></div>';
        var k5 = day.dateKey + '|' + KEY_ROWS[4];
        tbodyH += '<div class="mc-row mc-keyword"><span class="mc-label">关键词：</span><span class="mc-text' + (items[k5] ? '' : ' mc-empty') + '">' + (items[k5] || '') + '</span></div>';
      }
      tbodyH += '</td>';
    }
    tbodyH += '</tr>';
  }
  $('tbody').innerHTML = tbodyH;

  // 月历只读：不绑定任何编辑事件

  $('panel-left').innerHTML = '';
  $('panel-review').innerHTML = '';
}

// ===== 左侧面板 =====
function renderLeftPanel(config, totals) {
  // 全量展示：每个子分类一行（含 0），按需求文档「明细全部展示」要求
  var fmt = function(v) { return v > 0 ? v : '-'; };
  var h = '<h4>本周累计</h4>';
  // 分类合计行：与明细行同样的 flex 布局，合计数右对齐
  h += '<div class="lp-cat lp-qw"><span>QW - Quality Work</span><span>' + totals.qw + '</span></div>';
  for (var i = 0; i < 7; i++) {
    h += '<div class="lp-item' + (totals.qwDetail[i] > 0 ? '' : ' lp-zero') + '"><span>1.' + (i+1) + '-' + config.qwNames[i] + '</span><span>' + fmt(totals.qwDetail[i]) + '</span></div>';
  }
  h += '<div class="lp-cat lp-gfp"><span>GFP - Guilt Free Play</span><span>' + totals.gfp + '</span></div>';
  for (var j = 0; j < 7; j++) {
    h += '<div class="lp-item' + (totals.gfpDetail[j] > 0 ? '' : ' lp-zero') + '"><span>2.' + (j+1) + '-' + config.gfpNames[j] + '</span><span>' + fmt(totals.gfpDetail[j]) + '</span></div>';
  }
  h += '<div class="lp-cat lp-proc"><span>Proc - Procrastination</span><span>' + totals.proc + '</span></div>';
  for (var k = 0; k < 5; k++) {
    h += '<div class="lp-item' + (totals.procDetail[k] > 0 ? '' : ' lp-zero') + '"><span>3.' + (k+1) + '-' + config.procNames[k] + '</span><span>' + fmt(totals.procDetail[k]) + '</span></div>';
  }
  $('panel-left').innerHTML = h;
}

// ===== 右侧复盘 =====
function renderReviewPanel(year, week, totals) {
  var review = getReview(year, week);
  // count 字段表示该项需要拆分为 N 个独立输入框；t='list' 走多框模式
  var items = [
    {k:'keyword', l:'1. 本周关键词', t:'input'},
    {k:'selfScore', l:'2. 自我打分', t:'input'},
    {k:'overallReview', l:'3. 总体评价', t:'textarea'},
    {k:'booksRead', l:'4. 本周读的书', t:'textarea'},
    {k:'moviesWatched', l:'5. 本周看的电影', t:'textarea'},
    {k:'top5Work', l:'6. 最有意义的5件工作', t:'list', count: 5},
    {k:'top3Stupid', l:'7. 干的最傻3件事', t:'list', count: 3},
    {k:'top3Quotes', l:'8. 最牛3句话', t:'list', count: 3},
    {k:'dinnerGuests', l:'9. 请吃饭的人', t:'textarea'}
  ];

  // 把 review[k] 规范化为数组（旧数据可能为字符串，按换行拆分）
  var asList = function(val, count) {
    var arr;
    if (Array.isArray(val)) arr = val.slice();
    else if (val) arr = String(val).split(/\r?\n/);
    else arr = [];
    while (arr.length < count) arr.push('');
    return arr;
  };
  var esc = function(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); };

  var h = '<h3>周复盘</h3>';
  for (var i = 0; i < items.length; i++) {
    var it = items[i];
    var raw = review[it.k];
    h += '<div class="rv-item"><label>' + it.l + '</label>';
    if (it.t === 'input') {
      h += '<input data-rv="' + it.k + '" value="' + esc(raw || '') + '">';
    } else if (it.t === 'list') {
      var list = asList(raw, it.count);
      h += '<div class="rv-list">';
      for (var n = 0; n < it.count; n++) {
        h += '<input class="rv-list-input" data-rv-list="' + it.k + '" data-rv-idx="' + n + '" placeholder="' + (n + 1) + '." value="' + esc(list[n]) + '">';
      }
      h += '</div>';
    } else {
      h += '<textarea data-rv="' + it.k + '">' + esc(raw || '').replace(/&quot;/g, '"') + '</textarea>';
    }
    h += '</div>';
  }
  var reward = totals.balance;
  var cls = reward >= 0 ? 'bal-pos' : 'bal-neg';
  h += '<div class="rv-reward ' + cls + '">10. 赢得奖励时间：' + reward + '</div>';

  $('panel-review').innerHTML = h;
  // 单值字段（input / textarea）
  $('panel-review').querySelectorAll('[data-rv]').forEach(function(el) {
    el.addEventListener('change', function() {
      var r = getReview(year, week);
      r[el.dataset.rv] = el.value;
      saveReview(year, week, r);
    });
  });
  // 多框列表：任一框 change，将所有同 key 的框收成数组写回
  $('panel-review').querySelectorAll('[data-rv-list]').forEach(function(el) {
    el.addEventListener('change', function() {
      var k = el.dataset.rvList;
      var arr = [];
      $('panel-review').querySelectorAll('[data-rv-list="' + k + '"]').forEach(function(inp) {
        arr.push(inp.value || '');
      });
      var r = getReview(year, week);
      r[k] = arr;
      saveReview(year, week, r);
    });
  });
}

// ===== 单元格编辑 =====
var editingCell = null;
var clipboard = null;             // 跨弹窗剪贴板：{ title, code }
var selection = null;             // { startId, endId }（覆盖矩形选区）

// 编码校验：
//   合法 = 空字符串 | 0 | 4 | 1.1~1.7 | 2.1~2.7 | 3.1~3.5
// 返回 { ok, value, msg }
function validateCode(raw) {
  if (raw === '' || raw === null || raw === undefined) return { ok: true, value: '' };
  var s = String(raw).trim();
  if (s === '') return { ok: true, value: '' };
  if (s === '0') return { ok: true, value: 0 };
  if (s === '4') return { ok: true, value: 4 };
  // 主.子：主∈{1,2,3}；子是单个数字 1~9
  var m = /^([123])\.([1-9])$/.exec(s);
  if (!m) return { ok: false, msg: '编码格式错误：必须是 0、4、1.1~1.7、2.1~2.7 或 3.1~3.5' };
  var main = parseInt(m[1], 10);
  var sub = parseInt(m[2], 10);
  var maxSub = main === 1 ? 7 : (main === 2 ? 7 : 5);
  if (sub > maxSub) {
    var name = main === 1 ? 'QW 仅支持 1.1~1.7' : (main === 2 ? 'GFP 仅支持 2.1~2.7' : 'Proc 仅支持 3.1~3.5');
    return { ok: false, msg: '编码超出范围：' + name };
  }
  return { ok: true, value: parseFloat(s) };
}

// ===== 撤销 / 重做 栈（仅日程 cells；keyitems / review 暂不入栈） =====
var undoStack = [];               // 每项：{ year, week, cells: 完整快照 }
var redoStack = [];
var UNDO_LIMIT = 100;

// 抓快照：cells + keyItems 一起保存（保证撤销能恢复 KI 的批量删 / 批量粘贴）
function takeSnapshot() {
  return {
    year: state.year,
    week: state.week,
    cells: JSON.parse(JSON.stringify(getCells(state.year, state.week))),
    keyItems: JSON.parse(JSON.stringify(getKeyItems(state.year, state.week)))
  };
}
function restoreSnapshot(snap) {
  saveCells(snap.year, snap.week, snap.cells);
  saveKeyItems(snap.year, snap.week, snap.keyItems);
  if (snap.year !== state.year || snap.week !== state.week) {
    state = { year: snap.year, week: snap.week };
  }
}

// 在任何会改 cells/keyItems 的操作之前调用：把当前快照压入 undo 栈，并清空 redo 栈
function pushUndoSnapshot() {
  undoStack.push(takeSnapshot());
  if (undoStack.length > UNDO_LIMIT) undoStack.shift();
  redoStack = [];
}

function performUndo() {
  if (undoStack.length === 0) { showToast('没有可撤销的操作'); return; }
  var prev = undoStack.pop();
  redoStack.push(takeSnapshot());
  if (redoStack.length > UNDO_LIMIT) redoStack.shift();
  restoreSnapshot(prev);
  renderAll();
  showToast('已撤销');
}

function performRedo() {
  if (redoStack.length === 0) { showToast('没有可重做的操作'); return; }
  var next = redoStack.pop();
  undoStack.push(takeSnapshot());
  if (undoStack.length > UNDO_LIMIT) undoStack.shift();
  restoreSnapshot(next);
  renderAll();
  showToast('已重做');
}

function isCoarsePointer() {
  return window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
}

// ===== 统一 cell id helpers（KI 行 + TS 行共用同一个选区/快捷键空间） =====
// id 形态：
//   - 关键事项：'KI|date|rowName'
//   - 时间格 ：'date|slot'
function isKeyItemId(id) { return typeof id === 'string' && id.indexOf('KI|') === 0; }

// 把任意 id 解析为 { type:'KI'|'TS', date, kiName?, slot?, slotIndex? }
function parseAnyCellId(id) {
  if (isKeyItemId(id)) {
    var p = id.split('|');
    return { type: 'KI', date: p[1], kiName: p[2], kiIndex: KEY_ROWS.indexOf(p[2]) };
  }
  var q = id.split('|');
  return { type: 'TS', date: q[0], slot: q[1], slotIndex: TIME_SLOTS.indexOf(q[1]) };
}

// 统一的行索引（0..KEY_ROWS.length-1 = KI；之后 = TS）
function unifiedRow(id) {
  var p = parseAnyCellId(id);
  return p.type === 'KI' ? p.kiIndex : (KEY_ROWS.length + p.slotIndex);
}
function unifiedCol(id) {
  var p = parseAnyCellId(id);
  return currentDateKeys.indexOf(p.date);
}
function totalRows() { return KEY_ROWS.length + TIME_SLOTS.length; }

// 由统一行/列还原成 id
function idFromUnified(row, col) {
  if (row < 0 || row >= totalRows() || col < 0 || col >= currentDateKeys.length) return null;
  if (row < KEY_ROWS.length) return 'KI|' + currentDateKeys[col] + '|' + KEY_ROWS[row];
  return currentDateKeys[col] + '|' + TIME_SLOTS[row - KEY_ROWS.length];
}

function bindCellClicks() {
  // v2.13.1：状态框点击只切状态，不进入编辑
  $('tbody').querySelectorAll('[data-ki-status-key]').forEach(function(box) {
    box.addEventListener('click', function(e) {
      e.stopPropagation();
      e.preventDefault();
      cycleKeyItemStatus(box.dataset.kiStatusKey);
    });
  });
  var coarse = isCoarsePointer();
  $('tbody').querySelectorAll('[data-cell]').forEach(function(td) {
    if (coarse) {
      // 移动端：单击直接打开编辑弹窗（按类型派发）
      td.addEventListener('click', function(e) {
        e.stopPropagation();
        var id = td.dataset.cell;
        if (isKeyItemId(id)) openKeyItemEdit(id); else openCellDialog(id);
      });
      return;
    }
    // 桌面端：mousedown 一站式处理选区（含拖动），避免与 click 事件竞争
    td.addEventListener('mousedown', function(e) {
      if (e.button !== 0) return;
      e.preventDefault();
      e.stopPropagation();
      var id = td.dataset.cell;
      if (e.shiftKey && selection) {
        selection = { startId: selection.startId, endId: id };
      } else {
        selection = { startId: id, endId: id };
      }
      applySelectionStyles();

      var moveHandler = function(ev) {
        var t = document.elementFromPoint(ev.clientX, ev.clientY);
        if (!t) return;
        var cellTd = t.closest && t.closest('[data-cell]');
        if (!cellTd) return;
        if (selection.endId !== cellTd.dataset.cell) {
          selection.endId = cellTd.dataset.cell;
          applySelectionStyles();
        }
      };
      var upHandler = function() {
        document.removeEventListener('mousemove', moveHandler);
        document.removeEventListener('mouseup', upHandler);
      };
      document.addEventListener('mousemove', moveHandler);
      document.addEventListener('mouseup', upHandler);
    });
    td.addEventListener('dblclick', function(e) {
      e.stopPropagation();
      var id = td.dataset.cell;
      if (isKeyItemId(id)) openKeyItemEdit(id); else openCellDialog(id);
    });
  });
}

// 计算选区矩形 { rowMin, rowMax, colMin, colMax }（统一行索引：KI 行 + TS 行）
function getSelectionRange() {
  if (!selection) return null;
  var sRow = unifiedRow(selection.startId);
  var eRow = unifiedRow(selection.endId);
  var sCol = unifiedCol(selection.startId);
  var eCol = unifiedCol(selection.endId);
  if (sRow < 0 || eRow < 0 || sCol < 0 || eCol < 0) return null;
  return {
    rowMin: Math.min(sRow, eRow),
    rowMax: Math.max(sRow, eRow),
    colMin: Math.min(sCol, eCol),
    colMax: Math.max(sCol, eCol)
  };
}

// 遍历选区每个 cell id
function forEachSelectedId(fn) {
  var r = getSelectionRange();
  if (!r) return;
  for (var ri = r.rowMin; ri <= r.rowMax; ri++) {
    for (var ci = r.colMin; ci <= r.colMax; ci++) {
      var id = idFromUnified(ri, ci);
      if (id) fn(id, ri, ci);
    }
  }
}

// 重新应用选区高亮样式
function applySelectionStyles() {
  document.querySelectorAll('.cell-selected,.cell-row-hl').forEach(function(el) {
    el.classList.remove('cell-selected','cell-row-hl');
  });
  if (!selection) return;

  var range = getSelectionRange();
  forEachSelectedId(function(id) {
    var td = document.querySelector('[data-cell="' + cssAttrEscape(id) + '"]');
    if (!td) return;
    td.classList.add('cell-selected');
    var next = td.nextElementSibling;
    if (next && next.classList.contains('cell-code')) next.classList.add('cell-selected');
  });

  // 行高亮
  if (!range) return;
  var allCells = document.querySelectorAll('#tbody [data-cell]');
  for (var i = 0; i < allCells.length; i++) {
    var td = allCells[i];
    var id = td.dataset.cell;
    var ri = unifiedRow(id), ci = unifiedCol(id);
    if (ri < 0 || ci < 0) continue;
    var inRow = ri >= range.rowMin && ri <= range.rowMax;
    var inCol = ci >= range.colMin && ci <= range.colMax;
    if (inRow && inCol) continue;
    if (inRow) td.classList.add('cell-row-hl');
    var nxt = td.nextElementSibling;
    if (nxt && nxt.classList.contains('cell-code') && inRow) nxt.classList.add('cell-row-hl');
  }
}

// data-cell 属性中的字符可能包含 `|`、`-`、`:`，全部为合法 CSS 字符；保险起见做转义
function cssAttrEscape(s) {
  return String(s).replace(/(["\\])/g, '\\$1');
}

// 移动选区（方向键）；shiftKey 用于扩展选区终点
function moveSelection(dCol, dRow, extend) {
  if (!selection) return;
  var anchorId = extend ? selection.endId : selection.startId;
  var col = unifiedCol(anchorId);
  var row = unifiedRow(anchorId);
  if (col < 0 || row < 0) return;
  var newCol = Math.max(0, Math.min(currentDateKeys.length - 1, col + dCol));
  var newRow = Math.max(0, Math.min(totalRows() - 1, row + dRow));
  var newId = idFromUnified(newRow, newCol);
  if (!newId) return;
  if (extend) {
    selection = { startId: selection.startId, endId: newId };
  } else {
    selection = { startId: newId, endId: newId };
  }
  applySelectionStyles();
  var td = document.querySelector('[data-cell="' + cssAttrEscape(newId) + '"]');
  if (td && td.scrollIntoView) td.scrollIntoView({ block: 'nearest', inline: 'nearest' });
}

// 顶部小 toast 提示
function showToast(msg) {
  var el = $('toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toast';
    el.className = 'toast';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.classList.add('toast-show');
  clearTimeout(showToast._t);
  showToast._t = setTimeout(function() { el.classList.remove('toast-show'); }, 1100);
}

// 读 / 写抽象：根据 id 类型，从对应数据源 get / set / delete
function getCellValue(id) {
  var p = parseAnyCellId(id);
  if (p.type === 'KI') {
    var items = getKeyItems(state.year, state.week);
    return { kind: 'KI', value: items[p.date + '|' + p.kiName] || '' };
  }
  var cells = getCells(state.year, state.week);
  var c = cells[id];
  return { kind: 'TS', value: c ? { title: c.title || '', code: (c.code === undefined ? '' : c.code) } : { title: '', code: '' } };
}

// 把同种类的内容写入若干 id；返回写入数量。如果剪贴板 kind 与目标 id 类型不同，跳过。
// op = 'paste' / 'delete'
function applyToSelection(op, payload) {
  var cells = getCells(state.year, state.week);
  var items = getKeyItems(state.year, state.week);
  var dirtyCells = false, dirtyItems = false, count = 0, skipped = 0;
  forEachSelectedId(function(id) {
    var p = parseAnyCellId(id);
    if (op === 'delete') {
      if (p.type === 'KI') {
        var k = p.date + '|' + p.kiName;
        if (items[k] !== undefined && items[k] !== '') { delete items[k]; _resetKiStatus(k); dirtyItems = true; count++; }
      } else {
        if (cells[id] !== undefined) { delete cells[id]; dirtyCells = true; count++; }
      }
    } else if (op === 'paste') {
      if (payload.kind !== p.type) { skipped++; return; }
      if (p.type === 'KI') {
        var k2 = p.date + '|' + p.kiName;
        if (payload.value && payload.value !== '') items[k2] = payload.value;
        else delete items[k2];
        dirtyItems = true; count++;
      } else {
        var pv = payload.value || { title: '', code: '' };
        var hasContent = (pv.title && pv.title !== '') || (pv.code !== '' && pv.code !== null && pv.code !== undefined);
        if (hasContent) cells[id] = { title: pv.title || '', code: (pv.code === undefined ? '' : pv.code) };
        else delete cells[id];
        dirtyCells = true; count++;
      }
    }
  });
  if (dirtyCells) saveCells(state.year, state.week, cells);
  if (dirtyItems) saveKeyItems(state.year, state.week, items);
  return { count: count, skipped: skipped };
}

// Excel 风格批量动作
function copySelectionToClipboard() {
  if (!selection) return;
  var v = getCellValue(selection.startId);
  clipboard = { kind: v.kind, value: JSON.parse(JSON.stringify(v.value)) };
  var hint;
  if (v.kind === 'KI') {
    hint = v.value || '';
  } else {
    hint = (v.value.title || '') + (v.value.code !== '' && v.value.code !== undefined ? '  ' + v.value.code : '');
  }
  showToast(hint ? '已复制：' + hint : '已复制（空格）');
}

function pasteClipboardToSelection() {
  if (!selection || !clipboard) { showToast('请先 Ctrl+C 复制'); return; }
  // TS 剪贴板需校验 code
  if (clipboard.kind === 'TS') {
    var cv = validateCode(clipboard.value && clipboard.value.code);
    if (!cv.ok) { showToast('剪贴板编码非法：' + cv.msg); return; }
  }
  pushUndoSnapshot();
  var r = applyToSelection('paste', clipboard);
  renderAll();
  var msg = '已粘贴到 ' + r.count + ' 格';
  if (r.skipped > 0) msg += '（跳过 ' + r.skipped + ' 个不同类型）';
  showToast(msg);
}

function deleteSelection() {
  if (!selection) return;
  pushUndoSnapshot();
  var r = applyToSelection('delete');
  renderAll();
  showToast('已清空 ' + r.count + ' 格');
}

// Excel Ctrl+D：把选区第一行的内容向下复制到选区其余行（按列独立，按类型独立）
function fillDownSelection() {
  var r = getSelectionRange();
  if (!r || r.rowMin === r.rowMax) return;
  pushUndoSnapshot();
  var cells = getCells(state.year, state.week);
  var items = getKeyItems(state.year, state.week);
  var dirtyCells = false, dirtyItems = false;
  for (var ci = r.colMin; ci <= r.colMax; ci++) {
    var srcId = idFromUnified(r.rowMin, ci);
    if (!srcId) continue;
    var srcType = parseAnyCellId(srcId).type;
    var srcVal = srcType === 'KI'
      ? (items[currentDateKeys[ci] + '|' + KEY_ROWS[r.rowMin]] || '')
      : cells[srcId];
    for (var ri = r.rowMin + 1; ri <= r.rowMax; ri++) {
      var tgtId = idFromUnified(ri, ci);
      if (!tgtId) continue;
      var tgtType = parseAnyCellId(tgtId).type;
      if (tgtType !== srcType) continue;   // 类型不同跳过
      if (tgtType === 'KI') {
        var k = currentDateKeys[ci] + '|' + KEY_ROWS[ri];
        if (srcVal) items[k] = srcVal; else { delete items[k]; _resetKiStatus(k); }
        dirtyItems = true;
      } else {
        var hasContent = srcVal && ((srcVal.title && srcVal.title !== '') || (srcVal.code !== '' && srcVal.code !== null && srcVal.code !== undefined));
        if (hasContent) cells[tgtId] = { title: srcVal.title || '', code: (srcVal.code === undefined ? '' : srcVal.code) };
        else delete cells[tgtId];
        dirtyCells = true;
      }
    }
  }
  if (dirtyCells) saveCells(state.year, state.week, cells);
  if (dirtyItems) saveKeyItems(state.year, state.week, items);
  renderAll();
}

// 全局键盘
document.addEventListener('keydown', function(e) {
  // ESC 关闭弹窗
  if (e.key === 'Escape') {
    if ($('cell-modal').classList.contains('active')) { closeModal('cell-modal'); return; }
    if ($('ki-modal').classList.contains('active')) { closeModal('ki-modal'); return; }
    if (selection) { selection = null; applySelectionStyles(); return; }
  }
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
  if ($('cell-modal').classList.contains('active') || $('ki-modal').classList.contains('active')) return;

  // 撤销 / 重做（无需选区即可使用）
  if (e.ctrlKey && (e.key === 'z' || e.key === 'Z')) {
    e.preventDefault();
    if (e.shiftKey) performRedo(); else performUndo();
    return;
  }
  if (e.ctrlKey && (e.key === 'y' || e.key === 'Y')) {
    e.preventDefault();
    performRedo();
    return;
  }

  if (!selection) return;

  // 进入编辑：Enter / F2（按类型派发）
  if (e.key === 'Enter' || e.key === 'F2') {
    e.preventDefault();
    if (isKeyItemId(selection.startId)) openKeyItemEdit(selection.startId);
    else openCellDialog(selection.startId);
    return;
  }

  // Excel 快捷键
  if (e.ctrlKey && (e.key === 'c' || e.key === 'C')) { e.preventDefault(); copySelectionToClipboard(); return; }
  if (e.ctrlKey && (e.key === 'v' || e.key === 'V')) { e.preventDefault(); pasteClipboardToSelection(); return; }
  if (e.ctrlKey && (e.key === 'd' || e.key === 'D')) { e.preventDefault(); fillDownSelection(); return; }
  if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); deleteSelection(); return; }

  // 方向键移动选区
  var moveMap = { ArrowUp:[0,-1], ArrowDown:[0,1], ArrowLeft:[-1,0], ArrowRight:[1,0] };
  if (moveMap[e.key]) {
    e.preventDefault();
    moveSelection(moveMap[e.key][0], moveMap[e.key][1], e.shiftKey);
  }
});

// 仅在点击主表格区域之外时取消选区；Esc 也可取消
// 之前实现会因为拖动结束后的 click 事件 target 落在 table/tbody 上而误清空选区，因此改为放白名单：
//   - 主表格内任何位置都不清空（包括拖动结束的 click 落点）
//   - 弹窗、左侧累计面板、右侧复盘内的点击不清空
//   - 顶部工具栏点击会通过自身按钮的 onclick 处理，不再额外清除选区
document.addEventListener('click', function(e) {
  if (!selection) return;
  if (e.target.closest('#main-table') || e.target.closest('.modal-box') ||
      e.target.closest('.left-panel') || e.target.closest('.review-panel') ||
      e.target.closest('.toolbar')) return;
  selection = null;
  applySelectionStyles();
});

// 解析 cell id (`日期|时段`) → { date, slot, slotIndex }
function parseCellId(id) {
  var parts = id.split('|');
  return { date: parts[0], slot: parts[1], slotIndex: TIME_SLOTS.indexOf(parts[1]) };
}

// 计算同一天向前/向后偏移 N 格的 cell id；越界返回 null
function shiftCellId(id, delta) {
  var p = parseCellId(id);
  if (p.slotIndex < 0) return null;
  var next = p.slotIndex + delta;
  if (next < 0 || next >= TIME_SLOTS.length) return null;
  return p.date + '|' + TIME_SLOTS[next];
}

function openCellDialog(id) {
  editingCell = id;
  var cells = getCells(state.year, state.week);
  var cell = cells[id] || { title: '', code: '' };
  var p = parseCellId(id);
  $('cell-dialog-title').textContent = (p.slot || '') + '   ' + (p.date || '');
  $('inp-title').value = cell.title || '';
  $('inp-code').value = (cell.code !== undefined && cell.code !== null && cell.code !== '') ? cell.code : '';
  var config = getConfig(state.year, state.week);
  $('code-hint').innerHTML =
    '允许编码：0=Rest · 4=MW · 1.1~1.7=QW(' + config.qwNames.join('/') + ')' +
    ' · 2.1~2.7=GFP(' + config.gfpNames.join('/') + ')' +
    ' · 3.1~3.5=Proc(' + config.procNames.join('/') + ')';
  $('btn-paste-cell').disabled = !(clipboard && clipboard.kind === 'TS');
  openModal('cell-modal');
  setTimeout(function() { $('inp-title').focus(); $('inp-title').select(); }, 50);

  // 任意输入框 Enter = 保存并跳下一格；Shift+Enter = 跳上一格；Tab = 切换字段（默认）；Ctrl+Enter = 保存并关闭；Ctrl+D = 复制上一时段
  var modalKeyHandler = function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (e.ctrlKey || e.metaKey) {
        saveCellAndAdvance(0);   // 保存关闭，不跳
      } else {
        saveCellAndAdvance(e.shiftKey ? -1 : 1);
      }
    } else if (e.key === 'd' && e.ctrlKey) {
      e.preventDefault();
      fillFromPrevSlot();
    }
  };
  $('inp-title').onkeydown = modalKeyHandler;
  $('inp-code').onkeydown = modalKeyHandler;
  // 实时校验：输入错就标红，正确则恢复
  $('inp-code').oninput = function() {
    var v = validateCode($('inp-code').value);
    $('inp-code').classList.toggle('input-error', !v.ok);
  };
  $('inp-code').classList.remove('input-error');
}

// 把上一时段的内容复制到当前弹窗输入框（Ctrl+D）
function fillFromPrevSlot() {
  if (!editingCell) return;
  var prevId = shiftCellId(editingCell, -1);
  if (!prevId) return;
  var cells = getCells(state.year, state.week);
  var prev = cells[prevId];
  if (!prev) return;
  $('inp-title').value = prev.title || '';
  $('inp-code').value = (prev.code !== undefined && prev.code !== null && prev.code !== '') ? prev.code : '';
  $('inp-code').focus();
  $('inp-code').select();
}

var editingKiKey = null;

// 接受任意形态的 id（'KI|date|name' 或 'date|name'），统一标准化为 'date|name' 存到 editingKiKey
function openKeyItemEdit(idOrKey) {
  var key = idOrKey;
  if (isKeyItemId(key)) key = key.substring(3);   // 去掉 'KI|' 前缀，得到 'date|name'
  editingKiKey = key;
  var parts = key.split('|');
  $('ki-dialog-title').textContent = (parts[1] || '') + '  ' + (parts[0] || '');
  var items = getKeyItems(state.year, state.week);
  $('inp-ki').value = items[key] || '';
  openModal('ki-modal');
  setTimeout(function() { $('inp-ki').focus(); $('inp-ki').select(); }, 50);
  $('inp-ki').onkeydown = function(e) {
    if (e.key === 'Enter') { e.preventDefault(); saveKeyItem(); }
  };
}

// 清空关键事项文本时，同步重置对应状态为 todo
function _resetKiStatus(key) {
  var parts = key.split('|');
  if (parts.length < 2) return;
  var row = parts[1];
  if (KEY_ITEM_STATUS_ROWS.indexOf(row) < 0) return; // 仅前三件事
  var ws = getISOWeek(new Date(parts[0] + 'T00:00:00Z'));
  var st = getKeyItemStatus(ws.year, ws.week);
  if (st[key]) { delete st[key]; saveKeyItemStatus(ws.year, ws.week, st); }
}

function saveKeyItem() {
  if (!editingKiKey) return;
  var val = $('inp-ki').value.trim();
  var items = getKeyItems(state.year, state.week);
  if ((items[editingKiKey] || '') !== val) pushUndoSnapshot();
  if (val) items[editingKiKey] = val; else { delete items[editingKiKey]; _resetKiStatus(editingKiKey); }
  saveKeyItems(state.year, state.week, items);
  closeModal('ki-modal');
  renderAll();
}

function clearKeyItem() {
  if (!editingKiKey) return;
  var items = getKeyItems(state.year, state.week);
  if (items[editingKiKey] !== undefined && items[editingKiKey] !== '') pushUndoSnapshot();
  delete items[editingKiKey];
  _resetKiStatus(editingKiKey);
  saveKeyItems(state.year, state.week, items);
  closeModal('ki-modal');
  renderAll();
}

function copyCellFromModal() {
  if (!editingCell) return;
  var cells = getCells(state.year, state.week);
  var c = cells[editingCell];
  clipboard = c ? { kind: 'TS', value: JSON.parse(JSON.stringify(c)) } : { kind: 'TS', value: { title: '', code: '' } };
  $('btn-paste-cell').disabled = !clipboard;
  var btn = $('btn-copy-cell');
  btn.textContent = '已复制';
  setTimeout(function() { btn.textContent = '复制此格'; }, 1200);
}

function pasteCellFromModal() {
  if (!editingCell || !clipboard || clipboard.kind !== 'TS') return;
  var v = clipboard.value || {};
  $('inp-title').value = v.title || '';
  $('inp-code').value = (v.code !== undefined && v.code !== null && v.code !== '') ? v.code : '';
}

// 保存当前弹窗内容到 editingCell，返回 { ok, payload } 或 { ok:false }
function commitCurrentCell() {
  if (!editingCell) return { ok: false };
  var title = $('inp-title').value.trim();
  var codeRaw = $('inp-code').value.trim();
  // 规则：事件名 与 编码 必须同时非空，或同时空（同时空 = 清空格子）
  if (title === '' && codeRaw !== '') {
    showToast('请填写事件名');
    var inpT = $('inp-title');
    inpT.classList.add('input-error');
    inpT.focus();
    return { ok: false };
  }
  if (title !== '' && codeRaw === '') {
    showToast('请填写分类编码（0=Rest · 4=MW · 1.x/2.x/3.x）');
    var inpC = $('inp-code');
    inpC.classList.add('input-error');
    inpC.focus();
    return { ok: false };
  }
  var v = validateCode(codeRaw);
  if (!v.ok) {
    showToast(v.msg);
    var inp = $('inp-code');
    inp.classList.add('input-error');
    inp.focus();
    inp.select();
    return { ok: false };
  }
  $('inp-code').classList.remove('input-error');
  var code = v.value;
  var cells = getCells(state.year, state.week);
  // 只有当内容真的变了才入栈，避免空 Enter 也压栈
  var existing = cells[editingCell];
  var newPayload = (title || codeRaw !== '') ? { title: title, code: code } : null;
  var changed = false;
  if (!existing && newPayload) changed = true;
  else if (existing && !newPayload) changed = true;
  else if (existing && newPayload) changed = (existing.title !== newPayload.title) || (existing.code !== newPayload.code);
  if (changed) pushUndoSnapshot();
  var payload = null;
  if (newPayload) {
    payload = newPayload;
    cells[editingCell] = payload;
  } else {
    delete cells[editingCell];
  }
  saveCells(state.year, state.week, cells);
  return { ok: true, payload: payload };
}

// 保存并按方向跳到相邻时段；direction=0 表示仅保存关闭。
function saveCellAndAdvance(direction) {
  var r = commitCurrentCell();
  if (!r.ok) return;
  if (direction === 0) {
    closeModal('cell-modal');
    renderAll();
    return;
  }
  var nextId = shiftCellId(editingCell, direction);
  if (!nextId) {
    // 已到边界，仅保存关闭
    closeModal('cell-modal');
    renderAll();
    return;
  }
  // 保持弹窗打开，仅切换 editingCell 与表单内容；无需关闭再开
  renderAll();
  openCellDialog(nextId);
}

function clearCell() {
  if (!editingCell) return;
  var cells = getCells(state.year, state.week);
  if (cells[editingCell] !== undefined) pushUndoSnapshot();
  delete cells[editingCell];
  saveCells(state.year, state.week, cells);
  closeModal('cell-modal');
  renderAll();
}

// ===== 归档 =====
function updateArchiveBtn(weekStats) {
  var btn = $('btn-archive');
  var t = weekStats.totals;
  var allOk = t.checkTotal === 0 && t.checkLoss === 0 && t.checkInvest === 0;
  if (isArchived(state.year, state.week)) { btn.textContent = '已归档'; btn.disabled = true; }
  else if (allOk) { btn.textContent = '确认归档'; btn.disabled = false; }
  else { btn.textContent = '确认归档'; btn.disabled = true; }
}

// 整理本周数据摘要文本，供导出/归档前的确认弹窗使用
function buildWeekSummary() {
  var dateKeys = getWeekDates(state.year, state.week).map(function(d) { return dateKey(d); });
  var cellsByDate = {};
  for (var i = 0; i < dateKeys.length; i++) cellsByDate[dateKeys[i]] = {};
  var allCells = getCells(state.year, state.week);
  Object.keys(allCells).forEach(function(k) {
    var p = k.split('|');
    if (cellsByDate[p[0]] && TIME_SLOTS.indexOf(p[1]) >= 0) cellsByDate[p[0]][p[1]] = allCells[k];
  });
  var stats = calcWeeklyStats(cellsByDate, dateKeys, getConfig(state.year, state.week).standard).totals;
  var keyItems = getKeyItems(state.year, state.week);
  var review = getReview(state.year, state.week);
  var filledTs = Object.keys(allCells).length;
  var filledKi = Object.keys(keyItems).filter(function(k) { return keyItems[k]; }).length;
  var filledRv = Object.keys(review).filter(function(k) {
    var v = review[k];
    if (Array.isArray(v)) return v.some(function(x) { return x && x.trim(); });
    return v && String(v).trim();
  }).length;
  return [
    '本周编号：' + state.year + ' 第 ' + state.week + ' 周',
    '已填时段：' + filledTs + ' 格',
    '已填关键事项：' + filledKi + ' 项',
    '已填复盘条目：' + filledRv + ' / 9',
    '统计：QW ' + stats.qw + ' · GFP ' + stats.gfp + ' · Proc ' + stats.proc + ' · Rest ' + stats.rest + ' · MW ' + stats.mw,
    '校验：总数 ' + stats.checkTotal + ' / 损益 ' + stats.checkLoss + ' / 投资 ' + stats.checkInvest
  ].join('\n');
}

// 导出 Excel：整体保存确认
function handleExport() {
  var summary = buildWeekSummary();
  if (!confirm('确认导出本周数据为 Excel？\n\n' + summary + '\n\n点「确定」立即导出（数据均已自动保存）')) return;
  exportExcel();
  showToast('已开始导出');
}

// =====【数据导出 / 导入：JSON 全量】=====
function pad2(n) { return n < 10 ? '0' + n : '' + n; }

function handleExportData() {
  var payload = exportAllData();
  if (payload.keyCount === 0) {
    if (!confirm('当前本机没有任何周数据可导出。仍要生成空 JSON 文件吗？')) return;
  }
  var json = JSON.stringify(payload, null, 2);
  var blob = new Blob([json], { type: 'application/json;charset=utf-8' });
  var url = URL.createObjectURL(blob);
  var d = new Date();
  var fname = '时间管理助手-数据-' +
    d.getFullYear() + pad2(d.getMonth() + 1) + pad2(d.getDate()) + '-' +
    pad2(d.getHours()) + pad2(d.getMinutes()) + '.json';
  var a = document.createElement('a');
  a.href = url; a.download = fname;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(function() { URL.revokeObjectURL(url); }, 1000);
  showToast('已导出 ' + payload.keyCount + ' 项 / ' + fname);
}

function handleImportClick() {
  var input = $('inp-import-file');
  input.value = '';   // 清空以便重复选同一文件
  input.click();
}

function handleImportFileChosen(e) {
  var file = e.target.files && e.target.files[0];
  if (!file) return;
  var reader = new FileReader();
  reader.onload = function(ev) {
    var text = ev.target.result;
    var payload;
    try { payload = JSON.parse(text); }
    catch (err) { alert('JSON 解析失败：' + err.message); return; }
    var sm = summarizeImport(payload);
    if (!sm.ok) {
      alert('文件无法导入：\n' + sm.errors.join('\n'));
      return;
    }
    var weekList = sm.weeks.map(function(w) { return w.year + '-W' + w.week + '（' + w.parts.length + ' 项）'; }).join('\n');
    var msg = '即将导入：\n\n' +
      '总条目：' + sm.totalKeys + '\n' +
      '涉及周：' + sm.weeks.length + ' 周\n' +
      (payload.exportedAt ? '导出时间：' + payload.exportedAt + '\n' : '') +
      '\n' + weekList +
      '\n\n本机已有的同周数据将被覆盖；未在文件中的周不受影响。\n点「确定」开始导入。';
    if (!confirm(msg)) return;
    try {
      var r = importAllData(payload, 'merge');
      showToast('导入成功：' + r.written + ' 项 / ' + r.weekCount + ' 周');
      // 整体重新渲染
      refreshTimeSlots();
      renderAll();
    } catch (err) {
      alert('导入失败：' + err.message);
    }
  };
  reader.onerror = function() { alert('读取文件失败'); };
  reader.readAsText(file, 'utf-8');
}

function handleArchive() {
  var summary = buildWeekSummary();
  if (!confirm('归档后本周数据将锁定且无法编辑。是否确认归档并导出 Excel？\n\n' + summary)) return;
  setArchived(state.year, state.week);
  exportExcel();
  renderAll();
  showToast('已归档');
}

// ===== Excel 导出（保留单元格颜色 + 包含累计 / 复盘） =====
// 使用 xlsx-js-style（SheetJS 社区 fork，原生支持 cell.s 样式）。
var XLSX_LIB_URL = 'https://cdn.jsdelivr.net/npm/xlsx-js-style@1.2.0/dist/xlsx.bundle.js';

function exportExcel() {
  if (window.XLSX && XLSX.__hasStyleSupport) { doExport(); return; }
  // 已有 xlsx 但没有样式支持（旧脚本可能已加载），需改换 lib
  var existing = document.querySelector('script[src*="xlsx"]');
  if (existing) existing.parentNode.removeChild(existing);
  if (window.XLSX) { try { delete window.XLSX; } catch (e) { window.XLSX = undefined; } }
  var s = document.createElement('script');
  s.src = XLSX_LIB_URL;
  s.onload = function() {
    if (window.XLSX) { window.XLSX.__hasStyleSupport = true; doExport(); }
    else showToast('Excel 库加载失败');
  };
  s.onerror = function() { showToast('Excel 库加载失败，请检查网络'); };
  document.head.appendChild(s);
}

// 分类 → Excel 颜色（fgColor / fontColor）
var EXCEL_CAT_COLOR = {
  'cat-rest': { fill: '4ADE80', font: '000000' },
  'cat-qw':   { fill: '16A34A', font: 'FFFFFF' },
  'cat-gfp':  { fill: '2563EB', font: 'FFFFFF' },
  'cat-mw':   { fill: 'FFFF00', font: '000000' },
  'cat-proc': { fill: 'DC2626', font: 'FFFFFF' }
};
var EXCEL_BORDER = {
  top: { style: 'thin', color: { rgb: 'D1D5DB' } },
  bottom: { style: 'thin', color: { rgb: 'D1D5DB' } },
  left: { style: 'thin', color: { rgb: 'D1D5DB' } },
  right: { style: 'thin', color: { rgb: 'D1D5DB' } }
};

function makeStyle(opts) {
  opts = opts || {};
  var s = { border: EXCEL_BORDER, alignment: { vertical: 'center', wrapText: true, horizontal: opts.align || 'center' } };
  if (opts.fill) s.fill = { patternType: 'solid', fgColor: { rgb: opts.fill } };
  s.font = { name: '微软雅黑', sz: opts.sz || 10, bold: !!opts.bold, color: { rgb: opts.font || '000000' } };
  return s;
}

// 加粗黑色外框（block 外四边都打 thick）
function applyBlockBorder(ws, r1, c1, r2, c2) {
  var encode = XLSX.utils.encode_cell;
  var THICK = { style: 'thick', color: { rgb: '000000' } };
  for (var r = r1; r <= r2; r++) {
    for (var c = c1; c <= c2; c++) {
      var addr = encode({ r: r, c: c });
      if (!ws[addr]) ws[addr] = { v: '', t: 's', s: makeStyle() };
      // 拷贝现有 style 避免污染共享对象
      var base = ws[addr].s ? JSON.parse(JSON.stringify(ws[addr].s)) : makeStyle();
      var b = base.border || {};
      if (r === r1) b.top = THICK;
      if (r === r2) b.bottom = THICK;
      if (c === c1) b.left = THICK;
      if (c === c2) b.right = THICK;
      base.border = b;
      ws[addr].s = base;
    }
  }
}

// 直接往 worksheet 写一个 cell（值 + 样式）
function placeCell(ws, r, c, value, style) {
  var addr = XLSX.utils.encode_cell({ r: r, c: c });
  var t = (typeof value === 'number') ? 'n' : 's';
  var v = value == null ? '' : value;
  ws[addr] = { v: v, t: t };
  if (style) ws[addr].s = style;
}

function doExport() {
  var year = state.year, week = state.week;
  refreshTimeSlots();      // 按本周配置重建 34 时段字符串
  var dates = getWeekDates(year, week);
  var dateKeys = dates.map(dateKey);
  var config = getConfig(year, week);
  var allCells = getCells(year, week);
  var keyItems = getKeyItems(year, week);
  var kiStatus = getKeyItemStatus(year, week);
  var review = getReview(year, week);
  var cellsByDate = {};
  dateKeys.forEach(function(d) { cellsByDate[d] = {}; });
  Object.keys(allCells).forEach(function(k) {
    var p = k.split('|');
    if (cellsByDate[p[0]] && TIME_SLOTS.indexOf(p[1]) >= 0) cellsByDate[p[0]][p[1]] = allCells[k];
  });
  var stats = calcWeeklyStats(cellsByDate, dateKeys, config.standard);
  var totals = stats.totals;

  var ws = {};
  var merges = [];

  // ===== Block A：主时间表（cols 0..14，rows 0..mainEndRow）=====
  var MAIN_COLS = 15;        // 1 + 7*2
  var MAIN_END_ROW = 1 + KEY_ROWS.length + TIME_SLOTS.length - 1;   // 0..(1+5+34-1)=39
  // 0 行：标题行
  placeCell(ws, 0, 0, year + '年第' + week + '周', makeStyle({ fill: 'E2E8F0', bold: true, sz: 11 }));
  for (var i = 0; i < 7; i++) {
    var label = WEEKDAYS[i] + ' ' + formatDate(dates[i]);
    placeCell(ws, 0, 1 + i * 2, label, makeStyle({ fill: 'E2E8F0', bold: true, sz: 11 }));
    placeCell(ws, 0, 1 + i * 2 + 1, '', makeStyle({ fill: 'E2E8F0', bold: true, sz: 11 }));
    merges.push({ s: { r: 0, c: 1 + i * 2 }, e: { r: 0, c: 1 + i * 2 + 1 } });
  }
  // 1..5 行：关键事项（第一件事 / 第二件事 / 第三件事 / 小确幸 / 关键词；居中显示）
  for (var ki = 0; ki < KEY_ROWS.length; ki++) {
    var rKi = 1 + ki;
    placeCell(ws, rKi, 0, KEY_ROWS[ki], makeStyle({ fill: 'F1F5F9', bold: true, align: 'center' }));
    for (var c1 = 0; c1 < 7; c1++) {
      var kv = keyItems[dateKeys[c1] + '|' + KEY_ROWS[ki]] || '';
      // v2.13.1：前三件事附加状态标记
      var prefix = '';
      if (ki < 3) {
        var stk = dateKeys[c1] + '|' + KEY_ROWS[ki];
        var st = kiStatus[stk] || '';
        if (st === 'done') prefix = '[✓] ';
        else if (st === 'ongoing') prefix = '[O] ';
        else if (st === 'todo') prefix = '[✕] ';
      }
      placeCell(ws, rKi, 1 + c1 * 2, prefix + kv, makeStyle({ bold: true, align: 'center' }));
      placeCell(ws, rKi, 1 + c1 * 2 + 1, '', makeStyle({ bold: true, align: 'center' }));
      merges.push({ s: { r: rKi, c: 1 + c1 * 2 }, e: { r: rKi, c: 1 + c1 * 2 + 1 } });
    }
  }
  // 6+ 行：时段
  for (var ts = 0; ts < TIME_SLOTS.length; ts++) {
    var rTs = 1 + KEY_ROWS.length + ts;
    placeCell(ws, rTs, 0, TIME_SLOTS[ts], makeStyle({ fill: 'F1F5F9', bold: true }));
    for (var c2 = 0; c2 < 7; c2++) {
      var cell = cellsByDate[dateKeys[c2]][TIME_SLOTS[ts]];
      var cls = cell ? getCatClass(cell.code) : '';
      var color = EXCEL_CAT_COLOR[cls];
      var st = color ? makeStyle({ fill: color.fill, font: color.font }) : makeStyle();
      placeCell(ws, rTs, 1 + c2 * 2, cell ? (cell.title || '') : '', st);
      var codeVal = (cell && cell.code !== '' && cell.code !== undefined && cell.code !== null) ? cell.code : '';
      placeCell(ws, rTs, 1 + c2 * 2 + 1, codeVal, st);
    }
  }

  // ===== Block B：本周累计（cols 0..1，紧接 Block A 下方留 1 空行）=====
  // 颜色规则与主表一致：QW=绿(白字)，GFP=蓝(白字)，Proc=红(白字)，Rest=浅绿(黑字)，MW=黄(黑字)
  var STATS_COL_END = 1;
  var rB = MAIN_END_ROW + 2;            // 空一行
  var STATS_START_ROW = rB;
  placeCell(ws, rB, 0, '本周累计', makeStyle({ fill: 'E2E8F0', bold: true, sz: 12, align: 'center' }));
  placeCell(ws, rB, 1, '', makeStyle({ fill: 'E2E8F0', bold: true, sz: 12 }));
  merges.push({ s: { r: rB, c: 0 }, e: { r: rB, c: 1 } });
  rB++;
  function writeStatRow(label, value, fill, font, bold) {
    placeCell(ws, rB, 0, label, makeStyle({ align: 'center', bold: !!bold, fill: fill, font: font }));
    placeCell(ws, rB, 1, value, makeStyle({ align: 'center', bold: !!bold, fill: fill, font: font }));
    rB++;
  }
  var QW = EXCEL_CAT_COLOR['cat-qw'];
  var GFP = EXCEL_CAT_COLOR['cat-gfp'];
  var PROC = EXCEL_CAT_COLOR['cat-proc'];
  var REST = EXCEL_CAT_COLOR['cat-rest'];
  var MW = EXCEL_CAT_COLOR['cat-mw'];

  writeStatRow('QW - Quality Work', totals.qw, QW.fill, QW.font, true);
  for (var qi = 0; qi < 7; qi++) writeStatRow('  1.' + (qi + 1) + '-' + config.qwNames[qi], totals.qwDetail[qi], QW.fill, QW.font);
  writeStatRow('GFP - Guilt Free Play', totals.gfp, GFP.fill, GFP.font, true);
  for (var gi = 0; gi < 7; gi++) writeStatRow('  2.' + (gi + 1) + '-' + config.gfpNames[gi], totals.gfpDetail[gi], GFP.fill, GFP.font);
  writeStatRow('Proc - Procrastination', totals.proc, PROC.fill, PROC.font, true);
  for (var pi = 0; pi < 5; pi++) writeStatRow('  3.' + (pi + 1) + '-' + config.procNames[pi], totals.procDetail[pi], PROC.fill, PROC.font);
  writeStatRow('Rest', totals.rest, REST.fill, REST.font, true);
  writeStatRow('MW', totals.mw, MW.fill, MW.font, true);
  var STATS_END_ROW = rB - 1;

  // ===== Block C：周复盘（cols 16..17，从 row 0 开始，与 Block A 右侧并排）=====
  var REVIEW_COL_START = 16;
  var REVIEW_COL_END = 17;
  var rC = 0;
  placeCell(ws, rC, REVIEW_COL_START, '周复盘', makeStyle({ fill: 'E2E8F0', bold: true, sz: 12, align: 'center' }));
  placeCell(ws, rC, REVIEW_COL_END, '', makeStyle({ fill: 'E2E8F0', bold: true, sz: 12 }));
  merges.push({ s: { r: rC, c: REVIEW_COL_START }, e: { r: rC, c: REVIEW_COL_END } });
  rC++;

  // 单值条目：label 在左列，value 在右列
  function writeReviewSingle(label, value) {
    placeCell(ws, rC, REVIEW_COL_START, label, makeStyle({ fill: 'F1F5F9', bold: true, align: 'left' }));
    placeCell(ws, rC, REVIEW_COL_END, value || '', makeStyle({ align: 'left' }));
    rC++;
  }
  // 多项条目：先 label 跨两列，再 N 行：左列 "{parent}.{n}"，右列 内容
  function writeReviewList(parentNum, label, key, count) {
    var v = review[key];
    var arr = Array.isArray(v) ? v : (v ? String(v).split(/\r?\n/) : []);
    placeCell(ws, rC, REVIEW_COL_START, label, makeStyle({ fill: 'F1F5F9', bold: true, align: 'left' }));
    placeCell(ws, rC, REVIEW_COL_END, '', makeStyle({ fill: 'F1F5F9', bold: true }));
    merges.push({ s: { r: rC, c: REVIEW_COL_START }, e: { r: rC, c: REVIEW_COL_END } });
    rC++;
    for (var n = 0; n < count; n++) {
      placeCell(ws, rC, REVIEW_COL_START, parentNum + '.' + (n + 1), makeStyle({ align: 'left' }));
      placeCell(ws, rC, REVIEW_COL_END, arr[n] || '', makeStyle({ align: 'left' }));
      rC++;
    }
  }

  writeReviewSingle('1. 本周关键词', review.keyword);
  writeReviewSingle('2. 自我打分', review.selfScore);
  writeReviewSingle('3. 总体评价', review.overallReview);
  writeReviewSingle('4. 本周读的书', review.booksRead);
  writeReviewSingle('5. 本周看的电影', review.moviesWatched);
  writeReviewList(6, '6. 最有意义的5件工作', 'top5Work', 5);
  writeReviewList(7, '7. 干的最傻3件事', 'top3Stupid', 3);
  writeReviewList(8, '8. 最牛3句话', 'top3Quotes', 3);
  writeReviewSingle('9. 请吃饭的人', review.dinnerGuests);
  writeReviewSingle('10. 赢得奖励时间', totals.balance);
  var REVIEW_END_ROW = rC - 1;

  // ===== 列宽 =====
  var colsW = [{ wch: 12 }];                                 // 标签列
  for (var cw = 0; cw < 7; cw++) colsW.push({ wch: 12 }, { wch: 6 });  // 7 天 (title 12 + code 6)
  colsW.push({ wch: 2 });                                    // 列 15：间隔
  colsW.push({ wch: 8 }, { wch: 38 });                       // 复盘左右列（左窄装数字，右宽装内容）
  ws['!cols'] = colsW;

  // ===== 合并 =====
  ws['!merges'] = merges;

  // ===== 整体范围（确保所有列都被识别） =====
  var lastRow = Math.max(STATS_END_ROW, REVIEW_END_ROW);
  ws['!ref'] = XLSX.utils.encode_range({ s: { r: 0, c: 0 }, e: { r: lastRow, c: REVIEW_COL_END } });

  // ===== 三块外加粗黑框 =====
  applyBlockBorder(ws, 0, 0, MAIN_END_ROW, MAIN_COLS - 1);                       // Block A
  applyBlockBorder(ws, STATS_START_ROW, 0, STATS_END_ROW, STATS_COL_END);         // Block B
  applyBlockBorder(ws, 0, REVIEW_COL_START, REVIEW_END_ROW, REVIEW_COL_END);      // Block C

  var wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, '周计划');

  var filename = year + '第' + week + '周.xlsx';
  if (window.showSaveFilePicker) {
    window.showSaveFilePicker({
      suggestedName: filename,
      startIn: 'documents',
      types: [{ description: 'Excel', accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] } }]
    }).then(function(handle) {
      return handle.createWritable().then(function(writable) {
        var buf = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        return writable.write(buf).then(function() { return writable.close(); });
      });
    }).catch(function() {
      XLSX.writeFile(wb, filename);
    });
  } else {
    XLSX.writeFile(wb, filename);
  }
}

// ===== 配置页（草稿模式） =====
// 进入时把当前配置克隆为 configDraft，所有改动写入 draft，直到用户在离开时显式确认才落盘。
var configDraft = null;
var configOriginal = null;     // 进入时的原始 JSON 字符串，便于检测是否修改
var configYearWeek = null;     // 锁定本次编辑针对的 year/week，避免切周污染

function renderConfig() {
  var year = state.year, week = state.week;
  configYearWeek = { year: year, week: week };
  var config = getConfig(year, week);
  configDraft = JSON.parse(JSON.stringify(config));
  configOriginal = JSON.stringify(config);

  var h = '';
  h += '<div class="config-hint" style="background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;padding:8px 12px;border-radius:6px;margin-bottom:12px;">⚠ 此处修改为草稿，需点「← 返回」时选择「保存」才会真正生效。</div>';

  h += '<div class="config-section"><h3>Quality Work 项目名称</h3><p class="config-hint">切换新周时默认继承上周配置</p><table class="config-table"><thead><tr><th>代码</th><th>项目名称</th></tr></thead><tbody>';
  for (var i = 0; i < 7; i++) h += '<tr><td>1.' + (i+1) + '</td><td><input data-cfg="qw-' + i + '" value="' + (configDraft.qwNames[i] || '').replace(/"/g,'&quot;') + '"></td></tr>';
  h += '</tbody></table></div>';

  h += '<div class="config-section"><h3>Guilt Free Play 子类名称</h3><table class="config-table"><thead><tr><th>代码</th><th>子类名称</th></tr></thead><tbody>';
  for (var j = 0; j < 7; j++) h += '<tr><td>2.' + (j+1) + '</td><td><input data-cfg="gfp-' + j + '" value="' + (configDraft.gfpNames[j] || '').replace(/"/g,'&quot;') + '"></td></tr>';
  h += '</tbody></table></div>';

  // 时段配置：仅设置起始时间，34 格 × 30 分钟自动展开
  if (!configDraft.startTime) configDraft.startTime = '7:00';
  h += '<div class="config-section"><h3>时段起始时间</h3>';
  h += '<p class="config-hint">总 34 格、每格 30 分钟不变；填写起始时间后自动生成全部时段。</p>';
  h += '<input type="time" data-cfg="startTime" value="' + normalizeHHMM(configDraft.startTime) + '" style="padding:6px;border:1px solid #d1d5db;border-radius:4px;font-size:14px;">';
  h += '<div id="config-slot-preview" style="margin-top:10px;font-size:12px;color:#475569;line-height:1.6;"></div>';
  h += '</div>';

  h += '<div class="config-section"><h3>系统参数</h3><p class="config-hint">标准数（每天标准休息格数，默认12）</p><input type="number" data-cfg="standard" value="' + configDraft.standard + '" style="width:80px;padding:6px;border:1px solid #d1d5db;border-radius:4px;"></div>';

  h += '<div class="config-section"><h3>Procrastination 子类（固定）</h3><table class="config-table"><tbody>';
  for (var k = 0; k < 5; k++) h += '<tr><td>3.' + (k+1) + '</td><td>' + configDraft.procNames[k] + '</td></tr>';
  h += '</tbody></table></div>';

  $('config-body').innerHTML = h;
  refreshSlotPreview();

  $('config-body').querySelectorAll('[data-cfg]').forEach(function(inp) {
    inp.addEventListener('input', function() {
      var key = inp.dataset.cfg;
      if (key === 'standard') configDraft.standard = parseInt(inp.value) || 12;
      else if (key === 'startTime') {
        configDraft.startTime = denormalizeHHMM(inp.value);
        refreshSlotPreview();
      }
      else if (key.indexOf('qw-') === 0) configDraft.qwNames[parseInt(key.split('-')[1])] = inp.value;
      else if (key.indexOf('gfp-') === 0) configDraft.gfpNames[parseInt(key.split('-')[1])] = inp.value;
    });
  });
}

// HTML <input type="time"> 需要 'HH:MM' 两位小时；core 内部允许 '7:00' 这种一位小时
function normalizeHHMM(s) {
  var p = String(s || '7:00').split(':');
  var h = parseInt(p[0], 10) || 0;
  var m = parseInt(p[1] || '0', 10) || 0;
  return (h < 10 ? '0' + h : '' + h) + ':' + (m < 10 ? '0' + m : '' + m);
}
function denormalizeHHMM(s) {
  var p = String(s || '07:00').split(':');
  var h = parseInt(p[0], 10) || 0;
  var m = parseInt(p[1] || '0', 10) || 0;
  return h + ':' + (m < 10 ? '0' + m : '' + m);
}

// 配置页「时段起始时间」下方的实时预览
function refreshSlotPreview() {
  var el = document.getElementById('config-slot-preview');
  if (!el) return;
  var slots = buildTimeSlots(configDraft.startTime || '7:00');
  el.innerHTML = '<b>共 ' + slots.length + ' 格：</b>' +
    slots[0] + ' / ' + slots[1] + ' / … / ' + slots[slots.length - 2] + ' / <b>' + slots[slots.length - 1] + '</b>';
}

// 是否有未落盘的修改
function configIsDirty() {
  if (!configDraft || !configOriginal) return false;
  return JSON.stringify(configDraft) !== configOriginal;
}

// 起始时间变更时，把已填 cells 按索引平移到新 slot key（避免数据丢失）
function remapCellsForStartTimeChange(year, week, oldStartTime, newStartTime) {
  if (!oldStartTime || !newStartTime || oldStartTime === newStartTime) return 0;
  var oldSlots = buildTimeSlots(oldStartTime);
  var newSlots = buildTimeSlots(newStartTime);
  var cells = getCells(year, week);
  var remapped = {};
  var moved = 0, kept = 0;
  Object.keys(cells).forEach(function(k) {
    var p = k.split('|');
    if (p.length < 2) { remapped[k] = cells[k]; kept++; return; }
    var idx = oldSlots.indexOf(p[1]);
    if (idx >= 0 && idx < newSlots.length) {
      remapped[p[0] + '|' + newSlots[idx]] = cells[k];
      moved++;
    } else {
      remapped[k] = cells[k];   // 不在 34 格内的旧 key 原样保留
      kept++;
    }
  });
  if (moved > 0) saveCells(year, week, remapped);
  return moved;
}

// 实际把 configDraft 落盘的统一入口（带 startTime 平移）
function persistConfigDraft() {
  var orig = JSON.parse(configOriginal);
  var yw = configYearWeek;
  var moved = remapCellsForStartTimeChange(yw.year, yw.week, orig.startTime || '7:00', configDraft.startTime || '7:00');
  saveConfig(yw.year, yw.week, configDraft);
  return moved;
}

// 离开配置页时调用：若有改动，弹确认；返回 true 表示允许离开
function tryLeaveConfig() {
  if (!configIsDirty()) return true;
  var ok = confirm('配置已修改但未保存。\n\n点「确定」保存修改\n点「取消」放弃修改并返回');
  if (ok) {
    var moved = persistConfigDraft();
    showToast('配置已保存' + (moved > 0 ? '，时段已平移 ' + moved + ' 格' : ''));
  } else {
    showToast('已放弃修改');
  }
  configDraft = null; configOriginal = null; configYearWeek = null;
  return true;
}

// 配置页「💾 保存」按钮
function handleSaveConfig() {
  if (!configDraft || !configYearWeek) { showToast('暂无修改'); return; }
  if (!configIsDirty()) { showToast('暂无修改'); return; }
  var moved = persistConfigDraft();
  configOriginal = JSON.stringify(configDraft);   // 同步基线，避免再次问询
  showToast('配置已保存' + (moved > 0 ? '，时段已平移 ' + moved + ' 格' : ''));
}

// 主页「💾 保存」按钮：先把当前焦点元素的值提交（触发其 change 落盘），再提示
function handleSaveAll() {
  if (document.activeElement && typeof document.activeElement.blur === 'function') {
    var ev = new Event('change', { bubbles: true });
    document.activeElement.dispatchEvent(ev);
    document.activeElement.blur();
  }
  showToast('已保存到本地');
}

// =============================================================
// ===== 移动端模块（iPhone / 华为）=====
// =============================================================
// 设计要点（详见需求文档 §17.3 / §19 / §20.3 / §20.5 / §20.9 / §20.11）：
//  · 单 HTML 入口、CSS+JS 视图切换；与 Windows 共用 app-core.js
//  · 默认进入「单日填写」；顶部 Tab 切换「单日 / 本周累计」
//  · 仅关键事项 5 行 + 34 个时段格可编辑（红框），其余区域只读
//  · 点击格子直接打开 cell-modal / ki-modal（复用 Windows 同一弹窗）

var viewMode = 'desktop';
var mobileState = { date: null };   // 当前选中的 YYYY-MM-DD 字符串

function detectViewMode() {
  var override = localStorage.getItem('tm_viewMode');
  if (override === 'desktop' || override === 'iphone' || override === 'huawei') return override;
  var ua = navigator.userAgent || '';
  if (/iPhone|iPod/.test(ua)) return 'iphone';
  if (/Huawei|HUAWEI|HONOR/i.test(ua)) return 'huawei';
  if (/Android/.test(ua)) return 'huawei';   // 其他 Android 暂归华为版（布局一致）
  return 'desktop';
}

function setViewMode(mode, opts) {
  viewMode = mode;
  document.body.dataset.viewMode = mode;
  if (!opts || opts.persist !== false) localStorage.setItem('tm_viewMode', mode);
  if (mode === 'desktop') {
    showPage('page-main');
  } else {
    if (!mobileState.date) mobileState.date = dateKey(today);
    showPage('page-mobile-day');
  }
  renderAll();
}

function escapeHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// 把 mobileState.date 解析为 { date, year, week, weekday }
function mobileContext() {
  var d = new Date(mobileState.date + 'T00:00:00Z');
  var iso = getISOWeek(d);
  var dow = d.getUTCDay();
  return {
    date: mobileState.date,
    year: iso.year,
    week: iso.week,
    weekday: WEEKDAYS[(dow + 6) % 7],
    ymdCompact: mobileState.date.replace(/-/g, '')
  };
}

// 同步 state.year/state.week，让 openCellDialog / openKeyItemEdit 能读到正确周数据
function syncStateToMobile(ctx) {
  state.year = ctx.year;
  state.week = ctx.week;
  refreshTimeSlots();
}

// =====【补齐锁定】本周内第一个 < 今天 且未填满 34 格的日期 =====
// 只在用户停留在"今天所在的 ISO 周"时启用；切到历史周/未来周不锁
// 返回 { date, filled } | null
function getMobileLockInfo() {
  var todayKey = dateKey(today);
  var todayIso = getISOWeek(today);
  var ctx = mobileContext();
  if (ctx.year !== todayIso.year || ctx.week !== todayIso.week) return null;

  var dates = getWeekDates(ctx.year, ctx.week).map(dateKey);
  var cellsAll = getCells(ctx.year, ctx.week);
  for (var i = 0; i < dates.length; i++) {
    var d = dates[i];
    if (d >= todayKey) break;   // 今天和未来不参与判定
    var filled = 0;
    for (var k in cellsAll) {
      var p = k.split('|');
      if (p[0] !== d) continue;
      if (TIME_SLOTS.indexOf(p[1]) < 0) continue;
      var cell = cellsAll[k];
      if (cell && cell.code !== '' && cell.code != null) filled++;
    }
    if (filled < 34) return { date: d, filled: filled };
  }
  return null;
}

// 计算当日已填写格数（用于 DateBar 进度条）
function dailyFilledCount(date, cellsToday) {
  var c = 0;
  for (var slot in cellsToday) {
    var cell = cellsToday[slot];
    if (cell && cell.code !== '' && cell.code != null) c++;
  }
  return c;
}

// =====【单日填写页】=====
function renderMobileDay() {
  if (!mobileState.date) mobileState.date = dateKey(today);

  // 锁定兜底：若用户当前日 > lockDate，强制归到 lockDate
  var lock = getMobileLockInfo();
  // 仅显示补齐提示，不自动跳转；前进导航按钮已有拦截

  var ctx = mobileContext();
  syncStateToMobile(ctx);

  var config = getConfig(ctx.year, ctx.week);
  var cellsAll = getCells(ctx.year, ctx.week);
  var keyItems = getKeyItems(ctx.year, ctx.week);
  var kiStatus = getKeyItemStatus(ctx.year, ctx.week);

  // 清除因 startTime 变更等导致的过期 slot 数据
  cleanStaleCells(ctx.year, ctx.week);
  cellsAll = getCells(ctx.year, ctx.week); // 重新读取已清理的数据

  // 收集今天的 cells（slot -> {title, code}）
  var cellsToday = {};
  Object.keys(cellsAll).forEach(function(k) {
    var p = k.split('|');
    if (p[0] === ctx.date && TIME_SLOTS.indexOf(p[1]) >= 0) cellsToday[p[1]] = cellsAll[k];
  });

  var stats = calcDailyStats(cellsToday, config.standard);
  var dFilled = dailyFilledCount(ctx.date, cellsToday);

  var h = '';
  h += renderM_DateBar(ctx, lock, dFilled);
  h += renderM_StorageDiag(ctx);
  h += renderM_KeyItems(ctx.date, keyItems, kiStatus);
  h += renderM_Schedule(ctx.date, cellsToday);
  h += renderM_BigFive(stats);
  h += renderM_Earnings(stats);
  h += renderM_Details(stats, config);
  h += renderM_Summary(stats);
  h += renderM_Checks(stats);
  h += renderM_Footer();

  $('mobile-day-body').innerHTML = h;
  bindMobileEvents();
}

function renderM_DateBar(ctx, lock, dFilled) {
  var h = '<div class="m-datebar">' +
    '<button class="m-nav-btn" data-day-step="-1" aria-label="前一天">◀</button>' +
    '<div class="m-date-info">第' + ctx.week + '周 · ' + ctx.weekday + ' · ' + ctx.ymdCompact + '</div>' +
    '<button class="m-nav-btn" data-day-step="1" aria-label="后一天">▶</button>' +
    '<button class="m-today-btn" data-go-today>今天</button>' +
    '</div>';
  // 锁定提示：lock 存在且锁定日不是当天 → 表示用户被强制停在 lockDate
  if (lock) {
    h += '<div class="m-locked-banner">⚠ ' + lock.date + ' 仅填了 ' + lock.filled +
      '/34 格，请先补齐才能切到后续日期</div>';
  }
  if (typeof dFilled === 'number') {
    var pct = Math.round(dFilled / 34 * 100);
    h += '<div class="m-fill-progress">本日已填 <strong>' + dFilled + '</strong> / 34 格' +
      '<div class="m-progress-bar"><div class="m-progress-fill" style="width:' + pct + '%"></div></div>' +
      '</div>';
  }
  return h;
}

function renderM_StorageDiag(ctx) {
  // 统计 localStorage 中 tm_ 开头的 key 数量和当前周数据状态
  var totalKeys = 0, weekKeys = 0;
  for (var i = 0; i < localStorage.length; i++) {
    var k = localStorage.key(i);
    if (k && k.indexOf('tm_') === 0) {
      totalKeys++;
      if (k.indexOf('tm_' + ctx.year + '_w' + ctx.week + '_') === 0) weekKeys++;
    }
  }
  var cells = getCells(ctx.year, ctx.week);
  var items = getKeyItems(ctx.year, ctx.week);
  var cellCount = Object.keys(cells).length;
  var itemCount = Object.keys(items).filter(function(k) { return items[k]; }).length;
  var diagCls = (cellCount === 0 && itemCount === 0) ? 'm-diag-empty' : 'm-diag-ok';
  return '<div class="m-diag ' + diagCls + '" style="margin:6px 12px;padding:6px 10px;border-radius:6px;font-size:11px;line-height:1.5;">' +
    'LS keys: ' + totalKeys + ' (本周' + weekKeys + ') | 时段格: ' + cellCount + ' | 关键事项: ' + itemCount +
    '</div>';
}

function renderM_KeyItems(date, keyItems, kiStatus) {
  var h = '<section class="m-section m-edit-zone"><div class="m-section-title">关键事项</div>';
  KEY_ROWS.forEach(function(row, idx) {
    var key = date + '|' + row;
    var val = keyItems[key] || '';
    var statusBox = '';
    if (idx < 3) {
      var st = (kiStatus && kiStatus[key]) || '';
      statusBox = renderKiStatusBox(key, st);
    }
    h += '<div class="m-row m-ki-row" data-ki-key="' + escapeHtml(key) + '">' +
      '<span class="m-row-label">' + row + statusBox + '</span>' +
      '<span class="m-row-value">' + escapeHtml(val) + '</span>' +
      '</div>';
  });
  h += '</section>';
  return h;
}

function renderM_Schedule(date, cellsToday) {
  var h = '<section class="m-section m-edit-zone"><div class="m-section-title">日程（每 30 分钟，共 34 格）</div>';
  TIME_SLOTS.forEach(function(slot) {
    var cell = cellsToday[slot];
    var cls = '';
    var code = '';
    var title = '';
    var empty = true;
    if (cell && (cell.code !== '' || cell.title)) {
      cls = getCatClass(cell.code);
      code = (cell.code === '' || cell.code == null) ? '' : cell.code;
      title = cell.title || '';
      empty = false;
    }
    h += '<div class="m-ts-row ' + cls + (empty ? ' m-ts-empty' : '') + '" data-cell-id="' + escapeHtml(date + '|' + slot) + '">' +
      '<span class="m-ts-slot">' + slot + '</span>' +
      '<span class="m-ts-title">' + escapeHtml(title) + '</span>' +
      '<span class="m-ts-code">' + (code === '' ? '' : code) + '</span>' +
      '</div>';
  });
  h += '</section>';
  return h;
}

function renderM_BigFive(stats) {
  var rows = [
    { label: 'Guilt Free Play',  v: stats.gfp,  cls: 'cat-gfp' },
    { label: 'Rest',             v: stats.rest, cls: 'cat-rest' },
    { label: 'Mandatory Work',   v: stats.mw,   cls: 'cat-mw' },
    { label: 'Quality Work',     v: stats.qw,   cls: 'cat-qw' },
    { label: 'Procrastination',  v: stats.proc, cls: 'cat-proc' }
  ];
  var h = '<section class="m-section"><div class="m-section-title">当日统计</div>';
  rows.forEach(function(r) {
    h += '<div class="m-stat-row ' + r.cls + '">' +
      '<span class="m-row-label">' + r.label + '</span>' +
      '<span class="m-row-value">' + r.v + '</span></div>';
  });
  h += '</section>';
  return h;
}

function renderM_Earnings(stats) {
  var balCls = stats.balance > 0 ? 'm-earn-bal-pos' : (stats.balance < 0 ? 'm-earn-bal-neg' : '');
  return '<section class="m-section"><div class="m-section-title">当日收益</div>' +
    '<div class="m-stat-row m-earn-qw"><span class="m-row-label">赚</span><span class="m-row-value">' + stats.earned + '</span></div>' +
    '<div class="m-stat-row m-earn-proc"><span class="m-row-label">赔</span><span class="m-row-value">' + stats.lost + '</span></div>' +
    '<div class="m-stat-row ' + balCls + '"><span class="m-row-label">结余</span><span class="m-row-value">' + stats.balance + '</span></div>' +
    '</section>';
}

function renderM_Details(stats, config) {
  function group(title, names, prefix, detail, totalVal, catClass) {
    var h = '<div class="m-detail-group">';
    h += '<div class="m-detail-head ' + catClass + '"><span>' + title + '</span><span>小计 ' + totalVal + '</span></div>';
    for (var i = 0; i < names.length; i++) {
      var v = detail[i] || 0;
      h += '<div class="m-detail-row' + (v === 0 ? ' lp-zero' : '') + '">' +
        '<span class="m-row-label">' + prefix + '.' + (i + 1) + ' ' + escapeHtml(names[i]) + '</span>' +
        '<span class="m-row-value">' + v + '</span></div>';
    }
    h += '</div>';
    return h;
  }
  var h = '<section class="m-section"><div class="m-section-title">当日明细</div>';
  h += group('QW 明细',   config.qwNames,   '1', stats.qwDetail,   stats.qw,   'cat-qw');
  h += group('GFP 明细',  config.gfpNames,  '2', stats.gfpDetail,  stats.gfp,  'cat-gfp');
  h += group('无效浪费',  config.procNames, '3', stats.procDetail, stats.proc, 'cat-proc');
  h += '</section>';
  return h;
}

function renderM_Summary(stats) {
  return '<section class="m-section"><div class="m-section-title">当日汇总</div>' +
    '<div class="m-stat-row"><span class="m-row-label">有效投资</span><span class="m-row-value">' + stats.validInvest + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">无效浪费</span><span class="m-row-value">' + stats.invalidWaste + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">潜力总数</span><span class="m-row-value">' + stats.potential + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">标准数</span><span class="m-row-value">' + stats.standard + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">可用数</span><span class="m-row-value">' + stats.available + '</span></div>' +
    '</section>';
}

function renderM_Checks(stats) {
  function row(label, v) {
    var bad = v !== 0;
    return '<div class="m-stat-row' + (bad ? ' m-check-bad' : '') + '">' +
      '<span class="m-row-label">' + label + '</span>' +
      '<span class="m-row-value">' + v + '</span></div>';
  }
  return '<section class="m-section"><div class="m-section-title">当日校验</div>' +
    row('校验总数', stats.checkTotal) +
    row('校验亏损', stats.checkLoss) +
    row('校验投资', stats.checkInvest) +
    '</section>';
}

function renderM_Footer() {
  // v2.10.0：同步按钮（手机端入口），状态点跟桌面共用样式
  var syncLabel = '☁ 同步设置';
  var dotCls = 'sync-dot-disabled';
  if (window.AppCore && AppCore.syncClient) {
    var s = AppCore.syncClient.getState();
    if (!s.config.enabled) dotCls = 'sync-dot-disabled';
    else if (s.pendingPushTimer || s.pendingPushWeek) dotCls = 'sync-dot-pending';
    else if (s.status === 'connected') dotCls = 'sync-dot-connected';
    else if (s.status === 'connecting') dotCls = 'sync-dot-connecting';
    else if (s.status === 'error') dotCls = 'sync-dot-error';
    else dotCls = 'sync-dot-disconnected';
  }
  return '<div class="m-footer">' +
    '<div class="m-footer-row">' +
      '<button class="m-mode-switch" data-open-sync><span class="sync-dot ' + dotCls + '"></span>' + syncLabel + '</button>' +
    '</div>' +
    '<div class="m-footer-row">' +
      '<button class="m-mode-switch" data-export-data>📤 导出数据</button>' +
      '<button class="m-mode-switch" data-import-data>📥 导入数据</button>' +
    '</div>' +
    '<div class="m-footer-row">' +
      '<button class="m-mode-switch" data-mode-switch="desktop">切换到桌面版</button>' +
    '</div>' +
    '</div>';
}

// =====【本周累计页】（只读） =====
function renderMobileWeek() {
  if (!mobileState.date) mobileState.date = dateKey(today);
  var ctx = mobileContext();
  syncStateToMobile(ctx);

  var config = getConfig(ctx.year, ctx.week);
  cleanStaleCells(ctx.year, ctx.week);
  var cellsAll = getCells(ctx.year, ctx.week);
  var dates = getWeekDates(ctx.year, ctx.week);
  var dateKeys = dates.map(dateKey);
  var cellsByDate = {};
  dateKeys.forEach(function(d) { cellsByDate[d] = {}; });
  Object.keys(cellsAll).forEach(function(k) {
    var p = k.split('|');
    if (cellsByDate[p[0]] !== undefined && TIME_SLOTS.indexOf(p[1]) >= 0) cellsByDate[p[0]][p[1]] = cellsAll[k];
  });
  var w = calcWeeklyStats(cellsByDate, dateKeys, config.standard);
  var t = w.totals;

  // 进度：应填写 = 34 * 7 = 238；已填写 = sum(filled)；剩余 = 238 - 已填写
  var expected = 34 * 7;
  var filled = 0;
  w.daily.forEach(function(d) { filled += d.filled; });
  var remain = expected - filled;
  var pct = expected === 0 ? 0 : Math.round(filled / expected * 100);

  var h = '';
  h += '<div class="m-datebar"><div class="m-date-info">' + ctx.year + '年第' + ctx.week + '周 · 本周累计（只读）</div></div>';

  // 填写进度
  h += '<section class="m-section"><div class="m-section-title">填写进度</div>' +
    '<div class="m-stat-row"><span class="m-row-label">应填写</span><span class="m-row-value">' + expected + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">已填写</span><span class="m-row-value">' + filled + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">剩余</span><span class="m-row-value">' + remain + '</span></div>' +
    '<div class="m-progress"><div class="m-row-label">完成度 ' + pct + '%</div>' +
    '<div class="m-progress-bar"><div class="m-progress-fill" style="width:' + pct + '%"></div></div></div>' +
    '</section>';

  // 五大类
  h += '<section class="m-section"><div class="m-section-title">五大分类（本周合计）</div>' +
    '<div class="m-stat-row cat-gfp"><span class="m-row-label">Guilt Free Play</span><span class="m-row-value">' + t.gfp + '</span></div>' +
    '<div class="m-stat-row cat-rest"><span class="m-row-label">Rest</span><span class="m-row-value">' + t.rest + '</span></div>' +
    '<div class="m-stat-row cat-mw"><span class="m-row-label">Mandatory Work</span><span class="m-row-value">' + t.mw + '</span></div>' +
    '<div class="m-stat-row cat-qw"><span class="m-row-label">Quality Work</span><span class="m-row-value">' + t.qw + '</span></div>' +
    '<div class="m-stat-row cat-proc"><span class="m-row-label">Procrastination</span><span class="m-row-value">' + t.proc + '</span></div>' +
    '</section>';

  // 收益
  h += '<section class="m-section"><div class="m-section-title">本周收益</div>' +
    '<div class="m-stat-row m-earn-qw"><span class="m-row-label">赚</span><span class="m-row-value">' + t.earned + '</span></div>' +
    '<div class="m-stat-row m-earn-proc"><span class="m-row-label">赔</span><span class="m-row-value">' + t.lost + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">结余</span><span class="m-row-value">' + t.balance + '</span></div>' +
    '</section>';

  // 明细 + 占比
  function detailGroup(title, names, prefix, detail, totalVal, catClass) {
    var h = '<div class="m-detail-group">';
    h += '<div class="m-detail-head ' + catClass + '"><span>' + title + '</span><span>小计 ' + totalVal + '</span></div>';
    for (var i = 0; i < names.length; i++) {
      var v = detail[i] || 0;
      var pct = totalVal === 0 ? 0 : Math.round(v / totalVal * 100);
      h += '<div class="m-detail-row' + (v === 0 ? ' lp-zero' : '') + '">' +
        '<span class="m-row-label">' + prefix + '.' + (i + 1) + ' ' + escapeHtml(names[i]) + '</span>' +
        '<span class="m-row-value">' + v + ' (' + pct + '%)</span></div>';
    }
    h += '</div>';
    return h;
  }
  h += '<section class="m-section"><div class="m-section-title">本周明细 · 占比</div>';
  h += detailGroup('QW 明细',   config.qwNames,   '1', t.qwDetail,   t.qw,   'cat-qw');
  h += detailGroup('GFP 明细',  config.gfpNames,  '2', t.gfpDetail,  t.gfp,  'cat-gfp');
  h += detailGroup('无效浪费',  config.procNames, '3', t.procDetail, t.proc, 'cat-proc');
  h += '</section>';

  // 汇总
  h += '<section class="m-section"><div class="m-section-title">本周汇总</div>' +
    '<div class="m-stat-row"><span class="m-row-label">有效投资</span><span class="m-row-value">' + t.validInvest + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">无效浪费</span><span class="m-row-value">' + t.invalidWaste + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">潜力总数</span><span class="m-row-value">' + t.potential + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">标准数 × 7</span><span class="m-row-value">' + (t.standard) + '</span></div>' +
    '<div class="m-stat-row"><span class="m-row-label">可用数</span><span class="m-row-value">' + t.available + '</span></div>' +
    '</section>';

  // 周复盘（可填写）
  h += renderM_Review(ctx.year, ctx.week, t);

  h += renderM_Footer();

  $('mobile-week-body').innerHTML = h;
  bindMobileEvents();
  bindMobileReviewEvents(ctx.year, ctx.week);
}

// 周复盘：手机端可填写版（与桌面端 review 字段同源，data-mrv / data-mrv-list 命名空间）
var REVIEW_ITEMS = [
  { k: 'keyword',       l: '1. 本周关键词',     t: 'input' },
  { k: 'selfScore',     l: '2. 自我打分',       t: 'input' },
  { k: 'overallReview', l: '3. 总体评价',       t: 'textarea' },
  { k: 'booksRead',     l: '4. 本周读的书',     t: 'textarea' },
  { k: 'moviesWatched', l: '5. 本周看的电影',   t: 'textarea' },
  { k: 'top5Work',      l: '6. 最有意义的5件工作', t: 'list', count: 5 },
  { k: 'top3Stupid',    l: '7. 干的最傻3件事',  t: 'list', count: 3 },
  { k: 'top3Quotes',    l: '8. 最牛3句话',      t: 'list', count: 3 },
  { k: 'dinnerGuests',  l: '9. 请吃饭的人',     t: 'textarea' }
];

function renderM_Review(year, week, totals) {
  var review = getReview(year, week);
  function asList(val, count) {
    var arr;
    if (Array.isArray(val)) arr = val.slice();
    else if (val) arr = String(val).split(/\r?\n/);
    else arr = [];
    while (arr.length < count) arr.push('');
    return arr;
  }
  var h = '<section class="m-section m-edit-zone"><div class="m-section-title">周复盘</div>';
  REVIEW_ITEMS.forEach(function(it) {
    var raw = review[it.k];
    h += '<div class="m-rv-item"><label class="m-rv-label">' + it.l + '</label>';
    if (it.t === 'input') {
      h += '<input class="m-rv-input" type="text" data-mrv="' + it.k + '" value="' + escapeHtml(raw || '') + '">';
    } else if (it.t === 'textarea') {
      h += '<textarea class="m-rv-textarea" data-mrv="' + it.k + '" rows="2">' + escapeHtml(raw || '') + '</textarea>';
    } else { // list
      var arr = asList(raw, it.count);
      for (var n = 0; n < it.count; n++) {
        h += '<input class="m-rv-input m-rv-list-input" type="text" ' +
          'data-mrv-list="' + it.k + '" data-mrv-idx="' + n + '" ' +
          'placeholder="' + (n + 1) + '." value="' + escapeHtml(arr[n]) + '">';
      }
    }
    h += '</div>';
  });
  // 第 10 项：奖励时间，由 balance 自动派生（只读）
  var reward = totals.balance;
  var cls = reward >= 0 ? 'm-rv-reward-pos' : 'm-rv-reward-neg';
  h += '<div class="m-rv-reward ' + cls + '">10. 赢得奖励时间：<strong>' + reward + '</strong></div>';
  h += '</section>';
  return h;
}

function bindMobileReviewEvents(year, week) {
  // 单值输入 / textarea
  document.querySelectorAll('[data-mrv]').forEach(function(el) {
    el.addEventListener('change', function() {
      var r = getReview(year, week);
      r[el.dataset.mrv] = el.value;
      saveReview(year, week, r);
      showToast('已保存');
    });
  });
  // 多框列表：任一框 change，将所有同 key 的框收成数组写回
  document.querySelectorAll('[data-mrv-list]').forEach(function(el) {
    el.addEventListener('change', function() {
      var k = el.dataset.mrvList;
      var arr = [];
      document.querySelectorAll('[data-mrv-list="' + k + '"]').forEach(function(inp) {
        arr.push(inp.value || '');
      });
      var r = getReview(year, week);
      r[k] = arr;
      saveReview(year, week, r);
      showToast('已保存');
    });
  });
}

// =====【移动端事件绑定】=====
function bindMobileEvents() {
  // 顶部 Tab：单日 / 本周累计
  document.querySelectorAll('.page-mobile.active .m-tab').forEach(function(b) {
    b.onclick = function() {
      var v = b.dataset.mv;
      if (v === 'week') {
        showPage('page-mobile-week');
        renderMobileWeek();
      } else {
        showPage('page-mobile-day');
        renderMobileDay();
      }
    };
  });
  // 日期前/后/今天（前进受补齐锁约束；后退/历史周不受限）
  document.querySelectorAll('[data-day-step]').forEach(function(b) {
    b.onclick = function() {
      var step = parseInt(b.dataset.dayStep, 10);
      var d = new Date(mobileState.date + 'T00:00:00Z');
      d.setUTCDate(d.getUTCDate() + step);
      var newDate = dateKey(d);
      if (step > 0) {
        var lock = getMobileLockInfo();
        if (lock && newDate > lock.date) {
          showToast('请先把 ' + lock.date + ' 的 34 格补齐');
          return;
        }
      }
      mobileState.date = newDate;
      renderMobileDay();
    };
  });
  var todayBtn = document.querySelector('[data-go-today]');
  if (todayBtn) todayBtn.onclick = function() {
    var lock = getMobileLockInfo();
    if (lock) {
      mobileState.date = lock.date;
      showToast(lock.date + ' 未补齐，已跳到该日');
    } else {
      mobileState.date = dateKey(today);
    }
    renderMobileDay();
  };
  // 关键事项：单击进入编辑（复用 Windows 弹窗）
  document.querySelectorAll('[data-ki-key]').forEach(function(el) {
    el.onclick = function() { openKeyItemEdit(el.dataset.kiKey); };
  });
  // 日程格：单击进入编辑（复用 Windows 弹窗）
  document.querySelectorAll('[data-cell-id]').forEach(function(el) {
    el.onclick = function() { openCellDialog(el.dataset.cellId); };
  });
  // 切换视图模式
  document.querySelectorAll('[data-mode-switch]').forEach(function(b) {
    b.onclick = function() { setViewMode(b.dataset.modeSwitch); };
  });
  // 数据导出 / 导入（手机端 footer，与桌面端共用 handler）
  document.querySelectorAll('[data-export-data]').forEach(function(b) {
    b.onclick = handleExportData;
  });
  document.querySelectorAll('[data-import-data]').forEach(function(b) {
    b.onclick = handleImportClick;
  });
  // v2.10.0：手机端同步入口（与桌面共用同一个 sync-modal）
  document.querySelectorAll('[data-open-sync]').forEach(function(b) {
    b.onclick = openSyncModal;
  });
  // v2.13.1：状态框点击只切状态
  document.querySelectorAll('[data-ki-status-key]').forEach(function(box) {
    box.onclick = function(e) {
      e.stopPropagation();
      cycleKeyItemStatus(box.dataset.kiStatusKey);
    };
  });
}

// ===== 同步 UI（v2.10.0 / 阶段 3.2） =====
// 与 AppCore.syncClient（在 app-core.js 中）配合：本模块只负责 DOM 事件 + 状态显示
var syncClient = AppCore.syncClient;

function setupSyncUI() {
  if (!syncClient) return;
  var btnSync = $('btn-sync');
  if (btnSync) btnSync.onclick = openSyncModal;

  if ($('btn-sync-test'))  $('btn-sync-test').onclick  = handleSyncTest;
  if ($('btn-sync-pull'))  $('btn-sync-pull').onclick  = handleSyncPull;
  if ($('btn-sync-push'))  $('btn-sync-push').onclick  = handleSyncPush;
  if ($('btn-sync-save'))  $('btn-sync-save').onclick  = handleSyncSaveBtn;
  if ($('btn-sync-close')) $('btn-sync-close').onclick = function() { closeModal('sync-modal'); };

  // v2.13.0：配对 UI
  setupPairUI();

  if ($('sync-hostname')) $('sync-hostname').oninput = updateSyncUrlPreview;
  if ($('sync-port'))     $('sync-port').oninput     = updateSyncUrlPreview;
  if ($('sync-auto-host')) $('sync-auto-host').onchange = function() {
    toggleSyncManualInputs();
    refreshDetectedHost();
    updateSyncUrlPreview();
  };

  // 启动 syncClient（注册 saveChange 监听）
  syncClient.init();
  syncClient.setCurrentWeek(state.year, state.week);

  // 订阅状态变化 → 更新右上角状态灯
  syncClient.onStateChange(updateSyncDot);
  updateSyncDot(syncClient.getState());

  // v2.12.0：监听远程变更推送 → 自动刷新当前周 UI
  window.addEventListener('sync-remote-change', function(e) {
    if (typeof console !== 'undefined') console.log('[sync] 收到远程变更，刷新 UI');
    renderAll();
  });

  // 启动时若已启用同步且 autoPull=true，静默拉取当前周
  // v2.10.1 hotfix：用 buildUrls 长度代替 cfg.hostname 非空判断
  // v2.11.1：延迟到 2.5s，确保 1.5s 离线队列 flush 先完成，避免
  // 服务端旧数据覆盖本地尚未推送的离线编辑。
  var cfg = syncClient.getSyncConfig();
  if (cfg.enabled && cfg.autoPull && syncClient.buildUrls(cfg).length > 0) {
    setTimeout(function() {
      // 先 flush 离线队列（确保本地离线编辑先推上去），再拉取
      syncClient.flushOfflineQueue().then(function() {
        return syncClient.pullWeek(state.year, state.week);
      }).then(function(r) {
        if (r && r.applied) {
          if (typeof console !== 'undefined') console.log('[sync] 启动拉取成功');
          renderAll();
        } else {
          if (typeof console !== 'undefined') console.log('[sync] 启动拉取：服务器无该周数据或队列优先推送');
        }
      }).catch(function(err) {
        if (typeof console !== 'undefined') console.warn('[sync] 启动拉取失败:', err.message);
      });
    }, 2500);
  }
}

function openSyncModal() {
  var cfg = syncClient.getSyncConfig();
  $('sync-enabled').checked = !!cfg.enabled;
  if ($('sync-auto-host')) $('sync-auto-host').checked = cfg.autoHost !== false;
  $('sync-hostname').value = cfg.hostname || '';
  $('sync-port').value = cfg.port || syncClient.DEFAULT_PORT;
  $('sync-lastip').value = cfg.lastIP || '';
  toggleSyncManualInputs();
  refreshDetectedHost();
  updateSyncUrlPreview();
  updateSyncStatusUI();
  $('sync-log').innerHTML = '';
  $('pair-qr-area').style.display = 'none';  // v2.13.0：关闭面板时隐藏 QR
  refreshDeviceList();  // v2.13.0：刷新设备列表
  openModal('sync-modal');
}

function readSyncModalConfig() {
  var auto = $('sync-auto-host') ? $('sync-auto-host').checked : true;
  return {
    enabled: $('sync-enabled').checked,
    autoHost: auto,
    hostname: ($('sync-hostname').value || '').trim(),
    port: parseInt($('sync-port').value, 10) || syncClient.DEFAULT_PORT,
    lastIP: ($('sync-lastip').value || '').trim()
  };
}

// v2.10.1：autoHost 勾选时禁用手动输入框，避免误导。
function toggleSyncManualInputs() {
  var auto = $('sync-auto-host') ? $('sync-auto-host').checked : true;
  if ($('sync-hostname')) $('sync-hostname').disabled = auto;
  if ($('sync-port'))     $('sync-port').disabled     = auto;
}

// v2.10.1：根据 autoHost 当前状态刷新「同步服务器（自动检测）」表单。
function refreshDetectedHost() {
  var el = $('sync-detected');
  if (!el) return;
  var cfg = readSyncModalConfig();
  var urls = syncClient.buildUrls(cfg);
  if (urls.length > 0) {
    el.value = urls[0];
  } else {
    el.value = '';
  }
}

function updateSyncUrlPreview() {
  var cfg = readSyncModalConfig();
  var urls = syncClient.buildUrls(cfg);
  var el = $('sync-url-preview');
  if (!el) return;
  if (urls.length === 0) {
    el.textContent = '尝试 URL：（未能从浏览器地址识别，请在高级设置填写电脑名）';
  } else {
    el.innerHTML = '尝试 URL（按顺序 fallback）：<br>' + urls.map(function(u, i) {
      return (i + 1) + '. <code>' + u + '</code>';
    }).join('<br>');
  }
  refreshDetectedHost();
}

// v2.13.0：扫码绑定 + 设备列表
function setupPairUI() {
  var btn = $('btn-pair-start');
  if (btn) btn.onclick = handlePairStart;
  var btnConfirm = $('btn-pair-confirm');
  if (btnConfirm) btnConfirm.onclick = handlePairConfirm;
  refreshDeviceList();
}

function handlePairStart() {
  $('pair-qr-area').style.display = 'none';
  logSync('正在生成配对码…', 'info');
  syncClient.pairStart().then(function(info) {
    var data = {
      hostname: info.hostname,
      ip: (info.lanIPs && info.lanIPs[0]) ? info.lanIPs[0].ip : '',
      port: info.port,
      httpsPort: info.httpsPort,
      code: info.pairCode
    };
    var jsonStr = JSON.stringify(data);
    // 用 qrcode-generator 生成 QR
    if (typeof qrcode !== 'undefined') {
      var qr = qrcode(0, 'M');
      qr.addData(jsonStr);
      qr.make();
      $('pair-qr-code').innerHTML = qr.createSvgTag({ scalable: true, cellSize: 3 });
    } else {
      $('pair-qr-code').innerHTML = '<div style="padding:20px;color:#dc2626;">QR 库未加载，请刷新页面。<br>配对码：<b>' + info.pairCode + '</b></div>';
    }
    $('pair-code-text').textContent = info.pairCode;
    $('pair-qr-area').style.display = '';
    logSync('配对码已生成：' + info.pairCode + '（5 分钟有效）。等待手机扫码…', 'info');
    // 每 5s 检查设备列表变化
    var checkCount = 0;
    var checkTimer = setInterval(function() {
      checkCount++;
      refreshDeviceList();
      if (checkCount >= 60) { clearInterval(checkTimer); } // 5 分钟后停止
    }, 5000);
    // 保存以便关闭面板时清理
    $('pair-qr-area')._pairTimer = checkTimer;
  }).catch(function(err) {
    logSync('生成配对码失败：' + err.message, 'error');
  });
}

function handlePairConfirm() {
  var codeInput = $('inp-pair-code');
  if (!codeInput) return;
  var code = (codeInput.value || '').trim();
  if (!/^\d{6}$/.test(code)) {
    logSync('请输入 6 位数字配对码', 'error');
    return;
  }
  logSync('正在验证配对码…', 'info');
  var platform = /iPhone/i.test(navigator.userAgent) ? 'ios'
    : (/Android|Huawei|HUAWEI|HONOR/i.test(navigator.userAgent) ? 'android' : 'unknown');
  syncClient.pairConfirm(code, '手机', platform).then(function(info) {
    syncClient.saveDeviceToken(info.token);
    logSync('设备已绑定！令牌已保存。', 'info');
    codeInput.value = '';
    refreshDeviceList();
    // 绑好后立即拉取一次当前周数据
    syncClient.flushOfflineQueue().then(function() {
      return syncClient.pullWeek(state.year, state.week);
    }).then(function(r) {
      if (r && r.applied) renderAll();
    }).catch(function() {});
  }).catch(function(err) {
    logSync('绑定失败：' + err.message, 'error');
  });
}

function refreshDeviceList() {
  var el = $('pair-device-list');
  if (!el) return;
  syncClient.getDevices().then(function(devices) {
    if (!Array.isArray(devices) || devices.length === 0) {
      el.innerHTML = '<div style="font:12px/1.4 system-ui,sans-serif;color:#94a3b8;">暂无已绑定设备</div>';
      return;
    }
    var h = '<div style="font:13px/1.6 system-ui,sans-serif;margin-top:8px;"><b>已绑定设备（' + devices.length + '/4）</b></div>';
    devices.forEach(function(d) {
      var ago = d.lastSyncAt ? Math.round((Date.now() - d.lastSyncAt) / 60000) : '?';
      h += '<div style="display:flex;align-items:center;justify-content:space-between;padding:6px 8px;margin:4px 0;background:#f8fafc;border-radius:6px;font:12px/1.4 system-ui,sans-serif;">' +
        '<span>' + (d.platform === 'windows' ? '💻' : '📱') + ' <b>' + d.name + '</b> · ' + d.platform +
        ' · 最后同步 ' + (ago === 0 ? '刚刚' : ago + '分钟前') + '</span>' +
        '<button onclick="deleteDevice(\'' + d.id + '\')" style="font:11px/1.4 system-ui,sans-serif;color:#dc2626;border:none;background:none;cursor:pointer;" title="解除绑定">✕</button>' +
        '</div>';
    });
    el.innerHTML = h;
  }).catch(function() {});
}

function deleteDevice(deviceId) {
  if (!confirm('确定解除此设备的绑定？该设备将无法再同步数据。')) return;
  syncClient.deleteDevice(deviceId).then(function() {
    logSync('设备已解绑', 'info');
    refreshDeviceList();
  }).catch(function(err) {
    logSync('解绑失败：' + err.message, 'error');
  });
}
// 暴露到全局供 onclick 调用
window.deleteDevice = deleteDevice;

function logSync(msg, level) {
  var el = $('sync-log');
  if (!el) return;
  var line = document.createElement('div');
  line.className = 'log-' + (level || 'info');
  var ts = new Date().toLocaleTimeString();
  line.textContent = '[' + ts + '] ' + msg;
  el.appendChild(line);
  el.scrollTop = el.scrollHeight;
}

function handleSyncTest() {
  syncClient.saveSyncConfig(readSyncModalConfig());
  logSync('测试连接...', 'info');
  syncClient.testConnection().then(function(r) {
    logSync('✓ 已连通 → ' + r.base, 'ok');
    var info = r.info || {};
    var ip = (info.lanIPs && info.lanIPs[0] && info.lanIPs[0].ip) || '无';
    logSync('  主机=' + info.hostname + '  IP=' + ip + '  HostID=' + (info.hostId || '').slice(0, 8) + '…', 'info');
    var cfg = syncClient.getSyncConfig();
    $('sync-lastip').value = cfg.lastIP || '';
    updateSyncStatusUI();
  }).catch(function(err) {
    logSync('✗ 连接失败: ' + (err.message || err), 'err');
    updateSyncStatusUI();
  });
}

function handleSyncPull() {
  syncClient.saveSyncConfig(readSyncModalConfig());
  var y = state.year, w = state.week;
  logSync('拉取本地正在显示的周：' + y + '/W' + w + '...', 'info');
  syncClient.pullWeek(y, w).then(function(r) {
    if (r.applied) {
      logSync('✓ 拉取成功，已覆盖本地数据', 'ok');
      renderAll();
    } else {
      logSync('· 服务器还没有该周的数据（404），本地未变动', 'info');
    }
    updateSyncStatusUI();
  }).catch(function(err) {
    logSync('✗ 拉取失败: ' + (err.message || err), 'err');
    updateSyncStatusUI();
  });
}

function handleSyncPush() {
  syncClient.saveSyncConfig(readSyncModalConfig());
  var y = state.year, w = state.week;
  logSync('推送本地正在显示的周：' + y + '/W' + w + '...', 'info');
  syncClient.pushWeek(y, w).then(function(r) {
    var resp = r.response || {};
    logSync('✓ 推送成功 (cells=' + (resp.cellsCount || 0) + '  items=' + (resp.keyitemsCount || 0) +
            '  st=' + (resp.keyitemStatusCount || 0) +
            '  config=' + (resp.hasConfig ? '✓' : '×') +
            '  review=' + (resp.hasReview ? '✓' : '×') + ')', 'ok');
    updateSyncStatusUI();
  }).catch(function(err) {
    logSync('✗ 推送失败: ' + (err.message || err), 'err');
    updateSyncStatusUI();
  });
}

function handleSyncSaveBtn() {
  var cfg = syncClient.saveSyncConfig(readSyncModalConfig());
  var hostDesc = cfg.autoHost ? '自动(' + (syncClient.getEffectiveHost(cfg) || '?') + ':' + syncClient.getEffectivePort(cfg) + ')'
                              : (cfg.hostname + ':' + cfg.port);
  logSync('设置已保存：enabled=' + cfg.enabled + ' 服务=' + hostDesc, 'ok');
  updateSyncStatusUI();
  updateSyncDot(syncClient.getState());
}

function updateSyncStatusUI() {
  if (!$('sync-status-text')) return;
  var s = syncClient.getState();
  var cfg = s.config;
  var text = '', detail = '';
  if (!cfg.enabled) {
    text = '● 同步已关闭';
    detail = '勾选「启用同步」后点 "测试连接" 即可使用（默认自动检测主机）';
  } else if (s.status === 'connected') {
    text = '✅ 已连接';
    var info = s.lastInfo || {};
    var hostShown = info.hostname || syncClient.getEffectiveHost(cfg) || cfg.hostname || '';
    detail = hostShown +
             (s.lastPushAt ? '  上次推送 ' + new Date(s.lastPushAt).toLocaleTimeString() : '') +
             (s.lastPullAt ? '  上次拉取 ' + new Date(s.lastPullAt).toLocaleTimeString() : '');
  } else if (s.status === 'connecting') {
    text = '🟡 连接中…';
  } else if (s.status === 'error') {
    text = '❌ 连接错误';
    detail = s.lastError || '';
  } else {
    text = '⚪ 已启用，未连接';
    detail = '点 "测试连接" 验证主机可达';
  }
  $('sync-status-text').textContent = text;
  $('sync-status-detail').textContent = detail;
}

function updateSyncDot(s) {
  // v2.11.0 hotfix：桌面端 dot 有 id="sync-dot"，手机端 footer 那个 dot 只有 class
  // 没 id。原实现 $('sync-dot') 只能更新桌面那个，手机端 dot 永远停在初次渲染
  // 的颜色（首次 renderM_Footer 时算出来的，常是蓝色 pending）。改成
  // querySelectorAll('.sync-dot') 同步刷新所有 dot。
  var dots = document.querySelectorAll('.sync-dot');
  if (!dots.length) return;
  s = s || syncClient.getState();
  var cls;
  if (!s.config.enabled) cls = 'sync-dot-disabled';
  else if (s.pendingPushTimer || s.pendingPushWeek) cls = 'sync-dot-pending';
  else if (s.status === 'connected') cls = 'sync-dot-connected';
  else if (s.status === 'connecting') cls = 'sync-dot-connecting';
  else if (s.status === 'error') cls = 'sync-dot-error';
  else cls = 'sync-dot-disconnected';
  var title = s.lastError ? ('错误: ' + s.lastError) : (s.status + (s.config.enabled ? '' : '（同步已关闭）'));
  for (var i = 0; i < dots.length; i++) {
    dots[i].className = 'sync-dot ' + cls;
    dots[i].title = title;
  }
  // 顺带刷新弹窗内的状态行（若打开）
  if (document.getElementById('sync-modal') && document.getElementById('sync-modal').classList.contains('active')) {
    updateSyncStatusUI();
  }
}

// ===== 启动 =====
document.addEventListener('DOMContentLoaded', init);
})();
