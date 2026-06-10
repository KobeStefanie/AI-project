// time-planner v89
// 缓存策略（v2.13.2 修复 iOS 同步协议+离线）：
//   - app-core.js 移除 iOS 强制 HTTP，跟随页面协议（HTTPS→HTTPS 同步，避开 Mixed Content）
//   - install 阶段逐个缓存核心资源，单文件失败不影响整体
//   - 同源资源 → cache-first + stale-while-revalidate
//     · 命中缓存：立即返回 → 离开 LAN 也能秒开
//     · 后台静默拉新版本，下一次访问看到新内容
//   - 跨域（xlsx-js-style CDN）→ cache-first
//   - 导航请求离线兜底：缓存和网络都失败时返回缓存中的任意 HTML
//
// 版本更新：浏览器周期性比对 service-worker.js 自身，
// 配合 app.js 的 updatefound → SKIP_WAITING → controllerchange → reload 流。
const CACHE_NAME = 'time-planner-v89';
// 注意：中文路径用 encodeURI 处理，避免不同浏览器 URL 编码差异
// 导致 cache.match 命中失败（iOS Safari 与 Chrome 行为不同）
const HTML_FILE = './' + encodeURI('时间管理助手.html');
const ASSETS = [
  './',
  HTML_FILE,
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
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      const localAssets = ASSETS.filter(u => !u.startsWith('http'));
      return Promise.allSettled(
        localAssets.map(url =>
          // 用 fetch + cache.put 替代 cache.add，以便剥离限制性缓存头
          fetch(url, { cache: 'no-cache' }).then(resp => {
            if (resp && resp.status === 200) {
              return cache.put(url, sanitizeForCache(resp));
            }
            throw new Error('HTTP ' + resp.status);
          }).catch(err => {
            console.warn('[sw] install 缓存失败:', url, err.message);
          })
        )
      );
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
    return cache.match(request).then(cached => {
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

  // PWA 元数据：不走 SW，让 Safari 拿原始网络响应
  if (url.origin === location.origin) {
    if (url.pathname === '/manifest.json'
        || url.pathname === '/icon-192.png'
        || url.pathname === '/icon.svg') {
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
