import { Router } from 'express';
import { asyncHandler } from '../middleware/error.js';
import { getDb, mapInspiration } from '../db/index.js';

export const reviewRouter = Router();

reviewRouter.get('/random', asyncHandler(async (req, res) => {
  const db = getDb();
  const mode = req.query.mode || 'all';
  const themeId = req.query.themeId;

  let where = '';
  const params = {};

  if (mode === 'raw') {
    where = "WHERE i.status = 'raw'";
  } else if (mode === 'theme' && themeId) {
    where = `WHERE EXISTS (SELECT 1 FROM theme_inspirations ti WHERE ti.inspiration_id = i.id AND ti.theme_id = @themeId)`;
    params.themeId = themeId;
  }

  const row = db.prepare(`
    SELECT i.*,
      COALESCE((SELECT json_group_array(json_object('id', t.id, 'title', t.title, 'color', t.color))
        FROM theme_inspirations ti JOIN themes t ON t.id = ti.theme_id WHERE ti.inspiration_id = i.id), '[]') AS themes
    FROM inspirations i
    ${where}
    ORDER BY RANDOM()
    LIMIT 1
  `).get(params);

  if (!row) return res.status(404).json({ error: '没有符合条件的灵感' });
  res.json(mapInspiration(row));
}));
