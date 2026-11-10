// mdcms: PWA disabled — unregisters any previously installed service worker
// and drops the caches it left behind, so nothing keeps serving old content.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.filter(k => k.indexOf('mdcms-') === 0).map(k => caches.delete(k)));
      const clients = await self.clients.matchAll({ type: 'window' });
      await self.registration.unregister();
      clients.forEach(client => { try { client.navigate(client.url); } catch (e) {} });
    } catch (e) { await self.registration.unregister(); }
  })());
});
