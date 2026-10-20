/* AgroIA — Interacción por voz en el Asesor agronómico (RFP-AGROIA-001).
 *
 * Enfoque híbrido (C): Web Speech API en el navegador por defecto y
 * transcripción en servidor (/voz/transcripcion) como respaldo. La
 * transcripción se inserta en el campo de texto para revisión/edición y
 * nunca se envía automáticamente. Comandos: enviar · borrar · cancelar ·
 * repetir (solo cuando se pronuncian solos).
 */
'use strict';

const VOZ = {
  soportado: false,
  modo: null, // 'webspeech' | 'servidor' | null
  activado: true,
  duracionMaxSeg: 60,
  idioma: 'es-CO',
  grabando: false,
  procesando: false,
  reconocimiento: null,
  recorder: null,
  chunks: [],
  inicio: 0,
  timerMax: null,
  transcripcion: '',
};

/* ─────────────────────────── utilidades ─────────────────────────── */

function vozSoportado() {
  return !!(window.SpeechRecognition || window.webkitSpeechRecognition) ||
    !!(navigator.mediaDevices && window.MediaRecorder);
}

function vozBtn() { return document.getElementById('chat-mic'); }
function vozInput() { return document.getElementById('chat-input'); }
function vozEstado() { return document.getElementById('chat-voz-estado'); }

function vozEstadoText(txt, clase) {
  const el = vozEstado();
  if (!el) return;
  el.textContent = txt || '';
  el.className = 'chat-voz-estado' + (clase ? ' ' + clase : '');
}

function vozError(mensaje) {
  vozEstadoText(mensaje, 'error');
  registrarMetricaVoz('error');
}

/* ─────────────────────────── métricas (RF-014 / TT-04) ─────────────────────────── */

function registrarMetricaVoz(tipo, duracionMs) {
  const body = { tipo };
  if (tipo === 'consulta' && duracionMs != null) body.duracion_ms = duracionMs;
  fetch(API + '/voz/metricas', {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify(body),
  }).catch(() => { /* métricas best-effort: no bloquear el flujo */ });
}

/* ─────────────────────────── parámetros de la función ─────────────────────────── */

async function cargarParametrosVozChat() {
  try {
    const p = await api('/voz/parametros');
    VOZ.activado = p.activado !== false;
    VOZ.duracionMaxSeg = p.duracion_maxima_segundos || 60;
    VOZ.idioma = (p.idioma || 'es').startsWith('es') ? 'es-CO' : (p.idioma || 'es');
    aplicarEstadoMic();
  } catch (e) {
    // Si no se pueden leer parámetros, se mantiene el comportamiento por defecto.
    VOZ.activado = true;
  }
}

function aplicarEstadoMic() {
  const btn = vozBtn();
  if (!btn) return;
  if (!VOZ.soportado) {
    btn.classList.add('hidden');
    return;
  }
  btn.classList.toggle('hidden', !VOZ.activado);
  btn.classList.toggle('recording', VOZ.grabando);
  btn.disabled = VOZ.procesando;
}

/* ─────────────────────────── captura y transcripción ─────────────────────────── */

function toggleVoz() {
  if (VOZ.grabando) { detenerVoz(); return; }
  iniciarVoz();
}

async function iniciarVoz() {
  const input = vozInput();
  if (!VOZ.soportado || !input) return;
  if (!VOZ.activado) {
    alert('La función de voz está desactivada por el administrador. Escriba su consulta.');
    return;
  }
  VOZ.transcripcion = '';
  if (window.SpeechRecognition || window.webkitSpeechRecognition) {
    await iniciarWebSpeech();
  } else {
    await iniciarGrabacionServidor();
  }
}

/* — Primario: Web Speech API — */

async function iniciarWebSpeech() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new SR();
  rec.lang = VOZ.idioma;
  rec.continuous = false;
  rec.interimResults = false;

  rec.onstart = () => {
    VOZ.grabando = true;
    VOZ.procesando = false;
    VOZ.inicio = Date.now();
    vozEstadoText('🎙️ Escuchando…', 'grabando');
    aplicarEstadoMic();
    armarTimerMax();
  };

  rec.onresult = (ev) => {
    let texto = '';
    for (let i = 0; i < ev.results.length; i++) {
      texto += ev.results[i][0].transcript;
    }
    VOZ.transcripcion = texto.trim();
  };

  rec.onerror = (ev) => {
    const err = ev.error || '';
    limpiarTimerMax();
    VOZ.grabando = false;
    aplicarEstadoMic();
    if (err === 'not-allowed' || err === 'service-not-allowed') {
      vozError('Permiso de micrófono denegado. Habilítelo en el navegador y vuelva a intentarlo; puede seguir escribiendo.');
    } else if (err === 'network') {
      vozError('Sin conexión o fallo del reconocimiento de voz. Escriba su consulta o intente de nuevo.');
      registrarMetricaVoz('error');
    } else if (err === 'no-speech') {
      vozEstadoText('No se detectó voz. Inténtelo de nuevo.', 'error');
    } else if (err === 'aborted') {
      vozEstadoText('');
    } else {
      // Otros errores (audio-capture, etc.) → probar respaldo en servidor
      iniciarGrabacionServidor();
    }
  };

  rec.onend = () => {
    limpiarTimerMax();
    VOZ.grabando = false;
    aplicarEstadoMic();
    if (VOZ.transcripcion) {
      procesarTranscripcion(VOZ.transcripcion, Date.now() - VOZ.inicio);
    }
  };

  VOZ.reconocimiento = rec;
  try {
    rec.start();
  } catch (e) {
    iniciarGrabacionServidor();
  }
}

function detenerVoz() {
  if (VOZ.reconocimiento) {
    try { VOZ.reconocimiento.stop(); } catch (e) { /* noop */ }
  }
  if (VOZ.recorder && VOZ.recorder.state !== 'inactive') {
    try { VOZ.recorder.stop(); } catch (e) { /* noop */ }
  }
  limpiarTimerMax();
}

/* — Respaldo: grabación con MediaRecorder → POST /voz/transcripcion — */

async function iniciarGrabacionServidor() {
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    vozError('Permiso de micrófono denegado o micrófono no disponible. Puede seguir escribiendo su consulta.');
    return;
  }
  const recorder = new MediaRecorder(stream);
  const chunks = [];
  // Indicador visual de nivel de audio (AnalyserNode → barra #chat-voz-nivel).
  const nivelEl = document.getElementById('chat-voz-nivel');
  let audioCtx = null;
  let rafNivel = null;
  if (window.AudioContext || window.webkitAudioContext) {
    try {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      audioCtx.createMediaStreamSource(stream).connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);
      if (nivelEl) nivelEl.classList.add('visible');
      const medir = () => {
        analyser.getByteTimeDomainData(data);
        let suma = 0;
        for (let i = 0; i < data.length; i++) {
          const v = (data[i] - 128) / 128;
          suma += v * v;
        }
        const rms = Math.sqrt(suma / data.length);
        if (nivelEl) nivelEl.querySelector('span').style.width = Math.min(100, rms * 400) + '%';
        rafNivel = requestAnimationFrame(medir);
      };
      medir();
    } catch (e) {
      audioCtx = null;
    }
  }
  const detenerNivel = () => {
    if (rafNivel) cancelAnimationFrame(rafNivel);
    if (audioCtx) { audioCtx.close().catch(() => {}); }
    if (nivelEl) nivelEl.classList.remove('visible');
  };
  recorder.ondataavailable = (ev) => { if (ev.data.size) chunks.push(ev.data); };
  recorder.onstop = async () => {
    detenerNivel();
    stream.getTracks().forEach((t) => t.stop());
    VOZ.grabando = false;
    VOZ.procesando = true;
    aplicarEstadoMic();
    vozEstadoText('⏳ Procesando…', 'procesando');
    const blob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
    try {
      const fd = new FormData();
      fd.append('audio', blob, 'consulta.webm');
      fd.append('idioma', 'es');
      const res = await fetch(API + '/voz/transcripcion', {
        method: 'POST',
        headers: headers(false),
        body: fd,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const det = data && data.detail;
        throw new Error((det && (det.message || det.code)) || 'Fallo de transcripción');
      }
      procesarTranscripcion(data.texto, Date.now() - VOZ.inicio);
    } catch (err) {
      VOZ.procesando = false;
      aplicarEstadoMic();
      vozError('No se pudo transcribir el audio: ' + err.message + '. Puede seguir escribiendo.');
      registrarMetricaVoz('error');
    }
  };
  VOZ.recorder = recorder;
  VOZ.chunks = chunks;
  VOZ.grabando = true;
  VOZ.inicio = Date.now();
  VOZ.transcripcion = '';
  vozEstadoText('🎙️ Escuchando…', 'grabando');
  aplicarEstadoMic();
  armarTimerMax();
  recorder.start();
}

function armarTimerMax() {
  limpiarTimerMax();
  VOZ.timerMax = setTimeout(() => {
    if (VOZ.grabando) detenerVoz();
  }, (VOZ.duracionMaxSeg || 60) * 1000);
}

function limpiarTimerMax() {
  if (VOZ.timerMax) { clearTimeout(VOZ.timerMax); VOZ.timerMax = null; }
}

/* ─────────────────────────── transcripción → campo → comandos ─────────────────────────── */

function procesarTranscripcion(texto, duracionMs) {
  VOZ.procesando = false;
  VOZ.transcripcion = '';
  aplicarEstadoMic();
  const normalizado = (texto || '').trim().toLowerCase().replace(/[.,!¿?¡]+$/g, '');
  const input = vozInput();
  if (!input) return;

  // Comandos de control (RF-08): solo si se pronuncian solos.
  if (normalizado === 'enviar') {
    registrarMetricaVoz('consulta', duracionMs);
    vozEstadoText('');
    enviarChat(new Event('submit'));
    return;
  }
  if (normalizado === 'borrar' || normalizado === 'cancelar') {
    input.value = '';
    vozEstadoText('Campo borrado.', 'ok');
    return;
  }
  if (normalizado === 'repetir') {
    vozEstadoText('');
    iniciarVoz();
    return;
  }

  // Contenido: insertar editable, sin envío automático (RF-05).
  input.value = (input.value ? input.value + ' ' : '') + (texto || '').trim();
  vozEstadoText('Transcripción lista. Revise y pulse Enviar.', 'ok');
  registrarMetricaVoz('consulta', duracionMs);
}

/* ─────────────────────────── administración (HU-07 / HU-08) ─────────────────────────── */

async function cargarVozParametros() {
  const root = document.getElementById('voz-params-root');
  if (!root) return;
  root.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const p = await api('/voz/parametros');
    root.innerHTML = `
      <h2>🎙️ Parámetros de voz</h2>
      <p class="muted">Controle la función de voz del Asesor agronómico (cambios inmediatos).</p>
      <div class="field">
        <label class="check"><input type="checkbox" id="voz-param-activado" ${p.activado ? 'checked' : ''}> Función de voz activada</label>
      </div>
      <div class="field">
        <label>Duración máxima por consulta (segundos)
          <input type="number" id="voz-param-duracion" min="5" max="300" value="${p.duracion_maxima_segundos}">
        </label>
      </div>
      <div class="field">
        <label>Idioma
          <input type="text" id="voz-param-idioma" maxlength="10" value="${esc(p.idioma)}">
        </label>
      </div>
      <button class="btn btn-primary" id="voz-param-guardar">💾 Guardar</button>
      <span id="voz-param-msg" class="muted"></span>`;
    document.getElementById('voz-param-guardar').addEventListener('click', guardarVozParametros);
  } catch (err) {
    root.innerHTML = errorBanner(err.message);
  }
}

async function guardarVozParametros() {
  const msg = document.getElementById('voz-param-msg');
  msg.textContent = 'Guardando…';
  const body = {
    activado: document.getElementById('voz-param-activado').checked,
    duracion_maxima_segundos: Number(document.getElementById('voz-param-duracion').value),
    idioma: document.getElementById('voz-param-idioma').value,
  };
  try {
    await api('/voz/parametros', { method: 'PUT', headers: headers(), body: JSON.stringify(body) });
    msg.textContent = '✅ Guardado.';
    await cargarParametrosVozChat();
  } catch (err) {
    msg.textContent = '❌ ' + err.message;
  }
}

async function cargarVozMetricas() {
  const root = document.getElementById('voz-metricas-root');
  if (!root) return;
  root.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const res = await api('/voz/metricas');
    const data = res.data || [];
    const filas = data.length
      ? data.map((m) => `
        <tr>
          <td>${esc(m.periodo)}</td>
          <td>${m.consultas}</td>
          <td>${m.errores}</td>
          <td>${m.duracion_media_ms ? (m.duracion_media_ms / 1000).toFixed(1) + ' s' : '—'}</td>
        </tr>`).join('')
      : '<tr><td colspan="4" class="muted">Sin registros todavía.</td></tr>';
    root.innerHTML = `
      <h2>📊 Métricas de uso de voz</h2>
      <p class="muted">Agregados mensuales — sin audio ni contenido de consultas.</p>
      <table class="tabla">
        <thead><tr><th>Periodo</th><th>Consultas por voz</th><th>Errores</th><th>Duración media</th></tr></thead>
        <tbody>${filas}</tbody>
      </table>`;
  } catch (err) {
    root.innerHTML = errorBanner(err.message);
  }
}

/* ─────────────────────────── inicialización ─────────────────────────── */

function initVoz() {
  VOZ.soportado = vozSoportado();
  const btn = vozBtn();
  if (!btn) return;
  btn.classList.toggle('hidden', !VOZ.soportado);
  btn.addEventListener('click', toggleVoz);
  cargarParametrosVozChat();
}

// Se invoca desde app.js (init) una vez cargado el DOM; la app es una SPA vanilla
// sin framework, así que el arranque queda atado al init principal.
