import { Router } from 'express';
import { asyncHandler } from '../middleware/error.js';
import { getDb, mapInspiration } from '../db/index.js';

export const timelineRouter = Router();

timelineRouter.get('/', asyncHandler(async (req, res) => {
  const db = getDb();
  const filters = [];
  const params = {};

  if (req.query.from) {
    filters.push('i.created_at >= @from');
    params.from = req.query.from;
  }
  if (req.query.to) {
    filters.push('i.created_at <= @to');
    params.to = req.query.to;
  }
  if (req.query.status) {
    filters.push('i.status = @status');
    params.status = req.query.status;
  }
  if (req.query.theme) {
    filters.push('EXISTS (SELECT 1 FROM theme_inspirations ti WHERE ti.inspiration_id = i.id AND ti.theme_id = @theme)');
    params.theme = req.query.theme;
  }
  if (req.query.media) {
    filters.push('EXISTS (SELECT 1 FROM media_assets ma WHERE ma.inspiration_id = i.id AND ma.type = @media)');
    params.media = req.query.media;
  }

  const where = filters.length ? `WHERE ${filters.join(' AND ')}` : '';

  const rows = db.prepare(`
    SELECT i.*,
      COALESCE((SELECT json_group_array(json_object('id', t.id, 'title', t.title, 'color', t.color))
        FROM theme_inspirations ti JOIN themes t ON t.id = ti.theme_id WHERE ti.inspiration_id = i.id), '[]') AS themes,
      COALESCE((SELECT json_group_array(ma.type) FROM media_assets ma WHERE ma.inspiration_id = i.id), '[]') AS media_types
    FROM inspirations i
    ${where}
    ORDER BY i.created_at DESC
    LIMIT @limit OFFSET @offset
  `).all({
    ...params,
    limit: Math.min(Number(req.query.limit || 200), 500),
    offset: Number(req.query.offset || 0)
  });

  const items = rows.map(row => {
    const note = mapInspiration(row);
    const mediaTypes = JSON.parse(row.media_types || '[]');
    return { ...note, mediaTypes };
  });

  // Group by YYYY-MM
  const grouped = new Map();
  for (const item of items) {
    const month = item.createdAt.slice(0, 7);
    if (!grouped.has(month)) grouped.set(month, []);
    grouped.get(month).push(item);
  }

  const months = Array.from(grouped.entries()).map(([month, notes]) => ({
    month,
    count: notes.length,
    notes
  }));

  res.json({ months });
}));
