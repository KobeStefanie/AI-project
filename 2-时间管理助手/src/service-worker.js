// time-planner v83
// 缓存策略（v2.10.2）：
//   - 同源 HTML / 同源静态资源 → cache-first + stale-while-revalidate
//     · 命中缓存：立即返回（0ms，不等网络）→ 离开 LAN 时点 PWA 图标也能秒开
//     · 后台静默拉新版本，下一次访问看到新内容
//   - 跨域（xlsx-js-style CDN）→ cache-first
//
// 版本更新依赖独立机制：浏览器会周期性抓 /service-worker.js 自身做 byte 比对，
// 配合 app.js 的 updatefound → SKIP_WAITING → controllerchange → reload 流，
// 修改源文件并刷一次即可看到新版，不影响离线场景。
const CACHE_NAME = 'time-planner-v85';
const ASSETS = [
  './',
  './\u65f6\u95f4\u7ba1\u7406\u52a9\u624b.html',
  './styles.css',
  './app-core.js',
  './app.js',
  './icon.svg',
  './icon-192.png',
  'https://cdn.jsdelivr.net/npm/xlsx-js-style@1.2.0/dist/xlsx.bundle.js'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS.filter(u => !u.startsWith('http')))));
  self.skipWaiting();
});

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

// cache-first + stale-while-revalidate
// 核心：命中缓存就立即返回（不等网络），后台异步拉新版写回缓存。
// 这是离线优先 PWA 的标准做法；让用户在 LAN 不可达时也能秒开应用。
function cacheFirstSWR(request) {
  return caches.open(CACHE_NAME).then(cache => {
    return cache.match(request).then(cached => {
      // 后台静默刷新（不阻塞当前请求）
      const networkPromise = fetch(request).then(resp => {
        if (resp && resp.status === 200 && resp.type !== 'opaque') {
          cache.put(request, resp.clone()).catch(() => {});
        }
        return resp;
      }).catch(err => {
        // 离线 / LAN 不可达：吞掉错误。若没缓存就交给外层 reject。
        if (cached) return cached;
        throw err;
      });
      // 优先命中缓存；缓存没有再等网络
      return cached || networkPromise;
    });
  });
}

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch (e) { return; }

  // PWA 元数据：让 Safari 装 PWA 时拿原始网络响应，避免 SW 缓存让 Safari 降级成书签。
  // 这些资源不经 SW，但浏览器/iOS 自身会缓存，离线时图标仍由 OS 缓存提供。
  if (url.origin === location.origin) {
    if (url.pathname === '/manifest.json'
        || url.pathname === '/icon-192.png'
        || url.pathname === '/icon.svg') {
      return; // 不调用 respondWith → 走默认网络 fetch
    }
  }

  // 同源一律走 cache-first SWR（HTML/JS/CSS/JSON/图片）
  // 跨域（CDN，URL 内容不变）也是 cache-first
  event.respondWith(cacheFirstSWR(req));
});

