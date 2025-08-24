self.addEventListener('install', function(e) {
  e.waitUntil(
    caches.open('rikshaw-app').then(function(cache) {
      return cache.addAll([
        './',
        './index.html',
        './script.js',
        './style.css',
        './manifest.json'
      ]);
    })
  );
});

self.addEventListener('fetch', function(e) {
  e.respondWith(
    caches.match(e.request).then(function(response) {
      return response || fetch(e.request);
    })
  );
});
