#!/usr/bin/env python3
"""API demo para evaluaciones (solo stdlib). Uso: python banca_demo_api.py [puerto]
GET /health -> {"status":"UP"}; GET /cuentas/<numero> (Bearer qa-token) -> cuenta; resto -> 404 {"error":...}."""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CUENTAS = {"0001": {"numero": "0001", "estado": "ACTIVA", "saldo": 1000}, "0002": {"numero": "0002", "estado": "BLOQUEADA", "saldo": 0}}


class H(BaseHTTPRequestHandler):
    def _json(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"status": "UP"})
        if self.path.startswith("/cuentas/"):
            if self.headers.get("Authorization") != "Bearer qa-token":
                return self._json(401, {"error": "no autorizado"})
            c = CUENTAS.get(self.path.rsplit("/", 1)[-1])
            return self._json(200, c) if c else self._json(404, {"error": "cuenta no existe"})
        return self._json(404, {"error": "no encontrado"})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1]) if len(sys.argv) > 1 else 8080), H).serve_forever()
