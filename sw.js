const CACHE_NAME = 'poker-excel-v1';

// Lista de todos os arquivos que o iPhone deve "baixar e guardar"
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  // As 21 tabelas da sua pasta 'Tabelas'
  './Tabelas/open_utg_100bb.png',
  './Tabelas/open_hj_100bb.png',
  './Tabelas/open_co_100bb.png',
  './Tabelas/open_btn_100bb.png',
  './Tabelas/open_sb_100bb.png',
  './Tabelas/bb_vs_utg_100bb.png',
  './Tabelas/bb_vs_hj_100bb.png',
  './Tabelas/bb_vs_co_100bb.png',
  './Tabelas/bb_vs_btn_100bb.png',
  './Tabelas/bb_vs_sb_100bb.png',
  './Tabelas/bb_vs_sb_call_100bb.png',
  './Tabelas/btn_vs_utg_100bb.png',
  './Tabelas/btn_vs_hj_100bb.png',
  './Tabelas/btn_vs_co_100bb.png',
  './Tabelas/co_vs_utg_100bb.png',
  './Tabelas/co_vs_hj_100bb.png',
  './Tabelas/hj_vs_utg_100bb.png',
  './Tabelas/sb_vs_utg_100bb.png',
  './Tabelas/sb_vs_hj_100bb.png',
  './Tabelas/sb_vs_co_100bb.png',
  './Tabelas/sb_vs_btn_100bb.png'
];

// Instalação: Salva tudo no cache do celular
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('Cacheando tabelas de poker...');
      return cache.addAll(ASSETS);
    })
  );
});

// Ativação: Limpa caches antigos se você atualizar o app
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
});

// Estratégia Cache First: Se tiver no celular, não usa internet
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      return cachedResponse || fetch(event.request);
    })
  );
});