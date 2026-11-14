// ffp: TX-SW frontend javascript
// TianxiaOS & Rasa-X-Machina Sovereign Polyglot PWA - Offline Service Worker

const CACHE_NAME = 'tianxiaos-v8.7.1-blaw-v5.0';
const STATIC_ASSETS = [
  '/',
  '/about',
  '/collins',
  '/privacy',
  '/terms',
  '/cockpit',
  '/tx_web_standards.js',
  '/brandkit.css',
  '/manifest.json',
  '/icon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[Tianxia SW] Pre-caching asset warning:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Network-only for API, checkout redirects, streams, and non-GET requests
  if (
    url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/stream') ||
    event.request.method !== 'GET'
  ) {
    return;
  }

  // Network-first with cache fallback for HTML & JS so updates appear immediately while staying offline-resilient
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && url.origin === self.location.origin) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(() => caches.match(event.request))
  );
});

self.addEventListener('push', (event) => {
  let data = { title: 'TianxiaOS Sovereign Notification', body: 'Mesh event logged.' };
  try {
    if (event.data) {
      data = event.data.json();
    }
  } catch (_) {
    if (event.data) data.body = event.data.text();
  }

  const options = {
    body: data.body,
    icon: '/icon.svg',
    badge: '/icon.svg',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    }
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});
