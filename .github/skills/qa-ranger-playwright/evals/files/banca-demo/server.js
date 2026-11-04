// Aplicación bancaria de ejemplo para evaluar la skill. No requiere dependencias adicionales.
// Ejecutar: node server.js [puerto]
const http = require('http');
const crypto = require('crypto');

const PORT = Number(process.argv[2] || process.env.PORT || 3000);
const USUARIOS = { 'usuario.qa': 'Clave-Prueba-1' };
const sesiones = new Map();          // token -> { usuario, saldo, movimientos }

const layout = (titulo, cuerpo, autenticado = true) => `<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>${titulo} — Banca Demo</title>
<style>body{font-family:sans-serif;margin:2rem} .error{color:#b00} nav a{margin-right:1rem}
#cargando{position:fixed;inset:0;background:rgba(255,255,255,.7);display:none}</style></head>
<body>${autenticado ? '<nav aria-label="Principal"><a href="/inicio">Inicio</a><a href="/transferencias/nueva">Transferencias</a><a href="/historial">Historial</a><a href="/salir">Salir</a></nav>' : ''}
<main>${cuerpo}</main></body></html>`;

function sesion(req) {
  const m = /sid=([a-f0-9]+)/.exec(req.headers.cookie || '');
  return m && sesiones.get(m[1]);
}
function body(req) {
  return new Promise(r => { let d = ''; req.on('data', c => d += c); req.on('end', () => r(d)); });
}
const fmt = n => '$ ' + n.toLocaleString('es-CO');

function transferir(s, { cuentaDestino, monto, descripcion }) {
  monto = Number(monto);
  if (!/^\d{11}$/.test(String(cuentaDestino || ''))) return { status: 400, codigo: 'CUENTA_INVALIDA', mensaje: 'La cuenta destino debe tener 11 dígitos' };
  if (!(monto > 0)) return { status: 400, codigo: 'MONTO_INVALIDO', mensaje: 'El monto debe ser mayor a cero' };
  if (descripcion && descripcion.length > 40) return { status: 400, codigo: 'DESCRIPCION_LARGA', mensaje: 'La descripción admite máximo 40 caracteres' };
  if (monto > s.saldo) return { status: 422, codigo: 'SALDO_INSUFICIENTE', mensaje: 'Saldo insuficiente' };
  s.saldo -= monto;
  const mov = { id: crypto.randomUUID(), referencia: 'REF-' + crypto.randomBytes(3).toString('hex').toUpperCase(), cuentaDestino, monto, descripcion: descripcion || '', estado: 'APLICADA', fecha: new Date().toISOString() };
  s.movimientos.unshift(mov);
  return { status: 201, mov };
}

const PAGINA_TRANSFERENCIA = layout('Nueva transferencia', `
<h1>Nueva transferencia</h1>
<form id="f" aria-label="Transferencia">
  <label>Cuenta destino <input name="cuentaDestino" inputmode="numeric"></label><br>
  <label>Monto <input name="monto" inputmode="numeric"></label><br>
  <label>Descripción <input name="descripcion"></label><br>
  <button type="submit">Continuar</button>
</form>
<section id="confirmacion" hidden aria-label="Confirmación">
  <p id="resumen"></p>
  <button id="confirmar" type="button">Confirmar transferencia</button>
  <button id="cancelar" type="button">Cancelar</button>
</section>
<div id="mensaje" role="alert"></div>
<div id="cargando" aria-hidden="true"></div>
<script>
const f = document.getElementById('f'), conf = document.getElementById('confirmacion'), msg = document.getElementById('mensaje');
let datos;
f.addEventListener('submit', e => {
  e.preventDefault();
  datos = Object.fromEntries(new FormData(f));
  msg.textContent = ''; msg.className = '';
  document.getElementById('resumen').textContent = 'Vas a transferir $ ' + Number(datos.monto).toLocaleString('es-CO') + ' a la cuenta ' + datos.cuentaDestino;
  f.hidden = true; conf.hidden = false;
});
document.getElementById('cancelar').onclick = () => { conf.hidden = true; f.hidden = false; };
document.getElementById('confirmar').onclick = async () => {
  const btn = document.getElementById('confirmar'); btn.disabled = true;
  document.getElementById('cargando').style.display = 'block';
  await new Promise(r => setTimeout(r, 400 + Math.random() * 600));       // latencia variable (atrapa tests con esperas fijas)
  const r = await fetch('/api/transferencias', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(datos) });
  const j = await r.json();
  document.getElementById('cargando').style.display = 'none';
  conf.hidden = true; f.hidden = false; btn.disabled = false;
  if (r.ok) { msg.textContent = 'Transferencia exitosa. Referencia ' + j.referencia; f.reset(); }
  else { msg.textContent = j.mensaje; msg.className = 'error'; }
};
</script>`);

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  const send = (status, html, headers = {}) => { res.writeHead(status, { 'content-type': 'text/html; charset=utf-8', ...headers }); res.end(html); };
  const json = (status, obj) => { res.writeHead(status, { 'content-type': 'application/json' }); res.end(JSON.stringify(obj)); };
  const s = sesion(req);

  if (url.pathname === '/health') return json(200, { ok: true });

  if (url.pathname === '/login' && req.method === 'GET')
    return send(200, layout('Ingreso', `<h1>Ingreso a Banca Demo</h1>
<form method="post" action="/login"><label>Usuario <input name="usuario" autocomplete="username"></label><br>
<label>Contraseña <input name="clave" type="password" autocomplete="current-password"></label><br>
<button type="submit">Ingresar</button></form>${url.searchParams.has('error') ? '<p role="alert" class="error">Usuario o contraseña incorrectos</p>' : ''}`, false));

  if (url.pathname === '/login' && req.method === 'POST') {
    const p = new URLSearchParams(await body(req));
    if (USUARIOS[p.get('usuario')] === p.get('clave')) {
      const sid = crypto.randomBytes(16).toString('hex');
      sesiones.set(sid, { usuario: p.get('usuario'), saldo: 5_000_000, movimientos: [] });
      return send(302, '', { location: '/inicio', 'set-cookie': `sid=${sid}; HttpOnly; Path=/; SameSite=Lax` });
    }
    return send(302, '', { location: '/login?error=1' });
  }

  if (url.pathname === '/api/login' && req.method === 'POST') {
    const p = JSON.parse(await body(req) || '{}');
    if (USUARIOS[p.usuario] !== p.clave) return json(401, { codigo: 'NO_AUTORIZADO', mensaje: 'Credenciales inválidas' });
    const sid = crypto.randomBytes(16).toString('hex');
    sesiones.set(sid, { usuario: p.usuario, saldo: 5_000_000, movimientos: [] });
    res.writeHead(200, { 'content-type': 'application/json', 'set-cookie': `sid=${sid}; HttpOnly; Path=/; SameSite=Lax` });
    return res.end(JSON.stringify({ ok: true }));
  }

  if (url.pathname.startsWith('/api/')) {
    if (!s) return json(401, { codigo: 'NO_AUTORIZADO', mensaje: 'Sesión requerida' });
    if (url.pathname === '/api/saldo') return json(200, { saldo: s.saldo });
    if (url.pathname === '/api/transferencias' && req.method === 'POST') {
      const r = transferir(s, JSON.parse(await body(req) || '{}'));
      return r.mov ? json(201, r.mov) : json(r.status, { codigo: r.codigo, mensaje: r.mensaje });
    }
    if (url.pathname === '/api/transferencias' && req.method === 'GET') return json(200, s.movimientos);
    const m = /^\/api\/transferencias\/([\w-]+)$/.exec(url.pathname);
    if (m && req.method === 'GET') {
      const mov = s.movimientos.find(x => x.id === m[1]);
      return mov ? json(200, mov) : json(404, { codigo: 'NO_ENCONTRADA', mensaje: 'Transferencia no encontrada' });
    }
    return json(404, { codigo: 'RUTA', mensaje: 'No existe' });
  }

  if (!s) return send(302, '', { location: '/login' });
  if (url.pathname === '/salir') { sesiones.delete(/sid=([a-f0-9]+)/.exec(req.headers.cookie)[1]); return send(302, '', { location: '/login', 'set-cookie': 'sid=; Max-Age=0; Path=/' }); }
  if (url.pathname === '/' || url.pathname === '/inicio')
    return send(200, layout('Inicio', `<h1>Inicio</h1><p>Hola, ${s.usuario}</p><section aria-label="Saldo"><h2>Saldo disponible</h2><p data-testid="saldo-valor">${fmt(s.saldo)}</p></section>`));
  if (url.pathname === '/transferencias/nueva') return send(200, PAGINA_TRANSFERENCIA);
  if (url.pathname === '/historial')
    return send(200, layout('Historial', `<h1>Historial</h1>${s.movimientos.length ? `<table><thead><tr><th>Referencia</th><th>Cuenta destino</th><th>Monto</th><th>Estado</th></tr></thead><tbody>${s.movimientos.map(m => `<tr><td>${m.referencia}</td><td>${m.cuentaDestino}</td><td>${fmt(m.monto)}</td><td>${m.estado}</td></tr>`).join('')}</tbody></table>` : '<p>No tienes transferencias registradas</p>'}`));
  send(404, layout('No encontrado', '<h1>Página no encontrada</h1>'));
}).listen(PORT, () => console.log(`Banca Demo escuchando en http://localhost:${PORT}`));
