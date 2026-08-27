/* AgroIA — Frontend integrado (SPA vanilla).
 * Consume la API del backend en el mismo origen.
 */
'use strict';

const API = '/api/v1';
const SESION_KEY = 'agroia_sesion';

const TABS_POR_ROL = {
  admin: ['inicio', 'sensores', 'carga', 'recomendaciones', 'historial', 'reportes', 'fincas', 'usuarios', 'auditoria', 'catalogo'],
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
  if (state.email) {
    h['X-User-Email'] = state.email;
    if (state.nombre) h['X-User-Nombre'] = state.nombre;
  }
  if (json) h['Content-Type'] = 'application/json';
  return h;
}

/* ─────────────────────────── utilidades ─────────────────────────── */

async function api(path, opts = {}) {
  const h = { ...(opts.headers || {}), 'X-User-Role': state.rol };
  if (state.email) {
    h['X-User-Email'] = state.email;
    if (state.nombre) h['X-User-Nombre'] = state.nombre;
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
  if (name === 'auditoria' && state.rol.toLowerCase() === 'admin') cargarAuditoria();
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
  // ── Flujo rápido: registrar nuevo ciclo desde Recomendaciones ──
  const btnCiclo = document.getElementById('reco-nuevo-ciclo');
  if (btnCiclo) btnCiclo.addEventListener('click', abrirModalIniciarCiclo);
  document.getElementById('form-carga').addEventListener('submit', enviarCarga);
  // ── Carga masiva: historial de ciclos (CSV) ──
  document.getElementById('form-carga-ciclos').addEventListener('submit', enviarCargaCiclos);
  document.getElementById('plantilla-ciclos').addEventListener('click', descargarPlantillaCiclos);
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
  // ── Modal de edición (fincas/lotes/usuarios) y controles de auditoría ──
  document.getElementById('modal-cerrar').addEventListener('click', cerrarModal);
  document.getElementById('modal-cancelar').addEventListener('click', cerrarModal);
  document.getElementById('audit-refrescar').addEventListener('click', () => cargarAuditoria(1));
  document.getElementById('audit-anterior').addEventListener('click', () => {
    if (auditState.page > 1) cargarAuditoria(auditState.page - 1);
  });
  document.getElementById('audit-siguiente').addEventListener('click', () => {
    if (auditState.page < auditState.totalPages) cargarAuditoria(auditState.page + 1);
  });
  document.getElementById('form-reporte').addEventListener('submit', enviarReporte);
  document.getElementById('repo-tipo').addEventListener('change', aplicarTipoReporte);
  document.getElementById('reporte-abrir').addEventListener('click', abrirReporte);
  document.getElementById('reporte-descargar').addEventListener('click', descargarReporteHtml);
  registrarSimulacion();
  document.getElementById('form-chat').addEventListener('submit', enviarChat);
  document.getElementById('chat-attach').addEventListener('click', () => {
    document.getElementById('chat-imagen').click();
  });
  document.getElementById('chat-imagen').addEventListener('change', e => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    if (!/^image\/(jpeg|png)$/.test(f.type)) {
      alert('Solo se permiten fotos en formato JPG o PNG.');
      e.target.value = '';
      return;
    }
    if (f.size > 4.5 * 1024 * 1024) {
      alert('La foto no puede superar 4,5 MB.');
      e.target.value = '';
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      chatImagen = reader.result;
      const pv = document.getElementById('chat-preview');
      document.getElementById('chat-preview-img').src = reader.result;
      pv.classList.remove('hidden');
    };
    reader.readAsDataURL(f);
  });
  document.getElementById('chat-quitar').addEventListener('click', limpiarChatImagen);
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
  // Trama de ejemplo con el formato REAL del firmware (POST /api/sensor),
  // incluyendo finca_id, posición de la toma y humedad/temperatura de suelo.
  document.getElementById('sim-trama').value = JSON.stringify({
    device_id: 'esp32-npk-001',
    finca_id: '8c2ea84f-b5fa-4291-a1e5-8b42fa5a9936',
    pos_x: 20.0,
    pos_y: 50.0,
    ph: 6.1,
    conductivity: 620,
    nitrogen: 260,
    phosphorus: 28,
    potassium: 95,
    soil_humidity: 31.0,
    soil_temperature: 19.5,
    humidity: 72.0,
    temperature: 21.2,
    rssi: -45,
    uptime_s: 604800,
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
    const selCiclos = document.getElementById('carga-ciclos-finca');
    const selRepo = document.getElementById('repo-finca');
    sel.innerHTML = '';
    selReco.innerHTML = '';
    selCarga.innerHTML = '<option value="">— Auto (según dispositivo) —</option>';
    selCiclos.innerHTML = '';
    selRepo.innerHTML = '';
    for (const f of state.fincas) {
      const opt = `<option value="${esc(f.id)}">${esc(f.nombre)} (${esc(f.departamento || '?')})</option>`;
      sel.innerHTML += opt;
      selReco.innerHTML += opt;
      selCarga.innerHTML += opt;
      selCiclos.innerHTML += opt;
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
        <div class="device-actions">
          <button type="button" class="btn btn-ghost" data-accion="lotes" data-id="${esc(f.id)}">🗂️ Lotes</button>
          <button type="button" class="btn btn-ghost" data-accion="editar-finca" data-id="${esc(f.id)}">✏️ Editar</button>
          <button type="button" class="btn btn-ghost btn-danger" data-accion="eliminar-finca" data-id="${esc(f.id)}" data-nombre="${esc(f.nombre)}">🗑️ Eliminar</button>
        </div>
        <div class="lotes-panel hidden" id="lotes-${esc(f.id)}"></div>
      </div>`;
  }).join('');
  div.querySelectorAll('.btn-copiar').forEach(b => {
    b.addEventListener('click', () => copiarTexto(b.dataset.copiar || '', b));
  });
  div.querySelectorAll('[data-accion="lotes"]').forEach(b => {
    b.addEventListener('click', () => toggleLotes(b.dataset.id));
  });
  div.querySelectorAll('[data-accion="editar-finca"]').forEach(b => {
    b.addEventListener('click', () => abrirEditarFinca(b.dataset.id));
  });
  div.querySelectorAll('[data-accion="eliminar-finca"]').forEach(b => {
    b.addEventListener('click', () => eliminarFinca(b.dataset.id, b.dataset.nombre || ''));
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

/* ────────────────────── edición/eliminación de fincas (admin) ────────────────────── */

function cerrarModal() {
  document.getElementById('modal-editor').classList.add('hidden');
}

async function abrirEditarFinca(id) {
  const f = state.fincas.find(x => x.id === id);
  if (!f) return;
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `✏️ Editar finca — ${f.nombre}`;
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="form-grid">
      <label class="field"><span>Nombre *</span><input id="ef-nombre" value="${esc(f.nombre)}" required /></label>
      <label class="field"><span>Departamento *</span><input id="ef-departamento" value="${esc(f.departamento || '')}" required /></label>
      <label class="field"><span>Municipio *</span><input id="ef-municipio" value="${esc(f.municipio || '')}" required /></label>
      <label class="field"><span>Propietario *</span><input id="ef-propietario" value="${esc(f.propietario || '')}" required /></label>
      <label class="field"><span>Teléfono *</span><input id="ef-telefono" value="${esc(f.contacto_telefono || '')}" required /></label>
      <label class="field"><span>Email</span><input id="ef-email" type="email" value="${esc(f.contacto_email || '')}" /></label>
      <label class="field"><span>Área (ha)</span><input id="ef-area" type="number" min="0" step="0.01" value="${f.area_hectareas != null ? f.area_hectareas : ''}" /></label>
      <label class="field"><span>Altitud (msnm)</span><input id="ef-altitud" type="number" step="0.01" value="${f.altitud_msnm != null ? f.altitud_msnm : ''}" /></label>
      <label class="field"><span>Vereda</span><input id="ef-vereda" value="${esc(f.vereda || '')}" /></label>
      <label class="field"><span>Latitud</span><input id="ef-lat" type="number" step="0.000001" min="-90" max="90" value="${f.latitud != null ? f.latitud : ''}" /></label>
      <label class="field"><span>Longitud</span><input id="ef-lng" type="number" step="0.000001" min="-180" max="180" value="${f.longitud != null ? f.longitud : ''}" /></label>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  const guardar = document.getElementById('modal-guardar');
  guardar.onclick = () => guardarEdicionFinca(id);
}

async function guardarEdicionFinca(id) {
  const msg = document.getElementById('modal-msg');
  const num = (v) => v === '' ? null : Number(v);
  const body = {
    nombre: document.getElementById('ef-nombre').value.trim(),
    departamento: document.getElementById('ef-departamento').value.trim(),
    municipio: document.getElementById('ef-municipio').value.trim(),
    propietario: document.getElementById('ef-propietario').value.trim(),
    contacto_telefono: document.getElementById('ef-telefono').value.trim(),
    contacto_email: document.getElementById('ef-email').value.trim() || null,
    area_hectareas: num(document.getElementById('ef-area').value),
    altitud_msnm: num(document.getElementById('ef-altitud').value),
    vereda: document.getElementById('ef-vereda').value.trim() || null,
    latitud: num(document.getElementById('ef-lat').value),
    longitud: num(document.getElementById('ef-lng').value),
  };
  try {
    const r = await api(`/fincas/${id}`, { method: 'PUT', headers: headers(), body: JSON.stringify(body) });
    msg.innerHTML = okBanner(`Finca <b>${esc(r.finca.nombre)}</b> actualizada.`);
    await cargarFincas();
    renderFincasList();
    setTimeout(() => document.getElementById('modal-editor').classList.add('hidden'), 900);
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
  }
}

async function eliminarFinca(id, nombre) {
  if (!confirm(`¿Eliminar la finca «${nombre}»?\n\nSe eliminarán también sus lotes, lecturas de sensores, dispositivos, recomendaciones y chat. Esta acción NO se puede deshacer.`)) return;
  try {
    const r = await api(`/fincas/${id}`, { method: 'DELETE', headers: headers() });
    alert(`Finca «${nombre}» eliminada.\nLecturas: ${r.detalle.lecturas} · Dispositivos: ${r.detalle.dispositivos} · Recomendaciones: ${r.detalle.recomendaciones}.`);
    await cargarFincas();
    renderFincasList();
    await cargarUsuarios();
  } catch (e) {
    alert('No se pudo eliminar: ' + e.message);
  }
}

/* ────────────────────── lotes: listar, crear, editar, eliminar ────────────────────── */

async function toggleLotes(fincaId) {
  const panel = document.getElementById('lotes-' + fincaId);
  if (!panel) return;
  if (!panel.classList.contains('hidden')) {
    panel.classList.add('hidden');
    return;
  }
  panel.innerHTML = '<p class="muted">Cargando lotes…</p>';
  panel.classList.remove('hidden');
  const r = await api(`/fincas/${fincaId}/lotes`);
  renderLotes(fincaId, r.data || []);
}

function renderLotes(fincaId, lotes) {
  const panel = document.getElementById('lotes-' + fincaId);
  if (!panel) return;
  const fila = (l) => `
    <div class="lote-row">
      <div class="lote-info">
        <b>🗂️ ${esc(l.nombre)}</b>
        <span class="muted">${l.area_ha != null ? l.area_ha + ' ha' : 'área sin dato'}</span>
        ${l.profundidad_suelo_cm != null ? `<span class="muted">prof. ${l.profundidad_suelo_cm} cm</span>` : ''}
        ${l.pedregosidad ? `<span class="muted">pedregosidad: ${esc(l.pedregosidad)}</span>` : ''}
        ${l.fecha_siembra ? `<span class="muted">🌱 siembra ${esc(l.fecha_siembra)}</span>` : ''}
        ${l.variedad ? `<span class="muted">variedad: ${esc(l.variedad)}</span>` : ''}
      </div>
      <div class="device-actions">
        <button class="btn btn-ghost" data-lote-ciclos="${esc(l.id)}">🔄 Ciclos</button>
        <button class="btn btn-ghost" data-lote-editar="${esc(l.id)}" data-nombre="${esc(l.nombre)}">✏️</button>
        <button class="btn btn-ghost btn-danger" data-lote-eliminar="${esc(l.id)}" data-nombre="${esc(l.nombre)}">🗑️</button>
      </div>
    </div>
    <div class="ciclos-panel hidden" id="ciclos-${esc(l.id)}"></div>`;
  panel.innerHTML = `
    ${lotes.length ? lotes.map(fila).join('') : '<p class="muted">Esta finca aún no tiene lotes activos.</p>'}
    <details class="lote-nuevo">
      <summary>➕ Agregar lote (cada lote puede tener características diferentes)</summary>
      <div class="form-grid">
        <label class="field"><span>Nombre del lote *</span><input id="ln-nombre" placeholder="Ej. Lote La Vega" required /></label>
        <label class="field"><span>Área (ha)</span><input id="ln-area" type="number" min="0" step="0.01" /></label>
        <label class="field"><span>Profundidad de suelo (cm)</span>
          <select id="ln-prof">
            <option value="">—</option>
            <option value="25">25 cm (somero)</option>
            <option value="45">45 cm</option>
            <option value="75">75 cm</option>
            <option value="100">100 cm (profundo)</option>
          </select>
        </label>
        <label class="field"><span>Pedregosidad</span>
          <select id="ln-pedregosidad">
            <option value="">—</option>
            <option value="Ninguna">Ninguna</option>
            <option value="Moderada">Moderada</option>
            <option value="Alta">Alta</option>
          </select>
        </label>
        <button type="button" class="btn btn-primary" id="ln-guardar">💾 Guardar lote</button>
      </div>
      <div id="ln-msg"></div>
    </details>`;
  panel.querySelectorAll('[data-lote-ciclos]').forEach(b => {
    b.addEventListener('click', () => toggleCiclos(fincaId, b.dataset.loteCiclos));
  });
  panel.querySelectorAll('[data-lote-editar]').forEach(b => {
    b.addEventListener('click', () => abrirEditarLote(fincaId, b.dataset.loteEditar, lotes.find(l => l.id === b.dataset.loteEditar)));
  });
  panel.querySelectorAll('[data-lote-eliminar]').forEach(b => {
    b.addEventListener('click', () => eliminarLote(fincaId, b.dataset.loteEliminar, b.dataset.nombre || ''));
  });
  document.getElementById('ln-guardar').addEventListener('click', () => crearLote(fincaId));
}

async function crearLote(fincaId) {
  const msg = document.getElementById('ln-msg');
  const num = (v) => v === '' ? null : Number(v);
  const sel = (id) => document.getElementById(id).value || null;
  const body = {
    nombre: document.getElementById('ln-nombre').value.trim(),
    area_ha: num(document.getElementById('ln-area').value),
    profundidad_suelo_cm: sel('ln-prof') ? Number(sel('ln-prof')) : null,
    pedregosidad: sel('ln-pedregosidad'),
  };
  if (!body.nombre) { msg.innerHTML = errorBanner('Indique el nombre del lote.'); return; }
  try {
    const r = await api(`/fincas/${fincaId}/lotes`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
    msg.innerHTML = okBanner(`Lote <b>${esc(r.lote.nombre)}</b> creado.`);
    await cargarFincas();
    const panel = document.getElementById('lotes-' + fincaId);
    const lr = await api(`/fincas/${fincaId}/lotes`);
    renderLotes(fincaId, lr.data || []);
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
  }
}

function abrirEditarLote(fincaId, loteId, lote) {
  if (!lote) return;
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `✏️ Editar lote — ${lote.nombre}`;
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="form-grid">
      <label class="field"><span>Nombre *</span><input id="el-nombre" value="${esc(lote.nombre)}" required /></label>
      <label class="field"><span>Área (ha)</span><input id="el-area" type="number" min="0" step="0.01" value="${lote.area_ha != null ? lote.area_ha : ''}" /></label>
      <label class="field"><span>Profundidad de suelo (cm)</span>
        <select id="el-prof">
          <option value="">—</option>
          ${[25, 45, 75, 100].map(p => `<option value="${p}" ${lote.profundidad_suelo_cm === p ? 'selected' : ''}>${p} cm</option>`).join('')}
        </select>
      </label>
      <label class="field"><span>Pedregosidad</span>
        <select id="el-pedregosidad">
          <option value="">—</option>
          ${['Ninguna', 'Moderada', 'Alta'].map(p => `<option value="${p}" ${lote.pedregosidad === p ? 'selected' : ''}>${p}</option>`).join('')}
        </select>
      </label>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = () => guardarEdicionLote(fincaId, loteId);
}

async function guardarEdicionLote(fincaId, loteId) {
  const msg = document.getElementById('modal-msg');
  const num = (v) => v === '' ? null : Number(v);
  const prof = document.getElementById('el-prof').value;
  const body = {
    nombre: document.getElementById('el-nombre').value.trim(),
    area_ha: num(document.getElementById('el-area').value),
    profundidad_suelo_cm: prof ? Number(prof) : null,
    pedregosidad: document.getElementById('el-pedregosidad').value || null,
  };
  try {
    const r = await api(`/fincas/${fincaId}/lotes/${loteId}`, { method: 'PATCH', headers: headers(), body: JSON.stringify(body) });
    msg.innerHTML = okBanner(`Lote <b>${esc(r.lote.nombre)}</b> actualizado.`);
    const lr = await api(`/fincas/${fincaId}/lotes`);
    renderLotes(fincaId, lr.data || []);
    setTimeout(() => document.getElementById('modal-editor').classList.add('hidden'), 900);
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
  }
}

async function eliminarLote(fincaId, loteId, nombre) {
  if (!confirm(`¿Eliminar el lote «${nombre}»? Su registro quedará en auditoría.`)) return;
  try {
    await api(`/fincas/${fincaId}/lotes/${loteId}`, { method: 'DELETE', headers: headers() });
    const lr = await api(`/fincas/${fincaId}/lotes`);
    renderLotes(fincaId, lr.data || []);
  } catch (e) {
    alert('No se pudo eliminar: ' + e.message);
  }
}

/* ────────────────────── ciclos productivos por lote ────────────────────── */

const OPCIONES_CULTIVOS = () => (state.cultivos || []).map(c =>
  `<option value="${esc(c.id)}">${esc(c.nombre)}</option>`).join('');

async function toggleCiclos(fincaId, loteId) {
  const panel = document.getElementById('ciclos-' + loteId);
  if (!panel) return;
  if (!panel.classList.contains('hidden')) {
    panel.classList.add('hidden');
    return;
  }
  panel.innerHTML = '<p class="muted">Cargando ciclos…</p>';
  panel.classList.remove('hidden');
  const r = await api(`/fincas/${fincaId}/lotes/${loteId}/ciclos`);
  renderCiclos(fincaId, loteId, r.data || []);
}

function renderCiclos(fincaId, loteId, ciclos) {
  const panel = document.getElementById('ciclos-' + loteId);
  if (!panel) return;
  const fila = (c) => `
    <div class="ciclo-row">
      <div class="ciclo-info">
        <b>🌱 ${esc(c.cultivo_nombre || 'Cultivo')}</b>
        <span class="muted">${esc(c.fecha_siembra || '?')}${c.fecha_cosecha ? ' → ' + esc(c.fecha_cosecha) : ' (sin cosechar)'}</span>
        ${c.rendimiento_tn_ha != null ? `<span class="muted">rinde ${c.rendimiento_tn_ha} t/ha</span>` : ''}
        ${c.calidad_cosecha ? badge(c.calidad_cosecha, c.calidad_cosecha === 'Premium' ? 'ok' : c.calidad_cosecha === 'Rechazo' ? 'critical' : 'warning') : ''}
        ${c.practicas_riego ? `<span class="muted">riego: ${esc(c.practicas_riego)}</span>` : ''}
        ${(c.aplicaciones || []).length ? `<span class="muted">🧪 ${c.aplicaciones.length} aplicación(es)</span>` : ''}
        ${(c.incidencias || []).length ? `<span class="muted">🐛 ${c.incidencias.length} incidencia(s)</span>` : ''}
        ${c.observaciones ? `<span class="muted">📝 ${esc(c.observaciones)}</span>` : ''}
      </div>
      <div class="device-actions">
        <button class="btn btn-ghost" data-ciclo-editar="${esc(c.id)}">✏️</button>
        <button class="btn btn-ghost btn-danger" data-ciclo-eliminar="${esc(c.id)}">🗑️</button>
      </div>
    </div>`;
  panel.innerHTML = `
    ${ciclos.length ? ciclos.map(fila).join('') : '<p class="muted">Este lote aún no tiene ciclos registrados.</p>'}
    <details class="lote-nuevo">
      <summary>➕ Registrar ciclo productivo (siembra → cosecha)</summary>
      <div class="form-grid">
        <label class="field"><span>Cultivo *</span>
          <select id="cic-cultivo-${esc(loteId)}"><option value="">— Seleccione —</option>${OPCIONES_CULTIVOS()}</select>
        </label>
        <label class="field"><span>Fecha de siembra *</span><input id="cic-siembra-${esc(loteId)}" type="date" required /></label>
        <label class="field"><span>Fecha de cosecha</span><input id="cic-cosecha-${esc(loteId)}" type="date" /></label>
        <label class="field"><span>Rendimiento (t/ha)</span><input id="cic-rend-${esc(loteId)}" type="number" min="0" step="0.01" /></label>
        <label class="field"><span>Calidad de cosecha</span>
          <select id="cic-calidad-${esc(loteId)}">
            <option value="">—</option>
            <option value="Premium">Premium</option>
            <option value="Estándar">Estándar</option>
            <option value="Rechazo">Rechazo</option>
          </select>
        </label>
        <label class="field"><span>Prácticas de riego</span>
          <select id="cic-riego-${esc(loteId)}">
            <option value="">—</option>
            <option value="Goteo">Goteo</option>
            <option value="Gravedad">Gravedad</option>
            <option value="Aspersión">Aspersión</option>
            <option value="Secano">Secano</option>
          </select>
        </label>
        <label class="field"><span>Aplicaciones (JSON opcional)</span>
          <textarea id="cic-aplic-${esc(loteId)}" rows="3" placeholder='[{"producto":"Urea","dosis_kg_ha":150,"fecha":"2026-01-15","tipo":"Fertilizante"}]'></textarea>
        </label>
        <label class="field"><span>Incidencias (JSON opcional)</span>
          <textarea id="cic-incid-${esc(loteId)}" rows="3" placeholder='[{"plaga":"Roya","severidad":"Alta","fecha":"2026-02-10","control":"Fungicida"}]'></textarea>
        </label>
        <label class="field"><span>Observaciones</span><input id="cic-obs-${esc(loteId)}" maxlength="4000" /></label>
        <button type="button" class="btn btn-primary" id="cic-guardar-${esc(loteId)}">💾 Guardar ciclo</button>
      </div>
      <div id="cic-msg-${esc(loteId)}"></div>
    </details>`;
  panel.querySelectorAll('[data-ciclo-editar]').forEach(b => {
    b.addEventListener('click', () => abrirEditarCiclo(fincaId, loteId, ciclos.find(c => c.id === b.dataset.cicloEditar)));
  });
  panel.querySelectorAll('[data-ciclo-eliminar]').forEach(b => {
    b.addEventListener('click', () => eliminarCiclo(fincaId, loteId, b.dataset.cicloEliminar));
  });
  document.getElementById('cic-guardar-' + loteId).addEventListener('click', () => crearCiclo(fincaId, loteId));
}

function _parseJsonOpcional(texto, etiqueta) {
  const t = (texto || '').trim();
  if (!t) return null;
  try {
    const v = JSON.parse(t);
    if (!Array.isArray(v)) throw new Error('no es un arreglo');
    return v;
  } catch {
    throw new Error(`${etiqueta} debe ser un JSON válido tipo arreglo (o vacío).`);
  }
}

async function crearCiclo(fincaId, loteId) {
  const msg = document.getElementById('cic-msg-' + loteId);
  const el = (id) => document.getElementById('cic-' + id + '-' + loteId);
  try {
    const body = {
      cultivo_id: el('cultivo').value,
      fecha_siembra: el('siembra').value,
      fecha_cosecha: el('cosecha').value || null,
      rendimiento_tn_ha: el('rend').value ? Number(el('rend').value) : null,
      calidad_cosecha: el('calidad').value || null,
      practicas_riego: el('riego').value || null,
      aplicaciones: _parseJsonOpcional(el('aplic').value, 'Aplicaciones'),
      incidencias: _parseJsonOpcional(el('incid').value, 'Incidencias'),
      observaciones: el('obs').value.trim() || null,
    };
    if (!body.cultivo_id || !body.fecha_siembra) {
      msg.innerHTML = errorBanner('Seleccione el cultivo y la fecha de siembra (obligatorios).');
      return;
    }
    msg.innerHTML = '<div class="ok-banner">⏳ Guardando ciclo…</div>';
    const r = await api(`/fincas/${fincaId}/lotes/${loteId}/ciclos`, {
      method: 'POST', headers: headers(), body: JSON.stringify(body),
    });
    msg.innerHTML = okBanner(`Ciclo de <b>${esc(r.ciclo.cultivo_nombre || 'cultivo')}</b> registrado (siembra ${esc(r.ciclo.fecha_siembra)}).`);
    const lr = await api(`/fincas/${fincaId}/lotes/${loteId}/ciclos`);
    renderCiclos(fincaId, loteId, lr.data || []);
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
  }
}

function abrirEditarCiclo(fincaId, loteId, ciclo) {
  if (!ciclo) return;
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `✏️ Editar ciclo — ${ciclo.cultivo_nombre || ''} (${ciclo.fecha_siembra})`;
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="form-grid">
      <label class="field"><span>Cultivo *</span>
        <select id="ec-cultivo"><option value="">— Seleccione —</option>
          ${(state.cultivos || []).map(c => `<option value="${esc(c.id)}" ${c.id === ciclo.cultivo_id ? 'selected' : ''}>${esc(c.nombre)}</option>`).join('')}
        </select>
      </label>
      <label class="field"><span>Fecha de siembra *</span><input id="ec-siembra" type="date" value="${esc(ciclo.fecha_siembra || '')}" required /></label>
      <label class="field"><span>Fecha de cosecha</span><input id="ec-cosecha" type="date" value="${esc(ciclo.fecha_cosecha || '')}" /></label>
      <label class="field"><span>Rendimiento (t/ha)</span><input id="ec-rend" type="number" min="0" step="0.01" value="${ciclo.rendimiento_tn_ha != null ? ciclo.rendimiento_tn_ha : ''}" /></label>
      <label class="field"><span>Calidad de cosecha</span>
        <select id="ec-calidad">
          <option value="">—</option>
          ${['Premium', 'Estándar', 'Rechazo'].map(q => `<option value="${q}" ${ciclo.calidad_cosecha === q ? 'selected' : ''}>${q}</option>`).join('')}
        </select>
      </label>
      <label class="field"><span>Prácticas de riego</span>
        <select id="ec-riego">
          <option value="">—</option>
          ${['Goteo', 'Gravedad', 'Aspersión', 'Secano'].map(q => `<option value="${q}" ${ciclo.practicas_riego === q ? 'selected' : ''}>${q}</option>`).join('')}
        </select>
      </label>
      <label class="field"><span>Aplicaciones (JSON)</span>
        <textarea id="ec-aplic" rows="3">${esc(JSON.stringify(ciclo.aplicaciones || []))}</textarea>
      </label>
      <label class="field"><span>Incidencias (JSON)</span>
        <textarea id="ec-incid" rows="3">${esc(JSON.stringify(ciclo.incidencias || []))}</textarea>
      </label>
      <label class="field"><span>Observaciones</span><input id="ec-obs" maxlength="4000" value="${esc(ciclo.observaciones || '')}" /></label>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = () => guardarEdicionCiclo(fincaId, loteId, ciclo.id);
}

async function guardarEdicionCiclo(fincaId, loteId, cicloId) {
  const msg = document.getElementById('modal-msg');
  const el = (id) => document.getElementById('ec-' + id);
  try {
    const body = {
      cultivo_id: el('cultivo').value || null,
      fecha_siembra: el('siembra').value || null,
      fecha_cosecha: el('cosecha').value || null,
      rendimiento_tn_ha: el('rend').value ? Number(el('rend').value) : null,
      calidad_cosecha: el('calidad').value || null,
      practicas_riego: el('riego').value || null,
      aplicaciones: _parseJsonOpcional(el('aplic').value, 'Aplicaciones'),
      incidencias: _parseJsonOpcional(el('incid').value, 'Incidencias'),
      observaciones: el('obs').value.trim() || null,
    };
    const r = await api(`/fincas/${fincaId}/lotes/${loteId}/ciclos/${cicloId}`, {
      method: 'PATCH', headers: headers(), body: JSON.stringify(body),
    });
    msg.innerHTML = okBanner(`Ciclo actualizado (siembra ${esc(r.ciclo.fecha_siembra)}).`);
    const lr = await api(`/fincas/${fincaId}/lotes/${loteId}/ciclos`);
    renderCiclos(fincaId, loteId, lr.data || []);
    setTimeout(() => document.getElementById('modal-editor').classList.add('hidden'), 900);
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
  }
}

async function eliminarCiclo(fincaId, loteId, cicloId) {
  if (!confirm('¿Eliminar este ciclo del historial del lote? La acción quedará en auditoría.')) return;
  try {
    await api(`/fincas/${fincaId}/lotes/${loteId}/ciclos/${cicloId}`, { method: 'DELETE', headers: headers() });
    const lr = await api(`/fincas/${fincaId}/lotes/${loteId}/ciclos`);
    renderCiclos(fincaId, loteId, lr.data || []);
  } catch (e) {
    alert('No se pudo eliminar: ' + e.message);
  }
}

/* ────────────────────── flujo rápido: iniciar ciclo (Recomendaciones) ────────────────────── */

function abrirModalIniciarCiclo() {
  const fincaId = document.getElementById('reco-finca').value;
  if (!fincaId) {
    alert('Seleccione primero la finca en Recomendaciones.');
    return;
  }
  const cultivoPresel = document.getElementById('reco-cultivo').value;
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = '🌱 Registrar nuevo ciclo';
  document.getElementById('modal-cuerpo').innerHTML = `
    <p class="muted">
      Se crea el ciclo en el historial del lote y se actualiza automáticamente el
      cultivo sembrado y la fecha de siembra de la finca para el análisis actual.
    </p>
    <div class="form-grid">
      <label class="field"><span>Cultivo *</span>
        <select id="ic-cultivo">
          <option value="">— Seleccione —</option>
          ${(state.cultivos || []).map(c => `<option value="${esc(c.id)}" ${c.id === cultivoPresel ? 'selected' : ''}>${esc(c.nombre)}</option>`).join('')}
        </select>
      </label>
      <label class="field"><span>Fecha de siembra *</span><input id="ic-siembra" type="date" required /></label>
      <label class="field"><span>Variedad (opcional)</span><input id="ic-variedad" maxlength="100" placeholder="Ej. Castillo, Caturra…" /></label>
      <label class="field"><span>Densidad de siembra (plantas/ha, opcional)</span><input id="ic-densidad" type="number" min="0" step="1" placeholder="Ej. 5000" /></label>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = () => iniciarCiclo(fincaId);
}

async function iniciarCiclo(fincaId) {
  const msg = document.getElementById('modal-msg');
  const cultivoId = document.getElementById('ic-cultivo').value;
  const fechaSiembra = document.getElementById('ic-siembra').value;
  const variedad = document.getElementById('ic-variedad').value.trim() || null;
  const densidad = document.getElementById('ic-densidad').value
    ? Number(document.getElementById('ic-densidad').value) : null;
  if (!cultivoId || !fechaSiembra) {
    msg.innerHTML = errorBanner('Seleccione el cultivo y la fecha de siembra (obligatorios).');
    return;
  }
  try {
    msg.innerHTML = '<div class="ok-banner">⏳ Registrando ciclo…</div>';
    const r = await api(`/fincas/${fincaId}/ciclo/iniciar`, {
      method: 'POST', headers: headers(),
      body: JSON.stringify({
        cultivo_id: cultivoId, fecha_siembra: fechaSiembra,
        variedad: variedad, densidad_siembra_plantas_ha: densidad,
      }),
    });
    msg.innerHTML = okBanner(
      `Ciclo de <b>${esc(r.ciclo.cultivo_nombre)}</b> registrado (siembra ${esc(r.ciclo.fecha_siembra)}).` +
      `<br><span class="muted">Finca actualizada: cultivo sembrado «${esc(r.finca.cultivo_sembrado)}» · lote «${esc(r.lote.nombre)}» con fecha de siembra.</span>`
    );
    // Actualizar el selector de cultivo de Recomendaciones con el nuevo cultivo
    document.getElementById('reco-cultivo').value = cultivoId;
    await cargarFincas();
    setTimeout(() => cerrarModal(), 1400);
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
  }
}

/* ────────────────────── cierre del ciclo: cosechar (Dashboard P1) ────────────────────── */

async function renderCicloActivo() {
  const div = document.getElementById('dashboard-ciclo');
  if (!div || !state.fincaId) return;
  div.innerHTML = '';
  try {
    const r = await api(`/fincas/${state.fincaId}/ciclo/activo`);
    if (!r.data) return;
    const c = r.data.ciclo;
    const rol = state.rol.toLowerCase();
    const boton = (rol === 'admin' || rol === 'agronomo')
      ? `<button type="button" class="btn" id="btn-cosechar">✏️ Cosechar ciclo</button>` : '';
    div.innerHTML = `
      <div class="ciclo-activo">
        <div class="ciclo-activo-info">
          <b>🔄 Ciclo activo:</b> 🌱 ${esc(c.cultivo_nombre || 'Cultivo')}
          <span class="muted">siembra ${esc(c.fecha_siembra || '?')}</span>
          ${c.variedad ? `<span class="muted">variedad ${esc(c.variedad)}</span>` : ''}
          <span class="muted">lote: ${esc(r.data.lote.nombre || 'principal')}</span>
        </div>
        ${boton}
      </div>`;
    const btn = document.getElementById('btn-cosechar');
    if (btn) btn.addEventListener('click', () => abrirModalCosechar(c));
  } catch {
    /* sin ciclo activo o sin acceso: no se muestra nada */
  }
}

function abrirModalCosechar(ciclo) {
  const hoy = new Date().toISOString().slice(0, 10);
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `✏️ Cosechar ciclo — ${ciclo.cultivo_nombre || ''} (siembra ${ciclo.fecha_siembra || '?'})`;
  document.getElementById('modal-cuerpo').innerHTML = `
    <p class="muted">Cierre del ciclo: el rendimiento queda registrado y alimenta el ROI de ciclos futuros.</p>
    <div class="form-grid">
      <label class="field"><span>Fecha de cosecha *</span><input id="cc-fecha" type="date" value="${hoy}" required /></label>
      <label class="field"><span>Rendimiento * (obligatorio para el ROI)</span>
        <div class="form-grid" style="grid-template-columns: 1fr 120px">
          <input id="cc-rend" type="number" min="0.01" step="0.01" placeholder="Ej. 4.5" required />
          <select id="cc-unidad">
            <option value="t_ha">t/ha</option>
            <option value="kg_ha">kg/ha</option>
          </select>
        </div>
      </label>
      <label class="field"><span>Calidad de cosecha (opcional)</span>
        <select id="cc-calidad">
          <option value="">—</option>
          <option value="Premium">Premium</option>
          <option value="Estándar">Estándar</option>
          <option value="Rechazo">Rechazo</option>
        </select>
      </label>
      <label class="field" style="grid-column: 1 / -1"><span>Resumen de aplicaciones (opcional)</span>
        <textarea id="cc-aplic" rows="3" placeholder="Pegue las dosis aplicadas, ej. Urea 150kg, DAP 80kg"></textarea>
        <input type="file" id="cc-csv" accept=".csv,text/csv" class="csv-input"
               title="O cargue un CSV pequeño con las dosis (Producto,Dosis,Unidad)" />
      </label>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  // CSV pequeño: parsea «Producto,Dosis,Unidad» y lo agrega al textarea
  document.getElementById('cc-csv').addEventListener('change', e => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      const lineas = String(reader.result).split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      const parsed = [];
      for (const l of lineas) {
        const cols = l.split(/[;,]/).map(x => x.trim());
        if (cols.length >= 2 && /\d/.test(cols[1])) {
          parsed.push(`${cols[0]} ${cols[1]}${cols[2] || 'kg'}`);
        } else if (l) {
          parsed.push(l);
        }
      }
      const ta = document.getElementById('cc-aplic');
      const actual = ta.value.trim();
      ta.value = (actual ? actual + ', ' : '') + parsed.join(', ');
      document.getElementById('modal-msg').innerHTML =
        okBanner(`CSV leído: ${parsed.length} aplicación(es) agregada(s) al resumen.`);
    };
    reader.readAsText(f);
  });
  document.getElementById('modal-guardar').onclick = () => cosecharCiclo();
}

async function cosecharCiclo() {
  const msg = document.getElementById('modal-msg');
  const fecha = document.getElementById('cc-fecha').value;
  const rend = Number(document.getElementById('cc-rend').value || 0);
  const unidad = document.getElementById('cc-unidad').value;
  const calidad = document.getElementById('cc-calidad').value || null;
  const aplic = document.getElementById('cc-aplic').value.trim() || null;
  if (!fecha || rend <= 0) {
    msg.innerHTML = errorBanner('Indique la fecha de cosecha y el rendimiento (obligatorio).');
    return;
  }
  try {
    msg.innerHTML = '<div class="ok-banner">⏳ Cerrando ciclo…</div>';
    const r = await api(`/fincas/${state.fincaId}/ciclo/cosechar`, {
      method: 'POST', headers: headers(),
      body: JSON.stringify({
        fecha_cosecha: fecha, rendimiento: rend, unidad_rendimiento: unidad,
        calidad_cosecha: calidad, resumen_aplicaciones: aplic,
      }),
    });
    const aplicaciones = (r.ciclo.aplicaciones || []).map(a => `${a.producto} ${a.dosis_kg_ha} ${a.unidad}`).join(', ');
    msg.innerHTML = okBanner(
      `Ciclo cosechado: rendimiento <b>${r.ciclo.rendimiento_tn_ha} t/ha</b>` +
      (r.ciclo.calidad_cosecha ? ` · calidad ${esc(r.ciclo.calidad_cosecha)}` : '') +
      (aplicaciones ? `<br><span class="muted">Aplicaciones registradas: ${esc(aplicaciones)}</span>` : '') +
      ((r.advertencias || []).length ? `<br>⚠️ ${esc(r.advertencias.join(' '))}` : '')
    );
    await cargarDashboard();
    if (state.tabActual === 'historial') await cargarHistorial();
    setTimeout(() => cerrarModal(), 1500);
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
  }
}

/* ────────────────────── labores / órdenes de trabajo (P1 widget) ────────────────────── */

const TIPO_LABOR_ICONO = {
  'Fertilización': '🧪', 'Enmienda': '🪨', 'Riego': '💧', 'Control Fitosanitario': '🛡️',
};

async function renderLaboresPendientes() {
  const div = document.getElementById('dashboard-labores');
  if (!div || !state.fincaId) return;
  div.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const r = await api(`/fincas/${state.fincaId}/labores/pendientes-hoy`);
    const labores = r.data || [];
    if (!labores.length) {
      div.innerHTML = '<p class="muted">Sin tareas pendientes. Genere órdenes de trabajo desde Recomendaciones.</p>';
      return;
    }
    const rol = state.rol.toLowerCase();
    const puedeGestionar = ['admin', 'administrador', 'agronomo', 'agrónomo'].includes(rol);
    div.innerHTML = labores.map(l => `
      <div class="labor-row">
        <div class="labor-info">
          <b>${TIPO_LABOR_ICONO[l.tipo] || '📋'} ${esc(l.tipo)}</b>
          <span>${esc(l.titulo)}</span>
          <span class="muted">programada ${esc(l.fecha_programada || '?')}</span>
          <span class="muted">${badge(l.estado, l.estado === 'Pendiente' ? 'warning' : 'ok')}</span>
        </div>
        ${puedeGestionar ? `
        <div class="device-actions">
          <button class="btn btn-ghost" data-labor-completar="${esc(l.id)}">✔️ Completar</button>
          <button class="btn btn-ghost" data-labor-cancelar="${esc(l.id)}">🚫 Cancelar</button>
        </div>` : ''}
      </div>`).join('');
    div.querySelectorAll('[data-labor-completar]').forEach(b => {
      b.addEventListener('click', () => actualizarLabor(b.dataset.laborCompletar, 'Completada'));
    });
    div.querySelectorAll('[data-labor-cancelar]').forEach(b => {
      b.addEventListener('click', () => actualizarLabor(b.dataset.laborCancelar, 'Cancelada'));
    });
  } catch {
    div.innerHTML = '<p class="muted">No se pudieron cargar las tareas pendientes.</p>';
  }
}

/* ────────────────────── alertas climáticas proactivas (P1) ────────────────────── */

const ICONOS_ALERTA = {
  lluvia_aplicacion: '⛅',
  helada_floracion: '🥶',
};

async function renderAlertasClimaticas() {
  const div = document.getElementById('dashboard-alertas');
  if (!div || !state.fincaId) return;
  div.innerHTML = '';
  try {
    const r = await api(`/fincas/${state.fincaId}/alertas-climaticas/activas`);
    const alertas = r.data || [];
    if (!alertas.length) return;
    div.innerHTML = alertas.map(a => `
      <div class="alerta-clima alerta-${esc(a.tipo)}">
        <span class="alerta-clima-ico">${ICONOS_ALERTA[a.tipo] || '⚠️'}</span>
        <div class="alerta-clima-cuerpo">
          <div class="alerta-clima-titulo">Alerta meteorológica · ${esc(a.severidad)}</div>
          <div class="alerta-clima-msg">${esc(a.mensaje)}</div>
        </div>
      </div>`).join('');
  } catch { /* sin alertas o error: no mostrar */ }
}

async function actualizarLabor(laborId, estado) {
  let observacion = null;
  if (estado === 'Completada') {
    if (!confirm('¿Marcar esta labor como completada? La fecha de ejecución se registrará con hoy.')) return;
    observacion = 'Aplicada según plan';
  } else if (estado === 'Cancelada') {
    if (!confirm('¿Cancelar esta orden de trabajo?')) return;
  }
  try {
    await api(`/labores/${laborId}`, {
      method: 'PATCH', headers: headers(),
      body: JSON.stringify({ estado, observaciones_ejecucion: observacion }),
    });
    await renderLaboresPendientes();
  } catch (e) {
    alert('No se pudo actualizar la labor: ' + e.message);
  }
}

/* ────────────────────── edición/eliminación de usuarios (admin) ────────────────────── */

function abrirEditarUsuario(u) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `✏️ Editar usuario — ${u.nombre}`;
  const fincasChk = state.fincas.map(f => {
    const marcada = (u.fincas || []).some(x => x.id === f.id);
    return `<label><input type="checkbox" class="eu-finca" value="${esc(f.id)}" ${marcada ? 'checked' : ''} /> ${esc(f.nombre)}</label>`;
  }).join('');
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="form-grid">
      <label class="field"><span>Nombre *</span><input id="eu-nombre" value="${esc(u.nombre)}" required /></label>
      <label class="field"><span>Email *</span><input id="eu-email" type="email" value="${esc(u.email)}" required /></label>
      <label class="field"><span>Rol</span>
        <select id="eu-rol">
          ${['Admin', 'Agronomo', 'Cliente', 'Tecnico', 'Investigador'].map(r => `<option value="${r}" ${u.rol === r ? 'selected' : ''}>${r}</option>`).join('')}
        </select>
      </label>
      <label class="field"><span>Estado</span>
        <select id="eu-activo">
          <option value="true" ${u.activo ? 'selected' : ''}>Activo</option>
          <option value="false" ${!u.activo ? 'selected' : ''}>Inactivo</option>
        </select>
      </label>
      <div class="field" style="grid-column: 1 / -1">
        <span>Fincas a las que tendrá acceso</span>
        <div class="eu-fincas">${fincasChk || '<span class="muted">No hay fincas.</span>'}</div>
      </div>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = () => guardarEdicionUsuario(u.id);
}

async function guardarEdicionUsuario(id) {
  const msg = document.getElementById('modal-msg');
  const body = {
    nombre: document.getElementById('eu-nombre').value.trim(),
    email: document.getElementById('eu-email').value.trim(),
    rol: document.getElementById('eu-rol').value,
    activo: document.getElementById('eu-activo').value === 'true',
    finca_ids: Array.from(document.querySelectorAll('.eu-finca:checked')).map(cb => cb.value),
  };
  try {
    const r = await api(`/usuarios/${id}`, { method: 'PUT', headers: headers(), body: JSON.stringify(body) });
    msg.innerHTML = okBanner(`Usuario <b>${esc(r.email)}</b> actualizado (${esc(r.rol)}).`);
    await cargarUsuarios();
    setTimeout(() => document.getElementById('modal-editor').classList.add('hidden'), 900);
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
  }
}

async function eliminarUsuario(u) {
  if (!confirm(`¿Desactivar la cuenta de «${u.nombre}» (${u.email})?\n\nNo podrá iniciar sesión. El registro queda en auditoría.`)) return;
  try {
    await api(`/usuarios/${u.id}`, { method: 'DELETE', headers: headers() });
    alert(`Usuario «${u.nombre}» desactivado.`);
    await cargarUsuarios();
  } catch (e) {
    alert('No se pudo desactivar: ' + e.message);
  }
}

/* ────────────────────── auditoría (solo admin) ────────────────────── */

const auditState = { page: 1, totalPages: 0 };

async function cargarAuditoria(pagina = 1) {
  const div = document.getElementById('auditoria-lista');
  const entidad = document.getElementById('audit-entidad').value;
  const q = document.getElementById('audit-busqueda').value.trim();
  const params = new URLSearchParams({ page: String(pagina), page_size: '15' });
  if (entidad) params.set('entidad', entidad);
  if (q) params.set('search', q);
  div.innerHTML = '<p class="muted">Cargando auditoría…</p>';
  try {
    const r = await api('/auditoria?' + params.toString());
    auditState.page = r.meta.page;
    auditState.totalPages = r.meta.total_pages;
    renderAuditoria(r.data || [], r.meta);
  } catch (e) {
    div.innerHTML = errorBanner(e.message);
  }
}

function renderAuditoria(filas, meta) {
  const div = document.getElementById('auditoria-lista');
  if (!filas.length) {
    div.innerHTML = '<p class="muted">Sin eventos registrados todavía.</p>';
    document.getElementById('audit-pagina').textContent = '';
    return;
  }
  const icono = {
    'auth.login': '🔐', 'finca.crear': '🏡', 'finca.actualizar': '✏️', 'finca.eliminar': '🗑️',
    'finca.agronomicos': '🧪', 'lote.crear': '🗂️', 'lote.actualizar': '✏️', 'lote.eliminar': '🗑️',
    'usuario.crear': '👥', 'usuario.actualizar': '✏️', 'usuario.eliminar': '🗑️', 'demo.reset': '🧹',
  };
  const detalleTxt = (d) => {
    if (!d || typeof d !== 'object') return '';
    const partes = [];
    if (d.nombre) partes.push(esc(d.nombre));
    if (d.finca) partes.push(esc(d.finca));
    if (d.campos && d.campos.length) partes.push('campos: ' + d.campos.join(', '));
    if (d.email) partes.push(esc(d.email));
    if (d.rol) partes.push(esc(d.rol));
    if (d.lecturas != null) partes.push(d.lecturas + ' lecturas');
    if (d.fincas_desvinculadas != null) partes.push(d.fincas_desvinculadas + ' fincas desvinculadas');
    return partes.join(' · ');
  };
  div.innerHTML = `
    <div class="tabla-audit-wrap">
      <table class="tabla-audit">
        <thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Detalle</th></tr></thead>
        <tbody>
          ${filas.map(a => `
            <tr>
              <td class="nowrap">${new Date(a.created_at).toLocaleString('es-CO')}</td>
              <td>${icono[a.accion] || '📌'} <b>${esc(a.usuario_nombre || a.usuario_email)}</b><br>
                  <span class="muted">${esc(a.usuario_email)} · ${esc(a.rol || '?')}</span></td>
              <td><code>${esc(a.accion)}</code><br><span class="muted">${esc(a.entidad)}${a.entidad_id ? ' · ' + a.entidad_id.slice(0, 8) : ''}</span></td>
              <td>${detalleTxt(a.detalle)}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
  document.getElementById('audit-pagina').textContent = `Página ${meta.page} de ${meta.total_pages} · ${meta.total} eventos`;
  document.getElementById('audit-anterior').disabled = meta.page <= 1;
  document.getElementById('audit-siguiente').disabled = meta.page >= meta.total_pages;
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

  // ── Características del lote: SIEMPRE obligatorias (aunque se registre
  //    la finca completa) — los parámetros del suelo y las dimensiones
  //    enriquecen el estudio. ──
  const profundidad = Number(document.getElementById('f-profundidad').value || 0);
  const pedregosidad = document.getElementById('f-pedregosidad').value.trim();
  const largo = Number(document.getElementById('f-largo').value || 0);
  const ancho = Number(document.getElementById('f-ancho').value || 0);
  if (!profundidad || !pedregosidad || largo <= 0 || ancho <= 0) {
    msg.innerHTML = errorBanner(
      'Complete las características del lote: profundidad efectiva del suelo, ' +
      'pedregosidad y dimensiones (largo × ancho). Estos datos enriquecen el ' +
      'estudio, incluso si registra toda la finca.'
    );
    return;
  }

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
    profundidad_suelo_cm: profundidad,
    pedregosidad: pedregosidad,
    largo_metros: largo,
    ancho_metros: ancho,
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
    renderCicloActivo();
    renderLaboresPendientes();
    renderAlertasClimaticas();
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

/* ─────────────────── carga masiva: historial de ciclos (CSV) ─────────────────── */

const PLANTILLA_CICLOS_CSV = [
  'lote,cultivo,fecha_siembra,fecha_cosecha,rendimiento,aplicaciones_texto',
  'Lote principal,Café,2021-04-10,2023-12-15,3.8,"Urea 150kg, DAP 80kg"',
  'Lote principal,Café,2024-03-01,2026-01-20,4.2,"KCl 100kg, Cal dolomítica 500kg"',
  'Lote La Vega,Plátano,2022-05-15,2023-08-30,12.5,"Urea 100kg"',
].join('\n');

function descargarPlantillaCiclos() {
  const blob = new Blob([PLANTILLA_CICLOS_CSV], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'historial_ciclos_ejemplo.csv';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
}

async function enviarCargaCiclos(e) {
  e.preventDefault();
  const out = document.getElementById('carga-ciclos-resultado');
  const fincaId = document.getElementById('carga-ciclos-finca').value;
  const file = document.getElementById('carga-ciclos-file').files[0];
  if (!fincaId) { out.innerHTML = errorBanner('Seleccione la finca para importar el historial.'); return; }
  if (!file) { out.innerHTML = errorBanner('Seleccione el archivo CSV del historial.'); return; }
  out.innerHTML = '<div class="ok-banner">⏳ Importando historial…</div>';
  try {
    const texto = await file.text();
    const r = await api(`/fincas/${fincaId}/ciclos/carga-csv`, {
      method: 'POST', headers: headers(), body: JSON.stringify({ csv_texto: texto }),
    });
    const erroresHtml = r.errores && r.errores.length
      ? `<div class="table-wrap" style="margin-top:10px"><table>
           <tr><th>Fila</th><th>Error</th></tr>
           ${r.errores.map(x => `<tr><td>${x.fila}</td><td>${esc(x.mensaje)}</td></tr>`).join('')}
         </table></div>`
      : '';
    out.innerHTML = `
      <div class="card">
        <h2>📥 Importación del historial de ciclos</h2>
        ${okBanner(
          `<b>${r.creados}</b> ciclo(s) importados de <b>${r.total_filas}</b> filas` +
          (r.lotes_creados ? ` · <b>${r.lotes_creados}</b> lote(s) creado(s)` : '') +
          (r.errores.length ? ` · ${r.errores.length} fila(s) con error` : '') + '.'
        )}
        ${erroresHtml}
      </div>`;
    await cargarFincas();
  } catch (err) {
    out.innerHTML = errorBanner(err.message);
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
  const presupuestoEl = document.getElementById('reco-presupuesto');
  const presupuesto = presupuestoEl && presupuestoEl.value ? Number(presupuestoEl.value) : null;
  const rendimientoEl = document.getElementById('reco-rendimiento');
  const rendimiento = rendimientoEl && rendimientoEl.value ? Number(rendimientoEl.value) : null;
  if (presupuesto != null) state.presupuesto = presupuesto; // solo sesión/memoria
  if (!finca) { out.innerHTML = errorBanner('Selecciona una finca.'); return; }
  out.innerHTML = '<div class="card"><p class="muted">⏳ Ejecutando motor de recomendaciones…</p></div>';
  try {
    const r = await api('/recomendaciones/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        finca_id: finca, cultivo_id: cultivo || null,
        presupuesto_cop: presupuesto, rendimiento_actual_t_ha: rendimiento,
      }),
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
      <button id="btn-generar-labores" onclick="generarLabores()">📋 Generar órdenes de trabajo</button>
      <span id="aceptar-estado" class="muted"></span>
    </div>
  </div>`;
}

async function generarLabores() {
  const a = state.ultimoAnalisis;
  const finca = document.getElementById('reco-finca').value;
  const estado = document.getElementById('aceptar-estado');
  const btn = document.getElementById('btn-generar-labores');
  if (!finca || !a) { if (estado) estado.textContent = 'Primero ejecute el análisis.'; return; }

  // Acciones de la tabla de diagnóstico (UC2) o ajustes del ranking (UC1)
  const acciones = (a.recomendaciones && a.recomendaciones.length)
    ? a.recomendaciones.map(r => ({ variable: r.variable, accion: r.accion }))
    : ((a.sugerencias_cultivos && a.sugerencias_cultivos[0] && a.sugerencias_cultivos[0].ajustes)
      ? a.sugerencias_cultivos[0].ajustes.map(r => ({ variable: r.variable, accion: r.accion }))
      : []);
  if (!acciones.length) {
    if (estado) estado.textContent = '⚠️ No hay acciones de diagnóstico que convertir en órdenes de trabajo.';
    return;
  }
  if (btn) btn.disabled = true;
  if (estado) estado.textContent = '⏳ Generando órdenes de trabajo…';
  try {
    const r = await api(`/fincas/${finca}/labores/generar`, {
      method: 'POST', headers: headers(), body: JSON.stringify({ acciones: acciones }),
    });
    if (estado) estado.textContent = `✅ ${r.creadas} orden(es) de trabajo creada(s). Revisa «Tareas pendientes» en el Inicio.`;
    if (btn) btn.textContent = '📋 Órdenes generadas';
    if (state.tabActual === 'inicio') await cargarDashboard();
  } catch (err) {
    if (estado) estado.textContent = err.message || 'No se pudieron generar las órdenes.';
    if (btn) btn.disabled = false;
  }
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

function fmtCOP(v) {
  if (v == null) return '—';
  const n = Number(v);
  return Number.isFinite(n) ? '$' + Math.round(n).toLocaleString('es-CO') : '—';
}

function renderPlanEconomico(pe) {
  if (!pe) return '';
  const dif = pe.diferencia_rendimiento_pct != null
    ? `<div><b>Diferencia de rendimiento estimada:</b> ${fmtNum(pe.diferencia_rendimiento_pct, 1)}%</div>` : '';
  const lisInc = (pe.incluidos || []).map(f =>
    `<li><b>${esc(f.variable)}</b> (${esc(f.prioridad || '—')}) — ${fmtCOP(f.costo_cop)}/ha</li>`).join('');
  const lisApl = (pe.aplazados || []).map(f =>
    `<li><b>${esc(f.variable)}</b> (${esc(f.prioridad || '—')}) — ${fmtCOP(f.costo_cop)}/ha · ${esc(f.motivo || '')}</li>`).join('');
  return `
  <div class="plan-eco">
    <h3>💰 Plan económico vs. plan ideal</h3>
    <p><b>Plan económico:</b> ${fmtCOP(pe.costo_plan)}/ha · <b>Plan ideal:</b> ${fmtCOP(pe.costo_ideal)}/ha ·
    presupuesto ${fmtCOP(pe.presupuesto_cop)}/ha · cobertura ${fmtNum(pe.cobertura_pct, 1)}%</p>
    ${dif}
    <div class="plan-eco-col">
      <div><b>✅ Incluidas (${(pe.incluidos || []).length}):</b><ul>${lisInc || '<li>Ninguna</li>'}</ul></div>
      <div><b>⏳ Aplazadas (${(pe.aplazados || []).length}):</b><ul>${lisApl || '<li>Ninguna</li>'}</ul></div>
    </div>
    <p class="muted">Las acciones de prioridad Crítica (pH, CE) siempre se incluyen. Los costos son estimaciones por hectárea.</p>
  </div>`;
}

/* ── Validador ML por variable (aprendizaje activo) ── */

function renderValidadorML(v) {
  if (!v) return '';
  const acuerdos = v.acuerdos || [];
  const desacuerdos = v.desacuerdos || [];
  const vars = (v.variables_promovidas || [])
    .map(x => ETIQUETAS_PARAM[x] || x).join(', ');
  let detalle = '';
  if (acuerdos.length) {
    detalle += `✅ Coincide con las reglas en ${acuerdos.length} variable(s)` +
      ` (${acuerdos.map(x => esc(x.variable)).join(', ')}) → confianza reforzada. `;
  }
  if (desacuerdos.length) {
    detalle += `🔀 Discrepa en ${desacuerdos.length} variable(s)` +
      ` (${desacuerdos.map(x => esc(x.variable)).join(', ')}) → prevalecen las reglas.`;
  }
  return `
    <div class="validador-ml">
      <b>🤖 Validador ML activo</b> (${esc(vars)}) — modelo promovido por
      aprendizaje activo con precisión real ≥ 85 %.
      <div class="muted" style="font-size:0.8rem;margin-top:3px">${detalle}</div>
    </div>`;
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
  if (a.variables_faltantes_esenciales && a.variables_faltantes_esenciales.length) {
    html += `
      <div class="completar-params">
        <h3>📝 Complete los parámetros esenciales</h3>
        <p class="muted">Para una recomendación más acertada, suministre los siguientes valores (medición de laboratorio o sensor). La recomendación actual <b>no tiene el 100% de certeza y requiere el aval de un agrónomo</b>.</p>
        <div class="params-fila">
          ${a.variables_faltantes_esenciales.map(v => `
            <label>${esc(ETIQUETAS_PARAM[v] || v)}
              <input id="completar-${esc(v)}" type="number" step="any" min="0" placeholder="${esc(ETIQUETAS_PARAM[v] || v)}">
            </label>`).join('')}
          <button type="button" class="btn btn-primary" onclick="completarParametros()">💾 Guardar y reanalizar</button>
        </div>
        <p id="completar-msg"></p>
      </div>`;
  }
  if (a.advertencia) html += `<div class="advertencia">${esc(a.advertencia)}</div>`;
  if (a.discordancia) html += `<div class="advertencia">🔀 Discordancia detectada: ${esc(JSON.stringify(a.discordancia))}</div>`;
  if (a.validacion_ml) html += renderValidadorML(a.validacion_ml);

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
      </table></div>
      ${renderPlanEconomico(a.plan_economico)}`;
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

/* ── Completar parámetros esenciales faltantes (aval de agrónomo) ── */

const ETIQUETAS_PARAM = {
  ph: 'pH (0-14)',
  nitrogeno: 'Nitrógeno (ppm)',
  fosforo: 'Fósforo (ppm)',
  potasio: 'Potasio (ppm)',
  conductividad_electrica: 'Conductividad eléctrica (µS/cm)',
};

async function completarParametros() {
  const a = state.ultimoAnalisis;
  const faltan = (a && a.variables_faltantes_esenciales) || [];
  const finca = document.getElementById('reco-finca').value;
  const msg = document.getElementById('completar-msg');
  const frame = {
    device_id: 'manual-' + String(finca).slice(0, 8) + '-params',
    finca_id: finca,
  };
  let completados = 0;
  for (const v of faltan) {
    const el = document.getElementById('completar-' + v);
    const val = el ? parseFloat(el.value) : NaN;
    if (!Number.isFinite(val)) continue;
    if (v === 'ph') frame.ph = val;
    else if (v === 'nitrogeno') frame.nitrogen = val;
    else if (v === 'fosforo') frame.phosphorus = val;
    else if (v === 'potasio') frame.potassium = val;
    else if (v === 'conductividad_electrica') frame.conductivity = val;
    completados += 1;
  }
  if (!completados) {
    if (msg) msg.innerHTML = errorBanner('Ingrese al menos un valor para guardar.');
    return;
  }
  try {
    await fetch('/api/sensor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-Role': state.rol },
      body: JSON.stringify(frame),
    });
    if (msg) msg.innerHTML = okBanner('Parámetros guardados. Reanalizando…');
    document.getElementById('form-analyze').requestSubmit();
  } catch (err) {
    if (msg) msg.innerHTML = errorBanner('No se pudieron guardar los parámetros: ' + err.message);
  }
}

/* ─────────────────────────── historial ─────────────────────────── */

async function cargarHistorial() {
  const div = document.getElementById('historial');
  if (!state.fincaId) {
    div.innerHTML = '<p class="muted">Selecciona una finca.</p>';
    return;
  }
  div.innerHTML = '<p class="muted">Cargando…</p>';
  await renderCicloActivoHistorial();
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

/* Ciclo activo también en Historial (P6): botón «✏️ Cosechar ciclo» */
async function renderCicloActivoHistorial() {
  const div = document.getElementById('historial-ciclo');
  if (!div || !state.fincaId) return;
  div.innerHTML = '';
  try {
    const r = await api(`/fincas/${state.fincaId}/ciclo/activo`);
    if (!r.data) return;
    const c = r.data.ciclo;
    const rol = state.rol.toLowerCase();
    const boton = (rol === 'admin' || rol === 'agronomo')
      ? '<button type="button" class="btn" id="btn-cosechar-hist">✏️ Cosechar ciclo</button>' : '';
    div.innerHTML = `
      <div class="ciclo-activo">
        <div class="ciclo-activo-info">
          <b>🔄 Ciclo activo:</b> 🌱 ${esc(c.cultivo_nombre || 'Cultivo')}
          <span class="muted">siembra ${esc(c.fecha_siembra || '?')}</span>
          ${c.variedad ? `<span class="muted">variedad ${esc(c.variedad)}</span>` : ''}
          <span class="muted">lote: ${esc((r.data.lote || {}).nombre || 'principal')}</span>
        </div>
        ${boton}
      </div>`;
    const b = document.getElementById('btn-cosechar-hist');
    if (b) b.addEventListener('click', () => abrirModalCosechar(c));
  } catch {
    /* sin ciclo activo: no se muestra nada */
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
      <h3>👤 ${esc(u.nombre)} ${badge(u.rol, u.rol === 'Admin' ? 'ok' : u.rol === 'Cliente' ? 'warning' : 'ok')}
        ${u.activo === false ? badge('Inactivo', 'critical') : ''}</h3>
      <div class="device-meta">
        <span>Email: <b>${esc(u.email)}</b></span>
        <span>Fincas: ${u.fincas && u.fincas.length
          ? u.fincas.map(f => esc(f.nombre)).join(', ')
          : '<span class="muted">ninguna</span>'}</span>
      </div>
      <div class="device-actions">
        <button type="button" class="btn btn-ghost" data-u-editar="${esc(u.id)}">✏️ Editar</button>
        <button type="button" class="btn btn-ghost btn-danger" data-u-eliminar="${esc(u.id)}">🗑️ Desactivar</button>
      </div>
    </div>`).join('');
  div.querySelectorAll('[data-u-editar]').forEach(b => {
    b.addEventListener('click', () => {
      const u = state.usuarios.find(x => x.id === b.dataset.uEditar);
      if (u) abrirEditarUsuario(u);
    });
  });
  div.querySelectorAll('[data-u-eliminar]').forEach(b => {
    b.addEventListener('click', () => {
      const u = state.usuarios.find(x => x.id === b.dataset.uEliminar);
      if (u) eliminarUsuario(u);
    });
  });
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
  const presEl = document.getElementById('repo-presupuesto');
  const rendEl = document.getElementById('repo-rendimiento');
  const presupuesto = presEl && presEl.value ? Number(presEl.value) : null;
  const rendimiento = rendEl && rendEl.value ? Number(rendEl.value) : null;

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
      body: JSON.stringify({
        finca_id: finca, tipo, cultivo_id: cultivo || null,
        presupuesto_cop: presupuesto, rendimiento_actual_t_ha: rendimiento,
      }),
    });
    reporteHtmlActual = r.html;
    state.ultimoReporte = r;
    const card = document.getElementById('reporte-preview-card');
    card.style.display = '';
    document.getElementById('reporte-iframe').srcdoc = r.html;
    prepararSimulacion(r, finca, cultivo);
    card.scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    document.getElementById('reporte-preview-card').style.display = 'none';
    alert('Error al generar el reporte: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '📄 Generar reporte';
  }
}

/* ── Simulación what-if (no toca la BD) ── */

let simFinca = null;
let simCultivo = null;
let simTimer = null;

function prepararSimulacion(r, finca, cultivo) {
  simFinca = finca;
  simCultivo = cultivo || null;
  const panel = document.getElementById('simular-panel');
  if (!panel) return;
  panel.style.display = '';
  // Valores iniciales desde el JSON embebido del reporte
  let suelo = {};
  try {
    const m = (r.html || '').match(/<script type="application\/json" id="datos-reporte">([\s\S]*?)<\/script>/);
    if (m) suelo = (JSON.parse(m[1]).soil) || {};
  } catch { /* sin datos: se usan valores por defecto */ }
  const presets = [
    ['ph', suelo.ph != null ? suelo.ph : 6, 'sim-ph'],
    ['nitrogeno', suelo.nitrogeno != null ? suelo.nitrogeno : 100, 'sim-n'],
    ['fosforo', suelo.fosforo != null ? suelo.fosforo : 50, 'sim-p'],
    ['potasio', suelo.potasio != null ? suelo.potasio : 150, 'sim-k'],
  ];
  for (const [_, val, id] of presets) {
    const input = document.getElementById(id);
    if (input) { input.value = val; actualizarSliderValor(id, val); }
  }
}

function actualizarSliderValor(id, val) {
  const label = document.getElementById(id + '-val');
  if (label) label.textContent = val;
}

function mapaSimulacion() {
  return {
    ph: parseFloat(document.getElementById('sim-ph').value),
    nitrogeno: parseFloat(document.getElementById('sim-n').value),
    fosforo: parseFloat(document.getElementById('sim-p').value),
    potasio: parseFloat(document.getElementById('sim-k').value),
  };
}

async function simularEnmienda() {
  if (!simFinca) return;
  const msg = document.getElementById('sim-msg');
  try {
    const r = await api('/reportes/simular', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({
        finca_id: simFinca,
        cultivo_id: simCultivo || null,
        soil_modificado: mapaSimulacion(),
      }),
    });
    msg.innerHTML =
      `Nueva clasificación: <b>${esc(r.clasificacion)}</b> · Confianza: <b>${Math.round(r.confianza * 100)}%</b>` +
      ` · Violaciones: ${r.violaciones} · Advertencias: ${r.advertencias}.` +
      (r.detalle && r.detalle.length
        ? `<br><span class="muted" style="font-size:.78rem">${r.detalle.slice(0, 4).map(d => esc(d.variable) + ' ' + esc(d.estado) + ' (' + esc(d.rango_ideal) + ')').join(' · ')}</span>`
        : ' · Sin violaciones con estos valores.');
  } catch (err) {
    msg.innerHTML = errorBanner('No se pudo simular: ' + err.message);
  }
}

function registrarSimulacion() {
  const panel = document.getElementById('simular-panel');
  if (!panel) return;
  panel.querySelectorAll('input[type="range"]').forEach(input => {
    input.addEventListener('input', () => {
      actualizarSliderValor(input.id, input.value);
      clearTimeout(simTimer);
      simTimer = setTimeout(simularEnmienda, 250);
    });
  });
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

const chatHistorial = {}; // finca_id → [{rol, contenido}] (imagen opcional)
let chatFincaActual = null;
let chatModo = null; // 'llm' | 'experto-local'
let chatMeta = null; // {confianza, fuentes} de la última respuesta
let chatImagen = null; // dataURL de la foto adjunta (o null)

function limpiarChatImagen() {
  chatImagen = null;
  const pv = document.getElementById('chat-preview');
  if (pv) pv.classList.add('hidden');
  const fi = document.getElementById('chat-imagen');
  if (fi) fi.value = '';
}

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
  div.innerHTML = hist.map(m => {
    const imgHtml = m.imagen
      ? `<img class="chat-img" src="${esc(m.imagen)}" alt="Foto adjunta del cultivo">`
      : '';
    return `<div class="chat-msg ${m.rol === 'user' ? 'chat-user' : 'chat-bot'}">${imgHtml}${esc(m.contenido)}</div>`;
  }).join('');
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
  if (!mensaje && !chatImagen) return;
  const mensajeFinal = mensaje || 'Mira esta foto de mi cultivo.';
  const imagenData = chatImagen; // dataURL o null

  btn.disabled = true;
  const hist = chatHistorial[fid] || (chatHistorial[fid] = []);
  hist.push({ rol: 'user', contenido: mensajeFinal, imagen: imagenData });
  input.value = '';
  limpiarChatImagen();
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
        mensaje: mensajeFinal,
        imagen_base64: imagenData ? imagenData.split(',')[1] : undefined,
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
    ? items.map(c => {
      const fisio = [
        c.profundidad_radicular_min_cm != null ? `raíz ≥ ${c.profundidad_radicular_min_cm} cm` : null,
        c.gdd_total_requerido != null ? `${c.gdd_total_requerido} GDD` : null,
        c.dias_ciclo != null ? `${c.dias_ciclo} días` : null,
      ].filter(Boolean);
      return `
      <div class="cultivo-card">
        <div class="icono">${esc(c.icono || '🌱')}</div>
        <h3>${esc(c.nombre)}</h3>
        ${c.nombre_cientifico ? `<p><i>${esc(c.nombre_cientifico)}</i></p>` : ''}
        ${c.descripcion ? `<p>${esc(c.descripcion)}</p>` : ''}
        ${fisio.length ? `<p class="muted mono">🌱 ${fisio.join(' · ')}</p>` : ''}
        ${c.activo === false ? badge('Inactivo', 'critical') : badge('Activo', 'ok')}
      </div>`;
    }).join('')
    : '<p class="muted">Sin resultados.</p>';
}

document.addEventListener('DOMContentLoaded', init);
