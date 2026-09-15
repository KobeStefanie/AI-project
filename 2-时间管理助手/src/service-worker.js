// time-planner v98
// 缓存策略（v2.13.3 修复离线功能）：
//   - 移除复盘中心文件缓存（桌面专用，不需离线）
//   - SW fetch 事件跳过 review-center/engine/ui 请求
//   - install 阶段逐个缓存核心资源，单文件失败不影响整体
//   - 同源资源 → cache-first + stale-while-revalidate
//     · 命中缓存：立即返回 → 离开 LAN 也能秒开
//     · 后台静默拉新版本，下一次访问看到新内容
//   - 跨域（xlsx-js-style CDN）→ cache-first
//   - 导航请求离线兜底：缓存和网络都失败时返回缓存中的任意 HTML
//
// 版本更新：浏览器周期性比对 service-worker.js 自身，
// 配合 app.js 的 updatefound → SKIP_WAITING → controllerchange → reload 流。
const CACHE_NAME = 'time-planner-v98';
// 注意：中文路径用 encodeURI 处理，避免不同浏览器 URL 编码差异
// 导致 cache.match 命中失败（iOS Safari 与 Chrome 行为不同）
const HTML_FILE = './' + encodeURI('时间管理助手.html');
const ASSETS = [
  './',
  HTML_FILE,
  './manifest.json',
  './styles.css',
  './app-core.js',
  './app.js',
  './qrcode-generator.js',
  './icon.svg',
  './icon-192.png'
];

// -------- 工具：剥离限制性缓存头，确保 Cache API 接受存储 --------
// iOS Safari 的 Cache API 严格遵循规范：遇到 Cache-Control: no-store
// 会拒绝 cache.put()。v88 起，服务器已改为 public,max-age=0，
// 此处额外剥离 no-store/no-cache/private 以防万一。
function sanitizeForCache(response) {
  const headers = new Headers(response.headers);
  const cc = headers.get('Cache-Control');
  if (cc) {
    const cleaned = cc
      .split(',')
      .map(s => s.trim())
      .filter(s => s && !s.startsWith('no-store') && !s.startsWith('no-cache') && !s.startsWith('private'))
      .join(', ');
    if (cleaned) {
      headers.set('Cache-Control', cleaned);
    } else {
      headers.delete('Cache-Control');
    }
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: headers
  });
}

// -------- install：逐个缓存，单文件失败不致命 --------
self.addEventListener('install', event => {
  console.log('[sw] install v98 开始，准备缓存', ASSETS.length, '个文件');
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      const localAssets = ASSETS.filter(u => !u.startsWith('http'));
      console.log('[sw] 需要缓存的本地文件:', localAssets);
      return Promise.allSettled(
        localAssets.map(url =>
          // 用 fetch + cache.put 替代 cache.add，以便剥离限制性缓存头
          fetch(url, { cache: 'no-cache' }).then(resp => {
            console.log('[sw] fetch 成功:', url, 'status:', resp.status);
            if (resp && resp.status === 200) {
              return cache.put(url, sanitizeForCache(resp)).then(() => {
                console.log('[sw] 缓存成功:', url);
              });
            }
            throw new Error('HTTP ' + resp.status);
          }).catch(err => {
            console.error('[sw] install 缓存失败:', url, err.message);
          })
        )
      ).then(results => {
        const failed = results.filter(r => r.status === 'rejected');
        if (failed.length > 0) {
          console.warn('[sw] install 完成，但有', failed.length, '个文件缓存失败');
        } else {
          console.log('[sw] install 完成，所有文件缓存成功');
        }
      });
    })
  );
  self.skipWaiting();
});

// -------- activate：清旧缓存 + 立即接管 --------
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

// -------- cache-first + stale-while-revalidate --------
function cacheFirstSWR(request) {
  return caches.open(CACHE_NAME).then(cache => {
    // ignoreSearch: true 让 /?iphone 也能匹配到缓存的 /
    return cache.match(request, { ignoreSearch: true }).then(cached => {
      // 后台静默刷新（不阻塞当前请求）
      const networkPromise = fetch(request).then(resp => {
        if (resp && resp.status === 200 && resp.type !== 'opaque') {
          cache.put(request, sanitizeForCache(resp)).catch(() => {});
        }
        return resp;
      }).catch(err => {
        if (cached) return cached;
        throw err;
      });
      // 优先命中缓存；缓存没有再等网络
      return cached || networkPromise;
    });
  });
}

// -------- fetch 事件 --------
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch (e) { return; }

  // 复盘中心：完全不走 SW（桌面专用，不需要离线）
  if (url.origin === location.origin) {
    if (url.pathname.includes('review-center')
        || url.pathname.includes('review-engine')
        || url.pathname.includes('review-ui')) {
      return;
    }
  }

  // HTML 导航请求：cache-first，并做多 URL 匹配（中文/编码变体兼容）
  if (req.mode === 'navigate') {
    event.respondWith(cacheFirstSWR(req).catch(() => {
      // 精确 URL 没命中 → 尝试缓存中任意 HTML（离线兜底）
      return caches.open(CACHE_NAME).then(cache =>
        cache.keys().then(keys => {
          for (const k of keys) {
            const kurl = new URL(k.url);
            if (kurl.pathname === '/' || kurl.pathname.endsWith('.html')) {
              return cache.match(k);
            }
          }
          throw new Error('no offline page');
        })
      );
    }));
    return;
  }

  // 同源 / 跨域静态资源 → cache-first SWR
  event.respondWith(cacheFirstSWR(req));
});
