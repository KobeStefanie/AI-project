import { Router } from 'express';
import { asyncHandler } from '../middleware/error.js';
import { getDb } from '../db/index.js';

export const calendarRouter = Router();

calendarRouter.get('/', asyncHandler(async (req, res) => {
  const db = getDb();
  const month = req.query.month; // YYYY-MM

  let dateFilter = '';
  const params = {};

  if (month) {
    dateFilter = `WHERE created_at >= @start AND created_at < @end`;
    params.start = `${month}-01`;
    const [y, m] = month.split('-').map(Number);
    const nextMonth = m === 12 ? `${y + 1}-01` : `${y}-${String(m + 1).padStart(2, '0')}`;
    params.end = `${nextMonth}-01`;
  }

  const rows = db.prepare(`
    SELECT
      DATE(created_at) AS date,
      COUNT(*) AS count,
      json_group_array(DISTINCT mood) AS moods,
      json_group_array(DISTINCT json_extract(keywords, '$[0]')) AS top_keywords
    FROM inspirations
    ${dateFilter}
    GROUP BY DATE(created_at)
    ORDER BY date ASC
  `).all(params);

  const items = rows.map(row => ({
    date: row.date,
    count: row.count,
    moods: parseSafe(row.moods, []),
    topKeywords: parseSafe(row.top_keywords, []).filter(Boolean).slice(0, 3)
  }));

  res.json({ items });
}));

calendarRouter.get('/date/:date', asyncHandler(async (req, res) => {
  const db = getDb();
  const rows = db.prepare(`
    SELECT id, content, summary, mood, status, keywords, created_at
    FROM inspirations
    WHERE DATE(created_at) = @date
    ORDER BY created_at DESC
  `).all({ date: req.params.date });

  res.json({ items: rows.map(row => ({
    id: row.id,
    content: row.content,
    summary: row.summary,
    mood: row.mood,
    status: row.status,
    keywords: JSON.parse(row.keywords || '[]'),
    createdAt: row.created_at
  })) });
}));

function parseSafe(str, fallback) {
  if (!str) return fallback;
  try { return JSON.parse(str); } catch { return fallback; }
}
