/* AgroIA — Lectura en voz alta de respuestas (RFP-AGROIA-002).
 *
 * Motor por defecto: Web Speech API (`speechSynthesis`). Si el navegador no
 * soporta síntesis o falla, se usa el respaldo en servidor (/lectura/sintetizar).
 * La preferencia (activado, voz, velocidad) se persiste por cuenta.
 */
'use strict';

const LECTURA = {
  soportado: false,
  activado: false,
  voz: 'femenina',
  velocidad: '1',
  hablando: false,
};

/* ─────────────────────────── utilidades ─────────────────────────── */

function limpiarTextoLectura(texto) {
  let t = String(texto || '');
  t = t.replace(/!\[[^\]]*\]\([^)]*\)/g, ' imagen ');
  t = t.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1');
  t = t.replace(/(\*\*|__)(.*?)\1/g, '$2');
  t = t.replace(/(\*|_)(.*?)\1/g, '$2');
  t = t.replace(/`([^`]*)`/g, '$1');
  t = t.replace(/^#{1,6}\s*/gm, '');
  t = t.replace(/^\s*[-*+]\s+/gm, '');
  t = t.replace(/^\s*\d+[.)]\s+/gm, '');
  t = t.replace(/\|/g, ' ');
  t = t.replace(/[*#_>~]/g, ' ');
  const unidades = {
    'kg/ha': 'kilos por hectárea',
    'g/ha': 'gramos por hectárea',
    't/ha': 'toneladas por hectárea',
    'meq/100 g': 'miliequivalentes por cien gramos',
    'cmol/kg': 'centimoles por kilo',
    'dS/m': 'decisiemens por metro',
    'ppm': 'partes por millón',
    '%': 'por ciento',
    '°C': 'grados centígrados',
    'pH': 'pe hache',
  };
  for (const [k, v] of Object.entries(unidades)) {
    t = t.split(k).join(' ' + v + ' ');
  }
  return t.replace(/\s{2,}/g, ' ').trim();
}

function registrarMetricaLectura(tipo, caracteres) {
  const body = { tipo };
  if (tipo === 'activacion' && caracteres != null) body.caracteres_leidos = caracteres;
  if (LECTURA.voz) body.voz_elegida = LECTURA.voz;
  fetch(API + '/lectura/metricas', {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body),
  }).catch(() => { /* best-effort */ });
}

function lecturaEstado(texto, clase) {
  const el = document.getElementById('lectura-estado');
  if (!el) return;
  el.textContent = texto || '';
  el.className = 'chat-voz-estado' + (clase ? ' ' + clase : '');
}

/* ─────────────────────────── síntesis ─────────────────────────── */

function vozRate() { return parseFloat(LECTURA.velocidad) || 1; }

function esFemenina(v) {
  const n = (v.name || '').toLowerCase();
  return /female|mujer|femenin|sabina|monica|paulina|maria|luisa|sofia|es-f/i.test(n);
}

function esMasculina(v) {
  const n = (v.name || '').toLowerCase();
  return /male|hombre|masculin|jorge|diego|pablo|carlos|es-m/i.test(n);
}

function elegirVozSintesis() {
  if (!window.speechSynthesis) return null;
  const voces = window.speechSynthesis.getVoices() || [];
  const es = voces.filter((v) => (v.lang || '').toLowerCase().startsWith('es'));
  const pool = es.length ? es : voces;
  const objetivo = LECTURA.voz === 'masculina' ? esMasculina : esFemenina;
  return pool.find(objetivo) || pool[0] || null;
}

function detenerLectura() {
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  LECTURA.hablando = false;
}

async function leerDesdeServidor(texto) {
  try {
    lecturaEstado('⏳ Preparando audio…', 'procesando');
    const res = await fetch(API + '/lectura/sintetizar', {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ texto, voz: LECTURA.voz, velocidad: LECTURA.velocidad }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const det = data && data.detail;
      lecturaEstado('No se pudo leer la respuesta: ' + ((det && (det.message || det.code)) || res.status), 'error');
      registrarMetricaLectura('error');
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.playbackRate = vozRate();
    audio.onended = () => { lecturaEstado(''); URL.revokeObjectURL(url); };
    audio.onerror = () => { lecturaEstado('No se pudo reproducir el audio.', 'error'); registrarMetricaLectura('error'); };
    audio.play();
    lecturaEstado('🔊 Reproduciendo…', 'grabando');
    registrarMetricaLectura('activacion', (texto || '').length);
  } catch (e) {
    lecturaEstado('No se pudo leer la respuesta.', 'error');
    registrarMetricaLectura('error');
  }
}

function leerTexto(texto) {
  const limpio = limpiarTextoLectura(texto);
  if (!limpio) return;
  if (!LECTURA.soportado) {
    leerDesdeServidor(limpio);
    return;
  }
  detenerLectura();
  const u = new SpeechSynthesisUtterance(limpio);
  const v = elegirVozSintesis();
  if (v) u.voice = v;
  u.lang = 'es-CO';
  u.rate = vozRate();
  u.onstart = () => {
    LECTURA.hablando = true;
    lecturaEstado(
      LECTURA.voz === 'mi-voz' ? '🔊 Reproduciendo (voz del navegador; la clonación se integrará en una fase posterior)' : '🔊 Reproduciendo…',
      'grabando',
    );
  };
  u.onend = () => { LECTURA.hablando = false; lecturaEstado(''); };
  u.onerror = (e) => {
    LECTURA.hablando = false;
    if (e.error === 'not-allowed' || e.error === 'synthesis-unavailable' || e.error === 'synthesis-failed') {
      leerDesdeServidor(limpio);
    } else {
      lecturaEstado('No se pudo leer la respuesta.', 'error');
      registrarMetricaLectura('error');
    }
  };
  window.speechSynthesis.speak(u);
  registrarMetricaLectura('activacion', limpio.length);
}

/* ─────────────────────────── chat: altavoz por respuesta + autolectura ─────────────────────────── */

function initChatLectura() {
  const cont = document.getElementById('chat-mensajes');
  if (!cont) return;

  const agregarBoton = (msgEl) => {
    if (msgEl.classList.contains('chat-typing')) return;
    if (msgEl.querySelector('.chat-leer-btn')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chat-leer-btn';
    btn.title = 'Leer en voz alta';
    btn.setAttribute('aria-label', 'Leer en voz alta');
    btn.innerHTML = '🔊';
    btn.addEventListener('click', (e) => { e.stopPropagation(); leerTexto(msgEl.textContent); });
    msgEl.appendChild(btn);
  };

  const observer = new MutationObserver((muts) => {
    for (const m of muts) {
      for (const nodo of m.addedNodes) {
        if (nodo.nodeType === 1 && nodo.classList && nodo.classList.contains('chat-msg')) {
          if (nodo.classList.contains('chat-bot')) {
            agregarBoton(nodo);
            if (LECTURA.activado && !nodo.classList.contains('chat-typing')) {
              leerTexto(nodo.textContent);
            }
          }
        }
      }
    }
  });
  observer.observe(cont, { childList: true });
  cont.querySelectorAll('.chat-msg.chat-bot').forEach(agregarBoton);
}

/* ─────────────────────────── preferencias del usuario ─────────────────────────── */

async function cargarPreferenciaLectura() {
  try {
    const p = await api('/lectura/preferencias');
    LECTURA.activado = p.activado !== false ? p.activado : false;
    LECTURA.voz = p.voz || 'femenina';
    LECTURA.velocidad = p.velocidad || '1';
  } catch (e) {
    LECTURA.activado = false;
  }
  const toggle = document.getElementById('lectura-toggle');
  if (toggle) toggle.checked = LECTURA.activado;
  const selVoz = document.getElementById('lectura-voz');
  if (selVoz) selVoz.value = LECTURA.voz;
  const selVel = document.getElementById('lectura-velocidad');
  if (selVel) selVel.value = LECTURA.velocidad;
  await refrescarOpcionMiVoz();
}

async function guardarPreferenciaLectura() {
  try {
    await api('/lectura/preferencias', {
      method: 'PUT',
      headers: headers(),
      body: JSON.stringify({ activado: LECTURA.activado, voz: LECTURA.voz, velocidad: LECTURA.velocidad }),
    });
  } catch (e) { /* best-effort */ }
}

async function refrescarOpcionMiVoz() {
  const opt = document.getElementById('lectura-mi-voz-option');
  if (!opt) return;
  try {
    const r = await api('/lectura/voz-personalizada');
    opt.hidden = !(r.existe && r.estado === 'activa');
  } catch (e) {
    opt.hidden = true;
  }
}

/* ─────────────────────────── voz personalizada (Fase 2, plus) ─────────────────────────── */

const MIVOZ = {
  grabando: false,
  chunks: [],
  recorder: null,
  stream: null,
  blob: null,
  inicio: 0,
  timer: null,
  audioCtx: null,
  rafNivel: null,
};

function miVozMsg(texto, clase) {
  const el = document.getElementById('mi-voz-msg');
  if (el) { el.textContent = texto || ''; el.className = 'muted' + (clase ? ' ' + clase : ''); }
}

function abrirModalMiVoz() {
  const modal = document.getElementById('modal-mi-voz');
  if (modal) modal.classList.remove('hidden');
  miVozMsg('');
  document.getElementById('mi-voz-guardar').classList.add('hidden');
  document.getElementById('mi-voz-preview').classList.add('hidden');
  // Previsualizar muestra existente, si la hay
  const audioEl = document.getElementById('mi-voz-preview');
  fetch(API + '/lectura/voz-personalizada/audio', { headers: headers() })
    .then((res) => {
      if (res.ok) {
        res.blob().then((b) => {
          audioEl.src = URL.createObjectURL(b);
          audioEl.classList.remove('hidden');
        });
      }
    })
    .catch(() => {});
}

function cerrarModalMiVoz() {
  detenerGrabacionMiVoz();
  const modal = document.getElementById('modal-mi-voz');
  if (modal) modal.classList.add('hidden');
}

async function grabarMiVoz() {
  if (!document.getElementById('mi-voz-consentimiento').checked) {
    miVozMsg('Debe marcar el consentimiento para grabar su voz.', 'error');
    return;
  }
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    miVozMsg('Permiso de micrófono denegado o micrófono no disponible.', 'error');
    return;
  }
  MIVOZ.stream = stream;
  MIVOZ.chunks = [];
  const recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (ev) => { if (ev.data.size) MIVOZ.chunks.push(ev.data); };
  recorder.onstop = () => {
    MIVOZ.grabando = false;
    clearInterval(MIVOZ.timer);
    detenerNivelMiVoz();
    stream.getTracks().forEach((t) => t.stop());
    MIVOZ.blob = new Blob(MIVOZ.chunks, { type: recorder.mimeType || 'audio/webm' });
    const url = URL.createObjectURL(MIVOZ.blob);
    const audioEl = document.getElementById('mi-voz-preview');
    audioEl.src = url;
    audioEl.classList.remove('hidden');
    document.getElementById('mi-voz-guardar').classList.remove('hidden');
    document.getElementById('mi-voz-grabar').classList.remove('hidden');
    document.getElementById('mi-voz-detener').classList.add('hidden');
    miVozMsg('Muestra lista. Puede escucharla y guardarla.', 'ok');
  };
  MIVOZ.recorder = recorder;
  MIVOZ.grabando = true;
  MIVOZ.inicio = Date.now();
  iniciarNivelMiVoz(stream);
  MIVOZ.timer = setInterval(() => {
    const seg = Math.round((Date.now() - MIVOZ.inicio) / 1000);
    document.getElementById('mi-voz-tiempo').textContent = seg + ' s';
    if (seg >= 30) detenerGrabacionMiVoz();
  }, 500);
  document.getElementById('mi-voz-grabar').classList.add('hidden');
  document.getElementById('mi-voz-detener').classList.remove('hidden');
  miVozMsg('Grabando… hable con naturalidad (máx. 30 s).', 'procesando');
  recorder.start();
}

function detenerGrabacionMiVoz() {
  if (MIVOZ.recorder && MIVOZ.recorder.state !== 'inactive') {
    MIVOZ.recorder.stop();
  }
}

function iniciarNivelMiVoz(stream) {
  if (!(window.AudioContext || window.webkitAudioContext)) return;
  try {
    MIVOZ.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = MIVOZ.audioCtx.createAnalyser();
    analyser.fftSize = 256;
    MIVOZ.audioCtx.createMediaStreamSource(stream).connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);
    const nivelEl = document.getElementById('mi-voz-nivel');
    if (nivelEl) nivelEl.classList.add('visible');
    const medir = () => {
      analyser.getByteTimeDomainData(data);
      let suma = 0;
      for (let i = 0; i < data.length; i++) { const v = (data[i] - 128) / 128; suma += v * v; }
      const rms = Math.sqrt(suma / data.length);
      if (nivelEl) nivelEl.querySelector('span').style.width = Math.min(100, rms * 400) + '%';
      MIVOZ.rafNivel = requestAnimationFrame(medir);
    };
    medir();
  } catch (e) {
    MIVOZ.audioCtx = null;
  }
}

function detenerNivelMiVoz() {
  if (MIVOZ.rafNivel) cancelAnimationFrame(MIVOZ.rafNivel);
  if (MIVOZ.audioCtx) { MIVOZ.audioCtx.close().catch(() => {}); }
  const nivelEl = document.getElementById('mi-voz-nivel');
  if (nivelEl) nivelEl.classList.remove('visible');
}

async function guardarMiVoz() {
  if (!document.getElementById('mi-voz-consentimiento').checked) {
    miVozMsg('Debe marcar el consentimiento para guardar su voz.', 'error');
    return;
  }
  if (!MIVOZ.blob) {
    miVozMsg('Grabe una muestra antes de guardar.', 'error');
    return;
  }
  miVozMsg('Guardando…', 'procesando');
  try {
    const fd = new FormData();
    fd.append('audio', MIVOZ.blob, 'mi-voz.webm');
    const res = await fetch(API + '/lectura/voz-personalizada', {
      method: 'POST',
      headers: headers(false),
      body: fd,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const det = data && data.detail;
      throw new Error((det && (det.message || det.code)) || 'Error al guardar');
    }
    if (data.estado === 'procesando') {
      miVozMsg('⏳ Clonando su voz en la nube… esto puede tardar unos minutos.', 'procesando');
      await refrescarOpcionMiVoz();
      const sel = document.getElementById('lectura-voz');
      if (sel) { sel.value = 'mi-voz'; LECTURA.voz = 'mi-voz'; guardarPreferenciaLectura(); }
      await esperarClonacionMiVoz();
      return;
    }
    miVozMsg('✅ Voz guardada. Aparecerá como "Mi voz" en el selector.', 'ok');
    await refrescarOpcionMiVoz();
    const sel = document.getElementById('lectura-voz');
    if (sel) { sel.value = 'mi-voz'; LECTURA.voz = 'mi-voz'; guardarPreferenciaLectura(); }
    setTimeout(cerrarModalMiVoz, 1200);
  } catch (e) {
    miVozMsg('No se pudo guardar la voz: ' + e.message, 'error');
  }
}

async function esperarClonacionMiVoz() {
  // Consulta el estado de clonación en el motor GPU hasta que quede activa.
  const maxIntentos = 20;
  for (let i = 0; i < maxIntentos; i++) {
    await new Promise((r) => setTimeout(r, 5000));
    try {
      const res = await api('/lectura/voz-personalizada/estado');
      if (res.estado === 'activa') {
        miVozMsg('✅ Voz clonada y lista para leer.', 'ok');
        await refrescarOpcionMiVoz();
        setTimeout(cerrarModalMiVoz, 1200);
        return;
      }
      if (res.estado === 'error') {
        miVozMsg('El motor no pudo clonar la voz. Intente con otra muestra.', 'error');
        return;
      }
    } catch (e) {
      /* reintenta */
    }
  }
  miVozMsg('La clonación sigue en curso; puede cerrar y volver más tarde.', 'procesando');
}

async function eliminarMiVoz() {
  if (!confirm('¿Eliminar su voz personalizada? Se borrará la muestra por completo.')) return;
  try {
    await api('/lectura/voz-personalizada', { method: 'DELETE', headers: headers() });
    if (LECTURA.voz === 'mi-voz') { LECTURA.voz = 'femenina'; const sel = document.getElementById('lectura-voz'); if (sel) sel.value = 'femenina'; guardarPreferenciaLectura(); }
    await refrescarOpcionMiVoz();
    miVozMsg('Voz eliminada.', 'ok');
    document.getElementById('mi-voz-preview').classList.add('hidden');
    document.getElementById('mi-voz-guardar').classList.add('hidden');
  } catch (e) {
    miVozMsg('No se pudo eliminar la voz: ' + e.message, 'error');
  }
}

/* ─────────────────────────── administración: métricas ─────────────────────────── */

async function cargarMetricasLectura() {
  const root = document.getElementById('lectura-metricas-root');
  if (!root) return;
  root.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const res = await api('/lectura/metricas');
    const data = res.data || [];
    const filas = data.length
      ? data.map((m) => `
        <tr>
          <td>${esc(m.periodo)}</td>
          <td>${m.activaciones}</td>
          <td>${esc(m.voz_elegida || '—')}</td>
          <td>${m.errores}</td>
          <td>${m.caracteres_leidos}</td>
        </tr>`).join('')
      : '<tr><td colspan="5" class="muted">Sin registros todavía.</td></tr>';
    root.innerHTML = `
      <h2>📈 Métricas de lectura en voz alta</h2>
      <p class="muted">Agregados mensuales — sin audio ni contenido de respuestas.</p>
      <table class="tabla">
        <thead><tr><th>Periodo</th><th>Activaciones</th><th>Voz elegida</th><th>Errores</th><th>Caracteres leídos</th></tr></thead>
        <tbody>${filas}</tbody>
      </table>`;
  } catch (err) {
    root.innerHTML = errorBanner(err.message);
  }
}

/* ─────────────────────────── inicialización ─────────────────────────── */

function initLectura() {
  LECTURA.soportado = !!(window.SpeechSynthesisUtterance && window.speechSynthesis);
  if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = () => { /* actualiza la lista curada */ };
    window.speechSynthesis.getVoices();
  }

  const toggle = document.getElementById('lectura-toggle');
  if (toggle) {
    toggle.addEventListener('change', () => {
      LECTURA.activado = toggle.checked;
      guardarPreferenciaLectura();
      registrarMetricaLectura('activacion');
      if (!LECTURA.activado) { detenerLectura(); lecturaEstado(''); }
    });
  }
  const selVoz = document.getElementById('lectura-voz');
  if (selVoz) {
    selVoz.addEventListener('change', () => { LECTURA.voz = selVoz.value; guardarPreferenciaLectura(); });
  }
  const selVel = document.getElementById('lectura-velocidad');
  if (selVel) {
    selVel.addEventListener('change', () => { LECTURA.velocidad = selVel.value; guardarPreferenciaLectura(); });
  }
  const btnCrear = document.getElementById('lectura-crear-voz');
  if (btnCrear) btnCrear.addEventListener('click', abrirModalMiVoz);
  const btnEliminar = document.getElementById('lectura-eliminar-voz');
  if (btnEliminar) btnEliminar.addEventListener('click', eliminarMiVoz);

  // Controles del modal "Crear mi voz"
  const modalCerrar = document.getElementById('mi-voz-cerrar');
  if (modalCerrar) modalCerrar.addEventListener('click', cerrarModalMiVoz);
  const btnGrabar = document.getElementById('mi-voz-grabar');
  if (btnGrabar) btnGrabar.addEventListener('click', grabarMiVoz);
  const btnDetener = document.getElementById('mi-voz-detener');
  if (btnDetener) btnDetener.addEventListener('click', detenerGrabacionMiVoz);
  const btnGuardar = document.getElementById('mi-voz-guardar');
  if (btnGuardar) btnGuardar.addEventListener('click', guardarMiVoz);
  const btnEliminarModal = document.getElementById('mi-voz-eliminar');
  if (btnEliminarModal) btnEliminarModal.addEventListener('click', eliminarMiVoz);
  const overlay = document.getElementById('modal-mi-voz');
  if (overlay) overlay.addEventListener('click', (e) => { if (e.target === overlay) cerrarModalMiVoz(); });

  cargarPreferenciaLectura();
  initChatLectura();
}
