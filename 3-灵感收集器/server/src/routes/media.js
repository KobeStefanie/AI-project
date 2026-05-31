import { Router } from 'express';
import { nanoid } from 'nanoid';
import { asyncHandler } from '../middleware/error.js';
import { getDb, mapMedia, nowIso } from '../db/index.js';
import { getNoteById } from './notes.js';
import { removeFileByUrl, toPublicUrl, upload, validateUploadedMedia } from '../services/media.js';

export const mediaRouter = Router();

mediaRouter.post('/notes/:inspirationId/media', upload.array('files', 12), asyncHandler(async (req, res) => {
  const db = getDb();
  const note = getNoteById(db, req.params.inspirationId);
  if (!note) return res.status(404).json({ error: '灵感不存在' });

  const counts = countMediaTypes(db, req.params.inspirationId);
  const created = [];
  const now = nowIso();

  const tx = db.transaction((files) => {
    for (const file of files) {
      const type = validateUploadedMedia(file, counts);
      counts[type] = (counts[type] || 0) + 1;
      const asset = {
        id: nanoid(),
        inspirationId: req.params.inspirationId,
        type,
        originalName: file.originalname,
        filename: file.filename,
        mimeType: file.mimetype,
        size: file.size,
        duration: Number(req.body?.duration || 0) || null,
        width: Number(req.body?.width || 0) || null,
        height: Number(req.body?.height || 0) || null,
        url: toPublicUrl(file.path, type),
        uploadStatus: 'uploaded',
        createdAt: now
      };
      db.prepare(`
        INSERT INTO media_assets (
          id, inspiration_id, type, original_name, filename, mime_type, size, duration, width, height, url, upload_status, created_at
        ) VALUES (
          @id, @inspirationId, @type, @originalName, @filename, @mimeType, @size, @duration, @width, @height, @url, @uploadStatus, @createdAt
        )
      `).run(asset);
      created.push(asset);
    }
    db.prepare('UPDATE inspirations SET media_status = ?, updated_at = ? WHERE id = ?').run('uploaded', now, req.params.inspirationId);
  });

  tx(req.files || []);
  res.status(201).json({ items: created });
}));

mediaRouter.get('/notes/:inspirationId/media', asyncHandler(async (req, res) => {
  const rows = getDb().prepare('SELECT * FROM media_assets WHERE inspiration_id = ? ORDER BY created_at ASC').all(req.params.inspirationId);
  res.json({ items: rows.map(mapMedia) });
}));

mediaRouter.delete('/asset/:assetId', asyncHandler(async (req, res) => {
  const db = getDb();
  const row = db.prepare('SELECT * FROM media_assets WHERE id = ?').get(req.params.assetId);
  if (!row) return res.status(404).json({ error: '媒体不存在' });
  db.prepare('DELETE FROM media_assets WHERE id = ?').run(req.params.assetId);
  removeFileByUrl(row.url);
  const remaining = db.prepare('SELECT COUNT(*) AS total FROM media_assets WHERE inspiration_id = ?').get(row.inspiration_id).total;
  db.prepare('UPDATE inspirations SET media_status = ?, updated_at = ? WHERE id = ?').run(remaining ? 'uploaded' : 'none', nowIso(), row.inspiration_id);
  res.status(204).end();
}));

function countMediaTypes(db, inspirationId) {
  const rows = db.prepare('SELECT type, COUNT(*) AS total FROM media_assets WHERE inspiration_id = ? GROUP BY type').all(inspirationId);
  return rows.reduce((acc, row) => {
    acc[row.type] = row.total;
    return acc;
  }, { audio: 0, image: 0, video: 0 });
}
