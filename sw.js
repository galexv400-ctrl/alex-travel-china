// Offline support for the trip site.
//
// The markdown files are fetched NETWORK-FIRST: when online you always get the
// latest version, and the copy is saved; when offline (China, planes, no
// signal) the last saved copy is shown. Everything is pre-saved on install, so
// opening the app once while online makes every tab available offline.

const CACHE = 'trip-2026-v111';

const MD = [
  'travel/china-2026/full-trip-plan.md',
  'travel/china-2026/hong-kong-itinerary.md',
  'travel/china-2026/bangkok-itinerary.md',
  'travel/china-2026/outfit-plan.md',
  'travel/china-2026/packing-list.md',
  'travel/china-2026/medication-guide.md',
  'travel/china-2026/intrepid-trip-notes.md',
];

const SHELL = ['./', 'index.html', 'manifest.json', 'lib/marked.min.js', 'icon-192.png', 'icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll([...SHELL, ...MD])).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;

  const isContent = url.pathname.endsWith('.md') || url.pathname.endsWith('/') || url.pathname.endsWith('index.html');

  if (isContent) {
    // Network first, fall back to the saved copy.
    e.respondWith(
      fetch(e.request, { cache: 'no-store' })
        .then(res => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(e.request, copy));
          }
          return res;
        })
        .catch(() => caches.match(e.request).then(r => r || caches.match('index.html')))
    );
  } else {
    // Static assets: saved copy first.
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});
