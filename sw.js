const CACHE='ps5-radar-shell-v1';
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['./','./index.html','./icon.svg'])));self.skipWaiting()});
self.addEventListener('activate',e=>{e.waitUntil(self.clients.claim())});
self.addEventListener('fetch',e=>{const url=new URL(e.request.url);if(url.pathname.endsWith('/data.json'))return; if(e.request.method==='GET'&&url.origin===self.location.origin)e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))});
