import { getDb } from './sqlite.js';

export { getDb };

export function nowIso() {
  return new Date().toISOString();
}

export function parseJson(value, fallback = []) {
  if (value == null || value === '') return fallback;
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

export function stringifyJson(value, fallback = []) {
  return JSON.stringify(Array.isArray(value) ? value : fallback);
}

export function mapInspiration(row) {
  if (!row) return null;
  return {
    id: row.id,
    content: row.content || '',
    summary: row.summary || '',
    transcript: row.transcript || '',
    transcriptQuality: row.transcript_quality,
    tags: parseJson(row.tags),
    keywords: parseJson(row.keywords),
    mood: row.mood,
    status: row.status,
    context: row.context || '',
    expanded: row.expanded || '',
    linkedIds: parseJson(row.linked_ids),
    sourceTypes: parseJson(row.source_types),
    sourceDetail: row.source_detail,
    syncStatus: row.sync_status,
    mediaStatus: row.media_status,
    aiStatus: row.ai_status,
    aiError: row.ai_error,
    processedAt: row.processed_at,
    device: row.device,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
    mediaAssets: row.media_assets ? parseJson(row.media_assets) : [],
    themes: row.themes ? parseJson(row.themes) : []
  };
}

export function mapTheme(row) {
  if (!row) return null;
  return {
    id: row.id,
    title: row.title,
    description: row.description || '',
    color: row.color,
    notes: row.notes || '',
    memberCount: row.member_count ?? 0,
    createdAt: row.created_at,
    updatedAt: row.updated_at
  };
}

export function mapMedia(row) {
  if (!row) return null;
  return {
    id: row.id,
    inspirationId: row.inspiration_id,
    type: row.type,
    originalName: row.original_name,
    filename: row.filename,
    mimeType: row.mime_type,
    size: row.size,
    duration: row.duration,
    width: row.width,
    height: row.height,
    url: row.url,
    uploadStatus: row.upload_status,
    createdAt: row.created_at
  };
}
