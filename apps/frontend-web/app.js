/* AgroIA — Frontend integrado (SPA vanilla).
 * Consume la API del backend en el mismo origen.
 */
'use strict';

const API = '/api/v1';
const SESION_KEY = 'agroia_sesion';

const TABS_POR_ROL = {
  admin: ['inicio', 'sensores', 'carga', 'recomendaciones', 'historial', 'reportes', 'fincas', 'usuarios', 'catalogo'],
  agronomo: ['inicio', 'sensores', 'carga', 'recomendaciones', 'historial', 'reportes', 'catalogo'],
  cliente: ['inicio', 'sensores', 'historial', 'reportes', 'catalogo'],
};

const state = {
  fincas: [],
  cultivos: [],
  dispositivos: [],
  fincaId: null,
  catalogo: [],
  usuarios: [],
  sesion: JSON.parse(localStorage.getItem(SESION_KEY) || 'null'),
  rol: '',
  email: '',
  nombre: '',
  tabActual: 'inicio',
  cargandoSensores: false,
};

if (state.sesion) {
  state.rol = state.sesion.rol || '';
  state.email = state.sesion.email || '';
  state.nombre = state.sesion.nombre || '';
}

function headers(json = true) {
  const h = { 'X-User-Role': state.rol };
  if (state.rol.toLowerCase() === 'cliente' && state.email) {
    h['X-User-Email'] = state.email;
  }
  if (json) h['Content-Type'] = 'application/json';
  return h;
}

/* ─────────────────────────── utilidades ─────────────────────────── */

async function api(path, opts = {}) {
  const h = { ...(opts.headers || {}), 'X-User-Role': state.rol };
  if (state.rol.toLowerCase() === 'cliente' && state.email) {
    h['X-User-Email'] = state.email;
  }
  const res = await fetch(API + path, { ...opts, headers: h });
  let body = null;
  try { body = await res.json(); } catch { /* sin cuerpo */ }
  if (!res.ok) {
    const detail = body && body.detail;
    const msg = (detail && (detail.message || JSON.stringify(detail))) || `HTTP ${res.status}`;
    const err = new Error(msg);
    err.detail = detail || null;
    throw err;
  }
  return body;
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function fmtNum(v, dec = 2) {
  if (v == null) return '—';
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(dec).replace(/\.?0+$/, '') : '—';
}

function badgeClase(clasificacion) {
  const c = String(clasificacion || '').toLowerCase();
  if (c.includes('no apta') || c === 'noapta') return 'critical';
  if (c.includes('apta') || c === 'alta') return 'ok';
  if (c.includes('moderada') || c.includes('marginal') || c === 'media' || c === 'baja') return 'warning';
  return '';
}

function badgeEstadoClase(estado) {
  const e = String(estado || '').toUpperCase();
  if (e === 'EXCESO' || e === 'CRITICA') return 'critical';
  if (e === 'DEFICIT' || e === 'ALTA' || e === 'ADVERTENCIA' || e === 'MEDIA') return 'warning';
  return 'ok';
}

function badge(texto, clase) {
  return `<span class="badge ${clase}">${esc(texto)}</span>`;
}

function errorBanner(msg) {
  return `<div class="error-banner">⚠️ ${esc(msg)}</div>`;
}

function okBanner(msg) {
  // El mensaje se inserta como HTML: los valores dinámicos DEBEN llegar
  // ya escapados con esc() desde el llamador (patrón usado en todos).
  return `<div class="ok-banner">✅ ${msg}</div>`;
}

/* ─────────────────────────── sesión y autenticación ─────────────────────────── */

function aplicarSesion(data) {
  state.sesion = data;
  state.rol = data.rol;
  state.email = data.email;
  state.nombre = data.nombre;
  localStorage.setItem(SESION_KEY, JSON.stringify(data));
  const info = document.getElementById('user-info');
  if (info) info.textContent = `👤 ${data.nombre} · ${data.rol}`;
  document.getElementById('login-screen').classList.add('oculto');
}

function cerrarSesion() {
  localStorage.removeItem(SESION_KEY);
  location.reload();
}

async function manejarLogin(e) {
  e.preventDefault();
  const msg = document.getElementById('login-msg');
  const btn = document.getElementById('login-btn');
  msg.innerHTML = '';
  btn.disabled = true;
  btn.textContent = '⏳ Verificando…';
  try {
    const data = await api('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: document.getElementById('l-email').value.trim(),
        password: document.getElementById('l-password').value,
      }),
    });
    await iniciarApp(data);
  } catch (err) {
    msg.innerHTML = errorBanner(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Entrar';
  }
}

async function loginDemo(datos) {
  const msg = document.getElementById('login-msg');
  msg.innerHTML = '';
  try {
    const data = await api('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: datos.email, password: datos.pass }),
    });
    await iniciarApp(data);
  } catch (err) {
    msg.innerHTML = errorBanner(err.message);
  }
}

async function iniciarApp(data) {
  aplicarSesion(data);
  await arrancarAplicacion();
}

/* ─────────────────────────── navegación ─────────────────────────── */

function goTab(name) {
  const rol = state.rol.toLowerCase();
  state.tabActual = name;
  if (name === 'fincas' && rol !== 'admin') {
    renderAccesoRestringido();
  }
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === `view-${name}`));
  if (name === 'historial') cargarHistorial();
  if (name === 'sensores') cargarSensores();
  if (name === 'inicio') cargarDashboard();
  if (name === 'fincas' && state.rol.toLowerCase() === 'admin') renderFincasList();
  if (name === 'usuarios' && state.rol.toLowerCase() === 'admin') cargarUsuarios();
}

/* ─────────────────────────── carga inicial ─────────────────────────── */

async function init() {
  // ── Autenticación ──
  const loginScreen = document.getElementById('login-screen');
  document.getElementById('form-login').addEventListener('submit', manejarLogin);
  document.getElementById('logout-btn').addEventListener('click', cerrarSesion);
  document.querySelectorAll('.demo-login').forEach(btn => {
    btn.addEventListener('click', () => loginDemo({ email: btn.dataset.email, pass: btn.dataset.pass }));
  });

  if (!state.sesion) {
    loginScreen.classList.remove('oculto');
    return;
  }
  aplicarSesion(state.sesion);
  await arrancarAplicacion();
}

async function arrancarAplicacion() {
  document.querySelectorAll('.tab').forEach(t =>
    t.addEventListener('click', () => goTab(t.dataset.tab)));

  aplicarRol();

  // ── Combos ubicación ──
  const depSel = document.getElementById('f-departamento');
  depSel.innerHTML = '<option value="">— Seleccione —</option>' +
    Object.keys(DEPARTAMENTOS).sort().map(d => `<option value="${esc(d)}">${esc(d)}</option>`).join('');
  depSel.addEventListener('change', poblarMunicipios);
  const munSel = document.getElementById('f-municipio');
  munSel.addEventListener('change', () => {
    document.getElementById('f-municipio-otro-wrap').style.display =
      munSel.value === '__otro' ? 'flex' : 'none';
  });

  // ── Multi-select de fincas (usuarios) ──
  const trigger = document.getElementById('u-fincas-trigger');
  const panel = document.getElementById('u-fincas-panel');
  trigger.addEventListener('click', e => { e.stopPropagation(); panel.classList.toggle('open'); });
  panel.addEventListener('click', e => e.stopPropagation());
  document.addEventListener('click', () => panel.classList.remove('open'));

  document.getElementById('finca-select').addEventListener('change', e => {
    state.fincaId = e.target.value || null;
    cargarDashboard();
  });
  document.getElementById('reco-finca').addEventListener('change', e => {
    document.getElementById('finca-select').value = e.target.value;
    state.fincaId = e.target.value || null;
  });
  document.getElementById('form-analyze').addEventListener('submit', enviarAnalisis);
  document.getElementById('form-carga').addEventListener('submit', enviarCarga);
  document.getElementById('form-finca').addEventListener('submit', enviarFinca);
  // ── Wizard de finca (3 secciones) — defensivo: si el HTML es viejo
  //    (caché), no debe romper el resto del arranque. ──
  const _el = id => document.getElementById(id);
  if (_el('wstep-1') && _el('wstep-2') && _el('wstep-3')) {
    document.querySelectorAll('.wizard-steps .wstep').forEach(b =>
      b.addEventListener('click', () => irWStep(Number(b.dataset.step))));
    document.querySelectorAll('[data-next]').forEach(b =>
      b.addEventListener('click', () => irWStep(Number(b.dataset.next))));
    if (_el('f-ubic-gps')) _el('f-ubic-gps').addEventListener('click', usarMiUbicacion);
    if (_el('f-ubic-mapa')) _el('f-ubic-mapa').addEventListener('click', abrirMapa);
    if (_el('f-ubic-enlace')) _el('f-ubic-enlace').addEventListener('click', () => {
      _el('f-enlace-wrap').style.display = '';
    });
    if (_el('f-enlace-aplicar')) _el('f-enlace-aplicar').addEventListener('click', aplicarEnlace);
    if (_el('f-mapa-cerrar')) _el('f-mapa-cerrar').addEventListener('click', cerrarPoligono);
    if (_el('f-mapa-limpiar')) _el('f-mapa-limpiar').addEventListener('click', limpiarMapa);
  }
  document.getElementById('form-usuario').addEventListener('submit', enviarUsuario);
  document.getElementById('form-reporte').addEventListener('submit', enviarReporte);
  document.getElementById('repo-tipo').addEventListener('change', aplicarTipoReporte);
  document.getElementById('reporte-abrir').addEventListener('click', abrirReporte);
  document.getElementById('reporte-descargar').addEventListener('click', descargarReporteHtml);
  document.getElementById('form-chat').addEventListener('submit', enviarChat);
  document.getElementById('repo-finca').addEventListener('change', e => {
    state.fincaId = e.target.value || null;
    renderChat();
  });
  document.querySelectorAll('.chat-sugerencias .chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.getElementById('chat-input').value = chip.dataset.pregunta || '';
      document.getElementById('form-chat').requestSubmit();
    });
  });
  renderChat();
  document.getElementById('sim-enviar').addEventListener('click', enviarTramaSimulada);
  document.getElementById('sim-trama').value = JSON.stringify({
    device_id: 'esp32-npk-001',
    humidity: 0.0, temperature: 26.8, conductivity: 0.0,
    ph: 8.6, nitrogen: 0.0, phosphorus: 0.0, potassium: 0.0,
    rssi: -41, uptime_s: 64,
  }, null, 2);
  document.getElementById('catalogo-search').addEventListener('input', e => renderCatalogo(e.target.value));

  await Promise.allSettled([cargarFincas(), cargarCultivos(), cargarDispositivos()]);
  if (state.rol === 'Admin') await cargarUsuarios();
  await cargarDashboard();
  cargarSalud();

  // ── Auto-refresco SOLO de la página de sensores IoT (cada 10 s) ──
  // Permite ver en tiempo real la ingesta de tramas del sensor sin
  // recargar el resto de la aplicación.
  setInterval(() => {
    if (state.tabActual === 'sensores' && state.fincaId && !state.cargandoSensores) {
      cargarSensores();
    }
  }, 10000);
}

function poblarMunicipios() {
  const dep = document.getElementById('f-departamento').value;
  const sel = document.getElementById('f-municipio');
  const munis = DEPARTAMENTOS[dep] || [];
  sel.innerHTML = '<option value="">— Seleccione —</option>' +
    munis.map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('') +
    '<option value="__otro">Otro (especificar)</option>';
  document.getElementById('f-municipio-otro-wrap').style.display = 'none';
}

function aplicarRol() {
  const rol = (state.rol || '').toLowerCase();
  const permitidas = TABS_POR_ROL[rol] || [];
  document.querySelectorAll('.tab').forEach(t => {
    t.style.display = permitidas.includes(t.dataset.tab) ? '' : 'none';
  });
  const formCard = document.getElementById('finca-form-card');
  if (formCard) formCard.style.display = rol === 'admin' ? '' : 'none';

  const info = document.getElementById('user-info');
  if (info) info.textContent = `👤 ${state.nombre || state.email} · ${state.rol}`;

  // Elementos con data-roles: solo visibles para los roles indicados
  document.querySelectorAll('[data-roles]').forEach(el => {
    const roles = (el.dataset.roles || '').split(',').map(r => r.trim().toLowerCase());
    el.style.display = roles.includes(rol) ? '' : 'none';
  });

  // Simulador de sensor solo para roles no-cliente (los clientes son solo lectura)
  const simCard = document.getElementById('sensor-sim-card');
  if (simCard) simCard.style.display = rol === 'cliente' ? 'none' : '';

  // Si la vista activa no está permitida, volver a inicio
  const vistaActiva = document.querySelector('.view.active');
  if (vistaActiva && !permitidas.includes(vistaActiva.id.replace('view-', ''))) {
    goTab('inicio');
  }
}

function renderAccesoRestringido() {
  const lista = document.getElementById('fincas-lista');
  lista.innerHTML = '<div class="advertencia">🔒 El rol <b>Agrónomo</b> no puede registrar fincas. Solo el administrador tiene esa función.</div>';
}

async function cargarSalud() {
  const setPill = (id, texto, ok) => {
    const el = document.getElementById(id);
    el.textContent = texto;
    el.className = `pill ${ok ? 'ok' : 'fail'}`;
  };
  try {
    const h = await api('/health');
    setPill('pill-api', 'API ✓', true);
    setPill('pill-db', h.database === 'connected' ? 'BD ✓' : 'BD ✗', h.database === 'connected');
  } catch {
    setPill('pill-api', 'API ✗', false);
  }
  try {
    await fetch('http://localhost:8004/api/v1/health');
    setPill('pill-iot', 'IoT ✓', true);
  } catch {
    setPill('pill-iot', 'IoT ✗', false);
  }
}

async function cargarFincas() {
  try {
    const r = await api('/fincas');
    state.fincas = r.data || [];
    const sel = document.getElementById('finca-select');
    const selReco = document.getElementById('reco-finca');
    const selCarga = document.getElementById('carga-finca');
    const selRepo = document.getElementById('repo-finca');
    sel.innerHTML = '';
    selReco.innerHTML = '';
    selCarga.innerHTML = '<option value="">— Auto (según dispositivo) —</option>';
    selRepo.innerHTML = '';
    for (const f of state.fincas) {
      const opt = `<option value="${esc(f.id)}">${esc(f.nombre)} (${esc(f.departamento || '?')})</option>`;
      sel.innerHTML += opt;
      selReco.innerHTML += opt;
      selCarga.innerHTML += opt;
      selRepo.innerHTML += opt;
    }
    if (state.fincas.length) {
      state.fincaId = state.fincas[0].id;
      const f = state.fincas[0];
      document.getElementById('finca-detail').textContent =
        `${f.departamento || ''} ${f.municipio ? '· ' + f.municipio : ''} ${f.altitud_msnm ? '· ' + f.altitud_msnm + ' msnm' : ''} ${f.area_hectareas ? '· ' + f.area_hectareas + ' ha' : ''}`.trim();
    }
  } catch (e) {
    document.getElementById('finca-detail').textContent = 'Sin fincas: ' + e.message;
  }
}

function renderFincasList() {
  const div = document.getElementById('fincas-lista');
  if (!state.fincas.length) {
    div.innerHTML = '<p class="muted">Aún no hay fincas registradas. Usa el formulario de la izquierda (rol administrador).</p>';
    return;
  }
  div.innerHTML = state.fincas.map(f => {
    const link = f.latitud != null && f.longitud != null
      ? `https://www.google.com/maps?q=${f.latitud},${f.longitud}` : (f.coordenadas_google || '');
    return `
      <div class="device-card">
        <h3>🏡 ${esc(f.nombre)} <span class="muted">${esc(f.departamento || '')} · ${esc(f.municipio || '')}</span></h3>
        <div class="device-meta">
          <span>Propietario: <b>${esc(f.propietario || '—')}</b></span>
          <span>Tel: ${esc(f.contacto_telefono || '—')}</span>
          ${f.contacto_email ? `<span>Email: ${esc(f.contacto_email)}</span>` : ''}
          ${f.vereda ? `<span>Vereda: ${esc(f.vereda)}</span>` : ''}
          ${f.area_hectareas ? `<span>Área: ${f.area_hectareas} ha</span>` : ''}
          ${f.area_calculada_ha ? `<span>Área calculada: ${f.area_calculada_ha} ha</span>` : ''}
          ${f.tipo_area && f.tipo_area !== 'finca_completa' ? `<span>Tipo de área: ${esc(f.tipo_area)}</span>` : ''}
          ${f.tiene_multiples_lotes ? '<span>Varios lotes: sí</span>' : ''}
          ${f.precision_gps != null ? `<span>Precisión GPS: ±${f.precision_gps} m</span>` : ''}
          ${f.largo_metros && f.ancho_metros ? `<span>Dimensiones: ${f.largo_metros} × ${f.ancho_metros} m</span>` : ''}
          ${link ? `<span>📍 <a href="${esc(link)}" target="_blank">Ver en Google Maps</a></span>` : ''}
        </div>
        <div class="device-meta finca-id-row">
          <span class="mono-id" title="ID de la finca (envíelo en la trama del sensor como finca_id)">ID: <code>${esc(f.id || '—')}</code></span>
          <button type="button" class="btn btn-ghost btn-copiar" data-copiar="${esc(f.id || '')}">📋 Copiar</button>
        </div>
      </div>`;
  }).join('');
  div.querySelectorAll('.btn-copiar').forEach(b => {
    b.addEventListener('click', () => copiarTexto(b.dataset.copiar || '', b));
  });
}

function copiarTexto(texto, boton) {
  const ok = () => {
    if (!boton) return;
    boton.textContent = '✅ Copiado';
    setTimeout(() => { boton.textContent = '📋 Copiar'; }, 1500);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(texto).then(ok).catch(() => { ok(); });
    return;
  }
  const ta = document.createElement('textarea');
  ta.value = texto;
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); } catch { /* sin soporte */ }
  document.body.removeChild(ta);
  ok();
}

/* ─────────────────── wizard de registro de finca (3 secciones) ─────────────────── */

const fincaWiz = {
  lat: null, lng: null, altitud: null, precision: null,
  fuente: null, geometria: null, areaCalc: null, perimetro: null,
  puntos: [], mapa: null, poligono: null, marcadores: [],
};

function irWStep(n) {
  if (n === 2 && !validarPaso1()) return;
  if (n === 3 && !validarPaso2()) return;
  document.querySelectorAll('.wstep').forEach(b =>
    b.classList.toggle('active', Number(b.dataset.step) === n));
  [1, 2, 3].forEach(i => {
    document.getElementById('wstep-' + i).style.display = i === n ? '' : 'none';
  });
}

function validarPaso1() {
  const msg = document.getElementById('finca-msg');
  const nombre = document.getElementById('f-nombre').value.trim();
  const dep = document.getElementById('f-departamento').value;
  const munSel = document.getElementById('f-municipio').value;
  const municipio = munSel === '__otro'
    ? document.getElementById('f-municipio-otro').value.trim() : munSel;
  if (!nombre || !dep || !municipio) {
    msg.innerHTML = errorBanner('Complete nombre, departamento y municipio antes de continuar.');
    return false;
  }
  msg.innerHTML = '';
  return true;
}

function validarPaso2() {
  const msg = document.getElementById('finca-msg');
  if (fincaWiz.lat == null || fincaWiz.lng == null) {
    msg.innerHTML = errorBanner('Defina la ubicación (GPS, mapa o enlace de Google Maps) antes de continuar.');
    return false;
  }
  msg.innerHTML = '';
  return true;
}

function actualizarResumenUbicacion() {
  const wrap = document.getElementById('f-ubicacion-resumen');
  wrap.style.display = '';
  document.getElementById('f-res-lat').textContent = fincaWiz.lat != null ? fincaWiz.lat.toFixed(5) : '—';
  document.getElementById('f-res-lng').textContent = fincaWiz.lng != null ? fincaWiz.lng.toFixed(5) : '—';
  document.getElementById('f-res-alt').textContent = fincaWiz.altitud != null
    ? `${Math.round(fincaWiz.altitud).toLocaleString('es-CO')} msnm` : '—';
  document.getElementById('f-res-prec').textContent = fincaWiz.precision != null
    ? `±${Math.round(fincaWiz.precision)} m` : '—';
}

function aplicarCoordenadas(lat, lng, extra = {}) {
  fincaWiz.lat = lat; fincaWiz.lng = lng;
  fincaWiz.precision = extra.precision ?? null;
  fincaWiz.fuente = extra.fuente || 'manual';
  fincaWiz.altitud = extra.altitud ?? null;
  fincaWiz.geometria = null; fincaWiz.puntos = [];
  fincaWiz.areaCalc = null; fincaWiz.perimetro = null;
  actualizarAreaCalc();
  actualizarResumenUbicacion();
  if (fincaWiz.altitud == null) cargarElevacion(lat, lng);
}

async function cargarElevacion(lat, lng) {
  try {
    const r = await api(`/location/elevation?lat=${lat}&lon=${lng}`, { method: 'GET' });
    fincaWiz.altitud = r.elevation ?? r.altitud ?? r.altitud_estimada_msnm ?? null;
    actualizarResumenUbicacion();
  } catch { /* altitud opcional */ }
}

function usarMiUbicacion() {
  const msg = document.getElementById('finca-msg');
  if (!navigator.geolocation) {
    msg.innerHTML = errorBanner('El navegador no soporta geolocalización.');
    return;
  }
  msg.innerHTML = '<div class="ok-banner">📍 Obteniendo ubicación…</div>';
  navigator.geolocation.getCurrentPosition(
    pos => {
      aplicarCoordenadas(pos.coords.latitude, pos.coords.longitude, {
        precision: pos.coords.accuracy,
        altitud: pos.coords.altitude ?? null,
        fuente: 'gps_navegador',
      });
      msg.innerHTML = okBanner('Ubicación obtenida con GPS del dispositivo.');
    },
    err => {
      msg.innerHTML = errorBanner('No se pudo obtener la ubicación: ' + (err.message || 'permiso denegado'));
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  );
}

function parsearCoordenadas(texto) {
  const t = (texto || '').trim();
  const par = /^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$/.exec(t);
  if (par) return [parseFloat(par[1]), parseFloat(par[2])];
  const url = /(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)/.exec(t);
  if (url) return [parseFloat(url[1]), parseFloat(url[2])];
  // Formato de Google sin coma: !3d<lat>!4d<lng>
  const d = /!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)/.exec(t);
  if (d) return [parseFloat(d[1]), parseFloat(d[2])];
  return null;
}

async function aplicarEnlace() {
  const msg = document.getElementById('finca-msg');
  const texto = document.getElementById('f-enlace').value.trim();
  if (!texto) {
    msg.innerHTML = errorBanner('Pegue un enlace de Google Maps o "lat, lng".');
    return;
  }
  let coords = parsearCoordenadas(texto);
  // Los enlaces cortos (maps.app.goo.gl/…) no traen coordenadas: se
  // resuelven en el backend siguiendo la redirección.
  if (!coords && /^https?:\/\//i.test(texto)) {
    msg.innerHTML = '<div class="ok-banner">🔗 Resolviendo enlace de Google Maps…</div>';
    try {
      const r = await api(`/location/resolver-enlace?url=${encodeURIComponent(texto)}`, { method: 'GET' });
      coords = [r.latitud, r.longitud];
    } catch (err) {
      msg.innerHTML = errorBanner('No se pudieron extraer coordenadas del enlace: ' + err.message);
      return;
    }
  }
  if (!coords) {
    msg.innerHTML = errorBanner('No se pudieron extraer coordenadas del enlace. Pegue un enlace de Google Maps o "lat, lng".');
    return;
  }
  aplicarCoordenadas(coords[0], coords[1], { fuente: 'google_maps' });
  msg.innerHTML = okBanner('Coordenadas aplicadas desde el enlace.');
}

/* ── Mapa (Leaflet, se carga desde CDN la primera vez) ── */

let leafletCargando = false;
function cargarLeaflet(cb) {
  if (window.L) { cb(); return; }
  if (leafletCargando) {
    const t = setInterval(() => { if (window.L) { clearInterval(t); cb(); } }, 250);
    return;
  }
  leafletCargando = true;
  const css = document.createElement('link');
  css.rel = 'stylesheet';
  css.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
  document.head.appendChild(css);
  const s = document.createElement('script');
  s.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
  s.onload = () => cb();
  s.onerror = () => {
    document.getElementById('finca-msg').innerHTML =
      errorBanner('No se pudo cargar el mapa (sin conexión). Use "Usar mi ubicación" o el enlace de Google Maps.');
  };
  document.head.appendChild(s);
}

function abrirMapa() {
  const msg = document.getElementById('finca-msg');
  msg.innerHTML = '';
  document.getElementById('f-mapa-wrap').style.display = '';
  document.getElementById('f-enlace-wrap').style.display = 'none';
  cargarLeaflet(() => {
    if (fincaWiz.mapa) { fincaWiz.mapa.invalidateSize(); return; }
    const centro = fincaWiz.lat != null ? [fincaWiz.lat, fincaWiz.lng] : [4.57, -75.64];
    fincaWiz.mapa = L.map('f-mapa').setView(centro, 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, attribution: '© OpenStreetMap',
    }).addTo(fincaWiz.mapa);
    fincaWiz.mapa.on('click', e => {
      fincaWiz.puntos.push({ lat: e.latlng.lat, lng: e.latlng.lng });
      fincaWiz.marcadores.push(L.marker(e.latlng).addTo(fincaWiz.mapa));
      if (fincaWiz.poligono) { fincaWiz.mapa.removeLayer(fincaWiz.poligono); fincaWiz.poligono = null; }
    });
  });
}

function cerrarPoligono() {
  const msg = document.getElementById('finca-msg');
  if (fincaWiz.puntos.length < 3) {
    msg.innerHTML = errorBanner('Marque al menos 3 vértices del lindero.');
    return;
  }
  const latlngs = fincaWiz.puntos.map(p => [p.lat, p.lng]);
  if (fincaWiz.poligono) fincaWiz.mapa.removeLayer(fincaWiz.poligono);
  fincaWiz.poligono = L.polygon(latlngs, { color: '#2e7d32', weight: 2 }).addTo(fincaWiz.mapa);
  fincaWiz.mapa.fitBounds(fincaWiz.poligono.getBounds(), { padding: [20, 20] });
  // Cálculo local del área (el backend lo recalcula con autoridad)
  fincaWiz.areaCalc = calcularAreaHa(fincaWiz.puntos);
  fincaWiz.perimetro = calcularPerimetroM(fincaWiz.puntos);
  // Geometría GeoJSON ([lng, lat], anillo cerrado)
  const anillo = fincaWiz.puntos.map(p => [p.lng, p.lat]);
  anillo.push([fincaWiz.puntos[0].lng, fincaWiz.puntos[0].lat]);
  fincaWiz.geometria = { type: 'Polygon', coordinates: [anillo] };
  // Centroide como punto de referencia de la finca
  const lat0 = fincaWiz.puntos.reduce((s, p) => s + p.lat, 0) / fincaWiz.puntos.length;
  const lng0 = fincaWiz.puntos.reduce((s, p) => s + p.lng, 0) / fincaWiz.puntos.length;
  fincaWiz.lat = lat0; fincaWiz.lng = lng0;
  fincaWiz.fuente = 'mapa';
  actualizarAreaCalc();
  actualizarResumenUbicacion();
  if (fincaWiz.altitud == null) cargarElevacion(lat0, lng0);
  msg.innerHTML = okBanner(`Polígono cerrado: ${fincaWiz.areaCalc.toFixed(2)} ha calculadas.`);
}

function limpiarMapa() {
  fincaWiz.marcadores.forEach(m => { if (fincaWiz.mapa) fincaWiz.mapa.removeLayer(m); });
  if (fincaWiz.poligono && fincaWiz.mapa) fincaWiz.mapa.removeLayer(fincaWiz.poligono);
  fincaWiz.marcadores = []; fincaWiz.puntos = [];
  fincaWiz.poligono = null; fincaWiz.geometria = null;
  fincaWiz.areaCalc = null; fincaWiz.perimetro = null;
  actualizarAreaCalc();
  document.getElementById('finca-msg').innerHTML = '';
}

function calcularAreaHa(puntos) {
  const lat0 = puntos.reduce((s, p) => s + p.lat, 0) / puntos.length;
  const xy = puntos.map(p => [
    p.lng * Math.cos(lat0 * Math.PI / 180) * 111320,
    p.lat * 110574,
  ]);
  let area = 0;
  for (let i = 0; i < xy.length; i++) {
    const [x1, y1] = xy[i], [x2, y2] = xy[(i + 1) % xy.length];
    area += x1 * y2 - x2 * y1;
  }
  return Math.abs(area) / 2 / 10000;
}

function calcularPerimetroM(puntos) {
  const R = 6371000;
  const rad = d => d * Math.PI / 180;
  let per = 0;
  for (let i = 0; i < puntos.length; i++) {
    const a = puntos[i], b = puntos[(i + 1) % puntos.length];
    const dLat = rad(b.lat - a.lat), dLng = rad(b.lng - a.lng);
    const h = Math.sin(dLat / 2) ** 2 +
      Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLng / 2) ** 2;
    per += 2 * R * Math.asin(Math.sqrt(h));
  }
  return per;
}

function actualizarAreaCalc() {
  const el = document.getElementById('f-area-calc');
  if (!el) return;
  if (fincaWiz.areaCalc != null) {
    el.innerHTML = `<b>${fincaWiz.areaCalc.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ha</b>
      <small>(calculada del polígono · perímetro ${Math.round(fincaWiz.perimetro || 0).toLocaleString('es-CO')} m)</small>`;
  } else {
    el.innerHTML = '— <small>(calculada automáticamente del polígono)</small>';
  }
}

function renderValidaciones(pasos) {
  const div = document.getElementById('finca-validaciones');
  if (!pasos || !pasos.length) { div.innerHTML = ''; return; }
  const icono = { ok: '✅', error: '❌', warn: '⚠️' };
  div.innerHTML = '<div class="val-box">' + pasos.map(p =>
    `<div class="val-step val-${p.estado}">${icono[p.estado] || '•'} <b>${p.paso}.</b> ${esc(p.mensaje)}</div>`
  ).join('') + '</div>';
}

async function enviarFinca(e) {
  e.preventDefault();
  const msg = document.getElementById('finca-msg');
  const btn = document.getElementById('finca-btn');
  msg.innerHTML = '';
  renderValidaciones(null);

  // HTML desactualizado en caché del navegador (sin wizard)
  if (!document.getElementById('f-vereda') || !document.getElementById('wstep-3')) {
    msg.innerHTML = errorBanner(
      'El formulario está desactualizado en su navegador. Recargue la página con Ctrl+F5 (o borre la caché).'
    );
    return;
  }

  const municipioSel = document.getElementById('f-municipio').value;
  const municipio = municipioSel === '__otro'
    ? document.getElementById('f-municipio-otro').value.trim()
    : municipioSel;

  if (!municipio) {
    msg.innerHTML = errorBanner('Selecciona un municipio o especifícalo.');
    return;
  }
  if (fincaWiz.lat == null || fincaWiz.lng == null) {
    msg.innerHTML = errorBanner('Define la ubicación de la finca en el paso 2.');
    return;
  }

  const area = document.getElementById('f-area').value
    ? Number(document.getElementById('f-area').value) : null;
  const enlace = document.getElementById('f-enlace').value.trim();
  const multi = document.querySelector('input[name="f-multi"]:checked');

  const body = {
    nombre: document.getElementById('f-nombre').value.trim(),
    departamento: document.getElementById('f-departamento').value,
    municipio: municipio,
    vereda: document.getElementById('f-vereda').value.trim() || null,
    propietario: document.getElementById('f-propietario').value.trim(),
    contacto_telefono: document.getElementById('f-telefono').value.trim(),
    contacto_email: document.getElementById('f-email').value.trim() || null,
    latitud: fincaWiz.lat,
    longitud: fincaWiz.lng,
    altitud_msnm: fincaWiz.altitud,
    precision_gps: fincaWiz.precision,
    fuente_geolocalizacion: fincaWiz.fuente,
    geometria: fincaWiz.geometria,
    coordenadas_google: enlace || `${fincaWiz.lat}, ${fincaWiz.lng}`,
    area_declarada_ha: area,
    area_hectareas: area,
    tipo_area: document.getElementById('f-tipo-area').value,
    tiene_multiples_lotes: multi ? multi.value === 'si' : false,
    tipo_riego: document.getElementById('f-tipo-riego').value || null,
    profundidad_suelo_cm: document.getElementById('f-profundidad').value
      ? Number(document.getElementById('f-profundidad').value) : null,
    pedregosidad: document.getElementById('f-pedregosidad').value || null,
    largo_metros: document.getElementById('f-largo').value ? Number(document.getElementById('f-largo').value) : null,
    ancho_metros: document.getElementById('f-ancho').value ? Number(document.getElementById('f-ancho').value) : null,
  };

  btn.disabled = true;
  btn.textContent = '⏳ Validando y guardando…';
  try {
    const r = await api('/fincas', { method: 'POST', headers: headers(), body: JSON.stringify(body) });
    const finca = r.finca || {};
    const fid = finca.id || '';
    renderValidaciones(r.validaciones);
    msg.innerHTML = okBanner(
      `Finca <b>${esc(finca.nombre)}</b> creada y validada con éxito.`
    ) + `
    <div class="finca-id-box">
      <div><b>ID de la finca (para el sensor):</b></div>
      <div class="finca-id-line">
        <code>${esc(fid)}</code>
        <button type="button" class="btn btn-ghost" data-copiar="${esc(fid)}">📋 Copiar</button>
      </div>
      <p class="muted">Envíe este ID en cada trama del sensor como <code>finca_id</code>, o úselo para registrar el dispositivo en <code>POST /api/v1/iot/dispositivos</code>.</p>
    </div>
    ${r.lote_principal ? `<p class="muted">🌱 Lote productivo creado: <b>${esc(r.lote_principal.nombre)}</b>${r.lote_principal.area_ha != null ? ` (${esc(String(r.lote_principal.area_ha))} ha)` : ''}.</p>` : ''}`;
    const btnCopia = msg.querySelector('[data-copiar]');
    if (btnCopia) btnCopia.addEventListener('click', () => copiarTexto(btnCopia.dataset.copiar || '', btnCopia));
    e.target.reset();
    fincaWiz.lat = null; fincaWiz.lng = null; fincaWiz.altitud = null;
    fincaWiz.precision = null; fincaWiz.geometria = null;
    fincaWiz.areaCalc = null; fincaWiz.perimetro = null; fincaWiz.puntos = [];
    document.getElementById('f-ubicacion-resumen').style.display = 'none';
    document.getElementById('f-mapa-wrap').style.display = 'none';
    document.getElementById('f-enlace-wrap').style.display = 'none';
    actualizarAreaCalc();
    irWStep(1);
    await cargarFincas();
    renderFincasList();
    await cargarDashboard();
  } catch (err) {
    renderValidaciones(err.detail && err.detail.validaciones);
    msg.innerHTML = errorBanner(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '💾 Guardar finca';
  }
}

async function cargarCultivos() {
  try {
    const r = await api('/catalogo/cultivos?page_size=100');
    state.cultivos = r.data || [];
    state.catalogo = state.cultivos;
    const sels = ['carga-cultivo', 'reco-cultivo'];
    for (const id of sels) {
      const sel = document.getElementById(id);
      const prev = sel.value;
      sel.innerHTML = '<option value="">— Sin cultivo (UC1) —</option>' +
        state.cultivos.map(c => `<option value="${esc(c.id)}">${esc(c.icono || '🌱')} ${esc(c.nombre)}</option>`).join('');
      if (prev) sel.value = prev;
    }
  // Cultivos para el selector de reportes
  const repoCultivo = document.getElementById('repo-cultivo');
  repoCultivo.innerHTML = '<option value="">— Auto (top del ranking) —</option>' +
    state.cultivos.map(c => `<option value="${esc(c.id)}">${esc(c.icono || '🌱')} ${esc(c.nombre)}</option>`).join('');
  aplicarTipoReporte();

  document.getElementById('catalogo-count').textContent = `(${state.catalogo.length} cultivos)`;
  renderCatalogo('');
  } catch (e) { console.error(e); }
}

async function cargarDispositivos() {
  try {
    const r = await api('/iot/dispositivos');
    state.dispositivos = r.data || [];
  } catch (e) { console.error(e); }
}

/* ─────────────────────────── dashboard ─────────────────────────── */

async function cargarDashboard() {
  if (!state.fincaId) return;
  const kpis = document.getElementById('kpis');
  kpis.innerHTML = '';
  try {
    const [lecturas, status] = await Promise.all([
      api(`/iot/lecturas/${state.fincaId}?limite=5`),
      api(`/iot/sensores/${state.fincaId}/status`),
    ]);
    const total = (lecturas.data || []).length;
    const online = (status.sensores || []).filter(s => s.status === 'online').length;
    const offline = (status.sensores || []).filter(s => s.status !== 'online').length;
    kpis.innerHTML =
      kpi(state.dispositivos.length, 'Dispositivos') +
      kpi(online, 'Sensores en línea') +
      kpi(offline, 'Sensores desconectados') +
      kpi(total, 'Lecturas recientes');
    renderTablaLecturas(lecturas.data || [], document.getElementById('dashboard-lecturas'), 5);
  } catch (e) {
    kpis.innerHTML = errorBanner(e.message);
  }
}

function kpi(num, label) {
  return `<div class="kpi"><div class="kpi-num">${num}</div><div class="kpi-label">${esc(label)}</div></div>`;
}

/* ─────────────────────────── sensores ─────────────────────────── */

async function cargarSensores() {
  if (!state.fincaId || state.cargandoSensores) return;
  state.cargandoSensores = true;
  try {
    await cargarDispositivos();
    const div = document.getElementById('dispositivos');
    div.innerHTML = state.dispositivos.length
      ? state.dispositivos.map(d => `
      <div class="device-card">
        <h3>🔌 ${esc(d.nombre || d.device_id)}</h3>
        <div class="device-meta">
          <span>ID: <b>${esc(d.device_id)}</b></span>
          <span>NPK: ${d.npk_calibrado ? '✅ calibrado' : '⚠️ sin calibrar'}</span>
          <span>RSSI: ${d.rssi != null ? d.rssi + ' dBm' : '—'}</span>
          <span>Uptime: ${d.uptime_s != null ? Math.round(d.uptime_s / 60) + ' min' : '—'}</span>
          <span>Última transmisión: ${d.ultima_transmision ? new Date(d.ultima_transmision).toLocaleString() : '—'}</span>
        </div>
      </div>`).join('')
      : '<p class="muted">No hay dispositivos registrados. Regístralos en POST /api/v1/iot/dispositivos.</p>';

    try {
      const status = await api(`/iot/sensores/${state.fincaId}/status`);
      const divS = document.getElementById('sensor-status');
      const sensores = status.sensores || [];
      divS.innerHTML = sensores.length ? `
      <div class="table-wrap"><table>
        <tr><th>Dispositivo</th><th>Última transmisión</th><th>Horas desde última</th><th>Estado</th></tr>
        ${sensores.map(s => `
          <tr>
            <td>${esc(s.device_id)}</td>
            <td>${s.last_transmission ? new Date(s.last_transmission).toLocaleString() : '—'}</td>
            <td>${s.hours_since_last != null ? s.hours_since_last.toFixed(1) : '—'}</td>
            <td>${badge(s.status === 'online' ? 'En línea' : s.status === 'datos_desactualizados' ? 'Datos desactualizados' : 'Desconectado', badgeClase(s.status))}</td>
          </tr>`).join('')}
      </table></div>`
      : '<p class="muted">Sin transmisiones registradas todavía.</p>';
    } catch (e) {
      document.getElementById('sensor-status').innerHTML = errorBanner(e.message);
    }

    try {
      const lecturas = await api(`/iot/lecturas/${state.fincaId}?limite=10`);
      renderTablaLecturas(lecturas.data || [], document.getElementById('lecturas'), 10);
    } catch (e) {
      document.getElementById('lecturas').innerHTML = errorBanner(e.message);
    }
  } finally {
    state.cargandoSensores = false;
    const ind = document.getElementById('sensores-actualizacion');
    if (ind) ind.textContent = `· Actualizado ${new Date().toLocaleTimeString()} (auto cada 10 s)`;
  }
}

const ETIQUETAS = {
  ph: ['pH', ''], nitrogeno: ['Nitrógeno', 'ppm'], fosforo: ['Fósforo', 'ppm'], potasio: ['Potasio', 'ppm'],
  conductividad_electrica: ['CE', 'dS/m'], humedad_ambiental: ['HR amb.', '%'], temperatura_ambiental: ['T amb.', '°C'],
  materia_organica: ['M.O.', '%'], cic: ['CIC', 'meq/100g'], humedad: ['Humedad suelo', '%'], temperatura_suelo: ['T suelo', '°C'],
};

function nombreFinca(fid) {
  if (!fid) return '';
  const f = (state.fincas || []).find(x => String(x.id) === String(fid));
  return f ? f.nombre : '';
}

function celdaFinca(fid) {
  if (!fid) return '<td>—</td>';
  const nombre = nombreFinca(fid);
  const corto = String(fid).slice(0, 8);
  return `<td>${nombre ? esc(nombre) : '—'} <code class="mini-id" title="${esc(fid)}">${esc(corto)}…</code></td>`;
}

function renderTablaLecturas(data, container, limit) {
  if (!data.length) {
    container.innerHTML = '<p class="muted">Sin lecturas todavía. Envía una trama en vivo o carga un archivo.</p>';
    return;
  }
  const columnas = ['ph', 'nitrogeno', 'fosforo', 'potasio', 'conductividad_electrica', 'humedad_ambiental', 'temperatura_ambiental', 'materia_organica', 'cic'];
  container.innerHTML = `
    <div class="table-wrap"><table>
      <tr><th>Fecha</th><th>Finca</th><th>Sensor</th>${columnas.map(c => `<th>${ETIQUETAS[c][0]}</th>`).join('')}<th>Calidad</th></tr>
      ${data.slice(0, limit).map(r => `
        <tr>
          <td>${r.ts ? new Date(r.ts).toLocaleString() : '—'}</td>
          ${celdaFinca(r.finca_id)}
          <td>${esc(r.sensor_id || '—')}</td>
          ${columnas.map(c => `<td>${fmtNum(r[c])}${r[c] != null && ETIQUETAS[c][1] ? ' ' + ETIQUETAS[c][1] : ''}</td>`).join('')}
          <td>${badge(r.calidad === 'OK' ? 'OK' : 'npk sin calibrar', r.calidad === 'OK' ? 'ok' : 'warning')}</td>
        </tr>`).join('')}
    </table></div>`;
}

/* ─────────────────────────── carga de archivo ─────────────────────────── */

async function enviarCarga(e) {
  e.preventDefault();
  const btn = document.getElementById('carga-btn');
  const out = document.getElementById('carga-resultado');
  const file = document.getElementById('carga-file').files[0];
  if (!file) { out.innerHTML = errorBanner('Selecciona un archivo primero.'); return; }

  const fd = new FormData();
  fd.append('file', file);
  const device = document.getElementById('carga-device').value.trim();
  const cultivo = document.getElementById('carga-cultivo').value;
  const finca = document.getElementById('carga-finca').value;
  if (device) fd.append('device_id', device);
  if (cultivo) fd.append('cultivo_id', cultivo);
  if (finca) fd.append('finca_id', finca);

  btn.disabled = true;
  btn.textContent = '⏳ Analizando…';
  out.innerHTML = '';
  try {
    const r = await api('/iot/carga', { method: 'POST', body: fd });
    out.innerHTML = `
      <div class="card">
        <h2>📥 Ingesta del archivo</h2>
        ${okBanner(`Archivo <b>${esc(r.nombre_archivo)}</b> (formato ${esc(r.formato)}) procesado para el dispositivo <b>${esc(r.device_id)}</b>.`)}
        <p class="muted">
          Variables recibidas (${r.variables_recibidas.length}): ${r.variables_recibidas.map(esc).join(', ') || '—'}<br/>
          Advertencias: ${(r.advertencias_ingesta || []).map(esc).join(', ') || 'ninguna'}
        </p>
      </div>
      <div class="card">${renderAnalisis(r.analisis)}</div>`;
  } catch (err) {
    out.innerHTML = errorBanner(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '⬆️ Cargar y analizar';
  }
}

async function cargarEjemplo(tipo) {
  const nombres = { csv: 'mediciones.csv', txt: 'mediciones.txt', json: 'mediciones.json' };
  try {
    const res = await fetch(`/ejemplos/${nombres[tipo]}`);
    if (!res.ok) throw new Error('No se pudo descargar el ejemplo.');
    const texto = await res.text();
    const mime = tipo === 'json' ? 'application/json' : tipo === 'csv' ? 'text/csv' : 'text/plain';
    const fd = new FormData();
    fd.append('file', new File([texto], nombres[tipo], { type: mime }));
    const cultivo = document.getElementById('carga-cultivo').value;
    const finca = document.getElementById('carga-finca').value;
    if (cultivo) fd.append('cultivo_id', cultivo);
    if (finca) fd.append('finca_id', finca);

    const btn = document.getElementById('carga-btn');
    const out = document.getElementById('carga-resultado');
    btn.disabled = true;
    btn.textContent = '⏳ Analizando…';
    out.innerHTML = '';
    try {
      const r = await api('/iot/carga', { method: 'POST', body: fd });
      out.innerHTML = `
        <div class="card">
          <h2>📥 Ingesta del ejemplo</h2>
          ${okBanner(`Archivo de ejemplo <b>${esc(r.nombre_archivo)}</b> procesado para el dispositivo <b>${esc(r.device_id)}</b>.`)}
        </div>
        <div class="card">${renderAnalisis(r.analisis)}</div>`;
    } catch (err) {
      out.innerHTML = errorBanner(err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = '⬆️ Cargar y analizar';
    }
  } catch (err) {
    document.getElementById('carga-resultado').innerHTML = errorBanner(err.message);
  }
}

/* ─────────────────────────── recomendaciones ─────────────────────────── */

async function enviarAnalisis(e) {
  e.preventDefault();
  const out = document.getElementById('reco-resultado');
  const finca = document.getElementById('reco-finca').value;
  const cultivo = document.getElementById('reco-cultivo').value;
  if (!finca) { out.innerHTML = errorBanner('Selecciona una finca.'); return; }
  out.innerHTML = '<div class="card"><p class="muted">⏳ Ejecutando motor de recomendaciones…</p></div>';
  try {
    const r = await api('/recomendaciones/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ finca_id: finca, cultivo_id: cultivo || null }),
    });
    state.ultimoAnalisis = r;
    out.innerHTML = `<div class="card">${renderAnalisis(r)}</div>${renderPanelAceptacion(r)}`;
  } catch (err) {
    out.innerHTML = errorBanner(err.message);
  }
}

/* ── Aceptación de recomendación (feedback humano → confianza del modelo) ── */

function renderPanelAceptacion(a) {
  const rol = (state.rol || '').toLowerCase();
  if (!['admin', 'administrador', 'agronomo', 'agrónomo'].includes(rol)) return '';
  return `
  <div class="card aceptar-rec">
    <h3>✅ Aceptación de la recomendación (${esc(state.rol || '')})</h3>
    <p class="muted">Al aceptar, la recomendación queda registrada como feedback y el modelo gana confianza para esta finca/cultivo (aprendizaje continuo).</p>
    <textarea id="aceptar-comentario" rows="3" placeholder="Amplíe, si es necesario, la recomendación o las acciones a implementar… (opcional)"></textarea>
    <div class="aceptar-fila">
      <button id="btn-aceptar-rec" onclick="aceptarRecomendacion()">✅ Aceptar recomendación</button>
      <span id="aceptar-estado" class="muted"></span>
    </div>
  </div>`;
}

async function aceptarRecomendacion() {
  const a = state.ultimoAnalisis;
  const finca = document.getElementById('reco-finca').value;
  const cultivo = document.getElementById('reco-cultivo').value;
  const comentarioEl = document.getElementById('aceptar-comentario');
  const estado = document.getElementById('aceptar-estado');
  const btn = document.getElementById('btn-aceptar-rec');
  if (!finca || !a) { if (estado) estado.textContent = 'Primero ejecute el análisis.'; return; }
  let cultivoId = cultivo || null;
  if (!cultivoId && a.sugerencias_cultivos && a.sugerencias_cultivos.length) {
    cultivoId = a.sugerencias_cultivos[0].cultivo_id || null;
  }
  if (btn) btn.disabled = true;
  if (estado) estado.textContent = '⏳ Registrando…';
  try {
    const r = await api('/recomendaciones/aceptar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        finca_id: finca,
        cultivo_id: cultivoId,
        comentario: comentarioEl ? comentarioEl.value.trim() || null : null,
        resumen: {
          cultivo: a.cultivo,
          clasificacion: a.clasificacion_upra,
          confianza: a.confianza,
          recomendaciones: a.recomendaciones || [],
        },
        clasificacion_previa: a.clasificacion_upra || null,
        confianza_previa: a.confianza != null ? a.confianza : null,
      }),
    });
    if (estado) estado.textContent = `✅ ${r.mensaje}`;
    if (btn) btn.textContent = '✅ Aceptada';
    if (comentarioEl) comentarioEl.disabled = true;
  } catch (err) {
    if (estado) estado.textContent = err.message || 'No se pudo registrar la aceptación.';
    if (btn) btn.disabled = false;
  }
}

function descAjustes(ajustes) {
  if (!ajustes || !ajustes.length) return '<span class="muted">— Sin ajustes necesarios.</span>';
  return ajustes.map(a => `
    <div class="ajuste-item">
      <b>${esc(a.variable)}</b> ${badge(a.estado || '', badgeEstadoClase(a.estado || ''))}
      <span class="muted">${esc(a.rango_ideal || '')}</span>
      <div class="ajuste-accion">${esc(a.accion || '')}${a.prioridad ? ` <span class="muted">(${esc(a.prioridad)})</span>` : ''}</div>
    </div>`).join('');
}

function badgeValidacion(estado) {
  const e = (estado || '').toLowerCase();
  if (e === 'pendiente_validacion' || e.includes('pendiente')) return '<span class="badge pendiente">Pendiente de validación técnica</span>';
  if (e.includes('textura')) return '<span class="badge textura">Sujeta a confirmación de textura</span>';
  if (e === 'preliminar') return '<span class="badge preliminar">Preliminar</span>';
  if (e === 'validada') return '<span class="badge validada">Validada</span>';
  return '';
}

function fmtPlan(plan) {
  if (!plan) return '—';
  const partes = [];
  if (plan.fuente) partes.push(`<b>Fuente:</b> ${esc(plan.fuente)}`);
  if (plan.frecuencia) partes.push(`<b>Frecuencia:</b> ${esc(plan.frecuencia)}`);
  if (plan.dosis) partes.push(`<b>Dosis:</b> ${esc(plan.dosis)}`);
  return partes.length ? `<div style="font-size:0.78rem;line-height:1.5">${partes.join('<br>')}</div>` : '—';
}

function renderAnalisis(a) {
  if (!a) return '<p class="muted">Sin resultado.</p>';
  const confianza = Math.round((a.confianza || 0) * 100);
  const confianzaReal = Math.round((a.confianza_real || 0) * 100);
  const respaldos = a.respaldos || 0;
  let html = `
    <div class="analisis-head">
      <div class="cultivo">${esc(a.cultivo)}</div>
      <div>${badge(a.clasificacion_upra, badgeClase(a.clasificacion_upra))} ${badgeValidacion(a.estado_validacion)}</div>
      <div style="flex:1;min-width:180px">
        <div class="confianza-bar"><div style="width:${confianza}%"></div></div>
        <span class="muted">Confianza ${confianza}%${confianzaReal ? ` (real ${confianzaReal}%)` : ''} · ${esc(a.modo)} · ${a.tiempo_respuesta_ms ? Math.round(a.tiempo_respuesta_ms) + ' ms' : ''}${respaldos ? ` · respaldada por ${respaldos} experto${respaldos !== 1 ? 's' : ''}` : ''}</span>
      </div>
    </div>`;

  if (a.fenologia_ajustada) html += `<div class="advertencia">🌱 ${esc(a.fenologia_ajustada)}</div>`;
  if (a.variables_faltantes_fertilidad && a.variables_faltantes_fertilidad.length) {
    html += `<div class="advertencia">🔬 Variables de fertilidad sin dato: ${esc(a.variables_faltantes_fertilidad.join(', '))}. La confianza global se redujo; la clasificación es preliminar.</div>`;
  }
  if (a.advertencia) html += `<div class="advertencia">${esc(a.advertencia)}</div>`;
  if (a.discordancia) html += `<div class="advertencia">🔀 Discordancia detectada: ${esc(JSON.stringify(a.discordancia))}</div>`;

  if (a.recomendaciones && a.recomendaciones.length) {
    html += `
      <div class="table-wrap"><table>
        <tr><th>Variable</th><th>Estado</th><th>Lectura</th><th>Rango ideal</th><th>Acción</th><th>Prioridad</th><th>Confiabilidad</th><th>Plan sugerido</th></tr>
        ${a.recomendaciones.map(r => `
          <tr>
            <td><b>${esc(r.variable)}</b></td>
            <td>${badge(r.estado, badgeEstadoClase(r.estado))}</td>
            <td>${r.valor_actual != null ? fmtNum(r.valor_actual) : '—'}</td>
            <td>${esc(r.rango_ideal || '—')}</td>
            <td>${esc(r.accion || '—')}${r.condicional ? ' <span class="badge preliminar">Condicional a confirmación de laboratorio</span>' : ''}${r.contexto ? `<div class="muted" style="font-size:0.78rem;margin-top:3px">${esc(r.contexto)}</div>` : ''}</td>
            <td>${esc(r.prioridad || '—')}</td>
            <td>${esc(r.confiabilidad || '—')}</td>
            <td>${fmtPlan(r.plan)}</td>
          </tr>`).join('')}
      </table></div>`;
  }

  if (a.sugerencias_cultivos && a.sugerencias_cultivos.length) {
    html += `<h3 style="margin-top:18px">🌾 Cultivos sugeridos (ranking del motor)</h3>`;
    html += `
      <div class="table-wrap"><table>
        <tr><th>#</th><th>Cultivo</th><th>Score</th><th>Clasificación</th><th>Confianza</th><th>Reglas</th><th>Descripción de reglas aplicadas</th></tr>
        ${a.sugerencias_cultivos.map((s, i) => `
          <tr>
            <td>${i + 1}</td>
            <td>${esc(s.icono || '')} ${esc(s.cultivo)}${s.nota_secano ? `<div class="muted" style="font-size:0.75rem">${esc(s.nota_secano)}</div>` : ''}</td>
            <td>${fmtNum(s.score, 1)}</td>
            <td>${badge(s.clasificacion, badgeClase(s.clasificacion))}</td>
            <td>${Math.round((s.confianza || 0) * 100)}%</td>
            <td>${s.reglas_especificas ?? '—'}</td>
            <td class="ajustes-desc">${descAjustes(s.ajustes)}</td>
          </tr>`).join('')}
      </table></div>`;
  }

  if (a.justificacion && a.justificacion.resumen) {
    html += `<p class="muted" style="margin-top:12px">📋 ${esc(a.justificacion.resumen)}</p>`;
  }
  return html;
}

/* ─────────────────────────── historial ─────────────────────────── */

async function cargarHistorial() {
  const div = document.getElementById('historial');
  if (!state.fincaId) {
    div.innerHTML = '<p class="muted">Selecciona una finca.</p>';
    return;
  }
  div.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const r = await api(`/recomendaciones/historial/${state.fincaId}?page_size=50`);
    const items = r.data || [];
    if (!items.length) {
      div.innerHTML = '<p class="muted">Sin recomendaciones aún. Ejecuta un análisis o carga un archivo.</p>';
      return;
    }
    const nombreCultivo = id => {
      const c = state.cultivos.find(x => x.id === id);
      return c ? `${c.icono || ''} ${c.nombre}` : id;
    };
    div.innerHTML = `
      <div class="table-wrap"><table>
        <tr><th>Fecha</th><th>Cultivo</th><th>Clasificación</th><th>Confianza</th><th>Estado</th></tr>
        ${items.map(h => `
          <tr>
            <td>${new Date(h.created_at).toLocaleString()}</td>
            <td>${esc(nombreCultivo(h.cultivo_id))}</td>
            <td>${badge(h.clasificacion_upra, badgeClase(h.clasificacion_upra))}</td>
            <td>${Math.round((h.confianza || 0) * 100)}%</td>
            <td>${badge(h.estado, h.estado === 'Advertencia' ? 'warning' : 'ok')}</td>
          </tr>`).join('')}
      </table></div>`;
  } catch (e) {
    div.innerHTML = errorBanner(e.message);
  }
}

/* ─────────────────────────── usuarios (solo admin) ─────────────────────────── */

async function cargarUsuarios() {
  try {
    const usuarios = await api('/usuarios');
    state.usuarios = usuarios || [];
    renderUsuariosList();
    renderMultiSelectFincas();
  } catch (e) {
    document.getElementById('usuarios-lista').innerHTML = errorBanner(e.message);
  }
}

const msFincasSeleccionadas = new Set();

function renderMultiSelectFincas() {
  const panel = document.getElementById('u-fincas-panel');
  panel.innerHTML = state.fincas.length
    ? state.fincas.map(f => {
        const sel = msFincasSeleccionadas.has(f.id);
        return `
        <label>
          <input type="checkbox" data-finca-id="${esc(f.id)}" ${sel ? 'checked' : ''} />
          <span>${esc(f.nombre)} <span class="muted">(${esc(f.departamento || '?')})</span></span>
        </label>`;
      }).join('')
    : '<p class="muted" style="padding:6px 8px">No hay fincas registradas todavía.</p>';

  panel.querySelectorAll('input[type="checkbox"]').forEach(cb => {
    cb.addEventListener('change', () => {
      if (cb.checked) msFincasSeleccionadas.add(cb.dataset.fincaId);
      else msFincasSeleccionadas.delete(cb.dataset.fincaId);
      actualizarTriggerFincas();
    });
  });
  actualizarTriggerFincas();
}

function actualizarTriggerFincas() {
  const trigger = document.getElementById('u-fincas-trigger');
  if (!msFincasSeleccionadas.size) {
    trigger.innerHTML = '<span class="muted">Seleccionar fincas…</span>';
    return;
  }
  const nombres = state.fincas
    .filter(f => msFincasSeleccionadas.has(f.id))
    .map(f => `<span class="ms-chip">${esc(f.nombre)}</span>`);
  trigger.innerHTML = nombres.join('');
}

function renderUsuariosList() {
  const div = document.getElementById('usuarios-lista');
  if (!state.usuarios.length) {
    div.innerHTML = '<p class="muted">Sin usuarios.</p>';
    return;
  }
  div.innerHTML = state.usuarios.map(u => `
    <div class="device-card">
      <h3>👤 ${esc(u.nombre)} ${badge(u.rol, u.rol === 'Admin' ? 'ok' : u.rol === 'Cliente' ? 'warning' : 'ok')}</h3>
      <div class="device-meta">
        <span>Email: <b>${esc(u.email)}</b></span>
        <span>Fincas: ${u.fincas && u.fincas.length
          ? u.fincas.map(f => esc(f.nombre)).join(', ')
          : '<span class="muted">ninguna</span>'}</span>
      </div>
    </div>`).join('');
}

async function enviarUsuario(e) {
  e.preventDefault();
  const msg = document.getElementById('usuario-msg');
  const btn = document.getElementById('usuario-btn');
  msg.innerHTML = '';

  const fincaIds = Array.from(msFincasSeleccionadas);

  const body = {
    nombre: document.getElementById('u-nombre').value.trim(),
    email: document.getElementById('u-email').value.trim(),
    password: document.getElementById('u-password').value,
    rol: document.getElementById('u-rol').value,
    finca_ids: fincaIds,
  };

  btn.disabled = true;
  btn.textContent = '⏳ Guardando…';
  try {
    const r = await api('/usuarios', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(body),
    });
    msg.innerHTML = okBanner(
      `Usuario <b>${esc(r.email)}</b> (${esc(r.rol)}) creado y relacionado con ${r.fincas.length} finca(s).`
    );
    msFincasSeleccionadas.clear();
    e.target.reset();
    await cargarUsuarios();
  } catch (err) {
    msg.innerHTML = errorBanner(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '💾 Guardar usuario';
  }
}

/* ─────────────────────────── reportes ─────────────────────────── */

let reporteHtmlActual = null;

function aplicarTipoReporte() {
  const tipo = document.getElementById('repo-tipo').value;
  const wrap = document.getElementById('repo-cultivo-wrap');
  wrap.style.display = tipo === 'siembra' ? 'none' : 'flex';
}

async function enviarReporte(e) {
  e.preventDefault();
  const btn = document.getElementById('reporte-btn');
  const tipo = document.getElementById('repo-tipo').value;
  const cultivo = document.getElementById('repo-cultivo').value;
  const finca = document.getElementById('repo-finca').value;

  if (!finca) {
    document.getElementById('reporte-preview-card').style.display = 'none';
    alert('Selecciona una finca para generar el reporte.');
    return;
  }

  btn.disabled = true;
  btn.textContent = '⏳ Generando…';
  try {
    const r = await api('/reportes/generar', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ finca_id: finca, tipo, cultivo_id: cultivo || null }),
    });
    reporteHtmlActual = r.html;
    const card = document.getElementById('reporte-preview-card');
    card.style.display = '';
    document.getElementById('reporte-iframe').srcdoc = r.html;
    card.scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    document.getElementById('reporte-preview-card').style.display = 'none';
    alert('Error al generar el reporte: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '📄 Generar reporte';
  }
}

function abrirReporte() {
  if (!reporteHtmlActual) return;
  const blob = new Blob([reporteHtmlActual], { type: 'text/html;charset=utf-8' });
  window.open(URL.createObjectURL(blob), '_blank');
}

function descargarReporteHtml() {
  if (!reporteHtmlActual) return;
  const blob = new Blob([reporteHtmlActual], { type: 'text/html;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'reporte-agroia.html';
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ─────────────────────────── chat asesor agronómico ─────────────────────────── */

const chatHistorial = {}; // finca_id → [{rol, contenido}]
let chatFincaActual = null;
let chatModo = null; // 'llm' | 'experto-local'
let chatMeta = null; // {confianza, fuentes} de la última respuesta

function chatFincaId() {
  const sel = document.getElementById('repo-finca');
  return (sel && sel.value) || state.fincaId || null;
}

function renderChat() {
  const div = document.getElementById('chat-mensajes');
  const nota = document.getElementById('chat-nota');
  const fid = chatFincaId();
  chatFincaActual = fid;
  const hist = fid ? (chatHistorial[fid] || []) : [];
  if (!hist.length) {
    div.innerHTML =
      '<div class="chat-msg chat-bot">👋 ¡Hola! Soy su asesor agronómico. ' +
      'Seleccione una finca y pregúnteme lo que necesite: cómo abonar, qué sembrar, ' +
      'qué significa cada medición del reporte…</div>';
    nota.textContent = fid
      ? 'Las respuestas usan la lectura de suelo y las reglas UPRA/Cenicafé/AGROSAVIA de la finca seleccionada.'
      : 'Seleccione una finca para poder consultar al asesor.';
    return;
  }
  div.innerHTML = hist.map(m =>
    `<div class="chat-msg ${m.rol === 'user' ? 'chat-user' : 'chat-bot'}">${esc(m.contenido)}</div>`
  ).join('');
  let extra = '';
  if (chatMeta) {
    const partes = [];
    if (chatMeta.confianza) partes.push('Confianza: ' + chatMeta.confianza);
    if (chatMeta.fuentes && chatMeta.fuentes.length) partes.push('Fuentes: ' + chatMeta.fuentes.join(' · '));
    if (partes.length) extra = ' · ' + partes.join(' · ');
  }
  nota.textContent = fid
    ? ((chatModo === 'llm'
      ? 'Respuestas del modelo de lenguaje con el contexto real de la finca (lectura + reglas UPRA/Cenicafé/AGROSAVIA).'
      : 'Respuestas del sistema experto local basadas en los datos de la finca y las reglas UPRA/Cenicafé/AGROSAVIA.') + extra)
    : '';
  div.scrollTop = div.scrollHeight;
}

async function enviarChat(e) {
  e.preventDefault();
  const input = document.getElementById('chat-input');
  const btn = document.getElementById('chat-btn');
  if (btn.disabled) return; // evita dobles envíos
  const mensaje = (input.value || '').trim();
  const fid = chatFincaId();

  if (!fid) {
    alert('Selecciona una finca para consultar al asesor.');
    return;
  }
  if (!mensaje) return;

  btn.disabled = true;
  const hist = chatHistorial[fid] || (chatHistorial[fid] = []);
  hist.push({ rol: 'user', contenido: mensaje });
  input.value = '';
  renderChat();

  const div = document.getElementById('chat-mensajes');
  div.insertAdjacentHTML('beforeend',
    '<div class="chat-msg chat-bot chat-typing">El experto está revisando su suelo… 🌱</div>');
  div.scrollTop = div.scrollHeight;

  btn.disabled = true;
  try {
    const r = await api('/chat/consultar', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({
        finca_id: fid,
        mensaje,
        historial: hist.slice(-7, -1),
      }),
    });
    hist.push({ rol: 'assistant', contenido: r.respuesta });
    chatModo = r.modo || 'experto-local';
    chatMeta = { confianza: r.confianza, fuentes: r.fuentes };
  } catch (err) {
    hist.push({
      rol: 'assistant',
      contenido: 'Hubo un problema al consultar: ' + err.message,
    });
  } finally {
    btn.disabled = false;
    renderChat();
  }
}

/* ─────────────────────────── simulador de sensor ─────────────────────────── */

async function enviarTramaSimulada() {
  const out = document.getElementById('sim-msg');
  const btn = document.getElementById('sim-enviar');
  let trama;
  try {
    trama = JSON.parse(document.getElementById('sim-trama').value);
  } catch {
    out.innerHTML = errorBanner('El JSON no es válido. Corrígelo e inténtalo de nuevo.');
    return;
  }
  btn.disabled = true;
  btn.textContent = '📡 Enviando…';
  out.innerHTML = '';
  try {
    // Endpoint real de los sensores físicos: POST /api/sensor
    const res = await fetch('/api/sensor', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify(trama),
    });
    const r = await res.json();
    if (!res.ok) {
      const detail = r && r.detail;
      throw new Error((detail && (detail.message || JSON.stringify(detail))) || `HTTP ${res.status}`);
    }
    out.innerHTML = okBanner(
      `Trama aceptada para <b>${esc(r.device_id)}</b> (finca ${esc(r.finca_id)}${r.auto_registrado ? ', auto-registrado' : ''}). ` +
      `Variables recibidas: ${esc((r.variables_recibidas || []).join(', ') || '—')} ` +
      `· Advertencias: ${esc((r.advertencias || []).join(', ') || 'ninguna')}.`
    );
  } catch (err) {
    out.innerHTML = errorBanner(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '📡 Enviar trama';
  }
}

/* ─────────────────────────── catálogo ─────────────────────────── */

function renderCatalogo(q) {
  const div = document.getElementById('catalogo');
  const ql = (q || '').toLowerCase().trim();
  const items = state.catalogo.filter(c =>
    !ql || (c.nombre || '').toLowerCase().includes(ql) ||
    (c.nombre_cientifico || '').toLowerCase().includes(ql) ||
    (c.descripcion || '').toLowerCase().includes(ql));
  div.innerHTML = items.length
    ? items.map(c => `
      <div class="cultivo-card">
        <div class="icono">${esc(c.icono || '🌱')}</div>
        <h3>${esc(c.nombre)}</h3>
        ${c.nombre_cientifico ? `<p><i>${esc(c.nombre_cientifico)}</i></p>` : ''}
        ${c.descripcion ? `<p>${esc(c.descripcion)}</p>` : ''}
        ${c.activo === false ? badge('Inactivo', 'critical') : badge('Activo', 'ok')}
      </div>`).join('')
    : '<p class="muted">Sin resultados.</p>';
}

document.addEventListener('DOMContentLoaded', init);
