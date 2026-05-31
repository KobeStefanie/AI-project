import { Router } from 'express';
import { asyncHandler } from '../middleware/error.js';
import { getDb, mapInspiration, nowIso, stringifyJson } from '../db/index.js';
import { getNoteById } from './notes.js';
import { analyzeInspiration } from '../services/ai.js';

export const analyzeRouter = Router();

analyzeRouter.post('/notes/:id/analyze', asyncHandler(async (req, res) => {
  const db = getDb();
  const note = getNoteById(db, req.params.id);
  if (!note) return res.status(404).json({ error: '灵感不存在' });

  db.prepare('UPDATE inspirations SET ai_status = ?, updated_at = ? WHERE id = ?')
    .run('processing', nowIso(), req.params.id);

  // Fire and forget - but wait for result in v1
  try {
    const result = await analyzeInspiration(note);
    db.prepare(`
      UPDATE inspirations SET
        summary = @summary,
        tags = @tags,
        keywords = @keywords,
        mood = @mood,
        expanded = @expanded,
        ai_status = 'done',
        ai_error = NULL,
        processed_at = @processedAt,
        updated_at = @updatedAt
      WHERE id = @id
    `).run({
      id: req.params.id,
      summary: result.summary || note.summary,
      tags: stringifyJson(result.tags || []),
      keywords: stringifyJson(result.keywords || []),
      mood: result.mood || note.mood,
      expanded: result.expanded || note.expanded,
      processedAt: nowIso(),
      updatedAt: nowIso()
    });
    res.json(getNoteById(db, req.params.id));
  } catch (err) {
    db.prepare('UPDATE inspirations SET ai_status = ?, ai_error = ?, updated_at = ? WHERE id = ?')
      .run('failed', err.message, nowIso(), req.params.id);
    res.status(500).json({ error: 'AI 分析失败', detail: err.message });
  }
}));

analyzeRouter.post('/notes/analyze-batch', asyncHandler(async (req, res) => {
  const db = getDb();
  const { ids } = req.body || {};
  if (!Array.isArray(ids) || ids.length === 0) {
    return res.status(400).json({ error: '请提供灵感 ID 列表' });
  }

  const results = [];
  for (const id of ids) {
    const note = getNoteById(db, id);
    if (!note) {
      results.push({ id, status: 'not_found' });
      continue;
    }
    db.prepare('UPDATE inspirations SET ai_status = ?, updated_at = ? WHERE id = ?')
      .run('processing', nowIso(), id);

    try {
      const result = await analyzeInspiration(note);
      db.prepare(`
        UPDATE inspirations SET
          summary = @summary, tags = @tags, keywords = @keywords,
          mood = @mood, expanded = @expanded,
          ai_status = 'done', ai_error = NULL,
          processed_at = @processedAt, updated_at = @updatedAt
        WHERE id = @id
      `).run({
        id,
        summary: result.summary || note.summary,
        tags: stringifyJson(result.tags || []),
        keywords: stringifyJson(result.keywords || []),
        mood: result.mood || note.mood,
        expanded: result.expanded || note.expanded,
        processedAt: nowIso(),
        updatedAt: nowIso()
      });
      results.push({ id, status: 'done' });
    } catch (err) {
      db.prepare('UPDATE inspirations SET ai_status = ?, ai_error = ?, updated_at = ? WHERE id = ?')
        .run('failed', err.message, nowIso(), id);
      results.push({ id, status: 'failed', error: err.message });
    }
  }

  res.json({ results });
}));
