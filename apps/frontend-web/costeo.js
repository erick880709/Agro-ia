/* AgroIA — Módulo AGC-COST (frontend F2–F7).
 * RFP AgroIA v4 §11: pantalla de parámetros con simulador, cotizador de
 * 4 pasos, identidad administrable, documentos de cobro y tablero.
 * Se carga después de app.js; usa el wrapper costeoApi() (agrega Content-Type
 JSON) sobre el global api(), además de esc(), state y errorBanner.
 */
'use strict';

/* ─────────────────────────── helpers ─────────────────────────── */

function cop(v) {
  if (v == null || v === '') return '—';
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  return '$' + n.toLocaleString('es-CO', { maximumFractionDigits: 0 });
}

function copDec(v) {
  if (v == null || v === '') return '—';
  const n = Number(v);
  if (!Number.isFinite(n)) return '—';
  return '$' + n.toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function pct(v) {
  if (v == null || v === '') return '—';
  return Number(v).toLocaleString('es-CO', { maximumFractionDigits: 2 }) + '%';
}

function tokenAuth() {
  return state.sesion && state.sesion.access_token
    ? { Authorization: 'Bearer ' + state.sesion.access_token }
    : {};
}

/**
 * Envoltorio de api() que inyecta Content-Type: application/json cuando el
 * body es un string JSON. Sin esto, FastAPI recibe un string en lugar de un
 * objeto y Pydantic falla con `model_attributes_type`.
 */
function costeoApi(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (typeof opts.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  return window['api'](path, { ...opts, headers });
}

async function descargarArchivo(url, nombre) {
  try {
    const res = await fetch(url, { headers: tokenAuth() });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error((err && err.detail && err.detail.message) || 'HTTP ' + res.status);
    }
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = nombre;
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (err) {
    alert(err.message);
  }
}

function filaMensaje(id) {
  const el = document.getElementById(id);
  return el || null;
}

function setMsg(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

const COSTEO = {
  conjuntoId: null,
  conjunto: null,
  sub: 'servicios',
  identidad: null,
  cobroConfig: null,
};

const ETIQUETA_ESTADO = {
  borrador: '📝 Borrador',
  en_revision: '🔎 En revisión',
  publicado: '✅ Publicado',
  archivado: '🗄️ Archivado',
};

const ETIQUETA_ESTADO_EST = {
  borrador: '📝 Borrador',
  emitida: '📤 Emitida',
  aceptada: '✅ Aceptada',
  rechazada: '❌ Rechazada',
  vencida: '⏰ Vencida',
};

const ETIQUETA_ESTADO_COBRO = {
  borrador: '📝 Borrador',
  emitido: '📤 Emitido',
  enviado: '✉️ Enviado',
  pagado_parcial: '💵 Pagado parcial',
  pagado: '✅ Pagado',
  vencido: '⏰ Vencido',
  anulado: '🚫 Anulado',
};

/* ─────────────────────── Pantalla de parámetros (F2) ─────────────────────── */

async function cargarCosteoParametros() {
  const root = document.getElementById('costeo-params-root');
  if (!root) return;
  root.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const [conjuntosRes, identidadRes, configRes] = await Promise.all([
      costeoApi('/costeo/conjuntos'),
      costeoApi('/costeo/identidad'),
      costeoApi('/costeo/cobro-config').catch(() => null),
    ]);
    COSTEO.identidad = identidadRes.identidad;
    COSTEO.cobroConfig = configRes ? configRes.config : null;
    const conjuntos = conjuntosRes.data || [];
    if (!COSTEO.conjuntoId && conjuntos.length) {
      const vigente = conjuntos.find((c) => c.estado === 'publicado') || conjuntos[0];
      COSTEO.conjuntoId = vigente.id;
    }
    root.innerHTML = `
      <h2>🧮 Parámetros de costeo <span class="muted">(catálogo versionado — RFP §6/§11)</span></h2>
      <div id="costeo-header"></div>
      <div class="costeo-subtabs" id="costeo-subtabs"></div>
      <div id="costeo-cuerpo"></div>
      <div id="costeo-msg"></div>`;
    renderCosteoHeader(conjuntos);
    renderCosteoSubtabs();
    await renderCosteoCuerpo();
  } catch (err) {
    root.innerHTML = errorBanner(err.message);
  }
}

function renderCosteoHeader(conjuntos) {
  const el = document.getElementById('costeo-header');
  const c = COSTEO.conjunto;
  const estado = c ? c.estado : '—';
  el.innerHTML = `
    <div class="costeo-header">
      <label class="field" style="flex:2">
        <span>Conjunto en edición (estado: <b>${esc(ETIQUETA_ESTADO[estado] || estado)}</b>${c ? ' · v' + esc(c.version) : ''})</span>
        <select id="costeo-select-conjunto" onchange="costeoCambiarConjunto(this.value)">
          ${conjuntos.map((c) => `<option value="${c.id}" ${c.id === COSTEO.conjuntoId ? 'selected' : ''}>${esc(c.nombre)} · v${c.version} · ${esc(c.estado)}</option>`).join('')}
        </select>
      </label>
      <div class="costeo-acciones">
        <button class="btn" onclick="costeoNuevoConjunto()">➕ Nuevo</button>
        <button class="btn btn-ghost" onclick="costeoClonar()">🧬 Clonar</button>
        <button class="btn btn-ghost" onclick="costeoValidar()">🔍 Validar</button>
        <button class="btn btn-primary" onclick="costeoPublicar()">🚀 Publicar</button>
        <button class="btn btn-ghost" onclick="costeoArchivar()">🗄️ Archivar</button>
        <button class="btn btn-ghost" onclick="costeoExportar()">⬇️ Exportar JSON</button>
        <button class="btn btn-ghost" onclick="document.getElementById('costeo-importar').click()">⬆️ Importar</button>
        <input type="file" id="costeo-importar" accept="application/json" class="hidden" onchange="costeoImportar(event)" />
      </div>
    </div>
    ${c ? `<p class="muted">Vigencia: ${esc(c.vigencia_desde || '—')} → ${esc(c.vigencia_hasta || 'indefinida')} · ${esc(c.notas || '')}</p>` : ''}`;
}

function renderCosteoSubtabs() {
  const el = document.getElementById('costeo-subtabs');
  const subs = [
    ['servicios', '🛠️ Servicios'], ['factores', '⚖️ Factores'], ['densidad', '📍 Densidad'],
    ['zonas', '🗺️ Zonas'], ['impuestos', '🧾 Impuestos'], ['politica', '📐 Política'],
    ['descuentos', '💸 Descuentos'], ['simulador', '🧪 Simulador'],
    ['identidad', '🏷️ Identidad'], ['cobro-config', '🔢 Cobros'],
  ];
  el.innerHTML = subs.map(([k, t]) =>
    `<button class="tab submenu-item ${COSTEO.sub === k ? 'active' : ''}" onclick="costeoSub('${k}')">${t}</button>`
  ).join('');
}

function costeoSub(sub) {
  COSTEO.sub = sub;
  renderCosteoSubtabs();
  renderCosteoCuerpo();
}

async function costeoCambiarConjunto(id) {
  COSTEO.conjuntoId = id;
  try {
    const res = await costeoApi(`/costeo/conjuntos/${id}`);
    COSTEO.conjunto = res.conjunto;
  } catch (err) {
    COSTEO.conjunto = null;
  }
  const c = COSTEO.conjunto;
  document.querySelector('#costeo-header').innerHTML = '';
  await cargarCosteoParametros();
}

async function renderCosteoCuerpo() {
  const el = document.getElementById('costeo-cuerpo');
  if (!COSTEO.conjunto) {
    el.innerHTML = '<p class="muted">Cargando conjunto…</p>';
    try {
      const res = await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}`);
      COSTEO.conjunto = res.conjunto;
    } catch (err) {
      el.innerHTML = errorBanner(err.message);
      return;
    }
  }
  const c = COSTEO.conjunto;
  const bloqueado = !(c.estado === 'borrador' || c.estado === 'en_revision');
  const aviso = bloqueado
    ? `<div class="ok-banner">ℹ️ El conjunto está <b>${esc(c.estado)}</b>: no es editable. Clone para crear una versión nueva.</div>`
    : '';
  el.innerHTML = aviso;
  const cont = document.createElement('div');
  cont.id = 'costeo-sub-cuerpo';
  el.appendChild(cont);
  switch (COSTEO.sub) {
    case 'servicios': await renderServicios(cont, c, bloqueado); break;
    case 'factores': await renderFactores(cont, c, bloqueado); break;
    case 'densidad': await renderDensidad(cont, c, bloqueado); break;
    case 'zonas': await renderZonas(cont, c, bloqueado); break;
    case 'impuestos': await renderImpuestos(cont, c, bloqueado); break;
    case 'politica': await renderPolitica(cont, c, bloqueado); break;
    case 'descuentos': await renderDescuentos(cont, c, bloqueado); break;
    case 'simulador': await renderSimulador(cont, c); break;
    case 'identidad': await renderIdentidad(cont); break;
    case 'cobro-config': await renderCobroConfig(cont); break;
  }
}

/* ── Servicios ── */
async function renderServicios(cont, c, bloqueado) {
  cont.innerHTML = `
    <h3>🛠️ Servicios cotizables</h3>
    ${bloqueado ? '' : `
    <div class="form-grid costeo-form">
      <label class="field"><span>Código</span><input id="srv-codigo" placeholder="muestreo_en_grilla" /></label>
      <label class="field"><span>Nombre</span><input id="srv-nombre" placeholder="Muestreo en grilla" /></label>
      <label class="field"><span>Unidad</span><input id="srv-unidad" value="punto" /></label>
      <label class="field"><span>Orden</span><input id="srv-orden" type="number" value="0" /></label>
      <label class="field"><span>Requiere lote</span><select id="srv-lote"><option value="true">Sí</option><option value="false">No</option></select></label>
      <button class="btn" onclick="srvCrear()">➕ Agregar servicio</button>
    </div>`}
    <table class="tabla"><thead><tr><th>Código</th><th>Nombre</th><th>Unidad</th><th>Lote</th><th>Orden</th><th>Activo</th><th></th></tr></thead>
    <tbody>${(c.servicios || []).map((s) => `
      <tr>
        <td><button class="btn-ghost-sm" onclick="srvVer('${s.id}')">${esc(s.codigo)}</button></td>
        <td>${esc(s.nombre)}</td><td>${esc(s.unidad)}</td>
        <td>${s.requiere_lote ? 'Sí' : 'No'}</td><td>${s.orden}</td>
        <td>${s.activo ? '✅' : '⛔'}</td>
        <td>${bloqueado ? '' : `<button class="btn-ghost-sm" onclick="srvEliminar('${s.id}')">🗑️</button>`}</td>
      </tr>`).join('')}</tbody></table>
    <div id="srv-detalle"></div>`;
}

async function srvCrear() {
  const body = {
    codigo: document.getElementById('srv-codigo').value.trim(),
    nombre: document.getElementById('srv-nombre').value.trim(),
    unidad: document.getElementById('srv-unidad').value.trim() || 'punto',
    requiere_lote: document.getElementById('srv-lote').value === 'true',
    activo: true,
    orden: Number(document.getElementById('srv-orden').value || 0),
  };
  if (!body.codigo || !body.nombre) { alert('Código y nombre son obligatorios.'); return; }
  try {
    await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/servicios`, { method: 'POST', body: JSON.stringify(body) });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function srvEliminar(id) {
  if (!confirm('¿Eliminar el servicio y sus componentes?')) return;
  try {
    await costeoApi(`/costeo/servicios/${id}`, { method: 'DELETE' });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function srvVer(id) {
  await refrescarConjunto();
  const s = (COSTEO.conjunto.servicios || []).find((x) => x.id === id);
  const det = document.getElementById('srv-detalle');
  if (!s || !det) return;
  const bloqueado = !(COSTEO.conjunto.estado === 'borrador' || COSTEO.conjunto.estado === 'en_revision');
  det.innerHTML = `
    <div class="card" style="margin-top:12px">
      <h4>${esc(s.codigo)} — componentes</h4>
      ${bloqueado ? '' : `
      <div class="form-grid costeo-form">
        <label class="field"><span>Código</span><input id="cmp-codigo-${id}" /></label>
        <label class="field"><span>Nombre</span><input id="cmp-nombre-${id}" /></label>
        <label class="field"><span>Tipo</span>
          <select id="cmp-tipo-${id}">
            <option>fijo</option><option>escalonado</option><option>por_unidad</option>
            <option>por_distancia</option><option>por_jornada</option>
            <option>porcentual</option><option>condicional</option>
          </select></label>
        <label class="field"><span>Orden</span><input id="cmp-orden-${id}" type="number" value="0" /></label>
        <label class="field"><span>Valor/config (JSON)</span><input id="cmp-config-${id}" placeholder='{"valor": 100000}' /></label>
        <label class="field"><span>Afectable por factores</span><select id="cmp-afec-${id}"><option value="false">No</option><option value="true">Sí</option></select></label>
        <button class="btn" onclick="cmpCrear('${id}')">➕ Componente</button>
      </div>`}
      <table class="tabla"><thead><tr><th>Orden</th><th>Código</th><th>Tipo</th><th>Factores</th><th>Config</th><th>Tramos</th><th></th></tr></thead>
      <tbody>${(s.componentes || []).map((c) => `
        <tr>
          <td>${c.orden}</td>
          <td><button class="btn-ghost-sm" onclick="cmpVer('${id}','${c.id}')">${esc(c.codigo)}</button></td>
          <td>${esc(c.tipo)}</td><td>${c.afectable_por_factores ? '✅' : '—'}</td>
          <td style="max-width:220px;font-size:11px">${esc(JSON.stringify(c.config || {}))}</td>
          <td>${(c.tramos || []).map((t) => `${t.desde}–${t.hasta || '∞'} ${cop(t.valor)}`).join('<br>')}</td>
          <td>${bloqueado ? '' : `<button class="btn-ghost-sm" onclick="cmpEliminar('${c.id}')">🗑️</button>`}</td>
        </tr>`).join('')}</tbody></table>
      <div id="cmp-detalle"></div>
    </div>`;
}

async function cmpCrear(servicioId) {
  let config = {};
  const raw = document.getElementById(`cmp-config-${servicioId}`).value.trim();
  if (raw) { try { config = JSON.parse(raw); } catch { alert('El JSON de config es inválido.'); return; } }
  const body = {
    codigo: document.getElementById(`cmp-codigo-${servicioId}`).value.trim(),
    nombre: document.getElementById(`cmp-nombre-${servicioId}`).value.trim(),
    tipo: document.getElementById(`cmp-tipo-${servicioId}`).value,
    orden: Number(document.getElementById(`cmp-orden-${servicioId}`).value || 0),
    afectable_por_factores: document.getElementById(`cmp-afec-${servicioId}`).value === 'true',
    config,
  };
  if (!body.codigo || !body.nombre) { alert('Código y nombre son obligatorios.'); return; }
  try {
    await costeoApi(`/costeo/servicios/${servicioId}/componentes`, { method: 'POST', body: JSON.stringify(body) });
    await refrescarConjunto();
    srvVer(servicioId);
  } catch (err) { alert(err.message); }
}

async function cmpEliminar(id) {
  if (!confirm('¿Eliminar el componente y sus tramos?')) return;
  try {
    await costeoApi(`/costeo/componentes/${id}`, { method: 'DELETE' });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function cmpVer(servicioId, componenteId) {
  await refrescarConjunto();
  const s = (COSTEO.conjunto.servicios || []).find((x) => x.id === servicioId);
  const c = (s.componentes || []).find((x) => x.id === componenteId);
  const det = document.getElementById('cmp-detalle');
  if (!c || !det) return;
  const bloqueado = !(COSTEO.conjunto.estado === 'borrador' || COSTEO.conjunto.estado === 'en_revision');
  det.innerHTML = `
    <div class="card" style="margin-top:8px">
      <h4>Tramos de ${esc(c.codigo)}</h4>
      ${bloqueado ? '' : `
      <div class="form-grid costeo-form">
        <label class="field"><span>Desde</span><input id="tr-desde-${c.id}" type="number" min="0" /></label>
        <label class="field"><span>Hasta (vacío = abierto)</span><input id="tr-hasta-${c.id}" type="number" min="0" /></label>
        <label class="field"><span>Valor</span><input id="tr-valor-${c.id}" type="number" step="0.01" min="0" /></label>
        <label class="field"><span>Modo</span><select id="tr-modo-${c.id}"><option>marginal</option><option>completo</option></select></label>
        <button class="btn" onclick="trCrear('${c.id}')">➕ Tramo</button>
      </div>`}
      <table class="tabla"><thead><tr><th>Desde</th><th>Hasta</th><th>Valor</th><th>Modo</th><th></th></tr></thead>
      <tbody>${(c.tramos || []).map((t, i) => `
        <tr><td>${t.desde}</td><td>${t.hasta ?? '∞'}</td><td>${cop(t.valor)}</td><td>${esc(t.modo)}</td>
        <td>${bloqueado ? '' : `<button class="btn-ghost-sm" onclick="trEliminar('${servicioId}','${c.id}',${i})">🗑️</button>`}</td></tr>`).join('')}</tbody></table>
    </div>`;
}

async function trCrear(componenteId) {
  const desde = document.getElementById(`tr-desde-${componenteId}`).value;
  const hasta = document.getElementById(`tr-hasta-${componenteId}`).value;
  const valor = document.getElementById(`tr-valor-${componenteId}`).value;
  const modo = document.getElementById(`tr-modo-${componenteId}`).value;
  if (desde === '' || valor === '') { alert('Desde y valor son obligatorios.'); return; }
  try {
    await costeoApi(`/costeo/componentes/${componenteId}/tramos`, {
      method: 'POST',
      body: JSON.stringify({ desde: Number(desde), hasta: hasta === '' ? null : Number(hasta), valor: Number(valor), modo }),
    });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function trEliminar(servicioId, componenteId, idx) {
  await refrescarConjunto();
  const s = (COSTEO.conjunto.servicios || []).find((x) => x.id === servicioId);
  const c = (s.componentes || []).find((x) => x.id === componenteId);
  const t = (c.tramos || [])[idx];
  if (!t || !confirm('¿Eliminar el tramo?')) return;
  try {
    await costeoApi(`/costeo/tramos/${t.id ?? ''}`, { method: 'DELETE' });
    await refrescarConjunto();
    cmpVer(servicioId, componenteId);
  } catch (err) { alert(err.message); }
}

/* ── Factores ── */
async function renderFactores(cont, c, bloqueado) {
  cont.innerHTML = `
    <h3>⚖️ Escalas de factores</h3>
    ${bloqueado ? '' : `
    <div class="form-grid costeo-form">
      <label class="field"><span>Código</span><input id="fac-codigo" placeholder="dificultad" /></label>
      <label class="field"><span>Nombre</span><input id="fac-nombre" placeholder="Dificultad del terreno" /></label>
      <label class="field"><span>Aplicación</span><select id="fac-aplicacion"><option>porcentual</option><option>multiplicativo</option></select></label>
      <label class="field"><span>Combinación</span><select id="fac-combinacion"><option>suma</option><option>multiplica</option></select></label>
      <button class="btn" onclick="facCrear()">➕ Factor</button>
    </div>`}
    ${(c.factores || []).map((f) => `
      <div class="card" style="margin-top:10px">
        <h4>${esc(f.codigo)} — ${esc(f.nombre)} <span class="muted">(${esc(f.aplicacion)}/${esc(f.combinacion)})</span></h4>
        ${bloqueado ? '' : `
        <div class="form-grid costeo-form">
          <label class="field"><span>Código opción</span><input id="opc-codigo-${f.id}" placeholder="pendiente_alta" /></label>
          <label class="field"><span>Etiqueta</span><input id="opc-etiqueta-${f.id}" placeholder="Pendiente alta" /></label>
          <label class="field"><span>%</span><input id="opc-pct-${f.id}" type="number" step="0.01" /></label>
          <button class="btn" onclick="opcCrear('${f.id}')">➕ Opción</button>
        </div>`}
        <table class="tabla"><thead><tr><th>Código</th><th>Etiqueta</th><th>%</th><th></th></tr></thead>
        <tbody>${(f.opciones || []).map((o) => `
          <tr><td>${esc(o.codigo)}</td><td>${esc(o.etiqueta)}</td><td>${pct(o.porcentaje)}</td>
          <td>${bloqueado ? '' : `<button class="btn-ghost-sm" onclick="opcEliminar('${f.id}','${o.id}')">🗑️</button>`}</td></tr>`).join('')}</tbody></table>
      </div>`).join('')}`;
}

async function facCrear() {
  const body = {
    codigo: document.getElementById('fac-codigo').value.trim(),
    nombre: document.getElementById('fac-nombre').value.trim(),
    aplicacion: document.getElementById('fac-aplicacion').value,
    combinacion: document.getElementById('fac-combinacion').value,
  };
  if (!body.codigo || !body.nombre) { alert('Código y nombre son obligatorios.'); return; }
  try {
    await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/factores`, { method: 'POST', body: JSON.stringify(body) });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function opcCrear(factorId) {
  const body = {
    codigo: document.getElementById(`opc-codigo-${factorId}`).value.trim(),
    etiqueta: document.getElementById(`opc-etiqueta-${factorId}`).value.trim(),
    porcentaje: Number(document.getElementById(`opc-pct-${factorId}`).value || 0),
    orden: 0,
  };
  if (!body.codigo || !body.etiqueta) { alert('Código y etiqueta son obligatorios.'); return; }
  try {
    await costeoApi(`/costeo/factores/${factorId}/opciones`, { method: 'POST', body: JSON.stringify(body) });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function opcEliminar(factorId, opcionId) {
  if (!confirm('¿Eliminar la opción?')) return;
  try {
    await costeoApi(`/costeo/factor-opciones/${opcionId}`, { method: 'DELETE' });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

/* ── Densidad / zonas / impuestos / descuentos ── */
async function renderDensidad(cont, c, bloqueado) {
  cont.innerHTML = `
    <h3>📍 Reglas de densidad de muestreo</h3>
    ${bloqueado ? '' : `
    <div class="form-grid costeo-form">
      <label class="field"><span>Área mín. (ha)</span><input id="den-min" type="number" step="0.1" /></label>
      <label class="field"><span>Área máx. (ha, vacío=∞)</span><input id="den-max" type="number" step="0.1" /></label>
      <label class="field"><span>Puntos mín.</span><input id="den-pmin" type="number" /></label>
      <label class="field"><span>Puntos máx.</span><input id="den-pmax" type="number" /></label>
      <label class="field"><span>Puntos/ha</span><input id="den-pha" type="number" step="0.1" /></label>
      <button class="btn" onclick="denCrear()">➕ Regla</button>
    </div>`}
    <table class="tabla"><thead><tr><th>Área</th><th>Puntos mín.</th><th>Puntos máx.</th><th>Puntos/ha</th><th></th></tr></thead>
    <tbody>${(c.densidad || []).map((d, i) => `
      <tr><td>${d.area_min}–${d.area_max ?? '∞'} ha</td><td>${d.puntos_min}</td><td>${d.puntos_max}</td><td>${d.puntos_por_ha ?? '—'}</td>
      <td>${bloqueado ? '' : `<button class="btn-ghost-sm" onclick="hijoEliminar('densidad',${i})">🗑️</button>`}</td></tr>`).join('')}</tbody></table>`;
}

async function denCrear() {
  const body = {
    area_min: Number(document.getElementById('den-min').value || 0),
    area_max: document.getElementById('den-max').value === '' ? null : Number(document.getElementById('den-max').value),
    puntos_min: Number(document.getElementById('den-pmin').value || 0),
    puntos_max: Number(document.getElementById('den-pmax').value || 0),
    puntos_por_ha: document.getElementById('den-pha').value === '' ? null : Number(document.getElementById('den-pha').value),
  };
  try {
    await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/densidad`, { method: 'POST', body: JSON.stringify(body) });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function renderZonas(cont, c, bloqueado) {
  cont.innerHTML = `
    <h3>🗺️ Zonas y desplazamiento</h3>
    ${bloqueado ? '' : `
    <div class="form-grid costeo-form">
      <label class="field"><span>Departamento</span><input id="zona-dep" /></label>
      <label class="field"><span>Municipio (vacío=todo)</span><input id="zona-mun" /></label>
      <label class="field"><span>Factor %</span><input id="zona-fac" type="number" step="0.01" value="0" /></label>
      <label class="field"><span>Km incluidos</span><input id="zona-km" type="number" step="0.1" value="0" /></label>
      <label class="field"><span>Tarifa km</span><input id="zona-tarifa" type="number" step="1" value="0" /></label>
      <label class="field"><span>Peajes</span><input id="zona-peajes" type="number" step="1" value="0" /></label>
      <button class="btn" onclick="zonaCrear()">➕ Zona</button>
    </div>`}
    <table class="tabla"><thead><tr><th>Depto</th><th>Municipio</th><th>Factor</th><th>Km incl.</th><th>Tarifa km</th><th>Peajes</th><th></th></tr></thead>
    <tbody>${(c.zonas || []).map((z, i) => `
      <tr><td>${esc(z.departamento)}</td><td>${esc(z.municipio || '*')}</td><td>${pct(z.factor)}</td>
      <td>${z.km_incluidos}</td><td>${cop(z.tarifa_km)}</td><td>${cop(z.peajes_estimados)}</td>
      <td>${bloqueado ? '' : `<button class="btn-ghost-sm" onclick="hijoEliminar('zonas',${i})">🗑️</button>`}</td></tr>`).join('')}</tbody></table>`;
}

async function zonaCrear() {
  const body = {
    departamento: document.getElementById('zona-dep').value.trim(),
    municipio: document.getElementById('zona-mun').value.trim() || null,
    factor: Number(document.getElementById('zona-fac').value || 0),
    km_incluidos: Number(document.getElementById('zona-km').value || 0),
    tarifa_km: Number(document.getElementById('zona-tarifa').value || 0),
    peajes_estimados: Number(document.getElementById('zona-peajes').value || 0),
  };
  if (!body.departamento) { alert('El departamento es obligatorio.'); return; }
  try {
    await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/zonas`, { method: 'POST', body: JSON.stringify(body) });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function renderImpuestos(cont, c, bloqueado) {
  cont.innerHTML = `
    <h3>🧾 Impuestos y retenciones</h3>
    ${bloqueado ? '' : `
    <div class="form-grid costeo-form">
      <label class="field"><span>Código</span><input id="imp-codigo" placeholder="IVA" /></label>
      <label class="field"><span>Nombre</span><input id="imp-nombre" /></label>
      <label class="field"><span>%</span><input id="imp-pct" type="number" step="0.01" /></label>
      <label class="field"><span>Base</span><select id="imp-base"><option>subtotal</option><option>directo</option><option>ajustado</option><option>lista</option></select></label>
      <label class="field"><span>Informativo</span><select id="imp-inf"><option value="false">No (incluye en total)</option><option value="true">Sí (no suma)</option></select></label>
      <button class="btn" onclick="impCrear()">➕ Impuesto</button>
    </div>`}
    <table class="tabla"><thead><tr><th>Código</th><th>Nombre</th><th>%</th><th>Base</th><th>Informativo</th><th></th></tr></thead>
    <tbody>${(c.impuestos || []).map((i, idx) => `
      <tr><td>${esc(i.codigo)}</td><td>${esc(i.nombre)}</td><td>${pct(i.porcentaje)}</td>
      <td>${esc(i.base)}</td><td>${i.informativo ? '✅' : '—'}</td>
      <td>${bloqueado ? '' : `<button class="btn-ghost-sm" onclick="hijoEliminar('impuestos',${idx})">🗑️</button>`}</td></tr>`).join('')}</tbody></table>`;
}

async function impCrear() {
  const body = {
    codigo: document.getElementById('imp-codigo').value.trim(),
    nombre: document.getElementById('imp-nombre').value.trim(),
    porcentaje: Number(document.getElementById('imp-pct').value || 0),
    base: document.getElementById('imp-base').value,
    informativo: document.getElementById('imp-inf').value === 'true',
  };
  if (!body.codigo || !body.nombre) { alert('Código y nombre son obligatorios.'); return; }
  try {
    await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/impuestos`, { method: 'POST', body: JSON.stringify(body) });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function renderPolitica(cont, c, bloqueado) {
  const p = c.politica || {};
  cont.innerHTML = `
    <h3>📐 Política comercial</h3>
    <div class="form-grid costeo-form">
      <label class="field"><span>Margen objetivo %</span><input id="pol-margen" type="number" step="0.01" value="${p.margen_objetivo ?? 0}" /></label>
      <label class="field"><span>Margen mínimo %</span><input id="pol-mmin" type="number" step="0.01" value="${p.margen_minimo ?? 0}" /></label>
      <label class="field"><span>Piso por visita (COP)</span><input id="pol-piso" type="number" step="1" value="${p.piso_visita ?? 0}" /></label>
      <label class="field"><span>Vigencia cotización (días)</span><input id="pol-vig" type="number" value="${p.vigencia_cotizacion_dias ?? 30}" /></label>
      <label class="field"><span>Redondeo múltiplo</span><input id="pol-mult" type="number" step="0.01" value="${p.redondeo_multiplo ?? 1}" /></label>
      <label class="field"><span>Modo redondeo</span>
        <select id="pol-modo">
          ${['ninguno', 'mitad_superior', 'techo', 'piso'].map((m) => `<option ${p.redondeo_modo === m ? 'selected' : ''}>${m}</option>`).join('')}
        </select></label>
      <button class="btn" ${bloqueado ? 'disabled' : ''} onclick="polGuardar()">💾 Guardar política</button>
    </div>`;
}

async function polGuardar() {
  const body = {
    margen_objetivo: Number(document.getElementById('pol-margen').value || 0),
    margen_minimo: Number(document.getElementById('pol-mmin').value || 0),
    piso_visita: Number(document.getElementById('pol-piso').value || 0),
    vigencia_cotizacion_dias: Number(document.getElementById('pol-vig').value || 30),
    redondeo_multiplo: Number(document.getElementById('pol-mult').value || 1),
    redondeo_modo: document.getElementById('pol-modo').value,
  };
  try {
    await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/politica`, { method: 'PUT', body: JSON.stringify(body) });
    await refrescarConjunto();
    setMsg('costeo-msg', okBanner('Política guardada.'));
  } catch (err) { alert(err.message); }
}

async function renderDescuentos(cont, c, bloqueado) {
  cont.innerHTML = `
    <h3>💸 Descuentos y recargos comerciales</h3>
    ${bloqueado ? '' : `
    <div class="form-grid costeo-form">
      <label class="field"><span>Código</span><input id="des-codigo" placeholder="manual" /></label>
      <label class="field"><span>Criterio</span><input id="des-criterio" value="manual" /></label>
      <label class="field"><span>Umbral</span><input id="des-umbral" type="number" step="1" value="0" /></label>
      <label class="field"><span>%</span><input id="des-pct" type="number" step="0.01" /></label>
      <label class="field"><span>Tope por rol (JSON)</span><input id="des-topes" placeholder='{"agronomo": 5, "admin": 20}' /></label>
      <button class="btn" onclick="desCrear()">➕ Regla</button>
    </div>`}
    <table class="tabla"><thead><tr><th>Código</th><th>Criterio</th><th>Umbral</th><th>%</th><th>Topes</th><th></th></tr></thead>
    <tbody>${(c.descuentos || []).map((d, i) => `
      <tr><td>${esc(d.codigo)}</td><td>${esc(d.criterio)}</td><td>${d.umbral}</td><td>${pct(d.porcentaje)}</td>
      <td>${esc(JSON.stringify(d.tope_rol || {}))}</td>
      <td>${bloqueado ? '' : `<button class="btn-ghost-sm" onclick="hijoEliminar('descuentos',${i})">🗑️</button>`}</td></tr>`).join('')}</tbody></table>`;
}

async function desCrear() {
  let topes = {};
  const raw = document.getElementById('des-topes').value.trim();
  if (raw) { try { topes = JSON.parse(raw); } catch { alert('JSON de topes inválido.'); return; } }
  const body = {
    codigo: document.getElementById('des-codigo').value.trim(),
    criterio: document.getElementById('des-criterio').value.trim() || 'manual',
    umbral: Number(document.getElementById('des-umbral').value || 0),
    porcentaje: Number(document.getElementById('des-pct').value || 0),
    tope_rol: topes,
  };
  if (!body.codigo) { alert('El código es obligatorio.'); return; }
  try {
    await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/descuentos`, { method: 'POST', body: JSON.stringify(body) });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

async function hijoEliminar(tipo, idx) {
  await refrescarConjunto();
  const lista = COSTEO.conjunto[tipo] || [];
  const item = lista[idx];
  if (!item || !confirm('¿Eliminar el elemento?')) return;
  try {
    await costeoApi(`/costeo/${tipo}/${item.id}`, { method: 'DELETE' });
    await refrescarConjunto();
  } catch (err) { alert(err.message); }
}

/* ── Simulador lado a lado (RF-16) ── */
async function renderSimulador(cont, c) {
  const factores = c.factores || [];
  cont.innerHTML = `
    <h3>🧪 Simulador <span class="muted">(borrador vs. vigente lado a lado — RF-16)</span></h3>
    <div class="form-grid costeo-form">
      <label class="field"><span>Área (ha)</span><input id="sim-area" type="number" step="0.1" value="1" /></label>
      <label class="field"><span>Puntos</span><input id="sim-puntos" type="number" value="10" /></label>
      <label class="field"><span>Km</span><input id="sim-km" type="number" step="0.1" value="0" /></label>
      <label class="field"><span>Servicio</span>
        <select id="sim-servicio">${(c.servicios || []).map((s) => `<option value="${esc(s.codigo)}">${esc(s.codigo)}</option>`).join('')}</select></label>
      <label class="field"><span>Cantidad</span><input id="sim-cantidad" type="number" value="10" /></label>
      <label class="field"><span>Descuento %</span><input id="sim-desc" type="number" step="0.01" value="0" /></label>
      ${factores.map((f) => `
        <label class="field"><span>${esc(f.nombre)}</span>
          <select id="sim-fac-${esc(f.codigo)}"><option value="">— sin aplicar —</option>
          ${(f.opciones || []).map((o) => `<option value="${esc(o.codigo)}">${esc(o.etiqueta)} (${pct(o.porcentaje)})</option>`).join('')}</select></label>`).join('')}
      <button class="btn btn-primary" onclick="costeoSimular()">▶️ Simular</button>
    </div>
    <div id="sim-resultado" style="margin-top:12px"><p class="muted">Corre un caso para comparar el borrador con el conjunto vigente.</p></div>`;
}

function _simCuerpo() {
  const servicio = document.getElementById('sim-servicio').value;
  const factores = {};
  (COSTEO.conjunto.factores || []).forEach((f) => {
    const el = document.getElementById(`sim-fac-${f.codigo}`);
    if (el && el.value) factores[f.codigo] = el.value;
  });
  return {
    area_ha: Number(document.getElementById('sim-area').value || 0),
    puntos: Number(document.getElementById('sim-puntos').value || 0),
    km: Number(document.getElementById('sim-km').value || 0),
    descuento_pct: Number(document.getElementById('sim-desc').value || 0),
    servicios: [{ codigo: servicio, cantidad: Number(document.getElementById('sim-cantidad').value || 0) }],
    factores,
  };
}

async function costeoSimular() {
  const body = _simCuerpo();
  const el = document.getElementById('sim-resultado');
  el.innerHTML = '<p class="muted">Calculando…</p>';
  const fila = (titulo, res) => `
    <div class="card" style="margin:8px 0">
      <h4>${titulo}</h4>
      <div class="sim-totales">
        <div><span>Subtotal directo</span><b>${cop(res.subtotal_directo)}</b></div>
        <div><span>Subtotal ajustado</span><b>${cop(res.subtotal_ajustado)}</b></div>
        <div><span>Precio lista</span><b>${cop(res.precio_lista)}</b></div>
        <div><span>Total final</span><b class="sim-total">${cop(res.total_final)}</b></div>
      </div>
      <table class="tabla"><thead><tr><th>Línea</th><th>Cant.</th><th>Valor</th></tr></thead>
      <tbody>${(res.lineas || []).map((l) => `<tr><td>${esc(l.componente_codigo)} — ${esc(l.descripcion)}</td><td>${l.cantidad}</td><td>${cop(l.valor)}</td></tr>`).join('')}</tbody></table>
      <p class="muted">Costo/punto: <b>${cop(res.indicadores && res.indicadores.costo_por_punto)}</b> · Costo/ha: <b>${cop(res.indicadores && res.indicadores.costo_por_ha)}</b></p>
      ${(res.advertencias || []).map((a) => `<div class="error-banner">⚠️ ${esc(a.mensaje)}</div>`).join('')}
    </div>`;
  try {
    const [borrador, vigente] = await Promise.all([
      costeoApi('/costeo/simular', { method: 'POST', body: JSON.stringify({ ...body, conjunto_id: COSTEO.conjuntoId }) }).catch((e) => ({ error: e.message })),
      costeoApi('/costeo/simular', { method: 'POST', body: JSON.stringify(body) }).catch((e) => ({ error: e.message })),
    ]);
    el.innerHTML = `
      <div class="sim-lado">${borrador.error ? errorBanner('Borrador: ' + borrador.error) : fila('📝 Conjunto en edición (borrador)', borrador)}</div>
      <div class="sim-lado">${vigente.error ? errorBanner('Vigente: ' + vigente.error) : fila('✅ Conjunto publicado vigente', vigente)}</div>`;
  } catch (err) {
    el.innerHTML = errorBanner(err.message);
  }
}

/* ── Identidad (F4) ── */
async function renderIdentidad(cont) {
  const i = COSTEO.identidad || {};
  cont.innerHTML = `
    <h3>🏷️ Identidad y contacto <span class="muted">(P-14 — se refleja en el PDF sin desplegar)</span></h3>
    <div class="form-grid costeo-form">
      <label class="field"><span>Nombre comercial</span><input id="id-nombre" value="${esc(i.nombre_comercial || '')}" /></label>
      <label class="field"><span>Razón social</span><input id="id-razon" value="${esc(i.razon_social || '')}" /></label>
      <label class="field"><span>NIT</span><input id="id-nit" value="${esc(i.nit || '')}" /></label>
      <label class="field"><span>Régimen</span><input id="id-regimen" value="${esc(i.regimen || '')}" /></label>
      <label class="field"><span>Sitio web</span><input id="id-web" value="${esc(i.sitio_web || '')}" /></label>
      <label class="field"><span>Correo</span><input id="id-correo" value="${esc(i.correo || '')}" /></label>
      <label class="field"><span>Dirección</span><input id="id-dir" value="${esc(i.direccion || '')}" /></label>
      <label class="field"><span>Ciudad</span><input id="id-ciudad" value="${esc(i.ciudad || '')}" /></label>
      <label class="field"><span>Latitud sede</span><input id="id-lat" type="number" step="0.000001" value="${i.sede_latitud ?? ''}" /></label>
      <label class="field"><span>Longitud sede</span><input id="id-lon" type="number" step="0.000001" value="${i.sede_longitud ?? ''}" /></label>
      <label class="field"><span>Color de acento</span><input id="id-color" value="${esc(i.color_acento || '#1b5e20')}" /></label>
      <label class="field"><span>Pie legal</span><textarea id="id-pie">${esc(i.pie_legal || '')}</textarea></label>
      <label class="field"><span>Términos y condiciones</span><textarea id="id-term">${esc(i.terminos_condiciones || '')}</textarea></label>
    </div>
    <div id="id-telefonos"></div>
    <button class="btn btn-primary" onclick="identidadGuardar()">💾 Guardar identidad</button>
    <div class="costeo-logo">
      ${i.logo_url ? `<img src="${esc(i.logo_url)}" alt="Logo actual" class="logo-preview" />` : '<p class="muted">Sin logo cargado.</p>'}
      <label class="field"><span>Cargar logo (PNG o SVG, máx. 2 MB)</span>
        <input type="file" accept=".png,.svg" onchange="logoSubir(event,false)" /></label>
    </div>`;
  renderIdentidadTelefonos(i.telefonos || []);
}

function renderIdentidadTelefonos(telefonos) {
  const el = document.getElementById('id-telefonos');
  el.innerHTML = `
    <h4>📞 Teléfonos (orden y etiqueta — RF-27)</h4>
    <table class="tabla"><thead><tr><th>Orden</th><th>Etiqueta</th><th>Número</th><th>WhatsApp</th></tr></thead>
    <tbody>${telefonos.map((t, idx) => `
      <tr>
        <td><input type="number" value="${t.orden}" onchange="idTelOrden(${idx})" style="width:70px" /></td>
        <td><input value="${esc(t.etiqueta)}" onchange="idTelEtiqueta(${idx})" /></td>
        <td><input value="${esc(t.numero)}" onchange="idTelNumero(${idx})" /></td>
        <td><select onchange="idTelWhats(${idx},this.value)"><option value="false" ${!t.whatsapp ? 'selected' : ''}>No</option><option value="true" ${t.whatsapp ? 'selected' : ''}>Sí</option></select></td>
      </tr>`).join('')}
      <tr><td colspan="4"><button class="btn-ghost-sm" onclick="idTelAgregar()">➕ Agregar teléfono</button></td></tr></tbody></table>`;
  COSTEO._telefonos = telefonos.map((t) => ({ ...t }));
}

function _idTel() { return COSTEO._telefonos || []; }
function idTelOrden(idx) { const t = _idTel()[idx]; t.orden = Number(document.querySelectorAll('#id-telefonos input[type=number]')[idx].value || 0); }
function idTelEtiqueta(idx) { _idTel()[idx].etiqueta = document.querySelectorAll('#id-telefonos tbody input')[idx * 2 + 1].value; }
function idTelNumero(idx) { _idTel()[idx].numero = document.querySelectorAll('#id-telefonos tbody input')[idx * 2].value; }
function idTelWhats(idx, v) { _idTel()[idx].whatsapp = v === 'true'; }
function idTelAgregar() {
  COSTEO._telefonos = _idTel().concat([{ etiqueta: 'Nuevo', numero: '', whatsapp: true, orden: _idTel().length }]);
  renderIdentidadTelefonos(_idTel());
}

async function identidadGuardar() {
  const body = {
    nombre_comercial: document.getElementById('id-nombre').value.trim(),
    razon_social: document.getElementById('id-razon').value.trim() || null,
    nit: document.getElementById('id-nit').value.trim() || null,
    regimen: document.getElementById('id-regimen').value.trim() || null,
    sitio_web: document.getElementById('id-web').value.trim() || null,
    correo: document.getElementById('id-correo').value.trim() || null,
    direccion: document.getElementById('id-dir').value.trim() || null,
    ciudad: document.getElementById('id-ciudad').value.trim() || null,
    sede_latitud: document.getElementById('id-lat').value === '' ? null : Number(document.getElementById('id-lat').value),
    sede_longitud: document.getElementById('id-lon').value === '' ? null : Number(document.getElementById('id-lon').value),
    color_acento: document.getElementById('id-color').value.trim() || null,
    pie_legal: document.getElementById('id-pie').value || null,
    terminos_condiciones: document.getElementById('id-term').value || null,
    telefonos: _idTel().filter((t) => t.numero).map((t, i) => ({ ...t, orden: i })),
  };
  if (!body.nombre_comercial) { alert('El nombre comercial es obligatorio.'); return; }
  try {
    const res = await costeoApi('/costeo/identidad', { method: 'PUT', body: JSON.stringify(body) });
    COSTEO.identidad = res.identidad;
    setMsg('costeo-msg', okBanner('Identidad guardada: los PDF reflejan los datos nuevos sin desplegar (CA-10/CA-11).'));
    renderCosteoCuerpo();
  } catch (err) { alert(err.message); }
}

async function logoSubir(event, oscuro) {
  const archivo = event.target.files && event.target.files[0];
  if (!archivo) return;
  const form = new FormData();
  form.append('archivo', archivo);
  form.append('oscuro', oscuro ? 'true' : 'false');
  try {
    const res = await fetch('/api/v1/costeo/identidad/logo', { method: 'POST', headers: tokenAuth(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error((data.detail && data.detail.message) || 'HTTP ' + res.status);
    setMsg('costeo-msg', okBanner('Logo cargado: ' + esc(data.logo_url)));
    await cargarCosteoParametros();
  } catch (err) { alert(err.message); }
}

/* ── Config de cobro (P-15) ── */
async function renderCobroConfig(cont) {
  const c = COSTEO.cobroConfig || {};
  cont.innerHTML = `
    <h3>🔢 Documentos de cobro <span class="muted">(P-15 — numeración y resolución)</span></h3>
    <div class="form-grid costeo-form">
      <label class="field"><span>Tipo</span><select id="cb-tipo">
        <option value="cuenta_cobro" ${c.tipo_documento !== 'factura_venta' ? 'selected' : ''}>Cuenta de cobro</option>
        <option value="factura_venta" ${c.tipo_documento === 'factura_venta' ? 'selected' : ''}>Factura de venta (DIAN aparte)</option>
      </select></label>
      <label class="field"><span>Prefijo</span><input id="cb-prefijo" value="${esc(c.prefijo || 'CC')}" /></label>
      <label class="field"><span>Desde</span><input id="cb-desde" type="number" value="${c.numero_desde ?? 1}" /></label>
      <label class="field"><span>Hasta</span><input id="cb-hasta" type="number" value="${c.numero_hasta ?? 10000}" /></label>
      <label class="field"><span>Resolución DIAN</span><input id="cb-res" value="${esc(c.resolucion_dian || '')}" /></label>
      <label class="field"><span>Resolución vigente hasta</span><input id="cb-resvig" type="date" value="${c.resolucion_vigencia_hasta || ''}" /></label>
      <label class="field"><span>Plazo de pago (días)</span><input id="cb-plazo" type="number" value="${c.plazo_pago_dias ?? 30}" /></label>
      <label class="field"><span>Aviso numeración restante</span><input id="cb-aviso" type="number" value="${c.aviso_numeracion_restante ?? 10}" /></label>
      <label class="field"><span>Cuenta bancaria</span><textarea id="cb-cuenta">${esc(c.cuenta_bancaria || '')}</textarea></label>
      <button class="btn btn-primary" onclick="cobroConfigGuardar()">💾 Guardar configuración</button>
    </div>`;
}

async function cobroConfigGuardar() {
  const body = {
    tipo_documento: document.getElementById('cb-tipo').value,
    prefijo: document.getElementById('cb-prefijo').value.trim() || 'CC',
    numero_desde: Number(document.getElementById('cb-desde').value || 1),
    numero_hasta: Number(document.getElementById('cb-hasta').value || 10000),
    resolucion_dian: document.getElementById('cb-res').value.trim() || null,
    resolucion_vigencia_hasta: document.getElementById('cb-resvig').value || null,
    plazo_pago_dias: Number(document.getElementById('cb-plazo').value || 30),
    medios_pago: COSTEO.cobroConfig ? (COSTEO.cobroConfig.medios_pago || {}) : {},
    cuenta_bancaria: document.getElementById('cb-cuenta').value || null,
    textos_legales: COSTEO.cobroConfig ? (COSTEO.cobroConfig.textos_legales || {}) : {},
    aviso_numeracion_restante: Number(document.getElementById('cb-aviso').value || 10),
  };
  try {
    const res = await costeoApi('/costeo/cobro-config', { method: 'PUT', body: JSON.stringify(body) });
    COSTEO.cobroConfig = res.config;
    setMsg('costeo-msg', okBanner('Configuración de cobro guardada.'));
  } catch (err) { alert(err.message); }
}

/* ── Acciones de conjunto ── */
async function refrescarConjunto() {
  const res = await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}`);
  COSTEO.conjunto = res.conjunto;
  const cont = document.getElementById('costeo-sub-cuerpo');
  if (cont) { cont.innerHTML = ''; await renderCosteoCuerpo(); }
}

async function costeoNuevoConjunto() {
  const nombre = prompt('Nombre del conjunto nuevo:');
  if (!nombre) return;
  try {
    const res = await costeoApi('/costeo/conjuntos', { method: 'POST', body: JSON.stringify({ nombre }) });
    COSTEO.conjuntoId = res.id;
    await cargarCosteoParametros();
  } catch (err) { alert(err.message); }
}

async function costeoClonar() {
  const pctReajuste = prompt('Reajuste porcentual masivo (ej. 9 para +9%, vacío = sin reajuste):', '');
  const body = { nombre: (COSTEO.conjunto.nombre || '') + ' (clon)' };
  if (pctReajuste !== '' && pctReajuste !== null) body.reajuste_pct = Number(pctReajuste);
  try {
    const res = await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/clonar`, { method: 'POST', body: JSON.stringify(body) });
    COSTEO.conjuntoId = res.id;
    setMsg('costeo-msg', okBanner('Conjunto clonado: ' + esc(res.nombre) + ' (v' + res.version + ').'));
    await cargarCosteoParametros();
  } catch (err) { alert(err.message); }
}

async function costeoValidar() {
  try {
    const res = await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/validar`, { method: 'POST' });
    const msg = document.getElementById('costeo-msg');
    msg.innerHTML = res.valido
      ? okBanner('✅ Validación aprobada. ' + (res.advertencias || []).map((a) => esc(a.mensaje)).join(' · '))
      : errorBanner('❌ ' + (res.errores || []).map((e) => esc(e.mensaje)).join('<br>'));
  } catch (err) { alert(err.message); }
}

async function costeoPublicar() {
  try {
    const res = await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/publicar`, { method: 'POST' });
    setMsg('costeo-msg', okBanner('✅ Conjunto publicado (v' + res.version + '). El anterior quedó archivado.'));
    await cargarCosteoParametros();
  } catch (err) { alert(err.message); }
}

async function costeoArchivar() {
  if (!confirm('¿Archivar el conjunto? Dejará de estar vigente.')) return;
  try {
    await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/archivar`, { method: 'POST' });
    await cargarCosteoParametros();
  } catch (err) { alert(err.message); }
}

async function costeoExportar() {
  try {
    const res = await costeoApi(`/costeo/conjuntos/${COSTEO.conjuntoId}/exportar`);
    const blob = new Blob([JSON.stringify(res, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `conjunto-costeo-${(COSTEO.conjunto.nombre || 'export').replace(/\s+/g, '-')}.json`;
    a.click();
  } catch (err) { alert(err.message); }
}

async function costeoImportar(event) {
  const archivo = event.target.files && event.target.files[0];
  if (!archivo) return;
  try {
    const res = await costeoApi('/costeo/importar', {
      method: 'POST',
      body: JSON.stringify(JSON.parse(await archivo.text())),
    });
    COSTEO.conjuntoId = res.id;
    setMsg('costeo-msg', okBanner('✅ Conjunto importado y validado (v' + res.version + ').'));
    await cargarCosteoParametros();
  } catch (err) { alert(err.message); }
}

/* ─────────────────────── Estimaciones (F3/F6) ─────────────────────── */

async function cargarEstimaciones() {
  const root = document.getElementById('estimaciones-root');
  if (!root) return;
  root.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const [lista, tablero, fincas] = await Promise.all([
      costeoApi('/estimaciones?limite=100'),
      state.rol.toLowerCase() === 'admin' ? costeoApi('/estimaciones/tablero').catch(() => null) : Promise.resolve(null),
      costeoApi('/fincas'),
    ]);
    COSTEO.fincas = (fincas.data || fincas || []).map ? (fincas.data || []) : [];
    root.innerHTML = `
      <h2>📐 Estimación de costos <span class="muted">(cotizador — RFP §11)</span></h2>
      ${tablero ? renderTablero(tablero) : ''}
      <div class="estim-acciones">
        <button class="btn btn-primary" onclick="estimacionNueva()">➕ Nueva estimación</button>
      </div>
      <div id="estim-lista">${renderEstimLista(lista.data || [])}</div>
      <div id="estim-detalle"></div>`;
  } catch (err) {
    root.innerHTML = errorBanner(err.message);
  }
}

function renderTablero(t) {
  const porServicio = Object.entries(t.ticket_promedio_por_servicio || {})
    .map(([k, v]) => `<div class="tbl-item"><span>${esc(k)}</span><b>${cop(v)}</b></div>`).join('');
  return `
    <div class="tbl-cards">
      <div class="tbl-card"><span>Total</span><b>${t.totales.total}</b></div>
      <div class="tbl-card"><span>Emitidas</span><b>${t.totales.emitidas}</b></div>
      <div class="tbl-card"><span>Aceptadas</span><b>${t.totales.aceptadas}</b></div>
      <div class="tbl-card"><span>Tasa de conversión</span><b>${(t.tasa_conversion * 100).toLocaleString('es-CO', { maximumFractionDigits: 1 })}%</b></div>
      <div class="tbl-card tbl-wide"><span>Ticket promedio por componente</span><div class="tbl-items">${porServicio || '—'}</div></div>
    </div>`;
}

function renderEstimLista(lista) {
  if (!lista.length) return '<p class="muted">Aún no hay estimaciones. Crea la primera con «Nueva estimación».</p>';
  return `<table class="tabla"><thead><tr><th>Consecutivo</th><th>Finca</th><th>Estado</th><th>Total</th><th>Vence</th><th>Acciones</th></tr></thead>
    <tbody>${lista.map((e) => `
      <tr>
        <td>${esc(e.consecutivo || 'borrador')}</td>
        <td>${esc(e.finca || '')}</td>
        <td>${ETIQUETA_ESTADO_EST[e.estado] || esc(e.estado)}</td>
        <td><b>${cop(e.total_final)}</b></td>
        <td>${esc(e.vence_en || '—')}</td>
        <td class="cell-acciones">
          <button class="btn-ghost-sm" onclick="estimacionVer('${e.id}')">👁️ Ver</button>
          ${e.estado === 'borrador' ? `<button class="btn-ghost-sm" onclick="estimacionEmitir('${e.id}')">📤 Emitir</button>` : ''}
          ${e.estado === 'emitida' ? `<button class="btn-ghost-sm" onclick="estimacionAceptar('${e.id}')">✅ Aceptar</button><button class="btn-ghost-sm" onclick="estimacionRechazar('${e.id}')">❌ Rechazar</button>` : ''}
          ${e.estado === 'aceptada' && state.rol.toLowerCase() === 'admin' ? `<button class="btn-ghost-sm" onclick="estimacionConvertir('${e.id}')">🗂️ Comisión</button>` : ''}
        </td>
      </tr>`).join('')}</tbody></table>`;
}

async function estimacionNueva() {
  const det = document.getElementById('estim-detalle');
  if (!COSTEO.fincas || !COSTEO.fincas.length) {
    det.innerHTML = errorBanner('No hay fincas registradas para cotizar.');
    return;
  }
  let vigentes = null;
  try { vigentes = await costeoApi('/costeo/parametros/vigentes'); } catch { /* sin conjunto */ }
  const servicios = vigentes ? (vigentes.conjunto.servicios || []) : [];
  const factores = vigentes ? (vigentes.conjunto.factores || []) : [];
  det.innerHTML = `
    <div class="card estim-form">
      <h3>Nueva estimación — flujo en una pantalla (RFP §11)</h3>
      <div class="form-grid costeo-form">
        <label class="field"><span>1️⃣ Finca</span>
          <select id="est-finca" onchange="estimFincaCambio()">${COSTEO.fincas.map((f) => `<option value="${f.id}">${esc(f.nombre || f.id)}</option>`).join('')}</select></label>
        <label class="field"><span>2️⃣ Servicio</span>
          <select id="est-servicio">${servicios.map((s) => `<option value="${esc(s.codigo)}">${esc(s.nombre)} (${esc(s.codigo)})</option>`).join('')}</select></label>
        <label class="field"><span>3️⃣ Cantidad / puntos</span><input id="est-cantidad" type="number" value="10" /></label>
        <label class="field"><span>Área (ha)</span><input id="est-area" type="number" step="0.1" value="1" /></label>
        <label class="field"><span>Km (editable)</span><input id="est-km" type="number" step="0.1" value="0" /></label>
        <label class="field"><span>Descuento %</span><input id="est-desc" type="number" step="0.01" value="0" /></label>
        ${factores.map((f) => `
          <label class="field"><span>${esc(f.nombre)}</span>
            <select id="est-fac-${esc(f.codigo)}"><option value="">— sin aplicar —</option>
            ${(f.opciones || []).map((o) => `<option value="${esc(o.codigo)}">${esc(o.etiqueta)} (${pct(o.porcentaje)})</option>`).join('')}</select></label>`).join('')}
        <button class="btn" onclick="estimVistaPrevia()">👁️ Vista previa</button>
        <button class="btn btn-primary" onclick="estimGuardarBorrador()">💾 Guardar borrador</button>
      </div>
      <div id="est-preview"></div>
    </div>`;
}

function estimFincaCambio() {
  const finca = (COSTEO.fincas || []).find((f) => f.id === document.getElementById('est-finca').value);
  if (finca && finca.area_hectareas) document.getElementById('est-area').value = finca.area_hectareas;
  // Distancia geodésica desde la sede (RF-07)
  costeoApi(`/estimaciones/sugerencia-km?finca_id=${encodeURIComponent(finca.id)}`)
    .then((r) => { if (r.km != null) document.getElementById('est-km').value = r.km; })
    .catch(() => {});
  // Puntos sugeridos por densidad (RF-05)
  const area = Number(document.getElementById('est-area').value || 1);
  costeoApi(`/estimaciones/sugerencia-puntos?area_ha=${area}`)
    .then((r) => { if (r.puntos_sugeridos) document.getElementById('est-cantidad').value = r.puntos_sugeridos; })
    .catch(() => {});
}

function _estimCuerpo() {
  const fincaId = document.getElementById('est-finca').value;
  const servicio = document.getElementById('est-servicio').value;
  const factores = {};
  document.querySelectorAll('#estim-detalle select[id^="est-fac-"]').forEach((sel) => {
    if (sel.value) factores[sel.id.replace('est-fac-', '')] = sel.value;
  });
  const area = Number(document.getElementById('est-area').value || 1);
  return {
    finca_id: fincaId,
    lotes: [{
      lote_id: null,
      area_ha: area,
      puntos: Number(document.getElementById('est-cantidad').value || 0),
      km: Number(document.getElementById('est-km').value || 0),
      servicios: [{ codigo: servicio, cantidad: Number(document.getElementById('est-cantidad').value || 0) }],
    }],
    factores,
    descuento_pct: Number(document.getElementById('est-desc').value || 0),
  };
}

async function estimVistaPrevia() {
  const el = document.getElementById('est-preview');
  const cuerpo = _estimCuerpo();
  el.innerHTML = '<p class="muted">Calculando vista previa…</p>';
  try {
    const res = await costeoApi('/costeo/simular', {
      method: 'POST',
      body: JSON.stringify({
        area_ha: cuerpo.lotes[0].area_ha,
        puntos: cuerpo.lotes[0].puntos,
        km: cuerpo.lotes[0].km,
        descuento_pct: cuerpo.descuento_pct,
        servicios: cuerpo.lotes[0].servicios,
        factores: cuerpo.factores,
      }),
    });
    el.innerHTML = `
      <div class="sim-totales">
        <div><span>Subtotal directo</span><b>${cop(res.subtotal_directo)}</b></div>
        <div><span>Subtotal ajustado</span><b>${cop(res.subtotal_ajustado)}</b></div>
        <div><span>Precio lista</span><b>${cop(res.precio_lista)}</b></div>
        <div><span>Total</span><b class="sim-total">${cop(res.total_final)}</b></div>
      </div>
      ${(res.advertencias || []).map((a) => `<div class="error-banner">⚠️ ${esc(a.mensaje)}</div>`).join('')}
      ${res.indicadores && res.indicadores.costo_por_ha ? `<p class="muted">💡 En lotes pequeños el costo por hectárea se ve alto porque el viaje y el montaje cuestan casi lo mismo en 1 ha que en 50 ha: el costo fijo se reparte entre menos hectáreas (RFP §2).</p>` : ''}`;
  } catch (err) { el.innerHTML = errorBanner(err.message); }
}

async function estimGuardarBorrador() {
  try {
    const res = await costeoApi('/estimaciones', { method: 'POST', body: JSON.stringify(_estimCuerpo()) });
    setMsg('est-preview', okBanner('Borrador guardado con total ' + cop(res.estimacion.total_final) + '.'));
    await cargarEstimaciones();
  } catch (err) { alert(err.message); }
}

async function estimacionVer(id) {
  const det = document.getElementById('estim-detalle');
  det.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const res = await costeoApi(`/estimaciones/${id}`);
    const e = res.estimacion;
    det.innerHTML = `
      <div class="card estim-det">
        <h3>${esc(e.consecutivo || 'Borrador')} — ${ETIQUETA_ESTADO_EST[e.estado] || esc(e.estado)}</h3>
        <p class="muted">Finca: ${esc(e.finca || '')} · Municipio: ${esc(e.municipio || '—')} · Área: ${e.area_total_ha} ha · Vence: ${esc(e.vence_en || '—')}</p>
        ${e.hash_snapshot ? `<p class="muted">🔒 Snapshot SHA-256: <code>${esc(e.hash_snapshot.slice(0, 16))}…</code></p>` : ''}
        <div class="sim-totales">
          <div><span>Subtotal directo</span><b>${cop(e.total_directo)}</b></div>
          <div><span>Subtotal ajustado</span><b>${cop(e.total_ajustado)}</b></div>
          <div><span>Precio lista</span><b>${cop(e.precio_lista)}</b></div>
          <div><span>Descuento</span><b>${cop(e.descuento_aplicado)}</b></div>
          <div><span>Total</span><b class="sim-total">${cop(e.total_final)}</b></div>
        </div>
        <table class="tabla"><thead><tr><th>Lote</th><th>Descripción</th><th>Cant.</th><th>Unidad</th><th>Valor</th></tr></thead>
        <tbody>${(e.lineas || []).map((l) => `<tr><td>${esc(l.lote || '—')}</td><td>${esc(l.descripcion)}</td><td>${l.cantidad}</td><td>${esc(l.unidad || '')}</td><td>${cop(l.valor)}</td></tr>`).join('')}</tbody></table>
        <div class="cell-acciones" style="margin-top:10px">
          ${e.estado === 'borrador' ? `<button class="btn btn-primary" onclick="estimacionEmitir('${e.id}')">📤 Emitir cotización</button>` : ''}
          ${e.estado === 'emitida' ? `<button class="btn" onclick="estimacionAceptar('${e.id}')">✅ Aceptar</button><button class="btn btn-ghost" onclick="estimacionRechazar('${e.id}')">❌ Rechazar</button>` : ''}
          ${e.estado === 'aceptada' && state.rol.toLowerCase() === 'admin' ? `<button class="btn" onclick="estimacionConvertir('${e.id}')">🗂️ Convertir en comisión</button>` : ''}
          <button class="btn btn-ghost" onclick="descargarArchivo('/api/v1/estimaciones/${e.id}/export?formato=pdf&audiencia=agricultor', 'cotizacion-${e.consecutivo || e.id}.pdf')">⬇️ PDF</button>
          <button class="btn btn-ghost" onclick="window.open('/api/v1/estimaciones/${e.id}/export?formato=html&audiencia=agricultor', '_blank')">🌐 HTML</button>
          ${state.rol.toLowerCase() !== 'cliente' ? `<button class="btn btn-ghost" onclick="estimacionRecalcular('${e.id}')">🔁 Verificar snapshot</button>` : ''}
        </div>
        ${(e.eventos || []).map((ev) => `<p class="muted" style="font-size:11px">🕘 ${esc(ev.fecha)} — ${esc(ev.evento)}: ${esc(ev.comentario || '')}</p>`).join('')}
      </div>`;
  } catch (err) { det.innerHTML = errorBanner(err.message); }
}

async function estimacionEmitir(id) {
  let autorizar = false, motivo = null;
  try {
    await costeoApi(`/estimaciones/${id}/emitir`, { method: 'POST', body: JSON.stringify({}) });
  } catch (err) {
    if (err.detail && err.detail.code === 'BAJO_PISO_RENTABILIDAD') {
      autorizar = confirm(err.message + '\n\n¿Autorizar como administrador? Debes justificar la excepción.');
      if (!autorizar) return;
      motivo = prompt('Motivo de la excepción al piso de rentabilidad (obligatorio):');
      if (!motivo) return;
      try {
        await costeoApi(`/estimaciones/${id}/emitir`, {
          method: 'POST',
          body: JSON.stringify({ autorizar_bajo_piso: true, motivo_excepcion: motivo }),
        });
      } catch (err2) { alert(err2.message); return; }
    } else {
      alert(err.message);
      return;
    }
  }
  await cargarEstimaciones();
  estimacionVer(id);
}

async function estimacionAceptar(id) {
  try {
    await costeoApi(`/estimaciones/${id}/aceptar`, { method: 'POST', body: JSON.stringify({}) });
    await cargarEstimaciones();
  } catch (err) { alert(err.message); }
}

async function estimacionRechazar(id) {
  const comentario = prompt('Motivo del rechazo (opcional):');
  try {
    await costeoApi(`/estimaciones/${id}/rechazar`, { method: 'POST', body: JSON.stringify({ comentario }) });
    await cargarEstimaciones();
  } catch (err) { alert(err.message); }
}

async function estimacionConvertir(id) {
  if (!confirm('¿Crear la comisión a partir de esta estimación aceptada?')) return;
  try {
    const res = await costeoApi(`/estimaciones/${id}/convertir-comision`, { method: 'POST' });
    alert('✅ Comisión creada: ' + cop(res.comision.valor_comision_cop) + ' COP.');
    await cargarEstimaciones();
  } catch (err) { alert(err.message); }
}

async function estimacionRecalcular(id) {
  try {
    const res = await costeoApi(`/estimaciones/${id}/recalcular`, { method: 'POST' });
    alert(res.coincide
      ? '✅ Snapshot reproducible: el total sigue siendo ' + cop(res.total_snapshot) + ' (CA-07).'
      : '❌ SNAPSHOT_INCONSISTENTE: ' + cop(res.total_guardado) + ' ≠ ' + cop(res.total_snapshot));
  } catch (err) { alert(err.message); }
}

/* ─────────────────────── Cliente: mis cotizaciones ─────────────────────── */

async function cargarCotizaciones() {
  const root = document.getElementById('cotizaciones-root');
  if (!root) return;
  root.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const lista = await costeoApi('/estimaciones?limite=100');
    root.innerHTML = `
      <h2>🧾 Mis cotizaciones <span class="muted">(ver, aceptar o descargar)</span></h2>
      <div id="cot-lista">${renderEstimLista(lista.data || [])}</div>
      <div id="estim-detalle"></div>`;
  } catch (err) {
    root.innerHTML = errorBanner(err.message);
  }
}

/* ─────────────────────── Documentos de cobro (F5) ─────────────────────── */

async function cargarCobros() {
  const root = document.getElementById('cobros-root');
  if (!root) return;
  root.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const [lista, aceptadas] = await Promise.all([
      costeoApi('/cobros?limite=100'),
      costeoApi('/estimaciones?estado=aceptada&limite=100'),
    ]);
    COSTEO.aceptadas = (aceptadas.data || []).filter((e) => !e.cobro);
    root.innerHTML = `
      <h2>🧾 Documentos de cobro <span class="muted">(numeración controlada — RFP §17)</span></h2>
      <div class="form-grid costeo-form">
        <label class="field"><span>Crear desde estimación aceptada</span>
          <select id="cob-estimacion"><option value="">— Seleccione —</option>
          ${COSTEO.aceptadas.map((e) => `<option value="${e.id}">${esc(e.consecutivo)} · ${esc(e.finca)} · ${cop(e.total_final)}</option>`).join('')}
          </select></label>
        <button class="btn" onclick="cobroCrear()">➕ Crear documento</button>
      </div>
      <table class="tabla"><thead><tr><th>Número</th><th>Estado</th><th>Finca</th><th>Total</th><th>Saldo</th><th>Vence</th><th>Acciones</th></tr></thead>
      <tbody>${(lista.data || []).map((d) => `
        <tr>
          <td><b>${esc(d.numero || 'borrador')}</b></td>
          <td>${ETIQUETA_ESTADO_COBRO[d.estado] || esc(d.estado)}</td>
          <td>${esc(d.finca || '')}</td>
          <td>${cop(d.total)}</td>
          <td>${cop(d.saldo)}</td>
          <td>${esc(d.fecha_vencimiento || '—')}</td>
          <td class="cell-acciones">
            <button class="btn-ghost-sm" onclick="cobroVer('${d.id}')">👁️</button>
            ${d.estado === 'borrador' ? `<button class="btn-ghost-sm" onclick="cobroEmitir('${d.id}')">📤 Emitir</button>` : ''}
            ${['emitido', 'enviado', 'pagado_parcial', 'vencido'].includes(d.estado) ? `<button class="btn-ghost-sm" onclick="cobroPago('${d.id}')">💵 Pago</button>` : ''}
            ${['emitido', 'enviado', 'pagado_parcial', 'vencido'].includes(d.estado) ? `<button class="btn-ghost-sm" onclick="cobroAnular('${d.id}')">🚫 Anular</button>` : ''}
            ${d.estado !== 'borrador' ? `<button class="btn-ghost-sm" onclick="descargarArchivo('/api/v1/cobros/${d.id}/pdf', 'cobro-${d.numero}.pdf')">⬇️</button>` : ''}
          </td>
        </tr>`).join('')}</tbody></table>
      <div id="cobro-detalle"></div>`;
  } catch (err) {
    root.innerHTML = errorBanner(err.message);
  }
}

async function cobroCrear() {
  const estimacionId = document.getElementById('cob-estimacion').value;
  if (!estimacionId) { alert('Seleccione una estimación aceptada.'); return; }
  try {
    await costeoApi(`/cobros?estimacion_id=${estimacionId}`, { method: 'POST' });
    await cargarCobros();
  } catch (err) { alert(err.message); }
}

async function cobroEmitir(id) {
  try {
    await costeoApi(`/cobros/${id}/emitir`, { method: 'POST' });
    await cargarCobros();
  } catch (err) { alert(err.message); }
}

async function cobroPago(id) {
  const valor = prompt('Valor del pago (COP):');
  if (!valor) return;
  const medio = prompt('Medio de pago (transferencia, efectivo…):', 'transferencia');
  try {
    await costeoApi(`/cobros/${id}/pagos`, { method: 'POST', body: JSON.stringify({ valor: Number(valor), medio }) });
    await cargarCobros();
  } catch (err) { alert(err.message); }
}

async function cobroAnular(id) {
  const motivo = prompt('Motivo de la anulación (obligatorio, mínimo 5 caracteres):');
  if (!motivo) return;
  try {
    await costeoApi(`/cobros/${id}/anular`, { method: 'POST', body: JSON.stringify({ motivo }) });
    await cargarCobros();
  } catch (err) { alert(err.message); }
}

async function cobroVer(id) {
  const det = document.getElementById('cobro-detalle');
  det.innerHTML = '<p class="muted">Cargando…</p>';
  try {
    const lista = await costeoApi('/cobros?limite=100');
    const d = (lista.data || []).find((x) => x.id === id);
    if (!d) throw new Error('Documento no encontrado.');
    det.innerHTML = `
      <div class="card" style="margin-top:10px">
        <h3>${esc(d.numero || 'Borrador')} — ${ETIQUETA_ESTADO_COBRO[d.estado] || esc(d.estado)}</h3>
        <div class="sim-totales">
          <div><span>Total</span><b>${cop(d.total)}</b></div>
          <div><span>Saldo</span><b class="sim-total">${cop(d.saldo)}</b></div>
        </div>
        <table class="tabla"><thead><tr><th>Descripción</th><th>Cant.</th><th>Valor</th></tr></thead>
        <tbody>${(d.lineas || []).map((l) => `<tr><td>${esc(l.descripcion)}</td><td>${l.cantidad}</td><td>${cop(l.valor)}</td></tr>`).join('')}</tbody></table>
        ${(d.pagos || []).length ? `<h4>Pagos</h4><table class="tabla"><thead><tr><th>Fecha</th><th>Medio</th><th>Valor</th></tr></thead><tbody>${d.pagos.map((p) => `<tr><td>${esc(p.fecha)}</td><td>${esc(p.medio || '—')}</td><td>${cop(p.valor)}</td></tr>`).join('')}</tbody></table>` : ''}
        ${d.motivo_anulacion ? `<div class="error-banner">🚫 Anulado: ${esc(d.motivo_anulacion)}</div>` : ''}
      </div>`;
  } catch (err) { det.innerHTML = errorBanner(err.message); }
}
