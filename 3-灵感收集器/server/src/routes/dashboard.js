import { Router } from 'express';
import { asyncHandler } from '../middleware/error.js';
import { getDb, nowIso } from '../db/index.js';

export const dashboardRouter = Router();

dashboardRouter.get('/', asyncHandler(async (_req, res) => {
  const db = getDb();
  const now = nowIso();
  const today = now.slice(0, 10);
  const weekStart = isoWeekStart(now).slice(0, 10);
  const monthStart = now.slice(0, 7) + '-01';

  const todayCount = db.prepare(
    'SELECT COUNT(*) AS total FROM inspirations WHERE created_at >= @today'
  ).get({ today })?.total || 0;

  const inboxCount = db.prepare(
    "SELECT COUNT(*) AS total FROM inspirations WHERE status = 'raw'"
  ).get()?.total || 0;

  const weekCount = db.prepare(
    'SELECT COUNT(*) AS total FROM inspirations WHERE created_at >= @weekStart'
  ).get({ weekStart })?.total || 0;

  const monthExpanded = db.prepare(
    "SELECT COUNT(*) AS total FROM inspirations WHERE status = 'expanded' AND created_at >= @monthStart"
  ).get({ monthStart })?.total || 0;

  const mediaFailed = db.prepare(
    "SELECT COUNT(DISTINCT inspiration_id) AS total FROM media_assets WHERE upload_status = 'failed'"
  ).get()?.total || 0;

  const totalCount = db.prepare('SELECT COUNT(*) AS total FROM inspirations').get()?.total || 0;

  const recentCount = db.prepare(
    "SELECT COUNT(*) AS total FROM inspirations WHERE created_at >= datetime('now', '-2 hours')"
  ).get()?.total || 0;

  res.json({
    todayCount,
    inboxCount,
    weekCount,
    monthExpanded,
    mediaFailed,
    totalCount,
    recentCount
  });
}));

function isoWeekStart(dateStr) {
  const d = new Date(dateStr);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff);
  return d.toISOString();
}
