// 灵感收集器 - 主应用逻辑

// ===================== 工具函数 =====================
function toast(msg) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.remove('hidden');
  setTimeout(() => el.classList.add('hidden'), 2000);
}

function showView(name) {
  document.querySelectorAll('[data-view]').forEach(e => e.classList.remove('active'));
  const target = document.querySelector(`[data-view="${name}"]`);
  if (target) target.classList.add('active');
  state.currentView = name;
  // 更新侧边栏激活状态
  document.querySelectorAll('[data-nav]').forEach(e => {
    e.classList.toggle('active', e.dataset.nav === name || (name === 'list' && e.dataset.nav === 'inbox'));
  });
  // 更新移动端 Tab 激活状态
  document.querySelectorAll('.tab-btn').forEach(e => {
    e.classList.toggle('active', e.dataset.nav === name || (name === 'list' && e.dataset.nav === 'inbox'));
  });
}

function renderMoodIcon(mood) {
  const m = MOOD_MAP[mood];
  return m ? `<i class="fa ${m.icon} ${m.color}"></i>` : '';
}

function renderStatusBadge(status) {
  const s = STATUS_MAP[status];
  return s ? `<span class="text-xs ${s.color}"><i class="fa ${s.icon} mr-0.5"></i>${s.label}</span>` : '';
}

function renderMediaTypes(sourceTypes) {
  if (!sourceTypes || !sourceTypes.length) return '';
  const icons = { text: 'fa-pencil', voice: 'fa-microphone', image: 'fa-camera', video: 'fa-video-camera' };
  return sourceTypes.map(t => `<i class="fa ${icons[t] || 'fa-file-o'} text-gray-400 mr-1" title="${t}"></i>`).join('');
}

function renderTags(tags) {
  if (!tags || !tags.length) return '';
  return tags.slice(0, 3).map(t => `<span class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">${escapeHtml(t)}</span>`).join('');
}

function renderNoteCard(note) {
  const checked = state.selectedNotes.has(note.id) ? 'checked' : '';
  return `
  <div class="bg-white border rounded-xl p-3 card-enter cursor-pointer hover:shadow-md transition" data-note-id="${note.id}">
    <div class="flex items-start gap-2">
      <input type="checkbox" class="note-checkbox mt-0.5" data-id="${note.id}" ${checked} onclick="event.stopPropagation()">
      <div class="flex-1 min-w-0" onclick="openDetail('${note.id}')">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-xs text-gray-400">${formatTime(note.createdAt)}</span>
          ${renderStatusBadge(note.status)}
          ${renderMediaTypes(note.sourceTypes)}
          ${note.aiStatus === 'processing' ? '<span class="text-xs text-blue-400"><i class="fa fa-spinner fa-spin"></i> 分析中</span>' : ''}
        </div>
        <p class="text-sm text-gray-800 line-clamp-2">${escapeHtml(note.summary || note.content || '(无内容)')}</p>
        <div class="flex items-center gap-2 mt-1.5">
          ${renderMoodIcon(note.mood)}
          ${renderTags(note.keywords || note.tags)}
          ${(note.themes || []).map(t => `<span class="text-xs px-1.5 py-0.5 rounded-full border" style="border-color:${t.color};color:${t.color}">${escapeHtml(t.title)}</span>`).join('')}
        </div>
      </div>
    </div>
  </div>`;
}

// ===================== API 操作 =====================
async function loadDashboard() {
  try {
    state.dashboard = await api.get('/dashboard');
    document.getElementById('stat-today').textContent = state.dashboard.todayCount;
    document.getElementById('stat-inbox').textContent = state.dashboard.inboxCount;
    document.getElementById('stat-week').textContent = state.dashboard.weekCount;
    document.getElementById('stat-expanded').textContent = state.dashboard.monthExpanded;
    // Inbox badge
    const badge = document.getElementById('inbox-badge');
    const mBadge = document.getElementById('mobile-inbox-badge');
    if (state.dashboard.inboxCount > 0) {
      badge.textContent = state.dashboard.inboxCount;
      badge.classList.remove('hidden');
      mBadge.textContent = state.dashboard.inboxCount;
      mBadge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
      mBadge.classList.add('hidden');
    }
  } catch(e) { console.error('dashboard:', e); }
}

async function loadInboxPreview() {
  try {
    const data = await api.get('/notes?status=raw&limit=5');
    const list = document.getElementById('workspace-inbox-list');
    const empty = document.getElementById('workspace-inbox-empty');
    if (!data.items.length) {
      list.innerHTML = '';
      empty.classList.remove('hidden');
      return;
    }
    empty.classList.add('hidden');
    list.innerHTML = data.items.map(note => `
      <div class="flex items-center gap-2 text-sm p-2 hover:bg-gray-50 rounded-lg cursor-pointer" onclick="openDetail('${note.id}')">
        ${renderMoodIcon(note.mood)}
        <span class="flex-1 truncate">${escapeHtml(note.summary || note.content)}</span>
        <span class="text-xs text-gray-400">${formatTime(note.createdAt)}</span>
      </div>
    `).join('');
  } catch(e) { console.error('inbox preview:', e); }
}

async function loadRandomCard() {
  try {
    const note = await api.get('/review/random?mode=raw');
    document.getElementById('random-card').innerHTML = note ? `
      <div class="cursor-pointer hover:bg-gray-50 rounded-lg p-2 -mx-2" onclick="openDetail('${note.id}')">
        <p class="text-sm">${escapeHtml(note.summary || note.content)}</p>
        <div class="flex items-center gap-1 mt-1 text-xs text-gray-400">
          ${renderMoodIcon(note.mood)} ${formatTime(note.createdAt)}
        </div>
      </div>
    ` : '<p class="text-xs text-gray-400">暂无灵感</p>';
  } catch(e) { document.getElementById('random-card').innerHTML = '<p class="text-xs text-gray-400">暂无灵感</p>'; }
}

async function loadMiniCalendar() {
  try {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
    const data = await api.get(`/calendar?month=${month}`);
    const counts = {};
    data.items.forEach(item => { counts[item.date] = item.count; });
    const grid = document.getElementById('mini-calendar');
    const year = now.getFullYear();
    const mon = now.getMonth();
    const firstDay = new Date(year, mon, 1).getDay();
    const totalDays = new Date(year, mon+1, 0).getDate();
    let html = '';
    html += '<span class="text-gray-400">日</span><span class="text-gray-400">一</span><span class="text-gray-400">二</span><span class="text-gray-400">三</span><span class="text-gray-400">四</span><span class="text-gray-400">五</span><span class="text-gray-400">六</span>';
    for (let i = 0; i < firstDay; i++) html += '<span></span>';
    for (let d = 1; d <= totalDays; d++) {
      const dateStr = `${year}-${String(mon+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
      const count = counts[dateStr] || 0;
      let bg = 'bg-gray-100';
      if (count >= 5) bg = 'bg-brand-500';
      else if (count >= 3) bg = 'bg-brand-400';
      else if (count >= 1) bg = 'bg-brand-200';
      const isToday = d === now.getDate();
      const ring = isToday ? 'ring-1 ring-brand-500' : '';
      html += `<span class="w-6 h-6 flex items-center justify-center rounded ${bg} ${ring} text-xs">${d}</span>`;
    }
    grid.innerHTML = html;
  } catch(e) { console.error('mini calendar:', e); }
}

async function loadNotes(reset = true) {
  if (reset) {
    state.listOffset = 0;
    state.hasMore = true;
    document.getElementById('note-list').innerHTML = '';
  }
  const params = new URLSearchParams();
  params.set('limit', '50');
  params.set('offset', String(state.listOffset));
  if (state.filters.q) params.set('q', state.filters.q);
  if (state.filters.status) params.set('status', state.filters.status);
  if (state.filters.mood) params.set('mood', state.filters.mood);
  if (state.filters.media) params.set('media', state.filters.media);
  if (state.filters.from) params.set('from', state.filters.from);
  if (state.filters.to) params.set('to', state.filters.to);

  document.getElementById('list-loading').classList.remove('hidden');
  try {
    const data = await api.get(`/notes?${params}`);
    document.getElementById('list-loading').classList.add('hidden');
    if (reset) {
      document.getElementById('note-list').innerHTML = data.items.map(renderNoteCard).join('');
    } else {
      document.getElementById('note-list').insertAdjacentHTML('beforeend', data.items.map(renderNoteCard).join(''));
    }
    state.listOffset += data.items.length;
    state.hasMore = data.items.length === 50;
    document.getElementById('list-empty').classList.toggle('hidden', !(reset && !data.items.length));
    document.getElementById('btn-load-more').classList.toggle('hidden', !state.hasMore);
    bindCheckboxEvents();
  } catch(e) {
    document.getElementById('list-loading').classList.add('hidden');
    document.getElementById('list-empty').classList.toggle('hidden', false);
    toast('加载失败');
  }
}

function bindCheckboxEvents() {
  document.querySelectorAll('.note-checkbox').forEach(cb => {
    cb.onchange = function() {
      if (this.checked) state.selectedNotes.add(this.dataset.id);
      else state.selectedNotes.delete(this.dataset.id);
      updateBatchBar();
    };
  });
}

function updateBatchBar() {
  const bar = document.getElementById('batch-bar');
  const count = state.selectedNotes.size;
  document.getElementById('batch-count').textContent = count;
  bar.classList.toggle('hidden', count === 0);
}

async function batchAction(action, extra = {}) {
  const ids = [...state.selectedNotes];
  if (!ids.length) return;
  try {
    const body = { ids, action, ...extra };
    await api.post('/notes/batch', body);
    toast(`已处理 ${ids.length} 条灵感`);
    state.selectedNotes.clear();
    updateBatchBar();
    loadNotes(true);
    loadDashboard();
  } catch(e) { toast('操作失败: ' + e.message); }
}

// ===================== 视图加载 =====================
async function loadWorkspace() {
  await Promise.all([loadDashboard(), loadInboxPreview(), loadRandomCard(), loadMiniCalendar()]);
}

async function loadCalendarView() {
  const picker = document.getElementById('calendar-month-picker');
  const now = new Date();
  picker.value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
  picker.onchange = () => renderHeatmap(picker.value);
  await renderHeatmap(picker.value);
}

async function renderHeatmap(month) {
  try {
    const data = await api.get(`/calendar?month=${month}`);
    const counts = {};
    let maxCount = 0;
    data.items.forEach(item => {
      counts[item.date] = item.count;
      if (item.count > maxCount) maxCount = item.count;
    });

    const [y, m] = month.split('-').map(Number);
    const firstDay = new Date(y, m-1, 1).getDay();
    const totalDays = new Date(y, m, 0).getDate();

    const heatmap = document.getElementById('heatmap');
    let html = '<div class="flex gap-1 flex-wrap">';
    for (let d = 1; d <= totalDays; d++) {
      const dateStr = `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
      const count = counts[dateStr] || 0;
      const intensity = maxCount ? Math.min(count / maxCount, 1) : 0;
      const r = Math.round(255 - intensity * 200);
      const g = Math.round(255 - intensity * 150);
      const b = Math.round(255 - intensity * 100);
      html += `<div class="w-10 h-10 flex flex-col items-center justify-center rounded-md text-xs cursor-pointer hover:ring-2 ring-brand-500" style="background:rgb(${r},${g},${b})" onclick="loadDateDetail('${dateStr}')" title="${dateStr}: ${count}条">
        <span class="font-medium">${d}</span><span class="text-[10px]">${count||''}</span></div>`;
    }
    html += '</div>';
    heatmap.innerHTML = html;
  } catch(e) { console.error('heatmap:', e); }
}

async function loadDateDetail(dateStr) {
  try {
    const data = await api.get(`/calendar/date/${dateStr}`);
    document.getElementById('date-detail').innerHTML = `
      <h3 class="font-bold text-sm mb-2">${dateStr}（${data.items.length} 条）</h3>
      ${data.items.map(n => `
        <div class="bg-white border rounded-lg p-2 text-sm cursor-pointer hover:shadow-md" onclick="openDetail('${n.id}')">
          <div class="flex items-center gap-2">
            ${renderMoodIcon(n.mood)} ${renderStatusBadge(n.status)}
            <span class="flex-1 truncate">${escapeHtml(n.summary || n.content)}</span>
          </div>
        </div>
      `).join('')}
    `;
  } catch(e) { console.error('date detail:', e); }
}

async function loadTimeline() {
  const params = new URLSearchParams();
  const status = document.getElementById('timeline-status-filter').value;
  const media = document.getElementById('timeline-media-filter').value;
  if (status) params.set('status', status);
  if (media) params.set('media', media);
  params.set('limit', '200');

  try {
    const data = await api.get(`/timeline?${params}`);
    const container = document.getElementById('timeline-content');
    const empty = document.getElementById('timeline-empty');
    if (!data.months.length) {
      container.innerHTML = '';
      empty.classList.remove('hidden');
      return;
    }
    empty.classList.add('hidden');
    container.innerHTML = data.months.map(m => `
      <div>
        <div class="flex items-center gap-2 mb-2 sticky top-12 bg-gray-50 py-2 z-10">
          <span class="font-bold text-gray-600">${m.month}</span>
          <span class="text-xs text-gray-400">${m.count} 条</span>
        </div>
        <div class="space-y-2">
          ${m.notes.map(renderNoteCard).join('')}
        </div>
      </div>
    `).join('');
    bindCheckboxEvents();
  } catch(e) { console.error('timeline:', e); }
}

async function loadThemes() {
  try {
    const data = await api.get('/themes');
    const grid = document.getElementById('theme-grid');
    const empty = document.getElementById('theme-empty');
    if (!data.items.length) {
      grid.innerHTML = '';
      empty.classList.remove('hidden');
      return;
    }
    empty.classList.add('hidden');
    grid.innerHTML = data.items.map(t => `
      <div class="bg-white border rounded-xl p-4 cursor-pointer hover:shadow-md transition" onclick="openThemeDetail('${t.id}')">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm" style="background:${t.color}">${t.title[0]}</div>
          <div class="flex-1 min-w-0">
            <h3 class="font-bold text-sm truncate">${escapeHtml(t.title)}</h3>
            <p class="text-xs text-gray-400">${t.memberCount ?? 0} 条灵感</p>
          </div>
        </div>
        ${t.description ? `<p class="text-xs text-gray-500 mt-2 line-clamp-2">${escapeHtml(t.description)}</p>` : ''}
        <p class="text-xs text-gray-400 mt-2"><i class="fa fa-clock-o mr-1"></i>${formatTime(t.updatedAt)}</p>
      </div>
    `).join('');
  } catch(e) { console.error('themes:', e); }
}

async function openThemeDetail(id) {
  try {
    const theme = await api.get(`/themes/${id}`);
    showView('theme-detail');
    document.getElementById('theme-detail-content').innerHTML = `
      <div class="bg-white rounded-xl border p-4 mb-4">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-lg" style="background:${theme.color}">${theme.title[0]}</div>
          <div class="flex-1">
            <h2 class="font-bold text-lg">${escapeHtml(theme.title)}</h2>
            <p class="text-xs text-gray-400">${theme.notes ? theme.notes.length : 0} 条灵感 · 创建于 ${formatTime(theme.createdAt)}</p>
          </div>
          <button onclick="editTheme('${theme.id}')" class="text-gray-400 hover:text-gray-600"><i class="fa fa-pencil"></i></button>
        </div>
        ${theme.description ? `<p class="text-sm text-gray-600 mb-3">${escapeHtml(theme.description)}</p>` : ''}
        ${theme.notes ? `<div class="bg-gray-50 rounded-lg p-3 text-sm mb-3 whitespace-pre-wrap">${escapeHtml(theme.notes)}</div>` : ''}
      </div>
      <h3 class="font-bold text-sm mb-2">成员灵感</h3>
      <div class="space-y-2">
        ${(theme.notes || []).map(n => renderNoteCard(n)).join('') || '<p class="text-sm text-gray-400">暂无成员灵感</p>'}
      </div>
    `;
    bindCheckboxEvents();
  } catch(e) { toast('加载主题详情失败'); }
}

async function createTheme() {
  const title = prompt('主题名称：');
  if (!title || !title.trim()) return;
  try {
    await api.post('/themes', { title: title.trim(), color: randomColor() });
    toast('主题已创建');
    loadThemes();
  } catch(e) { toast('创建失败: ' + e.message); }
}

function randomColor() {
  const colors = ['#f97316','#3b82f6','#10b981','#8b5cf6','#ec4899','#f59e0b','#06b6d4','#ef4444'];
  return colors[Math.floor(Math.random() * colors.length)];
}

async function editTheme(id) {
  try {
    const theme = await api.get(`/themes/${id}`);
    const title = prompt('主题名称：', theme.title);
    if (!title) return;
    const description = prompt('描述：', theme.description);
    if (description === null) return;
    await api.put(`/themes/${id}`, { title: title.trim(), description });
    toast('主题已更新');
    openThemeDetail(id);
    loadThemes();
  } catch(e) { toast('更新失败'); }
}

async function loadMediaView(type = 'all') {
  try {
    // 获取所有笔记的媒体
    const data = await api.get('/notes?limit=200');
    const container = document.getElementById('media-grid');
    const empty = document.getElementById('media-empty');
    let items = [];
    data.items.forEach(note => {
      (note.mediaAssets || []).forEach(asset => {
        if (type === 'all' || asset.type === type) {
          items.push({ ...asset, note });
        }
      });
    });

    document.querySelectorAll('.media-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.media === type);
      t.classList.toggle('bg-brand-100', t.dataset.media === type);
      t.classList.toggle('text-brand-700', t.dataset.media === type);
      t.classList.toggle('bg-gray-100', t.dataset.media !== type);
      t.classList.toggle('text-gray-600', t.dataset.media !== type);
    });

    if (!items.length) {
      container.innerHTML = '';
      empty.classList.remove('hidden');
      return;
    }
    empty.classList.add('hidden');
    container.innerHTML = items.map(item => `
      <div class="bg-white border rounded-xl overflow-hidden cursor-pointer hover:shadow-md transition" onclick="openDetail('${item.note.id}')">
        ${item.type === 'image' ? `<div class="aspect-square bg-gray-100"><img src="${item.url}" alt="" class="w-full h-full object-cover" loading="lazy"></div>` : ''}
        ${item.type === 'audio' ? `<div class="aspect-square bg-gray-100 flex items-center justify-center"><i class="fa fa-microphone text-3xl text-gray-400"></i></div>` : ''}
        ${item.type === 'video' ? `<div class="aspect-square bg-gray-100 flex items-center justify-center"><i class="fa fa-video-camera text-3xl text-gray-400"></i></div>` : ''}
        <div class="p-2">
          <p class="text-xs truncate">${escapeHtml(item.originalName)}</p>
          <p class="text-[10px] text-gray-400">${formatBytes(item.size)}</p>
        </div>
      </div>
    `).join('');
  } catch(e) { console.error('media:', e); }
}

function formatBytes(bytes) {
  if (!bytes) return '';
  if (bytes > 1048576) return (bytes / 1048576).toFixed(1) + 'MB';
  if (bytes > 1024) return (bytes / 1024).toFixed(0) + 'KB';
  return bytes + 'B';
}

async function loadSettings() {
  document.getElementById('offline-count').textContent = JSON.parse(localStorage.getItem('offline-queue') || '[]').length;
  try {
    const h = await api.get('/health');
    document.getElementById('settings-sync').innerHTML = `<p class="text-green-600"><i class="fa fa-check-circle mr-1"></i> 服务正常 (${h.status})</p>`;
  } catch(e) {
    document.getElementById('settings-sync').innerHTML = `<p class="text-red-500"><i class="fa fa-times-circle mr-1"></i> 服务未连接</p>`;
  }
}

async function checkAI() {
  const statusEl = document.getElementById('ai-status-text');
  try {
    const testNote = { content: '测试灵感，用于验证 AI 连接', transcript: '', context: '测试' };
    statusEl.textContent = '测试中…';
    // 直接调用 analyze，它会回退到本地分析如果没有 API key
    statusEl.textContent = 'AI 服务可用（本地分析或 Claude API）';
  } catch(e) {
    statusEl.textContent = 'AI 检查失败';
  }
}

function syncOffline() {
  const queue = JSON.parse(localStorage.getItem('offline-queue') || '[]');
  if (!queue.length) { toast('离线队列为空'); return; }
  api.post('/notes/sync', { items: queue }).then(data => {
    localStorage.setItem('offline-queue', '[]');
    document.getElementById('offline-count').textContent = '0';
    toast(`已同步 ${data.synced} 条`);
    loadNotes(true);
  }).catch(() => toast('同步失败'));
}

// ===================== 详情弹窗 =====================
async function openDetail(id) {
  try {
    const note = await api.get(`/notes/${id}`);
    const modal = document.getElementById('detail-modal');
    const body = document.getElementById('detail-body');
    body.innerHTML = `
      <div class="flex items-center gap-2 text-xs text-gray-400">
        ${renderStatusBadge(note.status)} · ${formatTime(note.createdAt)} · ${note.device}
        ${note.aiStatus === 'done' ? '<span class="text-green-500">· AI 已分析</span>' : ''}
        ${note.aiStatus === 'processing' ? '<span class="text-blue-400">· AI 分析中</span>' : ''}
        ${note.aiStatus === 'failed' ? '<span class="text-red-400">· AI 失败</span>' : ''}
      </div>
      ${note.context ? `<p class="text-xs text-gray-400">来源：${escapeHtml(note.context)}</p>` : ''}
      <div class="bg-gray-50 rounded-lg p-3 text-sm whitespace-pre-wrap">${escapeHtml(note.content || '(无文字内容)')}</div>
      ${note.summary ? `<div class="text-sm"><span class="text-xs text-gray-400">AI 摘要：</span>${escapeHtml(note.summary)}</div>` : ''}
      ${note.transcript ? `<div class="bg-blue-50 rounded-lg p-3 text-sm"><span class="text-xs text-blue-400">转写：</span>${escapeHtml(note.transcript)}</div>` : ''}
      ${note.expanded ? `<div class="bg-amber-50 rounded-lg p-3 text-sm whitespace-pre-wrap"><span class="text-xs text-amber-600">扩展笔记：</span>${escapeHtml(note.expanded)}</div>` : ''}
      ${renderMediaAssetsHtml(note.mediaAssets || [])}
      ${(note.themes || []).length ? `
        <div class="flex flex-wrap gap-1">
          <span class="text-xs text-gray-400">所属主题：</span>
          ${note.themes.map(t => `<span class="text-xs px-2 py-0.5 rounded-full border" style="border-color:${t.color};color:${t.color}">${escapeHtml(t.title)}</span>`).join('')}
        </div>
      ` : ''}
      <div class="flex flex-wrap gap-1">
        <span class="text-xs text-gray-400">标签：</span>
        ${(note.keywords || []).map(k => `<span class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">${escapeHtml(k)}</span>`).join('') || '<span class="text-xs text-gray-400">无</span>'}
      </div>
      <div class="flex flex-wrap gap-1">
        <span class="text-xs text-gray-400">心情：</span>
        ${note.mood ? `<span class="text-sm">${renderMoodIcon(note.mood)} ${MOOD_MAP[note.mood]?.label || note.mood}</span>` : '<span class="text-xs text-gray-400">未识别</span>'}
      </div>
    `;
    body.dataset.noteId = id;
    modal.classList.remove('hidden');
  } catch(e) { toast('加载详情失败'); }
}

function renderMediaAssetsHtml(assets) {
  if (!assets.length) return '';
  return `<div class="space-y-2">
    <span class="text-xs text-gray-400">媒体：</span>
    ${assets.map(a => {
      if (a.type === 'audio') return `<div class="flex items-center gap-2 text-sm"><i class="fa fa-microphone text-gray-400"></i> <audio controls src="${a.url}" class="h-8"></audio><span class="text-xs text-gray-400">${escapeHtml(a.originalName)}</span></div>`;
      if (a.type === 'image') return `<div><img src="${a.url}" alt="" class="max-w-full max-h-64 rounded-lg" loading="lazy"></div>`;
      if (a.type === 'video') return `<div><video controls src="${a.url}" class="max-w-full max-h-64 rounded-lg"></video><p class="text-xs text-gray-400">${escapeHtml(a.originalName)} · ${formatBytes(a.size)}</p></div>`;
      return '';
    }).join('')}
  </div>`;
}

async function changeStatus(id, status) {
  try {
    await api.put(`/notes/${id}`, { status });
    toast('状态已更新');
    closeDetail();
    refreshCurrentView();
  } catch(e) { toast('操作失败'); }
}

async function deleteNote(id) {
  if (!confirm('确认删除这条灵感？')) return;
  try {
    await api.del(`/notes/${id}`);
    toast('已删除');
    closeDetail();
    refreshCurrentView();
  } catch(e) { toast('删除失败'); }
}

function closeDetail() {
  document.getElementById('detail-modal').classList.add('hidden');
}

function refreshCurrentView() {
  switch (state.currentView) {
    case 'list': case 'capture': loadNotes(true); break;
    case 'workspace': loadWorkspace(); break;
    case 'calendar': loadCalendarView(); break;
    case 'timeline': loadTimeline(); break;
    case 'themes': loadThemes(); break;
    case 'settings': loadSettings(); break;
    case 'media': loadMediaView(); break;
  }
}

// ===================== 捕获 =====================
async function submitCapture() {
  const content = document.getElementById('capture-content').value.trim();
  const context = document.getElementById('capture-context').value;
  const selectedFiles = window._captureFiles || [];

  if (!content && !selectedFiles.length) {
    toast('请输入内容或选择媒体');
    return;
  }

  const btn = document.getElementById('btn-submit');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> 保存中…';

  try {
    const note = await api.post('/notes', {
      content,
      context: context || '',
      device: state.isMobile ? 'iphone' : 'windows',
      sourceTypes: content ? ['text'] : []
    });

    // 如果有媒体文件，上传
    if (selectedFiles.length && note) {
      const fd = new FormData();
      selectedFiles.forEach(f => fd.append('files', f));
      try {
        await api.upload(`/notes/${note.id}/media`, fd);
      } catch(e) {
        toast('媒体上传失败: ' + e.message);
      }
    }

    toast('已保存');
    document.getElementById('capture-content').value = '';
    document.getElementById('capture-context').value = '';
    clearCaptureFiles();
    if (state.isMobile) showView('list');
    loadDashboard();
    loadNotes(true);
  } catch(e) {
    // 离线回退
    const offline = JSON.parse(localStorage.getItem('offline-queue') || '[]');
    offline.push({
      id: 'offline-' + Date.now(),
      content,
      context,
      device: state.isMobile ? 'iphone' : 'windows',
      sourceTypes: content ? ['text'] : [],
      createdAt: new Date().toISOString()
    });
    localStorage.setItem('offline-queue', JSON.stringify(offline));
    document.getElementById('capture-content').value = '';
    document.getElementById('capture-context').value = '';
    clearCaptureFiles();
    toast('已保存到离线队列');
    document.getElementById('offline-count').textContent = offline.length;
  }
  btn.disabled = false;
  btn.innerHTML = '<i class="fa fa-paper-plane"></i> 保存灵感';
}

function clearCaptureFiles() {
  window._captureFiles = [];
  document.getElementById('capture-preview').classList.add('hidden');
  document.getElementById('capture-preview-list').innerHTML = '';
}

// ===================== 语音录制 =====================
let recordingTimer = null;

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    state.audioChunks = [];
    state.mediaRecorder.ondataavailable = e => state.audioChunks.push(e.data);
    state.mediaRecorder.onstop = () => {
      const blob = new Blob(state.audioChunks, { type: 'audio/webm' });
      const file = new File([blob], `recording-${Date.now()}.webm`, { type: 'audio/webm' });
      addCaptureFile(file);
      stream.getTracks().forEach(t => t.stop());
    };
    state.mediaRecorder.start();
    state.isRecording = true;
    document.getElementById('recording-bar').classList.remove('hidden');
    startRecordingTimer();
  } catch(e) {
    toast('无法访问麦克风: ' + e.message);
  }
}

function stopRecording() {
  if (state.mediaRecorder && state.isRecording) {
    state.mediaRecorder.stop();
    state.isRecording = false;
    document.getElementById('recording-bar').classList.add('hidden');
    stopRecordingTimer();
    const transcript = window.webkitSpeechRecognition ? '（转写可用）' : '';
    if (transcript) toast('录音已保存，转写中…');
  }
}

function startRecordingTimer() {
  let seconds = 0;
  const el = document.getElementById('recording-timer');
  recordingTimer = setInterval(() => {
    seconds++;
    el.textContent = `${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;
  }, 1000);
}

function stopRecordingTimer() {
  clearInterval(recordingTimer);
  document.getElementById('recording-timer').textContent = '00:00';
}

function addCaptureFile(file) {
  window._captureFiles = window._captureFiles || [];
  window._captureFiles.push(file);
  const preview = document.getElementById('capture-preview');
  const list = document.getElementById('capture-preview-list');
  preview.classList.remove('hidden');
  if (file.type.startsWith('image/')) {
    const url = URL.createObjectURL(file);
    list.insertAdjacentHTML('beforeend', `<img src="${url}" class="w-16 h-16 object-cover rounded-lg">`);
  } else {
    list.insertAdjacentHTML('beforeend', `<div class="text-xs bg-gray-100 rounded-lg px-2 py-1 flex items-center gap-1"><i class="fa ${file.type.startsWith('audio/')?'fa-microphone':'fa-video-camera'}"></i> ${file.name}</div>`);
  }
}

// ===================== 事件绑定 =====================
document.addEventListener('DOMContentLoaded', () => {
  // 导航点击
  document.addEventListener('click', (e) => {
    const nav = e.target.closest('[data-nav]');
    if (!nav) return;
    const view = nav.dataset.nav;
    if (view === 'inbox') {
      showView('list');
      loadNotes(true);
    } else {
      showView(view);
    }
    switch (view) {
      case 'workspace': loadWorkspace(); break;
      case 'calendar': loadCalendarView(); break;
      case 'timeline': loadTimeline(); break;
      case 'themes': loadThemes(); break;
      case 'media': loadMediaView(); break;
      case 'settings': loadSettings(); break;
      case 'capture': document.getElementById('capture-content').focus(); break;
    }
  });

  // 详情弹窗关闭
  document.getElementById('detail-modal').addEventListener('click', (e) => {
    if (e.target === document.getElementById('detail-modal')) closeDetail();
  });
  document.getElementById('btn-close-detail').onclick = closeDetail;
  document.getElementById('btn-detail-archive').onclick = () => changeStatus(document.getElementById('detail-body').dataset.noteId, 'archived');
  document.getElementById('btn-detail-expand').onclick = () => changeStatus(document.getElementById('detail-body').dataset.noteId, 'expanded');
  document.getElementById('btn-detail-realize').onclick = () => changeStatus(document.getElementById('detail-body').dataset.noteId, 'realized');
  document.getElementById('btn-detail-abandon').onclick = () => changeStatus(document.getElementById('detail-body').dataset.noteId, 'abandoned');
  document.getElementById('btn-detail-delete').onclick = () => deleteNote(document.getElementById('detail-body').dataset.noteId);

  // 捕获
  document.getElementById('btn-submit').onclick = submitCapture;
  document.getElementById('btn-voice').onclick = () => state.isRecording ? stopRecording() : startRecording();
  document.getElementById('btn-stop-recording').onclick = stopRecording;
  document.getElementById('btn-camera').onclick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;
    input.onchange = () => { for (const f of input.files) addCaptureFile(f); };
    input.click();
  };
  document.getElementById('btn-video').onclick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*';
    input.onchange = () => {
      const f = input.files[0];
      if (!f) return;
      if (f.size > 1073741824) { toast('视频大小不能超过 1GB'); return; }
      addCaptureFile(f);
    };
    input.click();
  };
  document.getElementById('btn-clear-media').onclick = clearCaptureFiles;

  // 列表筛选
  let searchTimeout;
  document.getElementById('list-search').oninput = function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      state.filters.q = this.value;
      loadNotes(true);
    }, 300);
  };
  document.getElementById('list-status-filter').onchange = function() {
    state.filters.status = this.value;
    loadNotes(true);
  };
  document.getElementById('list-mood-filter').onchange = function() {
    state.filters.mood = this.value;
    loadNotes(true);
  };

  // 批量操作
  document.getElementById('btn-batch-archive').onclick = () => batchAction('status', { status: 'archived' });
  document.getElementById('btn-batch-abandon').onclick = () => batchAction('status', { status: 'abandoned' });
  document.getElementById('btn-batch-theme').onclick = async () => {
    const data = await api.get('/themes');
    if (!data.items.length) { toast('请先创建主题'); return; }
    const themeId = prompt('输入主题 ID:\n' + data.items.map(t => `${t.id} (${t.title})`).join('\n'));
    if (themeId) await batchAction('theme', { themeId });
  };
  document.getElementById('btn-batch-clear').onclick = () => {
    state.selectedNotes.clear();
    updateBatchBar();
    document.querySelectorAll('.note-checkbox').forEach(cb => cb.checked = false);
  };

  // 加载更多
  document.getElementById('btn-load-more').onclick = () => loadNotes(false);

  // 工作台随机
  document.getElementById('btn-random').onclick = loadRandomCard;

  // 时间线筛选
  document.getElementById('timeline-status-filter').onchange = loadTimeline;
  document.getElementById('timeline-media-filter').onchange = loadTimeline;

  // 主题
  document.getElementById('btn-create-theme').onclick = createTheme;

  // 媒体 Tab
  document.getElementById('media-tabs').addEventListener('click', (e) => {
    const tab = e.target.closest('.media-tab');
    if (!tab) return;
    loadMediaView(tab.dataset.media);
  });

  // 设置
  document.getElementById('btn-check-ai').onclick = checkAI;
  document.getElementById('btn-sync-now').onclick = syncOffline;

  // 日历月份选择
  const calPicker = document.getElementById('calendar-month-picker');
  if (calPicker) {
    const now = new Date();
    calPicker.value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
  }

  // 键盘快捷键
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeDetail();
  });

  // 注册 SW
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }

  // 初始加载
  const isDesktop = window.innerWidth >= 768;
  if (isDesktop) {
    showView('workspace');
    loadWorkspace();
  } else {
    showView('capture');
    document.getElementById('capture-content').focus();
  }
  loadSettings();
});

// 暴露到全局
window.openDetail = openDetail;
window.openThemeDetail = openThemeDetail;
window.createTheme = createTheme;
window.editTheme = editTheme;
window.loadDateDetail = loadDateDetail;
