const CACHE_PREFIX = 'jona-offline-';
const CACHE_NAME = `${CACHE_PREFIX}v2`;
const SCOPE_URL = new URL(self.registration.scope);

const CORE_PATHS = [
  './',
  './index.html',
  './offline.js',
  './home.css?v=20260723-3',
  './site-touchup.css?v=20260723-1',
  './site-touchup.css?v=20260723-2',
  './assets/site-bg-1600.webp',
  './assets/weather-bg-1600.webp',
  './favicon.svg?v=3',
  './favicon-32x32.png',
  './favicon-16x16.png',
  './apple-touch-icon.png',
  './android-chrome-192x192.png',
  './404.html',
  './movilidad/',
  './movilidad/index.html',
  './jona-movilidad-fondo-poster.webp',
  './docs/',
  './docs/index.html',
  './clima/',
  './clima/index.html',
  './data/weather.json',
  './supermercados/',
  './supermercados/index.html',
  './apps/',
  './apps/index.html',
  './discord/',
  './discord/index.html',
  './assets/avatars/01_maite_pineyrua_segura.webp',
  './assets/avatars/02_victoria_alexandre.webp',
  './assets/avatars/03_luthien_fernandez.webp',
  './assets/avatars/04_martin_fernandez.webp',
  './assets/avatars/05_malena_benavides.webp',
  './assets/avatars/06_guillermo_barbeito.webp',
  './assets/avatars/07_josefina_rabaiotti.webp',
  './assets/avatars/08_mateo_borges.webp',
  './assets/avatars/09_carolina_lopez.webp',
  './assets/avatars/10_pedro_piaggio.webp',
  './assets/avatars/11_lucca_chakiyian.webp',
  './assets/avatars/12_juan_pablo_bottino.webp',
  './assets/avatars/13_juan_andres_piojo.webp',
  './assets/avatars/14_rocio_espinosa.webp',
  './assets/avatars/15_belen.webp',
  './assets/avatars/16_carolina_romero.webp'
];

const CORE_URLS = CORE_PATHS.map(path => new URL(path, SCOPE_URL).href);
const WEATHER_URL = new URL('./data/weather.json', SCOPE_URL).href;
const HOME_URL = new URL('./', SCOPE_URL).href;

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await Promise.allSettled(CORE_URLS.map(async url => {
      const request = new Request(url, { cache: 'reload' });
      const response = await fetch(request);
      if (response.ok) await cache.put(request, response);
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names
      .filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
      .map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

function cleanRequest(request) {
  const url = new URL(request.url);
  url.search = '';
  return new Request(url.href, { credentials: 'same-origin' });
}

async function networkFirstNavigation(request) {
  const cache = await caches.open(CACHE_NAME);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 4500);

  try {
    const response = await fetch(request, { signal: controller.signal });
    clearTimeout(timeout);
    if (response.ok) await cache.put(cleanRequest(request), response.clone());
    return response;
  } catch (error) {
    clearTimeout(timeout);
    const url = new URL(request.url);
    let cached = await cache.match(cleanRequest(request), { ignoreSearch: true });
    if (!cached && url.pathname.endsWith('/')) {
      cached = await cache.match(new URL('index.html', url).href, { ignoreSearch: true });
    }
    if (cached) return cached;
    const home = await cache.match(HOME_URL, { ignoreSearch: true });
    return home || Response.error();
  }
}

async function weatherNetworkFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const key = new Request(WEATHER_URL);
  try {
    const response = await fetch(request);
    if (response.ok) await cache.put(key, response.clone());
    return response;
  } catch (error) {
    return (await cache.match(key)) || Response.error();
  }
}

async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request, { ignoreSearch: true });
  if (cached) {
    fetch(request).then(response => {
      if (response.ok) cache.put(cleanRequest(request), response.clone());
    }).catch(() => {});
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok) await cache.put(cleanRequest(request), response.clone());
    return response;
  } catch (error) {
    return Response.error();
  }
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== SCOPE_URL.origin || !url.pathname.startsWith(SCOPE_URL.pathname)) return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(request));
    return;
  }

  if (url.pathname.endsWith('/data/weather.json')) {
    event.respondWith(weatherNetworkFirst(request));
    return;
  }

  if (/\.(?:mp4|webm|zip)$/i.test(url.pathname)) return;

  if (/\.(?:css|js|png|jpe?g|webp|svg|ico|woff2?)$/i.test(url.pathname)) {
    event.respondWith(cacheFirst(request));
  }
});
