import { Router } from 'express';
import { nanoid } from 'nanoid';
import { asyncHandler } from '../middleware/error.js';
import { getDb, mapTheme, nowIso } from '../db/index.js';
import { getNoteById } from './notes.js';

export const themesRouter = Router();

themesRouter.get('/', asyncHandler(async (req, res) => {
  const rows = getDb().prepare(`
    SELECT t.*, COUNT(ti.inspiration_id) AS member_count
    FROM themes t
    LEFT JOIN theme_inspirations ti ON ti.theme_id = t.id
    GROUP BY t.id
    ORDER BY t.updated_at DESC
  `).all();
  res.json({ items: rows.map(mapTheme) });
}));

themesRouter.post('/', asyncHandler(async (req, res) => {
  if (!req.body?.title?.trim()) return res.status(400).json({ error: '主题标题不能为空' });
  const db = getDb();
  const now = nowIso();
  const theme = {
    id: nanoid(),
    title: req.body.title.trim(),
    description: req.body.description || '',
    color: req.body.color || '#f97316',
    notes: req.body.notes || '',
    createdAt: now,
    updatedAt: now
  };
  db.prepare(`
    INSERT INTO themes (id, title, description, color, notes, created_at, updated_at)
    VALUES (@id, @title, @description, @color, @notes, @createdAt, @updatedAt)
  `).run(theme);
  res.status(201).json({ ...theme, memberCount: 0 });
}));

themesRouter.get('/:id', asyncHandler(async (req, res) => {
  const db = getDb();
  const theme = mapTheme(db.prepare(`
    SELECT t.*, COUNT(ti.inspiration_id) AS member_count
    FROM themes t
    LEFT JOIN theme_inspirations ti ON ti.theme_id = t.id
    WHERE t.id = ?
    GROUP BY t.id
  `).get(req.params.id));
  if (!theme) return res.status(404).json({ error: '主题不存在' });

  const noteIds = db.prepare('SELECT inspiration_id FROM theme_inspirations WHERE theme_id = ? ORDER BY created_at DESC').all(req.params.id);
  const notes = noteIds.map(row => getNoteById(db, row.inspiration_id)).filter(Boolean);
  res.json({ ...theme, notes });
}));

themesRouter.put('/:id', asyncHandler(async (req, res) => {
  const db = getDb();
  const existing = db.prepare('SELECT * FROM themes WHERE id = ?').get(req.params.id);
  if (!existing) return res.status(404).json({ error: '主题不存在' });

  db.prepare(`
    UPDATE themes SET title = @title, description = @description, color = @color, notes = @notes, updated_at = @updatedAt
    WHERE id = @id
  `).run({
    id: req.params.id,
    title: req.body.title ?? existing.title,
    description: req.body.description ?? existing.description,
    color: req.body.color ?? existing.color,
    notes: req.body.notes ?? existing.notes,
    updatedAt: nowIso()
  });

  res.json(mapTheme(db.prepare('SELECT t.*, (SELECT COUNT(*) FROM theme_inspirations ti WHERE ti.theme_id = t.id) AS member_count FROM themes t WHERE t.id = ?').get(req.params.id)));
}));

themesRouter.delete('/:id', asyncHandler(async (req, res) => {
  const result = getDb().prepare('DELETE FROM themes WHERE id = ?').run(req.params.id);
  if (!result.changes) return res.status(404).json({ error: '主题不存在' });
  res.status(204).end();
}));

themesRouter.post('/:id/notes', asyncHandler(async (req, res) => {
  const db = getDb();
  const theme = db.prepare('SELECT id FROM themes WHERE id = ?').get(req.params.id);
  if (!theme) return res.status(404).json({ error: '主题不存在' });
  const noteIds = Array.isArray(req.body?.noteIds) ? req.body.noteIds : [req.body?.noteId].filter(Boolean);
  if (!noteIds.length) return res.status(400).json({ error: '请选择灵感' });

  const now = nowIso();
  if (req.body?.action === 'remove') {
    const stmt = db.prepare('DELETE FROM theme_inspirations WHERE theme_id = ? AND inspiration_id = ?');
    const tx = db.transaction(() => noteIds.forEach(noteId => stmt.run(req.params.id, noteId)));
    tx();
  } else {
    const stmt = db.prepare('INSERT OR IGNORE INTO theme_inspirations (theme_id, inspiration_id, created_at) VALUES (?, ?, ?)');
    const tx = db.transaction(() => noteIds.forEach(noteId => stmt.run(req.params.id, noteId, now)));
    tx();
  }
  db.prepare('UPDATE themes SET updated_at = ? WHERE id = ?').run(now, req.params.id);
  res.json({ updated: noteIds.length });
}));

themesRouter.post('/:id/suggest', asyncHandler(async (req, res) => {
  const db = getDb();
  const theme = db.prepare('SELECT * FROM themes WHERE id = ?').get(req.params.id);
  if (!theme) return res.status(404).json({ error: '主题不存在' });
  const keywords = `${theme.title} ${theme.description}`.split(/\s+/).filter(Boolean);
  const candidates = db.prepare(`
    SELECT i.* FROM inspirations i
    WHERE NOT EXISTS (SELECT 1 FROM theme_inspirations ti WHERE ti.theme_id = @themeId AND ti.inspiration_id = i.id)
    ORDER BY i.created_at DESC
    LIMIT 50
  `).all({ themeId: req.params.id });
  const suggestions = candidates
    .map(row => ({ row, score: scoreCandidate(row, keywords) }))
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 8)
    .map(item => ({ id: item.row.id, content: item.row.content, summary: item.row.summary, score: item.score }));
  res.json({ items: suggestions });
}));

function scoreCandidate(row, keywords) {
  const text = `${row.content || ''} ${row.summary || ''} ${row.tags || ''} ${row.keywords || ''}`.toLowerCase();
  return keywords.reduce((score, keyword) => score + (text.includes(keyword.toLowerCase()) ? 1 : 0), 0);
}
