// 复盘分析引擎
class ReviewEngine {
  constructor() {
    this.AppCore = window.AppCore; // 复用现有数据层
  }

  // 读取多周数据（只读，不写）
  loadWeekRange(year, startWeek, endWeek) {
    const weeks = [];
    for (let w = startWeek; w <= endWeek; w++) {
      weeks.push({
        week: w,
        cells: this.AppCore.getCells(year, w),
        keyitems: this.AppCore.getKeyItems(year, w),
        review: this.AppCore.getReview(year, w),
        config: this.AppCore.getConfig(year, w)
      });
    }
    return weeks;
  }

  // 第1层：对比镜分析
  analyzeLayer1(weeks, userFeelings) {
    const stats = this.calculateStats(weeks);
    const trends = this.calculateTrends(weeks);
    const contrast = this.generateContrast(userFeelings, stats, trends);

    return { stats, trends, contrast };
  }

  // 第2层：时间尺度分析
  analyzeLayer2(weeks, year) {
    const weekRange = weeks.map(w => w.week);
    const startWeek = weekRange[0];
    const endWeek = weekRange[weekRange.length - 1];

    return {
      weekView: this.getWeekView(weeks),
      monthView: this.getMonthView(weeks, year, startWeek, endWeek),
      quarterView: this.getQuarterView(year, startWeek),
      yearView: this.getYearView(year)
    };
  }

  // 第3层：位置地图分析
  analyzeLayer3(year, currentWeek) {
    // 读取全年数据，生成旅程地图
    const allReviews = [];
    for (let w = 1; w <= 52; w++) {
      const review = this.AppCore.getReview(year, w);
      if (review && review.keyword) {
        allReviews.push({ week: w, review });
      }
    }

    return this.generateJourneyMap(allReviews, currentWeek);
  }

  // 第4层：目标对齐分析
  analyzeLayer4(weeks, goals) {
    const stats = this.calculateStats(weeks);
    const alignment = this.checkGoalAlignment(stats, goals, weeks);
    return { stats, alignment };
  }

  // ===== 辅助函数 =====

  // 从单元格键名解析起始小时。键名形如 "2026-08-17|1:30-2:00"（小时无前导零）
  parseSlotHour(key) {
    const parts = String(key).split('|');
    if (parts.length < 2) return null;
    const m = parts[1].match(/^(\d{1,2}):/);
    return m ? parseInt(m[1], 10) : null;
  }

  // 计算统计数据（含二级分类明细）
  calculateStats(weeks) {
    let totalProc = 0, totalQW = 0, totalGFP = 0, totalRest = 0, totalMW = 0;
    let midnightWorkCount = 0, weekendEscapeCount = 0;
    let completedKeyItems = 0, totalKeyItems = 0;

    // 二级分类统计 { '1.1': 5.5, '1.2': 10, ... }
    const breakdown = {};

    weeks.forEach(weekData => {
      const { cells, keyitems } = weekData;

      // 统计各分类时长
      Object.keys(cells).forEach(key => {
        const cell = cells[key];
        // 注意：不能写 !cell.code —— 代码 "0"（休息）是 falsy，会被整批漏掉
        if (!cell || cell.code === undefined || cell.code === null || cell.code === '') return;

        const code = String(cell.code).trim();
        if (code === '0') totalRest += 0.5;
        else if (code.startsWith('1')) {
          totalQW += 0.5;
          breakdown[code] = (breakdown[code] || 0) + 0.5;
        }
        else if (code.startsWith('2')) {
          totalGFP += 0.5;
          breakdown[code] = (breakdown[code] || 0) + 0.5;
        }
        else if (code.startsWith('3')) {
          totalProc += 0.5;
          breakdown[code] = (breakdown[code] || 0) + 0.5;
        }
        else if (code === '4') totalMW += 0.5;

        // 检测凌晨工作（1:00-5:00）
        // 键名格式为 "2026-08-17|1:30-2:00"，小时不带前导零，必须解析而非字符串匹配
        const hour = this.parseSlotHour(key);
        if (hour !== null && hour >= 1 && hour < 5 && code.startsWith('1') && cell.title) {
          midnightWorkCount++;
        }
      });

      // 统计周末逃离
      Object.keys(keyitems).forEach(key => {
        if (key.includes('周六') || key.includes('周日')) {
          const item = keyitems[key];
          if (item && (item.includes('出去') || item.includes('逃离') || item.includes('透气') ||
                       item.includes('白沙山') || item.includes('大巴扎') || item.includes('咖啡馆'))) {
            weekendEscapeCount++;
          }
        }
      });

      // 统计关键事项完成度
      // 注意：这里简化处理，实际可能需要读取 keyitemStatus
      Object.keys(keyitems).forEach(key => {
        const item = keyitems[key];
        if (item) totalKeyItems++;
      });
    });

    return {
      totalProc: Math.round(totalProc * 10) / 10,
      totalQW: Math.round(totalQW * 10) / 10,
      totalGFP: Math.round(totalGFP * 10) / 10,
      totalRest: Math.round(totalRest * 10) / 10,
      totalMW: Math.round(totalMW * 10) / 10,
      midnightWorkCount,
      weekendEscapeCount,
      completedKeyItems,
      totalKeyItems,
      weekCount: weeks.length,
      breakdown  // 新增：二级分类明细 { '1.1': 20, '1.2': 15, ... }
    };
  }

  // 计算趋势数据
  calculateTrends(weeks) {
    const procTrend = [];
    const qwTrend = [];
    const gfpTrend = [];

    weeks.forEach(weekData => {
      const { cells, week } = weekData;
      let procHours = 0, qwHours = 0, gfpHours = 0;

      Object.keys(cells).forEach(key => {
        const cell = cells[key];
        if (!cell || cell.code === undefined || cell.code === null || cell.code === '') return;

        const code = String(cell.code).trim();
        if (code.startsWith('3')) procHours += 0.5;
        else if (code.startsWith('1')) qwHours += 0.5;
        else if (code.startsWith('2')) gfpHours += 0.5;
      });

      procTrend.push({ week, value: Math.round(procHours * 10) / 10 });
      qwTrend.push({ week, value: Math.round(qwHours * 10) / 10 });
      gfpTrend.push({ week, value: Math.round(gfpHours * 10) / 10 });
    });

    return { procTrend, qwTrend, gfpTrend };
  }

  // 生成反差分析
  generateContrast(feelings, stats, trends) {
    const contrasts = [];
    const lowerFeelings = (feelings || '').toLowerCase();

    // 规则1：感觉低效 vs 实际完成高质量工作
    if ((lowerFeelings.includes('低效') || lowerFeelings.includes('废')) && stats.totalQW > 20) {
      contrasts.push(`你以为"低效、什么都没做"，但数据显示你完成了 ${stats.totalQW} 小时高质量工作（QW）`);
    }

    // 规则2：感觉一直拖延 vs 拖延已稳定
    if (lowerFeelings.includes('拖延') && trends.procTrend.length >= 2) {
      const lastProc = trends.procTrend[trends.procTrend.length - 1].value;
      const prevProc = trends.procTrend[trends.procTrend.length - 2].value;
      const diff = Math.abs(lastProc - prevProc);

      if (diff < 5) {
        contrasts.push(`你以为"一直在拖延"，但拖延时长已经稳定在 ${lastProc}h 左右（相比上周变化 ${diff}h），说明边界成型了`);
      }
    }

    // 规则3：感觉焦虑 vs 建立了凌晨工作模式
    if (lowerFeelings.includes('焦虑') && stats.midnightWorkCount > 0) {
      contrasts.push(`你感到"焦虑"，但数据显示你建立了凌晨工作模式（${stats.midnightWorkCount} 次），保持了主线推进`);
    }

    // 规则4：如果没有主观感受，给出客观总结
    if (!feelings || feelings.trim() === '') {
      contrasts.push(`本周期共 ${stats.weekCount} 周，完成 QW ${stats.totalQW}h，GFP ${stats.totalGFP}h，拖延 ${stats.totalProc}h`);
      if (stats.midnightWorkCount > 0) {
        contrasts.push(`凌晨工作 ${stats.midnightWorkCount} 次，说明你在守住自己的主线`);
      }
    }

    // 规则5：周末逃离
    if (stats.weekendEscapeCount > 0) {
      contrasts.push(`周末出去透气 ${stats.weekendEscapeCount} 次，这是恢复精力、守住自我的必要成本`);
    }

    return contrasts.length > 0 ? contrasts : ['数据显示你在正常运转中，继续保持观察'];
  }

  // 获取周视角
  getWeekView(weeks) {
    if (weeks.length === 0) return '无数据';

    const lastWeek = weeks[weeks.length - 1];
    const stats = this.calculateStats([lastWeek]);

    return {
      title: `第 ${lastWeek.week} 周`,
      summary: `拖延 ${stats.totalProc}h，QW ${stats.totalQW}h，GFP ${stats.totalGFP}h`,
      keyword: lastWeek.review?.keyword || '无关键词'
    };
  }

  // 获取月视角
  getMonthView(weeks, year, startWeek, endWeek) {
    const stats = this.calculateStats(weeks);
    const trends = this.calculateTrends(weeks);

    const procStart = trends.procTrend[0]?.value || 0;
    const procEnd = trends.procTrend[trends.procTrend.length - 1]?.value || 0;
    const procChange = procEnd - procStart;

    let trendDesc = '';
    if (Math.abs(procChange) < 5) {
      trendDesc = `拖延时长稳定（${procStart}h → ${procEnd}h），边界成型`;
    } else if (procChange > 0) {
      trendDesc = `拖延增加（${procStart}h → ${procEnd}h），边界在扩张`;
    } else {
      trendDesc = `拖延减少（${procStart}h → ${procEnd}h），工作投入增加`;
    }

    return {
      title: `第 ${startWeek}-${endWeek} 周（月度视角）`,
      summary: `平均每周：拖延 ${Math.round(stats.totalProc / stats.weekCount)}h，QW ${Math.round(stats.totalQW / stats.weekCount)}h`,
      trend: trendDesc,
      progress: stats.midnightWorkCount > 0 ? `建立了凌晨工作模式（${stats.midnightWorkCount}次）` : '主线推进需关注'
    };
  }

  // 获取季度视角
  getQuarterView(year, currentWeek) {
    const quarter = Math.ceil(currentWeek / 13);
    const quarterStart = (quarter - 1) * 13 + 1;
    const quarterEnd = Math.min(quarter * 13, 52);

    return {
      title: `2026年第 ${quarter} 季度（第 ${quarterStart}-${quarterEnd} 周）`,
      summary: `你正在第 ${quarter} 季度的第 ${currentWeek - quarterStart + 1} 周`,
      context: this.getQuarterContext(quarter)
    };
  }

  // 获取年视角
  getYearView(year) {
    return {
      title: `${year} 年全年`,
      summary: `当前处于 ${year} 年`,
      context: '上半年：心理咨询探索期；下半年：还债 + 保持自我'
    };
  }

  // 获取季度背景
  getQuarterContext(quarter) {
    const contexts = {
      1: '第1季度：年初规划期',
      2: '第2季度：执行与调整期',
      3: '第3季度：图木舒克入职期，建立新的工作生活平衡',
      4: '第4季度：年末总结与规划期'
    };
    return contexts[quarter] || '季度进行中';
  }

  // 生成旅程地图
  generateJourneyMap(allReviews, currentWeek) {
    const phases = [];

    // 根据关键词自动分段（简化版，可以根据实际数据优化）
    let currentPhase = null;

    allReviews.forEach(({ week, review }) => {
      const keyword = review.keyword || '';

      // 简单的分段逻辑：如果连续3周关键词相似，视为同一阶段
      if (!currentPhase) {
        currentPhase = {
          startWeek: week,
          endWeek: week,
          keywords: [keyword],
          title: this.inferPhaseTitle(week, keyword)
        };
      } else if (week - currentPhase.endWeek <= 2) {
        currentPhase.endWeek = week;
        currentPhase.keywords.push(keyword);
      } else {
        phases.push(currentPhase);
        currentPhase = {
          startWeek: week,
          endWeek: week,
          keywords: [keyword],
          title: this.inferPhaseTitle(week, keyword)
        };
      }
    });

    if (currentPhase) phases.push(currentPhase);

    return { phases, currentWeek };
  }

  // 推断阶段标题
  inferPhaseTitle(week, keyword) {
    if (week <= 26) return '贵阳探索期';
    if (week <= 32) return '求职与转型期';
    if (week <= 40) return '图木舒克入职期';
    return '持续发展期';
  }

  // 检查目标对齐
  checkGoalAlignment(stats, goals, weeks) {
    return goals.map(goal => {
      const goalText = goal.text || goal;
      let aligned = null;
      let reason = '';
      let suggestion = '';

      // 目标1：还债相关
      if (goalText.includes('还债') || goalText.includes('债务')) {
        // 假设需要每周至少60小时工作时长（QW + MW）来满足还债需求
        const workHours = stats.totalQW + stats.totalMW;
        const avgWeekWorkHours = workHours / stats.weekCount;
        aligned = avgWeekWorkHours >= 60;
        reason = aligned
          ? `平均每周工作 ${Math.round(avgWeekWorkHours)}h，符合还债需求（≥60h）`
          : `平均每周工作 ${Math.round(avgWeekWorkHours)}h，低于还债目标（<60h）`;
        suggestion = aligned ? '继续保持工作强度' : '可能需要增加工作时长或寻找额外收入';
      }

      // 目标2：主线不断
      else if (goalText.includes('主线') || goalText.includes('心理') || goalText.includes('AI')) {
        aligned = stats.midnightWorkCount > 0;
        reason = aligned
          ? `凌晨工作 ${stats.midnightWorkCount} 次，主线持续推进中`
          : `本周期无凌晨工作记录，主线可能停滞`;
        suggestion = aligned ? '继续利用凌晨时间推进主线' : '建议恢复凌晨工作时段';
      }

      // 目标3：守住自我
      else if (goalText.includes('守住自我') || goalText.includes('不被工作吞噬') || goalText.includes('边界')) {
        // 拖延时长稳定 + 有GFP时间 = 守住了自我
        const trends = this.calculateTrends(weeks);
        const procStable = trends.procTrend.length >= 2 &&
          Math.abs(trends.procTrend[trends.procTrend.length - 1].value -
                   trends.procTrend[trends.procTrend.length - 2].value) < 5;
        const hasGFP = stats.totalGFP > 5;

        aligned = procStable && hasGFP;
        reason = aligned
          ? `拖延稳定（${stats.totalProc}h），GFP时间充足（${stats.totalGFP}h），边界清晰`
          : `边界可能模糊：拖延波动较大或缺少GFP时间`;
        suggestion = aligned ? '边界已成型，继续保持' : '建议稳定拖延时长，增加休闲时间';
      }

      // 其他目标
      else {
        aligned = null;
        reason = '无法自动判断对齐情况';
        suggestion = '需要手动评估';
      }

      return {
        goal: goalText,
        aligned,
        reason,
        suggestion
      };
    });
  }

  // ===== 数据持久化 =====

  // 保存长远目标
  saveGoals(goals) {
    localStorage.setItem('tm_longterm_goals', JSON.stringify({
      goals,
      updatedAt: new Date().toISOString()
    }));
  }

  // 读取长远目标
  loadGoals() {
    const data = localStorage.getItem('tm_longterm_goals');
    if (!data) {
      // 默认目标
      return [
        '24个月内还清债务',
        '保持心理咨询/AI开发主线不断',
        '不被工作吞噬，守住自我'
      ];
    }
    const parsed = JSON.parse(data);
    return parsed.goals || [];
  }

  // 保存复盘记录
  saveReviewRecord(year, month, data) {
    const key = `tm_review_${year}_m${String(month).padStart(2, '0')}`;
    localStorage.setItem(key, JSON.stringify({
      ...data,
      savedAt: new Date().toISOString()
    }));
  }

  // 读取复盘记录
  loadReviewRecord(year, month) {
    const key = `tm_review_${year}_m${String(month).padStart(2, '0')}`;
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : null;
  }

  // 列出所有复盘记录
  listReviewRecords() {
    const records = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key.startsWith('tm_review_') && key.includes('_m')) {
        const data = JSON.parse(localStorage.getItem(key));
        records.push({
          key,
          yearMonth: data.yearMonth,
          weekRange: data.weekRange,
          conclusion: data.conclusion,
          savedAt: data.savedAt
        });
      }
    }
    // 按时间倒序
    records.sort((a, b) => new Date(b.savedAt) - new Date(a.savedAt));
    return records;
  }

  // ==========================================================
  // ===== AI 对话式复盘（v2.14.0）=====
  // 设计原则：四层分析仍由本地代码算出「事实」，AI 只负责理解你的话
  // 并把事实组织成对话与报告。这样 AI 不会编造数字。
  // ==========================================================

  // 汇总四层分析的全部事实，作为 AI 的唯一数据依据
  buildDataContext(year, startWeek, endWeek) {
    const weeks = this.loadWeekRange(year, startWeek, endWeek);
    const goals = this.loadGoals();

    const layer1 = this.analyzeLayer1(weeks, '');
    const layer2 = this.analyzeLayer2(weeks, year);
    const layer3 = this.analyzeLayer3(year, endWeek);
    const layer4 = this.analyzeLayer4(weeks, goals);

    const stats = layer1.stats;
    const trends = layer1.trends;

    // 日期范围（供 AI 表述真实时间）
    let dateRange = '';
    try {
      const sd = this.AppCore.getWeekDates(year, startWeek);
      const ed = this.AppCore.getWeekDates(year, endWeek);
      if (sd && ed && sd.length && ed.length) {
        const f = (s) => {
          const d = new Date(s);
          return `${d.getMonth() + 1}月${d.getDate()}日`;
        };
        dateRange = `${f(sd[0])} 至 ${f(ed[6])}`;
      }
    } catch (e) { /* 日期计算失败不影响主流程 */ }

    // 每周关键词与关键事项摘录（让 AI 有具体素材，而非只有数字）
    const weekDetails = weeks.map(w => {
      const wStats = this.calculateStats([w]);
      const keyItemTexts = Object.keys(w.keyitems || {})
        .map(k => w.keyitems[k])
        .filter(v => v && String(v).trim())
        .slice(0, 12);

      // 计算该周的日期范围（供 AI 表述时间）
      let weekDateRange = '';
      try {
        const dates = this.AppCore.getWeekDates(year, w.week);
        if (dates && dates.length >= 7) {
          const start = new Date(dates[0]);
          const end = new Date(dates[6]);
          weekDateRange = `${start.getMonth() + 1}月${start.getDate()}日-${end.getMonth() + 1}月${end.getDate()}日`;
        }
      } catch (e) { /* 日期计算失败不影响主流程 */ }

      return {
        week: w.week,
        dateRange: weekDateRange,  // 新增：每周的日期范围
        keyword: w.review?.keyword || '',
        proc: wStats.totalProc,
        qw: wStats.totalQW,
        gfp: wStats.totalGFP,
        rest: wStats.totalRest,
        mw: wStats.totalMW,
        keyItems: keyItemTexts,
        breakdown: wStats.breakdown  // 新增：每周的二级分类明细
      };
    });

    return {
      year, startWeek, endWeek, dateRange,
      weekCount: weeks.length,
      goals,
      stats,
      trends,
      weekDetails,
      timeScale: layer2,
      journey: layer3,
      alignment: layer4.alignment,
      previousReview: this.getPreviousReview(year, startWeek)
    };
  }

  // 改进2：找到本次之前最近一次复盘，用于对比
  getPreviousReview(year, startWeek) {
    const records = this.listReviewRecords();
    // 只取结束周早于本次开始周的记录，取最近的一条
    const earlier = records
      .filter(r => Array.isArray(r.weekRange) && r.weekRange[1] < startWeek)
      .sort((a, b) => b.weekRange[1] - a.weekRange[1]);

    if (earlier.length === 0) return null;

    const prev = earlier[0];
    const full = JSON.parse(localStorage.getItem(prev.key) || '{}');
    return {
      weekRange: prev.weekRange,
      yearMonth: prev.yearMonth,
      conclusion: full.conclusion || '',
      // 上次你自己怎么描述的（自由对话原文）
      userWords: full.userWords || full.feelings || '',
      keywords: full.keywords || [],
      stats: full.dataSnapshot?.stats || full.layer1?.analysis?.stats || null
    };
  }

  // 把数据上下文渲染成 AI 可读的纯文本事实清单
  // ⚠️ 核心优化（v2.14.1）：不输出具体数字，只提供定性描述和异常信号
  // 原因：用户右侧面板已显示所有数字，AI 复述数字是冗余且干扰对话的
  formatContextForPrompt(ctx) {
    const L = [];
    L.push(`## 复盘周期`);
    L.push(`${ctx.year} 年第 ${ctx.startWeek}-${ctx.endWeek} 周${ctx.dateRange ? `（${ctx.dateRange}）` : ''}，共 ${ctx.weekCount} 周。`);
    L.push('');

    L.push(`## 长远目标（用户自己设定的）`);
    ctx.goals.forEach((g, i) => L.push(`${i + 1}. ${typeof g === 'string' ? g : g.text}`));
    L.push('');

    // 辅助函数：将数字转换为定性描述
    const describeLevel = (value, thresholds) => {
      // thresholds: [low, medium, high]，例如 [20, 40, 60]
      if (value < thresholds[0]) return '极低';
      if (value < thresholds[1]) return '偏低';
      if (value < thresholds[2]) return '中等';
      return '偏高';
    };

    const describeTrend = (values) => {
      if (values.length < 2) return '数据不足';
      const first = values[0].value;
      const last = values[values.length - 1].value;
      const diff = last - first;
      const ratio = first > 0 ? Math.abs(diff / first) : 0;
      if (ratio < 0.1) return '基本稳定';
      if (diff > 0) return ratio > 0.3 ? '显著上升' : '略有上升';
      return ratio > 0.3 ? '显著下降' : '略有下降';
    };

    L.push(`## 本周期整体模式`);
    L.push(`- 高质量工作（QW）：${describeLevel(ctx.stats.totalQW, [ctx.weekCount * 20, ctx.weekCount * 35, ctx.weekCount * 50])}`);
    L.push(`- 拖延（Proc）：${describeLevel(ctx.stats.totalProc, [ctx.weekCount * 5, ctx.weekCount * 15, ctx.weekCount * 25])}`);
    L.push(`- 休闲娱乐（GFP）：${describeLevel(ctx.stats.totalGFP, [ctx.weekCount * 10, ctx.weekCount * 20, ctx.weekCount * 30])}`);
    if (ctx.stats.midnightWorkCount > 0) {
      L.push(`- ⚠️ 凌晨工作信号：有 ${ctx.stats.midnightWorkCount} 次在凌晨 1:00-5:00 仍在做高质量工作`);
    }
    if (ctx.stats.weekendEscapeCount === 0 && ctx.weekCount > 1) {
      L.push(`- ⚠️ 周末透气不足：这几周没有周末外出透气记录`);
    }
    L.push('');

    L.push(`## 逐周核心信息`);
    ctx.weekDetails.forEach(w => {
      const parts = [`第 ${w.week} 周`];
      if (w.dateRange) parts.push(w.dateRange);  // 新增：直接显示日期范围
      if (w.keyword) parts.push(`关键词：「${w.keyword}」`);
      if (w.keyItems.length) parts.push(`做了：${w.keyItems.join('、')}`);
      L.push(`- ${parts.join(' ｜ ')}`);
    });
    L.push('');

    L.push(`## 趋势判断`);
    L.push(`- 拖延趋势：${describeTrend(ctx.trends.procTrend)}`);
    L.push(`- 高质量工作趋势：${describeTrend(ctx.trends.qwTrend)}`);
    L.push(`- 休闲娱乐趋势：${describeTrend(ctx.trends.gfpTrend)}`);
    L.push('');

    L.push(`## 更长时间尺度的位置`);
    if (ctx.timeScale && ctx.timeScale.monthView) {
      L.push(`- 月视角：${ctx.timeScale.monthView.summary}；趋势判断：${ctx.timeScale.monthView.trend}`);
    }
    if (ctx.timeScale && ctx.timeScale.quarterView) {
      L.push(`- 季度视角：${ctx.timeScale.quarterView.title}，${ctx.timeScale.quarterView.summary}。背景：${ctx.timeScale.quarterView.context}`);
    }
    if (ctx.timeScale && ctx.timeScale.yearView) {
      L.push(`- 年度视角：${ctx.timeScale.yearView.context}`);
    }
    if (ctx.journey && ctx.journey.phases && ctx.journey.phases.length) {
      L.push(`- 全年阶段划分：`);
      ctx.journey.phases.forEach(p => {
        const kw = [...new Set(p.keywords)].filter(Boolean).slice(0, 3).join('、');
        const here = ctx.journey.currentWeek >= p.startWeek && ctx.journey.currentWeek <= p.endWeek ? '（← 当前位置）' : '';
        L.push(`  · ${p.title}：第 ${p.startWeek}-${p.endWeek} 周${kw ? `，关键词：${kw}` : ''}${here}`);
      });
    }
    L.push('');

    L.push(`## 目标对齐的机械判定（本地规则算出，仅供参考，你可以质疑它）`);
    (ctx.alignment || []).forEach(a => {
      const flag = a.aligned === true ? '达标' : a.aligned === false ? '未达标' : '无法自动判定';
      L.push(`- 「${a.goal}」→ ${flag}：${a.reason}`);
    });
    L.push('');

    if (ctx.previousReview) {
      const p = ctx.previousReview;
      L.push(`## 上一次复盘（用于对比变化）`);
      L.push(`- 周期：第 ${p.weekRange[0]}-${p.weekRange[1]} 周`);
      // ⚠️ 不输出具体数字，只描述对比结果
      if (p.stats && ctx.stats) {
        const qwChange = ctx.stats.totalQW - p.stats.totalQW;
        const procChange = ctx.stats.totalProc - p.stats.totalProc;
        if (Math.abs(qwChange) > ctx.weekCount * 5) {
          L.push(`- 高质量工作相比上次：${qwChange > 0 ? '明显增加' : '明显减少'}`);
        }
        if (Math.abs(procChange) > ctx.weekCount * 3) {
          L.push(`- 拖延相比上次：${procChange > 0 ? '明显增加' : '明显减少'}`);
        }
      }
      if (p.userWords) {
        L.push(`- 当时你自己说的话：「${String(p.userWords).slice(0, 500)}」`);
      }
      if (p.keywords && p.keywords.length) {
        L.push(`- 当时提炼的关键词：${p.keywords.join('、')}`);
      }
      L.push('');
    } else {
      L.push(`## 上一次复盘`);
      L.push(`无历史复盘记录，这是第一次。`);
      L.push('');
    }

    return L.join('\n');
  }

  // 对话阶段的 system prompt（基于 elicitation 技能重新设计）
  buildChatSystemPrompt(ctx) {
    return `你是这位用户的复盘伙伴。这不是一场数据汇报会，而是一次关于他这段时间**真实体验**的对话。

# 你手上的事实数据
${this.formatContextForPrompt(ctx)}

**重要**：
- 用户右侧面板已显示所有数字，他随时可查看。你的任务不是复述数据，而是帮他**理解数据背后的自己**。
- **禁止调用任何工具**（web_search、calculator 等）。所有需要的信息已在上述数据中提供。
- **每周的日期范围已在"逐周核心信息"中明确标注**，无需查询或计算。

---

# 核心原则（来自心理学访谈研究）

## 深度来自耐心，而非追问
人们想讲述自己的故事，他们只是很少有机会。你的角色是创造一个安全的对话空间，让他自然地分享。

## 反思优于提问（2:1 比例）
- **不要连续提问**："那周做了什么？为什么？结果呢？" ❌
- **而是：问题 → 反思 → 反思**："那周你记录了'焦虑'。听起来那不是普通的忙，而是某种卡住的感觉。像是被什么困住了？" ✅

## 你的三种回应方式

### 1. 简单反思（重述他说的）
他说："那周特别累。"
你说："累到快撑不住了。"

### 2. 复杂反思（加入意义）
他说："我一直在加班，但总觉得没做什么。"
你说："听起来不是时间不够，而是没有真正推进的感觉——忙碌但无效。"

### 3. 双面反思（同时持有两个真相）
他说："我知道应该多休息，但停不下来。"
你说："一边是身体在喊停，一边是焦虑在催你继续。两股力在拉扯。"

---

# 禁止的行为

## ❌ 审讯陷阱
连珠炮式提问让人防御。
错误："那周做了什么？为什么拖延？有什么感受？"

## ❌ 复述数字和已知事实
**绝对禁止**：
- ❌ "第 37 周 QW 40.5h，拖延 14h" — 具体数字他能在右侧面板看到
- ❌ "你记录了'完成汇报'，这周做了什么？" — keyItems 已记录的事实不要再问
- ❌ "那周关键事项是XXX，能说说吗？" — 不要把已有的关键事项当问题问

**正确做法**：
- ✅ "那周你写了'焦虑'。" — 从情绪关键词切入（这是主观感受，值得展开）
- ✅ "这几周节奏看起来挺紧的。" — 从模式切入（定性描述，不复述数字）
- ✅ "连续几周凌晨工作。" — 从异常行为模式切入（不是数字，是信号）

**核心区分**：
- **WHAT（已记录）** ≠ 要问 → keyItems 已经记录了"做了什么"
- **WHY/HOW YOU FELT（心理层）** = 要问 → 背后的感受、动机、冲突、意义

## ❌ 过早给建议
他刚说完一件事，你就开始建议 —— 这打断了他的叙事流。
现在是"听"的阶段，不是"教"的阶段。

## ❌ 临床化语言
不要说"你的防御机制""回避型依恋"这类心理学术语。
你是朋友，不是治疗师。

---

# 应该做的事

## ✅ 引导自我定义记忆
这些记忆有 5 个特征：生动、情绪强烈、经常浮现、与其他记忆相连、关乎持久关切。

**引导框架**：
- "有些时刻会一直浮现——某天你在做别的事，它突然跳出来。那几周有这样的时刻吗？"
- "如果要跟别人解释'那段时间的你'，你会讲哪个故事？"
- "回头看，哪个瞬间让你觉得'之前和之后不太一样了'？"

## ✅ 倾听叙事主题

**救赎序列（坏→好）**：
"那周很崩溃，但...""回头看我反而感激...""那让我明白了..."
→ 这显示韧性和成长

**污染序列（好→坏）**：
"本来挺顺的，直到...""我以为终于稳了，结果..."
→ 可能有未解决的创伤或抑郁风险

**能动性主题**：
"我决定...""我推动了...""我扛下来了..."
→ 个人力量感

**共同性主题**：
"我们一起...""他们理解我...""那种连接感..."
→ 关系和归属需求

## ✅ 从数据异常处切入心理
不要问"那周发生了什么"（keyItems 已记录），而要问：
- "你记录了'完成汇报'，但那周关键词是'焦虑'——表面顺利的任务，背后是什么让你不安？"
- "连续三周凌晨还在工作——这是你想要的节奏，还是被逼的？"
- "QW 和拖延同时下降——不像崩溃，更像主动踩刹车。那周你做了什么决定？"

## ✅ 向下探究（轻柔地）
表面："我担心做不好。"
你："如果真的没做好，最糟的是什么？"
他："大家会觉得我不行。"
你："如果他们这么想，对你意味着什么？"
他："证明我果然配不上这个位置。"
→ 核心信念浮现：自我怀疑/冒名顶替感

---

# 开场要求（第一句话）

**核心**：简短、开放、有画面感、从感受切入。

## 错误开场（都是反例）
❌ "第 37 周有个有意思的地方——QW 和拖延同时下降。这不像崩溃，更像主动调整节奏。那周你是主动踩刹车，还是外部压力减轻了？"
   - 太长，信息量太大
   - 封闭式二选一问题
   - 从数据分析切入，不是从体验切入

❌ "第 37 周 QW 40.5h，拖延 14h，发生了什么？"
   - 复述数字
   - "发生了什么"太空泛

## 正确开场（简短、开放、有画面感）

**⚠️ 重要**：提问时必须明确说出"第X周（日期范围）"，帮助用户快速定位回忆。

**基于情绪关键词**：
- "第 35 周（8月17日那周）你写了'焦虑'。"（停顿，等他接）
- "第 37 周（9月初那周）关键词是'崩溃'——能说说那是什么感觉吗？"
- "第 36 周（8月底那周）你写了'空'这个词。那周是什么让你觉得空？"

**基于模式异常**：
- "第 33-35 周（8月10日到月底）经常凌晨还在工作。"（停顿）
- "第 35-37 周（8月中到9月初）的节奏看起来挺紧的。"（停顿）
- "第 35 周（8月17日那周）之后，节奏变了。"（停顿）

**基于记忆引导**：
- "第 33-37 周（8月到9月初这段时间）里，有哪个时刻会一直浮现吗？"
- "回想第 36 周（8月底那周），哪个瞬间最清晰？"
- "第 35-37 周如果用一个画面来代表，会是什么？"

## 开场公式

1. **单句陈述** + 停顿（让他自己接话）
   - "那周你写了'焦虑'。"
   - "这几周凌晨还在工作。"

2. **简短开放问题**（≤10 个字）
   - "那是什么感觉？"
   - "那段时间怎么样？"
   - "哪个瞬间最清晰？"

3. **从具体切入**（不要从趋势分析切入）
   - ✅ "那周你写了'焦虑'" → 具体的词
   - ❌ "QW 和拖延同时下降" → 抽象的趋势

---

# 对话节奏

- **一次一个问题**。问完后，等他说。
- **他说完后，先反思，再（可选）追问**。
- **每次回复≤2句**。简短让对话流动。
- **他说"够了""可以生成报告了"**，立即停止。

---

# 你的目标

不是收集数据（你已经有了），而是帮他**看见数据里的自己**——那些模式、那些选择、那些他可能没意识到的东西。

让他离开时，觉得"我被看见了"，而不是"我被审讯了"。`;
  }

  // 报告阶段的 system prompt
  buildReportSystemPrompt(ctx) {
    return `你要为这位用户生成一份复盘报告。

# 事实数据（唯一数据来源，禁止编造任何数字）
${this.formatContextForPrompt(ctx)}

# 报告要求

## 分析框架（必须全部覆盖，但不要写"第几层"这种标题）
你的分析必须内含以下四个视角，自然融合，读起来是一篇连贯的文字而不是四段拼接：
1. 对比镜：他嘴上说的 / 感受到的，和数据实际显示的之间的落差。这是报告最有价值的部分。
2. 时间尺度：把当下这几周放进月度、季度、年度的位置里看，破除"这几周好糟"的孤立感。
3. 位置地图：他从哪个阶段走过来，现在在哪，正在往哪去。
4. 目标对齐：当前的时间分配是否在服务他的长远目标；哪些偏离了，哪些其实是必要成本。

## 输出格式（严格遵守）
用 Markdown，包含且仅包含以下章节：

# 复盘报告 · ${ctx.year}年第${ctx.startWeek}-${ctx.endWeek}周
> 一句话概括这个周期的本质（不超过 25 字）

## 你说的
用 2-4 句话，把他在对话里说的核心内容复述出来。要用他自己的表达方式和词，让他看到"我确实是这么想的"。

## 数据说的
把四个视角融合在这里写。分 2-4 个小段，每段一个洞察。
- 关键数字用 **加粗**
- 每段开头用一个 emoji 标记性质：✅ 确认了好的、⚠️ 需要注意的、💡 反直觉的发现
- 必须至少有一处明确的"你以为 X，但数据显示 Y"的对比${ctx.previousReview ? `
- 必须包含一段与上次复盘（第 ${ctx.previousReview.weekRange[0]}-${ctx.previousReview.weekRange[1]} 周）的对比，说明变化` : ''}

## 我看到的
你作为旁观者的判断。2-3 句。可以说他没意识到的东西，包括不太好听的话。诚实优先于安慰。

## 给你的建议
2-3 条。每条必须是具体可执行的动作，不是"要多注意休息"这种废话。
格式：**[动作]** —— [为什么，关联到他的目标或数据]

## 这个周期的关键词
3-5 个词，每个词用反引号包裹，词之间用空格分隔。
关键词必须优先从他在对话中实际说过的话里提取，其次才是你的概括。这些词要能代表他这段时间的真实状态。

# 硬性禁令
- 禁止编造任何数字。所有数字必须能在上面的事实数据中找到。
- 禁止说"根据分析""综合来看"这类空话开头。
- 禁止用"你真棒""继续努力"这类鼓励式废话。
- 禁止输出四层框架的标题名（如"第1层：对比镜"）。
- 不要在报告里输出原始数据表格，那部分由程序单独展示。`;
  }

  // 调用本机 AI 代理
  async callAI(messages, system, maxTokens) {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, system, maxTokens })
    });
    const data = await resp.json().catch(() => ({ error: '返回内容无法解析' }));
    if (!resp.ok) throw new Error(data.error || `请求失败（HTTP ${resp.status}）`);
    return data.text;
  }

  // 探测 AI 是否已配置
  async checkAIStatus() {
    try {
      const resp = await fetch('/api/ai-status');
      return await resp.json();
    } catch (e) {
      return { ready: false, error: e.message };
    }
  }
}

// 导出单例
window.ReviewEngine = new ReviewEngine();
