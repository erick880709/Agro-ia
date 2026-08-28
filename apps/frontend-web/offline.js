/* AgroIA — capa offline-first (PWA).
 * Cola IndexedDB de datos pendientes (tramas de sensores y labores) con
 * sincronización idempotente contra /api/v1/sync/*.
 */
'use strict';

const OFFLINE_DB = 'agroia-offline';
const OFFLINE_STORE = 'pendientes';
const OFFLINE_BANNER_ID = 'offline-banner';

function _abrirDB() {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) { reject(new Error('sin IndexedDB')); return; }
    const req = indexedDB.open(OFFLINE_DB, 1);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(OFFLINE_STORE)) {
        req.result.createObjectStore(OFFLINE_STORE, { keyPath: 'id' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function _pendientes() {
  const db = await _abrirDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(OFFLINE_STORE, 'readonly');
    const req = tx.objectStore(OFFLINE_STORE).getAll();
    req.onsuccess = () => { db.close(); resolve(req.result || []); };
    req.onerror = () => { db.close(); reject(req.error); };
  });
}

async function encolarOffline(tipo, payload) {
  // tipo: 'sensor' (trama completa) | 'labor' ({labor_id, estado, ...})
  try {
    const db = await _abrirDB();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(OFFLINE_STORE, 'readwrite');
      tx.objectStore(OFFLINE_STORE).add({
        id: (crypto.randomUUID ? crypto.randomUUID() : 'k-' + Date.now() + '-' + Math.random().toString(16).slice(2)),
        tipo,
        payload,
        creado: new Date().toISOString(),
      });
      tx.oncomplete = () => { db.close(); resolve(); };
      tx.onerror = () => { db.close(); reject(tx.error); };
    });
    await actualizarBannerOffline();
  } catch (e) {
    console.warn('offline: no se pudo encolar', e);
  }
}

async function actualizarBannerOffline() {
  const banner = document.getElementById(OFFLINE_BANNER_ID);
  if (!banner) return;
  try {
    const pend = await _pendientes();
    banner.style.display = pend.length ? '' : 'none';
    banner.innerHTML = `📡 <b>${pend.length}</b> registro(s) pendientes de sincronizar — ` +
      (navigator.onLine ? 'sincronizando…' : 'sin conexión; se enviarán al recuperar señal.');
  } catch {
    banner.style.display = 'none';
  }
}

async function sincronizarPendientes() {
  if (!navigator.onLine) return;
  const pend = await _pendientes();
  if (!pend.length) { await actualizarBannerOffline(); return; }
  const sensores = pend.filter(p => p.tipo === 'sensor');
  const labores = pend.filter(p => p.tipo === 'labor');
  const enviados = new Set();
  try {
    if (sensores.length) {
      const r = await api('/sync/sensor-readings', {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ items: sensores.map(p => ({ idempotency_key: p.id, trama: p.payload })) }),
      });
      sensores.forEach((p, i) => { if (!(r.errores || []).some(e => e.idempotency_key === p.id)) enviados.add(p.id); });
    }
    if (labores.length) {
      const r = await api('/sync/labores', {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ items: labores.map(p => ({ idempotency_key: p.id, ...p.payload })) }),
      });
      labores.forEach((p, i) => { if (!(r.errores || []).some(e => e.idempotency_key === p.id)) enviados.add(p.id); });
    }
  } catch (e) {
    console.warn('offline: sync falló', e.message);
  }
  if (enviados.size) {
    const db = await _abrirDB();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(OFFLINE_STORE, 'readwrite');
      enviados.forEach(id => tx.objectStore(OFFLINE_STORE).delete(id));
      tx.oncomplete = () => { db.close(); resolve(); };
      tx.onerror = () => { db.close(); reject(tx.error); };
    });
  }
  await actualizarBannerOffline();
}

function iniciarOffline() {
  if (!window.indexedDB) return;
  if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
    navigator.serviceWorker.register('/sw.js').catch(e => console.warn('sw: no registrado', e));
  }
  window.addEventListener('online', () => sincronizarPendientes().then(() => {
    if (typeof cargarDashboard === 'function') cargarDashboard();
  }));
  setInterval(() => { if (navigator.onLine) sincronizarPendientes(); }, 30000);
  actualizarBannerOffline();
}
