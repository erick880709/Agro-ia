"""Ejecuta la prueba defectuosa de evaluación y guarda su trace, el registro de la ejecución.

Usa un proyecto con Playwright instalado. Comprueba que falle la aserción prevista.
Un error de instalación no acredita la reproducción del defecto."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True, help='Proyecto con node_modules/@playwright/test')
    parser.add_argument('--output', type=Path, required=True, help='Directorio nuevo para esta reproducción')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    cli = args.project.resolve() / 'node_modules/@playwright/test/cli.js'
    if not cli.is_file() or args.output.exists():
        parser.error('Se requiere Playwright instalado y un directorio de salida nuevo')
    output = args.output.resolve()
    output.mkdir(parents=True)
    shutil.copyfile(root / 'files/transferencia-flaky.spec.ts', output / 'transferencia-flaky.spec.ts')
    config = {'testDir': str(output), 'outputDir': str(output / 'artifacts'),
        'reporter': [['json', {'outputFile': str(output / 'results.json')}]],
        'use': {'baseURL': 'http://127.0.0.1:3100', 'trace': 'on', 'video': 'on', 'screenshot': 'on'},
        'webServer': {'command': f'node {json.dumps(str(root / "files/banca-demo/server.js"))} 3100',
            'url': 'http://127.0.0.1:3100/health', 'reuseExistingServer': False}}
    (output / 'playwright.config.cjs').write_text('module.exports = ' + json.dumps(config), encoding='utf-8')
    # Guarda la reproducción dentro del proyecto para localizar @playwright/test.
    # NODE_PATH permite indicar otra ubicación del paquete.
    env = dict(os.environ, NODE_PATH=str(args.project.resolve() / 'node_modules'),
               E2E_USER='usuario.qa', E2E_PASSWORD='Clave-Prueba-1')
    run = subprocess.run(['node', str(cli), 'test', '--config', str(output / 'playwright.config.cjs')], env=env)
    traces = list((output / 'artifacts').rglob('trace.zip'))
    if run.returncode == 0 or not traces:
        print('No se reprodujo el fallo con un trace; revisar dependencias y resultados.', file=sys.stderr)
        return 1
    # Comprueba que falle la aserción prevista. Tener un trace no descarta un error de instalación.
    report = json.loads((output / 'results.json').read_text(encoding='utf-8'))
    if report.get('stats', {}).get('unexpected') != 1:
        return 1
    errors = json.dumps(report, ensure_ascii=False)
    if 'Transferencia exitosa' not in errors or 'toContain' not in errors:
        print('La corrida falló antes de la aserción prevista.', file=sys.stderr)
        return 1
    print(f'Trace de la reproducción: {traces[0]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
