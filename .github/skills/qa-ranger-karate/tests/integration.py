"""Ejecuta las plantillas Maven de Karate v1 y v2 contra una API local de prueba.

Requiere Java 21 y Maven. Comprueba las plantillas sin conectar con servicios externos."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

SKILL = Path(__file__).resolve().parents[1]


class Api(BaseHTTPRequestHandler):
    token_calls = 0

    def log_message(self, *args):
        pass

    def respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.rfile.read(int(self.headers.get('Content-Length', '0')))
        type(self).token_calls += 1
        self.respond(200, {'access_token': 'integration-token'})

    def do_GET(self):
        if self.headers.get('Authorization') != 'Bearer integration-token':
            self.respond(401, {'codigo': '401', 'mensaje': 'Sin token'})
        elif self.path == '/pagos/ID-EXISTENTE':
            self.respond(200, {'id': 'ID-EXISTENTE', 'estado': 'ACTIVO', 'fechaCreacion': '2026-10-05'})
        else:
            self.respond(404, {'codigo': '404', 'mensaje': 'No existe'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--maven', default='mvn.cmd' if os.name == 'nt' else 'mvn')
    parser.add_argument('--java-home', type=Path)
    args = parser.parse_args()
    env = os.environ.copy()
    if args.java_home:
        env['JAVA_HOME'] = str(args.java_home)
        env['PATH'] = str(args.java_home / 'bin') + os.pathsep + env['PATH']
    env.update(CLIENT_ID='integration-client', CLIENT_SECRET='integration-secret')
    server = ThreadingHTTPServer(('127.0.0.1', 0), Api)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        with tempfile.TemporaryDirectory(prefix='kit-karate-integration-') as directory:
            root = Path(directory)
            for line in ('v1', 'v2'):
                Api.token_calls = 0
                subprocess.run([sys.executable, str(SKILL / 'scripts/scaffold.py'),
                    '--nombre', line + '-tests', '--linea', line, '--dominios', 'pagos',
                    '--salida', str(root)], check=True, capture_output=True)
                project = root / (line + '-tests')
                config = project / 'src/test/java/karate-config.js'
                config.write_text(config.read_text(encoding='utf-8').replace('{{TOKEN_URL_DEV}}', base + '/token'), encoding='utf-8')
                run = subprocess.run([args.maven, '-B', '-q', 'test', '-DbaseUrl=' + base],
                    cwd=project, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
                print(run.stdout[-10000:], run.stderr[-2000:], flush=True)
                if run.returncode:
                    raise RuntimeError(f'{line}: Maven terminó con {run.returncode}')
                reports = list((project / 'resources/qa/reports').rglob('karate-summary-json.txt'))
                if not reports:
                    reports = list((project / 'resources/qa/reports').rglob('karate-summary.json'))
                if reports:
                    summary = json.loads(reports[0].read_text(encoding='utf-8'))
                    failed = summary.get('scenariosFailed', summary.get('scenariosfailed'))
                    if summary.get('scenariosPassed') != 3 or failed != 0:
                        raise RuntimeError(f'{line}: resultados inesperados: {summary}')
                else:
                    # Lee los escenarios de v2 desde Cucumber JSON. Ese archivo no usa el resumen de v1.
                    scenarios = []
                    for file in (project / 'resources/qa/reports').rglob('*.json'):
                        payload = json.loads(file.read_text(encoding='utf-8'))
                        if isinstance(payload, list):
                            for feature in payload:
                                if isinstance(feature, dict):
                                    scenarios.extend(e for e in feature.get('elements', []) if e.get('type') == 'scenario')
                    if len(scenarios) != 3 or any(not s.get('steps') or any(
                        step.get('result', {}).get('status') != 'passed' for step in s['steps']) for s in scenarios):
                        files = [str(f.relative_to(project)) for f in (project / 'resources/qa/reports').rglob('*.json')]
                        raise RuntimeError(f'{line}: Cucumber no acredita 3 escenarios aprobados: {files}')
                if Api.token_calls != 1:
                    raise RuntimeError(f'{line}: callSingle llamó {Api.token_calls} veces al token')
                print(f'{line}: 3 escenarios aprobados, token solicitado una vez', flush=True)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
