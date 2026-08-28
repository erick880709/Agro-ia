/* AgroIA — Frontend integrado (SPA vanilla).
 * Consume la API del backend en el mismo origen.
 */
'use strict';

const API = '/api/v1';
const SESION_KEY = 'agroia_sesion';

const TABS_POR_ROL = {
  admin: ['inicio', 'alertas', 'sensores', 'carga', 'recomendaciones', 'historial', 'reportes', 'fincas', 'reg-finca', 'usuarios', 'insumos', 'auditoria', 'bpa', 'equipo', 'comisiones', 'lista-trabajos', 'reentrenar', 'precios-cosecha', 'catalogo'],
  agronomo: ['inicio', 'alertas', 'sensores', 'carga', 'recomendaciones', 'historial', 'reportes', 'catalogo'],
  cliente: ['inicio', 'alertas', 'sensores', 'historial', 'reportes', 'catalogo'],
  extensionista: ['inicio', 'alertas', 'zona', 'sensores', 'historial', 'reportes', 'catalogo'],
};

const ICONOS_APROXIMADOS = {
  'custom:panela_v1': '🟫',       // bloque de panela (aproximado)
  'custom:chontaduro_v1': '🌴',   // palma de chontaduro (aproximado)
  'custom:lulo_v1': '🍊',         // cítrico naranja (aproximado)
  'custom:guayaba_v1': '🍐',      // fruto redondo (aproximado)
  'custom:granadilla_v1': '🟠',   // fruto naranja de pasiflora (aproximado)
  'custom:habichuela_v1': '🥬',   // vaina verde (aproximado)
  'custom:ahuyama_v1': '🟧',      // cucurbitácea naranja (aproximado)
  'custom:caucho_v1': '🌳',       // árbol de caucho (aproximado)
  'custom:fique_v1': '🌵',        // agave/suculenta (aproximado)
};

/** Resuelve el ícono de un cultivo: emoji directo o aproximación para 'custom:*'. */
function iconoCultivo(icono) {
  if (!icono) return '🌱';
  if (String(icono).startsWith('custom:')) return ICONOS_APROXIMADOS[icono] || '🌱';
  return icono;
}

// Íconos vectoriales reales creados por producto (especificación v4 — "custom pendiente")
const ICONOS_IMG = {
  'Panela / Caña panelera': '/img/iconos/panela.svg',
  'Chontaduro': '/img/iconos/chontaduro.svg',
  'Lulo': '/img/iconos/lulo.svg',
  'Guayaba': '/img/iconos/guayaba.svg',
  'Granadilla / Curuba': '/img/iconos/granadilla.svg',
  'Habichuela': '/img/iconos/habichuela.svg',
  'Ahuyama / Auyama': '/img/iconos/ahuyama.svg',
  'Caucho': '/img/iconos/caucho.svg',
  'Fique': '/img/iconos/fique.svg',
};

/** Imagen real del producto si existe; si no, el emoji representativo. */
function iconoImgCultivo(c) {
  const svg = ICONOS_IMG[c.nombre];
  if (svg) return `<img class="icono-img" src="${svg}" alt="${esc(c.nombre)}" />`;
  return iconoCultivo(c.icono);
}

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
  const h = {};
  const token = state.sesion && state.sesion.access_token;
  if (token) {
    h['Authorization'] = 'Bearer ' + token;
  } else {
    // Fallback demo (solo entornos de desarrollo sin token)
    h['X-User-Role'] = state.rol;
    if (state.email) h['X-User-Email'] = state.email;
    if (state.nombre) h['X-User-Nombre'] = state.nombre;
  }
  if (json) h['Content-Type'] = 'application/json';
  return h;
}

/* ─────────────────────────── utilidades ─────────────────────────── */

let _refreshEnCurso = null;

async function renovarSesion() {
  // Renueva el access token con el refresh token (una sola llamada concurrente).
  if (!_refreshEnCurso) {
    _refreshEnCurso = (async () => {
      const rt = state.sesion && state.sesion.refresh_token;
      if (!rt) throw new Error('Sin refresh token');
      const res = await fetch(API + '/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      });
      if (!res.ok) throw new Error('Refresh fallido');
      const data = await res.json();
      state.sesion = { ...state.sesion, ...data };
      localStorage.setItem(SESION_KEY, JSON.stringify(state.sesion));
      return data.access_token;
    })().finally(() => { _refreshEnCurso = null; });
  }
  return _refreshEnCurso;
}

async function _fetchApi(path, opts) {
  const h = { ...(opts.headers || {}) };
  const token = state.sesion && state.sesion.access_token;
  if (token) {
    h['Authorization'] = 'Bearer ' + token;
  } else {
    h['X-User-Role'] = state.rol;
    if (state.email) h['X-User-Email'] = state.email;
    if (state.nombre) h['X-User-Nombre'] = state.nombre;
  }
  return fetch(API + path, { ...opts, headers: h });
}

async function api(path, opts = {}) {
  const esRutaAuth = path.startsWith('/auth/');
  let res = await _fetchApi(path, opts);
  // 401 con token vigente/vencido → intentar renovar la sesión una vez
  if (res.status === 401 && !esRutaAuth && state.sesion && state.sesion.access_token) {
    try {
      await renovarSesion();
      res = await _fetchApi(path, opts);
    } catch {
      cerrarSesion();
      throw new Error('La sesión expiró. Inicia sesión nuevamente.');
    }
  }
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
  if (e === 'DEFICIT' || e === 'ALTA' || e === 'ADVERTENCIA' || e === 'MEDIA' || e === 'INTERACCION') return 'warning';
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
  // Revoca tokens en el servidor (fire-and-forget) y limpia la sesión local
  const sesion = state.sesion || {};
  if (sesion.refresh_token) {
    fetch(API + '/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(sesion.access_token ? { 'Authorization': 'Bearer ' + sesion.access_token } : {}),
      },
      body: JSON.stringify({ refresh_token: sesion.refresh_token }),
    }).catch(() => { /* sin red: se limpia local de todas formas */ });
  }
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
  if (name === 'alertas') cargarAlertasClima();
  if (name === 'fincas' && state.rol.toLowerCase() === 'admin') renderFincasList();
  if (name === 'usuarios' && state.rol.toLowerCase() === 'admin') cargarUsuarios();
  if (name === 'insumos' && state.rol.toLowerCase() === 'admin') cargarPreciosInsumos();
  if (name === 'auditoria' && state.rol.toLowerCase() === 'admin') cargarAuditoria();
  if (name === 'zona' && state.rol.toLowerCase() === 'extensionista') cargarZona();
  if (name === 'bpa' && state.rol.toLowerCase() === 'admin') cargarBpa();
  if (name === 'equipo' && state.rol.toLowerCase() === 'admin') cargarEquipo();
  if (name === 'comisiones' && state.rol.toLowerCase() === 'admin') cargarComisiones();
  if (name === 'lista-trabajos' && state.rol.toLowerCase() === 'admin') cargarListaTrabajos();
  if (name === 'precios-cosecha' && state.rol.toLowerCase() === 'admin') cargarPreciosCosecha();
  document.querySelectorAll('.tab-submenu.open').forEach(s => s.classList.remove('open'));
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
  const balanceModelo = document.getElementById('balance-modelo');
  if (balanceModelo) balanceModelo.addEventListener('change', () => renderBalanceHidrico());

  if (!state.sesion) {
    loginScreen.classList.remove('oculto');
    return;
  }
  aplicarSesion(state.sesion);
  await arrancarAplicacion();
}

async function arrancarAplicacion() {
  document.querySelectorAll('.tab').forEach(t => {
    if (!t.dataset.tab) return;
    t.addEventListener('click', () => goTab(t.dataset.tab));
  });

  // ── Menús desplegables (Administración y Ayuda) — flotantes sobre el contenido ──
  document.querySelectorAll('.tab-dropdown').forEach(dd => {
    const btn = dd.querySelector(':scope > button.tab, :scope > .tab');
    const sub = dd.querySelector('.tab-submenu');
    if (!btn || !sub) return;

    const posicionar = () => {
      const r = btn.getBoundingClientRect();
      const width = Math.max(sub.offsetWidth || 230, 230);
      const height = Math.max(sub.offsetHeight || 0, 0);
      let left = r.right - width;
      if (left < 8) left = 8;
      if (left + width > window.innerWidth - 8) left = window.innerWidth - width - 8;
      // Si no cabe hacia abajo, abre hacia arriba; si tampoco cabe, se pega arriba
      let top = r.bottom + 6;
      if (height && top + height > window.innerHeight - 8) {
        top = r.top - 6 - height;
        if (top < 8) top = 8;
      }
      sub.style.position = 'fixed';   // escapa del overflow del nav y flota sobre el body
      sub.style.top = `${top}px`;
      sub.style.left = `${left}px`;
      sub.style.right = 'auto';
    };
    const sincronizar = () => {
      if (!sub.classList.contains('open')) return;
      const r = btn.getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) {
        sub.classList.remove('open');  // el botón quedó fuera de pantalla
        return;
      }
      posicionar();
    };
    btn.addEventListener('click', e => {
      e.stopPropagation();
      const abrir = !sub.classList.contains('open');
      // Al abrir uno se cierra el otro
      document.querySelectorAll('.tab-submenu.open').forEach(s => {
        if (s !== sub) s.classList.remove('open');
      });
      sub.classList.toggle('open');
      if (abrir) posicionar();
    });
    window.addEventListener('resize', sincronizar);
    window.addEventListener('scroll', sincronizar, true);
  });
  document.addEventListener('click', e => {
    document.querySelectorAll('.tab-submenu.open').forEach(sub => {
      if (sub.contains(e.target)) return;
      const dd = sub.closest('.tab-dropdown');
      const btn = dd ? dd.querySelector(':scope > button.tab, :scope > .tab') : null;
      if (btn === e.target) return;
      sub.classList.remove('open');
    });
  });

  aplicarRol();

  // Extensionista: landing en «Mi zona» tras el login
  if ((state.rol || '').toLowerCase() === 'extensionista') goTab('zona');

  // ── Combos ubicación ──
  const depSel = document.getElementById('f-departamento');
  depSel.innerHTML = '<option value="">— Seleccione —</option>' +
    Object.keys(DEPARTAMENTOS).sort().map(d => `<option value="${esc(d)}">${esc(d)}</option>`).join('');
  depSel.addEventListener('change', poblarMunicipios);
  const pcDepSel = document.getElementById('pc-departamento');
  if (pcDepSel) {
    pcDepSel.innerHTML = '<option value="">— Seleccione —</option>' +
      Object.keys(DEPARTAMENTOS).sort().map(d => `<option value="${esc(d)}">${esc(d)}</option>`).join('');
  }
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
  const mLabor = document.getElementById('modal-labor');
  if (mLabor) {
    document.getElementById('modal-labor-cerrar').addEventListener('click', cerrarModalLabor);
    document.getElementById('modal-labor-cancelar').addEventListener('click', cerrarModalLabor);
    mLabor.addEventListener('click', e => { if (e.target === mLabor) cerrarModalLabor(); });
  }
  document.getElementById('audit-refrescar').addEventListener('click', () => cargarAuditoria(1));
  document.getElementById('bpa-cargar').addEventListener('click', cargarBpa);
  document.getElementById('equipo-cargar').addEventListener('click', cargarEquipo);
  document.getElementById('equipo-nuevo').addEventListener('click', () => abrirModalEmpleado());
  document.getElementById('com-cargar').addEventListener('click', cargarComisiones);
  document.getElementById('com-nueva').addEventListener('click', () => abrirModalComision());
  document.getElementById('lt-cargar').addEventListener('click', cargarListaTrabajos);
  document.getElementById('ml-reentrenar').addEventListener('click', reentrenarModelo);
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
  // incluyendo finca_id y posición geográfica del punto de toma
  // (latitude/longitude en grados decimales WGS84).
  document.getElementById('sim-trama').value = JSON.stringify({
    device_id: 'esp32-npk-001',
    finca_id: 'a0562767-13a8-4a49-bd98-e8097d5b2674',
    latitude: 4.578333,
    longitude: -75.666944,
    humidity: 94.0,
    temperature: 22.8,
    conductivity: 126.0,
    ph: 7.0,
    nitrogen: 5.0,
    phosphorus: 8.0,
    potassium: 20.0,
    rssi: -45,
    uptime_s: 3600,
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
  // Para Admin, «Fincas» e «Historial» ya están en el menú ⚙️ Administración:
  // se ocultan de la barra superior para no duplicarlas.
  const topOcultas = rol === 'admin' ? ['fincas', 'historial'] : [];
  const enSubmenuAdmin = t => !!t.closest('#admin-submenu');
  document.querySelectorAll('.tab').forEach(t => {
    if (!t.dataset.tab || enSubmenuAdmin(t)) return;
    const visible = permitidas.includes(t.dataset.tab) && !topOcultas.includes(t.dataset.tab);
    t.style.display = visible ? '' : 'none';
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
          <button type="button" class="btn btn-ghost" data-accion="agua" data-id="${esc(f.id)}">💧 Agua de riego</button>
          <button type="button" class="btn btn-ghost" data-accion="notif" data-id="${esc(f.id)}">🔔 Notificaciones</button>
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
  div.querySelectorAll('[data-accion="agua"]').forEach(b => {
    b.addEventListener('click', () => verAguaRiego(b.dataset.id));
  });
  div.querySelectorAll('[data-accion="notif"]').forEach(b => {
    b.addEventListener('click', () => verNotificaciones(b.dataset.id));
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
  const m = document.getElementById('modal-editor');
  m.classList.add('hidden');
  // Restaura los controles por si un modal de solo lectura los ocultó/cambió
  const guardar = document.getElementById('modal-guardar');
  if (guardar) guardar.style.display = '';
  const cancelar = document.getElementById('modal-cancelar');
  if (cancelar) cancelar.textContent = 'Cancelar';
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
        <button class="btn btn-ghost" data-lote-plagas="${esc(l.id)}">🐛 Plagas</button>
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
  panel.querySelectorAll('[data-lote-plagas]').forEach(b => {
    b.addEventListener('click', () => verPlagas(fincaId, b.dataset.lotePlagas));
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
    </div>
    <div id="ic-rotacion" class="rotacion-sugerida"></div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = () => iniciarCiclo(fincaId);
  cargarRotacionModal(fincaId);
}

/** Bloque «🔄 Rotación sugerida» dentro del modal de nuevo ciclo (1.F). */
async function cargarRotacionModal(fincaId) {
  const div = document.getElementById('ic-rotacion');
  if (!div) return;
  div.innerHTML = '';
  try {
    const r = await api(`/fincas/${fincaId}/recomendacion-rotacion`);
    const sugerencias = (r && r.sugerencias) || [];
    if (!sugerencias.length) return;  // regla de degradación: bloque omitido
    const opciones = (state.cultivos || []).map(c => ({ id: c.id, nombre: c.nombre }));
    div.innerHTML = `
      <div class="nota">
        <b>🔄 Rotación sugerida</b> — el último ciclo fue
        <b>${esc(r.cultivo_actual || '—')}</b>:
        <ul class="rotacion-lista">
          ${sugerencias.map(s => `
            <li>
              🌱 <b>${esc(s.cultivo)}</b>
              <span class="muted">· ${esc(s.motivo || s.beneficio || '')}</span>
              <button type="button" class="btn-ghost-sm" data-rot-cultivo="${esc(s.cultivo)}">Usar este cultivo</button>
            </li>`).join('')}
        </ul>
      </div>`;
    div.querySelectorAll('[data-rot-cultivo]').forEach(btn => {
      btn.addEventListener('click', () => {
        const nombre = btn.dataset.rotCultivo;
        const match = opciones.find(c => c.nombre.toLowerCase() === nombre.toLowerCase());
        const sel = document.getElementById('ic-cultivo');
        if (sel && match) sel.value = match.id;
      });
    });
  } catch {
    /* sin reglas o sin acceso: el bloque simplemente se omite */
  }
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
    let avisoAtipico = '';
    if (r.advertencia_rendimiento) {
      avisoAtipico = `<div class="advertencia" style="margin-top:8px">⚠️ ${esc(r.advertencia_rendimiento)}</div>`;
    }
    msg.innerHTML = okBanner(
      `Ciclo cosechado: rendimiento <b>${r.ciclo.rendimiento_tn_ha} t/ha</b>` +
      (r.ciclo.calidad_cosecha ? ` · calidad ${esc(r.ciclo.calidad_cosecha)}` : '') +
      (aplicaciones ? `<br><span class="muted">Aplicaciones registradas: ${esc(aplicaciones)}</span>` : '') +
      ((r.advertencias || []).length ? `<br>⚠️ ${esc(r.advertencias.join(' '))}` : '')
    ) + avisoAtipico;
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
    const porId = {};
    labores.forEach(l => { porId[l.id] = l; });
    div._labores = porId;
    div.innerHTML = labores.map(l => `
      <div class="labor-row" data-labor-fila="${esc(l.id)}">
        <div class="labor-info">
          <b>${TIPO_LABOR_ICONO[l.tipo] || '📋'} ${esc(l.tipo)}</b>
          <span>${esc(l.titulo)}</span>
          <span class="labor-finca">🏡 ${esc(l.finca_nombre || 'Finca')}${l.lote_nombre ? ` · 🗂️ ${esc(l.lote_nombre)}` : ''}</span>
          <span class="muted">programada ${esc(l.fecha_programada || '?')}</span>
          <span class="muted">${badge(l.estado, l.estado === 'Pendiente' ? 'warning' : 'ok')}</span>
        </div>
        <div class="device-actions">
          <button class="btn btn-ghost" data-labor-detalle="${esc(l.id)}">👁️ Ver detalle</button>
          ${puedeGestionar ? `
          <button class="btn btn-ghost" data-labor-completar="${esc(l.id)}">✔️ Completar</button>
          <button class="btn btn-ghost" data-labor-cancelar="${esc(l.id)}">🚫 Cancelar</button>` : ''}
        </div>
      </div>`).join('');
    div.querySelectorAll('[data-labor-fila]').forEach(fila => {
      fila.addEventListener('click', () => {
        const labor = (div._labores || {})[fila.dataset.laborFila];
        if (labor) verDetalleLabor(labor);
      });
    });
    div.querySelectorAll('[data-labor-detalle]').forEach(b => {
      b.addEventListener('click', e => {
        e.stopPropagation();
        const labor = (div._labores || {})[b.dataset.laborDetalle];
        if (labor) verDetalleLabor(labor);
      });
    });
    div.querySelectorAll('[data-labor-completar]').forEach(b => {
      b.addEventListener('click', e => { e.stopPropagation(); actualizarLabor(b.dataset.laborCompletar, 'Completada'); });
    });
    div.querySelectorAll('[data-labor-cancelar]').forEach(b => {
      b.addEventListener('click', e => { e.stopPropagation(); actualizarLabor(b.dataset.laborCancelar, 'Cancelada'); });
    });
  } catch {
    div.innerHTML = '<p class="muted">No se pudieron cargar las tareas pendientes.</p>';
  }
}

/* ── Detalle de una orden de trabajo (modal) ── */

function verDetalleLabor(l) {
  const m = document.getElementById('modal-labor');
  if (!m) return;
  document.getElementById('modal-labor-titulo').textContent = `📋 ${l.tipo || 'Labor'} — ${l.titulo || 'Orden de trabajo'}`;
  const img = l.imagen_url
    ? `<img src="${esc(l.imagen_url)}" alt="Foto de la labor" style="max-width:100%;border-radius:10px;margin-top:8px" />`
    : '<p class="muted">Sin foto adjunta.</p>';
  document.getElementById('modal-labor-cuerpo').innerHTML = `
    <div class="labor-detalle">
      <div class="labor-detalle-grid">
        <div><span class="muted">Finca</span><br/><b>🏡 ${esc(l.finca_nombre || '—')}</b></div>
        <div><span class="muted">Lote</span><br/><b>🗂️ ${esc(l.lote_nombre || '—')}</b></div>
        <div><span class="muted">Tipo</span><br/><b>${TIPO_LABOR_ICONO[l.tipo] || '📋'} ${esc(l.tipo || '—')}</b></div>
        <div><span class="muted">Estado</span><br/>${badge(l.estado, l.estado === 'Pendiente' ? 'warning' : l.estado === 'Completada' ? 'ok' : 'critical')}</div>
        <div><span class="muted">Producto</span><br/><b>${esc(l.producto || '—')}</b></div>
        <div><span class="muted">Dosis</span><br/><b>${l.dosis_kg_ha != null ? esc(l.dosis_kg_ha) + ' kg/ha' : '—'}</b></div>
        <div><span class="muted">Fecha programada</span><br/><b>📅 ${esc(l.fecha_programada || '—')}</b></div>
        <div><span class="muted">Fecha de ejecución</span><br/><b>✅ ${esc(l.fecha_ejecucion || '—')}</b></div>
      </div>
      <div class="labor-detalle-obs">
        <span class="muted">Observaciones de ejecución</span>
        <p>${esc(l.observaciones_ejecucion || 'Sin observaciones registradas.')}</p>
      </div>
      <div class="labor-detalle-foto">${img}</div>
    </div>`;
  m.classList.remove('hidden');
}

function cerrarModalLabor() {
  const m = document.getElementById('modal-labor');
  if (m) m.classList.add('hidden');
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

/* ────────────────────── menú «⛅ Alertas clima» (todos los roles) ────────────────────── */

const TITULOS_ALERTA = {
  lluvia_aplicacion: 'Lluvia fuerte / lixiviación',
  helada_floracion: 'Riesgo de helada',
};

function _etiquetaUbicacion(a) {
  const depto = (a.departamento || '').trim();
  const muni = (a.municipio || '').trim();
  if (depto && muni) return `${muni}, ${depto}`;
  if (depto) return depto;
  if (muni) return muni;
  return 'Ubicación sin registro';
}

function _claveUbicacion(a) {
  const depto = (a.departamento || '').trim();
  const muni = (a.municipio || '').trim();
  if (depto && muni) return `${depto}|${muni}`;
  if (a.latitud != null && a.longitud != null) return `coord|${a.latitud},${a.longitud}`;
  return `finca|${a.finca_id}`;
}

async function cargarAlertasClima() {
  const cont = document.getElementById('alertas-clima-listado');
  if (!cont) return;
  cont.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const r = await api('/alertas-climaticas');
    const alertas = r.data || [];
    if (!alertas.length) {
      cont.innerHTML = '<div class="advertencia">🌤️ No hay alertas climáticas activas para las fincas visibles. Las alertas se generan automáticamente cada 6 horas.</div>';
      return;
    }
    // Agrupar por tipo de alerta + ubicación: varias fincas en la misma zona
    // (departamento + municipio) comparten una sola tarjeta que muestra la ciudad.
    const grupos = new Map();
    alertas.forEach(a => {
      const clave = `${a.tipo}|${_claveUbicacion(a)}`;
      if (!grupos.has(clave)) grupos.set(clave, []);
      grupos.get(clave).push(a);
    });
    cont.innerHTML = [...grupos.values()].map(gs => {
      const a = gs[0];
      const varias = gs.length > 1;
      const ubicacion = _etiquetaUbicacion(a);
      const detalle = varias
        ? `<details class="alerta-clima-fincas">
             <summary>🏡 ${gs.length} fincas en esta ubicación</summary>
             <ul>${gs.map(g => `<li>${esc(g.finca_nombre)}</li>`).join('')}</ul>
           </details>`
        : `<div class="alerta-clima-finca">Finca: ${esc(a.finca_nombre)}</div>`;
      return `
        <div class="alerta-clima alerta-clima-bloque alerta-${esc(a.tipo)}">
          <span class="alerta-clima-ico">${ICONOS_ALERTA[a.tipo] || '⚠️'}</span>
          <div class="alerta-clima-cuerpo">
            <div class="alerta-clima-titulo">${TITULOS_ALERTA[a.tipo] || esc(a.tipo)} · ${esc(a.severidad)} · ${esc(a.fecha_alerta || '')}</div>
            <div class="alerta-clima-msg">${esc(a.mensaje)}</div>
            <div class="alerta-clima-ubi">📍 ${esc(ubicacion)}</div>
            ${detalle}
          </div>
        </div>`;
    }).join('');
  } catch (e) {
    cont.innerHTML = errorBanner(e.message);
  }
}

async function evaluarAlertasAhora() {
  if (!confirm('¿Evaluar ahora las alertas climáticas de todas las fincas?')) return;
  const btn = document.getElementById('btn-evaluar-alertas');
  if (btn) { btn.disabled = true; btn.textContent = 'Evaluando…'; }
  try {
    await api('/alertas-climaticas/evaluar', {
      method: 'POST', headers: headers(),
      body: JSON.stringify({ finca_id: null }),
    });
    await cargarAlertasClima();
  } catch (e) {
    alert('No se pudo evaluar: ' + e.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🔄 Evaluar ahora'; }
  }
}

/* ────────────────────── Precios de cosecha (admin, UC1 mercado) ────────────────────── */

async function cargarPreciosCosecha() {
  const lista = document.getElementById('precios-cosecha-lista');
  const cultivoSel = document.getElementById('pc-cultivo');
  if (!lista) return;
  try {
    const [precios, cultivos] = await Promise.all([
      api('/cultivos/precios'),
      api('/catalogo/cultivos?limite=200'),
    ]);
    if (cultivoSel && cultivoSel.options.length <= 1) {
      cultivoSel.innerHTML = '<option value="">— Seleccione cultivo —</option>' +
        (cultivos.data || []).map(c => `<option value="${esc(c.id)}">${esc(c.nombre)}</option>`).join('');
    }
    const filas = precios.data || [];
    if (!filas.length) {
      lista.innerHTML = '<p class="muted">Sin precios registrados. Registra el precio por cultivo y departamento para habilitar la utilidad estimada en las recomendaciones (UC1).</p>';
      return;
    }
    lista.innerHTML = `
      <div class="table-wrap"><table>
        <tr><th>Cultivo</th><th>Departamento</th><th>Precio COP/kg</th><th>Rendimiento t/ha</th><th>Fuente</th><th>Actualizado</th></tr>
        ${filas.map(p => `
          <tr>
            <td>${esc(p.cultivo || '—')}</td>
            <td>${esc(p.departamento)}</td>
            <td>$ ${fmtNum(p.precio_promedio_cop_kg, 0)}</td>
            <td>${p.rendimiento_promedio_t_ha != null ? fmtNum(p.rendimiento_promedio_t_ha, 1) : '—'}</td>
            <td>${esc(p.fuente || '—')}</td>
            <td>${esc(p.fecha_actualizacion || '—')}</td>
          </tr>`).join('')}
      </table></div>`;
  } catch (e) {
    lista.innerHTML = errorBanner(e.message);
  }
}

async function guardarPrecioCosecha(e) {
  e.preventDefault();
  const msg = document.getElementById('pc-msg');
  msg.innerHTML = '';
  const cultivoId = document.getElementById('pc-cultivo').value;
  const departamento = document.getElementById('pc-departamento').value.trim();
  const precio = parseFloat(document.getElementById('pc-precio').value);
  const rendimiento = document.getElementById('pc-rendimiento').value;
  if (!cultivoId || !departamento || !(precio > 0)) {
    msg.innerHTML = errorBanner('Selecciona cultivo, departamento y un precio mayor a 0.');
    return;
  }
  try {
    await api('/admin/precios-cosecha', {
      method: 'PUT', headers: headers(),
      body: JSON.stringify({
        cultivo_id: cultivoId,
        departamento,
        precio_promedio_cop_kg: precio,
        rendimiento_promedio_t_ha: rendimiento ? parseFloat(rendimiento) : null,
        fuente: 'Ingreso manual (panel admin)',
      }),
    });
    msg.innerHTML = okBanner('Precio actualizado.');
    await cargarPreciosCosecha();
  } catch (err) {
    msg.innerHTML = errorBanner(err.message);
  }
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

/* ── Enriquecimiento SIG (IGAC/UPRA) tras registrar la finca ── */

function renderSigEnriquecimiento(sig) {
  if (!sig || !sig.zona) return '';
  return `
    <div class="sig-banner">
      🗺️ <b>Capas oficiales IGAC/UPRA aplicadas:</b> textura <b>${esc(sig.zona.textura)}</b>,
      materia orgánica ${esc(String(sig.zona.materia_organica_pct))} %,
      CIC ${esc(String(sig.zona.cic_meq))} meq/100g · drenaje ${esc(sig.zona.drenaje || '—')}
      · profundidad ${esc(String(sig.zona.profundidad_efectiva_cm))} cm
      <div class="muted" style="font-size:0.78rem">Calidad <b>estimado_por_sig</b> — si el sensor envía datos reales, sobreescriben la estimación oficial.</div>
    </div>`;
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
    ${r.lote_principal ? `<p class="muted">🌱 Lote productivo creado: <b>${esc(r.lote_principal.nombre)}</b>${r.lote_principal.area_ha != null ? ` (${esc(String(r.lote_principal.area_ha))} ha)` : ''}.</p>` : ''}`
    + renderSigEnriquecimiento(r.enriquecimiento_sig);
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
        state.cultivos.map(c => `<option value="${esc(c.id)}">${iconoCultivo(c.icono)} ${esc(c.nombre)}</option>`).join('');
      if (prev) sel.value = prev;
    }
  // Cultivos para el selector de reportes
  const repoCultivo = document.getElementById('repo-cultivo');
  repoCultivo.innerHTML = '<option value="">— Auto (top del ranking) —</option>' +
    state.cultivos.map(c => `<option value="${esc(c.id)}">${iconoCultivo(c.icono)} ${esc(c.nombre)}</option>`).join('');
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
    renderBalanceHidrico();
  } catch (e) {
    kpis.innerHTML = errorBanner(e.message);
  }
}

/* ── Balance hídrico ETo/Kc (1.C) — bloque del Dashboard ── */

async function renderBalanceHidrico() {
  const div = document.getElementById('balance-hidrico');
  if (!div || !state.fincaId) return;
  div.innerHTML = '<p class="muted">Calculando…</p>';
  try {
    const modelo = document.getElementById('balance-modelo');
    const q = modelo ? `&modelo=${encodeURIComponent(modelo.value || 'auto')}` : '';
    const r = await api(`/fincas/${state.fincaId}/balance-hidrico?dias=7${q}`);
    const filas = (r.dias || []).map(d => `
      <tr>
        <td>${esc(d.fecha)}</td>
        <td>${d.et0_mm}</td>
        <td>${d.etc_mm}</td>
        <td>${d.precipitacion_mm}</td>
        <td>${d.deficit_mm}</td>
      </tr>`).join('');
    div.innerHTML = `
      <p class="muted">Cultivo: <b>${esc(r.cultivo || '—')}</b> · etapa ${esc(r.etapa_fenologica || '—')} · Kc ${r.kc_aplicado}${r.kc_aplicado_generico ? ' (genérico)' : ''}</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Fecha</th><th>ETo mm</th><th>ETc mm</th><th>Lluvia mm</th><th>Déficit mm</th></tr></thead>
        <tbody>${filas}</tbody>
      </table></div>
      <p><b>💧 Déficit acumulado: ${r.deficit_acumulado_7d_mm} mm</b> — ${esc(r.recomendacion || '')}</p>
      <p class="muted">Fuente: ${esc(r.fuente_pronostico || 'Open-Meteo')}</p>`;
  } catch (e) {
    div.innerHTML = `<p class="muted">💧 Balance hídrico no disponible: ${esc(e.message)}</p>`;
  }
}

/* ══════════════════ Módulos v4: agua, plagas, BPA, notificaciones, zona ══════════════════ */

async function verAguaRiego(fincaId) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = '💧 Agua de riego (FAO-29)';
  document.getElementById('modal-msg').innerHTML = '';
  const r = await api(`/fincas/${fincaId}/agua-riego`);
  const historial = (r.data || []).slice(0, 5).map(a => `
    <div class="labor-row"><div class="labor-info">
      <b>${esc(a.fecha)}</b>
      <span class="muted">CE ${a.ce_agua_ds_m ?? '—'} dS/m · RAS ${a.ras ?? '—'} · Cl ${a.cloruros_mg_l ?? '—'} · B ${a.boro_mg_l ?? '—'}</span>
      <span>${badge(a.clasificacion_restriccion === 'ninguna' ? 'Sin restricción' : a.clasificacion_restriccion === 'leve_moderada' ? 'Leve-moderada' : 'Severa', a.clasificacion_restriccion === 'ninguna' ? 'ok' : 'warning')}</span>
    </div></div>`).join('') || '<p class="muted">Sin análisis registrados.</p>';
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="labor-detalle">
      <div><span class="muted">Historial</span>${historial}</div>
      <div class="form-grid">
        <label class="field"><span>CE (dS/m)</span><input id="ag-ce" type="number" step="0.01" /></label>
        <label class="field"><span>RAS</span><input id="ag-ras" type="number" step="0.1" /></label>
        <label class="field"><span>Cloruros (mg/L)</span><input id="ag-cl" type="number" step="0.1" /></label>
        <label class="field"><span>Boro (mg/L)</span><input id="ag-b" type="number" step="0.01" /></label>
        <label class="field"><span>pH del agua</span><input id="ag-ph" type="number" step="0.1" /></label>
        <label class="field"><span>Fuente</span>
          <select id="ag-fuente"><option value="laboratorio">Laboratorio</option><option value="manual">Manual</option></select></label>
      </div>
      <div class="labor-detalle-obs"><span class="muted">Clasificación</span><p id="ag-resultado">Registre un análisis para ver la clasificación FAO-29.</p></div>
    </div>`;
  document.getElementById('modal-guardar').onclick = async () => {
    const body = {
      fecha: new Date().toISOString().slice(0, 10),
      ce_agua_ds_m: parseFloat(document.getElementById('ag-ce').value) || null,
      ras: parseFloat(document.getElementById('ag-ras').value) || null,
      cloruros_mg_l: parseFloat(document.getElementById('ag-cl').value) || null,
      boro_mg_l: parseFloat(document.getElementById('ag-b').value) || null,
      ph_agua: parseFloat(document.getElementById('ag-ph').value) || null,
      fuente: document.getElementById('ag-fuente').value,
    };
    try {
      const res = await api(`/fincas/${fincaId}/agua-riego`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
      document.getElementById('ag-resultado').innerHTML =
        `✅ <b>${res.clasificacion_restriccion.replace('_', ' / ')}</b> — ${esc(res.recomendacion)}`;
      await verAguaRiego(fincaId);
    } catch (e) { document.getElementById('ag-resultado').textContent = '⚠️ ' + e.message; }
  };
  m.classList.remove('hidden');
}

async function verNotificaciones(fincaId) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = '🔔 Notificaciones de la finca';
  document.getElementById('modal-msg').innerHTML = '';
  const pref = await api(`/fincas/${fincaId}/notificaciones/preferencias`);
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="form-grid">
      <label class="field"><span>Canal</span>
        <select id="nt-canal">
          ${['whatsapp', 'sms', 'email', 'ninguno'].map(c => `<option value="${c}" ${pref.canal === c ? 'selected' : ''}>${c}</option>`).join('')}
        </select></label>
      <label class="field"><span>Teléfono (con indicativo)</span><input id="nt-tel" value="${esc(pref.telefono || '')}" placeholder="573001234567" /></label>
      <label class="field"><span>Activo</span>
        <select id="nt-activo"><option value="true" ${pref.activo !== false ? 'selected' : ''}>Sí</option><option value="false" ${pref.activo === false ? 'selected' : ''}>No</option></select></label>
    </div>
    <p class="muted">Las alertas climáticas y las labores próximas a vencer se envían por el canal configurado (WhatsApp requiere credenciales configuradas en el servidor).</p>`;
  document.getElementById('modal-guardar').onclick = async () => {
    try {
      await api(`/fincas/${fincaId}/notificaciones/preferencias`, {
        method: 'PUT', headers: headers(),
        body: JSON.stringify({
          canal: document.getElementById('nt-canal').value,
          telefono: document.getElementById('nt-tel').value || null,
          activo: document.getElementById('nt-activo').value === 'true',
        }),
      });
      document.getElementById('modal-msg').innerHTML = '<p class="ok">✅ Preferencia guardada.</p>';
    } catch (e) { document.getElementById('modal-msg').innerHTML = errorBanner(e.message); }
  };
  m.classList.remove('hidden');
}

async function verPlagas(fincaId, loteId) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = '🐛 Monitoreo de plagas (MIP)';
  document.getElementById('modal-msg').innerHTML = '';
  const r = await api(`/fincas/${fincaId}/lotes/${loteId}/monitoreo-plagas`);
  const historial = (r.data || []).slice(0, 8).map(p => `
    <div class="labor-row"><div class="labor-info">
      <b>${esc(p.plaga_nombre)}</b>
      ${p.plaga_nombre_cientifico ? `<span class="muted"><i>${esc(p.plaga_nombre_cientifico)}</i></span>` : ''}
      <span class="muted">${esc(p.fecha)}</span>
      ${p.incidencia_pct != null ? `<span class="muted">incidencia ${p.incidencia_pct}%</span>` : ''}
      <span>${badge(p.severidad || '—', p.severidad === 'Alta' ? 'critical' : p.severidad === 'Media' ? 'warning' : 'ok')}</span>
    </div></div>`).join('') || '<p class="muted">Sin monitoreos registrados.</p>';
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="labor-detalle">
      <div><span class="muted">Historial</span>${historial}</div>
      <div class="form-grid">
        <label class="field"><span>Plaga *</span><input id="pg-nombre" placeholder="Broca del café" required /></label>
        <label class="field"><span>Nombre científico</span><input id="pg-cientifico" placeholder="Hypothenemus hampei" /></label>
        <label class="field"><span>Severidad</span>
          <select id="pg-sev"><option value="Baja">Baja</option><option value="Media">Media</option><option value="Alta">Alta</option></select></label>
        <label class="field"><span>Incidencia (%)</span><input id="pg-inc" type="number" step="0.1" min="0" max="100" /></label>
        <label class="field"><span>Método</span>
          <select id="pg-metodo"><option value="trampa">Trampa</option><option value="inspeccion_visual">Inspección visual</option><option value="otro">Otro</option></select></label>
      </div>
      <label class="field"><span>Observaciones</span><input id="pg-obs" /></label>
    </div>`;
  document.getElementById('modal-guardar').onclick = async () => {
    try {
      const res = await api(`/fincas/${fincaId}/lotes/${loteId}/monitoreo-plagas`, {
        method: 'POST', headers: headers(),
        body: JSON.stringify({
          fecha: new Date().toISOString().slice(0, 10),
          plaga_nombre: document.getElementById('pg-nombre').value,
          plaga_nombre_cientifico: document.getElementById('pg-cientifico').value || null,
          severidad: document.getElementById('pg-sev').value,
          incidencia_pct: parseFloat(document.getElementById('pg-inc').value) || null,
          metodo: document.getElementById('pg-metodo').value,
          observaciones: document.getElementById('pg-obs').value || null,
        }),
      });
      const gbif = res.enriquecimiento_gbif ? ` · GBIF: ${res.enriquecimiento_gbif.total_ocurrencias_co} ocurrencias reportadas en Colombia` : '';
      document.getElementById('modal-msg').innerHTML = `<p class="ok">✅ Registro guardado${gbif}.</p>`;
      await verPlagas(fincaId, loteId);
    } catch (e) { document.getElementById('modal-msg').innerHTML = errorBanner(e.message); }
  };
  m.classList.remove('hidden');
}

async function verCurva(cultivoId, nombre) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `📈 Curva de extracción — ${nombre}`;
  document.getElementById('modal-msg').innerHTML = '';
  document.getElementById('modal-guardar').style.display = 'none';
  document.getElementById('modal-cancelar').textContent = 'Cerrar';
  const r = await api(`/cultivos/${cultivoId}/curva-extraccion`);
  const filas = (r.data || []).map(p => `
    <tr><td>${esc(p.etapa_fenologica)}</td><td>${esc(p.nutriente)}</td><td>${p.pct_extraccion_acumulado}%</td><td>${esc(p.fuente || '—')}</td></tr>`).join('');
  document.getElementById('modal-cuerpo').innerHTML = r.data && r.data.length
    ? `<div class="table-wrap"><table><thead><tr><th>Etapa</th><th>Nutriente</th><th>% acumulado</th><th>Fuente</th></tr></thead><tbody>${filas}</tbody></table></div>`
    : '<p class="muted">Sin curva cargada: el motor usa el rango estático genérico (comportamiento actual).</p>';
  m.classList.remove('hidden');
}

async function verVariedades(cultivoId, nombre) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `🌾 Variedades — ${nombre}`;
  document.getElementById('modal-msg').innerHTML = '';
  document.getElementById('modal-guardar').style.display = 'none';
  document.getElementById('modal-cancelar').textContent = 'Cerrar';
  const altitud = state.fincas.find(f => f.id === state.fincaId)?.altitud_msnm;
  const r = await api(`/cultivos/${cultivoId}/variedades${altitud != null ? `?altitud_msnm=${Math.round(altitud)}` : ''}`);
  const filas = (r.variedades_compatibles || []).map(v => `
    <div class="labor-row"><div class="labor-info">
      <b>${esc(v.nombre_variedad)}</b>
      <span class="muted">${v.altitud_min_msnm ?? '?'}–${v.altitud_max_msnm ?? '?'} msnm</span>
      ${v.resistencias ? `<span class="muted">${esc(v.resistencias)}</span>` : ''}
      <span>${badge(v.mercado_objetivo || '—', 'ok')}</span>
    </div></div>`).join('') || '<p class="muted">Sin variedades cargadas para este cultivo.</p>';
  document.getElementById('modal-cuerpo').innerHTML = `
    <p class="muted">Filtradas por la altitud de la finca de análisis (${altitud != null ? Math.round(altitud) + ' msnm' : 'sin dato'}).</p>${filas}`;
  m.classList.remove('hidden');
}

/* ── 📏 Detalle de medición con el sensor (por cultivo) ── */

function _profundidadMedicion(raizCm) {
  // Profundidad de inserción del sensor según la zona de raíces activas
  if (raizCm == null) return { principal: null, secundaria: null, nota: 'Sin dato de profundidad radicular en la ficha.' };
  const principal = Math.max(8, Math.min(30, Math.round(raizCm * 0.4)));
  const secundaria = Math.max(4, Math.round(raizCm * 0.2));
  return { principal, secundaria, nota: null };
}

function verDetalleMedicion(c) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `📏 Detalle medición — ${c.nombre}`;
  document.getElementById('modal-msg').innerHTML = '';
  document.getElementById('modal-guardar').style.display = 'none';
  document.getElementById('modal-cancelar').textContent = 'Cerrar';
  const raiz = c.profundidad_radicular_min_cm;
  const p = _profundidadMedicion(raiz);
  const filaRaiz = raiz != null ? `<b>≥ ${raiz} cm</b>` : '<span class="muted">sin dato en ficha</span>';
  const filaPrincipal = p.principal != null
    ? `<b>${p.principal} cm</b> <span class="muted">(zona de raíces activas)</span>`
    : '<span class="muted">use el valor genérico de 10–15 cm</span>';
  const filaSecundaria = p.secundaria != null
    ? `<b>${p.secundaria} cm</b> <span class="muted">(lectura superficial de control)</span>`
    : '—';
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="labor-detalle">
      <div class="labor-detalle-grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr))">
        <div><span class="muted">Profundidad radicular del cultivo</span><br/>${filaRaiz}</div>
        <div><span class="muted">Profundidad de inserción del sensor</span><br/>${filaPrincipal}</div>
        <div><span class="muted">Segunda lectura (control)</span><br/>${filaSecundaria}</div>
      </div>
      <div class="labor-detalle-obs">
        <span class="muted">Procedimiento de medición</span>
        <ol class="steps" style="margin:6px 0 0; padding-left:18px">
          <li>Elija el punto: a 20–30 cm del tallo, sin piedras, raíces gruesas ni residuos.</li>
          <li>Si el suelo está muy seco, humedezca ligeramente y espere 10–15 minutos (los sensores NPK capacitivos necesitan contacto con el suelo).</li>
          <li>Entierre el sensor <b>verticalmente</b> hasta la profundidad indicada y presione para que las sondas queden en contacto total.</li>
          <li>Espere 30–60 segundos hasta que la lectura se estabilice.</li>
          <li>Tome <b>2–3 lecturas por zona</b> (misma profundidad) y registre el promedio en la plataforma.</li>
          <li>Limpie las sondas después de cada punto y cambie de punto si nota piedras o huecos de aire.</li>
        </ol>
      </div>
      <div class="labor-detalle-obs">
        <span class="muted">Frecuencia sugerida</span>
        <p>Mida al menos <b>1 vez al mes</b> y siempre antes de cada fertilización y en cambio de etapa fenológica. Envía cada trama con <code>latitude</code>/<code>longitude</code> del punto para el mapa de calor del lote.</p>
      </div>
    </div>`;
  m.classList.remove('hidden');
}

async function cargarZona() {
  const div = document.getElementById('zona-lista');
  if (!div) return;
  div.innerHTML = '<p class="muted">Cargando zona…</p>';
  try {
    const r = await api('/extensionista/dashboard-zona');
    const resumen = r.resumen || {};
    div.innerHTML = `
      <div class="grid-kpis">
        ${kpi(resumen.total_fincas || 0, 'Fincas en mi zona')}
        ${kpi(resumen.alertas_climaticas_activas || 0, 'Alertas activas')}
        ${kpi(resumen.recomendaciones_pendientes_validacion || 0, 'Pendientes de validación')}
      </div>
      <p class="muted">Municipios asignados: ${(r.municipios || []).map(esc).join(', ') || 'ninguno'}.</p>
      ${(r.fincas || []).map(f => `
        <div class="device-card">
          <h3>🏡 ${esc(f.nombre)} <span class="muted">${esc(f.municipio || '')}</span></h3>
          <div class="device-meta">
            <span>Cultivo: <b>${esc(f.cultivo_sembrado || '—')}</b></span>
            ${f.ultima_recomendacion ? `<span>Última recomendación: ${esc(f.ultima_recomendacion.clasificacion || '—')} (${Math.round((f.ultima_recomendacion.confianza || 0) * 100)}%)</span>` : ''}
            <span>Alertas activas: <b>${f.alertas_activas}</b></span>
          </div>
        </div>`).join('')}`;
  } catch (e) {
    div.innerHTML = errorBanner(e.message);
  }
}

async function cargarBpa() {
  const sel = document.getElementById('bpa-finca');
  if (sel && !sel.options.length) {
    sel.innerHTML = state.fincas.map(f => `<option value="${esc(f.id)}">${esc(f.nombre)}</option>`).join('');
  }
  if (!sel.value) return;
  const lista = document.getElementById('bpa-lista');
  const resumen = document.getElementById('bpa-resumen');
  const visitas = document.getElementById('bpa-visitas');
  lista.innerHTML = '<p class="muted">Cargando checklist…</p>';
  visitas.innerHTML = '<p class="muted">Cargando visitas…</p>';
  try {
    const [check, traz, vis] = await Promise.all([
      api(`/fincas/${sel.value}/bpa/checklist`),
      api(`/fincas/${sel.value}/bpa/reporte-trazabilidad`),
      api(`/fincas/${sel.value}/bpa/visitas`),
    ]);
    lista.innerHTML = (check.data || []).map((c, i) => `
      <div class="labor-row">
        <div class="labor-info"><b>${esc(c.categoria || '')}</b><span>${esc(c.item)}</span>
          ${c.fecha_verificacion ? `<span class="muted">verificado ${esc(c.fecha_verificacion)}</span>` : '<span class="muted">pendiente de verificación</span>'}</div>
        <select data-bpa-item="${esc(c.item)}" data-bpa-cat="${esc(c.categoria || '')}">
          <option value="">—</option>
          <option value="true" ${c.cumple === true ? 'selected' : ''}>✅ Cumple</option>
          <option value="false" ${c.cumple === false ? 'selected' : ''}>❌ No cumple</option>
        </select>
      </div>`).join('') || '<p class="muted">Sin checklist.</p>';
    const t = traz.checklist || {};
    resumen.innerHTML = `
      <p><b>Avance BPA:</b> ${t.cumplidos || 0} de ${t.total || 0} ítems cumplidos${t.pct_avance != null ? ` (${t.pct_avance}%)` : ''}.</p>
      <p class="muted">Aplicaciones con período de carencia: ${(traz.aplicaciones || []).filter(a => a.periodo_carencia_dias != null).length} · ${(traz.aplicaciones || []).filter(a => a.periodo_carencia_dias == null).length} sin carencia registrada.</p>
      <button class="btn" id="bpa-guardar">💾 Guardar checklist</button>
      <button class="btn" id="bpa-nueva-visita">➕ Registrar visita de verificación</button>`;
    document.getElementById('bpa-guardar').onclick = async () => {
      const items = [...lista.querySelectorAll('[data-bpa-item]')].map(s => ({
        item: s.dataset.bpaItem,
        categoria: s.dataset.bpaCat || null,
        cumple: s.value === 'true' ? true : (s.value === 'false' ? false : null),
      })).filter(x => x.cumple !== null);
      if (!items.length) { alert('Seleccione al menos un ítem para guardar.'); return; }
      await api(`/fincas/${sel.value}/bpa/checklist`, { method: 'PUT', headers: headers(), body: JSON.stringify({ items }) });
      await cargarBpa();
    };
    document.getElementById('bpa-nueva-visita').onclick = () => abrirModalVisitaBpa(sel.value, check.data || []);

    visitas.innerHTML = (vis.data || []).map(v => `
      <div class="labor-row">
        <div class="labor-info">
          <b>🗓️ Visita ${esc(v.fecha)}</b>
          <span class="muted">por ${esc(v.verificado_por_nombre || v.verificado_por_email || '—')} · ${(v.items || []).length} ítem(s) evaluado(s)</span>
          <span class="visita-items">${(v.items || []).map(it => `${it.cumple ? '✅' : '❌'} ${esc(it.item)}`).join(' · ')}</span>
        </div>
        <button type="button" class="btn-ghost-sm" data-visita-id="${esc(v.id)}">🗑️ Quitar</button>
      </div>`).join('') || '<p class="muted">Sin visitas de verificación registradas todavía.</p>';
    visitas.querySelectorAll('[data-visita-id]').forEach(btn => {
      btn.addEventListener('click', () => quitarVisitaBpa(sel.value, btn.dataset.visitaId));
    });
  } catch (e) {
    lista.innerHTML = errorBanner(e.message);
  }
}

/** Modal: registrar una visita/medición de verificación BPA. */
function abrirModalVisitaBpa(fincaId, checkData) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = '🗓️ Registrar visita de verificación BPA';
  document.getElementById('modal-cuerpo').innerHTML = `
    <p class="muted">Evalúe cada práctica durante la visita. La visita queda en la línea de tiempo
    de trazabilidad de la finca y actualiza el checklist vigente con la fecha de la visita.</p>
    <label class="field"><span>Fecha de la visita *</span>
      <input id="vis-fecha" type="date" value="${new Date().toISOString().slice(0, 10)}" required /></label>
    <div class="bpa-items">${(checkData || []).map(c => `
      <div class="labor-row">
        <div class="labor-info"><b>${esc(c.categoria || '')}</b><span>${esc(c.item)}</span></div>
        <select data-vis-item="${esc(c.item)}" data-vis-cat="${esc(c.categoria || '')}">
          <option value="">—</option>
          <option value="true">✅ Cumple</option>
          <option value="false">❌ No cumple</option>
        </select>
      </div>`).join('')}</div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = async () => {
    const fecha = document.getElementById('vis-fecha').value;
    const items = [...m.querySelectorAll('[data-vis-item]')].map(s => ({
      item: s.dataset.visItem,
      categoria: s.dataset.visCat || null,
      cumple: s.value === 'true' ? true : (s.value === 'false' ? false : null),
    })).filter(x => x.cumple !== null);
    if (!fecha) {
      document.getElementById('modal-msg').innerHTML = errorBanner('Indique la fecha de la visita.');
      return;
    }
    if (!items.length) {
      document.getElementById('modal-msg').innerHTML = errorBanner('Evalúe al menos un ítem para registrar la visita.');
      return;
    }
    try {
      document.getElementById('modal-msg').innerHTML = '<div class="ok-banner">⏳ Registrando visita…</div>';
      await api(`/fincas/${fincaId}/bpa/visitas`, {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ fecha, items }),
      });
      cerrarModal();
      await cargarBpa();
    } catch (e) {
      document.getElementById('modal-msg').innerHTML = errorBanner(e.message);
    }
  };
}

/** Quita una visita de la línea de tiempo (el checklist vigente no se toca). */
async function quitarVisitaBpa(fincaId, visitaId) {
  if (!confirm('¿Quitar esta visita de la trazabilidad BPA? El checklist vigente no se modifica.')) return;
  try {
    await api(`/fincas/${fincaId}/bpa/visitas/${visitaId}`, { method: 'DELETE', headers: headers() });
    await cargarBpa();
  } catch (e) {
    alert('No se pudo quitar la visita: ' + e.message);
  }
}

/* ══════════════════ Equipo de trabajo, comisiones y lista de trabajos (Admin) ══════════════════ */

const ROLES_EQUIPO_LABEL = {
  instrumentador: 'Instrumentador',
  cadenero_sensorista: 'Cadenero sensorista',
  chofer: 'Chofer',
  agronomo: 'Agrónomo',
};

async function cargarEquipo() {
  const lista = document.getElementById('equipo-lista');
  const tarifasDiv = document.getElementById('equipo-tarifas');
  const novedadesDiv = document.getElementById('equipo-novedades');
  lista.innerHTML = '<p class="muted">Cargando…</p>';
  const params = new URLSearchParams();
  const rol = document.getElementById('equipo-rol').value;
  const estado = document.getElementById('equipo-estado').value;
  const search = document.getElementById('equipo-search').value.trim();
  if (rol) params.set('rol', rol);
  if (estado) params.set('estado', estado);
  if (search) params.set('search', search);
  try {
    const [r, t, n] = await Promise.all([
      api(`/admin/equipo-trabajo?${params}`),
      api('/admin/equipo-trabajo/tarifas'),
      api('/admin/equipo-trabajo/novedades?estado=abierta'),
    ]);
    lista.innerHTML = (r.data || []).map(e => `
      <div class="labor-row">
        <div class="labor-info">
          <b>${esc(e.nombre_completo)}</b>
          <span class="muted">${esc(e.tipo_documento)} ${esc(e.numero_documento)} · ${esc(e.rol_etiqueta)}</span>
          <span>${e.estado === 'activo' ? badge('Activo', 'ok') : badge('Desvinculado', 'warning')} ·
            ingreso ${esc(e.fecha_ingreso)} · ${e.valor_dia_cop != null ? `$${fmtNum(e.valor_dia_cop, 0)}/día` : 'sin tarifa'}</span>
          <span class="muted">☎ ${esc(e.numero_contacto || '—')} · emergencia: ${esc(e.contacto_emergencia_nombre || '—')} (${esc(e.contacto_emergencia_telefono || '—')})</span>
        </div>
        <div class="row-actions">
          <button type="button" class="btn-ghost-sm" data-editar="${esc(e.id)}">✏️ Editar</button>
          <button type="button" class="btn-ghost-sm" data-novedad="${esc(e.id)}" data-nombre="${esc(e.nombre_completo)}">🏥 Novedad</button>
          ${e.estado === 'activo' ? `<button type="button" class="btn-ghost-sm" data-desvincular="${esc(e.id)}">🗑️ Desvincular</button>` : ''}
        </div>
      </div>`).join('') || '<p class="muted">Sin empleados registrados.</p>';
    lista.querySelectorAll('[data-editar]').forEach(b => b.addEventListener('click', () => {
      const emp = (r.data || []).find(e => e.id === b.dataset.editar);
      if (emp) abrirModalEmpleado(emp);
    }));
    lista.querySelectorAll('[data-desvincular]').forEach(b => b.addEventListener('click', async () => {
      if (!confirm('¿Desvincular este empleado? Queda conservado en la trazabilidad.')) return;
      await api(`/admin/equipo-trabajo/${b.dataset.desvincular}`, { method: 'DELETE', headers: headers() });
      await cargarEquipo();
    }));
    lista.querySelectorAll('[data-novedad]').forEach(b => b.addEventListener('click', () => abrirModalNovedad(b.dataset.novedad, b.dataset.nombre)));

    tarifasDiv.innerHTML = (t.data || []).map(x => `
      <div class="labor-row"><div class="labor-info"><b>${esc(x.rol_etiqueta)}</b>
        <span class="muted">valor por día de trabajo</span></div>
        <label class="field-inline"><span>$ COP</span><input type="number" min="0" step="1000"
          data-tarifa-rol="${esc(x.rol)}" value="${x.valor_dia_cop ?? ''}" placeholder="Ej. 120000" /></label></div>`).join('');
    tarifasDiv.querySelectorAll('[data-tarifa-rol]').forEach(inp => inp.addEventListener('change', async () => {
      if (inp.value === '' || Number(inp.value) < 0) return;
      await api(`/admin/equipo-trabajo/tarifas/${inp.dataset.tarifaRol}`, {
        method: 'PUT', headers: headers(),
        body: JSON.stringify({ valor_dia_cop: Number(inp.value) }),
      });
      await cargarEquipo();
    }));

    novedadesDiv.innerHTML = (n.data || []).map(x => `
      <div class="labor-row"><div class="labor-info">
        <b>🏥 ${esc(x.empleado_nombre)}</b>
        <span class="muted">${esc(x.tipo)} · desde ${esc(x.fecha_inicio)}${x.fecha_fin ? ` hasta ${esc(x.fecha_fin)}` : ''}${x.reemplazo_nombre ? ` · reemplazo: ${esc(x.reemplazo_nombre)}` : ''}</span>
      </div>
      <button type="button" class="btn-ghost-sm" data-cerrar-nov="${esc(x.id)}">✅ Cerrar novedad</button></div>`).join('')
      || '<p class="muted">Sin novedades abiertas.</p>';
    novedadesDiv.querySelectorAll('[data-cerrar-nov]').forEach(b => b.addEventListener('click', async () => {
      await api(`/admin/equipo-trabajo/novedades/${b.dataset.cerrarNov}/cerrar`, { method: 'PUT', headers: headers() });
      await cargarEquipo();
    }));
  } catch (e) {
    lista.innerHTML = errorBanner(e.message);
  }
}

function abrirModalEmpleado(emp = null) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = emp ? '✏️ Editar empleado' : '➕ Registrar empleado';
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="form-grid">
      <label class="field"><span>Nombres *</span><input id="eq-nombres" maxlength="120" value="${esc(emp?.nombres || '')}" /></label>
      <label class="field"><span>Apellidos *</span><input id="eq-apellidos" maxlength="120" value="${esc(emp?.apellidos || '')}" /></label>
      <label class="field"><span>Tipo documento</span>
        <select id="eq-tipo">${['CC', 'CE', 'TI', 'PASAPORTE', 'NIT'].map(t => `<option value="${t}" ${emp?.tipo_documento === t ? 'selected' : ''}>${t}</option>`).join('')}</select></label>
      <label class="field"><span>Número documento *</span><input id="eq-doc" maxlength="20" value="${esc(emp?.numero_documento || '')}" /></label>
      <label class="field"><span>Lugar de domicilio</span><input id="eq-domicilio" maxlength="200" value="${esc(emp?.lugar_domicilio || '')}" /></label>
      <label class="field"><span>Número de contacto</span><input id="eq-contacto" maxlength="20" value="${esc(emp?.numero_contacto || '')}" /></label>
      <label class="field"><span>Contacto de emergencia (nombre)</span><input id="eq-emergencia-n" maxlength="200" value="${esc(emp?.contacto_emergencia_nombre || '')}" /></label>
      <label class="field"><span>Contacto de emergencia (teléfono)</span><input id="eq-emergencia-t" maxlength="20" value="${esc(emp?.contacto_emergencia_telefono || '')}" /></label>
      <label class="field"><span>Rol *</span>
        <select id="eq-rol">${Object.entries(ROLES_EQUIPO_LABEL).map(([k, v]) => `<option value="${k}" ${emp?.rol === k ? 'selected' : ''}>${v}</option>`).join('')}</select></label>
      <label class="field"><span>Fecha de ingreso *</span><input id="eq-ingreso" type="date" value="${esc(emp?.fecha_ingreso || '')}" /></label>
      <label class="field"><span>Estado</span>
        <select id="eq-estado"><option value="activo" ${emp?.estado !== 'desvinculado' ? 'selected' : ''}>Activo</option>
          <option value="desvinculado" ${emp?.estado === 'desvinculado' ? 'selected' : ''}>Desvinculado</option></select></label>
      <label class="field"><span>Valor día (COP) — opcional</span><input id="eq-valor" type="number" min="0" step="1000" value="${emp?.valor_dia_cop ?? ''}" /></label>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = async () => {
    const body = {
      nombres: document.getElementById('eq-nombres').value.trim(),
      apellidos: document.getElementById('eq-apellidos').value.trim(),
      tipo_documento: document.getElementById('eq-tipo').value,
      numero_documento: document.getElementById('eq-doc').value.trim(),
      lugar_domicilio: document.getElementById('eq-domicilio').value.trim() || null,
      numero_contacto: document.getElementById('eq-contacto').value.trim() || null,
      contacto_emergencia_nombre: document.getElementById('eq-emergencia-n').value.trim() || null,
      contacto_emergencia_telefono: document.getElementById('eq-emergencia-t').value.trim() || null,
      rol: document.getElementById('eq-rol').value,
      fecha_ingreso: document.getElementById('eq-ingreso').value,
      estado: document.getElementById('eq-estado').value,
    };
    const valor = document.getElementById('eq-valor').value;
    body.valor_dia_cop = valor === '' ? null : Number(valor);
    if (!body.nombres || !body.apellidos || !body.numero_documento || !body.fecha_ingreso) {
      document.getElementById('modal-msg').innerHTML = errorBanner('Complete los campos obligatorios (*).');
      return;
    }
    try {
      if (emp) {
        await api(`/admin/equipo-trabajo/${emp.id}`, { method: 'PUT', headers: headers(), body: JSON.stringify(body) });
      } else {
        await api('/admin/equipo-trabajo', { method: 'POST', headers: headers(), body: JSON.stringify(body) });
      }
      cerrarModal();
      await cargarEquipo();
    } catch (e) {
      document.getElementById('modal-msg').innerHTML = errorBanner(e.message);
    }
  };
}

async function abrirModalNovedad(empleadoId, nombre) {
  const m = document.getElementById('modal-editor');
  document.getElementById('modal-titulo').textContent = `🏥 Novedad — ${nombre}`;
  let coms = { data: [] };
  let equipo = { data: [] };
  try {
    coms = await api('/admin/comisiones?estado=asignada');
    equipo = await api('/admin/equipo-trabajo?estado=activo');
  } catch { /* sin datos: modal sigue funcionando */ }
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="form-grid">
      <label class="field"><span>Tipo *</span>
        <select id="nov-tipo"><option value="incapacidad">Incapacidad</option>
          <option value="ausencia">Ausencia</option><option value="otro">Otro</option></select></label>
      <label class="field"><span>Fecha inicio *</span><input id="nov-inicio" type="date" value="${new Date().toISOString().slice(0, 10)}" /></label>
      <label class="field"><span>Fecha fin (opcional)</span><input id="nov-fin" type="date" /></label>
      <label class="field"><span>Comisión afectada (opcional)</span>
        <select id="nov-comision"><option value="">—</option>${(coms.data || []).map(c => `<option value="${esc(c.id)}">${esc(c.finca_nombre || c.finca_id)} · ${esc(c.estado)}</option>`).join('')}</select></label>
      <label class="field"><span>Reemplazo (opcional)</span>
        <select id="nov-reemplazo"><option value="">— Sin reemplazo —</option>${(equipo.data || []).filter(e => e.id !== empleadoId).map(e => `<option value="${esc(e.id)}">${esc(e.nombre_completo)} (${esc(e.rol_etiqueta)})</option>`).join('')}</select></label>
      <label class="field"><span>Descripción</span><textarea id="nov-desc" rows="2"></textarea></label>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = async () => {
    const body = {
      tipo: document.getElementById('nov-tipo').value,
      fecha_inicio: document.getElementById('nov-inicio').value,
      fecha_fin: document.getElementById('nov-fin').value || null,
      comision_id: document.getElementById('nov-comision').value || null,
      reemplazo_empleado_id: document.getElementById('nov-reemplazo').value || null,
      descripcion: document.getElementById('nov-desc').value.trim() || null,
    };
    if (!body.fecha_inicio) {
      document.getElementById('modal-msg').innerHTML = errorBanner('Indique la fecha de inicio.');
      return;
    }
    try {
      await api(`/admin/equipo-trabajo/${empleadoId}/novedades`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
      cerrarModal();
      await cargarEquipo();
    } catch (e) {
      document.getElementById('modal-msg').innerHTML = errorBanner(e.message);
    }
  };
}

async function cargarComisiones() {
  const sel = document.getElementById('com-finca');
  if (sel && !sel.options.length) {
    sel.innerHTML = '<option value="">Todas las fincas</option>' + state.fincas.map(f => `<option value="${esc(f.id)}">${esc(f.nombre)}</option>`).join('');
  }
  const params = new URLSearchParams();
  if (sel.value) params.set('finca_id', sel.value);
  const estado = document.getElementById('com-estado').value;
  if (estado) params.set('estado', estado);
  const lista = document.getElementById('com-lista');
  lista.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const r = await api(`/admin/comisiones?${params}`);
    lista.innerHTML = (r.data || []).map(c => `
      <div class="labor-row">
        <div class="labor-info">
          <b>🗂️ ${esc(c.finca_nombre || c.finca_id)}</b>
          <span class="muted">${esc(c.servicio || 'servicio sin especificar')} · asignada ${esc(c.fecha_asignacion)} · inicio ${esc(c.fecha_inicio_tomas || '—')} · fin ${esc(c.fecha_fin_tomas || '—')}</span>
          <span>${badge(c.estado, c.estado === 'finalizada' ? 'ok' : c.estado === 'cancelada' ? 'warning' : '')}
            · comisión ${c.valor_comision_cop != null ? `$${fmtNum(c.valor_comision_cop, 0)}` : '—'}
            · cobro ${c.valor_cobro_servicio_cop != null ? `$${fmtNum(c.valor_cobro_servicio_cop, 0)}` : '—'}
            · validación ${c.valor_validacion_cop != null ? `$${fmtNum(c.valor_validacion_cop, 0)}` : '—'}
            · plataforma ${c.valor_plataforma_cop != null ? `$${fmtNum(c.valor_plataforma_cop, 0)}` : '—'}</span>
          <span class="muted">${(c.miembros || []).map(x => `${esc(x.nombre)} (${esc(ROLES_EQUIPO_LABEL[x.rol_en_comision] || x.rol_en_comision)})`).join(' · ')}</span>
        </div>
        <div class="row-actions">
          ${c.estado === 'asignada' ? `<button type="button" class="btn-ghost-sm" data-fin="${esc(c.id)}">✅ Registrar fin de medición</button>` : ''}
          ${c.estado !== 'finalizada' ? `<button type="button" class="btn-ghost-sm" data-cancel="${esc(c.id)}">🗑️ Cancelar</button>` : ''}
        </div>
      </div>`).join('') || '<p class="muted">Sin comisiones registradas.</p>';
    lista.querySelectorAll('[data-fin]').forEach(b => b.addEventListener('click', async () => {
      if (!confirm('Registrar el fin de la medición de esta comisión (libera el equipo para otra finca)?')) return;
      await api(`/admin/comisiones/${b.dataset.fin}/finalizar`, { method: 'POST', headers: headers(), body: JSON.stringify({}) });
      await cargarComisiones();
    }));
    lista.querySelectorAll('[data-cancel]').forEach(b => b.addEventListener('click', async () => {
      if (!confirm('¿Cancelar esta comisión?')) return;
      await api(`/admin/comisiones/${b.dataset.cancel}`, { method: 'DELETE', headers: headers() });
      await cargarComisiones();
    }));
  } catch (e) {
    lista.innerHTML = errorBanner(e.message);
  }
}

async function abrirModalComision() {
  const m = document.getElementById('modal-editor');
  const [equipo] = await Promise.all([api('/admin/equipo-trabajo?estado=activo')]);
  const activos = equipo.data || [];
  const porRol = (rol) => activos.filter(e => e.rol === rol);
  document.getElementById('modal-titulo').textContent = '🗂️ Crear comisión';
  document.getElementById('modal-cuerpo').innerHTML = `
    <div class="form-grid">
      <label class="field"><span>Finca *</span>
        <select id="com-f">${state.fincas.map(f => `<option value="${esc(f.id)}">${esc(f.nombre)}</option>`).join('')}</select></label>
      <label class="field"><span>Servicio / tipo de reporte</span>
        <select id="com-servicio"><option value="">—</option>
          <option value="muestreo_suelos">Muestreo de suelos</option>
          <option value="recomendacion_siembra">Recomendación de siembra</option>
          <option value="reporte_completo">Reporte completo</option>
          <option value="balance_hidrico">Balance hídrico</option>
          <option value="trazabilidad_bpa">Trazabilidad BPA</option>
          <option value="otro">Otro</option></select></label>
      <label class="field"><span>Fecha de asignación *</span><input id="com-fasignacion" type="date" value="${new Date().toISOString().slice(0, 10)}" /></label>
      <label class="field"><span>Fecha inicio de tomas</span><input id="com-finicio" type="date" /></label>
      <label class="field"><span>Instrumentador *</span>
        <select id="com-instrumentador">${porRol('instrumentador').map(e => `<option value="${esc(e.id)}">${esc(e.nombre_completo)}</option>`).join('')}</select></label>
      <label class="field"><span>Cadeneros sensoristas * (Ctrl+clic para varios)</span>
        <select id="com-cadeneros" multiple size="4">${porRol('cadenero_sensorista').map(e => `<option value="${esc(e.id)}">${esc(e.nombre_completo)}</option>`).join('')}</select></label>
      <label class="field"><span>Chofer (opcional)</span>
        <select id="com-chofer"><option value="">—</option>${porRol('chofer').map(e => `<option value="${esc(e.id)}">${esc(e.nombre_completo)}</option>`).join('')}</select></label>
      <label class="field"><span>Agrónomo (opcional)</span>
        <select id="com-agronomo"><option value="">—</option>${porRol('agronomo').map(e => `<option value="${esc(e.id)}">${esc(e.nombre_completo)}</option>`).join('')}</select></label>
      <label class="field"><span>Valor comisión (COP)</span><input id="com-vcomision" type="number" min="0" step="10000" /></label>
      <label class="field"><span>Valor cobro servicio (COP)</span><input id="com-vcobro" type="number" min="0" step="10000" /></label>
      <label class="field"><span>Valor validación estudio (COP)</span><input id="com-vvalidacion" type="number" min="0" step="10000" /></label>
      <label class="field"><span>Valor plataforma (COP)</span><input id="com-vplataforma" type="number" min="0" step="10000" /></label>
      <label class="field"><span>Observaciones</span><textarea id="com-obs" rows="2"></textarea></label>
    </div>`;
  document.getElementById('modal-msg').innerHTML = '';
  m.classList.remove('hidden');
  document.getElementById('modal-guardar').onclick = async () => {
    const miembros = [];
    const instrumentador = document.getElementById('com-instrumentador').value;
    if (instrumentador) miembros.push({ empleado_id: instrumentador, rol_en_comision: 'instrumentador' });
    [...document.getElementById('com-cadeneros').selectedOptions].forEach(o => miembros.push({ empleado_id: o.value, rol_en_comision: 'cadenero_sensorista' }));
    const chofer = document.getElementById('com-chofer').value;
    if (chofer) miembros.push({ empleado_id: chofer, rol_en_comision: 'chofer' });
    const agronomo = document.getElementById('com-agronomo').value;
    if (agronomo) miembros.push({ empleado_id: agronomo, rol_en_comision: 'agronomo' });
    const num = (id) => { const v = document.getElementById(id).value; return v === '' ? null : Number(v); };
    const body = {
      finca_id: document.getElementById('com-f').value,
      servicio: document.getElementById('com-servicio').value || null,
      fecha_asignacion: document.getElementById('com-fasignacion').value,
      fecha_inicio_tomas: document.getElementById('com-finicio').value || null,
      miembros,
      valor_comision_cop: num('com-vcomision'),
      valor_cobro_servicio_cop: num('com-vcobro'),
      valor_validacion_cop: num('com-vvalidacion'),
      valor_plataforma_cop: num('com-vplataforma'),
      observaciones: document.getElementById('com-obs').value.trim() || null,
    };
    if (!body.fecha_asignacion) {
      document.getElementById('modal-msg').innerHTML = errorBanner('Indique la fecha de asignación.');
      return;
    }
    try {
      await api('/admin/comisiones', { method: 'POST', headers: headers(), body: JSON.stringify(body) });
      cerrarModal();
      await cargarComisiones();
    } catch (e) {
      document.getElementById('modal-msg').innerHTML = errorBanner(e.message);
    }
  };
}

async function cargarListaTrabajos() {
  const params = new URLSearchParams();
  const etapa = document.getElementById('lt-etapa').value;
  const estado = document.getElementById('lt-estado').value;
  const desde = document.getElementById('lt-desde').value;
  const hasta = document.getElementById('lt-hasta').value;
  if (etapa) params.set('etapa', etapa);
  if (estado) params.set('estado', estado);
  if (desde) params.set('desde', desde);
  if (hasta) params.set('hasta', hasta);
  const lista = document.getElementById('lt-lista');
  const chart = document.getElementById('lt-chart');
  lista.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const r = await api(`/admin/lista-trabajos?${params}`);
    const conteos = r.conteos_por_etapa || {};
    const maxEtapa = Math.max(1, ...Object.values(conteos));
    chart.innerHTML = `
      <h3>📈 Órdenes de trabajo por etapa</h3>
      ${Object.entries(r.etiquetas_etapa || {}).map(([k, v]) => `
        <div class="chart-row">
          <span class="chart-label">${esc(v)}</span>
          <div class="chart-bar"><div style="width:${Math.round((conteos[k] || 0) * 100 / maxEtapa)}%"></div></div>
          <span class="chart-num">${conteos[k] || 0}</span>
        </div>`).join('')}
      <p class="muted">Pendientes: ${(r.conteos_por_estado || {}).pendiente || 0} · En proceso: ${(r.conteos_por_estado || {}).en_proceso || 0} · Finalizadas: ${(r.conteos_por_estado || {}).finalizada || 0}</p>`;
    lista.innerHTML = (r.data || []).map(d => `
      <div class="labor-row" style="border-left:6px solid ${esc(d.semaforo)}">
        <div class="labor-info">
          <b>🏡 ${esc(d.nombre)}</b>
          <span class="muted">${esc(d.municipio || '—')} · ${esc(d.cultivo_sembrado || 'sin cultivo')}</span>
          <span>${badge(d.etapa_etiqueta, d.etapa === 'finalizada' ? 'ok' : d.etapa === 'reporte' ? 'ok' : 'warning')}
            · estado: ${esc(d.estado)} · inicio ${esc(d.fecha_inicio || '—')} · fin ${esc(d.fecha_fin || '—')}</span>
          ${(d.faltantes || []).length ? `<span class="muted">⚠️ Faltan: ${d.faltantes.map(esc).join(' · ')}</span>` : '<span>✅ Todas las actividades completas</span>'}
        </div>
      </div>`).join('') || '<p class="muted">No hay fincas que coincidan con los filtros.</p>';
  } catch (e) {
    lista.innerHTML = errorBanner(e.message);
  }
}

async function reentrenarModelo() {
  const msg = document.getElementById('ml-msg');
  msg.innerHTML = '<p class="muted">Encolando…</p>';
  try {
    const r = await api('/admin/ml/reentrenar', {
      method: 'POST', headers: headers(),
      body: JSON.stringify({ cultivos_incluidos: [], modo: document.getElementById('ml-modo').value }),
    });
    msg.innerHTML = `<p class="ok">✅ Job <code>${esc(r.job_id.slice(0, 8))}…</code> en cola (${esc(r.estado)}). ${esc(r.mensaje)}</p>`;
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
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

const CALIDAD_LECTURA = {
  OK: 'OK',
  'npk sin calibrar': 'npk sin calibrar',
  estimado_por_sig: '🗺️ estimado SIG',
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
          <td>${badge(CALIDAD_LECTURA[r.calidad] || (r.calidad || '—'), r.calidad === 'OK' ? 'ok' : r.calidad === 'estimado_por_sig' ? 'textura' : 'warning')}</td>
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
    ${pe.advertencia_precios ? `<div class="advertencia" style="margin:8px 0">${esc(pe.advertencia_precios)}</div>` : ''}
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
    const conMercado = a.sugerencias_cultivos.some(s => s.precio_promedio_cop_kg != null);
    html += `<h3 style="margin-top:18px">🌾 Cultivos sugeridos (ranking del motor)</h3>`;
    html += `
      <div class="table-wrap"><table>
        <tr><th>#</th><th>Cultivo</th><th>Score</th><th>Clasificación</th><th>Confianza</th>${conMercado ? '<th>Precio COP/kg</th><th>Utilidad COP/ha</th>' : ''}<th>Reglas</th><th>Descripción de reglas aplicadas</th></tr>
        ${a.sugerencias_cultivos.map((s, i) => `
          <tr>
            <td>${i + 1}</td>
            <td>${esc(s.icono || '')} ${esc(s.cultivo)}${s.mas_rentable ? ' <span class="badge ok">Más rentable</span>' : ''}${s.nota_secano ? `<div class="muted" style="font-size:0.75rem">${esc(s.nota_secano)}</div>` : ''}</td>
            <td>${fmtNum(s.score, 1)}</td>
            <td>${badge(s.clasificacion, badgeClase(s.clasificacion))}</td>
            <td>${Math.round((s.confianza || 0) * 100)}%</td>
            ${conMercado ? `<td>${s.precio_promedio_cop_kg != null ? '$ ' + fmtNum(s.precio_promedio_cop_kg, 0) : '—'}</td><td>${s.utilidad_estimada_cop_ha != null ? '$ ' + fmtNum(s.utilidad_estimada_cop_ha, 0) : '—'}</td>` : ''}
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
      return c ? `${iconoCultivo(c.icono)} ${c.nombre}` : id;
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

/* ────────────────────── precios de insumos (admin, ROI) ────────────────────── */

const PRODUCTOS_INSUMOS = [
  ['Cal dolomítica', 'pH (enmienda)'],
  ['Urea', 'Nitrógeno (N)'],
  ['DAP', 'Fósforo (P)'],
  ['KCl', 'Potasio (K)'],
  ['Compost', 'Materia orgánica (MO)'],
  ['Yeso agrícola', 'Calcio (Ca)'],
  ['Sulfato de magnesio', 'Magnesio (Mg)'],
  ['Azufre elemental', 'Azufre (S)'],
  ['Quelato de hierro', 'Hierro (Fe)'],
  ['Sulfato de manganeso', 'Manganeso (Mn)'],
  ['Sulfato de zinc', 'Zinc (Zn)'],
  ['Sulfato de cobre', 'Cobre (Cu)'],
  ['Bórax', 'Boro (B)'],
  ['Enmienda orgánica', 'CIC (gradual)'],
];

async function cargarPreciosInsumos() {
  const div = document.getElementById('precios-lista');
  if (!div || (state.rol || '').toLowerCase() !== 'admin') return;
  div.innerHTML = '<p class="muted">Cargando precios…</p>';
  let precios = [];
  try {
    const r = await api('/admin/precios-insumos');
    precios = r.data || [];
  } catch (e) {
    div.innerHTML = errorBanner(e.message);
    return;
  }
  const porProducto = {};
  precios.forEach(p => { porProducto[p.producto] = p; });
  div.innerHTML = `
    <div class="table-wrap"><table>
      <tr><th>Producto</th><th>Uso</th><th>Precio (COP/kg)</th><th>Actualizado</th></tr>
      ${PRODUCTOS_INSUMOS.map(([prod, uso]) => {
        const p = porProducto[prod];
        return `<tr>
          <td><b>${esc(prod)}</b></td>
          <td>${esc(uso)}</td>
          <td><input type="number" min="0.01" step="0.01" data-precio-prod="${esc(prod)}" value="${p ? p.precio_kg_cop : ''}" placeholder="Sin registro" /></td>
          <td>${p ? esc(p.fecha_actualizacion) : badge('estático', 'warning')}</td>
        </tr>`;
      }).join('')}
    </table></div>
    <button type="button" class="btn btn-primary" onclick="guardarPreciosInsumos()" style="margin-top:10px">💾 Guardar precios</button>`;
}

async function guardarPreciosInsumos() {
  const msg = document.getElementById('precios-msg');
  const items = [];
  document.querySelectorAll('[data-precio-prod]').forEach(el => {
    const val = parseFloat(el.value);
    if (Number.isFinite(val) && val > 0) {
      items.push({ producto: el.dataset.precioProd, precio_kg_cop: val });
    }
  });
  if (!items.length) {
    msg.innerHTML = errorBanner('Ingrese al menos un precio válido.');
    return;
  }
  try {
    const r = await api('/admin/precios-insumos', {
      method: 'PUT', headers: headers(),
      body: JSON.stringify({ precios: items }),
    });
    msg.innerHTML = okBanner(`💰 ${r.actualizados.length} precio(s) actualizado(s) (${esc(r.fecha_actualizacion)}). El ROI usará estas cotizaciones.`);
    await cargarPreciosInsumos();
  } catch (e) {
    msg.innerHTML = errorBanner(e.message);
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
  const modeloEl = document.getElementById('repo-modelo');
  const presupuesto = presEl && presEl.value ? Number(presEl.value) : null;
  const rendimiento = rendEl && rendEl.value ? Number(rendEl.value) : null;
  const modeloPronostico = modeloEl && modeloEl.value ? modeloEl.value : 'ambos';

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
        modelo_pronostico: modeloPronostico,
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
        <div class="icono">${iconoImgCultivo(c)}</div>
        <h3>${esc(c.nombre)}</h3>
        ${c.nombre_cientifico ? `<p><i>${esc(c.nombre_cientifico)}</i></p>` : ''}
        ${c.descripcion ? `<p>${esc(c.descripcion)}</p>` : ''}
        ${fisio.length ? `<p class="muted mono">🌱 ${fisio.join(' · ')}</p>` : ''}
        ${c.activo === false ? badge('Inactivo', 'critical') : badge('Activo', 'ok')}
        <div class="device-actions">
          <button type="button" class="btn btn-ghost" data-cultivo-medicion="${esc(c.id)}">📏 Detalle medición</button>
          <button type="button" class="btn btn-ghost" data-cultivo-curva="${esc(c.id)}" data-nombre="${esc(c.nombre)}">📈 Curva de extracción</button>
          <button type="button" class="btn btn-ghost" data-cultivo-variedades="${esc(c.id)}" data-nombre="${esc(c.nombre)}">🌾 Variedades</button>
        </div>
      </div>`;
    }).join('')
    : '<p class="muted">Sin resultados.</p>';
  div.querySelectorAll('[data-cultivo-medicion]').forEach(b => {
    b.addEventListener('click', () => {
      const c = state.catalogo.find(x => x.id === b.dataset.cultivoMedicion);
      if (c) verDetalleMedicion(c);
    });
  });
  div.querySelectorAll('[data-cultivo-curva]').forEach(b => {
    b.addEventListener('click', () => verCurva(b.dataset.cultivoCurva, b.dataset.nombre || ''));
  });
  div.querySelectorAll('[data-cultivo-variedades]').forEach(b => {
    b.addEventListener('click', () => verVariedades(b.dataset.cultivoVariedades, b.dataset.nombre || ''));
  });
}

document.addEventListener('DOMContentLoaded', init);
