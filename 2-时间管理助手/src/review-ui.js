// UI 控制层 - AI 对话式复盘（v2.14.0）
class ReviewUI {
  constructor() {
    this.engine = window.ReviewEngine;
    this.currentYear = 2026;
    this.currentStartWeek = 33;
    this.currentEndWeek = 36;
    this.currentStage = 1;

    // AI 对话上下文
    this.dataContext = null; // buildDataContext 的返回值
    this.chatMessages = [];  // [{role: 'user'|'assistant', content: '...'}]
    this.generatedReport = '';
    this.extractedKeywords = [];

    this.tempGoals = [];
  }

  // ===== 初始化 =====
  async init() {
    this.loadGoals();
    this.loadHistory();
    this.initWeekSelectors();
    this.initQuickSelect();

    // 检查 AI 是否可用
    const status = await this.engine.checkAIStatus();
    this.showAIStatus(status);

    // 预加载数据（用户可能直接点"开始对话"）
    this.previewData();
  }

  showAIStatus(status) {
    const banner = document.getElementById('ai-status-banner');
    if (!status.ready) {
      banner.className = 'ai-status error';
      banner.innerHTML = `⚠️ AI 未配置：${status.error || '请在项目根目录的 ai-config.json 中填写 API 配置'}`;
      banner.style.display = 'block';
    } else {
      banner.className = 'ai-status ready';
      banner.innerHTML = `✅ AI 已就绪（${status.model}）`;
      banner.style.display = 'block';
    }
  }

  // ===== 阶段切换 =====
  switchStage(stage) {
    this.currentStage = stage;

    // 更新顶部按钮状态
    document.querySelectorAll('.stage-btn').forEach(btn => {
      const s = parseInt(btn.dataset.stage);
      btn.classList.remove('active', 'completed');
      if (s === stage) btn.classList.add('active');
      else if (s < stage) btn.classList.add('completed');
    });

    // 切换内容区
    document.querySelectorAll('.stage-content').forEach(c => {
      c.classList.remove('active');
    });
    document.getElementById(`stage-${stage}`).classList.add('active');
  }

  // ===== 目标管理（复用旧逻辑）=====
  loadGoals() {
    const goals = this.engine.loadGoals();
    const goalsList = document.getElementById('goals-list');
    if (goals.length === 0) {
      goalsList.innerHTML = '<li style="color: #95a5a6;">尚未设置长远目标</li>';
    } else {
      goalsList.innerHTML = goals.map((g, i) => `<li>${i + 1}. ${g}</li>`).join('');
    }
  }

  editGoals() {
    const currentGoals = this.engine.loadGoals();
    this.tempGoals = [...currentGoals];
    document.getElementById('goal-edit-modal').classList.add('show');
    this.renderGoalEditList();
  }

  renderGoalEditList() {
    const container = document.getElementById('goal-edit-list');
    container.innerHTML = this.tempGoals.map((goal, index) => `
      <div class="goal-edit-item">
        <input type="text" value="${goal}" data-index="${index}" placeholder="输入长远目标..." />
        <button class="btn btn-secondary" onclick="reviewUI.removeGoal(${index})">删除</button>
      </div>
    `).join('');
  }

  addGoalInput() {
    this.tempGoals.push('');
    this.renderGoalEditList();
  }

  removeGoal(index) {
    if (this.tempGoals.length <= 1) {
      alert('至少保留一个目标');
      return;
    }
    this.tempGoals.splice(index, 1);
    this.renderGoalEditList();
  }

  saveGoalsFromModal() {
    const inputs = document.querySelectorAll('#goal-edit-list input');
    const goals = Array.from(inputs)
      .map(input => input.value.trim())
      .filter(g => g !== '');
    if (goals.length === 0) {
      alert('至少设置一个目标');
      return;
    }
    this.engine.saveGoals(goals);
    this.loadGoals();
    this.closeGoalModal();
    alert('目标已保存');
  }

  closeGoalModal() {
    document.getElementById('goal-edit-modal').classList.remove('show');
  }

  // ===== 历史复盘（复用旧逻辑）=====
  loadHistory() {
    const records = this.engine.listReviewRecords();
    const historyList = document.getElementById('history-list');
    if (records.length === 0) {
      historyList.innerHTML = '<p style="color: #95a5a6;">暂无历史复盘记录</p>';
      return;
    }
    historyList.innerHTML = records.map(record => `
      <div class="history-item">
        <div class="history-item-header">
          ${record.yearMonth} (第${record.weekRange[0]}-${record.weekRange[1]}周)
        </div>
        <div class="history-item-content">
          "${record.conclusion || '无结论'}"
        </div>
        <div class="history-item-actions">
          <button class="btn btn-secondary" onclick="reviewUI.viewHistory('${record.key}')">查看详情</button>
        </div>
      </div>
    `).join('');
  }

  viewHistory(key) {
    const data = JSON.parse(localStorage.getItem(key));
    alert(`历史复盘详情\n\n${data.yearMonth}\n第${data.weekRange[0]}-${data.weekRange[1]}周\n\n${data.conclusion}`);
  }

  // ===== 周选择器（改为手动输入）=====
  initWeekSelectors() {
    const startInput = document.getElementById('start-week-select');
    const endInput = document.getElementById('end-week-select');
    const yearSelect = document.getElementById('year-select');

    // 设置初始值
    startInput.value = this.currentStartWeek;
    endInput.value = this.currentEndWeek;

    const updateDateRange = () => this.updateDateRangeDisplay();
    yearSelect.addEventListener('change', updateDateRange);
    startInput.addEventListener('input', updateDateRange);
    endInput.addEventListener('input', updateDateRange);

    // 选择变化时自动刷新数据预览
    const refreshPreview = () => {
      this.updateDateRangeDisplay();
      this.previewData();
    };
    yearSelect.addEventListener('change', refreshPreview);
    startInput.addEventListener('input', refreshPreview);
    endInput.addEventListener('input', refreshPreview);

    this.updateDateRangeDisplay();
  }

  initQuickSelect() {
    const today = new Date();
    const currentWeek = this.getISOWeek(today);
    this.currentStartWeek = Math.max(1, currentWeek - 3);
    this.currentEndWeek = currentWeek;
    document.getElementById('start-week-select').value = this.currentStartWeek;
    document.getElementById('end-week-select').value = this.currentEndWeek;
  }

  getISOWeek(date) {
    const target = new Date(date.valueOf());
    const dayNr = (date.getDay() + 6) % 7;
    target.setDate(target.getDate() - dayNr + 3);
    const firstThursday = target.valueOf();
    target.setMonth(0, 1);
    if (target.getDay() !== 4) {
      target.setMonth(0, 1 + ((4 - target.getDay()) + 7) % 7);
    }
    return 1 + Math.ceil((firstThursday - target) / 604800000);
  }

  updateDateRangeDisplay() {
    const year = parseInt(document.getElementById('year-select').value);
    const startWeek = parseInt(document.getElementById('start-week-select').value);
    const endWeek = parseInt(document.getElementById('end-week-select').value);
    const display = document.getElementById('date-range-display');

    if (!startWeek || !endWeek) {
      display.style.display = 'none';
      return;
    }

    const startDates = window.AppCore.getWeekDates(year, startWeek);
    const endDates = window.AppCore.getWeekDates(year, endWeek);

    if (!startDates || !endDates || startDates.length === 0 || endDates.length === 0) {
      display.style.display = 'none';
      return;
    }

    const formatDate = (dateStr) => {
      const date = new Date(dateStr);
      return `${date.getMonth() + 1}月${date.getDate()}日`;
    };

    const startStr = formatDate(startDates[0]);
    const endStr = formatDate(endDates[6]);

    display.innerHTML = `📅 <strong>第${startWeek}周</strong>（${startStr}）至 <strong>第${endWeek}周</strong>（${endStr}）`;
    display.style.display = 'block';
  }

  // ===== 阶段1：数据预览 =====
  previewData() {
    const year = parseInt(document.getElementById('year-select').value);
    const startWeek = parseInt(document.getElementById('start-week-select').value);
    const endWeek = parseInt(document.getElementById('end-week-select').value);

    if (startWeek > endWeek) {
      document.getElementById('start-chat-btn').style.display = 'none';
      document.getElementById('data-panel').style.display = 'none';
      return;
    }

    this.currentYear = year;
    this.currentStartWeek = startWeek;
    this.currentEndWeek = endWeek;

    // 构建数据上下文（引擎已完成四层分析）
    this.dataContext = this.engine.buildDataContext(year, startWeek, endWeek);

    // 渲染右侧数据面板（常驻）
    this.renderDataPanel();

    // 显示"开始对话"按钮
    document.getElementById('start-chat-btn').style.display = 'inline-block';
  }

  // 渲染右侧数据面板
  renderDataPanel() {
    const panel = document.getElementById('data-panel');
    const statsDiv = document.getElementById('data-panel-stats');
    const weeksDiv = document.getElementById('data-panel-weeks');

    const s = this.dataContext.stats;

    // 总览统计
    statsDiv.innerHTML = `
      <div style="margin-bottom: 0.5em;"><strong>总计</strong></div>
      <div>• QW：${s.totalQW}h</div>
      <div>• GFP：${s.totalGFP}h</div>
      <div>• 拖延：${s.totalProc}h</div>
      <div>• 休息：${s.totalRest}h</div>
      <div>• 凌晨工作：${s.midnightWorkCount}次</div>
    `;

    // 逐周明细（带折叠的二级分类）
    weeksDiv.innerHTML = this.dataContext.weekDetails.map(w => {
      const kw = w.keyword ? `<div style="color: #7f8c8d; font-size: 0.9em; margin-top: 0.3em;">关键词：「${w.keyword}」</div>` : '';

      // 生成二级分类明细
      let breakdownHtml = '';
      if (w.breakdown && Object.keys(w.breakdown).length > 0) {
        const sortedCodes = Object.keys(w.breakdown).sort();
        const items = sortedCodes.map(code => {
          const hours = Math.round(w.breakdown[code] * 10) / 10;
          const label = this.getCodeLabel(code);
          return `<div style="padding: 0.2em 0;">• ${label}：${hours}h</div>`;
        }).join('');
        breakdownHtml = `
          <details style="margin-top: 0.5em;">
            <summary style="cursor: pointer; color: #667eea; font-size: 0.9em; user-select: none;">📊 明细</summary>
            <div style="padding: 0.5em 0 0 0.5em; font-size: 0.85em; color: #34495e;">${items}</div>
          </details>
        `;
      }

      return `
        <div style="padding: 0.8em; background: #f8f9fa; border-radius: 6px; margin-bottom: 0.8em;">
          <div style="font-weight: 600; margin-bottom: 0.3em;">第 ${w.week} 周</div>
          <div style="font-size: 0.9em; color: #555;">
            QW ${w.qw}h / GFP ${w.gfp}h<br>
            拖延 ${w.proc}h / 休息 ${w.rest}h
          </div>
          ${kw}
          ${breakdownHtml}
        </div>
      `;
    }).join('');

    panel.style.display = 'block';
  }

  // 获取代码对应的标签文本
  getCodeLabel(code) {
    // 从当前周的配置读取自定义名称
    const config = this.engine.AppCore.getConfig(this.currentYear, this.currentStartWeek);

    if (code.startsWith('1.')) {
      const idx = parseInt(code.substring(2)) - 1;
      return config.qwNames?.[idx] || `QW ${code}`;
    } else if (code.startsWith('2.')) {
      const idx = parseInt(code.substring(2)) - 1;
      return config.gfpNames?.[idx] || `GFP ${code}`;
    } else if (code.startsWith('3.')) {
      const idx = parseInt(code.substring(2)) - 1;
      return config.procNames?.[idx] || `Proc ${code}`;
    }
    return code;
  }

  // ===== 阶段2：对话 =====
  async startChat() {
    if (!this.dataContext) {
      alert('请先选择周范围并预览数据');
      return;
    }

    this.switchStage(2);
    this.chatMessages = [];

    // 显示系统提示
    this.addChatMessage('system', '🤖 AI 正在思考第一个问题...');

    // 调用 AI 生成开场问题
    try {
      const systemPrompt = this.engine.buildChatSystemPrompt(this.dataContext);
      const initMessages = [{ role: 'user', content: '开始复盘' }];
      const firstQuestion = await this.engine.callAI(initMessages, systemPrompt, 300);
      this.removeChatMessage('system');
      this.chatMessages.push({ role: 'assistant', content: firstQuestion });
      this.addChatMessage('ai', firstQuestion);
    } catch (e) {
      this.removeChatMessage('system');
      this.addChatMessage('system', '❌ AI 调用失败：' + e.message);
    }
  }

  addChatMessage(type, text) {
    const messagesDiv = document.getElementById('chat-messages');
    const msg = document.createElement('div');
    msg.className = `message ${type}`;
    msg.textContent = text;
    messagesDiv.appendChild(msg);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
  }

  removeChatMessage(type) {
    const messagesDiv = document.getElementById('chat-messages');
    const last = messagesDiv.lastElementChild;
    if (last && last.classList.contains(type)) {
      last.remove();
    }
  }

  async sendMessage() {
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text) return;

    // 禁用输入
    input.disabled = true;
    document.getElementById('send-btn').disabled = true;

    // 显示用户消息
    this.chatMessages.push({ role: 'user', content: text });
    this.addChatMessage('user', text);
    input.value = '';

    // 显示 AI 正在思考
    this.addChatMessage('system', '🤖 AI 正在思考...');

    try {
      const systemPrompt = this.engine.buildChatSystemPrompt(this.dataContext);
      const reply = await this.engine.callAI(this.chatMessages, systemPrompt, 400);
      this.removeChatMessage('system');
      this.chatMessages.push({ role: 'assistant', content: reply });
      this.addChatMessage('ai', reply);
    } catch (e) {
      this.removeChatMessage('system');
      this.addChatMessage('system', '❌ AI 调用失败：' + e.message);
    } finally {
      input.disabled = false;
      document.getElementById('send-btn').disabled = false;
      input.focus();
    }
  }

  // ===== 阶段3：生成报告 =====
  async finishChatAndGenerateReport() {
    if (this.chatMessages.length === 0) {
      alert('还没有进行对话');
      return;
    }

    this.switchStage(3);
    document.getElementById('report-content').innerHTML = '<p style="text-align:center;color:#7f8c8d;">🤖 AI 正在生成报告，请稍候...</p>';

    try {
      // 对话记录作为用户输入上下文，传给报告生成 prompt
      const conversationText = this.chatMessages
        .map(m => `${m.role === 'user' ? '用户' : 'AI'}：${m.content}`)
        .join('\n\n');

      const systemPrompt = this.engine.buildReportSystemPrompt(this.dataContext);
      const userPrompt = `# 对话记录（用户在对话中说的话）\n\n${conversationText}\n\n---\n\n现在请基于上面的事实数据和对话记录，生成复盘报告。`;

      this.generatedReport = await this.engine.callAI(
        [{ role: 'user', content: userPrompt }],
        systemPrompt,
        4000
      );

      // 提取关键词（在报告最后一节，反引号包裹）
      this.extractKeywords();

      // 渲染 markdown 报告 + 折叠的原始数据
      this.renderReport();
    } catch (e) {
      document.getElementById('report-content').innerHTML = `<p style="color:#e74c3c;">❌ 报告生成失败：${e.message}</p>`;
    }
  }

  extractKeywords() {
    // 从报告中提取 `关键词` 反引号格式
    const match = this.generatedReport.match(/`([^`]+)`/g);
    if (match) {
      this.extractedKeywords = match.map(m => m.replace(/`/g, '').trim()).filter(Boolean);
    } else {
      this.extractedKeywords = [];
    }
  }

  renderReport() {
    const container = document.getElementById('report-content');

    // 简易 markdown 渲染（足够应对 AI 输出的结构化报告）
    let html = this.generatedReport
      // 标题
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/^## (.+)$/gm, '<h2>$2</h2>')
      // blockquote
      .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
      // 加粗
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      // 行内代码
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // 列表（简化处理，不支持嵌套）
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      // 段落
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');

    // 包裹 <ul> 标签（连续的 <li> 自动组合）
    html = html.replace(/(<li>.+?<\/li>)/gs, match => {
      return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
    });

    // 包裹段落
    html = '<p>' + html + '</p>';

    // 修正多余的 <p> 包裹
    html = html
      .replace(/<p><h1>/g, '<h1>')
      .replace(/<\/h1><\/p>/g, '</h1>')
      .replace(/<p><h2>/g, '<h2>')
      .replace(/<\/h2><\/p>/g, '</h2>')
      .replace(/<p><blockquote>/g, '<blockquote>')
      .replace(/<\/blockquote><\/p>/g, '</blockquote>')
      .replace(/<p><ul>/g, '<ul>')
      .replace(/<\/ul><\/p>/g, '</ul>')
      .replace(/<p><\/p>/g, '');

    container.innerHTML = html;

    // 追加折叠的原始数据
    this.appendDataDetails(container);
  }

  appendDataDetails(container) {
    const s = this.dataContext.stats;
    const details = document.createElement('details');
    details.innerHTML = `
      <summary>📊 原始数据（点击展开）</summary>
      <table class="data-table">
        <thead>
          <tr>
            <th>指标</th>
            <th>数值</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>高质量工作 (QW)</td><td>${s.totalQW} 小时</td></tr>
          <tr><td>休闲娱乐 (GFP)</td><td>${s.totalGFP} 小时</td></tr>
          <tr><td>拖延 (Proc)</td><td>${s.totalProc} 小时</td></tr>
          <tr><td>休息 (Rest)</td><td>${s.totalRest} 小时</td></tr>
          <tr><td>无意义工作 (MW)</td><td>${s.totalMW} 小时</td></tr>
          <tr><td>凌晨工作次数</td><td>${s.midnightWorkCount}</td></tr>
          <tr><td>周末外出次数</td><td>${s.weekendEscapeCount}</td></tr>
        </tbody>
      </table>
      <h4 style="margin-top: 16px;">逐周数据</h4>
      <table class="data-table">
        <thead>
          <tr>
            <th>周</th>
            <th>QW</th>
            <th>GFP</th>
            <th>拖延</th>
            <th>休息</th>
            <th>关键词</th>
          </tr>
        </thead>
        <tbody>
          ${this.dataContext.weekDetails.map(w => `
            <tr>
              <td>第 ${w.week} 周</td>
              <td>${w.qw}h</td>
              <td>${w.gfp}h</td>
              <td>${w.proc}h</td>
              <td>${w.rest}h</td>
              <td>${w.keyword || '-'}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
    container.appendChild(details);
  }

  // ===== 保存复盘 =====
  saveCurrentReview() {
    if (!this.generatedReport) {
      alert('还没有生成报告');
      return;
    }

    const midWeek = Math.floor((this.currentStartWeek + this.currentEndWeek) / 2);
    const month = Math.ceil(midWeek / 4.33);

    // 汇总用户在对话中说的话（改进4：保存自由对话原文）
    const userWords = this.chatMessages
      .filter(m => m.role === 'user')
      .map(m => m.content)
      .join('\n\n');

    const reviewData = {
      yearMonth: `${this.currentYear}年${month}月`,
      weekRange: [this.currentStartWeek, this.currentEndWeek],
      userWords: userWords, // 用户的原始对话
      keywords: this.extractedKeywords,
      reportMarkdown: this.generatedReport,
      conclusion: this.extractConclusion(),
      dataSnapshot: {
        stats: this.dataContext.stats,
        trends: this.dataContext.trends
      },
      conversationLog: this.chatMessages,
      savedAt: new Date().toISOString()
    };

    this.engine.saveReviewRecord(this.currentYear, month, reviewData);
    alert('✅ 复盘已保存！');
    this.loadHistory();
  }

  extractConclusion() {
    // 从报告第一行提取一句话概括（blockquote 里的内容）
    const match = this.generatedReport.match(/^> (.+)$/m);
    return match ? match[1] : '复盘已完成';
  }

  // ===== 重新开始 =====
  backToStart() {
    if (!confirm('确认重新复盘？当前对话和报告将丢失（如需保留请先保存）')) {
      return;
    }
    this.switchStage(1);
    this.chatMessages = [];
    this.generatedReport = '';
    this.extractedKeywords = [];
    document.getElementById('chat-messages').innerHTML = '';
    document.getElementById('user-input').value = '';
    document.getElementById('report-content').innerHTML = '';
  }

  // ===== 周期数据对比功能 =====
  openWeekCompareModal() {
    document.getElementById('week-compare-modal').style.display = 'flex';
    this.renderWeekCompare();
  }

  closeWeekCompareModal() {
    document.getElementById('week-compare-modal').style.display = 'none';
  }

  async renderWeekCompare() {
    const year = parseInt(document.getElementById('year-select').value);
    const startWeek = parseInt(document.getElementById('start-week-select').value);
    const endWeek = parseInt(document.getElementById('end-week-select').value);

    if (!startWeek || !endWeek || startWeek > endWeek) {
      document.getElementById('week-compare-content').innerHTML = '<p style="color: #ef4444;">❌ 请选择有效的周数范围</p>';
      return;
    }

    document.getElementById('week-compare-content').innerHTML = '<p style="color: #94a3b8;">⏳ 加载中...</p>';

    // 加载每周数据
    const weeksData = [];
    for (let week = startWeek; week <= endWeek; week++) {
      const weekData = await this.loadWeekData(year, week);
      weeksData.push({ year, week, ...weekData });
    }

    // 渲染对比表格
    this.renderCompareTable(weeksData);
  }

  async loadWeekData(year, week) {
    const { getWeekDates } = window.AppCore;
    const dates = getWeekDates(year, week);
    const dateKeys = dates.map(d => `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}-${String(d.getUTCDate()).padStart(2, '0')}`);

    // 尝试从 localStorage 读取
    const cellsKey = `tm_${year}_w${week}_cells`;
    const configKey = `tm_${year}_w${week}_config`;
    let cells = {};
    let config = { standard: 168 };

    try {
      const cellsStr = localStorage.getItem(cellsKey);
      if (cellsStr) cells = JSON.parse(cellsStr);
      const configStr = localStorage.getItem(configKey);
      if (configStr) config = JSON.parse(configStr);
    } catch (e) {
      console.error('读取本地数据失败:', e);
    }

    // 如果本地无数据，尝试从服务器读取
    if (Object.keys(cells).length === 0) {
      try {
        const response = await fetch(`/sync-data/${year}/w${week}.json`);
        if (response.ok) {
          const serverData = await response.json();
          if (serverData.cells && serverData.cells.value) {
            cells = serverData.cells.value;
          }
          if (serverData.config && serverData.config.value) {
            config = serverData.config.value;
          }
        }
      } catch (e) {
        console.warn(`服务器无数据: ${year} w${week}`);
      }
    }

    // 按日期分组
    const cellsByDate = {};
    dateKeys.forEach(dk => { cellsByDate[dk] = {}; });
    for (const id in cells) {
      const [date, slot] = id.split('|');
      if (cellsByDate[date]) {
        cellsByDate[date][slot] = cells[id];
      }
    }

    // 计算统计
    const { calcWeeklyStats } = window.AppCore;
    const stats = calcWeeklyStats(cellsByDate, dateKeys, config.standard || 168);

    return {
      dates,
      stats,
      hasData: Object.keys(cells).length > 0
    };
  }

  // 渐进色生成函数（根据值在数组中的位置和总数计算）
  getProgressiveColor(index, total, scheme) {
    if (total === 1) {
      // 只有一个值时使用中间色
      if (scheme === 'green') return '#86efac'; // green-300
      if (scheme === 'blue') return '#7dd3fc';  // sky-300
      if (scheme === 'red') return '#fca5a5';   // red-300
    }

    // 计算位置比例（0 到 1）
    const ratio = total > 1 ? index / (total - 1) : 0;

    if (scheme === 'green') {
      // 浅绿到深绿：#dcfce7 -> #86efac -> #22c55e -> #15803d
      if (ratio < 0.33) return '#dcfce7'; // green-100
      if (ratio < 0.67) return '#86efac'; // green-300
      return '#22c55e'; // green-500
    }

    if (scheme === 'blue') {
      // 浅蓝到深蓝：#e0f2fe -> #7dd3fc -> #0ea5e9 -> #0369a1
      if (ratio < 0.33) return '#e0f2fe'; // sky-100
      if (ratio < 0.67) return '#7dd3fc'; // sky-300
      return '#0ea5e9'; // sky-500
    }

    if (scheme === 'red') {
      // 浅红到深红：#fee2e2 -> #fca5a5 -> #ef4444 -> #dc2626
      if (ratio < 0.33) return '#fee2e2'; // red-100
      if (ratio < 0.67) return '#fca5a5'; // red-300
      return '#ef4444'; // red-500
    }

    return 'white';
  }

  renderCompareTable(weeksData) {
    let html = '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 15px;">';

    // 表头
    html += '<thead><tr style="background: #1e293b; color: #e2e8f0;">';
    html += '<th style="padding: 12px; text-align: left; border: 1px solid #334155;">项目</th>';

    weeksData.forEach((wd, i) => {
      const label = String.fromCharCode(65 + i); // A, B, C, D...
      const dateStr = `${wd.dates[0].getUTCMonth() + 1}/${wd.dates[0].getUTCDate()}-${wd.dates[6].getUTCMonth() + 1}/${wd.dates[6].getUTCDate()}`;
      html += `<th style="padding: 12px; text-align: center; border: 1px solid #334155;">${label}<br>${wd.year}年第${wd.week}周<br>${dateStr}</th>`;
    });

    // 差值列
    for (let i = 0; i < weeksData.length - 1; i++) {
      const labelA = String.fromCharCode(65 + i);
      const labelB = String.fromCharCode(66 + i);
      html += `<th style="padding: 12px; text-align: center; border: 1px solid #334155; background: #0f172a;">${labelA}-${labelB}</th>`;
    }

    html += '</tr></thead><tbody>';

    let rowCount = 0; // 用于行斑马纹

    // 数据行（主行 + 可折叠明细行）
    const rows = [
      {
        label: 'QW 时间',
        key: 'qw',
        format: v => v ? v.toFixed(1) + 'h' : '0h',
        hasDetail: true,
        detailKeys: ['qwDetail'],
        colorScheme: 'green'
      },
      {
        label: 'GFP 时间',
        key: 'gfp',
        format: v => v ? v.toFixed(1) + 'h' : '0h',
        hasDetail: true,
        detailKeys: ['gfpDetail'],
        colorScheme: 'blue'
      },
      {
        label: '拖延时间',
        key: 'proc',
        format: v => v ? v.toFixed(1) + 'h' : '0h',
        hasDetail: true,
        detailKeys: ['procDetail'],
        colorScheme: 'red'
      },
      { label: '休息时间', key: 'rest', format: v => v ? v.toFixed(1) + 'h' : '0h' },
      { label: 'MW 时间', key: 'mw', format: v => v ? v.toFixed(1) + 'h' : '0h' },
      { label: '凌晨工作次数', key: 'lateWorkCount', format: v => v || 0 }
    ];

    rows.forEach((row, rowIndex) => {
      const rowId = `row-${rowIndex}`;
      const detailId = `detail-${rowIndex}`;

      // 斑马纹背景（白色和淡青色交替，对比度高）
      const isEven = rowIndex % 2 === 0;
      const rowBg = isEven ? 'white' : '#e0f2fe';

      // 主行
      html += '<tr>';

      // 项目列（如果有明细，添加展开按钮）
      if (row.hasDetail) {
        html += `<td style="padding: 10px; border: 1px solid #334155; background: #1e293b; font-weight: 500;">
          <span style="cursor: pointer; color: #e2e8f0;" onclick="reviewUI.toggleDetail('${detailId}', this)">
            ▶ ${row.label}
          </span>
        </td>`;
      } else {
        html += `<td style="padding: 10px; border: 1px solid #334155; background: #1e293b; color: #e2e8f0; font-weight: 500;">${row.label}</td>`;
      }

      const values = weeksData.map(wd => {
        if (!wd.hasData) return null;
        return wd.stats.totals[row.key] || 0;
      });

      // 找出最大值（用于大数字强调）
      const maxValue = Math.max(...values.filter(v => v !== null && v > 0));

      // 数据列 - 使用斑马纹背景 + 大数字强调
      values.forEach((v, i) => {
        const color = weeksData[i].hasData ? '#1e293b' : '#94a3b8';
        const content = v !== null ? row.format(v) : '-';

        // 大于最大值80%的数字用大字号+加粗
        const isBig = v !== null && maxValue > 0 && v >= maxValue * 0.8;
        const fontSize = isBig ? '18px' : '15px';
        const fontWeight = isBig ? 'bold' : 'normal';

        html += `<td style="padding: 10px; border: 1px solid #334155; text-align: center; color: ${color}; background: ${rowBg}; font-size: ${fontSize}; font-weight: ${fontWeight};">${content}</td>`;
      });

      // 差值列
      for (let i = 0; i < values.length - 1; i++) {
        const diff = (values[i] !== null && values[i + 1] !== null) ? (values[i] - values[i + 1]) : null;
        let diffHtml = '-';

        if (diff !== null) {
          const formatted = row.key === 'lateWorkCount' ? diff : diff.toFixed(1);
          if (diff > 0) {
            diffHtml = `<span style="color: #34d399;">+${formatted}</span>`;
          } else if (diff < 0) {
            diffHtml = `<span style="color: #f87171;">${formatted}</span>`;
          } else {
            diffHtml = '0';
          }
        }

        html += `<td style="padding: 10px; border: 1px solid #334155; text-align: center; background: #0f172a;">${diffHtml}</td>`;
      }

      html += '</tr>';

      // 明细行（初始隐藏）
      if (row.hasDetail) {
        html += this.renderDetailRows(weeksData, row, detailId);
      }
    });

    html += '</tbody></table></div>';

    // 添加说明
    html += `
      <div style="margin-top: 20px; padding: 12px; background: #1e293b; border-radius: 8px; color: #94a3b8; font-size: 12px;">
        <p style="margin: 0 0 8px 0;"><strong>说明：</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
          <li>点击 ▶ 可展开查看子分类明细（显示完整名称）</li>
          <li>行背景白色/浅灰交替，便于阅读不会看错行</li>
          <li>数值较大的格子用大字号+加粗显示（≥最大值的80%）</li>
          <li>绿色差值表示相比下一周增加，红色表示减少</li>
          <li>"-" 表示该周无数据</li>
        </ul>
      </div>
    `;

    document.getElementById('week-compare-content').innerHTML = html;
  }

  renderDetailRows(weeksData, parentRow, detailId) {
    let html = '';

    // 获取第一个有数据的周，从中读取配置
    const firstValidWeek = weeksData.find(wd => wd.hasData);
    if (!firstValidWeek) return html;

    // 从 localStorage 读取配置（包含子分类名称）
    const configKey = `tm_${firstValidWeek.year}_w${firstValidWeek.week}_config`;
    let config = {};
    try {
      const configStr = localStorage.getItem(configKey);
      if (configStr) config = JSON.parse(configStr);
    } catch (e) {
      console.error('读取配置失败:', e);
    }

    // 根据父行类型获取名称数组
    let names = [];
    let detailKey = '';
    if (parentRow.key === 'qw') {
      names = config.qwNames || [];
      detailKey = 'qwDetail';
    } else if (parentRow.key === 'gfp') {
      names = config.gfpNames || [];
      detailKey = 'gfpDetail';
    } else if (parentRow.key === 'proc') {
      names = config.procNames || [];
      detailKey = 'procDetail';
    }

    // 确定分类代码前缀
    let codePrefix = '';
    if (parentRow.key === 'qw') codePrefix = '1';
    else if (parentRow.key === 'gfp') codePrefix = '2';
    else if (parentRow.key === 'proc') codePrefix = '3';

    // 渲染每个子分类
    names.forEach((name, idx) => {
      // 检查是否所有周都是 0（跳过全是 0 的子分类）
      const hasAnyData = weeksData.some(wd => {
        if (!wd.hasData || !wd.stats.totals[detailKey]) return false;
        const arr = wd.stats.totals[detailKey];
        return Array.isArray(arr) && arr[idx] > 0;
      });

      if (!hasAnyData) return;

      // 斑马纹背景（基于子分类索引 idx，使用淡青色对比）
      const isEven = idx % 2 === 0;
      const rowBg = isEven ? 'white' : '#e0f2fe';

      // 生成唯一的行 id
      const rowId = `${detailId}-${idx}`;
      html += `<tr id="${rowId}" style="display: none;">`;

      // 显示格式：└ 1.1-AI
      const codeLabel = `${codePrefix}.${idx + 1}`;
      html += `<td style="padding: 8px 10px 8px 30px; border: 1px solid #334155; background: ${rowBg}; color: #475569; font-size: 14px;">└ ${codeLabel}-${name}</td>`;

      // 获取每周的值（数组索引对应子分类）
      const values = weeksData.map(wd => {
        if (!wd.hasData || !wd.stats.totals[detailKey]) return null;
        const arr = wd.stats.totals[detailKey];
        if (!Array.isArray(arr) || idx >= arr.length) return null;
        return arr[idx] * 0.5; // 转换为小时
      });

      // 找出最大值（用于大字号显示）
      const maxValue = Math.max(...values.filter(v => v !== null && v > 0));

      // 数据列
      values.forEach((v, i) => {
        if (v === null || v === 0) {
          html += `<td style="padding: 8px 10px; border: 1px solid #334155; text-align: center; color: #94a3b8; background: ${rowBg}; font-size: 14px;">-</td>`;
        } else {
          const content = v.toFixed(1) + 'h';
          // 大于最大值80%的数字用大字号+加粗
          const isBig = maxValue > 0 && v >= maxValue * 0.8;
          const fontSize = isBig ? '16px' : '14px';
          const fontWeight = isBig ? 'bold' : 'normal';
          html += `<td style="padding: 8px 10px; border: 1px solid #334155; text-align: center; color: #475569; background: ${rowBg}; font-size: ${fontSize}; font-weight: ${fontWeight};">${content}</td>`;
        }
      });

      // 差值列
      for (let i = 0; i < values.length - 1; i++) {
        const diff = (values[i] !== null && values[i + 1] !== null) ? (values[i] - values[i + 1]) : null;
        let diffHtml = '-';

        if (diff !== null) {
          const formatted = diff.toFixed(1);
          if (diff > 0) {
            diffHtml = `<span style="color: #34d399; font-size: 11px;">+${formatted}</span>`;
          } else if (diff < 0) {
            diffHtml = `<span style="color: #f87171; font-size: 11px;">${formatted}</span>`;
          } else {
            diffHtml = '<span style="font-size: 11px;">0</span>';
          }
        }

        html += `<td style="padding: 8px 10px; border: 1px solid #334155; text-align: center; background: #0f172a; font-size: 12px;">${diffHtml}</td>`;
      }

      html += '</tr>';
    });

    return html;
  }

  // 颜色变浅函数（混合白色）
  lightenColor(hex, ratio) {
    // 解析 hex 颜色
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);

    // 与白色 (255, 255, 255) 混合
    const newR = Math.round(r + (255 - r) * ratio);
    const newG = Math.round(g + (255 - g) * ratio);
    const newB = Math.round(b + (255 - b) * ratio);

    return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
  }

  toggleDetail(detailId, toggleElement) {
    // 查找所有以 detailId 开头的明细行（detailId-0, detailId-1, ...）
    const detailRows = document.querySelectorAll(`tr[id^="${detailId}-"]`);
    const isExpanded = detailRows[0]?.style.display !== 'none';

    detailRows.forEach(row => {
      row.style.display = isExpanded ? 'none' : 'table-row';
    });

    // 切换箭头方向
    toggleElement.innerHTML = isExpanded ? `▶ ${toggleElement.textContent.replace('▼', '').trim()}` : `▼ ${toggleElement.textContent.replace('▶', '').trim()}`;
  }
}

// 全局实例
const reviewUI = new ReviewUI();
window.addEventListener('DOMContentLoaded', () => {
  reviewUI.init();
});

// 全局函数（供 HTML onclick 调用）
function editGoals() { reviewUI.editGoals(); }
function closeGoalModal() { reviewUI.closeGoalModal(); }
function addGoalInput() { reviewUI.addGoalInput(); }
function saveGoals() { reviewUI.saveGoalsFromModal(); }
function startChat() { reviewUI.startChat(); }
function sendMessage() { reviewUI.sendMessage(); }
function finishChatAndGenerateReport() { reviewUI.finishChatAndGenerateReport(); }
function saveCurrentReview() { reviewUI.saveCurrentReview(); }
function backToStart() { reviewUI.backToStart(); }

// Enter 键发送消息
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('user-input');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }
});
