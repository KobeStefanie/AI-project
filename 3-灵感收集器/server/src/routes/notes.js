import { Router } from 'express';
import { nanoid } from 'nanoid';
import { asyncHandler } from '../middleware/error.js';
import { getDb, mapInspiration, mapMedia, nowIso, stringifyJson } from '../db/index.js';

export const notesRouter = Router();

const STATUS_VALUES = new Set(['raw', 'expanded', 'realized', 'archived', 'abandoned']);
const MOOD_VALUES = new Set(['excited', 'calm', 'low', 'confused', 'anxious', 'inspired', 'determined']);

notesRouter.get('/', asyncHandler(async (req, res) => {
  const db = getDb();
  const filters = [];
  const params = {};

  if (req.query.status) {
    filters.push('i.status = @status');
    params.status = req.query.status;
  }
  if (req.query.mood) {
    filters.push('i.mood = @mood');
    params.mood = req.query.mood;
  }
  if (req.query.from) {
    filters.push('i.created_at >= @from');
    params.from = req.query.from;
  }
  if (req.query.to) {
    filters.push('i.created_at <= @to');
    params.to = req.query.to;
  }
  if (req.query.source) {
    filters.push('i.source_types LIKE @source');
    params.source = `%"${req.query.source}"%`;
  }
  if (req.query.media) {
    filters.push(`EXISTS (SELECT 1 FROM media_assets ma WHERE ma.inspiration_id = i.id AND ma.type = @media)`);
    params.media = req.query.media;
  }
  if (req.query.theme) {
    filters.push(`EXISTS (SELECT 1 FROM theme_inspirations ti WHERE ti.inspiration_id = i.id AND ti.theme_id = @theme)`);
    params.theme = req.query.theme;
  }
  if (req.query.q) {
    filters.push(`(
      i.content LIKE @q OR i.summary LIKE @q OR i.transcript LIKE @q OR i.expanded LIKE @q OR
      i.tags LIKE @q OR i.keywords LIKE @q OR i.context LIKE @q OR
      EXISTS (
        SELECT 1 FROM theme_inspirations ti
        JOIN themes t ON t.id = ti.theme_id
        WHERE ti.inspiration_id = i.id AND t.title LIKE @q
      )
    )`);
    params.q = `%${req.query.q}%`;
  }

  const where = filters.length ? `WHERE ${filters.join(' AND ')}` : '';
  const rows = db.prepare(`
    SELECT i.*,
      COALESCE((SELECT json_group_array(json_object(
        'id', ma.id,
        'inspirationId', ma.inspiration_id,
        'type', ma.type,
        'originalName', ma.original_name,
        'filename', ma.filename,
        'mimeType', ma.mime_type,
        'size', ma.size,
        'duration', ma.duration,
        'width', ma.width,
        'height', ma.height,
        'url', ma.url,
        'uploadStatus', ma.upload_status,
        'createdAt', ma.created_at
      )) FROM media_assets ma WHERE ma.inspiration_id = i.id), '[]') AS media_assets,
      COALESCE((SELECT json_group_array(json_object(
        'id', t.id,
        'title', t.title,
        'color', t.color
      )) FROM theme_inspirations ti JOIN themes t ON t.id = ti.theme_id WHERE ti.inspiration_id = i.id), '[]') AS themes
    FROM inspirations i
    ${where}
    ORDER BY i.created_at DESC
    LIMIT @limit OFFSET @offset
  `).all({
    ...params,
    limit: Math.min(Number(req.query.limit || 100), 200),
    offset: Number(req.query.offset || 0)
  });

  res.json({ items: rows.map(mapInspiration) });
}));

notesRouter.post('/', asyncHandler(async (req, res) => {
  const db = getDb();
  const now = nowIso();
  const id = nanoid();
  const payload = normalizeInspirationPayload(req.body, { isCreate: true });

  db.prepare(`
    INSERT INTO inspirations (
      id, content, summary, transcript, transcript_quality, tags, keywords, mood, status, context,
      expanded, linked_ids, source_types, source_detail, sync_status, media_status, ai_status,
      ai_error, processed_at, device, created_at, updated_at
    ) VALUES (
      @id, @content, @summary, @transcript, @transcriptQuality, @tags, @keywords, @mood, @status, @context,
      @expanded, @linkedIds, @sourceTypes, @sourceDetail, @syncStatus, @mediaStatus, @aiStatus,
      @aiError, @processedAt, @device, @createdAt, @updatedAt
    )
  `).run({
    id,
    ...payload,
    createdAt: now,
    updatedAt: now
  });

  const note = getNoteById(db, id);
  res.status(201).json(note);
}));

notesRouter.get('/:id', asyncHandler(async (req, res) => {
  const note = getNoteById(getDb(), req.params.id);
  if (!note) return res.status(404).json({ error: '灵感不存在' });
  res.json(note);
}));

notesRouter.put('/:id', asyncHandler(async (req, res) => {
  const db = getDb();
  const existing = getNoteById(db, req.params.id);
  if (!existing) return res.status(404).json({ error: '灵感不存在' });

  const payload = normalizeInspirationPayload({ ...existing, ...req.body });
  const updatedAt = nowIso();

  db.prepare(`
    UPDATE inspirations SET
      content = @content,
      summary = @summary,
      transcript = @transcript,
      transcript_quality = @transcriptQuality,
      tags = @tags,
      keywords = @keywords,
      mood = @mood,
      status = @status,
      context = @context,
      expanded = @expanded,
      linked_ids = @linkedIds,
      source_types = @sourceTypes,
      source_detail = @sourceDetail,
      sync_status = @syncStatus,
      media_status = @mediaStatus,
      ai_status = @aiStatus,
      ai_error = @aiError,
      processed_at = @processedAt,
      device = @device,
      updated_at = @updatedAt
    WHERE id = @id
  `).run({ id: req.params.id, ...payload, updatedAt });

  res.json(getNoteById(db, req.params.id));
}));

notesRouter.delete('/:id', asyncHandler(async (req, res) => {
  const result = getDb().prepare('DELETE FROM inspirations WHERE id = ?').run(req.params.id);
  if (!result.changes) return res.status(404).json({ error: '灵感不存在' });
  res.status(204).end();
}));

notesRouter.post('/sync', asyncHandler(async (req, res) => {
  const notes = Array.isArray(req.body?.items) ? req.body.items : [];
  const created = [];
  const db = getDb();
  const insert = db.transaction((items) => {
    for (const item of items) {
      const now = nowIso();
      const id = item.id || nanoid();
      const payload = normalizeInspirationPayload(item, { isCreate: true });
      db.prepare(`
        INSERT OR IGNORE INTO inspirations (
          id, content, summary, transcript, transcript_quality, tags, keywords, mood, status, context,
          expanded, linked_ids, source_types, source_detail, sync_status, media_status, ai_status,
          ai_error, processed_at, device, created_at, updated_at
        ) VALUES (
          @id, @content, @summary, @transcript, @transcriptQuality, @tags, @keywords, @mood, @status, @context,
          @expanded, @linkedIds, @sourceTypes, @sourceDetail, 'synced', @mediaStatus, @aiStatus,
          @aiError, @processedAt, @device, @createdAt, @updatedAt
        )
      `).run({ id, ...payload, createdAt: item.createdAt || now, updatedAt: now });
      created.push(id);
    }
  });
  insert(notes);
  res.json({ synced: created.length, ids: created });
}));

notesRouter.post('/batch', asyncHandler(async (req, res) => {
  const { ids = [], action, status, themeId } = req.body || {};
  if (!Array.isArray(ids) || ids.length === 0) return res.status(400).json({ error: '请选择要批量处理的灵感' });

  const db = getDb();
  const now = nowIso();

  if (action === 'status') {
    if (!STATUS_VALUES.has(status)) return res.status(400).json({ error: '无效状态' });
    const stmt = db.prepare('UPDATE inspirations SET status = ?, updated_at = ? WHERE id = ?');
    const tx = db.transaction(() => ids.forEach(id => stmt.run(status, now, id)));
    tx();
    return res.json({ updated: ids.length });
  }

  if (action === 'theme') {
    const exists = db.prepare('SELECT id FROM themes WHERE id = ?').get(themeId);
    if (!exists) return res.status(404).json({ error: '主题不存在' });
    const stmt = db.prepare('INSERT OR IGNORE INTO theme_inspirations (theme_id, inspiration_id, created_at) VALUES (?, ?, ?)');
    const tx = db.transaction(() => ids.forEach(id => stmt.run(themeId, id, now)));
    tx();
    return res.json({ updated: ids.length });
  }

  res.status(400).json({ error: '不支持的批量操作' });
}));

notesRouter.post('/:id/link', asyncHandler(async (req, res) => {
  const db = getDb();
  const note = getNoteById(db, req.params.id);
  if (!note) return res.status(404).json({ error: '灵感不存在' });
  const linkedIds = new Set(note.linkedIds || []);
  const targetId = req.body?.targetId;
  if (!targetId) return res.status(400).json({ error: '缺少 targetId' });
  if (req.body?.action === 'remove') linkedIds.delete(targetId);
  else linkedIds.add(targetId);
  db.prepare('UPDATE inspirations SET linked_ids = ?, updated_at = ? WHERE id = ?').run(JSON.stringify([...linkedIds]), nowIso(), req.params.id);
  res.json(getNoteById(db, req.params.id));
}));

export function getNoteById(db, id) {
  const row = db.prepare(`
    SELECT i.*,
      COALESCE((SELECT json_group_array(json_object(
        'id', ma.id,
        'inspirationId', ma.inspiration_id,
        'type', ma.type,
        'originalName', ma.original_name,
        'filename', ma.filename,
        'mimeType', ma.mime_type,
        'size', ma.size,
        'duration', ma.duration,
        'width', ma.width,
        'height', ma.height,
        'url', ma.url,
        'uploadStatus', ma.upload_status,
        'createdAt', ma.created_at
      )) FROM media_assets ma WHERE ma.inspiration_id = i.id), '[]') AS media_assets,
      COALESCE((SELECT json_group_array(json_object(
        'id', t.id,
        'title', t.title,
        'color', t.color
      )) FROM theme_inspirations ti JOIN themes t ON t.id = ti.theme_id WHERE ti.inspiration_id = i.id), '[]') AS themes
    FROM inspirations i
    WHERE i.id = ?
  `).get(id);
  return mapInspiration(row);
}

function normalizeInspirationPayload(body = {}, options = {}) {
  const status = body.status || 'raw';
  if (!STATUS_VALUES.has(status)) {
    const error = new Error('无效状态');
    error.status = 400;
    throw error;
  }

  const mood = body.mood || null;
  if (mood && !MOOD_VALUES.has(mood)) {
    const error = new Error('无效心情');
    error.status = 400;
    throw error;
  }

  return {
    content: body.content || '',
    summary: body.summary || '',
    transcript: body.transcript || '',
    transcriptQuality: body.transcriptQuality || null,
    tags: stringifyJson(body.tags || []),
    keywords: stringifyJson(body.keywords || []),
    mood,
    status,
    context: body.context || '',
    expanded: body.expanded || '',
    linkedIds: stringifyJson(body.linkedIds || []),
    sourceTypes: stringifyJson(body.sourceTypes || inferSourceTypes(body)),
    sourceDetail: body.sourceDetail || null,
    syncStatus: body.syncStatus || 'synced',
    mediaStatus: body.mediaStatus || 'none',
    aiStatus: body.aiStatus || (options.isCreate ? 'pending' : 'pending'),
    aiError: body.aiError || null,
    processedAt: body.processedAt || null,
    device: body.device || 'windows'
  };
}

function inferSourceTypes(body) {
  const types = [];
  if (body.content) types.push('text');
  if (body.transcript) types.push('voice');
  return types.length ? types : ['text'];
}
