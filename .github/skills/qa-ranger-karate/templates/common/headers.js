// Define las cabeceras de trazabilidad y autenticación de cada solicitud HTTP.
// Uso en Background:  * configure headers = read('classpath:common/headers.js')
function fn() {
  var out = {
    'X-Request-Id': java.util.UUID.randomUUID() + '',
    'Accept': 'application/json'
  };
  var auth = karate.get('authHeader');
  if (auth && auth.Authorization) {
    out.Authorization = auth.Authorization;
  }
  return out;
}
