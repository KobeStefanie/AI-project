// 复盘中心 UI 层 - 简化版（按行斑马纹 + 完整子分类名称）

class ReviewUI {
  constructor() {
    this.currentYear = null;
    this.currentWeek = null;
  }

  // 渲染周期对比弹窗
  async showCompareDialog() {
    const modal = document.getElementById('modal-compare');
    modal.style.display = 'flex';

    // 默认最近4周
    const { getISOWeek } = window.AppCore;
    const now = new Date();
    const [year, week] = getISOWeek(now);

    document.getElementById('compare-year-start').value = year;
    document.getElementById('compare-week-start').value = week - 3;
    document.getElementById('compare-year-end').value = year;
    document.getElementById('compare-week-end').value = week;
  }

  closeCompareDialog() {
    document.getElementById('modal-compare').style.display = 'none';
  }

  // 加载周期数据并对比
  async loadCompareData() {
    const yearStart = parseInt(document.getElementById('compare-year-start').value);
    const weekStart = parseInt(document.getElementById('compare-week-start').value);
    const yearEnd = parseInt(document.getElementById('compare-year-end').value);
    const weekEnd = parseInt(document.getElementById('compare-week-end').value);

    // 生成周列表
    const weeks = [];
    let [y, w] = [yearStart, weekStart];
    while (y < yearEnd || (y === yearEnd && w <= weekEnd)) {
      weeks.push({ year: y, week: w });
      const { getNextWeek } = window.AppCore;
      [y, w] = getNextWeek(y, w);
      if (weeks.length > 10) break; // 最多10周
    }

    // 加载每周数据
    const weeksData = [];
    for (const { year, week } of weeks) {
      const weekData = await this.loadWeekData(year, week);
      weeksData.push({ year, week, ...weekData });
    }

    // 渲染对比表格
    this.renderCompareTable(weeksData);
  }

  async loadWeekData(year, week) {
    const { getWeekDates, getCells, getKeyItems, getConfig } = window.AppCore;
    const dates = getWeekDates(year, week);
    const cells = getCells(year, week);
    const keyitems = getKeyItems(year, week);
    const config = getConfig(year, week);

    // 统计数据（简化版，只调用 calcWeeklyStats）
    const stats = window.AppCore.calcWeeklyStats(year, week);

    return {
      dates,
      cells,
      keyitems,
      config,
      stats,
      hasData: Object.keys(cells).length > 0
    };
  }

  renderCompareTable(weeksData) {
    let html = '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 13px;">';

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

    let rowIndex = 0; // 用于行斑马纹

    // 数据行配置
    const rows = [
      {
        label: 'QW 时间',
        key: 'qw',
        format: v => v ? v.toFixed(1) + 'h' : '0h',
        hasDetail: true,
        detailKey: 'qwDetail',
        configKey: 'qwNames',
        bgColor: '#dcfce7'  // 浅绿色
      },
      {
        label: 'GFP 时间',
        key: 'gfp',
        format: v => v ? v.toFixed(1) + 'h' : '0h',
        hasDetail: true,
        detailKey: 'gfpDetail',
        configKey: 'gfpNames',
        bgColor: '#dbeafe'  // 浅蓝色
      },
      {
        label: '拖延时间',
        key: 'proc',
        format: v => v ? v.toFixed(1) + 'h' : '0h',
        hasDetail: true,
        detailKey: 'procDetail',
        configKey: 'procNames',
        bgColor: '#fee2e2'  // 浅红色
      },
      { label: '休息时间', key: 'rest', format: v => v ? v.toFixed(1) + 'h' : '0h', bgColor: '#f3f4f6' },
      { label: 'MW 时间', key: 'mw', format: v => v ? v.toFixed(1) + 'h' : '0h', bgColor: '#f3f4f6' },
      { label: '凌晨工作次数', key: 'lateWorkCount', format: v => v || 0, bgColor: '#f3f4f6' }
    ];

    rows.forEach((row) => {
      const detailId = `detail-${rowIndex}`;
      const isEven = rowIndex % 2 === 0;
      const rowBg = isEven ? 'white' : '#f9fafb'; // 白色和浅灰交替

      // 主行
      html += '<tr>';

      // 项目列
      if (row.hasDetail) {
        html += `<td style="padding: 10px; border: 1px solid #334155; background: ${row.bgColor}; font-weight: 500;">
          <span style="cursor: pointer; color: #1e293b;" onclick="reviewUI.toggleDetail('${detailId}', this)">
            ▶ ${row.label}
          </span>
        </td>`;
      } else {
        html += `<td style="padding: 10px; border: 1px solid #334155; background: ${row.bgColor}; color: #1e293b; font-weight: 500;">${row.label}</td>`;
      }

      // 获取所有周的值
      const values = weeksData.map(wd => {
        if (!wd.hasData) return null;
        return wd.stats.totals[row.key] || 0;
      });

      // 找出最大值（用于大字号显示）
      const maxValue = Math.max(...values.filter(v => v !== null));

      // 数据列
      values.forEach((v, i) => {
        const color = weeksData[i].hasData ? '#1e293b' : '#94a3b8';
        const content = v !== null ? row.format(v) : '-';

        // 大于最大值80%的数字用大字号+加粗
        const isBig = v !== null && maxValue > 0 && v >= maxValue * 0.8;
        const fontSize = isBig ? '16px' : '13px';
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
        html += this.renderDetailRows(weeksData, row, detailId, rowBg);
      }

      rowIndex++;
    });

    html += '</tbody></table></div>';

    // 说明
    html += '<div style="margin-top: 15px; padding: 12px; background: #1e293b; border-radius: 6px; color: #94a3b8; font-size: 12px;">';
    html += '<p style="margin: 0 0 8px 0;">说明：</p>';
    html += '<ul style="margin: 0; padding-left: 20px;">';
    html += '<li>点击 ▶ 可展开查看明细对比</li>';
    html += '<li>行背景色交替显示，便于阅读</li>';
    html += '<li>数值较大的格子用大字号+加粗显示</li>';
    html += '<li>绿色差值表示比上一周增加</li>';
    html += '<li>红色差值表示比上一周减少</li>';
    html += '</ul>';
    html += '</div>';

    document.getElementById('compare-result').innerHTML = html;
  }

  // 渲染明细行
  renderDetailRows(weeksData, parentRow, detailId, rowBg) {
    let html = '';

    // 从第一个有数据的周获取配置
    const firstValidWeek = weeksData.find(wd => wd.hasData);
    if (!firstValidWeek || !firstValidWeek.config) return html;

    const config = firstValidWeek.config;
    const names = config[parentRow.configKey] || [];

    // 遍历每个子分类
    names.forEach((name, idx) => {
      // 检查是否有任何一周有这个子分类的数据
      const hasAnyData = weeksData.some(wd => {
        if (!wd.hasData || !wd.stats.totals[parentRow.detailKey]) return false;
        const detailArray = wd.stats.totals[parentRow.detailKey];
        return Array.isArray(detailArray) && detailArray[idx] > 0;
      });

      if (!hasAnyData) return; // 跳过全是0的子分类

      html += `<tr id="${detailId}" style="display: none;">`;
      html += `<td style="padding: 8px 10px 8px 30px; border: 1px solid #334155; background: ${parentRow.bgColor}; color: #475569; font-size: 12px;">└ ${name}</td>`;

      // 获取所有周的这个子分类的值
      const values = weeksData.map(wd => {
        if (!wd.hasData || !wd.stats.totals[parentRow.detailKey]) return null;
        const detailArray = wd.stats.totals[parentRow.detailKey];
        if (!Array.isArray(detailArray) || idx >= detailArray.length) return null;
        return detailArray[idx] * 0.5; // 转换为小时（原始单位是半小时）
      });

      // 数据列
      values.forEach((v, i) => {
        if (v === null || v === 0) {
          html += `<td style="padding: 8px 10px; border: 1px solid #334155; text-align: center; color: #94a3b8; background: ${rowBg}; font-size: 12px;">-</td>`;
        } else {
          const content = v.toFixed(1) + 'h';
          html += `<td style="padding: 8px 10px; border: 1px solid #334155; text-align: center; color: #475569; background: ${rowBg}; font-size: 12px;">${content}</td>`;
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

  // 切换明细显示
  toggleDetail(detailId, arrow) {
    const detailRows = document.querySelectorAll(`tr[id="${detailId}"]`);
    const isExpanded = arrow.textContent.trim().startsWith('▼');

    detailRows.forEach(row => {
      row.style.display = isExpanded ? 'none' : '';
    });

    arrow.textContent = isExpanded ? `▶ ${arrow.textContent.substring(2)}` : `▼ ${arrow.textContent.substring(2)}`;
  }
}

// 全局实例
const reviewUI = new ReviewUI();
